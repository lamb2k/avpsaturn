# Master time on the console: where it goes and what moved (lane perf-hw, 2026-11-12)

Disc `avp_3h_A_fix7p1` = fix7n4 (source 9071bc8, head 9e65039) plus four switches, all ON: `-DSAT_PLACE_FN -DSAT_HOT_STACK_HW -DSAT_HOT_GFXRAM_HW -DSAT_HOT_GFX_HW -DSAT_PROF_LINE`. Source commit `be14055` (build id on the readout: `F2 BE1405`). Branch `lane/perf-hw-20261112`. Gameplay, graphics and sound code are not changed: only where code and data sit, and one new readout line.

**Labels.** EMULATED = strict Ymir (my own patched copy, JP BIOS, 4 MB cart, SH-2 cache on) with its stock bus costs, which do not tell the three RAMs apart. MODELLED = the same Ymir run with `HW_MODEL=1`: cache line fills, cache-through accesses and writes charged from published Saturn figures (section 2). CONSOLE = owner photos only (quoted, not measured here). Nothing in this note is a console measurement of the new disc.

## 1. Result in five lines
1. The console's slow master is memory placement, not the game. Stock Ymir charges one flat cost for a work RAM, low RAM and cart access, and charges nothing for instruction fetches. The board does not: Sega's FAQ gives 7 clocks to refill a 16 byte cache line from high RAM and 56 from low RAM. In fix7n4, 68 % of the instructions the master runs in the game tick come from low RAM, and the vblank snapshot reads its 128 KB graphics image from low RAM.
2. MODELLED, that alone reproduces the console. fix7n4 in the crowded stage 1 fight: TICK 56, MISS 33, DONE 27, PIC 32 (console fix7n: MISS about 45, DONE 13-15, PIC 31-36). With the cart a little slower than assumed (10 clocks a 16 bit beat) it reads TICK 50, MISS 40, DONE 19, PIC 33.
3. fix7p1 moves what the master and slave actually run into high RAM. MODELLED, same scene: TICK 60, MISS 0, DONE 60, PIC 39 to 42 (was 32); the master is busy 56 % of a field (was 87 %).
4. EMULATED (stock Ymir) nothing regresses: TICK 60, MISS 0, PIC 58 (was 52).
5. Still open: PIC stays under 60 because the slave's drawing (scroll 1 redraw, sprite build) is now the limit. That is the next target, section 9.

## 2. Hardware cost model (MODELLED)
Figures used (SH-2 clocks, `HW_*` environment variables of the profiling Ymir):

