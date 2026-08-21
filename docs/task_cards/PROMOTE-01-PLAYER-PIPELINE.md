# PROMOTE-01-PLAYER-PIPELINE task card

TASK: PROMOTE-01-PLAYER-PIPELINE
KIND: PROMOTE
STATUS: BLOCKED
CHECKPOINT: promote-player-pipeline
BASE: project_state.accepted_head
BRANCH: codex/avp-promote-01-player-pipeline
TIER: 1
DEPENDENCIES: [SALVAGE-01-PLAYER-LOAD-RENDER-INPUT, USER-01-PLAYER-BASELINE-REVIEW]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-01-PLAYER-AND-ENEMY, SALVAGE-04-CAMERA-STAGE-LAYERS]

## Objective

Promote approved loading, input, player asset, animation, and rendering decisions behind narrow `port_v2` interfaces.

## Owned paths

- `src/port_v2/player/**`
- `tests/port_v2/player/**`
- Card-scoped build/readback wiring, migration ledger, state, and card

## Existing systems to reuse

- Only SALVAGE-01 components explicitly approved or assigned an adapter/repair decision.

## Systems deliberately disabled

- Enemy, combat, camera, stage integration, HUD, PCM, and CDDA.

## Focused machine checks

- Strict interface compile, focused deterministic regressions, approval-lock checks, and adapter mutation negative control.

## Saturn build profile

Dedicated `PlayerPromotionBench` diagnostic.

## Emulator readback

Require the approved player invariants, runtime-ready, asset failure, input/pose/position/render count, and stability.

## Human-review requirement

No new review if output is byte/behavior equivalent to the approved package. Any approved behavior at risk requires renewed USER_REVIEW.

## Exclusions

- No silent change to approved scale, pivot, cadence, input feel, palette, or composition.

## Hard stops

- Interface cannot isolate authored-controller coupling, an approved invariant changes, or a material architecture decision is required.

## Next eligible cards

- `INTEGRATE-01-PLAYER-AND-ENEMY` after PROMOTE-02.
- `SALVAGE-04-CAMERA-STAGE-LAYERS` remains dependency-safe.
