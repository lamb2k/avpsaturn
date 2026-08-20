# Full-game native Alien vs Predator parity plan

Target: a private native Sega Saturn port of the complete US `avspu` arcade
game at functional parity. Capability Gate 1 is the player-controlled route
from cold boot through Round 1 and the Round 2 title. It proves the reusable
extraction, semantic runtime, Saturn renderer, audio path, and validation method;
it is not full-game completion.

This is the current-only plan of record. Superseded milestone/phase/slice
narratives were removed on 2026-08-19 because agents were treating historical
instructions as active work. Git history retains them.

Read with `AGENTS.md`, `docs/GOAL.md`, `docs/AGENT_HANDOFF.md`,
`docs/ROUND1_EXECUTION_PLAN.md`, and `docs/NEXT_AGENT_PROMPT.md`.

## Vocabulary

Use only:

- **Acceptance:** Capability Gate 1 conditions 1-7 and full-game conditions
  1-9. Only these affect the reported `0/7` and `0/9` counts.
- **Work:** steps S1-S6 and their checks. The active presentation body is
  decomposed into work packages RP0-RP12 and content batches A-C in
  `docs/ROUND1_EXECUTION_PLAN.md`. A green check proves a mechanism; it does
  not close a condition unless the entire required route passes.
- **Evidence:** `MEASURED`, `ADAPTED`, or `GAP`.

Do not introduce new milestones, phases, slices, or unrelated gates. Historical
commit messages may retain old terminology but are not instructions.

## Progress indexes

### Full-game conditions: 0/9

| # | Condition | Status and remaining work |
|---|---|---|
| 1 | Complete content and flow | **OPEN.** The current native route is incomplete and presentation-heavy sections remain static or skipped. Complete Rounds 1-7, progression, items, continue/game-over, attract, endings, and credits are required. |
| 2 | ROM-derived animation and presentation | **OPEN.** Street-alien and selected composition paths are proven; complete actors, effects, backgrounds, scenes, and runtime selection remain. |
| 3 | Game-derived collision | **OPEN.** Street defender hurt boxes are partially live. Attacks, reactions, projectiles, bosses, stage collision, and game-wide coverage remain. |
| 4 | Translated behavior | **OPEN.** Required player, enemy, boss, object, and PRNG routines are not translated across the game. |
| 5 | Extracted stage and game systems | **OPEN.** Stage scripts, camera, triggers, scoring, items, HUD, doors, exits, and progression are not consumed game-wide. |
| 6 | Complete native audio | **OPEN.** A Round 1 PCM subset exists; stage CDDA is currently disabled in the dirty runtime and complete music/voice/ownership/timing remain. |
| 7 | All-character single-player | **OPEN.** No character has a complete final-boss-to-credits native route. |
| 8 | Original multiplayer | **OPEN.** Joins, HUD/score ownership, camera, spawn, collision, load, and full routes at the original player count are not implemented or validated. |
| 9 | Final physical-hardware release | **OPEN.** No complete single- or multiplayer route has passed on physical NTSC Saturn hardware. |

### Capability Gate 1 conditions: 0/7

| # | Condition | Status and remaining work |
|---|---|---|
| 1 | Animation from ROM scripts at runtime | **OPEN.** ROM animation/emission runs for the street path, but record seeding, anchors, player, Stalkers, Chrysalis/boss, effects, HIT/KO/spawn, and all capture-derived pose decisions are incomplete. |
| 2 | Collision from game data | **OPEN.** Same-frame street defender hurt records are live. Player attack geometry, HIT/KO writers, reactions, projectile/broadcast paths, boss/Stalker schedules, and stage collision remain. Unknowns stay counted `GAP`, never invulnerability. |
| 3 | Enemy behavior from translated 68000 routines | **OPEN.** Current enemy logic is adapted C. Translate decisions, movement, attacks, separation, reactions, and PRNG ordering. |
| 4 | Spawns, camera, triggers, and flow from stage data | **OPEN.** The lifecycle is authored from captures/constants. Locate and consume source stage tables and routines. |
| 5 | Pixel and event validation | **OPEN.** Pose-format checks are strong, but complete presentation/actor coverage and MAME-vs-native semantic-event comparison are missing. |
| 6 | Existing regressions still pass | **BASELINE GREEN; final rerun open.** The historical 4,485-frame route and 12,000-frame soak are regressions only. Re-run after every replacement and finish on clean normal release. |
| 7 | Physical NTSC Saturn at sustained 60 Hz | **OPEN.** Requires the final clean Gate 1 image, digital pad, 32 Mbit cartridge, audible route, sustained frame-time evidence, and ten-minute soak. |

