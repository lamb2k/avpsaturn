# Stage sprite store: next-stage load-window keep, 2026-11-11 (lane sprite-store; HOST + offline pack replay + EMULATOR Yaba; hardware UNRUN)

Branch lane/sprite-store-20261111 on avp/integration d0540c8 (the evaluation tree merges native 97de971 into it: throwaway branch wip/sprite-store-eval-20261111, local). Switch: `STAGE_WINDOW=1` (build.py environment, default off) with `STAGE_WINDOW_PAD=2`.
Evidence: E:\AvP\learning\lane-sprite-store: builds wd_base (baseline), wd_n1, wd_n2 (final), wd_n2kl (final + SAT_KEYLOG, for Yaba), wd_win and wd_f2 (tree A without the native 97de971); logs b_*.log, fit_*.log, hostn2\ hostf2\ hostwin\ hostneg\, trans\ (Yaba),
headroom_*.log, unseen_*.json, fuzz runs fz\s16c0 to s21c3, harness\ (trans2.py, ys.py). All ROM-derived data stays outside git. Disk: DELETED.txt there lists the work directories removed.

## 1. Baseline (task 1)

Two trees, both built with recipe A of E:\AvP\learning\integration\run3ab2.sh (3h + ESSENTIALS remap + FONT_COLD + FPS_HUD), D12 assets, `CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 CHAR_FUZZ_KEY_STAGES=`, rowtrim 2:
- **Tree A** = avp/integration d0540c8 as it is (code of 5e49c52; native block 23,116 bytes, cold1_at 0x27df000). My default-off build of the lane head (`def`) is the integration lane's build of 5e49c52 (b_3A2): the 287 round-file stat rows are all equal,
  STORE.BIN is byte-identical, and the ISO differs in 3 of its 154,000 sectors (16, 18, 23: volume descriptors with the build date).
- **Tree B** = tree A with lane/wv-native-gfx-20261109 97de971 merged (throwaway branch wip/sprite-store-base-20261111 9eefb36, merge clean, no conflicts). **This is the baseline asked for.** Native block 20,944 bytes, **cold1_at 0x27e0000** (the step is back, as on disc 3h),
  cart pack room 1,622,016 (tree A 1,617,920). rc 0, no NO-GO, hw_free 2,136, lw_free 96, STORE 152,080 sectors of 262,144, ISO 316,149,760 bytes.

Dropped sprite keys, stage 0e (the only stage with drops; the four Wolverine files `_wv` of every stage drop 0 in all builds here):

| File | disc 3e | disc 3h (9fff850) | tree A (5e49c52) | **tree B = baseline (97de971 merged)** |
| --- | --- | --- | --- | --- |
| stage0e (3 or 4 players) | 179 | 243 | 323 | **265** |
| m1 Warrior | 224 | 304 | 480 | **360** |
| m2 Schaefer | 235 | 347 | 441 | **374** |
| m4 Hunter | 267 | 351 | 434 | **366** |
| m8 Linn | 244 | 356 | 439 | **372** |
| m3 | 254 | 349 | 393 | **360** |
| m5 | 282 | 335 | 431 | **362** |
| m9 | 275 | 329 | 423 | **355** |
| m6 | 244 | 279 | 328 | **300** |
| ma | 204 | 245 | 300 | **259** |
| mc | 223 | 292 | 377 | **320** |
| total, 11 files | 2,631 | 3,430 | 4,369 | **3,693** |

The native lane's 4 KB recovery takes tree A's 4,369 back to 3,693, not to 3h's 3,430: 0e is still above 3h. The cost left over is the remap's 328 tiles per file and the rest of what merged since 3h. Every other stage drops 0 (build log `dropped_keys`).

## 2. Load-window keep (task 2)

A stage file keeps the ROM pages its own stage reads, the front end's and the **whole next stage's** (tools/rounds_config.py), each with a page either side, because the Saturn kernel loads a stage file only
after the stage word has held 12 vblanks (saturn/rt/kernel.c round_check) and the game runs those frames on the old file. Pages a file keeps cannot take tile spill. Stage 0e keeps 1,177 of the ROM's 2,048 pages this way (1,181 with the fuzz script pages).

