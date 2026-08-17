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
- `tools/analyze_frontend_segments.py`
- `data/frontend_segments.json`
- `tools/analyze_frontend_geometry.py`
- `data/frontend_geometry.json`
- `capture_frontend_wipe.ps1`
- `tools/mame_capture_frontend_wipe.lua`
- `data/frontend_geometry_cadence1.json`

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
- A second ignored raw capture exists at `.deps\mame\frontend_wipe`: 130 files
  and about 17 MB, frames 1870..1912 at cadence 1. Regenerate it with
  `capture_frontend_wipe.ps1 -Refresh`. It is a separate directory so the
  cadence-2 capture above is never cleared.
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
- SUPERSEDED for both windows by "Frontend segmentation result 2026-08-17"
  below. These two sizing bullets remain as the record of what the cadence-2
  storage experiment measured, but stored frames are no longer the intended
  representation for either window. Read that section before acting on them.
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
- `tools/analyze_frontend_segments.py`:
  `01e99fd85e6c05eba6f437b4f0aeb89d3aad090fa4f915602ccd3e0c61bc3f8b`
- `data/frontend_segments.json`:
  `67ff4e52bfa53751567ea9adf1e3b7d9c6be1cea81ce0d220575a343265b072b`
- `tools/analyze_frontend_geometry.py`:
  `358197875022ea85a17e8d0969de9b34f2151f4ef321870b9f1d507ada36604e`
- `data/frontend_geometry.json`:
  `98af6e62dea6e3e11192a683601e84a2640333c4323bde9323528707d19375d3`
- `capture_frontend_wipe.ps1`:
  `1b9d27997d38e629f76d9a8f3448706da7d7938ae5750def77e07c7ef069ca29`
- `tools/mame_capture_frontend_wipe.lua`:
  `2ac0391ee05d337ff20ca36839ec538a64d3dfabcb56ffd9834269aea06aa242`
- `data/frontend_geometry_cadence1.json`:
  `9a98eb7ad39321b797311ea474ef4fc8bbd01167d101d05ce28fc897a62f694e`

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
  `AGENTS.md` as canonical with `CLAUDE.md` as the Claude Code pointer.
  `references/workflow.md` additionally records the generalizable lessons from
  the segmentation result: inspect frames before designing a codec because a
  window may be a native composition rather than video; detect fades against
  the most colourful frame, never the first; check RLE against raw before
  assuming compression; collapse repeated frames before sizing; and read the
  state machine to find the frame that starts CDDA.
- Skill hashes: `SKILL.md`
  `f900e9feae55a807dd82fabc0f0792ae0d126c98e36fb5fcb8fc84845ccd97ee`;
  `references/workflow.md`
  `5a6cba7ae33112861b14a10c89087d78f4af7d40ba1c22d4f1e681b67f09cc59`;
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
- CORRECTION to an earlier claim in this section: CDDA does **not** start
  after the Round 1 title. `cap_confirm_character()` sets
  `world->encounter_started = 1` at character confirmation
  (`capability_model.c:659`), and `main.c:1809` starts track 2 on that flag.
  Ordering inside the confirm-entry frame is: release scene 1, load the
  49,137-byte supplements (`main.c:1610`), then start CDDA (`main.c:1809`).
  The confirm-entry frame therefore carries the **last legal data-track
  read**. Both the character-confirm animation and the Round 1 title play
  while CDDA is active, so pre-CDDA streaming is not available to them and
  every payload they need must already be resident.
- Both retired 78,848-byte blocks are already committed: block 0 holds the
  64,118-byte Stalker archive from CHARACTER_SELECT (`main.c:1595`), block 1
  holds the 49,137-byte boss supplements from CHARACTER_CONFIRM
  (`main.c:1610`). Whole-block reuse strands the 14,730- and 29,711-byte
  tails. There is no free frontend block; treat "fit it in the retired
  blocks" as unavailable unless those archives are deliberately rescheduled.
- Cadence-2 sizes are lower bounds for characterization only. Measure at
  cadence 1 before fixing any layout.
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

## Frontend segmentation result 2026-08-17

