# Status

Only source of current state. Branch `decomp/main`. Backlog: docs/BACKLOG.md.

- P0: items 1, 2 and 3 done (item 3 pending merge of lane/item3).
- P1: first gate measured, docs/notes/AVP_FIRST_GATE.md; recommendation GO, awaiting coordinator.
- Whole-game comparison: not run. Hardware: UNRUN.

## Whole-game check, 2026-11-06 (HOST against MAME, attract run, golden_c)

Exact IRQ preemption: MAME records each real IRQ's interrupted PC and registers; lifted code takes the IRQ at the same instruction. Registers are global across tasks, as on the board. Masked as non-state: task SR/PC/USP fields, stacks, ff0258, f_1a36 save area, idle task state byte, current-task pointer. Seeded from MAME because the hardware test is skipped: object RAM, d3, a4. First divergence at dump 1179 after a one-object difference at 1125.

## Saturn image plays to Round 1, 2026-11-06 (EMULATOR, Yaba; not hardware)

Lane satint, items 15-18 joined in one image: lifted game + saturn/gfx + SMPC pad through the game's own latch. Scripted pad flag (KERNEL_CFLAGS=-DSAT_INPUT_SCRIPT, the retained route's schedule): attract, coin, Predator Warrior, Round 1 gameplay with sprites and all layers on screen, no fatal to vblank 2158. Timer readings are emulator-only, not Saturn timing: graphics about 16-22 ms, peak 63.6 ms, over the 16.7 ms field, so the game often runs at 30 Hz or below (overruns 882 of 2158 vblanks).
Memory (item 17): Round 1 pack from a MAME census to the boss clear, 1,793,444 bytes. It fits only because the opcode view is cut from 1.06 MB to a 226 KB side store of OP* reads, with each read rewritten to a store offset. Two ROM stretches the route never read hold scroll 1 and 3 tiles and one cold code chunk, so the cart image holds Round 1 only: other rounds must load between rounds (not built). Free: cart 960 bytes, ROM stretch 23 KB, high RAM 2.4 KB, low RAM 33 KB.
Host check, final ROM with the store: clean 3000 of 3000 against golden_c (attract). Real pad presses, full Round 1 to the boss, audio and hardware: not run.

## Whole-game check through boss clear, 2026-11-06 (HOST against MAME 0.289; not emulator or hardware)

Golden `golden_r1s`, saved input route tools/routes/r1_pw_ko_boss.txt (tools/mame_golden_run.py): Predator Warrior, Round 1 start (frame 2238), KOs at frames 6082, 9471 and 12657, continues (6692-6723, 13292), boss clear (route 6 at frame 15019), to frame 15700. Host check clean 15618 of 15618 dumps, work RAM and object RAM. Byte-identical to the retained harness's run of the same schedule. Mask unchanged.
IRQ placement at kernel points now requires work RAM equal to the next dump, so a host divergence shows as a diff and a missed IRQ. Timing inside native kernel code is therefore checked by state only, not by cycle.
MAME state saves at route points are in golden_r1s/sta (item 14 start). Loading them, and host fixtures, are not built: lifted tasks live on native stacks, which a RAM dump cannot restore. The full host check takes under a minute, which covers the need on host.

## Drawing on the slave SH-2, 2026-11-06 (EMULATOR, Yaba; timing MODELLED, not hardware)

Item 20. Master keeps game logic and copies a per-frame snapshot at vblank; slave draws from it and owns VDP1, VDP2, CRAM, caches and shadows. One handoff; a busy slave skips a picture, never the game. Scripted scene, vblanks 1000-1650, build flags -DSAT_INPUT_SCRIPT -DSAT_PROF, same route:
| | before | after |
| --- | --- | --- |
| game frame mean / p95 / top ms | 29.55 / 65.23 / 78.04 | 11.16 / 25.0 / 48.16 |
| graphics mean / p95 / top ms | 18.18 / 28.04 / 64.01 (master) | 7.53 / 19.51 / 35.97 (slave) |
| snapshot on master mean / p95 ms | none | 4.27 / 7.93 |
| overruns of 650 vblanks | 266 | 55 |
| pictures drawn of 650 | 650 | 533 |
Whole-run graphics peak after: 57.2 ms, outside the window. The game now reaches further in the same vblanks, so the scene is not frame-identical. 60 Hz does not hold yet.
Two artefacts: the grey wall was VDP1 trails, fixed by a clear polygon at the head of each list (manual plotting has no erase). The black box is authentic: MAME shows the same empty box for a few frames as the message closes.
Missing tiles: real pixels the pack lacks, because the pack is a census of one MAME route. 493 of about 500 lookups fall at vblanks 550-803, before Round 1 gameplay on this script's earlier coin; few arrive in gameplay. Not fixed.
Sprite tiles over golden_r1s (tools/sat_tile_funnel.py, MAME data, 15618 frames): commands mean 149.6, p95 373, max 520; 800-tile worst frame loses 172 off screen and 108 empty, already culled per tile. Row runs on that frame 153. Live sprite banks mean 5.1, p95 9, max 11 of 32. Merging rows is not built: it needs contiguous texture slots.
Unproven: VDP1 fill time and bus contention on hardware; command table overwritten while VDP1 still plots a late list.
