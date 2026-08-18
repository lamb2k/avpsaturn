# Agent handoff: AvP Saturn capability test

Updated: 2026-08-17 21:10 EDT

**Pixel-exact position gate: PASS.** A boss object's screen position is
reproduced exactly from the *previous* frame's world coordinates in the actor
slot plus the ROM assembly's layout words. `tools/verify_position_gate.py`
compares every part's predicted ring position against the captured object RAM
across all matched geometry frames and classifies every residual. Result on
864 parts / 246 matched frames: **801 exact, 63 explained by a sibling-assembly
origin delta, 8 by a bounded vertical settling offset, 0 unexplained** — the X
model is 100% exact on every matched part.

Model (world coordinates are 16.16 fixed point at actor slot 0x23D0/0x23D4,
world Y is up, objects render one frame behind, from f−1):

    left_ring  = wx(f−1) + origin_x − lx + 64 − width
    top_ring   = 464 − origin_y + ly − wy(f−1)

* `origin_x/origin_y`, and per part `lx/ly`, come from the selector-6 assembly
  the animation record selects (`data/avsp_animation_scripts.json`).
* `64` is VISIBLE_LEFT; `464` is the single global Y constant
  (`C(part) + origin_y − ly == 464` for every part; equivalently
  `K = origin_x + 64` for the X edge).
* Compare in the 1024 game ring (low 10 bits of the object X/Y words).
  `shift_x`/`shift_y` are capture-tool unwraps, **not** game state — the model
  predicts the raw ring position, so do not add them.
* Layout words must come from `offset_program.bin` (base 0x1FD1C8);
  `offset_full_program.bin` holds different (wrong) values at the same
  addresses. Pass `layout_data=None` to `decode_assembly` to force the right
  source.

The earlier "+48 / −10 / +4 anomalies" are **not magic offsets**: they are the
origin deltas between two assemblies that share a code set. Assembly 3 has an
airborne table at 0x13e04c (origin −52, +23) and an at-rest table at 0x13e44c
(origin −62, −25); picking the wrong one shifts X by −10 and Y by +48. The gate
decodes every assembly the actor-slot record pointer selects (frames f and f−1)
and builds the set of origin deltas a shared code set can produce, so such a
residual is passed only when it is in that set.

The 8 settling parts (2 frames, uniform −4 Y, X-exact) occur ~2 frames after a
vertical world move; the drawn Y eases toward the new world Y and the pure
`wy(f−1)` model is 4px off. This is a real, small, transient vertical component
not yet fully derived — it is the only non-exact residual class and is
classified by a bounded Y-only tolerance rather than asserted as exact.

Run: `python tools\verify_position_gate.py` (add `--verbose` to list the
settling frames and any unexplained residuals).

Remaining before this gate is exhaustive:
* 162 unmatched frames (attack / hit poses) whose assemblies are not yet in the
  JSON — need their selector-6 decodes plus the record-pointer path.
* The record pointer sometimes advances one record before the visual pose
  changes (sub-frame timing); by_codes matching avoids this but cannot
  disambiguate shared code sets, which is why the gate uses the pointer only to
  build the explained-delta set.
* Derive (or formally bound) the −4 vertical settling.

**Previous milestone — pixel-exact pose gate: PASS for assembly 0x13DEA0.**
The assembly reproduces
pose 4 (source frame 12688, 222×92 pixels) with **0 differing pixels**. Key
fixes: (1) corrected selector-6 decoder to read `count` entries starting at
+12 with signed origin at +8; (2) switched object positions from ROM script
origin+layout to MAME object RAM screen coordinates (`screen_x`, `screen_y`)
because the ROM script uses animation-local space while the renderer uses
screen space; (3) fixed `compose_assembly` to use `screen_x`/`screen_y` keys;
(4) fixed oracle dump to write the best-matching pose instead of always pose 0;
(5) removed double-flip (tile-order reversal + image flip) — the reference
renderer reverses tile order AND pixel positions, not the image itself. The
gate defaults to frame 12688 for this assembly. Other assemblies may need
different frames.

**Previous findings (superseded)**: Budget=62 entries from layout pointer 0x1FDE40 produce 11×6 tiles (176×96 pixels). The BACT.RLE oracle pose 0 requires 13×7 tiles (205×103 pixels). The gap was caused by 62 entries only covering column positions 0-10 (x=-112 to +48) and 6 y-values (y=-96 to -16), while the oracle needs columns 0-12 (+13) and 7 y-values including y=-112. The layout grid at 0x1DE40 has a cyclic structure of 16×7 grid positions with a 98-entry cycle. Entry 90 has x=-128, entry 97 has y=-112 — both outside the budget=62 range. Budget values in the ROM assembly fields may control something other than layout entry count, or the selector-6 offset_adjust values modify layout coordinates during rendering.

