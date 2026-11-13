# fix7w1: Wolverine master time, profiled and trimmed (lane wv-speed, 2026-11-13)

Disc `avp_3h_A_fix7w1`, branch `lane/wv-speed-20261113`, on `lane/quitcard-20261113` head `a978d300` (fix7p6, code `ea2c0da5`). Two new switches, both ON in the recipe, both default off in the tree: `SAT_WV_PLACE` and `SAT_GUEST_GROUPS_MM`. Labels as in the earlier perf notes: EMULATED = strict Ymir (my own copies, `E:\AvP\learning\lane-wv-speed\ymir_wv*`), MODELLED = the same Ymir with the board's memory costs (`HW_MODEL=1`: line fills by region, write buffer, A-bus cart 6 clocks a beat unless stated), CONSOLE = owner photos only. Nothing here is a console measurement. Read `AVP_PERF_HW_20261112.md` for the model.

## Result in six lines
1. **The master is not what holds Wolverine's fight below 60 in the model.** In steady fights on fix7p5 (`W0`), MODELLED, TICK 60 / MISS 0 / PIC 60 in every scene I ran (eight Wolverine windows). The "TICK about 56" of the earlier notes came from a window with a KO, a CONTINUE screen and a load in it (section 1). Wolverine is not heavier than Predator for the master: busy 42 to 60 % of a field as him, 49 to 64 % as Predator Warrior on the same stages.
2. **What was his own cost:** the guest layer (his hooks in the cart tail, the sprite group notes, the snapshot hook) was 9.8 K master cycles a vblank in a fight, 2.2 % of a field and 4 % of the master's busy time, almost all of it cache line fills from the cart. Plus his native pose emitter `f_aa38a` at about 1.5 % of a field (the game's own code, untouched).
3. **Fixes (each a switch, ON):** `SAT_WV_PLACE` puts his hooks and the lifted functions his scenes run into high RAM by heat; `SAT_GUEST_GROUPS_MM` drops the sprite group notes when Mega Man is not selected. The guest layer falls to 2.8 K cycles a vblank (0.6 % of a field), measured over 8,400 vblanks of seven scenes.
4. **Master busy, MODELLED, same bot scenes:** Wolverine 49.7 % to 48.3 % averaged over eight windows (the stage 1-1 crowd 59.8 to 54.7); on the deterministic tick-indexed route (2,900 vblanks of stage 1, special every 260 ticks) 64.2 to 62.2. Predator, three scenes: 55.1 to 54.6 (TICK, MISS and PIC unchanged; the bot makes up to 2.5 points of noise a scene).
5. **Margin:** with the master made 1.6 times slower than the model the crowd fight misses 10.8 ticks a second before and 5.0 after; with the slow cart model (10 clocks a beat, no write buffer) TICK stays 60 both ways.
6. **Exact:** on the tick-indexed Wolverine route, game RAM is identical in the flat memory model for placement alone, and with both switches differs only in dead stack scratch bytes where the timing moves a vblank; nothing in the game state moves over 3,500 ticks (section 6).

**What I did not do and cannot say:** there is no console number here. I could not reproduce a master limit in a Wolverine fight, so I cannot promise the console reaches 60 ticks from this change alone. I can say where the master's time goes (section 2), that his own share is now small, and what the larger shared costs are (section 7).

## 1. The premise, re-measured: Wolverine's fight is not master limited in the model
The "TICK about 56" in Wolverine fights (perf-pic note, section 5) does not reproduce in a fight. My first Wolverine run (`w0_crowd_m`, the arcade route of `wscene.sh`) read TICK 56.2 over its window, and the window was a CONTINUE screen and then the ranking: the pad route had not kept the player alive (stage word 02, then 00 in `gs.log`; `runs\w0_crowd_m\stage.png`, `end.png`). Windows that hold a KO, a continue or a load read low or high in TICK whatever the character. With the player held alive in the fight (stage select route, Wolverine picked, health held, a bot that also presses his special, attack plus jump together, every 300 vblanks; 1,200 vblanks from 700 into the stage) the fix7p5 disc `W0` reads TICK 60 / MISS 0 / PIC 60 in all eight scenes I ran (section 4). Predator on the same scenes is no faster.

