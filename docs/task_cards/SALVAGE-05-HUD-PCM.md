# SALVAGE-05-HUD-PCM task card

TASK: SALVAGE-05-HUD-PCM
KIND: SALVAGE
STATUS: BLOCKED
CHECKPOINT: salvage-hud-pcm
BASE: project_state.accepted_head
BRANCH: codex/avp-salvage-05-hud-pcm
TIER: 1
DEPENDENCIES: [SALVAGE-00-OLD-BUILD-BASELINE]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-05-HUD-PCM-REVIEW]

## Objective

Bench HUD and one short PCM cue independently and together over fixed semantic state, without CDDA or combat changes.

## Owned paths

- `tests/port_v2/hud_pcm_bench/**`
- Card-scoped HUD/PCM diagnostic/readback and test assets
- HUD/PCM migration entries, state, and card

## Existing systems to reuse

- Existing HUD assets/palette/rendering, PCM preparation/playback, diagnostics, and source timing evidence.

## Systems deliberately disabled

- CDDA, loading-phase redesign, combat changes, camera movement, and stage expansion.

## Focused machine checks

- Strict compile; zero/mid/full HUD; fixed PCM trigger; deterministic repeat; missing HUD asset and invalid/missing PCM controls; timing/stability readback.

## Saturn build profile

Dedicated `HudPcmSalvageBench` diagnostic.

## Emulator readback

Require runtime-ready, asset/audio failure, HUD state/render count, PCM event/start/end/underrun, and bounded stability.

## Human-review requirement

Required after AI self-review through `USER-05-HUD-PCM-REVIEW`.

## Exclusions

- No CDDA ownership, production promotion, or inferred audio approval.

## Hard stops

- Missing source/audio evidence, material SCSP ownership decision, or exhausted correction cycle.

## Next eligible cards

- `USER-05-HUD-PCM-REVIEW`.
