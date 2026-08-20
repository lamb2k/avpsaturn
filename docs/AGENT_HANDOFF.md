# Agent handoff

Current-only restart state. Git history contains superseded investigations;
this file contains only accepted evidence, live ownership, and ordered next
work. Always verify it with a fresh `git status --short --branch`,
`git log --oneline -10`, and process check.

## Repository state

- Repository: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Branch: `codex/avp-master-plan`
- HEAD: `82bb47e` (`Capture and census the full route at cadence 1 (RP2)`),
  on top of `402a540` (RP1 docs rotation), `dddd19a` (AvspSceneDef v0
  contracts), `2802e2c`, `e728c9b`, `aa0d671`, the Codex-reviewed
  `5bf237e`/`b681c04`, and Codex base `885f6bc`.
- Recent frontend commits:
  - `b681c04` - obey Jo's one-based palette contract (Codex-reviewed);
  - `5bf237e` - prove every held frontend VDP1 object (Codex-reviewed);
  - `aa0d671` - replace R1TITLE.RLE with ROM-derived title text over the
    native street (awaiting Codex review);
  - `e728c9b` - prove the confirmation shutter across the complete source
    interval (awaiting Codex review).
- Acceptance: Capability Gate 1 **0/7**; full game **0/9**.
- Active work: RP0, RP1 and RP2 **PASSED**; next is RP3 in
  `docs/ROUND1_EXECUTION_PLAN.md`. `aa0d671`/`e728c9b` were implemented and
  self-reviewed under the user's autonomous interim-supervisor
  authorization recorded in this session; Codex review remains the
  authoritative acceptance.

The worktree is intentionally and heavily dirty. It contains earlier actor,
collision, frontend, staged-loader, plan, test, analyzer, and private diagnostic
work plus an active frontend integration loop. Do not reset, clean, stash,
switch branch, bulk-stage, or assume any uncommitted path is disposable.

At this checkpoint, modified tracked paths include:

```text
AGENTS.md, CLAUDE.md, QWEN.md, README.md
avsp_collision.h, avsp_emit.c, avsp_frontend.c, avsp_frontend.h
build.ps1, capability_model.h, capture_frontend_rom.ps1, main.c
data/avsp_actor_class_model.json, data/avsp_actor_layout.json
data/avsp_animation_scripts.json, data/avsp_frontend_assets.json
data/avsp_table_set_gate.json, data/round1_debug_overlays.json
data/round1_hitbox_brackets.json, data/round1_hitbox_geometry.json
docs/AGENT_HANDOFF.md, docs/ARCHITECTURE.md, docs/GOAL.md
docs/HARDWARE_TEST.md, docs/NEXT_AGENT_PROMPT.md, docs/PARITY_PLAN.md
docs/TEST_PLAN.md, engine-patches/joengine-4bpp-sprites.patch
tests/avsp_anim_walk_test.c, tests/avsp_runtime_collision_test.c
tests/capability_model_test.c
tools/analyze_frontend_segments.py, tools/analyze_hitbox_brackets.py
tools/analyze_hitbox_geometry.py, tools/analyze_round1_debug_overlays.py
tools/analyze_street_alien_object_emission.py, tools/capture_frontend_cram.py
tools/check_layout_anchor.py, tools/decode_avsp_animation_scripts.py
tools/extract_avspu_stage1.py, tools/gate_avsp_table_set.py
tools/gen_avsp_frontend.py, tools/generate_stage1_route.py
tools/mame_capture_frontend_rom.lua, tools/measure_avsp_sprite_demand.py
tools/test_boss_rom_data.py, tools/verify_avsp_actor_classes.py
tools/verify_boss_rom_poses.py, tools/verify_frontend_cram.py
tools/verify_frontend_objects.py, tools/verify_pose_gate.py
tools/verify_position_gate.py
```

Untracked work includes `.claude/`, `.codex/`, `loader/`,
`docs/ROUND1_EXECUTION_PLAN.md`, frontend/screenshot helpers, the
`tools/diag_*` investigation set, MAME trace/dump probes, and local logs/TSVs.
Re-run Git status for the exact current inventory before staging. ROMs, raw
captures, generated copyrighted payloads, logs, and ISO/cue files remain
uncommittable even when they appear in the worktree.

