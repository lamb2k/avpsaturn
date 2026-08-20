# Qwen bootstrap

Read `AGENTS.md` first; it is the canonical instruction file for every agent
harness in this repository. Then read `docs/GOAL.md`,
`docs/AGENT_HANDOFF.md` completely, `docs/PARITY_PLAN.md`,
`docs/ROUND1_EXECUTION_PLAN.md`, `docs/TEST_PLAN.md`,
`docs/HARDWARE_TEST.md`, and finally
`docs/NEXT_AGENT_PROMPT.md` for the single current executable assignment.

The current task is private native CPS2-to-Saturn ROM translation work. Use
the bundled tools and stock MAME 0.289, preserve untracked diagnostics, never
commit ROMs/raw captures/logs/disc images, and verify all handoff claims against
the worktree. The active program is the scene-complete player route from cold
boot through the Round 2 title. RP0-RP3 are complete; the immediate assignment
is RP4's representative two-plane renderer, including NBG0 ownership, PNT page
mapping, per-object priority, and strict separation of the captured validation
fixture from production content. It precedes S5 and does not authorize new
screenshot/RLE playback. `docs/NEXT_AGENT_PROMPT.md` contains the exact current
execution contract; RP0-RP3 and older writer-trace instructions are history.

Codex owns the plan/review and Claude Cloud owns implementation. Qwen may assist
only with an explicitly assigned bounded analysis or check; it must not rotate
the canonical prompt or declare Capability Gate progress. Candidate findings go
into the handoff for Codex review. Qwen does not emit or act on the
Codex/Claude relay payload unless the user explicitly assigns that role.
