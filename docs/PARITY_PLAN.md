# Full-game native Alien vs Predator parity plan

Target: a private native Sega Saturn port of the complete US `avspu` arcade
game at **functional parity**. Round 1, "City of Despair", through the Round 2
title is Capability Gate 1: it proves the reusable extraction, semantic-runtime,
Saturn-rendering, audio and validation approach before expansion across the
remaining game. Passing Gate 1 is not full-game completion.

This document supersedes the capture-and-bind method for new work. Read it with
`AGENTS.md` and `docs/AGENT_HANDOFF.md`.

## Naming (read this before any other section)

This project has exactly **two** vocabularies. Everything else in this document
is history.

**Acceptance — what "done" means.** `Capability Gate 1` is the seven-condition
contract, its members written as "Gate 1 condition 3". The full-game goal is nine
conditions, written as "full-game condition 6". **Only these may be called
gates or conditions**, and only they move the 0/7 and 0/9 counts.

**Work — what is being built.** The plan of record is the vertical slice, steps
**S1 to S6**. A step's own pass criteria are **checks**: "S1 check 2", "check C".
A step can pass every check it has without moving Capability Gate 1, because a
step proves a mechanism and a condition requires all of Round 1.

**Retired names.** Earlier orderings are kept only in the historical records
below, under the names they were executed with. Do not plan new work with them.

| Retired name | What it was | Where it went |
|---|---|---|
| Milestones 1-7 | the pre-2026-08-18 execution order | milestone 1 closed, milestone 2 executed-not-closed; the rest replaced by S1-S6 |
| Phases A-E | the first 2026-08-18 re-sequence, superseded the same day | A deferred into S2; B/C became S1-S3; D became S5; E became S6 |
| Slice V | a standalone VDP1 proof | deferred, folded into S2/S3 |
| Phases 0-4 ("technical phases") | the original 2026-08-17 framing | superseded; retained for technical detail only |

If a section below uses a retired name, it is a record of work already done.
Forward-looking instructions use S-steps only.

## Full-game goal-progress index

Audited 2026-08-18 against the full-game destination in
[`GOAL.md`](GOAL.md). A Round 1 or single-actor proof may advance a condition,
but cannot close a global condition.

**Overall: 0 of 9 full-game conditions are closed.**

| # | Full-game condition | Status | Current evidence and remaining work |
|---|---|---|---|
| 1 | Complete content and flow | **OPEN — Gate 1 baseline only** | The current native route covers the frontend and Round 1 through the Round 2 title. Remaining rounds, characters, items, progression, attract flow, endings and credits are not integrated. |
| 2 | ROM-derived animation and presentation | **OPEN — Chrysalis composition slice proven** | One boss composition slice and limited decoders are proven. Complete actor/effect coverage, ROM-driven selection and all-game integration remain open. |
| 3 | Game-derived collision | **OPEN — Round 1 evidence captured** | Debug overlays and selected candidates exist; native collision still consumes inferred schedules and no game-wide collision dataset is integrated. |
| 4 | Translated behavior | **OPEN** | Writer PCs are located, but required player/enemy/boss/object routines and PRNG behavior are not translated across the game. |
| 5 | Extracted stage and game systems | **OPEN** | Round 1 lifecycle is still authored from captures; complete stage, camera, trigger, scoring, HUD and progression tables are not consumed. |
| 6 | Complete native audio | **OPEN — Round 1 subset proven** | Selected Round 1 CDDA/PCM events are captured and integrated. Complete music, voice, event ownership and transition coverage remain open. |
| 7 | All-character single-player validation | **OPEN** | No selectable character has a complete native full-game route through final boss, ending and credits. |
| 8 | Original multiplayer validation | **OPEN** | Full-game joins, HUD/score ownership, camera, spawn, collision and load behavior at the arcade revision's player count are not implemented or validated. |
| 9 | Final physical-hardware release | **OPEN** | Emulator precursors exist. No full-game single-player or multiplayer route has passed on physical NTSC Saturn hardware. |

## Capability Gate 1 progress index

Audited 2026-08-17 against every completion condition in
the former Round 1 charter. These seven technical conditions are retained as
the acceptance contract for Gate 1. Status describes the required Gate 1
implementation, not how much useful groundwork exists. No percentage is used
because a green host model cannot substitute for missing ROM-derived runtime
or physical-hardware proof.

**Gate 1: 0 of 7 conditions are closed.** The existing capture-derived native
route is a valuable regression baseline, not the Gate 1 implementation and not
the full-game destination.

**2026-08-18 collision records (milestone 2) — EXECUTED, NOT CLOSED.** The
actor-local record format is decoded from the game's own routines: selectors are
animation-record bytes `+8` (hurt) and `+9` (attack), the actor's `+0x50`
table-set pointer plus the words at `+0`/`+2` give the hurt and attack table
bases, strides are 8 and 16 bytes, and the test at `0x01D25E` is three axes of
signed centre plus unsigned half-extent with the depth delta projected into the
Y axis. `tools/decode_avsp_collision.py` emits the tracked, deterministic,
coordinate-only `data/avsp_collision.json` (10 trusted families including the
player, street aliens, Stalkers and the boss; 10 more explicitly flagged
suspect). `tools/verify_avsp_collision.py` falsifies it against two bounded
full-work-RAM captures: **21,908 non-overlapping active pairs produced no hit**,
and **44 of 56 hit latches are explained exactly** by an overlapping pair whose
attack record carries the latched value. The 12 residuals are named, not
smoothed: 8 are one simultaneous broadcast at frame 5463, and 4 belong to a
projectile/weapon path this decode does not cover. **Native collision is
deliberately unchanged**: the records are indexed by the live ROM
animation-record pointer at actor `+0x1C`, which the runtime does not yet carry
(pose selection is still capture-derived), so consuming them today would require
hand-mapped per-pose constants — the exact substitution this milestone forbids.
That linkage is **S1/S2** under the slice order below — this milestone
is the reason the order changed. Gate 1 condition 2 stays **OPEN**; Gate 1 stays
**0/7**. See the handoff's "Capability Gate 1 — collision records (milestone 2,
2026-08-18)" section for the routine addresses, SHA-256 evidence and exact
commands.

**2026-08-18 street-alien emission (milestone 1) — CLOSED.** The wrapper /
20-word watchpoints / analyzer are scenario-parameterized (no logic tied to
actor `0xFFA000`, base `0x7080A0`, frame 4253, or the five slots). **Both target
frames reproduce 20/20** from a fresh deterministic run: the alien is located
independently (first run of five `0x4xxx` codes), and on the active/display
bank it occupies exactly the word indices this milestone's exit check names
(80/84/88/92/96) at both frames. Writer attribution from the watchpoint bursts:
X|Y at PC `0x000AA214`, code|attr at PC `0x000AA216`, emitting actor
`A4 = A6 = 0xFF9DC0`, with a **different ROM part-table family per frame**
(`0x12F73C…` at 4214 vs `0x12FECE…` at 4253) — the anti-hardcoding property the
control frame exists to prove. The run is checked against the oracle's own route
capture (`.deps/mame/enemy_actions`): 1 differing work-RAM byte per frame
(a sub-pixel fraction low byte at `0xFF8392`), and the whole 8 KB active object
bank at 4253 byte-identical. The earlier failure this session was an instrument
defect — an off-by-one source-frame label plus an unreplayed post-anchor route
tail (P1 Left 4201–4210, `0xFF83C1 = 0x65` held from 4200) — not a fixture
defect; the fixture's declared state was corrected to its true origin with every
oracle value left byte-identical. **Gate 1 stays 0/7 conditions closed**;
milestone 1 advances conditions 1 and 5 without closing either. One open
metadata defect is recorded in the handoff: actor records are `0xC0` apart and
the fixture's `actor_base` `0xFFA000` is a valid street-alien actor but **not
the one that emits the target slots** — the emitter is `0xFF9DC0`, by watchpoint
`A4`/`A6` and by sprite-versus-worldX motion with the camera provably static
between the two frames. Committed at `40e7f76`. See the handoff's "Capability
Gate 1 — street-alien emission (2026-08-18 execution)" section for SHA-256
evidence and the exact reproduction command.

