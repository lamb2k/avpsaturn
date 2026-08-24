# REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION task card

TASK: REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION
KIND: REPAIR
STATUS: ACCEPTED
CHECKPOINT: repair-source-bound-combat-presentation
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [PROMOTE-01-PLAYER-PIPELINE, V2-B1, INTEGRATE-02-COMBAT, REPAIR-03-COMBAT-ACTOR-ALIGNMENT]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-03-PLAYABLE-SLICE]

## Objective

Extend only the promoted player/combat presentation boundary required to carry
the four measured source attack selectors, source player action/substate,
animation record, pose, pivot, grounding, and active-window state. Build the
expected contract from independent MAME `avspu` evidence, never from the current
Saturn candidate, so INTEGRATE-03 can replace its generic stitched attack
presentation without widening its owned integration paths.

## Owned paths

- `src/port_v2/player/**`
- `src/port_v2/integration/combat/**`
- `tests/port_v2/player/**`
- `tests/port_v2/integration/combat/**`
- Narrow source-combat capture and cadence-1 visual-QA tools and their tests
- One tracked source-derived combat-presentation contract; raw screenshots,
  crops, clips, memory dumps, and private logs remain ignored
- Combat-repair-profile-only adapter wiring in `main.c`, `build.ps1`, `makefile`,
  `verify.ps1`, and `asset_manifest.json` where required
- Card-scoped task, state, handoff, roadmap, and migration fields

`src/port_v2/integration/slice/**` remains owned by INTEGRATE-03 and must not be
changed by this repair.

## Existing systems to reuse

- MAME 0.289 and verified set `avspu` as the independent semantic and visual
  oracle.
- Exact contact fixtures at source samples 5190, 5236, 5283, and 5329 with
  selectors 1, 2, 3, and 4.
- Promoted player idle/walk assets, palette, pivot, grounding, and animation
  locks.
- Exact collision and class-`0x1F` HIT/KO semantic interfaces.
- The approved class-`0x1F` WALK presentation and the currently working enemy
  death/KO animation as regression locks, not as source-truth generators.
- Shared camera/world transform, stage, P1/P2 HUD, PCM, CDDA, residency, and
  canary locks; this card may only prove they remain unchanged.

## Systems deliberately disabled

- INTEGRATE-03 slice choreography and normal-release acceptance.
- Free-form player control, general attack rules, enemy AI, targeting, stage
  progression, frontend, full route, roster, and multiplayer.
- Physical Saturn and `SALVAGE-08-FRONTEND`.
- Any expected render hash learned from the current Saturn candidate.

## Focused machine checks

- Capture cadence-1 MAME windows beginning at least 12 frames before each
  attack through the complete reaction/recovery around samples 5190, 5236,
  5283, and 5329.
- Record player/enemy slot and identity, action, substate, selector, animation
  record, pose/object/tile identity, palette, world/lane/height/baseline,
  attack/hurt boxes, collision, health, HIT/KO, and source timing each frame.
- Store source screenshots and actor crops separately from Saturn output and
  hash them into a tracked source contract without committing private media.
- Prove selector 1/2/3/4 maps to its own source action, pose sequence, pivot,
  active window, and collision box. Reject a generic attack substitution.
- Reproduce source-relative offsets approximately 0/46/93/139 unless a bounded
  Saturn adaptation is explicitly measured and recorded; never slow runtime
  for review.
- Generate source-versus-Saturn crops, contact sheets, collision overlays,
  temporal strips, slowed clips, and a frame-indexed findings report.
- Reject wrong-but-valid stalker tiles, another alien family, wrong reaction
  record, wrong palette, selector/pose mismatch, contact without overlap,
  damage before active state, wrong defender, visible/semantic mismatch,
  floor penetration, pivot jumps, and candidate-derived expected hashes.
- Run strict portable C90 checks, deterministic repeats, and every approved
  player/combat regression lock.

## Saturn build profile

Use a dedicated source-bound combat-presentation repair profile. It must render
the four selector-specific player sequences and matching class-`0x1F`
reaction/death evidence at full speed. Produce slow motion only by postprocessing
cadence-1 captures. Do not claim normal-release or physical acceptance.

## Emulator readback

Run paired captures in pinned Yaba Sanshiro and require exact repeat of semantic
and visual traces. Per frame record selector, action/substate, pose, pivot,
height, rendered foot baseline, animation/object/tile/palette identities,
attack-active state, boxes, contact, attacker/defender, health, reaction, and
rendered actor identity. Codex must directly inspect source-versus-Saturn
contact sheets and temporal strips and record frame-specific findings and
repairs.

## Human-review requirement

This repair does not accept INTEGRATE-03. After the source-bound interface and
dedicated presentation bench pass, return to INTEGRATE-03 to consume the
interface, rebuild the complete normal-release scene, run Full, and present the
full-speed source/Saturn clips, slow-motion clip, overlays, timing comparisons,
alien-family comparison, grounding trace, and findings for renewed explicit
human review. Silence is not approval.

## Exclusions

- No change to approved player idle/walk artwork or global Y offset.
- No change to exact collision or HIT/KO semantic routines.
- No widening of attack/hurt boxes or actor movement merely to make silhouettes
  touch.
- No change to stage/camera appearance, HUD, PCM/CDDA payload or timing,
  residency, or canary behavior.
- No full enemy AI, targeting, free-form gameplay, Full-lane repair, physical
  testing, or frontend activation.
- No generated copyrighted media, raw capture, screenshot, clip, ROM, or memory
  dump may be committed.

## Hard stops

- Missing source fields or cadence-1 frames for any of the four contacts.
- The source asset package lacks a required player or class-`0x1F` pose.
- Correctness requires changing a promoted interface outside the owned
  player/combat presentation boundary.
- Any approved player, enemy WALK/death, camera/stage, HUD, audio, residency, or
  canary regression.
- Material architecture decision or exhausted bounded correction cycle.

## Next eligible cards

- `INTEGRATE-03-PLAYABLE-SLICE` only after this repair is accepted. It must then
  consume the source-bound interface, recapture the complete scene, rerun Full,
  and stop for renewed human review before physical Saturn or SALVAGE-08.
