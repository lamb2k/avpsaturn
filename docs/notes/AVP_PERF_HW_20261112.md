# Master time on the console: where it goes and what moved (lane perf-hw, 2026-11-12)

Disc `avp_3h_A_fix7p1` = fix7n4 (source 9071bc8, head 9e65039) plus four switches, all ON: `-DSAT_PLACE_FN -DSAT_HOT_STACK_HW -DSAT_HOT_GFXRAM_HW -DSAT_HOT_GFX_HW -DSAT_PROF_LINE`. Source commit `be14055` (build id on the readout: `F2 BE1405`). Branch `lane/perf-hw-20261112`. Gameplay, graphics and sound code are not changed: only where code and data sit, and one new readout line.

**Labels.** EMULATED = strict Ymir (my own patched copy, JP BIOS, 4 MB cart, SH-2 cache on) with its stock bus costs, which do not tell the three RAMs apart. MODELLED = the same Ymir run with `HW_MODEL=1`: cache line fills, cache-through accesses and writes charged from published Saturn figures (section 2). CONSOLE = owner photos only (quoted, not measured here). Nothing in this note is a console measurement of the new disc.

## 1. Result in five lines
1. The console's slow master is memory placement, not the game. Stock Ymir charges one flat cost for a work RAM, low RAM and cart access, and charges nothing for instruction fetches. The board does not: Sega's FAQ gives 7 clocks to refill a 16 byte cache line from high RAM and 56 from low RAM. In fix7n4, 68 % of the instructions the master runs in the game tick come from low RAM, and the vblank snapshot reads its 128 KB graphics image from low RAM.
2. MODELLED, that alone reproduces the console. fix7n4 in the crowded stage 1 fight: TICK 56, MISS 33, DONE 27, PIC 32 (console fix7n: MISS about 45, DONE 13-15, PIC 31-36). With the cart a little slower than assumed (10 clocks a 16 bit beat) it reads TICK 50, MISS 40, DONE 19, PIC 33.
3. fix7p1 moves what the master and slave actually run into high RAM. MODELLED, same scene: TICK 60, MISS 0, DONE 60, PIC 39 to 40 (was 32); the master is busy 56 % of a field (was 87 %).
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

## 5. Exactness (EMULATED, strict Ymir)
**Method.** The build's own scripted pad (`SAT_INPUT_SCRIPT`, the arcade route's schedule, indexed by vblank) plays from boot through the front end, stage 1 and into stage 2 (7,300 vblanks). My Ymir dumps the game's 64 KB work RAM at the start of game ticks 1000, 2000 ... 7000 (`HW_DUMP_TICKS`, `tools/perf/ramdiff.py`). With `HW_FLAT=1` every cached or cache-through access costs one cycle, so where code and data sit cannot move time: a placement-only change should give cycle-identical runs. The reference builds carry the same instructions (PROF line and the scripted pad in both) with the old layout: `B0P` = fix7n4 + PROF + script; `B0E` the same plus `SAT_BOOT_CLEAR_EQ`.

**Controls (they say how much the test can see).**
- The same build run twice, and on both of my Ymir copies: identical RAM at all 7 marks (stock and flat timing).
- Timing alone: the master 0.3 % slower changes only the 68000 stack scratch bytes (ff7fc6 to ff7fe7, 36 bytes over all 7 marks); 1 % slower, 4 bytes or fewer until tick 4000, then 250 to 420 bytes; 2 % slower, 31 bytes or fewer until tick 5000, then about 1000; the region model, 1,000 to 3,500 bytes. The game's state depends on timing, so a build that changes time by even a little cannot be compared byte for byte after a few thousand ticks.

**Results.**

