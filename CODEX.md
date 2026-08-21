# Codex bootstrap

Read `AGENTS.md` first. It is authoritative for this repository.

The active architecture decision and evidence are:

- `docs/research/CPS2_TO_SATURN_RESET.md`
- `docs/research/CPS2_TO_SATURN_SOURCE_LEDGER.md`
- `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md`

Execute only the current tranche in `docs/NEXT_AGENT_PROMPT.md`. Archived pre-reset documents are historical evidence, not instructions. Keep the AvP and MSHvSF lanes isolated, preserve uncommitted private work, and never turn host/emulator evidence into a hardware claim.

Use `docs/CODEX_REVIEW_TEMPLATE.md` for every implementor return. When creating
a separate implementor task, explicitly set `model: "gpt-5.6-terra"` and
`thinking: "xhigh"`; do not infer those launch fields from the supervisor's own
reasoning level.

The launch order is mandatory: verify the configured GitHub destination is
private; push and SHA-verify the reviewed candidate, supervisor
selection/invocation, and implementation-start branches; record them in
`docs/IMPLEMENTOR_INVOCATION.md`; only then create or resume the implementation
task. A locally committed but unpushed selection is not a valid launch base.