`tools/analyze_frontend_segments.py` (new) measures unique-frame transitions,
separates palette-only steps from structural steps, reports changed-pixel
bounding boxes, and greedily splits each window against a byte budget. It
writes `data/frontend_segments.json`. `tools/analyze_frontend.py` was
deliberately left untouched so its tracked report hash stays the checkpoint
anchor; the repository already uses one analyzer per investigation.

Verification of the new tool: its numpy RLE and coalesced-delta primitives
reproduce `analyze_frontend.py` byte-for-byte on `start_transition`
(strict 42,145 and coalesced 41,758, matching the tracked report). Do not
change those primitives without repeating that comparison.
`data/frontend_capture.json` still hashes `eefdf8c0...`, unchanged.

Measured at cadence 2, fitted to 352x224:

- `start_transition` 1770..1798: 15 runs over 9 distinct images, 116-colour
  union, 42,102 bytes, one segment. Fits one block. Unchanged conclusion.
- `character_confirm` 1800..2038: 47 runs over **31 distinct images**, so
  frames repeat non-consecutively and a distinct-image cache beats
  re-encoding every run. 188-colour union, 19 palette-only steps, 27
  structural steps, 103,962 bytes total, splitting into 75,115 + 34,692.
- `round_1_title` 2040..2160: 26 runs over 26 distinct images, 915-colour
  union, 506,973 bytes, peak 66,055 changed pixels in one step (84% of the
  screen). **Storage is infeasible**: a busy mid-window frame costs
  78,848 raw + ~465 palette bytes, so one frame alone exceeds one
  78,848-byte block, and its count/value RLE *expands* to ~84,500 bytes.
  Cadence 1 roughly doubles this to about 1 MB.
- The fade hypothesis was tested and **falsified**. Fades from black cannot be
  a function of a dark base frame, so the test was repeated against the most
  colourful frame in each window. That reference covers only 3/25 Round 1
  frames and 4/46 confirm frames. Neither window is a global CRAM fade; do
  not re-propose one.

Inspecting the frames explains why storage is the wrong representation:

- Frame 1800 is the four-panel character-select grid with the countdown.
  Frame 1900 shows those panels collapsing into horizontal bands. Frame 2038
  is black. The window is a **geometric panel wipe of an image that is
  already resident** in the 78,848-byte character-select surface.
- Frame 2040 is `ROUND 1 / CITY OF DESPAIR` text on black. Frame 2086 is the
  **live gameplay scene** (street, barricade, HUD, Predator, aliens) with the
  title text over it. Frame 2160 is the same scene with the text gone. The
  915-colour union is the street scene, not title art.

Architectural conclusion: neither window should ship as stored frames. Both
are native compositions of assets the runtime already holds.

- Character confirm is a VDP1 scaled-sprite or VDP2 line-scroll/window
  transform of the resident selection surface. Payload is a per-frame
  source/destination rectangle table, on the order of hundreds of bytes.
- Round 1 title is the existing native scene (reconstructed VDP2 street,
  VDP1 HUD overlays, actor archives) plus a small text overlay and a reveal.
  The runtime already renders all of it; only the text overlay and the
  reveal schedule are new.

This removes the RAM blocker rather than working around it, and it is the
only path consistent with "native SH-2 code, not stored video". The cost
moves from megabytes of pixels to a small geometry/timing table, but the
capture-exactness burden moves with it: the native transform must be proven
against a cadence-1 capture frame by frame, not asserted.

## Character-confirm wipe solved 2026-08-17

`tools/analyze_frontend_geometry.py` (new) recovers the confirm transition as
native geometry and validates it against the raw capture. It writes
`data/frontend_geometry.json`. The run raises rather than reporting a weak
result if either claim below fails, and a negative test confirms it: feeding
it the wrong static frame raises `frame 1884 is not the static frame inside
rows 40..223`.

Validated over the 13 sampled frames 1884..1908:

- The wipe is a **row shutter, not a vertical squeeze**. Every row of every
  wipe frame is byte-identical to static frame 1852 or entirely black, with
  no resampled or partially matching rows. This was visible in the capture as
  the countdown digits keeping their exact size while the panels vanish.
- The visible band closes **linearly and symmetrically**: 4 rows per source
  frame per edge about a fixed centre at row 131.5, from content rows 40..223
  to fully black. All 11 fitted top residuals are 0.
