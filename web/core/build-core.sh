#!/bin/bash
# Build the patched core and package it for EmulatorJS. Linux/WSL with git, make, zip, python3.
# usage: build-core.sh WORK_DIR OUT_DIR  (WORK_DIR on ext4; OUT_DIR gets yabause-legacy-wasm.data)
set -euo pipefail
WORK=${1:?work}; OUT=${2:?out}; HERE=$(cd "$(dirname "$0")" && pwd)
YAB=8926b0c6c347f8c5c755911ddb0ac695420ffbf8; RA=ed3265745eccec99b48f99e2a2ffc8a6a93823bb; EM=3.1.74
mkdir -p "$WORK" "$OUT"; cd "$WORK"
[ -d emsdk ] || git clone -q https://github.com/emscripten-core/emsdk.git
(cd emsdk && ./emsdk install $EM >/dev/null && ./emsdk activate $EM >/dev/null)
source emsdk/emsdk_env.sh >/dev/null 2>&1
[ -d yabause ] || git clone -q https://github.com/libretro/yabause.git
git -C yabause checkout -q "$YAB"; git -C yabause checkout -q -- .
git -C yabause apply --ignore-whitespace "$HERE/yabause-web.patch"
[ -d EJS-RetroArch ] || git clone -q https://github.com/EmulatorJS/RetroArch.git EJS-RetroArch
git -C EJS-RetroArch checkout -q $RA
cd yabause/yabause/src/libretro
emmake make -f Makefile platform=emscripten clean >/dev/null 2>&1 || true
emmake make -f Makefile platform=emscripten HAVE_THREADS=0 -j4 >/dev/null 2>&1
cp yabause_libretro_emscripten.bc "$WORK/EJS-RetroArch/libretro_emscripten.a"
cd "$WORK/EJS-RetroArch"; rm -f yabause_libretro.js yabause_libretro.wasm
EMCC_CFLAGS="--profiling-funcs -O3" emmake make -f Makefile.emulatorjs LIBRETRO=yabause TARGET=yabause_libretro.js HAVE_THREADS=0 HAVE_OPENGLES3=0 MIN_ASYNC=1 LTO=0 STACK_SIZE=4194304 INITIAL_HEAP=134217728 -j4 >/dev/null 2>&1
cp yabause_libretro.js yabause_libretro.wasm "$OUT/"; cp "$WORK/yabause/yabause/COPYING" "$OUT/license.txt"
cd "$OUT"
printf '{"name":"yabause","extensions":["cue","iso","chd","ccd","mds","m3u"],"options":{"defaultWebGL2":false},"save":"srm","repo":"https://github.com/libretro/yabause"}' > core.json
rm -f yabause-legacy-wasm.data; zip -q yabause-legacy-wasm.data yabause_libretro.js yabause_libretro.wasm core.json license.txt
sha256sum yabause-legacy-wasm.data
