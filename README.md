# AvP-style Sega Saturn Capability Test

This is a private, original-asset engineering slice for testing whether a
CPS2-scale belt-scroller presentation can be rebuilt around the Sega Saturn's
strengths. It is not a port of Capcom's game and contains no Alien vs. Predator
ROM data, art, audio, maps, or source code.

The prototype currently provides:

- 192x192 packed 4bpp player and enemy animation cels
- one player and four shared-texture enemies with lane/depth sorting
- an eight-slot VDP1 animation cache with live replacement counters
- a 512x256 indexed VDP2 corridor bitmap with camera parallax
- walk, dash, attack, special, hit, KO, enemy pursuit, and respawn states
- deterministic procedural placeholders and a hash-locked asset manifest
- a mandatory 4 MB extended RAM cartridge
- a 320x224 NTSC presentation target

The 320-wide output is intentional for this first build. Jo Engine's current
core path is fixed around 320-wide coordinates. A 352x224 mode should be a
separate engine/display milestone after the 192x192 sprite and cache path is
stable.

## Repository boundary

This directory is its own Git repository. Active development is on
`prototype/private-capability-test`. The existing Brooklyn Bangout repositories
are not dependencies and are not modified by this project.

Jo Engine is pinned to commit `556d081146211b6a1cfa6591d70f9487d406758b`.
`setup_engine.ps1` creates an ignored checkout under `.deps/joengine` and applies
the versioned patch in `engine-patches/`.

## Build

From PowerShell in this directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_engine.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Clean -Release
```

To use an existing local Jo Engine checkout as the clone source:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_engine.ps1 -SourceRepo ..\joengine
```

The build validates the procedural assets, runs the strict host test through
WSL/GCC, cross-compiles for SH-2, and produces `game.cue` and `game.iso`.

## Run the playable level

The validated Windows emulator path is Yaba Sanshiro 2 v1.20.37. Download the
hash-pinned official package and launch the disc image with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_emulator.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

Complete Yaba Sanshiro's first-run setup if prompted, then rerun `run.ps1`.
The launcher selects the 32 Mbit DRAM cartridge, which is the Saturn's 4 MB
expansion RAM. Do not select 4 Mbit Backup RAM; that is a save-memory device.

## Controls

- D-pad: move across and between lanes
- A: attack
- B: dash while held
- C: special attack
- X: toggle repeated cache-replacement stress

The HUD reports player health, score, Jo Engine's VDP1 usage percentage, cache
slot count, detected cartridge, bytes copied, replacement count, and stress
state.

## Validation status

Verified on August 16, 2026:

- deterministic asset regeneration and SHA-256 comparison pass
- all 15 actor cels are 192x192, 18,432-byte packed 4bpp files
- gameplay model passes 12,000 deterministic frames under strict C90 warnings
- Jo Engine patch applies cleanly to the pinned commit
- release SH-2 compilation, link, ISO construction, and cue construction pass
- Yaba Sanshiro 2 v1.20.37 boots the release image with its HLE BIOS path
- the 32 Mbit DRAM cartridge is detected as 4 MB
- the playable corridor renders the 192x192 player, four pursuing enemies,
  background, HUD, transparency, overlap, and live cache counters

The booted build reported 77% Jo Engine VDP1 usage, 36,864 DMA bytes, and two
cache swaps in the captured encounter. See [the emulator-native boot capture](docs/boot-proof.bmp).
Attack/special cache replacement, stress mode, sustained frame pacing, and real
Saturn behavior remain to be measured.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/TEST_PLAN.md](docs/TEST_PLAN.md) for the engineering rationale and next
gates.
