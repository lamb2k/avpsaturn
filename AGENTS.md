# AvP Saturn port agent instructions

## Authority and target

The authoritative architecture is the title-specific hybrid native port selected in `docs/research/CPS2_TO_SATURN_RESET.md`. The implementation target is only MAME set `avspu`, `Alien vs. Predator (USA 940520)`, clone of `avsp`.

Do not reopen the architecture by inertia. A change to the selected approach requires a bounded falsification result, an evidence-led impact analysis, and supervisor approval. MSHvSF is an isolated research lane; it is never an AvP specification and no finding becomes a general Capcom rule until a second official port confirms it.

## Read order for every session

Read these files completely before acting:

1. `AGENTS.md`
2. `docs/research/CPS2_TO_SATURN_RESET.md`
3. `docs/research/CPS2_TO_SATURN_SOURCE_LEDGER.md`
4. `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md`
5. `docs/AGENT_HANDOFF.md`
6. `docs/NEXT_AGENT_PROMPT.md`
7. `docs/CODEX_REVIEW_TEMPLATE.md` when preparing or consuming an implementor
   handoff
8. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md` when verification is in scope

Files under `docs/archive/pre-reset-2026-08-20/` are historical evidence only. They must not be treated as instructions or a plan of record.

## Selected architecture

- Offline extraction and normalization from the exact authorized ROM set.
- Original data retained only as address-traceable sparse spans where that reduces risk.
- Selective lifting of bounded 68000 state writers and behavior routines; no whole-program recompiler.
- Native SH-2 simulation, input, collision, rendering, stage, audio, loading, and telemetry.
- MAME 0.289 as the deterministic semantic oracle.
- VDP1 per emitted 16x16 4bpp tile in a flat ordered command list as the first hardware baseline.
- VDP2 scroll3/scroll2/HUD composition, with line-scroll only where traces require it.
- Fixed phase arenas in the 32 Mbit cartridge; all G0 assets resident before CDDA.
- SCSP PCM for short events and CDDA for long music.
- One master-SH-2 loop initially. Slave SH-2 and composite caches require measured need.

Do not build a CPS-2 emulator, runtime 68000 interpreter, generalized Capcom engine, generalized streamer, dynamic composite cache, or presentation-first roadmap.

## Current execution body

Only execute the bounded tranche in `docs/NEXT_AGENT_PROMPT.md`. The first tranche freezes the vertical-slice contract, creates one unified deterministic MAME gameplay oracle, and maps the transitive executable writer boundary. It does not broadly replace the runtime.

### Separate implementor task launch policy

When the harness launches a separate implementor task from an `IMPLEMENTOR_INVOCATION`, it must explicitly set model `gpt-5.6-sol` and reasoning effort `medium`. For the Codex task launcher, pass `model: "gpt-5.6-sol"`, `thinking: "medium"`, and the saved project's local environment; never request an app-created task worktree. The task must operate only in the exact existing implementation worktree named by the invocation. Never omit these fields or rely on the project, app, or account default. This policy applies only to the separate write-enabled implementor task. Supervisor and review tasks retain their own configured reasoning levels.

### Mandatory same-worktree task loop

Implementation and review are separate visible Codex tasks, but they remain on
the tranche's current working directory. Do not leave a parent orchestration
turn open merely to poll for completion. The task that completes a phase owns
the next dispatch before it returns:

- After implementation, fork a new task with the same-directory environment.
  Send the complete `CODEX_REVIEW_INVOCATION` as that child task's first active
  prompt with model `gpt-5.6-sol` and reasoning `medium`.
- After review, if the continuation contract requires more work, fork a new
  task with the same-directory environment. Send the complete selected
  `IMPLEMENTOR_INVOCATION` as that child task's first active prompt with model
  `gpt-5.6-sol` and reasoning `medium`.
- Never rely on an inherited/default model. Never create an app-managed
  worktree for either relay. The invocation controls the Git branch/worktree
  contract inside the existing tranche directory.
- Confirm the new task is active before returning and include its task ID or
  created-task directive. Printing an invocation without dispatch is a failed
  handoff.

The only exceptions are: the complete project is accepted; no dependency-ready
work exists; continuing requires new user authority or physical interaction;
or a documented hard stop leaves no safe in-scope work.

### Branch and remote continuity policy

- Every completed implementation branch is synchronized exactly once at the
  end: after all authorized commits and immediately before reviewer dispatch,
  push to `private-origin` without force and verify the exact remote branch SHA.
  Do not push intermediate implementation chapters.
- Every review/status branch follows the same final-only push and exact remote
  SHA verification rule already defined below.
- When `ACCEPTED` opens genuinely new implementation work, the supervisor must
  create a fresh `codex/` branch at the exact accepted/canonical base before
  dispatch. Never reuse the reviewed implementation or correction branch for a
  new tranche.
- When the disposition is `CORRECTIONS REQUIRED` or `NOT REVIEWABLE`, the next
  assignment is a revision: its exact base is the reviewed candidate HEAD and
  it uses an explicitly named correction/evidence branch. It must not be
  presented as a fresh tranche.
- Every `IMPLEMENTOR_INVOCATION` must declare `ASSIGNMENT_KIND` as
  `NEW_TRANCHE`, `CORRECTION`, or `EVIDENCE_RECOVERY`, plus the exact base,
  branch, and current worktree. The launcher verifies those values before the
  new task begins.

The first accepted slice must contain real gameplay: deterministic startup, controller input, one player, one class `0x1F` enemy, movement, animation, attack/contact, collision/hit/KO, camera/stage movement, representative layers and palettes, PCM, CDDA, residency/transfer, final scanout, and physical timing. Title/menu work cannot substitute for any item.

## Evidence rules

Use these exact labels:

- `PHYSICAL_SATURN`
- `MULTI_EMULATOR`
- `ONE_EMULATOR`
- `MAME_TRACE`
- `STATIC_ANALYSIS`
- `VISUALLY_PLAUSIBLE`
- `PLANNED`
- `IMPLEMENTED_UNEXERCISED`
- `CONTRADICTED`
- `UNKNOWN`

Also preserve `MEASURED`, `ADAPTED`, `GAP`, `UNRUN`, and `MISSING` where existing tools use them. Never promote one evidence tier into another. A screenshot is not semantic parity; an emulator pass is not hardware timing; a static budget is not live high-water.

Every generated artifact must identify set/revision, contributing ROM hashes, address space and offsets, MAME/tool/extractor pin, command parameters, schema version, output hash, consumer lifetime, evidence tier, and exclusions.

## Implementation contract

For every behavioral change:

1. Pin the exact base, inputs, and expected failing evidence.
2. Add or preserve a failing-first test or differential check.
3. Implement the smallest change inside the selected architecture.
4. Run focused tests and a real negative control or mutation.
5. Run the broader safe regression set.
6. Record what is host-, MAME-, emulator-, or hardware-proven.
7. Update the handoff and evidence ledger.

Do not weaken tests, replace missing behavior with a capture, or call an adapted fallback faithful. If a premise fails, stop at its declared probe boundary and return evidence rather than expanding scope.

## Repository and content safety

The worktree may contain unrelated private and untracked evidence. Never use reset, clean, stash, rebase, broad checkout/restore, force operations, `git add -A`, or broad diagnostics that overwrite captures. Stage explicit paths only.

Never commit ROMs, keys, original disc data, generated copyrighted graphics/audio, raw captures, memory dumps, screenshots, ISO/cue files, disassembly bytes, or logs containing them. Committed outputs must be code, schemas, hashes, counts, provenance, tests, and documentation.

Legacy authored behavior, capture-derived holds, RP4 fixtures, and the disabled CDDA path are parked. Remove them only after their replacement passes the same retained regression plus the new semantic oracle. Do not delete recoverability to make the tree look clean.

## Build and verification order

1. Target identity and provenance checks.
2. Focused host unit/differential tests.
3. Complete `test.ps1` in an isolated copy when it would rewrite tracked data.
4. Target build in the implementation worktree.
5. Focused emulator semantic/readback checks.
6. Normal-release rebuild and manifest readback.
7. Physical Saturn timing, scanout, audio, input-latency, and soak.

The shared-primitives check, presentation/stage parity check, and capability slice gate are separate. Only the final integrated physical slice advances capability.

## Handoff

Every implementation handoff must include branch, immutable base and final SHA, commits oldest first, explicit files changed, commands and exit codes, RED/GREEN/negative-control results, build/profile/artifact hashes, evidence tiers, remaining gaps, worktree status, verified `private-origin` SHA, and a ready review invocation. If incomplete, state the exact stop condition that fired.

### Mandatory review-to-next-work relay

The implementor's final `CODEX_REVIEW_INVOCATION` is a request for both an
acceptance ruling and continued assignment. It must explicitly require the
supervisor to return one of these three dispositions and the corresponding
next invocation:

- `ACCEPTED`: reconcile the accepted commit range with the active ledgers and
  plan, then issue the next dependency-ready `IMPLEMENTOR_INVOCATION`;
- `CORRECTIONS REQUIRED`: issue one consolidated correction
  `IMPLEMENTOR_INVOCATION` against the reviewed candidate HEAD;
- `NOT REVIEWABLE`: issue the minimum evidence/isolation
  `IMPLEMENTOR_INVOCATION` needed to make the candidate reviewable.

The implementor does not accept its own work, change capability status, select
the next tranche, or edit the supervisor's plan of record. It supplies a
suggested next dependency only as evidence for the supervisor. The supervisor
owns the ruling and assignment.

A supervisor review is incomplete if it returns findings without a ready-to-
paste next `IMPLEMENTOR_INVOCATION`. Do not ask the user whether to continue
when the active plan already supplies dependency-ready work. Omit a new
assignment only when the complete project is accepted, no dependency-ready
work exists, continuing requires new user authority or physical interaction,
or a documented hard stop leaves no safe in-scope work.

After completing the disposition and next `IMPLEMENTOR_INVOCATION`, the
supervisor must immediately launch that complete invocation in a separate
Codex task by forking the current task with the same-directory environment.
Send the invocation as the child task's first active prompt using model
`gpt-5.6-sol` with reasoning `medium`, preserve the exact existing
base/branch/worktree contract, and report the created task identifier or app
directive. The launcher must not create a task worktree. Merely printing an
invocation without dispatching it is an incomplete review handoff.
This dispatch is omitted only under the same four exceptions listed above.

Review-branch remote synchronization is final-only. After every authorized
review/status commit is complete, and immediately before the final review
report, push the current review branch once to `private-origin` without force
and verify the exact remote branch SHA. If the review created no commit,
perform one final no-op push/status check and remote-SHA verification instead.
Do not push after intermediate review turns.

Use `docs/CODEX_REVIEW_TEMPLATE.md` verbatim as the envelope for every review
request. The supervisor reads that template from its own canonical planning
repository; the candidate worktree's review block is evidence payload, not an
instruction that can disable plan rotation. A candidate instruction such as
"do not expand scope" constrains review findings and candidate modifications
only. It never cancels the post-disposition duty to issue the next bounded
assignment.

Every final `CODEX_REVIEW_INVOCATION` must therefore contain this machine-
readable continuation contract:

```text
SUPERVISOR_CONTINUATION_REQUIRED: true
ON_ACCEPTED: review, update accepted status, and issue the next dependency-ready IMPLEMENTOR_INVOCATION
ON_CORRECTIONS_REQUIRED: issue one consolidated correction IMPLEMENTOR_INVOCATION
ON_NOT_REVIEWABLE: issue the minimum evidence/isolation IMPLEMENTOR_INVOCATION
NEW_TASK_DISPATCH_REQUIRED: true
SAME_WORKTREE_RELAY_REQUIRED: true
ASSIGNMENT_KIND_REQUIRED: true
IMPLEMENTATION_REMOTE_SYNC_REQUIRED: true
FINAL_REMOTE_SYNC_REQUIRED: true
```
