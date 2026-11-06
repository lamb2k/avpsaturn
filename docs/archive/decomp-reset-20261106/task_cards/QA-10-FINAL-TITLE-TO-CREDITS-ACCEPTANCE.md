# QA-10-FINAL-TITLE-TO-CREDITS-ACCEPTANCE task card

TASK: QA-10-FINAL-TITLE-TO-CREDITS-ACCEPTANCE
KIND: QA
STATUS: BLOCKED
CHECKPOINT: qa-final-title-to-credits
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [QA-09-RELEASE-HARDENING]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
TERMINAL: true
NEXT_ELIGIBLE_CARDS: []

## Objective

Accept the exact release image from cold boot through credits for all four
playable characters and the declared one-, two-, and three-player matrix.

## Owned paths

- Final acceptance reports, immutable manifest/provenance archive, state, and card.

## Existing systems to reuse

- Exact QA-09 release candidate and complete approved evidence matrix.

## Systems deliberately disabled

- All implementation and scope changes.

## Focused machine checks

- Reproduce every required build, route, character, multiplayer, workload,
  negative-control, artifact, and provenance claim.

## Saturn build profile

Exact `release-normal-release` candidate with immutable identity.

## Emulator readback

Repeat the complete emulator matrix against that same image; keep it separate
from physical results.

## Human-review requirement

Require every declared explicit review response and approved-component lock.

## Exclusions

- No partial title, character, player-count, or evidence-tier substitution.

## Hard stops

- Any missing evidence, unknown required behavior, mismatch, instability,
  inferred approval, or relabeled non-physical proof.

## Next eligible cards

- None. This is the terminal release-acceptance card.
