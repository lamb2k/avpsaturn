# Game speed: the arcade against our port (2026-11-12, lane perf)

Question (owner): on the console the game "feels like full speed", but the readout shows few completed task walks in crowded fights (stage 1: PIC 31-35, DONE 13-15, MISS about 45; light scene PIC 33, DONE 42; fix7n, build F2 1CA3E8). How does game TIME on our port compare to the ARCADE?

Tiers used in every number: **MAME** = MAME 0.289 `avspu` (the arcade program on an emulated 68000, a stock build, scripted walking bot with the player's health held at 0xff83c0). **YMIR** = my own patched copy of strict Ymir (E:\AvP\learning\lane-perf\ymir_gs, JP BIOS, 4 MB cart, SH-2 cache emulated, per-region bus cycles as shipped in Ymir) running the fix7n2 disc (`avp_3h_A_fix7n2`, build id F2 DAD102), stage 1-1 Coffee Shop as Predator Warrior, same kind of bot, health held. **MODELLED** = Ymir with the master SH-2 slowed down (see section 4); not a console measurement. **CONSOLE** = only the owner's photos quoted above. No number here is a console measurement of game speed: nobody has read one yet. That is what the new TICK field is for.

## Answer in five lines

1. The arcade clock is the **gameplay tick**, not the vblank and not the task walk. One tick = one pass of the gameplay loop (task at ff00d8). It adds one to ff8019, runs the player and all actors, and that is what advances animation, movement, hit stop and enemy AI. The vblank interrupt adds one to ff8018 and wakes sleeping tasks (fades, palette steps, route waits); it does not run game logic.
2. **MAME, arcade, busy scenes:** 59.99 ticks per 60 vblanks over 57,715 gameplay frames, and 60.00 with 8 or more enemies on screen (3,792 frames). The arcade does not slow down in these scenes: it catches up. A tick that runs past a vblank is followed at once by the next one (up to 3 in a row), so a late tick costs no game time.
3. **YMIR, our port, stock:** 60.00 ticks per 60 vblanks in the same fight (1,885 vblanks), DONE 60, MISS 0, PIC median 47 (worst windows 30). So in stock Ymir the game runs at full speed and only the pictures drop.
4. **DONE is not game speed.** DONE = 60 minus the vblanks in which one whole pass over all 16 tasks had not finished. The gameplay task is task 4; a cut pass has usually already run the tick. With the catch-up logic DONE falls to 25 while the game still runs at 90 percent, and to 17 at 79 percent. CUT counts tasks a vblank skipped, also not a speed.
5. **Is the console at full speed?** Not established. Stock Ymir cannot reproduce the console's MISS (it says 0, the console says about 45), so Ymir's master is faster than the console's. If I slow the master until Ymir shows the console's crowded-fight numbers, the game runs at about 41 to 48 ticks per 60 (about 70 to 80 percent speed) in that fight. That is MODELLED. The honest status: the owner's "feels like full speed" and this model disagree, and one photo of the new TICK field settles it.

## 1. The arcade's own clock (68K code, MAME)

Source (disassembly, no listing copied here):

| What | Where | Behaviour |
|---|---|---|
| IRQ level 2 | 0xe0e | once per vblank: pushes registers, samples inputs, runs sound and palette steps, `addq.b #1,ff8018` (at 0xe80), `st.b ff0266` (dispatcher flag, 0xe88), `clr.b ff81bc` (0xe8c), then counts down every sleeping task and wakes it at zero |
| Dispatcher | 0xd86 | clears ff0266, walks 16 task records (0xff0058 + 0x20 each, run when state is 4 or more), restarts from task 0 whenever ff0266 is set, calls 0x11ec (idle) after a full pass and starts again |
| Gameplay loop | 0x8062 | task at ff00d8 (index 4). `st.b ff81bc` (0x808a), `addq.b #1,ff8019` (0x8094), latch inputs (0x166ac), route dispatch (0x8164) = the tick, output latch (0x1188), then 0x8140 |
| Catch-up | 0x8140 | if ff81bc is still set (no vblank during the tick): clear the catch-up count, sleep one vblank. If the IRQ cleared it (the tick crossed a vblank): count up and run the next tick now; at 4 in a row sleep anyway |
| Hit stop, animation, enemy motion | inside the tick | per-actor bytes consumed during the 0x8164 pool traversal (see AVP_LEARNING_NOTES.md) |
| Sleeping-task countdowns | IRQ | per vblank, not per tick: fades, palette tasks, route waits run on the video clock |

MAME confirmation (this lane, tools/gamespeed/gs_walk.lua): write-tap census of the writers of the clocks over 3,500 frames: ff8018 is written by 0xe86 (the IRQ) 3,418 times and by 0x809a (the tick) 3,727 times, plus 4 boot clears; ff0266 is written by 0xd8c (the dispatcher's clear) 179,108 times (about 51 walk starts a frame) and by 0xe8e (the IRQ) 3,418 times. Over 60,000 frames the advance of ff8019 equals the count of fetches of 0x808a exactly (62,722), and ff8018 advances once per frame (59,918 for 60,000 frames; the 82 missing are boot frames before the IRQ is enabled).

Game time therefore has two clocks: the tick clock (ff8019, gameplay) and the vblank clock (ff8018, fades, waits, sound). A port that falls behind slows the first and not the second. The readout's TICK is the first, per 60 vblanks.

## 2. MAME: how the arcade behaves in busy scenes (MAME tier)

Walking bot, 60,000 frames from boot (stages 02, 04, 06, 08, 0a, 0c), per-frame counters (E:\AvP\learning\lane-perf\gamespeed\s60k\frames.tsv): ff8018, ff8019, fetches of 0x808a (tick starts), 0xd86, 0x11ec (idle after a full pass), 0xdb8 (task runs), 0x8156 (catch-up taken), 0x814a (sleep), emulated time of each tick (0x808a to 0x8144), object-list entries and distinct enemy actors in it.

Active gameplay = not in a hold (3 or more frames with no tick start: fades, loads, cutscene waits, where the loop is held by design), not in fast-forward (ff81b9, a held button speeds scripted scenes), in a stage: 57,715 frames.

| Measure | Result |
|---|---|
| Ticks per 60 vblanks, all active gameplay | **59.99** (57,706 ticks in 57,715 frames) |
| Frames with 0 tick starts / 2 or more | 9 (0.016 percent) / 0 |
| Same, 8 or more enemies on screen | 60.00 over 3,792 frames, 81 catch-up events |
| Stage 02 alone (frames 1140-3100, up to 10 enemies) | 59.97 (1,840 ticks in 1,841 frames) |
| One tick's CPU time | median 7.0 ms, p90 10.9, p99 14.7; a frame is 16.77 ms |
| Frames holding a tick longer than a frame | 128 of about 58,000, every one absorbed by the catch-up |
| Frames with at least one completed walk (the DONE analogue) | 99.99 percent; median 53 to 71 completed walks a frame (the idle task spins) |

By enemy count (distinct enemy actors in the object list): average tick time grows from 6.4 ms (none) to 9.7 ms (8 or more), p99 per frame 11 ms to 26 ms; the p99 above 16.77 is the catch-up case. The ticks per 60 stay at 60.00 in every bucket (59.97 to 60.00). The arcade's 68000 runs at about 40 to 60 percent load in a crowded fight, with spikes that the catch-up absorbs; its own busy-scene rate is **60 ticks a second, no logic dropped**. (MAME times the 68000 as an approximation; the real board may differ by some percent, and the bot is not a human, so it is an emulator-tier statement.)

## 3. YMIR: same counters on the port (YMIR tier, fix7n2)

Probe: the patched Ymir copy watches the write stream. It keeps a shadow of the lift's counters at their fix7n2 addresses (from `wd_hw/sat.map`: RAMB 0x060DEC14, sat_dbg 0x060DEA64, sat_gfx_stats 0x060FEF84; ff8018 is RAMB+0x8018) and prints one line per vblank (the write of `sat_dbg.vblanks`): the game's IRQ and tick bytes, ticks, task runs, idle calls (completed passes), MISS (`overruns`), SKIP, FLIP, CUT (`tkskip`), pictures, VDP1 command count and `game_ticks` (the FRT at the end of the pass). Checks on the addresses: over 1,946 consecutive vblank lines of run f10 the shadowed ff8018 byte advances exactly as the vblank counter (0 exceptions), the ff8019 byte advances exactly as the number of tick writes (0 of 1,945), the stage word reads 02 in the stage, the picture counter follows PIC on the screen (screenshots runs\*\p*.png), and the log has no gap in the vblank sequence.

Stock run f10 (E:\AvP\learning\lane-perf\ymir_gs\runs\f10), fight = 1,885 vblanks from 300 after the stage word:

| Measure | Result |
|---|---|
| Ticks per 60 vblanks (windows without fast-forward) | **60.00**, every window |
| MISS / DONE | 0 / 60 in every fight window |
| PIC per 60 | median 47, worst window 30 (console crowd: 31 to 35) |
| SKIP per 60 | median 13 |
| Master pass length (FRT ticks at pass end, field = 3,503) | median 1,540, p90 2,048, max 2,864 |
| VDP1 commands in the picture | 260 to 525 in the crowd |

The port's game logic, lifted from the same 68K code, keeps the tick count at 60 as long as the master finishes a tick inside a field. Ymir's master uses about 45 percent of a field in the crowd.

## 4. What the console's DONE 13-15 means in game time (MODELLED)

Stock Ymir says MISS 0; the console says MISS about 45. So the console's master is slower than Ymir's. Two attempts to find out how much:

1. **Ymir's own "hardware" bus table** (the one saturn.cpp keeps commented out as "passes misctest but too slow because the cache model is inaccurate"): run hw1 gives PIC 30 (console 31-35) but MISS 0 and ticks 60; the master pass grows only to a median of 2,163. Not enough: the master's code and data mostly hit the cache in Ymir, so the table barely moves it. Whatever slows the console's master (bus contention with the slave and the VDP1/VDP2 writers, cache line fills charged as one access in Ymir, cart code) is not in Ymir.
2. **Master slowed by a factor f** (GS_MSLOW, only the master SH-2's cycles, the slave and the video chips untouched), same scene, same bot (runs f10 to f35; one run each, deterministic enough that repeated runs agree to 1 to 2 ticks):

| f | ticks per 60 (whole fight) | worst 60-vblank window | MISS median / max | DONE median / min | PIC median | SKIP median |
|---|---|---|---|---|---|---|
| 1.0 | 60.00 | 60 | 0 / 0 | 60 / 60 | 47 | 13 |
| 1.5 | 60.00 | 60 | 0 / 6 | 60 / 54 | 41 | 19 |
| 2.0 | 59.66 | 57 | 11 / 29 | 49 / 31 | 36.5 | 23.5 |
| 2.5 | 53.82 | 38 | 34.5 / 49 | 25.5 / 11 | 31 | 29 |
| 2.75 | 48.68 | 33 | 41 / 52 | 19 / 8 | 34 | 27 |
| 3.0 | 47.57 | 27 | 43 / 54 | 17 / 6 | 36 | 25 |
| 3.5 | 37.33 | 20 | 50 / 55 | 10 / 5 | 36 | 23 |

The console's crowded-fight reading (MISS about 45, DONE 13-15, PIC 31 to 35) is reproduced at f between the 3.0 and 3.5 runs (MISS 43 and 50, DONE 17 and 10), and PIC comes out right although it was not fitted. Pooling all 169 windows of the slowed runs, the relation between DONE and the game's tick rate is:

| DONE in the window | ticks per 60 (median, min to max) | PIC median |
|---|---|---|
| 50 to 60 | 60 (59 to 60) | 41.5 |
| 40 to 49 | 60 (59 to 60) | 31.5 |
| 30 to 39 | 59 (58 to 60) | 30 |
| 20 to 29 | 54 (47 to 60) | 32 |
| 15 to 19 | 48 (38 to 52) | 34 |
| 10 to 14 | 41 (33 to 47) | 36 |
| 5 to 9 | 30 (20 to 37) | 39 |
| **11 to 17 (the console's 13-15)** | **43.5 (p10 36, p90 48)** | 35.5 |

So under this model, DONE 13-15 corresponds to about 36 to 48 game ticks per 60 vblanks, roughly 60 to 80 percent of the arcade's speed, and DONE must fall below about 35 before any game time is lost. Everything hinges on the model (one uniform slowdown of the master, game scheduling identical to the console's, which it is: same code). It does not establish the console number, and the light scene (console DONE 42) is not reproduced by a uniform factor: in the quiet part of the stage the slowed master's pass ends near 1,100 ticks and still finishes inside the field, where the console already misses 18 of 60. Something besides a uniform slowdown (bursts, the master's snapshot work when the layers scroll) matters there.

## 5. What DONE and CUT really are (kernel.c f_d86 / sat_vblank, fps_hud.c)

- `game_done` is cleared at every vblank entry and set when the dispatcher completes one walk over all 16 task records without a new vblank having set the flag (the 0xff0266 byte, set by the lifted IRQ body). MISS counts vblanks entered with it still clear; DONE = 60 minus MISS per 60 vblanks. It measures "the CPU was idle before the next vblank", which is a load flag.
- The gameplay task is index 4. A vblank during the tick (or the tick running to the end of the field) makes the dispatcher restart at task 0 when the tick returns (the flag is only looked at between tasks); the tick has run, tasks 5 to 15 (idle task 6, the fade and palette helper tasks) were skipped for that pass. That skip is CUT: tasks, not game time. The arcade restarts the same way (0xd9a), so the order of starvation is the same.
- When the gameplay task is behind, the restarted pass runs it again at once (its countdown was decremented by the vblank), which is the arcade's catch-up. Game time is lost only when the master cannot get through enough ticks over a stretch of frames: the backlog (ticks owed) is what ticks per 60 shows and DONE does not.
- TASK RUN counted task runs, which includes the idle spin (the dispatcher walks the list about 200 times a vblank in Ymir; 51 in MAME) and sat at the display cap of 9999. It has no game-time meaning and is dropped.
- DONE rises to 60 and falls to a few percent as utilisation goes from under to over one field, long before ticks fall (table above): high MISS with ticks at 60 is a master that is nearly full, not one that is losing time.

## 6. The new readout field (branch lane/gamespeed-20261112)

`TICK n CUT n` replaces `TASK RUN n CUT n` on readout line 4. TICK = gameplay ticks the game ran in the window, per 60 vblanks; 60 = full arcade speed. It is read from `sat_dbg.ff8018`, which already holds the game's IRQ byte (high) and tick byte (low) in one 32-bit word written at the end of every vblank handler, so both counts come from one instant. Only `saturn/rt/fps_hud.c` changed: no kernel change, no RAM (it reuses the unused slot `st[8]` in the cart-resident state), cart tail +52 bytes (text 0x610 to 0x648 plus 4 bytes less rodata; the SUPER_ANSWER's tail margin was about 330 bytes), low RAM free stays 96. Behaviour: reads 0 outside play (menus, fades, loads: the loop is held), may read above 60 for a moment in scripted scenes (a held button fast-forwards them in the arcade), the byte wraps at 256 so a window over 250 vblanks is not shown.

**Checked in YMIR (private verification disc, not staged; built from commit 86a0603, build id F2 86A060, recipe of lane-hwboot runhw.sh with my own work dir):** stock master, the readout reads `TICK 60 CUT 26` in the Coffee Shop crowd (run v10, screenshot ymir_gs\runs\v10\p001113.png) and 0 outside play. With the master slowed 3.0x (run v30) the three readout photos read TICK 36 (MISS 49, DONE 11), TICK 59 (MISS 31, DONE 30) and TICK 35 (MISS 52, DONE 8), and each equals the probe's count for the matching 60-vblank window (36, 59 and 35; matched on MISS, SKIP and PIC as well). The probe's addresses were moved by +0xD8 for this build (GS_OFF) because the newer base commit shifted high RAM. The readout code is the only change; the disc was deleted after the check as the disk rule asks (rebuild with E:\AvP\learning\lane-perfbuild_gs.sh).

How to read it on the console: stage 1 crowded fight, photo of the readout. TICK 60 with DONE 13: the master is full but the game is at speed (the owner's feel). TICK about 45: the game really runs at 75 percent there, and the cost is master time, not graphics (PIC is the slave). The stage 1 crowd in this model sits where TICK 45 and DONE 14 go together.

## Files

- E:\AvP\learning\lane-perf\gamespeed\ gs_walk.lua (MAME probe and bot), run_mame.sh, an_mame.py, an_mame2.py, an_ymir.py, sweep_summary.py, s60k\frames.tsv, t3\writers.txt
- E:\AvP\learning\lane-perf\ymir_gs\ patched Ymir sources (sh2.cpp, pad.cpp, build.bat; derived from Ymir, kept out of the repo), run\ (exe copies, never deleted), runs\* (gs.log per run, screenshots, run.log), ygs.py, gs_ymir.py
- Branch lane/gamespeed-20261112 (off lane/hwboot-20261110): saturn/rt/fps_hud.c, tools/gamespeed/
