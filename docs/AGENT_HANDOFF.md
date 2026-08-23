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

`PROMOTE-07-CDDA-RESIDENCY` is accepted at evidence commit
`684ed1b27e840ac940bc95484b32d7f6e3972a01` with implementation commit
`89f60047a7a43542e194e8fd745724e74d9f70df`. Two committed-SHA pinned-Yaba
runs agree semantically at normalized ISO
`e99bd3a5cdc79b922222c25d65010d6fed011829cd89c3688b268f71774f8f74`:
both Jo/SGL-free production interfaces are version 1, the port lock and canaries
pass, fallback/failures are zero, both illegal operations reject, the declared
legal read succeeds, and each run observes 692 bounded stability frames. Linked
BSS ends at `0x06088370` with 228496 bytes of headroom. The source-frame binding
remains `ADAPTED`; normal release and physical Saturn remain unrun. The active
card is now `INTEGRATE-03-PLAYABLE-SLICE`, status `READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal at INTEGRATE-03-PLAYABLE-SLICE in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve every approved component lock, integrate only the promoted player, enemy, combat, camera/stage, HUD, PCM, CDDA, and residency interfaces, run the card's exact normal-release checks, and stop at the declared subjective or physical checkpoint.
