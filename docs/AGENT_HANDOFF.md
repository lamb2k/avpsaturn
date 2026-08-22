# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot
## Preserved paused work

- The dirty primary canonical worktree remains untouched.
- The dirty `prototype/avp-clean-playable-skeleton` worktree remains intact.
- V2-2B remains `CORRECTIONS_REQUIRED` in its dirty correction worktree. Its
  blockers affect exact HIT/KO promotion, not this diagnostic salvage.
- `SALVAGE-00-OLD-BUILD-BASELINE` is accepted only as a technical build/emulator
  baseline: its physical Saturn state remains `UNRUN`, automatic window captures
  remain black, and the observed distorted enemy pixels are not visually accepted.

## Current task and next action

PROMOTE-01/USER-01-PLAYER-BASELINE-REVIEW locks remain accepted. USER-04 exact response was `pass for
camera and stage`; that presentation is locked, but row-scroll is uncaptured.

USER-05 final exact response is `keep going`. The corrected P1 HUD colors,
active P2 HUD presentation, and short Predator melee PCM cue are approved and
locked. P2 gameplay/input, joins, multiplayer, CDDA, normal release, a second
emulator, and physical Saturn remain `UNRUN`.

SALVAGE-05B remains technically accepted at
`6127957eee7ca419d39fe4b716dd41df2c255fb0`: active-P2 MAME routes repeat,
reject the P1-only `PRESS START` control, and paired clean builds/pinned Yaba
runs reproduce normalized ISO `127c2f04...a1035b34`. The P1/P2 HUD and PCM
locks must not change without renewed review.

SALVAGE-02 is technically accepted at
`17da61f6d647577fc19ac29e30bcbe624ff4d248`. Paired clean builds and pinned
Yaba runs reproduce normalized ISO `dbbb2678...3ea8c4` and screenshot
`c175ab98...acdae8`. Readback repeats class `0x1F`, palette `0x11`, stationary
`x=192`, translated `x=240`, five source objects, 32 rendered VDP1 tiles,
zero asset/late-read/tile misses, intact canaries, and two rejected missing
bank/rank controls. The tracked perturbation also rejects a 39-to-38-frame
walk-duration mutation. This is one-emulator evidence; physical Saturn is
`UNRUN`.

The active card is now `USER-02-ENEMY-BASELINE-REVIEW`, status
`AWAITING_USER_FEEDBACK`, on predeclared branch
`codex/avp-user-02-enemy-review`. Perform no implementation. Present the
ignored package at `build/feedback/USER-02-ENEMY-BASELINE-REVIEW/`, record the
exact response, and infer no approval from silence. `SALVAGE-03-COLLISION`
remains dependency-safe while feedback is pending, but cannot alter this
reviewed enemy result. V2-2B remains paused.
