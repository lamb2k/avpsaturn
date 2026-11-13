#!/bin/bash
# usage: routeB.sh TAG SUFFIX : versus, boss rush, ending routes on a staged disc
TAG=$1; S=$2
cd /e/AvP/learning/lane-loading/ymir
AUTO=1800 QMAX=3500 ./lroute.sh $TAG ${S}_vs "b: r:420 t:down:8:30 t:start:8:300 t:start:8:300 t:start:8:300 t:a:8:300 t:a:8:300 r:300 q:2 p:arena r:600"
AUTO=1800 QMAX=3500 ./lroute.sh $TAG ${S}_br "b: r:420 t:down:8:20 t:down:8:20 t:start:8:200 r:900 t:a:8:60 q:2 p:boss r:600"
R="b: r:420 t:down:8:20 t:down:8:20 t:down:8:20 t:start:8:200 r:900 t:a:8:300"; for i in $(seq 1 18); do R="$R t:right:6:40"; done
AUTO=3000 QMAX=9000 ./lroute.sh $TAG ${S}_end "$R t:start:8:60 q:2 p:end1 q:2 p:end2 q:2 p:end3 r:600"
echo done > ${S}_B.done
