# Question for the super agent: how do we close the last performance gap to a steady 60 pictures/s?

## Where things stand (emulated, Yaba with SH-2 cache ON; no hardware numbers yet)
- **Port:** Capcom's AvP CPS2 lifted to the Saturn. The master SH-2 runs the game (60/s, 0 overruns). The slave SH-2 builds the picture: VDP1 sprites plus the VDP2 scroll layers.
- **Bottleneck found and mostly fixed:** a changed HUD word redraws the whole scroll-1 text layer. `draw_scroll1` cost 9.2K of a 10-11K-tick draw; the field is about 3,495 ticks.
- **Exact fixes, all switches, verified identical over 600 host frames plus in-emulator counters:**
  - `SAT_S1_MEMO` (424 B high RAM);
  - `SAT_S1_BLANKROWS` (~300 B);
  - `SAT_HOME_FONT_COLD` (frees 1,920 B).
- **Pictures/s with all three (idle / walk / attack):**
  - 0e: 58.8 / 57.9 / 57.5 (skipped 2-3.5%);
  - 1e: 60 / 60 / 60;
  - 24: 56.7 / 57.5 / 58.3 (sprite build alone is 1.5-2.1K ticks there).
- **Heaviest picture:**
  - 0e: 5.0K ticks (was 11.4K);
  - 24: about 6.7K.
- **Not built:** a dirty-row text redraw. The lane found that skipping rows without re-stamping their tile slots could evict a displayed tile.
- **Unmeasured:**
  - co-op (no two-pad harness);
  - bosses, the Berserker, busy two-player fights;
  - the first frame of a stage (a 42.9K-tick one-off of cold cart-resident pack lookups);
  - real hardware, where VDP1 draw time, cart/low-RAM cost and clock mode decide.
- **Memory:** about 1,448 B high RAM free with all three fixes plus the readout. The cart tail is about 330 B under a 4 KB step (each step costs 32 tiles per stage).

## Sources
- Notes:
  - lane/perf-reconcile-20261110 `docs/notes/AVP_PERF_RECONCILE_20261110.md`;
  - `E:\AvP\learning\lane-perf\REVIEW_ANSWER_60FPS.md`;
  - AVP_STAGE_SPRITES section 9;
  - AVP_FPS_*.
- Logs: `E:\AvP\learning\lane-perf\runs\*\log.json`, `verify\`, `peak\`; tools in `tools/perf`.
- Code: `saturn/gfx/sat_gfx.c` (draw_scroll1, home_row_map, home_maps_rows, the plot), `saturn/rt/kernel.c`, `sat_rt.h`.
- Repo: E:\AvP\worktrees\integration (avp/integration d0540c8). The A/B recipes are in `E:\AvP\learning\integration\run3ab2.sh`.
- Hardware boot fixes, needed for any console disc: lane/hwboot-20261110 d2b12d8.

## Question
What concrete changes get every scene to a steady 60 new pictures per second on a real Saturn, ranked by expected whole-frame gain per byte and per risk?

## Cover
1. **What still costs time in the worst remaining pictures** (0e attack, 24): the per-stage breakdown from the logs, separating scroll layers, sprite build, VDP1 plot wait and tile uploads.
2. **A safe dirty-row or incremental scroll-1 redraw** that keeps tile-slot residency correct (re-stamp, pin, or a generation counter). Give the cost and an exactness argument.
3. **The sprite build on heavy stages:**
   - incremental or cached VDP1 command lists;
   - batching;
   - command reuse between frames;
   - moving hot code from cart to work RAM (Yaba recompiles cart code, but what does hardware pay for cart reads?).
4. **The stage's first frame:** prewarm caches during the load window.
5. **Co-op and bosses:** predict the cost and say how to measure it, e.g. a second-pad harness design.
6. **What only the console can tell us,** and the exact readings to take with the SAT_FPS_HUD readout on the A/B discs, once rebuilt with the boot fixes.
7. **Memory plan:** which fixes fit in the remaining high RAM and cart margin, and what to move cold to make room.

## Constraints
- Workspace optimisation rule: measure first; prefer removing repeated work, data layout, batching and offline conversion over new assembly; label emulated vs console figures; instruction counts aren't timing.
- Every fix is a default-off switch with an exactness or look check.
- Read-only for you: no builds or pushes, no SD card, no focus-stealing (SW_SHOWNOACTIVATE, PostMessage only), no ROM data off the PC.

Write the answer to `E:\AvP\learning\lane-perf\SUPER_ANSWER_PERF_GAP.md`.
