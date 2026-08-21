# Implementor invocation: AvP hybrid tranche 1

Generated: 2026-08-20, America/New_York

## Resolved repository coordinates

| Field | Exact value |
|---|---|
| Supervisor repository | `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest` |
| Supervisor branch | `codex/avp-master-plan` |
| Audited pre-reset baseline | `e79f666c865b096192aa102137db1cfdfad6c321` |
| Authoritative supervisor decision commit | `b3c95d810ba76d287ca8fdcefb594c42cae0cdb3` |
| Implementation branch | `codex/avp-hybrid-tranche-1` |
| Implementation worktree | `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-hybrid-tranche1` |
| Implementation initial HEAD | `b3c95d810ba76d287ca8fdcefb594c42cae0cdb3` |
| Separate-task model | `gpt-5.6-sol` |
| Separate-task reasoning | `low` |
| Exact target | MAME set `avspu`, `Alien vs. Predator (USA 940520)`, clone/romof `avsp` |
| MAME | `.deps\mame\mame0289\mame.exe`, 0.289, SHA-256 `af6966108d9b52c22465c6d50f4e5d50cc371b50f2d27dc443935f287aad37a3` |
| Jo Engine | commit `556d081146211b6a1cfa6591d70f9487d406758b` |
| Jo patch | `engine-patches\joengine-4bpp-sprites.patch`, SHA-256 `845bde3e67100c96a52132fa13db05bacf9411ef68a9eb34dd80e04a063b086d` |
| Saturn emulator package | Yaba Sanshiro `1.20.37-2986eb`, archive SHA-256 `c34ff6766633f319bdb993481e4b82c9297d4e2a1ff1fda73a3cff4d380c2f5c` |
| Isolated reference lane | `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF`, branch `codex/mshvsf-reference-lane`, HEAD `dc5d3ea81ac8751b312234bac95d51370151a8e5` |

The implementation worktree was created clean at the supervisor decision commit. Its `.deps` and `avspu` paths are junctions to the authorized private dependency and ROM stores in the supervisor repository. Do not modify or commit through those junctions. The intentionally dirty supervisor worktree is not the implementation worktree and must not be cleaned, reset, or used for implementation commits.

## IMPLEMENTOR_INVOCATION

Launch this invocation as a separate Codex task with explicit launcher fields `model: "gpt-5.6-sol"` and `thinking: "low"`. Do not rely on an inherited default.

```text
Work only in:
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-hybrid-tranche1

Required branch:
codex/avp-hybrid-tranche-1

Immutable base and required initial HEAD:
b3c95d810ba76d287ca8fdcefb594c42cae0cdb3

Before doing anything, run and record:
  git branch --show-current
  git rev-parse HEAD
  git status --short

Stop immediately if the branch or HEAD differs, or if the implementation
worktree is unexpectedly dirty. Do not switch, reset, clean, stash, rebase,
or merge. Do not touch the supervisor worktree.

Read completely, in order:
  AGENTS.md
  docs/research/CPS2_TO_SATURN_RESET.md
  docs/research/CPS2_TO_SATURN_SOURCE_LEDGER.md
  docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md
  docs/AGENT_HANDOFF.md
  docs/TEST_PLAN.md
  docs/HARDWARE_TEST.md
  docs/NEXT_AGENT_PROMPT.md

Treat the selected title-specific hybrid native architecture as authoritative.
Execute the complete Tranche 1 in docs/NEXT_AGENT_PROMPT.md: freeze the
vertical-slice contract and provenance, produce the two-cold-run deterministic
MAME gameplay oracle with a one-frame perturbation control, and map the complete
transitive executable writer boundary. Do not modify production Saturn runtime
behavior in this tranche and do not resume the archived RP roadmap.

Use only MAME set avspu. Keep the MSHvSF lane isolated and read-only as a
one-title reference. Raw private evidence remains under ignored .deps paths;
never commit ROMs, keys, captures, state files, screenshots, audio, memory
dumps, opcode/disassembly bytes, ISO/cue files, or generated copyrighted assets.

Follow the RED/GREEN/negative-control, stop, commit, and return contracts in
docs/NEXT_AGENT_PROMPT.md. Make coherent explicit-path commits on the
implementation branch. Return the complete consolidated report and a ready
CODEX_REVIEW_INVOCATION only when the tranche passes or a declared stop
condition actually fires. That review invocation must request both the
supervisor disposition and continued assignment, include the continuation
fields required by AGENTS.md, and require Codex to return the next bounded
IMPLEMENTOR_INVOCATION appropriate to ACCEPTED, CORRECTIONS REQUIRED, or NOT
REVIEWABLE. Do not self-accept or choose the next tranche.
```

## Launch note

Launch the separate implementation task with the invocation block above and the implementation worktree as its working directory. Explicitly select `gpt-5.6-sol` with `low` reasoning in the task-launch call. Do not ask it to merge or pull the later administrative commit that records this invocation; its immutable base is the supervisor decision commit shown above.
