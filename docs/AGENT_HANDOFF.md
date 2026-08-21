# Active agent handoff

## Tranche 1 checkpoint

The selected architecture remains approach E: a title-specific hybrid native AvP port, with MAME 0.289 as semantic oracle. The Tranche 1 implementation payload is commit `a80b5e1f47944473fcea34165bc3d468d16771e2` on `codex/avp-hybrid-tranche-1`, based on immutable supervisor base `b3c95d810ba76d287ca8fdcefb594c42cae0cdb3`.

No Saturn production gameplay, rendering, audio, or loading behavior changed. MSHvSF remains an isolated, read-only one-title reference lane.

## Completed evidence

- `data/avsp_vertical_slice_contract.json` freezes `avspu` USA 940520, canonical 16-ROM identity, MAME `0.289 (mame0289)`, source window 4080-5469 (1,390 frames), source/aperture policy, actor slots, schema and exclusions. SHA-256: `74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638`.
- `capture_vertical_slice.ps1` restores the pinned private EEPROM baseline for each cold boot and runs two identical captures plus a one-frame Button 2 perturbation at frame 4510. Raw traces, images, state/register data and instruction trace remain ignored under `.deps/mame/vertical_slice/`.
- `data/avsp_vertical_slice_oracle_manifest.json` is `MAME_TRACE`: cold-run ledgers are byte-identical (`0e143028a76df6365fb64adfd241238e979cb05d95109a6eac09332b37654e30`), all declared fields are non-vacuous, and the perturbation changes identity first at source frame 4510. Manifest SHA-256: `fc788981297841bdb5f6a3385e7ba7c54afed20ebfa726d7303ff8bba730dfd0`.
- `data/avsp_translation_boundary.json` maps the private opcode trace with explicit `opcodes` instruction and `program` data spaces: 7,314 executed PCs, 8,478 executed edges, zero unresolved computed targets, 714 manually semantic PCs (9.762%), 6,556 mechanically liftable PCs, and 44 hardware-facing event-replacement PCs. Actor fields and CPS/QSound exits are counted without committing trace text or opcode bytes. Manifest SHA-256: `31f2c42d5fd4c53004c737e80cc12d909735ffd6e45304442fa2035ee208e097`.

## RED/GREEN and commands

- RED: `tools/verify_avsp_vertical_slice_oracle.py --generate` failed before new capture because no unified provenance-pinned ledger existed.
- GREEN: `tests/test_avsp_vertical_slice_oracle.py`, `tests/test_avsp_translation_boundary.py`, oracle generation and boundary generation all exit 0. Each test includes its real rejection/mutation control.
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
Review C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-hybrid-tranche1 on branch codex/avp-hybrid-tranche-1 against immutable base b3c95d810ba76d287ca8fdcefb594c42cae0cdb3. Review the Tranche 1 commits oldest first: a80b5e1f47944473fcea34165bc3d468d16771e2 and the current handoff commit. Verify that no production Saturn runtime behavior changed; only avspu is used; MSHvSF remains read-only; raw ROM/capture/state/screenshot/audio/trace data stays ignored under .deps; the vertical-slice contract, two-cold-run oracle, one-frame perturbation, and opcode/program writer-boundary counts agree; every executed PC is classified with zero unresolved indirect targets; and focused controls pass. Treat the complete test.ps1 C compile failure (undefined CAP_ENCOUNTER_START_TRANSITION and CAP_START_TRANSITION_FRAMES in the immutable base) as the documented stop condition, not as a Tranche 1 runtime fix request. Return findings with evidence tiers and do not expand scope.
```
