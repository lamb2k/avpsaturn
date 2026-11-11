# Performance track: picture rate reconciled, bottleneck found, 2026-11-10

Lane `lane/perf-reconcile-20261110` (off avp/integration 7df02a3, code of disc 3e 45c867c). Evidence tier: EMULATOR (Yaba, emulated ticks) and MODELLED; HARDWARE UNRUN.
Harness `tools/perf/` (run.py, an.py, report.py, pf.py, hud.py), evidence in `E:\AvP\learning\lane-perf\runs\<run>\log.json` (per-vblank counters), `bursts.json`.
Yaba: General\UseSh2Cache=true for every timing figure, Sound\SoundCore=1, Volume 100, VideoCore 1, own copy, port 9732, launched minimised then restored without
activation and sent to the bottom of the z-order (a minimised Yaba stalls its frame pump). Cache OFF is labelled where used.
Tick unit: slave FRT, phi/128; one 60 Hz vblank is about 3,730 ticks at the 28.6 MHz clock (the game runs 352 wide).

## 1. What the counters measure (kernel.c, sat_gfx.c, sat_rt.h)

- `sat_dbg.gfx_ticks`: the slave's FRT from its wake (the timer is reset there) to the return of `sat_gfx_draw`, written once per finished draw. It is wake-to-return time:
  all of the slave's work for one snapshot plus the short waits inside the draw. It does not include the time the slave sleeps waiting for the next snapshot, and it does not include
  VDP1's plot (PTMR starts it, the slave carries on, and only the next draw's `plot_wait_end` would wait for it). Measured waits inside it (stage timers, 3e opening and walk):
  wait for the previous plot 2 to 4 ticks, frame-change latch in `plot_start` about 58, wait for the master's layer half 14 to 200. So a draw's ticks are almost all slave CPU work.
- `sat_gfx_stage[0..5]` (every build): FRT at stages of the draw: 0 start, 5 after `draw_sprites` (the sprite commands are built and the plot is started right after), 1 after
  `plot_start`, 2 before the layer wait, 3 after the three layer passes (= the end of the draw).
- `gfx_skips`: vblanks on which the master found the slave still drawing (`gfx_handed != gfx_done`) and so took no snapshot. That vblank gets no new picture.
- held (`plot_held`, `sat_gfx_plot_waits`): vblanks on which a plot had been started but VDP1 had not set CEF yet, so the frame change was withheld and the last picture stays one more vblank.
- a picture (what reaches the screen) = one VDP1 frame-buffer swap = `plot_shown` incremented in `sat_gfx_vblank` (FBCR = 3). `plot_started` counts PTMR, `gfx_done` counts finished draws.
- `obj_flips`: writes of the object-bank flip word (one per game frame, 60 per second at full speed). `overruns`: vblanks entered with the game frame unfinished.
- "picture finished" in the stage-sprites note (section 9) is not one of these: tm.py counted a frame as a picture only when gfx_ticks changed to a value above 5,000 with pieces drawn, i.e. only draws
  longer than 1.3 vblanks.

## 2. The truth, cache ON

New pictures per second = swaps per 60 vblanks, kernel counters read per single stepped frame; discs 2 (70af5ed), 3a (4c3dc09, ELF rebuilt: HW.BIN and LW.BIN match the ISO), 3e (45c867c).
Scenes after the same stage load plus 300 vblanks: idle, walk right (key held 150 vblanks), attack on the spot; the free run is 20 s of wall time of random input, not matched between discs.
(see the report table; per-run files `report.py`)

Findings:
1. With nothing changing on scroll layer 1, every disc shows 53 to 58 new pictures per second, no held pictures (cache ON), 0 overruns, game 60 frames per second.
2. The draw time is bimodal. 65 to 96 percent of draws take under 1.5 K ticks (0.4 vblank); the rest take 9.5 to 11.5 K ticks (2.6 to 3.1 vblanks). The stage-sprites lane measured only the second kind.
3. Whenever scroll layer 1 (the HUD text layer: score, bars, banners, the GO arrow) changes, the draw takes the long form. While that happens on every picture the slave cycle is about 4 vblanks:
   15 pictures per second (stage 0e, first seconds of the stage on discs 2 and 3a/3e: bursts show 21 to 30 swaps per 64 vblanks). The free-run averages with random input were 20 to 52 swaps per second on 0e and 36 to 49 on 1e.
