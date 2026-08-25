# ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION task card

TASK: ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION
KIND: ORACLE
STATUS: BLOCKED
CHECKPOINT: oracle-alien-state-facing-presentation
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT]

## Objective

Source-close class-`0x1F` state/substate dispatch, target/approach/lane steering,
facing and crossing, attack/presentation selection, cooldown/reposition,
HIT/KO/removal, RNG, and scheduler ordering so one source actor state owns
facing, animation record, and rendered assembly.

## Owned paths

- Card-scoped MAME inputs/capture/analyzer tools
- Ignored private traces, captures, disassembly, and actor crops
- Tracked derived reports and fixtures under `data/oracle09_*`
- Coverage/migration/state fields and this card

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, ORACLE-05 route evidence, accepted enemy assets,
  HIT/KO writer maps, and deterministic class-`0x1F` tooling.

## Systems deliberately disabled

- All production runtime, route-only rule generalization, disconnected
  presentation adapters, frontend, Saturn/physical acceptance, and generic AI.

## Focused machine checks

- Counterfactual player placement left/right/above/below, target crossing,
  motion during approach/attack, attacking during approach/attack, and
  inside/outside range. Bind state/facing/animation/assembly from one source
  tick; reject facing, assembly, lane-rule, RNG, and scheduler mutations.

## Saturn build profile

None. This is read-only source closure.

## Emulator readback

No Saturn emulator or physical-Saturn acceptance evidence.

## Human-review requirement

None; the source-closed implementation must later pass QA-12 and renewed
USER-09.

## Exclusions

- No production-path write, generic behavior tree, other alien archetype,
  multiplayer targeting, frontend activation, or physical claim.

## Hard stops

- A bounded state uses unresolved source authority, the experiments cannot
  discriminate target-relative behavior, or state/facing/assembly identity
  remains disconnected.

## Next eligible cards

- `SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT` after acceptance.