The model is a lower bound for the master (perf-hw note, section 2), so the work below does two things: it removes what is Wolverine's own cost, and it measures the margin (section 5).

**A trap found on the way.** The Ymir profile I copied (`prof` of the perf-pic lane) carried a saved bonus-character setting in its backup RAM (Wolverine and Mega Man both on, `UNLOCK_FLAGS` bit 8 up): `boot.c` writes a saved setting over `sat_guest_sel`, so even the `GUEST_DEFAULT=0` "Predator" runs had the guest layer on and the Mega Man bit set (which also switches the palette keep path off). All runs in this note use a fresh backup RAM (the perf-hw lane's `prof_fresh`, md5 `08851ed5`): `W` builds select only Wolverine (`sel` = 1), `P` builds select nothing (`sel` = 0, the release behaviour). The first set of profiles (`old_sel3` folders) is kept but is not used for any number here, except that the heat file `place_fn_wv.json` was made from it (section 9).

## 2. Profile of the master in Wolverine fights (MODELLED, `W0` = fix7p5 recipe with `GUEST_DEFAULT=1`)
Windows as in section 1. A field is 447 K master cycles.

**Totals.** Master busy (game tick plus vblank handler): stage 1-1 crowd (list entry 0) 59 % of a field, heavy stage 0A (entry 4) 57 %, 1-2 boss 44 %, other entries 44 to 47 %. Of the busy cycles 45 % are instructions and 55 % stalls.

**By memory region (share of the master's busy cycles; crowd and stage 0A):**
| stall | share | where it comes from |
|---|---|---|
| writes to high RAM | 15 to 16 % (plus 4 to 5 % write buffer waits) | the 68000 register file `sat_cpu`, task stacks, `sat_alien_last`: the lifted code keeps every register in memory |
| instruction fills, high RAM | 9 to 11 % | a 4 KB cache against 490 KB of hot code |
| instruction fills, low RAM | 6.0 % (crowd), 9.5 % (0A) | 1.3 % and 2.9 % of the instructions: functions no profiled scene had ranked into high RAM (`f_61a36`, `f_af8b4`, `f_255fa`, `f_25606`, `f_60c2e` ...) |
| data fills, cart | 4.6 to 5.9 % | ROM image and opcode view tables (`ROMB`, `OPX`) and his block `wv_blk` (23 KB, 0.25 % of a field) |
| data fills, high RAM | 5.5 to 5.9 % | `RAMB` (game RAM), `task_stacks`, `sat_gfxram` |
| instruction fills, cart | 3.0 to 3.2 % | his hooks, `sat_guest_group`, `f_b0c9a` (8 KB, dialogue) |
98 % (crowd) and 96 % (0A) of the instructions run from high RAM.

**By function, stage 0A, `W0` (cycles a vblank, share of a field):**
| function | where | cycles | field | what it is |
|---|---|---|---|---|
| `sat_gfx_snapshot_layers` + `snap_layer` | HW | 26.1 K + 7.8 K | 5.8 + 1.7 % | the vblank snapshot's layer sums (irq) |
| `sat_gfx_snapshot_begin` | HW | 18.0 K | 4.0 % | the vblank snapshot copy (irq) |
| `pb_at` | HW | 24.3 K | 5.4 % | the 68000 address to RAM lookup, a call per access (tick) |
| `f_aa016` | HW | 7.9 K | 1.8 % | game: sprite assembly |
| `f_aa38a` | HW | 5.9 K | 1.3 % | game: pose assembly emitter; his native records use it (7.2 K in the crowd against 0.3 K as Predator) |
| `f_dispatch` | HW | 5.4 K | 1.2 % | the lifted code's dispatcher |
| `sat_gfx_vblank` | HW | 5.7 K | 1.3 % | the vblank hand-off |
| `f_61a36` | LW | 5.1 K | 1.1 % | game; ran from low RAM, 3.9 K of it line fills |
| his guest layer (15 `wv_*` and `sat_guest_*` functions) | cart and HW | 9.8 K | 2.2 % | section 3 (aggregate of seven scenes) |
Past these a long tail: 99 % of the instructions come from about 300 functions.

**Stock timing (EMULATED)** was not profiled again: the stock Ymir charges nothing for instruction fetches, so it cannot see any of this (perf-hw note, section 1). The earlier lanes' stock runs read TICK 60 in these scenes (`PROF T22 G9 O2 I67`).

## 3. The two fixes
Both are default off in the tree and ON in the fix7w1 recipe (the fix7p6 recipe plus `-DSAT_WV_PLACE -DSAT_GUEST_GROUPS_MM`). Neither changes what the game computes.

**`SAT_WV_PLACE` (`saturn/rt/build.py`, `saturn/rt/place_fn_wv.json`): his code, and the lifted code his scenes run, placed by heat.**
- Before: `wolverine.o`, `wv_features.o` and `wv_sound.o` (his player hooks, the pad hook, the snapshot hook, the Berserker events, the healing factor, the flash) were linked whole into the cart tail, never function by function. Every call into them paid the A-bus line fill (48 clocks a 16 byte line in the model against 7 from high RAM): `wv_nat_sync`, `sat_guest_wolverine_objects`, `is_wolverine`, `sat_guest_wolverine_tick` and `wv_tick_inner`, `wv_pad_inner`, `wv_player`, `wv_reset`. Together with `sat_guest_group` and `sat_guest_objects` the guest layer was 9.8 K cycles a vblank (2.2 % of a field) over seven scenes.
- Now: with the switch the three objects are built with `-ffunction-sections` and enter the `SAT_PLACE_FN` planner as cart tail functions, ranked by cost per byte with every other function. `place_fn_wv.json` is the heat of Wolverine scenes (stage list entries 0 to 5 and 7, the stage 1 opening with its talk box; `fn_heat.py` on the profiles of `W0`) and is added to `place_fn.json`'s heat. It also names the lifted functions those scenes run from low RAM or the cart (`f_61a36`, `f_255fa`, `f_25606`, `f_60c2e` ...; about 22 K cycles a vblank of fills, 5 % of a field, in the heavy scenes) and the planner moves them into high RAM, demoting never-run code in their place. The fix7p2 rule holds: nothing that ran in fix7n4's high RAM is demoted.
- Budgets (the planner relinks until both RAMs fit): high RAM free 72, low RAM free 580, cart tail free 2,516 (fix7p6: 56, 612, 2,516).

**`SAT_GUEST_GROUPS_MM` (`saturn/game/game_bind.c`; `build.py` passes it to the object): no sprite group notes for Wolverine alone.**
- Before: `f_aa59a` (the sprite origin routine, once per sprite group of the frame) called `sat_guest_group` in the cart tail whenever any bonus character was selected, and `sat_guest_objects` walked the list at each snapshot. The list is read only for a guest drawn through `guest_draw` (Mega Man) and, in the skin build, for Wolverine's shot refusal. The native Wolverine uses none of it (`is_wolverine_shot` is not compiled in the native build; `guest_draw` answers 0 for his slot).
- Now: the call is made only when the Mega Man bit of `sat_guest_sel` is set. With Wolverine alone the list stays empty and `sat_guest_objects` has nothing to walk (it fell from 2.1 K to 0.3 K cycles a vblank, `sat_guest_group` from 2.2 K to 0). With Mega Man selected, alone or with him, nothing changes.
- Not changed on purpose: the player update hook (once per player update), the pad hook (once a vblank) and the snapshot hook. Each is small once in high RAM (section 4). Folding `wv_nat_sync` away would change when the native tables switch, which the quit-to-title fix of fix7p3 depends on.

## 4. Before and after
MODELLED, `HW_MODEL=1`, fresh backup RAM, same route and bot. The bot reads the wall clock, so two runs of one scene are not move for move the same (the same disc twice differs by up to 1 point of busy time); for a move-for-move comparison see the tick-indexed pair under the table. `W0` / `P0` = fix7p5 recipe (`GUEST_DEFAULT=1` / release `GUEST_DEFAULT=0`), `W6` / `P6` = the fix7w1 recipe on fix7p6. busy % = master tick plus vblank handler as a share of a field; TICK, MISS, PIC, SKIP per 60 vblanks as the readout counts them (TICK above 60 = catch-up inside the window after a load, the same for Wolverine and Predator).

| scene | build | busy % | master kcycles / vblank | TICK | MISS | PIC | SKIP |
|---|---|---|---|---|---|---|---|
| stage0_m | before | 59.8 | 286 | 60.0 | 0.0 | 60.0 | 0.0 |
| stage0_m | after | 54.7 | 262 | 60.0 | 0.0 | 60.0 | 0.0 |
| s0e_m | before | 60.6 | 290 | 65.0 | 0.1 | 59.8 | 0.2 |
| s0e_m | after | 59.2 | 283 | 65.1 | 0.0 | 59.8 | 0.2 |
| stage1_m | before | 43.8 | 210 | 60.0 | 0.0 | 60.0 | 0.0 |
| stage1_m | after | 42.5 | 203 | 60.0 | 0.0 | 60.0 | 0.0 |
| stage2_m | before | 44.6 | 214 | 77.4 | 0.0 | 60.0 | 0.0 |
| stage2_m | after | 47.1 | 225 | 77.5 | 0.0 | 60.0 | 0.0 |
| stage3_m | before | 44.1 | 211 | 60.0 | 0.0 | 60.0 | 0.1 |
| stage3_m | after | 42.1 | 201 | 60.0 | 0.0 | 60.0 | 0.0 |
| stage4_m | before | 53.0 | 254 | 92.2 | 0.0 | 59.9 | 0.1 |
| stage4_m | after | 50.8 | 243 | 92.4 | 0.0 | 59.9 | 0.1 |
| stage5_m | before | 46.2 | 221 | 60.0 | 0.0 | 60.0 | 0.0 |
| stage5_m | after | 45.0 | 215 | 60.0 | 0.0 | 60.0 | 0.0 |
| stage7_m | before | 45.7 | 219 | 61.2 | 0.1 | 60.0 | 0.0 |
| stage7_m | after | 44.9 | 215 | 61.2 | 0.1 | 60.0 | 0.0 |
| pred0_m | before | 63.4 | 303 | 60.0 | 0.0 | 60.0 | 0.0 |
| pred0_m | after | 64.3 | 308 | 60.0 | 0.0 | 60.0 | 0.0 |
| pred1_m | before | 51.3 | 245 | 60.0 | 0.0 | 60.0 | 0.0 |
| pred1_m | after | 48.8 | 234 | 60.2 | 0.0 | 60.0 | 0.0 |
| pred4_m | before | 50.7 | 243 | 92.7 | 0.0 | 59.9 | 0.1 |
| pred4_m | after | 50.7 | 243 | 92.7 | 0.0 | 59.9 | 0.1 |

Scene names: `stage0` stage select entry 0 (stage 1-1, the Coffee Shop crowd), `s0e` the same starting at the stage's first vblank with the opening talk box (1,500 vblanks), `stage1` the 1-2 boss, `stage2`, `stage3`, `stage5`, `stage7` early entries, `stage4` stage 0A (the heaviest), `pred0`, `pred1`, `pred4` Predator Warrior on entries 0, 1 and 4. Averages: Wolverine 49.7 % to 48.3 % (eight windows), Predator 55.1 % to 54.6 % (three). Wolverine `stage2` reads worse after (44.6 to 47.1): the two runs did not run the same functions (six lifted functions ran only in the second, none hot enough for high RAM); the guest layer itself fell there like everywhere (`sat_guest_group` 1.6 K to 0, `wv_nat_sync` 1.6 K to 0.6 K). Predator `pred0` reads +0.9 and `pred1` -2.5: noise of the bot, not a code path (the instruction counts of the functions in the difference are equal; their stalls vary with where lines land in the cache).

**Deterministic pair (tick-indexed route, MODELLED, window from vblank 1,500 to 4,400 of the scripted stage 1; the same game ticks on both discs):** `WT0b` (fix7p5 layout) busy 64.2 %, 307.4 K master cycles a vblank; `WT1b` (both switches) 62.2 %, 297.5 K (-3.2 %). In it the guest layer fell 13.2 K to 4.0 K cycles a vblank, cart stalls 12.9 K to 7.5 K, and low RAM stalls rose 17.2 K to 20.5 K (functions of the route that are in neither heat file run from low RAM; section 9).

## 5. Margin: how much slower can the master be
`GS_MSLOW=1.6` multiplies every master cycle by 1.6 (the speed lane's brute force test, the model otherwise unchanged). `c10` = `HW_CARTBEAT=10 HW_WBUF=0` (cart 10 clocks a beat, no write buffer: the slow end of what the console might be). MODELLED, same bot, 1,200 vblanks:
| scene | setting | `W0` before: busy / TICK / MISS | `W6` after: busy / TICK / MISS |
|---|---|---|---|
| crowd (entry 0) | cart 10, no write buffer | 69.5 % / 60.0 / 0.0 | 67.0 % / 60.0 / 0.0 |
| 0A (entry 4) | cart 10, no write buffer | 60.3 % / 90.6 / 0.0 | 58.8 % / 91.0 / 0.2 |
| crowd | master x1.6 | 88.6 % / 59.2 / **10.8** | 85.9 % / 60.0 / **5.0** |
| 0A | master x1.6 | 77.3 % / 85.7 / **7.9** | 76.1 % / 86.1 / **6.0** |
The master would have to be about 1.5 times slower than my model before the crowd fight starts to miss ticks, and the change moves that point out a little. A console that is slower than that is outside what this lane can say.

## 6. Exactness
Method as in fix7p2 section 4: the build's own scripted pad indexed by game ticks (`SAT_INPUT_SCRIPT` + `SAT_INPUT_SCRIPT_TICK` + `SAT_BOOT_CLEAR_EQ`), here with a new test flag `SAT_INPUT_SCRIPT_WV` (`pad.c`): one right tap on the character select picks Wolverine (verified: the player block's character byte +0xd2 reads 1 at every mark, and the state reads 020008, his special, at tick 600), and attack plus jump together for 8 ticks every 260 ticks of the stage. Healing and the flash are in the recipe, so they run (his health at the marks 101, 101, 97, 101, 71, 30, 47). My Ymir dumps all 64 KB of game RAM at stage ticks 300, 600, 1000, 1500, 2000, 3000 and 3500 (`tools/perf/ramdiff.py`). The test flags are in test builds only: reference `WT0b` = fix7p5 source with the test route, new `WT1b` = the same plus both switches (built on the fix7p5 base; the fix7p6 change is the quit card and the boot diagnostics, not a game path). 
| pair (all on the tick-indexed Wolverine route, 7 marks over 3,500 ticks) | model | result |
|---|---|---|
| `WT0b` against `WT2b` (`SAT_WV_PLACE` alone) | flat (`HW_FLAT=1`: placement cannot move time) | **identical**, all 65,536 bytes at all 7 marks |
| `WT0b` against `WT2b` | stock timing | 2 to 4 bytes at each mark, all in the 68000 stack scratch (ff7fc6 to ff7fe7): the interrupt landing at another instruction |
| `WT0b` against `WT1b` (both switches) | flat | 2 to 4 bytes at each mark (6 marks of 7), all in ff7fc6 to ff7fe7; 0 at tick 3500 |
| `WT0b` against `WT1b` | stock timing | the same stack bytes plus about 18 bytes in ff0634 to ff065b, constant at all 7 marks; nothing else differs (0 other bytes at tick 3500) |
So placement is exact by construction and by test. `SAT_GUEST_GROUPS_MM` removes instructions (a call and a list walk), so the vblank lands at other instructions and the stack scratch moves, exactly the "timing alone" control of fix7p2 section 4 (a master 0.3 % slower changes 36 bytes of ff7fc6 to ff7fe7). The bytes at ff0634 to ff065b are a leftover in a 68000 stack area: identical at every mark of a run, written once early (they are the same in each run of one build, different between the builds with and without the group call), never read as state: every game variable (positions, health, enemy pool, stage, random state) is equal at all 7 marks. Wolverine fights, special and healing run in the route (character byte 1 at every mark; his health 101, 101, 97, 101, 71, 30, 47; 8 to 10 enemies alive). I did not prove the ff0634 bytes dead by a write trace; the 3,500 tick equality of everything else is the evidence.


## 7. Pipelining master work onto the slave (the coordinator's fallback): measured, not implemented
Where the master's non-logic time goes (stage 0A as Wolverine, MODELLED, cycles a vblank on the master, `W0`), and what could move:
| candidate | cycles | share of a field | slave cost if moved | sync risk |
|---|---|---|---|---|
| vblank snapshot: `sat_gfx_snapshot_begin` + `_layers` + `snap_layer` + `sat_gfx_vblank` | 58 K | 13 % (a quarter of the master's busy time) | the same cycles (the slave runs the same code, from the same memories) | high, see below |
| the layer sums alone (`snap_layer` and the sums inside `_layers`) | about 16 K (estimate, not separated in the profile) | 3.6 % | about 16 K, plus a copy | medium |
| guest hooks, palette and talk patches (after this lane) | 2.8 K, of which the palette keep path is almost nothing | 0.6 % | not worth a hand-off | low |
| `pb_at` (the lookup, a call per access) | 24 K | 5.4 % | cannot move: it is the game tick's own address translation | n/a |
The slave's own budget: its draw of one picture takes 1,100 to 1,300 FRT ticks mean, p99 about 2,100 (a field is 3,500), so about 0.37 of a field mean and 0.6 at the 99th percentile (perf-pic note). Adding the 58 K cycles (0.13 field) gives about 0.5 mean and 0.73 p99: it fits on average, with little room at the peaks, and the slave also waits for the master's half of the picture today.

**Why I did not implement it.** The snapshot is a consistent cut of the game's RAM, graphics RAM image and object list taken in the vblank handler while the game tick is preempted. On the slave the master's game tick keeps running during the copy and writes the same memories through the lifted code's `WR8/16/32` (`pb_at` stores, no hook to flag a write), so the snapshot would tear; holding the master's tick during the slave's copy gives the cycles back and gains nothing. The slave-side half that is safe is the sums over the snapshot copy (after the master has copied the layer cells, the slave computes the sums and the change flags from its own buffer): about 16 K cycles a vblank (3.6 % of a field, 7 % of the master's busy time) for a copy of a few KB and a double buffered hand-off. That is the item I would try first; it changes when the slave learns of a changed layer (the flags arrive a half picture later), so it needs its own look check, which this lane did not have time for. The first candidate on the master's own side is a dirty flag for `snap_layer`, as the perf-hw note (section 11, item 3) already says.

## 8. Gates
- **Build (fails the build):** `vdp2_cycle_check` PASS; alignment gate 347 data symbols (0 of unknown type), 49 reviewed cast sites, 199 accessor calls, 287 round files and `REVEAL.BIN`: 0 hits; boot data addresses ok; Wolverine block canary ok (`wv_blk` 0x27f5f08, 23,116 bytes, inside the cart tail). Budgets of the shipped disc (`P6`): high RAM free 72, low RAM free 580, cart tail free 2,516 (fix7p6: 56, 612, 2,516; fix7p5: 72, 500, 2,372).
- **Tests on the tree:** `tests/align_gate_test.py` (pass), `tests/lat_protocol_test.py` (PASS), `tests/vdp2_cycle_check_test.py` (PASS).
- **Ymir misalignment gate (`tools/ymir_misalign_gate.py`, my own patched exe, fresh backup RAM, EMULATED):** the default route (boot, menu, ARCADE start, stage 1, KO, continue) on the shipped disc `P6` and on its Wolverine-on twin `W6`: **0 data accesses** (5,605 and 5,793 instruction fetch artefacts filtered); the stage select 1-2 boss as Wolverine (`W6`) and as Predator (`P6`), 900 vblanks: 0; four of the six exactness runs of section 6 (`WT0b` stock, `WT1b` stock, `WT2b` flat and stock): 0 each (the logs of the two flat runs of `WT0b` and `WT1b` were overwritten before I read them).
- **TICK and PIC in Predator scenes (MODELLED):** TICK 60.0 / 60.0 / 92.7 and PIC 60.0 / 60.0 / 59.9 on entries 0, 1 and 4 before; TICK 60.0 / 60.2 / 92.7 and PIC 60.0 / 60.0 / 59.9 after (92.7 is the catch-up window of entry 4, equal before and after). MISS 0 in all. Busy time 63.4 to 64.3, 51.3 to 48.8, 50.7 to 50.7.
- **Wolverine:** TICK 60 / MISS 0 / PIC 60 in the crowd, boss and entries 3, 5, 7 before and after; entries 2, 4 and 7 and the opening window read TICK above 60 from the catch-up after the load, MISS 0 to 0.1, PIC 59.8 to 60.0, same before and after.
- **Staged disc:** `E:\AvP\package-integration\fenrir\avp_3h_A_fix7w1` (track01 = the `P6` image, 26 audio tracks of the build, cue, `SHA256SUMS`, `README.txt`); booted from its cue in my Ymir, Predator Warrior stage 1-2, readout `F2 EBF3F3`, TICK 60, PIC 60, DONE 60, MISS 0 (the readout has 5 lines, no HW line, as fix7p6).
- Test flags in the shipped disc: none. `SAT_INPUT_SCRIPT*`, `SAT_BOOT_CLEAR_EQ` only in `WT0b`, `WT1b`, `WT2b` (never staged).

## 9. Not done, risks
- **No console number.** All timings are the model; I could not reproduce a master limit in a Wolverine fight; the 1.6 times slower master still misses 5 ticks a second in the crowd after the change.
- **Gain is small.** Wolverine's own guest layer is 2.2 % of a field before and 0.6 % after; the whole change is about 1.4 points of master busy time on average (0 to 5 by scene). The big master costs are shared with Predator: the snapshot (13 % of a field), `pb_at` (5.4 %), the register file writes (15 % of busy cycles). Those are the next work; the pipelining numbers are in section 7.
- **Heat file.** `place_fn_wv.json` was made from the first set of profiles (the ones with the bonus setting on Wolverine plus Mega Man in the backup RAM, section 1). The functions that ran are the same; the guest functions' weights are a little high (the group notes and the palette recopy ran). Regenerating from the fresh runs needs one more 25 minute build; it is not expected to move a function.
- **Left in low RAM or the cart on purpose:** `f_af8b4` (8.6 KB, 0.5 % of a field in 0A) and `f_b0c9a` (8.3 KB, dialogue) are too big for their cost per byte; his block `wv_blk` (23 KB) stays in the cart (data fills 0.25 % of a field). Functions that none of the 8 Wolverine scenes ran (the ending, versus, later stages as Wolverine, Boss Rush) stay where fix7p3's heat put them; the deterministic route shows 3 K cycles a vblank more low RAM stalls after than before for that reason.
- **`f_aa38a`** (his native pose emitter, 1.5 % of a field): the game's code; its cost follows the size of his pose assemblies (7.2 K cycles a vblank as him, 0.3 K as Predator). Smaller assemblies or the hot ones in fast RAM are the lever; not touched here (owner rule: no replacement, native character).
- **Mega Man** was not built or run (no data in the recipe). The switch leaves a Mega Man selection as it was (the group notes stay on) but it was not exercised.
- Predator numbers are one run a scene; the bot's noise (up to 2.5 points of busy time) is larger than the change there.

## 10. Files
- Lane folder `E:\AvP\learning\lane-wv-speed`: `pbuild.sh`, `wscene.sh` (scene routes), `worker.sh` and `tasks.txt` (the 30 scene runs), `exact.sh`, `busy.py`, `table.py`, `top.py`, `kinds.py`, `hooks.py`, `symdiff.py` (analysis), `ymir_wv`, `ymir_wv2`, `ymir_wv3` (my three Ymir copies, paths compiled in, built from the perf-pic lane's sources with `drv.py` gaining a Wolverine bot `bw` and `NOAUTO`), `an_*.txt`, `heat_*.json`, `exact/` (RAM dumps), `DELETED.txt`.
- Repo: `saturn/rt/build.py` (switches, planner), `saturn/rt/place_fn_wv.json`, `saturn/game/game_bind.c`, `saturn/rt/pad.c` (`SAT_INPUT_SCRIPT_WV`), `tools/wvspeed/` (the scripts above that are repo-sized).