The concurrent frontend loop was actively restarting pinned Yaba Sanshiro
during the plan refresh. The observed PID changed from 13484 to 44108, so the
PID below is only the latest snapshot, not a stable owner token:

```text
yabasanshiro PID 44108
```

It may belong to the concurrent frontend loop. Do not launch a second emulator
against the same profile. Confirm ownership before stopping it; the owning agent
must terminate all emulator/MAME processes before its checkpoint finishes.

## Implementation report: RP2 - full-route cadence-1 capture and census

- Base: `402a540`; implementation commit `82bb47e` on
  `codex/avp-master-plan`.
- Changed files: `tools/mame_capture_full_route.lua` (new),
  `capture_full_route.ps1` (new), `tools/census_full_route.py` (new),
  `tools/verify_route_census.py` (new), `test.ps1` (census gate),
  `data/round1_route_census.json` (new, tracked semantics only),
  `data/round1_route_census_controls.json` (new).
- Capture: deterministic cold-boot cadence-1 run, frames 1-18000, composite
  of the two proven input schedules (`mame_capture_stage1.lua` frames
  0-4200 verbatim, `mame_capture_stage1_full.lua` re-based to
  relative = frame - 4200). NVRAM baseline snapshotted to
  `.deps/mame/full_route_nvram_baseline` and restored before every run.
  Regions per frame, delta-encoded: gfxram in 64 KiB thirds, work RAM
  0xFF0000-0xFFFFFF, QSound RAM 0x618000-0x619FFF (program-space
  read_range); CPS-A, CPS-B, objram1, objram2, output from their named
  MAME shares because those are MEASURED write-only through the 68000
  read map (program reads return zero). Per-frame screenshots. Raw
  capture private at `.deps/mame/full_route` (~2.0 GiB).
- Route coverage MEASURED from the capture: boss defeat and 1P RESULTS at
  ~14760, Round 2 interior gameplay by 16200, so the held Round 2 title is
  inside the window; the heuristic route dies and continues during street
  and boss combat (continue loops visible as the paired 1501/901-frame
  groups), recorded as played, per the existing stage1 timing policy.
- Census (`data/round1_route_census.json`, 122 groups): frame signature =
  CPS-A layer bases + video-control word + CPS-B block hash + palette
  population bitmap; additional full-frame-rewrite cut when a frame
  rewrites two or more gfxram thirds (measured p99.9 of per-frame gfx
  delta is one third). Groups carry provisional bit-15 AvspSceneDef v0
  IDs, scroll ranges, object-count ranges, input-word runs, per-layer map
  hash counts, row-scroll hash counts, QSound change counts, and review
  flags; region timelines carry change counts and stream hashes only.
  Known landmarks align: character-select shutter group `0x801a`
  (1693-1958, object max 362), Round 1 title `0x801c` (1972-2073), street
  gameplay `0x801d` (2074-5542), results `0x8078`, Round 2 `0x8079`. The
  Round 2 title shares group `0x8079` with Round 2 gameplay - same
  signature because the title text is scroll1 over the already-loaded
  interior scene, consistent with the proven Round 1 title mechanism;
  splitting it is RP6 semantic-ID work.
- Checks, all PASS:
  1. deterministic re-run: an independent cold-boot capture
     (`full_route_rerun`) produced a byte-identical census;
  2. census regenerated twice from the same capture: byte-identical;
  3. negative controls (one-frame boundary shift, perturbed group
     boundary): both detected, recorded in
     `data/round1_route_census_controls.json`;
  4. `test.ps1` exit 0 including the new `tools/verify_route_census.py`
     structural gate (groups tile the route exactly, unique bit-15 IDs);
  5. every MAME process terminated (count 0 verified before commit).
- Review flags: 3 groups flagged `unexplained-full-frame-rewrite`
  (boundaries at 80, 5566/6200-region, 12799); human review scope for RP6.
