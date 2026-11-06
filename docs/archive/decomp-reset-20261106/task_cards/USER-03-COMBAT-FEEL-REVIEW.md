# USER-03-COMBAT-FEEL-REVIEW task card

TASK: USER-03-COMBAT-FEEL-REVIEW
KIND: USER_REVIEW
STATUS: ACCEPTED
CHECKPOINT: review-combat-feel
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 0
DEPENDENCIES: [INTEGRATE-02-COMBAT]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REPAIR-03-COMBAT-ACTOR-ALIGNMENT, PROMOTE-04-CAMERA-STAGE, ORACLE-01-FULL-REFERENCE-ROUTE, ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX, ORACLE-03-ENDING-CREDITS-DELTAS]

## Objective

Present self-reviewed combat evidence and wait for explicit feel feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-03-COMBAT-FEEL-REVIEW/**`
- Combat/user-feedback migration fields and review state only

## Existing systems to reuse

- Exact INTEGRATE-02 screenshot/clip, readback, profile/commit, systems, adaptations, and pacing notes.

## Systems deliberately disabled

- All combat or presentation changes.

## Focused machine checks

- Verify evidence identity, deterministic machine claims, and package completeness.

## Saturn build profile

Reuse exact `CombatIntegrationBench` image.

## Emulator readback

Reuse INTEGRATE-02 readback only.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record exact response and derived approvals/changes/priority.

## Exclusions

- No implementation or inferred approval.

## Hard stops

- Missing evidence or feedback; set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- A bounded combat `REPAIR` card if requested; otherwise
  `PROMOTE-04-CAMERA-STAGE`.
- The three read-only Oracle cards may proceed while pending because they cannot
  alter the reviewed combat result.

## Recorded feedback

- Exact observation: `Does it seem like the positioning of of the player and enemy is incorrect it misaligned?`
- Exact priority response: `ok let’s do that since it is a durable requirement unless it would be best to defer once other dependencies are satisfied that would rectify the misalignment`
- Derived requested change: correct player/enemy relative position, shared
  lane/ground alignment, and attack-facing relationship before dependent
  presentation promotion. No component approval is inferred.
- Disposition: `CHANGES_REQUESTED`; activate only
  `REPAIR-03-COMBAT-ACTOR-ALIGNMENT`.

## Repair return

- `REPAIR-03-COMBAT-ACTOR-ALIGNMENT` is accepted at
  `4abbc86f596c27d7873a96016c3e52c2d777edb4`.
- The ignored package was regenerated from that exact commit and normalized ISO
  `3c4096835741882f7a815483c47e37c9bcf2bfbb0ef3fb846ee2c20e67526b7b`.
- The regenerated package remained unapproved until the renewed response below.

## Renewed feedback

- Exact response: `much better lets keep going`
- Approved components: corrected source-relative player/enemy positioning and
  actor order; shared lane/ground baseline; attack-facing-toward-enemy
  relationship; and the shown corrected scale, palette, and readability.
- Requested changes: none.
- Priority: continue with `PROMOTE-04-CAMERA-STAGE`.
- Scope boundary: second and third HIT reaction timing, general attack/damage
  rules, enemy AI, combat audio, normal release, a second emulator, and
  physical Saturn remain unpromoted or `UNRUN`.
- Disposition: `ACCEPTED`; activate only `PROMOTE-04-CAMERA-STAGE`.
