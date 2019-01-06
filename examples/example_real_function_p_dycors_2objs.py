"""
.. module:: test_simple
  :synopsis: Test Simple
.. moduleauthor:: XiaWei
"""
from opdelft.algorithms.pySOT.experimental_design import SymmetricLatinHypercube
from opdelft.algorithms.pySOT.sot_sync_strategies import SyncStrategyNoConstraintsMutipro
from opdelft.algorithms.pySOT.rbf import RBFInterpolant, CubicKernel, LinearTail
from opdelft.algorithms.pySOT.adaptive_sampling import CandidateDYCORS

from opdelft.algorithms.poap.controller import MultiproController
import numpy as np
import os
import logging
from opdelft.problems.real_functions import *

def obj_func(paramters):
    """
    The function for objective function evaluation.
    :param paramters: A tuple (x, simid, iterid)
        x: the dim dimensional parameter vector
        simid: the index of simulation ID in each iteration
        iterid: the index of iteration ID
        simid and iterid is used control a batch of simulations running simultaneously in each iteration.
    :return: the objective function value [subobj1, subobj2] (a list of multiple sub objectives)
    """
    data = delft3d_2objs(dim=4) #Initializaiton for the problem class
    x, simid, iterid = paramters
    simiter = iterid
    simid = simid
    result = data.objfunction(x, simid, simiter)
    return result

def main():
    # -----------Initilizae logging-----------------#
    if not os.path.exists("./logfiles"):
        os.makedirs("logfiles")
    if os.path.exists("./logfiles/test_simple.log"):
        os.remove("./logfiles/test_simple.log")
    logging.basicConfig(filename="./logfiles/test_simple.log",
                        level=logging.INFO)

    # -----------Initilizae result saving-----------------#
    if not os.path.exists("./result"):
        os.makedirs("result")

        """ histroy_data folder is needed when you need to 
        save the simultion output of each evaluation"""
    if os.path.exists("./result/history_data"):
        os.rmdir("./result/history_data")
    if not os.path.exists("./result/history_data"):
        os.makedirs("./result/history_data")

        """ pysot_tesult.txt file is for saving the objective 
        function value and parameter vector of each evaluations"""
    if os.path.exists("./result/pysot_result.txt"):
        os.remove("./result/pysot_result.txt")

    fp = open("./result/pysot_result.txt", "a")
    fp.write("Iteration\tSimID\tObj\tParmaters\n")
    fp.close()

    # -----------set the threads and budget-----------------#
    nthreads = 10
    maxeval = 80
    nsamples = nthreads

    # (1) Initilize the Optimization problem
    data = delft3d_2objs(dim=4)
    logging.info(data.info)
    data.home_dir = './'

    # (2) Experimental design
    # Use a symmetric Latin hypercube with 2d + 1 samples
    exp_des = SymmetricLatinHypercube(dim=data.dim, npts=20)

    # (3) Surrogate model
    # Use a cubic RBF interpolant with a linear tail
    surrogate = RBFInterpolant(kernel=CubicKernel, tail=LinearTail, maxp=maxeval)

    # (4) Adaptive sampling
    adapt_samp = CandidateDYCORS(data=data, numcand=1000 * data.dim)

    # (5) Use the multiprocessing-based sychronous strategy without non-bound constraints
    strategy = SyncStrategyNoConstraintsMutipro(obj_func,
                                                worker_id=0, data=data, maxeval=maxeval, nsamples=nsamples,
                                                exp_design=exp_des, response_surface=surrogate,
                                                sampling_method=adapt_samp)

    # (6) Use the multiprocessing-based sychronous controller
    controller = MultiproController()
    controller.strategy = strategy

    # Run the optimization strategy
    result = controller.run()
    print "result", result



if __name__ == "__main__":
   main()



