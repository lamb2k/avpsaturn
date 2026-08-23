# PROMOTE-06-PCM task card

TASK: PROMOTE-06-PCM
KIND: PROMOTE
STATUS: READY
CHECKPOINT: promote-pcm
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [PROMOTE-05-HUD, SALVAGE-05-HUD-PCM, USER-05-HUD-PCM-REVIEW]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-07-CDDA-RESIDENCY]

## Objective

Promote the approved short Predator melee PCM cue behind a semantic audio port
without changing its bytes or approved timing.

## Owned paths

- Future `src/port_v2/audio/pcm/**`, focused tests, card-scoped wiring/readback,
  migration fields, state, and card

## Existing systems to reuse

- Approved cue identity and timing 147/150/200.

## Systems deliberately disabled

- CDDA, broad combat mixing, new cues, route ownership, and physical claims.

## Focused machine checks

- Byte/timing lock, deterministic event repeat, wrong-cue/timing mutation,
  strict compile, SCSP allocation, and canaries.

## Saturn build profile

Dedicated `PcmPromotionBench`.

## Emulator readback

Require semantic cue event, trigger frames, allocation/canaries, audio failure
flags, stability, and exact image/profile binding.

## Human-review requirement

No new review if the approved audible result is unchanged; renew USER-05 if at risk.

## Exclusions

- No complete audio parity or physical audibility claim.

## Hard stops

- Cue/timing regression, unbounded mixer ownership, or material audio interface.

## Next eligible cards

- `SALVAGE-07-CDDA-RESIDENCY`.
