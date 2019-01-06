"""
.. module:: test_subprocess_partial_info
  :synopsis: Test an external objective function with partial info
.. moduleauthor:: David Eriksson <dme65@cornell.edu>
"""

from pySOT import SyncStrategyNoConstraints, SymmetricLatinHypercube, \
    CandidateDYCORS, RBFInterpolant, CubicKernel, LinearTail
from poap.controller import ThreadController, ProcessWorkerThread
import numpy as np
import sys
import os.path
import logging
if sys.version_info < (3, 0):
    # Try to import from subprocess32
    try:
        from subprocess32 import Popen, PIPE
    except Exception as err:
        print("ERROR: You need the subprocess32 module for Python 2.7. \n"
              "Install using: pip install subprocess32")
        exit()
else:
    from subprocess import Popen, PIPE


def array2str(x):
    return ",".join(np.char.mod('%f', x))


class SumfunExt:
    def __init__(self, dim=10):
        self.xlow = -5 * np.ones(dim)
        self.xup = 5 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Sumfun function \n" +\
                             "Global optimum: f(0,0,...,0) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)


class CppSim(ProcessWorkerThread):

    def handle_eval(self, record):
        val = np.nan
        # Continuously check for new outputs from the subprocess
        self.process = Popen(['./sumfun_ext', array2str(record.params[0])], stdout=PIPE, bufsize=1, universal_newlines=True)

        for line in self.process.stdout:
            try:
                val = float(line.strip())  # Try to parse output
                if val > 350:  # Terminate if too large
                    self.process.terminate()
                    self.finish_success(record, 350)
                    return
            except ValueError:  # If the output is nonsense we terminate
                logging.warning("Incorrect output")
                self.process.terminate()
                self.finish_cancelled(record)
                return
        self.process.wait()

        rc = self.process.poll()  # Check the return code
        if rc < 0 or np.isnan(val):
            logging.info("WARNING: Incorrect output or crashed evaluation")
            self.finish_cancelled(record)
        else:
            self.finish_success(record, val)


def main():
    if not os.path.exists("./logfiles"):
        os.makedirs("logfiles")
    if os.path.exists("./logfiles/test_subprocess_partial_info.log"):
        os.remove("./logfiles/test_subprocess_partial_info.log")
    logging.basicConfig(filename="./logfiles/test_subprocess_partial_info.log",
                        level=logging.INFO)

    print("\nNumber of threads: 4")
    print("Maximum number of evaluations: 200")
    print("Sampling method: Candidate DYCORS")
    print("Experimental design: Symmetric Latin Hypercube")
    print("Surrogate: Cubic RBF")

    assert os.path.isfile("./sumfun_ext"), "You need to build sumfun_ext"

    nthreads = 4
    maxeval = 200
    nsamples = nthreads

    data = SumfunExt(dim=10)
    print(data.info)

    # Create a strategy and a controller
    controller = ThreadController()
    controller.strategy = \
        SyncStrategyNoConstraints(
            worker_id=0, data=data,
            maxeval=maxeval, nsamples=nsamples,
            exp_design=SymmetricLatinHypercube(dim=data.dim, npts=2*(data.dim+1)),
            sampling_method=CandidateDYCORS(data=data, numcand=100*data.dim),
            response_surface=RBFInterpolant(kernel=CubicKernel, tail=LinearTail,
                                            maxp=maxeval))

    # Launch the threads and give them access to the objective function
    for _ in range(nthreads):
        controller.launch_worker(CppSim(controller))

    # Run the optimization strategy
    result = controller.run()

    print('Best value found: {0}'.format(result.value))
    print('Best solution found: {0}\n'.format(
        np.array_str(result.params[0], max_line_width=np.inf,
                     precision=5, suppress_small=True)))

if __name__ == '__main__':
    main()
