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

## Tranche 2A result — strict host-suite baseline restored

Branch `codex/avp-host-baseline-tranche-2a` from immutable base
`c9d6dc420df999dae9b8bedaea4bf0f735214ea2`. Two owned production/test files
changed; no other production source, and no oracle/boundary/contract artifact,
was altered.

- **Defect.** `capability_model.c` already enters `CAP_ENCOUNTER_START_TRANSITION`,
  advances its timer, and leaves it at `CAP_START_TRANSITION_FRAMES`, but
  `capability_model.h` declared neither symbol, so the strict C90 host build
  failed at `capability_model.c:961` and `:967`.
- **RED** (`e42224a`): `tests/capability_model_test.c` gained
  `test_start_transition_boundary`, which pins the literal
  `CAP_START_TRANSITION_FRAMES == 30` independently and, with literal step counts
  (29 then one more), the actual state/timer boundary: start moves MAIN_MENU to
  START_TRANSITION at timer 0; 29 no-input steps hold START_TRANSITION at timer
  29; the 30th step advances to CHARACTER_SELECT and resets the timer. The shared
  `start_encounter` helper and `test_character_selection_semantics` now traverse
  the transition before character select. At base this fails strict compilation
  with the two settled undeclared symbols.
- **GREEN** (`7f7453d`): `capability_model.h` adds `CAP_ENCOUNTER_START_TRANSITION`
  immediately after `CAP_ENCOUNTER_MAIN_MENU` and defines
  `CAP_START_TRANSITION_FRAMES` as `30` (CPS2 source frames 1689-1718) beside the
  frontend selection timing constants. Strict
  `gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2` of
  `capability_model.c tests/capability_model_test.c` links and the binary exits 0
  (12,000 deterministic frames).
- **Negative controls** (isolated scratch copies, production test unchanged):
  duration `30`→`29` aborts on `CAP_START_TRANSITION_FRAMES == 30`
  (`capability_model_test.c:45`, exit 134); MAIN_MENU start assignment
  `START_TRANSITION`→`CHARACTER_SELECT` aborts on
  `world.encounter_state == CAP_ENCOUNTER_START_TRANSITION`
  (`capability_model_test.c:54`, exit 134).
- **Cumulative regression.** The complete `test.ps1` reaches and passes the
  formerly blocked gameplay-model compile and exits 0 through the full suite.
  Focused oracle/boundary tests pass; deterministic regeneration keeps the oracle
  ledger `f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1`, the
  boundary artifact `95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4`,
  and the contract `74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638`
  byte-identical; `avspu` verifies good. The fresh worktree required private
  inputs (`.deps`, `avspu` ROMs junctioned read-only to the live cache) and the
  git-ignored `generated/avsp_collision.h` prerequisite, regenerated
  deterministically to its committed report identity
  (`e1e41ea1f1a3666342e8b17e7c42f54e24437af181ccea141d6400019547cc5a`).

Evidence tier: `MEASURED` host only. Saturn target build, emulator, release,
audio, and physical-hardware lanes remain `UNRUN` and unchanged; Capability Gate
stays 0/12. No resource layout or runtime package changed.

## Supervisor acceptance and V2A selection

Codex reviewed the complete
`c9d6dc420df999dae9b8bedaea4bf0f735214ea2..eef350a3de6e44d1648a861ab98215c3d61ce20c`
range and accepted Tranche 2A at
`eef350a3de6e44d1648a861ab98215c3d61ce20c`. The range changes only
`capability_model.h`, `tests/capability_model_test.c`, this handoff, and the
evidence ledger. Strict C90 GREEN and the complete focused oracle/boundary
controls pass; the immutable-line RED reproduces exactly the two missing
declarations; independent duration and transition-state mutations abort at the
intended assertions. The accepted contract, oracle, and boundary Git blobs
remain `74016fb2...`, `106fffb9...`, and `95e002b7...`; `avspu` verifies good.

