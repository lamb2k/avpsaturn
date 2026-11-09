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

## Group loop out of the snapshot (lane/fps-group-20261109), in progress, paused 2026-11-09

All EMULATOR (Yaba) / MODELLED; hardware unrun. Paused at the coordinator's request (the owner is playing the integrated disc in Yaba; the CPU is contended). No Yaba runs or builds are active.

### Switch
`SAT_GUEST_GROUPS_EARLY` (default off), `saturn/rt/guests.c` and `saturn/rt/kernel.c`. `=1`: when the game's frame is finished (`f_d86`, right after `game_done`) the master classifies every sprite group once (guest body, guest shot, Wolverine shot or flash). The snapshot consumes that and skips the group loop when no group is special. `=2`: check build; the snapshot still classifies itself and counts groups whose early class differs; per-task counters (see below).
The early result is used only if all of these hold, else the snapshot classifies as before:
- vblank stamp: made in the frame this vblank ends (the vblank count rises before the snapshot runs);
- group-write sequence unchanged (`sat_guest_group` counts every call);
- `sat_guest_sel` unchanged;
- not invalidated: `sat_guest_groups_task(i)` runs before every game task that runs after `game_done` and clears the result unless task i is in the mask `SAT_GUEST_GROUPS_TASKS` (default 0: every task invalidates). The flag is cleared at the start of the early run and set last behind a barrier, so a vblank inside the run falls back.
State lives in high work RAM (`.data`): every `.bss` goes to low work RAM, which has about 100 bytes free (the first link failed by 124 bytes). Counters exist only in profile (`SAT_GUEST_PROF`), check (`=2`) and host (`SAT_GUEST_GSTAT`) builds.

### Host equivalence test
`tests/test_guest_groups_early.py` with `tests/guest_groups_early_test.c`: 1,500 random scenarios (random players, shots, flashes, groups, lists, palettes, `sat_guest_sel` 0 to 3, a stand-in Mega Man), real `guests.c` and `wolverine.c`. List, count and palette dumps are byte-identical for `=0`, `=1`, `=2`, including stale cases: no early run (frame overran), state changed after a non-listed task, a group written after the early run, the setting changed, the vblank stamp off in either direction, and a listed task (stays valid). Last run: early result used in 558 snapshots, own classification 801, 164 snapshots with a special group, 0 groups differing between the early and the snapshot classification. Removing any of the three stamp checks makes the test fail. Not covered by the test by design: a game task that changes actor state after `game_done` without calling `sat_guest_groups_task` (it is called by the dispatcher for every task).

### Yaba, 3 seeds x 400 vblanks (profile build, owner recipe flags + SAT_WV_JUMP=1, D11; valid timing runs, taken before the CPU contention)
| Arm | New % | Held % | Held per seed | Late % | Snapshot ticks | Build ticks |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| BASE (switch off) | 81.9 | 2.2 | 3.2/2.7/0.7 | 15.9 | 489 | 1767 |
| E1 (`=1`, strict guard, no task listed) | 83.5 | 2.2 | 3.2/3.2/0.2 | 14.2 | 503 | 1847 |

E1 used the early result in **0 of 1,000 snapshots**: the dispatcher keeps walking the task list after `game_done` (per frame about 60 idle calls and 63 task runs, from `sat_dbg`), so some task always runs after the early pass and clears it. Done alone, the early run costs 91 ticks (1,191 runs, one a frame) and lands in the wait for the vblank: game-done mean 2,525 (BASE) and 2,710 (E1; includes the snapshot and the IRQ body), game overruns 5 in 1,188 vblanks for both, and 1 of 399 samples would pass one field (3,495) once the early cost is added. So the strict form moves nothing and the snapshot block is not smaller (E1 503 vs 489, noise).
Builds: BASE hw_free 7,752 / lw_free 24 (profile), E1 7,744 / 24, E2 7,736 / 24. Each differing build is a full pack rebuild (about 28 min), not the 35 s kept-round-files case.

### E2 run (check build, every post-done task allowed): invalid for timing, but its logic counters are readable
The E2 run (3 seeds, `EARLY_WL=0xffff`: every task allowed, so the early result is never invalidated by a task and the counters see every post-done run) was stopped after seed 1 (seed 2 was in progress) at the coordinator's request, with other Yabas competing for the CPU. **Its timing is invalid and is not used.** The counters are logic counts of the emulated game, not timings, so seed 1's are recorded; they come from one seed and one contended run, read them as indicative:
- post-done task runs by task index (window of 400 vblanks): task 6 7,203 runs (about 18 a frame), task 3 8, task 4 8; no other task runs after the frame is finished;
- runs after which the classification or the group-write sequence differed from the early result: task 6 133 of 7,203 (1.8%), task 4 8 of 8, task 3 0 of 8.
- check build, same run (snapshot side): 334 snapshots, early result valid by stamp in 325, own classification in 9, **0 groups with a different class**, but 0 snapshots with a special group (no Wolverine shot or flash in that window), so the zero says only that the plain classification (all groups class 0) did not change after the frame was finished; it does not exercise the special classes. The host test does.
So the post-done walk is mostly one polling-like task (6) that nonetheless changes the inputs about once in fifty runs, and tasks 3 and 4 run once a second or so. The counter joins two things (the sequence moving because a group was written, and the classification changing with no group written); the sequence part is already caught by the stamp, only the second needs a task guard. The run cannot say which it was, so the safe conclusion for now is that task 6 cannot simply be listed (it would have returned a stale result in up to 133 of the cases the stamp does not cover, if those were state changes). Next (when resumed): split the counter in two (sequence moved / classification changed with the sequence unchanged), rerun E2 one seed at a time on an idle CPU, and if task 6 only ever moves the sequence, list task 6 (and 3 if it stays at 0) in `SAT_GUEST_GROUPS_TASKS`; if it changes the classification itself, recompute the early result at the end of each post-done walk instead, which costs 91 ticks a walk and so only pays if the walk count is small (here about 60 a frame, so it does not), or drop the idea.
A list of tasks justified by measurement is empirical; a stronger guarantee needs the lifted task code read for writes to the player blocks, shot and flash actors.
The recommendation for the owner recipe stays "do not turn it on" until a listed-task build shows a snapshot gain and 0 differences.

## Next steps (not done)
1. Group loop (about 44 ticks a snapshot): precompute during the game frame, or skip the loop when Mega Man is off and no Wolverine shot or flash group exists (needs its own equivalence check). Then a true fold into the kernel copy (30 to 40 ticks at most).
2. Natural fade, continue screen, stage-end transition and Mega Man data are not covered by the look check; run them when a play-through lane has a state near each.
3. These are Yaba numbers; real Saturn cart-RAM code speed is not modelled. Hardware unrun.

## Tooling kept
`profarms.sh`, `bld.sh`, `run.ps1`, `queue.ps1`, `tab.sh`, `table.py`, `an\` in the evidence folder. Two temporary measurement trees (HWRAM macro on a83ba1a and c4489a4; the draw_home revert) are saved as `wt_a83.patch`, `wt_c44.patch`, `wt_dh.patch` there. Intermediate discs and workdirs were deleted.
