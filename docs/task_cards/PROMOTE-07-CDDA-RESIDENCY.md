# PROMOTE-07-CDDA-RESIDENCY task card

TASK: PROMOTE-07-CDDA-RESIDENCY
KIND: PROMOTE
STATUS: READY
CHECKPOINT: promote-cdda-residency
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SALVAGE-07-CDDA-RESIDENCY, USER-07-CDDA-RESIDENCY-REVIEW]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-03-PLAYABLE-SLICE]

## Objective

Promote accepted CDDA/data-read ownership and the first complete phase manifest
behind audio and asset/load ports.

## Owned paths

- Future `src/port_v2/audio/cdda/**`, `src/port_v2/residency/**`, focused
  tests, card-scoped wiring/readback, migration fields, state, and card

## Existing systems to reuse

- Accepted SALVAGE-07 ownership/manifest evidence and promoted PCM.

## Systems deliberately disabled

- New stage content, generalized streaming, and unrelated gameplay changes.

## Focused machine checks

- Interface compile, deterministic ownership repeat, manifest/canary locks, and
  rejected illegal-read, missing-region, or altered-track dependencies.

## Saturn build profile

Dedicated `CddaResidencyPromotionBench`.

## Emulator readback

Require semantic audio/load events, ownership transitions, all allocation
domains, high-water/canaries, fallback flags, timing, and stability.

## Human-review requirement

Carry forward only explicit audible approval; otherwise activate a bounded review.

## Exclusions

- No physical claim and no whole-game residency claim.

## Hard stops

- Ownership or canary failure, unmeasured required allocation, or approved PCM regression.

## Next eligible cards

- `INTEGRATE-03-PLAYABLE-SLICE`.
