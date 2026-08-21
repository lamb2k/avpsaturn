# USER-01-PLAYER-BASELINE-REVIEW task card

TASK: USER-01-PLAYER-BASELINE-REVIEW
KIND: USER_REVIEW
STATUS: AWAITING_USER_FEEDBACK
CHECKPOINT: review-player-baseline
BASE: project_state.accepted_head
BRANCH: codex/avp-user-01-player-review
TIER: 0
DEPENDENCIES: [SALVAGE-01-PLAYER-LOAD-RENDER-INPUT]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-01-PLAYER-PIPELINE, SALVAGE-02-ENEMY-RENDER-ANIMATION]

## Objective

Present the self-reviewed player bench and wait for explicit component-scoped feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-01-PLAYER-BASELINE-REVIEW/**`
- Player entries in `data/port_v2_migration_map.yaml`
- `project_state.yaml` and this card for review state only

## Existing systems to reuse

- Exact SALVAGE-01 build, screenshot/clip, emulator readback, profile/commit, active/disabled systems, adaptations, and stability notes.

## Systems deliberately disabled

- All implementation and all changes to the reviewed output.

## Focused machine checks

- Verify the package binds the exact bench commit/profile and contains every practical contract item.

## Saturn build profile

Reuse the exact `PlayerSalvageBench` image; do not rebuild behavior.

## Emulator readback

Reuse and verify SALVAGE-01 readback; do not manufacture new acceptance evidence.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record the exact response; derive approved components, changes, priority, and next bounded card. Silence is not approval.

## Exclusions

- No code, asset, palette, pivot, animation, or feel correction.

## Hard stops

- Missing/mismatched evidence package or no user response. Set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- `PROMOTE-01-PLAYER-PIPELINE` after approval.
- `SALVAGE-02-ENEMY-RENDER-ANIMATION` may proceed while feedback is pending because it cannot alter the player package.
