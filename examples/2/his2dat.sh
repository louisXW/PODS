#!/bin/sh
    #
    # This script is an example for convert the NEFIS format file into DAT file which is easy readable by code.
	# The code here is ViewerSelector commends. The ViewerSelector tool is developed by Deltares to inspect and select data from NEFIS files.
	# A detailed description about the NEFIS ViewerSelector refer to the programmer manual https://content.oss.deltares.nl/delft3d/manuals/NEFIS_Viewer_Selector_Programmers_Manual.pdf
    # Adapt and use it for your own purpose
    #
    # xiawei@u.nus.edu
    # 6 Jan 2019
    # 
    #
    #


    #
    # Set the environemnt path of the ViewerSelector (vs) tool here.
    # 
export PATH=$PATH:/home/users/nus/e0022672/delft3d7208/bin/lnx64/util/bin
export PAGER=more
> ZCURU.dat
> ZCURV.dat
> ZCURW.dat
vs <<zzzz 2>his2dat_log  
rele all
use trih-f34.dat def trih-f34.def
let ZCURU = ZCURU (1;1;1) from his-series
let ZCURV = ZCURV (1;1;1) from his-series
let ZCURW = ZCURW (1;1;1) from his-series
write ZCURU to ZCURU.dat
write ZCURV to ZCURV.dat
write ZCURW to ZCURW.dat
zzzz
