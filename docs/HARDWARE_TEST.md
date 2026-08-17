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

Keep `game.cue`, `game.iso`, and `stage1_audio.wav` together. Select `game.cue` when the loader asks
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
- `game.cue`, `game.iso`, and `stage1_audio.wav` from the same normal-release build
- cold boot, not an in-game reset from another title

## Acceptance route

1. Cold boot and confirm the reference scene appears without an asset error.
2. Confirm the full 224-line picture is stable in 352x224 and the full-width
   mapping shows both horizontal source edges. Record any CRT, scaler, or
   capture-device overscan separately from the digital framebuffer.
3. Press Start at the title, then B at Predator Warrior select, and confirm the
   native route reaches the Round 1 title before gameplay begins.
4. Verify D-pad lane movement advances the complete 48-frame captured walk
   loop; verify A weapon, B melee attack, neutral C jump,
   direction+C dash, any two face buttons emergency attack, and X diagnostic
   HUD. Confirm the top panel, Player 2 prompt, and Over Heat meter stay fixed
   while the street scrolls; one A press must visibly drain the weapon meter
   and its refill must advance without moving the HUD. Confirm all five
   controlled actions use their captured clips, return
   cleanly to idle, retain all three palette layers, and never show a partially
   replaced cel. Allow an enemy to land a normal hit and then a KO; confirm the
   exact 25-frame hit reaction and 96-frame launch/fall/bounce sequence play to
   the standing full-health respawn without input corruption.
5. Confirm Stage 1 CD audio begins after the first input, remains stereo and
   free of stalls through the room transition, and survives a pause/resume.
   Press A once and confirm the isolated Predator weapon cue starts five action
   frames later, remains stereo, and neither stops nor ducks the CDDA track.
   Repeated A presses after the heat meter recovers must replay it cleanly
   without channel lock-up or cartridge-read corruption.
6. Fight through the five-enemy opening wave and three-enemy reinforcement wave.
   Confirm enemies can simultaneously show unlike walk, attack, hit, and KO
   poses without one actor changing another actor's cel. The proven alien clips
   must last 39, 120, 36, and 140 frames respectively, with no KO flicker.
7. Confirm eight total KOs unlock the room and moving right reaches the exit
   transition.
8. Defeat Chrysalis and confirm the native Stage Clear state.
9. Leave the encounter running for ten minutes and watch for partial sprites,
   palette corruption, controller loss, CD stalls, or dropped video sync.

Record console model/region, boot device, cartridge, display path, result, and
any visible failure. The hardware gate remains open until this route passes on
a physical Saturn; an emulator screenshot cannot close it.