`tools/stage_window.py` replaces the next-stage term with the pages read in the first 45 frames after the stage word changed (tools/rounds_fuzz.lua `ROUNDS_WINDOW=45`, 3.75 times the 12 vblank hold),
unioned over every census run that has window files, with `STAGE_WINDOW_PAD` (default 2) more pages of margin either side of each window page. The next stage's own file restores whatever the old file spilled over
(the existing restore machinery: `back = written & keep - own`). Data: `WORK/stage_window.json` (tools/stage_window.py WORK CENSUS RUNDIR...), 28 run directories in the final build (runs per stage word: 28 for 02 to 06, 24 for 0a to 10 including 0e, 20 for 14 to 22, 18 for 24, 13 for 26).
The old rule is recomputed from the census (lane-chars/census.json plus the KO and continue pages) and has to reproduce rounds.json's keep_pages exactly for all 209 files, else the tool refuses. The fuzz page rule (char_fuzz.augment `window=`) uses the same window.
A stage without window data keeps the whole next stage (none of the 20 stages lacks data). Default off: with the switch unset every code path is the one before (the identity above).

Pages freed per stage file (pad 0 / pad 2): 0c 49 / 14, **0e 183 / 176**, 1e 125 / 80, 1c 17 / -7 (pad 2 keeps more than the old rule there, harmless), 24 20 / 7, of about 1,000 to 1,180 kept.

### Per-step drop tables (build log `dropped_keys`; tiles = in main + spill in stage0e)

| Step | Tree | Build | 0e drops (11 files) | stage0e tiles | STORE sectors | ISO bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | A | integration as is (def) | 323 to 480, total 4,369 | 22,460 | 151,962 | 315,910,144 |
| 1 | A | STAGE_WINDOW=1, pad 0, same fuzz data (win) | **0 in all 11** | 22,715 | 139,147 | 289,665,024 |
| 2 | A | pad 2, fuzz seeds 16, 17 merged (f1) | 0 | 22,797 | 158,898 | 330,115,072 |
| 3 | A | pad 2, seeds 16 to 19 merged (f2) | 0 | 22,826 | 150,607 | 313,135,104 |
| 0 | B | **baseline: 97de971 merged** (base) | **265 to 374, total 3,693** | 22,503 | 152,080 | 316,149,760 |
| 1 | B | STAGE_WINDOW=1, pad 2, same fuzz data (n1) | **0 in all 11** | 22,715 | 140,179 | 291,776,512 |
| 2 | B | **final: pad 2, seeds 16 to 19 merged (n2)** | **0 in all 11** | 22,826 | 147,054 | 305,856,512 |

Every other file drops 0 in every step; hw_free 2,136 and lw_free 96 are the same in all (the switch touches no kernel code). The four fuzz seeds add 111 tiles to 0e (22,715 to 22,826) and 465 to 1c (21,525 to 21,990 on tree B).
Total restore bytes in the 287 round files: 41.8 MB baseline, 32.8 MB with the window (files no longer restore pages they do not keep), 35.1 MB final.

Offline replay of the packer (tools/stage_headroom.py, **replay, not a measurement**: it leaves out the home caption and edge keys, which is why the base 0e shows 5 dropped keys here against 265 in the build; KB of cart room still free in the file):

| File | base data, no window | final data (seeds 16 to 19), no window | final data, window pad 2 |
| --- | --- | --- | --- |
| stage0c | 337 | 337 | 425 |
| stage0e | 3.1 KB, 5 keys dropped | **149 keys dropped** | **157.8 KB** |
| stage1c | 200 | 200 | 199 |
| stage1e | 239 | 239 | 330 |
| stage24 | 150 | 150 | 156 |

The window is what lets the new fuzz seeds into 0e: without it they would take 149 more keys out of the replay (about 410 in the build).

## 3. Gates on the final build (n2: tree B, window pad 2, seeds 16 to 19)

- fit.py (copy of D12, FIT_GFX_GUEST/FRONT, FIT_DIALOG_KEYS, STAGE_WINDOW=1): **76 of 76 stage rows and front_wv gate True** (77 rows), 0 Wolverine-own keys dropped, 0 missing guest keys, Schaefer and Wolverine variants drop 0 everywhere
  (baseline tree A fit.py on the same inputs without the window: the 0e Schaefer variants drop 284 / 302 / 251 / 214).
