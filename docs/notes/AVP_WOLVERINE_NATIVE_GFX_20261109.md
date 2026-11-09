# Wolverine drawn natively: his poses as the game's own animation data, 2026-11-09

Lane `lane/wv-native-gfx-20261109`, from `avp/integration` 4bfcdf6. Owner brief: "There shouldn't be any replacement. Wolverine should be a native character." This note is the design for drawing him with no per-frame sprite replacement, plus a one-pose prototype (his stand).

Evidence labels: **READ** = source inspection (lifted C in the build's `gen/`, repo source); **DATA** = computed on this PC from the decrypted program image `rt.bin` of the integration work directory (nothing from it is committed; addresses and counts only); **MODELLED** = arithmetic from READ/DATA numbers; **EMULATOR** = Yaba, own copy, paused capture. Nothing here is MAME, HOST or HARDWARE. No ROM bytes, no generated tables, no screenshots are committed; `gen_c.py` output stays in the build's `gen/` as today.

## 0. Verdict

- **It fits and it is cheap in RAM.** The game already has the whole mechanism: a player's current *frame record* (block +0x1c) points at a *pose assembly*, and the game's own emitter (`0xa9cb6` -> `0xaa38a`) turns that into object-list entries. Wolverine's poses can be written in the emitter's *family 0x000A* format (inline dx/dy per piece, 8 bytes a tile) and reached by changing data the game already reads. No RAM, no new draw code. The format is the one `avsp_emit.c` decodes and the repo verified against 6,139 live frames.
- **Tiles: still 1,474, same gate.** The emitter writes the same tile keys the skin writes today, so the stage packs (`stage_keys`) and `fit.py` (stage24_ma: 38 tiles of margin) do not change. What changes the fit is only the cart tail size (4 KB step = 32 tiles), see section 5.
- **Not free of work.** Sixteen-byte records are easy; the part that decides the schedule is the *slot map*: Schaefer's animation tables have 192 slots whose records the state machine drives (timers, event bytes, hit and grab indexes). Each slot needs a Wolverine chain with the same contract. That map is not extracted yet (section 6, stage 0).
- **Prototype (section 8): his stance pose, idle step 0, drawn by the game's emitter from a 236-byte assembly, skin skipped for that pose.** Switch `-DSAT_WV_NATIVE_GFX`, default off; default-off objects identical (checked by section sizes). Result in section 8.

## 1. How the game turns a player's animation state into sprite objects (READ + DATA)

Player block `ff8380 + 0x100 * i` (`PLAYER_INTERFACE.md`). Fields used by the animation path:

| Offset | Meaning | Where it is read or written |
| --- | --- | --- |
| +0x04..06 | state (`020000` stand, `020002` walk, `020006` attack ...) | state routines, `f_195ec` |
| +0x0a | frame timer (ticks left in the current record) | `f_1656e` counts it down |
| +0x0f | facing, bit 0 set = facing right | origin routine, emitter |
| +0x10 / +0x14 / +0x18 | x / height-depth word / z | origin routine |
| +0x1c | **current frame record** (32-bit pointer) | set by `f_16526`, advanced by `f_1656e` |
| +0x24 / +0x25 | record flags (copied from record +2): bit 15 of the word = "last record", low byte = a per-record parameter the state routines test | `f_1656e`, attack, walk, jump routines |
| +0x2e | OR value for the object x word | emitter |
| +0x50 | box table T (per character) | collision `f_1cf54` family |
| +0x90 | hit hold, set from the timer when the record has an attack box | `f_1656e` |
| +0xd2 | character number (Schaefer 1) | animation set |

**Choosing an animation.** `f_1b0c4` (0x1b0c4) reads the character's animation base from a per-character table of four longs at **0x1b0e0** (`[Warrior 0x15e240, Schaefer 0x162f90, Hunter 0x168564, Linn 0x16d122]`, a PC-relative table, held in the `OPX` store at offset 0x925a) and calls `f_16518` with the animation index in d0. `f_1b0f0` does the same with a second table at **0x1b104** (Schaefer 0x163074). Schaefer-only code also loads bases as constants: `0x162f90` (at 0x199e2 and 0x1a568) and **`0x1630f6`** (eight sites between 0x21e12 and 0x25a04, among them the 0x25xxx jump routines). `f_16518` (0x16518): `record = base + s16(*(u16 *)(base + 2 * (index & 0xff)))`; `f_16526` stores it in +0x1c, copies record +0 to +0x0a (timer) and record +2 to +0x24 (flags). So **an animation is an index into a table of 16-bit offsets relative to the table's own base**, which gives each table a +-32 KB reach.

**Advancing.** `f_1656e` (0x1656e), once per tick from the state routines: timer -1; at zero, next = record + 16, or, if the *current* flags word is negative (bit 15), the 32-bit target stored at record + 16 (jump record, 20 bytes); store the new record and reload timer and flags; if the new record's +9 (attack index) is nonzero, +0x90 gets the timer (the sibling `f_16536` at 0x16536 adds a test of the actor tag byte +8 being 0, a player). State routines end a move by testing the flags word for bit 15 (the terminal record) or the low byte for their parameter.

**Frame record (16 bytes, 20 for a jump record)** (`avsp_anim_script.h`, DATA on Schaefer's):

| Record offset | Meaning |
| --- | --- |
| +0 | duration in ticks (u16; a terminal "hold" record has 4095) |
| +2 | flags word: bit 15 jump/terminal; low byte = parameter (walk records 0x0a 0x06 0x07 ...; attack records 0 then 1 for the live frames) |
| +4 | **pose assembly address** (u32, anywhere in the 68000 space) |
| +8 | hurt box index into T (`T + T[0] + idx * 8`) |
| +9 | attack box index into T (`T + T[2] + idx * 16`) |
| +10 | unused in Schaefer's records seen |
| +11 | shadow index, read by the shadow emitter `f_aaa12` (6 or 7 on the ground, 0 = none) |
| +12..15 | event data; +15 is read by other actors (`f_bca58` uses it as a hold-position index while Schaefer grabs) |
| +16 (jump record) | u32 target |

**Drawing.** The actor draw loop calls `f_a9cb6` (0xa9cb6): `rec = *(a4+0x1c); asm = *(rec+4);` it reads the assembly's first word, a tag, and dispatches (tag 6 -> `f_aa016` multi-part group with offsets from the shared table at 0x1fd1c8; 2 -> `f_a9d52` single entry; 4 -> `f_a9dee`; 0xa -> `f_aa382` -> `f_aa38a`, inline dx/dy; 0xc -> two records follow). Each record starts with a **budget** word (tiles; subtracted from the frame's budget d7, the actor is skipped when it goes negative). Every family calls `f_aa59a` (the origin; readable form `sprite_origin_compute` in `saturn/game/game_hot.c`): `y = 0x100 - (z - cam_z)`, `x = x - cam_x + 0x40`, then `+/- ` the group's offset pair by the facing bits, high half across, low half down. It then writes 8-byte entries `x | or_value, y, code, attr` into the object list at `a1`. `attr` = `[h-1 | w-1 | flip bits | palette row]`; with the actor's +0x0d <= 0 (players) the assembly's own palette bits stand; facing right XORs the hflip bit and mirrors x as `origin - width - dx`. `avsp_emit.c` is the C port of all of this (families 2, 4, 6, 0xa). Family **0xA** record: `[000a][budget][count][pad][D2 hi][D2 lo]` then per piece `[code][attr][dx][dy]` (8 bytes); a real example exists in Schaefer's own data (0x167eee: `000a 002a 0003 0000 0000ffec ...`).

**Hit boxes** are attached by the record's +8/+9 and live in T, a per-character table: Schaefer's T is at 0x11b166 (hurt table 0x11b16a, 12 entries of 8 bytes; attack table 0x11b1ca, up to 38 of 16), chosen at spawn from a per-character table at **0x19744** (`f_195ec` path 0x19736: `+0x50 = OP32(table + char * 4)`). Today's skin overwrites four bytes of the chosen entries around every collision call (`sat_guest_wolverine_boxes`).

**Snapshot.** `sat_gfx_snapshot_begin` (sat_gfx.c ~2000) copies the object list and, if a guest is selected, calls `sat_guest_objects` (guests.c -> `sat_guest_wolverine_objects`, wolverine.c). That is the replacement pass: it finds Schaefer's entries by palette 1 and place, removes them, shifts the list, inserts ~29 one-tile entries from `wv_tiles`, and rewrites two palette rows. Yaba numbers from `AVP_FPS_HELD_20261109.md` (FRT ticks, not ms): remove 38, shift 18, tiles 38, name check 8, palette 1, about 103 per call that draws him. The brief's ~0.7 ms on the master is taken as given and is not re-measured here.

## 2. Where Schaefer's data lives in the ROM image (DATA)

All addresses are 68000 ROM-image addresses; the Saturn holds the image at `ROMB` 0x02400000.

| Item | Address | Size |
| --- | --- | --- |
| Animation index tables, 16-bit offsets | T1 0x162f90 (80 slots), T0 0x163032 (32, reader not identified), T2 0x163074 (64), T3 0x1630f6 (16) | 192 slots, 384 bytes |
| Frame records reachable from them | 0x163158 .. 0x165474 | 411 records, 6,964 bytes; 60 + 25 + 16 distinct chain starts |
| Pose assemblies | 0x165488 .. 0x167eee | 182 assemblies, 5,044 bytes (175 family 6, 6 family 2, 1 family A); the range is 10.6 KB, the rest is other tables |
| Box table T | 0x11b166 (+ hurt 0x11b16a, attack 0x11b1ca) | about 1.5 KB |
| Per-character base tables | 0x1b0e0, 0x1b104 (anim), 0x19744 (T) | 16 bytes each, in the `OPX` store |
| Stand | slot 0, record 0x163158: one record, 4095 ticks, flags 0x8000, jumps to itself; assembly 0x165488 | many other slots (15, 24..28, 44..47, 58) and chain ends point at the same record |
| Walk | slot 2, 0x1631b0: 12 records, 2 to 6 ticks each, parameter bytes 0x0a 0x06 .. 0x10, loop | |
| Attack chain | slots 32..36 (`f_24454` asks for `0x20 + chain stage`), special 36: 0x163644, 0x163688, 0x1636dc, 0x163740 ... (slot 36 has attack index 4 in four records and is probably the special, not confirmed), each ends in a 4095-tick terminal record | |

Page ownership (`rounds.json`, page = 1 KB): the record page of the stand (1420), the table page (1419) and the assembly pages (1429..1439) are in `keep_pages` of **all 19** stage files and in the shared set, so no stage file spills tiles over them, and the loader's ROM restores (which only put back pages some file overwrote) never touch them: bytes written there persist across stage loads.

## 3. How tile codes reach the Saturn packs

A pose piece's `code` is a CPS2 tile key (16 bits; 128 bytes of 4-bit pixels at `key * 128` in the arcade graphics region). The snapshot turns each object-list entry into one VDP1 command per 16x16 cell (`code + bx + 16 * by`), taking the pixels from the stage's pack through `pack_index` (sat_gfx.c ~335, a hash from key to tile). Packs are per stage file, built at disc time (`tools/rounds_pack.py` and `satgfx_pack.py`): the sprite keys of the stage census fill the cart room (`SAT_PACK` .. `cold1_at`) and continue in ROM stretches the stage does not read. Wolverine's guest variants (`stageXX_wv`, `tools/wolverine/guest_rounds.py`) take the base file's keys, drop Schaefer's own, add his `stage_keys`.

His tiles use *free* keys (assets.py picks sprite keys no stage file uses; `gfx_wolverine.bin` carries the pixels at those keys), so nothing collides with the arcade's tiles. `fit.py` repacks every Schaefer-containing file twice, once as Schaefer (`sch_tiles`, `sch_drop`) and once as the Wolverine variant (`wolv_tiles`, `wolv_drop`), with the same cart room, and passes a file when the Wolverine variant drops no more tiles than Schaefer's and none of his own. D11: 76 of 76, stage24_ma drops 2,872 (Schaefer) against 2,834 (Wolverine): 38 tiles of margin; room 1,630,208 bytes.

Native references change none of that: the set of keys is the set of keys his emitted poses use (69 poses, 2,105 tile entries, 1,474 distinct keys, 1,217 tiles in his first palette row and 278 in the second), written into assemblies instead of `wv_tiles`.

### 3b. Data source: decode his MSHvSF records directly (coordinator request; DATA tier from a MAME 0.289 `mshvsf` run, nothing committed)

D11 was captured at run time (`mame_wolverine.lua`: object lists per frame, boxes through the marvel-hitboxes profile). MSHvSF is a CPS2 game with the same object RAM and sprite words, and its program ROM holds his animation as records of the same family as AvP's. Dump: `tools/wolverine/mshvsf_dump.lua` (data and opcode views of the 4 MB program space, player blocks, object lists, the graphics bank 0x0000..0x9fff, run through the MSHvSF repo's `tools/run_mshvsf_mame.py` with the input schedule `lane-wolverine/full.txt`) into `E:\AvP\learning\lane-wv-native-gfx\mshvsf`. Decoder check: `tools/wolverine/mshvsf_verify.py`.

