# Status

Only source of current state. Branch `decomp/main`. Backlog: docs/BACKLOG.md.

- P0: items 1, 2 and 3 done (item 3 pending merge of lane/item3).
- P1: first gate measured, docs/notes/AVP_FIRST_GATE.md; recommendation GO, awaiting coordinator.
- Whole-game comparison: not run. Hardware: UNRUN.

## Whole-game check, 2026-11-06 (HOST against MAME, attract run, golden_c)

Exact IRQ preemption: MAME records each real IRQ's interrupted PC and registers; lifted code takes the IRQ at the same instruction. Registers are global across tasks, as on the board. Masked as non-state: task SR/PC/USP fields, stacks, ff0258, f_1a36 save area, idle task state byte, current-task pointer. Seeded from MAME because the hardware test is skipped: object RAM, d3, a4. First divergence at dump 1179 after a one-object difference at 1125.

## Saturn image plays to Round 1, 2026-11-06 (EMULATOR, Yaba; not hardware)

Lane satint, items 15-18 joined in one image: lifted game + saturn/gfx + SMPC pad through the game's own latch. Scripted pad flag (KERNEL_CFLAGS=-DSAT_INPUT_SCRIPT, the retained route's schedule): attract, coin, Predator Warrior, Round 1 gameplay with sprites and all layers on screen, no fatal to vblank 2158. Timer readings are emulator-only, not Saturn timing: graphics about 16-22 ms, peak 63.6 ms, over the 16.7 ms field, so the game often runs at 30 Hz or below (overruns 882 of 2158 vblanks).
Memory (item 17): Round 1 pack from a MAME census to the boss clear, 1,793,444 bytes. It fits only because the opcode view is cut from 1.06 MB to a 226 KB side store of OP* reads, with each read rewritten to a store offset. Two ROM stretches the route never read hold scroll 1 and 3 tiles and one cold code chunk, so the cart image holds Round 1 only: other rounds must load between rounds (not built). Free: cart 960 bytes, ROM stretch 23 KB, high RAM 2.4 KB, low RAM 33 KB.
Host check, final ROM with the store: clean 3000 of 3000 against golden_c (attract). Real pad presses, full Round 1 to the boss, audio and hardware: not run.

## Whole-game check through boss clear, 2026-11-06 (HOST against MAME 0.289; not emulator or hardware)

Golden `golden_r1s`, saved input route tools/routes/r1_pw_ko_boss.txt (tools/mame_golden_run.py): Predator Warrior, Round 1 start (frame 2238), KOs at frames 6082, 9471 and 12657, continues (6692-6723, 13292), boss clear (route 6 at frame 15019), to frame 15700. Host check clean 15618 of 15618 dumps, work RAM and object RAM. Byte-identical to the retained harness's run of the same schedule. Mask unchanged.
IRQ placement at kernel points now requires work RAM equal to the next dump, so a host divergence shows as a diff and a missed IRQ. Timing inside native kernel code is therefore checked by state only, not by cycle.
MAME state saves at route points are in golden_r1s/sta (item 14 start). Loading them, and host fixtures, are not built: lifted tasks live on native stacks, which a RAM dump cannot restore. The full host check takes under a minute, which covers the need on host.

## Drawing on the slave SH-2, 2026-11-06 (EMULATOR, Yaba; timing MODELLED, not hardware)

Item 20. Master keeps game logic and copies a per-frame snapshot at vblank; slave draws from it and owns VDP1, VDP2, CRAM, caches and shadows. One handoff; a busy slave skips a picture, never the game. Scripted scene, vblanks 1000-1650, build flags -DSAT_INPUT_SCRIPT -DSAT_PROF, same route:
| | before | after |
| --- | --- | --- |
| game frame mean / p95 / top ms | 29.55 / 65.23 / 78.04 | 11.16 / 25.0 / 48.16 |
| graphics mean / p95 / top ms | 18.18 / 28.04 / 64.01 (master) | 7.53 / 19.51 / 35.97 (slave) |
| snapshot on master mean / p95 ms | none | 4.27 / 7.93 |
| overruns of 650 vblanks | 266 | 55 |
| pictures drawn of 650 | 650 | 533 |
Whole-run graphics peak after: 57.2 ms, outside the window. The game now reaches further in the same vblanks, so the scene is not frame-identical. 60 Hz does not hold yet.
Two artefacts: the grey wall was VDP1 trails, fixed by a clear polygon at the head of each list (manual plotting has no erase). The black box is authentic: MAME shows the same empty box for a few frames as the message closes.
Missing tiles: real pixels the pack lacks, because the pack is a census of one MAME route. 493 of about 500 lookups fall at vblanks 550-803, before Round 1 gameplay on this script's earlier coin; few arrive in gameplay. Not fixed.
Sprite tiles over golden_r1s (tools/sat_tile_funnel.py, MAME data, 15618 frames): commands mean 149.6, p95 373, max 520; 800-tile worst frame loses 172 off screen and 108 empty, already culled per tile. Row runs on that frame 153. Live sprite banks mean 5.1, p95 9, max 11 of 32. Merging rows is not built: it needs contiguous texture slots.
Unproven: VDP1 fill time and bus contention on hardware; command table overwritten while VDP1 still plots a late list.

