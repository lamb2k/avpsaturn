# Loading screens: what happens, what it costs, what to change (lane loading, 2026-11-12)

Branch `lane/loading-20261112` (private-origin), base `lane/perf-hw-20261112` at fd88228 (fix7p2). Worktree `E:\AvP\worktrees\loading`, evidence `E:\AvP\learning\lane-loading`.

**Labels.** EMULATED = my own Ymir (below). MODELLED = arithmetic on EMULATED numbers or on a stated assumption. CONSOLE = owner photos only: none for this note, nothing here is a console measurement. The owner's console runs from a Fenrir SD card (an optical drive emulator); that matters for seeks (section 2).

## 1. Short answer

- **Almost every wait is a file read.** Boot to a usable title menu is 44.6 s EMULATED, of which 11.3 s is the BIOS, 13.9 s the loader (5 files, 2,003 sectors), 8.4 s the front end file, 11 s the arcade's own copyright/title sequence. A stage, boss, versus arena or ending load is 7.6 to 12 s behind a black NOW LOADING card; game over and quit to title each re-read the front end file (8.5 s).
- **Menus, story, character select, continue and stage-to-stage screens that are not a file load cost nothing:** no CD sector read, the slave draws a new picture in every vblank (59 to 60 swaps a second), no stall.
- **The drive is not the limit, the number of reads is.** A load runs at 107 to 123 sectors/s against 150 at 2x. Each stage file starts with 36 to 94 tiny regions (1 to 50 sectors) that are read one by one; every read is a CD block play command. Reading them in one go (`SAT_LOAD_COALESCE`, landed default off, byte-exact) takes 1.0 to 1.9 s off each load in Ymir.
- **The big remaining lever is the amount of data.** Round files compress to 0.49 (front end) and 0.62 (stages) of their size with zlib, the boot files to 0.44 to 0.55. Not implemented (proposal 2).
- **One transition is worse than the rest and inconsistent:** quit to title shows the frozen pause menu for 8.7 s with no NOW LOADING card, then black 2.5 s, then the arcade copyright and warning screens (proposal 3).

## 2. Method and what Ymir models

Own copy of the Ymir baseline (a9f0cdae, `C:\Game Dev\Emulators\Ymir-baseline-a9f0cdae`), patched only to log (sources and build in `E:\AvP\learning\lane-loading\ymir`: `cdblock.cpp`, `vdp.cpp`, `vdp_renderer_sw.cpp`, `pad.cpp`, `build.bat`): every CD play/seek command and every data sector read with its FAD, every VBlank-IN, every VDP1 frame-buffer swap, every pad change, and a hash plus a black-pixel count of every finished frame, all stamped with the scheduler's master clock cycle count. Seconds are derived from the VBlank-IN stamps (59.83 Hz, 478,660 master cycles a frame in the 352 mode), so every time below is emulated time, not wall time. Real JP BIOS, 4 MB RAM cart, SH-2 cache on, stock bus costs, software renderer, HLE CD block (`UseLLE = false`), `ReadSpeed = 2`. Pad only by file (`ymir_pad.txt`), no window input, window labelled, no focus taken.

What Ymir's CD block models (read from `cdblock.cpp`, `cd_drive.cpp`): 150 sectors/s at 2x (one drive tick per sector, 6.67 ms; 13.3 ms at 1x, used for audio tracks); the 200 buffer CD block with the drive pausing when the buffers are full; the SCSP CDDA pacing; a fixed 5 drive ticks (33 ms) for **every** play command, whatever the distance (`kSeekTicks = 5`, "TODO: calculate realistic seek time"); the BIOS's own power-on sequence, which runs as it would on a console.
What it does not model: seek distance or head travel, spin-up and CLV speed changes, rotational latency (a read of the sector that just went by costs a turn on a drive), retries, the SH-1's real firmware timing. So: transfer time is right, a flat 33 ms per read command stands for everything else, and **a real optical drive would pay more for every far jump (stage files have 2 or 3 runs, 22,000 to 79,000 sectors apart) and for every tiny read**. A Fenrir (ODE) has no head: its per-command latency is unknown to me (ASSUMED small), so Ymir's flat figure may be close for the owner's console. Console numbers are needed before the seek proposals are priced.

