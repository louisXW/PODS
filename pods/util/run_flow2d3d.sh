#!/bin/bash
    #
    # This script is an example for running Delft3D-FLOW modified by Xia Wei for the demo purpose.
    # Adapt and use it for your own purpose
    #
    # adri.mourits@deltares.nl
    # 27 Dec 2010
	# xiawei@u.nus.edu
	# 06 Jan 2019
    # 
    #
    # This script starts a single-domain Delft3D-FLOW computation on Linux
    #


    #
    # Set the config file here
    # 
argfile=config_d_hydro.xml

    #
    # Set the directory containing delftflow.exe here
    #
export ARCH=lnx64
export D3D_HOME=/home/users/nus/e0022672/delft3d7208/bin
exedir=$D3D_HOME/$ARCH/flow2d3d/bin
 
    #
    # No adaptions needed below
    #

    # Set some (environment) parameters
export LD_LIBRARY_PATH=$exedir:$LD_LIBRARY_PATH 

rm -rf com-f34*
rm -rf tri-rst.f34.*
rm -rf trih-f34*
rm -rf trim-f34*
rm -rf ZCURU.dat
rm -rf ZCURV.dat
rm -rf ZCURW.dat
rm -rf tri-diag*
rm -rf TMP_*

    # Run
$exedir/d_hydro.exe $argfile
