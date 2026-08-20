# Architecture

This is a native SH-2 Sega Saturn port, not a CPS2 emulator. Private host tools
decode the canonical `avspu` ROM and deterministic MAME evidence into semantic
manifests and private generated payloads. The Saturn runtime consumes those
semantics through native actor, renderer, stage, input, and audio systems.

```text
avspu ROM + stock-MAME evidence
  -> deterministic decoders and falsification checks
  -> semantic manifests and private generated bundles
  -> native SH-2 state/scene systems
  -> VDP1 objects + VDP2 layers + SCSP/PCM + CDDA
  -> ISO member verification -> emulator -> physical Saturn
```

## Runtime ownership

The project currently uses Jo Engine for startup, SGL integration, file/audio
helpers, callbacks, controller access, sprite registration, and selected VDP
helpers. It is a dependency, not the game architecture. Project modules own:

- `capability_model`: native world, encounter, input, player/enemy state;
- `avsp_actor`: canonical source-derived actor view;
- `avsp_anim`: ROM animation record walk and control flow;
- `avsp_emit`: semantic CPS object/part decoding;
- `avsp_collision`: source-derived collision records and overlap;
- `avsp_frontend`: frontend bundle loading, state objects, and selection;
- the planned presentation manager: explicit VDP2 mode/bank ownership, scene
  programs, parallax, priority, and lifetime arenas;
- `main.c`: integration and diagnostics, to be reduced rather than expanded.

Production correctness may not depend on a Jo debug module occupying a needed
VDP2 plane. NBG0 debug printing must move to VDP1/NBG2 or be excluded from
production profiles before gameplay scroll2 uses NBG0.

## Boot and executable layout

Pinned Yaba showed a measured monolithic first-read envelope near 400 KiB. This
is not a Saturn executable limit. The runtime uses a staged boot:

1. compact `/0.bin` loads at `0x06004000`;
2. it GFS-loads `/GAME.BIN` into low work RAM at `0x00200000`;
3. a position-independent trampoline at `0x060d0000` copies the payload over
   the loader, purges SH-2 cache, and jumps to the payload's own `___Start` at
   `0x06004000`;
4. the loader never initializes SGL; the payload initializes Jo/SGL normally.

The build verifies both ISO members. Release mode may not bypass BSS safety.
`__bend` and all Jo sprite arrays must remain below `0x060c0000`, where SGL's
sort-list reservation begins. Current dirty configuration uses
`JO_MAX_SPRITE=128` and `JO_FS_MAX_FILES=128`; clean-map and live high-water
checks decide whether that remains safe.

## Canonical actor and game-logic path

`AvspActor` mirrors only source fields consumed by native code: class, state,
sub-state, action, animation record, table set, position, facing, health, and
activation/lifecycle fields. Presentation and collision derive from the same
current actor record.

Frame ordering is fixed:

1. resolve the actor's current ROM animation record and collision view;
2. step native gameplay using that same-frame view;
3. render from that record;
4. advance the animation once for the next frame.

Behavior is statically translated routine by routine into SH-2 C. There is no
68000 interpreter. Each translation gets a deterministic source fixture and a
semantic differential check for state/action/record, movement, spawns, hits,
damage, camera, audio, and PRNG ordering.

## Actor graphics path

The reconstructed 16 MiB CPS2 graphics region is checked byte-for-byte against
MAME. ROM animation scripts identify the required assemblies and tiles; the
port ships only the working set required by the active lifetime bundle.

Animation records are 16-byte poses with separate 4-byte negative-flags jump
records. High-byte animation semantics are flip plus sequence index; the low
byte is a parameter. Observed mid-program pointers are not distinct programs.

Assemblies decode to semantic objects/parts: tile or code identity, palette,
position, size, flip, priority, order, and lifetime. The Saturn path does not
copy CPS object RAM descriptors or bank-flip machinery.

Default actor emission is one VDP1 sprite per CPS object. AvP measurements show
roughly 84 peak per-object commands versus roughly 904 per-tile commands at the
same drawn pixels. Per-tile emission remains a measured fallback, not the
default. Captured whole cels remain regression oracles and adapted fallback
only until the corresponding ROM path passes.

## Presentation architecture

### Resolution

The visible field is 352x224. CPS2's 384-pixel width maps through one
endpoint-aligned 384-to-352 transform; 224 lines remain 1:1. Crop, vertical
stretch, black bars, cross-layer seams, and independent per-tile squeezing are
failures.

