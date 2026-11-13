#!/bin/bash
# usage: wscene.sh INSTANCE_N NAME TAG [MODEL 1|0]  Wolverine fight (GUEST_DEFAULT=1 build TAG): boot, title, ARCADE, character select -> right (WOLVERINE) -> start, stage 1, then the bot for 1200 vblanks with health held; window of 1200 vblanks
N=$1; NAME=$2; TAG=$3; MODEL=${4:-1}
D=/e/AvP/learning/lane-perf-pic/ymir_pic$N; cd $D
L=/e/AvP/learning/lane-perf-pic
if [ -z "$EXE" ]; then [ -f run/ymir-pic.exe ] && EXE=ymir-pic.exe || EXE=ymir-pic3.exe; fi
export EXE HW_PROF=1
[ "$MODEL" = 1 ] && export HW_MODEL=1
export DRV="w:3300 t:start:3 t:a:8 s:12 s:12 p:select t:right:0.8 t:start:5 s:30 p:stage v: x:reset b:1200 x:dump p:end"
./runp.sh $NAME E:/AvP/learning/lane-perf-pic/iso_$TAG.cue $L/elf_$TAG.elf