## Immediate work body: scene-complete Round 1 presentation

This body precedes S5 because missing/flattened presentation currently prevents
an honest end-to-end Gate 1 route. It does not add another acceptance gate.

Required route:

`legal/QSound/Capcom/opening -> all story panels -> title wait -> Start
transition -> character select -> confirm/shutter -> Round 1 title -> every
Round 1 presentation scene -> results/intermission -> Round 2 title`.

Requirements:

- no automated scene skip in the accepted normal route;
- no new screenshot/framebuffer/RLE runtime content;
- every replacement derives from ROM tilemaps, objects, palettes, scroll,
  priority, input, timing, and audio data or translated source routines;
- all four selection positions and source controls work;
- Predator Warrior is the accepted gameplay route; other selections remain an
  explicit `ADAPTED` fallback;
- attract/demo, service, continue/game-over, S5 AI, and physical hardware stay
  outside this body;
- Capability Gate 1 remains `0/7` when this body finishes unless an entire Gate
  condition independently closes.

The granular dependency graph, work-package status, agent ownership, shared-
primitives check, and content-batch checks are in
`docs/ROUND1_EXECUTION_PLAN.md`. `docs/NEXT_AGENT_PROMPT.md` contains only the
first dependency-ready executable package.

Current presentation evidence:

- Jo-compatible one-based surface palettes and bounded copies pass at
  `b681c04`;
- 25 held CRAM/register observations contain 22 exact surface comparisons and
  zero adjacent palette-boundary writes;
- 25 held VDP1 schedules containing 44 objects pass geometry, colour, order,
  clipping, cursor-cycle, and negative-control checks through the RP0 chain;
- the confirmation shutter and ROM-derived Round 1 title pass at `e728c9b` and
  `aa0d671`; `R1TITLE.RLE` is no longer a runtime option;
- RP1-RP3 provide `AvspSceneDef v0`, the 18,000-frame cadence-1 route census,
  and the host/SH-2 minimal scene runtime;
- RP4 extraction/generation is committed through `8fd75b3`: source frames
  3474-3674, two fitted VDP2 strips, map patches, palette cycle, independent
  scroll, and a captured object schedule retained only as a validation fixture;
- RP4 remains in progress until NBG0 ownership, two-page map addressing,
  per-object VDP1/VDP2 priority, live register/VRAM/CRAM state, fixture
  isolation, and resource bounds pass.

### Presentation work-package model

The overall plan remains S1-S6. RP0-RP12 are implementation scheduling units,
not replacement milestones or new acceptance conditions. Current ordering is:

1. finish and review RP4's two-plane renderer without shipping its captured
   object fixture;
2. run RP5 G0/CDDA residency and RP6 semantic scene IDs as isolated ownership
   lanes from a committed integration baseline;
3. pass the RP7 shared-primitives
   check;
4. integrate frontend/opening content, street/interior presentation, and
   boss/results/Round 2 title as Batches A-C;
5. pass the continuous-route integration check, then close the stricter Round 1
   presentation parity check and resume S5/S3/S4/S6.

Every batch updates the tracked variance ledger. A shared-primitive defect
invalidates dependent batch results; it cannot be relabelled as a local visual
variance. Only the integration owner changes shared runtime/build files and the
execution-plan status table. Other agents start from an exact committed SHA in
separate worktrees and return explicit commit SHAs plus checks.

## Presentation architecture, including parallax

### Static frontend pages

The current active frontend base is indexed 8bpp NBG1, not direct-colour. A
static fitted page may remain indexed only when all of these are measured:

- no more than 255 nontransparent RGB555 colours;
- no colour merging, alias, missing palette reference, or invalid object bank;
- converter output equals ISO member, decoded RAM, and NBG1 VRAM;
- palette payload equals CRAM under the active bitmap/palette registers;
- host and live 352x224 output match the source after Saturn RGB555 conversion.

