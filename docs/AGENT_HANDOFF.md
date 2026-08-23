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

`PROMOTE-05-HUD` is accepted at
`d957b3b022e1e1d3598e04ee03b980e59bfe0c03`. The approved corrected P1 and
active P2 Maj. Schaefer HUD now flow through a bounded Jo/SGL-free semantic HUD
interface and a declared temporary legacy renderer adapter. Two committed-SHA
builds and paired pinned-Yaba readbacks agree at normalized ISO
`4039b82163492278e02e7e0f97a2f0bdc73737a4a728aa74dc70321a38f63782`;
P1/P2 states, one-based CRAM binding, render counts, canaries, negative controls,
and byte-identical screenshots retain USER-05's final exact `keep going` lock.
P2 gameplay/input/join/multitap and physical Saturn remain `UNRUN`. The active
card is `PROMOTE-06-PCM`, status `READY`, in the existing continuity worktree
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review` on
branch `codex/avp-user-02-enemy-review`.

The accepted camera/stage, corrected P1/P2 HUD, and short PCM cue remain locked.
Physical Saturn is still `0/12`; no host, MAME, emulator, or user evidence
changes that fact.

Resume prompt:

> Resume the AvP salvage Goal at PROMOTE-06-PCM in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; preserve every approved player, enemy, combat, camera/stage, promoted P1/P2 HUD, and PCM lock, promote only the approved short Predator melee PCM cue behind a semantic audio port, then commit, push to private-origin, and verify the remote SHA.