**Layout (MSHvSF, player 1 block 0xff3800, big-endian)**

| Where | What |
| --- | --- |
| block +0x34 / +0x38 / +0x3c | current frame record / next record / frames left (the same trio as AvP's +0x1c / +0x0a) |
| block +0x68 | box-id table base (0x1ce0f2): 16-byte entries; entry 1 = the standing ids; +0x70..+0x7a hold the current entry (attack ids +0x70, +0x72; hurt ids +0x74..+0x7a) |
| block +0x6c | box geometry table (0x3a2000): 8-byte records `s16 x, u16 x radius, s16 y, u16 y radius`; a box id indexes it (`id & 0x1fff`) |
| frame record, 16 bytes (20 with a jump target) | `+0 u16 flags` (0, 0x80, 0x82, 0x100 seen on attack records), `+2 u16 duration` (bit 15 = jump record, `u32` target at +16), `+4 u32 assembly`, `+8 u32 flags` (0x80000000, 0xa0008000), `+12 u32 box-set index` (the entry of the table above) |
| assembly | `[0002][cell budget][pair count n][u32 position table]`, then n + 1 parts `[code][attr]` (attr as the CPS2 word: height-1 and width-1 nibbles, flip bits, palette 12 or 13 for his two rows; the facing flip is added at draw time) |
| position table | `[0002][s16 x0][s16 y0]` then n pairs of `s8 dx, dy`: each part is placed at the previous part's position plus its pair; facing left draws `x = origin - width - cumulative x` (AvP's emitter does the same) |
| per-character table 0xc38a (read at 0xc220) | 24 longs that are **code addresses** (opcode view), one handler routine per character: not animation data. His animation selection is in his handler; the table of his animations (index -> first record) is not extracted yet |