The implementation must also respect Jo's intentional one-based palette
contract: reserve hardware index zero, use at most 255 live colours, and write
only through the palette's 255-entry data range. A block-base write that aliases
the preceding allocation is not evidence of a valid representation.

If a page fails, use a bank-preserving VDP2 tilemap. A frontend-only RGB555
bitmap is a valid measured fallback but consumes 262,144 bytes of VDP2 VRAM and
requires explicit mode reconfiguration. It is not the gameplay architecture.

### Scrolling gameplay and interstitial scenes

The street has measured non-identical layer motion; one flattened surface is
incapable of parallax. Target mapping:

| CPS2 content | Saturn target |
|---|---|
| scroll3 rear | NBG1 |
| scroll2 main and row-scrolled | NBG0 |
| actors and transient objects | VDP1 |
| source-proven tilemap foreground above objects | NBG2 or bounded VDP1 extraction |

Apply the common endpoint-aligned 384-to-352 transform at plane level: 11/12
horizontal zoom plus transformed scroll offsets, with 224 source lines kept
1:1. Never squeeze individual source tiles. Drive NBG0 line scroll only if the
captured 1,024-word source table proves nonconstant per-line values.

Before NBG0 is assigned, move Jo debug output to VDP1/NBG2 or exclude it from
production profiles. Own VDP2 banks/registers explicitly by presentation state.

The target remains `ADAPTED` until a Saturn prototype proves:

- independent NBG0/NBG1 scroll at source-derived rates;
- exact endpoint mapping without crop, bars, seams, or vertical stretch;
- captured line-scroll behavior where required;
- source layer/object insertion and priority at deliberate overlaps;
- correct VRAM, CRAM, and register readback;
- negative controls for zoom, row entry, palette bank, and priority.

If hardware plane zoom cannot reproduce endpoint alignment, the only approved
fallback is complete-layer ROM render, one global 384-to-352 fit, then 8x8
retile/deduplication. Reject it if colour or memory budgets do not close.

### Scene program

Each presentation bundle contains:

- immutable tiles/cells/map pages;
- explicit palette mapping;
- VDP1 object tiles and command records;
- a compact timed operation stream for layer page/priority/scroll, line scroll,
  map patches, palette ranges/fades, object emit/retire, input/state, audio, and
  procedural masks/wipes.

Translate a source writer when a scene is driven by a ROM tilemap/object
routine. Captured changed frames are comparison oracles, not payloads.

Use fixed arenas:

- F0: legal/opening/story/title and Start transition;
- F1: select/cursor/confirm;
- G0: all Round 1 presentation through Round 2 title, including row-scroll
  data and interstitial objects.

All G0 data required during stage CDDA must be resident before CDDA begins. If
G0 does not fit with actors/PCM, deduplicate and phase PCM first. Add a
stop/load/resume boundary only at a source-proven silent interval.

## Work steps S1-S6

### S1: canonical actor spine — passed

Carry only runtime-consumed fields from the CPS actor record, including class,
state/sub-state/action, animation record, table set, position, facing, health,
and active flags. Keep collision and presentation views derived from the same
canonical actor/frame. Do not exhaustively map unused words.

### S2: animation script walk and native emission — in progress

- Interpret 16-byte pose records and 4-byte negative-flags jumps.
- Treat the high animation byte as flip plus sequence index and the low byte as
  parameter; do not collapse them into a generic flags field.
- Resolve program entry/control flow from ROM records rather than observed
  mid-program pointers.
- Emit semantic object fields to VDP1; do not mirror raw CPS descriptor buffers.
- Validate decoded poses pixel-for-pixel against capture oracles before runtime
  promotion.
- Complete runtime record selection and placement for the full Round 1 cast.

### S3: format and cast widening — in progress

Generalize the checked family decoders to player, Stalker, Chrysalis/boss,
effects, and remaining tag/selector formats. Build a tile working set from
actually referenced scripts and measure reuse. Do not assume tile sharing or
phase-overlay savings until manifests quantify them.

### S4: game-derived collision — in progress

Consume selectors from the same animation record used for rendering and resolve
families through the actor's checked class/table-set data. Complete:

