#!/bin/bash
# usage: stage_l.sh TAG : disc folder E:/AvP/learning/lane-loading/disc_TAG from iso_TAG.iso + the build's audio tracks (hard links, same drive), cue like the Fenrir folders
set -e
TAG=$1; L=/e/AvP/learning/lane-loading; D=$L/disc_$TAG; A=$L/wd/audio/music
mkdir -p "$D"
ln -f $L/iso_$TAG.iso "$D/track01.bin" 2>/dev/null || cp $L/iso_$TAG.iso "$D/track01.bin"
cue="FILE \"track01.bin\" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n"
first=1
for f in $A/t*.raw; do b=$(basename $f); n=${b:1:2}; ln -f $f "$D/track$n.bin" 2>/dev/null || cp $f "$D/track$n.bin"
  if [ $first = 1 ]; then cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n"; first=0
  else cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    INDEX 01 00:00:00\n"; fi
done
printf "$cue" | sed 's/$/\r/' > "$D/$TAG.cue"
echo "$D $(grep -c TRACK "$D/$TAG.cue") tracks"
