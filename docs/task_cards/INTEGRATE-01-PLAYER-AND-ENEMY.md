# INTEGRATE-01-PLAYER-AND-ENEMY task card

TASK: INTEGRATE-01-PLAYER-AND-ENEMY
KIND: INTEGRATE
STATUS: ACCEPTED
CHECKPOINT: integrate-player-enemy
BASE: project_state.accepted_head
BRANCH: codex/avp-user-02-enemy-review
TIER: 1
DEPENDENCIES: [PROMOTE-01-PLAYER-PIPELINE, PROMOTE-02-ENEMY-PIPELINE]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-03-COLLISION, SALVAGE-04-CAMERA-STAGE-LAYERS]

## Objective

Combine promoted player and enemy pipelines with one promoted background, adding no combat behavior.

## Owned paths

- `src/port_v2/integration/player_enemy/**`
- `tests/port_v2/integration/player_enemy/**`
- Card-scoped diagnostic/readback, ledger, state, and card

## Existing systems to reuse

- Approved promoted player and enemy interfaces plus a fixed bench background.

## Systems deliberately disabled

- Collision, attack, damage, HIT/KO, camera motion, HUD, PCM, and CDDA.

## Focused machine checks

- Strict compile; player/enemy regression locks; deterministic co-residency/render-order repeat; one missing-dependency or order perturbation.

## Saturn build profile

Dedicated `PlayerEnemyIntegration` diagnostic.

## Emulator readback

Require both approved actor invariants, render order/count, memory canaries, asset failure, and stability.

## Human-review requirement

No new review if both approved outputs remain unchanged; otherwise renew the affected review.

## Exclusions

- No combat or behavior expansion.

## Hard stops

- Any approved component regression, memory-ownership collision needing architecture change, or exhausted correction cycle.

## Next eligible cards

- `SALVAGE-03-COLLISION`
- `SALVAGE-04-CAMERA-STAGE-LAYERS`
