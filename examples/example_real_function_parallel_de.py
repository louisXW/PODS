from algorithms.differential_evoluation._differentialevolution import *
from ObjectlongbothPDE import *

def upr_flow(paramters):

    data = delft3d(dim=9)
    x, simid, genid = paramters
    simiter = genid
    simid = simid
    print "this is %d iteration %d simulation" % (simiter, simid)
    result = data.objfunction(x, simid, simiter)
    print result
    return result

if __name__ == '__main__':
    # Maximize the fitness function in parallel
    if not os.path.exists("./logfiles"):
        os.makedirs("logfiles")
    if os.path.exists("./logfiles/test_simple.log"):
        os.remove("./logfiles/test_simple.log")
    logging.basicConfig(filename="./logfiles/test_simple.log",
                        level=logging.INFO)
    if os.path.exists("./history_data"):
        os.system("rm -rf history_data")
    if not os.path.exists("./history_data"):
        os.makedirs("history_data")
    fp = open("/home/users/nus/e0022672/scratch/upr_exp/pde/pde_init/cali_both/exp1/pysot_result.txt", "a")
    fp.write("Iteration\tSimID\tObj\tParmaters\n")
    fp.close()
    bounds = [(0.1, 2.0), (0.1, 1.0), (0.1, 1.0), (0, 0.005), (0, 0.005), (0, 0.05), (0.001, 0.002), (0.001, 0.002), (0.02, 0.03)]
    result = differential_evolution(upr_flow, bounds, parallel=True, maxiter= 7, popsize=24, tol=0, init='given')
    print  result.x, result.fun

