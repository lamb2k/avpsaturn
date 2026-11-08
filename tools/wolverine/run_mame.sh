#!/bin/bash
# usage: run_mame.sh SEQ LAST FROM SNAPSTEP OUTDIR   (MSHvSF via the MSHvSF repo's tools/run_mshvsf_mame.py; output ROM-derived, keep under E:/AvP/learning)
set -e
H=$(cd "$(dirname "$0")" && pwd)
R="${MSHVSF_REPO:-/c/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-MSHvSF}"
PY="${MSHVSF_PY:-$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe}"
out=${5:?}; rm -rf "${out:?}"; mkdir -p "$out/snap/wv"
export WV_ROOT="$(cygpath -m "$out")" WV_SEQ="$(cygpath -m "$1")" WV_LAST=$2 WV_FROM=$3 WV_SNAP=$4
cd "$R"
"$PY" tools/run_mshvsf_mame.py -- mshvsf -video none -sound none -nothrottle -skip_gameinfo -snapshot_directory "$(cygpath -m "$out/snap")" -autoboot_script "$(cygpath -m "$H/mame_wolverine.lua")" 2>&1 | tail -3
