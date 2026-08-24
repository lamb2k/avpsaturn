# SALVAGE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER task card

TASK: SALVAGE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER
KIND: SALVAGE
STATUS: BLOCKED
CHECKPOINT: salvage-predator-warrior-action-controller
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-03-PLAYABLE-SLICE, ORACLE-06-ROUND1-ENCOUNTER-RULES]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER]

## Objective

Isolate and implement only the source-supported Predator Warrior subset for
the first live encounter. Consume real controller input and own movement,
lanes, facing, four measured attacks, startup/active/recovery, action movement
and grounding, health, HIT, KO, and return to control.

## Owned paths

- Future bounded player-action salvage bench/core and focused tests
- Card-scoped Target adapter/readback, migration/coverage state, and this card

## Existing systems to reuse

- ORACLE-04/06 fixtures, promoted player presentation, REPAIR-09 attack assets,
  exact collision/HIT/KO, and all approved stage/HUD/audio/residency locks.

## Systems deliberately disabled

- Fixed-frame attack schedules, contact-count attack selection, generic attack
  booleans as production authority, direct render calls, complete weapons or
  specials, other characters, enemies, frontend, and full route.

## Focused machine checks

- Strict Jo/SGL-free portable core; source differential; deterministic input
  ledger repeat; input/timing/box/interruption mutations; no fixed-frame or
  contact-count authority; approved-lock regressions.

## Saturn build profile

Dedicated `PredatorWarriorActionSalvageBench` diagnostic only.

## Emulator readback

Require sampled input, action/substate, startup/active/recovery, movement,
facing, boxes, health/HIT/KO, return-to-control, render-port outputs, canaries,
failures, and bounded stability.

## Human-review requirement

No acceptance of feel here; USER-09 reviews the integrated encounter.

## Exclusions

- No four-character abstraction beyond architecture-justified fields, no
  gameplay result injected from a review timeline, and no approved lock drift.

## Hard stops

- Missing source rule, required interface widening beyond the bounded action
  controller, approved regression, nondeterminism, or architecture decision.

## Next eligible cards

- `PROMOTE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER`.
