# REPAIR-01-PLAYER-CROP-PIVOT task card

TASK: REPAIR-01-PLAYER-CROP-PIVOT
KIND: REPAIR
STATUS: ACCEPTED
CHECKPOINT: repair-player-crop-pivot
BASE: project_state.accepted_head
BRANCH: codex/avp-repair-01-player-crop-pivot
TIER: 1
DEPENDENCIES: [SALVAGE-01-PLAYER-LOAD-RENDER-INPUT]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-01-PLAYER-BASELINE-REVIEW, SALVAGE-02-ENEMY-RENDER-ANIMATION]

## Objective

Repair only the user-observed cropped player sprite by correcting the player cel/pivot placement, while preserving the verified loading, input, movement, animation cadence, palette, command count, and fixed-background baseline.

## Owned paths

- `main.c` player-bench draw/pivot path only
- `tools/extract_avspu_stage1.py` grounded player idle/walk pivot and crop-rejection path only
- `tests/port_v2/player_bench/**`
- Regenerated player cel/archive payloads and card-scoped diagnostic/readback under ignored `build/**`
- Ignored `build/feedback/REPAIR-01-PLAYER-CROP-PIVOT/**`
- Player-rendering migration-ledger entry and card/state/handoff updates

## Existing systems to reuse

- Exact accepted SALVAGE-01 `PlayerSalvageBench` build, player assets, input path, movement bounds, animation scripts, palette path, VDP1 emission, deterministic ISO normalization, and pinned-emulator readback.
- USER-01 exact response: `the character sprite is cropped but moving.`

## Systems deliberately disabled

- Enemy, collision, damage, HIT/KO, camera movement, stage redesign, HUD, PCM, and CDDA.
- Player asset replacement, palette correction, animation retiming, input-feel changes, and background changes.

## Focused machine checks

- Touched-code strict compile and focused player render/pivot tests.
- Deterministic repeat of corrected player bounds, pivot, render count, command identity, ISO member hashes, and emulator readback.
- A real negative control that restores the rejected crop/pivot condition and must fail the full-visible-player assertion.
- Regression locks for accepted SALVAGE-01 loading, input edges, movement, animation cadence, palette, canary, zero late reads, and fixed background.

## Saturn build profile

Reuse the dedicated `PlayerSalvageBench` profile so corrected output remains directly comparable to USER-01 evidence.

## Emulator readback

Require runtime-ready, zero asset failures, intact canaries, zero late reads, player position/pose/pivot/render count, full visible player bounds for idle and walk, sampled right/down/left input edges, and bounded stability in the repository-pinned emulator.

## Human-review requirement

Return the corrected ignored package to `USER-01-PLAYER-BASELINE-REVIEW`; movement observation is not approval, and promotion remains blocked until explicit component-scoped approval.

## Exclusions

- No production-interface promotion or change outside the player crop/pivot correction.
- No claim of physical Saturn proof; physical validation remains `UNRUN`.

## Hard stops

- The crop cannot be corrected without changing player assets, palette, animation cadence, input behavior, background composition, or renderer architecture.
- Deterministic bounds/readback cannot distinguish corrected output from the rejected pivot, the bounded correction cycle is exhausted, or the protected worktrees are unsafe.

## Next eligible cards

- `USER-01-PLAYER-BASELINE-REVIEW` with a new ignored corrected package.
- `SALVAGE-02-ENEMY-RENDER-ANIMATION` remains dependency-safe because it cannot alter the player result.

## Accepted result

- Evaluated commit: `76e497b1bcadc2b4ff8326bc855f7cef1bc7d336`.
- Fast lane, focused contract, rejected-pivot negative control, two clean Target builds, paired pinned-emulator readback, and paired evidence validation: `PASS`.
- Corrected idle bounds: `(56,74)-(136,184)`; sampled walk bounds: `(28,88)-(152,184)`; rejected idle bottom: `232`.
- Normalized repeat ISO SHA-256: `7a9326d08607813fb88fb969de5f8f92b233649575e694b742e87141c6f28ef6`.
- User status: `AWAITING_USER_FEEDBACK`; production interface: none; physical Saturn: `UNRUN`.
