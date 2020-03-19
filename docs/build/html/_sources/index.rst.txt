.. PODS documentation master file, created by
   sphinx-quickstart on Sun Jan  6 20:29:21 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PODS!
===================================
PODS is a python-based optimization toolbox for computing expensive problems (e.g., environmental model calibation). PODS package including 1) a standalone PODS algorithm code; 2) examples using PODS with test function; 3) examples using PODS with expensive simulaiton problems (e.g., Deflt3D-FLOW). 

Environmental problems are usually complicate since there are usually massive model input and output files. In addition, these models are usually computationally expensive to run. These features make the implementation of advanced algorithm on these problems difficult.  The PODS toolbox provides a framework coupling the advanced optimisation methods (e.g., surrogate optimisation algorithms, evolution algorithms) with real problems. The problems used here for demo in the example is Delft3D models. With minor modification PODS can be used for the optimisation of other real problems. 

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   install
   quickstart
   tutorials/index
   examples/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
