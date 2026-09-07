# Verification model

Tests retire one claim at one evidence tier. Machine validation, fidelity
evidence, emulator self-review, user approval, and physical proof remain
independent.

## R7C cadence (current owner delivery focus)

| Change boundary | Required work |
| --- | --- |
| Docs/state/policy only | Fast -WorkflowOnly, policy negatives, diff check |
| Small native/SPEC edit | DEV below plus relevant fixture validation |
| Complete source program | Whole-program and complete-scene host comparison, attributable mutations; Oracle and Target as owned |
| Scheduler, memory, renderer, audio or nondeterminism | Prior checks plus paired cold Emulator and focused continuous visual/audio evidence |
| Complete scene | Full census, changed-input route, zero unexplained gameplay/ownership gaps, actual continuous scene inspection |
| Full R7C candidate | QA-13 full completion/repeat/perturbed/failure routes, normal interactive build, then USER-10 |

A blocked or exhausted lane stays required and incomplete. No deadline, docs
change or source-only PASS reopens it. Do not launch exhausted gates without
the existing owner ruling. Small edits do not run full capture ceremony.
No per-actor/per-program human review; QA-13 then USER-10 is the current gate.
Old BENCH instructions below apply only to actual salvage cards.

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

For documentation/state-only changes:

```powershell
.\verify.ps1 -Lane Fast -WorkflowOnly
```

This explicit scope runs workflow-policy, task-card/state and migration-map
checks only. The report records workflow-only, not a complete Fast acceptance.
Default Fast retains every existing focused deterministic check; Oracle retains
its full inventory. Nothing is deleted from acceptance to accelerate docs.
Use -Test to add a directly relevant host check without the entire runtime lane.

For the live-gameplay pivot, Fast also verifies the serial read-only Oracle
exception, the player-action/AI/encounter dependency chain, the frontend gate,
and negative transitions that would relabel the scripted capability slice as
playable Round 1 or physical proof.

## ARCH-01 control-plane lane

`ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN` runs control-plane checks only:

- task-card, dependency, active-state, and head-role consistency;
- JSON-compatible YAML/schema validation for the three coverage ledgers;
- four-character and three-player target consistency;
- ADR presence and required-section validation;
- staged architecture-rule declarations and activation conditions;
- workflow policy tests, Fast workflow checks, and `git diff --check`.

ARCH-01 does not run Oracle capture, Target, emulator, Full, or physical Saturn
lanes. It does not compile or modify runtime code. The architecture boundary
checks are staged: rules for `src/port_v2/core/**`, production adapters, and
phase manifests activate only when those paths/cards are introduced, so
accepted legacy code is not failed retroactively.

## Oracle lane

```powershell
.\verify.ps1 -Lane Oracle
```

Oracle verifies MAME provenance, deterministic oracle artifacts,
translation/writer boundaries, validators, and mutation controls. Use it when
the active task changes evidence, lifted behavior, source identity, or a trust
boundary. Missing pinned private inputs makes the lane `INCOMPLETE`, never an
unqualified pass.

The future full-game Oracle cards require two identical source runs and one
non-vacuous perturbation control. ORACLE-01 covers cold boot through credits,
ORACLE-02 covers all four character action matrices, and ORACLE-03 covers ending
and credits deltas. Unknown or uncaptured behavior remains `UNKNOWN`; partial
route evidence is never reported as complete.

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

## Interactive authority and mutation quality

The normal callback must not select gameplay updates from captured source-frame
cadence/phase arrays. The same source clock/input semantics must drive real
controller and differential adapters. Absolute source-frame labels are observation
coordinates only; test shifted labels and source-supported changed-input routes.
Pool ordering, hitstop, timers and release remain source-bound.

A literal retained-authority0 in the scene generator is not a measured gate.
Measure the production call graph and emitted native ownership, including
capture-schedule reachability, before claiming zero hidden authority.
Keep complete1972..5566 source population and native boot2040..5566 alignment;
early exits at5523/5551 cannot accept a complete Coffee Shop scene.

Compile/link must pass strict C90 before a behavior mutant executes. Require the
intended assertion/differential/exit, bounded process timeouts, and report kills,
survivors, invalid builds, timeouts, environment errors and compile-negative tests
separately. An unrelated error is not a kill. Existing causal tests remain binding.
SoundCore0 technical visual capture cannot establish audible PCM/CDDA parity.
