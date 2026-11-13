# SAT_LOAD_LZ: compressed boot files and round tile regions (lane loading, 2026-11-13)

Branch `lane/loading-lz-20261112` on private-origin (the lane's `lane/loading-20261112` rebased onto fix7q2, `628bab5b`; same commits), worktree `E:\AvP\worktrees\loading`, evidence `E:\AvP\learning\lane-loading`. Switch: `BOOT_CFLAGS=-DSAT_LOAD_LZ` (with `-DSAT_LOAD_COALESCE -DSAT_BOOT_DISC_ORDER`), default off, the builder follows the flag (`saturn/rt/build.py`, `tools/sector_store.py`, `tools/lzstore.py`). Labels: EMULATED = my own stock Ymir (real JP BIOS, 2x CD, flat bus costs); MODELLED = the perf-hw lane's region-aware cost model (`HW_MODEL=1`, my copy `ymir2-hw.exe`); CONSOLE = none, nothing here is a console measurement.

## 0. First, a correction to my earlier note

`SAT_LOAD_COALESCE` as I first delivered it staged tiny regions over the first 130 sectors of the pack room after the tile region had been read and corrupted the tile data of 157 of 287 round files. The first `SAT_LOAD_SUM` (rotating xor) could not see it: it cancels over overlapping regions. Fixed in `18921a6b` (coal_big; multiplicative sum; `tools/loading/coalesce_replay.py` replays the loader over all 287 files: 0 differ), taken into fix7p3. Everything below uses the fixed code and the multiplicative sum.

**Update 2026-11-13 (fix7p5): section 10 supersedes the numbers of sections 1, 4, 7 and 9 below: faster inflate, one read a file, all 287 files compressed, versus no longer slower; power-on to title 31.2 s, loads 1.3 to 1.6 s shorter than plain (EMULATED).**

## 1. Result in one paragraph

Compression pays on the boot and on every file load, by less than the CD figures alone suggest because the SH-2 decodes slowly (about 70 cycles per output byte for deflate), so the decode is the limit once it is overlapped with the read. EMULATED, same route, fix7p3 recipe against the same recipe with `SAT_LOAD_LZ`: **power-on to the title logo 38.2 s to 33.5 s (-4.7 s)**; stage load 8.0 s to 7.2 s (-0.8 s); game over / quit to title / ending to title 6.5 s to 5.9 s (-0.65 s); Boss Rush -0.7 s; stage 24 to the ending -0.7 s; versus +0.4 s (worse: its file is many short runs). MODELLED agrees: stage 1 8.09 s to 7.49 s, boot -5.2 s. Every load is byte-exact (section 5). It is a modest gain on loads and a real one on the boot; the next step is a faster decoder (section 7).

## 2. Codec choice (measured)

Ratio of compressed size to raw, per independent chunk, on the shipped bytes of `avp_3h_A_fix7p2` (2 KB = the unit of the sector store, 8 KB = what a boot file could use). `lzbench.c` (byte LZ4-style, LZSS 12/4 and 10/6, a word-aligned LZSS) and zlib (deflate level 9, order-0 Huffman only):

| file | LZ4 2K/8K | LZSS12/4 2K/8K | word LZSS 2K/8K | Huffman only 2K/8K | **deflate 2K/8K** |
|---|---|---|---|---|---|
| stage R020 | .868/.834 | .838/.798 | .888/.857 | .716/.724 | **.664/.648** |
| stage R190 | .864/.829 | .836/.792 | .885/.852 | .711/.717 | **.663/.644** |
| front end R286 | .692/.655 | .669/.642 | .698/.672 | .634/.660 | **.527/.508** |
| ROM.BIN | .585/.543 | .577/.550 | .583/.551 | .651/.663 | **.496/.460** |
| LW.BIN | .776/.667 | .776/.658 | .780/.671 | .884/.864 | **.686/.574** |
| HW.BIN | .819/.724 | .817/.715 | .827/.735 | .883/.867 | **.715/.616** |
| OPX.BIN | .777/.691 | .766/.690 | .788/.711 | .830/.818 | **.675/.599** |

Byte LZ stops at 0.79 to 0.87 on the tile data (it is 4 bit pixels with a small palette: the gain is in the entropy coding, not the repeats), so a decode that costs 6 to 15 cycles a byte (LZ4 class) saves 13 to 21 % of the CD and does not repay its decode on a stage; order-0 Huffman is good on the tiles (0.72) and useless on code. **Deflate (LZ77 + Huffman) wins on every file** and is a standard format: the builder needs only zlib, the loader a 1.4 KB decoder. LZMA reaches 0.41 to 0.54 but is out of reach of a 28 MHz SH-2. Decode cost, EMULATED in the loader: **about 3.8 s per 1.6 MB tile region before the decoder was tuned (68 cycles per byte, stock Ymir; the SH-2 has no variable shift, so the hot loop uses multiply based shifts and keeps the bit buffer in locals)**; with the decode overlapped with the read the measured loss per load is the 1.5 s tail in section 4. MODELLED (HW_MODEL=1): the same tail, 1.7 s.

## 3. Design

- **Where it decodes.** In the loader (`saturn/rt/boot.c`, resident at 0x06004000, its own region below the runtime image): the loader's bss grows by 6.5 KB (decoder tables 2 KB, 8 KB tail scratch) and `names[256]` shrinks to 64 (the disc has 14 root files), end of loader bss `0x06013c50` against the limit `0x06013fe0`. **Nothing in the runtime's high RAM (72 free), low RAM (500 free) or cart (2,372 free) changes**: the kernel is untouched by this switch.
- **Boot files** (LW, ROM, OPX, COLD1, HW): the five ISO files are replaced by 32 KB-block deflate streams (header sector `LZB1`), read into the end of their destination and decoded forward **in place**. Decodable before high RAM is set up: the decoder needs only the loader's own memory and the destination.
- **Round files**: the tile region of each file (the first region after the mark larger than 64 sectors; 218 K of the 342 K sectors) is taken out of the stream and stored as compressed blocks in a blob area of STORE.BIN. Blocks are the pieces (at most 32 sectors of raw data) of the distinct runs of the deduplicated tile data, so the sharing between the variants of a stage survives and each piece is stored once. The head sector gets bit 0 of the region's byte count set and a unit table at byte 1024 (`tools/lzstore.py` header). Head, sound, tiny regions and everything after the tile region stay in the plain stream: **all of fix7p3's/7q2's round file contents (the 54 ROM patch pages included) are unchanged**, the builder only moves the tile region.
- **Overlap with the read.** The streams are read with GFS's non-blocking read (`GFS_NwFread` / `GFS_NwExecOne`, CPU transfer) into the end of the destination and each stream is decoded as soon as its sectors are in, while the drive reads on (`lz_stream`, `lzdec.h LzUnit`). The cache is switched on only around each decode step (the loader runs with the BIOS's cache off; GFS writes behind it) and purged on the way in.
- **In place, proven per file.** The decoder writes from the start while the streams sit at the end, so the last bytes of the region must not be overwritten before they are read: the builder finds, per file, the smallest `tail` (0 to 8,192 bytes, copied to scratch once everything has arrived) for which the loader's own `lz_unit` (the same source, compiled for the host as a DLL) decodes the unit exactly in place. A file that does not fit keeps its tile region in the plain stream: 11 of 287 with 32 sector pieces (the builder prints it), they load as before.
- **Disc**: store 150,430 sectors against 152,420 plain (pool 124,412 + blobs 26,015); the five boot files 2,000 sectors to about 1,030.

