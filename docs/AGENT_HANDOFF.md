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

The candidate still requires one consolidated Tier 2 disposition. The next
card, `docs/task_cards/V2-B1.md`, is intentionally blocked until that verdict is
`ACCEPTED`; it produces executable native behavior rather than more mapping.

## Operating commands

```powershell
.\verify.ps1 -Lane Fast
.\verify.ps1 -Lane Oracle
.\tools\New-ReviewBundle.ps1 -Base f2c9a4725dffdcb2e5689c70914511674fb3c9ef -Task workflow-simplification
```

Keep corrections on the current checkpoint branch/worktree. After acceptance,
activate the next task by updating `project_state.yaml` and the card status,
then use `tools/start-agent-task.ps1`. Launch and review renderings live under
ignored `build/` paths and are never committed as source history.
