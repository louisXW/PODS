.. _howtoinstall:

Install PODS
===============

Preparing your system to use PODS
------------------------------------

1. **python** & **pySOT**

Before starting you will need to Python installed. Recommend python 2.7 since PODS was developed and tested based on this verison.
You will need to have pySOT (0.1.36) installed. Other python module like (scipy, numpy， pyDOE) needed will be installed automatically once the pySOT is installed.

To install the pySOT (0.1.36) package with conda run one of the following:

	.. code-block:: bash

		conda install -c conda-forge pysot

		conda install -c conda-forge/label/gcc7 pysot


pySOT is a open source toolbox is for optimization of computationally expensive black-box objective functions. 
more information about pySOT refer to: https://pysot.readthedocs.io/en/latest/index.html


2. **Delft3D**

To work with Delft3D problem you may need to have Delft3D installed.

Delft3D is an open source software which simulates two-dimensional (in either the horizontal or a vertical plane) and three-dimensional flow, sediment transport and morphology, waves, water quality and ecology and is capable of handling the interactions between these processes.

The Delft3D installation manual on both windows and linux links to https://content.oss.deltares.nl/delft3d/manuals/Delft3D-Installation_Manual.pdf

You may also want to compile the open source on your platform. The instruction links to https://oss.deltares.nl/c/document_library/get_file?uuid=e3bf2d05-f59f-4d4a-8c13-97bcbaa84060&groupId=21119


Install **PODS** on your system
----------------------------------
There are two options to install PODS

1. install from repostitory with setup.py

|  1.1. Clone the repository:

	.. code-block:: bash
	
		git clone https://github.com/louisXW/PODS.git

|  1.2. Navigate to the folder with setup.py file:
	
	.. code-block:: bash
	
		cd PODS
	
|  1.3. Install PODS with setup.py if you have admister root

	.. code-block:: bash
	
		python setup.py install

|  1.4. Most cases you might work on a remote workstation without root. Install PODS with setup.py locally

	.. code-block:: bash
	
		python setup.py install --user
	
2. install with pip (option avaiable onece the repository is public)

	.. code-block:: bash
	
		pip install PODS	
	
	

