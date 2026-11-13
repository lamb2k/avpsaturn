#!/bin/bash
# usage: grab.sh TAG   copy a finished build's iso/map/elf/align out of wd_TAG (the pbuild wrapper can be lost; python finished)
T=$1; W=/e/AvP/learning/lane-wv-speed/wd_$T; L=/e/AvP/learning/lane-wv-speed
cp $W/sat.iso $L/iso_$T.iso; cp $W/sat.map $L/map_$T.txt; cp $W/sat.elf $L/elf_$T.elf; cp $W/align_gate.txt $L/align_$T.txt 2>/dev/null; $L/mkcue1.sh $T; echo "rc 0 (grabbed)" >> $L/b_$T.log; echo grabbed $T
