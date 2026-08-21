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
- No gameplay, rendering, audio, loading, build, emulator, or physical result
  changed during this governance update.

## Current task and next action

The active card is `SALVAGE-00-OLD-BUILD-BASELINE`. In a new card-scoped branch,
read that card, inventory the old build without changing production behavior,
run its focused checks and dedicated baseline diagnostic, record the migration
ledger result, and stop at its predeclared next-card boundary.

The first human checkpoint is `USER-01-PLAYER-BASELINE-REVIEW`, after the
player loading/rendering/input bench has passed AI emulator self-review.
