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

`SALVAGE-01-PLAYER-LOAD-RENDER-INPUT` is accepted at `fc9f46746d082e4ccfe800304f49c55bec3e3800`:
paired clean builds and pinned Yaba readback passed exact package, normalized-disc,
runtime-ready, asset, late-read, canary, VDP1-command, and input-edge checks. Physical Saturn remains `UNRUN`.

USER-01 returned `the character sprite is cropped but moving.` Motion remains an
observation, not approval. REPAIR-01 corrected the grounded player pivot at
`76e497b1bcadc2b4ff8326bc855f7cef1bc7d336`: paired clean builds and pinned Yaba
readback prove idle bounds `(56,74)-(136,184)`, sampled walk bounds
`(28,88)-(152,184)`, the same seven-command/input/canary/zero-late-read locks,
and normalized ISO `7a9326d08607813fb88fb969de5f8f92b233649575e694b742e87141c6f28ef6`.
The real negative control restores the rejected idle bottom `232` and fails the
full-visible-cel invariant. Physical Saturn remains `UNRUN`.

The active card is `USER-01-PLAYER-BASELINE-REVIEW`, status
`AWAITING_USER_FEEDBACK`. Perform no implementation. Present ignored
`build/feedback/USER-01-PLAYER-BASELINE-REVIEW/` and record the exact response.
The old response is retained as `prior-response.json` and does not approve the
corrected output. `PROMOTE-01` remains blocked. `SALVAGE-02` is the only
independent eligible implementation while feedback is pending and must not
alter the player package.
