#!/bin/bash
# Mutation check for tests/host_gfx_s1_dirty.sh (lane perf2, 2026-11-11): the test must FAIL when the incremental redraw is broken on purpose.
# usage: tests/host_gfx_s1_dirty_mutation.sh GENDIR [FRAMES] [SEEDS]
#   S1D_TEST_NORESTAMP  no re-stamp of the kept rows' tile slots (a lookup of a changed row can take a kept row's slot)
#   S1D_TEST_NOWIDEN    changed rows only, no widening to the blocks they can change (a kept row keeps a stale column map)
# Exit status 0 only if every mutation is caught (a differing frame, or a nonzero verify count).
HERE=$(cd "$(dirname "$0")/.." && pwd); GEN=$(cd "$1" && pwd); FR=${2:-1500}; SEEDS=${3:-"777 1 2"}; T=${TMPDIR:-/tmp}/gfx_s1d_mut; mkdir -p "$T"
B="gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=1 -DSAT_HOME -DSAT_S1_MEMO -DSAT_S1_BLANKROWS -I $HERE/saturn/gfx -I $GEN -DNS1=1800"
$B "$HERE/tests/host_gfx_s1_dirty.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/ref" || exit 2
missed=0
for m in S1D_TEST_NORESTAMP S1D_TEST_NOWIDEN; do
  $B -DSAT_S1_DIRTY -D$m "$HERE/tests/host_gfx_s1_dirty.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/mut_$m" || exit 2
  caught=0
  for s in $SEEDS; do
    SEED=$s FRAMES=$FR "$T/ref" > "$T/ref.txt" 2> /dev/null
    SEED=$s FRAMES=$FR "$T/mut_$m" > "$T/mut.txt" 2> "$T/mut.err"; rc=$?
    d=$(paste -d' ' "$T/ref.txt" "$T/mut.txt" | awk '($5 == 0 && $11 == 0) && ($3 != $9 || $4 != $10) { n++ } END { print n+0 }')
    echo "$m seed $s: exit $rc, differing frames $d, $(grep s1d "$T/mut.err" | sed 's/.*verify rows/verify rows/;s/, empty.*//')"
    if [ "$rc" -ne 0 ] || [ "$d" -gt 0 ]; then caught=1; fi
  done
  if [ $caught -eq 0 ]; then echo "$m: NOT CAUGHT"; missed=1; else echo "$m: caught"; fi
done
exit $missed
