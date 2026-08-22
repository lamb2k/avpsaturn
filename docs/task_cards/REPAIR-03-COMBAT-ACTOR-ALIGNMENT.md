# REPAIR-03-COMBAT-ACTOR-ALIGNMENT task card

TASK: REPAIR-03-COMBAT-ACTOR-ALIGNMENT
KIND: REPAIR
STATUS: ACCEPTED
CHECKPOINT: repair-combat-actor-alignment
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-02-COMBAT]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-03-COMBAT-FEEL-REVIEW]

## Objective

Replace the CombatIntegrationBench's mixed generic/source actor placement with
a durable source-relative position, lane, height, and facing adapter derived
from the retained deterministic MAME combat frames.

## Owned paths

- `src/port_v2/integration/combat/**`
- `tests/port_v2/integration/combat/**`
- CombatIntegrationBench-only wiring in `main.c`
- Card-scoped task, state, handoff, roadmap, and migration fields

## Existing systems to reuse

- Accepted INTEGRATE-02 contact/damage/HIT/KO semantic interface and event
  sequence.
- Retained MAME frames, actor coordinates, active object lists, and source
  screenshots for samples 5190 and 5329.
- Approved player, enemy, stage, HUD, PCM, collision, and HIT/KO regression
  locks.

## Systems deliberately disabled

- General attack/damage rules, second/third reaction timing, AI, stage
  progression, HUD, PCM, CDDA, and normal release.

## Focused machine checks

- Strict C90 compile and deterministic repeat of the source-relative alignment
  view.
- Reject the previous generic placement, inverted actor order, wrong facing,
  and excessive lane/ground separation as real negative controls.
- Regress the accepted four-event semantic ledger and every approved component
  lock unchanged.

## Saturn build profile

Reuse the dedicated `CombatIntegrationBench` with repair-only alignment
readback; do not change normal release.

## Emulator readback

Require exact player/enemy X, lane, height, facing relationship, bounded
baseline separation, attack-toward-target status, unchanged semantic events,
zero failures, intact canaries, and corrected HIT/KO screenshots in two pinned
emulator runs.

## Human-review requirement

Required through renewed `USER-03-COMBAT-FEEL-REVIEW`; machine or emulator
evidence cannot approve subjective alignment.

## Exclusions

- No fresh MAME capture unless retained evidence lacks a required field.
- No change to combat outcomes, animation records/timing, actor art, palettes,
  stage, camera, HUD, audio, or physical-evidence status.

## Hard stops

- Missing source position/facing/pivot evidence, approved-component regression,
  material coordinate-architecture change beyond the bounded adapter, or
  exhausted correction cycle.

## Next eligible cards

- `USER-03-COMBAT-FEEL-REVIEW` with a regenerated ignored package.
