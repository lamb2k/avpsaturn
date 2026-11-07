#!/bin/bash
# Build web/.site (git-ignored) for wrangler: page, EmulatorJS runtime without other cores, pinned core, licence texts. Never any game data.
# usage: stage-site.sh EJS_CHECKOUT CORE_DATA_FILE COPYING_GPL2
set -euo pipefail
EJS=${1:?ejs checkout}; CORE=${2:?core file}; GPL2=${3:?GPL-2.0 text}
HERE=$(cd "$(dirname "$0")" && pwd); SITE="$HERE/.site"
rm -rf "${SITE:?}"; mkdir -p "$SITE/runtime/cores"
cp "$HERE"/public/* "$SITE/"
cp "$HERE/core/yabause-web.patch" "$HERE/core/build-core.sh" "$SITE/"
cp "$GPL2" "$SITE/LICENSE-GPL-2.0.txt"; cp "$EJS/LICENSE" "$SITE/LICENSE-GPL-3.0.txt"
cp "$EJS/data/loader.js" "$EJS/data/emulator.css" "$EJS/data/version.json" "$SITE/runtime/"
cp -r "$EJS/data/src" "$EJS/data/compression" "$EJS/data/localization" "$SITE/runtime/"
cp "$CORE" "$SITE/runtime/cores/yabause-legacy-wasm.data"
find "$SITE" -type f \( -name '*.chd' -o -name '*.iso' -o -name '*.raw' -o -name '*.bin' \) -print -delete
find "$SITE" -type f -size +24M -print
find "$SITE" -type f | wc -l; du -sh "$SITE"; sha256sum "$SITE/runtime/cores/yabause-legacy-wasm.data"