- player and enemy attack geometry;
- HIT/KO record trajectories and external pointer writers;
- damage, reaction, recovery, death, and score paths;
- projectile and broadcast-hit ownership;
- Stalker/boss schedules;
- stage collision and traversal constraints.

Frame order is fixed:

1. resolve current ROM animation/collision view;
2. step gameplay using that view;
3. render from the same record;
4. advance once for the next frame.

### S5: translate behavior — open after presentation body

Translate relevant 68000 routines to static SH-2 C functions over the canonical
actor/world structs. No 68000 interpreter. For each routine:

1. locate entry, callers, dispatch path, fields read/written, and source tables;
2. create a deterministic source fixture with inputs and semantic outputs;
3. translate control flow, arithmetic width/sign, table access, and side effects;
4. identify PRNG algorithm and consumption order or record an explicit adapted
   decision;
5. compare state, action, animation-record, spawn, movement, hit, and audio
   events; widen frame comparison only around mismatches;
6. replace adapted logic only when the differential check passes.

Room 1 class `0x1F` behavior is first. Then player, reactions, Stalkers,
Chrysalis/boss, effects, and stage systems.

### S6: Saturn budgets, audio, and hardware — open

Measure, do not estimate, peak:

- low/high work RAM and BSS boundary;
- both expansion-cartridge banks and lifetime fragmentation;
- VDP1 texture and command memory;
- VDP2 banks, maps, line tables, and modes;
- CRAM;
- SCSP RAM;
- DMA, CD reads, CDDA/PCM ownership;
- master/slave SH-2 frame time at 60 Hz.

The 32 Mbit expansion cartridge is mandatory. Expansion RAM does not relax
internal work-RAM, VDP1, VDP2, CRAM, or SCSP limits.

## Critical path after the current presentation body

The detailed presentation path is RP0-RP12 in
`docs/ROUND1_EXECUTION_PLAN.md`. After that body:

1. Translate S5 Room 1 class `0x1F` behavior and PRNG consumption.
2. Finish S3/S4 across player, Stalkers, boss, effects, collision, reactions,
   projectiles, and stage collision.
3. Decode/consume Round 1 stage scripts, spawns, camera, triggers, doors, exits,
   scoring, items, and Round 2 transition; remove the hardcoded wave lifecycle.
4. Run the entire frontend-to-Round-2 route after every integration body.
5. Complete S6 budgets and Capability Gate 1 condition 7 on physical hardware.
6. Widen stage by stage through all rounds, all characters, endings/credits,
   original multiplayer count, and final physical-hardware validation.

## Established evidence that should not be re-derived casually

- The reconstructed 16 MiB graphics region matches MAME's `:gfx` byte-for-byte.
- Animation pose-to-pose deltas are 16 bytes; jump records are 4 bytes.
- A 732-frame animation free-run is exact.
- The player capture archive contains 103 whole poses costing 417,488 bytes;
  tile/script reuse is predicted to reduce this but remains to be measured.
- The street-alien assembly/emission path is checked, and 28/28 listed boss
  assemblies (29 oracle poses) pass zero-difference pixel comparisons.
- Five decoded assemblies without capture oracles remain excluded, not proven.
- The scoped position check covers 408/408 frames and 1,443 parts, with 1,435
  exact and eight bounded `y=-4` settling residuals. Goal-strength exact mode
  remains red until the writer is derived.
- Collision selectors are animation-record bytes `+8` hurt and `+9` attack;
  the actor `+0x50` table-set selects the bases. Records use checked 8-byte hurt
  and 16-byte attack strides and a signed-centre/unsigned-half-extent overlap.
- Bounded collision evidence includes 21,908 non-overlap pairs with no hit and
  44/56 explained hit latches; broadcast/projectile residuals remain named.
- Exact HIT and KO anchors cover 36/36 and 140/140 frames. The checked corpus
  covers 25,104 street actor-frames with zero per-class constant mismatches.
- The street scroll2/scroll3 movement ratio is about 0.757 over the measured
  moving interval; interior sampled motion is 1:1 and cannot be generalized to
  the street.