The next dependency-ready body is Tranche 2B / V2A in
`docs/NEXT_AGENT_PROMPT.md`: derive and validate the smallest closed executable
writer/routine set responsible for the class `0x1F` enemy HIT and KO animation
repoints in source frames 5191-5469. The committed result is a provenance-rich
manifest and its generator/tests, not raw trace/disassembly/opcode material and
not production lifted C. It must bind every selected PC/edge to the accepted
translation boundary, correlate the HIT/KO semantic changes to executed writer
sites, close calls/data/event exits, and prove zero unresolved or unattributed
selected dependencies. Capability Gate remains 0/12.

## Tranche 2B candidate — class 0x1F HIT/KO writer-set closure

Branch `codex/avp-writer-map-tranche-2b` began at immutable base
`065ddfdb586184074973c2bccad55a45007f5f32`. The candidate adds only the owned
focused test, mapper/validator, bounded metadata manifest, and two evidence
documents. No production C/H, accepted oracle/boundary/contract, build/package
path, `.deps`, or ROM input changed.

- RED commit `5e823a3`: `python tests/test_avsp_hit_ko_writer_set.py` exited 1
  because the production mapper did not exist.
- GREEN commit `1483137`: mapper self-test, deterministic generation, and the
  focused artifact test exit 0. The manifest contains 3 routine units, 13
  selected PCs, 3 selected dynamic edges, zero selected computed targets,
  zero unresolved/unattributed dependencies, and 2 typed HIT/KO event exits.
  HIT frame 5191 and KO frame 5330 both correlate exact `anim_record` writer
  `0x016526`; this closes `GAP_EXTERNAL_REPOINT` as ownership only.
- Both validator paths reject all nine required deep-copy mutations. The
  isolated private-input control changes the HIT animation pointer in memory
  and is rejected; canonical private evidence remains read-only.
- Two `--generate` runs are byte-identical at SHA-256
  `d2f000c01555ef10b1db83fc13d8217fc536bcc579dfd17991e832ed54005430`.
- Focused writer-set, oracle, and boundary tests exit 0. The first cumulative
  run stopped because the known ignored `generated/avsp_collision.h`
  prerequisite was absent. It was regenerated from read-only junctioned
  inputs (report identity `e1e41ea1...`), after which complete `test.ps1`
  exited 0. Five regenerated pre-existing provenance drifts were inspected and
  explicitly restored; accepted artifacts remain byte-identical.

Evidence is limited to `MAME_TRACE`, `STATIC_ANALYSIS`, and `MEASURED` host
results. Behavioral zero-diff lifting, Saturn target/emulator/release/audio,
memory/video timing, physical hardware, and every Capability Gate condition
remain open. Supervisor review and continuation selection are required.

## Tranche 2B correction — target-actor-derived writer closure

- RED `7bba0cf`: the expanded focused test failed at the candidate because
  routine `0x016526` had no derived caller/callee closure. The original nine
  shape mutations already rejected; the new derivation controls exposed the
  missing target-write, semantic, routine, dependency, and alignment binding.
- GREEN derives from a private MAME 0.289 target-actor watchpoint capture:
  1,390 semantic samples create 1,389 execution intervals (no synthetic final
  epoch). HIT sample 5191 binds the exact `0xffa01c` long write in interval
  5190; KO sample 5330 binds its own instance in interval 5329. Both resolve
  actual store PC `0x016526` from watchpoint successor `0x01652a`, the opcode
  effective address, and live `A6=0xffa000`; the former ambiguous KO repeat at
  interval 5342 is not selected.
- The manifest now contains two connected dynamic transition paths (152 HIT,
  178 KO executed PCs), the 11-PC dispatch and the complete eight-PC
  `0x016518..0x016534` animation pointer-selection routine. It records dynamic
  callers/callees, typed HIT/KO exits, program-space pointer dependencies, and
  zero unresolved/unattributed dependencies. No production C/H changed.
