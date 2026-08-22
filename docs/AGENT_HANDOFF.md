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

The active card is `SALVAGE-02-ENEMY-RENDER-ANIMATION`, status `READY`, on
clean branch `codex/avp-salvage-02-enemy-pipeline`. Isolate class `0x1F` enemy
assets, rendering, and animation only; retain all approved player, stage,
HUD, and PCM locks. The observed distorted enemy pixels are unaccepted until
the card's source, negative-control, diagnostic, and pinned-emulator evidence
passes. V2-2B remains paused and does not block this salvage.