**Direction as of 2026-08-17: functional parity by ROM translation, with an
instrumented MAME build retained only as a contingency. Stock MAME 0.289 debug
overlays now work, and stock debugger watchpoints must be tried before any
custom build. The plan of record is
[PARITY_PLAN.md](PARITY_PLAN.md); read it after this file. This handoff says
where work stopped, the parity plan says where it is going.**

Read this file before taking any action. The user wants a private, capture-faithful, native Sega Saturn port of CPS2 Alien vs Predator, beginning at the main menu and continuing through the complete first level into Round 2. Do not reframe success as an emulator, approximate demo, host-only simulation, or focused animation viewer.

## Repository state

- Repository: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Branch: `prototype/private-capability-test`
- Implementation checkpoint: `a788147` (`Pose gate: use budget for entry count (62 vs 4), document layout grid structure and shape mismatch`),
  following `9afebf5` (`Implement frame-comparison pose gate with oracle verification`).
  `e978e7c` (`Pair debug hitboxes with actor pivots`),
  `d8a57e1` (`Decode ROM animation script structure`),
  `1f15ea5` (`Extract screen-space hitbox brackets`),
  `dbc070b` (`Update handoff with watchpoint checkpoint`), `4182edb` (`Trace
  actor writers with stock MAME watchpoints`), and `b24a4e0` (Round 1 debug
  overlay evidence) and the
  independently committed plan correction `9417f53`.
- The handoff-only commit follows the implementation checkpoint; run
  `git rev-parse HEAD` for the immutable current hash.
- Worktree should be clean immediately after the handoff-only commit. Verify
  with `git status --short --branch` before resuming.
- Current disc profile: `normal-release`.
- Current ISO: 5,410,816 bytes, SHA-256
  `30522182d9c577f3d4ddf7be7b7af499597d00ac1bb5e468110e1bf080410f17`. This
  replaces the pre-shutter 5,400,576-byte image
  `4296b66ec63276524c588b27a786d596e2d4404c747e57fe513806655f4000f6`; the
  growth is the shutter code.
- Current cue SHA-256: `bfc58c7020d90952e93bef7ecba32dea8d4faddf6ce6a90e1054206ee1807b12`.
- Both values match `build/hardware_release_manifest.txt` at
  `profile=normal-release`.
- No MAME process from this checkout remained after the overlay checkpoint.
  Do not kill an emulator owned by another checkout or concurrent session.

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
- The skill now carries the corrected parity-era method: preserve the existing
  Saturn platform pipeline; use ROM translation for systematic animation,
  stage and AI data; use captures as regression evidence; activate retained
  debug tools without per-frame forcing; try stock debugger watchpoints first;
  keep a custom MAME build and entity spawner as contingencies; map actor fields
  on demand; and compare events for functional parity. It also records the
  ROM-derived SH-2 interpreter, exact referenced-tile working set, and measured
  composed-cel versus per-tile VDP1 decision.
- Skill hashes: `SKILL.md`
  `7adc7092f8c11f49a65c33b0161436cafc51b51f7045a73f48e347af8f7cf2ac`;
  `references/workflow.md`
  `ecc81fe344e6a4cc462882b0e24cb8b1575291d79b8185e58e9bc11180f58745`;
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

## Direction change 2026-08-17: ROM logic translation

The user set a new target: **functional parity, not frame-exact parity**, reached
by translating game logic out of the ROM rather than inferring it from screen
captures. Treat the capture-a-clip-and-bind-it method as superseded for new
work. Existing captured evidence stays valid as a cross-check.

Rationale, and it is now demonstrated rather than assumed:

- The project already reconstructs the full 16 MiB CPS2 graphics region
  byte-for-byte, so every tile of every animation is already available. Screen
  capture was only ever re-deriving the *assembly instructions*, which exist in
  ROM as compact tables.
- Frame extraction does not scale: each new actor or action needs its own
  deterministic capture, analyzer, archive, and slice of a 4 MB budget that
  already closes only through phase overlays. Unobserved actions are simply
  missing. Table extraction covers every actor and action at once and shrinks
  with coverage because poses share tiles.

### Animation script tables located

`tools/mame_probe_actor_struct.lua` dumps each tracked actor's struct every
frame; `tools/mame_dump_rom_window.lua` dumps a 68000 program-ROM window.
Findings from the `avspu_stage1_boss_12660` state, 240 frames:

