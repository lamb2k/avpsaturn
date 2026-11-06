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

## Round 1 played on real pad input, 2026-11-06 (EMULATOR, Yaba; not hardware)

Real input: `saturn/rt/play_yaba.py` posts key messages to Yaba's own window; the emulated pad goes through SMPC to the game's latch. No scripted flag. Closed-loop bot `saturn/rt/play_round1_bot.py` reads RAM over MCP and picks keys.
Run: Predator Warrior from coin to Round 2 title card, attract 0 throughout, 2 process legs joined by a save state at v10919. Section 1 clear v4909-range, boss (ffa3c0 class 06) from v5834, 5 KOs in the leg counts with credited continues returning 101 health, boss health to below zero about v23085, ff81f3 set v23142, section 3 v23325. Screenshots and logs: E:\AvP\learning\lane-play\proof.
ff81f3 is a section clear flag, not boss clear. Boss clear is ff81f3 set in section 2 (ffd182) followed by section 3. An earlier run's flag at v4885 was section 1.
Fixes: 25 targets in 7 unresolved jump tables (tools/satint_scan_tables.py; the fatal was 0xe1 at 0x4af24), added as an extra lifted chunk in the lane's work directory only: they still need adding to the shared roots.
Not re-proven: that run predates the new pack, the speed merge and the readout. The final image had short runs only (about 2200 vblanks, no fatal). The bot played far worse than the MAME route and needed many more ticks.
Yaba speed in gameplay falls from about 60 to about 20 vblanks/s within a minute, the same with near-zero polling, key input or heavy reads, from one save state. So it is not MCP. Cause not found. A long-lived process fell further, to about 3-5, with other host load present.

Pack: real-play key log (SAT_KEYLOG, first ~2600 vblanks) plus a census from Round 1 start. 1079 sprite and 64 scroll 1 keys were missed by the old pack; 1202 of 1883 sprite extras fit, in play census order first, and attract-only tiles left the pack. Main 1,648,296 bytes. Missing counter 1224 before (about v2600), 940 at v2157 after: not the same point, and not fixed. The title's digits and some round card letters still draw blank in shots taken before this pack; not rechecked after. Room came from moving one more cold chunk into the rest of the tile ROM stretch.

Audio: hooked in; clips load through low RAM to SCSP RAM at boot. Pick: per-channel slots. Capture from a patched Yaba (saturn/audio/yaba_wav_dump.patch, SCSP output), same 14 commands, against MAME, saturn/audio/compare_raw.py:
| | per channel | single mixed stream |
| --- | --- | --- |
| frame cost, worst, emulator timer | 0.10 ms | 2.16 ms |
| 10 ms loudness correlation, median per second | 0.735 | 0.844 |
| level against MAME | +1.0 dB | +2.1 dB |
The stream sounds closer by this measure, at about 22 times the worst cost, and Yaba likely undercharges its bus reads. The mix uses 2 slots and 16 KB, not the 3 slots of the MSHvSF evidence. Effects in the slot build run quieter than MAME over the first 11 s. Not tuned.
Game image capture: non-silent; clips 0x24e, 0x254 and 0x203 matched by correlation 0.81-0.997. CD music is in the capture. Not compared to a MAME run of the same play, because the play differs. No person has listened.

Package, item 26: `saturn/package/build_package.py`, output E:\AvP\package-play: two data images (DMA off and on), cue, tracks, hashes, HARDWARE_TEST.md, with on-screen bars for game, drawing and VDP1 time, and Y and Z test modes for fetch against fill. Hardware: UNRUN. The bars ran on Yaba; the DMA image did not get a gameplay run, only the build.
