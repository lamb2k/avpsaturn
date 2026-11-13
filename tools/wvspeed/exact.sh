#!/bin/bash
# usage: exact.sh NAME TAG MODE   (env YN = Ymir copy suffix)  MODE flat | stock | model: tick-indexed exactness run of a SAT_INPUT_SCRIPT_TICK build: game RAM (64 KB) at stage ticks 300 600 1000 1500 2000 3000 3500 -> ymir_wvN/ram_NAME_<tick>.bin
NAME=$1; TAG=$2; MODE=${3:-flat}
L=/e/AvP/learning/lane-wv-speed; D=$L/ymir_wv${YN}; cd $D
export EXE=ymir-wv.exe SCRIPTED=1 GV=${GV:-5200} HW_DUMP_RTICKS=300,600,1000,1500,2000,3000,3500
case $MODE in flat) export HW_FLAT=1;; model) export HW_MODEL=1 HW_PROF=1;; esac
./runp.sh $NAME E:/AvP/learning/lane-wv-speed/iso_$TAG.cue $L/elf_$TAG.elf