Routes (scripts `route.py`, `lroute.sh`; the wait in every step is in emulated frames, so a run repeats): shipping disc `avp_3h_A_fix7p2` (EMULATED runs r1 to r7), then my builds L1 to L3 (recipe of fix7p2 plus the switches of section 4). Screenshots every 4 to 5 emulated seconds, plus per step, in `ymir\runs\<run>`. Tools: `an.py` (trace parse), `loads.py` (CD bursts per load, file named from the ISO and the STORE run table), `summ.py` (picture gaps), `blank.py` (black frame stretches).

## 3. Transition inventory (EMULATED, shipping disc fix7p2, stock Ymir CD model)

"Dead" = the time from the last live picture to the next live picture: the slave stops drawing (no VDP1 swap) while GFS reads with interrupts masked. All dead times below are exactly a file read.

| # | Transition | Files read (sectors) | CD time | Screen | Dead time |
|---|---|---|---|---|---|
| 1 | Power-on to title menu | BIOS: IP `0.BIN` 17 (7.1 s). Loader, in this order: `LW.BIN` 511, `ROM.BIN` 1,024, `OPX.BIN` 127, `COLD1.BIN` 65, `HW.BIN` 276 = 2,003 sectors, 4 jumps back (11.3 to 25.2 s). Then the front file R286, 901 sectors, 1 run (25.4 to 33.8 s) | 22.5 s from first loader read to the end of the front file (129 sect/s) | black 0 to 1.8 s, BIOS shards and SEGA SATURN logo to 6.8 s, SEGA licence text to 11 s; loader progress screen (grey, coloured bands, a tick moving per 128 sectors) 11.3 to 33.9 s; the game's own red copyright and WARNING text 33.9 to ~40 s, title logo 40 s, menu list 44.6 s | 44.6 s power-on to menu; 22.6 s of progress screen, never blank after the BIOS |
| 2 | Title, ARCADE, intro story, character select | none | 0 | story plays (A skips), select with its 15 s timer | 0: no stall, 59 to 60 swaps/s throughout |
| 3 | Character select to stage 1-1 | `R020` 539 + `R001` 551 + 3 head/table sectors = 1,093 sectors in 7 runs | 8.9 s (122 sect/s) | select held 2.5 s after the press (pick, the 12 vblank settle), then black **NOW LOADING** card, bottom right | 9.0 s card (+2.5 s select hold = 11.6 s from the press) |
| 4 | Stage to stage (stage word change): the real case is stage 24 clear to the ending | `R205` 217 + `R019` 695 = 914 sectors | 7.6 s | NOW LOADING card, then the ending scenes | 7.6 s. Every other stage change is the same path as 3 (file size 912 to 1,481 sectors, 6.1 to 9.9 s at 150/s) |
| 5 | KO, CONTINUE?, Start, character choice, back in play | none | 0 | CONTINUE? countdown 20 s over the held stage; select overlay; play resumes | 0 |
| 6 | Continue countdown expires, GAME OVER, ranking, title | R286 front file again, 901 sectors | 8.45 s | GAME OVER card (live), black NOW LOADING card, BEST 50 HUNTERS ~9 s (live), title | 8.5 s card |
| 7 | Pause, QUIT TO TITLE | R286, 901 sectors, loaded by `sat_main` after a full restart | 8.45 s | **the pause menu stays frozen, no NOW LOADING**, 8.7 s; then black 2.5 s; red copyright, WARNING ~5 s; title; menu about 18 s after the press | 8.7 s frozen + 2.5 s black |
| 8 | VERSUS: rules, select, arena | `R211`, 1,032 sectors, 1 run | 8.5 s | NOW LOADING card, ROUND I card (live), fight | 8.6 s card |
| 9 | STAGE SELECT: title, select, list, Start | `R020` + `R001` as 3 | 8.9 s | black hold ~0.3 s from title to select; card | 9.0 s card |
| 10 | BOSS RUSH start | `R030` 312 + `R002` 910 + 3 = 1,225 sectors, 6 runs | 10.0 s | card | 10.1 s |
| 11 | STAGE SELECT, ENDING entry (run `le` on build L1, same layout class) | `R194` 253 + `R195` 1,178 + 3 = 1,434 sectors | 12.0 s | card | 12.1 s |
| 12 | Ending to title | R286 | 8.45 s | ending credits (live), card, then front end | 8.5 s card |

Not measured: the post-credits reveal (Wolverine overlay: `REVCODE.BIN` 1, `REVEAL.BIN` 82, `RVVOICE.BIN` 14 sectors, a few seconds at most; needs a cleared game with him switched on), second-player join mid-stage (a character joining takes its file at the next stage word, no extra load seen), mixed variants other than Predator Warrior solo. Music: CDDA tracks share the drive; the game restarts music after each load (`sat_audio_resume_music`).

