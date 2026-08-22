# USER-08-FRONTEND task card

TASK: USER-08-FRONTEND
KIND: USER_REVIEW
STATUS: BLOCKED
CHECKPOINT: review-frontend
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [QA-08-FRONTEND]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-08-FRONTEND, ORACLE-01-FULL-REFERENCE-ROUTE, ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX, ORACLE-03-ENDING-CREDITS-DELTAS]

## Objective

Present the ignored frontend evidence package and wait for exact user feedback.
Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-08-FRONTEND/**`
- Exact feedback, approval-lock, review-state, and coverage fields only

## Existing systems to reuse

- Exact QA-08 package, candidate identity, captures, readback, and limitations.

## Systems deliberately disabled

- All implementation, asset, scene, input, route, loading, and audio changes.

## Focused machine checks

- Verify package identity and completeness only.

## Saturn build profile

Reuse the exact QA-08-reviewed frontend image.

## Emulator readback

Reuse QA-08 readback only; do not create new acceptance evidence.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"
Record the exact response. Silence is not approval. Set
`AWAITING_USER_FEEDBACK` until the response is recorded.

## Exclusions

- No implementation and no approval inferred from emulator evidence or silence.

## Hard stops

- Missing package/evidence identity or pending user feedback.

## Next eligible cards

- `PROMOTE-08-FRONTEND` only after explicit approval or an exact bounded repair.
- The three read-only Oracle cards may proceed while feedback is pending because
  they cannot alter the reviewed frontend result.
