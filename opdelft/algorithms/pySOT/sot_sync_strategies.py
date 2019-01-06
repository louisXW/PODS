"""
.. module:: sot_sync_strategies
   :synopsis: Parallel synchronous optimization strategy

.. moduleauthor:: David Bindel <bindel@cornell.edu>,
                David Eriksson <dme65@cornell.edu>

:Module: sot_sync_strategies
:Author: David Bindel <bindel@cornell.edu>,
        David Eriksson <dme65@cornell.edu>

"""

from __future__ import print_function
import numpy as np
import math
import logging
from pySOT.experimental_design import SymmetricLatinHypercube, LatinHypercube
from pySOT.adaptive_sampling import CandidateDYCORS
from poap.strategy import BaseStrategy, RetryStrategy
from pySOT.rbf import *
from pySOT.utils import *
from pySOT.rs_wrappers import *
import multiprocessing # Modfied on 10:39 PM 30 Jan
import time

# Get module-level logger
logger = logging.getLogger(__name__)

class SyncStrategyNoConstraints(BaseStrategy):
    """Parallel synchronous optimization strategy without non-bound constraints.

    This class implements the parallel synchronous SRBF strategy
    described by Regis and Shoemaker.  After the initial experimental
    design (which is embarrassingly parallel), the optimization
    proceeds in phases.  During each phase, we allow nsamples
    simultaneous function evaluations.  We insist that these
    evaluations run to completion -- if one fails for whatever reason,
    we will resubmit it.  Samples are drawn randomly from around the
    current best point, and are sorted according to a merit function
    based on distance to other sample points and predicted function
    values according to the response surface.  After several
    successive significant improvements, we increase the sampling
    radius; after several failures to improve the function value, we
    decrease the sampling radius.  We restart once the sampling radius
    decreases below a threshold.

    :param worker_id: Start ID in a multi-start setting
    :type worker_id: int
    :param data: Problem parameter data structure
    :type data: Object
    :param response_surface: Surrogate model object
    :type response_surface: Object
    :param maxeval: Stopping criterion. If positive, this is an 
                    evaluation budget. If negative, this is a time
                    budget in seconds.
    :type maxeval: int
    :param nsamples: Number of simultaneous fevals allowed
    :type nsamples: int
    :param exp_design: Experimental design
    :type exp_design: Object
    :param sampling_method: Sampling method for finding
        points to evaluate
    :type sampling_method: Object
    :param extra: Points to be added to the experimental design
    :type extra: numpy.array
    :param extra_vals: Values of the points in extra (if known). Use nan for values that are not known.
    :type extra_vals: numpy.array
    """

    def __init__(self, worker_id, data, response_surface, maxeval, nsamples,
                 exp_design=None, sampling_method=None, extra=None, extra_vals=None):

        # Check stopping criterion
        self.start_time = time.time()
        if maxeval < 0:  # Time budget
            self.maxeval = np.inf
            self.time_budget = np.abs(maxeval)
        else:
            self.maxeval = maxeval
            self.time_budget = np.inf

        # Import problem information
        self.worker_id = worker_id
        self.data = data
        self.fhat = response_surface
        if self.fhat is None:
            self.fhat = RBFInterpolant(kernel=CubicKernel, tail=LinearTail, maxp=maxeval)
        self.fhat.reset()  # Just to be sure!

        self.nsamples = nsamples
        self.extra = extra
        self.extra_vals = extra_vals

        # Default to generate sampling points using Symmetric Latin Hypercube
        self.design = exp_design
        if self.design is None:
            if self.data.dim > 50:
                self.design = LatinHypercube(data.dim, data.dim+1)
            else:
                self.design = SymmetricLatinHypercube(data.dim, 2*(data.dim+1))

        self.xrange = np.asarray(data.xup - data.xlow)

        # algorithm parameters
        self.sigma_min = 0.005
        self.sigma_max = 0.2
        self.sigma_init = 0.2

        self.failtol = max(5, data.dim)
        self.succtol = 3

        self.numeval = 0
        self.numeval_old = 0 #modified at 2017 0918
        self.simid = 0     #Modified at 2017 09 18
        self.iteration = 0 #modified at 2017 09 18 09:14
        self.status = 0
        self.sigma = 0
        self.resubmitter = RetryStrategy()
        self.xbest = None
        self.fbest = np.inf
        self.fbest_old = None

        # Set up search procedures and initialize
        self.sampling = sampling_method
        if self.sampling is None:
            self.sampling = CandidateDYCORS(data)

        self.check_input()

        # Start with first experimental design
        self.sample_initial()

    def check_input(self):
        """Checks that the inputs are correct"""

        self.check_common()
        if hasattr(self.data, "eval_ineq_constraints"):
            raise ValueError("Optimization problem has constraints,\n"
                             "SyncStrategyNoConstraints can't handle constraints")
        if hasattr(self.data, "eval_eq_constraints"):
            raise ValueError("Optimization problem has constraints,\n"
                             "SyncStrategyNoConstraints can't handle constraints")

    def check_common(self):
        """Checks that the inputs are correct"""

        # Check evaluation budget
        if self.extra is None:
            if self.maxeval < self.design.npts:
                raise ValueError("Experimental design is larger than the evaluation budget")
        else:
            # Check the number of unknown extra points
            if self.extra_vals is None:  # All extra point are unknown
                nextra = self.extra.shape[0]
            else:  # We know the values at some extra points so count how many we don't know
                nextra = np.sum(np.isinf(self.extra_vals)) + np.sum(np.isnan(self.extra_vals))

            if self.maxeval < self.design.npts + nextra:
                raise ValueError("Experimental design + extra points "
                                 "exceeds the evaluation budget")

        # Check dimensionality
        if self.design.dim != self.data.dim:
            raise ValueError("Experimental design and optimization "
                             "problem have different dimensions")
        if self.extra is not None:
            if self.data.dim != self.extra.shape[1]:
                raise ValueError("Extra point and optimization problem "
                                 "have different dimensions")
            if self.extra_vals is not None:
                if self.extra.shape[0] != len(self.extra_vals):
                    raise ValueError("Extra point values has the wrong length")

        # Check that the optimization problem makes sense
        check_opt_prob(self.data)

    def proj_fun(self, x):
        """Projects a set of points onto the feasible region

        :param x: Points, of size npts x dim
        :type x: numpy.array
        :return: Projected points
        :rtype: numpy.array
        """

        x = np.atleast_2d(x)
        return round_vars(self.data, x)

    def log_completion(self, record):
        """Record a completed evaluation to the log.

        :param record: Record of the function evaluation
        :type record: Object
        """

        xstr = np.array_str(record.params[0], max_line_width=np.inf,
                            precision=5, suppress_small=True)
        if record.feasible:
            logger.info("{} {:.3e} @ {}".format("True", record.value, xstr))
        else:
            logger.info("{} {:.3e} @ {}".format("False", record.value, xstr))

    def adjust_step(self):
        """Adjust the sampling radius sigma.

        After succtol successful steps, we cut the sampling radius;
        after failtol failed steps, we double the sampling radius.
        """

        # Initialize if this is the first adaptive step
        if self.fbest_old is None:
            self.fbest_old = self.fbest
            return

        # Check if we succeeded at significant improvement
        if self.fbest < self.fbest_old - 1e-3 * math.fabs(self.fbest_old):
            self.status = max(1, self.status + 1)
        else:
            self.status = min(-1, self.status - 1)
        self.fbest_old = self.fbest

        # Check if step needs adjusting
        if self.status <= -self.failtol:
            self.status = 0
            self.sigma /= 2
            logger.info("Reducing sigma")
        if self.status >= self.succtol:
            self.status = 0
            self.sigma = min([2.0 * self.sigma, self.sigma_max])
            logger.info("Increasing sigma")

    def sample_initial(self):
        """Generate and queue an initial experimental design."""

        if self.numeval == 0:
            logger.info("=== Start ===")
            self.iteration = 1  #modified 2017 09 18
        else:
            logger.info("=== Restart ===")
        self.fhat.reset()
        self.sigma = self.sigma_init
        self.status = 0
        self.xbest = None
        self.fbest_old = None
        self.fbest = np.inf
        self.fhat.reset()

        start_sample = self.design.generate_points()
        assert start_sample.shape[1] == self.data.dim, \
            "Dimension mismatch between problem and experimental design"
        start_sample = from_unit_box(start_sample, self.data)

        if self.extra is not None:
            # We know the values if this is a restart, so add the points to the surrogate
            if self.numeval > 0:
                for i in range(len(self.extra_vals)):
                    xx = self.proj_fun(np.copy(self.extra[i, :]))
                    self.fhat.add_point(np.ravel(xx), self.extra_vals[i])
            else:  # Check if we know the values of the points
                if self.extra_vals is None:
                    self.extra_vals = np.nan * np.ones((self.extra.shape[0], 1))

                for i in range(len(self.extra_vals)):
                    xx = self.proj_fun(np.copy(self.extra[i, :]))
                    if np.isnan(self.extra_vals[i]) or np.isinf(self.extra_vals[i]):  # We don't know this value
                        proposal = self.propose_eval(np.ravel(xx))
                        proposal.extra_point_id = i  # Decorate the proposal
                        self.resubmitter.rput(proposal)
                    else:  # We know this value
                        self.fhat.add_point(np.ravel(xx), self.extra_vals[i])

        # Evaluate the experimental design
        for j in range(min(start_sample.shape[0], self.maxeval - self.numeval)):
            start_sample[j, :] = self.proj_fun(start_sample[j, :])  # Project onto feasible region
            self.iteration = j // self.nsamples + 1        #Modified 2017 09 18
            proposal = self.propose_eval(np.copy(start_sample[j, :]), j, self.iteration)    #Modified 2017 09 18
            self.resubmitter.rput(proposal)



        if self.extra is not None:
            self.sampling.init(np.vstack((start_sample, self.extra)), self.fhat, self.maxeval - self.numeval)
        else:
            self.sampling.init(start_sample, self.fhat, self.maxeval - self.numeval)

    def sample_adapt(self):
        """Generate and queue samples from the search strategy"""

        self.adjust_step()

        nsamples = min(self.nsamples, self.maxeval - self.numeval)
        new_points = self.sampling.make_points(npts=nsamples, xbest=np.copy(self.xbest), sigma=self.sigma,
                                               proj_fun=self.proj_fun)
        for i in range(nsamples):

            proposal = self.propose_eval(np.copy(np.ravel(new_points[i, :])), i, self.iteration)     #Modified 2017 09 19
            self.resubmitter.rput(proposal)

    def start_batch(self):
        """Generate and queue a new batch of points"""

        if self.sigma < self.sigma_min:
            self.sample_initial()
        else:
            self.sample_adapt()

    def propose_action(self):
        """Propose an action"""

        current_time = time.time()
        if self.numeval >= self.maxeval or (current_time - self.start_time) >= self.time_budget:
            return self.propose_terminate()
        elif self.resubmitter.num_eval_outstanding == 0:
            self.iteration = self.iteration + 1
            self.start_batch()
            self.numeval_old = self.numeval  #modified 2017 0918
        return self.resubmitter.get()

    def on_reply_accept(self, proposal):
        # Transfer the decorations
        if hasattr(proposal, 'extra_point_id'):
            proposal.record.extra_point_id = proposal.extra_point_id

    def on_complete(self, record):
        """Handle completed function evaluation.

        When a function evaluation is completed we need to ask the constraint
        handler if the function value should be modified which is the case for
        say a penalty method. We also need to print the information to the
        logfile, update the best value found so far and notify the GUI that
        an evaluation has completed.

        :param record: Evaluation record
        :type record: Object
        """

        # Check for extra_point decorator
        if hasattr(record, 'extra_point_id'):
            self.extra_vals[record.extra_point_id] = record.value

        self.numeval += 1
        # print ('Iteration number %d Evaluation number %d' %(self.iteration, self.numeval))
        record.worker_id = self.worker_id
        record.worker_numeval = self.numeval
        record.feasible = True
        self.log_completion(record)
        self.fhat.add_point(np.copy(record.params[0]), record.value)
        if record.value < self.fbest:
            self.xbest = np.copy(record.params[0])
            self.fbest = record.value