Every load goes through `round_check` (kernel.c) except the front end file in `sat_main` (rows 1, 7, 12 first read). Each round file is a list of regions: region 0 the sound data (251 sectors, to the pack room at 0x02654000, taken into SCSP RAM by the `mark` call), 36 to 94 tiny regions of 1 to 50 sectors (arcade ROM pages the stage restores, to 0x2400000 to 0x25ff000), the big tile region (460 to 788 sectors, back into the pack room); stage files also end with 4 more tiny regions in some variants. Median file: 48 tiny regions, 42 of them ahead of the tile region, 161 sectors of them.

**Why a load runs at 107 to 123 sectors/s, not 150 (EMULATED).** Trace of the stage 1 load: sectors 74.37 to 75.8 s arrive one every 37 ms (53 sectors in 1.4 s): each tiny region is its own GFS read, so each is a new play command with its 5 tick (33 ms) seek. Overhead per load: front end 2.4 s (69 tiny reads), stage 1.6 s. That is what `SAT_LOAD_COALESCE` removes.

## 4. What I landed (all default off, in the tree)

### 4.1 The TR readout line (`SAT_TR_LINE`, `saturn/rt/fps_hud.c`, `kernel.c`)

One extra line on the readout, row 20, above PROF (row 21). The LD, TICK/CUT, HW and PROF lines are unchanged.

`TRn ffff>tttt Ts.t [L]`: the n-th transition since boot that left the screen without a new picture for at least 12 vblanks (0.2 s), the scene code left and the scene code arrived at, the time, and `L` when a file load was inside it. Scene code: high byte = the game's mode byte ff8001 (bit 7 added while ff81b0 is nonzero: attract, title, ranking), low byte = the stage word's low byte ff81e9 (00 = front end). Time: seconds and tenths with no new slave picture. With `L` it is the load's whole-second clock (the D of the LD line, +-1 s, because GFS runs with interrupts masked and the vblank count stands still) plus the vblanks that followed; without `L` it is counted in vblanks (1/60 s). The power-up and restart front end load (`sat_main`) is timed with the same clock through `sat_fps_boot`.

Implementation: a cold function in the cart (`sat_fps_vb`) called once per vblank from the existing slave-watchdog block in the vblank handler (kernel.c: 3 lines), reading the slave's picture counter and 4 game bytes; 14 words of cart data. Cost (same recipe, same base, L3 against `perf-hw` P5): **cold1 grew about 700 bytes** (cold1_at 0x027df000 to 0x027de000, one 4 KB step down; cart tail free 2,372 to 5,752; Wolverine block still outside the ROM image, canary ok); high RAM free 56 (unchanged), low RAM free 2,376 (P5 2,392: 16 bytes).

A finding that shapes it: in menus, story, select, continue and stages the slave draws a picture every vblank, so a transition without a file read never opens a stall and the line does not fire for it. That is the answer for rows 2, 5 (continue) and the story. Only file loads (and the restart) stop the pictures.

**Ymir proof (EMULATED).** Final build L3 (source b0882b6c, readout id `F2 B0882B`), one route: boot, ARCADE, Predator Warrior, stage 1, KO, game over, ranking, title, ARCADE again, stage 1, pause, QUIT TO TITLE, ARCADE again, stage 1 (`runs\l3a`, `runs\l3b`; screenshots `runs\l3a\crops.png`, `runs\l3b\after2_crop.png`):

| readout | Ymir truth (trace: picture swaps stopped, CD time) |
|---|---|
| `TR2 0200>0202 T8.0 L` after select to stage 1 (`LD1 F20 S1090 D8`) | no swap for 8.17 s, CD 7.88 s |
| `TR3 0202>0200 T7.0 L` after game over (front end file) | no swap for 6.77 s, CD 6.55 s |
| `TR4 0200>0202 T8.0 L` after the next stage 1 | no swap for 8.16 s, CD 7.88 s |
| `runs\l3b` (boot, stage 1, quit to title, ARCADE, stage 1): `TR4 0200>0202 T8.0 L` after the second stage load | the restart's front end load is counted as TR3 (TR1 boot, TR2 stage 1, TR3 restart, TR4 stage 1) |

TR1 is the power-up front end load (`sat_fps_boot`); the readout is not legible during the restart's copyright screen (the font cells are redrawn at the next menu, as on the shipping disc), so the restart's own TR line was not photographed, only counted. Times agree with the truth to the whole second the clock gives. On the shipping-recipe build L1 (before the left-scene fix) the same lines read `TR1 0202>0202 T9.0 L`, `TR2 0200>0200 T8.0 L` for CD 8.93 s and 8.45 s (`runs\la\crop_stage1.png`, `crop_ranking.png`).

