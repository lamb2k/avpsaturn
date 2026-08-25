# SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT task card

TASK: SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT
KIND: SPEC
STATUS: BLOCKED
CHECKPOINT: spec-first-live-encounter
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT, ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS, ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER]

## Objective

Produce reviewed machine-readable executable contracts for the bounded player
action/equipment graph, navigation, alien state/facing/presentation, collision
selectors, and encounter authority. Every field records classification,
provenance, type/signedness, guard, reads/writes, and mutation control.

## Owned paths

- Tracked `data/spec01_*` schemas, contracts, generated fixtures, validators,
  this card, and the coverage/migration/state fields required to bind them

## Existing systems to reuse

- Only accepted ORACLE-07/08/09 reports, existing source-identity hashes,
  accepted Port V2 interface contracts, and deterministic schema tooling.

## Systems deliberately disabled

- Production runtime, raw-trace consumption by implementation, visual guesses,
  frontend, Saturn/physical acceptance, and automatic UNKNOWN substitution.

## Focused machine checks

- Schema/type/provenance validation; complete guard/read/write inventory;
  deterministic generation; required non-vacuous mutation per field family;
  and a validator that blocks any required `UNKNOWN` behavior.

## Saturn build profile

None. This is a host-executable specification gate.

## Emulator readback

No Saturn emulator or physical-Saturn acceptance evidence.

## Human-review requirement

Codex directly reviews the executable specification and evidence binding;
subjective gameplay review remains at renewed USER-09.

## Exclusions

- No implementation from raw MAME traces/disassembly notes, no invented
  transition, no hidden adaptation, frontend activation, or physical claim.

## Hard stops

- Missing required provenance/type/guard/read/write/mutation metadata, any
  implementation-required UNKNOWN, nondeterministic fixture, or Oracle drift.

## Next eligible cards

- `REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER` only after the executable
  contracts and all required classifications are accepted.
