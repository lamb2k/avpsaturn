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

## Integration checkpoint (2026-08-31)

All five integration tasks pass. The owner EXE was repackaged without fork
source edits as
`yabasanshiro-1.20.37-2986eb-debug-rig-mcp-d7767591`; archive SHA-256 is
`6f157f15da4d01cca9ef044d32352b8e6d3cf6b71a44ad3303aaeb9939015864`
and EXE SHA-256 is
`d77675912421a7435d02d844625a6ef68ba0e55ef17c9845f08651eb98f54b45`.
`setup_emulator.ps1` validates both identities and retains the Aug-10 package
as the explicit `Aug10` control.

Two cold runs on each executable produce identical 575-sample semantic
ledgers, canonical SHA-256
`7fae4a7cffe2c35a0df8a3c181a5ffa8f141f5b113500d67de1fd60f071a56fc`.
Two identical dynarec burst runs align at frame 2094 and capture cadence-1
frames 2095..2125. Their manifest SHA-256 is
`13afd26ef889b6f792ade52989749eeec1dc23203b5eb1def55ac85ccca31c1f`;
same-frame hashes match and the animated window has seven distinct hashes.
The invalid interpreter/dynarec mixed control is excluded because its launch
conditions were not identical.

`prepare_mcp_visual_qa.py` verifies every manifest image hash and cadence,
crops the presented aperture, and emits a lossless full-speed WebP plus a
cadence-1 contact sheet. Direct inspection passes with stable Predator
identity, P1-only HUD, coherent actor animation, both VDP2 planes, palette,
and priority. The visual artifact SHA-256 values are
`2cec2564fef8c37f315b072c5037c84f3089c6e34e0cb52d90028aa15be475a5`
and `ff3444630d8ab19fc0f86273261336015fec2b079135787d8f34d05a831e466e`.
Captured PNGs, manifests, ROMs, and ISOs remain ignored.

Capture settings were restored to VideoCore 4 and SoundCore 1. Evidence tier
remains `ONE_EMULATOR`; the SCU-DMA A-bus rule remains physical-tier-only and
physical Saturn remains `UNRUN`.

## Owner delivery 2 (2026-09-01): save_state and the validated pre-roll flow

The debug-rig fork adds one MCP tool, `save_state {slot}`: writes
`<itemnum>_<slot>.yss` to the configured SaveStates directory (pauses around
the save, resumes only if it was running) and returns the file path, size,
SHA-256, and emulated frame count. Rebuilt EXE:
`C:\ybexact\build-qt-route2\src\qt\yabasanshiro.exe`, SHA-256
`da2ffb341532f10808d8f9659c875a96cbc29ebc10a454426415059c7cef8746`.
Source delta refreshed at `C:\ybexact\fork-delta-vs-aug10-snapshot.patch`
(16 files; the only new delta is DebugMcpServer.cpp - emulation core
untouched).

This is the pre-roll primitive for the recorded frame-574 visual-lane
blocker. Owner-validated flow on a private copy of the current native
`game.iso` + `stage1_audio.wav`:

1. Pre-roll leg, dynarec `Advanced\SH2Interpreter=3`: set `autostart=true`
   (one-shot - it must be re-set before every launch), free-run to the
   window edge, `pause`, `save_state {slot}`. Kill the process.
2. Capture legs, interpreter `Advanced\SH2Interpreter=0` (core id 0 in this
   build; id 1 is the debug interpreter and id 2 does not exist - it fails
   init): one fresh process per leg, `pause`, `load_state {slot}`,
   `framebuffer_burst`.

Owner validation evidence: state saved at dynarec frame 2005; two
independent interpreter processes loading that slot produced byte-identical
12-row burst manifests including row 1, with seven unique hashes in an
animating window. Within-process repeat loads under dynarec are NOT
deterministic (warm translation-cache residue) - always capture from a
fresh interpreter process, never re-load inside a session that has run.

Semantics to respect:
- The emulated frame counter is a session counter, not part of the saved
  state: after `load_state` it restarts near 1, so burst manifests are
  load-relative. Paired legs get identical numbering; align row-for-row.
- The first presented frames after a load can differ from the pre-save
  presented imagery (the VDP1 framebuffer is not in a savestate). Cross-leg
  identity held from row 1 in validation; against pre-save imagery, exclude
  the first 4 rows (mirrors breakpoint_resume_preroll_excluded).

Integration tasks, in order: (1) repackage this EXE in the pinned layout and
pin it as the new debug-rig identity, keeping Aug-10 and d7767591 as
explicit controls; (2) rerun negative controls A/B on the new EXE; (3) add a
savestate negative control repeating the two-leg identity check above;
(4) rebuild the blocked native visual gate on this flow: dynarec pre-roll
past the frame-574 point, save, then paired fresh-interpreter legs bursting
the transition window. Evidence tier stays ONE_EMULATOR; capture hygiene
(VideoCore=1/SoundCore=0 for capture, restore 4/1, re-set the pinned
SH2Interpreter=3 after interpreter legs, kill stray processes, commit no
captures or states) is unchanged. Savestate .yss files are capture
artifacts: never commit them.

## Owner delivery 2 integration checkpoint (2026-09-01)

Tasks 1-3 pass. The owner EXE is repackaged without fork-source edits as
`yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34`; archive SHA-256 is
`0d6b44afae0f99a76f5ba3090a3ce307137c9fc305ffa67d0c0a04bf040dd34b`
and EXE SHA-256 is
`da2ffb341532f10808d8f9659c875a96cbc29ebc10a454426415059c7cef8746`.
The Aug-10 and d7767591 packages remain explicit controls.

Two cold new-rig runs and both explicit control runs reproduce all 575
semantic samples. The new-rig sample SHA-256 is
`1a6a8c39e83ae29ed1ab2c00e2ce735a281445e4b31bb89b7402fec2767f2f59`
and its canonical semantic SHA-256 is
`179120458393d519a5c3896de6c43ac9a99024f63d579c107c60ad64d5c68798`.
Two cold framebuffer legs align at emulator frame 2050; frames 2051..2081
match row-for-row at canonical sequence SHA-256
`6d64c5aea1e3666d5dae9515bef9a08ec49169702474697d4ca55d12661e75e0`
and contain nine distinct hashes.

The savestate control saves dynarec slot 8 at diagnostic frame 200 / emulator
frame 1950. The 10,381,254-byte state SHA-256 is
`24fee31d69f4606ce8a364199b8599019411680f68ce0378c94a64e487f1eb93`.
Two fresh interpreter processes load it once and produce identical
load-relative frames 1..12, including row 1, at manifest SHA-256
`ec0aebb185f673ee4be3fb4505ac207472e715266fb4f5440ab0f38cbc3e5979`.

Task 4 remains BLOCKED after its bounded three-attempt pass. The first attempt
exposed and corrected the helper's hidden 30-second HTTP ceiling. The unchanged
native image then failed to reach diagnostic target 3470 within 300 seconds
and target 3400 within 600 seconds, so no transition savestate or visual
acceptance was produced. Do not retry this body without an owner-ruling change
to the capture boundary. Normal settings are restored to VideoCore 4,
SoundCore 1 and SH2Interpreter 3; no emulator process remains. Captures and
states remain ignored, evidence stays ONE_EMULATOR, and physical Saturn stays
UNRUN.
