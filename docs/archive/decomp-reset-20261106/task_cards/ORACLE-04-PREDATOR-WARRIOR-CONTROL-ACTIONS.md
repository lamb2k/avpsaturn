# ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS task card

TASK: ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS
KIND: ORACLE
STATUS: ACCEPTED
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

## Validated evidence

- Two 261-frame cold-boot control captures are byte-identical at sample SHA-256
  `498592af6d91405d9458104b2530fd59bb0c3f4c9ee8e220ac2b83fb71f266cb`.
- A one-frame right-input suppression at source frame 2525 changes the input at
  only that frame and first changes downstream player state at frame 2527;
  perturbed sample SHA-256 is
  `2c8ddf142c2dc176a9ca2261b30f237c69aae432238b0ef835d1143ee0edf4ad`.
- Right, left, up-lane, and down-lane responses each begin two frames after the
  input edge. The bounded source displacements are +45 X, -45 X, +7 Z, and
  -12 Z, with the measured facing changes retained in the public report.
- Attack selectors 1 through 4 bind to active/contact offsets +4/+5, +5/+6,
  +7/+8, and +8/+9 frames. Their measured damage sequence is 87 to 63, 63 to
  39, 39 to 8, and 8 to -1, with exact attack/hurt boxes and visual hashes.
- `data/oracle04_predator_warrior_control_actions.json` is deterministic across
  two generations at SHA-256
  `abee00783583ea121958cd030a4a12dbbdbc7c7ac3466cb1cf6a5fdea58d95e4`.
- Complete move-set coverage, interruption/cancellation, and player-side RNG
  consumption remain `UNKNOWN`; Saturn emulator and physical Saturn remain
  `UNRUN`.
- Focused negative controls, `Fast`, and `Oracle` pass. The Oracle run also
  repaired the stale post-refresh writer-manifest provenance pins; regeneration
  changed only the two refreshed input hashes, and all writer-closure mutations
  and downstream HIT/KO, combat, and playable-slice locks pass.
