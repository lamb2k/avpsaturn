# USER-10-ROUND1-PLAYTHROUGH-REVIEW task card

TASK: USER-10-ROUND1-PLAYTHROUGH-REVIEW
KIND: USER_REVIEW
STATUS: BLOCKED
CHECKPOINT: review-round1-playthrough
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [QA-13-ROUND1-END-TO-END-DIFFERENTIAL]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-08-FRONTEND]

## Objective

Present source and Saturn full-speed Round 1 playthroughs, the interactive image
and controls, source-closure coverage, native-C systems, explicit adaptations
and unknowns, route/enemy/boss/collision/navigation evidence, corrected
objective discrepancies, and physical status for explicit user review. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-10-ROUND1-PLAYTHROUGH-REVIEW/**`
- Exact feedback, approval locks, review/migration/coverage state, and this card

## Existing systems to reuse

- Exact QA-13 candidate and continuous source/Saturn evidence only.

## Systems deliberately disabled

- All implementation, frontend, other characters, multiplayer, later stages,
  new evidence tiers, and physical-status changes.

## Focused machine checks

- Verify candidate/package identity, controls, completion-route coverage,
  discrepancy disposition, and the distinction between emulator and physical
  proof.

## Saturn build profile

Reuse the exact QA-13 image; do not rebuild behavior.

## Emulator readback

Reuse QA-13 continuous evidence only; create no new acceptance tier.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"
Remain `AWAITING_USER_FEEDBACK` until explicit feedback. Silence is not approval.
Playthrough completion, emulator output, or prior review is not approval.

## Exclusions

- No implementation, inferred acceptance, frontend activation, physical claim,
  other-character scope, multiplayer, or full-game claim.

## Hard stops

- Missing/mismatched playthroughs or image, noninteractive evidence, missing
  coverage/discrepancy status, or pending user feedback.

## Next eligible cards

- `SALVAGE-08-FRONTEND` only after explicit USER-10 acceptance. Otherwise create
  only the bounded correction required by recorded feedback.
