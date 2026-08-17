# Capability test plan

## Gate A: reproducible source decode

- Official MAME reports the local `avspu` set as good.
- The reconstructed 16 MiB graphics region matches MAME's `:gfx` bytes.
- The deterministic Stage 1 capture produces the expected state files.
- No ROM, decoded asset, capture, or disc image is tracked by Git.

Status: passed on August 16, 2026.

## Gate B: native Saturn build and boot

- Strict host gameplay tests pass for at least 10,000 deterministic frames.
- Release SH-2 compilation, link, ISO, mixed-mode cue, and CDDA construction succeed.
- The image boots with a 4 MB cartridge and no asset failure.
- VDP1 transparency and aligned palette layers render correctly over VDP2.
- The Press Start composition remains stable until Start, then character select
  remains stable until the confirming B input.

Status: passed in Yaba Sanshiro 2 v1.20.37 on August 16, 2026. The 12,000-frame
test and clean release build passed, and visual inspection confirmed the exact
working-set pixels at original scale over the reconstructed background/HUD in
the Saturn's native 352x224 mode.

## Gate C: frame-exact presentation reconstruction

- Group all visible CPS2 object commands into actors and props.
- Match the MAME reference enemy variants, palettes, positions, pivots, and
  priority in the Saturn 352x224 full-width mapping.
- Preserve the active object-RAM bank and reproduce tilemap priority when the
  flattened boot oracle is replaced by independently animated actors.
- Remove static HUD values from the background and drive them natively.
- Produce an automated image-difference report with separately stated crop and
  color-quantization tolerances.

Status: in progress. The converter retains the final visible CPS2
object/priority result as a lossless offline 8bpp oracle with 76 visible colors.
The release boot instead traverses lossless Press Start and character-select
key states. Active-bank selection is guarded by a 54-command capture signature, and
an exhaustive frame-local grouping manifest identifies actors, shadow sprites,
and props while marking three edge fragments as candidates. The display now
uses native 352x224 with a deterministic pre-scaled VDP2 full-width fit and a
  matching VDP1 actor transform. The captured HUD is now split into fixed VDP1
  overlays with live native health and weapon interiors; it no longer scrolls
  with the VDP2 street. Remaining HUD states, enemy archetypes, actor-level
  priority, and image-difference acceptance remain open.
The post-input gameplay scene now binds the validated alien actor's exact
39-frame walk, 120-frame attack, 36-frame hit, and 140-frame KO schedules to
independent Saturn actor slots.
An unfrozen natural-contact replay additionally validates contact offsets 48
and 119, maximum observed X reach of 68 source pixels, and 111 pixels of
approach displacement over 38 frame intervals.
The HUD probe additionally verifies a maximum observed Predator Warrior health
value of 101, a 64-pixel weapon meter, a 40-pixel isolated-shot cost, and
one-pixel recharge every three frames. Its emergency-attack route also records
a six-unit health cost at the frame-81 action boundary. The latest Yaba diagnostic showed the
fixed HUD, full-width street, actors, and blinking Player 2 prompt together.

The automated encounter build also traversed the cartridge-preloaded route
cache and visibly reached the capture-derived character-select, results, and
Round 2 title surfaces. No data-track reads occur after Stage 1 CDDA begins.

## Gate D: first playable Stage 1 encounter

- Repeat the proven walk/attack/hit/KO extraction for remaining enemy archetypes.
- Reproduce camera bounds, lanes, collisions, encounter triggers, and enemy
  behavior for the first combat room.
- Support player movement and attacks without partial cels or palette damage.
- Reach the Chrysalis boss room, Stage Clear, results, intermission, and the
  Round 2 boundary deterministically.
- Validate the Chrysalis actor at `FF A3C0`, preserve its exact frame-12660 idle,
  and extract the 44-frame leap, 106-frame walk, and uninterrupted 189-frame
  attack/recovery clips into an indexed archive. Require contacts at offsets
  21/55/97 for 10/10/16 health. Also require the natural frame-13491 melee
  impact to reduce boss health from 38 to 35 and drive the exact 40-frame hit
  clip from frames 13492-13531. Verify the original `/SPR4/BACT.RLE` remains
  119,868 bytes with SHA-256
  `a7efabb6894204475a6aacde4945c6cc4751b150d7d9007349566c86b78220f8`
  and `/SPR4/BHIT.RLE` is 5,900 bytes with SHA-256
  `c4f6db6ce3ec9d3505a543bc8340b9bee949bde297c53dc2f386a10ffe501ebb`.
  Require a deterministic lethal frame-13491 impact followed by all 428 KO
  frames from 13492-13919, including exact per-frame X/Y trajectory and the
  grounded corpse. Verify `/SPR4/BKO.RLE` is 43,232 bytes with SHA-256
  `9ad615f5e61615142d5be3b91a10fd16e9519ff304d204da704f9fe6e609f78a`.
  Require changing walk/attack/hit/KO poses in Yaba Sanshiro with no `BOSS
  SUPPLEMENT BUFFER`, `BKO.RLE`, `BOSS ACTION` RLE/index, or VDP1 failure
  before Round 2.
