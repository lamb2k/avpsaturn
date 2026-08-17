# Architecture

## Native conversion direction

This is a native Saturn renderer and gameplay shell, not a CPS2 emulator.

```text
local avspu ROM -> MAME-verified CPS2 decode -> generated CD/cartridge assets
                                              |
                               exact 4bpp palette layers -> VDP1 actors
                               512x256 indexed bitmap  -> VDP2 NBG1
                               QSound reference mix   -> Saturn CDDA track 2

Saturn input -> native SH-2 lane/combat model -> actor transforms and ordering
```

MAME is an offline reference oracle. The Saturn executable does not contain a
68000/Z80 interpreter, CPS2 register emulation, or ROM access. Python reproduces
the CPS2 ROM interleave and recursive 2 MiB bank unshuffle, then decodes the
captured video state into Saturn-ready local assets.

## Exact sprite path

CPS2 characters are assemblies of 16x16 4bpp tiles, frequently using more than
one 16-color subpalette per actor. Flattening an actor into one quantized bitmap
caused the earlier oversized, approximate result.

The current path instead:

1. reads CPS2 object commands and tile codes
2. preserves original pixels and scale
3. maps CPS2 pens 0-14 to Saturn indices 1-15; Saturn index 0 stays transparent
4. emits one 192x192 VDP1 cel per source palette layer
5. draws all layers at the same pivot and depth

The active actor VDP1 working set contains six 192x192 packed 4bpp slots, or
110,592 bytes of texture data: two idle Predator layers, three replaceable
attack layers, and one replaceable alien layer. The first attack sequence
contains ten captured poses and three layers per pose, totaling 552,960 source
bytes in the 4 MB cartridge. The first blue-alien track adds ten single-layer
poses, or 184,320 source bytes. Each pose update replaces only its corresponding
55,296-byte player group or 18,432-byte enemy slot. Four exact CPS2 alien
variants plus the three player-layer palettes occupy seven 16-color banks in
one Saturn 256-color CRAM allocation. Eight bounded enemy actors reuse the same
current alien VDP1 texture, so the crowd adds draw commands and transforms
rather than eight duplicate texture allocations. This separates source
residency from VDP1 texture residency and leaves room for commands and a larger
animation cache.

The converter retains the final visible CPS2 object/priority result as an
offline 352x224 8bpp comparison surface. Its 76 visible source colors fit
losslessly inside one 256-color palette and consume 78,848 bytes; only the
horizontal coordinates are resampled from 384 to 352. An ignored 86,016-byte
384x224 source oracle is retained as well. These are flattened comparison
oracles, not the final animation architecture or the normal release boot path.

The normal release instead allocates two 78,848-byte VDP1 frontend surfaces:
the verified frame-1440 Press Start state and frame-1800 Predator Warrior
selection state. Their 110 and 115 source colors respectively remain lossless.
The native controller state machine waits for Start, then A, before beginning
the Round 1 title and gameplay route.

After confirmation, the menu surface becomes a reusable route-sequence slot.
Thirteen verified 384x224 capture anchors are horizontally fit to 352x224,
palette-indexed without color loss, and count/value RLE encoded. Their
compressed data is loaded through Jo Engine's cartridge-backed allocator before
track 2 begins. State changes decode into one 78,848-byte work buffer, replace
the existing VDP1 texture, and update the same 256-color CRAM bank. This avoids
additional VDP1 residency and data-track seeks during CDDA playback.

## Background and HUD

The converter reconstructs CPS2 scroll layers from captured graphics RAM,
CPS-A/CPS-B registers, tile graphics, and palettes. It horizontally fits the
512x256 reconstruction into a 469-pixel content region inside a 512x256 VDP2
256-color bitmap. The arcade HUD is
currently baked from the captured scroll layer, so its displayed values are
static and are not yet driven by native gameplay state.

## Display mapping