- Per-object actor emission measured about 84 peak commands versus about 904
  per-tile commands at identical drawn pixels. Per-object is the default; test
  per-tile only as a measured fallback.
- The current source palette archive is a limited snapshot. Palette coverage is
  an archive-content issue, not proof of a CRAM limit.
- The staged loader and BSS corrections are described in the handoff. Release
  mode must never be used to hide a Jo bounds failure.

## Evidence and checks

### Labels

- `MEASURED`: source/ROM or live native data plus a passing falsification check.
- `ADAPTED`: deliberate Saturn/native substitution with its scope and counter
  exposed.
- `GAP`: required source behavior/data absent or unresolved.

Every manifest/result names source route, actor/class, record or ROM address,
input schedule, output sink, count, hash, and negative control where applicable.
Do not promote correlation to provenance or a screenshot to interaction/timing
proof.

### Presentation checks

- cadence-1 source capture contains every required scene and input path;
- semantic scene manifest contains no framebuffer payload;
- converter/assets regenerate byte-identically;
- host renderer reproduces every changed source frame after RGB555 conversion
  with zero unexplained differences;
- title/select/Round 1 readback proves bytes, registers, palettes, objects,
  timing, and 352x224 geometry separately;
- two-plane street proves parallax, row scroll if needed, and priority;
- normal digital-pad route has no skip, crop, bars, stale cursor, static RLE
  fallback, missing scene, or late disc read;
- source-timed CDDA/PCM is audible and does not freeze transitions.

### Actor and behavior checks

- pixel-exact pose checks isolate format from placement;
- independent placement checks derive origin/offset, not captured coordinates;
- event comparisons cover state/action/record transitions, spawns, attacks,
  hits, damage, KO, camera, and audio;
- negative controls perturb a source field/constant and must fail;
- existing 4,485-frame route and 12,000-frame soak remain regressions, not
  acceptance substitutes.

### Saturn checks

Run analyzer/converter -> host -> focused Saturn -> ISO hash/readback -> full
`test.ps1` -> visible normal route -> `-EncounterTest` through `COMPLETE` ->
clean normal-release title boot -> physical hardware when ready.

## Reference-port boundary

The separate MSHvSF Saturn project is research evidence only. It may inform a
specific AvP architecture question, such as colour-bank representation,
cartridge lifetimes, command lists, CD/audio ownership, or VDP2 layout. It may
not contribute ROM assets, addresses, fighter constants, package sizes, or
unverified assumptions, and its branch must never be merged wholesale.

Promote a reference finding only through:

`reference claim -> falsification/confidence -> explicit AvP probe -> AvP
validation -> minimal AvP-specific implementation`.

The hybrid parallax architecture above is selected from AvP measurements; it
still requires the AvP Saturn prototype before it becomes `MEASURED`.

## Explicit deferrals

- custom MAME build unless stock watchpoints/captures prove insufficient;
- exhaustive actor-struct mapping beyond runtime consumers;
- frame-exact whole-game parity when semantic-event parity is sufficient;
- attract/demo during Capability Gate 1 presentation work;
- regional versions other than canonical `avspu`;
- public distribution, demonstration, or promotion without rights-holder and
  licensing authorization.

## Scope, rights, and external references

This is a private capability test. ROMs, raw captures, generated copyrighted
assets, disc images, private opcode dumps, and derived executable content stay
out of Git. Nothing authorizes public distribution or promotion; see
`NOTICE.md`.

Primary reference classes:

- the `avspu` ROM and deterministic stock-MAME 0.289 observations;
- the game's Development-mode debug overlays;
- Capcom CPS2 schematics and open hardware cores for independent video behavior;
- Sega Saturn hardware/programming documentation and measured live readback;
- MAME documentation for supported debugger/capture behavior.

Useful public starting points:

- https://sudden-desu.net/entry/alien-vs-predator/
- https://datacrystal.tcrf.net/wiki/CPS2:Hardware_information
- https://gitlab.com/loic.petit/cps2-reverse
- https://petitl.fr/cps2/
- https://github.com/jotego/jtcores
- https://docs.mamedev.org/initialsetup/compilingmame.html

Hardware sources constrain sprite/tilemap priority, masking, palette, and video
timing. They do not contain game logic and do not replace ROM routine/table
translation.
