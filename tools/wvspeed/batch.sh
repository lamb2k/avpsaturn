#!/bin/bash
# usage: batch.sh TAG PREFIX GD  runs the scene list on two Ymir copies (wv, wv2)
cd /e/AvP/learning/lane-wv-speed
TAG=$1; P=$2; K=$3
if [ "$K" = w ]; then A="stage:0 stage:1 stage:2 stage:3"; B="stage:4 stage:5 stage:7"; else A="pred:0 pred:1"; B="pred:4"; fi
( for k in $A; do n=${P}_${k/:/}_m; NOAUTO=1 ./wscene.sh $n $TAG $k 1; done ) &
( for k in $B; do n=${P}_${k/:/}_m; YN=2 NOAUTO=1 ./wscene.sh $n $TAG $k 1; done ) &
wait
