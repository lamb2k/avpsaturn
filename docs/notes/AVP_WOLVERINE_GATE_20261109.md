# Wolverine KO fix and Round 1 gameplay gate, 2026-11-09

Lane `lane/wolverine-gate-20261109`, from `9728e4e` (lane/wolverine-anim-20261109). Tiers: HOST (tests, fit, build), EMULATOR (Yaba, own copy, port 9713).
Hardware UNRUN. Evidence: `E:\AvP\learning\lane-wolverine-gate` (not in the repository; no ROM data leaves the PC).

## 1. Invisible Wolverine at KO: cause and fix

Cause (Yaba, state 0400, frame-exact trace `rec\ko_before.jsonl`): in the dying state the game's death blink toggles the player block byte +1
(0201 / 0200, every frame, about 60 frames, Schaefer included: `rec\ko_sch.jsonl`). `is_wolverine()` used that byte as the character id, so the slot stopped
being his every other frame. The pad hook then called `wv_reset()` (clock to 255, step_now to 0xffff) and the next frame restarted the knockdown at its first pose.
Sampled on the blank frames, nothing was drawn.

Fix (`d5f2dda`, wolverine.c): the identity is latched while he is alive (`wvid_`) and kept while the state byte is 04 (dying); the slot is dropped as before when byte +0
is zero. On the game's blank blink frames `wv_blank()` hides the body, as the game hides Schaefer's, so the blink stays authentic (a steady body would be one `continue`
removed in `sat_guest_objects`). Host test `test_ko_blink` (90 ticks of blink, clock never resets, body hidden on exactly the blank frames, reset on slot clear).

Before / after (same harness, health of player 1 zeroed on stage 02): before, `cur` flickers 8 / 255, `wall` 0..1, step 0x75 (flying pose) on every other frame;
after, `cur` stays 8 (knockdown), `wall` counts 78..109+, step 0x83, 0x84 (lying pose) held to the end of the KO. Clips: `clips\ko_before.gif`, `clips\ko_after.gif`, sheets beside them.
The OFF and ON switches share the code path (SAT_WV_NATIVE_TIMING is not involved).

## 2. Round 1 gameplay gate

Bot: `r2bot.py` (from r1bot.py). Same bot for all three runs, disc built from the same tree: Wolverine switch OFF (`disc_offk12`), SAT_WV_NATIVE_TIMING ON (`disc_onk12`), Schaefer
(`-DSAT_GUEST_DEFAULT=0`, `disc_schk12`, deleted after the gate). Debug assists are in the harness, not in any build: no build define was used, all discs are release-flag builds.
- invulnerable player: the harness writes health back to 101 when it falls under 70 (not in KO), `BOT_INVULN=1`;
- boosted damage: when the boss (actor ffa3c0, hp at +0x40, 248 max) is engaged, its health word is set to 20 (`BOT_BOSSBOOST=1`), so about four real hits kill it;
- warp: when the boss is more than 130 px away the player is moved 70 px from it, at most every 120 vblanks (`BOT_BOSSWARP=1`). Without it the bot never reached the boss through the xenos that keep respawning at 7-16 v/s.
- melee only (attack and jump, no gun key) for every run so Schaefer's gun does not make the baseline easier; the kill assist (`BOT_BOSSKILL`, poke the boss dead) was armed at 900 vblanks and never fired.
The boss death, the clear flag (ff81f3 set in section 2), the section change and the section 3 start are all the game's own events.

| Check | OFF | ON (native timing) | Schaefer |
| --- | --- | --- | --- |
| Boss present / actor gone / clear flag / section 3 (vblank) | 5206 / 5721 / 6549 / 6735 | 5202 / 6019 / 6800 / 6974 | 5267 / 5950 / 6976 / 7155 |
| 1,200 vblanks into section 3, no fatal, no stuck | yes (x 1664) | yes (x 1664) | yes (x 1589) |
| Fatal | none | none | none |
| Hits taken (0202xx entries) | 36 | 37 | 2 |
| Grabbed by an enemy (0204xx entries) | 2 | 1 | 0 |
| KO | 0 (invulnerable) | 0 | 0 |
| Pick-ups (health up by 5 or more) | 1 | 2 | 1 |
| Score at the end (HUD) | 48,000 | 44,000 | 58,500 |
| HUD | name Maj.Schaefer, Schaefer portrait, health bar, boss bar, score all drawn | same | same |
| Scripted events (stage lights-out before the boss, boss bar, door to section 3) | seen | seen | seen |

Not equal, stated plainly: the bot took 36-37 hits with Wolverine and 2 with Schaefer in about the same stretch (runs are not deterministic and Yaba ran 6-13 v/s against 33 v/s for the Schaefer run, so this is
an observation, not a measurement). Likely sources are his MSHvSF hurt boxes, shorter reach and slower recovery against Schaefer's data; it was not isolated. Score is 24-25 percent lower with Wolverine.
The HUD name still reads Maj.Schaefer in the Wolverine runs (`names()` patches ROM bytes at 0xaedca / 0xac699; the cause was not investigated): found, not fixed.
The 0204xx state is the player being GRABBED by an enemy (xeno on his back, `clips\throw_off_k12.gif`, `clips\throw_on_k12.gif`), not a throw he performs; he shows his MSHvSF throw poses (move 10) while held, which reads as hunched and struggling.
Frame-exact traces in `rec\gate_off_throw1.jsonl` (state 020406, cur 10, 52 frames) and `rec\gate_on_throw0.jsonl` (020408, 120 frames, still held at the cap).

## 3. fit gate (pre-existing failure, assets changed)

fit.py with the anim lane's D6 assets already FAILED at `9728e4e`: stage24_ma lost one more arcade tile than the Schaefer baseline (wolv_drop 2873, sch_drop 2872). The anim lane's fit ran at 04:42, before its later code
growth; the cold-code block (`cold1_at`, 4 KB steps) crossed a page and took 4,096 bytes of pack room (`cart_pack_room` 1,634,304 -> 1,630,208, round_code_ends.json of its own final w1 shows the same). The code fix is not the cause.
Used the lane's own K 12 tile merge set `D6k12` (1,474 Wolverine tiles, same moves and boxes as D6, contact sheet "still clean" per the anim notes): fit 76 of 76 files gate True, 0 own tiles dropped, 0 missing keys, margin to Schaefer 0 in the tightest file, for OFF and ON builds.

## Build and tests
Build (POSE_KEYS=0 KEEP_ROUND_FILES=1, assets D6k12): OFF hw_free 4,616, lw_free 72, cart_free 6,348 (full pack rebuild 1,836 s); ON lw_free 68, cart_free 6,292. Python tests in WSL: 91 run, 61 pass, 30 private-dep errors (the baseline); test_wolverine_* 22 of 22 with the C fixture.

## Yaba notes
Mid-run freezes (the core stops, PC fixed) happened three times: during a memory_write while a second MCP session was polling, during an outside screenshot call, and on boot twice. The final runs used one MCP session (the watcher thread is off by default now), and a watchdog (`seq.sh`) restarts a run whose log goes quiet for 4 minutes. Do not call the MCP port of a running leg from outside.
