# INTEGRATE-04-COLD-BOOT-TO-ROUND1 task card

TASK: INTEGRATE-04-COLD-BOOT-TO-ROUND1
KIND: INTEGRATE
STATUS: BLOCKED
CHECKPOINT: integrate-cold-boot-round1
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-03-PLAYABLE-SLICE, PROMOTE-08-FRONTEND]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full]
OPTIONAL_LANES: [Physical]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [ORACLE-01-FULL-REFERENCE-ROUTE, ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX, ORACLE-03-ENDING-CREDITS-DELTAS]

## Objective

Integrate cold boot, frontend, credits/start, four-character select/confirm,
loading, and the accepted playable slice into Round 1 gameplay.

## Owned paths

- Future cold-boot/route integration paths and tests, exact release wiring,
  readback, migration/coverage fields, state, and card

## Existing systems to reuse

- Promoted frontend and accepted physical capability-slice components only.

## Systems deliberately disabled

- Route bodies after the measured Round 1 scope and unmeasured character actions.

## Focused machine checks

- Deterministic cold-boot route/input ledger, load/audio ownership, all approved
  locks, no fallback, and route/identity/load perturbation controls.

## Saturn build profile

Exact integration profile, then `release-normal-release` at checkpoint.

## Emulator readback

Require route/substates, selected identity, semantic outputs, ownership,
allocations/canaries, scanout, timing, fallback, and stability.

## Human-review requirement

Renew review for any approved component or frontend result at risk.

## Exclusions

- No complete-game claim and no invented post-Round-1 behavior.

## Hard stops

- Approved regression, illegal ownership, missing source transition, or
  material route architecture decision.

## Next eligible cards

- The three read-only full-game Oracle cards.
