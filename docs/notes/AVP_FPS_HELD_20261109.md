# Why the Wolverine v4.1 build holds 14% of pictures, 2026-11-09 (EMULATOR Yaba VideoCore 1, stepped; MODELLED; hardware UNRUN)

Lane `lane/fps-held-20261109`, off `lane/fps-compare-20261109` (1531ffd). Evidence: `E:\AvP\learning\lane-fps-held` (logs, per-run `H_<arm>_s<seed>` dirs, `arms_table.md`).
Harness as the compare lane: profile B depth 8, Stage 02 fight driven by drive.py + stp3.py, 3 seeds x 400 vblanks (3 a step), my own Yaba copy on MCP port 9711,
one run at a time. Another lane's Yaba ran at the same time; Yaba is stepped, so emulated ticks should not move. All times are FRT ticks (1 tick = 4.77 us, a field is 3,496).

## Answer
The extra held pictures come from the **Wolverine pass in the master's frame snapshot** (`sat_guest_objects`), not from the profile rings, the v4/v4.1 integration,
the c4489a4 merge or the draw_home wait. In the bot's Stage 02 fight P1 is Schaefer's slot, so with Wolverine on (SAT_GUEST_DEFAULT=1) **the "Warrior" in the compare
runs is Wolverine on screen** (objects per plot 88 against 59). The pass removes Schaefer's sprites, shifts the 8-byte object list by his ~29 tiles, writes the tiles and
two palette rows, and the palette sum flip makes the next snapshot recopy page 0. On Yaba that is **+300 ticks (1.4 ms) on the master snapshot (644 vs 340)**.
The slave's command build starts after the snapshot, so a plot whose build is long (2,100+ ticks) is submitted too late and shown a field later:
held 11-16% instead of 0.7%. The command build itself is not slower (1,715-1,835 vs 1,767).

## Arms (single change each; held per seed is seed 1/2/3; commands, snapshot and build are pooled means per plot)
| Arm | What | New % | Held % | Skip % | Late % | Held per seed | Commands | Snapshot | Build (excl uploads) |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| B0 | all-off profile build as the compare lane (head, guests on, rings in high RAM), rerun today | 79.6 | 11.4 | 0.2 | 8.8 | 6.5/16.0/11.7 | 338 | 644 | 1835 |
| FC | frame-chain final as built by lane-fps (wFinB, no guests, low-RAM rings), rerun in today's harness | 89.4 | 0.6 | 0.0 | 10.1 | 0.2/0.7/0.7 | 346 | 337 | 1767 |
| G0 | head, guests built in, Wolverine OFF (SAT_GUEST_DEFAULT=0), rings in high RAM | 89.9 | 0.7 | 0.0 | 9.5 | 1.2/0.2/0.5 | 355 | 340 | 1715 |
| W83 | a83ba1a (v4.1, older frame chain) + HWRAM patch, guests on | 80.4 | 9.4 | 0.2 | 10.1 | 9.0/13.2/6.0 | 337 | 639 | 1812 |
| DH | head with 3e62e47's draw_home wait reverted, guests on | 76.3 | 13.9 | 0.3 | 9.5 | 17.5/14.2/10.0 | 352 | 643 | 1878 |
| N2 | guests on, name-byte check never run (NAMES_LAZY=2) | 79.0 | 10.8 | 0.1 | 10.1 | 16.2/5.5/10.7 | 344 | 631 | 1840 |
| N1 | guests on, name check only after a stage load (NAMES_LAZY=1) | 77.1 | 13.5 | 0.1 | 9.3 | 16.5/11.7/12.5 | 363 | 626 | 1930 |
| GP2 | guests on + pass tick probe (SAT_GUEST_PROF) | 77.7 | 11.4 | 0.4 | 10.5 | 16.5/8.2/9.5 | 350 | 645 | 1878 |
| GW | guests on + per-phase probe (reference for GWF) | 78.3 | 14.5 | 0.1 | 7.1 | 14.5/17.7/11.2 | 343 | 652 | 1844 |
| GWF | GW + word-wide list moves (SAT_GUEST_FAST_LIST=1) | 83.8 | 3.6 | 0.0 | 12.6 | 2.5/5.7/2.5 | 356 | 560 | 1768 |
| F1P | earlier probe build of the same FAST_LIST change | 82.1 | 6.5 | 0.1 | 11.3 | 8.2/6.5/4.7 | 356 | 552 | 1770 |
| F2 | FAST_LIST + NAMES_LAZY=1 + 32-bit object reads | 83.2 | 3.2 | 0.1 | 13.5 | 5.2/1.7/2.7 | 357 | 551 | 1772 |
| F3 | F2 + SAT_GUEST_PAL_KEEP=1 | 85.5 | 2.3 | 0.0 | 12.1 | 4.0/1.2/1.7 | 375 | 473 | 1867 |

