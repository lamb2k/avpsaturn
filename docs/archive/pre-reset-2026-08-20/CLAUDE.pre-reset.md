# Claude Code bootstrap

Read `AGENTS.md` in this directory now. It is the canonical instruction file
for every agent harness working in this repository; this file only adds the
Claude Code specifics and must stay minimal so the two never diverge. Then
read `docs/GOAL.md` for the full-game destination, followed by
`docs/AGENT_HANDOFF.md` completely for the authoritative restart checkpoint
and `docs/PARITY_PLAN.md` for the current direction and step order. Then read
`docs/ROUND1_EXECUTION_PLAN.md` for the active work-package graph, ownership,
and internal checks. The method is full-game functional parity by translating
game logic out of the ROM, with Round 1 as Capability Gate 1 and stock MAME
0.289 as the primary observation instrument. Finally read
`docs/NEXT_AGENT_PROMPT.md` when present for the first executable body only.

Claude Cloud is the implementation owner; Codex is the supervisor and plan
owner. Work from the exact base SHA named by Codex on a separate branch/worktree
and implement only the assigned scope. In `SUPERVISED_IMPLEMENTATION`, that is
`docs/NEXT_AGENT_PROMPT.md`. In `AUTONOMOUS_BOOK_IMPLEMENTATION`, it is the
ordered execution book named by the invocation; `docs/NEXT_AGENT_PROMPT.md`
remains context and is not rotated. Do not change the acceptance contract,
declare Capability Gate progress, or replace the canonical prompt.

At a candidate completion boundary, update `docs/AGENT_HANDOFF.md` with:

- an **Implementation report** naming base SHA, implementation commits, changed
  files, checks and exact results, generated/member hashes, remaining
  `ADAPTED`/`GAP` items, and every local/private check marked `UNRUN`;
- a **Suggested next body** with the evidence-based rationale, without editing
  the canonical plan or prompt.

End the response with a complete copy-paste `CODEX_REVIEW_INVOCATION`. Keep it
as a relay payload rather than repeating repository policy. It must name the
repository/worktree, branch, Codex base SHA, Claude commit SHA(s), objective,
implemented behavior, owned/overlapping files, checks passed/failed/`UNRUN`,
remaining `ADAPTED`/`GAP` items, and the exact local/private validation Codex
must perform. Ask Codex to return `ACCEPTED`, `CORRECTIONS REQUIRED`, or
`NOT REVIEWABLE` and to finish with the next `CLAUDE_INVOCATION`.

Codex reviews the commits and local private evidence. Address one bounded Codex
review list, then wait for Codex to accept, land, update plan status, and rotate
`docs/NEXT_AGENT_PROMPT.md`. If the current body is incomplete, report the exact
resume point and do not describe it as completed.

That stop is the default `MODE: SUPERVISED_IMPLEMENTATION`. If the invocation
instead states `MODE: AUTONOMOUS_BOOK_IMPLEMENTATION` (or the deprecated alias
`MODE: AUTONOMOUS_IMPLEMENTATION`), read
`docs/AUTONOMOUS_EXECUTION_BOOK.md` and execute every assigned chapter without
waiting for Codex between chapters. Each behavioral chapter must record a real
RED result before its production fix, reach GREEN, run its negative controls
and assigned regression tier, commit a candidate checkpoint, update the named
candidate run ledger, and continue immediately.

Book mode grants execution continuity, not planning or acceptance authority.
Do not rotate `docs/NEXT_AGENT_PROMPT.md`, edit canonical plan/package status,
declare completed work, or change Capability Gate progress. Return to Codex
once after the complete book, or earlier only for a hard stop defined by the
book. Ordinary failing tests are implementation work and are not a reason to
pause. Delegated `PACKAGE: RP<n>` workers never receive book-wide integration
authority.

The active program is the complete player-controlled presentation route from
cold boot through the Round 2 title. The immediate executable body is narrower:
finish RP4's representative NBG1/NBG0/VDP1 stage renderer. Follow
`docs/NEXT_AGENT_PROMPT.md`; do not repeat RP0-RP3 or promote the captured RP4
object schedule from validation fixture to production content.

Claude Code specifics:

- The `port-cps2-to-sega-saturn` skill is available to Claude Code at
  `C:\Users\lambd\.claude\skills\port-cps2-to-sega-saturn` through a
  directory junction to the canonical Codex copy. If the skill is not listed
  in your session, read its `SKILL.md` and `references/workflow.md` directly
  from the Claude path before working.
- Sessions sometimes start in the parent workspace
  `C:\Game Dev\BrooklynBangoutX`, which belongs to a different project and is
  not a Git repository. This repository is independent; run git from this
  directory or with `git -C`.
- Where `AGENTS.md` says `apply_patch`, use your Edit/Write tools; the
  requirement is the same precise, minimal edits that preserve unrelated
  user work.
- Build scripts locate their bundled Python, MAME, and Jo Engine
  dependencies; do not assume `python` or `mame` is on PATH.

## Reasoning and delegation policy

Optimize for total successful-work cost and speed.

### Default: Opus Medium

The primary agent owns implementation, testing, routine debugging and
execution of already-proven designs.

Do not delegate merely because work is technical.

### High technical consultant

Use `supervisor` for:
- reverse engineering
- unknown 68000 semantics
- writer/reader tracing
- control-flow reconstruction
- hypothesis/falsification work
- unexplained parity divergence
- bounded architectural questions

After the uncertainty is resolved, return implementation to the Medium primary
agent and record any plan-changing conclusion for Codex review.

### xhigh escalation

Use `deep-supervisor` only when High cannot confidently resolve the
specific uncertainty, including:
- competing hypotheses surviving falsification
- contradictory evidence
- unresolved indirect control flow
- ambiguous writer attribution
- unresolved PRNG/call ordering
- persistent differential-replay failures
- major architecture forks
- repeated bounded failures

Do not use xhigh simply because the task is difficult.

xhigh solves the unresolved question and returns execution to Medium.

### Existing project plan

Consult the existing project plan, handoff and current work contract before
creating a new plan.

Do not re-plan established work unless new evidence falsifies an existing
decision.

If implementation evidence falsifies the contract, stop the affected path and
record the contradiction in the handoff. Propose a correction for Codex review;
do not silently redesign the architecture.

### Review

Run the contract's implementation checks and optionally use a fresh High
technical review for an unresolved correctness question. Codex performs the
authoritative implementation and acceptance review.

Escalate to xhigh only when the High consultant identifies a
material unresolved correctness question.

Avoid repeated review loops.
