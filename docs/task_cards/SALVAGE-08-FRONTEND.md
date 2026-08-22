# SALVAGE-08-FRONTEND task card

TASK: SALVAGE-08-FRONTEND
KIND: SALVAGE
STATUS: BLOCKED
CHECKPOINT: salvage-frontend
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-03-PLAYABLE-SLICE]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [QA-08-FRONTEND]

## Objective

Isolate legal/logos, attract, title, credit wait, measured four-character
select/confirm, and loading handoff without giving scene bytecode gameplay authority.

## Owned paths

- Future frontend bench/adapters, presentation-scene fixtures, focused tests,
  readback, migration/coverage fields, state, and card

## Existing systems to reuse

- `AvspSceneDef`, scene manifest, measured frontend interaction, and current
  source-derived frontend assets.

## Systems deliberately disabled

- Enemy AI, collision, damage, player actions, wave completion, and Round 1 rules.

## Focused machine checks

- Deterministic input ledger, four identity/grid/no-wrap/latency/confirm
  contracts, scene transitions, line-scroll gating, and perturbation controls.

## Saturn build profile

Dedicated `FrontendSalvageBench`.

## Emulator readback

Require route/substate, cursor/character identity, input response, load
ownership, scene operations, line-scroll use, canaries, failures, and stability.

## Human-review requirement

Required through `USER-08-FRONTEND` after QA.

## Exclusions

- No gameplay bytecode, fabricated cancel behavior, or complete-route claim.

## Hard stops

- Source interaction mismatch, unsupported scene operation, unknown load
  ownership, or material frontend architecture decision.

## Next eligible cards

- `QA-08-FRONTEND`.
