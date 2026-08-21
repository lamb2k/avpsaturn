# Verification model

Tests retire one claim at one evidence tier. Machine validation, fidelity
evidence, emulator self-review, user approval, and physical proof remain
independent.

## DEV inner loop

For every implementation iteration run:

- strict compile for touched code;
- directly relevant focused tests;
- a deterministic repeat;
- one non-vacuous negative control that fails when the tested behavior or
  artifact is deliberately perturbed.

DEV is scoped to the active task card. Do not run the complete writer boundary,
Oracle lane, or Full suite on every input, animation, rendering, asset, or
integration edit.

## BENCH self-review

Before a subsystem can receive a salvage decision, run:

- its isolated subsystem test;
- its dedicated Saturn diagnostic build;
- a pinned-emulator boot of the exact image;
- automated runtime-ready and asset-failure readback;
- actor position and render-count diagnostics where relevant;
- a bounded stability run;
- a screenshot or short clip when visible or audible;
- comparison with the old-build baseline and existing source evidence.

A BENCH result can establish technical viability and measured fidelity. It
cannot self-approve subjective scale, pivot, cadence, feel, palette,
composition, camera, or audio qualities.

## CHECKPOINT integration and review

For combined promoted systems run:

- focused regression checks for every previously approved component at risk;
- the combined diagnostic build and emulator readback;
- deterministic repeat and negative control;
- a human-review package under ignored `build/feedback/<task-id>/` whenever
  appearance or feel is subjective.

The package records screenshot/clip, readback, build profile and commit, active
and disabled systems, adaptations, stability/frame-pacing notes, and exact
questions. Approval is explicit and component-scoped; silence is not approval.

## Fast workflow lane

```powershell
.\verify.ps1 -Lane Fast
```

Fast runs workflow-policy, task-card/state, migration-map schema, and existing
focused deterministic checks without regenerating private captures. Run it for
this governance update and as the ordinary repository-level smoke lane.

## Oracle lane

```powershell
.\verify.ps1 -Lane Oracle
```

Oracle verifies MAME provenance, deterministic oracle artifacts,
translation/writer boundaries, validators, and mutation controls. Use it when
the active task changes evidence, lifted behavior, source identity, or a trust
boundary. Missing pinned private inputs makes the lane `INCOMPLETE`, never an
unqualified pass.

## Target and normal-release lanes

Build-only iteration is explicit:

```powershell
.\verify.ps1 -Lane Target -TargetProfile EncounterTest -BuildOnly
```

Saturn-facing acceptance requires the exact `release-normal-release` image and
profile-specific semantic, resource, render, and final-scanout emulator
readback. A build or emulator launch alone is not acceptance. Use focused
diagnostic profiles for BENCH work; reserve normal release for checkpoint risk
boundaries and acceptance.

## Full lane

```powershell
.\verify.ps1 -Lane Full
```

Full runs the complete legacy and generator chain in `test.ps1` and may rewrite
tracked evidence. Run it only at acceptance, before merge, after foundational
tooling changes, or when a task card names it. Use a clean owned worktree or
isolated shadow copy and review every generated diff.

## Physical lane

Physical Saturn testing is separate and follows `docs/HARDWARE_TEST.md`. Only
that procedure may create `PHYSICAL_SATURN` evidence. Oracle, Full, Target,
normal-release emulator, and human-review results do not substitute for it.
