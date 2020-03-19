"""

This is an example running parallel differential evolution with test problems

"""

from pods.algorithms.differential_evoluation._differentialevolution import *
from pods.problems.test_functions import *
import os.path
import logging
import os

def obj_func(paramters):

    data = Ackley(dim=10)
    x, simid, genid = paramters
    simiter = genid
    simid = simid
    result = data.objfunction(x)
    return result

if __name__ == '__main__':
    #-----------Initilizae logging-----------------#
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

    # (1) Optimization problem
    data = Ackley(dim=10)
    print(data.info)
    data.workdir = './'
    logging.info(data.info)
    bounds = [(-15, 20), (-15, 20), (-15, 20), (-15, 20), (-15, 20), (-15, 20), (-15, 20), (-15, 20), (-15, 20), (-15, 20)]
    result = differential_evolution(obj_func, bounds, parallel=True, maxiter= 7, popsize=4, tol=0, init='latinhypercube')
    print  result.x, result.fun

