.. _convert_his2dat:

================================================================
Convert NEFIS to DAT
================================================================

This his2dat tool is an example for convert the NEFIS format file into DAT file which is easy readable by code.

The his2dat tool was worted in ViewerSelector commends. The ViewerSelector tool is developed by Deltares to inspect and select data from NEFIS files.


An exmaple to convert NEFIS to DAT
----------------------------------

Read and write velcotiy data in U direction from NEFIS file to DAT file.

	1. create a bash file. Add following line into the head of the bash file
	
		.. code-block:: bash
	
			#!/bin/sh
		
	2. add the **vs** util in **Delft3D** into environment path

		.. code-block:: bash
		
			export PATH=$PATH:/home/users/nus/e0022672/delft3d7208/bin/lnx64/util/bin
		
			export PAGER=more
	
	3. create an empty DAT file to sotry the data

		.. code-block:: bash
		
			> ZCURU.datIN 

	4. use **vs** tool to read the NEFIS file and write velcotiy data to DAT file.
	
		.. code-block:: bash
		
			vs  
			
			rele all
			
			use trih-f34.dat def trih-f34.def
			
			let ZCURU = ZCURU (1;1;1) from his-series

			write ZCURU to ZCURU.dat


A detailed description about the NEFIS ViewerSelector refer to the programmer manual https://content.oss.deltares.nl/delft3d/manuals/NEFIS_Viewer_Selector_Programmers_Manual.pdf  

