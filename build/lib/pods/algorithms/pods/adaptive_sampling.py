"""
.. module:: adaptive_sampling
   :synopsis: Ways of finding the next point to evaluate in the adaptive phase

.. moduleauthor:: David Eriksson <dme65@cornell.edu>,
                David Bindel <bindel@cornell.edu>

:Module: adaptive_sampling
:Author: David Eriksson <dme65@cornell.edu>,
        David Bindel <bindel@cornell.edu>

"""

import math
import scipy.stats as stats
from merit_functions import *
import types


def __fix_docs(cls):
    """Help function for stealing docs from the parent"""
    for name, func in vars(cls).items():
        if isinstance(func, types.FunctionType) and not func.__doc__:
            for parent in cls.__bases__:
                parfunc = getattr(parent, name, None)
                if parfunc and getattr(parfunc, '__doc__', None):
                    func.__doc__ = parfunc.__doc__
                    break
    return cls



class CandidateSRBF(object):
    """An implementation of Stochastic RBF

    This is an implementation of the candidate points method that is
    proposed in the first SRBF paper. Candidate points are generated
    by making normally distributed perturbations with standard
    deviation sigma around the best solution. The candidate point that
    minimizes a specified merit function is selected as the next
    point to evaluate.

    :param data: Optimization problem object
    :type data: Object
    :param numcand: Number of candidate points to be used. Default is min([5000, 100*data.dim])
    :type numcand: int
    :param weights: Weights used for the merit function, to balance exploration vs exploitation
    :type weights: list of numpy.array

    :raise ValueError: If number of candidate points is
        incorrect or if the weights aren't a list in [0, 1]

    :ivar data: Optimization problem object
    :ivar fhat: Response surface object
    :ivar xrange: Variable ranges, xup - xlow
    :ivar dtol: Smallest allowed distance between evaluated points 1e-3 * sqrt(dim)
    :ivar weights: Weights used for the merit function
    :ivar proposed_points: List of points proposed to the optimization algorithm
    :ivar dmerit: Minimum distance between the points and the proposed points
    :ivar xcand: Candidate points
    :ivar fhvals: Predicted values by the surrogate model
    :ivar next_weight: Index of the next weight to be used
    :ivar numcand: Number of candidate points
    :ivar budget: Remaining evaluation budget

    .. note:: This object needs to be initialized with the init method. This is done when the
        initial phase has finished.

    .. todo:: Get rid of the proposed_points object and replace it by something that is
        controlled by the strategy.
    """

    def __init__(self, data, numcand=None, weights=None):
        self.data = data
        self.fhat = None
        self.xrange = self.data.xup - self.data.xlow
        self.dtol = 1e-3 * math.sqrt(data.dim)
        self.weights = weights
        if self.weights is None:
            self.weights = [0.3, 0.5, 0.8, 0.95]
        self.proposed_points = None
        self.dmerit = None
        self.xcand = None
        self.fhvals = None
        self.next_weight = 0
        self.numcand = numcand
        if self.numcand is None:
            self.numcand = min([5000, 100*data.dim])
        self.budget = None

        # Check that the inputs make sense
        if not(isinstance(self.numcand, int) and self.numcand > 0):
            raise ValueError("The number of candidate points has to be a positive integer")
        if not((isinstance(self.weights, np.ndarray) or isinstance(self.weights, list))
               and max(self.weights) <= 1 and min(self.weights) >= 0):
            raise ValueError("Incorrect weights")

    def init(self, start_sample, fhat, budget):
        """Initialize the sampling method after the initial phase

        This initializes the list of sampling methods after the initial phase
        has finished and the experimental design has been evaluated. The user
        provides the points in the experimental design, the surrogate model,
        and the remaining evaluation budget.

        :param start_sample: Points in the experimental design
        :type start_sample: numpy.array
        :param fhat: Surrogate model
        :type fhat: Object
        :param budget: Evaluation budget
        :type budget: int
        """

        self.proposed_points = start_sample
        self.budget = budget
        self.fhat = fhat

    def remove_point(self, x):
        """Remove x from proposed_points

        This removes x from the list of proposed points in the case where the optimization
        strategy decides to not evaluate x.

        :param x: Point to be removed
        :type x: numpy.array
        :return: True if points was removed, False otherwise
        :type: bool
        """

        idx = np.sum(np.abs(self.proposed_points - x), axis=1).argmin()
        if np.sum(np.abs(self.proposed_points[idx, :] - x)) < 1e-10:
            self.proposed_points = np.delete(self.proposed_points, idx, axis=0)
            return True
        return False

    def __generate_cand__(self, scalefactors, xbest, subset):
        self.xcand = np.ones((self.numcand,  self.data.dim)) * xbest
        for i in subset:
            lower, upper = self.data.xlow[i], self.data.xup[i]
            ssigma = scalefactors[i]
            self.xcand[:, i] = stats.truncnorm.rvs(
                (lower - xbest[i]) / ssigma, (upper - xbest[i]) / ssigma,
                loc=xbest[i], scale=ssigma, size=self.numcand)

    def make_points(self, npts, xbest, sigma, subset=None, proj_fun=None,
                    merit=candidate_merit_weighted_distance):
        """Proposes npts new points to evaluate

        :param npts: Number of points to select
        :type npts: int
        :param xbest: Best solution found so far
        :type xbest: numpy.array
        :param sigma: Current sampling radius w.r.t the unit box
        :type sigma: float
        :param subset: Coordinates to perturb, the others are fixed
        :type subset: numpy.array
        :param proj_fun: Routine for projecting infeasible points onto the feasible region
        :type proj_fun: Object
        :param merit: Merit function for selecting candidate points
        :type merit: Object

        :return: Points selected for evaluation, of size npts x dim
        :rtype: numpy.array

        .. todo:: Change the merit function from being hard-coded
        """

        if subset is None:
            subset = np.arange(0, self.data.dim)
        scalefactors = sigma * self.xrange

        # Make sure that the scale factors are correct for
        # the integer variables (at least 1)
        ind = np.intersect1d(self.data.integer, subset)
        if len(ind) > 0:
            scalefactors[ind] = np.maximum(scalefactors[ind], 1.0)

        # Generate candidate points
        self.__generate_cand__(scalefactors, xbest, subset)
        if proj_fun is not None:
            self.xcand = proj_fun(self.xcand)

        dists = scp.distance.cdist(self.xcand, self.proposed_points)
        fhvals = self.fhat.evals(self.xcand)

        self.dmerit = np.amin(np.asmatrix(dists), axis=1)
        self.fhvals = unit_rescale(fhvals)

        xnew = merit(self, npts)
        self.proposed_points = np.vstack((self.proposed_points,
                                          np.asmatrix(xnew)))
        return xnew


