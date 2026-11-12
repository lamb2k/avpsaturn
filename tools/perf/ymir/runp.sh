#!/bin/bash
# usage: runp.sh NAME CUE ELF   -> runs hw_run.py (profiling / model Ymir) with symbol addresses taken from the build's ELF; env HW_* GV DOWNS RIGHTS pass through
NAME=$1; CUE=$2; ELF=$3
NM=/e/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe
sym() { $NM $ELF | awk -v n="_$1" '$3==n {print $1}'; }
cd /e/AvP/learning/lane-perf-hw/ymir_hw
mkdir -p runs
dbg=$(sym sat_dbg); ramb=$(sym RAMB); st=$(sym sat_gfx_stats); gd=$(sym game_done)
export GS_EXE=E:/AvP/learning/lane-perf-hw/ymir_hw/run/${EXE:-ymir-hwp4.exe} GS_CUE=$CUE
export GS_OFF=$(printf "%d" $(( 0x$dbg - 0x060DEA64 ))) GS_OFF2=$(printf "%d" $(( 0x$st - 0x060FEF84 ))) GS_OFFR=$(printf "%d" $(( 0x$ramb - 0x060DEC14 ))) HW_RAMB=$ramb HW_DBG=$dbg HW_TAG=$NAME
[ -n "$gd" ] && export HW_GD=$gd
echo "addr dbg=$dbg ramb=$ramb stats=$st gd=$gd off=$GS_OFF off2=$GS_OFF2" > runs/$NAME.addr
if [ -n "$SCRIPTED" ]; then python exact_run.py $NAME ${GV:-6000} > runs/$NAME.out 2>&1; else python hw_run.py $NAME ${GV:-1520} ${DOWNS:-0} ${RIGHTS:-0} > runs/$NAME.out 2>&1; fi
