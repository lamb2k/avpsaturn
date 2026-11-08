#!/bin/bash
# Lane avp-megaman: regenerate Mega Man's build inputs from the user's own MvC ROM set (mvsc + mvscroms overlay).
# Nothing ROM-derived is committed; everything lands under OUT (default E:/AvP/learning/lane-megaman).
# usage: build_inputs.sh AVP_WORK [OUT] [OTHER_GUEST_REMAP_JSON]
#   AVP_WORK: a finished build's WORK dir (rounds.json, screen_keys.txt, key_rank.json, round_code_ends.json, rom_final.bin)
set -e
H=$(cd "$(dirname "$0")" && pwd)
WORK=${1:?AVP_WORK}; OUT=${2:-/e/AvP/learning/lane-megaman}; EXCL=${3:-/e/AvP/learning/lane-wolverine/out/remap.json}
mkdir -p "$OUT"
python "$H/schedule.py" "${MSEQ3:-E:/AvP/learning/guest-analysis/mseq3.txt}" "$(cygpath -m "$OUT/full.txt")" "$(cygpath -m "$OUT/windows.json")"
python "$H/schedule_win.py" "${MSEQ3:-E:/AvP/learning/guest-analysis/mseq3.txt}" "$(cygpath -m "$OUT/win.txt")"
"$H/run_mame.sh" "$OUT/full.txt" 8180 2100 60 "$OUT/full"      # moves, hits, KO
"$H/run_mame.sh" "$OUT/win.txt" 7800 2100 60 "$OUT/win"        # charged Mega Buster shots, round win pose
"$H/run_mame.sh" "$OUT/full.txt" 2100 1000 20 "$OUT/sel"       # select, stage card and VS portraits
python "$H/assets.py" "$(cygpath -m "$OUT/full")" "$(cygpath -m "$OUT/win")" "$(cygpath -m "$OUT/sel")" "$(cygpath -m "$OUT/windows.json")" \
  "$(cygpath -m "$WORK")" "$(cygpath -m "$OUT/out")" "" "$(cygpath -m "$EXCL")"
python "$H/fit.py" "$(cygpath -m "$WORK")" "$(cygpath -m "$OUT/out")" | tee "$OUT/fit_all.log"
