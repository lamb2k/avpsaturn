# INTEGRATE-03-PLAYABLE-SLICE task card

TASK: INTEGRATE-03-PLAYABLE-SLICE
KIND: INTEGRATE
STATUS: BLOCKED
CHECKPOINT: integrate-playable-slice
BASE: project_state.accepted_head
BRANCH: codex/avp-integrate-03-playable-slice
TIER: 2
DEPENDENCIES: [INTEGRATE-02-COMBAT, USER-03-COMBAT-FEEL-REVIEW, SALVAGE-04-CAMERA-STAGE-LAYERS, USER-04-STAGE-REVIEW, SALVAGE-05-HUD-PCM, USER-05-HUD-PCM-REVIEW]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full]
OPTIONAL_LANES: [Physical]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: []

## Objective

Integrate approved player, enemy, combat, camera/stage, HUD, and PCM components, then add loading phases, CDDA ownership, residency, and canaries one component at a time.

## Owned paths

- `src/port_v2/integration/slice/**`
- `tests/port_v2/integration/slice/**`
- Card-scoped release wiring/readback, migration ledger, state, and card

## Existing systems to reuse

- Only promoted or explicitly approved components and exact source evidence.

## Systems deliberately disabled

- Full-route content, roster, multiplayer, generalized engine work, and physical acceptance until prerequisites pass.

## Focused machine checks

- Strict compile; all approved regression locks; deterministic slice replay; illegal CDDA data-read and canary/asset perturbation controls; Oracle, exact normal-release Target/emulator, and Full at acceptance.

## Saturn build profile

Dedicated integration profiles during iteration; exact `release-normal-release` for checkpoint acceptance.

## Emulator readback

Require semantic, resource, render, final-scanout, PCM/CDDA ownership, high-water/canary, fallback, frame-pacing, and stability domains bound to exact image/profile.

## Human-review requirement

Renew review for any approved component at risk. A final integrated subjective checkpoint precedes physical testing.

## Exclusions

- No physical claim from host/emulator results and no silent approval drift.

## Hard stops

- Any approved regression, illegal ownership, missing exact evidence, material architecture decision, or exhausted correction cycle.

## Next eligible cards

- R8 physical capability-slice card only after exact normal-release checkpoint acceptance.
