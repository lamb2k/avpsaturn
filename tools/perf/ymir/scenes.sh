#!/bin/bash
# usage: scenes.sh PREFIX CUE ELF "downs list"
cd /e/AvP/learning/lane-perf-hw/ymir_hw
P=$1; CUE=$2; ELF=$3
for d in $4; do
  DOWNS=$d GV=1300 HW_PROF=1 HW_RESET_AT=200 HW_DUMP_AT=1280 ./runp.sh ${P}_d$d $CUE $ELF
done
