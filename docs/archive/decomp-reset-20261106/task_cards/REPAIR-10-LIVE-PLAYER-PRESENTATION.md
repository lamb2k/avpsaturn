# REPAIR-10-LIVE-PLAYER-PRESENTATION task card

TASK: REPAIR-10-LIVE-PLAYER-PRESENTATION
KIND: REPAIR
STATUS: ACCEPTED
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

## Validated evidence

- Implementation commit:
  `4ea7c1829013e95b5ffdc34ef02ea5c133ee9a80`.
- Strict C90 live-encounter replay passes twice. Source-facing `0 -> -1` and
  `1 -> +1`, every selector's `presentation_first` and `return_frame`, invalid
  selectors, reversed-facing mutation, and restored legacy-attack-flash
  mutation are checked.
- Fast and Oracle lanes pass. Both normal interactive and diagnostic Saturn
  Target profiles build with strict warnings-as-errors.
- Two cold pinned Yaba Sanshiro `1.20.37-2986eb` runs use normalized diagnostic
  ISO SHA-256
  `26368cd72ad93d7df423ddf94d81ea5daf537dee3041f6c6568f4848d3b60921`.
  Their 448 semantic samples and final state are identical: four player
  contacts, two alien contacts, one deliberate miss, HIT/KO/clear/continued
  movement, zero failures/fallbacks, and intact canaries.
- Genuine Windows.Graphics.Capture action frame 182 is bound to the same commit.
  The renewed interactive ISO SHA-256 is
  `4b73b534f9a2f542f5e51680b1332c235201aa2b88b58f12391b04c0951e0f5f`.
- Review package:
  `build/feedback/USER-09-LIVE-ENCOUNTER-REVIEW-RENEWED`.
- Technical repair acceptance does not accept subjective weapon/no-weapon
  progression, AI, collision feel, or physical Saturn behavior.