## Round 1 played on real pad input, 2026-11-06 (EMULATOR, Yaba; not hardware)

Real input: `saturn/rt/play_yaba.py` posts key messages to Yaba's own window; the emulated pad goes through SMPC to the game's latch. No scripted flag. Closed-loop bot `saturn/rt/play_round1_bot.py` reads RAM over MCP and picks keys.
Run: Predator Warrior from coin to Round 2 title card, attract 0 throughout, 2 process legs joined by a save state at v10919. Section 1 clear v5711, boss (ffa3c0 class 06) from v5834, 7 KOs (v4595 to v19970), each continued with a coin and start, returning 101 health, boss health to below zero about v23085, ff81f3 set v23142, section 3 v23325. Screenshots and logs: E:\AvP\learning\lane-play\proof.
ff81f3 is a section clear flag, not boss clear. Boss clear is ff81f3 set in section 2 (ffd182) followed by section 3. An earlier run's flag at v4885 was section 1.
Fixes: 25 targets in 7 unresolved jump tables (tools/satint_scan_tables.py; the fatal was 0xe1 at 0x4af24), added as an extra lifted chunk in the lane's work directory only: they still need adding to the shared roots.
Not re-proven: that run predates the new pack, the speed merge and the readout. The final image had short runs only (about 2200 vblanks, no fatal). The bot played far worse than the MAME route and needed many more ticks.
Yaba speed in gameplay falls from about 60 to about 20 vblanks/s within a minute, the same with near-zero polling, key input or heavy reads, from one save state. So it is not MCP. Cause not found. A long-lived process fell further, to about 3-5, with other host load present.

Pack: real-play key log (SAT_KEYLOG, first ~2600 vblanks) plus a census from Round 1 start. 1079 sprite and 64 scroll 1 keys were missed by the old pack; 1202 of 1883 sprite extras fit, in play census order first, and attract-only tiles left the pack. Main 1,648,296 bytes. Missing counter 1224 before (about v2600), 940 at v2157 after: not the same point, and not fixed. The title's digits and some round card letters still draw blank in shots taken before this pack; not rechecked after. Room came from moving one more cold chunk into the rest of the tile ROM stretch.

Audio: hooked in; clips load through low RAM to SCSP RAM at boot. Pick: per-channel slots. Capture from a patched Yaba (saturn/audio/yaba_wav_dump.patch, SCSP output), same 14 commands, against MAME, saturn/audio/compare_raw.py:
| | per channel | single mixed stream |
| --- | --- | --- |
| frame cost, worst, emulator timer | 0.10 ms | 2.16 ms |
| 10 ms loudness correlation, median per second | 0.735 | 0.844 |
| level against MAME | +1.0 dB | +2.1 dB |
The stream sounds closer by this measure, at about 22 times the worst cost, and Yaba likely undercharges its bus reads. The mix uses 2 slots and 16 KB, not the 3 slots of the MSHvSF evidence. Effects in the slot build run quieter than MAME over the first 11 s. Not tuned.
Game image capture: non-silent; clips 0x24e, 0x254 and 0x203 matched by correlation 0.81-0.997. CD music is in the capture. Not compared to a MAME run of the same play, because the play differs. No person has listened.

Package, item 26: `saturn/package/build_package.py`, output E:\AvP\package-play: two data images (DMA off and on), cue, tracks, hashes, HARDWARE_TEST.md, with on-screen bars for game, drawing and VDP1 time, and Y and Z test modes for fetch against fill. Hardware: UNRUN. The bars ran on Yaba; the DMA image did not get a gameplay run, only the build.

Later build, same day, after the speed merge and with 2 KB task stacks: one continuous process, 57 vblanks/s, route rerun by the bot from boot. Round 1 boss cleared, section 3 at about v21400, no fatal. Stack canary, read at each KO and every 600 vblanks through 8 KOs and continues: least free 1728 of 2048 bytes (task 4), then 1808 (task 2). No stack room change needed. The run went on into Round 2 (not built: wrong background and tiles, as expected) until stopped.

## Final package, proof on its bytes, 2026-11-06 (EMULATOR, Yaba; hardware UNRUN)

