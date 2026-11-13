#!/bin/bash
# usage: exact.sh INSTANCE_N NAME CUE ELF MODE   MODE flat | stock | model   tick-indexed exactness run of a SAT_INPUT_SCRIPT_TICK build: game RAM (64 KB) at stage ticks 300 600 1000 1500 2000 3000 3500 -> ymir_picN/ram_NAME_<tick>.bin
N=$1; NAME=$2; CUE=$3; ELF=$4; MODE=${5:-flat}
D=/e/AvP/learning/lane-perf-pic/ymir_pic$N; cd $D
[ -f run/ymir-pic.exe ] && export EXE=ymir-pic.exe || export EXE=ymir-pic3.exe
export SCRIPTED=1 GV=${GV:-5200} HW_DUMP_RTICKS=300,600,1000,1500,2000,3000,3500
case $MODE in flat) export HW_FLAT=1;; model) export HW_MODEL=1 HW_PROF=1;; esac
./runp.sh $NAME $CUE $ELF
