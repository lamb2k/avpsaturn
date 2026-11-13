#!/bin/bash
# usage: stage_q.sh TAG [ISO] [AUDIO_WD] : disc folder disc_TAG from iso (default iso_TAG.iso) + the build's audio tracks, cue like the Fenrir folders
set -e
TAG=$1; L=/e/AvP/learning/lane-quitcard; ISO=${2:-$L/iso_$TAG.iso}; AUD=${3:-$L/wd_$TAG}; D=$L/disc_$TAG; A=$AUD/audio/music
mkdir -p "$D"
cp "$ISO" "$D/track01.bin"
cue="FILE \"track01.bin\" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n"
first=1
for f in $A/t*.raw; do b=$(basename $f); n=${b:1:2}; ln -f $f "$D/track$n.bin" 2>/dev/null || cp $f "$D/track$n.bin"
  if [ $first = 1 ]; then cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n"; first=0
  else cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    INDEX 01 00:00:00\n"; fi
done
printf "$cue" | sed 's/$/\r/' > "$D/$TAG.cue"
echo "$D $(grep -c TRACK "$D/$TAG.cue") tracks"
