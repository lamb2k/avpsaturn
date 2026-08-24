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

The active card is `INTEGRATE-03-PLAYABLE-SLICE`, status `READY` and still
`CHANGES_REQUESTED` pending renewed human review, in
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review`
on `codex/avp-user-02-enemy-review`. Candidate
`82965ef80223a03937e0b527d16161ed68d874a0` consumes the accepted source-bound
interface. Its exact normal-release ISO is
`4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`;
paired 577-sample traces, 297 cadence-1 combat frames, source mutations, visual
QA, and Full pass. The ignored package is
`build/feedback/INTEGRATE-03-PLAYABLE-SLICE`. Present it and record the exact
response; do not infer approval.

All approved locks remain preserved. Physical Saturn is still `0/12` and
`UNRUN`; `SALVAGE-08-FRONTEND` remains inactive.

Resume prompt:

> Resume the AvP salvage Goal at the renewed INTEGRATE-03 human-review checkpoint in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; present build/feedback/INTEGRATE-03-PLAYABLE-SLICE and record the exact response to the required review question, keep the candidate unaccepted until explicit approval, and do not begin physical Saturn or SALVAGE-08.
