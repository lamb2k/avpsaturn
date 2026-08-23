# PROMOTE-04-CAMERA-STAGE task card

TASK: PROMOTE-04-CAMERA-STAGE
KIND: PROMOTE
STATUS: ACCEPTED
CHECKPOINT: promote-camera-stage
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-02-COMBAT, USER-03-COMBAT-FEEL-REVIEW, SALVAGE-04-CAMERA-STAGE-LAYERS, USER-04-STAGE-REVIEW]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-05-HUD]

## Objective

Promote the approved adapted camera and two-plane stage presentation behind
bounded camera-state and render-port interfaces.

## Owned paths

- Future `src/port_v2/camera/**`, `src/port_v2/stage/**`, and focused tests
- Card-scoped wiring, readback, migration fields, state, and card

## Existing systems to reuse

- USER-04-approved camera/stage result, framing, priority, palette, and canaries.

## Systems deliberately disabled

- New stage content, row-scroll approximation, route progression, and gameplay.

## Focused machine checks

- Approved-lock regression, deterministic camera step/repeat, rejected priority
  or plane dependency, strict compile, and exact package identity.

## Saturn build profile

Dedicated `CameraStagePromotionBench`.

## Emulator readback

Require camera/scroll state, plane/PNT canaries, priority, framing, render
counts, asset failures, stability, and explicit adapted row-scroll status.

## Human-review requirement

No new review if approved output is unchanged; renew USER-04 for any visible risk.

## Exclusions

- No source-faithful row-scroll claim until measured and no physical claim.

## Hard stops

- Approved presentation regression, unsupported scroll dependency, or material
  route-interface decision.

## Next eligible cards

- `PROMOTE-05-HUD`.

## Accepted result

- Implementation commit:
  `b6ef0ceff9fc4ed8cf06948cc353e7ce67950d3c`.
- Production interfaces: `src/port_v2/camera/camera.h` and
  `src/port_v2/stage/stage.h`; neither depends on Jo Engine or SGL.
- Strict C90, deterministic repeat, and wrong-aperture, missing-plane,
  palette-dependency, and priority-inversion controls pass.
- Two committed-SHA `CameraStagePromotionBench` builds normalize to ISO
  SHA-256 `d4caec944c0f1f3f9593960073d037cc24f9fa31f1a207f5dc4f617fb000ce33`.
- Paired pinned Yaba Sanshiro 1.20.37-2986eb readbacks pass with identical
  semantic state after excluding only the emulator wall-frame counter.
- Fixed frame 20 remains `[0,7]` with 477 objects; frame 45 `[0,7]` advances
  to frame 46 `[10,15]`; plane/PNT canaries, CRAM 2/3, priority 2<3<4<6,
  port submissions, assets, and late-read guards all pass.
- Paired screenshots are byte-identical at SHA-256
  `288b63d3f02cd1def08e6fbfdeab18badd1ddf52628436c4685a4e4df38768aa`;
  no renewed user review is required.
- Row-scroll remains `ADAPTED_UNCAPTURED`; normal release, a second emulator,
  and physical Saturn remain `UNRUN`.
