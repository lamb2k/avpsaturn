#!/bin/bash
# usage: run_mame.sh SEQ LAST FROM SNAPSTEP OUTDIR   (MvC set mvsc with the user's mvscroms overlay; output ROM-derived, keep under E:/AvP/learning)
set -e
H=$(cd "$(dirname "$0")" && pwd)
MAME="${MAME_EXE:-/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest/.deps/mame/mame0289/mame.exe}"
ROMS="${MVSC_ROMPATH:-C:/Game Dev/Emulators;E:/AvP/learning/guest-analysis/mvscroms}"
out=${5:?}; rm -rf "${out:?}"; mkdir -p "$out/snap/wv"
export WV_ROOT="$(cygpath -m "$out")" WV_SEQ="$(cygpath -m "$1")" WV_LAST=$2 WV_FROM=$3 WV_SNAP=$4
cd "$out"
"$MAME" mvsc -rompath "$ROMS" -video none -sound none -nothrottle -skip_gameinfo -nvram_directory "$(cygpath -m "$out/nv")" -cfg_directory "$(cygpath -m "$out/cfg")" -snapshot_directory "$(cygpath -m "$out/snap")" -autoboot_script "$(cygpath -m "$H/mame_megaman.lua")" 2>&1 | tail -3
