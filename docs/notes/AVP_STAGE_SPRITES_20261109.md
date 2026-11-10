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

## 6. Row-trimmed sprite tiles (SAT_TILE_ROWTRIM, default OFF; owner "Let's try it", 2026-11-09 evening; EMULATOR Yaba + HOST; hardware UNRUN)

Switch: `-DSAT_TILE_ROWTRIM` in KERNEL_CFLAGS; build.py then packs SGP2 (kernel and packs cannot disagree). Run the owner recipe with `CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 CHAR_FUZZ_KEY_STAGES=` (empty: keys in every stage).
- Format: a sprite tile is a record, u16 row mask (bit 15 = row 0), u16 spare, 8 bytes per set row. A cleared row is eight zero bytes in the plain tile, so the 128 byte slot is byte for byte the SGP1 one. A u32 base every 1024 payloads and a u16 per payload locate a record (4 byte units). Spill segments, tail fill and the page checks work unchanged. Runtime: sat_gfx.c rowtrim_decode writes each 8 byte row once into VDP1 VRAM (no buffer).
- Pixel identity: tests/test_rowtrim_pack.py (every payload read back as the C does, main and spill); tests/host_gfx_rowtrim_identity.sh: 600 random frames, 1,735 sprite uploads, a third in spill, VDP1/VDP2/CRAM/register hashes identical to SGP1, FIT 1 and 0; a one byte corruption is caught.
- Tiles gained (real packer, owner recipe, text fixes in): the four stages 0e/1c/1e/24 hold 18.9K/20.2K/20.8K/21.0K tiles (were 14.7K to 16.6K), +4,200 in 0e. With the fuzz keys in every stage, stages 02 to 26 drop 0 sprite keys in every file replayed, so their 11 variants pack identically and the sector store stays small (it overflowed without rowtrim).
- Built (wd2, owner recipe + rowtrim): no NO-GO; hw_free 1,004 (1,252 without: -248 B, hw_image +220), lw_free 60 (unchanged), cart_free 4,340 (unchanged), cold1 unchanged (c13, 84,348, 5,085). STORE 199,683 sectors (limit 262,144; 199,518 for the same build without rowtrim), ISO 413,431,808 bytes.
- Gates on that build: fit.py on a copy of D11 with the rowtrim flags: 76 of 76 rows gate True, 0 Wolverine-own dropped, 0 missing guest keys, front_wv True. check_round_pages 0 of 287, check_screen_keys 0 of 287, check_caption_keys 287 files short 0. WSL unittest discover: 131 run, 30 errors (the known private-dependency load errors), 0 failures. Host rowtrim identity test passes.
- Drawing path cost (Yaba, emulated FRT ticks, SatDebug): the peak slave graphics frame in the same scripted 0e walk (Warrior, seed 5, two runs each, repeatable to 2 ticks): fix without rowtrim 24,447 / 24,449 (118 uploads peak), with rowtrim 24,381 / 24,381 (122 uploads peak): not slower. Mean gfx_ticks per sample 1,432 and 1,527 (no rowtrim), 1,373 and 1,547 (rowtrim): inside scene noise (sd 200 to 460); snap_ticks 814 to 854 and game_ticks 2,340 to 2,430 equal. No Schaefer-only scene: character select did not take Schaefer or Linn in my harness (see below). Integration (no fix) peak 21,741: the fix builds' peak frame is 2,700 ticks higher; the cause was not isolated (not rowtrim).
- Missing-key counter (sat_gfx_stats.missing per 1,000 vblanks, 60 s of fuzz play after the warp, same input seed; counts every key the pack lacks including keys of blank tiles, so only a proxy): integration / fix without rowtrim / fix with rowtrim: 0e Warrior 1,534-1,898 / 1,153-1,477 / 982-1,126; 1c 1,360 / 1,157 / 1,052; 1e 1,814 / 1,157 / 1,077; 24 1,345 / 1,405 / 1,235; second run set ("l", still Warrior) 0e 1,680 / 1,408 / 1,265; 24 1,961 / 1,354 / 1,480.
- Images (paused framebuffer_burst, six frames each, D:\AvP-lanes\lane-stage-sprites\y2\shots\<disc>_<char>_<stage>0..b2; side by side montages y2\montage\<stage>_<char>_b<n>.png with integration | fix | fix+rowtrim, and y2\montageef_<stage>.png with MAME fuzz stills (D:\AvP-lanes\lane-stage-sprites\mame\c0, c2 snap) beside Yaba integration and rowtrim). Looked at: 0e_l_b1, 0e_w_b1, 1e_w_b1, 24_l_b2, ref_0e, ref_1e, nothing else. What they show: on the integration disc 0e (0e_l_b1, left) and 1e (1e_w_b1, left; ref_1e third tile) the player is drawn only as the cyan "1P" marker with its spear or an incomplete marker, no body; in the fix and fix+rowtrim frames the Predator is drawn whole (1e_w_b1 middle: in the air at the top; right: at the right edge) and the 1P marker is complete. The moments are NOT the same game moment (Yaba input timing differs, the fight differs), so this is an example of the symptom, not a pair; the 0e 0e_l_b1 fix and rowtrim frames also have no visible body at the marker, so one frame does not prove it fixed. No frame-exact comparison against MAME was possible.
- Harness limits: character select did not pick Schaefer or Linn (both "l" runs show P-Warrior), so no Schaefer or Linn scene was played in Yaba; the Yaba 0e Warrior frames of the fix are not frame-synchronous to MAME; fix_w_0e's first run produced no output (repeated as t1/t2).

