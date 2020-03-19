.. _example2_1:

Single Objective Problem
========================

This is an demo to use the DYCORS in parallel for the calibraiton of the Delft3D problem with Single Objective Problem. The experiment setting is the same with example in :ref:`example1`. Users just need to change the parameter nthreads to be the number of parallel processors that users want to use.

.. code-block:: python

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
		nthreads = 4 # set this to the nubmer of parallel processors that users want to use.
		maxeval = 80
		nsamples = nthreads

		# (1) Initilize the Optimization problem
		data = delft3d_1objs(dim=4)
		logging.info(data.info)
		data.home_dir = '/Users/xiawei/Desktop/opdelft/examples/'

		# (2) Experimental design
		# Use a symmetric Latin hypercube with 2d + 1 samples
		exp_des = SymmetricLatinHypercube(dim=data.dim, npts=12)

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



