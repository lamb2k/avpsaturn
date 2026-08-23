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

`PROMOTE-06-PCM` is accepted at
`5fc2b8ff00d7074da8f58697e4a1761ed282db58`. The approved capture-exact
Predator melee cue now flows through a bounded Jo/SGL-free semantic PCM
interface and a declared temporary SCSP adapter. Two committed-SHA builds and
paired pinned-Yaba readbacks agree at normalized ISO
`aecbd1b9169776c5a312028133279c89c9596f2cfa568734c643a16899306566`;
cue identity, 147/150/200 and 387/390/440 timing, channel 1 allocation, canaries,
zero underruns, and the promoted HUD regression lock all pass. No new subjective
audio or physical Saturn claim is made. The active card is
`SALVAGE-07-CDDA-RESIDENCY`, status `READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal at SALVAGE-07-CDDA-RESIDENCY in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve every promoted player, enemy, combat, camera/stage, P1/P2 HUD, and PCM lock, isolate only one CDDA/data-read ownership transition and one explicit phase residency manifest, then commit, push to private-origin, and verify the remote SHA.
