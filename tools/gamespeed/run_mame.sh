#!/bin/sh
# usage: run_mame.sh NAME MAXF
OLD="/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot"
OUT=/e/AvP/learning/lane-perf/gamespeed/${1:?name}
mkdir -p "$OUT/nvram" "$OUT/cfg"
rm -rf "$OUT/nvram/avspu"; cp -r "$OLD/.deps/mame/full_route_nvram_baseline" "$OUT/nvram/avspu"
chmod -R u+w "$OUT/nvram"
cd "$OLD"
GS_OUT="E:/AvP/learning/lane-perf/gamespeed/$1" GS_MAXF=${2:-40000} \
  ./.deps/mame/mame0289/mame.exe avspu -rompath "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest" -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_delay 0 -nvram_directory "E:/AvP/learning/lane-perf/gamespeed/$1/nvram" -cfg_directory "E:/AvP/learning/lane-perf/gamespeed/$1/cfg" \
  -seconds_to_run 100000 -autoboot_script "E:/AvP/learning/lane-perf/gamespeed/gs_walk.lua" > "$OUT/stdout.txt" 2>&1
echo "exit $?" >> "$OUT/stdout.txt"
