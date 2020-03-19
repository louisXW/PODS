#!/bin/bash
    #
    # This script is an example for running Delft3D-FLOW
    # Adapt and use it for your own purpose
    #
    # adri.mourits@deltares.nl
    # 27 Dec 2010
    # 
    #
    # This script starts a single-domain Delft3D-FLOW computation on Linux
    #


    #
    # Set the config file here
    # 
argfile=config_flow2d3d.xml





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
#./clean.sh
#clean the result files in the previous run
rm -rf com-up22*
rm -rf tri-rst.up22.*
rm -rf trih-up22*
rm -rf trim-up22*
rm -rf Tem.dat
rm -rf Tem.def
rm -rf ZCURU.dat
rm -rf ZCURV.dat
rm -rf ZCURW.dat
rm -rf tri-diag*
rm -rf TMP_*

    # Run
$exedir/d_hydro.exe $argfile
