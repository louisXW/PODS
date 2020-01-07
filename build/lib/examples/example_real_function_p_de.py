from opdelft.algorithms.differential_evoluation._differentialevolution import *
from opdelft.problems.real_functions import *
import os

def obj_func(paramters):

    data = delft3d_flow(dim=4)
    x, simid, iterid = paramters
    simid = simid
    iterid = iterid
    data.home_dir = '/Users/xiawei/Desktop/opdelft/examples/'
    result = data.objfunction(x, simid, iterid)
    return result

if __name__ == '__main__':
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
    if os.path.exists("./result/pde_result.txt"):
        os.remove("./result/pde_result.txt")

    fp = open("./result/pde_result.txt", "a")
    fp.write("Iteration\tSimID\tObj\tParmaters\n")
    fp.close()

    data = delft3d_flow(dim=4)
    logging.info(data.info)
    data.home_dir = '/Users/xiawei/Desktop/opdelft/examples/'

    bounds = [(0.1, 1.0), (0.1, 1.0), (0.0, 0.005), (0, 0.005)]
    result = differential_evolution(obj_func,data, bounds, parallel=True, maxiter= 7, popsize=4, tol=0, init='latinhypercube')
    print  result.x, result.fun

