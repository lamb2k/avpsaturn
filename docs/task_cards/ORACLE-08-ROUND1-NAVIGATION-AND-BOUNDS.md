# ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS task card

TASK: ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS
KIND: ORACLE
STATUS: READY
CHECKPOINT: oracle-round1-navigation-bounds
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION]

## Objective

Recover the Coffee Shop movement authority: walkable lane range, depth and
wall/obstacle extents, floor/terrain constraints, rejection or clamping,
stage-segment/camera bounds, and route-trigger boundaries.

## Owned paths

- Card-scoped MAME boundary inputs/capture/analyzer tools
- Ignored private traces, captures, and boundary overlays
- Tracked derived reports and fixtures under `data/oracle08_*`
- Coverage/migration/state fields and this card

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, ORACLE-06 stage/controller evidence, accepted
  camera/stage infrastructure, and source actor/stage writer maps.

## Systems deliberately disabled

- All production runtime, screen-space clamps, arbitrary stage limits, frontend,
  Saturn/physical acceptance, and gameplay implementation.

## Focused machine checks

- Independently reproduce every bounded edge and run a source counterfactual
  into each non-walkable side. Record requested movement, accepted/rejected
  displacement, responsible routine/table, actor state, camera, and trigger.
- Reject missing-wall, widened-lane, bypassed-obstacle, and screen-clamp
  mutations.

## Saturn build profile

None. This is read-only source closure.

## Emulator readback

No Saturn emulator or physical-Saturn acceptance evidence.

## Human-review requirement

None; navigation is consumed later by SPEC-01 and QA-12.

## Exclusions

- No production-path write, guessed screen bounds, later-stage generalization,
  frontend activation, or physical claim.

## Hard stops

- A required Coffee Shop boundary lacks source authority or counterfactual,
  evidence is nondeterministic, or the derived contract cannot explain the
  source rejection/clamp behavior.

## Next eligible cards

- `ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION` after acceptance.
