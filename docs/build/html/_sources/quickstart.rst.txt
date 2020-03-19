Quick Start
===========

Once the PODS module and the dependencies are installed. You can quick start with the examples set in the PODS package.

There are few simple examples you can start with to get familar with how to work with a real problems with advanced optimizaiton algorithms e.g., pySOT.

To run the examples inside PODS.

1. Navigate to the examples folder

   .. code-block:: bash
   
		cd PODS/examples
		
2. Open any of the examles_*.py file and modified the envrionemtnal variable accordingly.

	   .. code-block:: bash
	   
			data.home_dir = 'THE_DIR_WHERE_YOUR_SAVE_PODS/PODS/examples/'  

3. Specify the path of delft3d /bin folder for the executable file (*.sh) inside the model.

	3.1 his2dat.sh 
	
	   .. code-block:: bash
   
			export PATH=$PATH:YOUR_DELFT3D_BIN_DIR/lnx64/util/bin
	
	3.2 run_flow2d3d.sh

	   .. code-block:: bash
   
			export ARCH=lnx64
			export D3D_HOME=YOUR_DELFT3D_BIN_DIR
			exedir=$D3D_HOME/$ARCH/flow2d3d/bin	


	
	
	

		