4. The FPS lanes' held 11.4 percent and 2.9 percent were cache OFF Yaba (lane-fps-held yabause.ini: UseSh2Cache=false) on Stage 02, Wolverine pass. With the cache ON `held` is 0 to 1 percent everywhere. The two earlier readings measured different things and different settings.

## 3. The bottleneck: scroll 1 redraw, `home_maps_rows` and `home_row_map`

SAT_PERF_STAGES markers inside `draw_scroll1` (3e recipe, stage 0e, cache ON, heavy draws only, ticks per draw, median of 16):
sprites built and plot started 0.7 to 2.2 K; layer wait 0.1 K; scroll 2 and 3 0 to 0.9 K; **scroll 1 9.2 K**, of which `home_maps_rows` (the blank mask of 29 rows) 1.5 K, `home_row_map` (the 48 to 44 column fit, 29 rows) 6.2 K, the cell loop 1.4 K.
The column fit (greedy pick of 4 droppable columns, 4 x 48 steps a row) is recomputed for all 29 rows on every scroll 1 change, 19 of them fully blank rows whose answer never changes.
A heavy draw also holds the slave past the next vblank: the next snapshot is skipped for 2 to 3 vblanks, so no new sprite picture is built although the sprites of that draw were plotted in its first 0.7 K ticks.
(The VDP2 scroll registers are written at the end of the draw, so the background also lags the sprites by the length of the draw.)
Not the cause: tile uploads (0 to 50 sprite uploads, 0 to 2 layer uploads in the heavy draws), VDP1 plot time (held 0 percent), snapshot (0.75 to 0.85 K), the game (1.1 to 2.3 K of 3.7 K).

## 4. Fixes (all default off)

| Switch | What | hw RAM | Heavy draw (cache ON) | Exact |
| --- | --- | --- | --- | --- |
| SAT_S1_MEMO | direct mapped memo of `home_map` (key: blank mask, HUD flag; value: the 4 dropped columns), blank-row fast path, story-box weights only for the box | 424 B (8 entries; code 328, table 96) | 9.5 to 11.4 K -> 3.2 to 5.8 K | yes (pure function; debugger verify counters in SAT_PERF_STAGES builds) |
| SAT_S1_EVERY=n | while a stage is played scroll 1 is redrawn at most every n pictures | about 72 B | see report | no: a changed HUD word shows up to n-1 pictures late (33 ms at 2) |

hw_free on 3e is 520: MEMO leaves 96, both leave about 24. The readout below needs 216 B hot (hw_free 304) and does not fit together with MEMO.

## 5. Readout, SAT_FPS_HUD

Default off. Rows 24 and 25 on the menu layer (NBG3) once a second: `PIC n GAME n` (new pictures and game frames in the last second) and `MISS n SKIP n HELD n`.
Code in the cart tail (`saturn/rt/fps_hud.c`, 0.7 KB, cold code), hot side one call a second and two words. Cost on: hw_free 520 -> 304 (216 B: the call site, the priority and layer checks), lw_free unchanged (84),
the cart tail steps by 4 KB (cart_free 4,556 -> 7,496), which costs stage 0e 64 more dropped rare sprite keys (243, against 179 on 3e); every other stage drops 0 as before.
Cost off: none (same objects).

## 6. Review answer checked (REVIEW_ANSWER_60FPS.md), field length, cache OFF

- The review's bottleneck (scroll 1 redraw) matches the stage-timer data above. Field length: draws that finish in 1 field top out at 3,458 ticks and draws that need 2 start at 3,670; draws needing 3 end at 10,603 and 4 start at 10,631
  (3,452 draws, runs d2/a3/e3 0e and 1e, cache ON). With the wake offset s: F - s in [3,458, 3,670] and 3F - s in [10,603, 10,631], so F is 3,470 to 3,590, about 3,495. The 3,728 in the task text is refuted.
