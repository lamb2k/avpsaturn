# Tranche 2A implementor invocation

The immutable implementation base is the supervisor selection commit
`c9d6dc420df999dae9b8bedaea4bf0f735214ea2`. The invocation record itself is a
later supervisor-only commit and must not replace that base.

```text
IMPLEMENTOR_INVOCATION

MODE: SUPERVISED_IMPLEMENTATION

REPOSITORY:
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest

SUPERVISOR_SELECTION_WORKTREE:
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-hybrid-tranche1

IMPLEMENTATION_WORKTREE:
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-host-baseline-tranche2a

IMPLEMENTATION_BRANCH:
codex/avp-host-baseline-tranche-2a

BASE_SHA:
c9d6dc420df999dae9b8bedaea4bf0f735214ea2

TASK_LAUNCH_MODEL:
gpt-5.6-sol

TASK_LAUNCH_THINKING:
low

OBJECTIVE:
Execute only docs/NEXT_AGENT_PROMPT.md: restore the strict host-suite baseline
with the exact start-transition enum and 30-frame duration declarations,
literal boundary tests, two scratch negative controls, and the complete
host/generator regression. Do not begin V2.

PLAYABLE_OR_OBSERVABLE_OUTCOME:
Strict C90 gameplay-model compilation and the complete test.ps1 suite pass from
the clean implementation branch. No Saturn, emulator, release, or physical
claim is authorized.

WORKTREE_CREATION:
git -C "C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest" worktree add -b codex/avp-host-baseline-tranche-2a "C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-host-baseline-tranche2a" c9d6dc420df999dae9b8bedaea4bf0f735214ea2

OWNED_PATHS:
- capability_model.h
- tests/capability_model_test.c
- docs/AGENT_HANDOFF.md for final evidence
- docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md for final evidence

SETTLED_SOLUTION:
- Add CAP_ENCOUNTER_START_TRANSITION immediately after MAIN_MENU.
- Add CAP_START_TRANSITION_FRAMES = 30 with source-frame provenance.
- Pin literal 30 and the 29/30 state/timer boundary in tests.
- Update the shared start_encounter test helper.
- Do not modify capability_model.c.
- Treat c7e8f80a54725977a5e61486bb9960f37f1680b7 as read-only evidence;
  do not cherry-pick it.

TDD_AND_VERIFICATION:
Follow every RED, GREEN, REFACTOR, NEGATIVE CONTROL, REGRESSION, COMMIT, hard
stop, evidence-tier, resource, and return requirement in
docs/NEXT_AGENT_PROMPT.md. Preserve oracle ledger
f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1 and
boundary artifact SHA-256
95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4.

COMMIT_CONTRACT:
Make a RED test commit, a GREEN minimal-header commit, and a final evidence
commit. Stage explicit paths only. Do not amend, rebase, merge, cherry-pick,
clean, reset, broad-stage, or commit private/generated payloads.

RETURN_CONTRACT:
Return the complete final report required by docs/NEXT_AGENT_PROMPT.md and end
with a fully populated CODEX_REVIEW_INVOCATION copied from
docs/CODEX_REVIEW_TEMPLATE.md. Do not self-accept or select V2.
```

## Launch note

If launched as a separate Codex task, explicitly set `model` to
`gpt-5.6-sol` and `thinking` to `low` in the task-creation call. The repository
agent profile is also pinned to those values.
