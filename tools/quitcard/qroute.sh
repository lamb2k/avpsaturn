#!/bin/bash
# usage: qroute.sh TAG NAME "STEPS"   route on the staged disc_TAG (pad file only); GS_EXE picks the exe (default stock ymir2-sdl3, MIS=1 the strict copy)
TAG=$1; NAME=$2; STEPS=$3
L=/e/AvP/learning/lane-quitcard
NM=/e/AvP/worktrees/saturn-hw/.deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe
sym() { $NM $L/elf_$TAG.elf | awk -v n="_$1" '$3==n {print $1}'; }
export GS_DBG=$(sym sat_dbg) GS_RAMB=$(sym RAMB)
if [ -n "$MIS" ]; then export GS_EXE=$L/ymr/run/ymir2-mis.exe; else export GS_EXE=$L/ymr/run/ymir2-sdl3.exe; fi
cd $L/ymr
AUTO=${AUTO:-600} python route.py $NAME E:/AvP/learning/lane-quitcard/disc_$TAG/$TAG.cue "$STEPS" > $NAME.out 2>&1
