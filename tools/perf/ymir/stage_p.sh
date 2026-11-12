#!/bin/bash
# usage: stage_p.sh ISO OUTDIR NAME : Fenrir folder (track01 = the iso, audio tracks from the build's audio/music), like integration/fenrir_pkg.sh
set -e
ISO=$1; D=$2; name=$3; A=/e/AvP/learning/lane-perf-hw/wd/audio/music
mkdir -p "$D"
cp $ISO "$D/track01.bin"
cue="FILE \"track01.bin\" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n"
first=1
for f in $A/t*.raw; do b=$(basename $f); n=${b:1:2}; cp $f "$D/track$n.bin"
  if [ $first = 1 ]; then cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n"; first=0
  else cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    INDEX 01 00:00:00\n"; fi
done
printf "$cue" | sed 's/$/\r/' > "$D/$name.cue"
echo "$D $(grep -c TRACK "$D/$name.cue") tracks"
