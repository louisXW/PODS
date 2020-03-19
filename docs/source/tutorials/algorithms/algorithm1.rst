.. _algorithm1:

PODS
======

PODS (Parallel Optimization with Dynamic coordinate search using Surrogates) is a parallel surrogate-based algorithm for optimization of HEB (High-dimensional, Expensive, and Black-box) problems. PODS is an expansion of serial DYCORS and incorporated the Surrogate-Distance Metric for selecting of multiple evaluation points in each iteration, which is required to implement an algorithm in parallel. 

The synchronous parallelization with multiprocessing python model is implementited in PODS.

.. [1] D. Eriksson, D. Bindel, and C. Shoemaker. 
	Surrogate Optimization Toolbox (pySOT). github.com/dme65/pySOT, 2015 .
	
.. [2] Rommel G Regis and Christine A Shoemaker.
    Combining radial basis function surrogates and dynamic coordinate search in high-dimensional expensive black-box optimization.
    Engineering Optimization, 45(5): 529–555, 2013.

.. [3] Rommel G Regis and Christine A Shoemaker.
    Parallel stochastic global optimization using radial basis functions.
    INFORMS Journal on Computing, 21(3):411–426, 2009.