Verified: his stance (record 0xd1d30, assembly 0x2b3a70, 11 parts, 29 cells) reproduces MAME's object list entry by entry (codes, attr, order), and the position table predicts every part position: **22 of 22 parts match** on frames 1995 and 2200 (`mshvsf_verify.py`; frame 2061's record had already advanced). Durations match what the capture saw (the idle chain 0xd1d30.. is 4 ticks a record, the record pointer changes every 3 to 4 frames). The LP chain starts at 0xd2878; its records carry box-set indexes 0x10..0x13 and the ids change with the record (live attack id 0x1f from the second record on), so **hit boxes are exact per record**, which D11's sampled boxes are not.

**Region and size.** His records lie around 0xd1000..0xd6fff: 908 candidate 16-byte records (155 jump records), 398 assemblies, 3,610 parts, 9,116 distinct tile cells for every move he has (supers, taunts and all; the scan includes some false positives and is not a reachability walk). The six moves D11 started from (idle, walk, jump, LP, HP, HK; frames 1990..2399) visit **72 records and 59 assemblies**:

| Form | Bytes |
| --- | ---: |
| MSHvSF native: 72 records + 59 assemblies + position tables | 1,152 + 4,378 = **5.5 KB** |
| Converted to AvP family A (one 16x16 tile a piece, 8 bytes) | 15,652 + 1,152 = 16.8 KB |

