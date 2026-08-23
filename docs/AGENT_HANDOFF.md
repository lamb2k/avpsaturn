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

`SALVAGE-07-CDDA-RESIDENCY` is technically accepted at
`17967a50b62318dae81d12f33c18b92ce8f72b37`. Two committed-SHA pinned-Yaba
runs agree at normalized ISO
`46ffc83235340f48e7636692cd8c207d7a58285890af6bccdba348e10d2d8698`:
Track 2 ownership starts and returns, one late read and one illegal window are
rejected, the declared legal read succeeds, all phase allocations are explicit,
and the canaries and linked high-water pass. The binding to source frame 2520 is
`ADAPTED`, and physical Saturn remains unrun. The exact USER-07 response is
`yup that works keep going with the next body of work`, explicitly approving
the bounded Track 2 audible result with no requested change. The active card is
now `PROMOTE-07-CDDA-RESIDENCY`, status `READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal at PROMOTE-07-CDDA-RESIDENCY in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve every approved component and the exact USER-07 Track 2 approval, promote only the accepted CDDA ownership and phase-residency contracts behind narrow port_v2 interfaces, then run the card's focused, Target, and pinned-emulator checks.
