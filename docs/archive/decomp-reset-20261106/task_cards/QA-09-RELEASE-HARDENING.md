# QA-09-RELEASE-HARDENING task card

TASK: QA-09-RELEASE-HARDENING
KIND: QA
STATUS: BLOCKED
CHECKPOINT: qa-release-hardening
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-07-THREE-PLAYER-MULTIPLAYER]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [QA-10-FINAL-TITLE-TO-CREDITS-ACCEPTANCE]

## Objective

Harden repeatable clean builds and the complete cold-boot/full-route,
worst-workload, audio, controller, loader, and long-soak matrix.

## Owned paths

- Release QA fixtures/reports/manifests, coverage state, and card; no new gameplay.

## Existing systems to reuse

- Accepted four-character, three-player production line and all exact manifests.

## Systems deliberately disabled

- Feature implementation, source approximation, and release-scope expansion.

## Focused machine checks

- Repeated clean builds, artifact hashes, every route/character/player matrix,
  worst workloads, canaries, negative controls, and long deterministic replays.

## Saturn build profile

Exact `release-normal-release` only.

## Emulator readback

Complete semantic/resource/render/scanout/audio/route/fallback/timing readback.

## Human-review requirement

Confirm all required component-scoped reviews exist; do not infer missing approval.

## Exclusions

- No implementation correction without a new bounded repair card.

## Hard stops

- Any crash, fallback, canary, draw-end, late-read, missed-field, audio-loss,
  provenance, or physical soak failure.

## Next eligible cards

- `QA-10-FINAL-TITLE-TO-CREDITS-ACCEPTANCE`.