- Validate the native Stalker slots at `FF A240` and `FF A300` as actor ID 0,
  palette 17, and 24 source health. Require the 57-frame walk, 17-frame attack,
  12-health natural contact evidence, and 157-frame KO interval to build into
  `/SPR4/SACT.RLE` at exactly 64,118 bytes. Start must release the obsolete
  78,848-byte title surface and load that archive before character confirmation
  starts CDDA. In Yaba Sanshiro, require distinct purple Stalkers beside
  Chrysalis and successful arrival at Round 2 with no archive, RLE, index,
  palette, VDP1, or late-KO failure.
- Start the Stage 1 CD audio track without disabling SCSP output.
- Play the capture-exact Predator weapon PCM on action frame 5 while CDDA
  remains active; verify the ISO copy is 159,192 bytes with SHA-256
  `777c55dd2c1087a6db728ca0f9a22f82516b573815d2d8899092eaf98b225d4e`.
- In the encounter diagnostic, require `SHOT 1`, `PLAYED 1`, and latched
  `SEEN 1`; this proves the Jo/SGL PCM channel entered its playing state. The
  physical-console listening test remains the final waveform/output gate.
- Play the capture-exact melee composite on action frame 3 and verify
  `/AUDIO/MELEE.PCM` is 144,752 bytes with SHA-256
  `e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125`.
  Repeated B presses must retrigger without exhausting the six PCM slots.
  The emulator encounter diagnostic currently reaches `KO 8/8` with both
  weapon and melee `SEEN 1`; physical listening remains pending.
- Require all four natural player-health events to repeat QSound sample
  `8016:e690` on voice 12 three frames later. Verify `/AUDIO/HIT.PCM` is
  88,016 bytes with SHA-256
  `85ac8562bf83b87e1ffd858f5775271d4e4165105074e01fe008e34cae059ba6`,
  as independent evidence for the shared vocal component.
- Require the three nonlethal contacts to use the common two-frame impact and
  the final contact to use its distinct two-frame KO impact. Verify
  `/AUDIO/IMPACT.PCM` is 68,064 bytes with SHA-256
  `c1c576c3cd7ad260f1255b167f6fbb69ca31badb6cad8bc52ea0e4bd4b00bb88`
  and `/AUDIO/KOIMP.PCM` is 79,280 bytes with SHA-256
  `421e344948349beb64e3a86fa9bd9ed1677c74320959cb7e64935b2a962b2560`.
  Treat these as component evidence, not separate runtime starts.
- Verify the direct normal-contact composite `/AUDIO/CONTACT.PCM` is 90,768
  bytes with SHA-256
  `fe554dad2073d662f6f45fb85a081bccff00874dbb04ad32cdc66fba8e24b9e2`
  and the KO composite `/AUDIO/KOCONT.PCM` is 87,260 bytes with SHA-256
  `d06eca83fc1bfea94671cfc4ec18f66de2358d26edf54e7478cf544261cbec60`.
  Require nonzero normal/KO counts and contact `SEEN 1` in the encounter
  diagnostic. After those latches are proven, the diagnostic suppresses later
  enemy windups so its forced KO cannot hit-lock the automated completion
  route; production gameplay retains normal enemy attacks. The verified Yaba
  Sanshiro run reaches Round 2 with `CONTACT 10/1 SEEN 1`, `KO 8/8`,
  `ACTIVE 0`, and `LVL 1`.
- Verify `/AUDIO/BOSSIN.PCM` is 134,568 bytes with SHA-256
  `7b804d77853d06a02454c4776c81b705e126a953862535d35585828620bf2b40`
  and starts on boss-intro timer 8. Verify `/AUDIO/BOSSCLR.PCM` is 637,084
  bytes with SHA-256
  `2b8e5ac3619d40b4760b28f1f0828a911f729d550607c333a27d614a47a485b8`
  and starts on boss-defeat timer 150. Require `PCM SEQ 1/1` and latched
  `SEEN 1` after the Round 2 boundary. The refreshed Yaba Sanshiro encounter
  route now satisfies this diagnostic gate; physical listening remains pending.
- Require the fixed SCSP budget to keep weapon, melee, contact, and the
  mutually exclusive boss sequences on channels 0, 1, 2, and 3 respectively.
- Verify `/AUDIO/DOOR.PCM` is 164,076 bytes with SHA-256
  `3e745afcc9054e3d24948f6841b9a7d397a16506228fadfecb53e28629baaee7`
  and starts on doorway timer 44. Verify `/AUDIO/TRANS.PCM` is 175,256 bytes
  with SHA-256
  `b6de8fd84e682bc55d7255521d542d191bfa44390ce26cefc2ee467c917c21af`
  and starts on interior-transition timer 38. Require `PCM D/T 1/1` and
  latched `SEEN 1` after Round 2. The refreshed Yaba Sanshiro route satisfies
  this gate while retaining the boss-sequence and earlier audio latches. Both
  events share channel 4. Physical listening remains
  pending.
