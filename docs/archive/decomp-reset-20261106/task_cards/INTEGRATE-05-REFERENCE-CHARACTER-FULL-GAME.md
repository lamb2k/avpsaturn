# INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME task card

TASK: INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME
KIND: INTEGRATE
STATUS: BLOCKED
CHECKPOINT: integrate-reference-character-full-game
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-04-COLD-BOOT-TO-ROUND1, ORACLE-01-FULL-REFERENCE-ROUTE]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-06-FOUR-CHARACTER-ROSTER]

## Objective

Integrate the measured stage-segment card results into one reference
character's complete title-to-ending-and-credits route.

## Owned paths

- Reference-route integration and acceptance tests, release wiring, coverage
  fields, state, and card; stage behavior remains owned by instantiated cards

## Existing systems to reuse

- Accepted INTEGRATE-04 route, ORACLE-01, and accepted stage-segment card outputs.

## Systems deliberately disabled

- Unmeasured character deltas, duplicated player engines, and multiplayer.

## Focused machine checks

- Full deterministic route, every package/transition, approved locks, no
  fallback, workload-class regressions, route perturbation, and clean rebuild.

## Saturn build profile

Exact full-route integration profile and release-normal-release checkpoints.

## Emulator readback

Require route/content coverage, semantic events, allocations/canaries, audio
ownership, scanout, timing, fallback, and long stability.

## Human-review requirement

Use segment-scoped reviews and renew any approved component at risk.

## Exclusions

- No activation until Goal Mode instantiates and adds every measured stage
  segment dependency from the template.

## Hard stops

- Missing route body, uninstantiated segment card, unknown workload, approved
  regression, or absent physical proof for a new workload class.

## Next eligible cards

- `INTEGRATE-06-FOUR-CHARACTER-ROSTER`.
