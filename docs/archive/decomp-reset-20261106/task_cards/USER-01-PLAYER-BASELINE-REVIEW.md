# USER-01-PLAYER-BASELINE-REVIEW task card

TASK: USER-01-PLAYER-BASELINE-REVIEW
KIND: USER_REVIEW
STATUS: ACCEPTED
CHECKPOINT: review-player-baseline
BASE: project_state.accepted_head
BRANCH: codex/avp-user-01-player-review
TIER: 0
DEPENDENCIES: [SALVAGE-01-PLAYER-LOAD-RENDER-INPUT, REPAIR-01-PLAYER-CROP-PIVOT]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REPAIR-01-PLAYER-CROP-PIVOT, PROMOTE-01-PLAYER-PIPELINE, SALVAGE-02-ENEMY-RENDER-ANIMATION]

## Objective

Present the self-reviewed player bench and wait for explicit component-scoped feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-01-PLAYER-BASELINE-REVIEW/**`
- Player entries in `data/port_v2_migration_map.yaml`
- `project_state.yaml` and this card for review state only

## Existing systems to reuse

- Exact corrected REPAIR-01 build, screenshot/clip, emulator readback, profile/commit, full idle/walk bounds, active/disabled systems, adaptations, and stability notes.

## Systems deliberately disabled

- All implementation and all changes to the reviewed output.

## Focused machine checks

- Verify the package binds the exact bench commit/profile and contains every practical contract item.

## Saturn build profile

Reuse the exact corrected `PlayerSalvageBench` image; do not rebuild behavior.

## Emulator readback

Reuse and verify REPAIR-01 readback; do not manufacture new acceptance evidence.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record the exact response; derive approved components, changes, priority, and next bounded card. Silence is not approval.

## Exclusions

- No code, asset, palette, pivot, animation, or feel correction.

## Hard stops

- Missing/mismatched evidence package or no user response. Set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- `REPAIR-01-PLAYER-CROP-PIVOT` is required by the exact crop feedback.
- `PROMOTE-01-PLAYER-PIPELINE` after approval.
- `SALVAGE-02-ENEMY-RENDER-ANIMATION` may proceed while feedback is pending because it cannot alter the player package.

## Prior review result

- Exact response: `the character sprite is cropped but moving.`
- Disposition: `CHANGES_REQUESTED` for player rendering.
- Requested change and first priority: restore the full visible player sprite by repairing its crop/pivot placement.
- The observed movement is recorded but is not inferred as approval of animation, input feel, or rendering.
- Approved components: none.
- Next bounded card: `REPAIR-01-PLAYER-CROP-PIVOT`.

## Corrected package awaiting review

- REPAIR-01 commit: `76e497b1bcadc2b4ff8326bc855f7cef1bc7d336`.
- Paired normalized ISO SHA-256: `7a9326d08607813fb88fb969de5f8f92b233649575e694b742e87141c6f28ef6`.
- Idle canvas bounds: `(56,74)-(136,184)`; sampled walk bounds: `(28,88)-(152,184)`.
- The rejected pivot reproduces bottom `232` and is rejected by the negative control.
- A new exact response is required; the prior response does not approve the corrected output.

## Current review result

- Exact response: `Looks good keep going`
- Disposition: `APPROVED` for the corrected player package.
- Approved components: corrected full-visible player image/pivot/palette and fixed-background presentation; shown idle/walk animation presentation; demonstrated right/down-lane/left movement and facing behavior.
- Requested changes: none.
- Evidence boundary: approval does not include enemy pixels, combat, camera, HUD, audio, normal-release, or physical Saturn proof.
- Next bounded card: `PROMOTE-01-PLAYER-PIPELINE`.
