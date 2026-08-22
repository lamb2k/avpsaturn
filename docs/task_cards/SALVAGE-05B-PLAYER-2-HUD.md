# SALVAGE-05B-PLAYER-2-HUD task card

TASK: SALVAGE-05B-PLAYER-2-HUD
KIND: SALVAGE
STATUS: READY
CHECKPOINT: salvage-player-2-hud
BASE: project_state.accepted_head
BRANCH: codex/avp-salvage-05b-player-2-hud
TIER: 1
DEPENDENCIES: [SALVAGE-05-HUD-PCM, REPAIR-05-HUD-COLORS]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-05-HUD-PCM-REVIEW]

## Objective

Salvage the real active Player 2 HUD presentation and fixed semantic health/weapon states from `avspu`, render them in the dedicated Saturn HUD bench, and return a review package before any later tranche. This card does not implement Player 2 gameplay.

## Owned paths

- `main.c` HUD-bench-only Player 2 state, asset loading, palette-safe drawing, and diagnostics
- `tools/extract_avspu_stage1.py` Player 2 HUD extraction only
- One card-scoped deterministic MAME Player 2 HUD capture tool under `tools/**`
- `data/player2_hud_capture.json` and card-scoped tracked source-analysis evidence
- `tests/port_v2/player2_hud_bench/**` and minimal reuse updates under `tests/port_v2/hud_pcm_bench/**`
- Minimal diagnostic-profile wiring in `build.ps1`, `makefile`, and `verify.ps1` only if the existing `HudPcmSalvageBench` cannot isolate the required state
- Ignored `build/feedback/USER-05-HUD-PCM-REVIEW/**`
- HUD migration-ledger entry and card/state/handoff updates

## Existing systems to reuse

- Corrected one-based HUD palette binding and exact semantic CRAM values accepted at `949316331c7c12a9ae630ef5f5ebc846e4d2aef5`.
- Existing `HudPcmSalvageBench`, generated 8bpp HUD path, fixed P1 zero/mid/full states, pinned-emulator readback, and deterministic normalized-disc workflow.
- Approved PCM SHA-256 `e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125`, event/start/end timing `147/150/200`, and cue WAV SHA-256 `db539742a1cb77e2364055a26781c7bf0f1499f24fae1191c8b3f693e7b987d0`.
- User priority responses: `what about player 2 hud?` and `Let’s do that before we move on`.

## Systems deliberately disabled

- Player 2 controller input, character selection, movement, animation, collision, combat, score ownership, joins/continues, multiplayer integration, and multitap topology.
- PCM payload/format/timing, CDDA, enemy, camera, stage, loading-phase, and production-interface changes.
- Any change to approved P1 player presentation or camera/stage presentation.

## Focused machine checks

- Bind the active Player 2 HUD pixels, palette indices, placement, and visible semantic fields to deterministic `avspu` source evidence.
- Exercise P2 zero/mid/full health and weapon states twice with exact render counts, bounds, asset hashes, CRAM values, canaries, and zero late reads.
- Retain the corrected P1 HUD color/readback contract and approved PCM payload/timing byte-for-byte.
- Run a real negative control that substitutes the existing blinking `PRESS START` prompt or wrong-side/P1 binding for the active P2 HUD and must fail.
- Reject missing P2 HUD assets and any capture or normalized-ISO identity drift.

## Saturn build profile

Reuse `HudPcmSalvageBench` when it can isolate the active P2 HUD without weakening existing evidence; otherwise add only a dedicated `Player2HudSalvageBench` diagnostic profile.

## Emulator readback

Require runtime-ready, exact active-P2 state and draw ownership, corrected semantic CRAM values, zero HUD/audio failures, unchanged PCM timing, intact canaries, zero late reads, 352x224 final scanout, bounded stability, and two byte-identical normalized builds in the repository-pinned emulator.

## Human-review requirement

Return the active P2 HUD plus the locked P1/PCM evidence to `USER-05-HUD-PCM-REVIEW`. Do not infer approval from machine or emulator evidence.

## Exclusions

- No claim that multiplayer gameplay, a second controller, three-player parity, normal release, or physical Saturn is proven.
- No HUD production-interface promotion or general multiplayer architecture.

## Hard stops

- Deterministic source evidence cannot distinguish an active P2 HUD from the join prompt or cannot bind its semantic fields.
- Source activation requires unavailable input topology or physical interaction.
- P2 HUD salvage requires changing approved P1 palette/presentation, PCM, or stage/player locks.
- A material multiplayer state architecture decision is required, the real negative control cannot distinguish the wrong binding, or the bounded correction cycle is exhausted.

## Next eligible cards

- `USER-05-HUD-PCM-REVIEW` with active Player 2 HUD evidence and unchanged P1/PCM locks.
