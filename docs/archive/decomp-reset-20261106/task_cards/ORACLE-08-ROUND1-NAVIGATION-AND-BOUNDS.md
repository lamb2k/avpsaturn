# ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS task card

TASK: ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS
KIND: ORACLE
STATUS: ACCEPTED
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

## Validated evidence

- Two independently launched navigation captures are byte-identical across
  1,301 samples and all player position writes. Two independently launched
  class-`0x1F` boundary captures are also byte-identical across 151 samples and
  enemy position writes.
- The Coffee Shop player interval is world-space and dynamic: at measured
  `bound_x=832`, routine `0x01b000` resolves X to `864..1184`. The lower lane
  reaches world-Z 224 through the dynamic depth base; Up input increases source
  world-Z and Down decreases it. SPEC-01 must translate that world axis rather
  than copy it as screen-Y.
- The walkable shape is not rectangular. Obstacle actor `0xffb380`,
  class `0x0A`, type `0x14`, at `(1123,323)` stops the player at X 1091 in the
  upper/middle lane through response block `0x01d930`. Deactivating only that
  obstacle lets the identical Right schedule reach X 1184; the lower diagonal
  route also passes it and reaches `(1184,224)`.
- Terrain record `0x0b2136` with bytes `0202808010080080` independently rejects
  Up movement at world-Z 327 through writer `0x0b1c68`; removing the obstacle
  actor does not widen that terrain boundary.
- A class-`0x1F` actor is not clamped to the player's X interval: controlled
  X positions 840 and 1200 remain accepted on its next tick. Controlled Z 200
  and 420 are restored to 300 by actor writer `0x060c84`. This forbids a shared
  player/enemy rectangle while leaving target-relative steering semantics to
  ORACLE-09.
- ORACLE-06 identity binds the Coffee Shop camera lock at scroll2-X 768 through
  frame 4994, first unlock at 4995, and the next lock at 944 on frame 5071.
  The generalized unlock guard remains unknown and cannot be replaced with a
  guessed screen-X, timer, or kill rule.
- The public report is `data/oracle08_round1_navigation_bounds.json`, SHA-256
  `db7c9897d27920564855a1abd355d23bc83a00bbb1c5536a120a29f1352c444f`,
  at evidence commit `718c2986060e4264defa9e54c613670bd89c0fa8`.
  `Fast` and `Oracle` pass. Saturn emulator and physical Saturn remain `UNRUN`;
  no production gameplay path changed.
