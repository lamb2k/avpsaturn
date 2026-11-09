# Wolverine native fighter: design plan, 2026-11-09

Lane `lane/wolverine-native-20261109`, off `lane/wolverine-anim-20261109` (9728e4e). DESIGN ONLY: no gameplay code changed. Tiers used below:
**MEASURED** = MAME 0.289 `avspu` (the arcade ROM, Schaefer/Linn/Warrior/Hunter driven by one scripted pad run, `tools/wolverine/char_measure.lua`),
**READ** = lifted-source or build-object reading (sizes from the lane's last build objects), **MODELLED** = estimate or proposal. Nothing is hardware or Yaba here.
No ROM data is in the repository: the notes carry addresses, counts and derived numbers only; raw logs stay in `E:\AvP\learning\lane-wolverine-native` (c0..c3, n1, n2, rd1).

## 0. Summary of the plan

1. **Fork depth.** The player is not one Schaefer routine. It is a character-neutral state machine (`f_195ec`, 35.7 KB of SH-2 over 55 routines in 0x194da..0x1b620) that reaches
   Schaefer-specific code only through ten character-indexed pointer tables (indexed by player byte +0xd2, 1 = Schaefer) plus about 35 inline `+0xd2` compares/table reads.
   Schaefer's private code is **9 distinct routines, 18.5 KB** (section 1). Forking all 55 + 9 routines (54 KB) would cost about 420 tiles of sprite room and break stage 24.
   Recommended fork ("D1"): copy **only the two routines whose behaviour must differ** (attack `f_24454`, 956 B; special `f_24f04`, 982 B = 1.9 KB), turn the other seven char-private routines into stubs
   (gun, weapon-hold, 0x0a, 0x14) or leave them shared (jump, pre-tick), and move every number (damage, pushback, hitstop, reach, frame durations, walk weight) into a **patch table over Schaefer's own data in the cart-RAM ROM image**,
   applied when the guest is selected and undone when it is not. Stage 0 forks everything once (test build only) to prove the fork mechanism is byte-identical to Schaefer before anything changes.
2. **Where it runs.** Cart tail (cold1) with the rest of the guest code, like the skin: net code about the same as the skin today (5.5 KB vs 5.8 KB), data 16 KB vs 19.5 KB (MODELLED). Low RAM stays untouched (76 B free).
3. **Moves.** Same set as today minus two optional pieces in the recommended minimal set: Berserker Barrage (49 exclusive tiles) and the heavy hit reaction (99 exclusive tiles). Full set stays buildable. Combos use the existing buttons only:
   attack taps give LP, LP, HP, then the kick (AvP's own chain order is 3 punches then the 02000e finisher), attack+jump = Tornado Claw at a 6-health cost, as for every AvP character.
4. **Feel.** "Walks slow but slashes fast": walk exactly at Schaefer's weight (2.08 px/tick, reverting the skin's x1.375 = 2.86), attack rhythm at Linn's (12-tick taps instead of 15; chain 62 ticks vs Schaefer 77).
5. **Proof.** A field-by-field diff of the 61 interface fields (+ outbound region list) against Schaefer, same scripted pad run: exact in Stage 0, allowlisted deltas afterwards (section 3).
6. **Effort** about 11 to 14 working days for one lane; riskiest parts are the lifted-code fork generator and pose timing (section 8).

## 1. Which Schaefer routines a native Wolverine replaces and which stay (with addresses)

Addresses are the arcade 68k addresses the lifted code keeps (`f_XXXXX`); SH-2 sizes are `nm -S` sizes of `lifted_XXXXX` / `f_XXXXX` in the lane's last build (`E:\AvP\learning\lane-wolverine-anim\w1\obj-Os\c*.o`, -Os). READ tier.

### 1.1 How the player is built (READ, lifted source `learning/lift/run/c3/lifted_mem.c`, MAME confirms)

- `f_195ec` (5,952 B) is the whole player update, called once per tick with a6 = block (ff8380 + 0x100 * player). It switches on state byte +4 (0x195f6, five targets for +4 = 0 init, 2 normal, 4 `L1b132` (dying), 6 `L1b546`, 8 `L1b5d2` (entering); 0 and 2 and 8 are
  observed, the rest inferred), then on +5 (0x197c8, eight targets: 0 actions `L197f2`, 2 hit `L1a96e`, 4 grabbed `L1b450`, 6 `L1b53c`, 8 `L207cc` (getting up per the anim lane), 0xa `L1a7fa`, 0xc `L1989e`, 0xe `L17d14`; 0, 2, 4 observed),
  then on **+6, the action**, through a word table at 0x1986e (0x19850: actions 0x00 stand `f_198b0`, 0x02 walk `f_1997e`, 0x04 jump stub `f_19ae6`,
  0x06 attack stub `f_19b02`, 0x08 special stub `f_19b1e`, 0x0a `f_19b3c`, 0x0c gun stub `f_19b5a`, 0x0e finisher `f_19b78`, 0x10 `f_19b9c`, 0x12 `f_19c8a`, 0x14 `f_19d6a`, 0x16 `f_19d88`, 0x18 `f_19db0`, 0x1a `f_19f34`).
- The five 92 to 100 byte stubs (`f_19ae6`, `f_19b02`, `f_19b1e`, `f_19b3c`, `f_19b5a`, and `f_19d6a`) read **+0xd2** and `DISPATCH` through a 4-entry long-pointer table in the ROM image. Order: Warrior, Schaefer, Hunter, Linn.
- Animation is data driven: `f_1656e` (shared) decrements the frame timer +0x0a, loads the next 16-byte frame record into +0x1c/+0x1e (pointer), +0x24 (script) and the hit/hurt box indices (record bytes 8 and 9). A record is
  `duration(2) flags(2) sprite-assembly pointer(4) hurt-box idx, attack-box idx, 2 bytes, pad`. The attack/hurt box *tables* hang off the character block `T` (+0x50): hurt = `T + word T[0] + idx*8`, attack = `T + word T[2] + idx*16` (this is what `wolverine.c` boxes already use).
  **Consequence:** an attack's startup/active/recovery is the record durations, so changing the durations of the records changes the move's rhythm with no code.

### 1.2 Character-indexed dispatch (READ, tables dumped from the ROM image with `tools/wolverine/rom_dump.lua`)

| Slot | Table | Warrior | Schaefer | Hunter | Linn | Schaefer routine, SH-2 bytes (incl. private callees) |
| --- | --- | --- | --- | --- | --- | --- |
| jump (04) | 0x19af2 | 233c4 | **2539e** | 2693a | 27af8 | 2,812 (2539e + 252e6) |
| attack (06) | 0x19b0e | 22554 | **24454** | 25b14 | 271d0 | 956 |
| special (08) | 0x19b2c | 23132 | **24f04** | 266e6 | 276a0 | 982 |
| 0a | 0x19b4a | 23cd0 | **2501e** | 26de0 | 277c0 | 2,186 (never entered in any scripted run) |
| gun (0c) | 0x19b68 | 24060 | **2576a** | 24060 | 28452 | 2,228 (12-shot burst) |
| pre-tick | 0x197e2 | 23950 | **255fa** | 23958 | 28170 | 1,084 |
| action 14 | 0x19d78 | 22e00 | **24c64** | 263c2 | 27434 | 1,980 (Schaefer never enters 020014; Warrior, Hunter, Linn do) |
| held-item | 0x1b482 | 2276a | **24582** | 25d2a | 27432 | 6,116 (Linn's is a 4 byte stub) |
| 19c7a / 19f24 | two tables | 2c92 | **2f70** | 2de6 | 31ec | 144 each, same routine |
| character data | 0x1b0e0 / 0x1b104 | 15e240 / 15e36e | **162f90 / 163074** | 168564 / 168692 | 16d122 / 16d23a | T block (22 KB region) |

Schaefer-private total: **18,488 B** over 9 distinct routines (Linn: 18.5 KB, Warrior about 22 KB). The census confirms the attack handler's own footprint is tiny: `f_24454` (68k extent 0x24454..0x2457c, 296 B) writes only
+07, +80..+82, +92, +95, +9d (none are in the 61 interface fields) and reads +06, +07, +24, +6e, +ee. The special `f_24f04` (0x24f04..0x25018) writes +14/+16/+18 (position), +5c, +6e, +70, +9e, +9f, +ad.

### 1.3 Replace / keep, by concern

| Concern | Routine(s), address | Verdict | Reason |
| --- | --- | --- | --- |
| State machine, state/action dispatch | `f_195ec` 5,952 B; wrapper already in `game_bind.c` | **Keep shared** | Character neutral apart from +0xd2 sites; Wolverine keeps +0xd2 = 1, so every inline site behaves as Schaefer (walk weight, hit reactions, getup). A fork would cost 5.9 KB for no difference. |
| Input | pad word read in `f_195ec` pre-part (0x19764..0x197ba reads ff8060/ff8061) and `saturn/rt/pad.c` | **Keep**; drop the skin's motion-input injection (`sat_guest_wolverine_pad`, 460 B) in the minimal set | AvP buttons only (attack, jump, gun C). |
| Stand / walk / depth | `f_198b0` 2,788, `f_198e2` 2,508, `f_1997e` 3,268, shared movement `f_1656e` 15, `f_165a4`, `f_165c4` | **Keep shared** | Walk weight is wanted exactly as Schaefer's. The skin's `wv_speed` (x1.375) is removed. |
| Attack chain (06) and finisher kick (0e) | `f_24454` 956 (Schaefer attack), `f_19b78` 156 + `f_1a3e2` 396 (finisher, shared) | **Fork `f_24454`**; finisher shared, data patched | Chain order is already 3 attacks then the 02000e kick, the same shape as Wolverine's LP, LP, HP, HK. |
| Special / desperation (08) | `f_24f04` 982, drain `f_1b492` (cost 6 per call, measured) | **Fork `f_24f04`** | Needs his Tornado records and timing; cost stays 6 through the shared drain. |
| Jump (04) and air attacks | `f_2539e` 2,060 + `f_252e6` 752 | **Keep shared (Schaefer's)**; data patched | Arc and air-kick are physics + records; patch durations/records only. |
| Gun (0c) | `f_2576a` 2,228 (burst), wrapper `sat_guest_wolverine_bullet` 112 B | **Stub** in minimal set (button does nothing); full set maps C to Berserker through the same stub slot | No gun for him. |
| Held weapons | `f_24582` 6,116, pickups `f_19f9a` 300 (wrapper already refuses weapons) | **Stub** the held-item slot, **keep** the food/score pickup wrapper | He claws, never carries a weapon (section 5). |
| Slots 0a, 14, pre-tick | `f_2501e` 2,186, `f_24c64` 1,980, `f_255fa` 1,084 | **Stub / keep shared** | Never entered in the Schaefer run; saves 3.4 KB if stubbed. |
| Damage taken, hit reaction | `f_1d492`, `f_1d314`, `f_1d504` (damage_apply), `f_1d622`, `f_1d6e2`, `f_1d73a`; player branch at `L1a96e` (+5 = 2) | **Keep shared, never fork** | These are the engine every enemy uses; they read the attacker's record. Wolverine's "own damage taken" is the same engine with his hurt boxes. |
| Grabbed / held | `L1b450` (+5 = 4), enemy `f_1d908` (tag 14) writes player +10,+12,+16,+1a,+5c,+5e | **Keep shared** | AvP players are grabbed, not grabbers (section 5). |
| KO / continue | state 04xx, `L1b132` branch, HUD routines (8164, 91e4, 9750, a000, ac*, ad*) | **Keep shared** | System code reads +40,+42,+44,+d0,+f2..+fc. The invisible-at-KO fault is fixed in `lane/wolverine-gate-20261109`; native inherits that fix (draw path, `sat_guest_objects`). |
| Collision passes | `f_1cf54`, `f_1d03e`, `f_1d116` | **Keep shared**, remove the skin's box poke/undo hook (808 B) once records are patched in the image | The patch layer puts his boxes where the game already looks. |
| Presentation | `sat_guest_objects` 1,092 B, `wv_advance` 776 B, tables | **Keep** (tick-based pose clock slaved to state entry), drop hold/recovery/chain/landed logic (`move_for` 520 B, `wv_tick_move` ~620 B, `after_tick` 512 B, `wv_move_len` 128 B) | The clock no longer has to fight Schaefer's timers; the timers are his own. |

## 2. How the fork is dispatched, and its memory cost

### 2.1 Mechanism (extends what `GUEST_WRAP` in `saturn/rt/build.py:39` and `game_bind.c` already do)

- A **fork generator** (`tools/wolverine/forkgen.py`, new) runs at build time over the generated lifted sources `WORK/src/c*.c`: it extracts the named routines' text, renames `f_24454` to `wvf_24454` (and its labels), keeps all
  calls to shared lifted routines (`f_1656e`, `f_1a3e2`, `f_1b492`, ...) unchanged, and applies a small **patch list keyed by 68k PC** (`P(0x2448cu)`: replace the immediate). Output is a `.c` compiled with the guest objects into the cart tail.
  Nothing ROM-derived is committed: the repository holds the generator and the patch list (PCs and replacement constants), the same split `gen_c.py` already uses.
- The stubs that dispatch by +0xd2 are wrapped like `f_195ec` is today: `f_19b02` (attack) becomes `if (is_wolverine(a6)) wvf_24454(); else lifted_19b02();` (and `f_19b1e` special; `f_19b5a`, `f_19b3c`, `f_19d6a` stubs). Default-off define `SAT_WV_NATIVE`; the skin remains the fallback (section 6).
  Dispatch through the ROM-image pointer tables (patching 0x19b0e+4 to a fake address) is not used: it needs a new entry in the generated `f_dispatch` lookup and an image write; wrapping the stub is smaller and already proven (the same pattern as `f_195ec`, `f_19f9a`, `f_1cf54`).
- The **patch table** (`wv_patch[]`: address, length, bytes; MODELLED about 40 entries, 600 B) is applied to the ROM image in cart RAM (ROMB at 0x02400000, the page the names hack already writes) in `names(on)`-style when `sat_guest_sel & 1`, with originals saved (about 300 B bss) and restored when it is switched off.
  Schaefer's records are only used by the slot Wolverine replaces, so an in-place patch is safe (the skin pokes and undoes around every collision call because it was not allowed to assume that). It covers: attack records (damage index byte 9, reaction byte 11, pushback bytes 12/13, hitstop byte 14, box x/y/halves), hurt boxes, frame durations of the chain/finisher/special/jump/hit scripts.

### 2.2 Size (READ for existing parts, MODELLED for the new ones; SH-2 -Os)

| Item | Skin today (`wolverine.o`, READ) | Native, recommended set A (MODELLED) | Native, Stage 0 identity test (not shippable) |
| --- | --- | --- | --- |
| Text | 5,796 B | about 5,300 B: objects 1,092, advance 776, reset ~300, glue/wrappers/patch apply ~600, **forked attack 956 + special 982**, pickup/names ~250, rest | 5,300 + 16.6 KB (all 9 private routines, minus the two already counted) |
| Tables | 19,524 B: tiles 16,840, boxes 1,584, steps 396, lift 396, pose_start 140, rest | about 16,300 B: tiles 14,592 (set A), steps 320, lift 396, pose_start 120, patch table 600, pal/row 104, rest | same as set A |
| bss | 229 B | about 260 B (+ originals backup ~300 B) | same |
| Region | cart tail (cold1) with `guests.c`, `home_cold.c` | cart tail | cart tail (use `GUEST_STAGES` limited build) |

Where it goes and why:
- **Low RAM: no.** `lw_free` is 76 B (latest `b_d6off3.log`); every byte there is already lifted code.
- **High RAM: no.** `hw_free` 4,616 B and the heat ordering keeps the hottest chunks there. The fork is cold code (a tap or a special, a few calls per second).
- **Cart tail (cold1): yes.** `cold1_at` is computed from the cold size rounded to 4 KB (`build.py:428`); `cart_free` 6,432 B is just that rounding slack, so the recommended +0 net KB fits inside it. Anything beyond the slack pushes `cold1_at` down and costs sprite room.
- **Stretches** (free: 68,164 / 60,416 / 58,368 / 27,000 / 11,544 / 620) are an option for the Stage 0 identity build only, because tile spill uses those same pages in the stages that overflow the cart. They are not free: 1 KB of code there is 8 sprite tiles of round-file room.

### 2.3 Tile budget (READ: `D6/remap.json`, `gen_c.py` output; fit.py 1,511 tiles, limit about 1,514, stage 24 tightest: Wolverine drop 2,606 against Schaefer 2,607)

One sprite tile is 128 B (16x16 at 4 bpp, 8 per KB). Code placed in the cart tail or a stretch displaces tiles 1 KB to 8. With a 1-tile margin at stage 24 the rule is: **net code change must be zero or negative, or be paid for by dropping tiles.** Exclusive tile counts per move (tiles no other move uses):

| Move | steps | exclusive tiles | notes |
| --- | --- | --- | --- |
| tornado | 11 | 107 | the desperation move |
| hit_h | 15 | 99 | heavy reaction (health delta 17 or more) |
| jump | 9 | 92 | air poses |
| hp / lp | 11 / 14 | 83 / 68 | |
| hit_m / hit_etc | 11 / 9 | 61 / 65 | |
| walk | 18 | 56 | |
| berserker | 23 | 49 | gun slot move; no gun for him |
| knockdown | 18 | 29 | |
| idle, hk, throw, crouch | 12, 19, 22, 6 | 0 | all tiles shared with other moves |

| Set | keys (tiles) | poses | tile entries (8 B each) | steps | change vs full |
| --- | --- | --- | --- | --- | --- |
| Full (today, 14 moves) | 1,511 | 69 | 2,105 (16,840 B) | 198 | |
| **A: drop berserker + hit_h** (recommended minimal) | 1,363 | 59 | 1,824 (14,592 B) | 160 | -148 tiles (about 18.9 KB of pixel room), -2.2 KB descriptors, -38 steps |
| B: A and hit_m (one reaction + knockdown) | 1,302 | 52 | 1,614 | 149 | -209 tiles |
| C: A and tornado (no desperation move) | 1,256 | 56 | 1,711 | 149 | -255 tiles; not recommended, drops a signature move AvP characters all have |
| D: A and knockdown pose (uses hit reaction) | 1,334 | 56 | 1,752 | 142 | -177 tiles |

Recommended: **A.** It frees 148 tiles, which pays for the whole native code delta ten times over (the fork adds about 1.9 KB = 15 tiles, and Stage 0's 18 KB identity build never ships). It restores the stage-24 margin from 1 tile to about 130 (MODELLED; re-run `fit.py`, section 6). The near-duplicate merge at K 12 (-37 more tiles, measured last pass) stays as reserve. Core vs droppable:

| Move | Class | Saves if dropped (tiles / steps / descriptor bytes) |
| --- | --- | --- |
| idle, walk, lp, hp, hk, jump, knockdown, hit_etc, crouch (getup), tornado, throw (grabbed) | **core** | - |
| hit_m (medium reaction) | droppable | 61 / 11 / 267 entries x 8 = 2.1 KB when merged into hit_etc |
| hit_h (heavy reaction) | **droppable (recommended)** | 99 / 15 / 3.0 KB with berserker dropped (A) |
| berserker | **droppable (recommended)** | 49 / 23 / 0.4 KB, plus no gun-slot code (2.2 KB) and no motion-input code (460 B) |
| tornado | core in AvP terms | 107 / 11; only drop if size forces it |

## 3. The 61 interface fields: contract and the diff harness

The 61 fields are the rows of `docs/guests/PLAYER_INTERFACE.md` (census over 328,049 frames, Schaefer, stages 02 to 26). Two corrections to that census, found while reading `iface.tsv`: the +40 external-writer list (296 routines) is an artefact of the census walk script writing held health from whichever actor was running, so the true writers of +40 are the damage, drain, heal and continue paths below; and the file counts byte/word accesses together, so a few `+xx` pairs (+0e/+0f, +1c/+1e) are one long field.

Because the recommended fork leaves the state machine shared, **the native Wolverine writes every one of the 61 fields in the same place Schaefer does**. What can differ is only what the two forked routines and the patch table touch. The contract below says, per field, who reads it, what the native side must keep true, and how the harness checks it.

Verify classes: **X** exact every tick in all stages of the plan (identity stage and after), **T** same value sequence but retimed (his durations differ), **D** deliberately different (allowlist with a numeric bound), **S** system/script owned, must not be disturbed (check the writers did their job, not the player).

| Field | What it is (MEASURED/READ; "inferred" where only access pattern is known) | Outside readers (class) | Native must | Class |
| --- | --- | --- | --- | --- |
| +00 | active flag | everything (20 tags) | stay nonzero while playing; system clears at game over (91e4, 9750, a466) | X |
| +02 | script/cutscene flag | 1d314, 1e396, 797d6 | untouched (scripts set it; fork never writes) | S |
| +04/+05/+06 | state, substate, action | 299 routines, enemy AI | same transitions; action values differ in time only | X (value set), T (durations) |
| +08 | actor tag, 0 for players | collision/damage | constant | X |
| +0e (long with +0f) | height and facing/flags, inferred from jump writes | AI 0c, 1d25e, aaa12 | written by jump (shared) and knockback (1d314) | X |
| +10 | x | 594 routines | movement shared; stage scripts write it for cutscenes (98436) | X (walk speed unchanged) |
| +12, +16, +1a | grab link and held offsets | 1d908, 3ac0c | written only by tag 14 while held; fork never writes | S |
| +14, +18 | depth (two copies) | AI, 1d25e, 1d6b2 | written by walk (shared), special (fork must keep writing both, `f_24f04` does) | X |
| +1c/+1e | frame record pointer (long) | collision, 483ee, 52188, 585be, aaa12 | patched records keep addresses; fork must never leave it pointing outside the image | X |
| +24 | animation script/word | 30d34, 32422, 9aa90 | written by `f_1656e`; fork reads | X |
| +2c | hitstop | 1cf54, 1d1f8 | written by the collision pass from record byte 14; his values differ | D (bounded: Linn 6 to 12) |
| +40 | health | HUD, 1d492, 1d504, 20a10, 3c29e, 5767e | only damage_apply, drain (6 per Tornado), heal, continue write it | X (path), D (damage amounts) |
| +42, +44 | displayed health / previous | ac92a, ac9fc | HUD owns | S |
| +46, +48 | last-hit accumulators | 1d314 | engine writes | X |
| +4c | kind/size flag | AI 0c | constant for the slot | X |
| +4e | hit class (record byte 13) | 1cf54, 1d314, 1d622 | engine writes; his records define values | D |
| +50/+52 | T block pointer (long) | 1cf54, 1d1f8 | keep Schaefer's address (the image is patched in place) | X |
| +54 | size/ordering | AI, 1d1f8, b0c22 | constant; written by 1f652 | X |
| +56 | pickup state | bca58 | engine | S |
| +5c, +5e | depth ring / lane history (very hot: 951k writes) | AI, 1d908 | written by walk and the special | X |
| +6a, +6c, +6e, +70, +72 | hit hand-off from record bytes 11/12/13: reaction type, push, class | player hit state, 1d314 | engine writes; Wolverine hit states read them | D (values), X (use) |
| +74 | held item / pickup target | 1bc38 | the pickup wrapper (`f_19f9a`) refuses weapons | X |
| +7c | scripted-move counter | 9aa90 | untouched | S |
| +84 | read by 1689a (AI) | AI | constant | X |
| +8a, +8c, +8e | camera follow values | c400, ccf8, 1ce98 | written by camera code from +10/+18 | X |
| +92, +96 | AI aggro/noise | 19 and 58 AI routines | written in walk/special (shared) | X |
| +98 | damage-state | 1d73a | engine | X |
| +9e | cooldown | 1c9a8, AI | special writes it (fork) | X |
| +ae | scripted-move owner | 94b3a | script | S |
| +c0, +c2, +c4, +c6, +ca | gun/projectile slot | 21ef8 | not written once the gun slot is a stub (Schaefer writes them) | D (Wolverine: zero writes, documented) |
| +d0 | lives/credit | 8836 and 28 more | system | S |
| +d2 | character index | 1689a, 9750, 797d6 ... | stays 1 | X |
| +d4, +e0, +e2, +ee, +f2, +f4, +f6, +f8, +fc | score, HUD stocks, camera lane, continue | system and 166ac | system | S |

Total 61. **The harness is built from this table**: each row is a test, so a field nobody exercised cannot silently regress.

### 3.1 Harness design (HOST first, EMULATOR second)

1. **Scripted input.** A pad script (frame, mask) covering stand, walk, depth, attack taps and mashing (3 chains), jump, jump attack, special, being hit (light, heavy, knockdown), being grabbed (tag 14), getting up, pickup, KO and continue. The MAME `char_measure.lua` plan phases (idle, walk, depth, atk1, atk_chain, gun, jump, jump_atk, dash, dash_atk, special) are the seed; the fight stretch and a Ganado/grabber room cover the hit and grab rows. Same script feeds both runs.
2. **Runs.** A: the Schaefer build (guest off, char 1). B: the same binary, guest on, `SAT_WV_NATIVE`, Schaefer in the slot (the guest draws the poses, the logic is the fork). Deterministic: fixed seed (the existing `golden_seed.bin`), no wall-clock input. Preferred tier is the lift host runner (`tools/lift_runner/host_kernel.c`, `HOST_CHECK` mode) because it is exact and fast; the Yaba tier runs the same script through `play_yaba.py` and samples with the MCP port (own copy, 9714).
3. **Sampling.** Every vblank dump the 256-byte player block (ff8380) plus the outbound page list (ff1800 collision lists, ff8600..ff8aff spawns, ff7f00..ff8300 globals, enemy blocks ff9a00..ffc6ff). Compare per field.
4. **Report.** For each of the 61 rows: first divergent tick, divergent tick count, class (X/T/D/S) and verdict. X fails on any divergence; T is compared after aligning on state entry; D must stay inside its documented bound; S is checked as "the writer ran and the value is what Schaefer's run had".
5. **Stage gates.** Stage 0: all 61 X (identity build, patch table empty, all 9 private routines forked) and all outbound pages equal. Stage 1: patch table on, expected D set only; every unlisted field still X. Stage 2: native logic on, T/D set documented per row; Round 1 to boss run (section 6).
6. **Unit tier.** A host test next to `tests/wolverine_clock_test.c` that runs the fork routine and the lifted routine on the same register/RAM state for each reachable entry (the lift gate pattern used by `learn_unit`), so a Stage 0 failure is localised to a routine.

## 4. Measured per-character data (what Wolverine is scaled from)

MAME 0.289, stage 02 start, same pad script per character (`run_char_measure.sh NAME CHAR`), 60 Hz ticks. n is small for damage (see the note under the table). Evidence: `E:\AvP\learning\lane-wolverine-native\c0..c3, n1, n2`.

| Property | Schaefer | Linn | Warrior | Hunter | Wolverine proposal | Source/addresses |
| --- | --- | --- | --- | --- | --- | --- |
| Walk, px/tick (100 px, 118-tick walk) | **2.08** (48 ticks) | 2.50 (40) | 2.22 (45) | 2.38 (42) | **2.08** (x1.0; was 2.86 in the skin) | walk_r phase; shared walk `f_1997e`, MSHvSF's own walk is 2.8 |
| Depth, px/tick | 1.0 | 1.2 | 1.0 | 1.1 | 1.0 | walk_up/down phases |
| Dash | none (walk state) | none | none | none | none (see Q4) | `dash` phase: 020002 throughout |
| Attack tap length (state 020006) | 15 | 12 to 13 | 12 | 12 (020014) | **12** | state run lengths |
| Startup / active / recovery of the first tap | 3 / 6 / 6 | 2 / 7 / 3 | - | - | **2 / 4 / 6** | frame durations, records 163644.., 16d68c.. |
| Chain | 3 punches, pause, 02000e kick (32 ticks) | 6-hit flurry in one state, 5 more taps | 3 + 020014 chain | 4 via 020014 | LP, LP, HP then kick | chain log |
| Damage index byte 9 per hit | 0x08, 0x10, 0x23; kick 0x0c | 0x02, 0x05, 0x0a, 0x12, 0x1a, 0x26 | 5, 12, 28; 6, 8, 16, 32 | 6, 8, 16, 32 | 0x04, 0x06, 0x14, kick 0x1c | attack record byte 9, `f_1d504` |
| Forward reach of box edge (px from origin) | 80, 94, 105; kick behind (96) | 63, 75, 71, 85, 91, 86 | 75, 87, 112 | 72; 106 to 128 | 72, 78, 95, kick 100 (forward) | record x and half width |
| Hitstop (record byte 14, ticks) | 8, 8, 12; kick 10; special 4 | 6, 7, 8, 9, 12; special 7 | 8, 10, 12 | 10, 12 | 7, 8, 10; kick 12; special 4 | `f_1cf54` writes it to the defender +0x2c |
| Reaction class (byte 11) | 0x14/0x12 stagger; 0xf0 on the 3rd, kick, special | 0x11 stagger; 0xf0 on 3rd/6th and special | | | stagger LP/LP/HP, 0xf0 on kick and Tornado | record byte 11 |
| Special (08) | 57 ticks, hits 25/20 both sides, hitstop 4 | 88 ticks, hitstop 7 | 55 to 61 | 86 to 90 | **57** ticks, hits both sides, reach 56 | state runs |
| Special cost | **6 health** (81 to 75) | **6** (36 to 30) | - | - | **6** | `f_1b492` (cost table 0x1b4bc, 6 per call) |
| Jump | 33 ticks (57 with air kick) | 36 | | | 33 (as Schaefer; shared handler) | 020004 runs |
| Gun / burst | 12-shot burst, 42 to 49 ticks, no health cost | 14-shot, 43 | | | none | 02000c |
| Hit stun / knockdown (player) | 28 ticks / 107 | 26 to 28 / 101 to 116 | 30 / 99 | 24 to 28 / 87 | 28 / 107 (as Schaefer, shared machine) | 0202xx runs |
| Held by an enemy (tag 14) | 60 ticks (020400, 020406) | not reached | 60 | reached | as Schaefer | 0204xx |
| Hits taken from stage-02 enemies | 10 | 10, 17 | | | | health deltas |

Note on damage: the *landed* damage on a stage-02 enemy was 24 for the light attacks and 31 for the strongest hit, for both Schaefer and Linn, from only 9 events. The byte-9 index goes through a lookup (`f_1d504`: column = table[class*32 + difficulty] + byte 9 as a byte, row from armour, then a damage table), so index is **not** proportional to HP lost. The plan therefore treats byte 9 as a relative strength and ends Stage 3 with a calibration run (section 7) against a stationary enemy. Nothing about absolute HP per hit is claimed here.

Role read from the table. Warrior: balanced, longest reach. Schaefer: heaviest walker, big slow hits, a back-sweep finisher. Linn: fastest walker, short reach, six quick hits in one state. Hunter: fast walker, long reach 12-tick chain. Wolverine fits between Schaefer and Linn: Schaefer's weight on the ground, Linn's rhythm on the swing, a forward kick finisher that knocks down, and a short two-sided Tornado for crowds.

## 5. Design: fitting him into AvP's beat 'em up

### 5.1 Walk and weight
Keep Schaefer's walk speed exactly (the skin's x1.375, `wv_speed_tab`, is removed in Stage 2). Reason: the owner asked for "walks slow", AvP's four walk at 2.08 to 2.50 and his MSHvSF walk is 2.8, so any boost would make him the fastest on the screen. His walk *animation* is distance driven (kept) so feet match ground speed. Depth lanes are the same 1.0 px/tick; hit windows in depth (record half-depth `dzh`) are 8 to 13 for every chain hit in the game; his chain uses 10.

### 5.2 Moves, with frame data (reasoning relative to Schaefer/Linn); PROPOSAL (MODELLED), tune in Stage 3
Ticks at 60 Hz. "Total" is the state's length. Reach is the forward edge of the attack box from his origin.

| Move (AvP slot) | Input | Startup / active / recovery | Total | Dmg idx | Reach | Hitstop | Reaction | Poses reused (no new art) | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LP1 (06, stage 0) | attack | 2 / 4 / 6 | 12 | 0x04 | 72 | 7 | stagger | `lp` poses (12 poses, 14 steps) | Linn's first tap is 12 ticks; reach between Linn 63 and Schaefer 80; index between Linn 0x02 and Schaefer 0x08 |
| LP2 (06, stage 1) | attack again | 2 / 4 / 6 | 12 | 0x06 | 78 | 8 | stagger | `lp` | between Linn's second (0x05) and Schaefer's first (0x08) |
| HP (06, stage 2) | attack again | 3 / 5 / 8 | 16 | 0x14 | 95 | 10 | stagger (not knockdown) | `hp` (3 attack poses) | slightly longer than the other taps; below Schaefer's third hit (0x23 = 35) and near Linn's fourth (0x12) |
| HK finisher (0e) | attack again | 4 / 6 / 12 | 22 | 0x1c | 100 | 12 | **knockdown** (byte 11 = 0xf0) | `hk` | Schaefer's finisher is 32 ticks and hits behind him; a forward kick at 22 ticks is "slash fast" without out-damaging the chain |
| Chain total | 4 taps | | **62** vs Schaefer 77 (-19%) | 4+6+20+28 = 58 | | | | | sustained index per tick including the finisher: Wolverine 58/62 = 0.94, Schaefer (8+16+35+12)/77 = 0.92, Linn 99/93 = 1.06 (6 hits in the 93-tick atk_chain run); he swings faster at Schaefer's output |
| Tornado Claw, desperation (08) | attack + jump | 2 / 48 / 7 | 57 (as Schaefer, active 2 to 50 measured) | 0x19 multi-hit | 56 both sides | 4 | knockdown | `tornado` (11 steps, 107 exclusive tiles) | Cost 6 health through `f_1b492`, one call, as Schaefer and Linn measured; both-side box handles corners and surrounds |
| Jump (04) | jump | shared | 33 | | | | | `jump` | arc and air kick are Schaefer's physics; air poses time-stretched over them |
| Air attack | jump, then attack | shared | to landing | Schaefer air records 0x0f then 0x18 | | | | `jump` poses | "Rising/diving claws" of the reference list are not separate AvP moves (see 5.7) |
| Hit stagger / medium / heavy (0202) | taken | 28 | 28 | | | | | `hit_etc`, `hit_m` (and `hit_h` in the full set) | length is the shared machine's, picked by damage taken |
| Knockdown / getup (0202 > 21, 0208) | taken | 107 | 107 | | | | | `knockdown`, `crouch` | |
| Grabbed (0204) | by tag 14 enemy | 60 | 60 | | | | | `throw` poses (22 steps, 0 exclusive tiles) | |

### 5.3 Combos and controls (existing system only)
- **Chain rule:** AvP chains by button, not by hit: a tap inside the state continues, 30 idle ticks resets (`AVSP_PW_COMBO_RESET_FRAMES 30`, Warrior; Schaefer's `f_24454` stage counter behaves alike). Native follows it, so the skin's "chain on a landed hit" (`SAT_WV_NATIVE_TIMING`, the `landed_` bookkeeping, the collision answer d0 hook, about 300 B) is **dropped**: it is a new rule none of the other four have.
- **Desperation:** attack and jump together, 6 health, as all four; no meter.
- **Gun button C:** not a claw button in the recommended set (the gun slot is a stub). Full-set option: C plays Berserker Barrage directly with no motion input (the skin's quarter-circle injection goes away with `sat_guest_wolverine_pad`, 460 B).
- **Dash:** AvP has none (forward-forward is the walk state for all four; measured: no faster travel). A real dash is a new action slot (use the freed gun slot 0c, about 400 B of fork plus 8 steps) and would be the only new mechanic. **Question 4.**
- **Throw/grab:** AvP players do not grab; the grab state is the player being held by a tag 14 enemy for about 60 ticks (`f_1d908` writes the player's position, MEASURED at 60 ticks in the Schaefer and Warrior runs). The skin's `throw` poses are used for that held state. A "Feral Grab" would be a new mechanic and is **not** planned.

### 5.4 Enemies and situations
- **Alien swarms / multiple attackers:** the Tornado is the crowd tool (both sides, multi-hit, hitstop 4); the chain's knockdown finisher clears the front enemy. Enemy cap and AI read his position, state and size fields only (rows +10, +14/+18, +4c, +54, +92, +96), all unchanged.
- **Grab/pounce enemies (tag 14):** held for 60 ticks and released; nothing in the run shortens it with input. Whether mashing attack shortens it is not measured (**Q9**; measurable in Stage 3 from the same script).
- **Large bosses:** damage goes through the boss armour row in `f_1d504`; his lower index per tick helps boss fights less than Schaefer's heavy hits. Tornado is the boss tool. Use the Stage 3 calibration run (a boss-armour class dummy) before accepting numbers.
- **Depth lanes and wall corners:** chain boxes are 10 half-depth (like the others, 8 to 13), Tornado 40. World bounds (864..1184 x, depth 224..327, upper walkway 1091) are the shared walk's.

### 5.5 Weapons and pickups
AvP characters carry weapons and fire guns. Wolverine **claws instead**: the pickup wrapper (`f_19f9a`) already lets him take food (kind 0x0a) and score items (0x0b) and answers "nothing to pick up" for weapon kinds (02, 03, 07, 08, 0e). The rest of the game is unaffected (the item stays on the floor for a co-op partner; scripted weapon drops remain). The held-item routine `f_24582` (6.1 KB) and the gun burst `f_2576a` (2.2 KB) are never compiled for him. **Question 2** if the owner wants him to use pickups.

### 5.6 Healing factor
Not recommended as a regen: AvP has no regen, and a regen would change the score/continue balance (health is what ends a life; `damage_apply` floors a player at 6; heal `pickup_heal` 0xbc638 adds a table value capped at 0x65). The only version that fits existing systems is a **data patch: food heals more for him** (the heal table value x1.5), no timer, no new code, visible as a faster return to full after a pickup. That table was not measured here, so it is a Stage 3 task if the owner wants it. **Question 3** (recommend: drop).

### 5.7 Reference move list mapped to AvP's existing slots (Marvel Cosmic Invasion is flavour only)
| Reference move | AvP slot used | Verdict |
| --- | --- | --- |
| Reverse Claw (hold attack, counter) | none (no hold/block in AvP) | not planned |
| Feral Grab, throw | none (players are grabbed, not grabbers) | not planned |
| Adamantium Stab (grab then attack) | none | not planned |
| Adamantium Rage (Focus special) | attack + jump desperation, health cost | **Tornado Claw** (existing) |
| Rising Claws / Downward Slash | jump and the air attack state (shared) | one jump attack, no separate rising/diving states |
| Blade Rusher (forward, forward, attack) | forward-forward is just walk in AvP | not planned unless Q4 says yes |
| Healing Factor | none | drop (Q3) |

### 5.8 Knockdown, getup, invulnerability, co-op consistency
All reaction rules are the shared machine's, so he behaves like the other four to enemies and to a co-op partner: light hit stagger 28 ticks, a knockdown about 107 ticks (Schaefer 107, Linn 101 to 116, Warrior 99, Hunter 87), held 60 ticks. His hurt boxes: the skin pokes MSHvSF's per-pose hurt boxes (half width 39, uneven from pose to pose). Recommended: use Schaefer's stock hurt boxes so enemy AI and co-op hits land identically (**Question 6**). Getup invulnerability: not measured (the scripted run never reached 0208xx); Stage 3 measures it from the same harness and the native keeps whatever the shared machine does. The finisher and Tornado knock enemies down like Schaefer's byte-11 0xf0 records, so a co-op partner is not trapped by hitstop (hitstop 12 and 4 are inside the existing 3 to 20 range).

### 5.9 Pose coverage of Schaefer's states (the question asked of Linn's states)
Every state the shared machine puts a Schaefer-slot player in during the scripted run has a Wolverine move already in the resident set; none needs new art. Linn's extra states (020014 one-tick chain steps, the 6-stage flurry) are not entered because the slot is Schaefer's.

| State seen (MEASURED) | Ticks | Wolverine move (poses) |
| --- | --- | --- |
| 020000 stand | idle | `idle` (12 poses, 59-tick loop) |
| 020002 walk, depth, "dash" | | `walk` (distance driven) |
| 020004 jump (33, 57 with air kick) | | `jump` (7 poses) + `wv_lift` arc |
| 020006 attack (15 per tap) | | `lp`, `lp`, `hp` |
| 02000e finisher (32) | | `hk` |
| 020008 special (57 to 63) | | `tornado` |
| 02000c gun (42 to 49) | | `berserker` (full set) or none (set A) |
| 020200/020202 hit (28), knockdown (107) | | `hit_etc`/`hit_m`/`hit_h` by damage, `knockdown` |
| 020400/020406 grabbed (60) | | `throw` poses |
| 0208xx getting up (anim lane) | | `crouch` |
| 04xxxx KO | | `knockdown` poses; draw path from the gate lane |
| 080000 entering (64 to 347) | | `idle`/`walk` |

### 5.10 Linn base vs Schaefer base (the owner chose Schaefer; recorded for the file)
Linn's private routines are 18.5 KB (jump 5,246, tick-pre 1,968, state 14 3,652); her chain is a six-hit flurry in one state, so mapping Wolverine's four-hit chain onto it means rewriting the stage counter. Schaefer's chain (3 punches + 02000e finisher) is the same shape as LP, LP, HP, HK, and Schaefer's walk is the weight asked for. Schaefer base + Linn timing data is the smaller change. Linn is used only for the number column.

## 6. Switch plan and gates

- **Define:** `-DSAT_WV_NATIVE` (default off), under `SAT_GUESTS`. Off: build is identical to today's skin build (flag-only rebuild; compare disc sha as the skin lane already did). On: native; skin code paths compiled out or left unreached.
- **Fallback:** the skin stays in the tree. `sat_guest_sel` bit 0 chooses Wolverine; the OPTIONS row stays. A second selector bit or a build define can force the skin if native fails a gate.
- **Gates (all must pass to switch the default):**
  1. `tools/wolverine/fit.py` over 76 stage files: gate True, 0 own tiles dropped, stage 24 not worse than Schaefer's drop count (set A expected to improve it). Tile total reported.
  2. Build: rc 0, `hw_free` not below 4,616, `lw_free` not below 76, `cart_free` reported, stretch_free unchanged. Both switch states.
  3. Python and host tests: existing 22 `test_wolverine_*`, a new native clock/fork unit test, and the 61-field diff (section 3.1) at Stage 0 and 1.
  4. Round 1 to boss clear, Schaefer vs native Wolverine: same scripted pad where possible. The previous bot did not clear the boss in 1,100 s at Yaba's 7 to 16 v/s, so this gate needs either the host runner or a longer bot; record kills, KO ticks, boss present tick, no fatal, no stuck.
  5. Save/load 4 cycles (plots advance), pick-ups (food, score, weapon refusal), continue, KO draw (the gate lane's fix included), P2 join with Wolverine in slot 1.
  6. Look clips: idle, walk, chain (all four stages), jump and air attack, Tornado, each hit reaction, knockdown/getup, grabbed, KO, and a side-by-side with the skin. Reviewed by eye by the owner.
  7. Console/hardware stays UNRUN until the owner does it.

## 7. Staged implementation, effort, risks

| Stage | Content | Effort | Exit |
| --- | --- | --- | --- |
| 0 | Harness (section 3.1) on the host runner; `forkgen.py` extracts and renames the 9 private routines; wrappers for the 6 stubs; skin disabled. Patch table empty. | 3 to 4 days | 61 fields X over the scripted run, outbound pages equal; fit check not applicable (test build `GUEST_STAGES=02`) |
| 1 | `nativepatch.py`: apply/undo patch table over the image; Wolverine records and durations in; attack/hurt box poke hook and `landed_` removed. Prune to the shipping fork (attack + special; others stubbed or shared). | 2 days | only the listed D rows differ; fit/build gates |
| 2 | Native logic: chain stage to move map (LP, LP, HP, kick), special, tick-based pose clock from state entry, walk x1.0, motion-input and chain-on-hit code removed; poses for set A. | 3 to 4 days | look clips, Round 1 run, no regression of the gate lane's KO fix |
| 3 | Calibration: stationary-enemy damage curve for byte 9 (host runner), pushback, hitstop, getup invulnerability, grab-mash; owner questions answered; tune the Section 5.2 numbers. | 2 days | numbers table replaces proposals |
| 4 | Gates 1 to 6 on the final candidate in parallel; docs; KNOWN ISSUES row if any. | 2 to 3 days | switch ready |

Total about 12 to 15 working days (about 11 if Stage 3 is cut to the damage curve only).

### Risks, most severe first
1. **Fork generator on the lifted sources.** The fork is generated C (`goto` labels shared across routines inside one lifted body, condition-code macros, `DISPATCH` calls). Mitigation: Stage 0 proves identity routine by routine with the unit tier before any edit; fork only two routines for shipping, so a generator bug is bounded to about 2 KB.
2. **Tile margin at stage 24 (1 tile).** Any code in the cart tail or a stretch costs sprite room. Mitigation: set A frees 148 tiles; K 12 merge in reserve; fit.py run on every stage-file change; never ship the Stage 0 18 KB build.
3. **Damage/pushback are table lookups, not the numbers in the record.** Only 9 hit events were measured. Mitigation: Stage 3 calibration before any claim; Stage 1/2 keep Schaefer-family byte 9 values scaled the way Linn's chain scales.
4. **Pose timing against patched record durations.** The pose clock is tick-based while the machine now runs on his durations; a mismatch shows as pops. Mitigation: pose clock reset on every state entry, durations generated from one table (`gen_c.py` NATIVE / `wv_steps`), look clips per move.
5. **Unmeasured states.** 020014 (unused by Schaefer), 0a, 0x10 to 0x1a stubs, getup (0208), exit states were not entered in the scripted run; if a stage script forces one, the shared machine handles it for Schaefer but a stubbed slot would not. Mitigation: only stub slots the Stage 0 diff run never enters; run the full-route bot at Stage 2.
6. **Interface gaps in the census** (health never dropped to zero; continue not covered). Mitigation: Stage 0 script adds KO and continue; fields in S class are checked by the writers.
7. **Yaba is slow (7 to 16 v/s)** and the Round 1 bot is nondeterministic across builds, so equivalence evidence has to come from the host runner; whether `host_kernel.c` links the guest wrappers is unconfirmed and is Stage 0's first task.
8. **Another lane owns the KO invisibility fix** (`lane/wolverine-gate-20261109`). Native must adopt it, not duplicate it; merge order matters.

## 8. Owner questions (recommendation first)
1. Drop the heavy hit reaction `hit_h` and Berserker in the minimal set A? **Recommend yes** (-148 tiles, restores the stage-24 margin); the full set stays buildable.
2. Should he be able to pick up weapons? **Recommend no** (claws instead), as built today.
3. Healing factor? **Recommend drop**; if kept, only as "food heals 1.5x" (data patch).
4. A real dash? **Recommend no** (none of the four has one; it would be the first new mechanic).
5. Desperation cost 6 health like Schaefer and Linn? **Recommend yes.**
6. Hurt boxes: Schaefer's stock boxes, or MSHvSF's per-pose boxes? **Recommend Schaefer's** (enemy and co-op consistency).
7. Finisher kick knocks down and is a 22-tick forward kick (Schaefer's is a 32-tick back sweep)? **Recommend yes.**
8. Chain by button only (no hit confirm)? **Recommend yes** (matches the other four).
9. Should attack mashing shorten an enemy grab? Not measured; ask after Stage 3.

## 9. Evidence and tools added in this lane
- `tools/wolverine/char_measure.lua`, `run_char_measure.sh`: scripted per-character run (states, position, health, frame record, 16-byte attack record, nearby enemies). `MS_NOHOLD=1` leaves health free so special costs show.
- `tools/wolverine/rom_dump.lua`, `run_rom_dump.sh`: dump ranges of the 68k program space (opcode view) to read the character tables.
- Raw logs (ROM-derived, not committed): `E:\AvP\learning\lane-wolverine-native` (`c0` Warrior, `c1` Schaefer, `c2` Linn, `c3` Hunter, `n1`/`n2` health-free runs, `rd1` table dumps, `syms.txt` object symbol sizes, `fnext.json` 68k extents).
- Sizes: `nm -S` over `w1/obj-Os/c*.o` of `lane-wolverine-anim`; per-move tile sets from `D6/remap.json` (`moves_one`); not re-fit here.

## 10. What this note does not claim
No gameplay change, no hardware or Yaba result, no damage-per-hit number. Frame data, byte-9 indices, reach and hitstop in sections 4 and 5.2 are proposals scaled from the measured columns. Code and data sizes of the native build are estimates until Stage 1 links. Absolute enemy HP loss per hit and the heal table are open.

## 10. Owner decisions (2026-11-09)
- Colours: his costume is the colour he already is in play, red and yellow (sprite palette unchanged). The artist's select portrait,
  HUD face and rank icon are recoloured to match: PNG indices 7-10 blue -> #ee3300 #cc0000 #880000 #550000 (from his in-game sprite), and
  the backdrop (index 1, was crimson #cc3333) -> navy #112255. Built as asset set E:\AvP\learning\lane-wolverine-merge\D8r.
- Move set: an overall minimal combo and move set, with Berserker Barrage as the special (attack+jump, 6 health), not Tornado Claw.
  Minimal set = walk (Schaefer weight), jump, chain LP LP HP + finisher kick (button chain, Linn speed), one jump attack, Berserker Barrage,
  plus the shared states (hit, knockdown, getup, KO, held). Dropped: Tornado Claw (107 exclusive tiles), hit_h (99), dash, motion inputs,
  chain-on-hit. This reverses Section 8 Q1 on Berserker; frees about 206 tiles (estimate, re-fit needed).
- Route confirmed: native character forked from Schaefer's code; Schaefer's walk weight, Linn's attack speed; no new game concepts.
