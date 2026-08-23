# INTEGRATE-03-PLAYABLE-SLICE task card

TASK: INTEGRATE-03-PLAYABLE-SLICE
KIND: INTEGRATE
STATUS: READY
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

## Current candidate checkpoint

- Candidate implementation: `3273779516051a6b6f62719bc0bdceef07655310`.
- Exact `release-normal-release` ISO repeat:
  `8a3cecba96d5fbe2b891bb8abe2d2df36b4f26e3d8c3f8a4dc64998244586129`.
- Host deterministic repeat, real negative controls, Fast, exact release build,
  and paired pinned-emulator semantic/readback review pass.
- Clean integrated HIT and KO frames retain the approved player/enemy alignment,
  camera/stage, P1/P2 HUD, PCM, and CDDA locks with zero fallback, late-read, or
  canary failures.
- Physical Saturn is `UNRUN`; emulator and user review are not physical proof.
- Required Full is blocked by generator drift in three artifacts outside this
  card's owned paths: `data/avsp_palette_coverage.json`,
  `data/avsp_translation_boundary.json`, and
  `data/avsp_vertical_slice_oracle_manifest.json`.
- The final integrated subjective checkpoint is pending. Do not activate
  `SALVAGE-08-FRONTEND` until the checkpoint, Full lane, and physical procedure
  are complete.

### Review correction 1

Exact user feedback:

> I don’t see a contact or hit just the alien and player loads camera pans
> animation of window breaking happens. They don’t engage in combat.

Disposition: `CHANGES_REQUESTED`. The semantic events passed, but the original
human-review presentation exposed each attack for only about 0.4 seconds and
then held the final KO indefinitely. Correct the Saturn review timeline to give
the approach, attack, HIT reaction, and KO durable visible holds without
changing the measured combat events or approved presentation/audio locks.