E:\AvP\package-final from commit 5b2484b, avp_saturn.iso sha256 ff6d0524269c1c6552a0449f81d4cabbbc41deeb6067506690f62ae5a3b40605. Lift rebuilt from tools/roots.txt alone: host check clean 15618 of 15618, and again with all six ROM stretches overwritten (cold code and tile spill: 0xd1000, 0x105000, 0x13f000, 0x171000, 0x184000, 0x198000).
Bot on that image (same hash before and after), one continuous process: Predator Warrior from boot, 8 KOs, 27 continue presses, boss from v5015, ff81f3 set in section 2 with attract 0 at v24006 (second MCP session polling only those markers), section 3 at v24201, no fatal. Boss clear seen directly.
Pack: cold code off the cart, so all real-play keys, all logged scroll 1 and the early attract story fit. Keys 14208 / 2010 / 2972 / 307. Still missing: 1202 sprite, 283 scroll 2 and 112 scroll 3 keys, all later attract demo scenes (logged to v7876). Missing counter (lookups, not unique tiles) 215 at v24201 on the bot route; 2830 at v7802 idle in attract.
Speed: command shadow on the sprite stage (only changed VDP1 words) made it worse under Yaba, MODELLED, same flags and window: graphics mean / p95 / top 7.62 / 18.9 / 50.6 ms before, 8.51 / 21.95 / 52.43 after. Not kept. Yaba may undercharge VDP1 RAM writes, so hardware could differ.

## Round files from CD, 2026-11-07 (lane rounds; built, HOST check on Round 1 only; EMULATOR run blocked, hardware UNRUN)

One file per stage word ff81e8 (20 files, RNN.BIN): sound set, ROM restores, tile pack. Stage 0 is attract, front end and credits; attract demos at mode 2 load their stage's file. The master stops the game between task walks, waits for the slave, blanks the display and reads through the loader's GFS, kept resident in 0.BIN; music restarts afterwards. Nothing loads mid-stage.
ROM: 725 KB of pages no walk reads; lifted cold code stays there. Sprites past the cart's room go to ROM pages this stage, the next stage and the front end do not read (with a page either side); each file restores pages it needs that another file overwrites. The six old stretches are gone: later rounds read 0x105000 and 0x13f000.
Census (MAME): tools/rounds_walk.py, all four characters to the ending with health written, four without it for 60000 frames each, attract, plus golden2's census. A host run proved the KO paths matter: with census lacking them, garbage ROM diverged at the first continue (vblank 6705).
Host check, per-stage garbage in every page a stage does not keep, golden_r1s: clean 15618 of 15618, baseline also clean. Later rounds have no such check yet; golden_full is in golden2's format.
Load, MODELLED at 300 KB/s: 1.7 to 9.9 s, seek not counted. Not measured.
Does not fit: stage 0e drops 600 sprite keys, stage 24 drops 225 (highest key numbers, draw blank). Sound: stages with more clips than SCSP RAM drop some, listed by tools/rounds_config.py. Music 24 commands, 27 tracks, 289 MB, capped at 80 s a render.
Yaba fault on this PC since about 23:30 on 11-06: VideoCore 1 exits 0xc0000409 in 4 s, every other core says "Cannot initialize Video", all builds, install matches its zip. Plain OpenGL 4.6 on the NVIDIA works from a test program. Bundled software GL has no GLSL 4.0. Last good run 18:52.
Lift: this image uses roots from decomp/main; golden2 is adding roots for later rounds, so unresolved targets are expected past Round 1 until those land.
## Whole game to the ending on host, 2026-11-07 (HOST against MAME 0.289; not emulator or hardware)

Route tools/routes/pw_full_game.txt: Predator Warrior, all 7 rounds, ending, staff credits, GAME OVER, attract at frame 317389, to frame 317990. Real ports only, no RAM writes, no invulnerability: closed-loop bot tools/mame_route_bot.lua, 115 KOs with continues. It starts from the r1 route to frame 15700. Replay reached the same end state and KO count; ending checked on stills.
Golden `golden_full` (LEARN_DELTA=1, changed words per IRQ, 341 MB, every IRQ kept; host needs GOLD_DELTA=1). Host check clean 317908 of 317908, work RAM and object RAM, missed IRQ 0, on an incrementally rebuilt private tree (no build from scratch of the final roots). golden_r1s on the same build: clean 15618 of 15618.
Fixes: kernel task record clear now allows an IRQ between its longs (first RAM divergence, dump 76725, native kernel atomic, IRQ at 0xf66 in MAME). IRQ placement now also requires the current task and the object list to match, as shared wrappers and object-only loops looked identical (object diffs from dump 60215, wrong task at dump 314110). 15 roots added, mostly computed jump tables the map misses when a call sits between table read and jump (0x7d412, 0x61d8c forms).
13 unlifted targets were odd branch targets, an address error on a 68000, from data decoded as code. Lifter now emits UNHANDLED for them; none was reached on this route. 12 of the 13 source sites were never read in MAME's opcode space; 0x6cc56 was read but not executed.
Census for other rounds: E:\AvP\learning\lane-golden2\census (README.md there).
Unproven: other characters, 2 players, other branches and endings, Saturn image past Round 1. As before, a clean run does not check cycle timing inside native kernel code.

