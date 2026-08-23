# SALVAGE-07-CDDA-RESIDENCY task card

TASK: SALVAGE-07-CDDA-RESIDENCY
KIND: SALVAGE
STATUS: READY
CHECKPOINT: salvage-cdda-residency
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [PROMOTE-06-PCM]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-07-CDDA-RESIDENCY]

## Objective

Isolate CDDA/data-read ownership and one phase-scoped residency manifest,
including all memory domains, high-water, legal windows, and canaries.

## Owned paths

- Future CDDA/residency bench, manifest fixtures, focused tests, readback,
  migration fields, state, and card

## Existing systems to reuse

- Existing loading/audio diagnostics, approved PCM path, and source audio events.

## Systems deliberately disabled

- New route content, generalized cache/streamer, gameplay changes, and full CDDA.

## Focused machine checks

- Deterministic ownership transitions, manifest schema, high-water/canaries,
  illegal data-read and missing-allocation controls, and source-event binding.

## Saturn build profile

Dedicated `CddaResidencySalvageBench`.

## Emulator readback

Require ownership state, track/event, data-read windows, allocation high-water,
canaries, asset/fallback flags, timing, and stability.

## Human-review requirement

Audible output requires a new bounded USER_REVIEW card before subjective approval.

## Exclusions

- No monolithic archive, general cache, or physical Saturn proof.

## Hard stops

- Illegal drive overlap, unknown allocation, unsupported audio event, or
  material residency architecture decision.

## Next eligible cards

- `PROMOTE-07-CDDA-RESIDENCY`.
