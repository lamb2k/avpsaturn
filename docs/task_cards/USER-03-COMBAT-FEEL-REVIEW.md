# USER-03-COMBAT-FEEL-REVIEW task card

TASK: USER-03-COMBAT-FEEL-REVIEW
KIND: USER_REVIEW
STATUS: AWAITING_USER_FEEDBACK
CHECKPOINT: review-combat-feel
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [INTEGRATE-02-COMBAT]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-04-CAMERA-STAGE, ORACLE-01-FULL-REFERENCE-ROUTE, ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX, ORACLE-03-ENDING-CREDITS-DELTAS]

## Objective

Present self-reviewed combat evidence and wait for explicit feel feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-03-COMBAT-FEEL-REVIEW/**`
- Combat/user-feedback migration fields and review state only

## Existing systems to reuse

- Exact INTEGRATE-02 screenshot/clip, readback, profile/commit, systems, adaptations, and pacing notes.

## Systems deliberately disabled

- All combat or presentation changes.

## Focused machine checks

- Verify evidence identity, deterministic machine claims, and package completeness.

## Saturn build profile

Reuse exact `CombatIntegrationBench` image.

## Emulator readback

Reuse INTEGRATE-02 readback only.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record exact response and derived approvals/changes/priority.

## Exclusions

- No implementation or inferred approval.

## Hard stops

- Missing evidence or feedback; set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- A bounded combat `REPAIR` card if requested; otherwise
  `PROMOTE-04-CAMERA-STAGE`.
- The three read-only Oracle cards may proceed while pending because they cannot
  alter the reviewed combat result.
