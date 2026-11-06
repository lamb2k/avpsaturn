# USER-07-CDDA-RESIDENCY-REVIEW task card

TASK: USER-07-CDDA-RESIDENCY-REVIEW
KIND: USER_REVIEW
STATUS: ACCEPTED
CHECKPOINT: review-cdda-residency
BASE: project_state.candidate_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [SALVAGE-07-CDDA-RESIDENCY]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-07-CDDA-RESIDENCY]

## Objective

Present the exact ignored SALVAGE-07 audible package and wait for explicit
feedback about the bounded Track 2 cue. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-07-CDDA-RESIDENCY-REVIEW/**`
- CDDA/residency user-feedback fields and review state only

## Existing systems to reuse

- Exact `CddaResidencySalvageBench` image, cue, Track 2 WAV, committed build
  record, paired pinned-emulator readback, and diagnostic screenshot.

## Systems deliberately disabled

- All CDDA, loading, residency, route, PCM, gameplay, and presentation changes.

## Focused machine checks

- Verify package identity, source commit, normalized image, Track 2 payload,
  readback, and explicit physical-evidence boundary.

## Saturn build profile

Reuse the exact committed `CddaResidencySalvageBench` image. Do not rebuild or
alter the reviewed result.

## Emulator readback

Reuse SALVAGE-07 run 1 and run 2 only. The package and review are one-emulator
evidence, not physical Saturn proof.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record the exact response and derived approvals, requested changes, and priority. Silence is not approval.

## Exclusions

- No implementation, inferred approval, source-timing promotion, second-emulator
  claim, normal-release claim, full-route claim, or physical Saturn claim.

## Hard stops

- Missing/mismatched package evidence or no exact feedback. Remain
  `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- `PROMOTE-07-CDDA-RESIDENCY` only after explicit audible approval.
- A bounded CDDA `REPAIR` card if the exact response requests a correction.

## Current review state

- Package: `build/feedback/USER-07-CDDA-RESIDENCY-REVIEW/`.
- Implementation commit: `17967a50b62318dae81d12f33c18b92ce8f72b37`.
- Normalized ISO SHA-256:
  `46ffc83235340f48e7636692cd8c207d7a58285890af6bccdba348e10d2d8698`.
- Track 2 WAV SHA-256:
  `42e755b02ba0e59e514a07dabe2f8273390e641c2ab410e4af8b7f1b656f2a43`.
- Review status: `APPROVED` only for the bounded audible result described below.

## Review result

- Exact response: `yup that works keep going with the next body of work`.
- Disposition: `APPROVED` for the bounded Track 2 audible output presented in
  the exact USER-07 package.
- Requested changes: none.
- Priority: continue with `PROMOTE-07-CDDA-RESIDENCY`.
- Evidence boundary: approval does not establish exact source music timing,
  full-route or normal-release integration, second-emulator evidence, or
  physical Saturn proof.
