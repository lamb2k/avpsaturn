# SALVAGE-03-COLLISION task card

TASK: SALVAGE-03-COLLISION
KIND: SALVAGE
STATUS: ACCEPTED
CHECKPOINT: salvage-collision
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SALVAGE-00-OLD-BUILD-BASELINE]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: [Target, Emulator]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [V2-2B, V2-B1, SALVAGE-04-CAMERA-STAGE-LAYERS]

## Objective

Isolate and evaluate source collision selectors and hitboxes without applying authored damage, HIT, or KO behavior.

## Owned paths

- `tests/port_v2/collision_bench/**`
- Card-scoped collision adapter candidates
- Collision migration entry, state, and card

## Existing systems to reuse

- `avsp_collision.*`, source hitbox evidence, existing collision tests, and read-only prototype collision deltas.

## Systems deliberately disabled

- Damage, HIT, KO, enemy AI, and visual changes.

## Focused machine checks

- Strict compile; overlap/no-overlap/edge focused tests; deterministic repeat; translated/empty hitbox negative control; source-evidence binding.

## Saturn build profile

Host bench first; optional dedicated `CollisionSalvageBench` only if target-facing behavior is exercised.

## Emulator readback

If built for Saturn, require selector inputs/outputs, actor positions, no authored damage writes, and stability.

## Human-review requirement

None for this card. If the bench exposes subjective output, stop and activate a predeclared USER_REVIEW card; do not infer approval.

## Exclusions

- No acceptance or repair of V2-2B and no authored damage approximation.

## Hard stops

- Unsupported source dependency, unsafe evidence state, material interface decision, or exhausted correction cycle.

## Next eligible cards

- `V2-2B` may resume independently.
- `V2-B1` after SALVAGE-03 and accepted V2-2B.
- `SALVAGE-04-CAMERA-STAGE-LAYERS` remains dependency-safe.
