# Answer: closing the gap to a steady 60 pictures/s

Answers `docs/notes/REVIEW_QUESTION_PERF_GAP_20261111.md` (lane/perf-reconcile-20261110 f3dff5e).

**Basis.** Read-only review of `avp/integration` d0540c8 (`saturn/gfx/sat_gfx.c`, `saturn/rt/kernel.c`, `build.py`, `fps_hud.c`, `pad.c`) and the notes on that branch and the lane branch. Nothing was built or run. I could not read anything under `E:\AvP` (`runs\*\log.json`, `verify\`, `peak\`, `REVIEW_ANSWER_60FPS.md`), so every figure below is quoted from the pushed notes or derived from them, and is EMULATOR (Yaba, cache ON) unless marked. Costs in bytes and ticks for proposed changes are estimates from reading the code, not compiles.

## Short answer

1. A picture is lost only when one slave draw runs past a field (about 3,458 ticks from the wake). With B, 0e loses 1.2 to 2.5 pictures a second, so the gap is two or three over-long draws a second, each one a scroll-1 change.
2. The one change that should close 0e is an **incremental scroll-1 redraw with a re-stamp pass** (section 2). It is exact for the picture, costs about 300 B of code and 8 B of snapshot, and takes a HUD change from about 2 to 3 K ticks to an estimated 0.3 to 0.6 K.
3. Stage 24 is not explained by the pushed numbers: 6.7 K with 1.5 to 2.1 K of sprite build leaves about 4.6 K in the layers. Split it with the stage timers before building anything for it (section 1).
4. For sprites there is nothing to adopt blind. Yaba's cost is 4.4 ticks a command plus 332, so about 600 commands fill a field on their own; pairing and hints were both slower on Yaba. The console's ticks per command decide (sections 3 and 6).
5. The stage's first frame may be a full-cache scan per refused lookup, which has a 20-byte exact fix. That is a hypothesis; two existing counters confirm or kill it (section 4).

## Ranking

| # | Change | Expected gain (EMULATOR) | Bytes (estimate) | Risk | Exact |
|---|---|---|---|---|---|
| 1 | `SAT_S1_DIRTY`: incremental scroll-1 redraw, re-stamp first | 0e heavy draw 5.0 K to about 2.5 to 3.0 K, so no skip; 24 gains the same 1.5 to 2.5 K | about 300 B hot, 8 B low RAM | medium: residency argument below must hold | picture-exact, not VRAM-byte-exact |
| 2 | `SAT_CACHE_FULLSTAMP`: remember a failed free-slot scan for the rest of the draw | only if refusals are confirmed on the first frame; then most of the 31.8 K | about 20 B hot, 4 B bss | low | yes |
| 3 | Per-second draw peak on the readout | none; makes the console readings decisive | about 150 B cold, 12 B hot | low | n/a |
| 4 | Second-pad script (`SAT_INPUT_SCRIPT2`) | none; measures co-op | test builds only | low | n/a |
| 5 | Incremental scroll 2 (same re-stamp idea) | up to 0.9 K on scroll steps, only if the stage-24 split shows it | about 250 B hot | medium | picture-exact |
| 6 | Sprite build changes (pairing, hints, command reuse) | negative on Yaba; unknown on console | 512 B to 1 KB | high without console data | yes |

Do 1, 3 and 4 now. Do 2 after reading two counters. Hold 5 and 6 for measurements.

## 1. What still costs time

What the notes support:

| Part of a heavy draw | 3h plain, 0e | B (derived) |
|---|---|---|
| Sprites built, plot started | 0.7 to 2.2 K | same |
| Layer wait | 0.1 K | same |
| Scroll 2 and 3 | 0 to 0.9 K | same |
| Scroll 1 | 9.2 K (blank mask 1.5, column fit 6.2, cell loop 1.4) | about 2 to 3 K, from the 5.0 K total |
| Tile uploads | not a cause (0 to 50 sprite, 0 to 2 layer) | same |
| VDP1 plot wait | 2 to 4 ticks; held 0 to 1 % | same |

- **0e attack (5.0 K):** still a scroll-1 draw. The sprites and plot start take at most 2.2 K, so the draw fits a field once scroll 1 drops under about 1 K.
- **24 (6.7 K):** the note gives only the total and the sprite build. About 4.6 K sits in the layer phase, more than B's scroll 1 costs on 0e. Candidates are a scroll-2 redraw with row scroll on (64 columns by 15 rows, 960 lookups, instead of 375) or a larger non-blank scroll-1 area. I cannot tell which from the pushed data.
- **Measurement to take first:** build h3V (B plus `SAT_PERF_STAGES`), stage 24 attack and walk, median and worst of `sat_gfx_stage[5]`, `[7]-[6]`, `[8]-[7]`, `[9]-[8]`, `[10]`, `[11]`, `[12]` over the heavy draws only, plus `layer_uploads` and `refused_layer`. That is the breakdown the question asks for, and it decides whether item 5 is worth building.

How a skip arises (`kernel.c` vblank hook): the master takes a snapshot only when `gfx_done == gfx_handed`. A draw of 3.5 to 7 K therefore costs exactly one picture, and the slave then idles to the next vblank. Shaving a 5.0 K draw to 3.6 K gains nothing; it has to get under about 3,458.

## 2. Incremental scroll-1 redraw that keeps residency correct

**Why the plain skip is unsafe.** A layer slot is evictable when its stamp is not the current draw's (`cache_find`). The stamp advances every draw, and a slot is re-stamped only when its key is looked up. A full redraw looks up every visible cell, so it protects itself. A redraw of some rows leaves the other rows' slots with old stamps, and the first upload in a dirty row can take one of them while the name table still points at it.

**Design, `SAT_S1_DIRTY` (default off, needs MEMO and BLANKROWS):**

1. **Master, exact dirty rows.** In `snap_layer`'s copy pass for scroll 1 (it runs only when the sum moved), compare each word with the one it replaces and set bit `row` of a mask when they differ. Store the mask and the previous sum in the snapshot: `s1_rows`, `s1_from`. If the seed changed (position, `hud_flush`, `sel_ok`), set every bit. No hash is involved, so there is no collision case.
2. **Slave, when the mask may be used.** Only if `drawn_valid`, `snap.s1_from == drawn_s1`, the position key is unchanged, `snap.home == 0`, `snap.sel_ok == 0`, and the previous scroll-1 draw had no `refused_layer`. Anything else takes today's full path. `s1_from == drawn_s1` covers abandoned draws (`plot_wait_end` or `plot_start` returning early) and skipped snapshots: if the slave did not draw the picture the mask was computed against, it redraws everything.
3. **Slave, widen the mask to whole blocks.** A row's column map depends on the blank masks and weights of its block (the run of adjacent non-blank rows that `home_row_map` extends over). So redraw each dirty row plus every non-blank run touching it above and below, judged on the new contents. A dirty row that is now blank still spreads to both neighbours, which covers a block being split.
4. **Slave, re-stamp pass, before any lookup.** For every visible row not being redrawn and not a skipped blank row, read each of the 45 names from `sh_s1`, and for names other than `CLEAR_NAME` set that slot's stamp to the current one (slot = character number minus `CELL_S1 >> 5`). No hash, no pack access.
5. **Slave, redraw the widened rows** with the existing code: `home_row_blank`, `home_row_map` (memo), the cell loop.

**Exactness argument.**
- A clean row's output is a function of its words, its column map, the position, the menu flags and the bank mapping. Its words are unchanged (step 1, exact compare). Its map is unchanged because no row of its old or new block changed (step 3). `sat_gfx_bank` is a fixed formula, so the palette part of a name cannot move. So the name table entries of a clean row are already what a full redraw would write.
- Its slots still hold its tiles: scroll-1 slots are only reassigned inside `cache_find` on `s1_cache`, which is only called from `home_row_blank` and the cell loop, and step 4 stamps every clean row's slots before either runs. `cache_find` never takes a slot with the current stamp.
- Redrawn rows run unchanged code.
- **Limit:** VDP2 VRAM is not byte-identical to the plain build when a miss occurs. The plain build may evict a tile that a later row needs and upload it again into another slot; this one cannot. The displayed pixels are the same. `tests/host_gfx_s1_identity.sh` must therefore compare the resolved layer (each name followed to its 8x8 cell and bank) instead of the VRAM hash, or it will report a false difference. BLANKROWS hit the same class of problem and solved it by not probing; that route is not open here.
- Add a `SAT_PERF_STAGES` verify counter as for the memo: on a debugger switch, run the full path into a scratch comparison and count rows whose names differ.

**Cost.** Per HUD change in play: the top HUD block (rows 0 to 4) or the bottom one, so about 5 rows through the blank pass, memo and cell loop instead of 10, plus about 450 shadow reads for the re-stamp. Estimated 0.3 to 0.6 K ticks against 2 to 3 K. Memory: about 300 B hot code, 8 B in the snapshot (low RAM; the structure must stay a multiple of 16, so check `lw_free`, which is 84 to 100).

**If the block is still too dear:** keep the 29 blank masks (232 B) and each row's four dropped columns (116 B) between draws. Then only the changed rows go through the blank pass and the cell loop, and a clean row is redrawn only if its dropped columns come out different. The masks stay valid while no lookup was refused. This is the second step, not the first: it adds 350 B and one more invariant.

**Not recommended:** `SAT_S1_EVERY`, or any deferral of the whole layer. The changes are sparse, and each one costs a skip whenever it is finally drawn; the lane measured no gain.

## 3. Sprite build on heavy stages

- **Where the cliff is (EMULATOR):** the FPS-compare lane measured 4.40 ticks a command plus 332 (stage 02, profile build). Stage 24's 1.5 to 2.1 K is then about 270 to 400 commands. The vanish lane's peak of 618 commands in a stage 02 fight is about 3,050 ticks of build, which leaves about 400 for everything else. On Yaba's model busy fights dip below 60 whatever scroll 1 does.
- **Pairing and slot hints:** both measured slower on Yaba (new pictures 77.5 % to 71.5 % and 68.8 %). Pairing does remove 28 % of commands, so its value depends on the console's VDP1 command overhead. Keep both off until the console says.
- **Command reuse between frames:** weak as designed. The two alternating command tables mean a reused command must sit at the same offset two builds back, and every tile still has to be looked up to re-stamp its texture slot, which is the larger share of the build (54 % in the lane's ablation). The earlier command shadow made Yaba slower. Park it unless the console shows VDP1 VRAM writes dominating.
- **One exact micro-candidate:** blank tiles inside an object's grid walk the hash chain and then probe `blank_seen` every frame. Probing `blank_seen` first is equivalent (a key is recorded there only after a hash miss against the current pack, and the table is cleared on a pack swap) and saves the walk for blanks, at the price of one low-RAM read on every hit. It pays only if blanks are a large share: read `sat_gfx_census.empty` against `tiles` on stage 24 before trying it.
- **Cart and low RAM on the console:** the drawing code is already in high RAM. What the slave reads from slower memory every frame is the snapshot, the name shadows, `blank_seen` and `pack_index` (all low RAM) and, on a miss, the pack keys and tile data (cart). I do not have a trustworthy figure for the console's cart or low-RAM access cost against high RAM, and Yaba does not model it. This is a console reading, not something to design around now. The master side matters more here: lifted game code placed in the cart by heat is where a cart penalty would show, as GAME below 60.

## 4. The stage's first frame

- **Known:** 35.3 to 42.9 K ticks once per stage entry, 31.8 K of it in `home_maps_rows` on the first scroll-1 draw, with the game not yet in play.
- **Hypothesis to test:** 31.8 K over 1,392 cells is about 23 ticks a cell, which is far more than a hash miss plus a short binary search. When no slot is free, `cache_find` scans the whole slot array (768 for scroll 1) and returns `NOSLOT` without recording anything, so every later refused cell scans it again. A first picture with more distinct scroll-1 tiles than the cache holds would cost exactly this.
- **Check with existing counters:** on the h3V stage-entry capture, read `sat_gfx_stats.refused_layer` and `sat_gfx_pf[4]` (scan iterations) for that draw. If `pf[4]` is in the hundreds of thousands, the hypothesis holds.
- **Fix if it holds, `SAT_CACHE_FULLSTAMP`:** when the scan finds nothing, store the current stamp in the cache; a later miss in the same draw with that stamp returns `NOSLOT` at once. Nothing can become free inside one draw, so the result is identical. About 20 B.
- **If it does not hold:** the cost is cold pack lookups, and the honest options are to leave it (it is inside a load) or to spread the first scroll-1 draw over several pictures, which shows a partly drawn HUD. I would leave it until the console shows how long it really is: the readout's peak (section 6) gives that in one stage entry.
- **Prewarming in the load window** does not remove work; it only moves it earlier inside the same frozen moment, and it needs the first picture's scroll-1 contents before the game has written them. Not recommended.

## 5. Co-op and bosses

- **Prediction (EMULATOR model):** each extra command is 4.4 ticks. A second player body of 20 to 40 tiles adds about 90 to 180 ticks; a boss of 60 to 120 tiles adds about 260 to 530; a second HUD block makes more scroll-1 rows non-blank, which item 1 mostly neutralises. Stages already near a field on sprites (24, stage 02 fights) will lose pictures in co-op on this model.
- **Second-pad harness:** `pad.c` already has `sat_pad_raw2` and a scripted first pad (`SAT_INPUT_SCRIPT`). Add `SAT_INPUT_SCRIPT2`, test builds only: the same schedule for pad 2, offset by a fixed number of vblanks, with its own coin and start. It needs no emulator support, takes no focus, is deterministic, and the same disc gives a repeatable co-op load on the console with one person. Label it scripted, never interactive proof.
- **Bosses and the Berserker:** `play_full_bot.py` and the stage select reach them; run the same idle, walk and attack scenes and report commands per plot alongside pictures per second, so results can be compared across stages by load.

## 6. What only the console can tell us

Readings on the rebuilt A and B discs (boot fixes in), 20 s each, same spot, video of the readout: stage 02 fight, 0e idle/walk/attack, 1e, 24, one boss, the Berserker, one stage entry. Note the typical and the lowest PIC, and GAME, MISS, SKIP, HELD.

| Reading | Meaning | What it selects |
|---|---|---|
| GAME under 60 or MISS over 0 | the master is short | game code and data placement (cart, low RAM); no slave change helps |
| HELD over 0 | VDP1 has not finished the plot | hardware erase and pairing A/B discs; the full-screen clear polygon and scaled tiles are the suspects |
| SKIP over 0, HELD 0, GAME 60 | the slave is short | A against B gives scroll 1's share on the console; what remains in B is item 1, then sprites |
| PIC under 60 with SKIP 0 and HELD 0 | plot started too late for the swap | frame-change timing, the open question from the vanish lane |

The readout lacks a time. Add one row, `DRAW n PEAK n`: the largest `gfx_ticks` in the last second and since the stage began (a compare and store on the hot side, formatting in the cart). One tick is 4.76 microseconds and a field is about 3,503 ticks on the console (hwtest note). That row gives the first-frame cost, the draw's margin to a field, and, with commands per plot from a `SAT_PERF_HUD` disc, the console's ticks per command, which is the number section 3 waits on.

## 7. Memory plan

| Item | High RAM | Low RAM | Cart tail |
|---|---|---|---|
| B today (FONT_COLD, MEMO, BLANKROWS, readout) | 1,448 free | 84 free | about 330 B under a step |
| 1 `SAT_S1_DIRTY` | about -300 | -8 to -16 | 0 |
| 2 `SAT_CACHE_FULLSTAMP` | about -24 | 0 | 0 |
| 3 Readout peak row | about -12 | 0 | about -150 |
| After 1 to 3 | about 1,100 free | about 70 free | about 180 B under a step |
| Second step of 1 (stored masks and drops) | about -500 more | 0 | 0 |

- Everything recommended fits without moving anything cold.
- The cart tail is the tight one: item 3 uses half of the 330 B. Nothing else here should add cart bytes; a crossed step costs 32 tiles a stage and more dropped keys on 0e.
- The readout is a test-disc feature. On an owner disc without it, the tail is about 1.4 KB lighter and high RAM 216 B better.
- If more high RAM is needed later, the next cold candidates are the remaining `HOME_OS` menu writers in `sat_gfx.c` (`draw_home`, `home_cell`), which run only in menus. Moving them costs cart tail, so check the step first.

## Order of work

1. Stage-24 split and the two first-frame counters (measurement only, existing builds).
2. `SAT_S1_DIRTY` with the resolved-layer host test and the verify counter; A/B on 0e, 1e, 24.
3. `SAT_CACHE_FULLSTAMP` if the counters say so.
4. Readout peak row and `SAT_INPUT_SCRIPT2`; rebuild the A/B discs with the boot fixes.
5. Console readings; only then decide on pairing, hardware erase, scroll 2 and any sprite-build change.
