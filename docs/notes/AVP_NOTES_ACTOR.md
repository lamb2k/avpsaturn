# AvP source campaign: actor lane notes
nStatus: Investigation. Evidence: Fact or Historical evidence per its tier labels; old numbers are not a baseline.

Lane 2 of AVP_SOURCE_CAMPAIGN.md. Reconstruction in `source_recon/avsrc_actor.c`, gate in `source_recon/gates/actor.*`.
Tiers: **source** (read), **unicorn-differential** (learn_unit), **MAME** (probe `tools/learn_actor_probe_alloc.lua`, run `actor_alloc_d`,
Coffee Shop route, dump under E:\AvP\learning\mame). Nothing here is a console result. Addresses only; no tables.

## Who owns the 103 missing lifetimes (MAME + scene report)

Every source lifetime joins to its allocation with 0 unmatched (`tools/learn_actor_lineage.py`). 96 of the 103 are below; the other 7 start on
frame 5566, the last frame of the window, and are boundary rows.

| Missing | Lifetime | Allocated at | Owner (tag/class) |
| ---: | --- | --- | --- |
| 26 of 32 | tag 24 class 0x10 variant 4 | 0xa73b4 | tag 28 class 0x0e, emitter, period 49 ticks |
| 21 of 224 | tag 24 class 0x3d | 0x23226 | player, weapon hold body |
| 15 of 113 | tag 24 class 0x49 variant 0 | 0x8f0cc | tag 4 class 0 |
| 10 of 26 | tag 24 class 0x10 | 0x19f62 | player |
| 8 of 20 | tag 24 class 0x4e | 0x1d634 | player attacking (hit effect) |
| 6 of 8 | tag 24 class 0x49 variant 1 | 0x8f106 | tag 4 class 3 |
| 4 of 7 | tag 24 class 0x4b | 0x231c8 | player, weapon hold start |
| 2 of 5 | tag 24 class 0x4e | 0x1d634 | tag 4 class 0 attacking |
| 1 | tag 28 class 0x0e | 0xbc826 | tag 20 class 5 (drop) |
| 1 | tag 28 class 0x0c | 0xbc86a | tag 20 class 0xa (drop) |
| 1 | tag 24 class 0x20 | 0x1ac12 | player |
| 1 | tag 4 class 4 | 0x2fa14 | tag 4 class 0 |

Reading: no missing lifetime comes from the spawn table. Those rows are all placed. The gap is three things:
1. **One missing emitter (tag 28 class 0x0e) owns 26.** It is spawned by a drop from tag 20 class 5, frame 3892. First puff in the probe 3925, then every 49 frames.
2. **Player-owned children diverge with the player.** 0x3d, 0x4b, 0x10 (0x19f62), 0x20, 0x4e, 0x49: the owner body exists natively, so these need the spawn call in the owner, on the owner's own conditions. Not new actor bodies: all these classes except 0x20 already have lifetimes matched.
3. Tag 28 class 0x0c is one drop (2806); its native state stays parked by the capture budget.

Not verified: that adding these owners removes the gaps. That needs a native run, in avp-native.

## Pools (source, unicorn-differential)

Ten pools. Each has a byte count and a word stack of free slot addresses. Alloc pops, release clears a field set and pushes; a record is not cleared on alloc, so a body must set what it reads.

- Tag at +8 is written once at reset (`pools_reset`, 0x1729c) and survives release: release clears the longs at +0, +4 and +0xc, never +8. Player slots have tag 0: that is the source's "is a player" test throughout hit code.
- Order: pool 4 allocates lowest slot first, every other pool highest first (its stack is filled the other way, 0x17326). Retained ledgers agree: first tag 20 row is ffb600.
- A failed alloc is a no-op. Callers branch on it; 218 sites use pool 24. Native code must allow failure: an exhausted pool drops an effect, it does not error.
- Tick order, from 0x849e: tags 4, 8, 12, 16, 20, 24, 28, 36. Tags 32 and the second 0x18 pool (ffe280) are not traversed there.
- Tags 8 and 12 run a pre-dispatch timer: +0x48 counts down, and at zero clears +0x47. Tag 20 clears three per-player words and ff221c first.
- Release can happen inside the traversal, in any order: a slot freed during the tick is reusable by a later body in the same tick, because pop has no delay. That is what makes slot order depend on tick order.

## Spawn table (source, unicorn-differential)

`spawn_table_step`, 0x1be5e. Runs per tick, walks a 16-byte entry table selected by stage word ff81e8. Spawning is camera-driven, entry by entry: all due entries in one tick; a failed alloc holds the cursor and retries next tick. Entry filter: signed byte +0xa against difficulty ff81eb, byte +0xb against player form ff820e. Kinds 0x1c and 0x18 are controls: 0x1c sets ff8218 and calls 0x17a1e, 0x18 calls 0xad580 (from the audio path, not traced here). The other 0x1bf70 path is reached only with ff81c7 set: a debug placement tool driven by the joystick. Not reconstructed.

Consequence: the table is state (camera, difficulty, form, pool room), not a frame schedule, so it fits the rule against capture authority. In the route, 14 source lifetimes join to a table row; every other lifetime was spawned by a body.

## Health writes: most "unowned damage" is not damage (MAME + source)

The scene report's 93 unowned events are by writer:

