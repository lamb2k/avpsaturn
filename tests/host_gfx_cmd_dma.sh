#!/bin/bash
# HOST identity of SAT_CMD_DMA (lane perf-pic, 2026-11-12): VDP1 VRAM (command tables without the 16 bytes of a command that are never written), VDP2 VRAM, CRAM, registers frame for frame against the build
# without it, FIT 1 and 2, 600 frames of random objects and layers. The host copy stands in for the SCU DMA; the board's DMA is checked in Ymir (screens, game RAM). Needs WORK/gen: usage tests/host_gfx_cmd_dma.sh GENDIR
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); GEN=$(cd "$1" && pwd); T=${TMPDIR:-/tmp}/gfx_cd; mkdir -p "$T"
for fit in 1 2; do
 for cs in 16 3 1; do
  B="gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -DSAT_HOME -DCMD_DMA_MASK -DSAT_S1_MEMO -DSAT_S1_BLANKROWS -I $HERE/saturn/gfx -I $GEN"
  S="$HERE/tests/host_gfx_s1_identity.c $HERE/saturn/gfx/sat_gfx.c"
  $B $S -o "$T/base" 2>/dev/null; "$T/base" > "$T/base.txt"
  $B -DSAT_CMD_DMA -DCMD_STG=$cs $S -o "$T/dma" 2>"$T/dma.err" || { echo "dma build failed"; head -5 "$T/dma.err"; exit 1; }
  "$T/dma" > "$T/dma.txt"
  if cmp -s "$T/base.txt" "$T/dma.txt"; then echo "fit$fit CMD_STG=$cs: identical, $(wc -l < "$T/base.txt") frames"; else echo "fit$fit CMD_STG=$cs: DIFFERENT"; diff "$T/base.txt" "$T/dma.txt" | head -4; fi
 done
done
