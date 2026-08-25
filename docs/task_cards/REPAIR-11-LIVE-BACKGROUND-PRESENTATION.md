# REPAIR-11-LIVE-BACKGROUND-PRESENTATION task card

TASK: REPAIR-11-LIVE-BACKGROUND-PRESENTATION
KIND: REPAIR
STATUS: READY
CHECKPOINT: repair-live-background-presentation
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL]
REQUIRED_LANES: [Fast, Target, Emulator]
OPTIONAL_LANES: [Oracle, Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-09-LIVE-ENCOUNTER-REVIEW]

## Objective

Correct only the renewed USER-09 background corruption: bridge the live
encounter camera from source world space into the two captured VDP2 plane
coordinate spaces before submitting scroll positions. Preserve the reviewed
attack animation sequence, player-tracking class-`0x1F` AI, all gameplay
semantics, and every prior presentation lock.

## Owned paths

- `main.c` live-encounter stage/camera bridge only
- Focused stage-bridge checks under `tests/port_v2/integration/live_encounter/**`
- This card, USER-09 feedback, state, roadmap, handoff, migration, and coverage
  ledgers
- Ignored `build/feedback/REPAIR-11-LIVE-BACKGROUND-PRESENTATION/**`

## Existing systems to reuse

- The exact RP4 street-plane transform, captured scroll2/scroll3 relationship,
  384-to-352 source mapping, VDP2 layer/palette/priority ports, live camera,
  and QA-12 diagnostic and visual harness.

## Systems deliberately disabled

- Player action/equipment, attack selection or timing, alien state/AI,
  navigation, collision, damage, HIT/KO, encounter authority, HUD, audio,
  frontend, route expansion, multiplayer, and physical-status changes.

## Focused machine checks

- Prove camera world X 768 maps to the captured opening plane scrolls rather
  than raw PNT offsets; cover the bounded post-unlock camera range and both
  plane origins; reject the current raw-camera/raw-half-camera bridge.
- Rerun the strict REIMPLEMENT-12 replay and QA-12 differential unchanged to
  lock the reviewed attack sequence, tracking AI, collision/damage, HIT/KO,
  clear, and continued movement.

## Saturn build profile

Build the exact live-encounter diagnostic and normal interactive targets from
the committed candidate. Preserve all accepted asset, residency, palette,
priority, canary, and zero-fallback locks.

## Emulator readback

Collect paired pinned semantic runs and direct visual evidence at opening and
post-unlock camera positions. Require coherent street planes across the full
viewport, exact gameplay ledger equality, intact canaries, and zero asset,
render, or fallback failures.

## Human-review requirement

Renew `USER-09-LIVE-ENCOUNTER-REVIEW` after machine and emulator checks. Ask
exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?"
Keep the reported neutral-facing reversal explicitly unresolved unless a
separate bounded repair is activated.

## Exclusions

- No attack or AI changes, neutral-facing repair, new stage art, frontend
  activation, physical claim, source-closure promotion, or complete Round 1
  claim.

## Hard stops

- Any gameplay semantic change; any change to the reviewed attack sequence or
  player-tracking alien AI; any new stage asset or guessed art substitution;
  target failure, nondeterminism, missing mutation reject, or absent visual
  proof at both camera positions.

## Next eligible cards

- Renewed `USER-09-LIVE-ENCOUNTER-REVIEW` only. The neutral-facing reversal
  remains recorded for that review, `SALVAGE-08-FRONTEND` remains blocked, and
  physical Saturn remains `UNRUN`.
