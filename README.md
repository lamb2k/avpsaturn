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
- verifies 233 additional 60-frame route samples and 26 hashed visual anchors
  from the cold Press Start screen through the definitive Round 2 title boundary
- boots into lossless capture-derived Press Start and Predator Warrior select
  surfaces; Start and B traverse those native states before Round 1 begins
- copies thirteen cartridge-preloaded, capture-derived route states into the
  shared VDP2 bitmap from the Round 1 title through the Round 2 title
- preserves original sprite scale and exact 15-color CPS2 subpalettes
- captures isolated Predator walk, weapon, melee, jump, dash, emergency-attack,
  hit, and KO timelines from verified CPS2 state, reduces the eight clips to
  103 exact poses, and animates them through three aligned VDP1 palette layers
- validates one native CPS2 alien actor slot through exact 39-frame walk,
  120-frame attack, 36-frame hit, and 140-frame KO timelines; 42 deduplicated
  288x192 poses are bound to the corresponding Saturn-native actor states
- validates an unfrozen natural-contact replay: the tracked alien strikes at
  attack offsets 48 and 119 and approaches at 111/38 CPS2 pixels per frame
- separates the arcade HUD from the scrolling CPS2 street, keeps it fixed in
  VDP1, and drives health and Over Heat interiors from native Saturn state
- validates 101 observed Predator Warrior health units, eight-unit tracked
  alien damage, and a 64-unit weapon meter with a 40-unit shot cost and
  one-unit recharge every three frames; the 81-frame emergency attack costs
  six health units at completion
- runs a capture-derived first-room lifecycle with five opening enemies, three
  reinforcements, a locked combat boundary, clear hold, and exit transition
- transitions into a reconstructed industrial boss room and animates Chrysalis
  from an exact idle plus captured 44-frame leap, 106-frame walk, and complete
  189-frame attack/recovery clips; a natural three-health hit adds its exact
  40-frame reaction, while a deterministic lethal replay adds the complete
  428-frame launch, tumble, and grounded KO trajectory; 29 deduplicated
  288x192 poses stream through one VDP1 slot
- identifies the two boss-room Stalkers at `FF A240` and `FF A300`, preserves
  their distinct CPS2 palette-17 artwork, and binds a 57-frame walk, 17-frame
  attack, two-frame visible impact onset, and 157-frame KO interval to native
  Stalker states; 37 poses compress to a 64,118-byte indexed archive
- gives all eight bounded enemy actors independent 288x192 VDP1 cel slots with
  four exact CPS2 alien palettes, so unlike actions cannot overwrite each other
- retains a palette-preserving 352x224 offline reference surface containing the
  complete horizontally fitted CPS2 object/priority result
- boots in the Saturn's native 352x224 mode with the 4 MB expansion cartridge
- builds a mixed-mode disc with the verified Stage 1 QSound route rendered as
  native Saturn CD audio track 2
- runs a small native lane-combat model; enemies wait for the first input

The normal release now begins at the capture-derived Press Start screen, waits
for Saturn Start, shows the default Predator Warrior character-select capture,
and waits for B before entering Round 1. These frontend surfaces preserve their
source pixels and palettes but are still flattened key states rather than the
complete arcade attract/menu animation. Thirteen later route states use the
same lossless horizontal fit and the shared VDP2 bitmap. Their compressed
sources are loaded before CDDA starts, so state changes do not seek away from
the audio track. The title and character-select source blocks are retired in
sequence to load the Stalker and Chrysalis action archives without expanding
the cold-boot working set. The converter retains the 384x224 object/priority oracle
offline. The proven alien walk/attack/hit/KO clips are state-bound. Chrysalis
walk and attack are bound to native states. The attack now uses its captured
189-frame preparation/contact/recovery schedule and source contact offsets
21/55/97 with 10/10/16 health damage. A normal melee strike captured at source
frame 13491 drives the boss's exact 40-frame nonlethal hit reaction instead of
falling back to idle art. Boss-room adds now render their captured purple
Stalker species rather than the street-alien substitute and use their observed
17-frame attack plus 12-health contact. The Stalker nonlethal-hit
timeline remains represented by the exact visible KO onset until a natural
nonlethal capture is obtained. A separate lethal frame-13491 replay drives
Chrysalis through the exact 428-frame source interval 13492-13919, including
its capture-derived screen trajectory and grounded corpse. Exact AI/spawn timing for every
archetype, remaining boss action/voice sounds, and every intermediate Stage 1
action remain incomplete.

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

The committed `data/stage1_route.json` is the copyright-safe route-evidence
ledger. It records ordered milestones, capture hashes, runtime phases, and the
automated continues that must not be mistaken for authored timing. Run
`tools/generate_stage1_route.py --verify-captures` to check every private local
anchor plus the complete active-object-bank sample series. The generated C
header is ignored and consumed by the native build.

Jo Engine is pinned to commit `556d081146211b6a1cfa6591d70f9487d406758b`.

