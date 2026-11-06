#!/bin/sh
# usage: [GOLDEN=name] run.sh N [STOP]
D=$(cd "$(dirname "$0")" && pwd)
G=/mnt/e/AvP/learning/mame/${GOLDEN:-golden_c}/probe.tsv
cd /mnt/e/AvP/learning/lift/run && gcc -DPREEMPT -w -O1 -g -rdynamic -I. "$D/host_kernel.c" c*.o -o lift_runner && STOP_DIV=${2:-6} timeout -s SEGV ${TMO:-120} ./lift_runner /mnt/e/AvP/learning/rt.bin $G $G.io.txt $1 "$D/mask.txt" 2>&1 | tail -${TAIL:-30}