- check_round_pages: PASS 0 of 287 (813 pages are tile spill somewhere); check_screen_keys: 0 of 287; check_caption_keys: 287 files short 0.
- HOST goldens with garbage (0xA5) in every ROM page the built keep list of the loaded file does not hold (ROUNDS_SWAP from round_keep.json) and the dropped-page read watch (ROUNDS_SWAP_TRAP): **all six clean**: r1s 15,618, full 317,908, c1 272,171, c2 369,051, c3 333,669, 2p 329,918 of the same count, 0 dropped-page reads, missed IRQ 0 (hostn2/; 4, 21, 21, 21, 21, 16 file loads simulated at the kernel's 12 vblank hold).
- WSL unittest discover: 162 run, **30 errors (the known private-dependency set: oracle and spec02 modules, the same 30 test names as the run before the change), 0 failures**, 2 skipped. New: tests/test_stage_window.py (9 tests), tests/test_char_fuzz.py +1 (`--add`).
- STORE: 147,054 of 262,144 sectors (final); 158,898 at the largest step (tree A, step 2).
- Default-off identity: above (`def` equals the integration lane's 5e49c52 build, round file for round file).

The same gates also passed on tree A's final (f2: fit 77/77, checks 0, six goldens clean with 0 dropped-page reads, `hostf2\`) and on step 1 (win: fit 77/77, checks 0, six goldens clean, `hostwin\`).

### Is the host check sensitive to the window? (negative controls, hostneg\ and swap_neg*.txt)
- The window-only pages (read in the first 45 frames of the next stage and by neither the old stage nor the front end) made garbage in every file's keep list: golden_c1, c2, c3 and full diverge at the **24 to 26 transition** (RAM difference one frame after the stage 26 file swaps in; vblank 268,525 of golden_c1), clean at every earlier transition.
  So the window pages are read in the hold in at least one real transition and the data must be right; golden_r1s and golden_2p stop before that transition.
- 15 of stage 04's own exclusive pages made garbage: DROPPED PAGE READ rom 100000 page 400 (stage file 4) at vblank 5483, 30 frames after the stage 04 file swapped in (golden_r1s). The harness catches a read of a page the file does not keep.

### Saturation of the window data
Pages new to the union per added run (16 runs for 0e, 12 for stages 14 to 26): 0e 87, 3, 2, 3, 0, 0, 0, 1, 0, 3, 0, 0, 0, 0, 0, 2; the late additions are one to three pages and
almost all within a page of a known one (new pages not covered by the previous union padded by one page: 0e 1, 2, 1 over runs 8 to 16; 24 2, 2, 2). Hence `STAGE_WINDOW_PAD=2` (the cost is 7 of the 183 pages freed in 0e).
The risk that remains is a page read in the first 12 vblanks of a stage entered by a route the 24 runs did not take (a different predecessor than the next stage in the census order, as in the home BOSS RUSH, which already jumps 04, 08, 0a, 1a, 24 with the old rule too).

## 4. Stage change evidence (Yaba)

Disc: n2kl = the final build n2 plus `-DSAT_KEYLOG` (same keep lists and packs: round_keep.json and round_stats.json are byte-identical to n2; hw_free 2,064). Emulator: my own copy of yaba-mcp-sdl (E:\AvP\learning\lane-sprite-store\yaba), `General\UseSh2Cache=false`,
SoundCore 1, Volume 100, MCP port 9740, started SW_SHOWNOACTIVATE, window "AvP SPRITESTORE: ...", PostMessage input only, no focus calls. Warrior, home warp to the stage. EMULATOR evidence (not console).

Why not "play the stage to its end": a random-input bot needs the 16,000 frames (0c) or 40,000 (0e) the MAME fuzz runs took, at 10 to 17 emulated vblanks a second here: more than 40 minutes a stage, and two of those sessions hung (below).
Instead (harness/trans2.py): enter the stage, let it run 900 vblanks, pause, set the clear flag ff81f3 (the flag the arcade sets at the boss's death; the stage's own controller then runs its clear and writes the next stage word itself:
probe_clear.py, 0c ends 1,140 vblanks after the poke), then 30 frame bursts with a save state before each. When the word changes, the state two bursts earlier is loaded. From that one state, each variant steps the same frames and logs per step the vblank,
stage word, round file, md5 of the 64 KB game work RAM, sprite objects and commands, and the bitmap of sprite keys asked (KEYLOG):

| Variant | What differs from A |
| --- | --- |
| A | the build as is (tile spill in the pages the window rule freed) |
| A2 | nothing (repeatability) |
| R | every page the old file spilled tiles over holds the ROM's own bytes (disc/ROM.BIN): the game reads what the old rule would have kept |
| Z | **every page the rule freed** (the next stage's census pages the old file does not keep for any reason) holds 0xA5: the worst case, all of them garbage |
| Q | control: all of the next stage's own census pages that neither the old stage nor the front end read hold 0xA5 |

Identical work RAM, objects, commands and key bitmaps for every step means the game never used a page the rule gave away during the stage change.

| Leg | Old file | Spill | Pages freed (Z) | Window pages kept only for the next stage | Q pages | Steps | Word changes | File load starts | Result against A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0c to 0e (prev to 0e) | stage0c_m1 (file 70) | 9 regions, 440 KB | 35 | 74 | 63 | 88 | step 7 (vb 3,794 to 3,804) | vb 3,816 (12 vblank hold), file 80 loaded at step 57 | A2, R, Z, Q: **work RAM equal at all 88 steps, objects and commands equal, key bitmaps equal** |
| 0e to 10 (0e to next) | stage0e_m1 (file 80) | 25 regions, 710 KB | **176** | 12 | 159 | 84 | step 7 (vb 4,542 to 4,552) | vb 4,561, file 90 loaded at step 53 | R, Z, Q: **equal at all 84 steps** |

Sprite keys asked before the file load (KEYLOG, from the saved state to the start of the load): 0 in 0c to 0e, 2 in 0e to 10; **absent from the old file: 0** (so no piece drew blank in the hold). Asked in all, to 30 frames after the load: 32,332 and 32,589 (the new stage's first uploads), equal in every variant.
Q equal to A means the game does not read those next-stage pages in the hold in these two transitions either; it is the host neg control (above, 24 to 26) that shows a transition where it does. The in-state test has no variant that differs, so it shows no sensitivity of its own;
its value is the Z result: with 176 pages of the 0e file's freed pages garbage, the 0e to 10 change is bit for bit the same.
Paused frames (A, single steps through the hold, the NOW LOADING screen and 30 frames after the load): E:\AvP\learning\lane-sprite-store\trans\n2kl_0c_0e_10\leg_0c_0e\A_008..022, 058, 063, 087.png and n2kl_0e_10r\leg_0e_10\A_008..019, 054, 059, 083.png.
Looked at: A_012 of 0e to 10 (Warrior and a Xenomorph drawn whole on the 0e screen as the word changes), and 0c to 0e A_008, A_015, A_022 (NOW LOADING), A_063 and A_087 (the new stage's fade-in with its HUD); nothing blank, no wrong tiles.

Limits: two legs (0c to 0e is the "prev to 0e" load, 0e to 10 the "0e to next"), one character, the clear started by the flag poke and not by a boss kill (the stage's own clear code runs from there), emulator only. Not run: 1c, 1e, 24 legs (the MAME window data has 12 runs for them),
the BOSS RUSH transitions that skip stages (04 to 08, 08 to 0a, 0a to 1a, 1a to 24: the old rule did not keep the target stage there either, so the window rule does not make them worse by construction, but they were not run).
Harness stalls (not isolated, listed because a stall can also be a game fault): three Yaba sessions stopped answering. (1) the first approach (periodic pause, save_state, resume every 3 s while a bot played 0c, tree A disc): the master spun in the BIOS with SR=0xF0 (PC 0x6004B5A, registers constant)
at vb 21,988 with no file load running, fatal word 0; (2) the first session on the final disc, in the burst and save loop of the 0e to 10 leg after the 0c to 0e leg had finished (an MCP call that never returned, Yaba stopped between bursts and answering other calls); (3) the next session of that leg,
after variants A and A2, as R began (same picture). None repeated in the final sessions (88 and 84 steps, five and four variants).
Harness changes after them: no periodic saves, a heartbeat watchdog that exits after 240 s, and RESUME_SLOT to continue from a saved state in a new session; the 0e to 10 leg was run that way from the state its first session had saved (slot 5).

## 5. Fuzz seeds (task 3)

Runs: seeds 16 to 21, one MAME run (tools/rounds_fuzz.py, ROUNDS_WINDOW=45 ROUNDS_SCRIPTLOG=1, 330,000 frames, health held) for each of the four characters, 24 runs, about 1.3 h for each batch of 8 in parallel at below normal priority.
Output E:\AvP\learning\lane-sprite-store\fz\s<seed>c<n> (c0 Warrior, c1 Schaefer, c2 Linn, c3 Hunter). The data before these seeds was 8 runs a character (lane-vanish fz_a to d, stage-sprites seeds 11 to 14).
Measure (tools/fuzz_unseen.py): the sprite keys a run looked up that the route census, any character's fuzz or body keys, or the screen keys do not hold, and of them the ones whose tile has a visible pen (a blank tile draws nothing).
Each batch is checked against everything before it, so the last batch is a held-out sample of what the merged data misses.

Visible keys new to the data, summed over the two seeds of a batch (per character: Warrior, Schaefer, Linn, Hunter, seed a + seed b):

| Stage | seeds 16, 17 against the 8-run data | seeds 18, 19 against that + 16, 17 | **seeds 20, 21 against that + 16 to 19 (what the final data still misses)** |
| --- | --- | --- | --- |
| 0e | 75 (50+0, 13+0, 0+4, 4+4) | 31 (9+17, 0+0, 0+0, 5+0) | **26** (all Linn, one run) |
| 1c | 330 (Linn 96, Hunter 234) | 208 (22, 8, 48+84, 46) | **208** (40, 13, 17+62, 76) |
| 1e | 7 | 18 | **0** |
| 24 | 102 (51 Warrior, 51 Hunter) | 13 | **0** |
| other stages, seeds 20, 21 | | | 12: 181, 20: 122, 14: 74, 02: 43, 04: 14, 10: 14, 0c: 13, 08: 3, 16: 7, 18: 7, 22: 5, 06, 0a, 1a, 26: 0 |

What remains is a heavy tail in a few runs: one run of one character finds 50 to 230 keys in one stage that 8 to 20 other runs did not (Hunter 1c 234 and 76, Linn 1c 96 and 84, Warrior 0e 50), most of the other runs find a few or none.
In stage 0e the visible new keys per batch of 8 runs fell 75, 31, 26 (the last all from one Linn run); 1e fell 7, 18, 0; 24 fell 102, 13, 0; 1c did not fall (330, 208, 208, mostly Linn and Hunter), and stages 12, 20 and 14 show 181, 122 and 74 in the last batch.
The census is a sample, as the stage-sprites lane said; this is the size of the sample error measured with fresh seeds, per eight runs. I did not look at what the 1c, 12 and 20 keys draw.

Fit of the merged data (all packs keep every key of the data; build log, fit.py): the final build (seeds 16 to 19 merged, window pad 2) drops 0 keys in all 209 files, 77 of 77 fit rows pass. The data with seeds 20, 21 merged as well (`wd_f3`, 14 runs a character, 19 to 32 window runs a stage)
was replayed with tools/stage_headroom.py for every stage: 0 keys dropped in all 19 stages, 0e headroom 155.6 KB (replay), 1c 185.8, 24 155.2, 1e 329.0. It was not built (replay only); the merge is `python tools/char_fuzz.py WORK 1=... --add` (data in
E:\AvP\learning\lane-sprite-store\wd_f3\char_fuzz.json and stage_window.json). Not covered by any of this: keys of a character's moves no fuzz run reaches (a script enumerator over the ROM's move tables would give them without a run; not started).

## Switch

| Switch | Default | Effect |
| --- | --- | --- |
| STAGE_WINDOW | off | a stage file keeps the next stage's first-45-frames pages instead of all of the next stage's (WORK/stage_window.json); applies in build.py, tools/wolverine/fit.py, tools/stage_headroom.py |
| STAGE_WINDOW_PAD | 2 | pages of margin either side of every window page, on top of the one the keep rule adds |

Tools: tools/stage_window.py (window data builder and apply), tools/stage_headroom.py (packer replay with headroom), tools/fuzz_unseen.py (new keys of fuzz runs against the data), tools/char_fuzz.py `--add` (extend WORK/char_fuzz.json by more runs).
Recipe change for the A/B discs: add `STAGE_WINDOW=1 STAGE_WINDOW_PAD=2` to the environment and copy `stage_window.json` and the extended `char_fuzz.json` into the work directory (E:\AvP\learning\lane-sprite-store\wd_f2).
