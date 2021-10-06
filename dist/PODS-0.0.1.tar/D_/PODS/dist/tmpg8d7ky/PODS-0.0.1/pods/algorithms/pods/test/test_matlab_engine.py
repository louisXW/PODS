"""
.. module:: test_matlab_engine
  :synopsis: Test with MATLAB objective function
.. moduleauthor:: David Eriksson <dme65@cornell.edu>
"""

from pySOT import Ackley, SyncStrategyNoConstraints, LatinHypercube, \
    RBFInterpolant, CubicKernel, LinearTail, CandidateDYCORS
from poap.controller import ThreadController, ProcessWorkerThread
import numpy as np
import os.path
import logging

# Try to import the matlab_wrapper module
try:
    import matlab_wrapper
except Exception as err:
    print("\nERROR: Failed to import the matlab_wrapper module. "
          "Install using: pip install matlab_wrapper\n")
    exit()


class MatlabWorker(ProcessWorkerThread):
    def handle_eval(self, record):
        try:
            self.matlab.put('x', record.params[0])
            self.matlab.eval('matlab_ackley')
            val = self.matlab.get('val')
            if np.isnan(val):
                raise ValueError()
            self.finish_success(record, val)
        except:
            logging.info("WARNING: Incorrect output or crashed evaluation")
            self.finish_cancelled(record)


def main():
    if not os.path.exists("./logfiles"):
        os.makedirs("logfiles")
    if os.path.exists("./logfiles/test_matlab_engine.log"):
        os.remove("./logfiles/test_matlab_engine.log")
    logging.basicConfig(filename="./logfiles/test_matlab_engine.log",
                        level=logging.INFO)

    print("\nNumber of threads: 4")
    print("Maximum number of evaluations: 500")
    print("Sampling method: CandidateDYCORS")
    print("Experimental design: Latin Hypercube")
    print("Surrogate: Cubic RBF")

    nthreads = 4
    maxeval = 500

    data = Ackley(dim=10)
    print(data.info)

    # Use the serial controller (uses only one thread)
    controller = ThreadController()
    controller.strategy = \
        SyncStrategyNoConstraints(
            worker_id=0, data=data,
            maxeval=maxeval, nsamples=nthreads,
            exp_design=LatinHypercube(dim=data.dim, npts=2*(data.dim+1)),
            response_surface=RBFInterpolant(kernel=CubicKernel, tail=LinearTail,
                                            maxp=maxeval),
            sampling_method=CandidateDYCORS(data=data, numcand=100*data.dim))

    print("\nNOTE: You may need to specify the matlab_root keyword in "
          "order \n      to start a MATLAB  session using the matlab_wrapper "
          "module\n")

    # We need to tell MATLAB where the script is
    mfile_location = os.getcwd()

    # Launch the threads
    for _ in range(nthreads):
        worker = MatlabWorker(controller)
        try:
            worker.matlab = matlab_wrapper.MatlabSession(options='-nojvm')
        except Exception as err:
            print("\nERROR: Failed to initialize a MATLAB session.\n")
            exit()

        worker.matlab.workspace.addpath(mfile_location)
        controller.launch_worker(worker)

    # Run the optimization strategy
    result = controller.run()

    # Print the final result
    print('Best value found: {0}'.format(result.value))
    print('Best solution found: {0}\n'.format(
        np.array_str(result.params[0], max_line_width=np.inf,
                     precision=5, suppress_small=True)))


if __name__ == '__main__':
    main()
