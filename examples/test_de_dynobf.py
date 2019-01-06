from _differentialevolution import *

# from scipy.optimize import differential_evolution
import numpy as np
from Objectlong24PDE import *

def ackley(paramters):
    data = delft3d(dim=9)
    # print data.info
    x, simid, genid = paramters
    print ('test', x, 'simulation id is',simid, 'generation id is',genid)
    arg1 = -0.2 * np.sqrt(0.5 * (x[0] ** 2 + x[1] ** 2))
    arg2 = 0.5 * (np.cos(2. * np.pi * x[0]) + np.cos(2. * np.pi * x[1]))

    return -20. * np.exp(arg1) - np.exp(arg2) + 20. + np.e

if __name__ == '__main__':
    bounds = [(-5, 7), (-5, 5)]
    result = differential_evolution(ackley, bounds, parallel=True, maxiter= 8, popsize=6, tol=0)
    print  result.x, result.fun

