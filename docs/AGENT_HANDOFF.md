# Active agent handoff

## Tranche 1 checkpoint

The selected architecture remains approach E: a title-specific hybrid native AvP port, with MAME 0.289 as semantic oracle. The Tranche 1 implementation payload began at commit `a80b5e1f47944473fcea34165bc3d468d16771e2` on `codex/avp-hybrid-tranche-1`, based on immutable supervisor base `b3c95d810ba76d287ca8fdcefb594c42cae0cdb3`, and the supervisor review's five blocking findings were then corrected on the same branch (see "Tranche 1 review corrections" below).

No Saturn production gameplay, rendering, audio, or loading behavior changed. MSHvSF remains an isolated, read-only one-title reference lane.

## Completed evidence

- `data/avsp_vertical_slice_contract.json` freezes `avspu` USA 940520, canonical 16-ROM identity, MAME `0.289 (mame0289)`, source window 4080-5469 (1,390 frames), source/aperture policy, actor slots, schema (including `bank_writes`) and exclusions. SHA-256: `74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638`.
- `capture_vertical_slice.ps1` stages a pinned private **config** baseline and restores it (declared absence today) plus the pinned NVRAM baseline before every MAME process, records each run's starting config identity, and runs two identical cold captures plus a one-frame Button 2 perturbation at frame 4510. Raw traces, images, state/register data and instruction trace remain ignored under `.deps/mame/vertical_slice/`.
- `data/avsp_vertical_slice_oracle_manifest.json` is `MAME_TRACE`: both cold boots start from identical pinned config (`config_baseline_sha256=absent`, per-run all `absent`) and NVRAM and are byte-identical (semantic ledger `f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1`); every declared field including `bank_writes` is non-vacuous; an input-excluded projection of the perturbation first differs downstream at source frame 4512 (after the injected frame 4510), changing the `player` field class. Manifest SHA-256: `106fffb92cc5a14acf5fdae7eb14d33b7d9206b9f9ecffcbac67a6fc326696d2`.
- `data/avsp_translation_boundary.json` maps the private opcode trace (SHA-256 `9bbbc28715668348aeb4d206b7381073123c5b22ec9e2f2557bda1622e142f5f`) with explicit `opcodes` instruction and `program` data spaces: 7,314 executed PCs, 8,222 executed edges (never crossing an interrupt/flush discontinuity), 1,389 interrupt entries. 1,833 direct transfers are cross-checked against the decrypted **opcode** image and observed successors with zero contradictions/mismatches; 126 computed sites are all resolved (275 observed targets) so unresolved indirect targets are zero **by computation**; every executed PC and code target is word-aligned in ROM (0 instruction-space violations). The **program/data** image is enforced: 2 ROM data spans (`0x1f4600`, `0x1f4e00`) are read in-bounds from it, RAM/hardware operands must lie outside it, and all 7,314 executed PCs diverge between the two images (proving the CPS-2 opcode/program spaces are distinct). 714 manually semantic PCs (9.762%), 6,556 mechanically liftable, 44 hardware-facing. No trace text or opcode bytes are committed. Manifest SHA-256: `95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4`.

## Tranche 1 review corrections

The supervisor review's five blocking findings were corrected without any production Saturn runtime change:

1. **Pinned config parity.** `capture_vertical_slice.ps1` snapshots/stages the intended private config baseline and restores identical bytes (or identical declared absence) before every MAME process, recording each run's starting config identity. `validate_provenance` requires exactly the three unique runs `cold_run_1`, `cold_run_2`, `one_frame_perturbation`, each with its expected perturbation frame and the identical pinned config; a missing run, a duplicate run, or a per-run config/frame mismatch is rejected.
2. **Downstream perturbation gate.** The verifier compares an input-excluded semantic projection and requires a declared downstream `player/enemy/object/audio/scanout` change strictly after frame 4510, recording the first downstream-different source frame (4512) and changed field classes; a synthetic input-only mutation fails the control.
3. **`bank_writes` in the ledger.** `bank_writes` is now part of the canonical per-frame ledger entry (so it participates in two-run determinism) and has its own non-vacuity check.
4. **Auditable boundary proof.** `unresolved` is computed, never assigned: every direct/computed edge is enumerated, control kinds preserved, direct targets decoded from the pinned opcode image and cross-checked against the disassembly operand and observed successors. The program/data image is actually enforced (ROM data spans read in-bounds, RAM/hardware operands required outside the ROM image, and opcode↔program divergence over every executed PC), and missing/contradictory targets fail.
5. **Real mutation controls.** The boundary self-test builds a synthetic model plus a synthetic committed report and runs the production validators. Seven model controls (remove PC, edge, computed target, global attribution, misaligned PC, out-of-bounds ROM span, identical opcode/program images) and five committed-artifact controls (zeroed opcode/dynamic-validated, zeroed observed targets, zeroed program bytes + wrong hash, removed global attribution, removed address-space attribution) each make validation fail. The focused test wrapper also loads and validates the committed boundary artifact.

