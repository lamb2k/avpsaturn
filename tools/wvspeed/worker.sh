#!/bin/bash
# usage: worker.sh LANE_INDEX NLANES  YNSUFFIX : runs every NLANES-th line of tasks.txt on Ymir copy ymir_wv<YNSUFFIX>
cd /e/AvP/learning/lane-wv-speed
I=$1; N=$2; YNS=$3; k=0
while IFS='|' read name tag kind envs x; do
  if [ $((k % N)) = $I ]; then
    env YN=$YNS NOAUTO=1 $envs ./wscene.sh $name $tag $kind 1
    echo "$name done" >> worker_$I.log
  fi
  k=$((k+1))
done < tasks.txt
