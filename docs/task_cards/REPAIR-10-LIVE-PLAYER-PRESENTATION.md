# REPAIR-10-LIVE-PLAYER-PRESENTATION task card

TASK: REPAIR-10-LIVE-PLAYER-PRESENTATION
KIND: REPAIR
STATUS: READY
CHECKPOINT: repair-live-player-presentation
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: [Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-09-LIVE-ENCOUNTER-REVIEW]

## Objective

Correct the live Predator Warrior presentation boundary reported at USER-09:
map measured left/right facing to the renderer without inversion, and prevent
the unrelated legacy attack clip from flashing before each selector-owned
source attack sequence begins. Preserve selectors 1-4 and their approved
source timing, poses, collision, damage, reaction, and KO locks.

## Owned paths

- `main.c` live player adapter only
- `src/port_v2/gameplay/player_action/**`
- `tests/port_v2/integration/live_encounter/**`
- This card, USER-09 feedback, state, roadmap, handoff, migration, and coverage
  ledgers
- Ignored `build/feedback/REPAIR-10-LIVE-PLAYER-PRESENTATION/**`

## Existing systems to reuse

- ORACLE-04 measured facing values and presentation-first offsets; the accepted
  PROMOTE-10 controller; REPAIR-09 selector-owned source presentation; and the
  exact INTEGRATE-04A target/emulator harness.

## Systems deliberately disabled

- Street-alien AI decisions, player/alien collision or damage behavior,
  selector order, complete move set, frontend, route expansion, multiplayer,
  and physical-status changes.

## Focused machine checks

- Strict C90 host replay twice; assert source facing `0 -> -1` and `1 -> +1` at
  the CapActor boundary; assert every selector holds the control pose before
  `presentation_first`, owns every presentation tick, and ends at its measured
  return; reject a reversed-facing mutation and a restored generic-attack-flash
  mutation.

## Saturn build profile

Build the exact live-encounter diagnostic and normal interactive target from
the committed candidate; preserve all accepted residency and asset locks.

## Emulator readback

Collect two pinned cold semantic runs plus a visible interactive clip. Require
identical ledgers, correct direction-to-facing signs, no generic attack pose on
the two startup ticks, selector-owned presentation thereafter, and unchanged
contact/damage/HIT/KO/clear behavior.

## Human-review requirement

Renew `USER-09-LIVE-ENCOUNTER-REVIEW` after machine and emulator checks. Ask
exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"
Do not treat this player-presentation repair as acceptance of the separately
reported AI or player/alien collision problems.

## Exclusions

- No AI/collision correction, new attack invention, selector reordering,
  physical claim, frontend activation, or complete Round 1 claim.

## Hard stops

- Any change to selector-specific source records/timing, collision/damage,
  alien behavior, accepted presentation locks outside the two named boundary
  defects, target failure, semantic nondeterminism, or missing mutation reject.

## Next eligible cards

- Renewed `USER-09-LIVE-ENCOUNTER-REVIEW`; the reported AI and collision issues
  remain unresolved and `SALVAGE-08-FRONTEND` remains blocked.
