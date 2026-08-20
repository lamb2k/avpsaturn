# Next agent prompt: RP3 - minimal scene runtime and route controller

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

RP0 passed at `aa0d671`/`e728c9b`, RP1 at `dddd19a`, and RP2 at `82bb47e`
on `codex/avp-master-plan`, implemented under the user's autonomous
interim-supervisor authorization; Codex review remains the authoritative
acceptance and may reopen any of them with corrections. If HEAD differs,
reconcile the newer commits and update the handoff before implementing.

## Scope: RP3 only

Implement the minimal scene runtime against the committed RP1 contracts
(`avsp_scene.h`, `avsp_scene_player.h`, `avsp_route.c`), per
`docs/ROUND1_EXECUTION_PLAN.md` RP3:

1. An `AvspScenePlayer` implementation executing exactly the v0
   operations: hold/duration with input mask, layer-page selection,
   scroll update, palette-range update or fade, object
   add/update/remove, sparse map-cell patch, audio event, and scene
   transition. No scripting language, no dynamic scene allocator, no
   universal asset cache.
2. Host-compilable C90 core so the same player logic runs in WSL host
   tests and on the SH-2; Jo/SGL side effects behind the existing
   platform seams (as `capability_model.c` does).
3. Synthetic host fixtures: hand-built envelopes covering every opcode,
   an end-to-end two-scene route through `AvspRouteController`, and
   diagnostic failures for unknown scene, bad version, and truncated
   payloads (never skip).
4. Diagnostics counted through `AvspSceneDiagnostics`; unknown scenes and
   malformed envelopes are hard, reported errors.
5. Keep `data/round1_route_census.json` group boundaries as the evidence
   source when choosing fixture shapes; do not finalize semantic scene
   IDs (that is RP6).

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

1. WSL host scene-runtime tests pass, including one negative control per
   diagnostic path.
2. Full SH-2 build links with the player compiled in (`__bend` recorded).
3. `test.ps1` exit 0.
4. No emulator processes left running.

## Checkpoint and continuation discipline

Commit coherent explicit-path checkpoints only after their checks pass.
Update `docs/AGENT_HANDOFF.md` newest-first with exact commits, checks,
hashes, `UNRUN` items, and remaining `ADAPTED`/`GAP` items.

When invoked for autonomous execution and RP3 passes, rotate this file to
the next dependency-ready package (RP4 representative renderer or RP5
residency experiment per the execution plan), update the plan status with
evidence, and continue. Stop only for a falsified contract, unsafe or
unauthorized action, cross-package architectural conflict, missing private
evidence, or an unrecoverable required-check failure.

If operating under the Codex-supervisor/Claude-implementor workflow, stop
at the candidate completion boundary and emit the required
`CODEX_REVIEW_INVOCATION` instead. Do not self-accept or change Capability
Gate progress.
