#!/bin/sh
# usage: run_walk.sh NAME CHAR [MAXF]   Output E:/AvP/learning/lane-wolverine/palcensus/NAME (ROM-derived, stays on this PC).
OLD="/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot"
HERE="$(cd "$(dirname "$0")" && pwd -W)"
OUT=/e/AvP/learning/lane-wolverine/iface/${1:?name}
mkdir -p "$OUT/nvram" "$OUT/cfg"
cp -r "$OLD/.deps/mame/full_route_nvram_baseline" "$OUT/nvram/avspu"
chmod -R u+w "$OUT/nvram"
cd "$OLD"
WV_HERE="$HERE" AM_OUT="E:/AvP/learning/lane-wolverine/iface/$1" AM_CHAR=${2:-0} AM_MAXF=${3:-450000} \
  ./.deps/mame/mame0289/mame.exe avspu -rompath "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest" -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_delay 0 -nvram_directory "E:/AvP/learning/lane-wolverine/iface/$1/nvram" -cfg_directory "E:/AvP/learning/lane-wolverine/iface/$1/cfg" \
  -autoboot_script "$HERE/iface_census.lua" > "$OUT/stdout.txt" 2>&1
echo "exit $?" >> "$OUT/stdout.txt"
