# fix7n4: the TICK game-speed readout on the hwboot line (2026-11-12)

Disc `avp_3h_A_fix7n4`, source 9071bc8, build id `F2 9071BC`, FIT 2. Base: fix7n3 (`AVP_HWBOOT_FIX7N3_20261112.md`, source 2cb8435, disc kept unchanged). Labels: EMULATOR = strict Ymir (real JP BIOS, 4 MB cart); nothing here is a console measurement.

## What came in
- From `lane/gamespeed-20261112` (private-origin): `86a0603` (fps_hud.c: line 4 `TASK RUN n CUT n` becomes `TICK n CUT n`, read from `sat_dbg.ff8018`, reusing `st[8]`) and `1eac6b2` (note `docs/notes/AVP_GAMESPEED_20261112.md` and `tools/gamespeed/`). Cherry-picked as 11430bc and bca8f6c. The only conflict was in `fps_hud.c`: the lane's 5 readout rows against this line's 6 (the `HW SND ... TEST` line is kept), resolved by keeping the 6 rows and adding the lane's `st[8]` set-up and comment. Nothing from either side was dropped.
- TICK = gameplay ticks the game ran per 60 vblanks: the byte at ff8019 (one per pass of the gameplay loop) over the vblank counter at ff8018, from one 16 bit word. 60 is the arcade's rate. The speed lane's finding (MAME: 59.99 over 57,715 busy frames; strict Ymir port: 60.00 in the same fight) is in its note; the console reading is what the new field is for. DONE, PIC and CUT are not game speed.

## One more fix
The LD clock (SMPC status report, `kernel.c rtc_secs`) once returned minutes or seconds that were not BCD while a peripheral INTBACK was still queued: Ymir showed `LD2 ... D1705 B18` after a continue. It now reads again (up to three times) until both bytes are valid BCD and otherwise keeps the last good value (9071bc8). Seen again in Ymir afterwards: `D10 B145`, `D9 B69` as before.

## Gates (all on 9071bc8)
- Build (the build itself fails on them): VDP2 access cycle rules (`tools/vdp2_cycle_check.py`: PASS); data alignment (`tools/align_gate.py`: 319 data symbols, 46 reviewed cast sites, 197 accessor calls, 287 round files and `REVEAL.BIN`: 0 hits); low RAM free 96 bytes; high RAM free 924; cart free 5,008 (cold1 end to cart end); Wolverine block `0x27f7de0` size 23,116 outside the ROM image and every stretch.
- Tests: `tests/align_gate_test.py`, `tests/lat_protocol_test.py`, `tests/vdp2_cycle_check_test.py`: pass.
- Ymir data-misalignment gate (`tools/ymir_misalign_gate.py --run`, boot, title, stage 1, KO, continue with another character, next stage, on the shipping disc): 0 data accesses (about 7,000 instruction-fetch artefacts filtered). Also 0 in two Wolverine passes (below).

## Ymir readout checks (EMULATOR)
- Shipping disc (Predator Warrior, stage 1, continue screen): six lines drawn, `TICK 60 CUT 32/48`, `HW SND 1 OK TEST 7`, `F2 9071BC`, PRESS START visible.
- Wolverine-on test build (`GUEST_DEFAULT=1`, same source; builds 11430bc..bca8f6c and 9071bc8): stage 1 fights `TICK 60 CUT 24 to 44`, `PIC 40 to 60`, `MISS 0`, `SKIP 0 to 20`; his first talk box ("They keep coming, bub. We gotta fall back!") drawn with his face, no fault, PRESS START and the HUD inset visible; two continues (SELECT YOUR CHARACTER, back in play), stage 2 load. One window right after a file load read `TICK 172`: the catch-up of the loading time (the game runs the ticks the load held back), not a speed; the README says so.
- Not checked: the console; sound.

## Housekeeping
Intermediate ISOs and test builds of this lane were deleted after the gates; see `E:\AvP\learning\lane-hwboot\DELETED-20261112.txt`. The staged discs under `E:\AvP\package-integration\fenrir` (fix7n3, fix7n4 and the older ones) were not touched.
