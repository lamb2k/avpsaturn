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

`PROMOTE-04-CAMERA-STAGE` is accepted at
`b6ef0ceff9fc4ed8cf06948cc353e7ce67950d3c`. The approved two-plane
composition now flows through bounded Jo/SGL-free camera and stage interfaces.
Two committed-SHA builds and paired pinned-Yaba readbacks agree at normalized
ISO `d4caec944c0f1f3f9593960073d037cc24f9fa31f1a207f5dc4f617fb000ce33`;
fixed framing, scroll, CRAM, priorities, plane/PNT canaries, and byte-identical
screenshots retain USER-04's exact `pass for camera and stage` lock. Row-scroll
remains `ADAPTED_UNCAPTURED`, and physical Saturn remains `UNRUN`. The active
card is `PROMOTE-05-HUD`, status `READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal at PROMOTE-05-HUD in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve every approved player, enemy, combat, promoted camera/stage, P1/P2 HUD, and PCM lock, promote only the approved corrected P1 and active P2 HUD behind a semantic interface, then commit, push to private-origin, and verify the remote SHA.
