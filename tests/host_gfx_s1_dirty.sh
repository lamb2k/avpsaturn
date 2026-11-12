#!/bin/bash
# HOST identity of SAT_S1_DIRTY (lane perf-pic, 2026-11-12): the resolved scroll 1 layer (every visible name followed to its cell, flips, bank), VDP1 VRAM, CRAM, registers and the rest of VDP2 VRAM
# frame for frame against the plain build and against MEMO+BLANKROWS, FIT 1 and FIT 2, a stage like run (STICKY: flags and position hold) and a heavy one (S1HEAVY: more tiles than slots).
# Needs WORK/gen with home_font.inc and home_pal.inc (ROM-derived, not in git): usage tests/host_gfx_s1_dirty.sh GENDIR
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); GEN=$(cd "$1" && pwd); T=${TMPDIR:-/tmp}/gfx_s1d; mkdir -p "$T"
# first frame where two outputs differ (a very large number when they do not)
firstdiff() { diff "$1" "$2" | grep '^<' | head -1 | awk '{print $2}' | grep . || echo 999999; }
# Under slot starvation (more distinct visible tiles than slots: the S1HEAVY modes saturate it) which cells go blank depends on the order of the lookups, and a partial redraw looks up in another
# order than a full one, so the two builds differ from the first frame in which the plain build refuses a cell. Until then they must be identical; the test says where that frame is.
for fit in 1 2; do
 for mode in "plain:" "sticky:-DSTICKY" "heavy:-DSTICKY -DS1HEAVY" "heavyj:-DS1HEAVY" "play:-DPLAYLIKE" "playheavy:-DPLAYLIKE -DS1HEAVY"; do
  mn=${mode%%:*}; mf=${mode#*:}
  B="gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -DSAT_HOME -DRESOLVED_S1 -DPRINT_REF $mf -I $HERE/saturn/gfx -I $GEN"
  S="$HERE/tests/host_gfx_s1_identity.c $HERE/saturn/gfx/sat_gfx.c"
  $B -DSAT_S1_MEMO -DSAT_S1_BLANKROWS $S -o "$T/ref" 2>"$T/ref.err" || { echo "ref build failed"; head -3 "$T/ref.err"; exit 1; }
  "$T/ref" > "$T/ref.txt" 2>/dev/null
  $B $S -o "$T/base" 2>/dev/null; "$T/base" > "$T/base.txt" 2> "$T/base.ref"
  # first frame in which the plain build refused a layer cell
  fr=$(awk 'NR>1 && $3!=p {print $2; exit} {p=$3}' "$T/base.ref"); [ -n "$fr" ] || fr=999999
  d=$(firstdiff "$T/base.txt" "$T/ref.txt")
  if [ "$d" = 999999 ]; then echo "fit$fit $mn memo+blank vs plain: identical, $(wc -l < "$T/ref.txt") frames"; else echo "fit$fit $mn memo+blank vs plain: first difference at frame $d (first refusal $fr)"; fi
  $B -DSAT_S1_MEMO -DSAT_S1_BLANKROWS -DSAT_S1_DIRTY $S -o "$T/dirty" 2>"$T/dirty.err" || { echo "dirty build failed"; head -5 "$T/dirty.err"; exit 1; }
  "$T/dirty" > "$T/dirty.txt" 2> "$T/dirty.cnt"; grep '^s1 dirty' "$T/dirty.cnt"
  d=$(firstdiff "$T/base.txt" "$T/dirty.txt")
  if [ "$d" = 999999 ]; then echo "fit$fit $mn DIRTY vs plain: identical, $(wc -l < "$T/dirty.txt") frames (plain refuses from frame $fr)";
  elif [ "$d" -ge "$fr" ]; then echo "fit$fit $mn DIRTY vs plain: identical up to the first refused cell (frame $fr), differs from frame $d (slot starvation, lookup order)";
  else echo "fit$fit $mn DIRTY vs plain: DIFFERENT at frame $d, before any refusal (first refusal $fr)"; fi
  if [ -n "$MUTATE" ]; then   # the test must see a restamp or a block expansion that is left out
   for m in NORESTAMP NOEXPAND; do
    $B -DSAT_S1_MEMO -DSAT_S1_BLANKROWS -DSAT_S1_DIRTY -DSAT_S1D_TEST_$m $S -o "$T/mut" 2>/dev/null; "$T/mut" > "$T/mut.txt" 2>/dev/null
    d=$(firstdiff "$T/base.txt" "$T/mut.txt")
    if [ "$d" = 999999 ]; then echo "  mutation $m: not seen here"; elif [ "$d" -lt "$fr" ]; then echo "  mutation $m: DETECTED at frame $d, before any refusal"; else echo "  mutation $m: seen only from frame $d (after the first refusal $fr)"; fi
   done
  fi
 done
done
