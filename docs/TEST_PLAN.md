# Capability Test Plan

## Acceptance gate A: build integrity

- Clean setup checks out the pinned Jo Engine commit.
- The 4bpp patch applies without rejects.
- Generated assets match `asset_manifest.json` byte for byte.
- Strict host gameplay tests run for at least 10,000 deterministic frames.
- Release SH-2 link, ISO build, and cue build complete without warnings from the
  project sources.

Status: passed on August 16, 2026.

## Acceptance gate B: emulator render

Configure a 4 MB extended RAM cartridge and boot `game.cue` in a current Saturn
emulator. Confirm:

- no `4MB RAM CART REQUIRED` or asset failure message
- player palette uses the first 16-color bank
- all crawler instances use the second bank
- pixel index zero is transparent around every cel
- background appears behind actors and HUD appears in front
- mirrored actors retain the correct pivot and ground contact
- all four enemies can overlap without corrupting textures
- A and C replace the two action slots without a visible partial frame
- X stress mode increases both DMA byte and swap counters

Status: blocked in the current Windows session because bundled Kronos 2.1.5 and
Yabause 0.9.14 both reported that they could not initialize.

## Acceptance gate C: performance capture

Run a fixed 10-minute route with stress mode off and on. Capture:

- missed frames and frame-time distribution
- maximum Jo Engine VDP1 usage percentage
- maximum visible VDP1 command count
- cache replacements and bytes per second
- CD-to-cartridge load time at room entry
- any sprite corruption during overlapping attacks

Pass target: sustained 60 Hz with no partial cels, no palette-bank corruption,
and no gameplay stall longer than one frame after room load.

## Acceptance gate D: real Saturn

Test on a Saturn with a compatible 4 MB cartridge using an optical disc or
validated optical-drive emulator. Repeat gate C with video capture. The real
hardware result is authoritative for bus contention, VDP1 erase/draw timing,
and cartridge compatibility.

## Decision after the test

- If gate C and D pass comfortably, expand one player to a 12-16 frame movement
  and attack set before adding enemy types.
- If fill rate fails while cache replacement remains stable, reduce transparent
  canvas area or split actors into tighter VDP1 parts.
- If transfer timing fails, keep the 192x192 presentation but prefetch complete
  encounter banks at room boundaries.
- If VDP1 memory is the limiting factor, reduce resident frames before reducing
  visible color depth or enemy count.
