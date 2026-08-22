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

`SALVAGE-03-COLLISION` is accepted at
`cd31823d82024b6e33a25e8963ded5493c204772`. The active card is `V2-B1`, status
`READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`, based on `project_state.production_head`
`033be384bcc4e678408b465f102925841eab4333`. Promote only the accepted exact
class `0x1F` HIT/KO behavior behind `src/port_v2/combat/hit_ko`, with strict host
differentials and a real substitution negative control. Do not broaden into
attack, damage, AI, route, camera/stage, HUD, PCM, or unrelated collision work.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal from V2-B1 in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; read the required controls, preserve every protected worktree and approved lock, promote only the accepted exact class 0x1F HIT/KO behavior behind src/port_v2/combat/hit_ko with strict host differentials and a real substitution negative control, then commit, push to private-origin, and verify the remote SHA.
