# Tranche 2B implementor invocation

```text
IMPLEMENTOR_INVOCATION

SUPERVISOR_REPOSITORY: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
SUPERVISOR_WORKTREE: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-host-baseline-tranche2a
SUPERVISOR_BRANCH: codex/avp-v2-writer-map-selection
SUPERVISOR_SELECTION_SHA: 065ddfdb586184074973c2bccad55a45007f5f32
ACCEPTED_IMPLEMENTATION_BRANCH: codex/avp-host-baseline-tranche-2a
ACCEPTED_IMPLEMENTATION_HEAD: eef350a3de6e44d1648a861ab98215c3d61ce20c

IMPLEMENTATION_WORKTREE: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-writer-map-tranche2b
IMPLEMENTATION_BRANCH: codex/avp-writer-map-tranche-2b
IMMUTABLE_BASE_SHA: 065ddfdb586184074973c2bccad55a45007f5f32
REMOTE: private-origin
REMOTE_URL: https://github.com/stevedamnvan/AvPSaturnCapabilityTest-private.git
REMOTE_VISIBILITY: PRIVATE (verified before implementation resume)
REMOTE_ACCEPTED_BRANCH_SHA: codex/avp-host-baseline-tranche-2a=eef350a3de6e44d1648a861ab98215c3d61ce20c
REMOTE_SUPERVISOR_INVOCATION_RECORD_SHA: codex/avp-v2-writer-map-selection contains dad3bdeedf0cab9e2f31fa3b491fe50830f0ec1e
REMOTE_IMPLEMENTATION_START_SHA: codex/avp-writer-map-tranche-2b=065ddfdb586184074973c2bccad55a45007f5f32
REMOTE_PUSH_GATE: SATISFIED before implementation resume; re-verify with git ls-remote

MODEL: gpt-5.6-sol
THINKING: low
AGENT_PROFILE: .codex/agents/avp-implementer.toml

AUTHORITATIVE_EXECUTION_BOOK: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-writer-map-tranche2b\docs\NEXT_AGENT_PROMPT.md
REVIEW_RETURN_TEMPLATE: C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-writer-map-tranche2b\docs\CODEX_REVIEW_TEMPLATE.md

OBJECTIVE: Execute all of Tranche 2B / V2A. Produce and validate the deterministic class 0x1F, type 0x0C enemy HIT/KO executable writer/routine manifest for source frames 5191-5469, including exact HIT and KO anim_record writer ownership, selected call/data/event closure, accepted-boundary membership, and zero unresolved or unattributed selected dependencies. Do not emit or integrate production lifted C.

AUTHORITATIVE_ARCHITECTURE:
- avspu USA 940520 only; MSHvSF remains read-only reference evidence.
- MAME 0.289 semantic oracle; accepted contract/oracle/boundary are immutable.
- Opcode image supplies instructions and code targets; program image supplies ROM data.
- Selective title-specific lifting only; no emulator, broad recompiler, generalized Capcom engine, or presentation-first work.
- This tranche closes the lift contract only. Host differential lift is a later supervisor-selected body.

OWNED_PATHS:
- tools/map_avsp_hit_ko_writer_set.py
- tests/test_avsp_hit_ko_writer_set.py
- data/avsp_hit_ko_writer_set.json
- docs/AGENT_HANDOFF.md for final evidence only
- docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md for final evidence only

FORBIDDEN_PATHS_AND_OUTPUTS:
- capability_model.c, capability_model.h, main.c, Saturn runtime/build/package files
- tools/map_avsp_translation_boundary.py and all accepted contract/oracle/boundary JSON
- .deps, avspu ROM contents, generated runtime headers, archived plans
- raw trace lines, disassembly text, opcode/program bytes, screenshots, state dumps, copyrighted asset data

PRIVATE_PROVISIONING:
- .deps is a git-ignored junction to C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest\.deps
- avspu is a git-ignored junction to C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest\avspu
- Treat both junction targets as read-only evidence. Never delete, rewrite, clean, stage, or commit them.

REQUIRED_SEQUENCE:
1. Read AGENTS.md and every active file named by its read order, including the complete docs/NEXT_AGENT_PROMPT.md.
2. Verify the private remote and the three recorded remote SHAs, then verify branch codex/avp-writer-map-tranche-2b and exact base 065ddfdb586184074973c2bccad55a45007f5f32 before edits.
3. Commit the focused production-validator contract test RED before the mapper/artifact exists.
4. Implement the bounded mapper, validator, and deterministic committed manifest; run GREEN.
5. Run all nine committed-artifact mutation controls and the end-to-end private-correlation scratch mutation.
6. Generate twice and prove byte identity; run the focused oracle/boundary tests, complete safe host suite, and git diff checks.
7. Commit final evidence in the two allowed documentation files.
8. Return through the complete filled docs/CODEX_REVIEW_TEMPLATE.md envelope. Do not self-accept or rotate the plan.

DECISION_TABLE:
- Preferred/selected: close both class 0x1F HIT and KO anim_record writer paths with zero unresolved/unattributed selected dependencies.
- If HIT closes but KO remains ambiguous after same-epoch writer correlation, dynamic call-context closure, and semantic before/after plus program-data validation: stop with falsification evidence; do not accept HIT-only.
- Player, camera/stage, whole-window, production lift, and broader engine bodies are not authorized alternatives.

REQUIRED_GREEN_COMMANDS:
- python tools/map_avsp_hit_ko_writer_set.py --self-test
- python tools/map_avsp_hit_ko_writer_set.py --generate
- python tests/test_avsp_hit_ko_writer_set.py
- python tests/test_avsp_vertical_slice_oracle.py
- python tests/test_avsp_translation_boundary.py
- powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test.ps1
- git diff --check

STOP_CONTRACT: Stop only at a hard stop declared in docs/NEXT_AGENT_PROMPT.md. Do not weaken a validator, change an accepted artifact, expand to production lifting, or convert a partial HIT-only result into success.

COMMIT_CONTRACT: RED test; GREEN mapper/validator/manifest; final evidence/handoff. Stage explicit owned paths only. No amend, rebase, merge, cherry-pick, broad add, clean, reset, force, or private/generated commit.

RETURN_CONTRACT: Report exact branch/base/final SHA, commits oldest first, exact changed files, RED/GREEN/refactor exits, nine production-validator mutations, end-to-end scratch mutation, output hash/counts/entry PCs, two-generation determinism, cumulative regression, evidence tiers, exclusions, remaining gaps, status, and a complete CODEX_REVIEW_INVOCATION requesting supervisor disposition plus the corresponding next IMPLEMENTOR_INVOCATION.
```
