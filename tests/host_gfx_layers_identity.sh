#!/bin/bash
# HOST identity of the graphics driver with the scroll layers on (frame chain lane, 2026-11-09).
# usage: tests/host_gfx_layers_identity.sh BASE_WORKTREE   (a checkout of the commit to compare against, e.g. c0e091e)
# Runs 600 random frames at FIT 1 and 0 against BASE_WORKTREE and this tree: sequential (sat_gfx_frame) and threaded (master runs the first half, wakes the
# slave thread, sleeps a random time, runs the layer half; the slave thread draws). Every VDP1 VRAM, VDP2 VRAM, CRAM and register hash must match.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); BASE=$(cd "$1" && pwd); T=${TMPDIR:-/tmp}/gfx_ident; mkdir -p "$T"
for fit in 1 0; do
 gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -I "$BASE/saturn/gfx" "$HERE/tests/host_gfx_layers_identity.c" "$BASE/saturn/gfx/sat_gfx.c" -o "$T/base$fit"
 gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -I "$HERE/saturn/gfx" "$HERE/tests/host_gfx_layers_identity.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/seq$fit"
 gcc -std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=$fit -DTHR -DSAT_LAYERS_WAIT_SPINS=4000000000UL -I "$HERE/saturn/gfx" "$HERE/tests/host_gfx_layers_identity.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/thr$fit" -lpthread
 "$T/base$fit" > "$T/base$fit.txt"; "$T/seq$fit" > "$T/seq$fit.txt"
 cmp "$T/base$fit.txt" "$T/seq$fit.txt" && echo "FIT $fit sequential: identical, $(wc -l < "$T/base$fit.txt") frames"
 for d in 0 50 400 2000; do "$T/thr$fit" $d > "$T/thr$fit.$d.txt" 2> "$T/thr$fit.$d.err"; cmp "$T/base$fit.txt" "$T/thr$fit.$d.txt" && echo "FIT $fit threaded, master delay up to ${d} us: identical ($(cat "$T/thr$fit.$d.err"))"; done
done