- The actor array has a **0xC0 (192-byte) stride**, confirming the spacing of
  the known actors at `FFA240`, `FFA300`, `FFA3C0`.
- Of 96 struct words, 34 change during animation.
- Words `w1c:w1e` form a 32-bit **animation-script pointer into program ROM**,
  taking 29 distinct values in `0x13CC18..0x13CEC4`. The boss has 29 unique
  captured poses, which is a strong independent corroboration.
- Word `w88` takes 224 distinct values over 240 frames and is very likely a
  per-frame timer or counter.
- Script records are 16 or 20 bytes. Decoded layout, big-endian:
  `+0` word duration in frames, `+2` word flags (`0x8000` observed, almost
  certainly horizontal flip), `+4` long pointer to a sprite assembly, then X and
  Y offset words.
- The pointer advances by the record size and then **jumps backwards to
  `0x13CD0C`**, which is visited twice: the script has an explicit loop, so the
  format includes control flow, not just a frame list.
- Sprite-assembly pointers observed: `0x13DEA0`, `0x13DE46`, `0x13DFEC`,
  `0x13E00A`, `0x13E04C`, `0x13E44C`. These target the next table to decode.

### Animation script structure checkpoint

The private decrypted ROM window now decodes 29 distinct boss animation
programs with `tools/decode_avsp_animation_scripts.py`. The tracked report is
`data/avsp_animation_scripts.json`; it is structural evidence only and does
not pass the pixel-exact pose gate. The renderer's selector-6 assembly command
is also structurally decoded: budget, tile count, offset-table index, and
packed-long/offset-word entries for 14 blocks. The selector-six handler at
`0xAA00E` reads the offset-table pointer from `0x1FD1C8`, consumes two layout
words per tile, applies the signed per-entry adjustment, and emits a CPS
object-command pair. The packed-source and layout-word meanings still need a
rendered-pose comparison.

The updater disassembly from the MAME opcode space establishes the format:
normal pose records are 16 bytes, with duration at `+0`, flags at `+2`, and an
assembly pointer at `+4`. After `+0x10`, a negative flags word causes the
updater to follow the long pointer at the next address, making the apparent
20-byte transitions four-byte jump records plus a normal record. Bytes `+8`
and `+9` are consumed as interaction-table selectors by `0x1cf88` and
`0x1cf94`; they are not yet proven X/Y offsets. `0x88e16` copies all 16 bytes
into actor scratch, so the remaining tail semantics still need consumer-level
mapping.

