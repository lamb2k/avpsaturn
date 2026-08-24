# SALVAGE-11-STREET-ALIEN-AI task card

TASK: SALVAGE-11-STREET-ALIEN-AI
KIND: SALVAGE
STATUS: BLOCKED
CHECKPOINT: salvage-street-alien-ai
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [PROMOTE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER, ORACLE-05-STREET-ALIEN-AI]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-11-STREET-ALIEN-AI]

## Objective

Implement only the measured class-`0x1F` AI loop required for the first live
encounter: target selection, approach, lane adjustment, facing, attack
selection/execution, recovery/cooldown, player contact/damage, HIT, KO, and
source-required deterministic RNG consumption.

## Owned paths

- Future class-`0x1F` AI salvage core/bench and focused tests
- Card-scoped Target adapter/readback, migration/coverage state, and this card

## Existing systems to reuse

- ORACLE-05/06 fixtures, promoted enemy presentation, exact collision/HIT/KO,
  promoted player action state, scheduler evidence, and approved locks.

## Systems deliberately disabled

- General behavior-tree framework, enemy scripting language, general CPS-2 AI
  engine, bosses, other archetypes, multiplayer targeting, and frontend.

## Focused machine checks

- Host differential and source counterfactuals; deterministic repeat; distance,
  lane, timer, health, attack-timing, and RNG mutations; current-state contact
  and damage; scheduler-order and approved-lock regressions.

## Saturn build profile

Dedicated `StreetAlienAiSalvageBench` diagnostic.

## Emulator readback

Require target, AI state/timers, movement/lane/facing, selected attack phases,
RNG cursor, collision/damage, player and alien HIT/KO, canaries, failures, and stability.

## Human-review requirement

No acceptance of feel here; USER-09 reviews the integrated behavior.

## Exclusions

- No authored fallback, scripted review timing, generic AI framework, extra
  archetype, multiplayer, or approved presentation change.

## Hard stops

- Missing source branch/RNG ownership, unsupported scheduler dependency,
  approved regression, nondeterminism, or material architecture decision.

## Next eligible cards

- `PROMOTE-11-STREET-ALIEN-AI`.