class SyncStrategyNoConstraintsMutipro(BaseStrategy):
    """Parallel synchronous optimization strategy without non-bound constraints.

    This class implements the parallel synchronous SRBF strategy
    described by Regis and Shoemaker.  After the initial experimental
    design (which is embarrassingly parallel), the optimization
    proceeds in phases.  During each phase, we allow nsamples
    simultaneous function evaluations.  We insist that these
    evaluations run to completion -- if one fails for whatever reason,
    we will resubmit it.  Samples are drawn randomly from around the
    current best point, and are sorted according to a merit function
    based on distance to other sample points and predicted function
    values according to the response surface.  After several
    successive significant improvements, we increase the sampling
    radius; after several failures to improve the function value, we
    decrease the sampling radius.  We restart once the sampling radius
    decreases below a threshold.

    :param worker_id: Start ID in a multi-start setting
    :type worker_id: int
    :param data: Problem parameter data structure
    :type data: Object
    :param response_surface: Surrogate model object
    :type response_surface: Object
    :param maxeval: Stopping criterion. If positive, this is an
                    evaluation budget. If negative, this is a time
                    budget in seconds.
    :type maxeval: int
    :param nsamples: Number of simultaneous fevals allowed
    :type nsamples: int
    :param exp_design: Experimental design
    :type exp_design: Object
    :param sampling_method: Sampling method for finding
        points to evaluate
    :type sampling_method: Object
    :param extra: Points to be added to the experimental design
    :type extra: numpy.array
    :param extra_vals: Values of the points in extra (if known). Use nan for values that are not known.
    :type extra_vals: numpy.array
    """

    def __init__(self, obj_func, worker_id, data, response_surface, maxeval, nsamples,
                 exp_design=None, sampling_method=None, extra=None, extra_vals=None):

        # Check stopping criterion
        self.start_time = time.time()
        if maxeval < 0:  # Time budget
            self.maxeval = np.inf
            self.time_budget = np.abs(maxeval)
        else:
            self.maxeval = maxeval
            self.time_budget = np.inf

        # Import problem information
        self.obj_func = obj_func
        self.worker_id = worker_id
        self.data = data
        print ('number of objectives', self.data.no_sub_objs)
        self.fhat = response_surface
        if self.fhat is None:
            self.fhat = RBFInterpolant(kernel=CubicKernel, tail=LinearTail, maxp=maxeval)
        self.fhat.reset()  # Just to be sure!

        self.nsamples = nsamples
        self.extra = extra
        self.extra_vals = extra_vals

        # Default to generate sampling points using Symmetric Latin Hypercube
        self.design = exp_design
        if self.design is None:
            if self.data.dim > 50:
                self.design = LatinHypercube(data.dim, data.dim+1)
            else:
                self.design = SymmetricLatinHypercube(data.dim, 2*(data.dim+1))

        self.xrange = np.asarray(data.xup - data.xlow)

        # algorithm parameters
        self.sigma_min = 0.005
        self.sigma_max = 0.2
        self.sigma_init = 0.2

        self.failtol = max(5, data.dim)
        self.succtol = 3

        self.numeval = 0
        self.numeval_old = 0 #modified at 2017 0918
        self.simid = 0     #Modified at 2017 09 18
        self.iteration = 0 #modified at 2017 09 18 09:14
        self.status = 0
        self.sigma = 0
        self.resubmitter = RetryStrategy()
        self.xbest = None
        self.fbest = np.inf
        self.fbest_old = None

        #Record the objectives of each evaluations in a history list
        self.parameters =[]
        self.sub_objs = []
        self.sub_objs_best = None

        # Set up search procedures and initialize
        self.sampling = sampling_method
        if self.sampling is None:
            self.sampling = CandidateDYCORS(data)

        self.check_input()
        # Start with first experimental design
        self.sample_initial()

    def check_input(self):
        """Checks that the inputs are correct"""

        self.check_common()
        if hasattr(self.data, "eval_ineq_constraints"):
            raise ValueError("Optimization problem has constraints,\n"
                             "SyncStrategyNoConstraints can't handle constraints")
        if hasattr(self.data, "eval_eq_constraints"):
            raise ValueError("Optimization problem has constraints,\n"
                             "SyncStrategyNoConstraints can't handle constraints")

    def check_common(self):
        """Checks that the inputs are correct"""

        # Check evaluation budget
        if self.extra is None:
            if self.maxeval < self.design.npts:
                raise ValueError("Experimental design is larger than the evaluation budget")
        else:
            # Check the number of unknown extra points
            if self.extra_vals is None:  # All extra point are unknown
                nextra = self.extra.shape[0]
            else:  # We know the values at some extra points so count how many we don't know
                nextra = np.sum(np.isinf(self.extra_vals)) + np.sum(np.isnan(self.extra_vals))

            if self.maxeval < self.design.npts + nextra:
                raise ValueError("Experimental design + extra points "
                                 "exceeds the evaluation budget")

        # Check dimensionality
        if self.design.dim != self.data.dim:
            raise ValueError("Experimental design and optimization "
                             "problem have different dimensions")
        if self.extra is not None:
            if self.data.dim != self.extra.shape[1]:
                raise ValueError("Extra point and optimization problem "
                                 "have different dimensions")
            if self.extra_vals is not None:
                if self.extra.shape[0] != len(self.extra_vals):
                    raise ValueError("Extra point values has the wrong length")

        # Check that the optimization problem makes sense
        check_opt_prob(self.data)

    def proj_fun(self, x):
        """Projects a set of points onto the feasible region

        :param x: Points, of size npts x dim
        :type x: numpy.array
        :return: Projected points
        :rtype: numpy.array
        """

        x = np.atleast_2d(x)
        return round_vars(self.data, x)

    def log_completion(self, record):
        """Record a completed evaluation to the log.

        :param record: Record of the function evaluation
        :type record: Object
        """

        xstr = np.array_str(record.params[0], max_line_width=np.inf,
                            precision=5, suppress_small=True)
        if record.feasible:
            logger.info("{} {:.3e} @ {}".format("True", record.value, xstr))
        else:
            logger.info("{} {:.3e} @ {}".format("False", record.value, xstr))

    def adjust_step(self):
        """Adjust the sampling radius sigma.

        After succtol successful steps, we cut the sampling radius;
        after failtol failed steps, we double the sampling radius.
        """

        # Initialize if this is the first adaptive step
        if self.fbest_old is None:
            self.fbest_old = self.fbest
            return

        # Check if we succeeded at significant improvement
        if self.fbest < self.fbest_old - 1e-3 * math.fabs(self.fbest_old):
            self.status = max(1, self.status + 1)
        else:
            self.status = min(-1, self.status - 1)
        self.fbest_old = self.fbest

        # Check if step needs adjusting
        if self.status <= -self.failtol:
            self.status = 0
            self.sigma /= 2
            logger.info("Reducing sigma")
        if self.status >= self.succtol:
            self.status = 0
            self.sigma = min([2.0 * self.sigma, self.sigma_max])
            logger.info("Increasing sigma")

    def sample_initial(self):
        """Generate and queue an initial experimental design."""

        if self.numeval == 0:
            logger.info("=== Start ===")
            self.iteration = 1  #modified 2017 09 18
        else:
            logger.info("=== Restart ===")
        self.fhat.reset()
        self.sigma = self.sigma_init
        self.status = 0
        self.xbest = None
        self.fbest_old = None
        self.fbest = np.inf
        self.fhat.reset()

        start_sample = self.design.generate_points()
        assert start_sample.shape[1] == self.data.dim, \
            "Dimension mismatch between problem and experimental design"
        start_sample = from_unit_box(start_sample, self.data)

        if self.extra is not None:
            # We know the values if this is a restart, so add the points to the surrogate
            if self.numeval > 0:
                for i in range(len(self.extra_vals)):
                    xx = self.proj_fun(np.copy(self.extra[i, :]))
                    self.fhat.add_point(np.ravel(xx), self.extra_vals[i])
            else:  # Check if we know the values of the points
                if self.extra_vals is None:
                    self.extra_vals = np.nan * np.ones((self.extra.shape[0], 1))

                for i in range(len(self.extra_vals)):
                    xx = self.proj_fun(np.copy(self.extra[i, :]))
                    if np.isnan(self.extra_vals[i]) or np.isinf(self.extra_vals[i]):  # We don't know this value
                        proposal = self.propose_eval(np.ravel(xx))
                        proposal.extra_point_id = i  # Decorate the proposal
                        self.resubmitter.rput(proposal)
                    else:  # We know this value
                        self.fhat.add_point(np.ravel(xx), self.extra_vals[i])

        # Evaluate the experimental design
        params = []
        simid = []
        genid = []
        for j in range(min(start_sample.shape[0], self.maxeval - self.numeval)):
            start_sample[j, :] = self.proj_fun(start_sample[j, :])  # Project onto feasible region
            self.iteration = j // self.nsamples + 1        #Modified 2017 09 18
            # proposal = self.propose_eval(np.copy(start_sample[j, :]), j, self.iteration)    #Modified 2017 09 18
            params.append(np.copy(start_sample[j, :]))
            simid.append(j)
            genid.append(self.iteration)

        nprocessors = min(self.nsamples, multiprocessing.cpu_count())
        pool = multiprocessing.Pool(nprocessors)

        paramters = zip(params, simid, genid)
        objfuns = pool.map(self.obj_func, paramters)
        self.on_complete(objfuns, params)

        if self.extra is not None:
            self.sampling.init(np.vstack((start_sample, self.extra)), self.fhat, self.maxeval - self.numeval)
        else:
            self.sampling.init(start_sample, self.fhat, self.maxeval - self.numeval)

    def sample_adapt(self):
        """Generate and queue samples from the search strategy"""

        self.adjust_step()

        nsamples = min(self.nsamples, self.maxeval - self.numeval)
        new_points = self.sampling.make_points(npts=nsamples, xbest=np.copy(self.xbest), sigma=self.sigma,
                                               proj_fun=self.proj_fun)
        params = []
        simid = []
        genid = []
        for i in range(nsamples):
                        # proposal = self.propose_eval(np.copy(start_sample[j, :]), j, self.iteration)    #Modified 2017 09 18
            params.append(np.copy(np.ravel(new_points[i, :])))
            simid.append(i)
            genid.append(self.iteration)
            # proposal = self.propose_eval(np.copy(np.ravel(new_points[i, :])), i, self.iteration)     #Modified 2017 09 19
            # self.resubmitter.rput(proposal)
        nprocessors = min(self.nsamples, multiprocessing.cpu_count())
        pool = multiprocessing.Pool(nprocessors)
        paramters = zip(params, simid, genid)
        # energies = self.func(params, *self.args)
        objfuns = pool.map(self.obj_func, paramters)
        self.on_complete(objfuns, params)

    def start_batch(self):
        """Generate and queue a new batch of points"""

        if self.sigma < self.sigma_min:
            self.sample_initial()
        else:
            self.sample_adapt()

    def propose_action(self):
        """Propose an action"""

        current_time = time.time()
        if self.numeval >= self.maxeval or (current_time - self.start_time) >= self.time_budget:
            # return self.propose_terminate()
            return "The total calibration finished", self.fbest
        elif self.resubmitter.num_eval_outstanding == 0:
            self.iteration = self.iteration + 1
            self.start_batch()
            self.numeval_old = self.numeval  #modified 2017 0918
        # return self.resubmitter.get()

    def on_reply_accept(self, proposal):
        # Transfer the decorations
        if hasattr(proposal, 'extra_point_id'):
            proposal.record.extra_point_id = proposal.extra_point_id

    def on_complete(self, objfuns, parameters):
        """Handle completed function evaluation.

        When a function evaluation is completed we need to ask the constraint
        handler if the function value should be modified which is the case for
        say a penalty method. We also need to print the information to the
        logfile, update the best value found so far and notify the GUI that
        an evaluation has completed.

        :param record: Evaluation record
        :type record: Object
        """
        self.numeval += np.size(objfuns, 0)

        # Record calculated evaluations into a history list
        for indx, item in enumerate(objfuns):
            self.sub_objs.append(item)
            self.parameters.append(parameters[indx])

        sub_objs = np.asarray(self.sub_objs)

        if np.size(sub_objs, 1) != self.data.no_sub_objs:
            raise ValueError('Number of sub objectives mismatch')

        if self.data.no_sub_objs > 1:
            obj = 0
            # Recalculate the fitness of each evaluations based on the Dynamically Normalized Objective Function
            for i in range(self.data.no_sub_objs):
                obj = obj + (sub_objs[:, i] - min(sub_objs[:, i])) / float(max(sub_objs[:, i])-min(sub_objs[:, i]))

            # Rebuild the surrogate (RBF)
            self.fhat.reset()
            for indx, item in enumerate(obj):
                self.fhat.add_point(self.parameters[indx], item)
        elif self.data.no_sub_objs == 1:
            obj = sub_objs[:, 0]
            for indx, item in enumerate(obj):
                self.fhat.add_point(self.parameters[indx], item)

        # Record the best solution based on the new fitness value
        index1 = obj.argmin()
        self.xbest = self.parameters[index1]
        self.fbest = obj[index1]
        self.sub_objs_best = sub_objs[index1]
        print ("fbest_old", self.fbest_old)
        print ("fbest", self.fbest)
        print ("subfbest", self.sub_objs[index1])

