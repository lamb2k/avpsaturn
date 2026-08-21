# WF-1 task card

TASK: WF-1
KIND: REPAIR
STATUS: ACCEPTED
CHECKPOINT: workflow-simplification-accepted
BASE: f2c9a4725dffdcb2e5689c70914511674fb3c9ef
BRANCH: codex/avp-workflow-simplification
TIER: 2
DEPENDENCIES: []
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-00-OLD-BUILD-BASELINE]

## Objective

Historical accepted workflow simplification that established the task-card/state control system. The salvage pivot extends that system; this card is not active.

## Owned paths

- Historical workflow policy and control artifacts only.

## Existing systems to reuse

- `project_state.yaml`, `docs/PARITY_PLAN.md`, task cards, `verify.ps1`, and review/launch tooling.

## Systems deliberately disabled

- All gameplay, rendering, audio, loading, and physical implementation.

## Focused machine checks

- Preserved accepted Fast workflow result; current workflow is checked by the active repository Fast lane.

## Saturn build profile

None.

## Emulator readback

None.

## Human-review requirement

None.

## Exclusions

- No new work under this accepted historical card.

## Hard stops

- Do not reactivate; create a bounded dependency-ready card.

## Next eligible cards

- `SALVAGE-00-OLD-BUILD-BASELINE`.
