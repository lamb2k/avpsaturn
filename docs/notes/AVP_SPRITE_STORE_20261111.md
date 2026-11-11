# Stage sprite store: next-stage load-window keep, 2026-11-11 (lane sprite-store; HOST + offline pack replay + EMULATOR Yaba; hardware UNRUN)

Branch lane/sprite-store-20261111 on avp/integration d0540c8. Switch: `STAGE_WINDOW=1` (build.py environment, default off) with `STAGE_WINDOW_PAD=2`.
Evidence: E:\AvP\learning\lane-sprite-store (builds wd_base, wd_win, wd_f1, wd_f2, wd_f2kl; logs b_*.log, fit_*.log, hostwin\, hostf2\, hostneg\, trans\, headroom_*.log, unseen_*.json; fuzz runs fz\s16c0 to s21c3).
All ROM-derived data stays outside git.

## 1. Baseline (task 1)

Recipe A of E:\AvP\learning\integration\run3ab2.sh (3h + ESSENTIALS remap + FONT_COLD + FPS_HUD) on avp/integration d0540c8 with lane/wv-native-gfx-20261109 97de971 merged
(throwaway branch wip/sprite-store-base-20261111 9eefb36, merge clean). Build `base`: rc 0, no NO-GO, hw_free 2,136, lw_free 96, cart_free 4,428, native block 20,944 bytes,
**cold1_at 0x27e0000** (the same as disc 3h; the remap build without 97de971 was at 0x27df000), STORE 152,080 sectors of 262,144, ISO 316,149,760 bytes.

Dropped sprite keys, stage 0e (only stage with drops; the four Wolverine files `_wv` of every stage hold all of their keys):

| File | 3e | 3h (9fff850) | remap, 5e49c52 | **base (this tree)** |
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
| total of the 11 files | 2,631 | 3,430 | 4,369 | **3,693** |