class SyncStrategyPenalty(SyncStrategyNoConstraints):
    """Parallel synchronous optimization strategy with non-bound constraints.

    This is an extension of SyncStrategyNoConstraints that also works with
    bound constraints. We currently only allow inequality constraints, since
    the candidate based methods don't work well with equality constraints.
    We also assume that the constraints are cheap to evaluate, i.e., so that
    it is easy to check if a given point is feasible. More strategies that
    can handle expensive constraints will be added.

    We use a penalty method in the sense that we try to minimize:

    .. math::
        f(x) + \\mu \\sum_j (\\max(0, g_j(x))^2

    where :math:`g_j(x) \\leq 0` are cheap inequality constraints. As a
    measure of promising function values we let all infeasible points have
    the value of the feasible candidate point with the worst function value,
    since large penalties makes it impossible to distinguish between feasible
    points.

    When it comes to the value of :math:`\\mu`, just choose a very large value.

    :param worker_id: Start ID in a multi-start setting
    :type worker_id: int
    :param data: Problem parameter data structure
    :type data: Object
    :param response_surface: Surrogate model object
    :type response_surface: Object
    :param maxeval: Function evaluation budget
    :type maxeval: int
    :param nsamples: Number of simultaneous fevals allowed
    :type nsamples: int
    :param exp_design: Experimental design
    :type exp_design: Object
    :param sampling_method: Sampling method for finding
        points to evaluate
    :type sampling_method: Object
    :param extra: Points to be added to the experimental design
    :type extra: numpy.array
    :param penalty: Penalty for violating constraints
    :type penalty: float
    """

    def __init__(self, worker_id, data, response_surface, maxeval, nsamples,
                 exp_design=None, sampling_method=None, extra=None,
                 penalty=1e6):

        # Evals wrapper for penalty method
        def penalty_evals(fhat, xx):
            penalty = self.penalty_fun(xx).T
            vals = fhat.evals(xx)
            if xx.shape[0] > 1:
                ind = (np.where(penalty <= 0.0)[0]).T
                if ind.shape[0] > 1:
                    ind2 = (np.where(penalty > 0.0)[0]).T
                    ind3 = np.argmax(np.squeeze(vals[ind]))
                    vals[ind2] = vals[ind3]
                    return vals
            return vals + penalty

        # Derivs wrapper for penalty method
        def penalty_derivs(fhat, xx):
            x = np.atleast_2d(xx)
            constraints = np.array(self.data.eval_ineq_constraints(x))
            dconstraints = self.data.deriv_ineq_constraints(x)
            constraints[np.where(constraints < 0.0)] = 0.0
            return np.atleast_2d(fhat.deriv(xx)) + \
                2 * self.penalty * np.sum(
                    constraints * np.rollaxis(dconstraints, 2), axis=2).T

        SyncStrategyNoConstraints.__init__(self,  worker_id, data,
                                           RSPenalty(response_surface, penalty_evals, penalty_derivs),
                                           maxeval, nsamples, exp_design,
                                           sampling_method, extra)
        self.penalty = penalty

    def check_input(self):
        """Checks that the inputs are correct"""

        self.check_common()
        if not hasattr(self.data, "eval_ineq_constraints"):
            raise AttributeError("Optimization problem has no inequality constraints")
        if hasattr(self.data, "eval_eq_constraints"):
            raise AttributeError("Optimization problem has equality constraints,\n"
                                 "SyncStrategyPenalty can't handle equality constraints")

    def penalty_fun(self, xx):
        """Computes the penalty for constraint violation

        :param xx: Points to compute the penalty for
        :type xx: numpy.array
        :return: Penalty for constraint violations
        :rtype: numpy.array
        """

        vec = np.array(self.data.eval_ineq_constraints(xx))
        vec[np.where(vec < 0.0)] = 0.0
        vec **= 2
        return self.penalty * np.asmatrix(np.sum(vec, axis=1))

    def on_complete(self, record):
        """Handle completed function evaluation.

        When a function evaluation is completed we need to ask the constraint
        handler if the function value should be modified which is the case for
        say a penalty method. We also need to print the information to the
        logfile, update the best value found so far and notify the GUI that
        an evaluation has completed.

        :param record: Evaluation record
        :type record: Object
        """

        # Check for extra_point decorator
        if hasattr(record, 'extra_point_id'):
            self.extra_vals[record.extra_point_id] = record.value

        x = np.zeros((1, record.params[0].shape[0]))
        x[0, :] = np.copy(record.params[0])
        penalty = self.penalty_fun(x)[0, 0]
        if penalty > 0.0:
            record.feasible = False
        else:
            record.feasible = True
        self.log_completion(record)
        self.numeval += 1
        record.worker_id = self.worker_id
        record.worker_numeval = self.numeval
        self.fhat.add_point(np.copy(record.params[0]), record.value)
        # Check if the penalty function is a new best
        if record.value + penalty < self.fbest:
            self.xbest = np.copy(record.params[0])
            self.fbest = record.value + penalty

