# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot

Future production cards use `production_head` on the existing continuity line.

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

REPAIR-09 is accepted at implementation
`417ed808e10f0f255948b1e6ecf0223399509c74`. Its interface version 2 binds
selector-specific player presentation, collision, damage, and the matching
class-`0x1F` alien reaction to one independently captured MAME source event.
The four contacts reproduce relative offsets `0/46/93/139`; wrong-but-valid
object/tile families, palette, and selector mutations reject. Fast, focused
C90, applicable Oracle checks, two deterministic Target builds, paired pinned
emulator readbacks, and paired 297-frame visual captures pass. The generic
Oracle wrapper remains `INCOMPLETE` only for protected V2-2B private writer
inputs absent from this continuity worktree.

The active card is again `INTEGRATE-03-PLAYABLE-SLICE`, status `READY` for its
still-`CHANGES_REQUESTED` correction, in
`C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-user-02-enemy-review`
on `codex/avp-user-02-enemy-review`. It must replace its stitched choreography
with the accepted source-bound interface, rebuild the complete
`release-normal-release` scene, rerun Full, and stop for renewed explicit human
review. Do not relabel the repair bench as acceptance of INTEGRATE-03.

All approved locks remain preserved. Physical Saturn is still `0/12` and
`UNRUN`; `SALVAGE-08-FRONTEND` remains inactive.

Resume prompt:

> Resume the AvP salvage Goal at INTEGRATE-03-PLAYABLE-SLICE in the existing AvPSaturnCapabilityTest-user-02-enemy-review worktree on codex/avp-user-02-enemy-review; consume accepted REPAIR-09 implementation 417ed808e10f0f255948b1e6ecf0223399509c74 through the slice-owned paths, replace the stitched choreography with the source-bound selector/collision/damage/reaction pipeline, preserve every approved lock, rebuild the complete normal-release scene, rerun Full, and stop for renewed explicit human review before physical Saturn or SALVAGE-08.
