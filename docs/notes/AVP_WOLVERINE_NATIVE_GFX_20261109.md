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
Result (run1, 11-09, EMULATOR, paused A/B in one stage 02 scene): the game's emitter drew the stance from the 236-byte assembly (`N.png`, record 0x163158 held pointer 0x300000, trace in `shots/run1/trace.jsonl`); the player's frame record, timer and flags read as Schaefer's stand throughout. The object list of the native leg holds 23 first-row and 5 second-row tiles of his stance and the game's shadow entry; the skin leg's list holds Schaefer's two blocks (the skin's tiles are inserted later, in the snapshot). Differences seen: none beyond the 8 px mirror-axis shift (measured: native tile columns span object x 24..104 against the skin's 32..112 about the same actor x) and the camera, which scrolled 10 px between the legs and explains most of the apparent shift between the two screenshots. The shadow is present in both lists and the luminance band under the feet is the same in both pictures (35.5 against 33.0). This prototype is superseded by section 11 (the flag now maps the whole native block).

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

## 11. V2 milestone: native idle, walk and first claw attack (flag `-DSAT_WV_NATIVE_GFX`, default off)

Evidence tiers: **DATA** (program image), **HOST** (lifted game on a PC against MAME's golden, WSL gcc), **BUILD** (SH-2 link, D11 assets), **EMULATOR** (Yaba, own copy, port 9718). **No hardware.** Everything ROM-derived stays under `E:\AvP\learning\lane-wv-native-gfx` and `D:\AvP-lanes\lane-wv-native-gfx` (images and dumps are not in git).

### 11.1 What was built

- `tools/wolverine/gen_native.py` writes the block `gen/wv_native.inc` (and `.bin` for the host runner). One 64 KB window at 68000 address 0x300000 (`PAGE[0x30]`), **24,736 bytes**: 17,904 bytes of Schaefer's index tables and frame records relocated verbatim (548 reachable records, 0x163158..0x16754e, the span's own assemblies stay in the ROM image); then his native data, **6,832 bytes**: 27 records in 3 chains at 0x3045f0..0x3047ac, 22 pose assemblies (5,640 bytes, family 0xA), his box table T' (748 bytes: the donor's 12 hurt and 38 attack entries, plus 3 hurt and 1 attack entry of his own).
- **Idle**: MSHvSF's 17-record standing loop (0xd1c90, jump record at the end, ticks per record 4 to 12 from the ROM); 12 records are kept, the 5 whose tiles are not in the stage packs lend their ticks to the record before (the rule of `assets.py` THIN; D11's own idle is also 12 steps). **Walk**: Schaefer's 12-record skeleton (durations, flag parameter bytes, event bytes, shadow index: his walk speed is therefore exactly Schaefer's, as the plan's first pass asks), with his pose chosen by phase from MSHvSF's 16-record walk cycle. **First claw attack**: MSHvSF's light punch (0xd2878, 6 records; box-set indexes name his hurt and attack ids, boxes converted by the rule of `boxes.py`): startup record (flag 0), live record (flag 1, attack index into T', 7 ticks), terminal record (flag 0x8001, 4095 ticks, jump to itself, the donor chain's own shape).
- Tile pixels are matched to D11 keys with the weighted distance of `tilemerge.py` (K = 12): 632 ROM cells matched exactly, 434 within K by a merged tile, none "far" in the kept records. No new tile key: the stage packs and `fit.py` are unchanged.
- **Access points, all redirected, none patched in place**: the 26 opcode-store slots (4 bytes each, written when the setting turns on, restored when it turns off), the 11 immediates of the lifted code (`build.py` rewrites them to read `sat_wv_tb[4]`, a 16-byte table in the cart that holds Schaefer's own table addresses or the relocated ones), and the per-character box table entry at 0x19748 (named T' while on). `wv_nat_sync` runs once a vblank (pad hook) and on every player update; it also writes the second palette row of his 136 second-row tile entries from the stage word.
- While a player's frame record lies in his native range the skin leaves that player alone: the replacement pass, the move clock with its holds and recovery, the box swap and the x1.375 walk scale all skip him (`wv_nat_drawn`). Everything else (his other moves, hit reactions, grabs, KO) still goes through the relocated donor records and the skin, unchanged.
- Switches: build `-DSAT_WV_NATIVE_GFX` (with `GUEST_ASSETS`); runtime `wv_nat_dbg` bit 0 (debug port) takes the native data on or off in the same build (`native` / `skin` legs below).

### 11.2 Identity of the relocation (donor-equivalent data), HOST

Plan V2 order: relocated records holding Schaefer's own data first, only named pointer-address changes allowed. Runner: `tools/lift_runner/build_native_host.py --reloc 1` (new `host_reloc.c`: window page, 26 slots, the 11 immediates), the golden-checked lifted game against MAME's `golden_c1` route (272,171 vblanks, Schaefer). Named pointer changes the harness accepts: 4-byte values equal to the golden value plus the delta 0x19d070 inside Schaefer's table and record range (in work RAM, in the IRQ registers, in the PDUMP records), and nothing else.

| Run | Result |
| --- | --- |
| Plain runner (baseline) | clean 272,171 of 272,171, missed IRQ 0 |
| Relocated block (verbatim, 132 jump targets rebased, 26 slots, 11 immediates), mask extended for the pointer fields (+0x1c record, +0x52 table base, +0x96, +0xa6 of 0x80-aligned blocks) | **clean 272,171 of 272,171, 0 differing bytes outside the named pointer fields, missed IRQ 0** (a first version stopped matching at vblank 1130 because a pointer-holding register and a table base in an object block were compared raw; found by IRQ debug, fixed by the named-change rules above) |

Data-level proof (`reloc_check.py`; its closure was cut at 0x165480 by a range test, the full closure used by the host run has 548 records in two clusters and 132 jump targets, section 11.1): 637 records of the first relocation compared, 55,584 emitted object entries equal, 0 mismatches. Not the same as a 61-field diff against the base run: `fielddiff.py` of two runs is only meaningful where the golden mask does not hide a field; the 61-field diff of the relocated run against the base run follows.

`fielddiff.py` of the relocated run's PDUMP (one clean run, its own file) against the base run's: **frames 272,171, 61 fields x 2 players: 0 differing; whole 256-byte player blocks: 0 frames differing; collision lists, effect spawns, projectile pool hashes: 0 frames differing**. The `globals` hash (ff7f00..ff82ff) differs in 311 single, isolated frames (119 runs, the first at 5,298) and the enemy and object blocks hash in 1 frame (271,101); the golden compare outside the mask is clean in every one of those frames, the first 0x100 bytes of that region are masked by `mask.txt` (timers the golden does not model) and the differences are one frame wide, which fits an IRQ landing one instruction apart (the relocated run's IRQ is at instruction 54,031, the base run's at 54,032); I did not isolate the bytes, so the cause is **inferred, not shown**.

### 11.3 His native data, HOST (FREERUN, fight pad, same pad script, `scenario.py`)

Base runner against the relocated runner with his native block (idle, walk, attack chains and T' on, Schaefer's art, no skin): both reach the same set of state transitions (stand -> attack -> stand, attack -> hit reaction, ...), no new edge; the native run lands the light punch (24 damage, then 31 for the stronger hit the donor chain already gives) at vblank 1508 and 1520, which Schaefer's own chain misses in that window.

### 11.4 Memory (BUILD, D11, owner recipe, work directories from `integration/w1`)

| | flag off (avp/integration 4bfcdf6) | flag on |
| --- | ---: | ---: |
| hw_free | 1,252 | **1,252** |
| lw_free | 60 | **40** (the 11 rewritten sites and the 16-byte table) |
| cart_free | 4,340 | **7,136** |
| cold1_at | 0x27e2000 | **0x27db000** (7 steps of 4 KB: 224 tiles) |
| block `wv_blk` | - | 0x27f35a0 .. 0x27f9640, 24,736 bytes |
| wolverine.o text / data / rodata | 5.9 K / 14 B / 19.5 K | 6.6 K / 24.8 K / 19.9 K |
| fit.py, 76 stage files | 76 of 76 | **76 of 76, gate True**, no own key dropped, stage24_ma margin 48 tiles (Schaefer variant drops 3,128, his 3,080; before this lane 38 at the integration room) |
| ISO | 391,497,728 | 385,818,624 |

The block is in the cart tail: the build's canary line (`build.py`) reports it **outside the ROM image (0x2400000..0x2600000) and every ROM stretch, inside the tail**, so no stage file, stage 26 included, can drop or overwrite it. 17.9 KB of the block is the donor span copied for identity; the span's assembly gap (5.9 KB between the two record clusters) could be compacted out at the price of 30 changed table words, and the donor copies could go once every slot has a native chain. The brief's 108-byte margin was one D6 build; this link's margin before the step was 244 bytes (cart_free 4,340 minus 4,096), and the flag-on build crosses it by 6.8 KB, accepted here as a measurement build.

### 11.5 Yaba: paused sequence, contact, free-running comparison (EMULATOR)

Same saved machine state loaded for every leg (stage 02, he stands, enemies near), mode set by poking `wv_nat_dbg` / `sat_guest_sel` in that state. Paused legs advance one frame at a time (`framebuffer_burst`); the trace per frame is in `shots/att*/trace.jsonl`.

- **Idle**: the player's frame record walks 0x3045f0..0x3046a0 and jumps back to 0x3045f0 (12 records, 4 to 12 ticks each), no skin pass drawing him.
- **Walk** (`right`, `left`): state 020002, records 0x3046b4..0x304764, parameter bytes 0a 06 07 09 0e 0e 0a 05 08 07 01 10, loop; x advances 10, 16, 7, 9 px over the first four records of a `left` press (1,182 -> 1,172 -> 1,156 -> 1,149 -> 1,140), Schaefer's own stride; the skin leg takes 13, 22, 10, 12 (1,184 -> 1,127) because of its x1.375 scale, which is skipped for native records.
- **First claw attack**: tap at frame 27 (att3): state 020006 at once, record 0x304778 for 2 ticks (startup, hold 2), 0x304788 for 7 ticks (live, flag 1, attack index set), terminal 0x304798 (flag 8001), back to stand at frame 37: **10 ticks from press to stand** against 16 for the skin leg (frames 27 to 43; Schaefer's records 0x163644, 0x163654, 0x163664, 0x163674 are 13 ticks, the rest is the skin's held updates). A fast second tap restarts the chain (frames 127, 135); a hit interrupts it (att3 frame 186: state 020200, record 0x301364, health 101 -> 91, the same frame in the skin leg: the same enemy timing, the same hit).
- **Contact**: the enemy-health counter I log (tag-0c blocks) did not move in the native legs (att3, att4, att5) and moved in one skin leg only (att4: 174 -> 150 -> 126 at frames 66 and 81, because the skin's longer attack was still running when an enemy walked in). The contact sheet `evidence/lp_native_vs_skin_att4.png` (every second frame from 4 to 24, native over skin) shows his claws at full reach with bright spark effects beside them in both rows (native frames 14 to 16, skin 16 to 18), so **contact is seen in the Yaba frames but not counted there; the damage count (24 per light hit) is the HOST result of 11.3**. A scripted enemy at a fixed distance is what a counted Yaba contact needs; not done. The attack box against the claws is checked on the data (`native_overlay.py`, `evidence/overlay_lp.png`): the live record's box sits on the extended claws, his hurt box covers the body and the feet are on the line.
- **Free-running comparison** (same state, same input schedule paced by polling the emulated vblank counter, 15 s a leg, two repetitions, Schaefer = `sat_guest_sel` 0; the player's health is topped up in every leg alike so a leg is not cut short):

| Run | Leg | Emulated vblanks / wall s | Pictures started / shown per vblank | Skipped (d_skips / vblank) | Record changes seen |
| --- | --- | ---: | ---: | ---: | ---: |
| att1 | native | 56.4, 56.8 | 0.78 / 0.78 | 0.22, 0.23 | 149, 144 (all native) |
| att1 | skin | 46.2, 46.3 | 0.75 / 0.75 | 0.25, 0.26 | 91, 86 |
| att1 | Schaefer | 59.4, 59.4 | 0.78 / 0.78 | 0.22, 0.21 | 102, 116 |
| att3 | native | 53.8, 58.2 | 0.75, 0.80 | 0.26, 0.20 | 96, 127 |
| att3 | skin | 47.9, 49.2 | 0.73, 0.78 | 0.27, 0.22 | 74, 75 |
| att3 | Schaefer | 59.3, 59.6 | 0.75, 0.60 | 0.24, 0.40 | 81, 86 |

So in this scene the skin costs about **20 percent of the emulator's frame rate against Schaefer** (46 to 49 against 59), the native path takes it back to **95 percent in att1 (56.6) and 91 to 98 percent in att3** (53.8, 58.2). The scene is the same state but the enemies are not scripted, so picture counts differ by the fights; the vblank rate is the cleanest column. **Emulated game work** (the guest pass's own ticks, `sat_gprof`) is not in these runs: the build has no `SAT_GUEST_PROF`, so that column is not reported. Host speed here is dominated by Yaba's recompilation of the cart-resident guest code on every call (the dropout lane's finding), which is exactly what the native path removes from the per-frame path; presentation (new/held/skipped/late) is reported as started, shown and skipped pictures, the late count (`plot waits`) per leg was 15 and 14 (native), 23 and 20 (skin), 8 and 8 (Schaefer) in att1 and 0 and 1, 1 and 1, 0 and 0 in att3. A hardware figure does not exist.

### 11.6 Flag-off identity against avp/integration (BUILD)

Two builds from copies of `integration/w1` with the owner recipe: avp/integration 4bfcdf6 (`git archive`, `id_a`) and this branch at the pushed head with `-DSAT_WV_NATIVE_GFX` undefined (`id_b`). Result: `HW.BIN`, `LW.BIN`, `COLD1.BIN`, `OPX.BIN` and `ROM.BIN` byte-identical (sha256), the `nm` symbol tables of the two `sat.elf` identical, the whole staged disc directory (all 287 round files, IP.BIN and the rest) hash-identical, and `sat.iso` the same size (391,497,728 bytes) with 3 of 191,161 sectors different (sectors 16 to 23: the ISO9660 volume descriptor and directory records, which carry the build time). Memory of the flag-off link: hw_free 1,252, lw_free 60, cart_free 4,340, cold1_at 0x27e2000, as the integration owner build.

### 11.7 What is not done, plainly

- Only idle, walk and the first claw attack are native. The other 189 slots still run the relocated donor records and the skin (hits, jump, throw, KO, the finisher, Berserker); the skin pass, the clock and the box swap are still in the build.
- LP keeps 3 of the 6 ROM records (the others' tiles are not resident in the stage packs); startup and live frames are 2 and 7 ticks, not the ROM's 2, 2, 2, 1, 2. His other attack records, the slot census, T' for every record, native walk durations, jump arc, palette from the game's table: stages 3 to 6 of section 7.
- The mirror axis change of 8 px (section 4.1) is in these captures. The shadow on the stand (run1) was not missing: the shadow object is in both object lists and the luminance band under his feet is the same in both pictures; the offset the coordinator saw between N.png and S.png was mostly the camera scrolling 10 px between the legs.
- Input is paced by the poll of the vblank counter, not by a scripted pad inside the machine (needs a build flag); enemies are not scripted; no unassisted Round 1; no hardware.

## 12. Not done, not claimed

- Slot roles (stage 0), any chain longer than the stand, any move but the stand. No hit box, timing or palette-table change in the prototype.
- No identity run beyond section sizes for the flag off; no hardware; no hardware-speed claim.
- The cart tail with the flag on crosses the 244-byte slack (prototype +862 bytes) and so costs one 4 KB page; it is a proof build, not a candidate.

## 13. Step 2 (11-09, after the census of AVP_WOLVERINE_NATIVE_CENSUS_20261109.md): every chain native

Evidence tiers as in section 11; the census note has the slot map this builds on. **No hardware.**

### 13.1 What changed
- `gen_native.py` now emits **all 135 distinct chains** (572 records) of the 227 index entries. Idle, walk and the first claw attack keep milestone 1's ROM-timed chains. Every other chain keeps **the donor's skeleton** (durations, flag byte = root-motion index and sub-state trigger, `+10/+11`, event bytes `+12..15`, jump structure, jump targets remapped) and takes poses and boxes from a **role's MSHvSF chain** (`ROLE_T1` / `chain_role`, `SRC` in the generator; MSHvSF animation index decoded in the census note, section 5). Only resident tiles are used: a record whose tiles are not all in the packs is dropped and its ticks go to the record before it, so **no new tile key, the fit is unchanged by construction**. Nothing of Schaefer's records is copied any more; only his four index tables (456 bytes) are, so the 17.9 KB donor span of milestone 1 is gone from the block: **22 to 24 KB, was 24,736 bytes**.
- Roles (first assignment; the provisional ones are marked): ground holds and aliases idle; the 6-record crouch/landing chains the landing chain (1.3: knees bent); the chain `0x20 + stage` T1.32/33 the first claw attack (ROM timing), T1.34 his second light punch, T1.35 his heavy punch (donor timing: **the owner's "timing change is a comparison" rule: none shipped**); the special T1.42 (state 020008) the Berserker flurry (MSHvSF sub-table 22 entry 10: 18 records, each with an attack box, 6 of them resident); the kick states T1.14/16/41 his kick (9.2); the 12 grab/held chains his hit-reaction poses; T2 (hit, knockdown, getup): flinch holds the medium/light/heavy hit sets (14.2-14.4), knockdown flight the jump poses, ground the landing poses, the 9-record getup chain the landing poses over its ticks.
- **T3 (48 slots) is not a jump table.** Its chains are the gun action's aim poses (state 02000c, 30k selections in play: 16 directions times three sets); the skin maps 02000c to his Berserker already (`move_for`). Native: each T3 chain shows one flurry pose chosen by slot, so the rapid slot cycling of that state animates the flurry, and the hold record carries that pose's attack box. **Provisional**: how Berserker deals damage and costs health natively is plan section 6's explicit-action design; the stock cost rule and multi-hit are untouched and the projectile suppression stays.
- **The leap (state 020004)** is not a jump either: Schaefer's is a flat low leap (`AVP_WOLVERINE_GROUND_20261109.md`), the arc is the skin's `wv_lift`. Native: chain T1.37's 4,095-tick hold is replaced by 11 arc records (2 to 3 ticks, sub-steps of the six resident jump poses, lifted by the owner's apex, `WV_JUMP_SCALE` default 0.838 = SAT_WV_JUMP=1) laid over the 25 ticks the hold lasts in the host trace, then the terminal hold. The state routine ends the leap by its own physics (x velocity), so the arc ends with it.
- `native_states_proof.py` (Yaba schedule: chain x3, leap, leap + attack, Berserker motion, idle under attack, hits), `buttons.pad` and `state_runs.py` (host).

### 13.2 HOST (WSL runner `reloc`, new block, FREERUN, `buttons.pad`, golden_c1 from vblank 1133, 7,000 vblanks)
Same pad and start as the plain runner (`base`, Schaefer). Both runs reach the same set of state transitions (33 and 34 transitions, none new in the native run); the native player's frame record is in the native window for 4,901 of 7,000 frames (the rest is before spawn and the first update), never stuck. Native run selected 47 slots (T1.0/1/2/3/10/13/14/32/37/48/55/76, T3.3..6, 21 T2 slots, 7 T0 entrance chains). **No-hang, no-stuck-state check, not identity**: the golden compare cannot hold once durations and boxes differ (section 11.3). The identity of the relocation itself (milestone 1, 272,171 / 272,171) is unchanged: `reloc_block.py`, `host_reloc.c` and `mask_reloc.py` were not touched.

### 13.3 Build, memory, fit (BUILD, owner recipe + `-DSAT_WV_NATIVE_GFX`, workdir copy of integration/w1, KEEP_ROUND_FILES=1)
| | milestone 1 (24,736 B block, merged select-screen fix not in) | step 2, final (25,128 B block) |
|---|---:|---:|
| hw_free | 1,252 (integration then) | **964** (= integration 55cf228) |
| lw_free | 40 | 40 |
| cart_free | 7,136 | 6,336 |
| cold1_at | 0x27db000 | 0x27db000 (7 steps of 4 KB = 224 tiles, as milestone 1) |
| fit.py, 76 stage files | 76 of 76 | **76 of 76, gate True**, stage24_ma: Schaefer drops 3,128, Wolverine 3,080 (margin 48), no own key dropped |
| block | 24,736 | 25,128 (135 chains, 572 records, 54 assemblies, T' 844 B) |
The block grew a little (leap arc, 54 assemblies) although the 17.9 KB donor span is gone, because the donor span's replacement is 9.7 KB of records; **no memory is credited yet**: the skin's tables (`wv_tiles` 16.8 KB, boxes, text) are still linked, so the tail still crosses the same 4 KB steps. The credit exists only after step 3. WSL unittest: 106 run, 30 errors = the known private-dependency set (same as integration's baseline).

### 13.4 Yaba (EMULATOR, own copy, port 9718, SH-2 cache emulation ON as the milestone legs; paused legs from one saved state: stage 02, chain, enemies near)
Paused legs, native (`shots/states1`, `kill2`, `long1`; pictures inspected as contact sheets):
- **Chain** LP, LP, HP (taps at 6, 22, 38): states 020006 at 8, 24, 40; every frame of the native leg has the player's frame record in the native window (700 of 700); poses differ by stage (first claw attack, second light punch, heavy punch), drawn by the game's emitter, no skin pass.
- **Leap (020004)**: crouch, then the arc rises and falls over about 18 frames and lands (frames 118..136), 33 ticks per leap in both leaps; Schaefer's leg is flat as designed.
- **Berserker (state 02000c from QCF + attack)**: 9 ticks of flurry poses; the Warrior's health went 174, 150, 126 (24 per contact, every 4 ticks) and the score rose, so the T3 hold records' attack box deals the multi-hit damage natively; no gun projectile (suppression unchanged).
- **Hits**: flinch holds with the hit spark; 020200/020202 with the donor's 4,095-tick hold and the game's own end.
- **Knockdown and KO** (`PROOF_KILL`, health 1, unassisted): 040000, 040200, 040202, 040204, 040206, 040400, then he is removed and the game-over cut plays (frame 196-216), the same sequence as Schaefer's leg. **Found and fixed in this lane**: the first KO build drew him floating at screen height during 040400 because MSHvSF poses carry their own height; the generator now floor-aligns every pose whose height the game supplies (`floor_cells`); the leap arc lifts a floor-aligned pose by D11's sole height. Re-run after the fix (kill2): flight, landing and removal read as Schaefer's.
Free-running (`perf1`, 15 s a leg, two repetitions, same schedule, health topped up in every leg, host shared with other lanes, so only the ratios mean anything): emulated vblanks per wall second **native 59.55 / 59.08, skin 55.01 / 54.42, Schaefer 59.52 / 59.60**; pictures started per vblank 0.84 / 0.84, 0.76 / 0.76, 0.88 / 0.89; skipped (plot waits) 0, 0 / 2, 3 / 0, 0. The native path is at Schaefer's host speed in this run; the skin costs about 8 percent here (it cost 20 percent in milestone 1's busier host). A second, longer native leg recorded with OBS (`perf1b`, 70 s x 2) ran while two other builds and the recorder were using the host: 43.05 and 40.99 vblanks/s (0.76 started per vblank); it is footage, not a measurement. Hardware: none.

### 13.5 Not done in this step (plain)
- Step 3 (retire the skin machinery) and its memory credit: the skin's pass, clock, holds, box swap and the projectile-pool manipulation are **still in the build**; they skip a player whose record is native, which is now every state of a Wolverine player in the legs above. Not verified: grabbed/held (020400, 020406) and getup (040208) in Yaba, stage transitions, continue after KO, save/load, stage 26, both player slots and mixed co-op, a full unassisted Round 1.
- No timing comparison variants (22-tick kick finisher, 12/12/16/28), no HK in the chain, no native Berserker action (the gun action's state is reused; cost rule and projectile suppression untouched), no talk-box face, no palette-from-game-table.
- Roles marked provisional in the generator (grab chains show his hit poses, T1.11/12/13/20 ground holds show idle or landing, unreached chains idle) are the first assignment; reaction poses beyond the resident set are the nearest resident ones (tile cost in the census note section 5).
- Comparison disc for the owner (faster heavy punch, chain with and without HK): not built, the variants do not exist yet.

### 13.6 Late additions
- **Flag-off identity (BUILD)**: avp/integration 55cf228 (`git archive`) and this branch with the flag undefined, owner recipe, copies of integration/w1: `HW.BIN`, `LW.BIN`, `COLD1.BIN`, `OPX.BIN`, `ROM.BIN` byte-identical (sha256), `sat.elf` the same size (2,047,072 bytes). The two builds were stopped after the link (round files were still rebuilding because the merged select-screen change touched pack inputs); the disc image and sector comparison were not repeated.
- **Berserker hooks** (for the sound, flash/freeze and healing lanes), `wolverine.c`, native build only, weak default-empty functions: `wv_on_berserker_start(player)` on the tick his state becomes 02000c, `wv_on_berserker_connect(player, damage)` on a tick in that state where the tag-0c enemy blocks lost health (read from the enemies' health words, not the collision code), `wv_on_berserker_end(player)` the first tick after. Cost: lw_free 40 to 32, cart_free 6,336 to 6,168, hw_free 964 unchanged.
- **OBS footage** of a native leg (`perf1b`): E:\AvP\learning\integrationideo6-11-09 21-55-55.mkv, window "AvP NATIVE: perf1 [port 9718]", 70 s x 2 free-running legs, native Wolverine fighting in stage 02; host shared with two builds and the recorder: 43.05 and 40.99 vblanks/s (footage only; the clean numbers are in 13.4).


## 14. Step 3 (11-10): Berserker as his own action, skin machinery out of the native build, lifecycle checks, comparison discs

Evidence tiers as in section 11. **No hardware.** Evidence (not in git): `E:\AvP\learning\lane-wv-native-gfx\evidence3` (traces, summaries, logs, contact sheets; `ev/` in the text is `evidence3/`, the Yaba shots are `evidence3/shots`). Yaba legs ran on a shared, busy host (emulated vblanks per wall second 20 to 40, other lanes on 9721-9725): speed numbers are noisy and not reported; pictures were judged from paused `framebuffer_burst` frames. Owner decisions applied: stay resident-only (no extra tiles); the flurry poses are kept; claws only (no gun code for him); the cost is the stock special's, 6 health, charged on connect; multi-hit with a per-target cap; chain LP LP HP with HK only as a comparison; every timing change ships as a comparison first.

### 14.1 Berserker: what runs now
- **State 02000c, routine `sat_wv_bz_run`** (wolverine.c). Schaefer's own 02000c routine is `f_2576a` (table 0x893e entry of character 1; `f_24060` is the Warrior's and Hunter's gun, so the earlier `f_24060` wrapper never saw him). game_bind.c wraps `f_2576a` (native build only): a Wolverine player runs his routine, everyone else the lifted body. Nothing of the gun runs for him: no shot, muzzle flash, gun sound, heat or ammo test, and the projectile-pool suppression, the shot refusal in the collision wrappers and the draw-time shot drop (guests.c) are not compiled in the native build. The co-op partner's gun is the stock routine (no wrapper on `f_24060` in the ELF).
- **Entry**: QCF + attack (pad hook) no longer injects the gun button. It releases all three buttons for 4 vblanks and sets a request (`bz_req`, 6 vblanks); the pre-hook of his player update (`wv_bz_enter`) applies the engine's own entry rules (stand or walk state, `+0x5c`, `+0xad`, `+0x8b` clear, `ff8208` and `ff822b` clear, not stage word 0a) and writes the state the stock entry writes (02000c00, lock `+0xad`). The plain gun button stays masked (one line in the pad hook): it does nothing for him.
- **Action** (the state machine's conventions for a melee action): lock `+0xad`, action class `+0x92`, facing `f_1a364`, a **new strike id (`f_1d768`) at every record**, frame record advanced by `f_1656e`, exit through `f_1a3e2` when the terminal record is reached. His own chain (gen_native.py `BZ`: 12 strike records of 4 ticks and a terminal record, 48 ticks; poses = the six resident flurry poses in the order the stock gun burst visits them, T3 slots 6 6 5 5 4 3 3 4 5 5 6 6, so the approved look is unchanged).
- **Contact box**: MSHvSF's record of these poses carries one box, a column above his head (forward -12..12, up 108..144, hit id 97), which cannot touch a standing enemy; the strikes use the light punch's reach (forward 26..84, id 31) at the heavy punch's body band (up 13..85). **Owner-visible approximation**: the poses are the spin and the claws-up pose while contact is forward (sparks on the enemy in front of him while his claws are raised, `ev/bz8/sheet.png`).
- **Cost and cap**: the collision wrappers (game_bind.c; one byte `sat_wv_bz` is tested in every pass, the cart is entered only while he is in the action) ask `sat_wv_bz_gate` before a pass and tell `sat_wv_bz_hit` after one that hit. The first connect of an activation charges the stock rule (`f_1b492`: 6, health left under 6 goes to 0), nothing on a whiff. A target takes at most `WV_BZ_CAP` = 6 strikes per activation (6 targets tracked); a refused pass answers "no hit" the way the lifted exit does.
- **Hooks** (`wv_on_berserker_start/connect/end`): names, arguments and call points unchanged (pre-hook of his update, state 02000c, enemy-health based contact); `start` now fires on the tick the state is entered.

Yaba (EMULATOR, builds b3 and b8, paused legs from one saved state, `tools/wolverine/native_bz_proof.py`, traces `ev/bz*`):

| Leg | Result |
|---|---|
| Whiff (bz4) | QCF + A: state 02000c entered 2 frames after the press; 12 strike records 0x3027ac..0x30286c, 4 ticks each, strike id 75 -> 86; back to stand after 47 ticks; health 101 throughout; `sat_wv_bz` set and cleared; no shot, flash or gun state |
| Contact (bz8, enemy pinned 60 px in front, 87 hp) | hits at frames 5, 16, 27, 38: enemy 87 -> 63 -> 39 -> 15 -> dead (24 per hit, score 100 -> 2800), health 101 -> **95 once**, constant afterwards |
| Cap 6 (bz10, enemy health pinned) | six hits (frames 5, 16, 27, 38, 49, 60: one per strike); the run was cut at frame 63 by another enemy's hit (020202, `bz` cleared at once), so the seventh refusal was not seen at cap 6 |
| Cap 2 test build (cap2c, `-DWV_BZ_CAP=2`) | two hits (frames 5 and 18), then strikes 3..12 refused (no damage while the enemy stayed in reach), the flurry ran to its end (frame 67), cost 101 -> 95 once |

Grab conflict (found, stock behaviour): the QCF contains down + forward; with an enemy within about 70 px the engine starts its grab (020400/020406) before the motion's attack button arrives, so the request cannot be accepted. The old gun injection had the same conflict; it is the stock game's walk-into-enemy grab.

### 14.2 Skin machinery retired from the native build (flag on); the skin build stays (flag off)
Compiled out under `-DSAT_WV_NATIVE_GFX`: sprite removal and reinsertion and the whole-list pass (`sat_guest_objects` keeps the HUD/select names and his two palette rows), the hold/recovery scheduler and move clock (`wv_tick_move`, `wv_advance`, `wv_begin_move`, `move_for`, the tables `wv_nat_tab`, `wv_steps`, `wv_lift`, `wv_tiles`, `wv_box`), collision patch-and-restore (`sat_guest_wolverine_boxes`, `poke4`, the undo list, the box calls in `guest_pass`), in-place Schaefer record changes, the walk scale (`wv_speed`), the after-tick observer, the gun wrapper with the projectile suppression, the shot refusal and the shot drop. The native ELF has none of `wv_tiles`, `wv_box`, `sat_guest_wolverine_boxes/_bullet/_gun/_after_tick`, `lifted_24060`. With the flag off the same sources compile to the same code (identity below).

### 14.3 Memory (BUILD, D11, owner recipe + `-DSAT_WV_NATIVE_GFX`, workdir copy of integration/w1)

| | integration 55cf228 (flag off) | step 2 native (b368017) | **step 3 native** |
|---|---:|---:|---:|
| hw_free | 964 | 964 | **1,080** |
| lw_free | 60 | 32 | **104** |
| cart_free | 4,340 | 6,168 | **4,140** (44 bytes before the next 4 KB step) |
| cold1_at | 0x27e2000 | 0x27db000 | **0x27e2000** |
| block `wv_blk` | - | 25,128 | 22,064 |
| wolverine.o text / data / rodata | 5.9 K / 14 B / 19.5 K | 6.6 K / 24.8 K / 19.9 K | **3.1 K / 22.2 K / 0.5 K** |
| ISO | 391,499,776 | 385,818,624 | **391,497,728** (one sector under the integration disc) |
| fit.py, 76 stage files | 76 of 76 | 76 of 76 | **76 of 76, gate True**; stage24_ma: Schaefer drops 2,872, Wolverine 2,834 (margin 38); cart pack room 1,630,208 |

**The native tail is back at the integration owner build's step: the memory credited is the 7 four-KB steps (224 tiles) step 2 had spent**; against flag off the native build costs no tiles (the stage24_ma figures are identical: 2,872 / 2,834, margin 38). Removing the skin was not enough for the last step (3,552 bytes were still missing): the rest came from sharing the 48 T3 slots (3,196 bytes: the stock gun's aim chains are dead for him), dropping T's unused leading entries (112 bytes; the collision pass adds sign-extended word offsets, so nothing was renumbered) and packing the palette marks and slot offsets as deltas (about 400). hw_free grew by 116 and lw_free by 44 against integration (the skin hooks left game_bind.c, the clock's statics left low RAM).

### 14.4 Gates
- **HOST identity, stock Schaefer with the flag on** (wrappers linked, guest off `WV_SEL=0`, golden-checked lifted game): golden_c1 clean 272,171 of 272,171, golden_2p (the second Schaefer slot) clean 329,918 of 329,918, 0 differing bytes, missed IRQ 0, the same as the plain runner.
- **Flag-off identity against avp/integration**: two builds from pristine copies of integration/w1, owner recipe, the integration archive and this branch with the flag undefined: `HW.BIN`, `LW.BIN`, `COLD1.BIN`, `OPX.BIN` and `ROM.BIN` are byte-identical (sha256), `sat.elf` has the same size (2,047,072 bytes) and the same sorted `nm` table (sha256 fc883e35...), `sat.iso` has the same size (391,499,776) and 56 bytes differ in sectors 16, 18 and 23 (the ISO9660 volume descriptor and directory records, which carry the build time). The rounds were rebuilt in both builds (the integration w1 receipt did not match), 1,804 and 1,732 s.
- fit.py D11 (on a copy of the asset directory): 76/76, gate True, none of his own keys dropped, no missing guest key.
- WSL unittest: 106 run, 30 errors (the known private-dependency set, as integration), 1 skipped.
- Builds: rc 0, no NO-GO.

### 14.5 The unverified states of section 13.5 (EMULATOR, tools `native_soak.py`, `native_coop.py`, `r1run.py`)

| State / flow | Result |
|---|---|
| Soak, stage 02, unassisted (soak2: 10,776 vblanks, 2,503 polls) | 19 state words reached; every sample has his frame record in the native window (0 donor records); 3 KOs with 3 continues (the game's own continue, the select screen, his slot chosen again); 0 stuck states (the three holds over 400 vblanks are the continue countdowns); 0 fatals |
| Grabbed / held 020400, 020406, thrown 020408 | reached in play and in Round 1: native records 0x300db4.., 0x300f2c..; no stall; the poses are his hit poses (placeholder, 14.7) |
| Getup / KO 040200 040202 040204 040206 040208 040400 | reached, same sequence as Schaefer's; he is removed and respawns through the continue |
| Stage entrance 080000, section and **stage changes** | reached after continues and in Round 1 (section 1, boss, then the game's own stage change: NOW LOADING, "ROUND 2 WAR IN THE UNDERPASS", 600 vblanks of play in the new stage with his native records, claws in the stage's second palette row; `ev/shots/clear_14420.png`, `after_14588.png`, `after_end_15190.png`) |
| Continue after KO, restart | works (3 in the soak, 6 in the Round 1 run); every Yaba launch is a cold boot with the block applied |
| Save/load | the Yaba save state (cart RAM and BSS) loaded for every paused leg and for the second Round 1 leg; the game's own saves hold nothing of his |
| Stage 26 | **not reached**: the stage select goes to 24, and a warp to 0x26 ends in FATAL 0xe2 detail 0x91ec on the **unmodified integration build as well** (`ev/st26base`), so it is not this lane's result. Established: the block is in the cart tail, outside the ROM image and every ROM stretch (the build canary), and fit.py's `stage26_m*_wv` files pass with none of his keys dropped. A full-play run to the ending was not done. |
| Co-op: Wolverine P1 with Warrior, Hunter, Linn as P2; Wolverine P2 with Warrior, Hunter, Linn as P1 (`ev/coop_*`) | 92 to 137 samples each; his frame records native in every sample; the partner's states normal; 0 anomalies, 0 fatals; his Berserker entered in 5 of the runs; no shot actor owned by him in any run; the Warrior partner's gun fired normally in the one run where it was pressed while he was present (6 shots owned by the partner) |
| Wolverine as P1 and as P2 | both slots work (the runs above) |
| Unassisted Round 1 (`r1run.py`: no top-up, no boss boost, no warp, no kill; two legs joined by a Yaba save state in the boss fight) | boss present at vblank 5019 (first leg) and 9221 (second leg, from the saved state), 6 KOs and continues in all, 12 Berserker motions played, boss cleared (flag in section 2 at vblank 14420), the next stage (Round 2) entered at 14588 and played 600 vblanks; no fatal, no stuck state |

Bug found and fixed in this lane: `wv_nat_sync` runs from the pad hook (vblank) and from the player update and wrote the four table-base immediates with `+=`; two callers in a row doubled them (table base 0x49d070 = 0x162f90 + 2 * 0x19d070, the game hung; seen twice in Yaba). All its writes are absolute now.

### 14.6 Comparison variants and the owner disc
Knobs (gen_native.py, build time; defaults are the standing decisions): `WV_CHAIN` 3 (default: LP, LP, HP; the stock stage counter has four stages, so the two `& 3` sites of the lifted attack routine read his count `sat_wv_cn`, 4 for everyone else) or 4 (LP, LP, HP, HK); `WV_HP_TICKS` 0 (default: the donor's heavy stage skeleton, 2/2/6/5/3 = 18 ticks) or N (rescaled; 12 for the fast heavy punch). The kick keeps the donor stage's 18-tick skeleton (not the planned 22 or 28), its reach from MSHvSF and its height lowered to the body band (the ROM's box, up 103..127, never connected). Yaba chain checks (pinned enemy, 6 taps): default LP, LP, HP and then LP again (the counter wraps at 3); `WV_HP_TICKS=12` heavy punch records 2/1/4/3/2; `WV_CHAIN=4` LP, LP, HP, HK (records 0x300a30..0x300a80) and the kick connects.
Disc set `E:\AvP\package-integration\wv_native_compare_1` (iso + cue + 26 audio tracks per disc; the tracks stored once and hard-linked into the other folders): `A_default`, `B_fast_heavy_punch`, `C_chain_with_kick`, README.txt. Each packaged cue boots in Yaba to a stage 02 standing frame with native records.

### 14.7 Not done, and owner decisions
- Hardware, a full-play run to stage 26, speed numbers (host busy). The grabbed, held and thrown chains and the ground holds still show his reaction poses (the placeholder roles of 13.1): visible when he grabs.
- Owner-visible decisions: (1) the Berserker's contact geometry (the poses spin, the box reaches forward); (2) cap of 6 hits per target and 48 ticks; (3) the kick box lowered; (4) which comparison variant becomes the default. Also the grab that comes before the QCF is finished when an enemy is close.
- Tail margin: 44 bytes before the next 4 KB step (a lane that adds data must trim first).


### 14.8 Follow-up (11-10, head after e33b9cf): connect events on the real enemy pool, cart tail

**Event bug (features lane).** `wv_enemy_hp()` summed ff9a00..ffc700 in steps of 0x100 with a tag test; the enemy pool is 20 blocks of 0xc0 from ff9580 (health +0x40, the boss ffa3c0), so the scan landed on a real block about one time in three and `wv_on_berserker_connect` missed most contacts. Now `wv_pool_loss` walks the pool: per block the health at the last look is kept (40 bytes of low RAM), the damage is the sum of the losses of blocks live at both looks. A block not in use reads as unknown, not 0 (a block that leaves or joins the pool, seen flickering in Yaba, is no damage; the first version without this reported 87 for it), and a dying block (health 0xffff) counts 0, so the killing blow is reported. Names, arguments and call points of the three hooks are unchanged. Nothing else reads it: the 6-health charge and the hit cap are in the collision wrappers (`sat_wv_bz_hit`, `sat_wv_bz_gate`), not in the events.
Yaba (build with `-DWV_BZ_EVENT_TEST`: counters start, connect calls, damage summed, end; traces `evidence3/ct2`, `wh6`):
| Leg | Result |
|---|---|
| Contact (ct2: enemy pinned 60 px in front, health held up) | strike ids 50..55 hit, 56..61 refused (cap 6 binds with a target in reach), health 101 -> 95 once, start 1, **connect calls 14, damage 327** (every 24-point hit and the killing blow's remainder), end 1 |
| Whiff (wh6: every enemy put 400 px behind him each frame) | 12 strikes, health constant, no hit flag, counters 1, 0, 0, 1: no connect event, although pool blocks left and joined the pool three times during the flurry |

**Cart tail.** The features lane (heal 258 bytes, flash 198) adds 458 bytes against a margin of 44; recovered 692 bytes, behaviour and drawn output unchanged: cart_free 4,140 -> **4,832** (736 bytes before the next 4 KB step; the 692 includes +72 bytes of code for the pool walk and the palette walk). Three changes, all in the generated block: (1) chains with byte-identical records are stored once (11 chains, 380 bytes; a terminal that jumps to itself behaves the same in either copy); (2) the 48 T3 slots, which only the stock gun routine reads, answer with the Berserker's own chain instead of a chain of their own (68 bytes); (3) the second-row palette marks, a 340-byte table, are gone: second-row tiles carry palette 0 in the block (his first row is always 1) and the runtime walks the 54 assemblies when the stage's row changes. Block 22,064 -> 21,616 bytes, `.rodata` 504 -> 164, text +72. Costs: low RAM 104 -> 68 free (the pool's 40 bytes); hw_free unchanged 1,080. Drawn output: Round 1 and the following stage in Yaba with his second palette row correct (`evidence3/shots/soak_end.png`), soak9 (8,047 vblanks, 22 state words, every frame record native, 0 fatals).

Gates for this follow-up: build rc 0; fit.py D11 76/76, gate True, stage24_ma 2,872 / 2,834 (margin 38, room 1,630,208, no key of his dropped); HOST golden_c1 clean 272,171, golden_2p clean 329,918 (guest off, flag on, 0 differing, missed IRQ 0); WSL unittest 106 run, 30 errors, 1 skipped (baseline); flag-off identity against the integration archive build (built from this commit, owner recipe, flag undefined): `HW.BIN`, `LW.BIN`, `COLD1.BIN`, `OPX.BIN`, `ROM.BIN` byte-identical (sha256), `sat.elf` the same size and the same sorted `nm` table, `sat.iso` the same size (391,499,776).

### 14.9 Follow-up 2: one connect call per landed strike (sounds lane)
**Where the 14 calls came from** (ct2: 6 strikes hit, 14 calls, damage 327). Not the scan: the harness. Its `pin` helper puts the *nearest* enemy in front of him every frame and holds its health up, so after a hit the next-nearest enemy is pinned too, and each strike landed on one to three targets (the cap is per target, so six strikes per target: three pinned enemies give up to 18 hits). The old call came from the pool diff, once per tick with a loss, so it fired once per tick that damaged someone, more than once per strike when two targets were hit on different ticks. A real fight has the same shape: a strike that hits two enemies is one landed strike.
**Now** the call is driven by the hit, once per strike: `sat_wv_bz_hit` arms it on the first hit of a strike (`bz_fired` = the strike record last armed, a hit of the same strike on another target arms nothing). The game applies the damage a tick later, so the call is made on the second look of the pre-hook after the arming, with the pool's loss summed over those looks (`wv_pool_loss`, unchanged). A hit of the next strike before that (the last tick of one strike, the first of the next) makes the waiting call first; the state ending first makes it before `wv_on_berserker_end`. Whiff: no call. A hit on something that is not in the pool (a crate) is a landed strike: a call with damage 0.
Yaba (`-DWV_BZ_EVENT_TEST` build, `evidence3/ct4 ct5 ct6 wh7`):
| Leg | Strikes with a hit | Counters (start, connect calls, damage, end) |
|---|---|---|
| ct6: one target only (the others 400 px behind him), health not held | 4 (strike ids 44..47, the target dies) | 1, **4**, 87 (24, 24, 24, 15 on the strike that hit it), 1; health 91 -> 85 once |
| ct5: one target, health held up | 6 (70..75; 76..81 refused, cap 6) | 1, **6**, 24 (the harness rewrites the target's health to 400 every frame, so most of the 24-point losses are gone before the look), 1; health 101 -> 95 once |
| ct4: pinned enemies rotate (several targets) | 9 (105..113) | 1, **9**, 312, 0 at frame 100 (the flurry was still running): one call per strike, 48 per strike while two targets were hit |
| wh7: every enemy 400 px behind him | 0 | 1, **0**, 0, 1; health 101 constant |
Cost: cart_free 4,832 -> **4,620** (524 bytes before the next 4 KB step; the features lane's 458 leave 66), low RAM free 68 -> 52. hw_free 1,080. Gates on this commit: build rc 0, fit.py D11 76/76, gate True, stage24_ma 2,872 / 2,834, room 1,630,208, HOST golden_c1 clean 272,171 and golden_2p clean 329,918 (0 differing, missed IRQ 0), WSL unittest 106 run / 30 errors / 1 skipped, flag-off identity (built from this commit): the five BINs byte-identical to the integration archive build, `sat.elf` same size and sorted `nm` table, `sat.iso` same size 391,499,776

## 15. Owner decisions of 11-10 (head after 7f26a1f): chain B default, Berserker on attack + jump, no kick, hurt boxes, shadow, co-op gun

### 15.1 Chain B is the default; the Berserker is his special (attack + jump)
- `gen_native.py`: `WV_HP_TICKS` defaults to 12 (variant B, LP LP HP with the 12-tick heavy punch). A (`WV_HP_TICKS=0`, the donor's 18-tick heavy punch) and C (`WV_CHAIN=4`, kick as 4th stage) stay as switches for comparison builds only.
- The special input is the game's own: attack + jump pressed together (any two of gun, attack, jump) enters state 020008 through `f_1a7e6`, which refuses at health 0, while busy and in the special already. `game_bind.c` wraps `f_24f04` (Schaefer's special routine, table 0x891e entry of character 1) instead of `f_2576a` (old gun state 02000c): for a Wolverine player `sat_wv_bz_run` runs the native Berserker (12 strikes, cost 6 on the first connect, cap 6 a target, the same hooks and recovery), for anyone else the stock routine. `build.py` `GUEST_WRAP` and `build_native_host.py` name `24f04`. The QCF + attack entry, `bz_req`, `wv_bz_enter`, the DP injection and the whole motion machinery are gone from the native build (`wolverine.c`: native `sat_guest_wolverine_pad` = `wv_nat_sync` + the gun mask only; the skin build keeps its code). Hooks: `wv_berserker_events` watches state 020008.
- Stock rule at low health (code, `f_1a7e6` and `f_1b492`, and Yaba `lh*` runs with the health word set before the press, harness assist): the press is refused at health 0 only (Yaba lh0: the jump comes out instead); with any health 1 and up the special starts and runs all 12 strikes; the cost is charged on connect, never on a whiff; health that would be left under 6 goes to 0 (health 1 -> 0 on the 6th hit in lh1, the flurry still finishes; health 8 -> 0 on the first connect in lhb8). Nothing was changed from the stock rule.
- Yaba, final build (`-DWV_BZ_EVENT_TEST` counters; SH-2 cache emulation ON for these runs, so speeds before and after the owner's 11-10 UseSh2Cache=false rule are not comparable; no speed number is quoted): whiff (`wh9`, every enemy moved 400 px behind): state 020008, health 101 constant, hit flag never set, start 1, connect calls 0, end 1. Contact (`ct8`, one target in front, health held): health 101 -> 95 once, 6 strikes connect (cap 6), connect calls 6, damage 24 (the harness rewrites the target's health), start 1, end 1. `wh8` (an earlier whiff run) had a contact on the first strike before the harness assist moved the enemies (cost charged once, no damage), a harness race, not a change in the rule.

### 15.2 Hurt boxes follow the donor, kick states give way to claw slashes
- **Cause found by the pose-sheet question** (records 3003d0/3003e0, a blue box floating above lying poses): `gen_native.py` replaced every record's hurt box by the MSHvSF pose's own box. The engine lets a hit land only when the target's record names a hurt box (`f_1cf54` and its siblings refuse at once when the target's record byte +8 is 0) and Schaefer's records name none in the hit reactions, knockdown flight and ground, getup, landing, crouch and his special (donor index 0 in 224 of the 227 slots' records listed in `boxcheck_pre.txt`). The native build therefore made him hittable in all of those states (and the box of a tucked jump pose stood 45 px above the pose). Now: a record whose donor names no hurt box keeps none (as the stock character and the skin build); a named MSHvSF box is used only where it covers at least half of the pose's height, otherwise the idle's standing box (leap launch and landing, T1.3 / T1.10 / T0 aliases). Block 21,716 -> 21,708 bytes. The leap arc (T1.37) keeps the donor's ground box (stock leaps are ground-level; the owner's 88 px lift of the sprite is visual only); lifting the box with the sprite is a one-line change if wanted.
- The Berserker records keep his flurry hurt box (hittable during the 48 ticks; Schaefer's own special names none, so it is unhittable in stock). Switch `WV_BZ_HURT=0` builds the stock (unhittable) form for a comparison. Owner decision.
- **Kick states** (`ROLE_T1`, owner 11-10 "why does wolverine still kick"): T1.41 (state 02000a, the lunging attack of Schaefer's slot0a routine `f_2501e`, donor attack boxes 12 and 21 on records 2 and 3; MSHvSF's flying kick), T1.16 (state 02000e, entered by the action-request path `f_1ab1a`, donor attack box 8 on record 2) and T1.14 (a 2-record hold of the stand handler `f_198b0`, no attack box) took his HK poses. Now T1.41 and T1.16 show the heavy-punch claw slashes (resident set) with the heavy punch's attack box band, T1.14 the first light slash; every duration, flag and donor box index is the stock one. No other state draws a kick pose (roles after: HK none; `WV_KICK=1` brings the kick poses back, as chain C does for stage 3). Cost: no new tiles; 52 assemblies instead of 54, block 21,708 -> 21,164 bytes. The triggers of 02000a and 02000e could not be produced in Yaba this session (walk + attack gives the normal chain, jump + attack stays in 020004; a poked state does not run the routine's own entry), so those two are checked on the offline pose sheet (`evidence: poses/kick_after.png`), not in play.

### 15.3 Shadow under his feet
Yaba paused A/B from one saved state, stock Schaefer against Wolverine (`shad1`, flag build, SH-2 cache on): the shadow ellipse is the game's own object and sits on the same rows in both (rows 436-465, same draw order: the feet are in front of it), so (a) order and (c) size are not the cause. (b) position: his soles sit about 2 screen px (stand) to 7 px (walk) lower than Schaefer's against that ellipse (about 1 to 2.5 Saturn rows); his boots end in dark outline and dark red, which reads as covered by the black ellipse. `FEET` (the feet line below the origin's row) moves from 13 to 14 (`WV_FEET`), raising every native pose and the box rectangles by one row. A pixel comparison after the change is not possible with the captures taken (`shad2` landed in a different scene), so the one-row raise is judged from `shad1`, not measured after.

### 15.4 Co-op: the partner's gun was stripped (cause found, fixed in the native build)
Owner: "we should confirm the gun still works". Yaba co-op, Wolverine selected, Warrior partner holding its gun button: `sat_pad_raw2` showed the C press and the game's pad word `in0` did not (0xffff against 0xefff with Wolverine not selected, where the Warrior's gun state 02000c and a shot object appear). Cause: `is_wolverine()` tests block byte +1 (`WV_CHAR_OFF 1`, calibrated in single player). In co-op byte +1 is 1 for both players (run `gunA7`: ids +1 = 1, 1; character index +0xd2 = 0, 1), so every player counted as Wolverine and the pad hook cleared the gun bit of the partner (and the partner was treated as Wolverine by the tick, wall and cap hooks). Fix: in the native build only, `WV_CHAR_OFF` is 0xd2, the game's own character index (0 Warrior, 1 Schaefer, 2 Hunter, 3 Linn). The skin build (flag off, avp/integration) keeps the old test and therefore has the same defect: it is a finding for the integration line, not changed here to keep the flag-off identity.

**Co-op gun proof after the fix** (`tools/wolverine/native_gun_proof.py`, own pad_set Yaba copy, VideoCore 2, port 9718, `UseSh2Cache=false`; build with the fix; evidence `evidence4/ev/gm_*`, `gun_long_*`, table `evidence4/gun_analysis_table.txt`). The partner holds nothing: it presses its gun (C) 32 times, 12 vblanks each, 150 vblanks apart (60 apart overheated the gun: state 02001a, the OVER HEAT gauge, same with Wolverine off), at the nearest enemy pinned 130 px in front (health set once, so damage shows); the pool is logged every poll (a poll is 5 to 13 vblanks; a per-frame log is not possible on this copy, so a shot count is a lower bound). Each run is labelled from the game's own character indexes (+0xd2), the run is refused when they are not the wanted pair (earlier selects were mislabelled by the select sequence).
| Run (labels from +0xd2) | Presses | Gun actions seen (state 02000c polls) | Shot objects (tag 4, class 0, spawn edges) | Owner of the shots | Pool slots owned by Wolverine | Travel | Enemy health drops |
|---|---|---|---|---|---|---|---|
| Wolverine P1 + Warrior P2, P2 fires | 32 | 32 | 8 | P2 block 0x8480 only | 0 | up to 76 px | 53 events, to 56 |
| Wolverine P2 + Hunter P1, P1 fires (rerun; the first run's vblank counter froze for 8,393 polls from outside and resumed, no fatal) | 32 | 50 | 9 | P1 block 0x8380 only | 0 | up to 95 px | 64 events, to 56 |
| baseline stock Schaefer P1 + Warrior P2 (Wolverine off), P2 fires | 32 | 35 | 9 | 0x8480 only | 0 | up to 78 px | 62 events, to 56 |
| baseline stock Schaefer P2 + Hunter P1 (Wolverine off), P1 fires | 32 | 42 | 10 | 0x8380 only | 0 | up to 72 px | 62 events, to 25 |
| 2P stage run, Wolverine P1 + Warrior P2, 50 gun presses, Wolverine taps attack and plays his special, 7,893 vblanks (2 min 11 s of game time), no FATAL | 50 | 53 | 13 | 0x8480 only | 0 | up to 99 px | 102 events, to 0 (enemy killed) |
The muzzle flash is the second pool object class: tag 4 with class 0x402 (and 0x401/0x400, the impact sparks) appears with every gun action (36 to 52 objects a run), and the same kinds appear in the baseline. Counts match in kind between Wolverine and baseline. Before the fix the same press produced no gun action at all (`gunA2..A7`: `in0` 0xffff with the C press on `sat_pad_raw2`).
Not delivered: a paused picture of a partner shot hitting. The pad_set copy only runs with VideoCore 2, whose screenshots omit the VDP1 sprites (players, enemies and shots are absent from every picture of those runs; the HUD and backgrounds are there), so the proof is the pool log, not a picture. `evidence4/ev/gun_hit_sheet_hunter_p1_wolverine_p2.png` shows the HUD and talk box only.

### 15.5 Final numbers (build recipe + `-DSAT_WV_NATIVE_GFX`, D11, copy of integration/w1)
Build rc 0; hw_free 1,080, lw_free 84 (was 52), cart_free 5,872 (was 4,620; 1,776 bytes before the next 4 KB step, the features lane's 458 fit), block 21,164 bytes (was 21,616), ISO 391,497,728. fit.py D11 (copy) 76/76, gate True, stage24_ma 2,872 / 2,834, room 1,630,208. Flag-off identity against avp/integration on the final source: HW, LW, COLD1, OPX, ROM sha256 equal, sorted nm table equal (fc883e35...), ISO size 391,499,776. HOST golden_c1 clean 272,171 and golden_2p clean 329,918 (guest off, flag on, 0 differing, missed IRQ 0). WSL unittest 106 run, 30 errors, 1 skipped (re-run after the WSL restart). Capture pair `evidence4/ev/capture_pair_stage02.png` (left integration, right this build, stage 02, same vblank offset): background intact in both.


## 16. Lane reorganisation (11-10): all of Wolverine's gameplay code, heal and flash taken over, Berserker unhittable

### 16.1 "Every player counts as Wolverine": confirmed on the integration build, fixed in every build
- Integration build (flag off, `sat_guest_sel` 1, one player): P1 Hunter (+0xd2 = 2): block byte +1 = 1, `wvid_[0]` = 1; P1 Warrior (+0xd2 = 0): +1 = 1, `wvid_[0]` = 1 (`evidence4/ev/d2_integ_hunter`, `d2_integ_warrior`, `cap.json`). So `is_wolverine()` (test `R8(PL(i) + 1) == 1`) is true for every live player, one player or two, whenever the guest is enabled: the whole-list draw pass draws the stock character with Wolverine's parts, the pad hook strips its gun bit and his hooks act on it. The owner's pictures (P.Hunter with Wolverine parts on stage 0e, a stray figure in a P.Warrior ending run) are what this predicts. I did not re-take those two pictures.
- Fix: `WV_CHAR_OFF` = 0xd2 (the game's character index; `guests.c` guest_draw already used it) in every build, native and skin. Fixed build (owner heal/flash build, guest selected, `evidence4/ev/d2_fixed_hunter`, `d2_fixed_warrior`): the same lone Hunter and lone Warrior read `wvid_` = 0 (byte +1 is still 1), and the co-op runs (gun proof, heal) show the partner untouched. Other paths audited: `wv_player()`, the pad mask, the tick pre-hook, `wv_berserker_events`, the collision wrapper (`sat_wv_bz` bits only for him), pickup, draw pass and the features code (`WVF_IS_WV`) all go through `is_wolverine()` or the +0xd2 test; the HUD/select names are slot data (the Schaefer slot reads WOLVERINE), not per player.
- Consequence for flag-off identity: HW, LW, OPX, ROM and the sorted symbol table are byte-equal to avp/integration, `sat.elf` size equal; COLD1.BIN differs (the character test lives in cold code). Expected and intended.
- Tests that set the character at +1 (`tests/wolverine_clock_test.c`, `wolverine_list_identity_test.c`) now set `WV_CHAR_OFF`.

### 16.2 Heal and flash (features lane, handed over at 87f7325)
Branch `lane/wv-features-20261109` merged into this branch (its own commits plus its earlier merges of this branch; content: `wv_features.c`, the `build.py` wiring that renames the tick and pad hooks, `build_native_host.py --wvf 1`, `wvf_*.py`, its notes `AVP_WOLVERINE_FEATURES_20261109.md`). `build_native_host.py` reconciled: the native host wraps 24f04 and not 24060 (the native `game_bind.c` has no f_24060 wrapper). Owner settings built: `-DSAT_WV_HEAL -DSAT_WV_HEAL_DELAY=180 -DSAT_WV_HEAL_STEP=30 -DSAT_WV_HEAL_AMT=1 -DSAT_WV_FLASH=1 -DSAT_WV_FLASH_FREEZE=12` (flash at the move's start = the attack + jump entry).
- Memory (BUILD, owner recipe + `-DSAT_WV_NATIVE_GFX` + those switches): rc 0, hw_free 1,080, lw_free 84, cart_free 5,412 (without the switches 5,872: the features cost 460 bytes; 1,316 bytes before the next 4 KB step), cold1_at 0x27e2000 unchanged, ISO 391,497,728. State stays in the cart (`CARTVAR`), nothing in bss.
- Co-op heal (Yaba, `evidence4/ev/heal_*`): both players' health set to 50, enemies kept away. Wolverine P1 + Warrior P2: Wolverine +1 after the 180-tick delay (first rise 207 ticks after the poke) and then about every 30 ticks, 50 -> 81 in 1,100 vblanks; the Warrior stays 50 the whole time. Hunter P1 + Wolverine P2: Wolverine rises the same way, the Hunter stays 50.
- Flash at the attack + jump entry (paused legs, one frame at a time, `evidence4/ev/fl_bz1`): the enemy pool's hitstop byte +0x2c is 12 on every live enemy slot on the first frame of state 020008 and counts down 12 -> 0 over 12 frames; the boss pool (ff9280) and the partner's byte are never set by it (free-running `flash_wv_p1_warrior_p2`: boss pool 0 throughout, partner 0 at every special start). Screen brightness per picture (mean of the frame, normal 90.1): 67.7 and 70.3 (two dim frames, 75 to 78 percent), 152.4 twice (the bright pop), then 91.3 normal. The VDP2 colour offset registers cannot be read through the debugger (read as 0), so brightness is the evidence.
- Not done by this lane: sounds (`WV_SFX_BERSERKER` unset, for the sounds lane).

### 16.3 Berserker unhittable (WV_BZ_HURT=0 default)
The Berserker records carry no hurt box (as donor T1.42, Schaefer's special): the engine refuses any hit on a record whose hurt index is 0. `WV_BZ_HURT=1` builds the hittable form for comparison. Yaba (`hurt_bz1`, `hurt_bz2`): the record byte +8 reads 0 on every frame of state 020008 (two flurries, 118 frames) and 12 as soon as he is back to stand; health only moves by the 6-point cost (101 -> 95). No enemy attack landed on him in those windows, so the check is the engine's own rule plus the absence of hits, not an observed refused hit; hits on him at stand (hurt index 12) are in `jmp1` (health 101 -> 91 -> 81 with hit-reaction states) from the same stand records.

### 16.4 Cache-ON look (owner rule: play/look/gameplay checks cache off, one cache-on smoke pass)
One free-running pass with `UseSh2Cache=true` (the lane's VideoCore 1 Yaba copy; the pad_set copy only runs VideoCore 2, whose pictures omit VDP1 sprites): stage 02, Wolverine P1, unassisted walking and fighting policy, attack chain and Berserker (attack + jump) repeatedly, 100 s, 3,342 vblanks, 850 polls: states 020002, 020008 (149 polls), 020004, 020202, 020006, 02000e (21 polls), 020000; no anomaly (no record outside his native window, no state held over 300 vblanks), no fatal. Pictures `evidence4/ev/look_cache_on/cache_on_look_sheet.png`: sprites, Berserker poses, enemies and background intact. No speed number is quoted from any cache-off run.

### 16.5 Gates on this head (build with the owner heal and flash switches)
Build rc 0; fit.py D11 (copy) 76/76, gate True, stage24_ma 2,872 / 2,834; HOST golden_c1 clean 272,171 and golden_2p clean 329,918 (guest off, flag on, features compiled via `--wvf 1`, 0 differing, missed IRQ 0); WSL unittest 106 run, 30 errors (the known set, same names), 1 skipped after the test fix above; flag-off identity as in 16.1.

## 17. Knockdown and jump poses, Schaefer tables for Dutch, grab poses (11-10)

### 17.1 No jump pose without a jump
- T1.3 / T1.10 (and T0.3 / T0.10) are 2-record knee-bend holds that the game also uses for the state-020004 turn holds and the stage entrance. They showed his tucked jump poses. They now use his LAND poses. The leap arc (T1.37) and the jump attack (T1.38) keep their JUMP poses.
- Knockdown flight (T2.14 / 16 / 20) used the JUMP role. It now uses HIT_H. Switches in `gen_native.py`: `WV_KD_JUMP=1` and `WV_LEAP_TUCK=1` restore the old forms for comparison.
- Yaba, free-running, NOJUMP soak on the final build: 0 anomalies, no JUMP role in any state (`recmap.py` of `soak.jsonl`); knockdown flight reads HIT_H (T2.14 / 16 / 20), the leap holds and getup read LAND.

### 17.2 Schaefer's tables stand while no Wolverine player exists
- The per-slot index tables (`sat_wv_tb`) are global to a character slot, so Dutch Schaefer in the opening street scene drew from the native block. `wv_live()` is true only while a live player block has +0xd2 == 1; `wv_nat_sync()` flips to the native tables only then and restores Schaefer's otherwise.
- Yaba, opening and attract (build g6, `attract_shots.py`, 36 samples to vblank 5,295, Start pressed by window message): `sat_wv_tb` = 0x162f90 in every sample; the opening street scene shows Dutch with Linn drawn normally.
- Limit: a Dutch NPC that coexists with a live Wolverine player is not handled (the stage-26 ending could not be reached; a warp to stage 26 crashes on the unmodified integration build as well).

### 17.3 Grab: stock grab stays on, better poses
- Owner decision: keep the stock grab (walking into a standing enemy) and give it better poses. `WV_NO_GRAB=1` is the default-off switch that suppresses it for Wolverine (an `f_1a586` wrapper returning 0, wired in `game_bind.c`, `build.py` and `build_native_host.py`).
- Chain 020400 -> 020406 (lift, T1.55) -> 020408 (slam, T1.56): the hold uses his claw-forward poses (MSHvSF 8.3), the slam his slash (8.2); donor timing and the donor attack box are kept; the hurt box is his standing box.
- Yaba, free-running into an enemy (`soak_020406_*`, `soak_020408_*` strip): 020406 x3 and 020408 x17 reached, every record in the native window, 0 anomalies.

### 17.4 Tools (code only; their outputs are local, not in git)
`attract_shots.py` (attract and opening shots with the table base), `recmap.py` (record to role), `motion_compare.py`, `mshvsf_catalog.py`, `baseline_table.py`, `baseline_swap.py` (CURRENT vs PROPOSED mapping sheet for the remap, review only), `tile_cost.py`. `play_yaba.py` now starts Yaba with SW_SHOWNOACTIVATE, at the bottom of the z-order and BelowNormal; it takes no focus and sends no global input.

### 17.5 Remap review
The review sheet (`baseline_swap.png/.md/.csv`, local) proposed a full swap of 866 new tiles (+877 against the keys his native records used, +567 against the 1,474-key pack). An independent MAME-driven review (`REVIEW_ANSWER.md`, local) corrected three identities and cut the set to the essentials; section 18 is what was built.

### 17.6 Gates on this head
Build rc 0 (full rebuild b_w5, then cached b_w6): hw_free 1,080, lw_free 84, block 20,912 bytes (was 21,164) ending at 0x27fe784, ISO 391,497,728. fit.py D11 (copy) 76/76, gate True, no own key dropped, stage24_ma 2,872 / 2,834 (margin 38), cart pack room 1,630,208; HOST (guest off, flag on, features via `--wvf 1`) golden_c1 clean 272,171 and golden_2p clean 329,918, 0 differing, missed IRQ 0; WSL unittest 106 run, 30 errors (the known set, identical names), 1 skipped. Flag-off identity was not re-run on this head: every change since 16.1 sits behind `SAT_WV_NATIVE_GFX` or `WV_NO_GRAB` (the `GUEST_WRAP` additions and the `f_1a586` wrapper are gated on the same flags); a re-run belongs to the release candidate. Yaba (cache off, own copy): opening scene, Wolverine stage-02 free-running soak with no JUMP role and 0 anomalies, grab strip.

## 18. Essentials remap (11-10): one consistent mapping from the arcade Wolverine

Switch: `WV_REMAP` (default 1) in `gen_native.py`; `WV_REMAP=0` builds the section 17 mapping (comparison only). Needs the D12 asset set (below). All ROM-derived output is local, never in git.

### 18.1 Identities (MAME, headless, the owner's `mshvsf` set: player 1's animation record logged per frame)
| Input | Entry |
|---|---|
| standing medium punch, then medium punch again (MP, MP: the double claw) | 8.1, then 8.4 |
| jumping light / medium / heavy punch | 12.0 / 12.1 / 12.2 |
| QCF + punch, then taps (Berserker Barrage) | 22.22, then 22.24 / 22.23, then 22.25 |
| forward + medium punch / heavy punch, close (the two throws) | 16.0 / 16.2 |
| swept | 14.9, 14.31 (lying), 18.0 (get-up) |
| F, D, DF + two punches (Weapon X) | 23.0, 23.1 (56 frames), 23.2, lands with 23.3 |
Corrections to the 11-10 sheet: the double claw's input is medium PUNCH twice (not kicks); 23.1 is the Weapon X hyper, not the Barrage; 18.0 is the get-up from a knockdown, not an air attack; 22.10 (today's Berserker before this) is the Drill Claw family.

### 18.2 What each Schaefer state shows now
| State / slots | Arcade source | New tiles |
|---|---|---|
| attack stages 1 and 2 (T1.32, T1.33 alias), lunge 02000a (T1.41) | 8.1 records 2, 5, 6 (the thrust, its hold, the resident hold); stage 2 reuses them (8.4 is the upgrade) | 8.1 |
| attack stage 3, finisher 02000e (T1.16) | 8.2 (unchanged) | 0 |
| jump attack (T1.38) | 12.2 records 1, 2, effect sprites apart from the body dropped (`MASS_RECS`: the slash spark below the body raised the whole pose) | 12.2 |
| Berserker 020008 (own chain, 12 records of 4 ticks) | 22.22 r1, then 22.24 r1 / 22.23 r1 alternating (ten), then 22.25 r0; every record keeps the strike box; hurt 0 as before | 22.2x |
| auto-grab hold 0204xx (T1.48..54) | 16.2 records 3 (the hold) and 5 (the stab) | 16.2 |
| auto-grab leap 020406 (T1.55) and stomp 020408 (T1.56) | 16.0 record 1 (hop up), record 5 (stab down); Schaefer's code, timing and attack box 24 unchanged | 16.0 |
| after the stomp (T1.57) | 1.3 (resident) | 0 |
| ground, lying (T2 two-record ground chains) | 14.31 (one lying frame; the ground state was a crouch) | 14.31 |
| getup (T2.23, T2.24) | 22.5 (resident) | 0 |
| entrance close (T0.24) | 23.3, the landing after Weapon X (resident) | 0 |
| state 020014 (T1.64..79, 13 chains) | 8.1 thrust (their donor attack boxes kept as the other roles keep theirs) | 0 |
| KO tumble, hit flinch, knockdown flight | unchanged (14.x resident) | 0 |

State 020014 is not a weapon pickup: the attack branch at 0x1a6dc enters 020006 and then 020014 when the player block's word at +0x5a is non-zero. That word is the link to an enemy that has seized him (the enemy-side grab routines such as 0x538f4 write each block's +0x5a with the other's pointer; the 0x53ffe style sites clear it). So it is the break-free attack. Read from the lifted source; not reproduced in Yaba (no enemy grab of the player was triggered in any run).

### 18.3 Tiles: the D12 asset set (`make_d12.py`)
- `gen_native.py` with `WV_ADD` adds the tiles of the frames the remap names (SRC entries with record indexes) that have no resident tile within the merge distance K = 12, deduplicated among themselves, at free AvP sprite keys (`gfx_wolverine.bin`, `remap.json` keys and `stage_keys` of every stage). Modelled 334 tiles, built **328**.
- `WV_KEYS_OUT` lists the keys his native records draw: **1,441** (1,164 before). `stage_keys` of every stage becomes those plus filler (33 of D11's skin-only keys) up to D11's count of **1,474**, so no stage file's resident tile count grows; the 328 other skin-only keys leave the pack. `gen_c.py` takes `WV_SKIP_KEYCHECK=1` for these sets (the skin tables are not drawn in native builds). The native block is byte-identical before and after the pruning (`make_d12.py` checks).
- fit.py on a copy of D12: **76 of 76, gate True**, no own key dropped, no missing guest key; **Wolverine tiles per stage file: change 0 at most, -31 at stage 0e (14,874 -> 14,843)**; stage 0e margins (Schaefer drops minus Wolverine drops) 396, 270, 379, 334 (392, 273, 345, 329 before); tightest file stage24, margin 40 / 44 / 44 (38 to 49 before).
- Cost: the block grew from 20,912 to 23,316 bytes (9 more assemblies), then 23,116 with 020014 on 8.1 records. cold1_at moved 0x27e2000 -> 0x27e1000 (one 4 KB step), cart pack room 1,630,208 -> 1,626,112 (32 tiles at every file, charged to Schaefer's variants too, so the margins above already include it).

### 18.4 Yaba (cache off, own copy, window messages only; builds b_r2 then b_r3 = 020014)
Free-running soaks, 0 anomalies each (play, into-enemy, knockdown): the states reach the new roles (`recmap.py`): LP1 (double claw), BERS3 (Berserker chain), GRAB_HOLD, GRAB_LIFT, GRAB_SLAM, GETUP, LYING (T2.21, T2.22), ENTR (T0.24). Pictures (local): `remap/play_berserker.png`, `play_attack.png`, `into_grab.png` (hop up with the claws raised, stab down), `play_lying.png` (knockdown flight and the lying frame), `play_down_getup.png`. Not captured in play: the jump attack T1.38 (the soak policy does not press attack in the air) and 020014 (no seizing enemy). Before and after pose sheets with the arcade frames beside ours: `remap/remap_sheet.png` (`remap_sheets.py`).

### 18.5 Tools
`remap_probe.py` (per-record tile cost and pictures of any arcade entries), `make_d12.py`, `remap_sheets.py`.

### 18.6 Gates on the final head (build b_r3, D12, owner heal and flash switches)
- Build rc 0 (b_r2 full, 1,974 s; b_r3 cached with 020014 on 8.1, 24 s): hw_free 1,080, lw_free 84, block 23,116 bytes, cold1_at 0x27e1000.
- fit.py on a D12 copy (b_r2 and again on b_r3): 76/76, gate True, none of his own keys dropped, no missing guest key; Wolverine tiles per stage file +0 at most, -31 at stage 0e; stage 0e margins 396 / 270 / 379 / 334; tightest stage24 40 / 44 / 44; cart pack room 1,626,112.
- HOST (guest off, flag on, `--wvf 1`): golden_c1 clean 272,171, golden_2p clean 329,918, 0 differing, missed IRQ 0. WSL unittest: 106 run, 30 errors (the known set, same names), 1 skipped.
- Flag-off identity: the run (`identity.sh`, two builds) compared this tree against `git archive avp/integration`. By the time it ran, `avp/integration` (5e49c52) already contained this branch's remap (c6a7294) and 98 other commits (disc 3h, the perf lane), so the two sides differ in HW, LW, COLD1, ROM and size (489 MB against 391 MB) for reasons unrelated to the switches: the result is not a valid identity check and is not used. The owner-approved speed-up moves the identity to the integration lane's combined A/B build; nothing here waits on it. The change set since the last valid identity (section 16.1) is behind `SAT_WV_NATIVE_GFX` and `WV_NO_GRAB`, or runs only with `GUEST_ASSETS`.
- Rebuilding the asset set: `make_d12.py WORK D11 MSHVSF_DUMP D12_OUT`, then build with `GUEST_ASSETS=D12_OUT` and `WV_SKIP_KEYCHECK=1` (the native block needs the D12 tiles; with D11 `gen_native.py` stops with a NO-GO naming the role whose frames are not resident, or build with `WV_REMAP=0`).
