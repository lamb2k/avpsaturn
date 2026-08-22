# SALVAGE-04-CAMERA-STAGE-LAYERS task card

TASK: SALVAGE-04-CAMERA-STAGE-LAYERS
KIND: SALVAGE
STATUS: READY
CHECKPOINT: salvage-camera-stage
BASE: project_state.accepted_head
BRANCH: codex/avp-salvage-04-camera-stage
TIER: 1
DEPENDENCIES: [SALVAGE-00-OLD-BUILD-BASELINE]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-04-STAGE-REVIEW, SALVAGE-05-HUD-PCM]

## Objective

Bench camera, VDP2 stage layers, priority, palette ownership, and 384-to-352 framing at a fixed checkpoint and one deterministic scroll step.

## Owned paths

- `tests/port_v2/stage_bench/**`
- Card-scoped stage diagnostic/readback and test assets
- Stage/camera/palette migration entries, state, and card

## Existing systems to reuse

- Existing scene/route/CRAM/street-plane/scanout systems and source stage evidence.

## Systems deliberately disabled

- Combat changes, HUD, PCM, CDDA, frontend presentation, and broad stage progression.

## Focused machine checks

- Strict compile; fixed and threshold scroll tests; deterministic repeat; missing plane/stale disc/priority perturbation; final-scanout and CRAM readback.

## Saturn build profile

Dedicated `CameraStageSalvageBench` diagnostic.

## Emulator readback

Require runtime-ready, asset failure, camera/scroll, layer/priority/palette, framing/scanout, render counts, and stability.

## Human-review requirement

Required after AI self-review through `USER-04-STAGE-REVIEW`.

## Exclusions

- No production promotion or full-route stage work.

## Hard stops

- Missing source evidence, approved actor output at risk, material VDP ownership decision, or exhausted correction cycle.

## Next eligible cards

- `USER-04-STAGE-REVIEW`
- `SALVAGE-05-HUD-PCM` may proceed while stage feedback is pending.
