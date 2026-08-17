# Architecture

## Native conversion direction

This is a native Saturn renderer and gameplay shell, not a CPS2 emulator.

```text
local avspu ROM -> MAME-verified CPS2 decode -> generated CD/cartridge assets
                                              |
                               exact 4bpp palette layers -> VDP1 actors
                               512x256 indexed bitmap  -> VDP2 NBG1

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

The working set contains seven 192x192 packed 4bpp cels, or 129,024 bytes of
texture data: two idle Predator layers, three attack Predator layers, and two
alien cels. Four exact CPS2 palette banks occupy one Saturn 256-color CRAM
allocation. This fits comfortably in VDP1 texture memory and leaves room for
commands and a future animation cache.

## Background and HUD

The converter reconstructs CPS2 scroll layers from captured graphics RAM,
CPS-A/CPS-B registers, tile graphics, and palettes. The present build quantizes
that 512x256 reconstruction into a VDP2 256-color bitmap. The arcade HUD is
currently baked from the captured scroll layer, so its displayed values are
static and are not yet driven by native gameplay state.

## What is exact and what is not

Exact in the current milestone:

- CPS2 graphics-region reconstruction
- selected object pixels, scale, transparency, and palette pens
- selected background/HUD capture reconstruction
- aligned multi-palette VDP1 assembly

Still approximate or incomplete:

- actor grouping from all 53 captured object commands
- enemy variants, palettes, poses, count, and exact object priority
- animation/state timing and full frame sets
- dynamic HUD values, scroll behavior, level triggers, combat, AI, and audio
- 384-wide CPS2 framing; the Jo Engine target is currently 320x224

## Next implementation sequence

1. Group captured CPS2 commands into complete actors and props.
2. Emit tight per-actor/per-palette cels and pivot metadata.
3. Reproduce the MAME reference frame through VDP1 object ordering.
4. Capture successive gameplay states and build animation manifests.
5. Replace prototype combat with Stage 1 scripts, collision, spawn, and camera
   data.
6. Add bounded CD-to-cartridge prefetch and VDP1 cache scheduling.
7. Port audio, complete the level, and verify on real Saturn hardware.

Additional frames should live on disc and in the 4 MB cartridge. Only the
current and predicted cels should occupy VDP1 VRAM. AI upscaling is a separate
offline enhanced-edition asset path; it should not be mixed into the exact
arcade baseline until the native reconstruction is validated.