### 4.2 `SAT_LOAD_COALESCE` (`saturn/rt/boot.c`, loader, BOOT_CFLAGS)

Reads a run of consecutive tiny regions as one `vread` into the pack room (region 0's address, whose sound part the `mark` call has already taken, and which the big tile region overwrites afterwards), then copies each to its address. Conditions: SECTOR_STORE variant, region 1 is the mark, region sizes 1 to 64 sectors and whole sectors, addresses multiples of 4, group size at most region 0's size. The staged bytes are read through the cache-through alias (the first try read them cached and the game booted to black: the CD transfer writes behind the cache).

Byte-exact proof (`SAT_LOAD_SUM`, test flag: a rotating sum of every region's bytes read back from its address, kept at 0x06013fb8/fbc and logged by the route): sums from Ymir equal the sums computed offline from the disc (`expsum.py`, each build's own ISO) for every load checked: L2 boot front end R286 `650be99a`, R020 `1bcab080`, R030 `11ea4562` (stage word 4), R286 after game over `650be99a`; L3 five loads R286 `169b5023`, R020 `1bcab080` (twice), R286 after game over and after the quit `169b5023`. 

EMULATED effect (stage loads from select, same route, same disc layout, switch off L1 vs on L2/L3):

| load | sectors | before | after | saved |
|---|---|---|---|---|
| front end R286 (boot) | 901 | 8.45 s | 6.55 s | 1.9 s (22 %) |
| stage 1 R020+R001 | 1,093 | 8.93 s | 7.88 s | 1.05 s (12 %) |
| boss R030+R002 | 1,225 | 9.96 s | 8.79 s | 1.17 s (12 %) |
| rate | | 107 to 123 sect/s | 139 sect/s | |

The same switch on a console is expected to save at least as much (a drive loses a turn between two reads of neighbouring sectors, Ymir charges 33 ms), but that is MODELLED reasoning, not measured.

### 4.3 `SAT_BOOT_DISC_ORDER` (boot.c)

The five boot files in the order they lie on the disc (COLD1 43, HW 109, LW 385, OPX 896, ROM 1106) instead of LW, ROM, OPX, COLD1, HW. Same bytes to the same addresses; failure codes unchanged. EMULATED: the loader's 2,003 sectors take 13.9 s either way (11.3 to 25.2 s): Ymir charges a flat 33 ms per command and no distance, so it cannot show a gain (4 fewer jumps back; 34 seeks instead of 99 in the log is the coalesce plus the order). Worth keeping because it is free and exact; its value is on an optical drive and is MODELLED only (4 jumps at an assumed 0.15 to 0.5 s = 0.6 to 2 s).

### 4.4 Gates

- Build gates on L1, L2, L3 (all pass): `vdp2_cycle_check` PASS; alignment static gate 326 data symbols (0 of unknown type), 48 cast sites (46 reviewed before + 2 new reviewed lines in `tools/align_sites.txt`: the coalesce copy and the test sum), 197 accessor calls, 287 round files and `REVEAL.BIN`, 0 hits; boot data addresses ok; Wolverine block canary ok; budgets on L3: high RAM free 56, low RAM free 2,376, cart free 5,752 (cold1 moved down a 4 KB step); L1 72 / 2,424 / 5,836.
- Tests: `tests/align_gate_test.py` (13 ok), `tests/lat_protocol_test.py` PASS, `tests/vdp2_cycle_check_test.py` PASS.
- Ymir misalignment gate (`tools/ymir_misalign_gate.py --run`, my copy of the strict exe with its log path moved to my folder, disc L2, default route boot, title, arcade, stage 1, KO, continue with another character): **0 data accesses** (6,094 instruction fetch artefacts filtered): `gate_misalign_L2.txt`.
- TICK in stock Ymir, stage 1 steady play (L2): `TICK 60 CUT 28`, `PIC 60 DONE 60 MISS 0 SKIP 0 HELD 0` (screenshot `runs\l2e\play2_crop.png`). One window straight after a load reads lower (the catch-up of the load, `TICK 44`), as documented in the fix7n4 note.

## 5. Proposals, ranked by time saved per risk (none changes gameplay)

Saved times are EMULATED (Ymir) unless marked MODELLED.

1. **Turn `SAT_LOAD_COALESCE` on in the recipe** (landed, verified byte-exact). 1.0 to 1.9 s per load, every load: boot front 1.9 s, each stage/versus/boss 1.0 to 1.2 s, game over and quit to title 1.9 s. Risk low: loader only, sums identical on 4 loads, alignment and misalignment gates clean. Needs one console session to confirm; if the console is slower per read (likely) the gain is larger. **Do first.**
2. **Compress the round files and the boot files (not implemented).** zlib level 6 on the shipped bytes (`zlib` sizes in `AVP_LOADING_20261112_data.txt`): front end R286 0.49, stage files 0.61 to 0.64, `LW` 0.44, `ROM` 0.44, `OPX` 0.55, `HW` 0.53, `COLD1` 0.49; sum over the 13 sampled round files 0.61. With a lighter LZSS-class coder the gain is smaller (ASSUMED 85 to 90 % of zlib's): stage load 7.9 s to about 5.2 s, front end 6.5 to 3.5 s, boot loader 13.9 to about 7.5 s; **power-on to menu from 44.6 s to about 34 s, every stage 2.5 to 3 s** (MODELLED from the table; decode time is free next to a 300 KB/s drive). Needs: an SH-2 decoder in the loader, per-region compression in `sector_store.py`, a scratch buffer (the pack room already serves as staging in the coalesce path), the pack and alignment gates re-run. Risk medium; the largest saving. Do after 1.
3. **Same card for quit to title (not implemented).** The pause picture stays frozen for 8.7 s and nothing says why, then 2.5 s black and 5 s of arcade copyright and warning text. The restart goes through `sat_main`, which loads before it has any picture of its own. Show the NOW LOADING card before `sat_home_restart` jumps (a few lines in `home_cold.c`, `sat_home_loading(1)` already exists), and consider skipping the arcade boot text on a restart (arcade code, outside this lane: ask). Saves no time; removes the one frozen-picture load. Risk low.
4. **Preload the next stage during stage-end screens (not feasible as asked).** The pack room (0x02654000 to 0x027de000, 1.6 MB) holds the live stage's tiles and has no twin; cart is full (ROM image 2 MB, cold code), low RAM free 2.4 KB, VDP and SCSP RAM hold the live uploads. The stage end screens still draw from the live pack. A preload needs a second 1.6 MB buffer that does not exist. Only a partial form exists: read the sound part (251 sectors, 1.7 s) of the next file into spare memory, which also does not exist. Dropped unless compression (2) frees 0.6 MB, then re-open: the compressed next file (about 1 MB) still would not fit.
5. **Fewer seeks: store layout and file order (not implemented).** Stage files are 2 or 3 runs: a stage-specific run plus the shared run(s) at the start of STORE.BIN, 22,000 to 79,000 sectors apart (`store_runs.json`). Ymir cannot price it (flat 33 ms). On an optical drive a jump that far is a full seek; on Fenrir probably nothing. MODELLED only: 1 to 2 jumps per load at an assumed 0.15 to 0.5 s = 0.15 to 1 s of 8. Needs a console number first. Boot order: landed as 4.3.
6. **Merge the boot files into one file.** Saves the GFS open and the directory reads per file (about 0.08 s each in Ymir, 5 files = 0.4 s) and, with the disc order switch, nothing else. Low value, build-side change. Behind 2, which touches the same files anyway.
7. **Keep the last picture or a proper card.** The card exists and covers every load except quit to title (3). A progress bar while loading is possible only between GFS reads (the 128 sector chunks of `vread`, as the boot display's tick does) and shows nothing the owner can use; not recommended.

Not for this lane: BIOS 11.3 s, the arcade's copyright, warning and title sequence (5.5 s of it before the menu), the continue and ranking timers.

## 6. Housekeeping

Intermediate discs and builds (`iso_L1/L2/L3.iso`, `disc_L1/L2/L3`, `wd`, `wd2`, `wd3`, `src_*`) are deleted after the gates: see `E:\AvP\learning\lane-loading\DELETED-20261112.txt`. The Ymir exes in `ymir\run` stay (mine). Evidence kept: `ymir\runs\*` (traces, screenshots), `an.py`, `loads.py`, `route.py` and the patched Ymir sources. Branch pushed to private-origin only; no owner disc staged; the readout change is for the orchestrator to fold in (flags: `-DSAT_TR_LINE` in KERNEL_CFLAGS; `BOOT_CFLAGS=-DSAT_LOAD_COALESCE -DSAT_BOOT_DISC_ORDER`).