The native lane's 4 KB recovery (97de971) takes the remap's 4,369 back to 3,693 (cart step back to 3h's), but 0e is still above 3h (3,430): the fuzz-key data and the remap's 328 tiles cost room that the step did not give back. Measured with the build log's `dropped_keys` per file.

## 2. Load-window keep (task 2)

A stage file keeps the ROM pages its own stage reads, the front end's and the **whole next stage's** (tools/rounds_config.py), each with a page either side, because the Saturn kernel loads a stage file only
after the stage word has held 12 vblanks (saturn/rt/kernel.c round_check) and the game runs those frames on the old file. Pages the file keeps cannot take tile spill. Stage 0e keeps 1,177 of the ROM's 2,048 pages this way.

`tools/stage_window.py` replaces the next-stage term with the pages read in the first 45 frames after the stage word changed (tools/rounds_fuzz.lua `ROUNDS_WINDOW=45`, 3.75 times the 12 vblank hold),
unioned over every census run that has window files, with `STAGE_WINDOW_PAD` (default 2) more pages of margin either side of each window page. The next stage's own file restores whatever the old file spilled over
(the existing restore machinery: `back = written & keep - own`). Data: `WORK/stage_window.json` (tools/stage_window.py WORK CENSUS RUNDIR...), 28 runs for the final build (16 of the 20 stages have 12 to 24 runs; 24 runs for 0e, 16 for 10).
The old rule is recomputed from the census (lane-chars/census.json, KO pages included) and has to reproduce rounds.json's keep_pages exactly, else the tool refuses. Fuzz pages (char_fuzz.augment `window=`) use the same window.
A stage without window data keeps the whole next stage (none of the 20 stages lacks data). Default off: with the switch unset every code path is the one before.

Pages freed per file: 0c 49, **0e 183** (pad 0; 176 with pad 2), 1e 125 (80), 1c 17 (-7: the 1c file keeps what 1e's window needs and more), 24 20 (7) of about 1,000 kept.

### Per-step drop tables (build log `dropped_keys`, file total tiles = in main + spill)

| Step | Build | 0e drops (11 files) | stage0e tiles held | STORE sectors | ISO bytes |
| --- | --- | --- | --- | --- | --- |
| 0 | base (above) | 265 to 374, total 3,693 | 22,503 | 152,080 | 316,149,760 |
| 1 | + STAGE_WINDOW=1, pad 0, same fuzz data | **0 in all 11** | 22,715 | 139,147 | 289,665,024 |
| 2 | + pad 2, fuzz seeds 16, 17 merged | **0** | 22,797 | 158,898 | 330,115,072 |
| 3 | + pad 2, fuzz seeds 16 to 19 merged (**final**) | **0** | 22,826 | 150,607 | 313,135,104 |

Every other file drops 0 in every step; the fuzz seeds add 111 tiles to 0e (22,715 to 22,826) and 465 to 1c (21,525 to 21,990). Restore bytes in the round files fall (all 287 files 41.8 MB base, 30.3 MB step 1) because the files no longer restore pages they do not keep.

Offline replay of the packer (tools/stage_headroom.py, replay: it leaves out the home caption and edge keys, which cost the base 0e about 260 more drops than the replay shows; KB of cart room still free in the file):

| File | base data, no window | final data (seeds 16 to 19), no window | final data, window pad 2 |
| --- | --- | --- | --- |
| stage0c | 337 | 337 | 425 |
| stage0e | 3.1 KB, 5 keys dropped | **149 keys dropped** | **157.8 KB** |
| stage1c | 200 | 200 | 199 |
| stage1e | 239 | 239 | 330 |
| stage24 | 150 | 150 | 156 |

so the window is what lets the 16 new fuzz seeds into 0e: without it they would take 149 more keys out of the replay (about 410 in the build).

## 3. Gates on the final build (F2: window pad 2, seeds 16 to 19)

- fit.py (copy of D12, FIT_GFX_GUEST/FRONT, FIT_DIALOG_KEYS, STAGE_WINDOW=1): **76 of 76 stage rows and front_wv gate True**, 0 Wolverine-own keys dropped, 0 missing guest keys, Schaefer and Wolverine variants drop 0 everywhere
  (without the window the 0e Schaefer variants drop 284 / 302 / 251 / 214, step 0 fit.py on the same tree).
- check_round_pages: PASS 0 of 287 (818 pages are tile spill somewhere); check_screen_keys: 0 of 287; check_caption_keys: 287 files short 0.
- HOST goldens with garbage (0xA5) in every ROM page the built keep list of the loaded file does not hold (ROUNDS_SWAP from round_keep.json, `swap_f2.txt`) and the dropped-page read watch (ROUNDS_SWAP_TRAP): **all six clean**: r1s 15,618, full 317,908, c1 272,171, c2 369,051, c3 333,669, 2p 329,918 of the same count, 0 dropped-page reads, missed IRQ 0 (hostf2\; 4, 21, 21, 21, 21, 16 file loads simulated).
- WSL unittest discover: 161 run, 30 errors (the known private-dependency set, same test names), 0 failures, 2 skipped; new tests/test_stage_window.py (9), test_char_fuzz.py +1.
- STORE: 150,607 of 262,144 sectors (final); 158,898 at the largest step.
- Default-off identity: DEFAULT_IDENTITY

Window step 1 (pad 0, 16 seeds not merged) also passed: six goldens clean (15,618 / 317,908 / 272,171 / 369,051 / 333,669 / 329,918, 0 dropped-page reads, missed IRQ 0, hostwin\), fit 77/77, the three checks, STORE 139,147.

### Is the host check sensitive to the window? (negative controls, hostneg\ and swap_neg*.txt)
- The window-only pages (read in the first 45 frames of the next stage and by neither the old stage nor the front end) made garbage in every file's keep list: golden_c1, c2, c3 and full diverge at the **24 to 26 transition** (RAM difference one frame after the stage 26 file swaps in; vblank 268,525 of golden_c1), clean at every earlier transition.
  So the window pages are read in the hold in at least one real transition and the data must be right; golden_r1s and golden_2p stop before that transition.
- 15 of stage 04's own exclusive pages made garbage: DROPPED PAGE READ rom 100000 page 400 (stage file 4) at vblank 5483, 30 frames after the stage 04 file swapped in (golden_r1s). The harness catches a read of a page the file does not keep.

### Saturation of the window data
Pages new to the union per added run (16 runs for 0e, 12 for stages 14 to 26): 0e 87, 3, 2, 3, 0, 0, 0, 1, 0, 3, 0, 0, 0, 0, 0, 2; the late additions are one to three pages and
almost all within a page of a known one (new pages not covered by the previous union padded by one page: 0e 1, 2, 1 over runs 8 to 16; 24 2, 2, 2). Hence `STAGE_WINDOW_PAD=2` (the cost is 7 of the 183 pages freed in 0e).
The risk that remains is a page read in the first 12 vblanks of a stage entered by a route the 24 runs did not take (a different predecessor than the next stage in the census order, as in the home BOSS RUSH, which already jumps 04, 08, 0a, 1a, 24 with the old rule too).

## 4. Stage change evidence (Yaba)

YABA_EVIDENCE

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

What remains is a heavy tail in a few runs: one run of one character finds 50 to 230 keys in one stage that 8 to 20 other runs did not (Hunter 1c 234, Linn 1c 84, Warrior 0e 50), the rest of the runs find none. 1c is the stage with the long tail (a rare enemy or event the fuzz reaches
about one run in four); 0e is down to one run in 8 finding keys (26 in the last batch, from 75 and 31); 1e and 24 found none in the last batch. The census is a sample, as the stage-sprites lane said; this is the size of the sample error, measured with fresh seeds.

Fit of the merged data (all packs keep every key of the data; build log, fit.py): the final build (seeds 16 to 19 merged, window pad 2) drops 0 keys in all 209 files, 77 of 77 fit rows pass. The data with seeds 20, 21 merged as well (`wd_f3`, 14 runs a character, 32 to 19 window runs a stage)
was replayed with tools/stage_headroom.py for every stage: 0 keys dropped in all 19 stages, 0e headroom 155.6 KB (replay), 1c 185.8, 24 155.2, 1e 329.0. It was not built (replay only); the merge is `python tools/char_fuzz.py WORK 1=... --add` (data in
E:\AvP\learning\lane-sprite-store\wd_f3\char_fuzz.json and stage_window.json). Not covered by any of this: keys of a character's moves no fuzz run reaches (a script enumerator over the ROM's move tables would give them without a run; not started).

## Switch

| Switch | Default | Effect |
| --- | --- | --- |
| STAGE_WINDOW | off | a stage file keeps the next stage's first-45-frames pages instead of all of the next stage's (WORK/stage_window.json); applies in build.py, tools/wolverine/fit.py, tools/stage_headroom.py |
| STAGE_WINDOW_PAD | 2 | pages of margin either side of every window page, on top of the one the keep rule adds |

Tools: tools/stage_window.py (window data builder and apply), tools/stage_headroom.py (packer replay with headroom), tools/fuzz_unseen.py (new keys of fuzz runs against the data), tools/char_fuzz.py `--add` (extend WORK/char_fuzz.json by more runs).
Recipe change for the A/B discs: add `STAGE_WINDOW=1 STAGE_WINDOW_PAD=2` to the environment and copy `stage_window.json` and the extended `char_fuzz.json` into the work directory (E:\AvP\learning\lane-sprite-store\wd_f2).
