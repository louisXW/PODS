# Import the necessary modules
# from pySOT import *
from pySOT import Ackley, SyncStrategyNoConstraints,SyncStrategyNoConstraintsMutipro, \
    SymmetricLatinHypercube, RBFInterpolant, CubicKernel, \
    LinearTail, CandidateDYCORS
from poap.controller import SerialController, ThreadController, BasicWorkerThread, ControllerMultipro
import numpy as np

# Decide how many evaluations we are allowed to use
def main():
    maxeval = 96

    # (1) Optimization problem
    # Use the 10-dimensional Ackley function
    data = Ackley(dim=9)
    print(data.info)

    # (2) Experimental design
    # Use a symmetric Latin hypercube with 2d + 1 samples
    exp_des = SymmetricLatinHypercube(dim=data.dim, npts=24)

    # (3) Surrogate model
    # Use a cubic RBF interpolant with a linear tail
    surrogate = RBFInterpolant(kernel=CubicKernel, tail=LinearTail, maxp=maxeval)
    # (4) Adaptive sampling
    # Use DYCORS with 100d candidate points
    adapt_samp = CandidateDYCORS(data=data, numcand=100*data.dim)
    # Use the threaded controller
    # controller = ThreadController()
    controller = ControllerMultipro()
    # (5) Use the sychronous strategy without non-bound constraints
    # Use 4 threads and allow for 4 simultaneous evaluations
    nthreads = 24

    strategy = SyncStrategyNoConstraintsMutipro(
            worker_id=0, data=data, maxeval=maxeval, nsamples=nthreads,
            exp_design=exp_des, response_surface=surrogate,
            sampling_method=adapt_samp)

    controller.strategy = strategy
    # Launch the threads and give them access to the objective function
    # for _ in range(nthreads):
    #     worker = BasicWorkerThread(controller, data.objfunction)
    #     controller.launch_worker(worker)
    # Run the optimization strategy
    result = controller.run()
    # Print the final result
    print result
    # print('Best value found: {0}'.format(result.value))
    # print('Best solution found: {0}'.format(
    #     np.array_str(result.params[0], max_line_width=np.inf,
    #                 precision=5, suppress_small=True)))
if __name__ == "__main__":
    main()