| # | Gate 1 condition | Status | Current evidence and remaining work |
|---|---|---|---|
| 1 | Animation from ROM scripts at runtime | **OPEN — Chrysalis tile-composition slice proven** | For the Chrysalis boss the runtime now composes all 29 of its poses from ROM-referenced 4bpp tiles (`compose_boss_rom_pose` in `main.c`, `generated/avsp_boss_rom.h`), and the boss's `BACT`/`BHIT`/`BKO` pose archives are no longer loaded for animation (they remain on disc only as host-test regression oracles). This is a composition slice, not full ROM animation: pose *selection* still uses the capture-derived per-frame clip/step tables (`boss_pose_for_frame`, `generated/avsp_boss_animation.h`), and the ROM selector-6 / control-word script interpreter is decoded host-side only, not yet linked into the runtime. The 29-pose / 28-assembly composition check passes 28/28 with 0 differing pixels, the focused KO/HIT builds and the full controller route through Round 2 all render on Yaba Sanshiro without an asset error, and a clean normal release boots to title. **Remaining:** link the ROM script interpreter for pose selection, and decode the player/street-aliens/Stalker programs to route them through the same tile-composition path (retiring their `/SPR4/*.RLE` archives), before this condition is closed. |
| 2 | Collision from the game's hitboxes | **OPEN — record format decoded and falsified; runtime unchanged** | The game's own routines give the format: selectors at animation-record `+8`/`+9`, table bases from actor `+0x50` words `+0`/`+2`, strides 8 and 16, and a three-axis centre/half-extent test at `0x01D25E` with the depth delta projected into Y. `data/avsp_collision.json` holds 10 trusted family table-sets (player, street aliens, Stalkers, boss) decoded deterministically, with 10 further families explicitly flagged suspect rather than invented. The controlled falsification passes: 21,908 non-overlapping active pairs produced no hit and 44/56 hit latches are explained exactly, with the 12 residuals named (one simultaneous broadcast, and a projectile/weapon path that is not decoded). Native collision still uses scalar range/lane checks and the inferred Chrysalis 21/55/97 and Stalker schedules, deliberately: the records are indexed by the live ROM animation-record pointer the runtime does not yet carry, so consuming them now would mean hand-mapped per-pose constants. **Remaining:** phase B must link ROM animation records into the runtime; then decode the projectile path, resolve the broadcast path and the attack-table lengths, and replace the inferred schedules. |
| 3 | Enemy behaviour from translated 68000 routines | **OPEN** | Stock watchpoints located animation/action/state writers. `cap_update_enemy()` remains hand-authored, no required AI path is translated, and PRNG use is not identified or recorded. |
| 4 | Spawns, camera and triggers from stage tables | **OPEN** | The current lifecycle, waves, camera and room transitions are capture-derived constants and authored C. Round 1 stage tables have not been located, extracted or consumed by the runtime. |
| 5 | Pixel and event-level validation | **OPEN — pixel groundwork proven** | The format-isolating pose check passes 28/28 (29 oracle poses) with zero differing pixels using captured screen geometry, in both default and self-contained modes. The independent position audit has a scoped pass on 408/408 geometry frames: 1,435/1,443 parts directly exact, 0 at sibling-origin deltas (the shared-code-set ambiguity is resolved by the actor-slot record pointer at frame f−1), 8 at a formally bounded `y=-4` whole-pose settle trail (the only non-zero residual in the scope; the one-step trail's exact writer is not yet disassembled), 0 frames unmatched, X 1,443/1,443 exact. Because the pose check requires every listed assembly to 0-diff an oracle, only the 28 assemblies with a captured-pose oracle are listed; the 5 decoded mid-attack/at-rest trace assemblies are excluded and reported in `excluded_no_oracle_assemblies`, not pixel-verifiable. A MAME-vs-native event parity harness is still missing. |
| 6 | Existing regressions still pass | **BASELINE GREEN; FINAL RE-RUN OPEN** | The current host model reaches Round 2 in 4,485 frames and its 12,000-frame deterministic soak passes; prior Yaba diagnostics exercised captured clips. These must pass again after ROM-derived animation, collision, stage and AI replacement, followed by a clean normal-release boot. |
| 7 | Physical NTSC Saturn at sustained 60 Hz | **OPEN** | Emulator precursor and image/hash evidence exist. No physical NTSC Saturn route, audible full-level proof, sustained-60-Hz measurement, or ten-minute hardware soak is recorded. The final candidate must be a clean `release-normal-release` build with a digital pad and 32 Mbit cartridge. |

The volatile evidence, exact commands, hashes, current HEAD and immediate work
queue stay in [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md); this table is the concise
Gate 1 index.

## Master execution plan (2026-08-18)

This is the current Capability Gate 1 order of work. It supersedes older resume
lists in the handoff and refines the broad phases below. The order was rebuilt
around the actor spine on 2026-08-18; the rationale and the current step table
follow. **Milestone 1 is closed
(2026-08-18); the first body assigned to the next agent is milestone 2 only.**

### Decisions taken this session (2026-08-18), binding going forward

1. **The plan is a vertical slice, not a system sweep.** The target is the Room 1
   fight, and the order is S1-S6 below. Systems are built in the order the slice
   needs them, so every piece of decoded data acquires a runtime consumer in the
   same step that decodes it.
2. **Do not decode a ROM table without a consumer.** Milestone 2 produced correct,
   falsified, unusable collision records. That is the failure mode this ordering
   exists to prevent.
3. **There is no Saturn AvP.** MAME's CPS2 `avspu` is the fidelity oracle for
   every parity claim, permanently.
4. **From the reference lane, take the representation and reject the granularity.**
   16-colour bank mode, flip in `CMDCTRL`, jump-next linked list and source order
   as draw order transfer directly, because both games are CPS2. One command per
   16x16 tile does not: 83.6% of AvP's objects are blocked sprites averaging 8.51
   tiles, so AvP emits **one VDP1 normal sprite per CPS2 object** - 86 commands at
   peak instead of 909. Per-tile is the fallback if per-object misses 60 Hz.
5. **The renderer measurement was deferred, not skipped.** The shipped build
   already draws more VDP1 sprite fill than the candidate pipeline needs, so the
   spine went first; frame time is measured in S2 where the producer is real.
6. **Game logic is translated statically, per routine, validated differentially** -
   see "How game logic gets translated". The actor record mirrors the game's own
   `0xC0` layout precisely so translated routines need no field shims.
7. **"Gate" means Capability Gate 1 only.** See Terminology.

Rough effort to a playable, faithful slice: **8-14 sessions**, with S5 (enemy
decisions and PRNG) the item most likely to overrun. That is an estimate, not a
commitment.

### Why this order changed (2026-08-18 re-sequence)

The previous order ran emission → collision → animation → stage → AI. Executing
it exposed a **dependency inversion**: milestone 2 decoded the collision record
format and falsified it successfully, then could not integrate, because the
records are indexed by the live ROM animation-record pointer at actor `+0x1C`
and **no actor in the native runtime carries one**. Stage triggers and enemy AI
read actor fields through the same record. Four of five remaining milestones were
therefore queued behind one missing abstraction.

The reason the runtime has no record pointer is architectural. Its unit of work
is a *precomposed pose picture*: `main.c` builds 288x192 cels and hands them to
`jo_sprite_add_4bits_image`, with pose selection from capture-derived tables and
collision from scalar lane tests in `capability_model.c`. ROM assemblies have no
runtime consumer, so nothing forces an actor to carry its record.

So the order below is rebuilt around **one spine — an actor that carries its ROM
record — and the renderer question that decides whether that spine is
affordable**. Decoding further ROM tables before that spine exists produces
correct evidence that cannot be consumed, which is what milestone 2 demonstrated.

The seven Gate 1 acceptance conditions are **unchanged**; only the execution
order and its exit checks are. Each step below has checks that can independently
go green, so progress is visible long before Capability Gate 1 closes.

### Terminology (binding on all documents and code in this repository)

**"Gate" means Capability Gate 1 and nothing else.** It is the seven-condition
acceptance contract in the index above, and the only thing in this project that
may be called a gate. Do not write "pose gate", "format gate", "coverage gate",
"exit gate", "hardware gate" or "the gate": every one of those was in use at
once, and a status line could read "the gate passes" while Capability Gate 1 sat
at 0/7.

Everything else is a **check** - a named pass criterion belonging to a step,
written as "S1 check 2" or "check C". Checks can go green individually; that is
the point of them, and it is why a green check must never be reported as gate
progress.

Two consequences worth stating outright:

- **Physical-hardware validation is not a separate gate.** It is Capability
  Gate 1 condition 7 and full-game condition 9. Call it by its condition number.
- **A closed step is not a closed condition.** S1 and S2 can pass every check
  they have while Capability Gate 1 stays 0/7, because a step proves a mechanism
  and a condition requires Round 1.

The one exception, and it is not ours: the isolated MSHvSF research lane has its
own "promotion gate" governing what may cross into AvP. Quote that term as the
research lane's, never as a gate of this project.

**Vertical-slice target: the Room 1 fight.** The player walks right from the
Round 1 start, meets the first street-alien wave, fights it, and the wave clears
- on real Saturn at 60 Hz, with animation, collision, damage and enemy decisions
all ROM-derived. *Faithful* means: same initial state and same inputs produce
the same state trajectory as MAME at the event level - per-frame animation
record pointer, hit events, health deltas, action/state transitions. Not pixel
equality, not cycle timing. The window is deliberately the one with the densest
existing evidence, `.deps/mame/enemy_actions` frames 4080-6200, so every layer
below has an oracle already on disk.

| Order | Step | Required work | Exit checks | Oracle |
|---|---|---|---|---|
| **S1** | **Actor spine** — PASSED 2026-08-18 | A native actor record mirroring the game's `0xC0` layout for the fields its own code consumes; port the collision overlap predicate and guards into C over that record | Field-for-field equality against 2,900 captured work-RAM frames, **and** the C predicate reproduces the Python falsification exactly (21,908 non-overlapping active pairs with no hit, 44/56 latches explained, same 12 residuals) | `.deps/mame/collision_probe*` |
| **S2** | **Animation from ROM scripts, and the renderer** (active: interpreter + record extraction validated; spine linked into the Saturn build; object-word formula CONFIRMED and coded in C with a passing host test (3/5 parts exact); origin routine `bsr $0AA59A` fully disassembled (also the source of the D1 flip mask - the actor's own facing byte); general part-table walk still open, header/count/skip mechanism unresolved after a systematic search; no live actor in `main.c` yet; VDP1 per-object renderer not started) | Link `avsp_anim_script.c` into the Saturn build; drive pose selection from the record pointer at `+0x1C` instead of the capture-derived clip tables; emit the object list and render it per CPS2 object (slice-V design, retained above) | The native walk reproduces MAME's exact per-frame animation-record-pointer sequence across the 2,121-frame street fight, and the produced object list matches MAME's captured active object list frame for frame | 5,302-frame object-list oracle |
| S3 | Widen to Round 1's cast | Player, remaining street aliens, Stalkers and Chrysalis onto the same spine; `/SPR4/*.RLE` archives demoted to regression oracles | Every slice actor selects poses and emits objects from ROM data; no capture-derived pose table in a runtime decision | same |
| S4 | Collision, damage, reaction | Consume the decoded boxes at runtime; decode the five post-hit routines at `0x1D314`, `0x1D504`, `0x1D492`, `0x1D622`, `0x1D6E2`; retire the inferred Chrysalis 21/55/97 and Stalker schedules | Every hit event and health delta in the slice window matches MAME; no inferred contact schedule remains in a runtime decision | recorded contacts |
| S5 | Enemy decisions | Identify the PRNG generator and call order, then translate the street-alien decision routines by the differential-replay method in "How game logic gets translated" | Same initial state and inputs produce the same action/state sequence as MAME, with a negative control that fails on a perturbed input | recorded calls |
| S6 | Integrate and run on hardware | Seed the wave from the captured initial state (an `ADAPTED` shortcut, labelled; stage-table decode is post-slice); re-measure resources; run host, soak, focused, full-route, clean normal release | 60 Hz on physical NTSC Saturn with a digital pad and 32 Mbit cartridge, and a deterministic replay matching the MAME event log | `docs/HARDWARE_TEST.md` |

The slice is **not** Capability Gate 1. It is one room, one enemy family, no
stage tables, no boss, no audio work. It exists to prove the method end to end
so that widening becomes mechanical. Gate 1 stays 0/7 until Round 1 itself
passes its seven acceptance conditions, and the full-game goal stays 0/9.

Post-slice, the earlier phase lettering still describes the widening work:
see the naming map at the top of this document for how the retired phase
letters map onto the S-steps.

**Rule carried out of milestone 2:** do not decode another ROM table in
isolation while S1 or S2 is open. Evidence that has no runtime consumer is
not progress toward Capability Gate 1, however well falsified it is.

### How game logic gets translated (method for S5, constrains S1)

The goal forbids shipping a 68000 interpreter, and hand-authored approximations
are the problem the project is trying to leave behind. The method is **static
translation, routine by routine, validated differentially**:

1. **Mirror the actor layout first (S1).** Translated routines read and
   write the game's actor fields. If the native actor struct mirrors the ROM's
   `0xC0` record — the fields already mapped: `+0x08` type, `+0x0F` facing,
   `+0x10/+0x14/+0x18` world x/y/z, `+0x1C` animation record, `+0x2C/+0x2D` hit
   value and source, `+0x50` collision table set, `+0x67` attacker id, `+0x68`
   per-attacker latch, `+0x70` suppress, `+0xD1` latch index — then translation
   is near-mechanical. If it does not, every routine needs a hand-written field
   shim, and the shims become the new inferred layer. **This is a phase-B design
   constraint, decided now rather than discovered in S5.**
2. **Both machines are big-endian.** 68000 and SH-2 share byte order, which
   removes an entire class of translation bugs; word and long reads of the same
   structures port directly.
3. **Translate per routine, not per program.** Disassemble the routine (capstone
   is already vendored under `.deps/capstone`), build its control-flow graph,
   enumerate computed-jump targets from the ROM jump tables rather than guessing,
   and emit C. Model the 68000 condition codes explicitly **only where a flag is
   consumed across instructions** — carrying a full CCR everywhere produces
   unreadable, slow code.
4. **Identify the PRNG generator and its call order before translating any AI.**
   Enemy decisions depend on it; a correct routine fed a different random stream
   diverges immediately and looks like a translation bug.
5. **Validate differentially, the same way collision was falsified.** Put stock
   MAME watchpoints on the routine's entry and on every field it writes, record
   thousands of real calls as (input actor state + RNG state) -> (every write),
   then require the translated C to reproduce every write for every recorded
   call. A routine is accepted only when its recorded-call replay is exact, with
   a negative control that fails when an input is perturbed.

This keeps translated behaviour honest without an emulator, and it produces
maintainable C rather than an opaque transliteration. It is also why S1's
struct decision cannot be deferred.

### Sprite demand measurement (2026-08-18, MEASURED)

AvP and the official Capcom Saturn reference title run on **the same arcade
hardware**, so the source primitive is identical and only the volume differs.
That makes the demand half of the phase-A question answerable from AvP's own
captures, with no Saturn code: the CPS2 active object list *is* the tile list.

`tools/measure_avsp_sprite_demand.py` over **5,302 captured frames** (street
wave, Stalkers, Chrysalis boss), decoding fields exactly as MAME 0.289
`cps2_render_sprites` does:

| Measure | Peak | Mean |
|---|---|---|
| objects per frame | 86 | 40.7 |
| **16x16 tiles per frame** | **909** | 346.3 |
| **distinct 16-colour palettes live per frame** | **13** | 6.5 |
| distinct tile codes per frame | 547 | 251.9 |
| largest single object | 55 tiles | — |

**Object block-size distribution (the finding that splits the hypothesis).**
Across 215,646 captured objects: **83.6% are blocked sprites**, averaging
**8.51 tiles each**; only 16.4% are 1x1. Peak frames hold 86 objects / 909
tiles. So the rendering granularity choice is worth roughly **10x**:

| Granularity | Commands at peak | Note |
|---|---|---|
| one command per 16x16 tile | **909** | the shape measured on the reference title |
| **one command per CPS2 object** | **86** | one source object entry -> one VDP1 normal sprite of `nx*16 x ny*16` |

Per-object is also the *more* faithful mapping: the CPS2 object entry is the
hardware's own unit, and a blocked sprite is one entry. VDP1 normal sprites
reach 504x255 and AvP's largest object is 55 tiles, so every AvP object fits one
command. The cost is that a block must be contiguous in VDP1 VRAM as an
`nx*16`-wide texture, which needs a per-block texture cache rather than a raw
tile upload.

**This is why the reference title's granularity is not copied.** Its measured
"every drawn command is a 16x16 normal sprite" is most likely a consequence of a
two-character fighter's object list being dominated by 1x1 entries, not a
deliberate expansion — but that is `UNRESOLVED` and does not matter, because AvP
follows AvP's object list. The *representation* half of the reference finding
(16-colour bank mode, flip in `CMDCTRL`, jump-next linked list, source order as
draw order) transfers directly; the *granularity* half does not.

Two consequences:

- **Colour RAM is not the constraint.** The risk that killed a per-tile pipeline
  was colour-RAM pressure. AvP needs at most **13** live 16-colour banks in a
  frame. Saturn CRAM holds 2,048 entries in 5:5:5 mode 1 — 128 such banks. AvP
  asks for roughly a tenth of that, and its worst measured frame still fits the
  64-bank mode 0 layout many times over. The current eight-bank allocation was
  sized for precomposed per-palette cels and is the thing that is actually tight.
- **The open question is throughput at a granularity we choose, not
  representation.** Sprite fill is the same either way — ~233k pixels at peak,
  since the same pixels are drawn — but command count differs 10x (86 versus
  909), and command-table reads plus per-command SH-2 build cost scale with
  command count. Per-object at 86 commands is below the reference title's
  measured 296-334, which is encouraging but is not an AvP measurement.

**Status: the renderer question is half-answered.** The demand side is `MEASURED`; the Saturn
throughput side is `UNRESOLVED`. Its probe is slice V below, which emits
**per-object** commands with per-tile retained as the fallback, and measures real
frame time at the 909-tile / 86-object peak frame (source frame 5776).

### Slice V — DEFERRED, folded into S2/S3 (decided 2026-08-18)

Slice V was going to run first, as a throwaway replay harness, to de-risk VDP1
throughput before the actor spine was designed. It was **deferred** on review,
because the risk it was buying down is already largely refuted by evidence in
hand:

- **The shipped build already sustains more VDP1 sprite fill than the candidate
  pipeline needs.** `main.c` draws 192x192 cels (36,864 px each) for the player
  layers plus up to `CAP_MAX_ENEMIES` enemy slots plus a 288x192 boss - on the
  order of 400k px of sprite fill per frame - and it reaches the Round 2 title
  on Saturn. A per-object pipeline draws ~233k px at its peak frame. **Fewer.**
- **Command count is not the risk it looked like.** Today's build issues on the
  order of ten sprite commands per frame; per-object peaks at 86. The shipped
  reference port issues 296-334 reachable commands per anchor. 86 is not where
  this breaks.
- **Every other budget has ~10x headroom:** 13 live palettes against 128 CRAM
  banks, 29.5 KB peak texture delta against a vblank DMA window.
- **The spine is not coupled to the answer.** An earlier framing overstated
  this. Whatever the spine produces is *a CPS2 object list*; whether the renderer
  consumes that list per-object or per-tile is a local decision downstream of it.
  Building the spine first therefore risks nothing.

The decisive practical point: as a standalone slice, V needs a replay harness
that is thrown away. Run the same work inside **S2**, where the runtime can
*produce* an object list instead of replaying one, and the harness becomes the
real path - and the 5,302-frame object-list oracle becomes meaningful, because
the producer is finally real.

**What is retained from the slice-V design**, for whoever does S2/S3: one VDP1
normal-sprite command per CPS2 object (`nx*16 x ny*16`, 16-colour bank mode,
flip in `CMDCTRL`, jump-next linked, source order as draw order), a per-block
texture cache with cartridge residency and per-frame delta DMA, per-tile
retained as the fallback, and the coverage check that every object shape and flag
combination in the 215,646 captured objects maps to a legal command. Frame time
still binds on physical Saturn, not an emulator.

### Slice V design detail (retained for S2/S3)

The renderer's producer and consumer are separable, so the consumer can be built
and measured now, with no actor spine, no collision and no AI.

- **Producer (harness only, never shipped):** replay captured CPS2 object lists
  frame by frame. S2 swaps this for the ROM-driven actor spine; the consumer
  does not change.
- **Consumer (real, permanent):** one VDP1 normal-sprite command per CPS2 object,
  `nx*16 x ny*16`, 16-colour bank mode, flip in `CMDCTRL`, jump-next linked, list
  order preserved as draw order.
- **Textures:** per-block cache built from ROM tiles, cartridge-resident, with the
  per-frame delta DMA'd in (measured: 5.7 KB mean, 15.2 KB p95, 29.5 KB peak).
- **Palettes:** the <=13 live 16-colour banks into VDP2 CRAM.

Gates: (1) **coverage** - every object shape and flag combination in the 215,646
captured objects maps to a legal VDP1 command, with unhandled cases enumerated;
(2) on Saturn, the peak frame holds 60 Hz with measured frame time; (3) the peak
texture delta lands inside vblank. If (2) fails at per-object, fall back to
per-tile and re-measure before redesigning anything upstream; report both command
counts either way.

Note what check (1) is **not**. When the producer replays MAME's own object list,
comparing the emitted list back to that list is close to vacuous. The
5,302-frame object-list oracle is **S2's** check, where the ROM-driven
producer must generate the list itself. Slice V's real result is the hardware
frame time, and emulator frame time is indicative only - gate (2) binds on
physical Saturn per `docs/HARDWARE_TEST.md`, or an FPGA core as a closer proxy
that is still not the physical-hardware condition.

**There is no Saturn Alien vs Predator to measure against. That is the project.**
Capcom never shipped one; this port is the first. So no phase above may be
gated on "matching the Saturn version", and no agent should go looking for an
AvP Saturn reference, disc, or memory dump — none exists. Two consequences:

- **The fidelity oracle is MAME's CPS2 `avspu`**, always. Every parity claim
  compares native Saturn behaviour to arcade behaviour under identical input.
- **The only official CPS2-to-Saturn port available is a different game**
  (MSHvSF, in the isolated research lane). It can teach *method* — how Capcom
  solved a CPS2-to-Saturn problem once — but it is not a specification, its
  numbers are not AvP budgets, and its rendering choice is a hypothesis AvP must
  test on its own content. AvP's cast, sprite sizes, palette count and
  scrolling-beat'em-up load differ from a two-character fighter's, and phase A
  exists precisely because that difference could flip the answer.

### Full-game continuation after Capability Gate 1

Gate 1 establishes reusable systems; it does not authorize stage-specific
hardcoding as the expansion method. Continue in this order:

| Program phase | Required work | Exit checks |
|---|---|---|
| A. Whole-game inventory and generalization | Inventory all animation programs, actors, hitboxes, stages, routines, items, weapons and audio events in `avspu`; generalize the proven extractors and semantic interfaces beyond Round 1 | Every remaining content family has an owner, source range, extractor/translator path, validation oracle and Saturn budget class |
| B. Remaining-round integration | Integrate each remaining round in arcade order using extracted tables and translated routines; run the cumulative title-to-current-endpoint route after every round | Every round passes animation, collision, behavior, stage, audio, transition and resource-lifetime checks without route-specific runtime fallbacks |
| C. Complete single-player | Complete the full route with every selectable character, including items, continues, final boss, ending and credits | All-character deterministic MAME/native event comparisons have no unexplained divergence and the clean normal release completes every route |
| D. Original multiplayer | Add the arcade revision's simultaneous-player capability after single-player is green; implement joins, HUD/score ownership, camera, spawns, collision, items and transitions | A maximum-player complete route passes deterministic, stress, emulator and physical-controller tests |
| E. Final hardware candidate | Measure peak CPU, VDP1/VDP2, RAM, cartridge, SCSP, DMA and CD/CDDA behavior across the complete game; restore a clean release | Required single-player and multiplayer routes pass at sustained 60 Hz on physical NTSC Saturn with digital pads, multitap and 32 Mbit cartridge |

### Immediate evidence contract

The ready-to-invoke, implementation-level contract is
[`NEXT_AGENT_PROMPT.md`](NEXT_AGENT_PROMPT.md). It now contains **the
integration half of S2 only** and does not authorize S3 or any later step.

Completed under the previous order, and still valid as evidence:

- Milestone 1's object-emission proof is closed at `40e7f76`, with corrected
  actor attribution at `4695dee`.
- Milestone 2's collision-record decode and falsification is at `35d2d4d`. Its
  records are correct and unconsumed; phase B is where they become live.

### Evidence labelling (adopted 2026-08-18)

New AvP artifacts carry one label per asserted field, the discipline taken from
the reference lane's `reference_engine/evidence.py`:

| Label | Meaning | Requirement |
|---|---|---|
| `MEASURED` | read from an instrument, or computed losslessly from such a reading | must name its source |
| `DECODED` | produced by a validated decoder over private source data into a tracked artifact | must name its source |
| `INFERRED` | a hypothesis consistent with evidence, not yet falsified | **must name what would falsify it** |
| `ADAPTED` | a deliberate choice by this port, not a claim about the original | must say why |
| `UNRESOLVED` | named, required, not known | **must name the probe that resolves it** |

`UNRESOLVED` is the only label allowed to carry no value. This exists because
two consecutive sessions lost time to unlabelled metadata that turned out to be
wrong (a fixture's declared capture state, and an actor base that was a
bystander), in both cases discovered only when a downstream result failed.
Milestone 2 begins from the existing cadence-1 debug-hitbox capture, tracked
screen-space/pivot candidates, animation-record interaction selectors, and
reader routines at `0x1CF94`/`0x1CF88`. Those are leads, not native collision
tables. The next agent must prove actor attribution and the ROM table format,
validate controlled hit and whiff routes, then replace the inferred Chrysalis
21/55/97 and Stalker contact schedules with game-derived actor-local boxes.

Do not change native collision from overlay geometry alone. If ROM/table
provenance or a falsification control remains open, retain the current runtime,
record the precise blocker, and leave milestone 2 open.

### CPS2-to-Saturn representation boundary

The Saturn runtime does **not** need to copy the CPS2 `0x708000` buffer, raw
four-word descriptor, 10-bit packing, or bank flip. Those are the source
machine's renderer contract and a high-value extraction oracle. Normalize each
proven entry into semantic fields—screen position, tile/code identity, palette,
size, flip, priority, order, and lifetime—then let native SH-2 code emit the
equivalent VDP1/VDP2 representation. Reproducing the CPS2 encoding literally
would confuse source evidence with the Saturn implementation.

### Applicable MSHvSF research findings

The isolated research lane remains `codex/mshvsf-reference-lane` at checkpoint
`43e88ac`. It is a method/evidence source, not an implementation dependency.

#### One discovery program, two Git lanes

Marvel research is folded into the **AvP discovery plan**, but its branch is
not folded into the AvP implementation history. Treat the work as one program
with two governed lanes:

| Lane | Branch ownership | Purpose | Scheduling rule |
|---|---|---|---|
| AvP production discovery | Continue from `codex/avp-master-plan` (master-plan root `e37ab9f`) until its changes are deliberately promoted to `prototype/private-capability-test` | Build the complete AvP port, with Round 1 as Capability Gate 1 | Always owns the critical path; current phase A remains first |
| MSHvSF official-port reference | `codex/mshvsf-reference-lane` (`dc5d3ea`) | Answer a named Saturn architecture or historical-fidelity question | Run only when it informs an upcoming AvP decision, or while AvP is independently blocked; open-ended fighter archaeology is not an AvP task |

The Marvel lane may create evidence, analyzers, templates and candidate
patterns. It may not directly change AvP runtime code, close an AvP goal
condition or establish an AvP hardware budget. These activation rules repeat
at equivalent design forks in later rounds; open-ended Marvel archaeology never
becomes a prerequisite for full-game content extraction.

#### When Marvel research should be activated

Marvel is most valuable at a **Saturn design fork**, not during every CPS2
decode. Activate it only when the result can choose or reject an AvP target-side
design within the next milestone.

| AvP point | Saturn decision Marvel can inform | Required Marvel investigation | How AvP uses the result |
|---|---|---|---|
| Renderer granularity (**deferred into S2**) | Precomposed cels versus one 16x16 VDP1 command per source tile; palette/flip/order representation; what stays resident in expansion RAM | Already delivered at `dc5d3ea`: every reachable command at four anchors is a 16x16 normal sprite in colour-bank mode, jump-next linked, flip in `CMDCTRL` | Recorded in the handoff as an `INFERRED` hypothesis with its falsifier. AvP must measure its own two pipelines and may legitimately reach the opposite answer; Marvel's counts are not AvP budgets |
| Phase B/C: actor spine and collision | Whether gameplay collision state is kept separate from presentation objects in the official Saturn port | Only investigate when Saturn actor/collision RAM fields and writer paths can be traced around a controlled hit and whiff | Use it as a candidate architecture pattern; AvP still consumes its own ROM-derived boxes and proves its own hit/whiff behavior |
| (superseded by phase A) animation extraction | Precomposed cels versus per-part VDP1 commands; palette/flip/order representation; what stays resident in expansion RAM | Capture Marvel VDP1 command tables, VDP1 VRAM, work RAM, and cartridge RAM at idle, normal startup/active/recovery, hit reaction, and character transition anchors | Compare the official port's measured command/VRAM/residency tradeoff with both AvP renderer prototypes; choose only after AvP measurements agree |
| Phase D: stage reconstruction, after AvP stage ownership is known | VDP2 layer division, background package boundaries, phase loading, and whether CD reads overlap music | Trace Marvel VDP2 registers/VRAM, file reads, DMA, and CDDA commands across stage entry and a stage/mode transition | Design AvP's background ownership and load windows, then validate against AvP's longer scrolling Round 1 route |
| Phase D: AI translation | Little direct value; fighter AI/object logic is not AvP enemy logic | Do not use Marvel as a shortcut for AvP AI or PRNG recovery | Translate AvP's own 68000 paths and RNG call order |
| Phase E: Saturn integration and budgeting | 4 MB cartridge layout/lifetimes, internal-RAM roles, master/slave SH-2 division, DMA/CD scheduling, SCSP/CDDA split | Add deterministic state dumps and access traces at boot, character load, normal hit, tag/super stress, audio event, and transition anchors | Turn measured official-port behavior into candidate constraints, then fill the AvP high-water/lifetime ledger with AvP measurements |
| Phase E: validation and release | Which differences are necessary platform adaptations versus avoidable reductions; what stress scene exposes the real limit | Complete Marvel gameplay/animation/audio/performance difference records and a tag/super worst-case run; validate any proposed general pattern on a second official port before calling it a Capcom standard | Classify AvP deviations honestly; an official compromise is precedent, not automatic permission |

The next useful Marvel package is therefore **not Hadouken by default**. The
normal-hit route already supplies the behavioral anchors needed to instrument
actor state, VDP1, memory residency, and damage/reaction. Add Hadouken only
when AvP reaches a projectile/effect decision requiring projectile allocation,
collision lifetime, VDP1 effect pressure, or audio-event routing. For worst-case
Saturn capacity, a tag/super scene is more informative than Hadouken.

Marvel research priority for AvP is:

1. deterministic dumps of work RAM, both cartridge banks, VDP1/VDP2, and SH-2
   state at the existing normal-hit anchors;
2. CD read, DMA, CDDA, and SCSP ownership across character load and one audio
   event;
3. VDP1 command/VRAM and CPU pressure during a tag/super stress route;
4. Hadouken/projectile mapping only when the AvP projectile/effect design needs
   that evidence;
5. second-title confirmation before promoting a Marvel-specific observation to
   a general Capcom Saturn rule.

#### Promotion procedure

A Marvel result enters AvP only through this sequence:

```text
Marvel claim and evidence
  -> falsification and confidence recorded on the Marvel branch
  -> explicit AvP question and probe added to this plan
  -> probe executed with AvP inputs on an AvP branch
  -> copyright-safe AvP result committed as a small AvP-specific change
```

Do not merge `codex/mshvsf-reference-lane` into an AvP branch and do not
cherry-pick its broad research-package commits. If a reusable tool is needed,
copy or reimplement only the minimal generic portion in a dedicated AvP commit,
record its Marvel source checkpoint, and validate it against AvP data. Never
transfer ROMs, extracted members, raw captures, generated copyrighted assets,
fighter constants, or unverified architecture assumptions.

#### Repository safety for lane changes

Before any branch switch, staging operation, or commit:

1. Run `git status --short --branch`, `git branch --show-current`, and
   `git rev-parse HEAD`.
2. Do not switch lanes with uncommitted tracked work unless that work has been
   identified, preserved, and intentionally carried. Never reset, delete,
   clean, or stash unknown user files merely to make the tree look clean.
3. Stage explicit paths only. The untracked `Marvel Super Heroes vs. Street
   Fighter/`, `nvram/`, `snap/`, `check_tail.py`, and one-off `tools/diag_*`,
   `tools/probe_*`, and screenshot helpers are not bulk-add targets.
4. A commit must belong to exactly one lane. Its message and handoff entry must
   state the lane, source checkpoint, evidence produced, and remaining work.
5. For truly concurrent work, use a separate worktree or task for the Marvel
   lane; do not alternate branches in a dirty checkout. Private inputs remain
   private and must not be duplicated into Git to make a worktree convenient.

Every status update must distinguish: **proven on Marvel**, **validated on
AvP**, **candidate transfer**, and **unresolved**. Only “validated on AvP” may
change the AvP implementation or goal-progress table.

Apply now:

- require an explicit source address/data/function, output sink, test,
  falsification, confidence, and uncertainty for the street-alien mapping;
- keep gameplay/animation semantics separate from CPS2 and Saturn machine
  representation—the wrong-sink `0x0169da` tilemap comparison is the concrete
  AvP example of why this matters;
- use deterministic semantic anchors and negative controls before promoting a
  decoder or reusable pattern.

Apply at milestones 6–7:

- add per-resource AvP high-water and lifetime measurements for work RAM,
  both 4 MB cartridge banks, VDP1 VRAM/commands, VDP2 VRAM, SCSP RAM, DMA, and
  CD access;
- build a media/runtime ownership table and one normal-hit event fixture that
  separates input, movement, collision, damage, reaction, and recovery;
- record every accepted Saturn difference in the classification ledger with a
  falsification test instead of treating an official-port compromise as
  automatic permission for AvP.

Do not import MSHvSF gameplay timing, addresses, package sizes, module formats,
or inferred hardware ownership. The MSHvSF Hadouken path, dynamic Saturn
ownership trace, and second-title validation remain useful research-lane work,
but none blocks AvP milestone 1.

## Why the method changes

The project reached a playable Round 1 by capturing finished frames off the
screen with deterministic MAME runs and binding those clips to a hand-written
native state machine. That method has a ceiling, and the project is at it:

- It cannot produce what was never observed. Any animation, enemy reaction, or
  AI branch that did not happen during a capture is simply absent.
- It does not scale. Every new actor or action needs its own capture, analyzer,
  archive, and slice of a 4 MB cartridge budget that already closes only
  through phase overlays. The player's eight clips alone cost 417,488 bytes.
- It cannot reach AI at all. Behaviour cannot be enumerated by observation.

Two facts make the alternative strictly better:

1. **The graphics are already solved.** The project reconstructs the full
   16 MiB CPS2 graphics region byte-for-byte, verified against MAME's `:gfx`.
   Every tile of every animation is already in hand. Screen capture was only
   ever re-deriving the *assembly instructions*.
2. **The instructions are in the ROM, and we found them.** See below.

Table extraction covers every actor and action at once, and shrinks with
coverage because poses share tiles.

## What parity means here

Functional parity, defined so it can be tested:

- Given the same initial state and the same input sequence, the native build
  reproduces the arcade's **actor state trajectory**: position, animation
  script position, health, timers and state transitions, within a stated
  tolerance, for the complete game. Gate 1 applies the same standard to Round
  1 through the Round 2 title.
- Collisions use the game's real hitboxes, not inferred windows.
- Animations play the ROM's real frame sequences and durations.

Explicitly **not** required: identical framebuffers, identical RNG streams, or
identical sub-pixel rounding. If AI consumes a PRNG, behaviour matches only for
the same generator and call order, so identify RNG use before translating AI
and record the decision.

## Established facts

Verified in this repository; do not re-derive.

**Memory**

- CPS2 work RAM is `0xFF0000..0xFFFFEF`.
- The actor array has a **0xC0 (192-byte) stride**. Known boss-room actors sit
  at `0xFFA240`, `0xFFA300`, `0xFFA3C0`.
- Player health is at `0xFF83C1`.
- Of the 96 words in a boss actor struct, 34 change during animation.

**Animation scripts, located in program ROM**

- Actor struct words `w1c:w1e` form a 32-bit **animation-script pointer**. For
  the boss, 29 observed pointer values in `0x13CC18..0x13CEC4` canonicalize to
  **six programs plus 23 mid-program aliases**.
- Script programs use 16-byte pose records plus four-byte long-pointer jump
  records. Decoded, big-endian, a pose record is `+0` duration, `+2` control
  word, `+4` long pointer to a sprite assembly, and an eight-byte tail. The
  control word splits into bit-15 horizontal flip, a seven-bit sequence index,
  and an independent low parameter byte. The tail is **not** an X/Y word pair:
  code at `0x1cf88`/`0x1cf94` consumes bytes `+9`/`+8` as interaction-table
  selectors, while `0x88e16` copies the complete 16-byte record into actor
  scratch. Bytes `+8`/`+9` are therefore labelled per-record in the report as
  interaction-table selectors (`tail_byte_8_selector` /
  `tail_byte_9_selector`); the remaining tail bytes `+10..+15` are kept
  explicitly unlabeled (`tail_bytes_10_15_unlabeled`) until their consumers are
  proven, with the raw tail retained.
- The animation updater at `0x16536`, `0x165C4` and `0x16644` advances by
  `0x10`, then follows the long pointer at the next record when the current
  flags word is negative. That four-byte jump record is why observed pointer
  deltas sometimes look like 20 bytes. The script has an explicit loop, so the
  format includes control flow, not just a frame list.
- Observed sprite-assembly pointers: `0x13DEA0`, `0x13DE46`, `0x13DFEC`,
  `0x13E00A`, `0x13E04C`, `0x13E44C`.
- The renderer at `0xA9CB6` dispatches on the first assembly word. The decoded
  boss assemblies use selector `6` (budget, object-command count, offset-table
  index, signed X/Y origin, then `(code, attribute, signed layout-adjust)`
  records), selector `2` (a 14-byte single centred object), or selector `10`
  (direct layout x/y words); the original 12 were all selector `6`, and the
  full 28-assembly pose set spans all three. The selector-six handler at
  `0xAA00E` reads the offset-table pointer from `0x1FD1C8`; each layout link
  advances by `4 + s16(layout_adjust)`. The pose check now proves all 28 decoded
  code sets and pixels (29 poses) against captured oracles. The independent
  position audit proves the previous-frame world-coordinate/layout model over
  its full matched scope (408/408 frames); the shared-code-set sibling deltas
  are resolved by the actor-slot record pointer at frame f−1, leaving only a
  transient four-pixel Y settling residual open.
- Word `w88` takes 224 distinct values over 240 frames; likely a frame timer.

**The retail ROM still contains Capcom's development tools**

- `0xFF81C7` byte, non-zero, is the master debug enable.
- `0xFF806C..0xFF806E` cache debug DIP rows 1..3:
  row 1 bit 0 entity spawner and info display, bit 1 entity monitor,
  bit 2 player monitor; row 2 **bit 6 stage collision**, **bit 7 hitboxes**;
  row 3 bit 1 disable CPU in attract demos, bit 2 extended entity info.
- `0xFF81D8` enables the software switch UI and disables the spawner.
- Hidden test menu when `0xFF21AA` equals 2 during the standard test menu:
  pattern viewer with hitbox measurement, scroll-layer viewers with collision
  "Hit Mode", story-text viewer, per-actor arrangement tools.
- Disconnected debug routines at `0xB1998` entity info, `0xB1866` player info,
  `0xB1A84` extended entity info; they need `A6` set up and `D0=0` in a task
  context.
- The entity spawner uses **Player 4** inputs, which stock MAME AvP does not
  provide. Under ROM extraction this is only an optional validation convenience,
  so it is not a reason to build MAME.

**Initial failures and the working activation path**

Enabling the overlays by writing the RAM flags does not work: the game
re-caches them from the physical switches every frame. Driving MAME's real DIP
ioports (`:DSWA 1-1`, `:DSWB 2-6`, `:DSWB 2-7`) while loading the mid-game state
`avspu_stage1_boss_12660` also left `0xFF81C7` at zero, because the flags are
cached during boot initialisation that already ran with debug off inside the
state. A cold boot with the switches held from frame 0 is necessary, but not
sufficient for this retail ROM: its physical-DIP-to-RAM copy routine is absent.
The verified stock-MAME path injects the retained software-switch bytes once
after startup RAM clearing, then lets the game's own routine derive the master
enable. The capture scripts and handoff record the exact frame and values.

## Capability Gate 1 technical phases (SUPERSEDED 2026-08-18)

> These phase sections predate the 2026-08-18 re-sequence and are retained for
> their technical detail only. **The order of work is the S1-S6 slice table in
> "Master execution plan" above**, not the phase numbering below. Where the two
> disagree, the slice table wins. Phase 1's instrument work and Phase 2's decode
> work are largely done; Phase 3's native reimplementation is what S2-S4 now
> carry out.

### Original phase framing

The numbered phases below are the detailed engineering decomposition for Gate
1. Once they pass, continue with the full-game program phases above; do not
treat the Round 1-specific nouns in these sections as the final scope.

## Phase 0 is NOT on the critical path (revised 2026-08-17)

This phase was written before the debug overlays were working. They now run in
**stock MAME 0.289**, enabled by setting `:HW_TYPE` Hardware to Development and
driving the active-low `:DSWA`/`:DSWB` fields from before the first frame, then
injecting the software-switch bytes once because the retail ROM dropped the
physical-DIP-to-RAM copy routine. Cold-boot runs hold `enable=01 row2=c0`
through gameplay.

Both original justifications for a custom build are weaker than they looked:

- **Entity spawner (needs Player 4).** It was valuable under the capture
  method, where each actor had to be *observed* animating. Under ROM table
  extraction, animations are read from script tables, so the spawner is a
  convenience for validation, not a dependency.
- **Write tracer.** MAME's stock debugger provides watchpoints. Try those
  first; they are very likely sufficient to find the routines that write the
  animation-script pointer and the state fields.

**Build MAME from source only if stock watchpoints prove inadequate for
tracing, or if the spawner becomes the cheapest way to validate a specific
actor.** Do not treat it as a prerequisite. The phases below remain in their
original form for that contingency.

## Phase 0 (contingency): instrumented MAME

Everything downstream depends on observing the game precisely, so this is
first. Build MAME from source per the official guide and carry the changes as a
tracked patch set, the way `engine-patches/joengine-4bpp-sprites.patch` already
does for Jo Engine.

Changes required, smallest first:

1. **Four-player, four-button AvP input.** Stock MAME configures three players
   and three buttons; the entity spawner needs P4. Without this the single most
   useful tool stays locked.
2. **Actor-RAM write tracer.** Log `(pc, address, value, frame)` for every
   write into the actor region. This is how the animation and AI routines are
   located: the code that writes `w1c:w1e` is the animation driver, and the
   code that writes the state fields is the AI.
3. Optional: a structured per-frame state dumper in C. Lua polling already
   works and is fast enough for 240-frame windows; add this only if full-level
   per-frame dumps prove too slow.

Try MAME's stock debugger (`-debug`) with watchpoints before building. The
custom build is only a fallback if stock watchpoints cannot locate the writers,
or if a later optional Player-4 validation proves materially cheaper than ROM
table extraction.

Deliverables: a documented build procedure, a tracked patch set, and a pinned
MAME source revision recorded beside the existing 0.289 pin.

Gate: the instrumented build boots `avspu`, exposes P4, and emits a write trace.

## Phase 1: turn on the game's own tools

Cold boot in Development hardware mode with the active-low debug DIPs held from
frame 0, inject the software-switch bytes once after initialisation because the
retail ROM removed the DIP-to-RAM copy, and then drive the existing
deterministic input route. Do not rewrite the switch bytes every frame.

1. Capture **hitboxes** across Round 1 for the player, street aliens, Stalkers
   and Chrysalis.
2. Capture **stage collision** for the street, doorway, interior and boss room.
3. Capture the **entity and player info monitors**; these display struct fields
   with meaning attached, which labels the 192-byte struct far faster than
   diffing values.
4. Optionally use the **entity spawner** to validate a specific actor in
   isolation. It is not the animation source and is not a dependency: extract
   complete animation sets from ROM script tables.

Deliverables: hitbox and collision datasets per actor and per room, plus a
map of only the actor fields consumed by the native runtime.

Gate: every Round 1 actor has real hitboxes recorded, replacing the inferred
contact offsets currently used for the boss (21/55/97) and Stalkers.

This phase alone removes the largest single source of approximation in combat,
and it is cheaper than Phase 2. Do it first.

## Phase 2: decode the tables

**2a. Animation scripts.** Extend the proven boss format into complete Round 1
coverage. The normal/jump discriminator is grounded in the updater: normal
records are 16 bytes and a negative control word is followed by a four-byte
pointer that redirects the script. The 28 decoded boss pose assemblies (all 29
poses; the 162 previously-unmatched frames now all match a decoded assembly)
pass the rendered-pose comparison. Record-selection timing is resolved (the
shared-code-set sibling origin is picked by the actor-slot record pointer at
frame f−1) and the proven tail selectors (bytes +8/+9, readers 0x1cf94/0x1cf88)
are labelled per-record, with +10..+15 kept explicitly unlabeled. Next: extract
every required player/enemy program and label the still-unproven tail bytes from
their consumers.

Validation, non-negotiable: every required ROM-decoded assembly must reproduce
an already-captured pose **pixel for pixel**, with ROM-derived position and
dimensions covered independently rather than hidden by captured placement.
That test converts every existing captured clip from source-of-truth into a
regression oracle.

**2b. Actor struct.** Map fields **on demand**, not exhaustively. Only the
fields the native runtime actually consumes need identifying; mapping all 96
words for completeness is wasted effort. Use the Phase 1 monitors as ground
truth and existing captured events as labels.

**2c. Stage data.** Spawn tables, camera bounds, scroll parameters, room
triggers and transitions for Round 1.

**2d. AI.** Use stock MAME debugger watchpoints first to find the routines that
write the script pointer and required state fields, disassemble them, and
translate them to C. Record RNG use explicitly the moment it appears. Use the
custom-build tracer only if stock watchpoints prove inadequate.

Exit checks for the phase: Round 1's animation, collision, spawn and AI data all exist
as extracted tables plus translated routines, with full required pose/position
coverage passing and no tolerance silently treated as exact.

## Phase 3: native reimplementation

- Preserve the working Saturn platform infrastructure: SH-2 build and ISO/cue
  pipeline, VDP1/VDP2 setup, 352x224 full-width mapping, palette allocation,
  HUD, camera, CDDA/SCSP paths and cartridge-allocation discipline. This is a
  replacement of gameplay and animation data sources, not a platform rewrite.
- Build a tile pipeline feeding VDP1 from the already-reconstructed graphics
  region, replacing the pose archives. Ship only the unique tile working set
  referenced by Round 1 scripts, not the 16 MiB reconstructed source region.
- Replace `player_pose_for_frame()` and the generated action tables with a
  small SH-2 script interpreter for the proven fields: duration, bit-15 flip,
  sequence index, parameter byte, assembly pointer, advance, backward jumps
  and termination. The proven interaction-selector tail bytes (+8/+9) may be
  included; the unproven +10..+15 are added only after their consumers prove
  them.
- Convert sprite assemblies into either load-time composed cels or per-tile
  VDP1 commands. Keep both options open until 60 Hz hardware measurements show
  the RAM, CPU and command-table tradeoff.
- Translate the 68k routines that write actor state into C functions over the
  native actor struct, replacing the hand-written enemy logic in
  `cap_world_step()`.
- Convert real hitboxes into native collision tables and stage tables into
  spawn, camera, scroll, room-trigger and transition data.
- Re-check the cartridge budget. Phase overlays may become unnecessary once
  poses collapse into shared tiles. The memory win and removal of phase
  overlays are predictions until real tile reuse is measured.

## Phase 4: validation

- **Parity harness, scoped to functional parity.** Run MAME and the native host
  model on the same input sequence and compare. Compare **events**, not every
  field of every frame: state transitions, spawn events, hit events, animation
  script transitions and their durations. A full per-frame diff of all fields
  is the instrument for frame-exact parity, which is not the target, and
  building it first wastes effort on sub-pixel and RNG noise that functional
  parity explicitly tolerates. Widen to per-frame only where an event-level
  mismatch needs localising.
- Keep the existing deterministic captures as regression oracles.
- Keep the verified native route (eight street KOs, Chrysalis, then Round 2 in
  4,485 model frames) and the 12,000-frame soak as regression tests for the
  translated behaviour.
- Then the existing checks in `docs/TEST_PLAN.md`: host tests, focused profile,
  full route, clean normal release, audible run, physical Saturn.

## Ordering and rationale

Follow the dated master execution plan above. Finish its narrow street-alien
five-slot proof first so the currently localized writer investigation is not
discarded mid-proof, then return immediately to real hitboxes because they
retire the largest collision approximations cheaply. The broad Phase 2 work is
still the bulk of the project. Phase 0 remains only a contingency if stock
watchpoints are inadequate. Phase 3 follows per actor only after that actor's
decoder and position checks are proven. Phase 4 runs continuously from the first
extracted events.

Do not start Phase 3 for an actor until its required pose/position coverage is
proven. The format check is green for the current 12 boss assemblies, but that
does not authorize replacing actors or actions whose tables remain undecoded.

## Pose and position checks

`tools/verify_pose_gate.py` is the format-isolating pixel check:

```powershell
python tools\verify_pose_gate.py
```

It decodes verified poses from `/SPR4/*.RLE`, checks that each ROM assembly has
the captured object-code set, composes with captured screen geometry, crops to
the non-transparent bounds, and requires **zero differing pixels** with no
colour tolerance. Current status: **28/28 decoded boss assemblies (29 oracle
poses) pass**. The
captured placement is intentional here: this test isolates code/tile/palette
and composition correctness and must not be described as a self-contained
position proof.

`tools/verify_position_gate.py` independently tests the ROM origins/layout
words against previous-frame actor world coordinates and captured object RAM:

```powershell
python tools\verify_position_gate.py
python tools\verify_position_gate.py --require-exact
```

The default scoped check passes when every tested residual is directly exact or
belongs to an explicit settling class (the shared-code-set sibling case is no
longer a residual: the check selects the sibling origin with the actor-slot
record pointer at frame f−1, the same one-frame source the world coordinates
use). Current scope: 408 geometry frames, 408 matched, 0 unmatched; 1,443
tested parts, 1,435 directly exact pairs, 0 sibling-origin residuals, 8
formally-bounded `x=0/y=-4` whole-pose settle parts, and zero other residuals;
X is 1,443/1,443 exact. The `(0,-4)` settle trail is the only non-zero
residual in the scope and is bounded (see AGENT_HANDOFF.md); its exact
object-Y writer is not yet disassembled. `--require-exact` is the goal-strength
check and currently **fails**, as it should, only until those 8 settling
residuals are derived (coverage itself is complete).

Neither check is an event-level parity harness. Goal condition 5 remains open
until full required animation coverage and the MAME-vs-native event comparison
both pass.

## Deferred full-game content and explicit exclusions

Attract mode, complete title/menu transitions, remaining rounds, endings,
credits and multiplayer are **deferred until Gate 1 proves the reusable
engine**, but they are required by the full-game goal and are not out of scope.

The following remain deliberately excluded or conditional:

- **Exhaustive actor struct mapping.** Map only fields consumed by the native
  runtime; see 2b.
- **Frame-exact comparison harness.** Functional parity uses semantic-event
  comparison and widens only around mismatches; see Phase 4.
- **A custom MAME build**, unless stock watchpoints prove inadequate. See the
  Phase 0 revision note.
- **Other regional revisions as shipped targets.** `avspu` is canonical;
  another revision is comparative evidence unless the user expands scope.
- **Public distribution or promotion** without explicit rights-holder and
  licensing authorization.

## Scope and rights

Unchanged and non-negotiable: this is a private capability test. ROMs, captures,
decoded assets and disc images stay out of Git. Extracted tables are derived
from copyrighted code and carry the same restrictions as the ROM. Nothing here
authorises distribution, public demonstration, or promotion; that requires an
explicit rights-holder and licensing review, as stated in `NOTICE.md`.

## External references

- Alien vs Predator debug tools teardown: https://sudden-desu.net/entry/alien-vs-predator/
- CPS2 hardware information: https://datacrystal.tcrf.net/wiki/CPS2:Hardware_information
- CPS2 board and custom-chip schematics: https://gitlab.com/loic.petit/cps2-reverse
- Schematics viewer: https://petitl.fr/cps2/
- Open Verilog CPS cores and KiCAD board schematics: https://github.com/jotego/jtcores
- Compiling MAME: https://docs.mamedev.org/initialsetup/compilingmame.html

The FPGA cores and schematics document the **hardware** half: sprite and
tilemap priority, masking, palette behaviour and video timing, which the Saturn
VDP1/VDP2 path must reproduce and currently infers from MAME. They do not
contain game logic and do not shortcut Phase 2. Their second use is as an
independent oracle where MAME behaviour looks driver-specific, as already
happened when its CPS2 screen turned out to be RGB32 and made pen identity
ambiguous.
