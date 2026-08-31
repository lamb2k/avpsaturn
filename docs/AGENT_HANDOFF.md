# REIMPLEMENT-13 active agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot` from branch
HEAD. `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` remains active. The accepted runtime
candidate remains `d04a65a2253175c6e820140feefc35419e2cca07` until the complete Coffee Shop zero-gap gate passes.
Workflow pivot / Preserved evidence work: Resume the AvP salvage Goal; retain SALVAGE-00-OLD-BUILD-BASELINE, USER-01-PLAYER-BASELINE-REVIEW, and evidence candidate `597f4ed517d4e715d814ff841bd00d3977803f85`.

Read `project_state.yaml`, this file, the active card, and current SPEC-02 contract/generated fixtures completely. Do not create another Goal, roadmap,
workflow, branch, task hierarchy, coverage system, or writer. Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, physical Saturn `UNRUN`, and all locks.
Never stage/reset/overwrite user-owned `data/avsp_anim_records.json` or `history.txt`; stage owned paths explicitly.

## Owner direction (2026-08-31): headless emulator visual-capture lane

Queue this as the next bounded body after the in-flight memory-plan program
checkpoints; do not interleave it mid-body. Goal: replace window-bound WGC for
all machine visual QA with frame-exact headless screenshots served by the
pinned emulator's own MCP endpoint; window-only WGC remains solely for
user-facing review packages.

Body: extend the existing diagnostic Yaba Sanshiro fork (the locally modified
source checkout `71c973f...` that already provides the `:9640/mcp` endpoint)
with one new MCP tool, `framebuffer_screenshot`: while paused via the existing
`pause`/`breakpoint_add`/`wait_for_stop` machinery, capture the emulator's own
rendered frame (renderer FBO readback, or the software video core buffer) and
return PNG bytes plus frame-identity metadata (emulated frame counter and
enough register/state identity to bind the image to a ledger row). Also
support a bounded frame-range capture-to-directory mode so whole-scene
cadence-1 sweeps do not need one HTTP round trip per frame. No gameplay,
timing, or emulation-semantics change is permitted.

Discipline:
- Carry the change as a tracked patch against the pinned upstream revision,
  committed in the engine-patches pattern; never commit emulator binaries or
  the source checkout itself.
- Rebuild, then re-pin: update `setup_emulator.ps1` and the source-ledger
  package/archive/EXE SHA-256 entries, and record the pin change as evidence.
- Negative control 1 (emulation unchanged): rerun one accepted paired
  cold-run scenario on the new build and require its semantic ledgers to
  remain byte-identical to the recorded hashes.
- Negative control 2 (capture determinism): the same frame across two cold
  runs must produce byte-identical image hashes; a different frame must not.
- Evidence tier: the screenshots are ONE_EMULATOR rendered output, the same
  tier as WGC; they upgrade no claim, and the SCU-DMA/A-bus rule remains
  physical-tier-only regardless of any screenshot.
- Integration: give the existing visual-QA scripts an MCP mode that produces
  the same cadence-1 contact sheets; from then on machine visual QA uses the
  MCP lane by default and window-only WGC is reserved for USER checkpoints.

After this body checkpoints, return to the standing plan (the earliest
Coffee Shop divergence and its scene regressions) with the MCP lane as the
default visual evidence path.

## Verified active boundary

The complete Coffee Shop record-type-20/class-`0x05` program and CPU-mediated cart-to-VDP1 upload boundary are committed at `2f516cd`. The full scene remains
intentionally RED at native frame 4006, scheduler code 29. Raw unexplained counters remain 327 actor-lifetime, 1234 spawn/despawn, 2 active-state,
93 collision/damage, 3 route/camera, and 281 audio/load rows until the next complete census. Do not reopen class-`0x05` or promote the candidate.

The bounded complete-Round-1 memory program is implemented in the current checkpoint. `data/reimplement13_round1_memory_plan.json` records the complete
work-RAM/cart map and 94-segment/1,517-writer census sizing. Target build-time asserts cover every carve. All 152 generated read-only SPEC tables form one
deterministic 46,564-byte SH-2 archive at cart `0x22711000`, SHA-256 `b2bae49f6182dcde3ced8d47342d5689c48b5095793ae4ec0ead61323c64d587`,
loaded only at the existing boot seam. Mutable state remains in the fixed runtime pool and composite scratch remains CPU-mediated. Round 1-to-2 loading is
inactive and reserved as `ADAPTED_PRESENTATION_FOR_USER_10`; intra-round loads remain inactive unless census-proven, camera-locked, CDDA-safe, and never mid-combat.

Focused memory, Target wiring, cart-upload, class-`0x05`, Oracle auxiliary, SPEC-02, and generator checks pass (18/130/4/4/114/180 mutations or suppressions).
Target passes with GAME.BIN 371,408 bytes, BSS end `0x060b1be0`, and GAME.BIN SHA-256 `857ffe7c695add3f38f82f5cea68ee303635e6919fd82982435bb47dbe2095de`.
The regenerated SPEC contract/fixture identities are `7a0db579d3751541d374444ebae60a009f9afedf75840457661b60de1fa93b3a` and
`ae84a21f139fc86d820b22a2e6277e838cd2b31e9f17519619e799418a5eb76b`. Two cold pinned-emulator runs pass byte-identically at normalized ISO SHA-256
`9a6ccf084933397826ae1a4d7128bbc1d3254a6b862e91d7291c8bc958a68e60`; both report the boot-loaded archive bound before native Round 1 initialization.
Window-only WGC confirms Predator identity, P1-only HUD, coherent actors, both VDP2 planes, palette, and priority. The SCU-DMA A-bus restriction remains
physical-tier-only; physical Saturn is `UNRUN`.
Fast and Oracle pass their memory/SPEC/Oracle checks and then stop at the preserved full-host frame-3782 Coffee Shop chronology RED; this is the active scene
divergence, not a memory-program acceptance failure.

## Exact next experiment

Commit and push the memory-program checkpoint, verify `private-origin` equals local SHA, then return to the earliest Coffee Shop frame-4006 player-collision
divergence. Regenerate the complete source/native census, identify its owning reusable source program, close every Coffee Shop-reachable branch from accepted
Oracle/SPEC evidence, and rerun affected scene regressions. Do not add a frame exception, authored delay, guessed rule, or further ad-hoc size squeeze.
