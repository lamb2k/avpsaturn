# Active agent handoff

## Supervisor decision

The 2026-08-20 audit selected approach E, a title-specific hybrid native port, and made `docs/research/CPS2_TO_SATURN_RESET.md` authoritative. The exact immutable supervisor commit is supplied by `docs/IMPLEMENTOR_INVOCATION.md`; this file intentionally does not attempt to self-reference its own commit hash.

Audit input baseline was `codex/avp-master-plan` at `e79f666c865b096192aa102137db1cfdfad6c321`. No runtime implementation was performed during the audit. The complete existing host suite passed in an isolated shadow copy; no new target build, emulator session, or physical Saturn run was claimed.

## Truth at handoff

- Target is exactly `avspu`, USA 940520, clone of `avsp`; local ROM verification passes under MAME 0.289.
- Existing extraction/oracle infrastructure is valuable and should be reused.
- Current gameplay remains predominantly authored C behavior.
- Runtime ROM actor coverage is limited to a street-alien WALK/ATTACK subset.
- HIT/KO has an explicit external animation-pointer-writer gap.
- Runtime rendering is per 16x16 tile, not per CPS object.
- Static demand peaks at 909 tiles; physical VDP1 performance is unknown.
- RP4 is a one-emulator bounded fixture, not a production stage or hardware proof.
- Shipped palette content covers 10 banks while measured routes reference 15.
- Stage CDDA is disabled in code.
- Capability slice is 0/12.

## Repository reorganization

The live agent and execution documents now point to the reset architecture. The exact pre-reset dirty planning state is preserved under `docs/archive/pre-reset-2026-08-20/` as historical evidence only. Runtime fallbacks and fixtures remain in source until replacements pass; they were not deleted for cosmetic cleanup.

## Next bounded tranche

Execute only `docs/NEXT_AGENT_PROMPT.md`: freeze the vertical-slice contract/provenance, build the unified deterministic MAME gameplay oracle, and produce the transitive executable writer boundary for the selected slice. Do not modify production runtime behavior in this tranche.

Expected implementation branch: `codex/avp-hybrid-tranche-1`. The supervisor launch invocation supplies the isolated worktree and exact immutable base.

## Required return

Return branch/base/final SHA, commits, explicit files, target/tool/input hashes, RED/GREEN/negative controls, exact commands and exits, generated schema/manifest hashes, unresolved executed edges/globals/hardware exits, evidence-tier changes, dirty status, and a review invocation. Stop on the conditions in the tranche rather than broadening architecture.
