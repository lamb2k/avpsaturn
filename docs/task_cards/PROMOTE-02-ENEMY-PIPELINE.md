# PROMOTE-02-ENEMY-PIPELINE task card

TASK: PROMOTE-02-ENEMY-PIPELINE
KIND: PROMOTE
STATUS: ACCEPTED
CHECKPOINT: promote-enemy-pipeline
BASE: project_state.accepted_head
BRANCH: codex/avp-user-02-enemy-review
TIER: 1
DEPENDENCIES: [SALVAGE-02-ENEMY-RENDER-ANIMATION, USER-02-ENEMY-BASELINE-REVIEW]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-01-PLAYER-AND-ENEMY]

## Objective

Promote approved enemy assets, rendering, animation, and one deterministic movement input behind `port_v2` interfaces.

## Owned paths

- `src/port_v2/enemy/**`
- `tests/port_v2/enemy/**`
- Card-scoped build/readback, migration ledger, state, and card

## Existing systems to reuse

- Only approved SALVAGE-02 components and recorded adapter/repair decisions.

## Systems deliberately disabled

- Collision, damage, HIT/KO, camera, HUD, PCM, and CDDA.

## Focused machine checks

- Strict interface compile, deterministic regressions, approval locks, and adapter mutation control.

## Saturn build profile

Dedicated `EnemyPromotionBench` diagnostic.

## Emulator readback

Require approved enemy position/pose/pivot/render-count invariants and stability.

## Human-review requirement

Renewed review is required before changing any approved enemy presentation or feel.

## Exclusions

- No AI expansion or combat behavior.

## Hard stops

- Approved invariant risk, unresolved authored-controller coupling, or material architecture decision.

## Next eligible cards

- `INTEGRATE-01-PLAYER-AND-ENEMY` after PROMOTE-01.
