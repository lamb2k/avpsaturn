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

The active VDP1 working set contains seven 192x192 packed 4bpp slots, or 129,024
bytes of texture data: two idle Predator layers, three replaceable attack
layers, and two alien cels. The first attack sequence contains ten captured
poses and three layers per pose, totaling 552,960 source bytes in the 4 MB
cartridge. Each pose replaces only the three 55,296-byte attack slots. Four
exact CPS2 palette banks occupy one Saturn 256-color CRAM allocation. This
separates source residency from VDP1 texture residency and leaves room for
commands and a larger animation cache.

Before gameplay starts, a separate reference mode draws the final visible CPS2
object/priority result as one 384x224 8bpp VDP1 surface. Its 76 visible source
colors fit losslessly inside one 256-color Saturn palette and consume 86,016
bytes. The converter derives this surface from the MAME reference after removing
the reconstructed background, so tilemap-priority occlusion is already resolved.
This is a flattened comparison oracle, not the final animation architecture.
The first player input replaces it with the actor working set and native
transforms.

## Background and HUD

The converter reconstructs CPS2 scroll layers from captured graphics RAM,
CPS-A/CPS-B registers, tile graphics, and palettes. The present build quantizes
that 512x256 reconstruction into a VDP2 256-color bitmap. The arcade HUD is
currently baked from the captured scroll layer, so its displayed values are
static and are not yet driven by native gameplay state.

## Display mapping

The arcade active picture is 384x224. The Saturn has no native 384-pixel
low-resolution mode, so the project force-includes a project-owned video
configuration selecting SGL's `TV_352x224` for every translation unit. This
preserves all 224 scanlines and original source-pixel scale while center-cropping
16 pixels at each horizontal edge. The remaining edge content will be exposed
through arcade-derived camera motion; fixed HUD elements must be moved inside
the 352-pixel safe area when the HUD becomes native. No horizontal resampling is
used in the exact baseline.

## What is exact and what is not

Exact in the current milestone:

- CPS2 graphics-region reconstruction
- selected object pixels, scale, transparency, and palette pens
- selected background/HUD capture reconstruction
- aligned multi-palette VDP1 assembly
- active CPS2 object-RAM bank and final visible boot object/priority result
- Saturn-native 352x224 initialization and original-scale 384-to-352 crop
- first ten-pose captured Predator attack sequence

Still approximate or incomplete:

- temporal confirmation of enemy and prop groupings beyond the player sequence
- enemy variants, palettes, poses, count, and exact object priority
- remaining player states, enemy animation/state timing, and full frame sets
- dynamic HUD values, scroll behavior, level triggers, combat, AI, and audio
- native HUD safe-area placement and arcade-derived camera behavior for the
  unavoidable 16-pixel-per-side crop

## Next implementation sequence

1. Extend the captured player timeline into idle, walk, hit, and KO clips.
2. Group enemy commands temporally and emit enemy animation and priority data.
3. Replace prototype combat with Stage 1 scripts, collision, spawn, and camera
   data.
4. Add bounded CD-to-cartridge prefetch and VDP1 cache scheduling.
5. Port audio, complete the level, and verify on real Saturn hardware.

Additional frames should live on disc and in the 4 MB cartridge. Only the
current and predicted cels should occupy VDP1 VRAM. AI upscaling is a separate
offline enhanced-edition asset path; it should not be mixed into the exact
arcade baseline until the native reconstruction is validated.
