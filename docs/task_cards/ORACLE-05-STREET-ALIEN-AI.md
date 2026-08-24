# ORACLE-05-STREET-ALIEN-AI task card

TASK: ORACLE-05-STREET-ALIEN-AI
KIND: ORACLE
STATUS: BLOCKED
CHECKPOINT: oracle-street-alien-ai
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [ORACLE-06-ROUND1-ENCOUNTER-RULES]

## Objective

Capture one complete class-`0x1F` street-alien behavior loop: spawn/init,
one-player target selection, approach, lane adjustment, facing, attack
selection, startup/active/recovery/cooldown, player collision/damage,
repositioning, HIT/recovery, KO/removal, relevant timers and RNG consumption,
and actor scheduler/update order.

## Owned paths

- Card-scoped MAME inputs/capture tools, ignored raw evidence, derived AI
  fixtures/reports, coverage/migration fields, state, and this card only

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, accepted class-`0x1F` identity/HIT/KO evidence,
  and existing provenance and controlled-capture tooling.

## Systems deliberately disabled

- All production runtime, Saturn, Probe 3, physical evidence, frontend,
  `production_head`, other enemy archetypes, bosses, and multiplayer.

## Focused machine checks

- Two identical captures and controlled counterfactuals for player distance,
  lane difference, player attack timing, enemy health, AI timer, and consumed
  RNG state; bind scheduler order and reject appearance-derived behavior trees.

## Saturn build profile

None. Read-only MAME/host source research.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; later implementation and playability review remain separate.

## Exclusions

- No production-path write, invented behavior tree, generic AI engine,
  archetype expansion, authored fallback, or physical-status transition.

## Hard stops

- Missing private inputs, nondeterminism, unresolved scheduler/RNG ownership,
  inadequate counterfactual, production-path drift, or another Oracle writer.

## Next eligible cards

- `ORACLE-06-ROUND1-ENCOUNTER-RULES` after this card is accepted.