## Run

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_emulator.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

`run.ps1` launches Yaba Sanshiro with a 32 Mbit DRAM cartridge, the Saturn 4 MB
RAM expansion. Controls follow the CPS2 panel order: D-pad to move, A for the
weapon, B for melee attack, and C to jump. Hold left or right and press C to
dash. Press A+B together for the health-draining emergency attack.
X toggles the diagnostic HUD.

Those are Saturn pad buttons, not keyboard keys. `run.ps1` sets the disc and
cartridge but deliberately does not rewrite the emulator's input configuration,
so the keyboard layout is whatever Yaba Sanshiro has stored. Note that the
Saturn face buttons are **not** bound to the A, B, and C keys; the literal `A`
key is D-pad left. The mapping recorded in
`%APPDATA%\YabaSanshiro\yabause.ini` on this machine is:

| Saturn input | Key | Saturn input | Key |
| --- | --- | --- | --- |
| Up / Down | `W` / `S` | A, weapon | `G` |
| Left / Right | `A` / `D` | B, melee and character confirm | `H` |
| Start | `Enter` | C, jump | `J` |
| L / R triggers | `5` / `6` | X / Y / Z | `T` / `Y` / `U` |

So the cold-boot route is `Enter` at Press Start, then `H` to confirm Predator
Warrior. If the game appears frozen at Press Start or character select, it is
waiting for one of those two inputs rather than failing. Verify the current
bindings by reading the `Input\Port\1\Id\1\Controller\2\Key\N` entries in that
ini; they are Qt key codes in the order up, right, down, left, R, L, Start, A,
B, C, X, Y, Z. The launcher no longer disables emulator audio.
It disables Yaba Sanshiro's persistent config autostart and supplies this
checkout's AvP disc exactly once with `-a/-i`. For Yaba only, it writes a
temporary cue with absolute track paths because Yaba 1.20.37 can resolve a
relative `FILE` entry against stale process state; the portable hardware cue
beside the ISO remains unchanged.

## Real hardware

Real Sega Saturn hardware is the acceptance target. Build the normal release
profile with `build.ps1 -Clean -Release`; diagnostic `-VisualTest`,
`-EncounterTest`, and `-BossHitTest` images are not release candidates. The console needs an
authorized homebrew boot path plus compatible 4 MB DRAM support. See
[docs/HARDWARE_TEST.md](docs/HARDWARE_TEST.md) for the exact cold-boot,
controller, video, encounter, and soak-test route. Physical-hardware validation
is still pending.

The runtime registers both 2 MB expansion-DRAM banks, using the full 4 MB
cartridge capacity rather than sacrificing captured animation or event audio.

## Verified status

Verified on August 17, 2026:

- official MAME reports the local `avspu` set as good
- the Python CPS2 graphics reconstruction matches MAME's 16 MiB `:gfx` region
- 54 captured commands decode from the verified active CPS2 object-RAM bank
- 361 four-frame-spaced captures retain the recorded active object bank; an
  independent two-bank render check confirms bank 2 at frames 2880 and 4200
- eight isolated cold-boot captures, including idle, walk, and the natural
  damage route, verify their required common pre-input object-RAM and palette state;
  the damage route is additionally screenshot-identical to idle through frame
  2608. Walk, weapon, melee, jump, dash, emergency attack, hit, and KO use exact
  48-, 23-, 22-, 42-, 24-, 81-, 25-, and 96-frame source clips
- the eight clips reduce to 103 shared poses; 309 palette-layer payloads compress
  from 5,695,488 decoded bytes to one 417,488-byte indexed cartridge archive
  and stream through three reusable VDP1 texture slots
- the independently visible right-side blue alien is tracked across frames
  4164-4200 and its ten authentic poses run through one replaceable VDP1 slot
- an exhaustive frame-local grouping manifest separates verified actors,
  ground-shadow sprites, and props from edge fragments awaiting temporal proof
- exact layered cels retain original scale and CPS2 palette pens
- the native model passes 12,000 deterministic frames, including the idle boot
  gate and the complete 5+3 opening-room lifecycle
- the isolated HUD probe proves a maximum observed player-health value of 101;
  the natural alien probe proves eight native damage units per contact
- the isolated gun probe drops the 64-pixel weapon meter from 64 to 24 and then
  restores one pixel every three frames; the native model uses the same values
- the complete private capture contains 233 ordered active-bank samples from
  frame 4260 through 18180; 26 hashed visual anchors prove Press Start,
  Predator Warrior selection, the Round 1 title, street, doorway dialogue,
  industrial transition, Chrysalis plus recurring Stalker waves, boss defeat,
  results, intermission, and the Round 2 boundary
- a controller-only route test reaches the Round 2 boundary without changing actor
  health, positions, encounter state, or timers outside normal player input
- the encounter diagnostic visibly reaches five active enemies, eight street
  KOs, room clear, the Chrysalis room with two recurring Stalker waves, boss
  defeat, Stage Clear, results, intermission, and Round 2 in Yaba Sanshiro
