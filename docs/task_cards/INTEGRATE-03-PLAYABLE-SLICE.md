# INTEGRATE-03-PLAYABLE-SLICE task card

TASK: INTEGRATE-03-PLAYABLE-SLICE
KIND: INTEGRATE
STATUS: BLOCKED
CHECKPOINT: integrate-playable-slice
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-02-COMBAT, USER-03-COMBAT-FEEL-REVIEW, PROMOTE-04-CAMERA-STAGE, PROMOTE-05-HUD, PROMOTE-06-PCM, PROMOTE-07-CDDA-RESIDENCY]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-08-FRONTEND]

## Objective

Integrate promoted player, enemy, combat, camera/stage, HUD, PCM, CDDA, and
phase residency into the exact playable capability slice and close the required
physical Saturn capability conditions.

## Owned paths

- `src/port_v2/integration/slice/**`
- `tests/port_v2/integration/slice/**`
- Card-scoped release wiring/readback, migration ledger, state, and card

## Existing systems to reuse

- Only promoted components, exact source evidence, and accepted phase manifests.

## Systems deliberately disabled

- Frontend/full-route content, roster, multiplayer, and generalized engine work.

## Focused machine checks

- Strict compile; all approved locks; deterministic replay; illegal CDDA read,
  canary/asset, and dependency-order controls; Oracle, exact normal-release
  Target/emulator, Full, and the declared physical procedure.

## Saturn build profile

Dedicated integration profiles during iteration; exact `release-normal-release` for checkpoint acceptance.

## Emulator readback

Require semantic, resource, render, final-scanout, PCM/CDDA ownership, high-water/canary, fallback, frame-pacing, and stability domains bound to exact image/profile.

## Human-review requirement

Renew review for any approved component at risk. A final integrated subjective
checkpoint precedes physical testing; explicit user approval is not physical proof.

## Exclusions

- No physical claim from host/emulator results and no silent approval drift.

## Hard stops

- Any approved regression, illegal ownership, missing exact evidence, material architecture decision, or exhausted correction cycle.

## Next eligible cards

- `SALVAGE-08-FRONTEND` only after the physical capability slice is accepted.
