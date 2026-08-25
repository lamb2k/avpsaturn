# REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER task card

TASK: REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER
KIND: INTEGRATE
STATUS: ACCEPTED
CHECKPOINT: reimplement-source-closed-live-encounter
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: [Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL]

## Objective

Retain the live encounter diagnostic harness and replace its gameplay
authorities with bounded implementations consuming only SPEC-01, its generated
fixtures, accepted Port V2 interfaces, and approved assets/presentation locks.

## Owned paths

- Bounded live player, navigation, class-`0x1F`, collision/encounter interfaces
  and adapters named by SPEC-01
- Exact focused/target/emulator tests, this card, and state/ledger updates

## Existing systems to reuse

- Current rendering, HUD, camera, audio, collision infrastructure, readback,
  emulator, visual-QA harness, accepted Port V2 interfaces, and SPEC-01 only.

## Systems deliberately disabled

- Automatic selector cycling, unbounded movement, route-only AI approximation,
  disconnected facing/presentation, raw-trace implementation, frontend,
  multiplayer, later stages, and physical-status changes.

## Focused machine checks

- Strict C90 deterministic replay twice; SPEC-01 guard/transition coverage;
  real mutations for selector/equipment, bounds, facing/assembly, collision,
  and encounter authority; preserve approved camera/death/damage/audio locks.

## Saturn build profile

Build the bounded live diagnostic and normal interactive image from a committed
candidate with unchanged harness infrastructure and declared SPEC-01 identity.

## Emulator readback

Two cold pinned runs with exact semantic equality and state-to-render identity;
no fallback, canary failure, late read, or disconnected presentation state.

## Human-review requirement

No direct user approval here. QA-12 must pass before renewed USER-09.

## Exclusions

- No raw MAME/disassembly/visual-guess implementation, generic framework,
  frontend activation, complete Round 1 claim, or physical claim.

## Hard stops

- Any required UNKNOWN, SPEC-01 violation, approved-lock regression,
  nondeterminism, target/emulator failure, or fallback behavior.

## Next eligible cards

- `QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL` after technical acceptance.

## Validated evidence

- SPEC-01 identity `a8a8d5ff...bd0f` is compiled into interface version 2;
  the committed source-closed candidate and hardened readback harness are at
  `7185c38c41a2575698f5b79ca32020d38d10c178`.
- Fast, Oracle, and target build-only lanes pass. Ten real source mutations
  covering combo timing, equipment visibility, wall bounds, alien facing,
  attack and KO assemblies, contact width, projection, camera origin, and
  clear authority are rejected.
- Two cold pinned Yaba runs use exact ISO `3ccd3873...a41`, the same committed
  source tree, and identical 471-frame semantic ledgers. They record four
  player contacts, one alien contact/damage event, one deliberate miss, three
  HIT events, one KO, unlock at frame 450, continued camera movement, intact
  canaries, and zero failures or fallbacks.
- The later KO record/assembly resolver now consumes each source record's
  exact `+0x04` assembly pointer; state, record, and assembly remain same-tick
  through the preserved death transition.
- This is technical acceptance only. The milestone remains
  `TECHNICAL_PROTOTYPE` / `ADAPTED_GAMEPLAY_SCAFFOLD` / `NOT_SOURCE_CLOSED` /
  `NOT_USER_APPROVED` until QA-12 and renewed USER-09 complete. Frontend is
  inactive and physical Saturn remains `UNRUN`.