## 7. Long-masked tiles (SAT_TILE_ROWTRIM=2), zero missing on every file, Hunter report (2026-11-10; EMULATOR Yaba with General\UseSh2Cache=false from here on; HOST; hardware UNRUN)

Timing and speed numbers in sections 1 to 6 were taken with the SH-2 cache emulation ON; the numbers below with it OFF (owner rule 2026-11-10). They are not comparable.

- Switch `-DSAT_TILE_ROWTRIM=2` (plain `-DSAT_TILE_ROWTRIM` is still the row masked SGP2). Record = u32 mask over the tile's 32 longs (bit 31 = long 0, set = not zero), then those longs: 0.617 of the plain tile on the 0e and 24 payloads (row masks 0.743; a byte trim would be 0.58, a word mask 0.57 but 64 decode steps). Magic SGP3. Same loop shape as the row decode (32 steps of one long instead of 16 of two). tools/char_fuzz.py, build.py, fit.py and the check tools take the value; `CHAR_FUZZ_KEY_STAGES=` (empty) puts the fuzz keys in every stage.
- Pixel identity: tests/test_rowtrim_pack.py (both modes, main and spill) and tests/host_gfx_rowtrim_identity.sh (600 random frames; VDP1, VDP2, CRAM and register hashes identical to SGP1 for SGP2 and SGP3, FIT 1 and 0; a one byte corruption is caught).
- Zero missing, offline replay of build.py's packer on the real data (owner recipe + text fixes + CHAR_FUZZ_KEYS=1 PACK_TAIL_FILL=1 + rowtrim 2): in stages 0e, 1c, 1e and 24 every file (the base file for three or four players, the 4 solo files, the 6 pairs and the four Wolverine files m2, m3, m6, ma `_wv`) holds every key and body key the fuzz runs looked up (0 not held). All eleven variants of a stage pack to identical bytes (22,469 tiles held in 0e, 21,307 in 1c, 21,852 in 1e, 23,078 in 24). Stages 02 to 26 drop 0 as before. One gap found by the Wolverine files: 28 keys in 1c that Warrior's fuzz play used and the census called Schaefer's own were taken out of the m3, m6 and ma guest files; tools/wolverine/guest_rounds.py now keeps what the other characters' fuzz data used (other_keys).
- Build E (owner recipe + rowtrim 2 + keys everywhere, on avp/integration c4d0df3 merged): rc 0, no NO-GO, hw_free 708, lw_free 60, cart_free 4,340, cold1 unchanged. The same tree without rowtrim: hw_free 964, so rowtrim 2 costs 256 bytes of high RAM (rowtrim 1 cost 248). STORE 160,816 of 262,144 sectors (199,518 for the four-stage keys without rowtrim), ISO 333,834,240 bytes.
- Gates on E: fit.py on a copy of D11 with the rowtrim flags: 76 of 76 rows True, 0 Wolverine-own dropped, 0 missing guest keys, front_wv True. check_round_pages 0 of 287, check_screen_keys 0 of 287, check_caption_keys 287 short 0. WSL unittest discover: 131 run, 30 errors (the known private-dependency load errors), 0 failures. HOST goldens golden_r1s, golden_full, golden_c1, golden_c2, golden_c3, golden_2p all clean (15,618, 317,908, 272,171, 369,051, 333,669, 329,918 of the same count) with garbage in every ROM page the built keep lists drop (ROUNDS_SWAP from the built round_keep.json) and the dropped page read watch on: 0 dropped page reads, missed IRQ 0.
- Versus on top: test branch test/stage-sprites-combined (this branch + lane/versus-20261109 2ada807 + lane/wv-native-gfx-20261109 7f26a1f, merged without conflicts; local, not pushed). Build F with SAT_WV_NATIVE_GFX and the 36 duel copies of the arena files (DUEL_FILES default on): rc 0, hw_free 568, lw_free 52, cart_free 4,508, native block canary ok (0x27f992c, 21,616 bytes, outside the ROM image and every stretch, cold1_at 0x27e2000), 323 round files, STORE 187,010 of 262,144 sectors, ISO 387,479,552 bytes. Headroom 75,134 sectors. The build-time guest tile check passed (no Wolverine tile lost); the native lane changes no pack input.
- Same moment, Yaba, paused framebuffer_burst, deterministic stepping (y2\det.py): after the stage loads the run pauses, steps single frames until the object count first changes (a game event, not the vblank count), then steps scripted keys in 2 frame chunks. Two runs of one disc are frame identical (screenshots equal pixel for pixel in chunks 10 to 40, int_s1 and int_s2) until the first input takes effect; after that the player drifts a few pixels between runs (chunk 50: px 528, 517, 528) because the game's random numbers depend on the absolute vblank count, which the load changes. Integration and the fix build give the same object and command counts in chunks 0 to 40 (px 564, 62 objects, 178 commands). So matched frames exist only for the opening of a stage; fights are near matches. Images (D:\AvP-lanes\lane-stage-sprites\y2\montage2): s_c040.png and s_c060.png (0e, integration left, fix + rowtrim right, the Warrior drawn whole in both, same pose), s_1c_c070.png (1c opens on the ROUND 7 card), hunter_ref.png (MAME Hunter stills beside Yaba).
- Objective in-play check (KEYLOG build wdH = E + -DSAT_KEYLOG, hw_free 636; y2\kl.py, vis.py): fuzz-play each stage 60 s for each character, read back every sprite key the game asked for, then ask each build's round file for the same keys. Visible-missing = asked, not in the file, tile has a visible pen. Not counting Wolverine's keys (below), integration / fix without rowtrim / fix + rowtrim 2 per run: 0e Warrior 219 / 0 / 0, Hunter 142 / 28 / 0, Linn 351 / 2 / 2; 1c Warrior 0 / 0 / 0, Hunter 0 / 0 / 0, Linn 291 / 0 / 0; 1e Warrior 120 / 0 / 0, Hunter 189 / 0 / 0, Linn 332 / 10 / 10; 24 Warrior 38 / 1 / 1; Wolverine files 0e / 1c / 1e: 35, 24, 69 integration; 35, 24, 5 fix; 7, 24, 0 fix + rowtrim. The few left (Linn 0e 2, Linn 1e 10, Warrior 24 1, Wolverine 0e 7 and 1c 24) are keys no census or fuzz run saw: the census is a sample. The Wolverine stage 24 run asked 15,394 keys (a stage load fell inside its window): not trustworthy, not repeated. Schaefer is Wolverine here (guest default).
- Wolverine's keys asked by every player (finding, not this lane's code): in all Warrior, Hunter and Linn runs 100 percent of the visible-missing keys that remain (587 to 961 per run) are Wolverine's remap keys; the game asked 650 to 960 of them per run. The player block's byte +1 reads 1 for Warrior, Hunter and Wolverine alike (Yaba, guest setting as shipped); the game's character index at +0xd2 is 0 Warrior, 1 Wolverine (Schaefer slot), 2 Hunter. wolverine.c is_wolverine() and wv_blank() test +1 against WV_CHAR_SCH, so his skin pass (sat_guest_objects) and hooks run on every player while the guest setting is on (the native lane switched to +0xd2). In a stage file without his tiles (every solo Warrior, Hunter and Linn file; the probe shows file 82 = stage0e_m4 for solo Hunter on the keylog disc) the skin pieces are absent, so they draw nothing and the stock body shows: guest on and off, paused 3 frame bursts from one saved state (gsel2.py, 10 clean same-state trials, integration and fix + rowtrim) give identical playfield pixels. They would draw where the file holds his tiles (a pair with the Schaefer slot). The P.Hunter in the owner's capture is the stock Hunter (gold armour, green greaves; MAME Hunter stills show the same body leaping), not a mixed sprite. The fix belongs on the integration line (+0xd2) and is not made here. The Yaba missing-key counter (about 1,000 per 1,000 vblanks) is mostly these asks, which is why it hardly moved between builds.
- Graphics peak on 0e (the "12 percent"): not reproduced with the cache emulation off. Peak since boot in the same flow: integration 33,353 ticks, fix + rowtrim 33,290 (the title menu's first frame, 65 uploads and 114 layer uploads, sets it, not the stage). Heavy frames (the ones the slave draws) in matched state: 20,857 integration, 20,873 fix + rowtrim; maximum over 100 sampled chunks 21,579 and 21,524 (integration, two runs) against 21,628. The earlier 24,447 against 21,741 were peaks since boot read at the end of a run with the cache emulation on, not repeated; no isolated cause, and not rowtrim (the same gap was in the build without it).
- Character select now steers by ff81cc (ys.enter_stage) and was checked on each character (Warrior 1, Schaefer 2, Hunter 4, Linn 8); the "l" runs in section 6 were Warrior.

Not done: Yaba A/B on the 2P pairs and the Wolverine pairs (no second pad); a repeat of the Wolverine stage 24 key log; hardware.
