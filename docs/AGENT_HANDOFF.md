# Agent handoff: AvP Saturn capability test

Updated: 2026-08-17 09:20 EDT

Read this file before taking any action. The user wants a private, capture-faithful, native Sega Saturn port of CPS2 Alien vs Predator, beginning at the main menu and continuing through the complete first level into Round 2. Do not reframe success as an emulator, approximate demo, host-only simulation, or focused animation viewer.

## Repository state

- Repository: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Branch: `prototype/private-capability-test`
- HEAD: the commit containing this handoff adds the Claude bootstrap pointer
  and the 2026-08-17 plan review on top of `14493fa` (`Add repository agent
  instructions`), which follows the deterministic frontend capture/analyzer
  checkpoint `2e61198`. Run `git rev-parse HEAD` for the immutable hash.
- Worktree should be clean immediately after the handoff commit. Verify with
  `git status --short --branch` before resuming.
- Current disc profile: `normal-release`.
- Current ISO: 5,400,576 bytes, SHA-256 `4296b66ec63276524c588b27a786d596e2d4404c747e57fe513806655f4000f6`.
- Current cue SHA-256: `bfc58c7020d90952e93bef7ecba32dea8d4faddf6ce6a90e1054206ee1807b12`.
- Emulator processes were closed before this checkpoint. Start fresh with `run.ps1` and verify the process command line.

Implementation and documentation files in this checkpoint:

- `AGENTS.md`
- `build.ps1`
- `capability_model.c`
- `main.c`
- `makefile`
- `prepare_avsp_port.ps1`
- `tests/capability_model_test.c`
- `tools/extract_avspu_stage1.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/HARDWARE_TEST.md`
- `docs/TEST_PLAN.md`
- `docs/AGENT_HANDOFF.md`
- `CLAUDE.md`

New tracked source/evidence files:

- `capture_boss_ko.ps1`
- `data/boss_ko_capture.json`
- `tools/analyze_boss_ko.py`
- `tools/mame_capture_boss_ko.lua`
- `capture_frontend.ps1`
- `data/frontend_capture.json`
- `tools/analyze_frontend.py`
- `tools/mame_capture_frontend.lua`

`git diff --check` passes; only existing LF-to-CRLF warnings are emitted.

## Agent bootstrap files

- `AGENTS.md` (added in `14493fa`) is the canonical, harness-neutral
  repository instruction file. `CLAUDE.md` is a thin tracked pointer for
  Claude Code sessions, which auto-load `CLAUDE.md`; keep `AGENTS.md`
  canonical and `CLAUDE.md` minimal so they cannot diverge.
- Agent sessions may start in the parent workspace
  `C:\Game Dev\BrooklynBangoutX`, a separate non-Git project workspace for the
  unrelated Brooklyn Bang Out game. An untracked `CLAUDE.md` there maps the
  workspace and routes agents into this repository; recreate it from this
  section if it is lost.
- The reusable skill is canonical at
  `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn` and reaches Claude
  Code through the machine-local directory junction
  `C:\Users\lambd\.claude\skills\port-cps2-to-sega-saturn` (recreate with
  `New-Item -ItemType Junction` after a profile reset; it is tracked
  nowhere).
- Where `AGENTS.md` says `apply_patch`, Claude Code sessions use their
  Edit/Write tools with the same preserve-unrelated-work discipline.

## Active frontend-fidelity checkpoint

This is evidence and sizing work only. It is not integrated into the Saturn
runtime yet, and it must not be described as a finished exact frontend.

- `capture_frontend.ps1` audits the private `avspu` ROM set with MAME 0.289,
  reuses or regenerates the raw capture, and runs the analyzer with bundled
  Python.
- The deterministic input route mirrors `tools/mame_capture_stage1.lua`.
- Raw samples cover CPS2 frames 1320 through 2160 inclusive at cadence 2: 421
  samples, 241 unique full frames, and 292 pose runs.
- Raw capture files are intentionally ignored under
  `.deps\mame\frontend`: 1,264 files and 170,685,151 bytes at this checkpoint.
  Regenerate them with `capture_frontend.ps1 -Refresh`; do not add ROMs or raw
  captures to Git.
- Tracked report `data/frontend_capture.json` SHA-256 is
  `eefdf8c0d9be6da796e9b61c52d8e89f7a4890d6380978b97543781037175f3f`.
- Full independent-palette RLE would be 15,528,546 bytes and is rejected.
- Start transition, frames 1770..1798: 15 samples, 9 unique frames, 116-color
  union, 41,758-byte coalesced stable-palette delta. This fits one retired
  78,848-byte frontend allocation.
- Character confirmation, frames 1800..2038: 120 samples, 31 unique frames,
  188-color union, 137,715-byte coalesced stable-palette delta. It does not fit
  one retired frontend allocation. The RGB-to-first-palette-pen experiment is
  worse at 208,630 bytes and is not exact because duplicate palette colors make
  reverse pen identity ambiguous.
- Round 1 title, frames 2040..2160, has a 915-color union and still needs
  segmentation into stable layers, palette fades, and changed regions.
