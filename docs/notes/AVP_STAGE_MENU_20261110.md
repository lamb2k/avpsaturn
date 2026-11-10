# Stage select names and the ENDING entry, 2026-11-10 (lane stage-menu; EMULATOR Yaba VideoCore 1, own copy port 9727; hardware UNRUN)

Branch `lane/stage-menu-20261110` on avp/integration e0c8848. Build: the owner recipe (docs/INTEGRATION.md). Evidence `E:\AvP\learning\lane-stage-menu` (ev\ captures and logs, build logs, ym.py/walk.py/endrun.py drivers); scratch work dir `D:\AvP-lanes\lane-stage-menu\w`.

## 1. Readable stage names

The arcade has no area names. What the game itself holds:
- 7 STAGEs. The round byte ff8222 is set from a table at 0xcca0 (one word per stage word, 00 to 24) when a stage clear advances the stage word; the stage-clear card prints "STAGE" + (ff8222 + 1) (code 0xac64c: `move.w $222(a5),d0 / addi.w #$31,d0`) and the boss name from a 16-byte table at 0xac6c8, indexed by the round.
- Boss names (data read of 0xac6c8): CHRYSALIS, RAZOR CLAWS, ARACHNOID, ALIEN QUEEN, POWER LOADER, MAD PREDATOR, ALIEN QUEEN.
- The text table at 0x11a870 has "SPECIAL STAGE" / "BREAK CONTROL BOX!" (messages 47, 48), printed by the controller of stage word 14 (controller table 0x1bdf0, code 0x2c3c4 to 0x2c74c; the message calls are at 0x2c452 and later).

So the menu shows `STAGE n-m`: n the round + 1, m the area's order inside the round. The last area of a round is its boss (home.c's rush comment, and the controller list), shown in a second row as BOSS + name; stage word 14 shows BONUS + SPECIAL STAGE.

| Menu | Stage word | Shown | Second row |
| --- | --- | --- | --- |
| 1 | 02 | 1-1 | |
| 2 | 04 | 1-2 | BOSS CHRYSALIS |
| 3 | 06 | 2-1 | |
| 4 | 08 | 2-2 | BOSS RAZOR CLAWS |
| 5 | 0a | 3-1 | BOSS ARACHNOID |
| 6 | 0c | 4-1 | |
| 7 | 0e | 4-2 | BOSS ALIEN QUEEN |
| 8 | 10 | 5-1 | BOSS POWER LOADER |
| 9 | 12 | 6-1 | |
| 10 | 14 | 6-2 | BONUS SPECIAL STAGE |
| 11 | 16 | 6-3 | |
| 12 | 18 | 6-4 | |
| 13 | 1a | 6-5 | BOSS MAD PREDATOR |
| 14 | 1c | 7-1 | |
| 15 | 1e | 7-2 | |
| 16 | 20 | 7-3 | |
| 17 | 22 | 7-4 | |
| 18 | 24 | 7-5 | BOSS ALIEN QUEEN |
| 19 | (24, ending) | ENDING | THE LAST BOSS IS CLEARED FOR YOU (row 3) |

Font and layout unchanged (sub(), label/value rows, ROW(0) and ROW(1); the widest value is "SPECIAL STAGE", 13 letters from column 23). The pick also sets the round byte (ff8222 = round) so a warped stage has the value the arcade's own advance would have set; before, ff8222 stayed 0 whatever stage was chosen (the card's STAGE n and boss name read it). It persisted through the load in Yaba (rnd 6 on stage word 24).

Captures (paused): `ev\sel_01.png` (1-1), `sel_10.png` (6-2 SPECIAL STAGE), `sel_18.png` (7-5 BOSS ALIEN QUEEN), `sel_19.png` (ENDING), and the whole run sel_01 to sel_19.

## 2. ENDING entry

