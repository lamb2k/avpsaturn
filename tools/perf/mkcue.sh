#!/bin/bash
# usage: mkcue.sh WORKDIR OUTDIR NAME : iso + cue + audio tracks (hard links where possible)
set -e
W=$1; D=$2; name=$3; mkdir -p $D
ln -f $W/sat.iso $D/$name.iso 2>/dev/null || cp $W/sat.iso $D/$name.iso
cue="FILE \"$name.iso\" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n"
for f in $W/audio/music/t*.raw; do b=$(basename $f); ln -f $f $D/$b 2>/dev/null || cp $f $D/$b; cue+="FILE \"$b\" BINARY\n  TRACK ${b:1:2} AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n"; done
printf "$cue" > $D/$name.cue
echo "$D $(grep -c TRACK $D/$name.cue) tracks"
