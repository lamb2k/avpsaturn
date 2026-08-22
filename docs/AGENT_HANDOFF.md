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

USER-01 returned `the character sprite is cropped but moving.` Motion remains an
observation, not approval. REPAIR-01 corrected the grounded player pivot at
`76e497b1bcadc2b4ff8326bc855f7cef1bc7d336`: paired clean builds and pinned Yaba
readback prove idle bounds `(56,74)-(136,184)`, sampled walk bounds
`(28,88)-(152,184)`, the same seven-command/input/canary/zero-late-read locks,
and normalized ISO `7a9326d08607813fb88fb969de5f8f92b233649575e694b742e87141c6f28ef6`.
The real negative control restores the rejected idle bottom `232` and fails the
full-visible-cel invariant. Physical Saturn remains `UNRUN`.

`USER-01-PLAYER-BASELINE-REVIEW` exact response is `Looks good keep going`.
The corrected full-visible player image/pivot/palette and fixed-background
presentation, shown idle/walk animation, and demonstrated movement/facing are
approved and locked. Enemy pixels, combat, camera, HUD, audio, normal release,
and physical Saturn remain outside this approval.

The active card is `PROMOTE-01-PLAYER-PIPELINE`, status `READY`. Promote only
the approved loading, input, player asset, animation, and rendering decisions
behind narrow `src/port_v2/player/**` interfaces in its declared clean branch/
worktree. Preserve the approved package byte/behavior locks and require renewed
USER_REVIEW if any approved invariant is at risk. Physical Saturn remains
`UNRUN`; V2-2B remains paused and does not block player promotion.
