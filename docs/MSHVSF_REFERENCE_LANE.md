# MSHvSF reference lane

This is a concurrent research lane for the private Alien vs Predator Saturn
conversion. It does not replace the AvP route, its parity plan, or its Git
history. The purpose is to use Marvel Super Heroes vs. Street Fighter as a
second Capcom CPS-2-to-Saturn reference so that reusable porting practices are
separated from AvP-specific implementation choices.

The volatile restart checkpoint for this branch is
`docs/MSHVSF_AGENT_HANDOFF.md`. The inherited `docs/AGENT_HANDOFF.md` describes
the AvP implementation line and is not the Marvel work queue.

## Operating rule

Use the MSHvSF CPS-2 program and graphics data to study Capcom's source-side
representation, and the official Saturn disc as a target-side observation
reference. Record conclusions as `MATCH`, `EQUIVALENT`, `PLATFORM ADAPTATION`,
`OPTIMIZATION`, `REDUCTION`, `ALTERATION`, `ADDITION`, `BUG`, or `UNRESOLVED`.
Do not promote a pattern into the AvP runtime until it has evidence on both
sides and a falsification test.

The two projects remain separate in implementation terms:

| Lane | Production target | Reference role |
|---|---|---|
| AvP | Native SH-2 Round 1 through the Round 2 boundary | Primary implementation and acceptance route |
| MSHvSF | Not a second Saturn build in this lane | Comparative Capcom architecture and fidelity evidence |

## First vertical slice

The initial comparison is deliberately narrow:

```text
input -> movement -> normal attack -> hit reaction -> projectile/special -> audio event -> render
```

For each event, maintain the following record:

| Field | Required content |
|---|---|
| Semantic concept | The behavior being compared |
| CPS-2 evidence | MAME state, ROM table, address, capture frame, or data hash |
| Saturn evidence | Disc member, observed behavior, address, or capture frame |
| Relationship | One fidelity classification from the list above |
| Test | Deterministic input and expected event sequence |
| Falsification | The observation that would disprove the mapping |
| Confidence | `HIGH`, `MEDIUM`, or `LOW` |
| AvP lesson | What can be reused, and what remains title-specific |

Gameplay timing and presentation timing must be recorded separately. A Saturn
animation reduction is not evidence of a gameplay reduction, and a visually
similar attack is not evidence of mechanically identical hit timing.

## Current local audit

Run from this repository root:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\audit_mshvsf_reference.py `
    --mame .\.deps\mame\mame0289\mame.exe
```

The audit is metadata-only. It records file hashes, cue references, track
types, archive members, and the MAME verification result without extracting or
rewriting ROM data. Its output is `data/mshvsf_reference_audit.json`.

The supplied reference set has two source-packaging defects, both handled by
temporary launch overlays that leave the supplied files unchanged:

1. The cue references `Marvel Super Heroes vs. Street Fighter.iso`, while the
   supplied binary is named `.bin`. This makes the cue internally inconsistent;
   do not silently rename or overwrite the supplied media.
2. `mshvsf.key` and `dl-1425.bin` are loose beside the archive instead of in
   MAME's set/shared-ROM layout. The MAME launcher creates a temporary hard-link
   overlay containing the archive and both loose dependencies.

The overlay passes MAME 0.289 `-verifyroms`: `romset mshvsf is good`. A cold
replay also produced the same derived vertical-slice report hash twice. The
Saturn launcher writes a temporary cue whose first `FILE` entry points at the
unchanged BIN and selects the 32 Mbit expansion cartridge. Yaba Sanshiro 2
v1.20.37 then reaches the licensed legal screen, title, and attract gameplay.

Verified reports:

- `data/mshvsf_reference_audit.json`: source hashes, cue defect, and passing
  MAME audit.
- `data/mshvsf_cps2_vertical_slice.json`: deterministic Ryu idle, walk, jump,
  normal, Hadouken, collision, and hit-reaction anchors.
- `data/mshvsf_saturn_first_pass.json`: two byte-identical cold replays of the
  Saturn Ryu route through idle, walk, jump, normal collision, visible health
  response, hit reaction, and recovery.
