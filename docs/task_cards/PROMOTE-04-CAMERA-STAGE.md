# PROMOTE-04-CAMERA-STAGE task card

TASK: PROMOTE-04-CAMERA-STAGE
KIND: PROMOTE
STATUS: READY
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
