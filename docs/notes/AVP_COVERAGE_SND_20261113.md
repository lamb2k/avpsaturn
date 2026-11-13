# Missing sound effects added (coverage lane, fix7c2 part A, 2026-11-13)

Branch `lane/coverage-snd-20261113` on `lane/coverage-20261113` 015c488d (fix7c1). EMULATED = my Ymir copies (`ymir\run\cov-sdl3.exe`; `ymir_gA\run\cov-gA.exe` adds a per-slot SCSP energy trace), MAME 0.289 avspu. Nothing is a console measurement. No RAM pokes in any Ymir run.

## Why they were missing (not what the first list assumed)
The 14 commands were not all "absent from the census". Eleven of them (0x08e, 0x14e, 0x14f, 0x05b, 0x064, 0x067, 0x07f, 0x087, 0x094, 0x12c, 0x134) are in the census sound lists of the files that use them, and they were rendered, but each render **never ended** (the Z80 loops them until a stop control; `render_mame.lua` caps them at 10 s, 110,000 samples). `build_pack.py` left every clip over 65,535 samples (the SCSP's 16 bit loop end) out ("past the SCSP's 16 bit loop end, left out"), and `rounds_config.py` then drops commands it has no clip for (`want = [c for c in f["sound"] if c in size]`) without a word. So no looping sound was ever in any pack (the loop path of `sat_audio.c` had never run). The other three (0x156, 0x04f, 0x056) have normal clips and were only absent from the census lists (the route censuses skip the story, and 7-2's flurry).
(`sounds.json` is keyed by hex without 0x for `build_pack.py` ("8e"), and the table channels come from there; an earlier lookup by decimal key gave wrong channels.)

## What changed
- `saturn/audio/build_pack.py` `loop_clip()`: a render that never ended becomes a seamless loop. Skip the first second (attack), find the period (autocorrelation, 0.18 to 0.7 s for these), cut a whole number of periods of about 0.6 s starting where the two ends meet best, and cross-fade the last 256 samples into the samples that follow so the wrap has no step. 5 to 8 KB a clip (5,141 / 7,749 / 5,886 / 5,972 / 5,332 / 6,291 / 5,997 samples at 11,025 Hz, 8 bit). The slot loops the whole clip (loop start 0, as `sat_audio.c` does), so the attack is not replayed: the effect starts at its steady state. Aliases share one clip (0x8e = 0x14e = 0x14f, 0x5b = 0x12c, 0x64 = 0x134: same sample, each keeps its own TL). `--all` builds now include the other looping commands too (0x5a, 0x84, 0x12a, 0x12b); still left out as too long: 0x21, 0x98, 0x248.
- `tools/audio_extra.py WORK RENDERS` (+ `tools/sound_extra.txt`): patches the finished `WORK/audio/rNNN.bin` packs (the first run keeps the originals as `WORK/audio_orig`, every run starts from them) instead of rerunning the census (the original census and route-census inputs are not in the repo). It adds the 14 where the census list or `sound_extra.txt` ("STAGEHEX CMDHEX USES") names them and the arcade plays them in that stage (route uses from `sound_rank.json`, or the MAME counts of the coverage logs). Fit rule = the rounds_config rule: SCSP room 0x7e000; score = route uses x 1000 + 500 for sounds every stage keeps; the lowest scored clips of the file go first; the plan is dropped (clip left out, reported) if it would cost more route plays than the new clip brings. Run it before `build.py`: `python tools/audio_extra.py WORK E:\AvP\learning\lane-audio`; renders are generated data (E:\AvP\learning\lane-audio sfx.wav sfx.tsv sounds.json), nothing is committed.
- Tile data is untouched: stage 0e still drops 659 keys (the 0e family 11 files, max 941 as before), stage 24 drops 0; budgets high RAM 72, low RAM 508, cart tail 2,332 (same as fix7c1; only audio data changed). ISO 326.5 MB (fix7c1: 326.1).

## Where each command plays (Saturn run against the MAME log of the same moment)
Saturn column: audio frame relative to the anchor music request of the scene (same anchor in MAME: story 0x1a, ending 0x1b, stage music), `STARTED` = the library started a clip (`sfx_started`), slot = the SCSP slot carrying it (per-slot mean |output| from 0 to the value shown, frames above 0 after the request). The raw captures were deleted after the checks (disk). Kept: runs/gA_*/trace.log (SLOTE lines: slot energy per 1/60 s) and audpoll.txt (every request and its outcome). The slot trace is the clean evidence because music and other effects share the mix; the 0.4 s RMS of the mix before and after a request is dominated by the music, so it is not proof.
| cmd | scene | MAME rel frame | Saturn rel frame | result |
|---|---|---|---|---|
| 0x156 | story (character intro) | +422 | +422 | STARTED, slot 13 0 to 325, 52 frames |
| 0x04f | front end story | +706 (also 2 later) | +706 | STARTED, slot 9 |
| 0x08e | story end | +916 | +916 | STARTED, slot 15 0 to 447, 64 frames |
| 0x14f | character select | +932 | +932 | STARTED, slot 13 0 to 451, 48 frames |
| 0x14e | character select | +948 | +948 | STARTED, slot 14 0 to 465, 32 frames |
| 0x08e 0x14f 0x14e | ending epilogue (ENDING entry) | +129 +150 +207 (MAME warp run, paced differently) | +955 +1067 +1371 | all STARTED, slots 15 / 13 / 14 active 150 to 164 frames; same order. The two timelines differ in pace because the MAME run was warped with clear flags and its credits ran faster; not a sound difference |
| 0x067 | stage 6-2 (14) | +1 | +1 | STARTED, slot 15 0 to 1,293, 394 frames (later request +1845 against +2561: state dependent) |
| 0x087 | stage 6-2 | +17 | +64 | STARTED, slot 15 |
| 0x067 | stage 6-5 (1a) | -66 | -452 | STARTED, slot 15 0 to 1,289 |
| 0x07f | stage 3-1 (0a) | +7, +49 | +23, +343 | STARTED, slot 15 0 to 1,011 |
| 0x07f | stage 6-1 (12) | -600, -126 | -600, -126 | STARTED, exact |
| 0x056 | stage 7-2 (1e), mash bot | +372, +384, +511 ... (48) | +878, +883, +888, +1038 ... | STARTED, slot 12, 25 to 39 frames each |
| 0x064, 0x134 | stage 7-3 (20), mash bot | +884 / +1836 | +573 / +1070 | STARTED, slots 11 / 13 (0x064 refused once by priority, as the arcade's channel rule) |
| 0x05b, 0x12c | stage 7-3 (20) | +1149 / +1370 | +2166 / +2630 | STARTED, slots 10 / 11 |
| 0x094 | stage 7-4 (22) | -35 | -396 | STARTED, slot 14 0 to 1,244, 396 frames |
Stage moments depend on what the player does (the Saturn runs use an idle player or a mash bot, MAME its own bot), so only the story, select and the exact 6-1 match are frame for frame; the others show the same sound starting on the same channel. Not triggered in my Saturn runs (the arcade logs have them, the route census uses them): 0x05b / 0x064 / 0x12c / 0x134 in 5-1 (10) and 0x067 in 2-1 (06); their clips are in those files.

## Budget (SCSP room 0x7e000 bytes of header, tables and clips), base stage files; the 134 variant files of the census follow the same plan
| file | added | dropped (route uses) | not fitted | free before | free after |
|---|---|---|---|---|---|
| front | 8e 14e 14f 156 4f 26d 252 | none | none | 171,978 | 119,978 |
| 2-1 stage06 | 67 | 5f(2) 12f(2) 140(4) | none | 942 | 6,428 |
| 3-1 stage0a | 7f | 114(0) 35 100 36 101 (any) | none | 1,314 | 1,360 |
| 4-2 stage0e | none | none | 56 | 1,212 | 1,212 |
| 5-1 stage10 | 64 134 5b 12c 56 | 81(9) 20e(9) | none | 224 | 2,592 |
| 6-1 stage12 | 7f | 10b(1) 42(1) | none | 554 | 2,088 |
| 6-2 stage14 | 67 87 26d 252 | none | none | 51,364 | 14,178 |
| 6-5 stage1a | 67 | 111(1) 22a(2) 237(3) | none | 540 | 6,544 |
| 7-2 stage1e | 56 | 22a(4) 233(6) | none | 566 | 3,544 |
| 7-3 stage20 | 64 134 5b 12c | 12e(8) 20e(9) 22a(9) | 56 | 1,022 | 552 |
| 7-4 stage22 | none | none | 94 | 1,474 | 1,474 |
| ending stage26 | 8e 14e 14f 156 | none | none | 167,254 | 152,674 |
Files that cannot take a command, and what I would trade: **0x056 in 4-2 and 7-3 and 0x094 in 7-4** have one to few route plays and need 4 to 6 KB; the cheapest victims are the 500 point KO/continue/game-over clips (0x42, 0x4b, 0x70, 0x13b) or a 2 play clip, and the plan costs more than the clip brings, so they stay out. Net route plays: 5-1 gives up 18 plays (0x81, 0x20e) for five new sounds, 7-3 gives up 26 (0x12e, 0x20e, 0x22a), 7-2 gives up 10, 6-5 gives up 6, 2-1 gives up 8, 6-1 gives up 2; each against more new route plays than it loses (the census counts). If the owner would rather keep those clips, give the clip a lower use count in `tools/sound_extra.txt` or drop the stage line there; the census-list additions follow the same score rule, so a stage where the new sound has fewer plays than the clips it would replace is already left alone.

## The 0x026d game-over loose end
Not a game-over sound: **0x026d is the name-entry jingle (a score that ranks) and 0x0252 the ranking page jingle**, both played while the STAGE file is loaded.
- MAME with the scoring bot (`mame\runs\go1`): 0x026d at f=6916 after the continue countdown, then ranking music 0x03. MAME with an idle player (score 0, `mame\runs\gA_idle`): no 0x026d, music 0x03 at f=6776 and 0x0252 at f=6795, the same sequence my first idle Saturn run had. So the Saturn takes the same path.
- Saturn with a scoring mash bot (`runs\gA_go`): 0x026d requested at the same point (2,000 frames after the continue music) and **unknown** there: it is in the table of the ending file only (stage26), no stage file and not the front end. Same for 0x0252.
- Fix: added to the front end (ranking after the reload), the ending file and stage 6-2 (free room). Verified in stage 1-1 before it was taken out again: with the stage file holding it, 0x026d STARTED (slot 10 0 to 1,212, 65 frames, `runs\gA_go3`). **The other stage files have no room: 0x026d + 0x0252 are 24.8 KB, and the cheapest way in is the table below (cost of the route plays each file would lose, from the patcher with 100 uses; "any" = KO/continue/game-over clips).** I did not take that trade; it is the owner's call (name entry is silent after a game over in every stage except 6-2, as before; in the front end and the ending it plays).
| stage file | route plays lost | any sounds lost | unused clips dropped |
|---|---|---|---|
| 1-1 | 0 | 6 | 0 |
| 1-2 | 10 | 0 | 1 |
| 2-1 | 17 | 0 | 0 |
| 2-2 | 8 | 1 | 0 |
| 3-1 | 2 | 13 | 1 |
| 4-1 | 21 | 0 | 0 |
| 4-2 | 36 | 0 | 0 |
| 5-1 | 45 | 0 | 0 |
| 6-1 | 16 | 0 | 0 |
| 6-2 | 0 | 0 | 0 (fits free) |
| 6-3 | 12 | 0 | 0 |
| 6-4 | 26 | 0 | 0 |
| 6-5 | 35 | 0 | 0 |
| 7-1 | 51 | 0 | 0 |
| 7-2 | 30 | 0 | 0 |
| 7-3 | 64 | 0 | 0 |
| 7-4 | 12 | 0 | 0 |
| 7-5 | 26 | 0 | 0 |
Cheapest to take: 1-1 (the most played stage) costs six of its KO/continue clips (0x42 0x43 0x44 0x48 0x113 0x4b) and no route play; 3-1 costs 2 route plays and 13 KO clips.

## Still silent (not in the 14)
0x084 and 0x098 (ending epilogue: 0x098 UNKNOWN in the ENDING run), 0x021, 0x248 (too long even as loops, or no steady period), 0x5a / 0x12a / 0x12b (loops now rendered; in no census list).
