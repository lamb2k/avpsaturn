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

## Next bounded work

Do not resume the archived RP roadmap or alter Saturn runtime behavior. Resolve the unrelated base compile defect in an authorized runtime tranche, then begin V2 only from the frozen oracle and boundary: lift the smallest selected writer set for player/class `0x1F` enemy, animation HIT/KO repoint, collision, camera, stage, and semantic event production. Preserve all raw evidence private.

## CODEX_REVIEW_INVOCATION

```text
Review C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-hybrid-tranche1 on branch codex/avp-hybrid-tranche-1 against immutable base b3c95d810ba76d287ca8fdcefb594c42cae0cdb3. Review the full range b3c95d8..HEAD: the original Tranche 1 commit a80b5e1f47944473fcea34165bc3d468d16771e2 and the review-correction commits that follow it (oldest first). Verify that no production Saturn runtime behavior changed; only avspu is used; MSHvSF remains read-only; raw ROM/capture/state/screenshot/audio/trace/opcode data stays ignored under .deps. Confirm the five corrections: (1) every cold run restores the identical pinned config baseline and records per-run config identity, and provenance rejects a per-run mismatch; (2) the perturbation gate compares an input-excluded projection and requires a downstream change after frame 4510 (recorded first-different frame and changed field classes), with a synthetic input-only mutation failing; (3) bank_writes participates in the canonical ledger and two-run determinism/non-vacuity; (4) unresolved indirect targets are zero by computation with direct targets validated against the pinned opcode image and the instruction/data boundary enforced; (5) the boundary self-test runs the production validator and each of the five removals (PC, edge, computed target, global attribution, address-space attribution) makes it fail, and the focused test validates the committed artifact. Treat the complete test.ps1 C compile failure (undefined CAP_ENCOUNTER_START_TRANSITION and CAP_START_TRANSITION_FRAMES in the immutable base) as the documented stop condition, not a Tranche 1 runtime fix request. Return findings with evidence tiers and do not expand scope.
```
