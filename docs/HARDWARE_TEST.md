# Real Saturn hardware test

The physical Sega Saturn is the acceptance target. Emulator results are an
intermediate check only. The current build is native SH-2/SGL code, reads its
asset pack through the Saturn CD filesystem, renders through VDP1/VDP2, polls
controller port 1, and requires a detected 32 Mbit (4 MB) DRAM cartridge.
The runtime registers both 2 MB cartridge banks; failure to access DRAM1 at
`0x22600000` is a hardware failure, not a reason to drop animation or audio.

## Build the hardware image

Use the normal release profile. Do not put `-VisualTest`, `-EncounterTest`,
`-BossHitTest`, or `-BossKoTest` on the hardware candidate:

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
   native route holds the capture-derived 240-frame confirmation interval and
   reaches the Round 1 title before gameplay begins. Listen for both Round 1
   cues, the withdrawal composite, and the breach composite at their visual
   boundaries; none may clip or stall CDDA. Confirm wave one appears without
   an asset error when the completed withdrawal buffer becomes enemy-animation
   RAM.
4. Verify D-pad lane movement advances the complete 48-frame captured walk
   loop; verify A weapon, B melee attack, neutral C jump,
   direction+C dash, A+B emergency attack, and X diagnostic HUD. Confirm B+C
   remains melee and A+C remains weapon rather than triggering the emergency
   attack. Confirm the top panel, Player 2 prompt, and Over Heat meter stay fixed
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
   Press B repeatedly and confirm the melee composite begins three action
   frames after each accepted attack, retriggers cleanly, and does not silence
   the weapon cue or CDDA music.
   Let an alien connect and confirm the normal impact begins two frames after
   health loss and the player-damage cue begins three frames after health loss.
   Let the final contact KO the player and confirm its two-frame impact is
   audibly distinct while the same damage cue follows on frame 3. Both direct
   contact composites must coexist with weapon, melee, and CDDA audio without
   channel loss.
   At the Chrysalis-room entry, confirm the isolated boss cue starts eight
   frames after the visual anchor. After defeating Chrysalis, confirm the
   three-part defeat/Stage Clear sequence begins at +150 frames, remains stereo,
   and continues cleanly across Stage Clear into the results transition.
   At the street doorway, confirm the isolated voice-4 cue starts at +44. In
   the following interior transition, confirm the voice-13 cue starts at +38
   without clipping, replaying the previous cue, or interrupting boss channel 3.
6. Fight through the five-enemy opening wave and three-enemy reinforcement wave.
   Confirm enemies can simultaneously show unlike walk, attack, hit, and KO
   poses without one actor changing another actor's cel. The proven alien clips
   must last 39, 120, 36, and 140 frames respectively, with no KO flicker.
7. Confirm eight total KOs unlock the room and moving right reaches the exit
   transition.
8. Defeat Chrysalis and confirm the native Stage Clear state. With the
   diagnostic enabled, require `PCM OPEN 1111`, `PCM D/T 1/1`,
   `PCM SEQ 1/1`, and all `SEEN 1` latches before Round 2.
   Before the defeat, confirm Chrysalis cycles the 106-frame captured walk and
   changes through the complete 189-frame attack/recovery sequence, with three
   contacts at offsets 21/55/97, without clipping, partial cels, palette
   corruption, or a `BOSS ACTION` allocation/decode failure.
   Land a nonlethal melee strike and confirm the complete 40-frame captured hit
   reaction plays before Chrysalis returns to AI control. The ISO must retain
   `/SPR4/BACT.RLE` at 119,868 bytes and add `/SPR4/BHIT.RLE` at 5,900 bytes;
   their SHA-256 values are
   `a7efabb6894204475a6aacde4945c6cc4751b150d7d9007349566c86b78220f8`
   and `c4f6db6ce3ec9d3505a543bc8340b9bee949bde297c53dc2f386a10ffe501ebb`.
   Deliver the lethal strike and confirm the complete 428-frame captured KO:
   launch, changing airborne tumble, landing, and 60-frame grounded-corpse
   hold before the explosion surface. The ISO must also retain
   `/SPR4/BKO.RLE` at 43,232 bytes with SHA-256
   `9ad615f5e61615142d5be3b91a10fd16e9519ff304d204da704f9fe6e609f78a`.
   No `BOSS SUPPLEMENT BUFFER`, `BKO.RLE`, or `BOSS ACTION RLE` failure is
   permitted; the combined supplement must be loaded before CDDA begins.
   Confirm every boss-room add uses the distinct purple Stalker artwork and
   57-frame walk rather than a street-alien cel. Observe at least one 17-frame
   Stalker attack and one complete 157-frame KO with no `SACT.RLE`, Stalker
   RLE/index, palette-bank, or VDP1 replacement failure.
9. Leave the encounter running for ten minutes and watch for partial sprites,
   palette corruption, controller loss, CD stalls, or dropped video sync.

Record console model/region, boot device, cartridge, display path, result, and
any visible failure. The hardware gate remains open until this route passes on
a physical Saturn; an emulator screenshot cannot close it.