- Fitted start is source frame 1885. Cadence 2 determined this only to +/-1
  source frame, so it was confirmed by an independent cadence-1 capture; see
  the confirmation below.

### Cadence-1 confirmation

`capture_frontend_wipe.ps1` and `tools/mame_capture_frontend_wipe.lua` capture
frames 1870..1912 at cadence 1 into `.deps\mame\frontend_wipe` (130 files,
about 17 MB, ignored). The lua input schedule is byte-identical to
`tools/mame_capture_frontend.lua`, so the route matches; the script refuses to
clear `.deps\mame\frontend`, so the cadence-2 capture backing the other
reports cannot be destroyed. The report is
`data/frontend_geometry_cadence1.json`.

Both captures agree on every model parameter, from different cadences,
directories, and static reference frames:

| parameter | cadence 2 | cadence 1 |
| --- | --- | --- |
| rows per source frame per edge | 4 | 4 |
| centre row | 131.5 | 131.5 |
| content rows | 40..223 | 40..223 |
| start source frame | 1885 (+/-1) | **1885 (+/-0)** |

The cadence-1 run fits 22 moving samples with zero residuals and observes the
last held sample at 1885 itself, so the start frame is now pinned rather than
extrapolated. Resume step 4 is satisfied for the wipe.

The first cadence-1 run failed usefully: `top edge is not linear: steps
[0 x14, 4 x22]`. The window legitimately contains a held prefix, and the
fitter had assumed the whole window was moving. It now locates the static
prefix, fits only the moving samples, and cross-checks the extrapolated start
against the last held sample, requiring `0 <= start - last_held < cadence`.
That check is what makes the cadence-2 and cadence-1 results comparable
instead of coincidentally similar.

Consequences:

- The confirm wipe needs **0 bytes of stored animation**. The Saturn clips the
  already-resident 78,848-byte character-select surface to a row band, which
  a progressive blackout of the VDP2 bitmap reproduces exactly. The existing
  release of that surface at CHARACTER_CONFIRM entry (`main.c:1610`) does not
  conflict with it; resume step 3 records the verified reasoning.
- The Round 1 title text is 110x37 at (132,90) with 9 colours: 4,070 bytes
  raw, about 2,035 bytes as one 4bpp VDP1 cel. That is the only genuinely new
  frontend asset.
- The blinking `PRESS START` element at (242,2), 103x29, is already
  implemented as a fixed VDP1 overlay.

Total new payload for the whole frontend animation is therefore on the order
of 2 KB, against roughly 1 MB for the stored-frame path that was rejected.

Not yet characterized in the confirm window: the 1800..1852 selected-panel
blink (regions 32x27 at (42,61) and 86x52 at (15,54), alternating structural
and single-CRAM-entry steps) and the exact appearance schedule of the title
text and `PRESS START` blinks between 1954 and 2034. Per-step boxes for all
of them are in `data/frontend_segments.json`.

## Shutter integrated 2026-08-17

The confirm shutter is now in the runtime, not only in analysis.

- `capability_model.h` declares `CAP_CONFIRM_SHUTTER_START_TIMER` 85,
  `CAP_CONFIRM_SHUTTER_ROWS_PER_FRAME` 4, and content rows 40..223.
  `cap_confirm_shutter_band()` in `capability_model.c` returns the band for a
  confirm timer and 0 once closed. Confirm timer 0 is source frame 1800, so
  timer 85 is source frame 1885; the model's existing 240-frame confirm hold
  already aligns Round title to source 2040.
- `tests/capability_model_test.c` adds `test_capture_exact_confirm_shutter()`,
  which asserts the model against all 43 sampled bands from the cadence-1
  capture, plus centre invariance and closed-stays-closed. That table is
  evidence: if an implementation change breaks it, fix the implementation.
- `main.c` adds `apply_confirm_shutter()`, called from `draw_world()` during
  CHARACTER_CONFIRM. It blacks only the rows newly hidden since the previous
  frame, four at each edge, straight into the VDP2 bitmap. No stored frames,
  no source surface, no change to the load or CDDA schedule.

Verified so far:

- Host tests pass, including the new shutter test and the existing
  12,000-frame soak; the controller-only route still reaches Round 2 in 4,485
  frames.
