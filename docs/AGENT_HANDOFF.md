# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot
The interactive salvage/promotion workflow remains authoritative.

## Preserved paused work

- The dirty primary canonical worktree remains untouched.
- The dirty `prototype/avp-clean-playable-skeleton` worktree remains intact and
  is classified as reusable state pending bench results.
- V2-2B remains `CORRECTIONS_REQUIRED` in its existing dirty validator-
  correction worktree. Its four recorded blockers remain unresolved. It is a
  dependency for exact HIT/KO promotion, not for early loading, input,
  rendering, animation, stage, palette, or diagnostic salvage.
- `SALVAGE-00-OLD-BUILD-BASELINE` is accepted only as a technical build/emulator
  baseline: its physical Saturn state remains `UNRUN`, automatic window captures
  remain black, and the observed distorted enemy pixels are not visually accepted.

## Current task and next action

PROMOTE-01 and its `USER-01-PLAYER-BASELINE-REVIEW` locks remain accepted. USER-04 exact response
was `pass for camera and stage`; the reviewed adapted camera/stage presentation
is locked, while uncaptured row-scroll prevents full source-faithful promotion.

USER-05 exact response is `sound is great hud looks broken in terms of colors`.
The short Predator melee PCM cue is approved and locked.

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

The active card is `USER-05-HUD-PCM-REVIEW`, status
`AWAITING_USER_FEEDBACK`. Present ignored package
`build/feedback/USER-05-HUD-PCM-REVIEW/` and ask the exact required question.
Do no implementation and infer no approval while feedback is pending.
