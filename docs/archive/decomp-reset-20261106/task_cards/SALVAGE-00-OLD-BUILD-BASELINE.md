# SALVAGE-00-OLD-BUILD-BASELINE task card

TASK: SALVAGE-00-OLD-BUILD-BASELINE
KIND: SALVAGE
STATUS: ACCEPTED
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

## Disposition evidence

- Evaluated commit: fcb7eaf0c3e6af28394908c251056daca7fb62c2
- Technical: PASS
- Fidelity: MEASURED, not accepted
- User: NOT_REVIEWED; unsolicited observations are preserved verbatim in
  build/feedback/SALVAGE-00-OLD-BUILD-BASELINE/observation.json
- Salvage: SALVAGE_WITH_ADAPTER
- Deterministic build repeat: PASS
- Invalid-disc negative control: PASS
- Pinned-emulator MCP repeat: PASS
- Physical Saturn: UNRUN
- Regression lock: ISO
  3649d96db8c4c46ba07af07c20754c60f70b441afde637d14590f1a18b5b45e7,
  phase 20, frames 3551/4768, SCX [0, 7], objects 477, asset
  failures 0, late reads 0 on both fresh boots.
- Visual blocker: automated window captures are black; the user's
  contemporaneous emulator screenshot shows distorted enemy pixels and does
  not grant visual acceptance.
- Activation: accepted as a technical baseline; SALVAGE-01 is active because
  its declared scope cannot alter the observed enemy or camera result.
- Exact next experiment: run SALVAGE-01's isolated player bench while retaining
  this MCP readback as a regression lock and deferring enemy-pixel corruption
  to SALVAGE-02.

## Next eligible cards

- `SALVAGE-01-PLAYER-LOAD-RENDER-INPUT`
- `SALVAGE-02-ENEMY-RENDER-ANIMATION`
- `SALVAGE-03-COLLISION`
- `SALVAGE-04-CAMERA-STAGE-LAYERS`
- `SALVAGE-05-HUD-PCM`
