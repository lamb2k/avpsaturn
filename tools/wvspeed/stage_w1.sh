#!/bin/bash
# stage the fix7w1 disc (build P6: the release recipe, GUEST_DEFAULT=0) as a Fenrir folder: track01 = the iso, audio tracks from the build, cue as the other discs
set -e
N=avp_3h_A_fix7w1; D=/e/AvP/package-integration/fenrir/$N; L=/e/AvP/learning/lane-wv-speed; A=$L/wd_P6/audio/music
mkdir -p "$D"
cp $L/iso_P6.iso "$D/track01.bin"
cue="FILE \"track01.bin\" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n"
first=1
for f in $A/t*.raw; do b=$(basename $f); n=${b:1:2}; cp $f "$D/track$n.bin"
  if [ $first = 1 ]; then cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n"; first=0
  else cue+="FILE \"track$n.bin\" BINARY\n  TRACK $n AUDIO\n    INDEX 01 00:00:00\n"; fi
done
printf "$cue" | sed 's/$/\r/' > "$D/$N.cue"
(cd "$D" && sha256sum *.cue track*.bin > SHA256SUMS)
echo "$D $(grep -c TRACK "$D/$N.cue") tracks"
