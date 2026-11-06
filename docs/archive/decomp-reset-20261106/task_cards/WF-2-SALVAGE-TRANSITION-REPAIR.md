# WF-2-SALVAGE-TRANSITION-REPAIR task card

TASK: WF-2-SALVAGE-TRANSITION-REPAIR
KIND: REPAIR
STATUS: ACCEPTED
CHECKPOINT: salvage-transition-repair
BASE: SALVAGE-00-OLD-BUILD-BASELINE evidence branch
BRANCH: codex/avp-wf-2-salvage-transition-repair
TIER: 0
DEPENDENCIES: [SALVAGE-00-OLD-BUILD-BASELINE]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-01-PLAYER-LOAD-RENDER-INPUT]

## Objective

Repair workflow validators that froze initialization state as permanent state,
then record the evidence-supported SALVAGE-00 disposition and activate the
dependency-safe SALVAGE-01 successor.

## Owned paths

- `tests/test_workflow_policy.py`
- `tests/test_task_card_state.py`
- `tests/test_port_v2_migration_map.py`
- `data/port_v2_migration_map.yaml`
- `project_state.yaml`
- `docs/PARITY_PLAN.md`
- `docs/AGENT_HANDOFF.md`
- `docs/task_cards/WF-2-SALVAGE-TRANSITION-REPAIR.md`
- Status/disposition fields in the SALVAGE-00 and SALVAGE-01 cards only.

## Existing systems to reuse

- The SALVAGE-00 committed evidence, ignored feedback package, and existing
  workflow/card/ledger validators.

## Systems deliberately disabled

- Gameplay, rendering, loading, asset, build, emulator, and production code.
- All physical Saturn claims.

## Focused machine checks

- Migration-ledger schema and legal-transition fixtures.
- Task-card/state transition fixtures and invalid-dependency negative control.
- Workflow-policy check, Fast lane, and `git diff --check`.

## Saturn build profile

None. This card must not run a Saturn build or emulator diagnostic.

## Emulator readback

None. Existing SALVAGE-00 readback is recorded evidence only.

## Human-review requirement

None. This workflow repair must neither solicit nor infer a visual approval.

## Exclusions

- No SALVAGE-01 implementation.
- No change to Capability Gate, V2-2B status, protected worktrees, or ignored
  SALVAGE-00 feedback artifacts.

## Hard stops

- Any protected-worktree mutation, evidence discrepancy, or need for a
  production/gameplay architecture decision.

## Disposition evidence

- The initialization-only validator assumptions were replaced with schema and
  legal-transition validation, including positive and negative transition
  fixtures.
- SALVAGE-00 evidence remains at
  `fcb7eaf0c3e6af28394908c251056daca7fb62c2`; no new Saturn evidence was run.
- SALVAGE-01 was activated only because its declared scope excludes the observed
  enemy/camera condition.

## Next eligible cards

- `SALVAGE-01-PLAYER-LOAD-RENDER-INPUT`.
