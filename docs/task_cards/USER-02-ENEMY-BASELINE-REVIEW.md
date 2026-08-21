# USER-02-ENEMY-BASELINE-REVIEW task card

TASK: USER-02-ENEMY-BASELINE-REVIEW
KIND: USER_REVIEW
STATUS: BLOCKED
CHECKPOINT: review-enemy-baseline
BASE: project_state.accepted_head
BRANCH: codex/avp-user-02-enemy-review
TIER: 0
DEPENDENCIES: [SALVAGE-02-ENEMY-RENDER-ANIMATION]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-02-ENEMY-PIPELINE, SALVAGE-03-COLLISION]

## Objective

Present the self-reviewed enemy bench and wait for explicit feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-02-ENEMY-BASELINE-REVIEW/**`
- Enemy entries in the migration map
- State/card review fields only

## Existing systems to reuse

- Exact SALVAGE-02 evidence package.

## Systems deliberately disabled

- All implementation and changes to reviewed enemy output.

## Focused machine checks

- Verify package/profile/commit/readback identity and contract completeness.

## Saturn build profile

Reuse exact `EnemySalvageBench` image.

## Emulator readback

Reuse SALVAGE-02 readback only.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record exact feedback and derived approvals/changes/priority.

## Exclusions

- No implementation or inferred approval; no code, asset, palette, pivot,
  cadence, or movement correction.

## Hard stops

- Missing evidence or feedback; set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- `PROMOTE-02-ENEMY-PIPELINE` after approval.
- `SALVAGE-03-COLLISION` may proceed while feedback is pending.
