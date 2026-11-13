# Pictures per second: the slave's draw, what it costs and what moved (lane perf-pic, 2026-11-12)

Disc `avp_3h_A_fix7q1` (and the A/B disc `avp_3h_A_fix7q1_dma`), source commit `d3cde00` (readout id `F2 D3CDE0`; later commits of the branch are tools and this note), branch `lane/perf-pic-20261112`, rebased onto fix7p3 (`lane/perf-hw-20261112` 13a20cc). The measurements of sections 2 to 4 were first made on fix7p2 (fd88228); section 5 repeats the scenes on the final base. It replaces fix7p3 (kept as it was). Read `AVP_PERF_HW_20261112.md` and `AVP_PERF_HW_FIX7P2_20261112.md` first for the cost model. Labels as there: **EMULATED** = strict Ymir with its stock bus costs, **MODELLED** = the same Ymir with the board's memory costs (`HW_MODEL=1`, lane copy `ymir_pic`, probes in `tools/perf/ymir/sh2_perf_pic.diff`), **CONSOLE** = owner photos only (none for this disc). Nothing here is a console measurement.

## 1. Result in six lines
1. **The scroll 1 (HUD text) redraw was the slave's cost, and two exact switches that were already in the tree were not in the fix7n4 to fix7p2 recipe.** `SAT_S1_MEMO` and `SAT_S1_BLANKROWS` (perf-reconcile, host-verified identical over 600 frames) were landed default off and the recipe of the hardware discs never turned them on. In fix7p2 the slave spent 54 to 62 % of its work per picture in scroll 1 (`draw_scroll1`, `home_row_blank`, `home_row_map`, the lookups behind them).
2. **MODELLED, stage 1-1 crowd: PIC 40.3 with fix7p2, 60.0 with MEMO and BLANKROWS, 60.0 with the new dirty-row redraw on top** (slave draw length mean 3,053 -> 1,949 -> 1,288 FRT ticks; a field is about 3,500; draws over a field 58 % -> 0 -> 0). Stage 0A (the heaviest of the 18 stage list entries): 32.7 -> 59.5 -> 60.0. The 1-2 boss: 54.3 -> 60.0 -> 60.0. Wolverine's fight: 57.2 -> 59.8. EMULATED (stock Ymir) crowd: 57.9 -> 60.0. **On the final base (fix7p3 against fix7q1): crowd 43.8 -> 60.0, stage 0A 34.4 -> 60.0, boss 57.2 -> 60.0, stage 1 end 58.4 -> 60.0 (section 5).**
3. **`SAT_S1_DIRTY` (new, `saturn/gfx/sat_gfx.c`): redraw only the scroll 1 rows that changed, and keep the tile slots of the others.** Picture-exact in the host test (resolved layer, VDP1, CRAM, registers, frame for frame, FIT 1 and 2, with a mutation check that the test sees a missing restamp and a missing block expansion). Costs 232 bytes of low RAM data and about 0.9 KB of code.
4. **Game RAM over the tick-indexed route (stage ticks 300 to 3500) is the same as in fix7p2**; the only bytes that differ are 2 to 5 at ff7fc6 to ff7fe7 per mark (the 68000 stack scratch), the same class as the placement lane found, and a control (the same build twice in stock timing) differs there too.
5. **`SAT_CMD_DMA` (VDP1 command table by SCU DMA, level 2) is built, host-identical, passes in Ymir, and is NOT in the main disc.** On SCU level 0 it hung the first stage load in Ymir (section 6); on level 2 it runs. MODELLED it saves 8 % of the slave's work per picture and nothing in PIC (the draw already fits a field); it is untested on a console, so it rides on a second disc `avp_3h_A_fix7q1_dma` as an A/B, not in the main one.
6. **Wolverine's fight stays at TICK 56**: the master, not the slave, is the limit there (his cart hooks), outside this lane.

