# SALVAGE-01-PLAYER-LOAD-RENDER-INPUT task card

TASK: SALVAGE-01-PLAYER-LOAD-RENDER-INPUT
KIND: SALVAGE
STATUS: ACCEPTED
CHECKPOINT: salvage-player-baseline
BASE: project_state.accepted_head
BRANCH: codex/avp-salvage-01-player-pipeline
TIER: 1
DEPENDENCIES: [SALVAGE-00-OLD-BUILD-BASELINE]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-01-PLAYER-BASELINE-REVIEW, SALVAGE-02-ENEMY-RENDER-ANIMATION]

## Objective

Bench loading/memory ownership, controller input, player assets, player rendering, and player animation independently, then together in one diagnostic.

## Owned paths

- `tests/port_v2/player_bench/**`
- Card-scoped player diagnostic/readback code and generated test assets
- Relevant migration-ledger entries and card/state updates

## Existing systems to reuse

- Old loading/build/input, player asset, animation, VDP1, palette, and diagnostic systems.
- Read-only prototype player and diagnostic deltas.

## Systems deliberately disabled

- Enemy, collision, damage, HIT/KO, camera movement, HUD, PCM, and CDDA.

## Focused machine checks

- Touched-code strict compile and focused loading/input/animation/render tests.
- Deterministic repeat.
- Missing asset plus stuck-input or mutated-duration negative controls.
- Canary, actor-position, pivot, render-count, and command diagnostics.

## Saturn build profile

Dedicated `PlayerSalvageBench` diagnostic.

## Emulator readback

Require runtime-ready, asset failure, sampled input edges, allocation/canary state, player position, pose, pivot, render count, and bounded stability.

## Human-review requirement

Required after AI self-review through `USER-01-PLAYER-BASELINE-REVIEW`.

## Exclusions

- No production interface promotion or authored gameplay acceptance.

## Hard stops

- Missing source identity, unsafe worktree state, material memory/renderer architecture decision, or exhausted correction cycle.

## Next eligible cards

- `USER-01-PLAYER-BASELINE-REVIEW`
- `SALVAGE-02-ENEMY-RENDER-ANIMATION` is dependency-safe while player feedback is pending.
