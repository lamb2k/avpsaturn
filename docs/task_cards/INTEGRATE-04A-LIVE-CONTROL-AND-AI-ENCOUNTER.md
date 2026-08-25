# INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER task card

TASK: INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER
KIND: INTEGRATE
STATUS: ACCEPTED
CHECKPOINT: integrate-live-control-ai-encounter
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-03-PLAYABLE-SLICE, ORACLE-06-ROUND1-ENCOUNTER-RULES, PROMOTE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER, PROMOTE-11-STREET-ALIEN-AI]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-09-LIVE-ENCOUNTER-REVIEW]

## Objective

Integrate real controller input, the promoted Predator Warrior action
controller, promoted class-`0x1F` AI, exact collision/damage and HIT/KO, one
measured encounter controller, and the approved stage/camera, HUD, PCM/CDDA,
loading, and residency into `FIRST LIVE GAMEPLAY ENCOUNTER`.

The free-running player must approach/retreat, change lanes, choose when to
attack, miss, contact, receive an enemy attack, damage/KO the alien, clear the
encounter, regain stage progression, and continue moving. The enemy must react
to current game state rather than a predetermined review timeline.

## Owned paths

- Future live-encounter integration core/adapters and focused tests
- Card-scoped deterministic ledgers, Target/readback, review package,
  migration/coverage state, and this card

## Existing systems to reuse

- Promoted player action and class-`0x1F` AI, ORACLE-06 rules, exact collision/
  damage/HIT/KO, and every approved rendering, stage, HUD, audio, residency,
  canary, zero-late-read, and fallback lock.

## Systems deliberately disabled

- Fixed-frame contact, damage without current overlap, teleported contact,
  event-count-only attack choice, presentation-owned positions/outcomes,
  scripted enemy timing without source AI state, frontend, roster, multiplayer,
  later encounters, bosses, and full route.

## Focused machine checks

- Source differential and counterfactual controls; deterministic host repeat;
  real ledger choices including misses and received attacks; fixed-frame,
  no-overlap, teleported-contact, event-count, presentation-override, and
  scripted-AI mutations; synchronized action/AI/collision trace; no regression.

## Saturn build profile

Dedicated live-encounter integration profile, then exact Target candidate.

## Emulator readback

Require paired emulator runs, image-based visual QA, synchronized input/player/
AI/collision/damage/HIT/KO/encounter trace, route unlock/continued movement,
resource/audio/fallback/canary state, and bounded stability.

## Human-review requirement

Required through `USER-09-LIVE-ENCOUNTER-REVIEW` using real interactive input;
deterministic ledgers alone do not approve playability.

## Exclusions

- No result emitted merely because a fixed frame was reached; no complete move
  set, other enemy, boss, multiplayer, frontend, or complete Round 1 claim.

## Hard stops

- Any scripted authority survives, current overlap/state cannot explain a
  result, source mismatch, approved regression, instability, or material architecture decision.

## Next eligible cards

- `USER-09-LIVE-ENCOUNTER-REVIEW`.

## Accepted technical result

- Implementation/evidence head: `d9021965dab64d47953d2e829c7d307b0b01a455`.
- Paired post-commit Yaba reads match across an exact 448-frame ledger and
  prove current-state input, AI, collision/damage, HIT/KO, target-KO-then-
  inactivity clear, route unlock, and continued movement with zero failures,
  fallbacks, or canary faults.
- Diagnostic ISO SHA-256: `3246659a2538ac6650a033a4fb0fa6d3795c6be40289a606383348ff747938c5`.
- Exact interactive ISO SHA-256: `ae65359601d56e5fbee82c94eb66acfd12ed8c842d95b8f7a63e51d78bca7a8a`.
- Genuine Windows Graphics Capture visual QA shows the intact Coffee Shop
  stage and live combat at frame 181. Physical Saturn remains `UNRUN`.
- Playability is not accepted here; it is awaiting explicit `USER-09` review.