| Events | Writer | What it is |
| ---: | --- | --- |
| 45 | 0x605aa | Class 0x1f spawn init: health, +42, +44 from one ROM word (0x118a6e) |
| 33 | 0x172ba | Pool wipe at round reset. Not gameplay; value zero |
| 7 + 1 | 0x1b4a4, 0x1b4b6 | `player_energy_drain`, called from weapon end 0x23260 (7 call sites total) |
| 4 | 0x1d5ee | Real hits on the player, `damage_apply` |
| 1 | 0x19706 | Player start, health 0x65 |
| 1 | 0x4bda2 | Class 6 (tag 12) spawn init, table 0x1183ee |
| 1 | 0xbc638 | `pickup_heal`, frame in the route |

Of 93, only 4 are damage. 78 are a wipe or spawn init and 8 are the weapon's own cost. The wider ledger also has other spawn and wipe writers per class (tag 20 bodies 0x6b338..0x6ed7c, 0x17360): a native scene compare should classify init writes apart from hits.

Witness for no clear on alloc: of the 45 class 0x1f inits, 18 replace health -1 and 17 replace 87 left in a reused slot (scene report). The 8 drains cost 6 each. The 4 player hits took 15, 17, 10, 17.

Damage rules are in `damage_apply` (0x1d504):
- Enemy: column = table[attack class*32+difficulty] + attack byte +9, wrapping as a byte. Row = table[armour +0x57*32+difficulty]. Then damage table. ff8244 with class 0x11 quarters; +0x73 halves; both floor at 1 even from 0.
- Player: row comes from the current health, per player table, so damage varies with remaining health. Another player's attack does 1. After damage, 0..5 becomes 0, so a player never holds under 6. Overkill stays -1.
- ff189e nonzero skips it.
- Heal adds a table value, from 5 if at 0, capped 0x65; at full it scores instead through 0xabdd2.

Open: 0x1d622 (hit effect) and 0x1d314, 0x1d492, 0x1d6e2, 0x1d73a are named call targets only. 0x1d622 spawns the 0x4e effects seen above; read, no gate.

## Hitstop survey (source + MAME)

Written at hit: `hit_commit` (0x1cfca and the forms at 0x1d0a8, 0x1d186): defender always gets attack record +0xe; attacker only if its own is zero. Measured values in route 3, 8, 10, 14, 20. Box test 0x1d200 refuses a defender with +0x2c nonzero, so a frozen actor cannot be hit again.

Consumer shapes over reachable code (75 `tst.b +0x2c(a6)` sites, 238 class entries, 52 with sites):

| Shape | Sites | Where |
| ---: | --- | --- |
| Test, decrement, skip dispatch this tick | 48 | most enemy classes; the native `source_hitstop` shape |
| Test, decrement, fall into the body on the tick it reaches 0 | 3 | tag 20 classes 2 (0x6b588), 0xf (0x6ed8a), 0x16 (0x7277e): one tick shorter |
| Test with a wider branch | 15 | same intent by first read; 9 + 3 + 2 + 1, not each traced |
| Other | 9 | three are the attacker test in hit_commit; 0x197fe and 0x1aad0 (player) carry further logic; the rest not traced |

Not hitstop, same offset:
- Class 0x1f in 0x1e9ce: `subq; bpl` countdown to the next phase. Also a read at 0x1e9ea. So in reaction states +0x2c drives the phase. Measured 56 writes.
- Tag 32 class 1 (0x20b60..0x20be4): +0x2c, +0x2d a pair of counters. 270 writes.
- Tag 36 class 3 (0x9a6a6, 0x9a740): word timer. 450 writes.
- Pool release clears the long at +0x2c, so a recycled slot starts with no hitstop.
- Tag 16 class 6 and tag 4 classes 0 and 4 receive attacker hitstop (10 writes) but have no consumer in the class survey. Then their value stays and only blocks being hit; release clears it. Lead, shared low code not excluded.

Per-class list under E:\AvP\learning\actor\field2c_by_class.txt. Assignment by nearest class entry, approximate for shared low code.

## Tag 28 class 0x0e (source, gate for the emit phase)

Entry 0xa726c. `emitter_tick` (0xa7394): while ff822a, ff81f3 and ff8208 are all zero, a word timer at +0x2a counts down; on passing zero it reloads 0x30, so period 49, measured 49 in the probe (frames 3925, 3974, 4023, ...). Spawns tag 24 class 0x10 variant 4 at its own position, then restarts animation. Earlier phases at 0xa72be do a ballistic drop (+0x30/+0x34/+0x38/+0x3c) from table velocities set at 0xbc838, then 0xa73e2 ends and 0xa73fe releases. Those phases are read, not gated.

## Gate notes

`gates/actor.py` uses the optional gate hooks in learn_unit.py, for its own units only: `setup` maps 0xffffxxxx onto RAM (word pointers sign-extend; the board folds them), `OP_READS` overlays pc-relative data read through the opcode space, `after_run` reports a4 as result and ignores d0 at stubs where it is scratch.

Limits of the gate:
- Unicorn does not expose live condition codes, so the Z result of alloc is compared through its callers (spawn, emitter), not directly.
- Domains: difficulty 0..31, health 0..0x65. Outside them the source's byte/word arithmetic is not modelled.
- `pools_reset` assumes stubs 0xae2f4 and 0x1c164 leave d1 zero. Read: both use other registers, ae2f4 only partly read.
- Spawn gate uses real table rows from ROM at run time.
