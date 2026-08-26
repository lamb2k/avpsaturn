# SPEC-02-ROUND1-EXECUTABLE-CONTRACT task card

TASK: SPEC-02-ROUND1-EXECUTABLE-CONTRACT
KIND: SPEC
STATUS: READY
CHECKPOINT: spec-round1-executable-contract
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REIMPLEMENT-13-SOURCE-CLOSED-ROUND1]

## Objective

Generate one compact executable Round 1 contract and fixtures from accepted
Oracle evidence, binding every implementation-required player, navigation,
scheduler, enemy, projectile, pickup, encounter, boss, collision/resource,
camera/route, audio/load, clear, and Round 2 handoff field.

## Owned paths

- `data/spec02_round1_executable_contract.json`
- `data/spec02_round1_generated_fixtures.*`
- Focused generators, validators, fixtures, state, coverage, migration, roadmap,
  handoff, and this card

## Existing systems to reuse

- Accepted ORACLE-10/11 evidence, SPEC-01 pattern, and accepted Port V2 interface
  identities. Do not create a second evidence system.

## Systems deliberately disabled

- Production gameplay, Saturn builds, frontend, raw-trace implementation,
  other characters, multiplayer, later stages, and physical status.

## Focused machine checks

- Every required field includes classification; source routine/table/frame;
  evidence hash; type/signedness; transition guard; reads/writes; and real
  mutation control. Required completion-route UNKNOWN count must be zero.

## Saturn build profile

None. Contract generation and host validation only.

## Emulator readback

None; accepted Oracle evidence is bound by hash without new runtime authority.

## Human-review requirement

None. SPEC-02 acceptance is technical and cannot infer USER-10 acceptance.

## Exclusions

- No optional/unreachable behavior forced into scope, raw disassembly notes as
  runtime input, implementation guesses, frontend, or complete-game contract.

## Hard stops

- Any required UNKNOWN, missing evidence hash/type/guard/reads/writes/mutation,
  non-deterministic generation, or unaccepted Oracle input.

## Next eligible cards

- `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` after executable-contract acceptance.
