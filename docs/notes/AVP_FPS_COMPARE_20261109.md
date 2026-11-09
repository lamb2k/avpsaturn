# FPS experiments on the Wolverine v4.1 build, 2026-11-09 (EMULATOR Yaba VideoCore 1, stepped; MODELLED; hardware UNRUN)

Branch `lane/fps-compare-20261109`: Wolverine v4.1 (a83ba1a) + codex/avp-wolverine-fps-next-20261109 (c4489a4, experiments default off)
+ the draw_home menu-copy wait from b0b5929 (3e62e47), + `SAT_VDP1_PROFILE_HWRAM` (1665742). Evidence: `E:\AvP\learning\lane-fps-compare`.

## Release-like build (recipe of the Wolverine disc: -DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1, assets v41/D)
- All off: rc 0, hw_free 4,624, lw_free 104. Stage fit (tools/wolverine/fit.py): 76 of 76 files, gate True, 0 Wolverine-own tiles dropped, 0 missing guest keys.
- Each experiment alone links: reuse 4,112; hints(512) 3,248; CPU slack profile (depth 4) 3,744; hardware erase 3,580; reserved pairs 16 3,800;
  reuse+stats 4,008; hints+stats 3,152 bytes high free; low free 104 in all.
- Host: 61 tests pass; 30 more need private MAME .deps not in a worktree (load errors, not failures).

## Measurement builds
Profile B (-DSAT_VDP1_PROFILE depth 8), no duel menu, guests on. The rings do not fit low work RAM beside the guest code (1,004 bytes over at depth 8,
260 at depth 2), so `SAT_VDP1_PROFILE_HWRAM` places them in high work RAM. All three arms are built that way; do not compare these numbers with the
frame-chain lane's low-RAM profile numbers. Stage 02 Warrior fight, drive.py + stp3.py from lane-fps, 3 seeds x 400 vblanks (3 a step), one Yaba at a time.

| Arm | New | Held | Skip | Late | Commands/plot | Build ticks (excl. uploads) | Ticks/command |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| off | 77.5% | 14.0% | 0.3% | 8.1% | 352 | 1,881 | 4.40 + 332 |
| SAT_GFX_PAIR_REUSE=1 | 71.5% | 23.0% | 1.6% | 3.9% | 253 | 2,079 | 5.92 + 579 |
| SAT_GFX_SLOT_HINTS=512 | 68.8% | 25.9% | 2.0% | 3.2% | 360 | 2,065 | 5.09 + 236 |

Per-seed new share: off 77.6/75.6/79.3, reuse 74.3/71.8/68.3, hints 72.1/62.6/71.8.

## Reading
- Pairing does cut commands on real game data: 352 -> 253 a plot (28%, close to the 29.3% synthetic corpus). On Yaba's SH-2 model the extra
  lookups and adjacency checks cost more CPU than the commands saved (build +198 ticks a plot), so more pictures miss the frame.
- Yaba's VDP1 time is a flat model (R about 670 ticks whatever the pixel or command count), so the VDP1-side saving of fewer commands cannot show
  here. Whether pairing pays depends on Saturn VDP1 command overhead against SH-2 build cost: a hardware question.
- Slot hints are a pure CPU change and are slower on Yaba (build +184 ticks, same commands). Without a hardware result that says otherwise, park them.
- Baseline note: this all-off build holds 14.0% of pictures, against 0.4% for the frame-chain final (Warrior, no guests, low-RAM rings). The cause is
  not established (guest pass in the snapshot, ring placement, or the v4/v4.1 integration); the held plots are the ones whose command build runs long
  (2,114 against 1,830 ticks).
- Not measured here: hardware erase and the CPU slack recorder need a Saturn (their own notes), reserved pairs is the secondary pairing comparison.