| Item | Figure | Source |
|---|---|---|
| High work RAM (SDRAM), cache hit | no wait | Sega Saturn FAQ, WORKRAM-H and WORKRAM-L speed (https://www.infochunk.com/saturn/segahtml_en/faq/prog/p02_10.htm) |
| High RAM, cache miss, 16 byte line | about 7 | same page |
| High RAM, write | 4 per longword; a one longword write buffer lets consecutive writes go faster | same page |
| Low work RAM (DRAM), cache miss, 16 byte line | 14 per longword x 4 = 56 | same page |
| Low RAM, write | 14 per longword (7 per word) | same page |
| SH-2 cache | 4 KB, 4 way, 16 byte lines, write through, no write allocate; cache-through alias 0x20000000 | Hitachi SH7604 manual (recalled, not re-fetched this session); the Sega FAQ page gives the alias addresses |
| A-bus cart (4 MB RAM cart, ST-TECH-47 timing 0x23301FF0) | **ASSUMED** 6 per 16 bit beat: 12 a long, 48 a line. Range tried 6 to 10 | no published figure found; Ymir's own commented hardware table has 4 (16 bit) and 8 (32 bit) for A-bus CS0/CS1, the SCU manual has wait count fields only |
| VDP2 VRAM and CRAM, CPU access | 40 | Ymir `saturn.cpp` commented table ("passes misctest", author's measured set; not independently confirmed) |
| VDP1 VRAM and frame buffer | 45; VDP1 registers 29 | same table |
| Write buffer | one write in flight; a later bus access waits for it | Sega FAQ page; modelled by `HW_WBUF=1` |
| FRT (profile line) | phi/128; one tick about 4.5 to 4.8 us, a field about 3,500 ticks | SH7604; hwtest note |

What the model changes in Ymir (`ymir_hw/sh2.cpp`, lane copy, kept out of the repo): the cache fill path charges the whole line fill by region, instruction fetch misses are charged (stock Ymir charges nothing), cache-through reads and writes are charged per access, writes go through a one entry write buffer. Per instruction the master's time is split into the game tick, the vblank handler and the idle spin by write taps on `game_done` and the vblank handler's first and last writes.

**Calibration against the console.** The model was not fitted: the figures above went in once. fix7n4 in stage 1-1 (Coffee Shop crowd, 1200 vblanks after the first 300, scripted walking bot, health held) gives MISS 33, PIC 32, SKIP 28 against the console's MISS about 45, PIC 31 to 36. It is therefore a lower bound for the master's slowness (the console is a little slower still: cart beat 10 gives MISS 40). The speed lane's uniform "master x3" reproduced the same MISS by brute force; this model says where the factor comes from.

## 3. Where the master's time goes
### EMULATED: instructions (stock Ymir, fix7n4, stage 1-1 crowd, 1200 vblanks, `hwprof_p1_stock`)
Master, 576 M cycles per CPU in the window: game tick and other tasks 178 M (31 %), vblank handler 76 M (13 %), idle spin 321 M (56 %). The idle spin is the dispatcher walking the task list again after the pass is done; it is not work.
- Instructions the master ran in tasks plus handler: 197.7 M. By where the code sits: low RAM 68.5 % of the tick's instructions (96 M), high RAM 26 %, cart 5.5 %.
- 99 % of them come from 271 functions, 196 KB; 651 functions ran at all (319 KB), 93 KB of those were in high RAM, 186 KB in low RAM, 39 KB in the cart.
- Slave (333 M instructions, 95 % from high RAM): `draw_scroll1`, `home_row_blank`, `cache_find`, `sat_gfx_draw`, `home_row_map`, the idle wait; 14.0 M writes to its stack in low RAM.

### MODELLED: cycles (same run with `HW_MODEL=1`, fix7n4)
Master window 573.8 M cycles: tick 385.5 M, handler 113.3 M, idle 75.0 M (busy 87 %).

| Cost (master, tick plus handler) | cycles | share of the window |
|---|---|---|
| instruction line fills from low RAM | 185.8 M | 32.4 % |
| data line fills from low RAM (the handler reading `sat_gfxram`) | 43.3 M | 7.5 % |
| instruction line fills from the cart | 37.3 M | 6.5 % |
| data line fills from the cart (ROM tables, opcode view) | 16.4 M | 2.9 % |
| write buffer waits (high and low RAM) | 20.8 M | 3.6 % |
| instruction and data fills from high RAM | 20.0 M | 3.5 % |
| executing instructions (CPI 1.15) | 172.6 M | 30.1 % |

Slave memory stalls 157 M of 574 M: low RAM write waits 69.6 M (its stack and layer shadows), low RAM data fills 45.2 M, VDP1 write waits 26.6 M.

Top functions, master tick plus handler (fix7n4; EMULATED instruction share, MODELLED cycle share, where they sat):

| function | size | where | EMULATED instr | MODELLED cycles | stalls in it |
|---|---|---|---|---|---|
| snap_layer (layer snapshot sums) | 232 | HW | 14.2 % | 11.4 % | 63 % |
| sat_gfx_snapshot_begin | 1200 | HW | 7.3 % | 4.6 % | 56 % |
| pb_at (68K address to RAM, a call per access) | 28 | HW | 10.8 % | 4.2 % | 13 % |
| f_167d0 | 1332 | LW | 1.8 % | 3.6 % | 80 % |
| f_aa016 | 3116 | LW | 3.2 % | 3.2 % | 74 % |
| f_17ff6 | 292 | LW | 4.4 % | 2.3 % | 10 % |
| f_dispatch | 96 | HW | 4.5 % | 2.2 % | 16 % |
| draw_list_sort | 348 | HW | 6.5 % | 1.7 % | 7 % |
| f_167ac, f_a9d8c, f_a9cb6, f_a9b90, f_a9d18, f_6075a, f_aaa12, f_a9d52, sat_guest_group (cart), lifted_1d03e ... | 100 to 1000 | LW (one in the cart) | 0.4 to 2.0 % each | 0.9 to 1.5 % each | 56 to 86 % |

The pattern: the functions that cost the most per instruction are the low RAM and cart ones (stalls 56 to 86 % of their time); the high RAM ones are mostly instruction bound.

### MODELLED ranking of where the master's time goes (fix7n4)
1. Code in low RAM refilling the cache (32 %).
2. The handler reading the graphics RAM image from low RAM (7.5 %).
3. Hot code in the cart, mainly the guest hooks in `guests.o` and chunk c22 (6.5 %).
4. ROM tables from the cart (2.9 %).
5. Write waits, the 68K address lookup `pb_at` (10.8 % of instructions, 4 % of cycles), the layer sums (`snap_layer`, 14 % of instructions).
Not a cost worth a change: cache-through reads (about 280 a vblank, 0.4 %), VDP2 writes by the master (0.2 %).

## 4. The switches (each default OFF in the tree, ON in the fix7p1 recipe)
| switch | what | effect |
|---|---|---|
| `SAT_PLACE_FN` | The lifted chunks and `guests.c` are built with `-ffunction-sections`. `saturn/rt/place_fn.json` holds the heat of 1,611 functions (instructions executed and instruction line fills in the game tick and the vblank handler, summed over 7 profiled play scenes: stage 1-1 twice, the 1-2 boss, 2-1, 2-2 boss, 3 and the scripted route through stages 1 and 2; `tools/perf/fn_heat.py`). `build.py` ranks functions by cost per byte and fills high RAM with the best 488 KB (1,165 functions); the rest leave. A hot function from low RAM, the cold1 tail or a ROM stretch swaps places with never-run functions of the same bytes, so every region keeps its size and the cart tail (`cold1_at`) does not move. | 756 functions (348 KB) move into high RAM, 574 KB of never-run code moves out |
| `SAT_HOT_STACK_HW` | the slave's stack (1 KB, 14 M writes in 1200 vblanks) moves from low to high RAM (`.hwstack`; the restart's bss clear skips it) | |
| `SAT_HOT_GFXRAM_HW` | kernel `.lwgfx` (the 128 KB graphics RAM image the handler reads each vblank, the sound tables) moves to high RAM | |
| `SAT_HOT_GFX_HW` | `sat_gfx.c` `.lwgfx` (snapshot, layer shadows, blank tags, pack index; 85 KB) moves to high RAM | |
| `SAT_PROF_LINE` | the readout's PROF line (section 6) | about 310 bytes of high RAM, about 530 of cart |

Room: the three data switches need 226 KB of high RAM; they depend on `SAT_PLACE_FN` for it. Budgets of the shipped build (fix7n4 in brackets): high RAM free 72 (924), low RAM free 2,432 (96), cart free 2,448 (5,008; `cold1_at` unchanged at 0x027DF000, so the 4 KB step is not crossed; 2 KB of the margin was given to cold code on purpose, `PLACE_FN_COLD1_EXTRA`). The planner relinks until both RAMs fit, so a future change that grows high RAM makes it demote more instead of failing.

Not changed: no assembly, no hot-loop edits. Not touched either: the `.hw` objects of the platform (kernel, gfx, audio), which stay in high RAM whole.

## 5. Exactness
(see the tables below; EXACT_RESULTS)

## 6. The PROF line (`saturn/rt/fps_hud.c`, `kernel.c`)
One new readout line on the row above `PIC`: `PROF T38 G12 S0 O4 I46`, percent of the master's time per second (60 vblanks), FRT based. T = the game tick (task 4's runs with the vblank handler's time taken out when a vblank landed inside one), G = graphics (the vblank snapshot and hand-off to the slave), S = sound (`sat_audio_frame`), O = the rest of the work (other game tasks, the game's vblank body, dispatcher), I = idle (the task walk was done, the master spun). They add to 100. The TICK/CUT line (line 4) and the HW line (line 6) are untouched; the other lines are unchanged. Cost: the handler adds 6 reads and sums per vblank, the tick adds 2 FRT reads. In the console model PROF reads from `T36..38 G12 S0 O4 I46` against the table's 42 % tick plus other tasks, 14 % handler, 44 % idle.

## 7. Photo checklist
See the README in the disc folder.

## 8. Gates
(see GATES)

## 9. Risks and what is next
(see RISKS)