- GAP: the census groups the Round 2 title with Round 2 gameplay (RP6
  splits by semantic evidence). GAP: audio grouping uses QSound RAM change
  counts only; no audio payload is captured or tracked.
- UNRUN: physical Saturn conditions; audible CDDA/PCM; the separately
  user-requested whole-game capture (`.deps/mame/full_game`, frames
  1-180000 via `capture_full_route.ps1 -CaptureName full_game
  -FinalFrame 180000`) was still recording at handoff time and is
  evidence-only for later rounds.

## Implementation report: RP1 - AvspSceneDef v0 shared contracts

Commit `dddd19a`. New files `avsp_scene.h`, `avsp_scene.c`,
`avsp_scene_player.h`, `avsp_route.c`, `tests/avsp_scene_test.c`; the test
is wired into `test.ps1` and both sources link into the SH-2 image
(`__bend` 0x060bf6d0, 2,352 bytes below the Jo/SGL boundary).

- AvspSceneDef v0 envelope: big-endian words, magic/version/scene-id/
  source-anchor/count/payload header; ten evidence-backed operations with
  length-prefixed records (additive within v0; incompatible changes bump
  the version).
- Scene-ID namespace: 16-bit, bit 15 provisional (RP6 retires), zero
  invalid. Unknown scenes fail diagnostically via one lookup policy.
- AvspScenePlayer lifetime (load/activate/step/draw/release; loads illegal
  after the CDDA late-read lock) and AvspRouteController explicit
  state-machine tables whose edges are validated at init.
- Checks: host contract test (2 positive, 11 negative controls) PASS;
  `test.ps1` exit 0; full build exit 0. Scene content, capture and
  rendering remain RP2-RP4.

## Implementation report: RP0 complete - shutter and Round 1 title

Commits `aa0d671` and `e728c9b`, implementing `docs/NEXT_AGENT_PROMPT.md`
(RP0 Parts A and B).

### Part B - Round 1 title (`aa0d671`)

- Measured composition: the title text is NOT objects - it is 48 scroll1
  glyph tiles (colour bank 0x26, no flips) forming "ROUND 1" and "CITY OF
  DESPAIR". Tilemap written at source 1971 (confirm input + 171); the bank
  fades dim-to-full over sixteen measured per-frame palette rows
  (1971-1986); the HUD tilemap appears at title + 32; the street scene
  layers pop at + 35 with no fade; the glyph tiles are replaced with blank
  glyphs at + 90; the window ends at + 120.
- `tools/gen_avsp_frontend.py round1_text_cels()` extracts the two lines as
  4bpp cels (`R1TXT0/1.BIN`, 1,472 VDP1 bytes) plus the sixteen measured
  fade rows (`R1TF.PAL`, 512 bytes), verifies tilemap identity across the
  interval and absence outside it, and records the `round1_title` timing
  block, `round1_title_text` schedule, and evidence hashes in the manifest.
- Runtime: text drawn as VDP1 objects in select-block sub-bank 13 (loaded
  with the select bundle, before the CDDA disc-read lock), fade by row
  lookup during late confirm, native street scene activated at + 35, HUD
  gated at + 32, select-bundle release deferred to + 90. `R1TITLE.RLE` is
  no longer generated, shipped, or selectable; the sequence table
  regenerates with twelve scenes.

### Part A - confirmation shutter (`e728c9b`)

- `tools/verify_confirm_shutter.py` replays every cadence-1 frame
  1860-1970: content rows 40..223 must be baseline-identical inside
  `cap_confirm_shutter_band()` and pure black outside. First masked frame
  pinned to source 1886 (frames-since-input 86), closure 1908; controls
  for start shift, band shift, and two wrong rates all fail. Report:
  `data/avsp_confirm_shutter_readback.json`.
- Two runtime phase defects fixed: the shutter consumed the leading
  encounter timer directly (one frame early; now converts to
  frames-since-input), and the confirm markers blinked forever (the
  source retires them permanently at frames-since-input 27).
