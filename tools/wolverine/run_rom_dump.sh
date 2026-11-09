#!/bin/sh
# usage: run_rom_dump.sh OUTFILE RANGES   (RANGES "1986e:60,19b68:40"); output is ROM-derived, keep under E:/AvP/learning.
OLD="/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-playable-loop-pivot"
HERE="$(cd "$(dirname "$0")" && pwd -W)"
D=$(dirname "$1"); mkdir -p "$D/nv" "$D/cfg"; cp -r "$OLD/.deps/mame/full_route_nvram_baseline" "$D/nv/avspu"; chmod -R u+w "$D/nv"
cd "$OLD"
RD_OUT="$(cygpath -m "$1")" RD_RANGES="$2" ./.deps/mame/mame0289/mame.exe avspu -rompath "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest" -video none -sound none -nothrottle -skip_gameinfo -autoboot_delay 0 -nvram_directory "$(cygpath -m "$D/nv")" -cfg_directory "$(cygpath -m "$D/cfg")" -autoboot_script "$HERE/rom_dump.lua" > "$D/rd_stdout.txt" 2>&1
