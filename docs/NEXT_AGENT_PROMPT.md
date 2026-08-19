# Next agent prompt: real ROM-derived frontend

## Scope lock

Implement the real title and character-select path from original AvP ROM data.
Do not begin S5 enemy AI, stage traversal, remaining-cast conversion, attract
mode, or physical-hardware claims in this checkpoint.

Read `AGENTS.md`, this handoff's newest section, `docs/PARITY_PLAN.md`,
`docs/TEST_PLAN.md`, and `docs/HARDWARE_TEST.md` in that order. Verify branch,
HEAD and worktree before relying on the handoff.

## Baseline already proven — do not re-derive

- The bounded S4 body is complete: canonical actor fields and generated class
  lookup are live, collision and rendering share one record, and HIT/KO remain
  counted GAP because host replay proved external state writers are required.
- `data/frontend_rom_composition.json` is the structural source of truth. It
  was generated from CPS layer/object/palette state, not screenshots.
- Measured live palette demand:
  - title frame 1620: 19 total banks;
  - select frames 1760/1790: 17 total banks;
  - Round 1 title frame 2100: 32 total banks.
- Character select is primarily three CPS tilemap layers. Its only settled
  sprite objects are the two-object 1P marker. The 1700 plate slide and 1900
  confirm are 360-object transient bursts; do not bake them into a background.
- Saturn output is 352x224. Preserve the established 384-to-352 full-width
  mapping with all 224 lines; do not crop, stretch vertically, or add black
  bars.
- Existing `MENUFIT.BIN`, `CHARFIT.BIN` and capture-derived sequence surfaces
  are regression oracles only. New runtime frontend content must come from ROM
  tables/assets.

## Required implementation

### 1. CRAM feasibility check first

- Inventory the current VDP2/VDP1 CRAM mode and all banks reserved by Jo Engine,
  fonts, frontend layers, cursor and combat.
- Model a frontend-only window of 32 16-colour banks / 512 colours.
- For each screen boundary, densely remap the CPS banks actually live on that
  screen into the frontend window. Emit a deterministic source-bank to Saturn-
  bank manifest.
- Rewrite converted VDP2 pattern-name palette indices and VDP1 cursor palette
  indices through the same mapping.
- Reload the mapping only at screen boundaries. Release or reassign it before
  combat. Perform every required disc read before CDDA playback begins.
- Add a host check that fails on overflow, an unmapped live bank, bank aliasing,
  or a pattern/object referring to a bank outside its screen mapping.
- If the active Saturn CRAM mode cannot expose 32 simultaneous 16-colour banks,
  implement the affected layer as 8bpp VDP2. Do not merge colours, discard a
  bank, or lower fidelity silently.

### 2. ROM tilemap conversion

- Reuse the existing CPS graphics/tilemap decoders and the exact bases/registers
  recorded in `data/frontend_rom_composition.json`.
- Convert title and character-select tilemaps into native VDP2 assets while
  retaining layer order, transparency, scroll offsets, palette references and
  352x224 geometry.
- Keep generated tile/palette bytes ignored. Track only code, deterministic
  manifests, hashes, dimensions, source addresses and counts.
- Render the title and settled select compositions without using captured
  `MENUFIT.BIN`/`CHARFIT.BIN` pixels. Keep the old surfaces available only to an
  offline pixel comparison.

### 3. Live selection objects and state

- Decode and render the 1P marker as live VDP1 objects from ROM-derived object
  data. It must move; no cursor pixels may be baked into a VDP2 layer.
- Implement controller movement over the actual supported character choices,
  including boundary/wrap behavior measured from the source route.
- Maintain explicit selected-character state. Implement confirm and cancel,
  and pass the selection into the gameplay initializer rather than always
  choosing the current predetermined character.
- Preserve the measured confirm shutter timing/geometry. The shutter may keep
  its current native implementation if its output still matches the oracle.
- Do not implement attract mode in this body.

### 4. Required validation

Run in order:

1. Palette-map, tilemap-conversion, cursor-state and selection-state host tests.
2. Deterministic regeneration twice; require byte-identical manifests/hashes.
3. Full `test.ps1`.
4. Focused Saturn frontend build and ISO-member hash verification.
5. Live normal-release boot: title waits indefinitely, Start reaches select,
   D-pad visibly changes the live cursor/selection, cancel returns correctly,
   confirm preserves the shutter and propagates the chosen state.
6. Capture title, settled select, cursor positions, confirm transition and
   Round 1 title at 352x224; compare against the established oracles with crop,
   palette and layer-order differences reported separately.
7. Re-run `-EncounterTest` through `COMPLETE` to prove frontend resource loads
   did not break combat memory, CD ownership or the cumulative route.
8. Final `-Clean -Release` title/menu boot.

An approximate visual mock-up is not an exit result. If CRAM, VDP2 format or
disc-lifetime evidence blocks a faithful implementation, stop at a clean
measured checkpoint and record the exact blocker instead of restoring a
capture-derived runtime surface.

## Repository safety

- Stay on `codex/avp-master-plan`; no remote publication.
- Preserve all unrelated untracked diagnostics.
- Stage explicit paths only; never broad-add, reset, clean or stash.
- Never commit ROMs, raw captures, generated copyrighted graphics/audio,
  emulator state, logs, ISO/cue/WAV output, or private disassembly bytes.
- Update `docs/AGENT_HANDOFF.md` newest-first and stop all emulator/MAME
  processes before handing off.
