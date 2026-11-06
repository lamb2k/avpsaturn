# QA-08-FRONTEND task card

TASK: QA-08-FRONTEND
KIND: QA
STATUS: BLOCKED
CHECKPOINT: qa-frontend
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SALVAGE-08-FRONTEND]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-08-FRONTEND]

## Objective

Independently validate the frontend salvage package, deterministic interaction,
scene/load ownership, and presentation evidence before human review.

## Owned paths

- Frontend QA tests/reports, ignored review-package preparation, coverage
  fields, state, and card; no production implementation paths

## Existing systems to reuse

- Exact SALVAGE-08 candidate, manifests, input ledgers, readback, and captures.

## Systems deliberately disabled

- Implementation corrections, route expansion, and all gameplay behavior.

## Focused machine checks

- Repeat all focused claims; verify artifact identity; independently run one
  input/scene/line-scroll mutation control and approved-lock regressions.

## Saturn build profile

Reuse exact `FrontendSalvageBench` image; do not rebuild a different candidate.

## Emulator readback

Independently collect and compare the exact SALVAGE-08 image/readback.

## Human-review requirement

Prepare the ignored `build/feedback/USER-08-FRONTEND/**` package.

## Exclusions

- No implementation, inferred approval, or physical Saturn claim.

## Hard stops

- Candidate mismatch, missing negative control, incomplete review package, or
  nondeterministic readback.

## Next eligible cards

- `USER-08-FRONTEND`.
