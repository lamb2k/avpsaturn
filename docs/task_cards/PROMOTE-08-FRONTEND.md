# PROMOTE-08-FRONTEND task card

TASK: PROMOTE-08-FRONTEND
KIND: PROMOTE
STATUS: BLOCKED
CHECKPOINT: promote-frontend
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SALVAGE-08-FRONTEND, QA-08-FRONTEND, USER-08-FRONTEND]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-04-COLD-BOOT-TO-ROUND1]

## Objective

Promote the explicitly approved frontend, measured four-character select, and
loading handoff behind route, input, render, audio, and asset ports.

## Owned paths

- Future `src/port_v2/frontend/**`, focused tests, card-scoped wiring/readback,
  migration/coverage fields, state, and card

## Existing systems to reuse

- Accepted SALVAGE/QA/USER-08 package and measured frontend interaction contract.

## Systems deliberately disabled

- Gameplay rules in scene bytecode, unmeasured cancel behavior, and route after
  the Round 1 handoff.

## Focused machine checks

- Strict interfaces, approved-lock repeat, exact input/route/load differentials,
  and rejected identity, latency, wrap, or scene-operation dependencies.

## Saturn build profile

Dedicated `FrontendPromotionBench`.

## Emulator readback

Require semantic route/input/render/audio/load events, selected identity
persistence, canaries, no fallback, final scanout, and stability.

## Human-review requirement

No renewed review if the approved frontend is unchanged; otherwise return to USER-08.

## Exclusions

- No Round 1 implementation or physical title-to-credits claim.

## Hard stops

- Approved regression, route/load ambiguity, or unmeasured behavior required.

## Next eligible cards

- `INTEGRATE-04-COLD-BOOT-TO-ROUND1`.
