# Real Saturn hardware test

The physical Sega Saturn is the acceptance target. Emulator results are an
intermediate check only. The current build is native SH-2/SGL code, reads its
asset pack through the Saturn CD filesystem, renders through VDP1/VDP2, polls
controller port 1, and requires a detected 32 Mbit (4 MB) DRAM cartridge.

## Build the hardware image

Use the normal release profile. Do not put `-VisualTest` or `-EncounterTest`
on the hardware candidate:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Clean -Release
```

Keep `game.cue` and `game.iso` together. Select `game.cue` when the loader asks
for a disc descriptor. `build/hardware_release_manifest.txt` records the image
hash, build profile, video mode, disc format, and cartridge requirement. ROMs,
generated assets, images, and the manifest remain ignored private artifacts.

The console needs an authorized homebrew-capable boot path and compatible 4 MB
DRAM support. An optical-drive emulator that leaves the cartridge slot free is
the simplest diagnostic configuration. A burned-disc workflow is acceptable
only when its boot method and cartridge can coexist. This repository does not
alter console copy protection or supply copyrighted disc data.

## Required first-pass setup

- NTSC Sega Saturn connected through a capture device or a display that accepts
  240p-family timing
- digital Saturn controller in port 1
- working 32 Mbit DRAM expansion cartridge
- `game.cue` plus `game.iso` from the same normal-release build
- cold boot, not an in-game reset from another title

## Acceptance route

1. Cold boot and confirm the reference scene appears without an asset error.
2. Confirm the full 224-line picture is stable in 352x224; the intended crop is
   16 arcade pixels at each horizontal edge, with no vertical crop or scaling.
3. Press a direction and confirm the build changes from the static reference to
   native gameplay.
4. Verify D-pad lane movement, A attack, B dash, C special, and X diagnostic HUD.
5. Fight through the five-enemy opening wave and three-enemy reinforcement wave.
6. Confirm eight total KOs unlock the room and moving right reaches the exit
   transition.
7. Leave the encounter running for ten minutes and watch for partial sprites,
   palette corruption, controller loss, CD stalls, or dropped video sync.

Record console model/region, boot device, cartridge, display path, result, and
any visible failure. The hardware gate remains open until this route passes on
a physical Saturn; an emulator screenshot cannot close it.