| switch | pair | result |
|---|---|---|
| `SAT_PLACE_FN` alone | `Z1` (function placement, PROF, script) against `B0P` | **identical**: the RAM images at all 7 marks, and every per-vblank counter the probe logs (task runs, idle runs, FRT at the pass end, tick writes, pictures, skips, overruns) over all 7,300 vblanks. The two runs are cycle for cycle the same. |
| `SAT_HOT_STACK_HW`, `SAT_HOT_GFXRAM_HW`, `SAT_HOT_GFX_HW`, and all four with PLACE_FN | `P2E` (all switches, script, EQ) against `B0E` | **not identical, and not established either way.** 962 differing bytes at tick 1000, 1,900 at tick 4000. The runs are not in step from the first field: the master's idle task runs in the first field (the one after the dispatcher starts) are 84 fewer (299 against 383) and the probe sees one more tick write before the first vblank, and the offset then stays constant. Stage 1 starts at the same vblank in both (1128); stage 2 starts at vblank 4745 (old layout) and 4575 (new): the open loop bot then plays a different fight. |

What I think this is, and what I could not show. The code that runs is the same except addresses (and, outside the EQ builds, one range check in the boot's bss clear). The data moves change the size of the two images the loader copies (high RAM image 789 KB to 564 KB, low RAM image 822 KB to 1,046 KB) and so the work between the CD finishing and the game's dispatcher starting; the game then starts at another phase of the video frame, a tick lands on the other side of the first vblank, and the game stays one tick out of step with the vblank-indexed script, which the timing controls show is enough to change the state. I tried to cancel the offset with a delay at `sat_main` (`HW_BOOTDELAY`): it did not move the first field, because that stretch is paced by the CD, not by instructions. I did not find the first-field difference's exact origin. **So the data moves are exact by construction (no source line of the game, renderer or sound code changed, the alignment gate passes on every moved table, the Ymir misalignment gate is clean) but Ymir has not confirmed it; treat them as unconfirmed.** A confirmation needs a start synchronised to the CD or to the first vblank (a Ymir save state at the stage start would do it).

## 6. The PROF line (`saturn/rt/fps_hud.c`, `kernel.c`)
One new readout line on the row above `PIC`: `PROF T38 G12 S0 O4 I46`, percent of the master's time per second (60 vblanks), FRT based. T = the game tick (task 4's runs with the vblank handler's time taken out when a vblank landed inside one), G = graphics (the vblank snapshot and hand-off to the slave), S = sound (`sat_audio_frame`), O = the rest of the work (other game tasks, the game's vblank body, dispatcher), I = idle (the task walk was done, the master spun). They add to 100. The TICK/CUT line (line 4) and the HW line (line 6) are untouched; the other lines are unchanged. Cost: the handler adds 6 reads and sums per vblank, the tick adds 2 FRT reads. Checked against the model's own split (master tick 42 %, handler 14 %, idle 44 % over the window): single seconds of the readout read `PROF T37 G9 S0 O3 I51` (model run), `T38 G11 S0 O1 I50` (stock Ymir) and `T38 G12 S0 O4 I46` (an earlier build), i.e. busy 49 to 54 % against 56 %, within what one second of a fight varies. The sound share is under 1 %.

## 7. Photo checklist
In the disc folder README (`E:\AvP\package-integration\fenrir\avp_3h_A_fix7p1\README.txt`): a) the readout in a crowded stage 1 fight (TICK, MISS, DONE, PIC, PROF), b) Wolverine's first dialogue box, c) a continue, d) on any bad first boot the HW line.

## 8. Before and after (MODELLED unless marked), stage 1-1 Coffee Shop crowd, 1200 vblanks after the first 300, scripted bot, health held
Same disc source, same route, TICK from the game's own byte (windows right after a file load are left out: TICK reads high there, it is catch-up).

