# INTEGRATE-02-COMBAT task card

TASK: INTEGRATE-02-COMBAT
KIND: INTEGRATE
STATUS: READY
CHECKPOINT: integrate-combat
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-01-PLAYER-AND-ENEMY, SALVAGE-03-COLLISION, V2-B1]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-03-COMBAT-FEEL-REVIEW]

## Objective

Add attack, collision, contact, damage, HIT, and KO one bounded behavior at a time to the promoted player/enemy integration.

## Owned paths

- `src/port_v2/integration/combat/**`
- `tests/port_v2/integration/combat/**`
- Card-scoped diagnostic/readback, ledger, state, and card

## Existing systems to reuse

- Promoted player/enemy/collision/HIT-KO interfaces and accepted source evidence.

## Systems deliberately disabled

- Camera progression, stage expansion, HUD, PCM, and CDDA.

## Focused machine checks

- Strict compile; per-behavior differential; deterministic replay; no-contact and mutated-writer controls; regress approved actor presentation.

## Saturn build profile

Dedicated `CombatIntegrationBench` diagnostic.

## Emulator readback

Require attack/contact/damage/HIT/KO semantic events and frames, actor states/positions, render counts, canaries, asset failures, and stability.

## Human-review requirement

Required after AI self-review through `USER-03-COMBAT-FEEL-REVIEW`.

## Exclusions

- No new enemy AI, stage, audio, or authored approximation.

## Hard stops

- Source mismatch, approved actor regression, unsupported exact dependency, or exhausted correction cycle.

## Next eligible cards

- `USER-03-COMBAT-FEEL-REVIEW`.