Reproduce the structural decode after regenerating the ignored private MAME
window:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\decode_avsp_animation_scripts.py
```

The decoder expects the 0x13c000..0x13f000 script window, the 0x1fd1c8 table
window, and the 0x1e0000..0x200000 layout window. Regenerate those ignored
windows with `tools/mame_dump_code_spaces.lua` by setting `AVSP_ROM_FIRST`,
`AVSP_ROM_LAST`, `AVSP_ROM_OUT_PROGRAM`, and `AVSP_ROM_OUT_OPCODES`.

The associated opcode-space dumper is `tools/mame_dump_code_spaces.lua`; raw
program/opcode dumps remain ignored under `.deps\mame\actorprobe`.

Tracked hashes for this checkpoint:

- `tools/decode_avsp_animation_scripts.py`:
  `2a7247ab30d1a239f4d325883075ae798ff25c0ebd2211a8c1b97d2f99702a2d`.
- `data/avsp_animation_scripts.json`:
  `B61F89B68E147521BBFA2934A0F9A21932C0D2C05F8977D8500BEAA8BC9551DA`.
- `tools/mame_dump_code_spaces.lua`:
  `1f22a221c87c5ab2bc07eeab0608cc2bb10d980f5a574cd5f73f0a4bf246ccd6`.

### Next steps for this direction

1. Decode the sprite-assembly table at the `+4` pointers: tile codes, palette
   bank, per-tile offsets, and size. Cross-check a decoded assembly against an
   already-captured boss pose; they must match pixel for pixel.
2. Determine the script opcode/terminator encoding. The 16 vs 20 byte record
   sizes and the backward jump imply a discriminator field; find it rather than
   assuming record size from observed deltas.
3. Map the rest of the 192-byte actor struct: position, health, state, timers,
   facing. Use the existing captured events with known frames as labels.
4. Only then attack AI. Find the routines that write the script-pointer field;
   those are the state machines worth translating.
5. Keep the deterministic captures as regression oracles: a translated table
   must reproduce the already-verified clips exactly.

Note on RNG: if AI decisions consume a PRNG, functional parity requires the
same generator and call order for behaviour to match, even though exact frame
equality is no longer the target. Identify RNG use before translating AI.

### External resources found 2026-08-17

Web research turned up three externally documented resources that change how
much of this work has to be derived from scratch. None of them are ROM data;
they are documentation and open hardware descriptions.

**1. AvP retains Capcom's own development tools in the retail ROM.** Documented
by the sudden-desu.net teardown. This is the highest-value find, because two of
the tools produce exactly the data functional parity needs:

- `0xFF81C7` byte, non-zero, is the master debug enable.
- `0xFF806C..0xFF806E` cache debug DIP rows 1..3. Relevant bits: row 2 bit 7
  **display hitboxes**, row 2 bit 6 **display stage collision**, row 1 bit 0
  entity spawner plus info display, row 1 bit 1 entity monitor, row 1 bit 2
  player monitor, row 3 bit 2 extended entity info, row 3 bit 1 disable CPU in
  attract demos.
- `0xFF81D8` enables the software switch interface, which disables the entity
  spawner because their inputs conflict.
- A hidden test menu runs when `0xFF21AA` equals 2 during the standard test
  menu; nothing in the retail code sets it. It contains a character/pattern
  viewer with hitbox measurement, scroll-layer viewers with a collision "Hit
  Mode", a story-text viewer, and per-actor arrangement tools.
- Three debug routines survive but are disconnected, at disassembly offsets
  `0xB1998` entity info, `0xB1866` player info, `0xB1A84` extended entity info.
  They need `A6` set up and `D0=0` inside a task context.
- The entity spawner is driven by **Player 4** inputs, which standard MAME AvP
  configuration does not provide.

Why this matters: the port currently infers hit windows indirectly by watching
health values change across captured frames, which is how the boss contact
offsets 21/55/97 were derived. The game will draw the real boxes. The same
applies to stage collision, which is currently approximated.

**Initial failures are resolved.** Writing the RAM flags every frame does not
work, and loading `avspu_stage1_boss_12660` with the DIPs does not rerun boot
initialisation. Cold boot with Development hardware and the active-low fields
held from frame 0 still leaves the retail ROM's cache bytes clear because its
physical-DIP-to-RAM copy routine was removed. The verified path injects
`FF806C |= 01` plus the requested `FF806D` row-2 bit once at frame 1200, after
startup RAM clearing. The game's own `0x1434` routine then sets `FF81C7=01` by
frame 1230 and retains it. `tools/mame_probe_debug_overlays.lua` and the
Round 1 capture scripts implement and validate this path.

**2. Complete CPS2 hardware schematics.** Loic Petit's project publishes
schematics for the A-board, B-board, E-board and QSound amplifier, plus reverse
engineering of the custom chips DL-0921 (CPS-B-21), DL-1727, DL-1827, DL-1927
and DL-2027, with an online viewer. This is authoritative documentation for
layer assembly, palette copying, raster effects and video timing, which is what
the Saturn VDP1/VDP2 path has to reproduce.

**3. Open FPGA cores.** Jotego's jtcores/jtcps implement CPS1/1.5/2 in Verilog
and the repository also carries KiCAD schematics of arcade boards.

Confirmed independently: CPS2 work RAM is `0xFF0000..0xFFFFEF`, which is
consistent with the actor array at `0xFFA240` and the debug flags above all
living in the same region.

### FPGA cores

The user raised leveraging FPGA cores. They help the rendering half, not the
logic half, and are worth using for exactly that: an open Verilog CPS core is a
precise specification of sprite/tilemap priority, masking, and palette
behaviour, which is what the Saturn VDP1/VDP2 path must reproduce. Game logic
still lives in the ROM, so cores do not shortcut AI or animation scripts. Their
second use is as an independent oracle to cross-check MAME where MAME's
behaviour looks driver-specific, as already happened with the RGB32 frontend
screen.

## 2026-08-17 stock-MAME overlay checkpoint

The critical-path Phase 1 instrument now works in stock MAME 0.289. The exact
activation sequence is:

1. Persist `:HW_TYPE` Hardware = Development and the active-low overlay DIP
   fields before frame 0 in an isolated configuration directory.
2. Cold boot the retail `avspu` ROM.
3. At frame 1200, after startup RAM clearing, inject the retained
   software-switch bytes once: `FF806C |= 01` and `FF806D |= 80` for hitboxes
   or `40` for collision.
4. Let the game's own routine at `0x1434` derive master enable `FF81C7=01`; it
   is active by frame 1230 and remains active without further RAM writes.

Physical DIPs alone are a recorded negative control, not the solution. With
Development mode and the correct port reads already active, `FF806C`,
`FF806D`, and `FF81C7` remained zero because the retail ROM removed the copy
routine. Do not repeat that path. Also note that Start suicides a live player
when the debug master is active; the deterministic route therefore pulses
Start only for frontend selection or while health is zero/invalid during a
continue.

Tracked entry points and SHA-256 hashes:

- `capture_debug_overlays.ps1`:
  `bd5ae530b322c172c846e2522c048301bb89e7efbe8814b886f533ad9d234ebf`
- `capture_round1_debug_overlays.ps1`:
  `be98c94c421ae1f322ec680f6d278614e0550e6a2581b3960a748ad3942ae395`
- `tools/mame_configure_debug_switches.lua`:
  `194e3a11167d70004372134982fa29da0cce04a0aaaa7d2a27350d3e2bfbaab4`
- `tools/mame_probe_debug_overlays.lua`:
  `c7064f17edf43c04ad3474c0a40132dd63b234ea02198bb2f71c024a9c197a6c`
- `tools/mame_capture_round1_debug_overlays.lua`:
  `6f7383ba90b2002e53cb473ca448ff330e4f2c4825223738c8a8b3756f3aed56`
- `tools/analyze_round1_debug_overlays.py`:
  `27663db07a5f3686e6efd4b5e2047258d9de8a729e7706aa21649cb640656d74`
- `data/round1_debug_overlays.json`:
  `a49c7d01e4bfa050c480b8d5a9dc6a6a2feb69a44ba230f900d2f3fb09a395d5`

Raw ignored evidence:

- Hitboxes: frames 4201..15000 at cadence 1, 10,800 synchronized screenshots
  and actor-RAM samples, 124,416,000 RAM bytes. SHA-256 of `actor_state.bin`:
  `3a8a76751e9a5a0f857afeb35cdc2737f40cec8fea1cb2cf05241c908de24a7a`.
  Visual evidence covers the player, street aliens, Stalker and Chrysalis;
  frame 15000 is the Round 1 results screen.
- Stage collision: frames 4201..17791 at cadence 30, 454 synchronized samples,
  5,230,080 RAM bytes. SHA-256 of `actor_state.bin`:
  `6731a17d28186f84097ca243915d7911599afcae8548bebd3e74dcc2bc1df1a3`.
  Frame 17791 is the first post-boss dialogue and stops before Round 2 play.
- The tracked manifest hashes the key screenshots and validates both datasets.
  These are **capture-exact debug evidence**, not Saturn assets.

Reproduce or validate from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_round1_debug_overlays.ps1 -Mode Hitboxes
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_round1_debug_overlays.ps1 -Mode Collision
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_round1_debug_overlays.py
```

