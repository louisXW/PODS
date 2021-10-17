"""
   Parallel synchronous optimization strategy using multiprocessing module.

   This is a simplified code from pySOT-0.1.36 (https://pysot.readthedocs.io/en/latest/) for P-DYCORS (parallel DYCORS).

   The parallel implementation using multiprocessing module as a replacement of

   the original event-based poap module (https://github.com/dbindel/POAP).

   This change devotes to make code easier to use.

"""

from __future__ import print_function
import numpy as np
import math
import logging
from experimental_design import SymmetricLatinHypercube, LatinHypercube
from adaptive_sampling import CandidateDYCORS
from rbf import *
from utils import *
import multiprocessing # Modfied on 10:39 PM 30 Jan
import time

# Get module-level logger
logger = logging.getLogger(__name__)


class SyncStrategyNoConstraintsMutipro(object):
    """Parallel synchronous optimization strategy without non-bound constraints.

    This class implements the parallel synchronous DYCORS strategy
    described by Wei Xia, Shoemaker and Taimoor.  After the initial experimental
    design (which is embarrassingly parallel), the optimization
    proceeds in phases.  During each phase, we allow nsamples
    simultaneous function evaluations. Samples are drawn randomly from around the
    current best point, and are sorted according to a merit function
    based on distance to other sample points and predicted function
    values according to the response surface.  After several
    successive significant improvements, we increase the sampling
    radius; after several failures to improve the function value, we
    decrease the sampling radius.  We restart once the sampling radius
    decreases below a threshold.

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
    :param simid: Indicates the index of simulation of a batch of simultaneous simulations in each iteration.
    :type simid: int
    :param iteration: indicates the index of iterations (generation)
    :type iteration: int
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

        # algorithm hyproparameters
        self.sigma_min = 0.2 * (0.5 ** 6)
        self.sigma_max = 0.2
        self.sigma_init = 0.2

        self.failtol = max(np.ceil(4.0 / self.nsamples), np.ceil(1.0 * data.dim / self.nsamples))
        self.succtol = 3
        self.maxfailtol = 4 * self.failtol

        # algorithm variable initialization
        self.numeval = 0
        self.numeval_old = 0 #modified at 2017 0918
        self.simid = 0     #Modified at 2017 09 18
        self.iteration = 0 #modified at 2017 09 18 09:14
        self.status = 0
        self.failcount = 0
        self.sigma = 0
        self.xbest = None
        self.fbest = np.inf
        self.fbest_old = None
        self.fbest_global = np.inf
        self.xbest_global = None

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

    def log_completion(self, obj, x, simid, iterid):
        """Record a completed evaluation to the log.

        :param record: Record of the function evaluation
        :type record: Object
        """
        xstr = np.array_str(x, max_line_width=np.inf,
                            precision=5, suppress_small=True)
        print("{} {:.3e} @ {}".format("evaluated simulation %s:"%(simid), obj, xstr))

        logger.info("{} {:.3e} @ {}".format("True", obj, xstr))

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
            self.failcount = 0

        else:
            self.status = min(-1, self.status - 1)
            self.failcount += 1
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
            print("=== Start ===")
            self.iteration = 1  #modified 2017 09 18
        else:
            logger.info("=== Restart ===")
            print("=== Restart ===")
        self.fhat.reset()
        self.sigma = self.sigma_init
        self.status = 0
        self.failcount = 0
        self.xbest = None
        self.fbest_old = None
        self.fbest = np.inf
        self.fhat.reset()

        start_sample = self.design.generate_points()
        assert start_sample.shape[1] == self.data.dim, \
            "Dimension mismatch between problem and experimental design"
        assert start_sample.shape[0] % self.nsamples == 0, \
            "set npts in experimental_design to be multiple of nsamples"
        start_sample = from_unit_box(start_sample, self.data)

        params = []
        simid = []
        genid = []
        iteration_pre = self.iteration
        for j in range(min(start_sample.shape[0], self.maxeval - self.numeval)):
            start_sample[j, :] = self.proj_fun(start_sample[j, :])  # Project onto feasible region
            self.iteration = j // self.nsamples + iteration_pre
            params.append(np.copy(start_sample[j, :]))
            simid.append(j % self.nsamples)
            genid.append(self.iteration)

        nprocessors = min(self.nsamples, multiprocessing.cpu_count())

        for batch_id in range(0, min(start_sample.shape[0], self.maxeval - self.numeval) // nprocessors):
            batch_first = batch_id * nprocessors
            batch_last = (batch_id + 1) * nprocessors

            paramters = zip(params[batch_first: batch_last], simid[batch_first: batch_last], genid[batch_first: batch_last])
            pool = multiprocessing.Pool(nprocessors)
            objfuns = pool.map(self.obj_func, paramters)
            pool.terminate()
            self.on_complete(objfuns, paramters)

        if self.extra is not None:
            self.sampling.init(np.vstack((start_sample, self.extra)), self.fhat, self.maxeval - self.numeval)
        else:
            self.sampling.init(start_sample, self.fhat, self.maxeval - self.numeval)

    def sample_adapt(self):
        """Generate samples from the search strategy and evaluate the samples in parallel"""

        self.adjust_step()

        nsamples = min(self.nsamples, self.maxeval - self.numeval)
        new_points = self.sampling.make_points(npts=nsamples, xbest=np.copy(self.xbest), sigma=self.sigma,
                                               proj_fun=self.proj_fun)
        params = []
        simid = []
        genid = []
        for i in range(nsamples):
            params.append(np.copy(np.ravel(new_points[i, :])))
            simid.append(i)
            genid.append(self.iteration)

        nprocessors = min(self.nsamples, multiprocessing.cpu_count())

        pool = multiprocessing.Pool(nprocessors)
        paramters = zip(params, simid, genid)
        objfuns = pool.map(self.obj_func, paramters)
        pool.terminate()
        self.on_complete(objfuns, paramters)

    def start_batch(self):
        """Generate and queue a new batch of points"""

        if self.sigma < self.sigma_min or self.failcount >= self.maxfailtol:
            self.sample_initial()
        else:
            self.sample_adapt()

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
        params = zip(*parameters)[0]
        simids = zip(*parameters)[1]
        iterids = zip(*parameters)[2]

        # Record calculated evaluations into a history list
        for indx, item in enumerate(objfuns):
            self.log_completion(item, params[indx], simids[indx], iterids[indx])
            self.fhat.add_point(params[indx], item)
            if item < self.fbest:
                self.xbest = params[indx]
                self.fbest = item
        if self.fbest < self.fbest_global:
            self.fbest_global = self.fbest
            self.xbest_global = self.xbest

        print ("Iteration: %s previous fbest: %s new fbest: %s "%(iterids[-1], self.fbest_old, self.fbest))