All arms: 3 seeds, 1,203 vblanks. Yesterday's compare run of the same B0 build: held 14.2/16.5/11.5 (14.0% pooled). Seed 1 differs by 8 points between days (the drive-in
vblank depends on wall clock), so read held to about +/-5 points and trust the snapshot ticks, which repeat on every guest-on arm (644, 645, 643, 639, 652).
Late rises as held falls (pictures move from a missed field to a slipped slave cadence), so New % is the better single figure (79.6 -> 85.5).
Per-seed new/held/skip/late for every arm: `arms_table.md` and `tab.sh` output in the evidence folder.

## Bisection
- (b) profile rings in high RAM vs low RAM: not a cause. G0 (rings in high RAM, guests built in) is 0.7% held, snapshot 340, same as FC (low-RAM rings, no guests).
- (c) v4/v4.1 integration and the c4489a4 merge: not a cause. G0 is the full head code with the guest setting off and is clean. W83 (v4.1 before c4489a4) shows the same fault (9.4%, snapshot 639).
- (d) 3e62e47 draw_home wait: not a cause. DH (reverted) is as bad as B0 (13.9%, snapshot 643). draw_home only runs on the menus.
- (a) guest pass: the cause. Setting off 0.7%; setting on 9-14% and +300 snapshot ticks, on both the v4.1 and the head code.
- Not the name-byte check: N2/N1 do not move the snapshot (631/626 vs 644). The check costs about 15 ticks a snapshot (probe).
- Not run: c4489a4 alone and no-guest (-DSAT_GUESTS absent) builds. The no-guest build forces a full pack rebuild (28-55 min; I stopped it), and G0/W83 already separate the causes.

## Where the 300 ticks go (probe sums over snapshots that drew Wolverine, ticks per call)
| Part | v4.1 byte loops (GW) | word moves (GWF) |
| --- | ---: | ---: |
| name check (30 cart RAM bytes) | 15 | 15 |
| setup | 1.5 | 1.5 |
| remove Schaefer's sprites (60 entries) | 33 | 31 |
| shift the list by his tiles (byte loop over ~480 bytes) | 83 | 20 |
| write his ~29 tiles | 56 | 40 |
| two palette rows | 17 | 11 |
| whole `sat_guest_objects` call (incl. the guests.c group loop, ~46) | 251 | 163 |
| palette sum / page-0 recopy / object copy before the pass, same snapshot | 404 | 402 |

A snapshot without Wolverine on screen is about 335 in total, so the pre-pass part is ~70 ticks higher when he is drawn: the sum flip makes page 0 recopy every frame.
F3 removes that (pre-pass 322) and the row rewrite, giving a snapshot of 473 (+135 over no Wolverine, from +300). The guest code runs from cart RAM (cold code), so
instruction counts are not the model: only the probe ticks and the snapshot ticks are evidence.

