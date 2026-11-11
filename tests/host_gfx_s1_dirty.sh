#!/bin/bash
# HOST exactness of SAT_S1_DIRTY (lane perf2, 2026-11-11). Needs the ROM-derived home_font.inc and home_pal.inc (not in git): usage tests/host_gfx_s1_dirty.sh GENDIR [FRAMES] [SEEDS]
# For each seed and pack size: the reference build (SAT_S1_MEMO + SAT_S1_BLANKROWS) and the same with SAT_S1_DIRTY must print the same resolved scroll 1 layer and the same everything-else hash on every frame,
# and the in-draw verify pass must count 0 kept rows that differ. Also the two thread mode (a torn layer half would change a hash).
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); GEN=$(cd "$1" && pwd); FR=${2:-1500}; SEEDS=${3:-"777 1 2 3 4 5"}; T=${TMPDIR:-/tmp}/gfx_s1d; mkdir -p "$T"
B="gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=1 -DSAT_HOME -DSAT_S1_MEMO -DSAT_S1_BLANKROWS -I $HERE/saturn/gfx -I $GEN"
bad=0
for ns in 700 1800; do
  for thr in "" "-DTHR -DSAT_LAYERS_WAIT_SPINS=4000000000UL -lpthread"; do
    tag=ns$ns${thr:+_thr}
    $B -DNS1=$ns $thr "$HERE/tests/host_gfx_s1_dirty.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/ref_$tag"
    $B -DNS1=$ns -DSAT_S1_DIRTY $thr "$HERE/tests/host_gfx_s1_dirty.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/dirty_$tag"
    for s in $SEEDS; do
      SEED=$s FRAMES=$FR "$T/ref_$tag" > "$T/ref_$tag.$s.txt" 2> "$T/ref_$tag.$s.err" || true
      SEED=$s FRAMES=$FR "$T/dirty_$tag" > "$T/dirty_$tag.$s.txt" 2> "$T/dirty_$tag.$s.err" && rc=0 || rc=$?
      if [ $rc -ne 0 ]; then echo "$tag seed $s: dirty build exit $rc"; bad=1; fi
      # a frame in which either build refused a lookup (more distinct tiles than slots) is not compared: which tiles lose out depends on the cache history
      # and neither are the frames after it until both builds have redrawn scroll 1 without a refusal (until then each shows its own refused cells)
      paste -d' ' "$T/ref_$tag.$s.txt" "$T/dirty_$tag.$s.txt" | awk '{ ref_r = $5; ref_d = $6; dr = $11; dd = $12;
          if (ref_r > 0 || dr > 0) { tainted = 1; skipped++; next }
          if (tainted) { if (ref_d > 0 && dd > 0) tainted = 0; else { skipped++; next } }
          if ($3 != $9 || $4 != $10 || $2 != $8) { n++; if (n <= 4) print "frame " $1 ": ref " $3 " " $4 " dirty " $9 " " $10 }
          compared++ }
          END { print "compared " compared+0 " differences " n+0 " skipped (refusal and the frames after) " skipped+0 > "/dev/stderr"; exit n > 0 }' 2> "$T/cmp.txt" && r=IDENTICAL || { r=DIFFERENT; bad=1; }
      cat "$T/cmp.txt" | head -5
      echo "$tag seed $s: $r over $(wc -l < "$T/ref_$tag.$s.txt") frames | ref: $(grep 'layer uploads' "$T/ref_$tag.$s.err") | dirty: $(grep 'layer uploads' "$T/dirty_$tag.$s.err") | $(grep 's1d' "$T/dirty_$tag.$s.err")"
    done
  done
done
exit $bad
