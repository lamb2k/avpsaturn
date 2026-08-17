# Capability test plan

## Gate A: reproducible source decode

- Official MAME reports the local `avspu` set as good.
- The reconstructed 16 MiB graphics region matches MAME's `:gfx` bytes.
- The deterministic Stage 1 capture produces the expected state files.
- No ROM, decoded asset, capture, or disc image is tracked by Git.

Status: passed on August 16, 2026.

## Gate B: native Saturn build and boot

- Strict host gameplay tests pass for at least 10,000 deterministic frames.
- Release SH-2 compilation, link, ISO, and cue construction succeed.
- The image boots with a 4 MB cartridge and no asset failure.
- VDP1 transparency and aligned palette layers render correctly over VDP2.
- The boot composition remains stable until the first player input.

Status: passed in Yaba Sanshiro 2 v1.20.37 on August 16, 2026. The 12,000-frame
test and clean release build passed, and visual inspection confirmed the exact
working-set pixels at original scale over the reconstructed background/HUD.

## Gate C: frame-exact presentation reconstruction

- Group all visible CPS2 object commands into actors and props.
- Match the MAME reference enemy variants, palettes, positions, pivots, and
  priority at the Saturn's chosen crop.
- Preserve the active object-RAM bank and reproduce tilemap priority when the
  flattened boot oracle is replaced by independently animated actors.
- Remove static HUD values from the background and drive them natively.
- Produce an automated image-difference report with separately stated crop and
  color-quantization tolerances.

Status: in progress. The boot reference mode now draws the final visible CPS2
object/priority result from one lossless 8bpp VDP1 surface with 76 visible
colors. Active-bank selection is guarded by a 54-command capture signature, and
an exhaustive frame-local grouping manifest identifies actors, shadow sprites,
and props while marking three edge fragments as candidates. Temporal grouping,
actor-level priority, crop policy, dynamic HUD state, and image-difference
acceptance remain open. The post-input gameplay scene still reuses two blue
alien cels and must not be described as frame-exact.

## Gate D: first playable Stage 1 encounter

- Extract and schedule authentic idle, walk, attack, hit, and KO frames.
- Reproduce camera bounds, lanes, collisions, encounter triggers, and enemy
  behavior for the first combat room.
- Support player movement and attacks without partial cels or palette damage.
- Reach the room completion transition deterministically.
- Add a comparison capture against the equivalent MAME route.

Status: open. The current combat logic is a native placeholder used only to
exercise movement, overlap, damage, and ordering.

## Gate E: performance and hardware

Run a fixed ten-minute route in emulator and on a real Saturn. Capture frame
time, missed frames, maximum VDP1 command/texture use, transfer bytes per
second, room load time, and overlap corruption. The pass target is sustained
60 Hz with no partial cels, palette corruption, or post-load gameplay stall
longer than one frame.

Status: open.

## Gate F: full-port candidate and rights review

After the first level is complete, expand the same architecture into a full
port candidate suitable for an internal development-team evaluation. Before
the build or its footage is distributed, demonstrated publicly, promoted, or
released, complete an explicit licensing and rights-holder authorization
review.

Status: future gate; no public distribution is authorized by this repository.
