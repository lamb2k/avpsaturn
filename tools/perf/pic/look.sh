#!/bin/bash
# usage: look.sh INSTANCE_N NAME CUE ELF  -> look_run.py on ymir_picN (stock timing)
N=$1; NAME=$2; CUE=$3; ELF=$4
D=/e/AvP/learning/lane-perf-pic/ymir_pic$N; cd $D
sed "s#lane-perf-pic/ymir_pic'#lane-perf-pic/ymir_pic$N'#" ../ymir_pic/look_run.py > look_run.py
[ -f run/ymir-pic.exe ] && export EXE=ymir-pic.exe || export EXE=ymir-pic3.exe
NM=/e/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe
sym() { $NM $ELF | awk -v n="_$1" '$3==n {print $1}'; }
dbg=$(sym sat_dbg); ramb=$(sym RAMB); st=$(sym sat_gfx_stats)
export GS_EXE=E:/AvP/learning/lane-perf-pic/ymir_pic$N/run/$EXE GS_CUE=$CUE
export GS_OFF=$(printf "%d" $(( 0x$dbg - 0x060DEA64 ))) GS_OFF2=$(printf "%d" $(( 0x$st - 0x060FEF84 ))) GS_OFFR=$(printf "%d" $(( 0x$ramb - 0x060DEC14 ))) HW_RAMB=$ramb HW_DBG=$dbg
mkdir -p runs; python look_run.py $NAME > runs/$NAME.out 2>&1