The arcade active picture is 384x224. The Saturn has no native 384-pixel
low-resolution mode, so the project force-includes a project-owned video
configuration selecting SGL's `TV_352x224` for every translation unit. All 224
scanlines are preserved. The runtime uses one full-width mapping: the converter
pre-scales VDP2 content by 352/384, VDP2 displays it at a deterministic 1:1,
and VDP1 uses the matching 0.9167 horizontal scale for actors. This avoids
losing HUD and playfield edges at the cost of 8.33% horizontal compression.
Pre-scaling replaced the earlier runtime NBG1 reduction experiment because its
SGL/emulator register path could silently fall back to a 1:1 crop.

## Sound mapping

The Saturn executable initializes SGL's native SCSP/CD audio driver. For the
current private proof, MAME renders the verified QSound Stage 1 route offline at
stereo 16-bit 44.1 kHz. The build trims save-state preroll and adds that ignored
WAV as CDDA track 2; gameplay starts it on the first encounter input. No Z80 or
QSound emulation runs on Saturn. This reference mix proves the end-to-end disc,
driver, and output route, but it contains the automated capture's mixed music
and effects. The production path must isolate music stems and event cues, keep
long music on CDDA, and trigger short attack, impact, enemy, boss, and voice
cues through bounded SCSP PCM channels.

## What is exact and what is not

Exact in the current milestone:

- CPS2 graphics-region reconstruction
- selected object pixels, scale, transparency, and palette pens
- selected background/HUD capture reconstruction
- lossless Press Start and Predator Warrior selection key states
- lossless key states for the Round 1/barricade sequence, doorway/interior
  transition, boss defeat, Stage Clear, results, intermission, and Round 2 title
- aligned multi-palette VDP1 assembly
- active CPS2 object-RAM bank and final visible boot object/priority result
- Saturn-native 352x224 initialization with one deterministic full-width fit
- first ten-pose captured Predator attack sequence
- first ten-pose temporally tracked blue-alien sequence
- first-room 5+3 crowd budget, four alien palette variants, combat lock, clear,
  and exit-state lifecycle

Still approximate or incomplete:

- temporal confirmation of remaining enemy variants, actions, and prop groups
- exact enemy pose selection, spawn coordinates/timing, AI, and object priority
- remaining player states, enemy animation/state timing, and full frame sets
- complete attract-mode, menu-transition, and character-select animation
- full animation between the verified route key states
- dynamic HUD values, exact scroll behavior, level triggers, combat, and AI
- isolated, event-synchronized QSound effects on native SCSP PCM channels
- native HUD safe-area placement and arcade-derived camera behavior for CRT
  overscan variability

## Next implementation sequence

1. Extend the captured player timeline into idle, walk, hit, and KO clips.
2. Extend the proven blue-alien track into attack, hit, and KO clips and repeat
   the temporal grouping for the remaining enemy palettes.
3. Replace prototype combat with Stage 1 scripts, collision, spawn, and camera
   data.
4. Add bounded CD-to-cartridge prefetch and VDP1 cache scheduling.
5. Replace the CDDA reference mix with isolated music/SFX assets and verify the
   complete level on real Saturn hardware.

## Hardware boundary

The executable is linked for the Saturn SH-2 and uses SGL/Jo Engine hardware
paths for CD files, controller port 1, VDP1 sprites, VDP2 background, and CRAM.
Startup checks address `0x24ffffff` for the physical 32 Mbit cartridge signature;
without it, the build reports `4MB RAM CART REQUIRED` and does not enter the
runtime. The disc is an ISO9660 Mode 1 image with Sega Saturn IP boot data and
NTSC `TV_352x224` initialization. Emulator configuration is not part of the
executable.

`build/hardware_release_manifest.txt` fingerprints the cue and ISO that must be
kept together. These structural checks establish a hardware-oriented image, but
only the cold-boot and soak route in `HARDWARE_TEST.md` can close the physical
hardware gate.

Additional frames should live on disc and in the 4 MB cartridge. Only the
current and predicted cels should occupy VDP1 VRAM. AI upscaling is a separate
offline enhanced-edition asset path; it should not be mixed into the exact
arcade baseline until the native reconstruction is validated.