- a focused `-BossHitTest` image repeatedly renders the 40-frame natural
  Chrysalis hit state, including supplemental pose 20, and the full encounter
  diagnostic subsequently reaches Round 2 with the same split archive loaded
- a focused `-BossKoTest` image renders the capture-derived 428-frame
  Chrysalis launch/tumble/corpse sequence; the complete encounter diagnostic
  then renders the same KO and reaches Round 2 without an allocation, RLE,
  index, palette, or VDP1 failure
- the 5,900-byte hit and 43,232-byte KO supplements share one aligned
  pre-CDDA allocation inside the retired character-select block; this avoids
  Jo Engine's unsplit-free-block trap and keeps both CD-load destinations
  four-byte aligned
- the same diagnostic visibly traverses the capture-derived character-select,
  results, and Round 2 surfaces from the preloaded route cache
- the native audio module links successfully and the mixed-mode cue exposes a
  168.015-second stereo 16-bit 44.1 kHz Stage 1 QSound reference as CD track 2
- the final visible object/priority result fits a single 78,848-byte 352x224
  VDP1 8bpp display surface with 76 visible colors; the ignored converter
  output also retains the 86,016-byte 384x224 source oracle
- the release SH-2 build, link, ISO, and cue generation complete successfully
- the eight-clip visual diagnostic boots from one indexed player archive and
  visibly cycles exact walking, all five controlled actions, and the automatic
  hit and KO clips through the three-layer VDP1 working set; captured per-frame offsets
  preserve the KO launch, fall, ground bounce, and respawn trajectory
- Yaba Sanshiro boots in 352x224 with the 4 MB cartridge, shows both horizontal
  source edges and all 224 source lines with no framebuffer black bars, and
  displays the asset working set over the reconstructed Stage 1 background;
  the fixed HUD, blinking Player 2 prompt, and live meters render above it
- the first event-level sound is isolated from QSound voice 12 by paired idle
  and weapon captures: a 0.902449-second, 44.1 kHz stereo cue is stored as
  signed 16-bit big-endian SCSP PCM and starts five action frames after A
- the same bus-level method isolates the three-start, two-voice melee
  composite as a 0.820590-second stereo cue and starts it three action frames
  after B; rapid attacks retrigger its own PCM channel instead of leaking slots
- the encounter diagnostic reaches the eight-enemy clear with both weapon and
  melee `SEEN 1` latches set, proving both cues entered SCSP playback channels
  while the full animation working set remained allocated
- all four natural player-health losses repeat the same QSound voice-12 start
  three frames later; paired mute-all/voice-12 captures isolate the resulting
  0.498957-second damage component as independent source evidence
- paired mute-all captures isolate a 0.385850-second common nonlethal contact
  impact and a distinct 0.449433-second final-KO impact
- direct two-voice captures produce 0.514558-second normal and 0.494671-second
  KO contact composites; each preserves impact at +2 and the vocal at +3 in
  one stream on fixed PCM channel 2
- the expanded encounter diagnostic reaches Round 2 with weapon, melee, and
  contact `SEEN 1` latches on fixed PCM channels 0 through 2; its one normal
  and one forced KO proof recover into `KO 8/8`, `ACTIVE 0`, and `LVL 1`
- deterministic boss-room captures isolate the Chrysalis entrance cue as
  0.762857 seconds of stereo SCSP PCM and the three-start defeat/Stage Clear
  sequence as 3.611587 seconds; native playback uses shared channel 3 at the
  measured +8 and +150 frame offsets
- the refreshed emulator route reaches Round 2 with `PCM SEQ 1/1` and
  `SEEN 1`, proving both sequence starts entered SCSP playback without losing
  the prior weapon, melee, or contact-channel latches
- paired doorway captures isolate a 0.930136-second voice-4 event at +44 and a
  0.993515-second voice-13 interior-transition event at +38; both reuse fixed
  PCM channel 4 because their verified source intervals do not overlap
- the combined emulator route reaches Round 2 with `PCM D/T 1/1`,
  `PCM SEQ 1/1`, and both `SEEN 1` latches while the earlier contact and
  weapon proofs remain intact
- the cold-boot route now holds the source-exact 240 frames after character
  confirmation and plays four capture-exact Round 1, withdrawal, and breach
  composites on channel 5; their verified payloads total 899,516 bytes
- the barricade boundary releases the completed 396,708-byte withdrawal PCM
  and reuses it for one contiguous 221,184-byte eight-alien decode pool, so the
  first wave becomes resident without a CD read or reduced animation set
- the refreshed emulator controller route crosses that RAM overlay and reaches
  the Round 2 card without an asset failure

Next proof gate: verify the full-width mapping, complete KO, and CD audio on
physical Saturn, then extend the proven QSound isolation to remaining combat effects while
replacing the approximate route gaps with the remaining captured
rooms, actors, and actions.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/TEST_PLAN.md](docs/TEST_PLAN.md).