| run | build | TICK | MISS | DONE | PIC | SKIP |
|---|---|---|---|---|---|---|
| model, figures of section 2 | fix7n4 | 56.0 | 32.9 | 27.1 | 31.9 | 28.0 |
| same | fix7p1 | 60.0 | 0 | 60 | 39.0 | 21.0 |
| model, cart 10 per beat (slower cart) | fix7n4 | 50.5 | 40.5 | 19.5 | 32.5 | 27.4 |
| same | fix7p1 | 60.0 | 0 | 60 | 40.1 | 19.8 |
| model, no write buffer at all | fix7n4 | 50.0 | 40.3 | 19.7 | 33.5 | 26.5 |
| same | fix7p1 | 60.0 | 0.4 | 59.6 | 30.0 | 30.0 |
| stock Ymir (EMULATED) | fix7n4 | 60.0 | 0 | 60 | 52.3 | 7.7 |
| same | fix7p1 | 60.0 | 0 | 60 | 57.8 | 2.1 |
| console (fix7n photos, crowded stage 1) | fix7n | not read | about 45 | 13-15 | 31-36 | |

Master time (model, default figures): busy 498.8 M of 573.8 M cycles (87 %) before, 319.7 M of 574.8 M (56 %) after. Memory stalls on the master: tick 260.5 M to 88.0 M, vblank handler 65.7 M to 24.3 M; on the slave 157 M to 57 M. In the model, instruction line fills from low RAM go from 186 M to 6 M, handler data fills from low RAM from 43 M to 1 M, cart code fills from 37 M to 4 M.

Other scenes (model, MISS / PIC, fix7n4 then fix7p1; TICK left out because those windows hold a file-load catch-up): 1-2 boss 4.7 / 43.1 then 0 / 54.2; stage 2-1 3.2 / 44.7 then 0 / 56.5; stage 3 5.6 / 44.9 then 0 / 43.8 (the game runs at full speed, so the slave draws more change per picture).

**Read the PIC columns carefully.** With the master fixed, the slave is the limit: its 309 M instructions a window (scroll 1 redraw in `draw_scroll1`, `home_row_blank` and `home_row_map`, `cache_find`, the sprite build) leave it busy about 80 %, and a game that now runs at 60 ticks hands it more change per picture than one at 50. PIC therefore rises by 20 to 36 % in four model runs and falls (33.5 to 30.0) in the one run that charges every write in full. SKIP stays high in the model because of that.

**The uniform slowdown test (speed lane's model, strict Ymir with the master's cycles scaled by 3.0, no memory model): no improvement, and none is possible there.** fix7n4: TICK 45.1, MISS 43.4, DONE 16.6, PIC 37.5; fix7p1: 43.0, 44.5, 15.5, 35.2. A uniform factor multiplies every instruction's cost alike, so it cannot see where code sits; the 4 percent that the new build is slower there is cache luck and the PROF code. Placement is a different kind of slowness, which is why the region-aware model above is the test that matters. The model's fix7n4 reproduces the console's MISS and PIC without any factor; the factor of 3 to 3.5 that the speed lane needed is what the missing memory costs add up to.

## 9. Gates
- Build (the build fails on them): `tools/vdp2_cycle_check.py` PASS; `tools/align_gate.py`: 325 data symbols (0 of unknown type), 46 reviewed cast sites, 197 accessor calls, 287 round files and `REVEAL.BIN`: 0 hits; boot data addresses ok; Wolverine block `0x27F2FB8` size 23,116 outside the ROM image and every stretch (canary ok); `cold1_at` 0x027DF000 unchanged. Budgets: high RAM free 72 (fix7n4 924), low RAM free 2,432 (96), cart free 2,448 (5,008).
- Tests: `tests/align_gate_test.py` (13 checks, 0 failures), `tests/lat_protocol_test.py` PASS, `tests/vdp2_cycle_check_test.py` PASS.
- Strict Ymir data misalignment gate (`tools/ymir_misalign_gate.py --run`, my own patched exe, shipped disc, boot, title, stage 1, KO, continue with another character): 0 data accesses (5,908 instruction fetch artefacts filtered).
- Strict Ymir, stock timing, the staged `avp_3h_A_fix7p1.cue`: TICK 60 and MISS 0 over the whole crowded fight (1200 vblanks), PIC 57.8; the readout shows `PROF`, `TICK 60 CUT 20`, `HW SND 1 OK TEST 7` and build id `F2 BE1405`.
- Strict Ymir, uniform 3x master: not better (section 8, explained). Region-aware model: better in every run for TICK, MISS and DONE; PIC better in four of five runs.
- Exactness: section 5 (placement alone: identical, cycle for cycle; the data moves: unconfirmed).

