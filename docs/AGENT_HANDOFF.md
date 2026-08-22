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

USER-01 returned `the character sprite is cropped but moving.` Player rendering
is `CHANGES_REQUESTED`; motion is an observation, not approval. The exact response
is in ignored `build/feedback/USER-01-PLAYER-BASELINE-REVIEW/response.json`.

The active card is `REPAIR-01-PLAYER-CROP-PIVOT`. Execute only its bounded
player cel/pivot correction in the clean card-scoped worktree/branch. Preserve
the SALVAGE-01 loading, input, movement, animation cadence, palette, command
count, fixed background, canary, zero-late-read, normalized-disc, and pinned-
emulator regression locks. Add a real negative control that restores the
rejected crop/pivot condition, then return the corrected ignored package to
USER-01. `PROMOTE-01` remains blocked. `SALVAGE-02` remains independent and
must not alter the player package.

The user's observed distorted enemy pixels remain unaccepted and are deferred
to SALVAGE-02. V2-2B remains paused and does not block player salvage.
