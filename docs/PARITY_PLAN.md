# Near arcade-perfect Round 1: parity plan

Target: a Sega Saturn build of Alien vs Predator Round 1, "City of Despair",
that is **functionally parity-accurate** with the CPS2 original. Enemies behave
correctly, animations play their real sequences at their real durations,
collisions use the real boxes, and the level plays as the arcade plays. This is
not bit-exact frame parity; see "What parity means here".

This document supersedes the capture-and-bind method for new work. Read it with
`AGENTS.md` and `docs/AGENT_HANDOFF.md`.

## Goal-progress index

Audited 2026-08-17 against every completion condition in
[`GOAL.md`](GOAL.md). Status describes the **required final implementation**,
not how much useful groundwork exists. No percentage is used because a green
host model cannot substitute for a missing ROM-derived runtime or physical
hardware proof.

**Overall: 0 of 7 final conditions are closed.** The existing capture-derived
native route is a valuable regression baseline, not the goal implementation.

| # | Goal condition | Status | Current evidence and remaining gate |
|---|---|---|---|
| 1 | Animation from ROM scripts at runtime | **OPEN — Chrysalis tile-composition slice proven** | For the Chrysalis boss the runtime now composes all 29 of its poses from ROM-referenced 4bpp tiles (`compose_boss_rom_pose` in `main.c`, `generated/avsp_boss_rom.h`), and the boss's `BACT`/`BHIT`/`BKO` pose archives are no longer loaded for animation (they remain on disc only as host-test regression oracles). This is a composition slice, not full ROM animation: pose *selection* still uses the capture-derived per-frame clip/step tables (`boss_pose_for_frame`, `generated/avsp_boss_animation.h`), and the ROM selector-6 / control-word script interpreter is decoded host-side only, not yet linked into the runtime. The 29-pose / 28-assembly composition gate passes 28/28 with 0 differing pixels, the focused KO/HIT builds and the full controller route through Round 2 all render on Yaba Sanshiro without an asset error, and a clean normal release boots to title. **Remaining:** link the ROM script interpreter for pose selection, and decode the player/street-aliens/Stalker programs to route them through the same tile-composition path (retiring their `/SPR4/*.RLE` archives), before this condition is closed. |
| 2 | Collision from the game's hitboxes | **OPEN — evidence captured** | Stock-MAME hitbox overlays and selected actor-relative candidates are tracked. Native collision still uses scalar range/lane checks and inferred Chrysalis 21/55/97 and Stalker contact schedules. Decode the game's box records, validate all required poses, and replace those checks. |
| 3 | Enemy behaviour from translated 68000 routines | **OPEN** | Stock watchpoints located animation/action/state writers. `cap_update_enemy()` remains hand-authored, no required AI path is translated, and PRNG use is not identified or recorded. |
| 4 | Spawns, camera and triggers from stage tables | **OPEN** | The current lifecycle, waves, camera and room transitions are capture-derived constants and authored C. Round 1 stage tables have not been located, extracted or consumed by the runtime. |
| 5 | Pixel and event-level validation | **OPEN — pixel groundwork proven** | The format-isolating pose gate passes 28/28 (29 oracle poses) with zero differing pixels using captured screen geometry, in both default and self-contained modes. The independent position audit has a scoped pass on 408/408 geometry frames: 1,435/1,443 parts directly exact, 0 at sibling-origin deltas (the shared-code-set ambiguity is resolved by the actor-slot record pointer at frame f−1), 8 at a formally bounded `y=-4` whole-pose settle trail (the only non-zero residual in the scope; the one-step trail's exact writer is not yet disassembled), 0 frames unmatched, X 1,443/1,443 exact. Because the pose gate requires every listed assembly to 0-diff an oracle, only the 28 assemblies with a captured-pose oracle are listed; the 5 decoded mid-attack/at-rest trace assemblies are excluded and reported in `excluded_no_oracle_assemblies`, not pixel-verifiable. A MAME-vs-native event parity harness is still missing. |
| 6 | Existing regressions still pass | **BASELINE GREEN; FINAL RE-RUN OPEN** | The current host model reaches Round 2 in 4,485 frames and its 12,000-frame deterministic soak passes; prior Yaba diagnostics exercised captured clips. These must pass again after ROM-derived animation, collision, stage and AI replacement, followed by a clean normal-release boot. |
| 7 | Physical NTSC Saturn at sustained 60 Hz | **OPEN** | Emulator precursor and image/hash evidence exist. No physical NTSC Saturn route, audible full-level proof, sustained-60-Hz measurement, or ten-minute hardware soak is recorded. The final candidate must be a clean `release-normal-release` build with a digital pad and 32 Mbit cartridge. |

The volatile evidence, exact commands, hashes, current HEAD and immediate work
queue stay in [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md); this table is the concise
goal index.

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
  script position, health, timers, and state transitions, within a stated
  tolerance, for the whole level.
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
  scratch. Keep the remaining tail fields unlabeled until their consumers are
  proven.
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
  advances by `4 + s16(layout_adjust)`. The pose gate now proves all 28 decoded
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
pass the rendered-pose comparison. Next: extract every required player/enemy
program, resolve record-selection timing, and label the remaining eight-byte tail
fields from their consumers.

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

Gate for the phase: Round 1's animation, collision, spawn and AI data all exist
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
  and termination. Add tail semantics only after their consumers prove them.
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
- Then the existing gates in `docs/TEST_PLAN.md`: host tests, focused profile,
  full route, clean normal release, audible run, physical Saturn.

## Ordering and rationale

Phase 1 is first because it is working in stock MAME and retires the largest
collision approximations cheaply. Phase 2 is the bulk of the work. Phase 0 is
only a contingency if stock watchpoints are inadequate. Phase 3 follows once
the decoder is proven. Phase 4 runs continuously from the first extracted
events.

Do not start Phase 3 for an actor until its required pose/position coverage is
proven. The format gate is green for the current 12 boss assemblies, but that
does not authorize replacing actors or actions whose tables remain undecoded.

## Pose and position gates

`tools/verify_pose_gate.py` is the format-isolating pixel gate:

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

The default scoped gate passes when every tested residual is directly exact or
belongs to an explicit settling class (the shared-code-set sibling case is no
longer a residual: the gate selects the sibling origin with the actor-slot
record pointer at frame f−1, the same one-frame source the world coordinates
use). Current scope: 408 geometry frames, 408 matched, 0 unmatched; 1,443
tested parts, 1,435 directly exact pairs, 0 sibling-origin residuals, 8
formally-bounded `x=0/y=-4` whole-pose settle parts, and zero other residuals;
X is 1,443/1,443 exact. The `(0,-4)` settle trail is the only non-zero
residual in the scope and is bounded (see AGENT_HANDOFF.md); its exact
object-Y writer is not yet disassembled. `--require-exact` is the goal-strength
gate and currently **fails**, as it should, only until those 8 settling
residuals are derived (coverage itself is complete).

Neither gate is an event-level parity harness. Goal condition 5 remains open
until full required animation coverage and the MAME-vs-native event comparison
both pass.

## Explicitly out of scope

Cut deliberately, to keep the target reachable:

- **Attract mode.** It is the game playing itself and needs the whole engine
  plus demo input scripting. The goal is a playable Round 1, not the demo. It
  becomes nearly free once the engine is done; revisit then, not now.
- **Exhaustive actor struct mapping.** See 2b.
- **Frame-exact comparison harness.** See Phase 4.
- **A custom MAME build**, unless stock watchpoints prove inadequate. See the
  Phase 0 revision note.
- **Boot logo and title screens.** They are long static holds, 79 to 255 frames
  each, per the boot timeline map. They are trivially reproducible whenever
  wanted and prove nothing about parity; do them last or never.

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
