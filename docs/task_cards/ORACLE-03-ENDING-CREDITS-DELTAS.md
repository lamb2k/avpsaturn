# ORACLE-03-ENDING-CREDITS-DELTAS task card

TASK: ORACLE-03-ENDING-CREDITS-DELTAS
KIND: ORACLE
STATUS: BLOCKED
CHECKPOINT: oracle-ending-credits-deltas
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-06-FOUR-CHARACTER-ROSTER]

## Objective

Capture final boss through credits for each character and classify only
measured common, Predator-shared, human-shared, and character-specific content.

## Owned paths

- Card-scoped MAME inputs/captures, ending/credits fixtures, ending matrix,
  private raw evidence, coverage fields, state, and card only

## Existing systems to reuse

- Pinned MAME capture/provenance tools and the measured four-character identities.

## Systems deliberately disabled

- Ending implementation, Saturn scenes/assets/audio, and route code changes.

## Focused machine checks

- Two deterministic runs per character body, transition/content/audio identity,
  cross-character comparison, and one ending/input perturbation control.

## Saturn build profile

None. MAME/host evidence only.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; presentation review occurs after implementation.

## Exclusions

- No inferred shared topology and no stopping before the credits transition.

## Hard stops

- Missing final-route access, nondeterminism, ambiguous identity, or missing evidence.

## Next eligible cards

- `INTEGRATE-06-FOUR-CHARACTER-ROSTER` after the reference game.
