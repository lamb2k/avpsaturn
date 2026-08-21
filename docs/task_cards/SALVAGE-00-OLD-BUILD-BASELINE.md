# SALVAGE-00-OLD-BUILD-BASELINE task card

TASK: SALVAGE-00-OLD-BUILD-BASELINE
KIND: SALVAGE
STATUS: READY
CHECKPOINT: salvage-old-build-baseline
BASE: project_state.accepted_head
BRANCH: codex/avp-salvage-00-old-build-baseline
TIER: 1
DEPENDENCIES: []
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-01-PLAYER-LOAD-RENDER-INPUT, SALVAGE-02-ENEMY-RENDER-ANIMATION, SALVAGE-03-COLLISION, SALVAGE-04-CAMERA-STAGE-LAYERS, SALVAGE-05-HUD-PCM]

## Objective

Preserve and reproduce the old-build baseline, inventory major subsystems and ownership, and establish diagnostic/emulator controls without changing production behavior.

## Owned paths

- `data/port_v2_migration_map.yaml`
- `tests/port_v2/old_build_baseline/**`
- Card-scoped diagnostic/readback additions only
- `project_state.yaml` and this card for disposition/activation

## Existing systems to reuse

- Existing `build.ps1`, makefile, profiles, manifests, diagnostics, readback, and pinned emulator.
- Read-only inspection of canonical, prototype, and V2-2B worktrees.

## Systems deliberately disabled

- New gameplay, rendering, asset, audio, loading, or production `port_v2` behavior.
- Writes to the dirty canonical, playable-skeleton, and V2-2B worktrees.

## Focused machine checks

- Strict compile of touched test/diagnostic code.
- Two deterministic baseline builds/readbacks.
- Invalid-disc or deliberately missing required-member negative control.
- Verify no protected worktree status changed.

## Saturn build profile

A dedicated `OldBuildBaseline` diagnostic profile; do not relabel it normal release.

## Emulator readback

Require build/profile/commit identity, runtime-ready, asset-failure, profile, manifest, and bounded stability fields from the pinned emulator.

## Human-review requirement

None for this card. If the bench exposes subjective output, stop and activate a predeclared USER_REVIEW card; do not infer approval.

## Exclusions

- No salvage decision for a subsystem not exercised by this card.
- No Oracle, Full, normal-release, or physical acceptance claim.

## Hard stops

- Any protected-worktree mutation, non-reproducible baseline, missing pinned emulator/input, material build architecture decision, or exhausted bounded correction cycle.

## Next eligible cards

- `SALVAGE-01-PLAYER-LOAD-RENDER-INPUT`
- `SALVAGE-02-ENEMY-RENDER-ANIMATION`
- `SALVAGE-03-COLLISION`
- `SALVAGE-04-CAMERA-STAGE-LAYERS`
- `SALVAGE-05-HUD-PCM`
