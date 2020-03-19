.. _example3:

Calibrate Delft3D-FLOW Problem with Differential Evolution
========================


This is an demo to use the Differential Evolution in parallel for the calibraiton of the Delft3D problem with Single Objective Problem. 

1. Import the differential evolution module and the optimization problem module.

.. code-block:: python

	from pods.algorithms.differential_evoluation._differentialevolution import *
	from pods.problems.real_functions import *
	import os


2. Define the objective evaluation function obj_func(). This function will be called by the optimizaiton algorithm (master) to do evaluation. Users need to set up the home_dir which will be used to nevigate the dir for simualtion evaluations

.. code-block:: python

	def obj_func(paramters):

		data = delft3d_flow(dim=4)
		x, simid, iterid = paramters
		simid = simid
		iterid = iterid
		data.home_dir = '/Users/xiawei/Desktop/pods/examples/'
		result = data.objfunction(x, simid, iterid)
		return result
		
3. Defin the main() function. Set up the configuration of the algorithms.

.. code-block:: python

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
		data.home_dir = '/Users/xiawei/Desktop/pods/examples/'

		bounds = [(0.1, 1.0), (0.1, 1.0), (0.0, 0.005), (0, 0.005)]
		result = differential_evolution(obj_func,data, bounds, parallel=True, maxiter= 7, popsize=4, tol=0, init='latinhypercube')
		print  result.x, result.fun


	


