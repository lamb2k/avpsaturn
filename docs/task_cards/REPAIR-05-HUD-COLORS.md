# REPAIR-05-HUD-COLORS task card

TASK: REPAIR-05-HUD-COLORS
KIND: REPAIR
STATUS: ACCEPTED
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

## Result

- Technical result: `PASS` at `949316331c7c12a9ae630ef5f5ebc846e4d2aef5`.
- Corrected the one-entry HUD palette shift: source index 1 now binds to Jo/CRAM palette entry 0 for one-based HUD texels.
- Paired clean target builds produced identical normalized ISO SHA-256 `6218e3d1e745552f6c64ef16f7c66cc044abc04772634f36ebefa9888e45a10d`.
- Both pinned-emulator runs read exact CRAM values yellow `0x83ff`, red `0x801f`, energy `0xbbf7`, and empty `0xc631`, with palette binding `PASS`.
- Four runtime negative controls passed, including reconstruction and rejection of the original zero-based palette binding.
- HUD assets, semantic values/fills, canaries, zero late reads, approved stage/player locks, and bounded 486-frame repeat remained stable.
- Approved PCM payload SHA-256 `e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125` and event/start/end timing `147/150/200` remained unchanged.
- Corrected ignored package: `build/feedback/USER-05-HUD-PCM-REVIEW/`; physical Saturn remains `UNRUN`.
- Successor: `USER-05-HUD-PCM-REVIEW`, awaiting renewed explicit feedback.
