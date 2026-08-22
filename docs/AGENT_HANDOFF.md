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

USER-05 original exact response is
`sound is great hud looks broken in terms of colors`. The short Predator melee
PCM cue is approved and locked. Renewed exact responses are
`what about player 2 hud?` and `Let’s do that before we move on`.

REPAIR-05 is technically accepted at
`949316331c7c12a9ae630ef5f5ebc846e4d2aef5`. It maps one-based HUD source
index 1 to Jo/CRAM entry 0. Paired clean builds and pinned Yaba interpreter
runs reproduce normalized ISO
`6218e3d1e745552f6c64ef16f7c66cc044abc04772634f36ebefa9888e45a10d`.
Both runs read yellow/red/energy/empty CRAM values `0x83ff/0x801f/0xbbf7/
0xc631`; the reconstructed old zero-based binding is rejected. HUD states,
canaries, zero failures/underruns/late reads, and stage/player locks pass.

PCM SHA-256 `e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125`
and timing `147/150/200` are unchanged. The cue remains an ADAPTED QSound-to-
SCSP result. Enemy corruption stays routed to SALVAGE-02. CDDA, combat, normal
release, a second emulator, and physical Saturn remain `UNRUN`; V2-2B remains
paused.

The active card is `SALVAGE-05B-PLAYER-2-HUD`, status `READY`, for clean branch
`codex/avp-salvage-05b-player-2-hud`. The existing `HUDP2.BIN` is only the
blinking `PRESS START` prompt and is not active P2 HUD evidence. Bind and render
the real active P2 HUD plus fixed semantic states in the HUD bench, preserve the
corrected P1 palette and approved PCM locks, run the declared Oracle/Target/
Emulator cycle, then return the ignored USER-05 package for renewed review.
Do not implement P2 input, gameplay, joins, multiplayer, or multitap topology.
