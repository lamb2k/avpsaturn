# Next agent prompt: RP1 - versioned shared contracts and ownership boundary

## Invocation

Work in:

`C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`

Use the `port-cps2-to-sega-saturn` skill. Read, in order:

1. `AGENTS.md`;
2. `docs/GOAL.md`;
3. `docs/AGENT_HANDOFF.md` completely;
4. `docs/PARITY_PLAN.md`;
5. `docs/ROUND1_EXECUTION_PLAN.md`;
6. `docs/ARCHITECTURE.md`;
7. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`;
8. this file.

Then run `git status --short --branch` and `git log --oneline -10`. Verify
every handoff claim against the worktree before relying on it. Preserve all
unrelated tracked and untracked work. Run Git only from this independent
repository.

RP0 passed at HEAD `e728c9b` on `codex/avp-master-plan` (`aa0d671` Round 1
title, `e728c9b` complete-interval shutter proof), implemented under the
user's autonomous interim-supervisor authorization; Codex review remains the
authoritative acceptance and may reopen RP0 with corrections. If HEAD
differs, reconcile the newer commits and update the handoff before
implementing. Do not reset, clean, stash, switch branches, or bulk-stage the
mixed worktree.

## Scope: RP1 only

Commit the versioned interface baseline from
`docs/ROUND1_EXECUTION_PLAN.md` RP1:

1. `AvspSceneDef v0`: the scene-definition envelope and schema version,
   supporting only the evidence-backed operations listed under RP3
   (hold/duration and input mask; layer-page selection; scroll update;
   palette-range update or fade; object add/update/remove; sparse map-cell
   patch; audio event; scene transition). Operations are additive within
   v0; incompatible changes require a version increment and a migration
   check.
2. Scene-ID namespace width and the provisional-ID policy (RP2 evidence
   finalizes the semantic list in RP6 - do not freeze it here).
3. Explicit unknown-scene behavior that fails diagnostically and never
   skips or coerces to a nearby scene.
4. The generated bundle header and member-manifest interface.
5. The `AvspScenePlayer` load/activate/step/draw/release interface.
6. The `AvspRouteController` explicit state-machine interface.
7. Presentation diagnostic and variance interfaces.

Express the contracts as headers plus host-compilable stubs with
deterministic host tests (envelope validation, version checks, unknown-scene
diagnostics, and negative controls for a truncated envelope, a wrong
version, and an unknown scene ID). Do not implement scene content, the
capture pipeline, or the stage renderer in this body.

## Constraints

- Native SH-2; no interpreters. ROM translation for systematic content.
- Preserve the one-based 1..255 palette contract, the 352x224 clip, the
  endpoint-aligned 384-to-352 fit, and the NBG1/NBG0/VDP1 architecture.
- Keep `JO_MAX_SPRITE=128` and JO_DEBUG. No new data reads after the CDDA
  late-read lock.
- Never commit ROMs, raw captures, generated copyrighted assets, audio,
  opcode dumps, logs, save states, disc images, or emulator state.
- Existing captures are regression oracles only.

## Required checks

1. Host tests for every new interface, including the negative controls.
2. Regenerate tracked manifests twice; byte-identical hashes.
3. `test.ps1` exit 0.
4. Clean focused Saturn build linking the new headers/stubs; `game.map`
   bounds unchanged expectations.
5. Terminate every emulator process afterwards.

Mark anything not run as `UNRUN`; a compile is not a check.

## Checkpoint and continuation discipline

Commit coherent explicit-path checkpoints only after their checks pass.
Update `docs/AGENT_HANDOFF.md` newest-first with exact commits, checks,
hashes, `UNRUN` items, and remaining `ADAPTED`/`GAP` items.

When invoked for autonomous execution and RP1 passes completely, rotate
this file to the next dependency-ready package (RP2 evidence probes and/or
RP5 residency experiment per `docs/ROUND1_EXECUTION_PLAN.md`), update the
execution-plan status with evidence, and continue. Stop only for a
falsified contract, unsafe or unauthorized action, cross-package
architectural conflict, missing private evidence, or an unrecoverable
required-check failure.

If operating under the Codex-supervisor/Claude-implementor workflow, stop
at the candidate completion boundary and emit the required
`CODEX_REVIEW_INVOCATION` instead. Do not self-accept or change Capability
Gate progress.
