# SALVAGE-02-ENEMY-RENDER-ANIMATION task card

TASK: SALVAGE-02-ENEMY-RENDER-ANIMATION
KIND: SALVAGE
STATUS: READY
CHECKPOINT: salvage-enemy-baseline
BASE: project_state.accepted_head
BRANCH: codex/avp-salvage-02-enemy-pipeline
TIER: 1
DEPENDENCIES: [SALVAGE-00-OLD-BUILD-BASELINE]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-02-ENEMY-BASELINE-REVIEW, SALVAGE-03-COLLISION]

## Objective

Bench class `0x1F` enemy assets, rendering, and animation first stationary and then with one deterministic translated position.

## Owned paths

- `tests/port_v2/enemy_bench/**`
- Card-scoped enemy diagnostic/readback code and generated test assets
- Relevant migration-ledger entries and card/state updates

## Existing systems to reuse

- Old enemy asset, animation, VDP1, palette, emission, diagnostic, and readback systems.
- Read-only prototype enemy deltas.

## Systems deliberately disabled

- Player behavior changes, collision/damage/HIT/KO, camera, HUD, PCM, and CDDA.

## Focused machine checks

- Strict compile; focused asset/animation/render tests; deterministic repeat; missing tile/bank and mutated-duration controls; actor position/pivot/render-count diagnostics.

## Saturn build profile

Dedicated `EnemySalvageBench` diagnostic.

## Emulator readback

Require runtime-ready, asset failure, enemy class/position/pose/pivot/render count/command identity, and stability.

## Human-review requirement

Required after AI self-review through `USER-02-ENEMY-BASELINE-REVIEW`.

## Exclusions

- No AI, collision, damage, exact HIT/KO, or production promotion.

## Hard stops

- Missing source identity, unsafe worktree state, material renderer architecture decision, or exhausted correction cycle.

## Next eligible cards

- `USER-02-ENEMY-BASELINE-REVIEW`
- `SALVAGE-03-COLLISION` is dependency-safe while enemy feedback is pending.