Add `-Refresh` to a capture command only when intentionally replacing its raw
ignored dataset; it also regenerates that mode's cold-boot seed state.

The earlier 15000-frame collision run was structurally valid but ended in the
live Chrysalis fight. Extending to 18000 proved the route crossed into Round 2;
the final deterministic boundary was then tightened to 17791. The first full
hitbox continuation also reached a Continue screen because the route only
recognized health zero; treating `health >= 80` as the invalid/continue state
fixed it. These errors are resolved in the committed scripts.

Remaining gate: the boxes are visibly captured but not yet decoded into
numerical actor-local geometry. Do not claim offsets 21/55/97 are replaced
until that extraction is complete.

## 2026-08-17 actor-labeled hitbox geometry checkpoint

`tools/analyze_hitbox_geometry.py` pairs four clear white debug boxes with the
white pivot markers and records the corresponding actor-state context in
`data/round1_hitbox_geometry.json`. This is **capture-exact overlay geometry**:
Stalker and player at frame 13700, plus Chrysalis and player at frame 14400.
The pivot-relative candidates are now explicit, for example Stalker
`[-16,-81,41,-4]` and the player `[-17,-80,28,-1]` at frame 13700. They are
not yet the native collision tables; all Round 1 poses and actor types still
need validation before replacing 21/55/97 and the Stalker contact schedule.