## 4. Before and after (EMULATED, same routes, fix7p3 recipe `L5B` against the same recipe plus LZ `L5`)

Swap gap = time with no new picture (the load's black card). Decode share = the part of the gap after the last sector arrived.

| transition | before | after | saved | CD busy / decode share after |
|---|---|---|---|---|
| power-on to title logo | 38.2 s | 33.5 s | -4.7 s | loader files: 15.2 s to 8.8 + 5.3 s CD, decode overlapped except about 1 s tail |
| select to stage 1 | 8.01 s | 7.20 s | -0.8 s | CD 5.7 s, decode tail 1.5 s |
| game over to front end | 6.52 s | 5.87 s | -0.65 s | CD 5.1 s, tail 0.75 s |
| quit to title | 6.69 s | 6.03 s | -0.65 s | same file |
| versus arena | 7.54 s | 7.97 s | **+0.4 s** | 22 runs, 24 seeks, decode tail |
| Boss Rush start | 8.99 s | 8.27 s | -0.7 s | |
| stage select ENDING arena | 11.88 s | 11.63 s | -0.25 s | |
| stage 24 to the ending | 6.64 s | 5.92 s | -0.7 s | |
| ending to title | 6.52 s | 5.87 s | -0.65 s | |
| continue, menus, story, stage select list | 0 | 0 | | no reads |

MODELLED (region-aware model, stage 1): 8.09 s to 7.49 s; boot to the end of the front end read 32.2 s to 27.0 s (-5.2 s).

## 5. Exactness

1. **Format and codec**, host: `lzhost.dll` (the loader's `lzdec.h`) decodes 7,283 zlib streams (stored, fixed, dynamic, Huffman-only, levels 0 to 9, 2 KB to 200 KB, real round and boot data) identically; also with the `__sh__` shift code path compiled on the host. `lzstore.py` rebuilds all 287 round files from the store with zlib alone (independent of the loader) identical to the originals, and runs the loader's `lz_unit` in place per file.
2. **In game, every file**: test build `SAT_LOAD_SELFTEST` (+ `SAT_LOAD_SUM`): the loader loads all 287 round files in turn, sums every region read back from its address and compares with the expected sums the builder wrote into the store header. Result: see section 8.
3. **Boot files**: byte-exact by the same construction (the builder decodes each boot file with the loader's `lz_unit` in place on the host and refuses the file unless the result equals the original, tail scratch included), and the game boots and plays from them on the final build (title, ARCADE, stage 1, KO, continue, game over, ranking, quit to title, versus, Boss Rush, the ENDING route: `runs\l6_a`, `l6_vs`, `l6_br`, `l6_end`). I did not diff the loaded images in Ymir memory.

## 6. Gates

Build gates (the build fails on them), final recipe build `L6`: see section 8. Misalignment gate, TICK: section 8.

## 7. What it does not do, and the next step

- The decoder is CPU bound: 70 cycles a byte (35 instructions plus the SH-2's branch costs per literal). The gain per load is about 0.7 s of an 8 s load because the CD time shrinks by 35 % and the decode (3.8 s per 1.6 MB, overlapped) is then the longer of the two. Halving the decode (16-bit refill loads, a two-symbol fast path, long stores to the cart) would take 0.7 s off every load again; deflate with `Z_HUFFMAN_ONLY` streams (no matches) decodes faster but compresses to 0.72 and was not measured. Not done.
- Sound regions (251 sectors) and tiny regions are not compressed (0.78 and 0.54 with deflate).
- The versus arena file is slower than plain (many short runs; 11 files stay plain).
- Boot files: LW and HW (code) compress to 0.54 and 0.58 but decode slower than they read; with the overlap the loader total is still 5.3 s shorter in all.
- Not done: console measurement; staging of the disc (waiting for the gates, section 8).

## 8. Gates and proofs on the final base (L6 = fix7q2's recipe + SAT_LOAD_LZ, source 9dfff96f, readout id `F2 9DFFF9`)

- **Every round file, in game (item 5.2):** the loader's self test on the final build (`L6T`, run `runs\st6`): **287 loads, 0 differ** (`sat_ld_diag`: loads 0x11f, fails 0, first failing none). The same on the build before the fix7q2 rebase (`L5T`, `runs\st5`): 287 loads, 0 fails. Each load is the SAT_LOAD_SUM (multiplicative sum of every region read back from its address) compared with the sum the builder computed from the original round file, so it covers boot front end, every stage and boss file, the versus arena files, the ending files and every character variant. The earlier first attempt of the self test hung on a stack clobber and a SUMS.BIN read: both fixed (history in the commits).
- **Build gates (the build fails on them), L6:** `vdp2_cycle_check` PASS; alignment gate 348 data symbols (2 of unknown type: counted, not failed; both are tables of the new loader code), 48 cast sites (no new reviewed site: the decoder has no cast of a non-literal pointer to a wide type), 199 accessor calls, 287 round files and `REVEAL.BIN`, 0 hits; boot data addresses ok; Wolverine canary ok; **budgets identical to fix7q2: high RAM free 72, low RAM free 500, cart tail free 2,372** (the switch touches only the loader); loader bss end 0x06013a50 against the limit 0x06013fe0.
- **Tests:** `align_gate_test` 13 ok, `lat_protocol_test`, `vdp2_cycle_check_test` PASS (unchanged files); `tools/loading/t_inflate.py` 7,283 streams, 0 bad; `lztest_store.py` all 287 rebuilt from the store identical.
- **Ymir data misalignment gate** (`tools/ymir_misalign_gate.py --run`, my strict exe copy, default route boot, title, ARCADE, stage 1, KO, continue): **0 data accesses** on L5 (7,064 instruction fetch artefacts filtered) and on the final L6 (7,135).
- **TICK 60 in play, stock Ymir (L6, stage 1):** `TICK 60 CUT 31`, `PIC 60 DONE 60 MISS 0 SKIP 0 HELD 0` (`runs\l6_a\play_crop.png`); L5: `TICK 60 CUT 14`, same PIC/DONE/MISS.
- **Routes played on L6 (EMULATED):** `l6_a` (boot, ARCADE, stage 1, KO, game over, ranking, title, ARCADE, stage 1, pause, quit to title), `l6_vs`, `l6_br`, `l6_end` (stage select ENDING: arena, ending, credits, front end). Times in section 4; the same routes on the fix7p3 recipe (`l5b_*`) are the baseline. HW-model runs `m5b` / `m5` (stage 1).
- **Staged:** `E:\AvP\package-integration\fenrir\avp_3h_A_fix7p4` (track01 = L6's ISO, 26 audio tracks as in the other discs, cue, README.txt, SHA256SUMS). The disc is on fix7q2 (`628bab5b`) as asked.

## 9. Known issues

- Versus is 0.4 s slower, 11 of 287 stage files are uncompressed (the in-place proof needs more than 8 KB of tail scratch for them).
- Gain per load is small (0.6 to 0.8 s) until the decoder is faster (section 7); the boot gain (-4.7 s) is real. The measure that decides is the console's: Ymir's CD model has no seek or rotational cost.
- `SAT_TR_LINE` stays in its own commits of the lane branch (not in this recipe).

## 10. Update 2026-11-13, fix7p5: faster inflate, one read a file, no uncompressed file

Source `f107798a` (readout id `F2 F10779`), branch `lane/loading-lz-20261112`, switch unchanged (`BOOT_CFLAGS=-DSAT_LOAD_LZ`, default off). Staged `E:\AvP\package-integration\fenrir\avp_3h_A_fix7p5` (track01 = `iso_L12`, SHA256SUMS). The kernel is untouched again: high RAM free 72, low RAM free 500, cart tail free 2,372, as fix7q2.

### 10.1 Result

EMULATED (my stock Ymir, same routes), seconds: fix7q2's recipe plain (`L12Q`), this lane's first disc fix7p4 (`L6`, v1 decoder), and fix7p5 (`L12`).

| transition | fix7q2 plain | fix7p4 (v1) | **fix7p5** | saved vs plain |
|---|---|---|---|---|
| power-on to the title logo | 38.18 | 33.50 | **31.16** | -7.0 |
| select to stage 1 | 8.01 | 7.20 | **6.42** | -1.6 |
| stage 1 again (second start of the route) | 7.99 | 7.20 | **6.44** | -1.55 |
| game over to the front end | 6.54 | 5.87 | **5.27** | -1.3 |
| quit to title | 6.67 | 6.03 | **5.42** | -1.25 |
| versus arena | 7.54 | 7.97 | **6.12** | -1.4 |
| Boss Rush start | 8.99 | 8.27 | **7.42** | -1.6 |
| stage select ENDING arena | 11.88 | 11.63 | **10.36** | -1.5 |
| stage 24 to the ending | 6.64 | 5.92 | **5.23** | -1.4 |
| ending to title | 6.54 | 5.87 | **5.28** | -1.3 |
| MODELLED, stage 1 | 8.07 | 7.49 | **6.79** | -1.3 |

Runs: `q12_*` (plain, `L12Q`), `l6_*` (fix7p4), `l12_*` (fix7p5), model `mq12` / `m5` / `m12`. fix7q2 plain here is rebuilt from the same source as fix7p5 with `BOOT_CFLAGS=-DSAT_LOAD_COALESCE -DSAT_BOOT_DISC_ORDER` only; its numbers equal the fix7p3-recipe numbers of section 4 (38.18, 8.01), so the earlier baseline stands. Menus, story, character select and continue do no reads and are unchanged.

MODELLED (HW_MODEL=1, stage 1 black card): fix7q2 plain 8.07 s, fix7p4 7.49 s, fix7p5 6.79 s. Nothing here is a console measurement. The gain is larger than fix7p4's on every load and **versus is no longer slower than plain**.

### 10.2 What changed

1. **Inflate v3** (`saturn/rt/lzdec.h`; the host DLL is built from the same text):
   - literal/length table 10 bits (was 9): the slow canonical path for longer codes was 6.3 % of the symbols and about 15 % of the decode instructions, it is 2.4 % of the symbols now;
   - one refill test per symbol (`nb <= 16`, 16 more bits, so at least 17 bits are in hand for any code); the output end is checked at the refill and at every match instead of at every literal; no shift-by-zero guard on the table-hit shift;
   - match copies: halfword moves when source and destination are both even (as v2), bytes unrolled by four otherwise.
   Host proof unchanged: `tools/loading/t_inflate.py` 7,283 zlib streams (stored, fixed, dynamic, Huffman-only, levels 0 to 9, 2 KB to 200 KB, real round and boot data), 0 bad, with the plain build and with the `__sh__` multiply-shift build of the DLL. Decode cost per 64 KB stream in the streaming loader (EMULATED, stock Ymir, cache on): 125 to 135 ms, about 55 cycles a byte (v1: 70). MODELLED (HW_MODEL=1): 145 ms a stream (the cart bus: byte stores to the pack room, cache line fills of the compressed input and of match sources).
2. **Content keyed pieces** (`tools/lzstore.py`): each file's tile region is cut into uniform 32 sector pieces from its own start, each distinct piece is compressed once (keyed by content) and the blob area is laid out in order of first use, a file's already placed, adjacent pieces being shared as one run. fix7p4 cut the pool at every sector run of the deduplicated raw data: 3 to 24 reads a file (a read is a seek; Ymir charges 33 ms each, a console more). Now **286 of 287 files are one read and one file is 3** (289 reads for 287 files; the loader merges neighbouring pieces into one `GFS_NwFread`). Price: blob area 26,015 to 27,742 sectors (+6.6 %), store 150,430 to 152,227 sectors (+3.6 MB on the disc). Uniform pieces also cured the 11 uncompressed files (10.3).
3. **Tail scratch 7,168 bytes** (was 8,192; `LZ_TMAX` in `boot.c` and `TMAX` in `tools/lzstore.py` are the same number): the shipped files need at most 7,168 (tail histogram: 0: 12 files, 512: 55, 1,024: 19, 1,536: 36, 2,048: 40, 3,072: 63, 4,096: 42, 5,120: 15, 6,144: 1, 7,168: 4). A file that needed more would stay uncompressed (the builder prints it). Loader bss end `0x06013ae0` (limit `0x06013fe0`; fix7p4 had `0x06013a50`).
4. **Alignment gate: 0 of unknown type** (was 2). The two symbols were the decoder's halfword tables `lz_lbase` and `lz_dbase`: a `const lz16` array carries no alignment the gate can prove from the map, so it counted them as unknown. They carry `aligned(4)` now (`LZ_AL4`). 348 data symbols, 49 cast sites (one reviewed site added: the SAT_LOAD_SUM test helper `boot_note`, not in a release build), 199 accessor calls, 0 hits.
5. **`SAT_LZ_DBG`** (test builds only): a free-running-timer probe in `lz_stream` that records, per tile stream, when the loader noticed its arrival and when its decode started and ended (`sat_ld_diag[8..]`, read with the route `y:` step). It produced 10.4.

### 10.3 The 11 uncompressed files, and versus

- **The 11 files** (rounds 4 and 50 to 59, all with a 790 sector tile region) failed the in-place proof with 8 KB of tail because the shared run cut points gave streams of odd sizes plus the per-stream sector padding. With uniform 32 sector pieces the same files prove in place with a 4,096 byte tail. All 287 files take the compressed path now (`raw_files: 0`).
- **Versus** was 0.4 s slower than plain in fix7p4 because the arena file was 22 reads. It is 5 read runs and 7 seeks now (fix7p4: 22 runs, 24 seeks; plain: 5 runs, 13 seeks): 7.54 s plain, 7.97 s fix7p4, 6.12 s fix7p5. I added no per-file cost rule: with one read a file the decode cost is the only thing against compression, and the model in 10.5 says compression wins on every file of this data. (If a future data set has a file that loses, the builder can keep it plain; it already does for a file that fails the in-place proof.)

### 10.4 What bounds a load now (measured)

The probe (stage 1, stock Ymir, the 25 streams of `R006`): each stream's decode starts the moment the previous one ends and takes 90 to 138 ms (mean 125); between two decodes the loop spends 20 to 33 ms moving the next stream's sectors from the CD block (GFS CPU transfer, `gftr_execCpu`); the drive delivers a stream (19 sectors on average) every 155 ms. Decode plus transfer is about 155 to 180 ms a stream, so the CPU is the bottleneck by 0 to 15 %: the decoder falls behind by about 25 ms a stream and is 0.6 s behind the drive when the last sector arrives. That is the whole "tail" (CD 5.67 s, swap 6.42 s). In the region-aware model it is 165 ms a stream against 155 ms. Two things that did **not** change it (the stage 1 swap stayed at 75.24 s to the frame): the cache on for the whole read instead of around each decode step, and 16 `GFS_NwExecOne` calls per poll instead of 1. So the polling loop is not the cost; the decode itself and the CPU read of the CD data port are.

### 10.5 Codec choice, by total load time (model)

Pipeline model (stock Ymir constants: CD 150 sectors/s, 1.5 ms of CPU per sector moved, deflate decode 125 ms per 64 KB, the real per-piece sizes of all 287 files, from the first sector of a tile read to the last byte decoded; the byte LZ at 0.80 of the raw size and 27 ms a piece, which is LZ4 class, 12 cycles a byte; ratios from section 2). It reproduces the measured stage 1: CD 3.29 s, tail 0.75 s (measured 3.26 s and 0.6 to 0.7 s).

| tile read, mean over the 287 files | total (first sector to last byte) |
|---|---|
| uncompressed | 5.1 s |
| LZ4 class (0.80, 12 cycles a byte) | 4.2 s |
| deflate as built (55 cycles a byte) | 3.9 s (CD 3.1 s) |
| deflate 30 % faster (39 cycles a byte) | 3.2 s |
| deflate 55 % faster (26 cycles a byte) | 3.2 s (CD bound) |

Deflate beats a decode-faster byte codec at today's speed because the 4 bit tile data only compresses by the entropy coding (LZ4 class stops at 0.80 to 0.87), and a faster deflate is CD bound at about 30 % less decode, so nothing is left to gain by changing codec: **a faster deflate has a ceiling of about 0.7 s a load** (stage loads 6.4 s to 5.7 s). I did not build LZ4: the model says it loses by 0.3 s before counting its larger store.

What a 30 % faster decode needs on an SH-2: the literal path is 28 instructions now (no variable shift: table, multiply, high word) and about 22 at best in hand-scheduled assembly, so assembly alone is worth perhaps 15 %, not 30 %. The two levers that would reach it are (a) the slave SH-2 decoding while the master moves sectors (25 ms against 125 ms of work a stream, the slave idle otherwise; the loader would have to start and stop the slave, which the kernel also does: console risk), and (b) a decode that writes the pack room in long words (the model charges every byte store to the cart bus). Neither is done.

### 10.6 Boot images in memory against the uncompressed build

Test builds with `-DSAT_LOAD_SUM` record the multiplicative sum and byte count of each boot file as `load()` left it in memory (`boot.c boot_note`, `sat_ld_diag[8..19]`), in Ymir, on the same HEAD: `L12B` (LZ) and `L12P` (plain). `tools/loading/bootsum.py` checks: the compressed file decoded with zlib alone equals the plain file; the LZ build's memory sum equals the sum of those bytes; the plain build's memory sum equals the sum of the plain file. Result (`bootsum_L12.txt`): COLD1, HW, LW, OPX and ROM are all equal (ROM's two sums are identical, 7e88fb03 over 2,097,152 bytes; the others differ only because the plain loader writes the file's exact size and the LZ loader whole sectors, zero padded). It is a 32 bit sum plus the offline byte comparison, not a byte dump of the memory.

### 10.7 Gates, final build `L12` (source `f107798a`)

- **Every round file, in game (item 5.2):** the loader's self test on the final source (`L12T`, run `runs\st12`, `SAT_LOAD_SELFTEST` + `SAT_LOAD_SUM`: every one of the 287 round files loaded in turn, the multiplicative sum of every region read back from its address compared with the sum the builder computed from the original round file): **287 loads, 0 differ** (`sat_ld_diag`: loads 0x11f, fails 0, first failing round none, rounds done 0x11f of 0x11f, at 160,008 frames; `runs\st12`). Covers the boot front end, every stage and boss file, the versus arena files, the ending files and every character variant.
- **Boot images in memory against the plain build:** 10.6, all five equal.
- **Build gates (the build fails on them), `L12`:** `vdp2_cycle_check` PASS; alignment gate 348 data symbols (0 of unknown type), 49 cast sites (all reviewed), 199 accessor calls, 287 round files and `REVEAL.BIN`, 0 hits; boot data addresses ok; Wolverine canary ok; **budgets identical to fix7q2: high RAM free 72, low RAM free 500, cart tail free 2,372**; loader bss end `0x06013ae0` against the limit `0x06013fe0` (the selftest build `0x06013d40`, the SAT_LOAD_SUM build `0x06013c10`). The store verifies every round file by rebuilding it from the store with zlib alone (the builder's `rebuild_round`): 287 of 287 identical; the in-place proof per file runs the loader's own `lz_unit`, compiled for the host, over the exact bytes laid out on the disc.
- **Tests:** `tests/align_gate_test.py` 13 ok, `tests/lat_protocol_test.py` PASS, `tests/vdp2_cycle_check_test.py` PASS; `tools/loading/t_inflate.py` 7,283 streams, 0 bad (plain DLL) and 0 bad (`__sh__` DLL).
- **Ymir data misalignment gate** (`tools/ymir_misalign_gate.py --run`, my strict exe copy `ymir2-mis.exe`, default route: boot, title, ARCADE, stage 1, KO, continue): **0 data accesses** on `L12` (5,819 instruction fetch artefacts filtered; `gate_misalign_L12.txt`), also 0 on the first v3 build `L10`.
- **TICK 60 in play, stock Ymir (`L12`, stage 1):** `TICK 60 CUT 28`, `PIC 60 DONE 60 MISS 0 SKIP 0 HELD 0`, readout id `F2 F10779` (`runs\l12_a\play_crop.png`).
- **Routes played on `L12` (EMULATED):** `l12_a` (boot, ARCADE, stage 1, KO, game over, ranking, title, ARCADE, stage 1, pause, quit to title), `l12_vs`, `l12_br`, `l12_end` (stage select ENDING: arena, ending, credits, front end); the same routes on fix7q2 plain (`q12_*`) are the baseline.
- **Staged:** `E:\AvP\package-integration\fenrir\avp_3h_A_fix7p5` (track01 = `iso_L12`, 26 audio tracks as in the other discs, cue, README.txt, SHA256SUMS).

### 10.8 Known issues, next

- Console time is unmeasured; Ymir's CD model has no seek or rotational cost and a flat 33 ms a read command, so a console that pays more per seek gains more from the one-read layout and from compression.
- The load is still decode bound by 0.6 to 1.0 s (10.4). The ceiling of a faster deflate is about 0.7 s a load (10.5); the levers are the slave SH-2 and long word stores, both console risk, not done. LZ4 class loses by the model.
- `SAT_TR_LINE` stays in its own commits of the lane branch (not in this recipe).
- The 11 uncompressed files of fix7p4 are gone (10.3); `LZ_TMAX` is 7,168 and a larger need falls back to plain.