- Cache OFF (the owner's normal Yaba play setting; look setting, labelled): the master falls behind too. Stage 0e disc 3e: pictures 46 / 41 / 37 per second (idle / walk / attack), held 0 / 13 / 21 percent, overruns 0 / 25 / 46 per 144 vblanks; free run 18 pictures per second, 244 overruns in 1,196 vblanks.
  Disc 2: 47 / 33 / 31, held 0 / 23 / 21, free run 30 per second. The emulation without cache is about 1.9 times slower per instruction, so a hung master shows there that the cache-ON runs do not show.

## 7. Memo A/B on disc 3g (f36b96b, GUEST_DEFAULT=0, reveal), Yaba cache ON, same scripted scenes

(g3base = avp_integration_3g as packaged; g3M = the same tree with SAT_S1_MEMO; hw_free 496 -> 72, cart_free and sprite store unchanged: stage 0e still drops 179 keys)
Stage 0e, pictures per second (idle / walk right / attack), skipped percent, burst at the stage opening (64 vblank bursts, 3 of them):
- g3base: 52.9 / 54.6 / 55.8; skipped 11.8 / 9.0 / 6.9; opening burst 31.3 swaps; heavy draws 9.5 to 11.4 K ticks
- g3M:   57.5 / 57.5 / 57.5; skipped 4.2 each; opening burst 46.9 swaps; heaviest draw 5.8 K ticks
(more stages and the blank-row and readout discs follow in the report)

## 8. SAT_S1_BLANKROWS and SAT_HOME_FONT_COLD

- SAT_S1_BLANKROWS (exact): rows of scroll 1 whose cells are one word with no tile (19 of 29 in play) are written once per map position and then skipped by the cell loop, the column fit and the lookups.
  Cost measured by compile: +296 bytes of hot code, +8 bytes bss (not the 64 bytes asked: the row test needs the cache lookups, which live in high RAM). The same logic in cart code would be about 40 bytes hot but a cart addition
  over 72 bytes steps the cart tail by 4 KB (3g cart_free 4,168), which takes room from the stage 0e sprite store (64 more dropped keys).
- SAT_HOME_FONT_COLD: moves the menu font cells and text palettes (1,920 bytes of rodata) from high RAM to the cart tail (saturn/rt/home_font_cold.c). That funds MEMO (424), BLANKROWS (about 300), the readout (216) and EVERY (72) together: all four on need about 1,000 bytes, leaving about 1,400 of hw_free on 3g.
  It adds 1.9 KB to the cart tail, so on its own it also steps the tail by 4 KB; on the readout discs the readout has already paid that step.
- SAT_S1_EVERY=2 changed nothing measurable on stage 0e once MEMO is on (m8e2 vs m8: opening burst 47.2 vs 47.8, idle 57.5 vs 56.7); it is not recommended.

## 9. The A/B pair on disc 3h (avp/integration 1583c9f), 2026-11-10 evening

Recipe: the 3h recipe (docs/INTEGRATION.md) plus the switches below. A = `-DSAT_HOME_FONT_COLD -DSAT_FPS_HUD`; B = A + `-DSAT_S1_MEMO -DSAT_S1_BLANKROWS`. Switch names are stable. SAT_S1_EVERY exists and is not recommended (no gain once MEMO is on).
Branch lane/perf-reconcile-20261110 merges onto 1583c9f (one build.py conflict, resolved, keeps the stage-select snap_bytes block).

Memory (build.py report, workdir copies of wd3h):
| Build | hw_free | lw_free | cart_free | stage 0e dropped keys |
| --- | ---: | ---: | ---: | ---: |
| 3h plain | 480 | 84 | 7,496 | 243 |
| 3h + FONT_COLD + MEMO + BLANKROWS | 1,664 | 84 | 5,576 | 243 |
| B (that + readout) | 1,448 | 84 | 4,460 | 243 |
Per switch: FONT_COLD frees 1,920 B hot (adds 1.9 KB cart); MEMO 424 B hot; BLANKROWS about 300 B hot; readout 216 B hot, about 1.4 KB cart. 3h already stepped the cart tail (243 dropped keys); B stays above the 4,096 byte step.

Exactness (all three switches):
- HOST: tests/host_gfx_s1_identity.sh (WSL gcc, WORK/gen for the ROM-derived font): 600 random HUD-like frames (scroll 1 mostly one blank word, rows of tiles that come and go, position that mostly holds, play flag toggling); VDP1 VRAM, VDP2 VRAM, CRAM and register hashes identical to the plain build for MEMO, BLANKROWS, FONT_COLD and all three together. It caught a slot-order difference in the first BLANKROWS (it probed the tile cache); fixed by testing blank_seen only. Menu modes (draw_home) are not host-safe and are covered in the emulator.
- EMULATOR (build h3V = B + SAT_PERF_STAGES verify counters, Yaba cache ON, 40 s random-input play): stage 0e memo hits 693, misses 26, differences 0, blank rows skipped 927, differences 0; stage 1e 329 / 33 / 0 and 972 / 0; stage 24 314 / 37 / 0 and 636 / 0.
  Still pair from one save state, memo off against on, frame 70: 0 differing pixels on 0e and 24; on 1e 201 pixels in the readout's text rows (PIC counts differ between the two runs), none elsewhere.

A/B results (cache ON, same scripted scenes; pictures per second = VDP1 swaps; stepped counters; see the table in the report):
| Stage, scene | 3h plain | B |
| --- | --- | --- |
| 0e idle / walk / attack | 52.9 / 55.8 / 55.4 (skipped 11.8 / 6.9 / 7.6 %) | 58.8 / 57.9 / 57.5 (2.1 / 3.5 / 3.5 %) |
| 0e stage-opening bursts (64 vblanks) | 30.6 swaps | 54.1 swaps |
| 1e idle / walk / attack | 56.7 / 54.2 / 39.2 | 60.0 / 60.0 / 60.0 (0 % skipped) |
| 24 idle / walk / attack | 3g plain 53.3 / 50.0 / 52.5 | 56.7 / 57.5 / 58.3 |
Heaviest slave picture: 0e 11.4 K -> 5.0 K; 1e 17.1 K -> 2.8 K; 24 12.0 K (3g) -> 6.7 K (sprite build alone is 1.5 to 2.1 K there).

## 10. gfx_peak 42,879 on 3h

Yaba cache ON, boot to the title, character select, then entering stage 2: gfx_peak 15.6 K at the title, 17.3 K when the character select opens, 42,879 after the stage is entered (3g: 17.2 K at the same moments, no jump). It is one draw at the start of a stage, set before gameplay; not the stage-select picture and not a per-frame cost.
Caught with the stage timers (h3V, same key sequence, stage 2 start): peak 35,251 on that build; of it 31.8 K ticks (stg[8] to stg[10]) are `home_maps_rows`, the blank-mask pass of the first scroll 1 draw of the stage: every cell of the 29 rows looks its tile up with cold caches (cache_find, then pack_find on the cart, blank_seen empty). It happens once per stage entry, while the stage loads, with the game not yet in play. Not a per-frame cost; a recurring hitch only if a stage change redraws scroll 1 cold (the same pass is what SAT_S1_BLANKROWS and the blank_seen table make cheap on later pictures). On the console the pack lookups on the cart cost more or less than Yaba models: unknown.

A disc (3h + FONT_COLD + readout, no memo or blank rows; h3A), cache ON: 0e idle/walk/attack 52.1 / 52.9 / 52.9 pictures per second (skipped 13.9 / 11.8 / 11.8 %), 1e 56.7 / 55.8 / 55.8, 24 52.9 / 50.4 / 54.2: the same as plain 3h, so the readout and the font move cost nothing measurable; B (above) is the speed-up.
