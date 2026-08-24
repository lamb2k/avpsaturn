# ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS task card

TASK: ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS
KIND: ORACLE
STATUS: READY
CHECKPOINT: oracle-predator-warrior-control-actions
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [ORACLE-05-STREET-ALIEN-AI]

## Objective

Capture only the source behavior needed to control Predator Warrior in the
first live encounter: controller inputs and edges, response latency,
horizontal/lane movement, facing, the four measured attack selectors, source
action/substate transitions, startup/active/recovery/return-to-control timing,
attack movement, attack/hurt boxes, health, HIT, KO where available,
interruption/cancellation, and relevant RNG use.

## Owned paths

- Card-scoped MAME inputs/capture tools, ignored raw evidence, derived
  frame-indexed fixtures/reports, coverage/matrix/migration fields, state, and
  this card only

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, REPAIR-09 source contracts, existing capture and
  provenance tooling, and the four measured selector anchors.

## Systems deliberately disabled

- All production runtime, Saturn, Probe 3, physical evidence, frontend,
  `production_head`, and complete four-character move-set changes.

## Focused machine checks

- Two identical captures; one real input perturbation; frame-indexed state and
  visual evidence; exact input/action/box/timing provenance; reject rules
  inferred from animation alone.

## Saturn build profile

None. Read-only MAME/host source research.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; later implementation and playability review remain separate.

## Exclusions

- No production-path write, gameplay implementation, complete move set, new
  MAME truth inferred from Saturn output, or physical-status transition.

## Hard stops

- Missing private inputs, nondeterminism, inadequate perturbation, ambiguous
  input/action binding, production-path drift, or another active Oracle writer.

## Next eligible cards

- `ORACLE-05-STREET-ALIEN-AI` after this card is accepted.
