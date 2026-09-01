# Headless MCP frame capture: integration handoff

The owner has rebuilt the Yaba Sanshiro debug-rig fork with two new MCP
tools and smoke-tested them end-to-end against the current Round 1 build.
This document is the integration contract; the standing owner hold on
modifying the emulator fork remains for everything except the tasks below.

## What the owner delivered

- Rebuilt Qt EXE: `C:\ybexact\build-qt-route2\src\qt\yabasanshiro.exe`,
  SHA-256 `d77675912421a7435d02d844625a6ef68ba0e55ef17c9845f08651eb98f54b45`.
- Complete source delta vs the deployed-EXE snapshot
  (`C:\ybexact-apply-check\yabasanshiro-1.20.37`, the exact tree that built
  the pinned Aug-10 EXE): `C:\ybexact\fork-delta-vs-aug10-snapshot.patch`
  (13 files). Emulation core is semantically identical to the pinned build
  (the only core-file delta is blank lines in `yabause.c`); all other
  changes are qt/UI-side compatibility work plus the two tools.
- New MCP tools on the existing `http://127.0.0.1:9640/mcp` endpoint:
  - `framebuffer_screenshot {path}`: PNG of the presented frame, returns
    frame count, MSH2 PC, image size, file SHA-256. Works running or paused.
  - `framebuffer_burst {directory, frames, prefix?}`: requires `pause`
    first; advances exactly one frame at a time through the emulator's own
    paint-pump frame step, captures each presented frame, writes
    `manifest.tsv` (frame/file/sha256) and returns its SHA-256.
- Smoke evidence (owner-run): 12-anchor sweep across frames 951-6441 of the
  current Round 1 ISO; bursts are frame-exact and track scene animation
  (unique-hash counts rise exactly in the pan/combat windows, and the still
  intro and stalled tail hash identically).

## Build configuration facts the packaging must respect

- SH2 core: devMiyax dynarec ON (`YAB_WANT_DYNAREC_DEVMIYAX=ON`), matching
  the rig's pinned `Advanced\SH2Interpreter=3`.
- Video: GL only. The Vulkan core is not in this build (its shaderc/glfw
  dependencies no longer exist on the machine). MCP-capture runs must set
  `Video\VideoCore=1` in `%APPDATA%\YabaSanshiro\yabause.ini` and restore
  `4` afterward; the pinned-oracle configuration is otherwise untouched.
- Sound: SDL2 development files are gone; use `Sound\SoundCore=0` for
  capture runs (restore `1`). SCSP emulation semantics are unaffected.
- Qt runtime: the EXE links Qt 6.8.3
  (`AvPSaturnCapabilityTest-ClaudePriorityArchitecture\.deps\qt-6.8.3-msvc2022`);
  package with `windeployqt --release --force` from that kit (the pinned
  package's 6.8.0 DLLs are too old and windeployqt skips them without
  `--force`).

## Integration tasks (in order)

1. Package the rebuilt EXE in the pinned-package layout and re-pin: record
   archive and EXE SHA-256 in `setup_emulator.ps1` and the source ledger as
   the debug-rig build, distinct from the Aug-10 pin.
2. Negative control A: two cold pinned-route runs on the new EXE produce
   byte-identical semantic ledgers, and those ledgers match the Aug-10 EXE's.
3. Negative control B: same-frame burst image hashes identical across two
   cold runs; a burst in an animated window (e.g. frames 1900-2000) must
   show differing per-frame hashes.
4. Add an MCP capture mode to the visual-QA scripts producing cadence-1
   contact sheets from `framebuffer_burst` manifests; WGC stays reserved
   for USER-facing packages.
5. Evidence tier stays ONE_EMULATOR. The SCU DMA A-bus rule stays
   physical-tier-only. Do not modify the fork source beyond re-packaging;
   restoring the Vulkan video core (shaderc + glfw network fetch,
   `YAB_WANT_VULKAN=ON`) is a separate owner-approved task.

## Traps encountered (do not rediscover)

- `pause` parks the SCSP worker via `ScspMuteAudio` -> `g_scsp_lock`; any
  frame execution while paused must `ScspUnMuteAudio` first or
  `SyncCPUtoSCSP` deadlocks the UI thread. The frame-step in
  `YabauseThread::requestFrameStep()` handles this.
- The GL widget's paint loop is the emulation driver; never call
  `YabauseExec()` from a marshalled MCP handler.
- The qt CMake target's post-build windeployqt step fails under NMake
  (multi-config path assumption) after a successful link; ignore it, and
  place the three libchdr libs into `Release\` subdirs before linking.
