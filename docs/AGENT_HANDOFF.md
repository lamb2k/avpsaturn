# Agent handoff: AvP Saturn capability test

Updated: 2026-08-17 08:28 EDT

Read this file before taking any action. The user wants a private, capture-faithful, native Sega Saturn port of CPS2 Alien vs Predator, beginning at the main menu and continuing through the complete first level into Round 2. Do not reframe success as an emulator, approximate demo, host-only simulation, or focused animation viewer.

## Repository state

- Repository: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Branch: `prototype/private-capability-test`
- HEAD: this committed handoff (`Add restart-safe Saturn port handoff`; run `git rev-parse HEAD` for its immutable checkout hash). The dirty KO implementation is based on prior commit `ae4fe35f6b809a6ce4b529a6ebfe0d3cf0e2de84` (`Add capture-exact Chrysalis hit reaction`).
- Worktree: intentionally dirty with the uncommitted capture-exact Chrysalis KO slice listed below.
- Current disc profile: `encounter-test`, not normal release.
- Current ISO: 5,410,816 bytes, SHA-256 `6cec92ca093308c081dcbbe156e3e5e62049cbedddb2830818e33aba039778e8`.
- Current cue SHA-256: `bfc58c7020d90952e93bef7ecba32dea8d4faddf6ce6a90e1054206ee1807b12`.
- Emulator processes were closed before this checkpoint. Start fresh with `run.ps1` and verify the process command line.

Modified tracked files:

- `build.ps1`
- `capability_model.c`
- `main.c`
- `makefile`
- `prepare_avsp_port.ps1`
- `tests/capability_model_test.c`
- `tools/extract_avspu_stage1.py`

New untracked source/evidence files:

- `capture_boss_ko.ps1`
- `data/boss_ko_capture.json`
- `tools/analyze_boss_ko.py`
- `tools/mame_capture_boss_ko.lua`

Do not discard these changes. `git diff --check` passes; only existing LF-to-CRLF warnings are emitted.

## What the KO slice contains

- A separate deterministic capture loaded from verified state `avspu_stage1_boss_12660`.
- Natural lethal impact at CPS2 source frame 13491, reducing Chrysalis health 3 to 0.
- Exact KO visual interval 13492 through 13919 inclusive: 428 frames.
- 24 exact object poses and 36 pose runs, palette bank 27 throughout.
- Temporal unwrapping of both CPS2 10-bit X and Y coordinates.
- Maximum unwrapped composite 240x112, inside the declared 288x192 Saturn canvas.
- Exact per-frame pivot trajectory in generated signed-short X/Y arrays.
- New `/SPR4/BKO.RLE`: 43,232 bytes, SHA-256 `9ad615f5e61615142d5be3b91a10fd16e9519ff304d204da704f9fe6e609f78a`.
- Eight archive poses are new after deduplication against the base and hit archives.
- Boss clips now total six: 1, 44, 106, 189, 40, and 428 frames.
- Production timing keeps the boss in KO through all 428 source frames, holds the corpse 60 more frames, aligns boss-defeat timer 0 to source 13920, boss-clear audio to 14070, and Stage Clear to 14160.
- A `-BossKoTest` build profile repeats the KO. Its diagnostic-only final-frame hold makes corpse inspection easier and does not change normal-release timing.

## Verified evidence

- Host capability tests pass.
- Controller-only route reaches the Round 2 boundary in 4,485 native model frames.
- Deterministic 12,000-frame soak passes.
- `-BossKoTest` compiles and builds a Saturn ISO.
- Focused ISO verifies `BACT.RLE`, `BHIT.RLE`, `BKO.RLE`, `SACT.RLE`, and all event PCM members byte-for-byte by SHA-256.
- A clean Yaba Sanshiro launch from the exact AvP temporary absolute-path cue renders the capture-derived Chrysalis KO launch, airborne tumble, changing poses, and final low corpse pose without an asset error.
- `run.ps1` avoids Yaba 1.20.37 stale relative-cue state by generating `%TEMP%\AvPSaturnCapabilityTest\game.yaba.cue` with absolute ISO/WAV paths. Still inspect the command line and screen; unrelated stale emulator instances have existed.

## Current blocker: full-route allocation

The full `-EncounterTest` build compiles, packages, and passes host tests, but the exact disc fails on Saturn runtime startup with:

```text
>>> Jo Engine error handler <<<
Dynamic memory usage: 99%
In jo_fs_read_file_ptr():
BKO.RLE: Out of memory
```

This failure was visually confirmed in Yaba Sanshiro on the current encounter-test ISO. The focused KO profile succeeds only because its working set is smaller. Therefore the KO slice is not yet proven in the complete first-level route and must not be committed as hardware-ready.

The current manifest says both `BHIT.RLE` (5,900 bytes) and `BKO.RLE` (43,232 bytes) load in `retired-character-select-before-cdda`. The earlier estimate that their 49,132-byte compressed total fits the retired 78,848-byte character-select block did not account for allocator overhead/current live allocations. Inspect actual allocation lifetimes, not only file sizes.

## Resume in this order

1. Inspect the allocation code around `load_boss_supplement_archives`, frontend-surface retirement, sequence surfaces, PCM buffers, and Jo Engine heap zones. Reproduce the failure with the exact current `-EncounterTest` build before editing.
2. Fix the full-route working set without adding an unmeasured CD data seek during active CDDA. Preferred directions to evaluate:
   - retire or relocate another no-longer-needed frontend/sequence allocation before loading BKO;
   - place BKO in a separately managed expansion-RAM bank rather than the congested general allocator;
   - reduce archive/allocator overhead only through lossless pose/archive packing;
   - phase-load BKO before CDDA only after proving a safe retired block large enough for both supplements.
3. Rebuild `-EncounterTest`, boot it, and visually verify the route passes the former BKO load point, reaches Chrysalis, plays the complete KO, then shows boss defeat, Stage Clear, results, and Round 2.
4. Update `README.md`, `docs/ARCHITECTURE.md`, `docs/HARDWARE_TEST.md`, and `docs/TEST_PLAN.md` with the capture/timing/archive evidence and remove only limitations that are actually proven resolved.
5. Build without diagnostic switches. Require host tests, 12,000-frame soak, exact ISO-member hashes, `profile=normal-release`, and a clean title/menu boot from `run.ps1`.
6. Review `git diff --check`, inspect all generated/capture changes, and commit the coherent slice, suggested message: `Add capture-exact Chrysalis KO sequence`.
7. Keep physical Saturn validation, the reusable-skill forward test, and the full-port team evidence package pending.

## Reproduction commands

From the repository root in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -BossKoTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -EncounterTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1

# Final build only after the full-route allocation issue is fixed:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

The build scripts locate their bundled Python/MAME/Jo Engine dependencies; do not assume `python` is on PATH. A bundled Python is also available at `C:\Users\lambd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

## Remaining product-level work

- Fix and verify the full-route BKO memory allocation.
- Verify the complete first level visually and audibly in the emulator, not only through host state transitions.
- Rebuild/boot normal release.
- Run the documented route on physical NTSC Saturn hardware with a digital controller and 32 Mbit RAM cartridge.
- Continue remaining fidelity gaps after the KO slice: exact Chrysalis action-selection AI, palette/explosion/victory details, remaining nonlethal Stalker reaction fidelity, and any route/intermediate details still listed in `docs/TEST_PLAN.md`.
- Once a faithful full slice passes, forward-test and refine the private skill at `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn`.
- Assemble the full-port evidence package for the development team before proposing anything beyond private use.