- Verify the cold-boot opening payloads and their channel-5 bindings:
  `/AUDIO/RND1A.PCM` is 113,208 bytes with SHA-256
  `5ae8de3a3a2c77c0764c2189b812b9cf49f8cbae9da32794303ba938096faf79`;
  `/AUDIO/RND1B.PCM` is 91,124 bytes with SHA-256
  `b9f0a3d96bd5610f00590a3c0ad1e03a6dcca30f7c2e77fce3a38f1511c80b99`;
  `/AUDIO/WITHDRW.PCM` is 396,708 bytes with SHA-256
  `f76bb4b4a9e6e3c404bb639c81dfb66dca174497267b0e24bcfd3e74761c58b1`;
  and `/AUDIO/BREACH.PCM` is 298,476 bytes with SHA-256
  `c2957aaa6e458d38fd336ef856f0eba78e1014c9ba070eb51830cb78b4570b64`.
  Require the 240-frame post-confirmation interval, all four starts, no asset
  failure at the barricade-to-wave boundary, and successful arrival at Round
  2. The refreshed Yaba Sanshiro route satisfies the state, allocation, and
  completion gates; physical listening remains pending.
- Add a comparison capture against the equivalent MAME route.

Status: in progress. A dense 361-sample capture validates the active CPS2 object
bank and identifies 87 unique player assemblies. Eight isolated cold-boot
captures include idle, six injected player inputs, and a natural enemy-damage
route. Walk uses a capture-verified 48-frame loop; the five controlled actions
use exact 23-, 22-, 42-, 24-, and 81-frame clips; automatic hit and KO use exact
25- and 96-frame clips. Together they reduce to 103 shared poses and 309
replaceable VDP1 palette-layer payloads. A Yaba Sanshiro visual diagnostic has
rendered the advancing walk loop and cycled all eight clips from one indexed
archive without partial cels or palette-layer loss, including the captured KO
launch, fall, bounce, and respawn offsets. A separately tracked blue alien
now advances through ten authentic single-layer poses from frames 4164-4200. A
capture-derived native route starts at Press Start and character select,
displays five initial enemies, adds three reinforcements after three defeats,
clears after eight defeats, unlocks the camera boundary, plays the door and
interior states, enters the industrial room, spawns captured Chrysalis plus
five Stalkers across the observed recurring waves, and reaches the Round 2
boundary through Stage Clear, results exit, and intermission. Thirteen route
states now use lossless capture-derived key surfaces instead of Jo-font
stand-ins. The mixed-mode image adds a 168.015-second QSound
route reference as native CD audio track 2. The 12,000-frame host test and the
automated Yaba Sanshiro diagnostic complete this lifecycle. A separate dense
900-frame boss capture plus a deterministic lethal replay reduce exact
idle/leap/walk/attack/hit/KO visuals to 29 archive poses. The natural melee
event proves a three-health impact followed by the 40-frame hit reaction; the
lethal replay proves the 428-frame KO and screen trajectory. Focused Yaba
Sanshiro images visibly render `/SPR4/BHIT.RLE` and `/SPR4/BKO.RLE`; the
complete encounter diagnostic then renders the KO and reaches Round 2 with all
audio latches retained. The emulator route renders
changing Chrysalis attack poses after deferring the decoded boss buffer to its
gameplay phase. The same
route now renders the distinct purple Stalker archive beside Chrysalis and
completes through Round 2 after loading it from the retired title-screen RAM
block before CDDA starts. Remaining player transitions, other enemy
archetypes, Chrysalis palette/explosion/victory detail and exact AI timing, a
natural nonlethal Stalker-hit clip, intermediate route detail,
combat SCSP cues, and comparison capture
remain open.

## Gate E: performance and hardware

Run the route in `docs/HARDWARE_TEST.md` on a real NTSC Saturn with a digital
controller and detected 32 Mbit DRAM cartridge. Record console/region, boot
device, cartridge, display path, cold-boot result, controls, encounter result,
and a fixed ten-minute soak. Capture frame time, missed frames, maximum VDP1
command/texture use, transfer bytes per second, room load time, and overlap
corruption. The pass target is sustained 60 Hz with no partial cels, palette
corruption, controller loss, video-sync loss, or post-load gameplay stall
longer than one frame.

Status: emulator precursor passed; physical-Saturn validation is open.

## Gate F: full-port candidate and rights review

After the first level is complete, expand the same architecture into a full
port candidate suitable for an internal development-team evaluation. Before
the build or its footage is distributed, demonstrated publicly, promoted, or
released, complete an explicit licensing and rights-holder authorization
review.

Status: future gate; no public distribution is authorized by this repository.
