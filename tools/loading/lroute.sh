#!/bin/bash
# usage: lroute.sh TAG NAME "STEPS"   route on the staged disc_TAG with RAM pokes (symbols from elf_TAG.elf)
TAG=$1; NAME=$2; STEPS=$3
L=/e/AvP/learning/lane-loading
NM=/e/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe
sym() { $NM $L/elf_$TAG.elf | awk -v n="_$1" '$3==n {print $1}'; }
export GS_DBG=$(sym sat_dbg) GS_RAMB=$(sym RAMB)
echo "dbg=$GS_DBG ramb=$GS_RAMB"
cd $L/ymir
AUTO=${AUTO:-240} python route.py $NAME E:/AvP/learning/lane-loading/disc_$TAG/$TAG.cue "$STEPS" > $NAME.out 2>&1
