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

`REPAIR-03-COMBAT-ACTOR-ALIGNMENT` is accepted at
`4abbc86f596c27d7873a96016c3e52c2d777edb4`. The retained MAME actor fields now
drive a durable source-relative 384-to-352 placement adapter; the old
coincident-X/misaligned baseline rejects, strict host/negative controls pass,
and two committed-SHA CombatIntegrationBench builds and pinned Yaba readbacks
agree at normalized ISO
`3c4096835741882f7a815483c47e37c9bcf2bfbb0ef3fb846ee2c20e67526b7b`. The
active card is renewed `USER-03-COMBAT-FEEL-REVIEW`, status
`AWAITING_USER_FEEDBACK`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`. The ignored corrected package is
`build/feedback/USER-03-COMBAT-FEEL-REVIEW/`. No successor implementation is
active and no user approval is inferred.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal at USER-03-COMBAT-FEEL-REVIEW in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; present the ignored corrected combat package, perform no implementation, record the exact response to the required review question, and activate only a predeclared dependency-safe successor after explicit feedback.
