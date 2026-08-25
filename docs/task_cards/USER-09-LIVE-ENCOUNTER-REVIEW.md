# USER-09-LIVE-ENCOUNTER-REVIEW task card

TASK: USER-09-LIVE-ENCOUNTER-REVIEW
KIND: USER_REVIEW
STATUS: CHANGES_REQUESTED
CHECKPOINT: review-live-encounter
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REPAIR-11-LIVE-BACKGROUND-PRESENTATION, SALVAGE-08-FRONTEND]

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

Reuse the exact QA-12-reviewed image; do not rebuild behavior.

## Emulator readback

Reuse QA-12 evidence only; create no new acceptance tier.

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

- `SALVAGE-08-FRONTEND` only after explicit acceptance; otherwise the bounded
  source-closure sequence beginning with
  `ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT`.

## Recorded feedback

Exact response:

> the character sprite is faving the wrong way with certain walking firectios.  attack sprites seem randomply selected such as weapon to no weapon to no weapon. impact works but the ai  and collosion between player and alien seem off. I'm not sure if these need to work at this point.&#x20;

Disposition: `CHANGES_REQUESTED`. Facing and attack-presentation coherence are
first priority in `REPAIR-10-LIVE-PLAYER-PRESENTATION`. AI and player/alien
collision are also required for the R7B first-live-encounter exit and remain
explicitly unresolved; they are not waived by the first bounded repair.

REPAIR-10 is technically accepted at
`4ea7c1829013e95b5ffdc34ef02ea5c133ee9a80`; renewed review now uses
`build/feedback/USER-09-LIVE-ENCOUNTER-REVIEW-RENEWED`. This wait state asks
whether facing is corrected and whether the weapon/no-weapon progression still
feels random. AI and collision remain known unresolved issues even if the
player-presentation repair is accepted.

## Source-closure course correction

Exact response:

> The current live encounter is a useful technical prototype, but it is not yet
> a faithful reproduction. The alien faces the wrong direction during some walk
> or attack states. Player attack presentation changes incoherently between
> weapon and no-weapon assemblies. The player can move through non-walkable wall
> or stage areas. The resulting player, AI, animation, and navigation systems
> feel disconnected from the original game. The next work must lift more
> confirmed source logic rather than repair isolated visible symptoms.

Disposition: `CHANGES_REQUESTED`, `NOT_USER_APPROVED`. The current live
encounter is retained as a `TECHNICAL_PROTOTYPE` and
`ADAPTED_GAMEPLAY_SCAFFOLD`; it is `NOT_SOURCE_CLOSED`. REPAIR-10 remains useful
bounded work, but isolated visible symptom repair is no longer the active path.

The required serial path is ORACLE-07, ORACLE-08, ORACLE-09, SPEC-01,
REIMPLEMENT-12, QA-12, and only then renewed USER-09. `SALVAGE-08-FRONTEND`
remains blocked. Physical Saturn remains `UNRUN`.

## Renewed review activation

QA-12 is accepted at `f99df5e1ece90694f17942796e32da2ddf855d42`
against exact gameplay candidate
`e23733545af0bebe1f9ae26c4f391a9080c7006f` and diagnostic ISO SHA-256
`8e20cb7e8c482035578422d8d1734cd9713adfc525ac5bf7c6dd8eade386bea8`.
The renewed review reuses that QA-reviewed behavior without rebuilding it.

The renewed launch entered `AWAITING_USER_FEEDBACK`; no acceptance was inferred
from QA, emulator output, images, silence, or prior approvals. Frontend
activation and physical-status promotion remained disabled. The required
question was asked exactly before the feedback below was received.

## Renewed review feedback

Exact responses, in order:

> the background looks correupted.&#x20;

> also confirm the attack animation sequence is correct. also the player resets to opposite direction when the key is supressed. overall this feels a bit more faithful . the alien ai also tracks the player

Disposition: `CHANGES_REQUESTED`, `NOT_USER_APPROVED`. The reviewed attack
animation sequence is correct and becomes a preservation lock. The observed
class-`0x1F` player tracking also becomes a preservation lock. "Overall this
feels a bit more faithful" is positive feedback but is not blanket approval.

The corrupted background is the first bounded repair because it was reported
first. The neutral sprite reversing after directional release is recorded and
remains unresolved for the following review/repair. Activate only
`REPAIR-11-LIVE-BACKGROUND-PRESENTATION`; keep frontend inactive and physical
Saturn `UNRUN`.
