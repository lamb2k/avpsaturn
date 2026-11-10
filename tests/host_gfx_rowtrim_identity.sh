#!/bin/bash
# HOST identity of SAT_TILE_ROWTRIM (lane stage-sprites, 2026-11-09): the same random frames, sprite tiles from an SGP1 pack and from an SGP2 pack of row masked records
# (a third of them in a spill area), must give the same VDP1 VRAM, VDP2 VRAM, CRAM and register hashes in every frame.
# usage: tests/host_gfx_rowtrim_identity.sh
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); T=${TMPDIR:-/tmp}/gfx_rowtrim; mkdir -p "$T"
for fit in 1 0; do
 gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -I "$HERE/saturn/gfx" "$HERE/tests/host_gfx_rowtrim_identity.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/plain$fit"
 gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -DSAT_TILE_ROWTRIM -DRT -I "$HERE/saturn/gfx" "$HERE/tests/host_gfx_rowtrim_identity.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/rt$fit"
 "$T/plain$fit" > "$T/plain$fit.txt"; "$T/rt$fit" > "$T/rt$fit.txt"
 cmp "$T/plain$fit.txt" "$T/rt$fit.txt" && echo "FIT $fit: SGP2 row trimmed sprite tiles identical to SGP1, $(wc -l < "$T/plain$fit.txt") frames, uploads $(tail -1 "$T/plain$fit.txt" | cut -d' ' -f3)"
done