### Static frontend

The active frontend base is a 512x256 indexed-8bpp NBG1 bitmap selected with
`COL_TYPE_256`. It is not direct colour. Title/select object schedules use
VDP1, including live cursor and transition objects.

Jo's palette allocator intentionally reserves hardware index zero and exposes
at most 255 colours through `jo_palette::data`; its own 8bpp TGA path shifts
pixels by one to match. ROM-derived fitted surfaces must follow the same
one-based `1..255` convention. Writing a 256-entry payload at the hardware
block base aliases a neighbouring Jo allocation and is not an accepted fix.

A fitted static 8bpp surface is permitted only when actual unique RGB555 colour
count, byte provenance, active registers, CRAM mapping, and live output all
pass. If not, use a bank-preserving tilemap or an explicitly budgeted
frontend-only RGB555 mode.

### Gameplay parallax and priority

The street has measured unequal scroll2/scroll3 movement, so the current
single flattened gameplay surface is a known fidelity gap. Target mapping:

```text
CPS scroll3 rear --------------------------> Saturn NBG1
CPS scroll2 main + optional row scroll ----> Saturn NBG0
CPS actors/transient objects --------------> Saturn VDP1
source tilemap foreground above actors ----> NBG2 or bounded VDP1 foreground
```

Both planes use the common 11/12 horizontal zoom and transformed independent
scroll offsets. NBG0 uses a VDP2 line-scroll table only if the captured
1,024-word source table is nonconstant after normalization. Layer/object
insertion and priority come from source evidence, not a global guess.

The presentation manager owns VDP2 allocation/registers per state. The hybrid
mapping remains `ADAPTED` until the two-plane prototype passes live readback,
source comparisons, memory checks, and deliberate zoom/row/palette/priority
negative controls.

If plane zoom cannot reproduce endpoint mapping, render each complete source
layer, apply one global fit, and retile/deduplicate to 8x8 VDP2 cells. Never fit
source tiles independently.

RP4 currently uses that approved whole-layer fallback: each complete source
plane is rendered in its own domain, fitted once to the common 352-pixel output,
then retiled and deduplicated. This preserves independent scroll/parallax; it is
not the rejected per-source-tile squeeze.

The RP4 production boundary is strict:

- NBG0 is owned by scroll2, so Jo printf must be disabled for production/RP4
  profiles or moved to a non-NBG0 diagnostic path;
- every generated PNT page is mapped explicitly and a live camera boundary
  crossing proves the second page;
- VDP1 Z orders objects only within VDP1. CPS priority classes are encoded as
  Saturn sprite-priority indices under the selected `SPCTL` type and mapped
  through `PRISA`-`PRISD` relative to NBG0/NBG1;
- the captured 201-frame object schedule is a focused validation fixture only.
  Production gameplay consumes translated ROM actor/object state;
- bundle bounds, frame offsets, page changes, uploads, command peaks, and all
  VDP/CRAM/cart ownership are explicit and measured.

### Scene programs

Every legal/opening/story/title/interstitial/result transition is represented
as ROM-derived immutable pages plus a timed operation stream:

- set layer page, priority, scroll, or line-scroll source;
- patch map cells;
- update palette ranges or fades;
- emit/update/retire VDP1 objects;
- apply procedural masks/wipes;
- advance input/state and audio events.

The 13 legacy capture-derived RLE holds are temporary approximations and
offline oracles. No new framebuffer animation is allowed. A source tilemap
writer is translated rather than replaced with captured frames.

The first committed scene-runtime contract is `AvspSceneDef v0`. Its envelope
is versioned and initially permits only evidence-backed hold/input, layer-page,
scroll, palette, object, sparse map-patch, audio, and transition operations.
Unknown scene IDs fail diagnostically instead of skipping. RP2 capture may use
provisional IDs; RP6 finalizes stable semantic IDs after the full route is
grouped. Incompatible envelope changes require a version increment and a
migration check.

`AvspScenePlayer` owns load/activate/step/draw/release behavior for one scene;
`AvspRouteController` is an explicit route state machine. Neither is a general
script VM, dynamic asset cache, or substitute for translated source routines.
The detailed interface and ownership contract is in
`docs/ROUND1_EXECUTION_PLAN.md` RP1-RP3.

## Memory and lifetime model

Budgets are independent:

- high and low work RAM, including BSS and upload scratch;
- expansion-cartridge bank 0 and bank 1;
- VDP1 texture and command memory;
- VDP2 VRAM banks, maps, line-scroll tables, and mode;
- CRAM;
- SCSP RAM;
- CD/data and CDDA ownership.

The 32 Mbit expansion cartridge is mandatory. Jo's allocator is treated as
whole-block unless current evidence proves splitting. Related lifetime assets
are packed contiguously.

Presentation arenas:

- F0: legal/opening/story/title and Start transition;
- F1: character select/cursor/confirm;
- G0: all Round 1 presentation through Round 2 title.

Immutable source lives in cartridge RAM; active maps/cells/objects live in VDP
memory; a bounded work-RAM buffer handles decode/upload. All G0 assets required
while stage CDDA plays must be resident before playback. Deduplicate and phase
PCM before introducing any source-proven silent CDDA load boundary.

## Audio

- Long-form source music maps to CDDA.
- Short effects/voices map to SCSP PCM with explicit lifetime ownership.
- Source QSound state/cues provide timing evidence.
- Data reads must complete before an uninterrupted CDDA interval begins.

The current dirty runtime has the stage CDDA call commented while setting its
started flag. The disc track existing is not proof of playback. Restore the
call only after residency is complete, then validate audible timing, PCM/CDDA
ownership, transition safety, and absence of late reads.

## Input

Saturn digital pad maps to source one-player controls:

- D-pad -> source directions;
- Saturn A/B/C -> the three source gameplay buttons;
- Start -> Start.

Character select is a non-wrapping 2x2 topology. Source acceptance appears
after three CPS frames; A/B/C confirm; no cancel was measured. Input repeat,
release, boundary behavior, and confirm debounce come from cadence-1 source
evidence. Predator Warrior is the accepted gameplay route until other character
logic/graphics pass independently.

## Fidelity status

### Measured

- reconstructed graphics ROM equality;
- animation record/control format and 732-frame free-run;
- selected actor assembly/emission and zero-difference pose checks;
- current source-derived street defender collision path;
- Jo-compatible one-based frontend palettes with exact held CRAM/register
  provenance and zero adjacent-boundary writes;
- eighteen ROM-derived title/select schedules and forty held VDP1 objects exact
  for geometry, colour, order, clipping, and cursor timing;
- complete confirmation shutter timing/rows and the ROM-derived Round 1 title
  composition, with `R1TITLE.RLE` retired from the runtime title path;
- 352x224 object clipping;
- unequal street layer motion requiring parallax;
- RP4 selected interval 3474-3674: scroll2 span 176 versus scroll3 span 154,
  complete whole-plane fitted cell sets, two map patches, and a constant-zero
  visible normalized row table for that interval;
- staged loader reaching an advancing native world.

### Adapted

- current enemy AI, wave lifecycle, camera, and portions of animation selection;
- current normal gameplay still uses flattened backgrounds and remaining route
  scene holds outside the focused RP4 fixture;
- non-Warrior selection falling back to Warrior gameplay;
- the RP4 hybrid mapping until NBG0 ownership, PNT paging, per-object priority,
  bundle hardening, and live resource/readback checks pass.

### Gaps

- complete no-skip legal/story/Round 1 presentation;
- wider-route row-scroll classification and complete layer priority/mutation
  evidence beyond the selected RP4 interval;
- live RP4 second-page crossing, source-class sprite priority, NBG0 ownership,
  and fixture/production separation;
- full Round 1 cast/emission/collision/AI/stage systems;
- restored verified CDDA and complete audio;
- physical 60 Hz and soak evidence.

## Next implementation order

1. Finish and supervisor-accept RP4: NBG0 ownership, explicit PNT pages,
   per-object priority, fixture separation, bounds, and live resource proof.
2. Run RP5 G0/CDDA residency and RP6 semantic-scene finalization in isolated
   ownership lanes.
3. Pass RP7 shared primitives and integrate content Batches A-C through the
   Round 2 title.
4. Close the continuous-route and Round 1 presentation parity checks, including
   audio and physical presentation evidence.
5. Resume S5 Room 1 behavior, then complete S3/S4 and stage translation.
6. Perform full S6 resource and physical-hardware validation.

The granular package status is in `docs/ROUND1_EXECUTION_PLAN.md`; the exact
first task and dirty-worktree state are in `docs/NEXT_AGENT_PROMPT.md` and
`docs/AGENT_HANDOFF.md`.