Cause of fatal 0xe2 at 0x91ec on stage word 26 (reproduced on the unmodified integration build, `ev\base26.log`: warp to 0x26 at the stage select, `fatal 226 detail 37356` = 0x91ec):
- 0x91e4 is the game's per-stage setup, run in the play mode's setup state (ff8004 = 4, ff8008 = 0, ff800c = 56). It jumps through a table of words at 0x91f0, one per stage word 00 to 24 (19 words). Word 26 reads the 20th word at 0x9216, which is code (`0x546d`, an `addq.w #2,12(a5)`), not a table entry, so the jump goes to 0x91f0 + 0x546d, an odd address no stage table holds: BADJUMP in the lift. On the board it would run garbage.
- The arcade never starts word 26 through that path. The stage 24 clear (0xcbd0 to 0xcc04) does `addq.w #2,$1e8(a5)` (word 24 to 26), calls 0xcc94 (which reads the round table past its end: ff8222 = 0x302d, 12333) and jumps to 0x8836, which sets ff8004 = 0a (the ending sequence, dispatch 0x14bd8) and clears the player blocks' states. The ending never runs the stage setup.
- Not the cause: a ROM page missing from the stage-26 round file (the file loads; the ending shows its pictures), score or player state. The round byte after the clear is 0x302d in the real flow too (the reveal lane's card has the same).

Fix: the ENDING entry does not start word 26. It starts the stage 24 arena (the stage select's entry 18 path, which starts at the boss) and, once the arena's play state runs (ff8004 = 4, ff8008 = 4) and the arena's stage file has loaded, sets the boss-down flag ff822a and the stage-clear flag ff81f3, the two flags the arena's controller sets itself when its boss dies. The game's own state machine then does the rest: 0x840a moves ff8008 to 6, stage 24's clear handler (0xcad6 to 0xcbfc) plays, adds 2 to the word, 0xcc94, 0x8836, and the ending runs from its own start. `sat_home_ending` (home.c, `ending_poll`, `sat_home_arm_ending`) holds the entry; the stage select arms it with the stage file load count so a stale load cannot release it early (first try compared too late and never fired, `ev\end3.out`). It clears at the title.

An earlier version only wrote ff822a 600 vblanks into the fight: the controller then waited for its wave script and the boss (class 0x26 with four class 0x11, 512 health) and cleared about 4000 vblanks later (`ev\pool2.out`, `end4.out`); writing ff81f3 in the play state clears at once (about 40 s of Yaba time of loading, 30 vblanks of play).

State at the reveal lane's card: it hooks stage word 0x26 with ff8005 = 8. The flow from the entry is the arcade's own, word 0x26 and ff8004 = 0a through the ending and credits, then 8 at the GAME OVER card (state sequence in `ev\endB.log`: word 36 sub 4, st8 6 (clear), word 38 sub 10 (ending), sub 12, then the title). The only difference from a played clear: the boss was not killed by the player (score 0 for the boss, no kill animation), and the controller's own sequence before the flag is skipped. Not run: the reveal lane's hook itself (not merged here).

Runs (Yaba, own copy, soft-core off VideoCore 1 as the other lanes, pad by PostMessage to my window only):
- Warrior, default pick (`ev\end5.log`, `end5_*.png`, `end5_sheet.png`): word 24 arena, clear, word 26, ship scenes, credits, "See you soon", epilogue text, BEST 50 HUNTERS ranking, title. No fatal.
- Wolverine, two Rights at the select (`ev\endB.log`, `endB_*.png`, `endB_sheet.png`; the HUD plate in `endB_plate.png` reads Wolverine): same path with the GAME OVER card (`endB_*` frame with "GAME OVER") before the ranking, then the title with the new PRESS START line. No fatal. Played from a fresh start, one player.
- A normal area start still works (`ev\area18.log`): stage select 18 (7-5, word 24, round byte 6) loads, reaches the play state (st8 4), ending flag 0, nothing cleared for it.

## 3. Owner requests added to this branch

- "remove the non-transparent layer from sub-menu overlays": no change was needed on this head. `sub()` fills the cells with glyph 1, but the menu layer draws glyph 1 as a clear cell for modes 3 and 4 (sat_gfx.c draw_home, `ch == 1 ? snap.home >= 3 ? 0 ...`; only the pause menu, mode 1, gets the translucent panel), and each letter has a 1 px halo. Paused captures before and after (`ev\before_*.png`, `after_*.png`, `sub_before_after.png`): OPTION MODE, GAME OPTION, SOUND TEST and SCREEN ADJUST pixel-identical (difference box none), title art visible behind the text in both. The black around the logo is the title picture's own background. Legibility: rows over the logo's orange lower half (CONTINUE, LIVES, EXIT on GAME OPTION, "PAD MOVES A CENTRE" on SCREEN ADJUST, "A PLAY C STOP" on SOUND TEST) are readable only through the halo; they are the weakest. Stage select stays mode 2 (black picture while the game is held), as asked.
- "first screen should say PRESS START": the boot title's "PRESS START BUTTON" with "ONLY ONE PLAYER" under it is the game's title message 2 (messages 3 and 4, "UP TO TWO / THREE PLAYERS", are the same lines for more credits), drawn by the big text writer 0xabbae that kernel.c already replaces in home builds. For messages 2 to 4 it now draws the first 11 letters of message 2's PRESS START BUTTON record (same row, palette and font) moved from column 6 to 13, centred, and no second line. No ROM bytes patched, nothing ROM-derived in git. The per-player PRESS START (messages 8 to 10) and every other message are untouched. Captures: `ev\boot_before_after.png`. Cost: kernel.c +96 B high RAM text. Not changed: the arcade build (SAT_HOME only).

## 4. Memory and gates

Same recipe, same asset set. hw_free / lw_free / cart_free:

| Build | hw_free | lw_free | cart_free |
| --- | --- | --- | --- |
| integration e0c8848 (base.log) | 964 | 60 | 4340 |
| stage names + ENDING (new3.log) | 788 | 60 | 8020 |
| + PRESS START (final, new4.log) | 692 | 60 | 8020 |

cart_free moved because the cold code moved and the round files were repacked around it (479 runs against 492, round sectors 332,553 against 332,673); the ISO is 386.2 MB against 391.5 MB.

- Build rc 0 (first build 2,069 s, the pack cache needs `disc\` in the work dir; later builds 22 to 27 s).
- `tests/home_stage_menu_test.c` (new: the name table against the game's, the row-2 text, the ENDING poll) and `tests/home_lives_test.c`: PASS (WSL gcc).
- tools/wolverine/fit.py (POSE_KEYS=0, FIT_GFX_GUEST/FRONT from the build's gen/hud, assets copied to scratch): 76 of 76 stage files and the front file pass, gate True, fail [] (`fit.log`).
- check_caption_keys: files 287, short 0. check_screen_keys: 0 stage files missing keys (the script on this branch indexes rounds.json's 210 names and fails on the 77 Wolverine variants unless padded; padded run: 285 stage files pass, the one reported file is `front_wv`, which the script skips only when named "front"). check_round_pages is not on this line (it and WORK/round_keep.json come with lane/stage-sprites); not run.
- WSL unittest: Ran 106, errors 30, skipped 1, same as the baseline before the change (`unittest_base_full.log`, `unittest_new.log`).
- HOST goldens clean, missed IRQ 0: r1s 15618, full 317908, c1 272171, c2 369051, c3 333669, 2p 329918 (`host.log`, `host2.log`; c3 and 2p were rerun after WSL was shut down mid-run). The goldens do not include the home code.
