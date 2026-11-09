#!/bin/sh
# usage: run_char_measure.sh NAME CHAR   (CHAR 0 Warrior, 1 Schaefer, 2 Linn, 3 Hunter). Output E:/AvP/learning/lane-wolverine-ground/NAME/objs.txt (ROM-derived, stays on this PC).
OLD="/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot"
HERE="$(cd "$(dirname "$0")" && pwd -W)"
OUT=/e/AvP/learning/lane-wolverine-ground/${1:?name}
mkdir -p "$OUT/nvram" "$OUT/cfg"
cp -r "$OLD/.deps/mame/full_route_nvram_baseline" "$OUT/nvram/avspu"
chmod -R u+w "$OUT/nvram"
cd "$OLD"
MS_NOHOLD=${MS_NOHOLD:-0} MS_OUT="E:/AvP/learning/lane-wolverine-ground/$1" WV_CHAR=${2:-1} \
  ./.deps/mame/mame0289/mame.exe avspu -rompath "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest" -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_delay 0 -nvram_directory "E:/AvP/learning/lane-wolverine-ground/$1/nvram" -cfg_directory "E:/AvP/learning/lane-wolverine-ground/$1/cfg" \
  -autoboot_script "$HERE/ap_measure.lua" > "$OUT/stdout.txt" 2>&1
echo "exit $?" >> "$OUT/stdout.txt"
