# Verification lanes

Tests retire one claim at one evidence tier. They do not promote themselves.
Use `verify.ps1` for routine work and keep `test.ps1` as the complete legacy
regression implementation.

## Fast

```powershell
.\verify.ps1 -Lane Fast
```

Runs workflow-policy checks plus the direct V2 writer/oracle/boundary tests. A
task can add focused Python tests with `-Test` or portable C commands with
`-Command`. Fast never regenerates private capture evidence.

Required during iteration. Behavioral work needs a failing-first fixture and a
real mutation or negative control.

## Oracle

```powershell
.\verify.ps1 -Lane Oracle
```

Runs target identity, writer-map self-tests and scratch mutations, committed
writer/oracle/boundary validators, and provenance bindings. If a pinned private
input is absent, the lane is `INCOMPLETE` and exits nonzero; it cannot report an
unqualified pass. Pass `-Regenerate` only in an assigned clean worktree that
owns the generated artifacts and has the pinned private inputs.

Required for oracle, translator, evidence schema, validator, writer-boundary,
or lifted-behavior changes.

## Target

Build-only iteration must be requested explicitly:

```powershell
.\verify.ps1 -Lane Target -TargetProfile EncounterTest -BuildOnly
```

Saturn-facing acceptance requires the exact normal image and profile-specific
semantic/render/final-scanout readback:

```powershell
.\verify.ps1 -Lane Target -TargetProfile Release -Emulator `
  -EmulatorCheck <checked-in-profile-readback-collector.ps1>
```

Builds Saturn-facing code with host tests skipped because Fast/Oracle are
separate. `Release` requests and verifies the exact `release-normal-release`
profile. Required artifacts must exist and are hashed. `-Emulator` is invalid
without at least one executable profile-specific collector/check; launching
alone is not evidence. The lane then automatically runs the checked-in
`tests/target/verify_release_readback.py`, which binds the ignored report to the
exact ISO/profile, accepted oracle, emulator identity, and semantic, resource,
render, and final-scanout domains. `-BuildOnly` returns the distinct status
`BUILD_ONLY` and is explicitly insufficient for Saturn-facing acceptance.

Required when Saturn-facing code, packaging, resources, or device behavior
changes. Before acceptance, the release profile must cold-boot and its relevant
semantic state, device resources, render state, and final scanout must pass
bounded emulator checks. Record the compile profile and artifact hashes; never
relabel this as physical evidence.

## Full

```powershell
.\verify.ps1 -Lane Full
```

Runs the complete `test.ps1` legacy/generator chain. It can rewrite tracked
evidence, so run it only in the checkpoint's clean worktree when those paths are
owned, or in an isolated shadow copy. Review every generated diff.

Required at acceptance, before merge, and after foundational tooling changes.
For Saturn-facing acceptance, Full never substitutes for the separate exact
`release-normal-release` Target plus emulator-readback gate.

## Risk mapping

| Tier | Typical change | Minimum lanes |
|---|---|---|
| 0 | Mechanical or documentation-only | Fast |
| 1 | Translated behavior or bounded runtime feature | Fast + Oracle; release Target + emulator readback if Saturn-facing |
| 2 | Oracle, validator, memory/device ownership, physical timing, architecture | Fast + Oracle + Full; release Target + emulator readback when Saturn-facing |

Physical Saturn testing is outside these host lanes. Follow
`docs/HARDWARE_TEST.md`; only that procedure may create `PHYSICAL_SATURN`
evidence.
