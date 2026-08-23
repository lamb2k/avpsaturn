# SALVAGE-07-CDDA-RESIDENCY task card

TASK: SALVAGE-07-CDDA-RESIDENCY
KIND: SALVAGE
STATUS: ACCEPTED
CHECKPOINT: salvage-cdda-residency
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [PROMOTE-06-PCM]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-07-CDDA-RESIDENCY-REVIEW]

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

- `USER-07-CDDA-RESIDENCY-REVIEW` is required before promotion because the
  salvage bench produces new audible output.

## Accepted technical result

- Evaluated commit: `17967a50b62318dae81d12f33c18b92ce8f72b37`.
- Strict C90 host contract passes deterministically with illegal-read,
  missing-allocation, and wrong-source-event controls.
- `CddaResidencySalvageBench` builds at linked BSS end `0x06087a70`, leaving
  230800 bytes below the `0x060c0000` work-RAM limit.
- Two committed-SHA pinned Yaba Sanshiro runs agree semantically at normalized
  ISO SHA-256 `46ffc83235340f48e7636692cd8c207d7a58285890af6bccdba348e10d2d8698`.
- Both runs observe Track 2 ownership, reject one late read and one illegal
  window, then complete the one legal 64-byte phase-boundary read with intact
  canaries, 72 bytes phase-owned work RAM, zero other-domain phase allocations,
  and zero runtime or asset failures.
- The source binding is `ADAPTED` to `street_combat_begins` at source frame
  2520; it is not claimed as an exact source-timed music implementation.
- Fast and the card-scoped source/Oracle checks pass. The generic Oracle lane
  remains `INCOMPLETE` only because its paused V2-2B private writer inputs are
  absent; that unrelated HIT/KO evidence does not block this CDDA result.
- Pinned-emulator visual self-review passes for the dedicated diagnostic. The
  debug-pause screenshots may expose alternating text planes, so semantic
  readback—not screenshot text—is the deterministic ownership evidence.
- Audible fidelity remains `AWAITING_USER_FEEDBACK`; a second emulator, normal
  release, full-route residency, and physical Saturn remain `UNRUN`.