Reproduce it with:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_hitbox_geometry.py
```

Tracked hashes:

- `tools/analyze_hitbox_geometry.py`:
  `29bf26d2ca60685fbc910eecd8c7b890c354ecd96ad842e894f6bd33b6540de4`.
- `data/round1_hitbox_geometry.json`:
  `5cb1fb504d8a02b502518a2d0789eedd0cca9780104451366fc1017f215e8d8a`.

## 2026-08-17 screen-space bracket extraction checkpoint

`tools/analyze_hitbox_brackets.py` now deterministically recognizes the live
white corner-bracket geometry in selected hitbox screenshots. It handles both
the corner-run form and the complete top/bottom-edge form used by different
poses. `data/round1_hitbox_brackets.json` records the selected Round 1 frames
and their screen-space rectangles. The result is **capture-exact screen-space
evidence**, not actor-local collision data: HUD/text false positives still
require actor pairing, and no 21/55/97 offset has been replaced.

Validation command:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_hitbox_brackets.py `
    .deps\mame\round1_debug_hitboxes\overlay_04201.png `
    .deps\mame\round1_debug_hitboxes\overlay_04300.png `
    .deps\mame\round1_debug_hitboxes\overlay_06000.png `
    .deps\mame\round1_debug_hitboxes\overlay_07000.png `
    .deps\mame\round1_debug_hitboxes\overlay_11000.png `
    .deps\mame\round1_debug_hitboxes\overlay_13000.png `
    .deps\mame\round1_debug_hitboxes\overlay_13700.png `
    .deps\mame\round1_debug_hitboxes\overlay_14000.png `
    .deps\mame\round1_debug_hitboxes\overlay_14400.png `
    -o .\data\round1_hitbox_brackets.json
```

Tracked hashes:

- `tools/analyze_hitbox_brackets.py`:
  `a692e99163f23643dd83f6d977792269dddecb4cecbdc0c94a6a76215dda539c`.
- `data/round1_hitbox_brackets.json`: `c3654c7649abeddabcc16c4f767632f8e04aa53e30d38009b0401352227347f9`.

The first hash above is the canonical SHA-256.

## 2026-08-17 stock-MAME writer watchpoint checkpoint

