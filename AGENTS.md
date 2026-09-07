# AvP Saturn port agent policy

## Authority and immediate scope

Codex Goal Mode owns interactive implementation. `docs/PARITY_PLAN.md` is the only roadmap;
`project_state.yaml` is state authority; the existing active task card owns execution.
Exactly one implementation task owns writes at a time. Direct Codex
implementation is the default for ordinary work; nested Codex executors are
not used for ordinary implementation. Claude is an optional bounded provider
only when the active card explicitly permits it. Preserve owner-selected
`gpt-5.6-sol` / `high`; do not change model/provider or add a controller.

Current delivery is R7C: one-player Predator Warrior, direct Round 1 entry,
complete stage and boss, clear, and specified stable Round 2 handoff.
Frontend, other characters, multiplayer and Round 2 gameplay are out of scope.
A complete source census or accepted SPEC is not an implemented playable level.

Read this file, the handoff, current state fields and the complete active card.
State history and accepted cards are provenance, not new instructions: read
only the history needed by the selected body. Use TEST_PLAN for checks,
EMULATOR_MCP_CAPTURE for capture, and HARDWARE_TEST before physical work.
The dated CPS2_TO_SATURN_RESET audit is architecture context, not a command to
restart completed research. Read its relevant section for boundary changes.
Do not reread thousands of historical checkpoint lines each iteration.

## Work that advances delivery

Continue REIMPLEMENT-13 in complete source-program bodies, then whole scenes.
Do not restart salvage benches or request human review after every actor/body.
Reuse accepted rendering, input, collision/HIT/KO, camera, HUD, PCM/CDDA,
loading/residency and diagnostics. The earlier salvage loop remains history.

1. Select the highest-fan-out dependency-safe gameplay body on the active card.
2. Implement from executable SPEC and accepted interfaces. If a required field
   is missing, amend the existing fixture from accepted Oracle evidence.
   New capture is a smallest bounded follow-up only when that evidence lacks it.
3. Run strict host compile, focused differential, deterministic repeat and
   attributable behavior mutations. Check a whole program, not one frame/slot.
4. Run broader lanes at TEST_PLAN risk boundaries. Inspect a real interactive
   image before describing it as playable. Keep every failed/unrun gate visible.
5. Coherently commit completed work, push it to `private-origin`, verify that
   the remote branch SHA equals local, and continue the existing dependency chain.

Within owned paths, automatically correct ordinary compile, test and integration
defects. Do not request permission for routine edits, tests or checkpoints.
An exhausted named gate stays blocked until the owner explicitly reopens it;
a deadline or a fresh commit does not renew its attempt budget. Preserve work
and continue another dependency-safe body when possible. Never count a failed
build/launcher/timeout as a behavioral mutation kill.

## Gameplay and evidence boundary

Use MAME set `avspu`, USA 940520, and pinned MAME 0.289. The architecture is
offline ROM extraction, source-addressed tables/routines, portable native C
on SH-2, fixed pools, VDP1 actors, VDP2 backgrounds and SCSP/PCM/CDDA adapters.
Do not build a CPS-2 emulator, general lifter, whole-program recompiler or ECS.

The normal interactive image must not use a captured frame ledger to select
gameplay invocations, movement, damage, lifetime, release or route outcomes.
Legitimate source timers, hitstop, scheduler guards and animation clocks are
allowed; recovered source rules, not observation rows, must own their updates.
Keep replay/capture alignment in the diagnostic/oracle adapter. Compare
source-slot/field/state semantics across platforms, not identical CPU addresses.

Require current input/state, changed-input causal behavior, full-scene coverage,
raw alongside narrowly normalized differences, and no unsupported dispatch.
A hardcoded zero is not evidence of absent retained authority.
A passing emulator check is not human approval or physical proof. No deadline
changes those gates. Do not promote a candidate from a fixture hash or commit.

## Review, physical and stop boundaries

USER-09 remains CHANGES_REQUESTED. USER-10 follows QA-13 and cannot be
self-approved. SALVAGE-08 remains gated on explicit accepted USER-10.
No per-body subjective review is required; approved behavior remains locked.
A user-approved component is locked; report a source contradiction and request
renewed review before intentionally changing its subjective behavior.

At USER-10 provide the exact interactive build, controls, continuous source and
Saturn clips, adaptations, comparisons and physical status under ignored
`build/feedback/<task-id>/`. Ask exactly:
"What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"
Stop for the answer. Never infer approval from silence.

Physical Saturn remains UNRUN; HW-01 remains READY_FOR_PHYSICAL. Its parked
status does not prohibit independent software R7C work. The historic
`independent_read_only_cards` exception remains source-only, serial and unable
to advance physical status. No emulator result advances physical acceptance.

Stop for unsafe worktree ownership, required credentials/legal permission,
destructive/device work, physical interaction, an unresolved material architecture
choice, or an exhausted/source blocker with no dependency-safe work remaining.
Reports state the blocker and exact unblock condition, not a request to redo a plan.

## Continuity, memory and repository safety

Use the existing branch/worktree. Preserve newer work and all ignored evidence.
Never reset, clean, stash, rebase, broadly restore, force-push or use `git add -A`.
Never modify or stage `data/avsp_anim_records.json` or `history.txt`.
Stage explicit owned paths only. No ROMs, keys, ISOs, raw traces, dumps, PNGs,
savestates or generated copyrighted media enter Git. No MSHvSF lane merge.

Preserve the existing per-region memory plan/asserts and CPU-mediated
cartridge-to-VDP1 upload rule. No SCU DMA A-bus endpoint, arena enlargement or
mid-combat data read. SPEC headroom is not runtime/texture/work-RAM headroom.
Physical DMA legality and timing margins need physical evidence.

## Handoff and reporting

Keep AGENT_HANDOFF under 50 lines and the active card under 220 lines.
Keep historical detail in Git and existing evidence, not appended active prose.
Report material results: playable extent, objective defects, named gap counts,
checks, build/commit/remote identities, blocked tiers and exact next body.
Never substitute mutation totals or row-match percentages for playability.

At a review/owner boundary include CODEX_REVIEW_INVOCATION with task, exact
local/remote/production/candidate identities, tested artifact, PASS/FAIL/UNRUN
lanes, evidence paths, disposition and one executable next assignment.
Do not emit a bare marker. Normal checkpoint commits are not human boundaries.
