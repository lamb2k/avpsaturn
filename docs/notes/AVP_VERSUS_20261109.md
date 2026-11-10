# Versus mode (Duel), 2026-11-09 and 11-10 (lane versus; EMULATOR, Yaba soft video core on port 9725; HARDWARE UNRUN)

Branch `lane/versus-20261109`, built on `lane/stage-sprites-20261109` (19f87b0). Evidence: `E:\AvP\learning\lane-versus` (logs\, out\<run>\ stills and paused bursts, deliver\ the before and after sheets).
Build: owner recipe (docs/INTEGRATION.md, -DSAT_DUEL_MENU in it) plus the stage-sprites candidate switches `CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1` (their gate set; their char_fuzz.json, cf_final). Judged from paused `framebuffer_burst` captures only (3 frames each), at game seconds counted in vblanks (the host was busy: the emulator ran 2 to 40 fps).

## 1. The three listed issues, re-checked on the current build

| # | Issue | On the current build | Cause | Fix |
| --- | --- | --- | --- | --- |
| 1 | Tile garbage in the RANDOM arenas (0e, 1c, 1e, 24) | **Hazard still there, symptom not reproduced in my runs.** Stage files for 0e/1c/1e/24 (every pair variant, arcade and Wolverine) still overwrite 33 to 44 ROM pages that stage 02's walk reads (tools/pagechk in evidence: 0e 33, 1c 41, 1e 44, 24 40 pages, among them the colour tables 0xffc00-0x1053ff, 0xbf000, 0xcf400-0xd07ff, 0x190800, 0x22000-0x22bff, 0x8cc00-0x8e3ff, 0xa5800-0xa67ff). Plain-file fights of 70 to 100 game seconds drew clean (stock pair on all four arenas; Wolverine pair, aliens high and a second stock run on 1c); the earlier lane's noise blocks (stills6, copied to deliver\1_garbage_before_earlier_lane.png) did not come back. | The duel reads ROM pages that only stage 02's census walk keeps (colour tables, effect and alien frame data); an arena's own file spills sprite tiles into them (rounds_pack free runs). Earlier lane: keeping those pages made 1c clean. | **Duel copies** of the arena files (below). The copies overwrite 0 pages of stage 02's set (checked on all 36). |
| 2 | Linn (P1) vs Hunter (P2): Hunter's body not drawn | **Does not reproduce.** Linn vs Hunter on stage 02 (m_lh_02) and on 0e, 1c, 1e, 24 draws both bodies, glaive and shadow (matrix below). The pair file `stage02_mc` drops 0 sprite keys. | The Duel 4 runs predate the aim fix 7a99ba4 (earlier lane's note); not isolated, and gone. | none needed |
| 3 | The stage's own enemies come in on 1e (aliens) and 24 (soldiers) | **Reproduced** (out\v2_1e_stock_plain: 4 stalkers, STALKER bar, 536% in 50 s; out\v2_24_stock_plain: 9 soldiers, PRIVATE and CORPORAL bars). | Not the 0xff1816 table: the duel parks it, and the logs show `spawner 4` all fight. The bodies are the **tag 12 pool's** (0xff9580, 20 slots of 0xc0): 1e's stalkers are class 0, 24's soldiers classes 08 14 15 1c, placed when the stage starts. `alien_cull` parked only class 0x1f (stage 02's doors) and the stage's tag 4 alien classes. | duel_smash.inc `alien_cull`: every live body of the tag 12 pool (+8 = 0x0c) is parked 400 px left of the arena each tick (the duel's own aliens are in the tag 20 pool). 1e and 24 fights of 70 s: 0 enemy bodies in play, kills 0 (out\v3_1e_stock_duel, v3_24_stock_duel, ENEMY log lines). |

## 2. What was built

- **Duel copies of the arena stage files** (saturn/rt/build.py `duel_plan`, kernel.c `duel_pairs`). For stage words 0e, 1c, 1e and 24 every pair variant (6 pairs) and every Wolverine pair variant (3) gets a second file, `<name>_d`, appended after the existing files (no file number moves), with the same keys, ranks and sound, but also keeping every ROM page stage 02's file keeps (952 pages of the 1 KB pages). While a duel is on (`sat_duel_on`) `round_check` loads the copy; normal play, stage select and boss rush keep the plain files, so the main game loses nothing. 36 files.
  - `DUEL_FILES=0` builds without them (A/B). `sat_duel_plain` (a test byte, 0 in play, poked by tools/play_versus.py PLAIN=1) makes a duel use the plain file again, for a before and after on one disc.
  - Cost with CHAR_FUZZ_KEYS=1: +111.5 MB of round files (ISO 525,490,176 against 413,093,888), **sector store 254,398 of 262,144 sectors** (the stage-sprites build alone: 199,518), hw_free 996, lw_free 60, cart_free 4,228. Each copy asks the same keys and drops 283 to 526 more of the (all four characters') candidate keys than its plain file (it has 264 to 350 fewer spill tiles because it avoids the pages); every file is capacity limited either way (census keys alone are 17,000 to 18,500 tiles against 14,700 to 16,300 stored).
  - Tight on the store. Cheaper form, described and not built: a `DUEL_FILES=inplace` switch (about 8 lines in `duel_plan`: add the keep set to the pair files' own `keep_pages` and make no copies) would put the same keep set into the pair files of those four stages themselves: 0 extra sectors, and 2 player arcade play on 0e, 1c, 1e, 24 then drops the same 283 to 526 keys the copies do.
- **Duel HUD and NOW LOADING** (home.c `sat_home_commit`, duel_smash.inc, kernel.c): since the menus draw from `sat_home_shown` (bc8e8fb, 11-08) only a menu loop's `sat_home_frame` copied text to it. The duel's percent and stock line (written each tick) never reached the screen, and "NOW LOADING" stayed in the corner for the whole fight (every duel on the integration build; out\base1c_ww). `sat_home_commit()` publishes the text without waiting for a vblank; `smash_hud` calls it each tick, `sat_home_loading(0)` calls it. Before and after: deliver\2_hud_before_after.png.
- **ARENA row back** in the duel menu (home_cold.c): ROUND 1 or RANDOM over stage words 02, 0e, 1c, 1e, 24 (138bdf1 had removed it, the arena code left dead). `sat_duel_force_arena` (a byte, 0 in play) is the test hook that picks a stage word without the menu.
- **Stage enemies parked in every arena** (above).
- Tools: tools in saturn/rt: `play_versus.py` (arena, pair, guest, paused bursts, enemy and record dumps; wraps play_smash.py), play_smash.py (title item, select order, KEEPDEPTH), play_yaba.py (window title).

## 3. Pairings

Every pairing of the four stock characters (guest off, `GUEST=0`) and of Wolverine (Schaefer's slot, `GUEST=1`) with each of the other three, once, on each of the five arenas (ROUND 1 = stage 02, then 0e, 1c, 1e, 24): 9 pairs x 5 arenas = 45 runs, P1 first. Each run: the real title menu, VERSUS, the game's select screen with both pads, a fight of 44 game seconds, two paused bursts of 3 frames (about 22 and 40 s), the bot trading hits and gun shots. All 45: fatal 0, the right two characters on the select (checked from the player records, `CHARS d2`), HUD names right, percent and stock line drawn, both bodies drawn, no stage enemy, no wrong-tile blocks. Sheets: deliver_matrix_arena_<arena>.png (one frame of each of the 9), deliver\matrix.tsv, out\m_<pair>_<arena>\ (stills and bursts), logs\m_<pair>_<arena>.log.

| P1 vs P2 | 02 | 0e | 1c | 1e | 24 |
| --- | --- | --- | --- | --- | --- |
| Warrior vs Schaefer | ok | ok (b) | ok | ok | ok |
| Warrior vs Hunter | ok | ok (b) | ok | ok | ok |
| Warrior vs Linn | ok | ok (b) | ok | ok | ok |
| Schaefer vs Hunter | ok | ok | ok | ok | ok |
| Schaefer vs Linn | ok | ok (b) | ok | ok | ok |
| Linn vs Hunter | ok | ok (b) | ok | ok | ok (c) |
| Warrior vs Wolverine | ok | ok (b) | ok | **ghost (a)** | ok (c) |
| Linn vs Wolverine | ok | ok (b) | **ghost (a)** | ok | ok |
| Hunter vs Wolverine | ok | ok (b) | ok | ok | ok |

- (a) **A second fighter for a few frames** (deliver_open_ghost_second_fighter_seen_twice.png): Linn vs Wolverine on 1c shows a gold Schaefer shaped figure at Linn's place beside the real Wolverine (it stays in two bursts and the end still, so some seconds), and Warrior vs Wolverine on 1e a half hidden second Wolverine behind the Warrior. 2 of the 15 Wolverine arena runs. **It is not the duel files or this lane's changes:** the integration disc with plain files (the first baseline run, 1c Warrior vs Wolverine) has the same second Wolverine beside the Warrior (logs\sheet_base1c.png, middle top), and four repeat runs on 1c and 1e (plain and copy, with record dumps: P3's record is empty, no extra body record near the fighters) did not show it. Both ghosts have the P2 slot's art at P1's place. Not isolated; the Wolverine guest draw pass (guests.c, wolverine.c: it replaces every palette 1 object by place) is the first suspect. Passed to the Wolverine lanes.
- (b) 0e: both fighters sit on the stage's lowest floor line, at the very bottom of the picture, so only the heads or feet show in the captures (the bot closes in on the other's depth and both drift down; the game's own limit, not a draw fault). Schaefer vs Hunter shows both whole. The sprites that show have the right colours and the HUD names are right.
- (c) 24: the scenery figure at the right edge (section 4).
- Stage 02 only: the first 8 s of every duel are the stage's own opening (aliens through the fence, a talk box "Why are you helping us?"), before the arena locks (g_ww_02_gun). Not touched.


## 4. Other things found (not all fixed)

- Duel fighters walk below the picture on 0e and 1c when both keep closing in on each other's depth: they sit on the stage's lowest line, below the HUD bars, so only shadows show. The game's own floor bound, not drawn wrong; the bot now holds depth (KEEPDEPTH).
- "GO" arrow: the stage's scroll prompt flashes in 1c and 0e once no enemy is left alive (seen in the stills, not on 1e and 24 where parked bodies stay allocated). Cosmetic, not fixed (the flag is not 0xff8239; found no cheap one).
- Stage 24: a scenery actor (a tag 0x18 record, class 3, 0xffc180) stands at the right edge of the picture the whole fight. Not an enemy, not parked.
- The enemy bar can still show faintly over the percent row (the clear panel rows are translucent since the option screen change): "Maj. SC" over "0%". Cosmetic.

## 5. Gates

- Build (owner recipe + CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1, work dir a copy of integration\w1, char_fuzz.json of the stage-sprites lane): full round files rebuild 2,836 s on the busy host, rc 0, no NO-GO, **hw_free 996, lw_free 60, cart_free 4,228**; sector store 254,398 of 262,144 sectors; ISO 525,490,176 bytes. Later kernel-only rebuilds (HUD, parking, arena row) keep the round files (hw_free 996, lw_free 60 each).
- tools/wolverine/fit.py on a copy of D11 (FIT_GFX_GUEST and FIT_GFX_FRONT from the build): 77 rows (76 stage rows and front_wv), **gate True, 0 Wolverine own keys dropped, 0 missing guest keys** (deliverit.log).
- tools/check_round_pages.py: **PASS, 0 of 323** round files break the page rule (the 36 copies keep stage 02's pages and overwrite none of them); tools/check_screen_keys.py PASS 0 of 323; tools/check_caption_keys.py 323 files, short 0.
- WSL `python3 -m unittest discover -s tests`: 131 run, 30 errors, 0 failures, 1 skipped. The 30 are the known private-dependency errors (`No module named capstone`, the accepted decrypted opcode image and its .deps files missing), none in a file this lane touched.
- Yaba (emulator): 45 pairing runs plus about 25 diagnostic runs, fatal 0 in all. Hardware unrun.


## 6. Switches and notes for the stage-sprites lane

| Switch | Default | Effect |
| --- | --- | --- |
| DUEL_FILES | on (copies) | 0 builds without them (A/B); an `inplace` form is described in section 2, not built |
| sat_duel_plain, sat_duel_force_arena | 0 | test pokes (bot only) |

No file of the stage-sprites lane changed except saturn/rt/build.py (a new `duel_plan` after `guest_plan` and one line in the rounds.inc writer); tools/rounds_pack.py, tools/char_fuzz.py and the packer are untouched. If the lane changes the keep rule, the copies follow it (they copy the plain file's keep_pages).

## 7. Not done

- Hardware: unrun. Emulator speed under the busy host was 2 to 40 fps, so no frame rate was measured.
- Not seen: the earlier lane's noise blocks on the current build (neither plain nor copy). The claim is structural (0 of 36 duel files touch a stage 02 page) plus clean 70 to 100 s fights.
- 3 or 4 player files, timed mode and sudden death on the arenas, the Wolverine ring-out in an arena, the GO arrow.