## 2. Where the slave's time goes, per picture (MODELLED, fix7p2, `tools/perf/slave_table.py`, `an_stage.py`)
Instructions and stall cycles per slave draw (cache line fills and write buffer waits), idle wait left out. A field is 3,500 FRT ticks = 448 K cycles. Windows: 1,200 vblanks, bot with health held (stage select, entry 0 = 1-1 crowd, entry 1 = 1-2 boss, entry 4 = stage 0A).

| group | crowd | boss | stage 0A |
|---|---|---|---|
| scroll 1 total (draw_scroll1, home_row_blank, home_row_map, name_of/bank, shifts) | 176 K instr + 9 K stall (about 41 % of the draw) | 82 K + 5 K | 207 K + 12 K |
| tile lookups `cache_find` (sprites and scroll 1) | 37 K + 20 K | 19 K + 12 K | 59 K + 31 K |
| sprite build and the rest of `sat_gfx_draw` (VDP1 command writes are most of its stall) | 40 K + 39 K | 22 K + 22 K | 65 K + 47 K |
| total per draw (instr + stall) | 271 K + 69 K | 133 K + 38 K | 368 K + 90 K |
| draws per window / PIC | 806 / 40.3 | 1,091 / 54.3 | 655 / 32.7 |

How a picture is lost: the master hands over a snapshot at each vblank only if the slave finished the last one (`gfx_done == gfx_handed`). A draw longer than a field costs that picture and the next hand-over. The draw length is read from `sat_dbg.gfx_ticks` (a `D` line per draw in the lane's Ymir). In the fix7p2 crowd, 58 % of the draws were over a field. The phases of a draw (`an_stage.py`, from `sat_gfx_stage`): sprite build 916 ticks, scroll 1 redraw 1,392 ticks in 57 % of the draws (of it `home_maps_rows` 652 and the row loop 739), scroll 2 and 3 about 10, the wait for the master's layer half about 0.

The rest of the time in the slave table is mostly the VDP1 command writes (about 45 cycles a long write, MODELLED: Ymir's own table), the 12 M stack writes of the lookup calls, and the hash walks.

## 3. The switches (each default OFF in the tree, ON in the fix7q1 recipe unless marked)
| switch | what | state |
|---|---|---|
| `SAT_S1_MEMO`, `SAT_S1_BLANKROWS` | exact memo of the column fit (`home_map`), blank-row skip (lane perf-reconcile 5640b80) | existed, not in the recipe; **ON now** |
| `SAT_S1_DIRTY` | master: `snap_layer_dirty` compares each scroll 1 word with the one it replaces and ORs a row mask into `snap.s1_dirty` (exact, no hash). Slave: when the last scroll 1 draw ran to the end with no refused cell, and position, menu mode and play flags are unchanged, and no menu or character select: `s1_restamp` stamps every clean non-blank row's tile slots with this draw's stamp before any lookup (so `cache_find` cannot evict a visible tile), `home_row_blank` runs for the dirty rows only (the others keep their blank masks), `s1_expand` widens the set to the rows next to a changed row and to every non-blank block with one (a block shares one column map), and only those rows go through the existing row code. Anything else takes today's full path. | new; **ON** |
| `SAT_GFX_COLD_CART` | set-up and menu code that never runs in play (`cache_setup`, `index_section`, `open_pack`, `sat_gfx_init`, `draw_home`, about 2 KB) linked into the cart tail instead of high RAM | new, optional; **OFF** (not needed without DMA; fits in Ymir: crowd PIC 60, draw mean 1,329) |
| `SAT_CMD_DMA` | sprite commands built in a work RAM buffer, moved to VDP1 by SCU DMA | new; **OFF**, see section 6 |
| build.py | when high RAM overflows the planner now also lets low RAM take the demoted cold code as far as it really has room (it only ever shrank `lw_slack` before, so a switch that added hot code to high RAM could not be fitted into 1 KB of free low RAM) | tool fix, all builds |
| test flags | `SAT_SCRIPT_FREEZE` (pad.c: the tick task waits 100 vblanks at fixed stage ticks so a screenshot shows one exact game state; test builds only) | off in every release recipe |

## 4. Exactness
**Host (EMULATED, `tests/host_gfx_s1_dirty.sh`, WSL gcc):** plain build, MEMO+BLANKROWS, and +DIRTY give the same hash frame for frame: VDP1 VRAM, CRAM, the display registers, VDP2 VRAM outside scroll 1, and scroll 1 *resolved* (each name of the visible 29 x 45 window followed to its cell with its flip and bank bits; raw VDP2 bytes differ because a partial redraw does not move a tile into another slot). Six data sets, FIT 1 and 2, 3,000 frames: random layers, a sticky stage like run, a play HUD (a few words change in the top and bottom rows every picture; `PLAYLIKE`, 1,400 of 1,500 scroll 1 draws partial), and heavy ones (`S1HEAVY`, more tiles than slots). In the heavy data the builds are identical until the first picture in which the plain build refuses a cell for lack of a slot (frame 2,254); from there which cells go blank depends on the order of the lookups, which a partial redraw changes (documented limit: under slot starvation the picture can differ for a picture or more, and the next full draw corrects it). Mutation check (`MUTATE=1`): leaving out the restamp is detected at frame 2,164, before any refusal, and leaving out the block expansion at frame 1 to 1,532.

**Ymir, game RAM (EMULATED, `ramdiff.py`):** `SAT_INPUT_SCRIPT` + `SAT_INPUT_SCRIPT_TICK` + `SAT_BOOT_CLEAR_EQ` builds, 64 KB of game RAM dumped at stage ticks 300, 600, 1000, 1500, 2000, 3000, 3500 (`HW_DUMP_RTICKS`), reference = the recipe without the switches, test = + MEMO + BLANKROWS + DIRTY. Both on fix7p2 (Q0T/Q2T) and on the final base (R0T/R2T): flat cost model (`HW_FLAT=1`): the same build twice is identical at all 7 marks; reference against test differs by 0 to 3 bytes a mark (17 bytes over the 7 marks), all at ff7fc6 to ff7fe7, the 68000's stack scratch. Stock timing: 2 to 5 bytes a mark in the same range (final base 27 bytes, fix7p2 21); the control, the same build twice in stock timing, differs by 3 bytes a mark there too (host timing moves where the interrupt lands). No byte of game state differs. Same method as the placement lane's section 4.

**Look check (EMULATED, auto pixel diff, `tools/perf/lookdiff.py`):** `SAT_SCRIPT_FREEZE` builds (`Q0TG` = recipe, `Q2TG` = + the three switches) pause the game's tick task for 100 vblanks after the tick that reads the pad at stage ticks 500, 900, 1400, 2000, 2600, 3200, 3700 (counted from the stage entry), so the screen settles on the picture of that exact game state while the vblank handler and the slave go on drawing. The game's tick counter at each mark is the same in both runs. Screenshots of the window compared pixel for pixel (a channel off by more than 24), the readout box left out and the 2P PRESS START flash left out (it is driven by the vblank counter, so its phase differs between builds; with it the marks 1, 3, 4 and 5 show 14,600 to 14,800 pixels, all in that one box): **0 differing pixels at all 7 marks** (stage 1-1 Coffee Shop). In the screenshots the readout of the old build at mark 1 reads PIC 55 SKIP 5, the new one PIC 60 SKIP 0, at the same game state. Diff sheets: lane folder `look_out`. Built on the final base's tree one commit after the three switches; the render code is the same.

## 5. PIC before and after (MODELLED unless marked; stage select scenes, bot, health held, 1,200 vblanks, `an_runs.py`)
**Final base: fix7p3 recipe (`B3`) against fix7q1 (`F3`) and fix7q1_dma (`F4`).** Cells: PIC / SKIP per 60 vblanks; slave draw length mean / p99 in FRT ticks; share of draws over a field (3,500 ticks).
| scene | fix7p3 | fix7q1 | fix7q1_dma |
|---|---|---|---|
| 1-1 Coffee Shop crowd (entry 0) | 43.8 / 16.2; 3,007 / 4,306; 43.8 % | **60.0 / 0.1**; 1,418 / 2,497; 0.1 % | 60.0 / 0; 1,218 / 2,231; 0 % |
| 1-2 boss (entry 1) | 57.2 / 2.8; 1,251 / 3,907; 5.2 % | **60.0 / 0**; 604 / 1,740; 0 % | 60.0 / 0; 715 / 1,669; 0 % |
| stage 0A (entry 4, the heaviest) | 34.4 / 25.6; 3,494 / 4,947; 74.7 % | **60.0 / 0**; 1,674 / 2,787; 0 % | 60.0 / 0; 1,476 / 2,547; 0 % |
| stage 1 end (entry 7) | 58.4 / 1.6; 1,254 / 3,744; 4.0 % | **60.0 / 0**; 738 / 1,739; 0 % | n/a |
TICK 60.0 and MISS 0 in every one of these runs.

**Step by step on the fix7p2 base (`Q0` = recipe, `Q1` = + MEMO + BLANKROWS, `Q2` = + DIRTY).**
| scene | fix7p2: PIC / SKIP / draw mean / p99 / over a field | + MEMO + BLANKROWS | + DIRTY |
|---|---|---|---|
| 1-1 crowd | 40.3 / 19.8 / 3,053 / 4,562 / 58 % | 60.0 / 0 / 1,949 / 3,007 / 0 % | 60.0 / 0 / 1,288 / 2,148 / 0 % |
| 1-2 boss | 54.3 / 5.7 / 1,536 / 4,302 / 9.9 % | 60.0 / 0 / 764 / 2,363 / 0 % | 60.0 / 0 / 627 / 1,572 / 0 % |
| stage 0A | 32.7 / 27.3 / 3,747 / 4,969 / 83 % | 59.5 / 0.5 / 2,176 / 3,526 / 1.3 % | 60.0 / 0 / 1,678 / 2,736 / 0 % |
| stage 1 end | 57.0 / 3.0 / 1,754 / 3,978 / 7.4 % | 60.0 / 0 / 937 / 2,585 / 0 % | 60.0 / 0 / 652 / 1,694 / 0 % |
| Wolverine, Coffee Shop (GUEST_DEFAULT=1 build; the in-stage part of the window, 1,022 and 1,138 vblanks) | 57.2 / 2.8 / 726 / 4,334 / 4.9 % | n/a | 59.8 / 0.2 / 584 / 2,130 / 0.3 % |
| EMULATED (stock Ymir), 1-1 crowd | 57.9 / 2.1 / 2,228 / 3,965 / 6 % | n/a | 60.0 / 0 / 1,017 / 1,766 / 0 % |
The other 15 stage list entries with MEMO + BLANKROWS (fix7p2 base): PIC 59.5 to 60.0. TICK is 60 in every scene but Wolverine's (55.8 before, 56.2 after: his hooks in the vblank handler and tick make the master the limit; a wait of up to 13,000 ticks for the master's layer half shows up once in a while in his fight). The bot reads the wall clock, so two runs of one scene differ a little (the crowd reads 40.3 on one base and 43.8 on the other with the same placement logic): the exactness runs use the tick-indexed script instead.

## 6. SAT_CMD_DMA (`avp_3h_A_fix7q1_dma` only)
The sprite commands (4 long writes of 45 cycles each, MODELLED, 1.4 M VDP1 writes and 42.7 M stall cycles in a 1,200 vblank window: 7.4 % of the slave's window) are built in a 2 x 2 command buffer in high RAM (128 bytes; `CMD_STG=2`, `CMD_STG` commands a batch) and moved to the command table by SCU DMA, the CPU building the next batch while the DMA runs, a bounded wait (`sat_cmd_dma_timeouts` counts a transfer that never ended) before each start and before the plot.
- **Host (EMULATED):** `tests/host_gfx_cmd_dma.sh`: VDP1 (command tables without the 16 bytes of a command the CPU never writes; VDP1 does not read them for a sprite), VDP2, CRAM, registers identical frame for frame over 600 frames, FIT 1 and 2, `CMD_STG` 16, 3 and 1.
- **Ymir (MODELLED), crowd:** PIC 60.0 as without it; sprite build 958 -> 762 ticks, slave work per picture 149 K -> 138 K cycles (instructions 89.5 K -> 108.1 K because of the polls, stall cycles 59.9 K -> 29.4 K), draw mean 1,288 -> 1,220. The whole draw barely moves because the slave then waits longer for the master's layer half.
- **Why it is not in the main disc:** (1) on SCU level 0, as the existing `SAT_TILE_DMA` experiment, the first stage load hung in Ymir (Q3 and Q3c: the vblank never came back, IMS read 0x0000B7FF with vblank-in masked, GFS had the mask and was waiting for its DMA end); the cause was not pinned down (the loader's SCU writes are not in my log); level 2 never loads. (2) It is untested on a console, and what the VDP1 write costs there is exactly what the model assumes. (3) No PIC to gain in the model. The photo of the DMA disc says whether the VDP1 writes matter.
- Final base `F4`: stage select crowd, boss and stage 0A all PIC 60.0, TICK 60, the first stage load passes; low RAM free 36 on that disc (500 on fix7q1).

## 7. Memory (final base; fix7p3 in brackets)
fix7q1: high RAM free 72 (56), low RAM free 500 (2,388), cart tail free 2,372 (2,372), `cold1_at` 0x027DF000 unchanged. fix7q1_dma: 72 / 36 / 2,372. The three switches moved about 1.9 KB of never-run code from high to low RAM (planner); DIRTY costs 232 bytes of `bm_keep`, 16 of snapshot, about 700 bytes of code. Low RAM free paid for it, which the planner could not do before the `build.py` change of section 3.

## 8. Gates
Build (fails on them): `vdp2_cycle_check` PASS, alignment gate (331 data symbols, 0 of unknown type, 46 reviewed cast sites, 199 accessor calls, 287 round files and REVEAL.BIN, 0 hits), boot data addresses, Wolverine block canary, budgets as above. Tests: `align_gate_test`, `lat_protocol_test`, `vdp2_cycle_check_test` pass; `tests/host_gfx_s1_dirty.sh`, `host_gfx_s1_identity.sh`, `host_gfx_cmd_dma.sh` pass. TICK 60 and MISS 0 in every Ymir run above. Ymir misalignment gate (`tools/ymir_misalign_gate.py --run`, boot, title, stage 1, KO, continue with another character): 0 data accesses on the staged fix7q1 (7,193 instruction fetch artefacts filtered) and on fix7q1_dma (6,905).

## 9. Risks and what is not known
- Everything is emulator and model; the A-bus cart figure, the VDP1 write cost (45 cycles a long) and the master/slave bus contention are the model's assumptions (note 1, section 10). A console PIC will tell. If the slave were 1.5 times slower than modelled, the 1-1 crowd would still draw in a field (mean 1,288 ticks, p99 2,148 of 3,500).
- DIRTY under slot starvation (section 4); `snap.s1_dirty` is one more snapshot field the master writes (the stage select's held title picture saves and restores the snapshot: after a restore a full draw runs because the menu mode is not play).
- Wolverine's fight is master limited (TICK 56). Not touched.
- The readout's PROF line is unchanged.
- The tick-aligned RAM test covers stage 1 (3,500 ticks); the stage change and the load are not tick-aligned.

## 10. Files
Lane folder `E:\AvP\learning\lane-perf-pic` (`ymir_pic`, `ymir_pic2..4`: the lane's Ymir copies, `runs/*`, `hwprof_*.txt`, `exact/` RAM dumps, `tables_slave.txt`). Repo: `tools/perf/pic/` (harness), `tools/perf/an_runs.py`, `an_stage.py`, `an_pic.py`, `slave_table.py`, `tools/perf/ymir/sh2_perf_pic.diff`, `tests/host_gfx_s1_dirty.sh`, `tests/host_gfx_cmd_dma.sh`, `tests/host_gfx_s1_identity.c`, `saturn/gfx/sat_gfx.c`, `saturn/rt/build.py`, `saturn/rt/pad.c`.