- `--self-test`, deterministic double `--generate`, focused writer/oracle/
  boundary tests, isolated private HIT/KO value and event removal, destination,
  required-edge, and alignment controls, and `-verifyroms avspu` pass. The
  manifest SHA-256 is `fd13d824a4858906584a949a4f02c87ea1ac76a17bc52504945e40fcba485796`.
  Full `test.ps1` remains unrun in this worktree because it lacks the staged
  ignored ROM/dependency tree; no Saturn/emulator/release/hardware claim moves.

## Tranche 2B correction — full seven-field health/hit closure

Branch `codex/avp-writer-map-tranche-2b-corrections` began clean at immutable
base `308143a687190a2f9be2b60ada669e907592a5b3`. It supersedes only the
preceding candidate correction above. The correction changes the owned mapper,
focused test, bounded manifest, and private-capture *tool* configuration; it
does not commit capture output, raw trace/opcodes/program data, ROMs, production
C/H, or any accepted contract/oracle/translation-boundary artifact.

- **RED** (`e54035f`): `python -B tests/test_avsp_hit_ko_writer_set.py` exited
  1 at the immutable base. It specifically exposed absent health/hit coverage,
  transitions, and writer instances; an out-of-bound selected PC; corrupt
  anchors and derived counts; an internally shaped but unobserved edge;
  routine/PC-union and caller/callee drift; and a synchronized integrity-hash
  anchor mutation.
- **GREEN** (`e203b7c`): the seven semantic fields are parsed from 1,390
  target-actor samples, with interval N aligned to semantic sample N+1. The
  private MAME 0.289 watchpoint parser retains `D0/D1` and `A0..A7`; actual
  68000 effective addresses and live bindings resolve health and hit writes.
  Health transitions are `87→63`, `63→39`, `39→8`, and `8→-1` at intervals
  5189, 5235, 5282, and 5328; selected health writer PCs are `0x01d58a`,
  `0x01d592`, and `0x0605a6`. There are 42 hit-value transitions and 50
  in-window hit observations at `0x0176c0`, `0x01d0ac`, `0x01e9ce`,
  `0x01e9dc`, and `0x01f31c`.
- The closed manifest records all seven fields with transition counts
  state/substate/action/animation-record/animation-timer/health/hit-value of
  `7/16/57/274/704/4/42`, 7 health and 50 hit observations, 301 selected PCs,
  302 selected dynamic edges, 12 routines, 9 computed targets, 2 typed event
  exits, and zero unresolved or unattributed dependencies. Its routine entries
  are `0x01e888`, `0x01f250`, `0x01f6c6`, `0x016518`, and the eight local
  health/hit writer contexts. Exact selected-PC, edge, routine,
  field-transition, and writer-observation hashes bind the result to the
  7,314-PC accepted translation boundary.
- **REFACTOR** (`fe375c6`): focused deep-copy controls additionally reject
  removal of health/hit observations or dependency PCs, health before-value,
  destination, width, actual-PC, and live-register corruption, plus an
  unattributed dependency. Mapper self-tests also reject HIT/KO writer removal,
  semantic/alignment/edge/routine/count/exclusion/raw-content changes. An
  in-memory private-input scratch control independently changes a health sample
  and removes a hit watchpoint; both fail end-to-end without altering canonical
  evidence.
- Two post-GREEN generations are byte-identical (119,800 bytes) at SHA-256
  `6be81db48baad4327f2ef53a879cba0c9f67bed610127494f16f3c6deab9ae28`.
  Mapper self-test, scratch mutation test, focused writer/oracle/boundary
  tests, and `mame.exe -rompath ..\\AvPSaturnCapabilityTest -verifyroms avspu`
  exit 0. An isolated-copy `test.ps1` run passed all preceding stages but
  stopped at the unrelated tile-budget control: `--scope round1 was accepted`
  against the current `AVSP_TILE_REGION_BYTES` carve. This correction neither
  changes nor claims that legacy-suite result.

Evidence remains `MAME_TRACE`, `STATIC_ANALYSIS`, and `MEASURED` host only.
There is no production lift, behavioral-differential result, Saturn build,
emulator, release, audio, timing, memory, scanout, or physical-hardware claim.
Capability Gate remains 0/12. Supervisor disposition is required before any
later tranche is selected.
