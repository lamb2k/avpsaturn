# Alien vs. Predator Sega Saturn private capability test

This repository is a private engineering prototype for testing a native Sega
Saturn conversion of Capcom's CPS2 Alien vs. Predator. It is not an emulator:
the build cross-compiles SH-2 code and feeds reconstructed graphics to VDP1 and
VDP2. It currently proves an authentic-asset presentation slice, not a complete
Stage 1 port.

Current milestone:

- verifies a user-supplied `avspu` ROM set with official MAME 0.289
- captures a deterministic Stage 1 reference and CPS2 video state
- reconstructs the captured CPS2 graphics region byte-for-byte
- decodes CPS2 background tilemaps, object commands, palettes, and priority
- preserves original sprite scale and exact 15-color CPS2 subpalettes
- draws the Predator from two or three aligned VDP1 palette layers
- draws exact alien object pixels through VDP1 over a reconstructed VDP2 stage
- boots with a lossless 8-bit VDP1 reference surface containing the complete
  captured CPS2 object pass, excluding hardware shadow-mask commands
- boots at 320x224 with the Saturn 4 MB expansion RAM cartridge
- runs a small native lane-combat model; enemies wait for the first input

The boot scene is intentionally stable for visual comparison. It now reproduces
the captured object layout and 78 visible object colors at original scale, but
it is not yet frame-exact: CPS2 hardware shadow masks are omitted instead of
being translated to a Saturn shadow pass, the 384-wide frame is center-cropped
to 320, and the HUD is static. On first input, the build switches to native
gameplay, whose smaller working set still reuses two alien cels and does not yet
reproduce the arcade animation state, combat, audio, or level progression.

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
cross-compiles for SH-2, and produces ignored `game.cue` and `game.iso` files.
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
special action, and X to toggle the diagnostic HUD.

## Verified status

Verified on August 16, 2026:

- official MAME reports the local `avspu` set as good
- the Python CPS2 graphics reconstruction matches MAME's 16 MiB `:gfx` region
- 53 captured CPS2 object commands decode into the reference scene
- exact layered cels retain original scale and CPS2 palette pens
- the native model passes 12,000 deterministic frames, including the idle boot
  gate
- the complete captured object pass fits a single 86,016-byte VDP1 8bpp surface
  with 78 visible colors
- the release SH-2 build, link, ISO, and cue generation complete successfully
- Yaba Sanshiro boots the image with the 4 MB cartridge and displays the exact
  asset working set over the reconstructed Stage 1 background/HUD

Next proof gate: translate the CPS2 shadow-mask objects, then split the full
reference surface into actor-grouped animation assets and complete the first
playable Stage 1 encounter.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/TEST_PLAN.md](docs/TEST_PLAN.md).