- `data/mshvsf_cps2_semantic_model.json` and
  `data/mshvsf_saturn_semantic_model.json`: system-by-system behavioral models
  with structural gaps kept explicit.
- `data/mshvsf_reconstructed_vertical_slice.json`: paired semantic event order
  and the exact first-pass/projectile boundary.
- `data/mshvsf_saturn_disc_manifest.json`: boot header, ISO filesystem, track
  layout, hashes, and the verified Saturn runtime observation.
- `data/mshvsf_saturn_asset_topology.json`: measured package-family counts and
  sizes without treating disc bytes as RAM residency.
- `data/mshvsf_saturn_program_inventory.json`: hashes, module boundaries,
  filename references, short SH-2 instruction samples, and static hardware
  address leads derived from ignored private members. Runtime ownership stays
  unresolved.
- `data/mshvsf_saturn_runtime_memory.json`: exact-frame MCP dumps at idle 3540,
  normal-active 3828, impact 3840, and recovery 3900. It records per-region
  hashes, nonzero and changed 4 KiB pages, changed-byte counts, and sequential
  VDP1 command-table summaries without committing raw memory.
- `data/mshvsf_saturn_vdp1_control_flow.json`: VDP1 command lists walked by real
  jump/call/return/skip control flow. Reports reachable slots separately from
  sequentially stored slots and from stored non-zero extent, plus command types,
  sprite sizes, flip use, colour banks and merged texture spans.
- `data/mshvsf_saturn_vdp2_scsp.json`: VDP2 colour ownership and SCSP slot
  activity at the same four anchors. Records the unreadable VDP2 register block
  as an explicit instrument limit.
- `data/reference_engine_normal_hit_report.json`: the generated CPS2-to-Saturn
  reference-engine normal-hit report, with input hashes, semantic events,
  per-frame VDP1 pressure, separate resource regions, unresolved fields,
  prohibited inferences and the required AvP probe.
- `data/mshvsf_correspondence.json`: one-sided and paired evidence records.
- `data/mshvsf_difference_ledger.json`: only differences supported by current
  evidence; exact mechanics and the Saturn projectile path remain unresolved.
- `data/mshvsf_hardware_budget.json`, `data/mshvsf_fidelity_scorecard.json`, and
  `data/mshvsf_porting_patterns.json`: open measurement ledger, six-dimension
  scorecard, and reusable/candidate pattern library.

Run the CPS-2 slice and its analyzer together:

```powershell
.\capture_mshvsf_vertical_slice.ps1
```

Regenerate and validate the tracked semantic/training package:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_mshvsf_saturn_disc.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_mshvsf_saturn_asset_topology.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\extract_mshvsf_saturn_members.py
$env:PYTHONPATH = (Resolve-Path .\.deps\capstone)
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_mshvsf_saturn_programs.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\build_mshvsf_semantic_models.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\validate_mshvsf_training_package.py
```

Run the Saturn reference without editing the source cue or BIN. Pass a native
Yaba Sanshiro play-record directory to reproduce a captured route:

```powershell
.\run_mshvsf_saturn_reference.ps1 `
    -PlayRecordDirectory .\.deps\mshvsf_saturn_playrecord\saturn_ryu_first_pass_b
```

Capture synchronized Saturn memory through stock Yaba Sanshiro v1.20.37's
localhost MCP debug server:

```powershell
.\capture_mshvsf_saturn_memory.ps1
```

The wrapper replays the same deterministic record, pauses on exact frame
boundaries, writes ignored raw dumps under `.deps\mshvsf_saturn_state`, and
regenerates `data/mshvsf_saturn_runtime_memory.json`. It refuses to overwrite
an existing raw capture.

The deterministic Saturn emulated-pad gate is closed. Yaba's native play-record
path restores a fixed backup state and applies exact Port 1 and Port 2 bytes at
recorded frames. Two cold replays produced the same 25 screenshot hashes. The
first pass intentionally stops after the normal-hit reaction; Hadouken command
acceptance and projectile lifecycle are second-pass work. Exact movement,
collision, damage, hitstop, and recovery relationships also stay `UNRESOLVED`
until paired internal measurements exist.