@__fix_docs
class CandidateDYCORS(CandidateSRBF):
    """An implementation of the DYCORS method

    The DYCORS method only perturbs a subset of the dimensions when
    perturbing the best solution. The probability for a dimension
    to be perturbed decreases after each evaluation and is capped
    in order to guarantee global convergence.

    :param data: Optimization problem object
    :type data: Object
    :param numcand: Number of candidate points to be used. Default is min([5000, 100*data.dim])
    :type numcand: int
    :param weights: Weights used for the merit function, to balance exploration vs exploitation
    :type weights: list of numpy.array

    :raise ValueError: If number of candidate points is
        incorrect or if the weights aren't a list in [0, 1]

    :ivar data: Optimization problem object
    :ivar fhat: Response surface object
    :ivar xrange: Variable ranges, xup - xlow
    :ivar dtol: Smallest allowed distance between evaluated points 1e-3 * sqrt(dim)
    :ivar weights: Weights used for the merit function
    :ivar proposed_points: List of points proposed to the optimization algorithm
    :ivar dmerit: Minimum distance between the points and the proposed points
    :ivar xcand: Candidate points
    :ivar fhvals: Predicted values by the surrogate model
    :ivar next_weight: Index of the next weight to be used
    :ivar numcand: Number of candidate points
    :ivar budget: Remaining evaluation budget
    :ivar minprob: Smallest allowed perturbation probability
    :ivar n0: Evaluations spent when the initial phase ended
    :ivar probfun: Function that computes the perturbation probability of a given iteration

    .. note:: This object needs to be initialized with the init method. This is done when the
        initial phase has finished.

    .. todo:: Get rid of the proposed_points object and replace it by something that is
        controlled by the strategy.
    """

    def __init__(self, data, numcand=None, weights=None):
        CandidateSRBF.__init__(self, data, numcand=numcand, weights=weights)
        self.minprob = np.min([1.0, 1.0/self.data.dim])
        self.n0 = None

        if data.dim <= 1:
            raise ValueError("You can't use DYCORS on a 1d problem")

        def probfun(numevals, budget):
            if budget < 2:
                return 0
            return min([20.0/data.dim, 1.0]) * (1.0 - (np.log(numevals + 1.0) / np.log(budget)))
        self.probfun = probfun

    def init(self, start_sample, fhat, budget):
        CandidateSRBF.init(self, start_sample, fhat, budget)
        self.n0 = start_sample.shape[0]

    def remove_point(self, x):
        return CandidateSRBF.remove_point(self, x)

    def make_points(self, npts, xbest, sigma, subset=None, proj_fun=None,
                    merit=candidate_merit_weighted_distance):
        return CandidateSRBF.make_points(self, npts, xbest, sigma, subset, proj_fun, merit)

    def __generate_cand__(self, scalefactors, xbest, subset):
        ddsprob = self.probfun(self.proposed_points.shape[0] - self.n0, self.budget - self.n0)
        ddsprob = np.max([self.minprob, ddsprob])

        nlen = len(subset)

        # Fix when nlen is 1
        # Todo: Use SRBF instead
        if nlen == 1:
            ar = np.ones((self.numcand, 1))
        else:
            ar = (np.random.rand(self.numcand, nlen) < ddsprob)
            ind = np.where(np.sum(ar, axis=1) == 0)[0]
            ar[ind, np.random.randint(0, nlen - 1, size=len(ind))] = 1

        self.xcand = np.ones((self.numcand, self.data.dim)) * xbest
        for i in range(nlen):
            lower, upper = self.data.xlow[i], self.data.xup[i]
            ssigma = scalefactors[subset[i]]
            ind = np.where(ar[:, i] == 1)[0]
            self.xcand[ind, subset[i]] = stats.truncnorm.rvs(
                (lower - xbest[subset[i]]) / ssigma, (upper - xbest[subset[i]]) / ssigma,
                loc=xbest[subset[i]], scale=ssigma, size=len(ind))