- MAME's CPS2 final screen bitmap is RGB32 here. The captured
  `pixels_####.bin` files are 384x224x4 final colors, not native stable palette
  indices.
- Cadence 2 is exploratory for storage characterization. Recapture the chosen
  representation at cadence 1 before calling it capture-exact.
- No runtime, generated Saturn archive, ISO, or release-manifest content was
  changed by this frontend checkpoint.

Deterministic source hashes:

- `capture_frontend.ps1`: `ad12c2a33c4d5838cdebc0d60ae16b4a1fd003454bd4305334de2b85eb5cb1c6`
- `tools/mame_capture_frontend.lua`: `59c8c6c53e9f3bc994fad9d6b55ebe3f78097390b1b6208c2b0c74155f951568`
- `tools/analyze_frontend.py`: `e7cf211482ae9c4521fc9a31c4d89e05efc4d3f3b5c4eb8f379dcd1b07bc3ddf`

## Process and restart state

- No MAME, Yaba Sanshiro, Mednafen, or RetroArch process was running at the
  checkpoint. No capture/build command is partially active.
- The latest normal-release ISO/cue remains the verified release listed above;
  the frontend analyzer did not rebuild or overwrite it.
- A reuse-only run of `capture_frontend.ps1` passed the ROM audit, reproduced
  every report total, and reproduced the report SHA-256 exactly.
- `tools/analyze_frontend.py` passes `py_compile`; the Pillow 14 deprecation was
  removed with a compatible fallback.
- An ignored accidental directory exists at
  `.deps\mame\.deps\mame\frontend` (421 files, 6,424,401 bytes) from an earlier
  relative snapshot path. It is not used. It may be removed later only after
  resolving and checking that exact absolute path.
- The reusable skill at
  `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn` records RGB32
  frontend-capture limits, cadence-1 release gating, full-screen crop checks,
  and whole-block allocator alignment rules. Its start step now names
  `AGENTS.md` as canonical with `CLAUDE.md` as the Claude Code pointer; that
  one-line prose edit is the only 2026-08-17 09:20 skill change.
- Skill hashes: `SKILL.md`
  `f900e9feae55a807dd82fabc0f0792ae0d126c98e36fb5fcb8fc84845ccd97ee`;
  `references/workflow.md`
  `6472d8c4c466addee790ee16acdfba4e201c066b97316252f118aaf2dfe580e0`;
  `agents/openai.yaml`
  `038134e6c419dc5654b404dac81317a21900e342e208841f44cd959b837c7e2b`.

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

## Full-route allocation resolution

The original `-EncounterTest` failure was reproduced exactly:

```text
BKO.RLE: Out of memory
```

Root cause: Jo Engine reuses but does not split a freed allocation. Loading the
5,900-byte hit archive first consumed the complete retired 78,848-byte
character-select block, so the second allocation could not use its apparent
tail. `load_boss_supplement_archives()` now makes one 49,137-byte allocation
and reads both files into fixed subranges before CDDA begins. The BKO subrange
starts at four-byte-aligned offset 5,904; the first unaligned attempt reached
the boss but correctly exposed `BOSS ACTION RLE` during KO decoding.

The aligned build passes both failures. In Yaba Sanshiro, the exact
`-EncounterTest` disc entered Stage 1, reached Chrysalis with Stalker adds,
rendered the changing 428-frame KO tumble, and arrived at the visible `ROUND 2
WAR IN THE UNDERPASS` card without an allocation, archive, RLE, palette, or
VDP1 error. Host tests still reach Round 2 in 4,485 frames and the 12,000-frame
deterministic soak passes.

## Plan review 2026-08-17

An independent feasibility pass checked the frontend plan against the tracked
report, `main.c`, and `docs/ARCHITECTURE.md`. The architecture holds; these
findings bound the remaining design:

- Representability is guaranteed. No captured frame exceeds 174 colours
  (report `maximum_colours_in_one_frame`), so every frontend frame fits one
  256-colour VDP2 palette. The 915-colour Round 1 union only forbids one
  whole-window stable palette, not per-segment palettes.
- CPS2 pen identity is not required for the frontend. The VDP2 route-still
  path is output-lossless: any consistent per-segment index assignment that
  reproduces exact final RGB is exact. The RGB32 capture limitation blocks
  pen-native claims only; do not spend more effort reversing pens here.
- Palette fades should be detected as colour bijections between adjacent
  unique frames: the index image stays constant and only CRAM entries change,
  so a fade step costs a palette update instead of a pixel delta. The
  analyzer cannot measure this yet.
- Residency deadlines from `main.c`: the title block is retired and the
  Stalker archive loads at CHARACTER_SELECT entry (`main.c:1595`); the
  character-select block is retired and the 49,137-byte supplement
  allocation loads at CHARACTER_CONFIRM entry (`main.c:1610`); CDDA track 2
  starts only at the first `world.encounter_started` frame (`main.c:1809`),
  after the Round 1 title. Every frontend animation therefore plays before
  CDDA, and data-track reads stay legal through the whole frontend.