- Live proof: confirm holds at 40/90/100/110; the capture samples fourteen
  NBG1 rows including both rows around each held band edge; sampled rows
  inside the band hash-match the open-band baseline, outside rows are
  zero, and a one-row band shift fails as a live control.
- ADAPTED on record: the source implements the shutter as 360 sliding
  0x3700 mask objects; the Saturn NBG1 row blackout reproduces the same
  pixels, proven per-frame across the complete interval.

### Checks (this session)

| Command | Result |
|---|---|
| `test.ps1` | Exit 0 (includes the new shutter verifier) |
| `py tools/verify_frontend_cram.py` | PASS - 25 holds, 22 surfaces exact, zero boundary writes |
| `py tools/verify_frontend_objects.py` | PASS - 25 holds, 25 schedules / 44 objects exact, live shutter rows proved |
| `py tools/verify_confirm_shutter.py` | PASS - 111 frames (26 open / 22 moving / 63 closed), 4 controls fail |
| manifest regeneration twice | byte-identical `data/avsp_frontend_assets.json` |
| `build.ps1 -FrontendShotTest` + capture | Exit 0; 25 holds from cold boot |
| `build.ps1 -EncounterTest` + live route | COMPLETE (state 18) at frame 3349, all states in order |
| `build.ps1 -Release` + boot | Exit 0; clean boot from the exact cue to `runtime_ready=1`, title state, frame 8 |

Physical Saturn validation, audible CDDA/PCM, and the live sprite
high-water ledger remain **UNRUN**. Capability Gate 1 remains **0/7**.

### Remaining `GAP`/`ADAPTED` in RP0 scope

- ADAPTED: shutter as NBG1 row blackout (pixel-proven) instead of 360 mask
  objects.
- GAP (moved to RP4/RP9): ambient street-actor animation (flames, caged
  aliens, robots) behind the Round 1 title; the native street scene is the
  flattened TILES bitmap plus gameplay actors.
- GAP: the 2P "PRESS START" attract prompt and the bottom-left credit line
  on scroll1 during confirm/title are not reproduced (1P capability test).

## Planning hierarchy

Read in this order:

1. `AGENTS.md` - canonical behavior and ownership;
2. `docs/GOAL.md` - full-game destination;
3. this handoff - volatile restart state;
4. `docs/PARITY_PLAN.md` - overall S1-S6/full-game route;
5. `docs/ROUND1_EXECUTION_PLAN.md` - RP0-RP12 dependencies and status;
6. `docs/NEXT_AGENT_PROMPT.md` - first executable package only;
7. architecture/test/hardware documents required by that prompt.

Only Capability Gate 1 and full-game conditions affect acceptance counts. Work
packages, batches, the shared-primitives check, and the continuous-route and
presentation-parity checks are internal scheduling and validation instruments.

## Accepted frontend evidence

### One-based palette contract - `b681c04`

- Jo palette index zero is reserved; opaque fitted surfaces use `1..255`.
- Bounded helpers copy at most 255 colours through `jo_palette::data`.
- Surface/subpalette canaries prove both adjacent 256-entry block boundaries.
- Nineteen live held observations contain eighteen exact surface comparisons,
  zero adjacent-boundary writes, and expected failures for the rejected
  zero-based payload and one-bank perturbation.

### Held VDP1 objects - `5bf237e`

- Eighteen schedules containing forty objects pass exact geometry, colour,
  order, 352x224 clipping, (176,112) origin, cursor-cycle, and timing checks.
- Four deliberate object perturbations fail.
- Select state has a live animation clock.
- Confirmation blink latency is corrected to the measured source timing.
- Character select remains a non-wrapping 2x2 grid with three-frame direction
  response, A/B/C confirm, no source-measured cancel, and selected ID
  propagation.

### Last accepted checks

| Command | Accepted result at `5bf237e` |
|---|---|
| `test.ps1` | Exit 0 |
| WSL `capability_model_test` | Route reaches Round 2 boundary in 4,485 frames |
| `tools/verify_frontend_cram.py` | 19 holds, 18 exact, controls fail |
| `tools/verify_frontend_objects.py` | 18 schedules / 40 objects exact, 4 controls fail |
| `build.ps1 -FrontendShotTest -SkipHostTests` | Exit 0 |