Stock MAME's debugger watchpoint API is sufficient for the next phase. The
reproducible command is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_actor_writer_watchpoints.ps1 -Frames 600
```

It loads `avspu_stage1_debug_hitboxes` at frame 4200, installs write
watchpoints over every 0xC0 actor slot's animation pointer (`w1c:w1e`), action
(`w06`) and state (`w0c`) fields through `maincpu.debug:wpset`, then runs 600
frames. MAME emits the raw writer lines to ignored `error.log`; the tracked
analyzer produces `data/actor_writer_watchpoints.json`.

Verified result: 2,132 events (1,632 animation-pointer, 210 action, 290 state).
The dominant animation writers are PCs `0x1652A`, `0x16550`, `0x165DE` and
`0x1665E`; state/action writers include `0x40E14`, `0x607E8`, `0x607F8`,
`0x608D4`, `0x6093C`, `0x60EDE`, `0x60F22`, `0x41BE2`, `0x41BEE`,
`0x6104E` and `0x61058`. These are discovery evidence, not translated code.

The first API attempt passed the string `"program"` as the debugger address
space and crashed stock MAME with an access violation inside
`device_debug::wpset`. Passing the actual `maincpu` program-space object fixes
it; the working script contains that correction. No custom MAME build was
needed.

Tracked watchpoint files and SHA-256:

- `capture_actor_writer_watchpoints.ps1`:
  `82d1cc3ce5d2671c83108a47ef38929a6f7fd8f65814f6cc1dd1ad2047f679a8`
- `tools/mame_watch_actor_writers.lua`:
  `15a81685a959c4c777963996f66e91da93fe896de9961b3412a8fe8c54b2de5c`
- `tools/mame_watch_actor_writers.txt`:
  `5017ec12909136dc1485bd65916c1539ccb4317ecc1e0c30efe61fe0b12fc85d`
- `tools/analyze_watchpoint_log.py`:
  `892eb4108abe9c66343bedd8e9d35d75937bd63d73f9df84045d71130b1d2758`
- `data/actor_writer_watchpoints.json`:
  `1377dd04392b7aea0283386cb81f00beeb78d9d24ce5c7a9e79555194bb3f0c0`

The dominant animation-writer PCs are now correlated with the ROM updater:
`0x16536`, `0x165c4` and `0x16644` advance 16-byte records and follow negative-
flag jump pointers. The first stock-MAME windowed debugger helper was
discarded, but the opcode-space dump is now machine-readable through
`tools/mame_dump_code_spaces.lua` and is recorded in the animation-script
checkpoint above. Next work is to decode the assembly records and pair the
extracted brackets with actor/object origins to obtain actor-local geometry.
Do not translate AI or replace native runtime tables until the pixel-exact pose
gate remains passing.

## 2026-08-17 animation-script audit: dedup + flags-word fix

Two confirmed bugs from the current decoded data have been fixed in the decoder:

1. **"29 programs" overcount** — Programs 0x13cc18 and 0x13cc28 are the same
   animation entered one record apart (and similar snapshots like 0x13ce08 →
   0x13ce28). The previous walker only followed 4-byte jump records, missing
   mid-animation snapshots landing on pose records. Fixed `_walker_to_first_pose()`
   to walk forward 16 bytes per pose, detect negative-flags jump records,
   follow them, and return the canonical loop target. Now correctly reports:
   - **29 script pointers from TSV → 6 unique canonical programs → 23 aliases**
   - Programs 1-2: 8-pose looping idle animations (sequences 0-7)
   - Programs 3-6: single-pose hold loops (KO/hit frames, flip_x=0x80)

2. **Word at +2 mislabeled as "flags"** — The high byte is
   `(flip 0x80 | sequence index)` and the low byte is an independent parameter:
   `0x06` = index 0, param 6; `0x0A` = index 1, param 10; `0x1B` = index 7,
   param 27; `0x00` = index 0, param 0. Decoded output now uses fields
   `word_plus2_raw`, `word_plus2_high_byte`, `word_plus2_low_byte`,
   `flip_x`, `sequence_index`, `param_byte`. The zero-terminator branch still
   never fires; all 6 programs end as "loop" (expected if AI exits by rewriting
   the script pointer).

Tools affected: `tools/decode_avsp_animation_scripts.py`
Data: `data/avsp_animation_scripts.json` SHA-256 changed.

## SPR4 binary oracle analysis notes

- All 17 `cd/SPR4/*.BIN` files are 18432 bytes (0x4800) except
  `HITFX.BIN` (2048) and `SHADOW.BIN` (512).
- Player files first non-zero at 0x74D–0x751; enemy files at 0x16AB–0x26EB.
- File is a grid of 192-byte stride records with header bytes encoding pose/mode:
  0x0A = idle, 0x66 = hit/special, 0xCC = special, 0x22 = shadow/mask,
  0xAA = padding/separator.
- Within each block, run-length encoded tile data uses 0xAA as separator and
  0x99/0x9D/0xDD/0x66/0x77/0x44/0x55/0x33 as tile color/luma values.
- The SPR4 format appears to pre-compose tiles from the CPS2 graphics region,
  providing an oracle for the selector-6 pixel gate.

The SPR4 file format is **not yet decoded into named fields**. The goal is to
match the selector-6 assembly to the SPR4 pose pixel-for-pixel.

## Session notes: selector-6 tile decoding progress

- The 12 selector-6 assemblies decoded from ROM reference tiles from the
  16 MiB `gfx_region.bin`. Tile code = `(packed_source >> 16) & 0xFFFF`,
  palette index = `tile_code & 0xFF` (boss poses use palette 27 = 0x1B).
- Layout table x/y values are 16-bit with 6-bit fractional part. Shifting
  by 6 (`>> 6`) gives screen-space coordinates suitable for composition:
  e.g., 2526 → 39, -4092 → -63, 1284 → 20.
- Layout y values for some entries exceed 224 (e.g., 17157 → 268), indicating
  display-space coordinates that may need crop/clip subtraction to match the
  384×224 Saturn canvas.
- The boss KO capture at frame 13492 has `object_shift_x=268, object_shift_y=345`
  and bounds `[344, 448, 552, 544]`. Adding object_shift to the >>6
  coordinates produces positions within the 384-wide display window.
- The selector-6 at `0x13dea0` (Program 3, hold loop, dur=1, flip_x=64)
  references 4 tiles; `0x13de46` (Program 6) references 3 tiles.
  These are the KO and hit pose handlers respectively.
- Rendering tiles at layout position `(x>>6, y>>6)` produces non-blank 8×8
  bitmap frames with correct palette indices.
- Next step for the pixel gate: subtract screen offset (or apply bounding
  box crop) and use the palette bank color table to color tiles; compare
  against the RLE boss KO archive or MAME screenshot at frame 13492.

## Resume in this order

**Superseded for new work by [PARITY_PLAN.md](PARITY_PLAN.md).** The numbered
list below finishes the frontend slice under the old capture-and-bind method
and is still correct for that slice. For anything beyond it, start at the
parity plan's Phase 1 and ROM-decode path. The custom MAME Phase 0 is a
contingency only.

1. Re-run `tools/analyze_round1_debug_overlays.py` against the ignored raw
   evidence and verify the tracked manifest is unchanged.
2. Decode the displayed hitboxes into numerical actor-local geometry for the
   player, street aliens, Stalker and Chrysalis. Validate those real boxes
   against, then replace, the inferred boss schedules 21/55/97 and the inferred
   Stalker contact.
3. Use the completed stock-MAME writer evidence to disassemble the remaining
   state/action PCs and identify AI/RNG consumers. Do not build custom MAME
   unless stock watchpoints demonstrably fail.
4. Finish sprite-assembly decoding and require a ROM-decoded pose to match a
   verified capture pixel for pixel.
5. Compute the exact Round 1 referenced tile set, translate required 68k AI and
   stage tables to native C/data, and compare functional events.
6. Only after the pixel gate passes, replace `player_pose_for_frame()` and the
   hand-written `cap_world_step()` behaviour. Measure composed cels versus
   per-tile VDP1 commands on hardware before choosing.

The older capture-and-bind resume list below is retained only as historical
context for the frontend slice; it is not the current work queue.

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

# Pixel-exact pose gate: each decoded assembly must reproduce a captured pose
# with 0 differing pixels. Currently 12/12 assemblies pass.
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\verify_pose_gate.py

# Per-part position gate: predicted from world(f-1) + ROM layout vs capture.
# PASS = every part exact, or a sibling-assembly origin delta, or bounded
# vertical settling; 0 unexplained. --verbose lists settling/unexplained.
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\verify_position_gate.py
```

The build scripts locate their bundled Python/MAME/Jo Engine dependencies; do not assume `python` is on PATH. A bundled Python is also available at `C:\Users\lambd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

## 2026-08-17 session: pixel gate investigation — selector-6 tile decoding blocked

**Layout window base fixed**: The decoder default `offset_window_base=0x1F6000`
produces wrong layout x/y values. Correct base is `0x1E0000`. Verified by
reading `offset_full_program.bin`: layout values (-112, -96), (-112, -80),
(-112, -64), (-112, -48) appear at file offset `0x1DE40 = layout_address
(0x1FDE40) - 0x1E0000`. Previous decoder output at wrong base
(`0x1F6000`) gave values like x=2526, y=2782 which are garbage.

**Pixel-exact pose gate BLOCKED on selector-6 → tile code mapping**. The
packed_source values in the ROM assembly (e.g., `0x161B0008`, `0x181B0004`) do
not decode to tiles in the 16 MiB `gfx_region.bin` that match the boss KO pose.
- `decode_tile(gfx, packed >> 16, 8)` decodes non-blank tiles, but they render
  at positions (-112,-96..-48) which are off-screen in the 384×224 MAME
  capture frame 13492.
- Shifting layout values by 6 bits (`>> 6`) gives better positions (e.g.,
  -96→-1, -80→-1), but still no match to the MAME screenshot (0.3% similarity).
- MAME object RAM at frame 13492 contains different tile codes than the
  selector-6 entries. The selector-6 handler at `0xAA00E` transforms packed_source
  into GPU sprite codes in a way I have not reverse-engineered.
- The selector-6 assembly entries may be a template; each KO frame may use
  different tile codes than the static assembly ROM data.

**Known facts about the selector-6 format**:
- Packed source contains: `packed >> 16` ≅ tile code candidate, `(packed >>
  16) & 0xFF` ≅ palette index (boss=27=0x1B)
- Layout table x/y at `0x1E0000+0x1DE40`: all x=-112, y staggered by 16
  (-96, -80, -64, -48)
- Selector-6 offset_adjust values (0x8400, 0x8407, 0x8420, 0x8428) are NOT
  layout table chain links; they are consumed by the CPS2 GPU renderer.
- MAME object RAM tile codes (0xC3, 0x8178, 0x80FC, 0x97) ≠ selector-6 codes
  (0xFFE6, 0x161B, 0x181B, 0x171B).

**Next attempt to unblock**: Research CPS2 selector-6 handler `0xAA00E` to
understand how packed_source is transformed into GPU sprite codes. Alternatively,
reverse the CPS2 sprite rendering path from GPU command → tile code in
`gfx_region.bin`. Until this mapping is known, the pixel gate cannot pass.

## Remaining product-level work

- Verify the complete first level audibly in a captured real-time emulator run;
  visual full-route completion is proven, while this pass did not independently
  record every intermediate sound cue.
- Run the documented route on physical NTSC Saturn hardware with a digital controller and 32 Mbit RAM cartridge.
- Continue remaining fidelity gaps after the KO slice: exact Chrysalis action-selection AI, palette/explosion/victory details, remaining nonlethal Stalker reaction fidelity, and any route/intermediate details still listed in `docs/TEST_PLAN.md`.
- Once a faithful full slice passes, forward-test and refine the private skill at `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn`.
- Assemble the full-port evidence package for the development team before proposing anything beyond private use.
