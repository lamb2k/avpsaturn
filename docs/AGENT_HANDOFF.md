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

The active card is `SALVAGE-01-PLAYER-LOAD-RENDER-INPUT`. Use its dedicated
card-scoped branch, run only its player loading/input/assets/rendering/animation
bench, keep enemy and camera behavior disabled, and retain the SALVAGE-00
pinned-emulator readback as a regression lock.

The first human checkpoint is `USER-01-PLAYER-BASELINE-REVIEW`, after the
player loading/rendering/input bench has passed AI emulator self-review.
