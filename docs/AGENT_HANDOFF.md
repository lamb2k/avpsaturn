# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot

Future production cards continue sequentially from `production_head`.

## Preserved evidence work

- The dirty canonical and `prototype/avp-clean-playable-skeleton` worktrees
  remain untouched.
- V2-2B is accepted at evidence commit
  `597f4ed517d4e715d814ff841bd00d3977803f85`, merged into production continuity
  by `033be384bcc4e678408b465f102925841eab4333`, and remotely verified. This is
  host/static/MAME evidence only, not Saturn proof.
- `SALVAGE-00-OLD-BUILD-BASELINE` remains a technical baseline only.
- `USER-01-PLAYER-BASELINE-REVIEW` and later explicit approvals remain
  component-scoped regression locks.

## Current task and next action

REPAIR-09 is accepted at `417ed808e10f0f255948b1e6ecf0223399509c74`.
Its interface version 2 binds selector-specific presentation, collision,
damage, and the class-`0x1F` reaction to one independent MAME source event.
The active card is `INTEGRATE-03-PLAYABLE-SLICE`, status `READY` and user
`APPROVED` for `SOURCE_BOUND_WITH_ADAPTED_INPUT`, in
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review`
on `codex/avp-user-02-enemy-review`. Candidate
`82965ef80223a03937e0b527d16161ed68d874a0` consumes the accepted source-bound
interface. Its exact normal-release ISO is
`4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`;
paired 577-sample traces, 297 cadence-1 combat frames, source mutations, visual
QA, and Full pass. Task fidelity is `ADAPTED` (`SOURCE_BOUND_WITH_ADAPTED_INPUT`):
six combat components are measured, while input choreography is adapted. The
actor comparator passes 297 frames and five mutations; all seven calculated
same-assembly flags were directly inspected. The exact approval is recorded
verbatim in the task card, state, and migration ledger. Preserve every named
component lock; add no comparator machinery without a concrete discrepancy.
All approved locks remain preserved. Physical Saturn is still `0/12` and
`UNRUN`: no Windows-visible Saturn loader/removable target or capture device was
detected, and the required Probe 3 representative/909-tile physical executable
is absent. This is a required-interaction/missing-evidence hard stop;
`SALVAGE-08-FRONTEND` remains inactive.

Resume prompt:

> Resume the AvP salvage Goal at the INTEGRATE-03 physical hard stop in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve exact ISO 4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef and all user-approved locks, connect and identify the declared Saturn/cart/loader/pad/capture setup, run Probe 3 representative/909-tile plus overload control, then execute the exact-image capability record twice and ten-minute soak; keep physical evidence UNRUN and SALVAGE-08 inactive until every physical condition passes.
