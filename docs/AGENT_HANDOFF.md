# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot

`ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN` initializes the four-character,
three-player, cold-boot-to-credits target without changing runtime behavior.
Future production cards use `production_head`; the already-active card keeps
its historical metadata and existing continuity branch.

## Preserved evidence work

- The dirty canonical and `prototype/avp-clean-playable-skeleton` worktrees
  remain untouched.
- V2-2B is accepted at evidence commit
  `597f4ed517d4e715d814ff841bd00d3977803f85`, merged into production continuity
  by `033be384bcc4e678408b465f102925841eab4333`, and remotely verified. This is
  host/static/MAME evidence only, not Saturn proof.
- `SALVAGE-00-OLD-BUILD-BASELINE` remains a technical baseline, not physical
  proof.
- `USER-01-PLAYER-BASELINE-REVIEW` and later explicit approvals remain
  component-scoped regression locks.

## Current task and next action

`INTEGRATE-02-COMBAT` is accepted at
`cc5f6999e8dd15146b739285db264b4b2ea45bfb`. It integrates four exact
source-measured contacts through the accepted player/enemy, collision, and
HIT/KO interfaces; strict host tests, the CombatIntegrationBench target build,
and paired pinned Yaba semantic readback pass. The active card is now
`REPAIR-03-COMBAT-ACTOR-ALIGNMENT`, status `READY`, in the existing continuity
worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`. USER-03 requested a durable correction
for player/enemy positioning, shared lane/ground alignment, and attack-facing
direction. Retained MAME frames 5190 and 5329 are sufficient for the bounded
source-relative transform; no fresh capture is currently required.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal from REPAIR-03-COMBAT-ACTOR-ALIGNMENT in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve every protected worktree and approved lock, derive the source-relative combat placement from retained MAME frames 5190 and 5329, reject the mixed generic/source transform, run the focused and pinned-emulator checks, then return corrected evidence to renewed USER-03 review.
