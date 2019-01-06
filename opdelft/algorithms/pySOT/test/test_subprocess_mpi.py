"""
.. module:: test_subprocess_mpi
  :synopsis: Test an external objective function
.. moduleauthor:: David Eriksson <dme65@cornell.edu>
"""

from pySOT import Sphere,SyncStrategyNoConstraints, \
    SymmetricLatinHypercube, CandidateDYCORS, \
    RBFInterpolant, CubicKernel, LinearTail
from poap.mpiserve import MPIController, MPIProcessWorker
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
# Try to import mpi4py
try:
    from mpi4py import MPI
except Exception as err:
    print("ERROR: You need mpi4py to use the POAP MPI controller")
    exit()


def array2str(x):
    return ",".join(np.char.mod('%f', x))


class CppSim(MPIProcessWorker):
    def eval(self, record_id, params, extra_args=None):
        try:
            self.process = Popen(['./sphere_ext', array2str(params[0])], stdout=PIPE, bufsize=1, universal_newlines=True)
            val = self.process.communicate()[0]
            self.finish_success(record_id, float(val))
        except ValueError:
            logging.info("WARNING: Incorrect output or crashed evaluation")
            self.finish_cancelled(record_id)


def main_worker():
    logging.basicConfig(filename="./logfiles/test_subprocess_mpi.log",
                        level=logging.INFO)
    CppSim().run()


def main_master(nworkers):
    if not os.path.exists("./logfiles"):
        os.makedirs("logfiles")
    if os.path.exists("./logfiles/test_subprocess_mpi.log"):
        os.remove("./logfiles/test_subprocess_mpi.log")
    logging.basicConfig(filename="./logfiles/test_subprocess_mpi.log",
                        level=logging.INFO)

    print("\nTesting the POAP MPI controller with {0} workers".format(nworkers))
    print("Maximum number of evaluations: 200")
    print("Search strategy: Candidate DYCORS")
    print("Experimental design: Symmetric Latin Hypercube")
    print("Surrogate: Cubic RBF")

    assert os.path.isfile("./sphere_ext"), "You need to build sphere_ext"

    maxeval = 200

    data = Sphere(dim=10)
    print(data.info)

    # Create a strategy and a controller
    strategy = \
        SyncStrategyNoConstraints(
            worker_id=0, data=data,
            maxeval=maxeval, nsamples=nworkers,
            exp_design=SymmetricLatinHypercube(dim=data.dim, npts=2*(data.dim+1)),
            sampling_method=CandidateDYCORS(data=data, numcand=100*data.dim),
            response_surface=RBFInterpolant(kernel=CubicKernel, tail=LinearTail,
                                            maxp=maxeval))

    controller = MPIController(strategy)

    # Run the optimization strategy
    result = controller.run()
    print('Best value found: {0}'.format(result.value))
    print('Best solution found: {0}\n'.format(
        np.array_str(result.params[0], max_line_width=np.inf,
                     precision=5, suppress_small=True)))

if __name__ == '__main__':
    # Extract the rank
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    nprocs = comm.Get_size()

    if rank == 0:
        main_master(nprocs)
    else:
        main_worker()
