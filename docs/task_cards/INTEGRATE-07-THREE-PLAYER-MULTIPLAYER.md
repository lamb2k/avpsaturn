# INTEGRATE-07-THREE-PLAYER-MULTIPLAYER task card

TASK: INTEGRATE-07-THREE-PLAYER-MULTIPLAYER
KIND: INTEGRATE
STATUS: BLOCKED
CHECKPOINT: integrate-three-player-multiplayer
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-06-FOUR-CHARACTER-ROSTER]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [QA-09-RELEASE-HARDENING]

## Objective

Integrate accepted multiplayer-template results for up to three simultaneous
local players through the proven Saturn controller/multitap topology.

## Owned paths

- Multiplayer integration/acceptance paths and tests, resource coverage, state,
  and card; topology/joins/camera/combat bodies remain separately instantiated

## Existing systems to reuse

- Accepted four-character game, common player runtime, and measured source semantics.

## Systems deliberately disabled

- Unsupported player counts, network play, and speculative topology.

## Focused machine checks

- Input identity, joins/credits/continues, camera, collision/combat, resource
  peaks, deterministic repeats, missing-controller/order controls, and soak.

## Saturn build profile

Exact one-, two-, and three-player release profiles as required by topology.

## Emulator readback

Require every player identity/input/state, camera/combat events, allocations,
canaries, render/audio peaks, fallback, timing, and stability.

## Human-review requirement

Review multiplayer readability and feel after machine/emulator self-review.

## Exclusions

- P2 HUD evidence alone is not gameplay, join, or multitap proof.

## Hard stops

- Missing physical topology, resource/timing failure, ambiguous input ownership,
  or uninstantiated multiplayer body.

## Next eligible cards

- `QA-09-RELEASE-HARDENING`.
