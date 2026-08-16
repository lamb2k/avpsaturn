# Architecture

## Direction

The prototype treats the Saturn as a split renderer rather than trying to make
VDP1 reproduce a complete CPS2 frame by itself:

```text
CD assets -> 4 MB RAM cartridge -> selected 192x192 cels -> VDP1 VRAM cache
                                         |
gameplay/lane state -> depth-sorted instances -> VDP1 sprite command list

512x256 indexed corridor -------------------------------> VDP2 NBG1
HUD text ------------------------------------------------> VDP2 NBG0
```

VDP2 owns the large, reusable background image. VDP1 owns characters, shadows,
and hit effects. Multiple enemies instance the same resident crawler frames, so
enemy count costs commands and fill rate but not a duplicate texture allocation
for every actor.

## Why 4bpp matters at 192x192

| Resource | 8bpp | Packed 4bpp | Saving |
| --- | ---: | ---: | ---: |
| One 192x192 cel | 36,864 B | 18,432 B | 18,432 B |
| Eight cache slots | 294,912 B | 147,456 B | 147,456 B |

Palette index zero is transparent, leaving 15 visible colors per subpalette.
One 256-color CRAM allocation is divided into sixteen 16-color banks. The test
uses separate player, crawler, and effect banks.

The current VDP1 texture working set is approximately:

| Allocation | Bytes |
| --- | ---: |
| Four always-resident player cels | 73,728 |
| Seven always-resident crawler cels | 129,024 |
| Eight replaceable 192x192 slots | 147,456 |
| Shadow and hit effect | 2,560 |
| Total texture data | 352,768 |

This leaves useful room inside VDP1's 512 KiB for command tables and engine
overhead. A 32-slot 192x192 cache would require 589,824 bytes by itself and is
therefore not a viable Saturn configuration.

## Animation and additional frames

Additional animation frames live on disc and in the 4 MB cartridge, not all in
VDP1 VRAM. The runtime swaps only the two cels needed by the current player
action into replaceable slots. The X-button stress mode cycles the remaining
slots and exposes total copied bytes and swap count on the HUD.

The next version should replace the synchronous proof-of-path replacements with
an explicit queue:

1. Animation state predicts the next clip.
2. The master SH-2 schedules a bounded transfer request.
3. SCU DMA copies one or more cels during a safe transfer window.
4. The cache slot becomes visible only after completion.
5. Gameplay retains a resident fallback cel if a requested frame is late.

That is how the team can add more frames without making animation count equal
to permanent VDP1 residency.

## AI-upscaled production path

AI upscaling should happen offline. The runtime format stays intentionally
simple:

1. Extract or author a legally usable source frame.
2. Upscale to a consistent high-resolution character sheet.
3. Clean silhouettes and stabilize repeated costume/facial details by hand.
4. Place each pose on a 192x192 canvas with a fixed ground contact and pivot.
5. Quantize each character family to a shared 15-visible-color palette.
6. Pack two pixels per byte, high nibble first.
7. Validate dimensions, byte count, palette range, and hashes.

Upscaling increases spatial detail; it does not generate credible in-between
animation by itself. New frames need pose-aware generation or drawing plus
manual timing, contact, hitbox, and palette cleanup.

## Current limitations

- 320x224 rather than the proposed 352x224 display mode
- synchronous Jo Engine sprite replacement rather than a measured SCU DMA queue
- one VDP2 bitmap layer rather than a multi-plane tile/line-scroll stage
- four enemies and a two-frame action cache, not an arcade-content-complete room
- procedural silhouettes, not production or AI-upscaled character art
- no audio path in this capability build
