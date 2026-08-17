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
  remains stable until the confirming A input.

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
matching VDP1 actor transform. Native HUD replacement, enemy temporal
grouping, actor-level priority, and image-difference acceptance remain open.
The post-input gameplay scene now uses a tracked ten-pose blue-alien sequence,
but its poses are not yet bound to arcade enemy states and it must not be
described as frame-exact.

The automated encounter build also traversed the cartridge-preloaded route
cache and visibly reached the capture-derived character-select, results, and
Round 2 title surfaces. No data-track reads occur after Stage 1 CDDA begins.

## Gate D: first playable Stage 1 encounter

- Extract and schedule authentic idle, walk, attack, hit, and KO frames.
- Reproduce camera bounds, lanes, collisions, encounter triggers, and enemy
  behavior for the first combat room.
- Support player movement and attacks without partial cels or palette damage.
- Reach the Chrysalis boss room, Stage Clear, results, intermission, and the
  Round 2 boundary deterministically.
- Start the Stage 1 CD audio track without disabling SCSP output.
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
automated Yaba Sanshiro diagnostic complete this lifecycle. Remaining player
transitions, enemy actions, intermediate route detail, exact arcade AI/spawn timing,
isolated SCSP event cues, and comparison capture remain open.

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
