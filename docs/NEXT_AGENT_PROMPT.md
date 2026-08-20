# Next agent prompt: RP2 - full-route cadence-1 capture and grouping

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

RP0 passed at `aa0d671`/`e728c9b` and RP1 at `dddd19a` on
`codex/avp-master-plan`, implemented under the user's autonomous
interim-supervisor authorization; Codex review remains the authoritative
acceptance and may reopen either with corrections. If HEAD differs,
reconcile the newer commits and update the handoff before implementing.

## Scope: RP2 only

Capture the complete no-skip source presentation route at cadence 1 and
produce the semantic census, per `docs/ROUND1_EXECUTION_PLAN.md` RP2:

1. Extend the stock-MAME 0.289 capture route from cold boot through the
   held Round 2 title with no skipped frames: source state, input,
   CPS-A/B registers, relevant work RAM, gfxram, object RAM, palette RAM,
   QSound state, and screenshots. Raw captures stay ignored and private.
2. Generate a raw machine manifest of hashes and per-frame write deltas.
3. Group consecutive frames automatically by state, maps, palettes,
   objects, scroll/priority, input acceptance, and audio changes.
4. Assign provisional scene IDs in the AvspSceneDef v0 namespace
   (bit 15 set). Human review focuses on transitions, unexplained
   full-frame changes, object insertion/removal, priority/palette
   changes, input windows, audio, and nonconstant row-scroll intervals.
5. Tracked output carries semantics, addresses, counts, ranges, and
   hashes only - never ROM bytes, framebuffer payloads, or audio.

Zero unclassified intervals is an RP12 requirement, not an RP2 gate; RP2
passes when the census covers the complete route and every group either
has a provisional ID or is explicitly listed as unclassified.

## Constraints

- Native SH-2 end goal; captures are evidence and regression oracles only.
- Never commit ROMs, raw captures, generated copyrighted assets, audio,
  opcode dumps, logs, save states, disc images, or emulator state.
- Do not modify shared runtime files in this body; RP2 is evidence-only
  and may run alongside RP5 in a separate worktree if desired.
- Stop every MAME process after capture.

## Required checks

1. Deterministic re-run of the capture route reproduces identical tracked
   hashes (or documents the exact nondeterminism boundary).
2. The census tool regenerated twice produces byte-identical tracked
   manifests.
3. Negative controls: a one-frame route shift and a perturbed group
   boundary must each change the census in the expected, detected way.
4. `test.ps1` exit 0.
5. Terminate every MAME process afterwards.

## Checkpoint and continuation discipline

Commit coherent explicit-path checkpoints only after their checks pass.
Update `docs/AGENT_HANDOFF.md` newest-first with exact commits, checks,
hashes, `UNRUN` items, and remaining `ADAPTED`/`GAP` items.

When invoked for autonomous execution and RP2 passes, rotate this file to
the next dependency-ready package (RP3 scene runtime, RP4 representative
renderer, or RP5 residency experiment per the execution plan), update the
plan status with evidence, and continue. Stop only for a falsified
contract, unsafe or unauthorized action, cross-package architectural
conflict, missing private evidence, or an unrecoverable required-check
failure.

If operating under the Codex-supervisor/Claude-implementor workflow, stop
at the candidate completion boundary and emit the required
`CODEX_REVIEW_INVOCATION` instead. Do not self-accept or change Capability
Gate progress.
