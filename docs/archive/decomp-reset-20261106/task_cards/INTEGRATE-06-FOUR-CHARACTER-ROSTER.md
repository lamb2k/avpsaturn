# INTEGRATE-06-FOUR-CHARACTER-ROSTER task card

TASK: INTEGRATE-06-FOUR-CHARACTER-ROSTER
KIND: INTEGRATE
STATUS: BLOCKED
CHECKPOINT: integrate-four-character-roster
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME, ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX, ORACLE-03-ENDING-CREDITS-DELTAS]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-07-THREE-PLAYER-MULTIPLAYER]

## Objective

Integrate accepted character-template results for Predator Warrior, Major
Schaefer, Predator Hunter, and Linn Kurosawa through one common player runtime.

## Owned paths

- Roster integration/acceptance paths and tests, coverage/matrix fields, state,
  and card; individual character behavior remains owned by instantiated cards

## Existing systems to reuse

- Reference full game, complete character/ending matrices, and accepted
  `PortV2CharacterDef` implementations.

## Systems deliberately disabled

- Duplicated player engines, unmeasured differences, and three-player expansion.

## Focused machine checks

- Per-character full route, shared-runtime invariants, action/collision/HUD/audio/
  ending matrices, cross-character mutation controls, and clean builds.

## Saturn build profile

Per-character exact route profiles and release-normal-release acceptance.

## Emulator readback

Require character identity/actions/resources, route/ending, semantic outputs,
allocations/canaries, audio, scanout, fallback, timing, and stability.

## Human-review requirement

Each instantiated character card includes explicit visual/feel review.

## Exclusions

- No activation until Goal Mode instantiates and adds all character-template
  dependencies.

## Hard stops

- Unknown matrix cell required by gameplay, copied player engine, missing
  character review, or physical workload failure.

## Next eligible cards

- `INTEGRATE-07-THREE-PLAYER-MULTIPLAYER`.