## 10. Risks
- **Everything is emulator and model.** The A-bus cart figure is an assumption (6 clocks a beat; 10 matches the console's MISS better), and the model leaves out contention between the two SH-2s for the high RAM bus. Moving the slave's data and stack into high RAM adds slave traffic on the bus the master uses; if the board charges for that, the master's gain is smaller than modelled. The master's idle spin (40 M writes a window, mostly its stack and `sat_cpu`) already loads that bus.
- **Unprofiled scenes.** 7 scenes decided what stays in high RAM. A function that none of them ran may now sit in low RAM where fix7n4 had it in high RAM (225 KB of fix7n4's high RAM code left it). No run here showed one, but the plan is data driven: more scenes (other stages, bosses, Wolverine and Mega Man play, versus) and a rebuild fix it. A rebuild takes about 13 minutes (the round files restore cart pages that hold code).
- **High RAM free is 72 bytes.** The planner relinks until both RAMs fit, so growth makes it demote more cold code instead of failing, but the margin is thin by design. Cart free is 2,448: 2 KB of the old margin went to cold code (`PLACE_FN_COLD1_EXTRA`) so that both work RAMs fit; `cold1_at` did not move, the 4 KB step is not crossed.
- **Not exercised in Ymir by this lane:** Wolverine's dialogue box (his code is not moved: `wolverine.o` and `wv_features.o` stay whole in the cart; `guests.o` is placed by the planner), the quit-to-title restart (`sat_home_restart` re-clears bss; the slave stack's range is skipped in the high RAM clear), Mega Man, versus. The alignment gate covers the data symbols of all of them.
- **PROF line:** one row above PIC, over the picture's bottom rows; the console's overscan may crop it (the readout's other lines sit at the very bottom). S reads 0 almost always (the sound frame is under 1 percent).
- **Test hooks:** `SAT_FSEC_ONLY`, `SAT_BOOT_CLEAR_EQ` and the `SAT_INPUT_SCRIPT` placement tweak exist for the exactness runs only and are off in every release recipe.

## 11. Next (ranked by the model)
1. The slave: redraw only the changed scroll 1 rows (SUPER_ANSWER_PERF_GAP, item 1) and the sprite build; PIC is bound by them now. `draw_scroll1`, `home_row_blank`, `home_row_map` and `cache_find` are 80 % of its instructions.
2. `pb_at`: the 68K address lookup is a call per access, 10.8 % of the master's instructions (4 % of its modelled cycles); an inline copy trades code size against room in high RAM.
3. `snap_layer`: 14 % of the master's instructions are the per-vblank sums over the visible layer cells; a dirty flag from the game's writes would remove most of it.
4. The idle spin writes about 40 M words a window (home poll, duel step, `sat_boot_stack`): call them once a field, not once a walk. It matters for the shared bus, not for the master's own time.
5. VDP1 command build through SCU DMA (slave VDP1 write waits 26 M cycles, 4.6 % of its time) and hot ROM tables copied into high RAM (cart data fills 2.9 %).
6. Read the console: the PROF line and TICK give the first measured split; the cart beat can be fitted from MISS in the same scene.

## 12. Files
Lane folder `E:\AvP\learning\lane-perf-hw`: `ymir_hw` and `ymir_hw2` (two copies of the profiling Ymir, so two runs go at once; paths are compiled in), `hwprof_*.txt` dumps, `runs/*`, `pbuild.sh`, `wd` (work dir). Repo: `tools/perf/` (`fn_heat.py` makes `saturn/rt/place_fn.json`; `ramdiff.py`, `hwtable.py`; `ymir/` scripts and `sh2_perf_hw.diff`), `saturn/rt/build.py` (planner), `kernel.c`, `fps_hud.c`, `pad.c`.
