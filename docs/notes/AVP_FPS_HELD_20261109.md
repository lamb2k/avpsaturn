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

## Next steps (not done)
1. Fold the pass into the object copy: write his tiles first and copy only the kept entries straight from the game list (removes the compaction, the shift and a second copy), or let the slave place his tiles during the command build. This should take most of the remaining ~135 ticks.
2. Run the release recipe (duel menu, no profile) with the three switches: check the link, compare the object list against the byte-loop pass (host test), and take a still pair of the fight palette.
3. These are Yaba numbers; real Saturn cart-RAM code speed is not modelled. Hardware unrun.

## Tooling kept
`profarms.sh`, `bld.sh`, `run.ps1`, `queue.ps1`, `tab.sh`, `table.py`, `an\` in the evidence folder. Two temporary measurement trees (HWRAM macro on a83ba1a and c4489a4; the draw_home revert) are saved as `wt_a83.patch`, `wt_c44.patch`, `wt_dh.patch` there. Intermediate discs and workdirs were deleted.
