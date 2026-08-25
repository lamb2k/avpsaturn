# SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT task card

TASK: SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT
KIND: SPEC
STATUS: ACCEPTED
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

## Validated evidence

- The committed executable contract covers every implementation-required field
  family: player action/equipment, navigation, source-world projection, alien
  state/presentation, collision/damage, encounter authority, and diagnostic
  observability. Every required field includes provenance, type/signedness,
  guard, reads, writes, and a non-vacuous mutation control.
- Required behavior has zero `UNKNOWN`, `UNRESOLVED`, `GUESSED`, or `FALLBACK`
  substitutions. Deferred generic AI, other archetypes, multiplayer, later
  Round 1 terrain, frontend, and physical Saturn behavior remain explicitly
  out of scope.
- Player action is discrete-edge driven with the measured 30-frame follow-up
  window; selector assemblies stay record-owned. Coffee Shop navigation uses
  the measured non-rectangular world-space envelope, while the explicit
  projection adapter makes increasing source world-z move upward on screen.
- The bounded class-`0x1F` implementation contract retains authored approach,
  crossing/lane response, state-owned facing/animation/assembly, measured RNG
  attack timing, bounded contact witnesses, and HIT/KO/inactive clear
  authority. Generic face-target, independent assembly selection, the legacy
  distance-160 collision guess, timer clear, and presentation clear are
  rejected.
- Same-tick diagnostics bind alien state, health, facing, animation record,
  assembly, collision, encounter, and camera authority, preventing the HUD or
  overlay from presenting stale state after a gameplay transition.
- The contract is
  `data/spec01_first_live_encounter_executable_contract.json`, SHA-256
  `a8a8d5ff06d70a8df4cc7687928e0eb5200927ac8901adb3eb76745c4b42bd0f`,
  at evidence commit `299468abad77a6d4b6e0afc6f63c97f0a1a69ae9`.
  `Fast` and `Oracle` pass, including deterministic regeneration, real
  field-family mutations, writer-map controls, and MAME `avspu` identity.
  Saturn emulator and physical Saturn remain `UNRUN`; no production gameplay
  path changed in SPEC-01.