- The two 78,848-byte blocks can be time-shared inside that window: play the
  41,758-byte start transition from the retired title block, free it, then
  stage confirm and Round 1 segments across one or both blocks. SACT and the
  supplements only need to be resident before `encounter_started`, so their
  load anchors may move later inside the pre-CDDA window. Whole-block reuse
  still applies: one allocation per block lifetime, four-byte-aligned
  subranges inside combined allocations.
- If cadence-1 payloads exceed the 157,696 bytes of both blocks, fall back to
  sequential pre-CDDA streaming: play the resident segment from one block
  while the next loads into the other. A 78,848-byte load costs roughly 16 to
  20 frames of CD time against a 240-frame confirm hold and 121-frame title
  window, so slack is ample; schedule loads on hold frames to avoid visible
  hitches.
- Cadence-2 sizes are lower bounds for characterization only. The 31 unique
  confirm frames came from 120 samples; cadence 1 can at most double unique
  frames and will raise delta totals. Measure at cadence 1 before fixing the
  block layout.
- CRAM fade updates must land in vblank. The scene path already rewrites the
  shared 256-colour bank per state change; reuse it and verify per-frame
  update size against the vblank budget on hardware, not only Yaba Sanshiro.
- Memory arithmetic from documented payloads: player archive 417,488, alien
  archive 131,552, boss base 119,868, Stalker archive 64,118, supplements
  49,137, resident event PCM 2,095,772, withdrawal 396,708 until its
  barricade release into the 221,184-byte decode pool, plus thirteen route
  stills, two 78,848-byte frontend surfaces, and the 78,848-byte decode
  buffer, against 4 MiB cartridge plus work RAM. The budget closes only
  because of phase overlays. New frontend animation payloads are compatible
  if they live in the retired-block/overlay regime; never move them into the
  cold-boot working set, which already exhausted the bounded startup heap
  once in Yaba Sanshiro.

## Resume in this order

1. Verify branch, HEAD, clean status, the release manifest profile, and that no
   emulator retained a stale cue.
2. The repository is already an independent Git repo even though it lives
   under `BrooklynBangoutX`. Relocation to `C:\Game Dev\AvPSaturnCapabilityTest`
   is optional organization work, not a technical requirement. If relocating,
   preserve `.git` plus the ignored private ROM, dependency, emulator, audio,
   and capture inputs; verify the old checkout before removing anything.
3. Extend `tools/analyze_frontend.py` first: parameterize the hardcoded
   `windows` tuple for subsegment ranges and add adjacent-unique-frame colour
   bijection (fade) detection, then inspect character-confirm frames 1800,
   1840, 1880, 1920, 1960, 2000, and 2038 and Round 1 title subsegments.
   Regenerating the report with new windows legitimately changes
   `data/frontend_capture.json`; re-record its SHA-256 here. Do not use the
   ambiguous reverse-pen experiment as source truth.
4. Choose the lossless representation per the 2026-08-17 plan review:
   per-segment index spaces, CRAM-delta fades, coalesced pixel deltas for
   structural changes. Fit payloads into the two 78,848-byte retired frontend
   blocks by time-sharing them inside the pre-CDDA window, moving the Stalker
   and boss-supplement load anchors later if they collide, or fall back to
   sequential pre-CDDA segment streaming. Keep whole-block allocation and
   four-byte alignment rules.
5. Recapture the accepted frontend segments at cadence 1, generate archives
   deterministically, integrate menu -> character confirm -> Round 1, and run
   host, focused, full-route, then clean normal-release gates.
6. Verify the complete first level audibly in a captured real-time run.
7. Run the normal release on physical NTSC Saturn hardware with a digital pad
   and 32 Mbit RAM cartridge; verify crop/black bars, audio, KO, and Round 2.
8. Forward-test the reusable skill and assemble the full-port team evidence
   package only after the faithful hardware slice passes.

## Reproduction commands

From the repository root in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -BossKoTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -EncounterTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1

# Reuse the raw frontend capture and reproduce the tracked report:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_frontend.ps1

# Regenerate the ignored raw frontend capture from verified MAME/ROM inputs:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_frontend.ps1 -Refresh

# Final clean release only after full-route changes pass:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Clean -Release
```

The build scripts locate their bundled Python/MAME/Jo Engine dependencies; do not assume `python` is on PATH. A bundled Python is also available at `C:\Users\lambd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

## Remaining product-level work

- Verify the complete first level audibly in a captured real-time emulator run;
  visual full-route completion is proven, while this pass did not independently
  record every intermediate sound cue.
- Run the documented route on physical NTSC Saturn hardware with a digital controller and 32 Mbit RAM cartridge.
- Continue remaining fidelity gaps after the KO slice: exact Chrysalis action-selection AI, palette/explosion/victory details, remaining nonlethal Stalker reaction fidelity, and any route/intermediate details still listed in `docs/TEST_PLAN.md`.
- Once a faithful full slice passes, forward-test and refine the private skill at `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn`.
- Assemble the full-port evidence package for the development team before proposing anything beyond private use.
