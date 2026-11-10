# Native Wolverine, step 1: slot census of Schaefer's animation tables (2026-11-09)

Lane `lane/wv-native-gfx-20261109`, after 48619cb (milestone 1) and the merge of avp/integration 55cf228. Plan V2 section 6 asks for native chains for every state Wolverine can reach. This note is the census that scopes it: which of Schaefer's animation slots each state uses, what the record flag and event bytes mean, and an estimate for the rest.

Evidence tiers: **HOST** = the lifted game on a PC (WSL gcc runner, `tools/lift_runner`) replaying MAME's golden routes; **READ** = lifted source; **DATA** = the program images (`rt.bin`, MSHvSF dump). No hardware, no emulator in this step. All ROM-derived output is under `E:\AvP\learning\lane-wv-native-gfx\census` and `D:\AvP-lanes\lane-wv-native2` (never in git).

## 1. Method

- Tool: `tools/lift_runner/host_kernel.c` gained a richer trace point line (`TP=16518,16526,165a4,16624`: the callee's `a0` table base, `d0` index, the caller block's state word, character number, tag and current record) and a `POKE=vblank:ffaddr:value[:bytes]` hook for scenario runs. `tools/wolverine/slot_census.py` turns the trace into per-slot counts; `slot_report.py` writes the full table (private).
- Selectors traced: `f_16518` (slot select), `f_165a4` and `f_16624` (slot select with root motion), plus the tail call `f_16526` (record store). `f_1b0c4` / `f_1b0f0` (character table lookups) end in `f_16518`, so they are covered.
- Runs: MAME's golden routes `golden_c1`, `c2`, `c3`, `full`, `2p` (Schaefer walks through the whole game, health held; 1,623,717 vblanks, each run **clean to its last vblank, 0 differing, 0 missed IRQ**): 477,005 selector calls on player blocks, 97,614 of them Schaefer's. Death / continue / game over are not in those routes (health is held), so a short free-running scenario (`FREERUN`, fight pad, health poked to 1 at vblank 1250) added the KO states (`04xxxx` through the knockdown slots below).
- Static cross-check (READ): every call of `f_1b0c4` / `f_1b0f0` / `f_16518` / `f_165a4` / `f_16624` in the lifted source with the constant it loads in `d0` (`E:\...\census\static_sites.json`).

## 2. The tables

227 index entries: T1 0x162f90 (80), T0 0x163032 (32), T2 0x163074 (64), T3 0x1630f6 (**48**; the older "16" counted only the plain jump slots). 224 of them name a record chain: **135 distinct chains, 548 records, 278 distinct pose assemblies**. Many slots alias one chain (the stand record is named by 26 slots).

| Table | Selected by | Role (from the states below) |
|---|---|---|
| T1 (80) | the player's own routines, via the per-character base (0x1b0e0) | stand, walk, turn/hold, attack chain, special, grabs, pickups, lifecycle |
| T0 (32) | state 08 only (stage entrance, select/continue) | copies of the first T1 chains for the entrance; 12 slots seen |
| T2 (64) | the per-character table 0x1b104; damage code | hit reactions, knockdown, getup, KO |
| T3 (48) | the jump and air routines (`0x25xxx` and others, base loaded as constant 0x1630f6) | jumps, one chain per direction/speed variant |

## 3. What Schaefer actually reaches (HOST)

