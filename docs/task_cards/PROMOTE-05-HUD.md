# PROMOTE-05-HUD task card

TASK: PROMOTE-05-HUD
KIND: PROMOTE
STATUS: ACCEPTED
CHECKPOINT: promote-hud
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [PROMOTE-04-CAMERA-STAGE, SALVAGE-05-HUD-PCM, REPAIR-05-HUD-COLORS, SALVAGE-05B-PLAYER-2-HUD, USER-05-HUD-PCM-REVIEW]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [PROMOTE-06-PCM]

## Objective

Promote the approved corrected P1 and active P2 HUD presentation behind a
semantic HUD render interface.

## Owned paths

- Future `src/port_v2/hud/**`, focused tests, card-scoped wiring/readback,
  migration fields, state, and card

## Existing systems to reuse

- Approved P1 colors/health/energy and active P2 Maj. Schaefer HUD/weapon locks.

## Systems deliberately disabled

- P2 joins, gameplay input, multiplayer state, new HUD art, and PCM changes.

## Focused machine checks

- Palette/CRAM and semantic-state locks, deterministic repeat, broken-color and
  missing-P2 controls, strict compile, and exact asset identity.

## Saturn build profile

Dedicated `HudPromotionBench`.

## Emulator readback

Require both HUD semantic states, palette ownership, render counts, canaries,
asset failures, final scanout, and stability.

## Human-review requirement

No new review if reviewed output is unchanged; renew USER-05 for visible risk.

## Exclusions

- Presentation does not prove P2 gameplay, joins, or multitap topology.

## Hard stops

- Approved color/P2 regression, unresolved production CRAM ownership, or
  material interface decision.

## Next eligible cards

- `PROMOTE-06-PCM`.
