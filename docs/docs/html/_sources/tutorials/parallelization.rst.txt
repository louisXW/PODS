.. _parallelization:

================================================================
Parallelization
================================================================

The parallel implementaion for both DYCORS and Differential Evolution use a synchronous parallel framework.

This parallelization strategy of the algorithm allows simultaneous function evaluations on multiple processors (cores) in batch mode and can greatly speedup the calibration of computationally expensive models by reducing the calibration time and making the calibration of some extremely expensive models possible.

Since real problems (different from math test functions) are usually model suit with a batch of simualtaiton files, it's usually technique difficult to implementaion parallelization with real problems. This is escipically true when the problems involues large number of files and with intensive postprcessing.

In opdelft two variable **iterid** and **simid** are frequently use for the parallelization control.
 
	**iterid** indicates the index of iterations.
	
	**simid** indicates the index of simulation of a batch of simultaneous simulations in each iteration. 

**iterid** and **simid** are used both in the main string of the algrithom and in the objective funciton evaluations to modify simualtion files, launch simuation executation, connect the each subprocess with main string of algorithm

	
The parallel controller used in opdelft is the multiprocesisng.pool() function in python.

   .. code-block:: bash
   
    #Initialization the pool class.
		
	pool = multiprocessing.Pool(nprocessors)
		
	#zip the a list of parameter vectors with iteration and simulation ID.
		
    paramters = zip(params, simid, iterid)
		
	#Use pool.map to run a batch of evaluations. self.obj_func is the evaltions function take paramters as input.
		
    objfuns = pool.map(self.obj_func, paramters)