The block form is 3 times smaller, because his parts are rectangles (592 parts carry 1,868 cells) and all 1,868 cells are non-blank (Capcom drew them tight, so no tile is spent on blank cells).

**What it does to the tiles.** The pixels are the same bytes D11 captured (gfx bank, code x 128). Without merging, the 59 assemblies reference 1,790 distinct tiles (1,868 cell uses; flipped duplicates: none beyond the same code). D11's 1,474 keys for 69 poses come from pose re-selection, pixel dedupe and the K12 near-duplicate merge, none of which the ROM does. So decoding does **not** shrink the tile set by itself; it changes only how a pose is described.

**Assessment.**
- Yes, decode directly. It gives the exact durations and jump structure, the exact box ids and boxes per record (a replacement for the sampled `boxes.json`), his true origin offsets per assembly (the heuristics of `pose_of` and `ground.py` guess where his feet are; the ROM states it relative to the actor), and the pose composition without a runtime capture. The conversion is a table walk: duration and jump word swap (`+2` <-> `+0`), box-set -> a T' entry, assembly -> AvP assembly, palette rows 12/13 -> rows 1 and the stage row.
- **Assembly form is a trade, not a given.** Keeping his rectangles (family 6 or 4 with a position table, 4 to 6 bytes a part) is 3 times smaller, but a block draws `code + bx + 16 * by`, so its tile keys must be consecutive in a 16-wide grid; K12 merging and pixel dedupe replace tiles by tiles elsewhere in the pack and break that. A tile costs 128 bytes of pack, an extra 1x1 entry 8 bytes, so for any tile that merging removes the 1x1 form wins. Use blocks only where nothing is merged; that is a per-pose decision for the generator and costs rectangles of free keys (`assets.py` takes free keys one at a time today).
- The full move list (9,116 cells) is far over the tile budget, so pose selection stays; what changes is that selection and thinning work from records (duration, role) instead of from frame diffs.
- Open: his animation index table and the engine state behind record flags `+0` and `+8` (start-up, active, cancel, hit-stop); MSHvSF's game speed against 60 ticks a second; palette tables (colours are still read from palette RAM). The official Saturn disc was not used. `mvscu.zip` (Marvel vs. Capcom) was not touched.

## 4. Design: Wolverine as data

### 4.1 The records and assemblies

