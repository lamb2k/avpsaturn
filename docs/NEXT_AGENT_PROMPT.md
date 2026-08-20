# Next agent prompt: RP4 - representative stage renderer

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

RP0 passed at `aa0d671`/`e728c9b`, RP1 at `dddd19a`, RP2 at `82bb47e`,
and RP3 at `a28f5df` on `codex/avp-master-plan`, implemented under the
user's autonomous interim-supervisor authorization; Codex review remains
the authoritative acceptance and may reopen any of them with corrections.
If HEAD differs, reconcile the newer commits and update the handoff
before implementing.

## Scope: RP4 only

Prove the representative two-plane stage renderer on one street interval,
per `docs/ROUND1_EXECUTION_PLAN.md` RP4. Select the interval from the RP2
census (`data/round1_route_census.json`, street group `0x801d`,
source frames 2074-5542) so it contains independent scroll2/scroll3
motion, a moving actor, a foreground insertion, a priority change, and
source-enabled row scroll (census `rowscroll_unique_hashes` > 1 marks
candidates). Prove, with measured evidence:

1. scroll3 -> NBG1 and scroll2 -> NBG0;
2. objects -> VDP1 and only source-proven foreground -> NBG2 or bounded
   VDP1;
3. the common plane-level endpoint-aligned 384-to-352 transform with
   independent per-plane scroll;
4. a normalized source row table, using VDP2 line scroll only if the
   source rows are nonconstant;
5. priority at deliberate overlaps;
6. exact VRAM/CRAM/register state and bounded command cost;
7. zoom, row, palette, and priority negative controls.

## Constraints

- Native SH-2 end goal; no CPS2 or 68000 interpreter.
- Do not modify the RP1 header contracts except by explicit versioned
  extension recorded in the handoff.
- Never commit ROMs, raw captures, generated copyrighted assets, audio,
  opcode dumps, logs, save states, disc images, or emulator state.
- The user-requested whole-game capture may still be recording under
  `.deps/mame/full_game`; do not start a second MAME instance while it
  runs, and stop every MAME process after it completes.

## Required checks

1. Offline verifiers prove the renderer's plane assignment, transform,
   row table, and priority against the private capture, each with its
   negative controls.
2. Full SH-2 build links (`__bend` recorded; only 624 bytes of high work
   RAM remained after RP3 - treat the margin as a hard constraint).
3. `test.ps1` exit 0.
4. Live Saturn-emulator validation of the rendered interval, then no
   emulator processes left running.

## Checkpoint and continuation discipline

Commit coherent explicit-path checkpoints only after their checks pass.
Update `docs/AGENT_HANDOFF.md` newest-first with exact commits, checks,
hashes, `UNRUN` items, and remaining `ADAPTED`/`GAP` items.

When invoked for autonomous execution and RP4 passes, rotate this file to
the next dependency-ready package (RP5 residency experiment or RP6
semantic scene IDs per the execution plan), update the plan status with
evidence, and continue. Stop only for a falsified contract, unsafe or
unauthorized action, cross-package architectural conflict, missing private
evidence, or an unrecoverable required-check failure.

If operating under the Codex-supervisor/Claude-implementor workflow, stop
at the candidate completion boundary and emit the required
`CODEX_REVIEW_INVOCATION` instead. Do not self-accept or change Capability
Gate progress.