Review round 2 closed three further validator gaps: provenance now rejects missing/duplicate/wrong-frame runs (was: accepted whatever records were present); the program/data image is read and bounds-enforced with proven opcode/program divergence (was: only sized and hashed); and `validate_committed` now rejects zeroed target/attribution/program evidence and is exercised by dedicated committed-artifact mutation controls (was: accepted those corruptions).

## RED/GREEN and commands

- RED: at the pre-correction HEAD the perturbation gate passed on an input-only change and the boundary asserted `unresolved=[]`; the boundary self-test was a literal set comparison. These are the corrected defects.
- GREEN: `tests/test_avsp_vertical_slice_oracle.py`, `tests/test_avsp_translation_boundary.py`, oracle generation and boundary generation all exit 0. Each test includes its real rejection/mutation control and validates the committed artifact.
- Determinism: `cold_run_1` and `cold_run_2` semantic ledgers are byte-identical (`f6e81316…`); the perturbation ledger differs (`883a5a08…`).
- MAME identity: `.deps/mame/mame0289/mame.exe -rompath . -verifyroms avspu` exits 0. The non-canonical local `dl-1425.bin` dependency is hash-recorded and excluded from the 16-member target-set contract.

## Regression result and stop boundary

The complete `test.ps1` run was attempted in this clean worktree. It stops at the immutable-base C compilation before the new tranche checks:

```text
capability_model.c:961:34: error: CAP_ENCOUNTER_START_TRANSITION undeclared
capability_model.c:967:39: error: CAP_START_TRANSITION_FRAMES undeclared
```

Both references are present at the immutable base while the enum/header does not define them. Repair requires a production-runtime change, prohibited in Tranche 1; this is the declared stop condition for the complete legacy host suite. It does not alter the passing MAME-only oracle or boundary evidence.

## Tranche 1 correction — round 3 (separation binding)

A validator-only correction closed the last committed-boundary falsification
gap without any production, runtime, oracle, or artifact change.

- **Defect.** `validate_committed` accepted the opcode/program separation proof
  whenever `executed_pcs_compared > 0` and `divergent_pcs > 0`. A weakened
  artifact claiming a single-PC divergence (`executed_pcs_compared=1`,
  `divergent_pcs=1`) therefore passed the completeness proof even though the
  real artifact compares and diverges over all 7,314 executed PCs.
- **RED** (`0ce0efe`): the focused test gained a committed-artifact
  negative-control battery — nine controls, each deep-copies the real committed
  artifact, mutates one field, and requires the production `validate_committed`
  to reject it. At base the two separation controls were ACCEPTED, so
  `python tests/test_avsp_translation_boundary.py` exited 1 on exactly those two.
- **GREEN** (`c353772`): `validate_committed` now additionally requires
  `opcode_program_separation.executed_pcs_compared == coverage.executed_pc_count`
  and `divergent_pcs == executed_pcs_compared`. The self-test committed-artifact
  controls grew from five to nine (adding zeroed direct sites, byte-count-only
  and hash-only program corruptions, and both separation reductions). All nine
  now reject; the unmodified artifact still validates.
- **Determinism.** `tools/map_avsp_translation_boundary.py --generate` twice
  reproduces `data/avsp_translation_boundary.json` byte-for-byte at SHA-256
  `95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4`
  (7,314 compared / 7,314 divergent over 7,314 executed PCs; unchanged). The
  oracle ledger (`f6e81316…`) and `avspu` `-verifyroms` are unaffected. Only
  `tools/map_avsp_translation_boundary.py` and
  `tests/test_avsp_translation_boundary.py` changed; no C/H/runtime/build/`.deps`
  file was touched. The complete `test.ps1` stop condition is unchanged
  (immutable-base `CAP_ENCOUNTER_START_TRANSITION` / `CAP_START_TRANSITION_FRAMES`
  undeclared, not repaired).

## Supervisor acceptance and next selection

Codex accepted Tranche 1 at
`a11527a18c6ec02d3bc3f3421674755a3102c6c5`. The exact target, deterministic
oracle, executable boundary, provenance contract, and all committed-artifact
controls are accepted at their recorded MAME/translated tiers. Capability Gate
remains 0/12; no Saturn runtime, emulator, release, or physical claim advanced.

The next dependency-ready body is `docs/NEXT_AGENT_PROMPT.md`: Tranche 2A
restores the strict host-suite baseline by adding the historically intended
start-transition enum member and exact 30-frame duration, with literal boundary
tests and scratch mutations. It is deliberately separate from V2 lifting.

Historical sibling commit `c7e8f80a54725977a5e61486bb9960f37f1680b7`
is read-only solution evidence. It must not be cherry-picked because it contains
unrelated loader/build/generator changes.

The Tranche 2A implementor must return through
`docs/CODEX_REVIEW_TEMPLATE.md`. The supervisor alone accepts the result and
selects V2 or a correction body.
