# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot

The project now advances through isolated salvage benches, focused validation,
Saturn emulator self-review, explicit human checkpoints, bounded salvage
decisions, promotion behind `port_v2` interfaces, and one-dependency
integration. The old mixed runtime and the playable-skeleton prototype are
reuse candidates, not production gameplay authority or parity gates.

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

`SALVAGE-01-PLAYER-LOAD-RENDER-INPUT` is accepted at
`fc9f46746d082e4ccfe800304f49c55bec3e3800`: two clean PlayerSalvageBench
builds normalize to the same disc identity, exact player package members
match, and pinned Yaba readback recorded runtime-ready, zero asset failures,
zero late reads, intact canaries, VDP1 commands, and right/down/left player
input edges. Physical Saturn remains `UNRUN`.

The active card is now `USER-01-PLAYER-BASELINE-REVIEW` and must perform no
implementation. The ignored package is
`build/feedback/USER-01-PLAYER-BASELINE-REVIEW/`. Ask exactly the card's
question, record the exact response, and never infer approval from silence.
While that feedback is pending, only predeclared `SALVAGE-02-ENEMY-RENDER-ANIMATION`
may proceed independently; it must not alter this player package.

The user's observed distorted enemy pixels remain unaccepted and are deferred
to SALVAGE-02. V2-2B remains paused and does not block player salvage.