## Whole-game fit, 2026-11-07 (lane fit; HOST against MAME 0.289; image built, not booted; hardware UNRUN)

Image rebuilt from a fresh code map of tools/roots.txt (same as golden2's): sat.iso sha256 3efdf5d91ff36f038094b547f8598d655b4655830612c45b032d04ff651e2234, E:\AvP\learning\lane-fit\work. Not booted: Yaba cannot start video on this PC.
Host check against golden_full, plain: clean 317908 of 317908, missed IRQ 0. With garbage in every ROM page a stage does not keep (ROUNDS_SWAP in tools/lift_runner/host_kernel.c, list from tools/rounds_hostcheck.py) and OP reads in their Saturn form (tools/rounds_hostfinal.py: each base rewritten to its store offset, the rest of opcode space 0xA5): clean 317908 of 317908. Keep lists needed no change.
The Saturn form found a real bug the old check could not: the side store lost parts of tables, because a table can run into real code (0x4ccb0 into 0x4ccc0) and a read past a store run sees other bytes. It diverged at vblank 19015. tools/lift_runner/oplog.sh now records each base's real read range for tools/satint_merge.py. Store 235,656 bytes of 256 KB. Only the Predator Warrior route proves those ranges.
Kernel: a vblank could land inside a long of a task record, which the 68000 never allows. Kernel longs on 4-byte boundaries are now one write, and the free count step is masked. Built, not run. Lifted code still splits every WR32 and RD32 and runs read-modify-write as several SH-2 instructions, so an IRQ can land inside those: not addressed.
Sprite drops: 0e 600 to 0, 24 225 to 174. Room came from ROM stretches of one page up and the unused cart tail above cold code. Stage 24 is now limited by the 14-bit payload index (16382 tiles), not by room. Drops go by use (tools/rounds_rank.py): every dropped key was seen by one walk only, none by the real route or a KO.
Sound drops are unchanged and still go largest first. Stage 10 drops clips the real route uses often, 0x4d and 0x118 at 232 uses each.
Other characters: single game each, health written, tools/rounds_walk.py with ROUNDS_ONCE. Stills show the character's own name and portrait in play in all 19 stages and the ending. No key, ROM page or sound falls outside the stage files; keys dropped in stage 24: Dutch 9, Linn 45, Hunter 120. No unassisted run and no host check for them.
Unproven: any boot of this image, the kernel change at run time, other characters' OP read ranges, 2 players, load times.

## Other characters and two players, 2026-11-07 (lane chars; HOST against MAME 0.289; image built, not booted; hardware UNRUN)

Saved routes, real ports only, no RAM writes (tools/mame_route_bot.lua with BOT_CHAR, BOT_P2): tools/routes/full_c1.txt, full_c2.txt, full_c3.txt, co2p_to_1e.txt. Goldens LEARN_DELTA=1.
| Route | Dumps clean, plain | Dumps clean, Saturn form | KOs |
| --- | --- | --- | --- |
| Schaefer (golden_c1), to attract | 272171 of 272171 | 272171 of 272171 | 94 |
| Linn (golden_c2), to attract | 369051 of 369051 | 369051 of 369051 | 57 |
| Hunter (golden_c3), to attract | 333669 of 333669 | 333669 of 333669 | 116 |
| Warrior (golden_full), to attract | 317908 of 317908 | 317908 of 317908 | 115 |
| Warrior + Schaefer (golden_2p), to stage 1e only | 329918 of 329918 | 329918 of 329918 | |
golden_r1s plain: clean 15618 of 15618, before the last audio-only change. Missed IRQ 0 on all. Saturn form means per-stage ROM garbage and OP reads through the store. The Saturn-form lift was checked with the keep lists and store of image 97790a2e; the final rebuild changed only sound sets. The two-player bot stuck in stage 1c or 1e on both tries, so stages 20 to 26 have no two-player data.
Kernel fixes, host and saturn/rt/kernel.c, the Saturn side not run: trap 11 was empty (ends all eight records; Schaefer and Linn reach it at game over); trap 8 now ends only the first live record with tag d1, as the board does; a resumed task gets d1 and a1 as the board leaves them. Host IRQ placement at dispatcher points now follows the golden's a0, since free-stack order depends on it. One root added, 30e0.
Sound drops go by use on the real routes (tools/rounds_config.py, WORK/sound_rank.json). Warrior census alone: stage 10 keeps 0x4d, 0x118, 0x4e, 0x119, 0x4f and 0x11a; only 2 route uses drop in the whole game. All five routes in one image: lost plays per route 143 to 307; worst stages 24 (64 clips, 53 used on a route), 20 (55, 40), 10 (67, 48), 1c (54, 48). All 516 KB of SCSP RAM is in use on those stages.
Sprite index: sprite words are now key << 16 | index. The 16K cap is gone; stages are limited by room.
Sprite keys dropped, one image for all routes, by rank: 0e 2681, 1c 158, 1e 733, 24 2561. Without two-player data: 0e 1915, 1e 363, 24 2561. Keys on a real route that draw blank: Warrior 0e 35, 24 336; Schaefer 24 1200; Linn 0e 296, 24 148; Hunter 0e 884, 24 62; two players 0e 779. Stage 0e and 24 are real gaps: room is the limit, about 2.2 MB of tiles against about 2.5 MB wanted.
Store 237,828 bytes of 256 KB. High RAM free 19.6 KB, low RAM 4.1 KB. Image E:/AvP/learning/lane-chars/work/sat.iso, 51.6 MB, sha256 97790a2e2a6ae6b86962900559c7ede49ec1111cec648e5d90e29dc6ff044747.
Two players, against the one-player union: 5983 new sprite keys summed over stages, new sound commands in nearly every stage (0x32x, the second player's clips), peak objects up to 132 from 96 (stage 18). Player 3 has no run; its cost is not measured. Second player was Schaefer only.
Unproven: any boot of this image, kernel fixes at run time on Saturn, any second player but Schaefer, three players, two players past stage 1e, other branches and endings, cycle timing inside native kernel code.

## Per-character stage files, 2026-11-07 (lane packs; HOST and replay against MAME 0.289; image built, not booted; hardware UNRUN)

Every stage now has 11 files on one disc: the one-for-all file, one per character, one per pair. Same candidates and keep lists; what will not fit drops other characters' material first (tools/rounds_variants.py, ROUNDS_VARIANTS). Three characters use the one-for-all file.
Selection: ff81cc holds a bit per character in play (1 Warrior, 2 Schaefer, 4 Hunter, 8 Linn). Bits are gathered while in a stage and cleared at the front end's load, as they drop around a KO and follow the cursor on the select screen. Replaying this over all five goldens picked the right file at all 95 loads (tools/rounds_variants_report.py); the kernel code itself has not run.
| Route | Blank keys, before | after | Lost sound plays, before | after |
| --- | --- | --- | --- | --- |
| Warrior | 371 | 0 | 157 | 7 (stage 24) |
| Schaefer | 1200 | 0 | 164 | 0 |
| Linn | 444 | 0 | 306 | 0 |
| Hunter | 946 | 0 | 215 | 4 (stage 24) |
| Warrior + Schaefer, to stage 1e | 779 | 0 | 143 | 28 (1c 13, 10 7, 08 6, 1a 1, 0e 1) |
Solo files drop no key that character's route, walks or KO showed. Each file still drops other characters' keys (about 5700 to 6000 per character over the game), and the sound table's lost plays above are all that character's route loses. In stage 0e two pairs not measured lose keys ranked from their walks, KO runs or the stand-in two-player run: Schaefer + Hunter 432, Hunter + Linn 1743. No pair drops a key from its own solo routes. Pairs not measured also lose 15 to 70 sound plays counted from their two solo routes, mostly stage 24.
Those pairs rank the second player's additions from the Warrior + Schaefer run only, so their real need is not measured.
Join path, not run: a character who joins or changes on a continue mid-stage keeps the current file until the next stage word, then gets the pair's file. Until then their keys outside that file draw blank and clips outside it are silent. A mid-stage load stays the owner's call.
Host check in Saturn form, same keep lists and store as image 97790a2e: clean 272171 of 272171 (c1), 369051 of 369051 (c2), 333669 of 333669 (c3), 317908 of 317908 (full), 329918 of 329918 (2p), missed IRQ 0. Sound and sprite files are not part of this check.
Image E:/AvP/learning/lane-packs/work/sat.iso, 502.6 MB (was 51.6), 210 round files, sha256 b5d86cd84a63ad3aa5d3cc3720f7959c1e3362ca677f1ea302cdedb9be9484fc. High RAM free 19.1 KB, low RAM 4.1 KB.
Unproven: any boot; GFS with 219 root entries in a directory over one sector (names table now 256, was 64); the kernel selector at run time; seek time on a larger disc; three players; any second player but Schaefer; two players past stage 1e.

## Characters, two players and sound on the Saturn image, 2026-11-08 (lane all; EMULATOR, soft-core Yaba; HOST against MAME 0.289; hardware UNRUN)

Package E:\AvP\learning\lane-all\pkgF, commit 5b60af3, avp_saturn.iso sha256 b9201af10abc27333c3a98a7ef5ff074202015bcfd6aa455bf144e419abcd3cb. Not copied to E:\AvP\package-all: two characters do not reach the ending on it. package-r7 untouched.
Host check, Saturn form, keep lists of this package: clean 317908 of 317908 (full), 272171 (c1), 369051 (c2), 333669 (c3), 329918 (2p), missed IRQ 0.

| Run, this package | Result |
| --- | --- |
| Linn | Boot to stage 26 and back to attract, vblank 277856, 82 KOs, 0 fatals. Selector picked stage*_m8 at every load. |
| Schaefer | Stages 02 to 1e, 0 fatals; held in 1e section 15 from vblank 221200 to 897123. |
| Hunter | Stages 02 to 1e, 0 fatals, past the 1c fault below; held in 1e section 15. |
| Two players | Not run on this package. |

Stage 1e hold: the Chrysalis (record ff a180, hp 49) sits on the wall at y 0xe9 and its whole record stays unchanged; Linn killed it on the same bytes. Writing ROM bytes back into the 287 pages stage 1e's file overwrote did not wake it from a held state, so a bad read before that point is not ruled out. Bot or image: not proven.
Previous package (52941db, sha256 49ce3871...): Schaefer and Linn to the ending, Hunter fatal 0xe2 in 1c, two players (Warrior + Schaefer) stages 02 to 1c on real port 2, where the bot stays in section 14.

Fatal 0xe2 at 0xa9cc4, found: an object's record at 0x333d4 (page 204) is read in stages 06, 10 and 12 but was not kept in 1c; its page held other bytes there, the script pointer read as 0, and the word at 0 indexed past the 8-entry table. Fix: every stage keeps pages two or more stages read (tools/rounds_config.py, ROUNDS_SHARED_MIN=2, no page either side). Cost in dropped sprite keys: 0e 2681 to 3521, 1c 158 to 1285, 1e 733 to 1757, 24 2561 to 3688; the file each character gets still drops no key of its own route (tools/rounds_variants_report.py). Pages read by one stage only stay exposed.
Earlier odd pointer (0x7767) on the old image: Yaba rounds an odd word read down; real hardware raises an address error there.

Other fixes: second pad read (saturn/rt/pad.c, P2 in the upper byte of in0, start 0x200, coin 0x2000); tiles fill never-read pages first; the Yaba runner voids a leg whose emulator does not own port 9640 (two lanes raced for it); the bot never saves state inside a load (such a state never resumes).
Sound: lane-emu's yabasanshiro.exe already has the AVP_SCSP_RAW hook and it runs under soft-core with SoundCore 0. Per-stage 20 s clips of Schaefer on the previous package: E:\AvP\learning\lane-all\capt\schaefer, all 20 stage words with sound. Against MAME clips anywhere in that capture: 62 clips, median correlation 0.567, 18 at 0.8 or above. The capture runs at wall rate, not game time. Nobody has listened.
Two-player HUD at 352 wide: the P2 health bar and score run to the right edge, no end cap; P1's portrait is cut on the left.
Tools: tools/whole_game_legs.py, tools/capture_stage_clips.py, tools/capture_clip_match.py; BOT_CHAR, BOT_P2/YABA_P2 in saturn/rt/play_full_bot.py and play_yaba.py.
Unproven: the stage 1e hold, two players on this package, three players, any boot outside soft-core Yaba, hardware.

## Constant-address tables per stage, no more tile room than before, alien grab run, 2026-11-08 (lane all; EMULATOR, soft-core Yaba, VideoCore 2 on own instances; HOST analysis; hardware UNRUN)

The 636 pages in every stage file cost sprite keys (stage 06 0 to 595 dropped, 1c 450 to 2327, 24 3070 to 4762). New layout, same fix for the read that faulted, no extra drops:
- tools/const_live.py: a stage keeps the constant-address table pages (page and the page after) of the functions that ran in that stage's census (instruction fetch ranges of the golden runs, sections/*.fetch.txt), plus those of any function that ran in 8 or more stages. 319 to 406 pages a stage; page 0x159 (f_5526a, the grab) is kept in stage 0c and 1c. Stage 0c's census ran f_5526a but not its grab branch, so function level is what catches it.
- tools/rounds_config.py: ROUNDS_CONST_LIVE=json, ROUNDS_PAD_MODE=budget, ROUNDS_FILL_MARGIN=10. Budget mode keeps the census pages without the page either side, adds the page after each own page (most read by other stages first) until the keep list is 10 pages smaller than the pkgG list (census, page either side, shared by 2 stages). Evidence for dropping the back padding: over the 16 readmap runs 2 of 4948 run-time page reads fell in padding that the census pages did not cover (one forward, one backward); forward padding is kept in budget order. Default (no env) is unchanged.
- Package E:\AvP\learning\lane-all\pkgJ\avp_saturn.iso (iso only, 496,470,016 bytes, sha256 6d72281c29f3ddadab13bf786df87787318b8fe311c6de0902f05619e9b543c5; warp image for the tests runW2\warpJ.iso, same keep lists).

Dropped sprite keys, one-for-all file per stage (pkgG before constants, pkgH 636 pages in every stage, pkgJ new):
| Stage | pkgG | pkgH | pkgJ |
| --- | --- | --- | --- |
| 06 | 0 | 595 | 0 |
| 0e | 3047 | 4379 | 2941 |
| 1c | 450 | 2327 | 334 |
| 1e | 1117 | 2742 | 975 |
| 24 | 3070 | 4762 | 3031 |
| all other stages | 0 | 0 | 0 |
All 210 files (20 stage files and 190 character files): none drops more keys than pkgG. Total over the 190 character files 72,912 (pkgG), 144,227 (pkgH), 69,551 (pkgJ). Largest file 3,112,960 bytes (pkgG 3,084,288). The front file restores 583,680 bytes on load (pkgG 479,232). Kernel RAM unchanged (hw_free 17,276, lw_free 4,104, same as pkgG).

ROM view check (tools/diag_romcheck.py, tools/romcheckN.sh, -DSAT_WARP image runW2\warpJ.iso, Warrior, after each stage's load, runW2\rc_*, rcR_*, rcT_*): the stage's own const pages differ from ROM in 0 of 319 to 406 in each of the 18 stages 02 to 24 (26 not run, no spill). The other const pages of the 636 (those of functions that never ran in that stage's census and run in fewer than 8 stages, 82 to 122 a stage) differ in 0 to 97 pages, in the stages that spill tiles into ROM pages (04 06 08 0c 0e 10 18 1c 1e 20 24). So the layout does not keep all 636 in every stage: that needs about 170 more pages a stage than the keep lists held before, and the stages at capacity (0e, 1c, 1e, 24) had none left. Several warp runs hung at boot or at the load and were rerun (stage 10 took 4 tries).

Alien grab, stage 0c section 6, Schaefer, write watchpoint on ff8380+0x1c and +0x1e for 0x4a9, execute breakpoint on f_5526a, read breakpoints on the character table at 0x56632 (tools/diag_wp2.py; states from tools/diag_mkstate.py; runs up to 200 s):
- pkgJ keep lists (runW2\hp9_1): f_5526a entered at v15251, 0 stops on 0x4a9, no FATAL to vblank 18206 (end of the stage 0c section).
- 636-page image (runW\cont4_seed53): f_5526a entered at v13294, then 119 stops at the table read (R0 = 0x2456636, ROM view 0x56636, Schaefer's entry), the player's +0x1c held 0x163220, 0x164f54, 0x164ff4, never 0x4a9, no FATAL to vblank 18780. Also runW\cont_seed13 and cont4_seed51: f_5526a entered, no 0x4a9, no FATAL.
Only a grab that latches reads the table (the old fault came from one): 1 in 3 of the grabs seen. Grabs are about 1 in 10 runs from these states. Unproven: a latching grab on the pkgJ keep lists; other characters; two players.

## Constant-address tables kept in every stage file, checked in the running ROM view, 2026-11-08 (lane all; EMULATOR, soft-core Yaba, VideoCore 2; hardware UNRUN)

Cause of fatal 0xe2 at 0xa9cc4 in stage 0c (an alien's grab, f_5526a, reads the table at 0x56632): page 0x159 was not in stage 0c's keep list, so the lifted code read 0 there, a2 += 0 gave 0x4a9, and 0x4a9 went into the player's animation pointer (ff8380 + 0x1c). Fix c0cfe85 plus d98f04d: tools/const_pages.py lists the 636 pages (1 KB, each with the page after) of tables the lifted code addresses by constant (lea or move #imm into a0-a6, OP or RD of a literal), and ROUNDS_CONST_PAGES makes every stage file keep them. Default is the whole 2 MB ROM (636 pages); the argument c0000 gives 550 and is not used. Package E:\AvP\learning\lane-all\pkgH holds avp_saturn.iso only (sha256 a40aa76eb3366b097df1e822d095375e25d2ea4cef78491ce80f34def0f31ecd); its second, DMA, build failed because another rounds config run rewrote rounds.json under it, not because of the fix. pkgI is the complete package for the 550 list (482,166,784 bytes, 3 MB larger).

What ran. ROM view = what PB() reads (ROMB + address), compared page by page (1 KB) with ROM.BIN by tools/diag_romcheck.py, RAM only read after the one sat_warp write:
| Image and stage | const pages not equal to ROM | other sampled pages not equal (tiles) |
| --- | --- | --- |
| pkgF, diag_l3 state, stage 0c after its load (before the fix) | 120 of 636, page 0x159 among them | 84 of 174 |
| -DSAT_WARP image with the 636 list (same rounds, keep lists patched), stage 0c, Linn | 0 of 636 | 69 of 174 |
| same image, stages 02 04 06 08 0a 0e 10 12 14 16 18 1a 1c 1e 20 22 24, Warrior | 0 of 636 in every one | 15 to 80 in the stages that spill tiles into ROM pages (04 06 08 0e 10 18 1c 1e 20 24), 0 in the others (no spill) |

Stage 26 not checked (no spill, ends at the credits). Not run: Schaefer or Hunter files (all 10 variant files of a stage share one keep list).
The grab itself did not recur on the new image: 3 Linn seeds of about 11,000 vblanks each in stage 0c section 6 (write watchpoint on ff8380+0x1c and +0x1e for 0x4a9, execute breakpoint on f_5526a): 0 grabs, 0 watch hits, 0 fatals (E:\AvP\learning\lane-all\runW\linnL_seed1 to 3). The page check is the proof for the read; the grab on the new image is unproven. A first attempt from the pkgF state on the pkgH disc is void: every round file's start sector differs between the images and the state holds the old directory (runH\s1_vid1_nogame, runH\seed1; it faulted as before).
Cost, 636 pages against none (pkgG against pkgH, one-for-all files): kept pages per stage file +147 to +198 KB (stage 0e 147, stage 26 198); dropped sprite keys 0e 3047 to 4379, 1c 450 to 2327, 1e 1117 to 2742, 24 3070 to 4762, 06 0 to 595 (the 550 list: 0e 4217, 1c 1932, 1e 2392, 24 4302, 06 187); spill in stage 06 5084 to 4608, 0e 5016 to 3912; stage files 10 to 220 KB smaller (tiles dropped), largest 2,861,056 bytes. Every stage still fits: both builds finish with no assertion, image 479,176,704 bytes (pkgH), kernel RAM unchanged (hw_free 17,308, lw_free 4,104, cart_free 5,764 bytes). tools/rounds_variants_report.py was not rerun on the 636 list, so "no key of a character file's own route dropped" is not rechecked.
Coverage: const_pages.py takes direct reads and lea only. The new argument "all" takes every immediate address in the lifted code (7,633 sites, 829 pages, 193 more): it also covers pointers loaded by move.l #imm (script pointers stored into records, 0x1412aa and the like) and lea with an index. Over the 16 readmap runs of earlier packages no page read at run time was missing from the census keep lists, so page 0x159 is the one the list added in practice; 219 of the 636 pages were read in none of those runs. In the running ROM view 2 to 27 of the extra 193 pages differ from ROM in the spill stages. Pointer chains (a table of pointers to data) are covered by the census only.
Tools: tools/diag_wp2.py (seeded bot, watchpoint, grab breakpoint), diag_mkstate.py, diag_romcheck.py, diag_romcheck_state.py, diag_runH.sh, mkstateW.sh, romcheckW.sh.
The grab is run in the next section (pkgJ layout). Unproven: the stage 1e hold (not rerun, may be the same class); hardware.

## Whole game to the ending on the Saturn image, 2026-11-07 (EMULATOR, soft-core Yaba, VideoCore 2, SoundCore 0; hardware UNRUN)

E:\AvP\package-r7, commit 84d6810, avp_saturn.iso sha256 cd2af4acc9bd9ec6b0b4bc1a70b68424e26c38580c1f3bac12bfba66b6ec7c7b, hashes equal before and after the run. Predator Warrior from boot through stages 02 to 24, stage 26 (ship, staff credits, epilogue, GAME OVER) seen on stills, back to attract at vblank 338866. Pad through pad_set, RAM only read. 130 KOs with continues, 0 fatals, 21 loads.
Not one process: 26 five-minute legs joined by save states, because emulated speed falls from about 45 to 12 vblanks/s within 20 minutes and a new process restores it. Cause in Yaba not found; the host was at 19% and two Yaba threads were pegged.
GFS reads all 219 root entries; the kernel selector picked the Warrior file at each stage. Load: 377 to 1529 sectors; 8 to 12 s of wall time on the emulator where read from logs, not Saturn timing.
Fixes: 6 jump table entries the code map missed (fatal 0xe1 at 0x4d698, stage 08; tools/table_gap_roots.py). Side store kept 256 bytes per indexed base, so a byte table at 0x6259a read other bytes for an index no census saw: Smasher's jump row 4 bytes off, it flew away and stage 0a could not end. Tables now run to the next code, up to 0x200 bytes (store 259,542 of 262,144). Longer tables can still lose their tail.
Open: fatal 0xe2 at 0xa9cc4 (word from a sprite script outside the 8-entry table) once in stage 0e on the previous image, at vblank 66509. Same-byte resume passed it and the final run did not hit it; registers never captured. Likely a data read in a ROM page the stage does not keep, not proven.
Not rerun after these changes: host check against the goldens. Unproven: one continuous process, other characters and 2 players on the image, audio in this run (SoundCore 0), the DMA image, IRQ inside split long accesses (no SR masking added, not seen to bite).
