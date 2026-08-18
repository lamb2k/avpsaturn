# MSHvSF reference lane

This is a concurrent research lane for the private Alien vs Predator Saturn
conversion. It does not replace the AvP route, its parity plan, or its Git
history. The purpose is to use Marvel Super Heroes vs. Street Fighter as a
second Capcom CPS-2-to-Saturn reference so that reusable porting practices are
separated from AvP-specific implementation choices.

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
- `data/mshvsf_saturn_disc_manifest.json`: boot header, ISO filesystem, track
  layout, hashes, and the verified Saturn runtime observation.
- `data/mshvsf_correspondence.json`: one-sided and paired evidence records.
- `data/mshvsf_difference_ledger.json`: only differences supported by current
  evidence; exact mechanics and the Saturn projectile path remain unresolved.

Run the CPS-2 slice and its analyzer together:

```powershell
.\capture_mshvsf_vertical_slice.ps1
```

Run the Saturn reference without editing the source cue or BIN. Pass a native
Yaba Sanshiro play-record directory to reproduce a captured route:

```powershell
.\run_mshvsf_saturn_reference.ps1 `
    -PlayRecordDirectory .\.deps\mshvsf_saturn_playrecord\saturn_ryu_first_pass_b
```

The deterministic Saturn emulated-pad gate is closed. Yaba's native play-record
path restores a fixed backup state and applies exact Port 1 and Port 2 bytes at
recorded frames. Two cold replays produced the same 25 screenshot hashes. The
first pass intentionally stops after the normal-hit reaction; Hadouken command
acceptance and projectile lifecycle are second-pass work. Exact movement,
collision, damage, hitstop, and recovery relationships also stay `UNRESOLVED`
until paired internal measurements exist.

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
