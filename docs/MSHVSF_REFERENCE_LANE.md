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

The supplied reference set currently has two packaging blockers that must
remain visible:

1. The cue references `Marvel Super Heroes vs. Street Fighter.iso`, while the
   supplied binary is named `.bin`. This makes the cue internally inconsistent;
   do not silently rename or overwrite the supplied media.
2. `mshvsf.key` and `dl-1425.bin` are now present beside the archive and their
   SHA-1 values match the MAME 0.289 manifest, but MAME still reports them as
   missing because they are not in the set/shared-ROM layout it searches. No
   CPS-2 behavior claim should be marked verified until the complete,
   authorized set passes `-verifyroms`.

These blockers do not prevent static inspection of the supplied media or
preparation of the comparison schema. They do prevent a reproducible MAME
behavior capture and a clean Saturn boot from the supplied cue as-is. Keep the
source files untouched; place them in the loader's expected set/shared-ROM
layout or package them through the normal authorized ROM-set workflow before
the next audit.

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

No pattern becomes an AvP standard from a single screenshot or from a local
file-name coincidence. The evidence chain is:

```text
complete ROM set -> deterministic MAME observation -> analyzer -> Saturn observation
-> correspondence/difference record -> AvP validation test
```

The MSHvSF lane is private research. Do not commit ROMs, raw captures, decoded
assets, disc images, or redistributed material.
