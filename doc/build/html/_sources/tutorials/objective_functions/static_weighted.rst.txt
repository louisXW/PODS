.. _static_weighted:

Static Weighted Objective Function
==================================

To sovle problems with multiple objectives with singale objective optimizaiton methods the traditional way is add multiple objectives into a singale objective funcction with a definted weight.

	.. math::
    
		\text{objective function}(X) := \sum\limits_{k \in K}{w_k * f_k(X)}

where 	  
	  :math:`X` is the parameter vector for the evalution function.
	  :math:`w_k` is the weight given for the :math:`k^{th}` objective funciton :math:`f_k(X)`.
	  :math:`K` is a set of objectives.

