# QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL task card

TASK: QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL
KIND: QA
STATUS: READY
CHECKPOINT: qa-live-encounter-source-differential
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: [Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-09-LIVE-ENCOUNTER-REVIEW]

## Objective

Run the complete source/Saturn scenario matrix for movement, every relevant
boundary, reversal/crossing, all bounded attacks/equipment states, misses and
contacts, alien approach/steering/attack/HIT/KO, and camera lock/unlock.

## Owned paths

- QA-12 scenario inputs, differential/readback tools, tracked reports,
  ignored clips/strips/crops/overlays/timelines, this card, and review state

## Existing systems to reuse

- SPEC-01, the committed REIMPLEMENT-12 candidate, pinned MAME/Yaba, accepted
  target/readback/visual-QA infrastructure, and approved regression locks.

## Systems deliberately disabled

- Gameplay implementation, post-QA decoration, frontend, later stages,
  multiplayer, physical-status changes, and approval from counters alone.

## Focused machine checks

- Cadence-1 per-frame input/state/substate/equipment/facing/animation/assembly,
  world/screen position, navigation, boxes/collision/damage/route comparison.
- Directly inspect full-speed clips, temporal strips, actor crops, facing and
  weapon continuity, navigation/collision overlays, and state timelines.
- Automatically reject wrong facing, unsourced equipment discontinuity, wall
  traversal, state/animation disagreement, family substitution, stale pose,
  unsupported contact/damage, or missing rendered transition.

## Saturn build profile

Reuse the exact committed REIMPLEMENT-12 diagnostic and normal interactive
images; do not rebuild a different gameplay candidate during acceptance.

## Emulator readback

Paired cold semantic and visual runs plus the complete consistency matrix;
one screenshot or one ledger is insufficient.

## Human-review requirement

After QA acceptance, renew USER-09 and ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"

## Exclusions

- No inferred user approval, frontend activation, physical proof, or acceptance
  with unresolved objective discrepancy.

## Hard stops

- Any automatic-fail condition, unresolved objective discrepancy, missing
  scenario/evidence view, nondeterminism, or candidate identity mismatch.

## Next eligible cards

- Renewed `USER-09-LIVE-ENCOUNTER-REVIEW` only after the full matrix passes.
