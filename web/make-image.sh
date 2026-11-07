#!/bin/bash
# Turn any package's .cue into the page's input: DIR/game.chd and DIR/build.json. Needs chdman (mame-tools). The image is never committed.
# usage: make-image.sh CUE OUT_DIR BUILD_LABEL COMMIT
set -euo pipefail
CUE=${1:?cue}; OUT=${2:?out dir}; LABEL=${3:?label}; COMMIT=${4:?commit}
mkdir -p "$OUT"
chdman createcd -f -i "$CUE" -o "$OUT/game.chd" >/dev/null 2>&1
BYTES=$(stat -c %s "$OUT/game.chd"); HASH=$(sha256sum "$OUT/game.chd" | cut -d' ' -f1)
printf '{"schema":1,"status":"ready","build":"%s","commit":"%s","image":{"path":"/files/game.chd","bytes":%s,"sha256":"%s"}}\n' "$LABEL" "$COMMIT" "$BYTES" "$HASH" > "$OUT/build.json"
cat "$OUT/build.json"
