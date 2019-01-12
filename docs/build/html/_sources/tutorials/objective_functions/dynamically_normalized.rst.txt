.. _dynamically_normalized:

Dynamically Normalized Objective Function
=========================================

This is dynamically normalized objective funciton formular for problems with multiple objectives:

	.. math::

		\text{objective function}(X) = \sum\limits_{k \in K} {\frac{{{f_k}(X) - f_k^{\min }(X)}}{{f_k^{\max }(X) - f_k^{\min }(X)}}} 

Where
	 :math:`X` is the parameter vector for the evalution function. 
	 :math:`f_k^{\max }(X)` and :math:`f_k^{\min }(X)` are the maximum and minimum values of :math:`{f_k}(X)` among all the evaluations completed  so far, and hence they  have to be updated dynamically in each iteration during  optimization.


