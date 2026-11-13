#!/bin/bash
# usage: scene.sh INSTANCE_N NAME CUE ELF DOWNS RIGHTS [MODEL(1|0)]   one stage-select scene on ymir_picN (N empty = ymir_pic); window 1200 vblanks after 300 into the stage
N=$1; NAME=$2; CUE=$3; ELF=$4; DN=${5:-0}; RT=${6:-0}; MODEL=${7:-1}
D=/e/AvP/learning/lane-perf-pic/ymir_pic$N
cd $D
if [ -z "$EXE" ]; then [ -f run/ymir-pic.exe ] && EXE=ymir-pic.exe || EXE=ymir-pic3.exe; fi
export EXE GV=1520 HW_PROF=1 HW_RESET_AT=300 HW_DUMP_AT=1500 DOWNS=$DN RIGHTS=$RT
[ "$MODEL" = 1 ] && export HW_MODEL=1
./runp.sh $NAME $CUE $ELF
