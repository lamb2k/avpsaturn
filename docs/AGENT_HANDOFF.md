# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap. Continue sequentially on
`codex/avp-playable-loop-pivot`.

## Workflow pivot

## Preserved evidence work

- Keep dirty/private worktrees, ignored evidence, recovery patches, and all
  component-scoped user locks untouched.
- Preserve V2-2B `597f4ed517d4e715d814ff841bd00d3977803f85`,
  `SALVAGE-00-OLD-BUILD-BASELINE`, and `USER-01-PLAYER-BASELINE-REVIEW`.
- REPAIR-09 is accepted at `417ed808e10f0f255948b1e6ecf0223399509c74`.
- INTEGRATE-03 is user-approved only as `SOURCE_BOUND_WITH_ADAPTED_INPUT` at
  `82965ef80223a03937e0b527d16161ed68d874a0`; exact ISO `4a142774...98ef`.
- HW-01 is parked `READY_FOR_PHYSICAL` / `WAITING_FOR_EXTERNAL_HARDWARE` with
  Probe ISO `82c3a86c...ef50`. Physical Saturn remains `UNRUN`; do not wait.
- ORACLE-04/05/06 and PROMOTE-10/11 remain accepted. The ORACLE-06 live-loop
  clear is explicitly adapted to target KO then inactivity.

## Current task and next action

INTEGRATE-04A is technically accepted at
`d9021965dab64d47953d2e829c7d307b0b01a455`. Two post-commit cold Yaba runs
match across an exact 448-frame ledger and prove real input, current-state
player/AI/collision/damage/HIT/KO, adapted clear, unlock, and continued
movement. Diagnostic ISO: `3246659a...938c5`; exact interactive ISO:
`ae65359601d56e5fbee82c94eb66acfd12ed8c842d95b8f7a63e51d78bca7a8a`.

USER-09 returned `CHANGES_REQUESTED`: player facing is wrong in some walking
directions, attacks flash incoherently between weapon/no-weapon poses, and AI
plus player/alien collision feel off. The active bounded implementation is
`REPAIR-10-LIVE-PLAYER-PRESENTATION`. Correct only the facing-sign mapping and
the two startup ticks that currently use the unrelated legacy attack clip;
preserve all four selector-owned source sequences and all combat locks. AI and
collision remain explicit unresolved follow-ups. Do not activate frontend work.

Resume prompt: Resume the AvP salvage Goal at REPAIR-10; complete focused
repeat/mutation, Target, paired emulator, and renewed USER-09 evidence while
keeping AI/collision unresolved and visible.
