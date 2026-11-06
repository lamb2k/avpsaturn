# Status

Only source of current state. Branch `decomp/main`. Backlog: docs/BACKLOG.md.

- P0: items 1, 2 and 3 done (item 3 pending merge of lane/item3).
- P1: first gate measured, docs/notes/AVP_FIRST_GATE.md; recommendation GO, awaiting coordinator.
- Whole-game comparison: not run. Hardware: UNRUN.

## Whole-game check, 2026-11-06 (HOST against MAME, attract run, golden_c)

Exact IRQ preemption: MAME records each real IRQ's interrupted PC and registers; lifted code takes the IRQ at the same instruction. Registers are global across tasks, as on the board. Masked as non-state: task SR/PC/USP fields, stacks, ff0258, f_1a36 save area, idle task state byte, current-task pointer. Seeded from MAME because the hardware test is skipped: object RAM, d3, a4. First divergence at dump 1179 after a one-object difference at 1125.
