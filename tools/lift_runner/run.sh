#!/bin/sh
# usage: run.sh N [STOP]
G=/mnt/e/AvP/learning/mame/golden_c/probe.tsv
cd /mnt/e/AvP/learning/lift/run && gcc -DPREEMPT -w -O1 -g -rdynamic -I. /mnt/e/AvP/worktrees/decomp-main/tools/lift_runner/host_kernel.c c*.o -o lift_runner && STOP_DIV=${2:-6} timeout -s SEGV 60 ./lift_runner /mnt/e/AvP/learning/rt.bin $G $G.io.txt $1 /mnt/e/AvP/worktrees/decomp-main/tools/lift_runner/mask.txt 2>&1 | tail -30