## Fixes (all default-off switches, committed on this branch)
- `SAT_GUEST_FAST_LIST=1` (wolverine.c): 32-bit moves for the list compaction and shift, 32-bit stores for tile and palette words, 32-bit reads on the big-endian target. Held 14.5 -> 3.6 (GW -> GWF), snapshot 652 -> 560.
- `SAT_GUEST_NAMES_LAZY=1` (wolverine.c): the 30-byte cart RAM compare runs only after a stage load (`sat_rounds.loads` moved). About 15 ticks a snapshot. `=2` never checks (measurement only).
- `SAT_GUEST_PAL_KEEP=1` (sat_gfx.c, wolverine.c): once Wolverine's rows are in page 0 and the game's page sum is unchanged, the snapshot does not recopy the page, the guest does not rewrite its rows and the sum is not flipped (so the slave's palette scan sees no change). Off when Mega Man is selected. Costs 148 bytes of high work RAM in the profile build (hw_free 8,028 -> 7,880; check the release link, which has 4,624 free). It still needs a still-pair look check of the colours: not done here.
- `SAT_GUEST_PROF`: probe counters `sat_gprof`, `sat_gprof_w` (measurement builds only).
- Best arm F3: New 85.5% (from 79.6), held 2.3% (from 11.4), snapshot 473 (from 644). Not yet at the frame-chain level (89.4 / 0.6 / 337): Wolverine still costs ~135 snapshot ticks and his extra objects add commands (375 vs 346).
- With all switches off the profile build matches the compare lane's p_off: hw_free 8,220, lw_free 88, loaded code identical (3 bytes differ in the ELF tail).

## Follow-up 2026-11-09 (second pass): release build, look check, fold

All EMULATOR (Yaba) / MODELLED, hardware unrun. Same harness, own Yaba on port 9711, windows titled "AvP FPS-HELD: ...". The machine was heavily loaded by other lanes, so runs were slow; emulated ticks are not affected.

### 1. Release recipe build (no profiling)
`-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1`, assets v41/D, workdir copy of the compare lane's w_off (KEEP_ROUND_FILES):
- rc 0. Before the PAL_KEEP page-0 fix: hw_free 4,468, lw_free 104. With the fix (final source): **hw_free 4,476, lw_free 104**. All switches off: 4,624 / 104, so the three switches cost 148 bytes of high work RAM.
- `tools/wolverine/fit.py` on that workdir with a copy of assets v41/D: **76 of 76 files, gate True, fail [], rc 0**. The fit looks at the pack layout, which the kernel switches do not change; the figures match the compare lane's all-off fit_off.log.

### 2. PAL_KEEP look check, and the page-0-only fix
The hardware-test lane (lane/hwtest-20261109, fef8eb0) found that `pal0_same`, once set for page 0, also froze pages 1 and up (the scroll-1 palette: fades, the continue screen) while Wolverine's rows were kept. Applied by hand: `pal0_same` is set only on page 0 and the skip test is `!(page == 0 && pal0_same) && sum != snap.pal_sum[page]`. Figures measured before the fix are marked "pre-fix".

Method. A pixel diff of whole pictures is not usable: the two modes change the snapshot timing, the game then runs a few frames apart and the shown picture lags by a plot, so differing pictures show timing, not colour. The check is exact and inside the build instead: a look-check build (`SAT_GUEST_PAL_KEEP=2`, release recipe + FAST_LIST + NAMES_LAZY; debug byte `sat_guest_pal_keep_off`, counters `sat_look_rows`, `sat_look_pg`, pointers `sat_look`). One Yaba session drives into the Stage 02 fight, saves a state, then replays the same pad script (130 steps of 3 vblanks) from that state with keep ON, with keep OFF (debug byte set: the v4.1 flip and recopy path) and with `sat_guest_sel` = 3 (the Mega Man bit, which switches keep off). In every snapshot the snapshot's page 0 is compared with the game's page 0 right after the guest pass, and at every pause the snapshot pages are read back and compared with the game's.
- Wolverine fighting (pre-fix; 331 / 319 / 315 snapshots ON / OFF / sel3): the snapshot page differs from the game page only in rows 1 and 21 (Wolverine's two rows) and in row 20 pen 15 (a clear pen that update_palette skips; identical in OFF and sel3, so not caused by the keep). No other row ever differs, in any mode. His rows are byte-identical to the constant table.
- Game-side palette changes (stand-in for a hit flash or explosion): 26 pokes into rows 5 and 7 of page 0 during the fight, which must force the recopy while the rows are kept. ON: 0 of 26 stale at the pause after the poke (OFF 1 of 26). The per-snapshot counter shows 21 (ON), 23 (OFF) and 20 (sel3) transient mismatches in the snapshot a poke lands in (the pause falls inside a snapshot): the same in all three modes. Natural hit flashes and explosions did not occur in the window.
- Fade on page 1 (post-fix build): row 4 of page 1 rewritten every step for 130 steps (a fade ramp). The snapshot's page 1 followed the game's: **0 of 130 steps stale at the pause with keep ON** (OFF 1 of 130, sel3 0 of 130). The per-snapshot counter, transients as above, was 74 ON, 59 OFF, 61 sel3. A natural stage-start fade is in the drive-in (vblank about 700 to 1,000), but Wolverine's rows are not kept there, so only the poked fade exercises the fixed path. The continue screen and the stage-end fade were not reached in the window; they use the same pages-1-and-up path, which now always follows the game.
- Mega Man: v41/D has no Mega Man data, so only the guard was checked: with `sat_guest_sel` = 3 the snapshot behaves like OFF (same rows, same page-1 result). The Mega Man palette path itself is unchecked.
- Stage transitions were not reached. The stills were not kept (the comparison needed none; `an\look.py` reproduces them; game images stay on this PC).

### 3. Fold of the pass (`SAT_GUEST_FOLD=1`, default off): no gain
In place: one scan counts Schaefer's sprites (r), one backward pass moves every kept entry straight behind his n tiles, falling back to the two-pass code when n < r. Host check `tests/test_wolverine_list_identity.py` (400 random lists x 4 builds: default, FAST_LIST, FAST_LIST+FOLD, all switches) gives a byte-identical list and palette; `tests/test_wolverine_runtime.py` still passes. Yaba, 3 seeds x 400 vblanks:

| Arm | New % | Held % | Held per seed | Snapshot | Build | Remove + shift part of the pass, ticks per call |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| F3b (FAST + LAZY + KEEP, pre-fix) | 85.2 | 1.7 | 1.0/3.7/0.5 | 474 | 1863 | 55.7 (37.7 scan, 18 shift) |
| F4 (F3b + FOLD, pre-fix) | 83.4 | 3.3 | 4.5/0.5/5.0 | 474 | 1870 | 56.6 (scan and move) |
| F3c (F3b rebuilt with the page-0 fix) | 86.5 | 2.9 | 1.2/7.2/0.2 | 486 | 1772 | 56 |

The in-place fold costs as much as the compaction and shift it replaces, so it does not pay: **snapshot 474 against 474**. It stays as a switch only because its host identity is tested; keep it off. A fold into the kernel's object copy (the copy loop already writes each entry once) is bounded by the same arithmetic: at most the ~56 ticks of scan and move less the test done in the copy loop, so 30 to 40, and it needs the group pass below to run first on the unshifted list. Not built.
Held moves by up to 7 points between seeds (F3c 0.2 to 7.2), so only the snapshot column separates arms. The post-fix snapshot (486) is 12 ticks above the pre-fix one (474): pages 1 and up compare their sums again, which the freeze had skipped.

### What is left in the pass (probe, ticks per call that drew Wolverine, F3c-style build)
Name check 8 (lazy), remove Schaefer's sprites 38, shift 18, tiles 38, palette 1, the `guests.c` group loop about 44, and 185 for the palette sum and object copy before the pass. An ablation build that skips the group loop (`SAT_GUEST_ABL_NOGROUPS`, measurement only: it also stops suppressing his shots) takes the whole call from 151 to 107. The group loop is the biggest single piece left. Its work could be done as the game calls `sat_guest_group` (once per sprite group, off the snapshot's critical path) with a per-frame "nothing special" flag, but the shot test reads actor state at call time, so equivalence needs its own check. Not done.

### Default-off identity
With every new switch off (and no probe), the profile build of the final source gives hw_free 8,220, lw_free 88 and an ELF the same size as the compare lane's `p_off`, with 3 bytes different (the same 3 as before the follow-up changes): loaded code unchanged.

## Next steps (not done)
1. Group loop (about 44 ticks a snapshot): precompute during the game frame, or skip the loop when Mega Man is off and no Wolverine shot or flash group exists (needs its own equivalence check). Then a true fold into the kernel copy (30 to 40 ticks at most).
2. Natural fade, continue screen, stage-end transition and Mega Man data are not covered by the look check; run them when a play-through lane has a state near each.
3. These are Yaba numbers; real Saturn cart-RAM code speed is not modelled. Hardware unrun.

## Tooling kept
`profarms.sh`, `bld.sh`, `run.ps1`, `queue.ps1`, `tab.sh`, `table.py`, `an\` in the evidence folder. Two temporary measurement trees (HWRAM macro on a83ba1a and c4489a4; the draw_home revert) are saved as `wt_a83.patch`, `wt_c44.patch`, `wt_dh.patch` there. Intermediate discs and workdirs were deleted.
