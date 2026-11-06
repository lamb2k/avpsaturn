# ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX task card

TASK: ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX
KIND: ORACLE
STATUS: BLOCKED
CHECKPOINT: oracle-four-character-actions
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-06-FOUR-CHARACTER-ROSTER]

## Objective

Measure all four characters across idle, movement, lane movement, attacks,
weapons/projectiles, jump/dash/special, pickups/throws, HIT/KO, continue, and
character-specific state/resources.

## Owned paths

- Card-scoped MAME inputs/captures, derived action fixtures, the four-character
  matrix, private raw evidence, state, and card only

## Existing systems to reuse

- Measured four-identity select contract and pinned MAME capture/provenance tools.

## Systems deliberately disabled

- Player runtime expansion, character implementation, Saturn assets, and gameplay.

## Focused machine checks

- Two deterministic samples per matrix body, source-state/event binding, and
  one action/input perturbation that invalidates the expected record.

## Saturn build profile

None. MAME/host evidence only.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; later visible/feel implementations require character-scoped reviews.

## Exclusions

- No assumption that the promoted player subset belongs to or generalizes
  across any character before evidence binding.

## Hard stops

- Missing action reachability, nondeterministic capture, ambiguous character
  state, or missing private evidence.

## Next eligible cards

- `INTEGRATE-06-FOUR-CHARACTER-ROSTER` after the reference game.
