# Alien vs. Predator Sega Saturn private capability test

This repository is a private engineering prototype for testing a native Sega
Saturn conversion of Capcom's CPS2 Alien vs. Predator. It is not an emulator:
the build cross-compiles SH-2 code and feeds reconstructed graphics to VDP1 and
VDP2. It currently proves an authentic-asset Stage 1 route slice, not a content-
complete or frame-exact port.

Current milestone:

- verifies a user-supplied `avspu` ROM set with official MAME 0.289
- captures a deterministic Stage 1 reference and CPS2 video state
- reconstructs the captured CPS2 graphics region byte-for-byte
- decodes CPS2 background tilemaps, object commands, palettes, and priority
- records 361 active-bank samples across the deterministic Stage 1 route and
  reduces the captured Predator assemblies to 87 unique poses
- preserves original sprite scale and exact 15-color CPS2 subpalettes
- animates the first authentic ten-pose Predator attack from three aligned
  VDP1 palette layers backed by the Saturn 4 MB cartridge
- animates a temporally tracked ten-pose blue alien sequence through one
  replaceable VDP1 slot over a reconstructed VDP2 stage
- runs a capture-derived first-room lifecycle with five opening enemies, three
  reinforcements, a locked combat boundary, clear hold, and exit transition
- transitions into a reconstructed industrial boss room, spawns an exact
  capture-derived Chrysalis assembly, and reaches a native Stage Clear state
- draws the eight bounded enemy actors from one shared VDP1 cel slot with four
  exact CPS2 alien palettes
- boots with a palette-preserving 352x224 VDP1 reference surface containing
  the complete horizontally fitted CPS2 object/priority result
- boots in the Saturn's native 352x224 mode with the 4 MB expansion cartridge
- builds a mixed-mode disc with the verified Stage 1 QSound route rendered as
  native Saturn CD audio track 2
- runs a small native lane-combat model; enemies wait for the first input

The boot scene is intentionally stable for visual comparison. It uses the
active CPS2 object-RAM bank and reconstructs the final visible object result
after CPS2 tilemap-priority masking. The converter retains the 384x224 source
oracle offline and builds a 352x224 Saturn display asset from it. The
presentation is not yet frame-exact: the HUD is static
and the boot oracle is flattened
rather than actor-driven. On first input, the build switches to native gameplay,
whose player attack now uses an authentic ten-pose CPS2 sequence. It still does
not yet bind the extracted enemy poses to the arcade's complete enemy state
machine, exact spawn timing, isolated event sound effects, or every intermediate
Stage 1 room and action.

The Saturn has no 384-pixel low-resolution output. The selected 352x224 mode
keeps all 224 source lines. The runtime fits all 384 horizontal source pixels
into 352 output pixels, an 8.33% horizontal compression. Backgrounds are
pre-scaled into a 469-pixel content region inside the 512-pixel VDP2 bitmap and
displayed at 1:1; this avoids an emulator-dependent VDP2 reduction path. Black
bands outside the 352x224 viewport in a resizable emulator window are
letterboxing and do not remove game pixels. Physical display overscan remains
a separate hardware acceptance test.

## Repository and content boundary

This directory is its own Git repository on
`prototype/private-capability-test`. ROMs, captures, decoded graphics, generated
headers, CD staging files, and disc images are ignored and must never be
committed.

Use only a legally obtained ROM set that you are authorized to use. Nothing in
this repository grants distribution rights to Capcom code or assets. Any work
beyond a private capability test, including team distribution, public demos,
promotion, or release, requires an explicit rights-holder and licensing review.

## Build

Place the complete USA 940520 MAME set in `avspu/`, then run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_engine.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_reference.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Clean -Release
```

The build validates the ROM set, reuses or creates the deterministic MAME
capture, regenerates ignored Saturn assets, runs the strict host model tests,
cross-compiles for SH-2, and produces ignored `game.cue`, `game.iso`, and
`stage1_audio.wav` files.
It also writes `build/hardware_release_manifest.txt` with the image hashes and
hardware profile. Keep all three files together and select the cue on a loader.
Use `prepare_avsp_port.ps1 -RefreshCapture` to deliberately recapture the MAME
reference.

Jo Engine is pinned to commit `556d081146211b6a1cfa6591d70f9487d406758b`.

## Run

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_emulator.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

`run.ps1` launches Yaba Sanshiro with a 32 Mbit DRAM cartridge, the Saturn 4 MB
RAM expansion. Controls are D-pad to move, A to attack, B to dash, C for the
special action, and X to toggle the diagnostic HUD. The launcher no longer
disables emulator audio.

## Real hardware

Real Sega Saturn hardware is the acceptance target. Build the normal release
profile with `build.ps1 -Clean -Release`; diagnostic `-VisualTest` and
`-EncounterTest` images are not release candidates. The console needs an
authorized homebrew boot path plus compatible 4 MB DRAM support. See
[docs/HARDWARE_TEST.md](docs/HARDWARE_TEST.md) for the exact cold-boot,
controller, video, encounter, and soak-test route. Physical-hardware validation
is still pending.

## Verified status

Verified on August 16, 2026:

- official MAME reports the local `avspu` set as good
- the Python CPS2 graphics reconstruction matches MAME's 16 MiB `:gfx` region
- 54 captured commands decode from the verified active CPS2 object-RAM bank
- 361 four-frame-spaced captures retain the recorded active object bank; an
  independent two-bank render check confirms bank 2 at frames 2880 and 4200
- the player timeline contains 87 unique assemblies, and its first ten-pose
  attack sequence runs from cartridge-resident source cels through three VDP1
  texture slots
- the independently visible right-side blue alien is tracked across frames
  4164-4200 and its ten authentic poses run through one replaceable VDP1 slot
- an exhaustive frame-local grouping manifest separates verified actors,
  ground-shadow sprites, and props from edge fragments awaiting temporal proof
- exact layered cels retain original scale and CPS2 palette pens
- the native model passes 12,000 deterministic frames, including the idle boot
  gate and the complete 5+3 opening-room lifecycle
- a controller-only route test reaches Stage Clear without changing actor
  health, positions, encounter state, or timers outside normal player input
- the encounter diagnostic visibly reaches five active enemies, eight KOs,
  room clear, the Chrysalis room, boss defeat, and Stage Clear in Yaba Sanshiro
- the native audio module links successfully and the mixed-mode cue exposes a
  168.015-second stereo 16-bit 44.1 kHz Stage 1 QSound reference as CD track 2
- the final visible object/priority result fits a single 78,848-byte 352x224
  VDP1 8bpp display surface with 76 visible colors; the ignored converter
  output also retains the 86,016-byte 384x224 source oracle
- the release SH-2 build, link, ISO, and cue generation complete successfully
- Yaba Sanshiro boots in 352x224 with the 4 MB cartridge, shows both horizontal
  source edges and all 224 source lines with no framebuffer black bars, and
  displays the asset working set over the reconstructed Stage 1 background/HUD

Next proof gate: verify the full-width mapping and CD audio on physical Saturn,
then isolate QSound event cues for SCSP PCM playback and replace the approximate
route gaps with the remaining captured rooms, actors, and actions.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/TEST_PLAN.md](docs/TEST_PLAN.md).
