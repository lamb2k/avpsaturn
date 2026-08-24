# ORACLE-06-ROUND1-ENCOUNTER-RULES task card

TASK: ORACLE-06-ROUND1-ENCOUNTER-RULES
KIND: ORACLE
STATUS: BLOCKED
CHECKPOINT: oracle-round1-encounter-rules
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-05-STREET-ALIEN-AI]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [SALVAGE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER]

## Objective

Capture one bounded Round 1 encounter: entry trigger, enemy spawn/position,
camera lock/bounds, stage/event state, audio event, encounter-active and clear
conditions, camera unlock, and route/segment continuation. Keep encounter
controller state, street-alien actor AI, and presentation events separate.

## Owned paths

- Card-scoped MAME inputs/capture tools, ignored raw evidence, derived
  encounter fixtures/reports, coverage/migration fields, state, and this card

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, ORACLE-04/05 evidence, measured stage/camera
  evidence, and existing route/provenance tooling.

## Systems deliberately disabled

- All production runtime, Saturn, Probe 3, physical evidence, frontend,
  `production_head`, later encounters, bosses, and complete Round 1 claims.

## Focused machine checks

- Two identical captures and a real entry/clear perturbation; frame-indexed
  controller/actor/presentation separation; reject scene-bytecode gameplay
  authority and presentation-owned clear/route progression.

## Saturn build profile

None. Read-only MAME/host source research.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; later implementation and playability review remain separate.

## Exclusions

- No production-path write, gameplay implementation, later route capture,
  scene-bytecode gameplay authority, or physical-status transition.

## Hard stops

- Missing private inputs, nondeterminism, ambiguous controller/AI/presentation
  ownership, inadequate perturbation, production drift, or another writer.

## Next eligible cards

- `SALVAGE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER` after physical acceptance of
  INTEGRATE-03 and this card's acceptance.
