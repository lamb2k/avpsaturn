# REPAIR-05-HUD-COLORS task card

TASK: REPAIR-05-HUD-COLORS
KIND: REPAIR
STATUS: READY
CHECKPOINT: repair-hud-colors
BASE: project_state.accepted_head
BRANCH: codex/avp-repair-05-hud-colors
TIER: 1
DEPENDENCIES: [SALVAGE-05-HUD-PCM]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-05-HUD-PCM-REVIEW]

## Objective

Repair only the user-observed broken HUD colors by correcting HUD palette/CRAM ownership or color binding while preserving the approved PCM cue and every accepted stage/player lock.

## Owned paths

- `main.c` HUD-bench palette/CRAM and HUD draw path only
- `tests/port_v2/hud_pcm_bench/**`
- Card-scoped HUD palette evidence/readback and ignored `build/feedback/USER-05-HUD-PCM-REVIEW/**`
- HUD migration-ledger entry and card/state/handoff updates

## Existing systems to reuse

- Exact accepted SALVAGE-05 `HudPcmSalvageBench`, HUD assets, semantic states, normalized-disc workflow, diagnostics, and pinned-emulator readback.
- Approved `/AUDIO/MELEE.PCM` payload SHA-256 `e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125` and event/start/end timing `147/150/200`.
- USER-05 exact response: `sound is great hud looks broken in terms of colors`.

## Systems deliberately disabled

- PCM payload, SCSP format, cue timing, event behavior, and audio presentation changes.
- Player, enemy, collision, combat, camera, stage, CDDA, loading-phase, and production-integration changes.

## Focused machine checks

- Touched-code strict compile and focused HUD palette/CRAM/color-binding checks against source HUD evidence.
- Deterministic repeat of corrected zero/mid/full HUD colors, values, fills, render counts, asset hashes, normalized ISO, and emulator readback.
- A real negative control that restores the rejected palette/bank/color binding and must fail the HUD color assertion.
- Regression locks for the approved PCM payload/timing and accepted stage/player assets, canaries, zero late reads, and disabled-system boundaries.

## Saturn build profile

Reuse the dedicated `HudPcmSalvageBench` profile so corrected HUD output remains directly comparable to USER-05 evidence.

## Emulator readback

Require runtime-ready; zero HUD/audio failures, PCM underruns, and late reads; intact canaries; exact zero/mid/full HUD state and color ownership; approved PCM payload/timing lock; final 352x224 scanout; and bounded stability in the repository-pinned emulator.

## Human-review requirement

Return the corrected ignored package to `USER-05-HUD-PCM-REVIEW`. The PCM cue is approved and locked; HUD presentation requires renewed explicit approval.

## Exclusions

- No HUD production-interface promotion, broader HUD redesign, audio change, or integration.
- No claim of physical Saturn proof; physical validation remains `UNRUN`.

## Hard stops

- Source HUD color evidence is missing or contradictory.
- Correcting colors requires a material CRAM/renderer architecture change or risks the approved PCM, stage, or player presentation.
- The negative control cannot distinguish corrected output, the bounded correction cycle is exhausted, or a protected worktree is unsafe.

## Next eligible cards

- `USER-05-HUD-PCM-REVIEW` with a corrected ignored screenshot and the unchanged approved PCM cue.
