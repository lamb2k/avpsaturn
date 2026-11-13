#!/bin/bash
# usage: bscene.sh N NAME CUE ELF RIGHTS  : stage select entry RIGHTS (6 = Boss Rush 0e, 17 = 7-5 Alien Queen) through drv.py, bot 1200 vblanks, stats read at the start and the end (missing tiles, refusals), shots
N=$1; NAME=$2; CUE=$3; ELF=$4; R=$5
D=/e/AvP/learning/lane-perf-pic/ymir_pic$N; cd $D
if [ -z "$EXE" ]; then [ -f run/ymir-pic.exe ] && EXE=ymir-pic.exe || EXE=ymir-pic3.exe; fi
export EXE HW_PROF=1 HW_MODEL=1
RT=""; for i in $(seq 1 $R); do RT="$RT t:right:0.7"; done
export DRV="w:3300 t:start:3 t:down:0.6 t:down:0.6 t:down:0.6 t:a:4 t:start:5$RT t:start:3 r:700 p:stage q:s0 x:reset b:1200 x:dump q:end p:end"
./runp.sh $NAME $CUE $ELF