Those results validate the committed frontend checkpoint only. The current
dirty tree must rerun its applicable checks. At the accepted checkpoint, the
normal no-skip route, `-EncounterTest`, normal-release boot, audible CDDA/PCM,
live sprite high-water, and physical Saturn validation were `UNRUN`. Any active
emulator observation made after that commit is unaccepted until recorded with
the exact build/member hashes and reviewed.

## Current RP0 gaps

SP1 palette ownership and SP2 held VDP1 objects pass. The immediate work is:

1. **SP3 confirmation shutter:** prove the VDP2/NBG1 row blackout across the
   complete cadence-1 interval, including start, centre, row rate, termination,
   and negative controls. The VDP1 object check proves the marker blink, not the
   shutter bands.
2. **SP4 Round 1 title:** capture the complete source interval, determine
   whether its composition is tilemap, object, palette, or mixed, then replace
   runtime `R1TITLE.RLE` with ROM-derived content over the native street scene.
3. Rerun focused/live/full regression checks and record resource/hash results.

The exact RP0 contract is `docs/NEXT_AGENT_PROMPT.md`. Its implementation owner
does not widen into scene runtime, parallax, row-scroll, G0/CDDA residency, S5,
or stage work. A separately assigned evidence-only RP2 probe may begin after
the current state is preserved, as allowed by the execution plan; it must not
edit RP0/shared runtime paths or reuse the active emulator profile concurrently.

## Round 1 go-forward order

After RP0:

1. RP1 commits versioned scene/runtime and ownership interfaces.
2. RP2-RP5 proceed in isolated worktrees: full-route capture/grouping, minimal
   scene runtime, representative two-plane renderer, and G0/CDDA residency.
3. RP6 finalizes stable scene IDs from the grouped source route.
4. RP7 passes every shared primitive required by dependent content.
5. Batches A-C integrate frontend/opening, street/interior, and boss/results to
   the Round 2 title.
6. RP11 passes a controller-driven continuous route with every mismatch in the
   variance ledger.
7. RP12 closes every presentation variance, including physical presentation
   evidence, then the project resumes S5/S3/S4/S6.

Only the integration owner edits shared runtime/build surfaces and the
execution-plan status table. Other agents start from an exact committed SHA,
claim one package and owned file set, work in a separate clean worktree, commit
coherent results, and return explicit SHAs/checks/`UNRUN` items for integration.

## Established evidence not to re-derive without a failing check

- reconstructed 16 MiB graphics region equals MAME's graphics region;
- pose records are 16 bytes and negative-flags jumps are 4 bytes;
- 732-frame animation free-run is exact;
- street-alien assembly/emission path is checked;
- 28/28 listed boss assemblies pass 29 oracle-pose comparisons;
- exact HIT 36/36 and KO 140/140 anchors;
- 25,104 street actor-frames have zero checked per-class constant mismatch;
- source-derived street defender collision runs with unknowns counted `GAP`;
- street scroll2 and scroll3 move at unequal measured rates, so final gameplay
  presentation requires independent planes/parallax;
- per-object actor emission is the default measured cost winner over per-tile.

## Before the next stop

- Update this file newest-first with exact commits, owned/overlapping paths,
  hashes, memory totals, checks, failures, `UNRUN` work, processes, and remaining
  `MEASURED`/`ADAPTED`/`GAP` items.
- The integration owner updates `docs/ROUND1_EXECUTION_PLAN.md` package/SP
  status only from accepted evidence.
- Replace `docs/NEXT_AGENT_PROMPT.md` only when its package passes or new
  evidence falsifies it. Do not append historical prompts.
- Under autonomous execution, rotate the prompt and continue to the next
  dependency-ready package without a planning pause. Under the
  Codex/Claude-review workflow, stop at candidate completion and emit the
  required `CODEX_REVIEW_INVOCATION`.
- Kill all emulator/MAME processes owned by the finishing agent.