class SyncStrategyProjection(SyncStrategyNoConstraints):
    """Parallel synchronous optimization strategy with non-bound constraints.
    It uses a supplied method to project proposed points onto the feasible
    region in order to always evaluate feasible points which is useful in
    situations where it is easy to project onto the feasible region and where
    the objective function is nonsensical for infeasible points.

    This is an extension of SyncStrategyNoConstraints that also works with
    bound constraints.

    :param worker_id: Start ID in a multi-start setting
    :type worker_id: int
    :param data: Problem parameter data structure
    :type data: Object
    :param response_surface: Surrogate model object
    :type response_surface: Object
    :param maxeval: Function evaluation budget
    :type maxeval: int
    :param nsamples: Number of simultaneous fevals allowed
    :type nsamples: int
    :param exp_design: Experimental design
    :type exp_design: Object
    :param sampling_method: Sampling method for finding
        points to evaluate
    :type sampling_method: Object
    :param extra: Points to be added to the experimental design
    :type extra: numpy.array
    :param proj_fun: Function that projects one point onto the feasible region
    :type proj_fun: Object
    """

    def __init__(self, worker_id, data, response_surface, maxeval, nsamples,
                 exp_design=None, sampling_method=None, extra=None,
                 proj_fun=None):

        self.projection = proj_fun
        SyncStrategyNoConstraints.__init__(self,  worker_id, data,
                                           response_surface, maxeval,
                                           nsamples, exp_design,
                                           sampling_method, extra)

    def check_input(self):
        """Checks that the inputs are correct"""

        self.check_common()
        if not (hasattr(self.data, "eval_ineq_constraints") or
                hasattr(self.data, "eval_eq_constraints")):
            raise AttributeError("Optimization problem has no constraints")

    def proj_fun(self, x):
        """Projects a set of points onto the feasible region

        :param x: Points, of size npts x dim
        :type x: numpy.array
        :return: Projected points
        :rtype: numpy.array
        """

        x = np.atleast_2d(x)
        for i in range(x.shape[0]):
            x[i, :] = self.projection(x[i, :])
        return x
