#!/bin/bash
# HOST identity of the scroll 1 switches (lane perf-reconcile, 2026-11-10). Needs WORK/gen with home_font.inc and home_pal.inc (ROM-derived, not in git): usage tests/host_gfx_s1_identity.sh GENDIR
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); GEN=$(cd "$1" && pwd); T=${TMPDIR:-/tmp}/gfx_s1; mkdir -p "$T"
B="gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=1 -DSAT_HOME -I $HERE/saturn/gfx -I $GEN"
$B "$HERE/tests/host_gfx_s1_identity.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/base"; "$T/base" > "$T/base.txt"
for v in "memo:-DSAT_S1_MEMO" "blank:-DSAT_S1_BLANKROWS" "memo+blank:-DSAT_S1_MEMO -DSAT_S1_BLANKROWS" "fontcold:-DSAT_HOME_FONT_COLD" "all:-DSAT_S1_MEMO -DSAT_S1_BLANKROWS -DSAT_HOME_FONT_COLD" "all+hud-every:-DSAT_S1_MEMO -DSAT_S1_BLANKROWS -DSAT_HOME_FONT_COLD"; do
  n=${v%%:*}; f=${v#*:}
  $B $f "$HERE/tests/host_gfx_s1_identity.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/$n" 2>"$T/$n.err" || { echo "$n: build failed"; head -3 "$T/$n.err"; continue; }
  "$T/$n" > "$T/$n.txt"
  if cmp -s "$T/base.txt" "$T/$n.txt"; then echo "$n: identical, $(wc -l < "$T/base.txt") frames"; else echo "$n: DIFFERENT"; diff "$T/base.txt" "$T/$n.txt" | head -4; fi
done
