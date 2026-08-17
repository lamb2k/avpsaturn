# Architecture

## Native conversion direction

This is a native Saturn renderer and gameplay shell, not a CPS2 emulator.

```text
local avspu ROM -> MAME-verified CPS2 decode -> generated CD/cartridge assets
                                              |
                               exact 4bpp palette layers -> VDP1 actors
                               512x256 indexed bitmap  -> VDP2 NBG1
                               QSound reference mix   -> Saturn CDDA track 2

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

The active actor VDP1 working set contains two 192x192 idle Predator layers,
three replaceable 192x192 player-action layers, eight independent 288x192
alien layers, one replaceable 288x192 boss layer, and three screen-fixed 8bpp
HUD overlays: 353,280 bytes of texture data. The
isolated player
captures produce an exact 48-frame walk loop, plus 23-frame weapon, 22-frame
melee, 42-frame jump, 24-frame dash, 81-frame emergency-attack, 25-frame hit,
and 96-frame KO clips. Pose deduplication reduces them to 103 shared assemblies
and 309 palette-layer payloads. Count/value RLE compresses their 5,695,488
decoded bytes to one 417,488-byte indexed cartridge archive, avoiding 309
separate CD seeks at boot. The validated alien actor adds exact 39-frame walk,
120-frame attack, 36-frame hit, and 140-frame KO schedules. Forty-two shared
poses occupy 1,161,216 decoded bytes and compress to a 131,552-byte indexed RLE
archive. Source-omitted CPS2 flicker frames retain the last valid pose without
changing clip timing. Each actor owns one 27,648-byte VDP1 slot, so eight
enemies can display unlike animation frames concurrently. Four exact alien
variants, three player-layer palettes, and the boss palette occupy eight
16-color banks in one Saturn 256-color CRAM allocation. Menus and route stills
were moved off VDP1 to keep the texture working set at roughly 77% of the Jo
Engine VDP1 user area, leaving command-table and texture headroom.

A dense 900-frame replay tracks the native Chrysalis actor at `FF A3C0` and
extracts exact 44-frame leap, 106-frame walk, and 189-frame uninterrupted
attack/recovery timelines. Together with the independently verified frame-12660
idle assembly, 20 unique 288x192 poses compress from 552,960 decoded bytes to a
119,868-byte indexed RLE
archive. Only one 27,648-byte pose is decoded at a time. Its main-RAM buffer and
VDP1 texture are created on first boss draw, after the opening PCM phase has
ended; allocating it at cold boot exhausts the bounded startup heap in Yaba
Sanshiro. Walk loops at its captured duration. The replay restores player health
after each sampled frame, exposing three uninterrupted attack contacts at source
offsets 21, 55, and 97 for 10, 10, and 16 health units. The native boss attack
uses that same 189-frame visual/contact schedule, a 108-pixel fitted trigger
reach, a 122-pixel fitted contact reach, and two-pixel approach movement. Leap
is preserved in the archive but not yet attached to an inferred native
transition, and unclassified hit/KO palette-effect frames deliberately fall
back to the exact idle pose.

An independent unfrozen-health replay preserves the same verified frame-4080,
4164, and 4200 object/palette anchors. It records native player-health changes
on attack offsets 48 and 119, both on the same captured contact pose, and a
111-pixel approach over 38 frame intervals. The native model therefore uses
two contact checks, 68 source pixels of observed reach, and a three-source-pixel
approach step instead of the earlier guessed frame-12 contact and one-pixel step.
Each validated contact removes eight native health units.

The converter retains the final visible CPS2 object/priority result as an
offline 352x224 8bpp comparison surface. Its 76 visible source colors fit
losslessly inside one 256-color palette and consume 78,848 bytes; only the
horizontal coordinates are resampled from 384 to 352. An ignored 86,016-byte
384x224 source oracle is retained as well. These are flattened comparison
oracles, not the final animation architecture or the normal release boot path.

The normal release retains two 78,848-byte frontend surfaces in cartridge RAM:
the verified frame-1440 Press Start state and frame-1800 Predator Warrior
selection state. Their 110 and 115 source colors respectively remain lossless.
They and the later route stills are copied into the shared 512x256 VDP2 bitmap,
so full-screen states consume no VDP1 texture slots.
The native controller state machine waits for Start, then B, before beginning
the Round 1 title and gameplay route.

The native action interface preserves the three-button CPS2 layout on the
Saturn face buttons: A is weapon, B is melee attack, and C is jump. A direction
plus C requests a directional dash, and the captured A+B chord requests the
emergency attack. Other two-button chords retain their primary action rather
than triggering an unverified shortcut. All five controlled actions are bound
to their isolated CPS2 clips.
Native D-pad locomotion advances the isolated 48-frame CPS2 walk loop; its
12 four-frame poses and the first 24 repeated frames are capture-verified.
Automatic player hit and KO states use clips extracted from a natural enemy-
damage capture, including captured per-frame screen offsets for the KO launch,
fall, ground bounce, and respawn. Each action capture cold boots through the
frontend and begins from an identical object-RAM and palette baseline before
injecting one input; the damage route remains byte-identical to idle through
the common baseline. Native clip lengths match the captured return-to-idle or
respawn boundaries.

After confirmation, the menu surface becomes a reusable route-sequence slot.
Thirteen verified 384x224 capture anchors are horizontally fit to 352x224,
palette-indexed without color loss, and count/value RLE encoded. Their
compressed data is loaded through Jo Engine's cartridge-backed allocator before
track 2 begins. State changes decode into one 78,848-byte work buffer, replace
the existing VDP1 texture, and update the same 256-color CRAM bank. This avoids
additional VDP1 residency and data-track seeks during CDDA playback.

## Background and HUD

The converter reconstructs CPS2 scroll layers from captured graphics RAM,
CPS-A/CPS-B registers, tile graphics, and palettes. It removes the screen-fixed
Scroll 1 HUD from the street and boss surfaces before horizontally fitting the
remaining 512x256 reconstruction into a 469-pixel content region inside a
512x256 VDP2 bitmap. Three capture-derived 8bpp VDP1 overlays restore the
Predator status panel, the blinking Player 2 Press Start prompt, and the Over
Heat meter at fixed Saturn screen coordinates. The health and weapon interiors
are rewritten only when native state changes, so they remain fixed while VDP2
scrolls. The cold-boot probe observes Predator Warrior health reaching 101.
The isolated gun probe proves a 64-pixel weapon meter, a 40-pixel shot cost,
and one-pixel recharge every three frames. The isolated emergency attack
applies its six-unit health cost on its frame-81 completion. Those values now
drive the model.

## Display mapping

The arcade active picture is 384x224. The Saturn has no native 384-pixel
low-resolution mode, so the project force-includes a project-owned video
configuration selecting SGL's `TV_352x224` for every translation unit. All 224
scanlines are preserved. The runtime uses one full-width mapping: the converter
pre-scales VDP2 content by 352/384, VDP2 displays it at a deterministic 1:1,
and VDP1 uses the matching 0.9167 horizontal scale for actors. This avoids
losing HUD and playfield edges at the cost of 8.33% horizontal compression.
Pre-scaling replaced the earlier runtime NBG1 reduction experiment because its
SGL/emulator register path could silently fall back to a 1:1 crop.

## Sound mapping

The Saturn executable initializes SGL's native SCSP/CD audio driver. For the
current private proof, MAME renders the verified QSound Stage 1 route offline at
stereo 16-bit 44.1 kHz. The build trims save-state preroll and adds that ignored
WAV as CDDA track 2; gameplay starts it on the first encounter input. No Z80 or
QSound emulation runs on Saturn. This reference mix proves the end-to-end disc,
driver, and output route, but it contains the automated capture's mixed music
and effects.

The first event cue now uses a deterministic bus-level isolation path. A Lua
tap records the Z80 writes to QSound ports `0xd000..0xd002`; the Predator weapon
starts PCM voice 12 at source frame 2530 after the frame-2525 input. Paired idle
and weapon runs mute every other QSound voice while preserving global pan,
echo, and filter programming. Their sample-by-sample difference is one
continuous 0.902449-second stereo signal, ending before voice 12 is reused at
frame 2582. The extractor emits unnormalised signed 16-bit big-endian 44.1 kHz
PCM for SGL/SCSP, and the ISO verifier proves `/AUDIO/GUN.PCM` matches the
capture artifact byte-for-byte. Native playback is bound to action frame 5 so
the cue keeps the captured input-to-audible delay while CDDA continues.

The melee action applies the same differential method to QSound voices 13 and
14. Its source transaction consists of voice 13 starts at frames 2528 and 2531
and a voice 14 start at frame 2532. The resulting composite is 0.820590 seconds
and 144,752 bytes of stereo SCSP PCM. Native playback begins at action frame 3;
rapid attacks stop and retrigger their own previous melee channel, matching the
source voice-reuse constraint without consuming all six Jo PCM slots.

The same bus-level route now covers two Stage 1 sequence events. QSound voice
12 starts the Chrysalis entrance at source frame 5468, eight frames after the
captured boss-room entry. Its differential is 0.762857 seconds and 134,568
bytes. The defeat/Stage Clear composite preserves voice 12 at frames 14070 and
14190 plus voice 10 at frame 14126 in one 3.611587-second, 637,084-byte stream.
It starts 150 frames after the frame-13920 boss-defeat anchor and is allowed to
continue across the native Stage Clear and results boundaries. A capture-tail
window rejects MAME startup transients before selecting the event, and a
second refreshed capture must reproduce both PCM hashes before integration.

The doorway route adds two more bounded events. Voice 4 starts at source frame
5384, 44 frames after the captured dialogue anchor, and is replaced at frame
5434. A forced stop at that exact replacement boundary isolates 0.930136
seconds and 164,076 bytes without retaining the new voice-4 sample. Voice 13
then starts at frame 5438, 38 frames after the interior-transition anchor, and
stops naturally at frame 5491; its capture is 0.993515 seconds and 175,256
bytes. They reuse one SCSP channel because the source intervals are disjoint.
For save-state captures with non-repeatable startup transients, reports hash the
declared tail-selection windows and final PCM rather than irrelevant preroll.

The cold-boot route preserves the 240-frame interval between Predator Warrior
confirmation and the Round 1 card. Four paired QSound captures bind the title
lead at confirmation +231, the title tail at Round-title +36, the withdrawal
composite at barricade +95, and the breach composite at barricade +259. Their
byte-exact SCSP payloads are 113,208, 91,124, 396,708, and 298,476 bytes, and
all four reuse channel 5 because their source windows are disjoint.

Those streams define a deliberate Saturn RAM phase boundary. The enemy RLE
archive is resident before CDDA begins, but its eight 27,648-byte decode
surfaces are deferred. At barricade +259, after the withdrawal source window
has ended, the runtime closes channel 5, releases the 396,708-byte withdrawal
buffer, and allocates one contiguous 221,184-byte alien decode pool from that
free block. It decodes and copies eight VDP1 textures before the breach reveals
wave one. No disc read occurs during the transition, and the breach PCM remains
resident while combat resources come online.

The production path must repeat this method for remaining dialogue and combat
effects, keep long music on CDDA, and allocate short cues across the six bounded
Jo/SGL PCM channels.

The native channel budget is explicit rather than first-free: weapon uses
channel 0, melee channel 1, and the mutually exclusive normal/KO contact
composites share channel 2. The mutually exclusive boss entrance and
defeat/Stage Clear sequences share channel 3. The sequential doorway and
interior-transition events share channel 4. The four sequential opening events
share channel 5. A cue may retrigger only its
own channel, preventing action bursts from consuming the remaining pool.

The natural alien-contact route proves the player-damage sound independently:
each of four health losses is followed three frames later by the same QSound
voice-12 sample start. A paired mute-all/voice-12 capture isolates 0.498957
seconds (88,016 bytes) of stereo SCSP PCM as independently verified evidence.
The first three nonlethal contacts also start the same impact sample two frames
after health loss, alternating QSound voices 13 and 14. The final contact starts
a distinct KO impact on voice 14 at the same two-frame delay. Paired mute-all
captures isolate the 0.385850-second normal impact and 0.449433-second KO
impact as independently verified evidence. Two additional direct differential
captures retain impact plus voice 12 in the same QSound mix: a 0.514558-second
normal-contact composite and a 0.494671-second KO-contact composite. Starting
the selected composite on native frame 2 reproduces its internal +2/+3 timing
with one SCSP command and safely retriggers the shared contact channel.

## What is exact and what is not

Exact in the current milestone:

- CPS2 graphics-region reconstruction
- selected object pixels, scale, transparency, and palette pens
- selected background/HUD capture reconstruction
- lossless Press Start and Predator Warrior selection key states
- lossless key states for the Round 1/barricade sequence, doorway/interior
  transition, boss defeat, Stage Clear, results, intermission, and Round 2 title
- aligned multi-palette VDP1 assembly
- active CPS2 object-RAM bank and final visible boot object/priority result
- Saturn-native 352x224 initialization with one deterministic full-width fit
- isolated captured Predator walk, weapon, melee, jump, dash, emergency-attack,
  hit, and KO clips, including the hit/KO screen-space trajectory
- exact state-bound walk, attack, hit, and KO clips for one validated alien
  actor slot, with independent VDP1 slots for all eight runtime enemies
- exact Chrysalis idle and captured leap, walk, and uninterrupted 189-frame
  attack/recovery sprite timelines; native walk/attack and three-contact state
  binding plus late boss-phase working-set allocation
- first-room 5+3 crowd budget, four alien palette variants, combat lock, clear,
  and exit-state lifecycle
- isolated Predator weapon QSound voice, processed stereo waveform, source
  timing, Saturn PCM conversion, ISO payload, and native action-frame binding
- isolated two-voice Predator melee composite with three verified starts,
  capture-derived action delay, and bounded native channel retriggering
- repeated natural player-damage voice transaction, isolated waveform, and
  capture-derived hit-frame binding
- direct two-voice nonlethal and KO contact composites, including their exact
  internal source timing and bounded shared-channel selection
- isolated Chrysalis entrance and defeat/Stage Clear sequence composites,
  source-anchor timing, bounded channel-3 playback, and Round 2 `SEQ 1/1`
  plus `SEEN 1` runtime evidence
- isolated doorway and interior-transition events with exact source replacement
  and stop boundaries, bounded channel-4 playback, and Round 2 `D/T 1/1` plus
  `SEEN 1` runtime evidence

Still approximate or incomplete:

- temporal confirmation of remaining enemy archetypes, variants, and prop groups
- exact spawn coordinates/timing, attack hit windows, AI, and object priority
- remaining player transition and interaction frame sets
- complete attract-mode, menu-transition, and character-select animation
- full animation between the verified route key states
- remaining HUD states, exact scroll behavior, level triggers, combat, and AI
- remaining isolated QSound boss-action and voice cues
- exact Chrysalis attack-selection AI plus hit, KO, and palette-effect visuals
- native HUD safe-area placement and arcade-derived camera behavior for CRT
  overscan variability

## Next implementation sequence

1. Extend the captured player timeline into remaining transition and interaction clips.
2. Repeat the proven state-slot capture for the remaining enemy archetypes and
   validate attack hit windows against player-health transitions.
3. Replace prototype combat with Stage 1 scripts, collision, spawn, and camera
   data.
4. Add bounded CD-to-cartridge prefetch and VDP1 cache scheduling.
5. Replace the CDDA reference mix with isolated music/SFX assets and verify the
   complete level on real Saturn hardware.

## Hardware boundary

The executable is linked for the Saturn SH-2 and uses SGL/Jo Engine hardware
paths for CD files, controller port 1, VDP1 sprites, VDP2 background, and CRAM.
Startup checks address `0x24ffffff` for the physical 32 Mbit cartridge signature;
without it, the build reports `4MB RAM CART REQUIRED` and does not enter the
runtime. Jo Engine registers the cartridge's first 2 MiB DRAM bank itself; the
port also registers the second bank at `0x22600000` so the native allocator can
use the complete 4 MiB cartridge without reducing sprite or PCM fidelity. The
disc is an ISO9660 Mode 1 image with Sega Saturn IP boot data and
NTSC `TV_352x224` initialization. Emulator configuration is not part of the
executable.

`build/hardware_release_manifest.txt` fingerprints the cue and ISO that must be
kept together. These structural checks establish a hardware-oriented image, but
only the cold-boot and soak route in `HARDWARE_TEST.md` can close the physical
hardware gate.

Additional frames should live on disc and in the 4 MB cartridge. Only the
current and predicted cels should occupy VDP1 VRAM. AI upscaling is a separate
offline enhanced-edition asset path; it should not be mixed into the exact
arcade baseline until the native reconstruction is validated.
