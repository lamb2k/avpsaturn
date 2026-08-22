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

`V2-B1` is accepted at `893268e8039195d2db572030905fc5e468fcabb2`.
It promotes only the exact class `0x1F` HIT/KO traces behind
`src/port_v2/combat/hit_ko/hit_ko.h`; host, Saturn diagnostic, and paired pinned
Yaba readback pass, while normal release and physical Saturn remain UNRUN.
The active card is `INTEGRATE-02-COMBAT`, status `READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`, based on `project_state.production_head`
`893268e8039195d2db572030905fc5e468fcabb2`. Integrate attack, contact,
collision, damage, HIT, and KO one bounded behavior at a time through the
accepted interfaces. Do not add AI, stage expansion, HUD, PCM, or CDDA.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal from INTEGRATE-02-COMBAT in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; read the required controls, preserve every protected worktree and approved lock, integrate attack, contact, collision, damage, HIT, and KO one bounded behavior at a time through the accepted interfaces, run the required host, Oracle, Saturn diagnostic, and pinned-emulator checks, then stop at USER-03 for exact feedback.