- `build.ps1` normal-release and `build.ps1 -EncounterTest` both compile,
  link, and build ISOs with every required member verified by size and
  SHA-256. No new compiler warnings.
- The working disc was rebuilt as `profile=normal-release` after the
  diagnostic build, so `game.iso`/`game.cue` are not a diagnostic image.

NOT yet verified: nobody has watched the shutter run in an emulator. The next
action for this change is a Yaba Sanshiro boot to confirm the band closes
smoothly, the countdown stays legible to the end, and no VDP2 tearing or
partial-row artefact appears. Until then, describe it as built and host-tested,
not as visually confirmed.

## Resume in this order

1. Verify branch, HEAD, clean status, the release manifest profile, and that no
   emulator retained a stale cue.
2. The repository is already an independent Git repo even though it lives
   under `BrooklynBangoutX`. Relocation to `C:\Game Dev\AvPSaturnCapabilityTest`
   is optional organization work, not a technical requirement. If relocating,
   preserve `.git` plus the ignored private ROM, dependency, emulator, audio,
   and capture inputs; verify the old checkout before removing anything.
3. RESOLVED, no change needed to the existing load schedule. The wipe does not
   need the character-select source block at all, so nothing conflicts with
   releasing it at CHARACTER_CONFIRM entry. Verified in `main.c`:
   - `activate_frontend_scene()` copies the surface into the VDP2 bitmap once
     and early-returns while the scene is unchanged (`main.c:737-752`), so
     the bitmap already holds the image after the confirm-entry frame.
   - `copy_snapshot_to_background()` is row-aligned at
     `background_bitmap + y * BACKGROUND_WIDTH` (`main.c:723-735`), so hiding
     one row is exactly the `jo_dma_copy(empty_row, target,
     BACKGROUND_WIDTH)` that function already performs.
   - `sequence_scene_for_world()` has no CHARACTER_CONFIRM case
     (`main.c:779`), so it returns -1 and `activate_route_sequence()`
     early-returns without touching the bitmap during the whole wipe
     (`main.c:817`). Nothing else rewrites the bitmap until ROUND_TITLE
     selects `AVSP_SEQUENCE_ROUND_1_TITLE`, which repaints it wholesale.
   The shutter is therefore a destructive progressive blackout of the VDP2
   bitmap, which is safe because the band only ever shrinks. Cost is eight
   row DMAs per source frame (four rows at each edge) of `BACKGROUND_WIDTH`
   bytes. It uses no cartridge RAM and is outside the phase-overlay budget.
   Implement it that way rather than extending any surface lifetime.
4. DONE for the wipe: the cadence-1 capture pinned the start frame at 1885
   and reproduced every other parameter. If the wipe model is changed, re-run
   both captures and require agreement again. A frame the shutter cannot
   reproduce is evidence the model is wrong, not a reason to restore a
   stored-frame fallback.
5. Characterize the two remaining confirm elements the same way: the
   1800..1852 selected-panel blink and the 1954..2034 title-text and
   `PRESS START` schedules. Extract the 110x37 nine-colour title text as one
   4bpp VDP1 cel.
6. Implement the shutter as the progressive VDP2 bitmap blackout described in
   step 3, driven by the fitted model, and add a host-model test that walks
   the band schedule deterministically. Then compose the Round 1 title from
   the existing native scene plus that text cel and a reveal schedule.
   Integrate
   menu -> character confirm -> Round 1 and run host, focused, full-route,
   then clean normal-release gates.
7. Verify the complete first level audibly in a captured real-time run.
8. Run the normal release on physical NTSC Saturn hardware with a digital pad
   and 32 Mbit RAM cartridge; verify crop/black bars, audio, KO, and Round 2.
9. Forward-test the reusable skill and assemble the full-port team evidence
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

# Reproduce the frontend segmentation result (needs the raw capture present):
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_frontend_segments.py --report

# Capture the wipe at cadence 1 and confirm the shutter model independently.
# This never touches .deps\mame\frontend:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_frontend_wipe.ps1

# Validate the character-confirm shutter model and its geometry report:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_frontend_geometry.py --report

# Measure an ad-hoc window without touching the tracked report:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_frontend_segments.py --window probe:1800:1900

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
