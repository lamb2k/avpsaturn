# Claude Code bootstrap

Read `AGENTS.md` in this directory now. It is the canonical instruction file
for every agent harness working in this repository; this file only adds the
Claude Code specifics and must stay minimal so the two never diverge. Then
read `docs/AGENT_HANDOFF.md` completely before acting; it is the
authoritative restart checkpoint. Then read `docs/PARITY_PLAN.md`, which is
the current direction and phase order: full-game functional parity by
translating game logic out of the ROM, with Round 1 as Capability Gate 1 and
stock MAME 0.289 as the primary observation instrument. Finally read
`docs/NEXT_AGENT_PROMPT.md` when present for the first executable body only.

Claude Code specifics:

- The `port-cps2-to-sega-saturn` skill is canonical at
  `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn` and exposed to
  Claude Code through a directory junction at
  `C:\Users\lambd\.claude\skills\port-cps2-to-sega-saturn`. If the skill is
  not listed in your session, read its `SKILL.md` and
  `references/workflow.md` directly from either path before working.
- Sessions sometimes start in the parent workspace
  `C:\Game Dev\BrooklynBangoutX`, which belongs to a different project and is
  not a Git repository. This repository is independent; run git from this
  directory or with `git -C`.
- Where `AGENTS.md` says `apply_patch`, use your Edit/Write tools; the
  requirement is the same precise, minimal edits that preserve unrelated
  user work.
- Build scripts locate their bundled Python, MAME, and Jo Engine
  dependencies; do not assume `python` or `mame` is on PATH.
