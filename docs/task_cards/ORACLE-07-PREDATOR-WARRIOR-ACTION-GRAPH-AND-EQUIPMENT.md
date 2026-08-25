# ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT task card

TASK: ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT
KIND: ORACLE
STATUS: READY
CHECKPOINT: oracle-player-action-graph-equipment
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [REPAIR-10-LIVE-PLAYER-PRESENTATION]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS]

## Objective

Source-close the bounded Predator Warrior controller required by the first live
encounter: input edges, action/substate dispatch, combo and equipment state,
animation/assembly selection, action movement/facing/timing, attack/hurt
selectors, interruption/cancellation, HIT/KO, and return to control.

## Owned paths

- Card-scoped MAME inputs and capture/analyzer tools
- Ignored private traces, captures, disassembly, and visual witnesses
- Tracked derived reports and fixtures under `data/oracle07_*`
- Coverage/migration/state fields and this card

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, ORACLE-04 and REPAIR-09 evidence, source writer
  maps, deterministic capture tools, and the live encounter only as a harness.

## Systems deliberately disabled

- All production gameplay/runtime writes, Saturn builds, automatic selector
  preservation, frontend work, physical-status changes, and implementation
  from visual inference.

## Focused machine checks

- Two independently launched identical captures; isolated and repeated button
  experiments across control/startup/active/recovery/HIT; movement+attack,
  equipment transitions, idle-duration changes, and direction reversal.
- Bind every transition to source routine/table/frame and require non-vacuous
  action-selection, equipment, cancellation, and assembly-identity mutations.

## Saturn build profile

None. This is read-only source closure.

## Emulator readback

No Saturn emulator or physical-Saturn acceptance evidence.

## Human-review requirement

None. The source-closed implementation must later pass QA-12 and renewed
USER-09.

## Exclusions

- No production-path write, arbitrary selector cycle, inferred weapon state,
  complete four-character move set, frontend activation, or physical claim.

## Hard stops

- Missing private inputs, nondeterminism, unresolved action/equipment writer
  needed by the bounded encounter, vacuous perturbation, or production drift.

## Next eligible cards

- `ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS` only after accepted source closure.
