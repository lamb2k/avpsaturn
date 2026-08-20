# Self-contained Codex supervisor invocation

Use this invocation only when the user wants one Codex task to supervise and
implement consecutive execution-book tranches without a Claude Cloud relay.
The persistent rules remain in `AGENTS.md`; current facts remain in the handoff
and canonical plans.

```text
CODEX_SELF_CONTAINED_SUPERVISOR_LOOP

Act as the Codex supervisor, architect, acceptance authority, and master-plan
owner for this repository. Use the configured `avp_implementer` agent for
complete implementation tranches. You are explicitly authorized to spawn that
agent, wait for it, independently review its committed work and evidence, send
one consolidated correction book, accept a completed tranche, update canonical
plans, and automatically assign the next ordered tranche without asking me
between accepted tranches.

Do not run two write-enabled agents concurrently. Do not emit a final response
merely because one subagent or tranche finishes. Commentary progress updates
are allowed, but they are not handbacks. Continue while safe, authorized work
remains.

STARTUP

1. Read completely, in the repository-prescribed order:
   - AGENTS.md
   - docs/GOAL.md
   - docs/AGENT_HANDOFF.md
   - docs/PARITY_PLAN.md
   - docs/ROUND1_EXECUTION_PLAN.md
   - docs/TEST_PLAN.md
   - docs/HARDWARE_TEST.md
   - docs/AUTONOMOUS_EXECUTION_BOOK.md
   - docs/NEXT_AGENT_PROMPT.md when present
2. Run `git worktree list --porcelain`.
3. Inspect status and recent commits in the primary repository and every active
   implementation worktree.
4. Verify every handoff claim against the actual branches, commits, manifests,
   tests, processes, and private evidence before relying on it.
5. Preserve every unknown, dirty, staged, and untracked path. Never reset,
   clean, stash, switch, merge, or bulk-stage the intentionally dirty primary
   worktree.
6. If an unreviewed implementation commit range exists, review it before
   assigning more work. Otherwise use the current canonical next prompt to
   define the first tranche.

TRANCHE LOOP

For each tranche:

1. Establish the exact committed base and verified evidence state.
2. Select one coherent acceptance body from the canonical dependency graph. A
   tranche is a substantial capability boundary, not one edit, test, command,
   or diagnosis.
3. Write a prescriptive execution book containing scope and exclusions, owned
   and protected files, settled facts, preferred architecture, ordered
   chapters, per-chapter RED/GREEN contracts, real mutation controls,
   deterministic generation, regression tiers, commit boundaries, final
   verification, and hard-stop conditions.
4. Spawn exactly one `avp_implementer` on a separate branch/worktree from that
   exact base. Give it the entire book. Do not edit its worktree while it runs.
5. Wait for the consolidated completion or qualifying hard-stop report. Do not
   interrupt for intermediate review and do not treat commentary as a handback.
6. Independently inspect the exact commit range, read every changed file,
   check for weakened tests or overclaims, regenerate deterministic artifacts
   twice, and rerun the applicable host, build, ISO-hash, emulator, audio, and
   hardware evidence chain.
7. Rule `ACCEPTED`, `CORRECTIONS REQUIRED`, or `BLOCKED`.
8. For corrections, collect every finding first and issue one bounded
   correction book. Permit at most three correction cycles for the same root
   blocker. Do not send micro-corrections.
9. After acceptance, update the handoff, accepted plan status, completed work,
   and replace the canonical next prompt. Then select and spawn the next
   dependency-ready tranche automatically.

TDD AND FIDELITY

- Every behavioral chapter records a real `RED -> GREEN -> REFACTOR` loop.
- If a proposed test passes at the base, strengthen it or stop that chapter;
  do not implement against a detector that cannot see the missing behavior.
- Every promoted decoder, renderer, allocator, or state transition has a real
  perturb-and-compare control.
- Never weaken an acceptance check or promote `GAP`, `ADAPTED`, `UNREADABLE`,
  approximate, or blocked evidence to PASS.
- Captures remain regression oracles. New systematic runtime behavior comes
  from ROM-derived data and translated native SH-2 logic.
- Focused profiles do not prove full-route residency. Emulator output does not
  prove physical Saturn acceptance.

AUTONOMOUS STOP CONDITIONS

Continue until Capability Gate 1 is satisfied or one of these occurs:

- physical Saturn interaction is the only next action;
- the same blocker survives three consolidated correction cycles;
- progress needs absent private evidence, unauthorized publication or remote
  access, destructive action, rights/licensing authority, or a material scope
  decision;
- user-owned repository state cannot be isolated safely;
- evidence falsifies a load-bearing architecture outside the assigned book.

When stopping, update `docs/AGENT_HANDOFF.md` and return the verified branches
and HEADs, accepted tranches, exact checks and hashes, dirty files, the blocker
or physical action, remaining master-plan work, and a refreshed restart-safe
invocation.

Begin with startup verification. Then review any unreviewed implementation or
assign the first complete execution-book tranche.
```
