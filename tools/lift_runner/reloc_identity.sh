#!/bin/sh
# Lane wv-native-gfx 11-09: the relocated donor block against the plain host runner, whole golden route (plan V2 section 5). HOST tier, WSL.
# usage (from the repo root, WORK = a saturn/rt/build.py work directory, OUT = a scratch directory on the same drive):
#   sh tools/lift_runner/reloc_identity.sh WORK OUT
set -e
WORK=$1; OUT=$2; mkdir -p "$OUT/hb" "$OUT/g1"
python tools/wolverine/reloc_block.py "$WORK/rt.bin" "$OUT/g1/block.bin"
python tools/wolverine/access_audit.py "$WORK" --emit-host "$OUT/g1/slots.txt" > /dev/null
python tools/lift_runner/mask_reloc.py "$OUT/g1/mask_reloc.txt"
python tools/lift_runner/build_native_host.py "$WORK" "$OUT/hb" base --guests 0
python tools/lift_runner/build_native_host.py "$WORK" "$OUT/hb" reloc --guests 0 --reloc 1
G=/mnt/e/AvP/learning/mame/golden_c1   # MAME's golden_c1 (probe.tsv, probe.tsv.io.txt); copy next to rt.bin and op.bin in $OUT/g1 first (see tools/lift_runner/run.sh)
echo "then, in WSL, in $OUT/hb (GOLD_DELTA=1 STOP_DIV=100000000 MASK as below):"
echo "  ./base  g1/rt.bin g1/probe.tsv g1/probe.tsv.io.txt 272171 g1/mask.txt"
echo "  WVBLOCK=g1/block.bin WVSLOTS=g1/slots.txt ./reloc g1/rt.bin g1/probe.tsv g1/probe.tsv.io.txt 272171 g1/mask_reloc.txt"
echo "both must end 'clean 272171 diff 0 missed 0'; PDUMP=file on each, then tools/wolverine/fielddiff.py A B"
