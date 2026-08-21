# USER-04-STAGE-REVIEW task card

TASK: USER-04-STAGE-REVIEW
KIND: USER_REVIEW
STATUS: BLOCKED
CHECKPOINT: review-stage
BASE: project_state.accepted_head
BRANCH: codex/avp-user-04-stage-review
TIER: 0
DEPENDENCIES: [SALVAGE-04-CAMERA-STAGE-LAYERS]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-05-HUD-PCM, INTEGRATE-03-PLAYABLE-SLICE]

## Objective

Present the self-reviewed camera/stage bench and wait for explicit visual/feel feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-04-STAGE-REVIEW/**`
- Stage/camera user-feedback migration fields and review state only

## Existing systems to reuse

- Exact SALVAGE-04 evidence package.

## Systems deliberately disabled

- All camera, stage, palette, priority, framing, and actor changes.

## Focused machine checks

- Verify package identity, readback, and completeness.

## Saturn build profile

Reuse exact `CameraStageSalvageBench` image.

## Emulator readback

Reuse SALVAGE-04 readback only.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record exact response and derived approvals/changes/priority.

## Exclusions

- No implementation or inferred approval.

## Hard stops

- Missing evidence or feedback; set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- A bounded stage `REPAIR` or promotion card after feedback.
- `SALVAGE-05-HUD-PCM` may proceed while pending.