106 of the 227 slots (85 distinct chains, 339 records, 189 assemblies) were selected. By state word (`+4..6`; calls are Schaefer's, summed over the five routes):

| State | Calls | Slots | What it is |
|---|---:|---|---|
| 020000 | 24,174 | T1.0 (stand), T1.29 | stand |
| 020002 | 22,907 | T1.2 | walk (12 records) |
| 020004 | 87 | T1.10, 3, 38, 6 | short holds: turn, crouch (T1.6 is 6 records, 3 hurt boxes) |
| 020006 | 705 | T1.32, 33, 34, 35 | attack chain by stage (`f_24454` asks for 0x20 + stage); 36 (special, not seen here) |
| 020008 | 365 | T1.42 | the gun action = today's Berserker slot: 14 records, 42 ticks, attack boxes 9, 10, 11, 13 |
| 02000a | 4,658 | T3.32..46 (even), T1.41 | air attack / second jump family (T3 even slots, 4 records each) |
| 02000c | 29,925 | T3.3..6 and T3.16..31 | jump (plain, 4 records: 2 + 2 + 4 ticks, then a 255-tick air hold) |
| 02000e | 117 | T1.14, 16 | landing / short recovery |
| 020010 | 39 | T1.0, 11, 12 | |
| 020012 | 168 | T1.13 | crouch-down |
| 020014 | 37 | T1.67..70, 76, 77 | 7-record chains with attack 33 (item/object use; not identified further) |
| 020016, 020018, 02001a | 2, 12, 9,008 | T1.31, 19, 23 | single-pose holds (02001a is 9,008 calls of a one-record hold: a "wait" state) |
| 020202 | 3,753 | T2.1..24, 45..57 | hit reactions (stand-up reaction chain T2.23/24: 9 records) |
| 0402xx, 040400, 040000 | ~700 | T2.13..22, 25, 29, 33, 37, 49, 54, 57 | knockdown flight, ground, getup, KO pose |
| 020400, 020406, 020408 | 198, 181, 3 | T1.48, 55, 56 | grabbed / held / thrown by an enemy |
| 080000 | 687 | T0.0..6, 10, 14, 16, 18, 24 and T3.3..6 | stage entrance |

Never selected in 1.6 M vblanks (the static scan says some of them can be): T1.1, 4, 5, 7..9, 15, 17, 18, 20..22, 24..28, 30, 36 (the special), 37, 39, 40, 43..47, 49..54, 57, 58, 60..66, 71..75, 78, 79; most T0 slots above 18; in T2 the entries 0, 3, 9 and the 25..44 aliases except 25, 29, 33, 37 (those four are the knockdown aliases that KO uses). The static scan finds constant-index selectors for 40 T1 slots (21 of them unseen in play), 10 T2 slots, and 16 routines that compute the index (the chain `0x20 + stage`, jump direction tables, grab/hold selection). Chain stages 1 to 3 (T1.33, 34, 35) occur in play, a few times each; the special chain T1.36 does not (its selector is the `f_2539e` routine). Wolverine's chain is LP, LP, HP by owner decision. **Treat every slot that has a static selector as reachable until a trace or the state routine proves otherwise.**

## 4. What the record bytes mean (READ + DATA)

- **Flags word `+2`**: bit 15 = last record (the target follows at `+16`, 20-byte record). The low byte is copied to block `+0x25`; **its low six bits are a root-motion index**: `f_165c4` / `f_16644` (the advance routines of the walk, jump and many reaction states) look it up in the shared table at 0x17188 (63 entries) and add a displacement of `index * 128 / 256` px (index 0 = none) to the block's x and depth in the direction `+0x0c & 0x1f` (a 32-direction table). This is the walk speed (walk records carry 0x0a 0x06 0x07 0x09 0x0e ...) and the push of attacks and reactions. **A native chain that keeps the donor's flags keeps the movement**, which is why Wolverine's walk speed equals Schaefer's in milestone 1.
- The **whole byte** is also tested by the state routines (about 90 sites between 0x213d0 and 0x28452): zero against non-zero (a nonzero byte on a record is the "live" trigger that advances the routine's sub-state `+7` and spawns the hit), and its sign (bit 7: a second trigger, used by the 020014 chains, byte 0xff). Wrong flags therefore break move progression, not just pictures.
- **`+8` hurt box, `+9` attack box**: indexes into the character's box table T (per character, 0x19744). `f_1656e` copies the timer to `+0x90` (hit hold) when `+9` is non-zero. Walk and stand chains use hurt 1 (6/7/8 for crouch); attack box indexes seen: 1, 2, 3 (chain), 4 (T1.36), 8, 9..13 (T1.42), 21, 24, 33, 37.
- **`+11` shadow index** (7, 6, 5, 4, 3 for the walk/crouch shadows; 13, 15 on knockdown) is read by the shadow emitter; **`+12..15` event bytes** are position/hold indexes: the grab chains carry 0x0f..0x14 in `+12` (read by the grab code to place the held victim), the stand has 0x01 in `+15`, the crouch and landing chains 0x0e..0x11.
- **Terminal holds** are 4,095 ticks (jump to themselves), T3 air holds are 255 ticks (the jump routine ends them on landing).
- Consequence for the generator: **copy the donor skeleton of every slot (durations, flags, +8/+9 indexes into T', +10/+11, event bytes, jump targets) and change only the assembly pointer and, where his MSHvSF record names them, the hurt/attack box indexes.** That is how milestone 1 built the walk, and it makes every state routine's contract hold by construction.

## 5. MSHvSF source data: his animation index (DATA, new)

His animation selection is not a code table: the program ROM has **27 sub-tables of 16-bit offsets at 0xd1a7e..0xd1c90, 238 entries, separated by zero words, each entry relative to its own sub-table's first word** (the same `base + s16(word)` scheme as AvP's `f_16518`), `tools/wolverine/mvlib.py` `MV.tables()`. Sub-table 0 is idle/walk, 1 jump and landing, 8 / 9 / 10 the light, medium and heavy punch and kick families, 14 a family of 35 short chains (hit reactions), 22 a family of 38 (specials, supers, knockdown, getup), 23 taunts/win poses, 24 effect objects. The records D11 captured (idle 0xd1c90, walk 0xd1da4, jump 0xd1fac, LP 0xd2878, HP 0xd29a4, HK 0xd2b10) are sub-table entries 0.0, 0.1, 1.0, 8.0, 8.2, 9.x.

**Art residency, the real limit.** The stage packs hold 1,474 tile keys chosen for D11's 69 poses. Of the MSHvSF records the move set needs, only some are fully drawable from resident tiles (K = 12 merge): idle 12 of 17 records, walk 10 of 16, jump forward 6 of 12, LP 3 of 6, HP 6 of 9, HK 5-6 of 8-9, landing 4 of 4. The ROM cells that are *not* resident (distinct 16x16 cells with no resident tile within K) for the move-set chains: idle 119, walk 162, jump 131-309 per direction, LP 40, HP 106, HK 66-120, union about **1,290 cells (upper bound; flips and merges among them not applied)**. stage24_ma has 48 tiles of margin. So "every record of every move" is a tile-budget decision (owner): the default stays "resident records only, the dropped records' ticks go to the previous one" (the rule milestone 1 used for idle, walk and LP), and each state's missing tiles are reported rather than silently traded.

## 6. Work estimate for the rest (MODELLED from the census; not measured)

| Package | Slots / chains | Notes |
|---|---|---|
| A. Ground set: stand aliases, turn/crouch/landing holds, 020010-1a | about 12 chains | skeleton copy + resident idle/crouch poses; mostly single-record chains |
| B. Chain, finisher, special: T1.32..36, T1.42 (Berserker as an explicit native action), 02000a family | 8 chains + routine changes | MSHvSF LP/HP/HK records for boxes and poses; the Berserker action changes the input path (`sat_guest_wolverine_pad`), cost rule and sounds; owner-bound items |
| C. Jump and air: T3 (48 slots, about 30 distinct chains of 3 poses + hold) | one pose triple reused across directions | root-motion bytes kept per slot; lift (apex 88 px) re-expressed; MSHvSF jump poses are half resident |
| D. Reactions: T2 (about 20 distinct short chains: flinch holds, knockdown flight/ground, getup 9 records, KO) | about 25 poses | small; sub-tables 14 / 22 supply hurt/knockdown art, D11's `hit_*`, `knockdown` poses are the resident subset |
| E. Grabs / lifecycle: T1.48, 55, 56 (+ unreached 49..54, 57), T0 entrance set, pickups (020014) | about 15 chains | event bytes carry the victim hold index; poses from his throw/grabbed art (not captured by D11) |
| F. Retire the skin machinery, measure memory, gates | whole build | only after A..E leave no donor-drawn state |

Rough size in this lane's units (one working session = one milestone-1-sized package with HOST proof, build, fit and Yaba legs): **A+D about one, C one, B one to two, E one, F one, plus a gates session**: about **five to six sessions**, if the tile decision is "resident records only". A "true MSHvSF motion" decision (about 1,290 more tiles for the move set alone, more for reactions) is not affordable at the current margin and would need packs larger than a 4 KB tail step buys (32 tiles); that is the one memory trade-off that needs the owner.

## 7. Not covered

- Death, continue and game over were reached only by the short poked scenario (states 04xxxx through T2.13..22). The `06xxxx` and `08xxxx` lifecycle states other than the entrance were not exercised.
- Mixed co-op and the second player slot: `golden_2p` includes a second Schaefer; its slot use matches player 1's.
- The state routine of each T1 slot was identified by state word, not by following every dispatcher; the static selector list (routine addresses per slot) is the starting point for the per-state specification of plan section 6.
