# USER-09-LIVE-ENCOUNTER-REVIEW task card

TASK: USER-09-LIVE-ENCOUNTER-REVIEW
KIND: USER_REVIEW
STATUS: CHANGES_REQUESTED
CHECKPOINT: review-live-encounter
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REPAIR-10-LIVE-PLAYER-PRESENTATION]

## Objective

Present the first live one-player encounter and obtain explicit playability
feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-09-LIVE-ENCOUNTER-REVIEW/**`
- Exact feedback, approval locks, review/migration/coverage state, and this card

## Existing systems to reuse

- Source reference clip; Saturn interactive clip; controller/input trace;
  player action timing; enemy decision trace; collision overlays; player and
  alien damage/HIT/KO chronology; encounter clear; active/disabled systems;
  and measured/adapted/unknown classification from INTEGRATE-04A.

## Systems deliberately disabled

- All implementation, gameplay, AI, presentation, frontend, route, evidence,
  emulator, and physical-status changes.

## Focused machine checks

- Verify package/candidate identity and completeness only; confirm the review
  is interactive-input evidence and remains distinct from physical proof.

## Saturn build profile

Reuse the exact INTEGRATE-04A-reviewed image; do not rebuild behavior.

## Emulator readback

Reuse INTEGRATE-04A evidence only; create no new acceptance tier.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"
Judge responsiveness, combat cadence, enemy behavior, contact readability,
encounter flow, and overall arcade feel. Record the exact response and remain
`AWAITING_USER_FEEDBACK` until received. Silence is not approval.

## Exclusions

- No implementation, inferred approval, physical proof, frontend activation,
  or complete Round 1 claim.

## Hard stops

- Missing/mismatched source or Saturn package, noninteractive evidence, absent
  traces/chronology, or pending user feedback.

## Next eligible cards

- `SALVAGE-08-FRONTEND` only after explicit acceptance; otherwise one bounded
  correction card for the issue chosen first.

## Recorded feedback

Exact response:

> the character sprite is faving the wrong way with certain walking firectios.  attack sprites seem randomply selected such as weapon to no weapon to no weapon. impact works but the ai  and collosion between player and alien seem off. I'm not sure if these need to work at this point.&#x20;

Disposition: `CHANGES_REQUESTED`. Facing and attack-presentation coherence are
first priority in `REPAIR-10-LIVE-PLAYER-PRESENTATION`. AI and player/alien
collision are also required for the R7B first-live-encounter exit and remain
explicitly unresolved; they are not waived by the first bounded repair.
