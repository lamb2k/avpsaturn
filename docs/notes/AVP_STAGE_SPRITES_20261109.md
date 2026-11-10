# Stage file sprites, 2026-11-09 (lane stage-sprites; HOST/offline measurements on the owner recipe build; Yaba A/B NOT completed; hardware UNRUN)

Branch lane/stage-sprites-20261109 on avp/integration 4ddab19, merged with lane/text-glyphs-20261109 (f62d289). Evidence D:\AvP-lanes\lane-stage-sprites
(fz\ fuzz runs, ev\ offline fit replays, build2.log, fit\, cf*\ char_fuzz.json files). All ROM-derived data stays outside git.

## 1. What is dropped and what is drawn (integration w1 build, before any change)

Asked = sprite keys the stage file lists (census union plus screen keys). Kept = asked minus dropped. "Census drawn" = dropped keys that a real route, a walk or a KO
run of the character(s) in the file drew (tools/rounds_rank.py / rounds_variants.py ranks). "Fuzz drawn" = sprite keys that independent button-fuzz play
(tools/rounds_fuzz.py, random jumps, attacks, guns, every direction, 4 characters, 8 runs per character, stages 02 to 26 in the last four) looked up in that stage and the file lacks
(dropped or never asked). Means over the files of the class.

| Stage | Class | Asked | Kept | Dropped | Dropped and drawn on census routes (route / walk / KO) | Fuzz drawn, not held |
| --- | --- | --- | --- | --- | --- | --- |
| 0e | 1P, 4 solo files | 23,030 | 19,419 | 3,611 | 0 / 0 / 0 | 1,613 |
| 0e | 2P, 6 pair files | 23,030 | 19,461 | 3,568 | 0 / 29 / 8 (Linn+Hunter: 169 walk, 49 KO) | 3,212 |
| 1c | 1P | 21,883 | 21,033 | 849 | 0 / 0 / 0 | 1,084 |
| 1c | 2P | 21,883 | 20,981 | 901 | 0 / 0 / 0 | 1,795 |
| 1e | 1P | 23,669 | 21,998 | 1,671 | 0 / 0 / 0 | 792 |
| 1e | 2P | 23,669 | 22,084 | 1,584 | 0 / 0 / 0 | 1,184 |
| 24 | 1P | 25,461 | 22,454 | 3,006 | 0 / 0 / 0 | 784 |
| 24 | 2P | 25,461 | 22,394 | 3,067 | 0 / 0 / 0 | 1,601 |

Findings:
- The per-character files (lane packs) already keep every key a character's own route, walks and KO runs drew: the stage files' "dropped and drawn" on the census is 0 for all
  1P files, and 0 for 2P except 0e Linn+Hunter. Of the dropped keys, 95 percent or more are other characters' art banks (e.g. Warrior's 0e file drops 2,385 of Schaefer's bank, 777 Hunter, 433 Linn).
- The blanks a player sees are mostly keys no file ever asked for (census gap), not dropped keys. Independent fuzz play looks up 8 to 10 percent more keys than the route census saw:
  400 to 1,300 per character and stage (5 to 10 percent of the keys looked up), whole poses of a jump attack, a hurt reaction, enemy frames the route never met.
  Leave-one-seed-out on the fuzz runs: each further seed still adds 100 to 500 new keys in stages 02 to 08, so the census does not saturate by itself.
- POSE_KEYS=0 in the owner recipe (WORK has no pose_keys.txt either): the avp-vanish pose fix (64c20f1) is not in the integrated builds. Its set was also only palettes 0 and 1
  (Warrior and Schaefer); the players' palettes are Warrior 0, Schaefer 1, Hunter 2, Linn 3. Wolverine's remap keys also collide with 140 of its keys (553 with the fuzz keys), which is why it was left out.

## 2. Fatal 0xe2 at 0xa9cc4 on stage 0e: cause found

- 0xa9cbe reads a sprite script word (`move.w (a0)+,d0`), 0xa9cc0 reads the word at table 0xa9ce4 + that word, 0xa9cc4 jumps through the 8 entries the lift knows; any other value is BADJUMP,
  fatal 0xe2. A script word from tile data is such a value.
- A tap on the table read (tools/rounds_fuzz.lua ROUNDS_SCRIPTLOG: 4 runs to stage 0e and 4 to stage 26) shows where player move scripts live: 41 pages in one stretch,
  0x161400 to 0x1717ff (pages 1410 to 1477), four blocks, one a character; no page outside it in any run, and a second independent run set found no new page.
