#!/bin/bash
# Debug helper for host_gfx_s1_dirty.c: usage host_gfx_s1_dirty_dump.sh GENDIR SEED FRAME [NS1]
# Builds the reference and the incremental build, runs both to FRAME and prints the cells of the resolved scroll 1 layer that differ at FRAME.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd); GEN=$(cd "$1" && pwd); SEED=$2; FR=$3; NS=${4:-1800}; T=${TMPDIR:-/tmp}/gfx_s1d; mkdir -p "$T"
F="-std=gnu99 -O1 -w -DSAT_GFX_HOST -DSAT_GFX_FIT=1 -DSAT_HOME -DSAT_S1_MEMO -DSAT_S1_BLANKROWS -I $HERE/saturn/gfx -I $GEN -DNS1=$NS"
gcc $F "$HERE/tests/host_gfx_s1_dirty.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/refd"
gcc $F -DSAT_S1_DIRTY "$HERE/tests/host_gfx_s1_dirty.c" "$HERE/saturn/gfx/sat_gfx.c" -o "$T/dirtyd"
SEED=$SEED FRAMES=$((FR + 1)) DUMPRES=$FR "$T/refd" 2> "$T/r.txt" > /dev/null || true
SEED=$SEED FRAMES=$((FR + 1)) DUMPRES=$FR "$T/dirtyd" 2> "$T/d.txt" > /dev/null || true
diff <(grep '^R' "$T/r.txt" | sed 's/ ch [0-9a-f]*//') <(grep '^R' "$T/d.txt" | sed 's/ ch [0-9a-f]*//') | head -${5:-30} || true
echo "cells differing: $(diff <(grep '^R' "$T/r.txt" | sed 's/ ch [0-9a-f]*//') <(grep '^R' "$T/d.txt" | sed 's/ ch [0-9a-f]*//') | grep -c '^<' || true)"
