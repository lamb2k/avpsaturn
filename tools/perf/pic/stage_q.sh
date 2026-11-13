#!/bin/bash
# usage: stage_q.sh TAG NAME  : Fenrir folder E:/AvP/package-integration/fenrir/NAME (track01 = iso_TAG.iso, audio tracks from wd_TAG/audio/music), cue, SHA256SUMS
set -e
TAG=$1; name=$2; L=/e/AvP/learning/lane-perf-pic; D=/e/AvP/package-integration/fenrir/$name; A=$L/wd_$TAG/audio/music
mkdir -p "$D"
cp $L/iso_$TAG.iso "$D/track01.bin"
cue="FILE \"track01.bin\" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n"
first=1
for f in $A/t*.raw; do b=$(basename $f); n=${b:1:2}; cp $f "$D/track$n.bin"
  if [ $first = 1 ]; then cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n"; first=0
  else cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    INDEX 01 00:00:00\n"; fi
done
printf "$cue" | sed 's/$/\r/' > "$D/$name.cue"
(cd "$D" && sha256sum *.cue track*.bin > SHA256SUMS)
echo "$D $(grep -c TRACK "$D/$name.cue") tracks"