- **Pose assembly: family 0xA**, one per pose (69), authored for facing = 0. For a pose piece captured facing right at `(dx, dy)` with hflip `h`: native `dx' = -16 - dx`, hflip `h ^ 1`, `dy' = dy` (the emitter mirrors a facing-right actor as `x = origin - 16 - dx'` and toggles the flip back). Header: budget = tile count, count = tile count, pad 0, D2 hi 0, D2 lo 0xfff5 (moves the feet to where the skin puts them, +11 px). Bytes: 12 + 8 * tiles; 69 poses and 2,105 tiles give **17,668 bytes**. Poses share almost no pieces (DATA: 52 of 2,105 entries repeat a piece of an earlier pose), so sharing through the two-record form 0xC saves nothing. Block objects (one entry per rectangle) would shrink the lists but need the tile keys laid out as consecutive rectangles, which is a different tile pack; not proposed here.
- **Mirror axis.** The emitter's mirror axis is fixed at the actor's x (`origin` for facing 0, `origin - 16 - dx` for facing 1 sum to a constant whatever D2 hi is). The skin mirrors about actor x + 8. Authoring the body centre on the axis therefore moves him **8 px to the left of the skin's place in both facings**; this is the one visible calibration change (visible in the prototype captures).
- **Frame records** (16 bytes, 20 for the terminal): one per step of his 14 moves (198 steps in D11 `moves_one`) plus a terminal. Per record: duration from the step (1..255, the field takes 4095), flags (bit 15 only on terminals; parameter byte per role: 0 for the startup frames, 1 on live frames, the walk's speed bytes), `+8` hurt index, `+9` attack index, `+11` shadow, `+12..15` from the Schaefer record of the same role. Compact source form for the generator output: 6 to 8 bytes a step, expanded to records by a small loop (about 100 bytes of code) when the data is applied; that keeps the tail near 1.4 KB instead of 3.2 KB.
- **Slot map**: 192 bytes, slot -> (move, first step), written into the four offset tables. Several slots share one chain (stand).

### 4.2 Reaching the data: patch the slots Schaefer's code already reads

Two ways to redirect Schaefer's animation, one rejected:

- **Rejected: fork every routine that holds a base constant** (nine Schaefer routines, 19 KB of C in the native lane's all-nine fork = 160 tiles). Not affordable.
- **Chosen: rewrite the data, not the code.** (1) The 192 offset words in T0..T3 are 16-bit offsets relative to each table's own base, so the new chains must lie within +-32 KB of 0x162f90: Schaefer's own record area (6,964 bytes) is exclusively his, and 4 KB is enough for the expanded records. Overwrite it, rewrite the 384 offset bytes. (2) Each record's +4 is a 32-bit pointer: point it into a **68000 address window that the page table maps to the assembly block**. `kernel.c` initialises `PAGE[256]` with `SAT_SINK` for 0x20..0x6f; `PAGE[0x30] = block` makes 0x300000 + offset readable by every `RD16`/`RD32` of the lifted code and adds no ROM-image page. (3) Shared with the other characters: nothing. Indexing is by character (0x1b0e0 entry 1) or by Schaefer-only constants, and the offset arrays and records are in pages only Schaefer's records read.

Delivery of the block, two options:
- **A (prototype and stages 1..3): runtime apply from the cart tail.** `sat_guest_wolverine_tick` (the `f_195ec` pre-hook) compares one record word per update and re-applies when the page was restored; `sat_guest_wolverine_pad` (once a vblank) undoes it when the setting is off. Needs the original bytes: 6,964 + 384 = 7.3 KB is too much to keep in RAM, but the stage file already carries "ROM restores" for pages it must put back, so undo = ask the loader (the same path that reloads the front file when the title menu hands back). The prototype keeps only the one original pointer (4 bytes).
- **B (end state): the data rides in the guest stage files.** `stageXX_wv` writes the Wolverine records and tables over Schaefer's record pages and the stock files restore them. Zero tail, zero apply code. Needs `guest_rounds.py` to emit a ROM-write region and the census to drop Schaefer's assembly pages (5 KB of dead data) from the guest files' keep sets, which also frees about 5 KB (40 tiles) for the packer. A change of the disc build, so after stage 3.

### 4.3 Palettes

Players have +0x0d = 0, so the assembly's attr low five bits are the palette row. First row = 1 (Schaefer's, `WV_SCH_PAL`). Second row (claws, highlights) = the row `wv_row1[stage word]` that a census found unused in that stage, which differs by stage (8..31). Options: (a) a one-bit-per-piece bitmap (2,105 bits = 263 bytes) and a loop that sets the row bits in the 401 second-row pieces when the stage word changes (once per stage load, 401 byte stores); (b) a fixed row for all stages, which needs a row no stage uses and does not exist in the census (22 serves only odd words); (c) merge the rows into one: his tiles use 26 distinct colours (16 and 14 pens), not possible without redrawing. **(a).** The 32 colours themselves stay a snapshot write for now (`wv_pal`, 64 bytes, `PAL_KEEP` makes it free when unchanged); later the first row's colours come from the ROM palette table the game already copies for Schaefer (patch its 32 bytes), so fades and hit flashes act on him natively. The second row stays ours.

### 4.4 Hit boxes and timing (second half, same mechanism)

- **Boxes.** A Wolverine T' (hurt 8 bytes, attack 16 bytes a distinct box; today `wv_box` is 8 bytes for each of 198 steps) at a second window page, and the per-character pointer at 0x19744 (entry 1) pointed at it, plus `+0x50` of a block that already spawned. Records' +8/+9 index T'. Removes `sat_guest_wolverine_boxes`, its undo list and the per-call hooks in `game_bind.c` `guest_pass` (780 bytes of code and the two wrappers).
- **Durations.** Come from the records. The time-warp tables, `wv_in_startup`, the held-tick logic and `wv_nat_tab` go where a slot's chain can carry the same total ticks as Schaefer's state routine expects. States whose length the state routine fixes (hitstun about 28 ticks, jump physics, the special's 57) keep their ticks; Wolverine's poses are distributed over them by duration, the loss against MSHvSF's authentic length is the one the plan already accepted ("native timing contract").
- **Jump arc.** Schaefer's jump has no vertical arc; today's lift table (88 px apex, owner 11-09) interpolates inside each step. Native: bake the lift of each step into D2 lo of that step's assembly (stair-step, 9 levels over 33 frames), or split the long steps into sub-steps with their own D2 (+250 bytes each). Open, section 6.

### 4.5 What becomes unnecessary

- **guests.c / wolverine.c:** the whole-list pass `sat_guest_wolverine_objects` (1,084 bytes of text) and its helpers (palette-and-place detection, removal, shift, tile insert, `WV_OX/WV_OY` calibration, `face_`, `wv_lift`, `wv_gy`, `SAT_WV_SCALE`, `SAT_GUEST_FOLD`, FAST_LIST code), the move clock (`wv_advance`, `wv_walk_step`, `wv_tick_move`, `wv_begin_move`, `move_for`, `wv_resting`, `wv_move_len`, `ONCE`, chain bookkeeping) and the f_195ec holds in `game_bind.c`, then the box hook.
- **Stays:** names (HUD text patch), pad motion inputs (`sat_guest_wolverine_pad`, 472 bytes), no-gun, pickups, the apply/undo and palette writer. Estimated remaining text about 1.5 to 2 KB (from 5.5 KB).
- **Cost the skin pays that goes away:** per snapshot the removal scan and shift (56 FRT ticks), the tile insert (38), and the palette-bearing atomic-publication machinery. The game's own emitter work replaces it; it already runs for Schaefer's sprites today, so this is not new work (a pose of 29 one-tile pieces vs 2 blocks costs the emitter a few more stores; MODELLED, not measured).
- **Gains in correctness:** the game's own offscreen cull, spawn-in and dying visibility gates, the blink on hit (+1 toggles, `wv_blank` and `wvid_` latch), frame tile budget, draw order inside the object list, and 2P overlap (the skin's removal by palette and place can eat the other player's tiles).

## 5. Budget (MODELLED from READ/DATA numbers; the prototype row is measured at link time)

Current sizes, the integration build `w1` (`wolverine.o`, nm): `wv_tiles` 16,840, `wv_box` 1,584, `wv_steps` 396, `wv_lift` 396, `wv_pose_start` 140, `wv_move_start` 30, `wv_pal` 64, `wv_row1` 40; text 5.5 KB (objects pass 1,084, boxes 780, advance 776, tick 612, after_tick 512, pad 472, move_for 500). Owner build slack: hw_free 1,252 B, lw_free 60 B, cart_free 4,340 B. The cart tail is sized in 4 KB steps `((total + 0x1fff) & ~0xfff)`, so the free room before a step is cart_free - 4096 = **244 bytes**; crossing it costs 32 tiles and rebuilds the round files (the brief's "108 bytes" is the native lane's figure for its own build).

| Item | Now | Native end state (delivery A) | Delta |
| --- | ---: | ---: | ---: |
| Tile pieces | 16,840 | 17,668 (assemblies incl. headers) | +828 |
| Steps, lift, pose start, move start | 962 | 1,400 (compact records source) + 192 (slot map) | +630 |
| Row-1 bitmap | 0 | 263 | +263 |
| Boxes | 1,584 | about 2,600 (T': 198 hurt, about 60 attack) | +1,000 |
| Text | 5,500 | about 1,900 + apply 400 | -3,200 |
| **Total tail** | about 25,100 | about 24,400 | **about -700 (MODELLED, +-1,000)** |
| High RAM | - | 0 (per-player clock state of about 100 bytes disappears) | <= 0 |
| Low RAM | - | 0 | 0 |

So the end state is roughly neutral to slightly smaller in the tail, with no guarantee it recovers a page; delivery B moves 17.7 + 3 KB out of the tail onto the disc and into Schaefer's dead pages, and is the way to buy tiles if needed. **Stage 1/2 intermediates carry both code paths and will cross the 244-byte slack**; they are measurement builds, not release candidates, and each reports its fit.

Tiles: unchanged at 1,474 keys, stage24_ma margin 38 tiles at the current room. A page lost to growth costs 32 of the 38, leaving 6 (still True). A pose rewritten natively adds no keys. Block objects or tile merging are separate levers.

Time: every frame the skin runs 103 FRT ticks (Yaba, measured by the held lane) plus the brief's 0.7 ms on the master; the native path replaces it by the emitter work the game already does. Console numbers: none, hardware unrun.

## 6. Risks and unknowns

1. **Slot roles are not extracted.** 192 slots, about 100 distinct chain starts; which state asks for which slot, and what the flags low byte, `+0x25` tests, `+9`, `+15` mean in each (walk speed? sound?), needs a trace of `f_16526` (a6, base, index) on the whole-game walk. Stage 0 below. Until then only slots whose chain is one terminal record (stand) are provably safe.
2. **State routines end moves by the record chain** (terminal flag, parameter byte). A chain with the wrong flag placement hangs a state or ends it early. Mitigation: copy Schaefer's flag skeleton per role, spread Wolverine's poses over it; the existing forked attack and special routines make the contract testable on HOST.
3. **Side effects of a longer chain than Schaefer's:** `+0x90` hold, `+15` grab index (other actors read it), shadow `+11`.
4. **Mirror axis -8 px** (section 4.1), both facings. Hit boxes calibrated against the skin's place shift with it. Check on a still pair.
5. **Second palette row** patched per stage; if the stage word changes between a patch and the next draw, claws show the wrong row for a frame. Patch inside the stage load hook, not the tick.
6. **Page persistence.** The patch lives in kept, shared ROM-image pages, so stage loads do not touch them, but a savestate, a load of the front file or a failed copy can leave a mix. One canary word checked per player update catches that.
7. **Other readers of Schaefer's data** outside the player: the ending, select-screen and demo scenes may draw Schaefer from the same records. The page census (a guest-aware run of `rounds_census`) says; the prototype does not touch those records except the stand.
8. **Frame tile budget d7.** The game skips an actor whose budget does not fit; his poses run 21 to 49 tiles against Schaefer's 32 to 60 cells, so the same order, but 49 is the largest (knockdown, crouch).
9. **Jump arc stair-stepping** (section 4.4).
10. **Yaba.** Writes to cart-resident ROM-image pages are plain stores; the lifted code reads them as data. Dynarec recompiles cart *code* on entry, which is why the removal of the cart-resident pass is worth more there than on hardware.
11. **Hardware.** Not run. The ROM image sits on the A-bus cart RAM, same as every table the game already reads; the new reads are about 30 pieces a frame.

## 7. Staged plan with checks

| Stage | Work | Check (tier) |
| --- | --- | --- |
| 0 Census | Trace `f_16518/16526/1656e` for the Schaefer route (a6, base, index, record) on MAME or the HOST lift runner; extract per slot: chain length, durations, flags parameter bytes, +8/+9/+11/+15; which consumers read +0x24/+0x25/+0x90. Output `slot_roles.json` (private). | Every slot of T0..T3 reached or marked unreached; consumers of +0x25 listed (HOST/MAME) |
| 1 Stand and idle | Prototype of this note, then idle as a 12-record chain (slot 0 and the other stand slots), terminal back to itself. The stand record cannot grow in place (the next record follows at +16), so slot 0 moves to a new chain and the old record keeps the static stance for jumps back to it. | Still pair native vs skin; **identity**: setting OFF, image and frame hashes equal the stock build over 600 vblanks; Wolverine as player 1, as player 2, both; stage 02 -> 04 -> 06 (patch persists); death and continue; save state and load (EMULATOR) |
| 2 Walk and jump | Walk (slot 2, 12-record skeleton), jump (slots 4, 5 and the private table T3). Lift baked in D2. | Same, plus walk speed unchanged, jump apex measured (EMULATOR) |
| 3 Attacks, hits, falls | All other slots with the flag skeletons; attack contract per role; remove the skin pass (`SAT_WV_NATIVE_GFX=2`: compiled out); remove holds where durations carry. | Host fork identity (nine routines still bit-identical), Round 1 gate notes repeated, hit counts, chain timings against the plan's 2/4/6 table |
| 4 Boxes | T' and the pointer at 0x19744; remove the collision hook. | Damage per accepted hit unchanged (24 / 31 on stage 02), special cost rule unchanged; both players |
| 5 Palette and delivery B | First-row colours from the game's palette table; guest stage files carry the block; Schaefer's dead pages freed. | `fit.py` with D12 gate True; palette fade and flash look; disc size |
| 6 Delete and measure | Remove dead skin code; re-measure link numbers; console A/B on the hardware discs. | hw_free, lw_free, cart_free reported; Yaba held/snapshot ticks; hardware if available |

Each stage ships default off and merges only after its identity row (stock Schaefer unchanged with the setting off; same ELF size and section sizes with the flag undefined).

## 8. Prototype: his stand drawn by the game's emitter

### Scope
Switch `-DSAT_WV_NATIVE_GFX` (default off). One pose: idle step 0, which is the stance pose of D11 (pose 17, 28 tiles, 236-byte assembly, 5 of them in the second palette row). One record changed: Schaefer's stand record 0x163158, assembly pointer (+4) rewritten to 0x300000, a window `PAGE[0x30]` maps to the assembly in the cart tail. Nothing else in the game or in Schaefer's data changes: the game's state machine, timers and boxes are Schaefer's. While that record is the player's current one the replacement pass skips him (`wv_nat_drawn`). Runtime debug variable `wv_nat_dbg` (poke over the debug port): bit 0 native on, bit 1 force the skin to draw idle step 0 so the A/B compares the same pose.

Files: `tools/wolverine/gen_c.py` (emits `wv_nat_asm`, `wv_nat_p1` under `#ifdef`), `saturn/guests/wolverine/wolverine.c` (apply on every Wolverine player update, undo from the vblank pad hook when the setting is off, skip in the pass), `tools/wolverine/native_gfx_proof.py` (paused A/B capture). Apply is idempotent and keeps the original pointer the first time it sees the record unpatched. The second palette row is written into the assembly's attr low bits from the stage word (5 byte stores) when the stage changes.

### Result
RESULT_PLACEHOLDER

## 10. Revision for plan V2 (owner-approved, 753c435): relocation, not in-place; the access-point audit

Plan V2 retires "in-place changes to Schaefer's records" and asks first for **relocated records holding donor-equivalent data**, with only named pointer-address changes, then Wolverine's art and combat data. This section replaces the in-place variant of section 4.2 (the prototype of section 8 still patches one pointer of the stand record in place; it is the minimal proof of the emitter path, not the architecture).

### 10.1 What a relocated block must be reachable through (DATA, `tools/wolverine/access_audit.py` on the integration work directory)

- **26 slots in the opcode store** that hold one of the four table bases (T1 0x162f90, T0 0x163032, T2 0x163074, T3 0x1630f6), each an entry of a per-character table (Schaefer = entry 1): 0x199e4 0x1b0e4 0x1b108 0x21e14 0x21ffe 0x2223a 0x2511e 0x25852 0x2591a 0x3834a 0x38442 0x3a668 0x3a696 0x3c664 0x3c698 0x486da 0x522ae 0x5325c 0x588a6 0x5894e 0x6f9d8 0x95c14 0x96794 0x968d2 0x9742c 0x977d2. Several are enemy and object routines that set the *player's* animation (grabs, holds, throws), so a redirect that only handles the player's own state routines would leave them on Schaefer's pictures. Each slot is 4 bytes in `OPX` (cart RAM, written once); a patched slot is a named pointer-address change.
- **10 code immediates** (0x1a568, 0x199e2 for T1; 0x21e12, 0x22238, 0x2511c, 0x2517c, 0x25250, 0x25850, 0x25918, 0x25a04 for T3), all in Schaefer-only code. A build-time rewrite of the lifted source (`build.py gen_sources` already rewrites `OP*` bases and renames wrapped routines) replaces each by a resolver macro that returns the block's address while the setting is on. That is the "small resolver at a proven access point"; it costs about 12 bytes of **high-RAM** code per site (hw_free 1,252 B; MODELLED, measured at link).
- **48 longs in the opcode store point into the record and assembly range** (17 distinct even values, 7 distinct odd values that cannot be aligned pointers): other actors draw sprites from assemblies that lie *between* Schaefer's (0x165414, 0x16542e, 0x16546e, 0x166000..0x16670a, 0x167000..0x167008) and four routines at 0xb67e2..0xb6aea use the record 0x16317c. So that range is **not Schaefer's alone**; overwriting it in place (the "dead pages" idea of section 4.2, option B) would break effects. The relocation copies and never overwrites. None of the 420 records reachable from Schaefer's tables points at an assembly outside the block.

### 10.2 The page-table mapping (lift_target.h)

`RD16/RD32/WR*` go through `pb_at(a) = PAGE[(a >> 16) & 0xff] + (a & 0xffff)`. `kernel.c` fills `PAGE[0x20..0x6f]` with `SAT_SINK`. **Reserve `PAGE[0x30]`**: one 64 KB window at 0x300000 mapped to the data block in the cart tail. Every value written into +0x1c, +0x50 or a record is then an ordinary 68000 address (block offset below 0x10000, even, big-endian in the block). An SH-2 pointer must never be stored into a game field. The block lies in the tail (`.cold1`), not in a ROM-image page, so it is available on **every stage including 26** (stage files spill tiles only over ROM-image pages the stage does not read; the tail is outside that set) and needs no restore after a stage load. The `PAGE` entry is set at boot and again in the guest select hook; a savestate that holds the cart RAM and the kernel BSS restores both. Audit still to run: write a canary into the block and read it through `RD32(0x300000 + k)` in stages 02, 24 and 26.

Alignment: the lifted `RD32` is two 16-bit loads, so records need 2-byte alignment only. The block is generated big-endian, so no byte swap exists on the SH-2.

### 10.3 Data-level identity of the relocation (DATA tier, `tools/wolverine/reloc_check.py`)

Copy Schaefer's block 0x162f90..0x167f20 (**20,368 bytes**: index tables, 420 reachable records, 182 assemblies) verbatim to 0x300000. Only two kinds of field change, each by the constant delta 0x19d070: the assembly pointer of 420 records and the jump target of 100 jump records (520 longs; 1,560 bytes differ from the donor, 2,080 allowed). The index tables are base-relative and are copied unchanged. Walking all 192 slots through the relocated and the original view: **637 records compared, every non-pointer byte equal; 55,584 object entries produced by the emitter (families 2, 4, 6, 0xA) for 32 actor states (facing, position, camera, OR value) equal; 0 mismatches.** This is the data proof only. The runtime proof (page table, resolver, 26 slots, 10 immediates, emitted object list, non-pointer player state, effects on other actors) is the HOST identity run with the native lane's `build_native_host.py` and `fielddiff.py`: not done here (section 11).

Budget consequence: the identity block is 20 KB, five tail steps, about 160 tiles, and stage24_ma has 38 tiles of margin. **The identity run is a HOST-only measurement, not a Saturn link.** Wolverine's own block replaces it (about 17.7 KB assemblies, about 4 KB records and tables, boxes) and is budgeted against the link map (section 5).

### 10.4 Baseline protocol (plan section 3)

Recorded for this lane: commit 4bfcdf6 plus this branch; assets D11; flags `POSE_KEYS=0 KEEP_ROUND_FILES=1`, `KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_WV_JUMP=1 -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1"` (plus `-DSAT_WV_NATIVE_GFX` for the prototype); emulator: the sprite-dropout lane's Yaba copy (own folder, port 9718, VideoCore 1, SoundCore 0). A host-load dependent dropout is a known property of that emulator, so every free-running number is paired with the stepped capture. `native_gfx_proof.py` reports separately: emulated vblanks per wall second, skipped pictures (`sat_dbg` +0x64), pictures started and shown (`plot_started`, `plot_shown`), plot waits, and the game's own pose (frame record, timer) per leg. Open: input scheduled by emulated ticks for the attack, pose-change counts per tick for the reference build, and a single-session A/B of Schaefer (setting off) against the skin and the native build.

## 11. Status against the V2 milestone

- Done: format and access findings (sections 1 to 3), the relocation data proof, the access-point audit, the stand prototype (section 8).
- **Not done: the one-attack native build, the clip, the performance comparison.** The path is long and I did not shortcut it: (1) HOST: build the relocated Schaefer-equivalent block into the native host runner (window page, 26 slots, 10 resolver sites) and run the 61-field and outbound-region comparison on the 272,171-frame route, only the named pointer deltas allowed; (2) generate Wolverine's block for idle, walk and one claw attack (slot 32 chain) with boxes in a character-owned table T' in the same window, flag skeleton copied from the donor chain; (3) target link, memory map, stage 26 canary; (4) Yaba clip with paused and free-running legs under the baseline protocol. Rough estimate: (1) and (2) about a day each, (3) and (4) half a day each, after a slot census limited to the slots this milestone touches (stand 0, 15, 24..28, 44..47, 58; walk 2; first claw attack 32 and 33; the terminal records).
- Fit: the approach fits (section 5). The stand prototype alone costs 862 bytes of tail and crosses a 4 KB step; that is expected and does not change the verdict.

## 12. Not done, not claimed

- Slot roles (stage 0), any chain longer than the stand, any move but the stand. No hit box, timing or palette-table change in the prototype.
- No identity run beyond section sizes for the flag off; no hardware; no hardware-speed claim.
- The cart tail with the flag on crosses the 244-byte slack (prototype +862 bytes) and so costs one 4 KB page; it is a proof build, not a candidate.
