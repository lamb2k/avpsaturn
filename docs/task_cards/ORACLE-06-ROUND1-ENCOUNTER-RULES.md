# ORACLE-06-ROUND1-ENCOUNTER-RULES task card

TASK: ORACLE-06-ROUND1-ENCOUNTER-RULES
KIND: ORACLE
STATUS: ACCEPTED
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

- `SALVAGE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER` after this card's acceptance;
  HW-01 remains parked for the separate INTEGRATE-03 physical procedure.

## Validated evidence

- Two 5,001-frame cold captures are byte-identical across samples, all 20 actor
  slots, controller writes, and QSound writes. The sample SHA-256 is
  `ccf58c95c821cee7f54a6c4148a62f1d15c3436a05e92f89fdaaca600325f120`.
- The credited Start route creates an input-responsive P1 actor. Withholding
  forward movement from frames 3700 through 3900 delays encounter-active state
  from 3715 to 3741 and the `scroll2_x=768` lock from 3821 to 4011.
- The source street set piece enters state 4, holds camera locks at 576, 768,
  and 944, and starts a capture-exact QSound voice batch with the first ten
  class-`0x1F` actors at frame 3574.
- The source does not clear that opening by kills: state 6 begins at frame
  6768 with six living aliens, and presentation transition removes those actors
  at frame 6919 before the warehouse continuation becomes active at 7088.
- Suppressing attacks changes actor outcomes but leaves the first camera unlock
  at frame 4995 with eight rather than seven living aliens. Timer-only clear,
  presentation-owned clear, wrong spawn, missing unlock, and missing
  continuation mutations are rejected.
- The bounded live implementation contract is therefore source-bound with one
  adapted ORACLE-05 alien: clear authority is target KO then inactivity, never
  a timer or presentation flag. The committed report SHA-256 is
  `aa1406321b11a2616427431ddf13bb24d948914e12765c66191dc934d1457ce9`.
  `Fast` and `Oracle` pass; Saturn emulator and physical Saturn remain `UNRUN`.