- Page 1477 (0x171400, Linn's last script words, 0x1713f0 to 0x171454) is kept by none of the 20 stage files (it was in the old tile spill stretch 0x171000). 67 of the 68 pages of the stretch were kept
  only by chance of the padding. Fuzz Linn runs read it in stages 04, 06, 0c and 0e. A stage file that puts tiles there hands the reader garbage: the 0xe2.
  It is not proven that this was the owner's crash (registers were never captured); it is a read in a dropped page of exactly that kind, reproduced as a read in MAME.
- Other pages the fuzz reads and no file keeps (stage 04: 0xa5800 to 0xa6bff, 662 to 666; 0c: 0x33000/0x33400, 0x56400; 0e: 1477 only): same class.
- Fix (CHAR_FUZZ_PAGES, default ON, a plain correctness fix): every stage file keeps the whole script stretch 0x161400 to 0x1717ff, and the pages the fuzz runs read in its stage, the front end's and
  the next stage's, each with a page either side (the rule of tools/rounds_config.py). Cost: 1 page for the script stretch, 1,399 pages over the 210 files (6.7 a file) for the fuzz reads. tools/check_round_pages.py (new)
  checks the built files: no file puts tiles on a page it keeps and every kept page another file overwrites is rewritten. 0 of 287 break the rule.
- Pad is not removable: cross-validated against the fuzz runs, pages read per stage but not kept: own pages only 15 to 24 missed, with front and next 12 to 18, with the page either side 5 to 7,
  as built 4 to 6, plus the new rule 0.

## 3. Room: options, measured (stage 0e Schaefer and Linn files are the tightest)

Tiles of 128 bytes (unique payloads). Capacity of 0e is 14,720 as built. All figures are for the keys that matter (census route/walk/KO, fuzz, the characters' body keys).

| Option | Tiles gained | Changes the runtime | State |
| --- | --- | --- | --- |
| Sector fill (PACK_TAIL_FILL): spill uses the odd last page of a ROM stretch, its sector tail rewrites the kept page after it with the ROM's bytes | +230 to +300 a file (0e 246, 24 299) | no | built, default off |
| Mirror dedupe (a tile that is another's flip) | about 350 to 480 (needs a flip flag in the key word) | yes (key word, command flags) | measured only |
| Next-stage keep as the 45-frame load window instead of the whole next stage (ROUNDS_WINDOW=45 in rounds_fuzz.lua: the game runs 12+ vblanks on the old file after the word changes) | 0e 1,448, 1e 976, 1a 1,168, 14 816, others 40 to 376; 1c 136, 24 160 | no | measured only (needs the census page lists in WORK; front end kept in full) |
| Row-trimmed tile encoding (16 bit row mask + non-empty rows) | need 0e Schaefer 17,011 -> 12,406 tiles; row trim to 9,969 | yes (upload in sat_gfx.c, offset table, code bytes in a build with lw_free 60) | measured only |
| Narrow the pad, front or next unions | 250 to 330 pages (0e) | no | rejected: misses 12 to 24 read pages a stage |
| Drop font banks (text lane) | name entry 3.4 KB, select digits 1.9 to 2.1 KB, all fonts 20 KB = 160 tiles | no | not worth it: all fonts cost 160 tiles; name entry and the select open from every stage (KO, continue) |

## 4. Fuzz keys per character (CHAR_FUZZ_KEYS, default OFF; visible)

tools/char_fuzz.py reads per-character fuzz runs (tools/rounds_fuzz.py, one character each; ROUNDS_CHAR 0 Warrior, 1 Schaefer, 2 Linn, 3 Hunter) into WORK/char_fuzz.json:
the sprite keys each stage word looked up and the keys drawn in the character's own palette (body). build.py adds them to the four stages 0e, 1c, 1e, 24 (CHAR_FUZZ_KEY_STAGES), ranked under the
routes and above the walks (fuzz 150,000, body 70,000), for the characters in the file's mask; every variant of a stage asks for all four characters' keys so only the ranks differ.

Why only four stages: the sector store (STORE.BIN) allows 2^18 sectors of 2 KB. In stages with room all 11 variants pack to identical files and are stored once (integration build: 121,921 unique sectors
of 332,673). Per-character keys in every stage made each variant differ: 274,925 unique sectors, "sector store: too large" (first build, build1.log). With the four stages whose variants already differ:
199,518 sectors, ISO 413 MB (was 374 MB). The other stages keep their blanks (below).

Data: lane-vanish fuzz runs (4 seeds, stages 02 to 0e) + this lane's seeds 11, 12, 13, 14 (stages 02 to 26), 8 runs a character; script log runs for the pages.

### Result, dropped and fuzz-drawn keys not held (offline replay of build.py's packer; seed 14 is HELD OUT in this table)

"Orig" = integration w1 (no text fixes). "+text" = text-glyphs fixes (FONT_KEYS, STORY_PAGES) alone. "Mine+text" = this lane with CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 and the text fixes.
Held-out column: sprite keys seed 14's runs looked up in the stage that the file lacks.

| Stage | File | Dropped, orig | +text | Dropped of census routes/walks/KO, mine+text | Held-out missing: +text | mine+text |
| --- | --- | --- | --- | --- | --- | --- |
| 0e | Warrior | 3,650 | 3,944 | 0 | 777 | 8 |
| 0e | Schaefer | 3,589 | 3,899 | 15 (7 KO, 8 walk) | 1,290 | 674 |
| 0e | Hunter | 3,526 | 3,833 | 7 KO | 759 | 58 |
| 0e | Linn | 3,679 | 3,970 | 0 | 1,343 | 750 |
| 0e | Warrior+Schaefer | 3,436 | 3,718 | 1 walk | 1,982 | 1,594 |
| 1c | Warrior / Schaefer / Hunter / Linn | 836 / 924 / 817 / 820 | 1,254 / 1,217 / 1,279 / 1,322 | 0 | 675 / 643 / 588 / 1,587 | 78 / 19 / 3 / 346 |
| 1c | Warrior+Schaefer | 913 | 1,219 | 0 | 1,079 | 129 |
| 1e | Warrior / Schaefer / Hunter / Linn | 1,662 / 1,678 / 1,610 / 1,734 | 2,053 / 2,008 / 1,944 / 2,076 | 0 | 613 / 724 / 493 / 1,020 | 44 / 2 / 3 / 273 |
| 1e | Warrior+Schaefer | 1,620 | 1,966 | 0 | 1,049 | 26 |
| 24 | Warrior / Schaefer / Hunter / Linn | 3,017 / 3,012 / 2,893 / 3,103 | 3,303 / 3,523 / 3,177 / 3,584 | 0 | 683 / 485 / 695 / 1,085 | 105 / 35 / 44 / 14 |
| 24 | Warrior+Schaefer | 2,944 | 3,330 | 201 walk | 1,317 | 1,066 |

(The dropped column counts the larger candidate set in mine+text: it asks for all four characters' keys, so its raw dropped count is not comparable; the tier columns are.)
Text-lane cost on the four stages (measured on the same packer): +300 to 650 dropped sprite keys for fonts and +100 to 190 for story pages, as that lane reports. Fonts cost 20 KB a file
(160 tiles); all of it is cheaper than the 230 to 300 tiles the sector fill returns.

Built check on the real round files, seed 14 included in the build (in sample): missing keys 0 in every 1c, 1e, 24 solo file and 0e Warrior, 36 for 0e Hunter, 678 Schaefer, 859 Linn.

Remaining gaps:
- Stage 0e Schaefer and Linn: the fuzz runs of those two looked up 14,500 and 15,700 keys in 0e; unique tiles needed 17,011 and 17,067 against 14,950 held. About 2,100 tiles short. Closing it needs the
  load-window keep (1,448) plus mirror dedupe (about 430) or the row encoding.
- 2P pairs in 0e and 24 (Warrior+Schaefer 1,594 and 1,066 held-out missing; other pairs worse): both bodies and both fuzz sets exceed the room.
- Stages 02 to 22 (not 0e/1c/1e/24): 400 to 1,300 fuzz-looked-up keys per character and stage are not held (blank pieces in normal play). The data is in char_fuzz.json; they cannot take it without the store
  growing past 2^18 sectors unless variants share bytes (idea: order tile payloads core-first and align the tile block to a sector so the 11 variants share their common prefix).
- Three or four players use the one-for-all file (all characters, drops 6,000 to 9,000 keys); not addressed.
- Boundaries: seed 14 is one run a character; stage 24 and 26 have two seeds (13 and 14).

## 5. Gates (owner recipe + CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1, work dir copy of integration/w1)

- Build: no NO-GO; hw_free 1,252, lw_free 60 (unchanged: round files only), cart_free 4,340; sector store 199,518 sectors (limit 262,144), ISO 413,093,888 bytes. First build without the four-stage limit failed ("sector store: too large").
- tools/check_round_pages.py: 0 of 287. tools/check_screen_keys.py: 0 of 287 miss a banner, font or screen key. tools/check_caption_keys.py: 287 files, short 0.
- tools/wolverine/fit.py on a copy of D11 (CHAR_FUZZ_KEYS=1, PACK_TAIL_FILL=1, FIT_GFX_GUEST/FRONT from the build): 76 of 76 stage rows gate True, 0 Wolverine-own keys dropped, 0 missing guest keys, front_wv True. Wolverine's remap keys are left out of the guest files' fuzz keys (tools/wolverine/guest_rounds.py).
- WSL unittest discover: 127 run, 30 errors (the known private-dependency load errors), 0 failures, no new ones; new tests/test_char_fuzz.py (8 tests); test_round_cache planner namespace updated.

## Switches

| Switch | Default | Effect |
| --- | --- | --- |
| CHAR_FUZZ_PAGES | on (correctness fix; needs nothing in WORK: the script stretch is built in; fuzz pages need WORK/char_fuzz.json) | keep the player script stretch and fuzz-read pages |
| CHAR_FUZZ_KEYS | off | per-character fuzz and body keys in CHAR_FUZZ_KEY_STAGES (0e, 1c, 1e, 24) |
| CHAR_FUZZ_KEY_STAGES | 0e,1c,1e,24 | stages that take the keys (store limit) |
| PACK_TAIL_FILL | off | spill uses the odd last page of a stretch |
| CHAR_FUZZ=0 | | turns the whole input off |

Not done: Yaba A/B of the built disc (the host-side Yaba harness started but stalled at vblank 0 once the machine was loaded, and a request to stop my own stale Yaba process was denied by the permission
classifier, so I stopped there); the load-window keep, the mirror flag and the row encoding are measurements only; 2P and 3P/4P files.
