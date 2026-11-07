# Browser test build (private, local only)

A page that boots a Saturn image in the browser with Coin/Start, keyboard, gamepad, Reset and a load bar. No game data, BIOS or core binary is in this repo.

## Inputs

- **Image (replaceable):** `make-image.sh CUE OUT_DIR LABEL COMMIT` writes `game.chd` and `build.json` to `OUT_DIR`. Run it on any package's `.cue`. The page checks size and SHA-256 and caches one image in IndexedDB.
- **Runtime:** EmulatorJS `data/` at tag v4.2.3 (e150dc049), with the core built by `core/build-core.sh` copied to `cores/yabause-legacy-wasm.data`. Its hash is pinned in `public/runtime-config.mjs`.

## Run

    node server.mjs --image OUT_DIR --runtime EJS_DATA_DIR --port 8793
    node test/edge-test.mjs EVIDENCE_DIR OUT_DIR EJS_DATA_DIR

Node 22 and Edge. The server binds to 127.0.0.1 only. Not deployed.

## Core

Libretro Yabause 0.9.15 at 8926b0c6c (GPL-2.0), EmulatorJS RetroArch at ed3265745 (GPL-3.0), Emscripten 3.1.74, patch `core/yabause-web.patch`:
- fetch functions with the right signature (wasm traps otherwise);
- instruction fetch from the whole A-bus window (our code runs from the cart);
- CD buffer free count restored on selector reset (round loads hang otherwise);
- whole raw sectors from 2048-byte CHD tracks (CHD does not boot otherwise);
- test-only reads: `web_peek8`, `web_pc`, CD audio counter, frame timer.

Core options: 4 MB RAM cart, high-level BIOS, no frameskip.
