# Qwen bootstrap

Read `AGENTS.md` first; it is the canonical instruction file for every agent
harness in this repository. Then read `docs/GOAL.md`,
`docs/AGENT_HANDOFF.md` completely, `docs/PARITY_PLAN.md`,
`docs/TEST_PLAN.md`, `docs/HARDWARE_TEST.md`, and finally
`docs/NEXT_AGENT_PROMPT.md` for the single current executable assignment.

The current task is private native CPS2-to-Saturn ROM translation work. Use
the bundled tools and stock MAME 0.289, preserve untracked diagnostics, never
commit ROMs/raw captures/logs/disc images, and verify all handoff claims against
the worktree. `docs/NEXT_AGENT_PROMPT.md` contains the Qwen-specific restart
details and exact retained writer-trace hashes.
