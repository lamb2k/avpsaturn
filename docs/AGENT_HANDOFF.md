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

PROMOTE-01 remains accepted at `602ec4f0e26f169e45684f031f805c4b2aed278f`
after `USER-01-PLAYER-BASELINE-REVIEW` returned the exact response
`Looks good keep going`; all approved-player locks remain intact.

SALVAGE-04 is technically accepted at
`a89a87b843a65388dae294b84519d115e6cf8f41`. Paired target builds and pinned
Yaba readbacks reproduce fixed frame 20 at scroll `(0,7)`/477 objects and the
frame 45-to-46 step `(0,7)` to `(10,15)`. Both VDP2 planes, PNT canaries, CRAM
payloads, priority `2<3<4<6`, and NTSC 352x224 framing pass. Normalized ISO is
`6523ba9302cef304179e43c56207396c16537c5c139b3d274b04cf8d68bf7850`.
The result remains ADAPTED because the enabled scroll2 row-scroll table is
uncaptured. Enemy distortion remains excluded for SALVAGE-02; physical Saturn
is `UNRUN`; V2-2B remains paused.

`USER-04-STAGE-REVIEW` is `AWAITING_USER_FEEDBACK`. Present only the ignored
`build/feedback/USER-04-STAGE-REVIEW/` package and ask the exact required
question. Perform no implementation and never infer approval from silence.
