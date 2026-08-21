# Active checkpoint

`project_state.yaml` is the machine-readable source of truth. The active task
card is the only current control body. Historical implementation and correction
narrative remains recoverable in Git and in the evidence ledger; do not append
it here.

## Current disposition boundary

- Tranche 2A is the last accepted implementation foundation.
- The V2-2B writer-map candidate is at the `review_candidate_head` recorded in
  `project_state.yaml`.
- The candidate records a 301-PC, 302-edge, 12-routine, nine-computed-target
  class `0x1F` HIT/KO closure over seven semantic fields, with two typed event
  exits and zero unresolved or unattributed selected dependencies.
- The committed writer manifest identity is recorded in `project_state.yaml`.
- Focused writer/oracle/boundary controls and an isolated complete host suite
  were reported passing. This is host/MAME evidence only.
- No native lifted HIT/KO routine, Saturn target result, emulator result,
  release result, audio result, or physical-hardware result is claimed.

The consolidated Tier 2 disposition is `CORRECTIONS REQUIRED`. Semantic and
provenance review found that the candidate does not retain exact writer evidence
for every selected field, constructs window-selected rather than call-rooted
control closure, and asserts rather than derives outgoing-edge, actor-field,
ROM-data, work-RAM, and exclusion dependencies. Saturn-scope review also found
two committed capture helpers outside the exhaustive owned-path contract.

Corrections stay on the existing candidate branch/worktree. The next card,
`docs/task_cards/V2-B1.md`, remains blocked until the corrected candidate is
re-reviewed and accepted; it produces executable native behavior rather than
more mapping.

## Operating commands

```powershell
.\tools\Invoke-TaskExecutor.ps1 -Task V2-2B -Executor Auto -TaskKind Correction -PlanOnly
.\tools\Invoke-TaskExecutor.ps1 -Task V2-2B -Executor Auto -TaskKind Correction
```

The executor performs one bounded provider invocation, then runs every required
lane and generates the candidate-bound bundle only when all lanes pass. It does
not retry or interpret failures. Codex Goal Mode inspects its ignored JSON
result, may explicitly resume the same session with `-ResumeSessionId` and a
bounded `-FeedbackPath`, and owns all reviewer invocation and consolidation.

After external semantic, provenance, and Saturn review, Goal Mode writes one
hashed disposition under ignored `build/`, integrates an accepted candidate
into the controller branch when applicable, and invokes:

```powershell
.\tools\Apply-ReviewDisposition.ps1 -DispositionPath <ignored-json-path>
```

The disposition helper validates and applies only the declared result. On
V2-2B acceptance it may mark V2-2B accepted and the explicitly named V2-B1 card
READY, but it never launches or implements V2-B1. Goal Mode inspects and commits
the resulting explicit state/card diff. No repository Stop hook or autonomous
control loop is installed.