The first internal-memory pass is measured on the Saturn side. Across the four
anchors, the 4 MiB cartridge and VDP2 VRAM are byte-identical while high work
RAM, low work RAM, sound RAM, VDP1 VRAM, SCSP registers, and color RAM change.
This proves stable residency during this short normal-hit window, not allocator
ownership or an AvP budget. Hadouken remains deferred.

## Reusable playbook outputs

The reference lane will grow these artifacts without modifying the AvP runtime:

1. `correspondence` records mapping semantic behavior, CPS-2 representation,
   Saturn responsibility, evidence, confidence, and a falsification test.
2. `difference ledger` records observable behavior and presentation changes
   independently, with one of the historical-fidelity classifications.
3. `hardware budget` records SH-2, VDP1, VDP2, work RAM, expansion RAM, SCSP,
   CD access, and DMA responsibilities.
4. `porting patterns` records the problem, Capcom's observed solution, the
   hardware rationale, constraints, and which AvP systems can reuse it.
5. `acceptance checklist` covers route parity, animation coverage, stress-case
   performance, loading, audio, and unresolved deviations.

The reusable method and initial hardware-responsibility map are recorded in
`docs/CAPCOM_SATURN_PORTING_PLAYBOOK.md` and
`docs/MSHVSF_SATURN_ARCHITECTURE.md`.

## CPS2-to-Saturn reference engine

`reference_engine/` is a host-side executable model of the translation boundary:
source semantic layer, translation layer, Saturn backend layer, with every field
labelled `MEASURED`, `DECODED`, `INFERRED`, `ADAPTED` or `UNRESOLVED` and the
labelling enforced in code. Its architecture is
`docs/CPS2_SATURN_REFERENCE_ENGINE.md`; the AvP-facing question set is
`docs/CPS2_SATURN_REFERENCE_ENGINE_AVP_ADAPTERS.md`.

It is not a Saturn runtime, not a CPS2 emulator, and not an AvP implementation
branch. Run the analyzers, the model and its tests with:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_mshvsf_saturn_vdp1.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_mshvsf_saturn_video_audio.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\build_reference_engine_report.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\run_reference_engine_tests.py
```

The two analyzers need the ignored raw captures under
`.deps\mshvsf_saturn_state`; the model and its tests run from tracked JSON
alone. `build_reference_engine_report.py --check` verifies the tracked report
against a fresh run without rewriting it.

The team package also includes:

- `docs/CAPCOM_SATURN_TRAINING_EXERCISES.md`
- `docs/CAPCOM_SATURN_PORT_CANDIDATE_CHECKLIST.md`
- `docs/CAPCOM_SATURN_PORT_ACCEPTANCE_CHECKLIST.md`
- `docs/CAPCOM_SATURN_FIDELITY_STANDARD.md`
- `docs/MSHVSF_TRAINING_PLAN_STATUS.md`
- `docs/MSHVSF_TO_AVP_TRANSFER_MATRIX.md`
- reusable JSON templates under `templates/capcom_saturn_porting/`

## Non-invasive AvP validation probe

The first reusable probe is methodological, not a gameplay transplant. On an
AvP branch created from the AvP line, replay one existing player-to-enemy normal
hit with a controlled neutral enemy and record input, movement, collision,
health response, hit reaction, and recovery as separate semantic anchors. Pass
only when two cold runs reproduce the same route and hashes. Do not merge this
MSHvSF branch into AvP, copy fighter timing values, or classify a Saturn hardware
responsibility from the external screenshots alone.

This keeps AvP history and implementation ownership independent while allowing
the evidence discipline proven here to be applied there deliberately.

No pattern becomes an AvP standard from a single screenshot or from a local
file-name coincidence. The evidence chain is:

```text
complete ROM set -> deterministic MAME observation -> analyzer -> Saturn observation
-> correspondence/difference record -> AvP validation test
```

The MSHvSF lane is private research. Do not commit ROMs, raw captures, decoded
assets, disc images, or redistributed material.
