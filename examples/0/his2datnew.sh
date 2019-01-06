#!/bin/sh
export PATH=$PATH:/home/users/nus/e0022672/delft3d7208/bin/lnx64/util/bin
export PAGER=more
#> Wl.dat
> ZCURU.dat
> ZCURV.dat
> ZCURW.dat
#> Sal.dat
vs <<zzzz 2>his2dat_log  
rele all
use trih-up22.dat def trih-up22.def
let ZCURU = ZCURU (1;1;1) from his-series
let ZCURV = ZCURV (1;1;1) from his-series
let ZCURW = ZCURW (1;1;1) from his-series
write ZCURU to ZCURU.dat
write ZCURV to ZCURV.dat
write ZCURW to ZCURW.dat
zzzz
