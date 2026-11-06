# INTEGRATE-02-COMBAT task card

TASK: INTEGRATE-02-COMBAT
KIND: INTEGRATE
STATUS: ACCEPTED
CHECKPOINT: integrate-combat
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [INTEGRATE-01-PLAYER-AND-ENEMY, SALVAGE-03-COLLISION, V2-B1]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-03-COMBAT-FEEL-REVIEW]

## Objective

Add attack, collision, contact, damage, HIT, and KO one bounded behavior at a time to the promoted player/enemy integration.

## Owned paths

- `src/port_v2/integration/combat/**`
- `tests/port_v2/integration/combat/**`
- Card-scoped diagnostic/readback, ledger, state, and card

## Existing systems to reuse

- Promoted player/enemy/collision/HIT-KO interfaces and accepted source evidence.

## Systems deliberately disabled

- Camera progression, stage expansion, HUD, PCM, and CDDA.

## Focused machine checks

- Strict compile; per-behavior differential; deterministic replay; no-contact and mutated-writer controls; regress approved actor presentation.

## Saturn build profile

Dedicated `CombatIntegrationBench` diagnostic.

## Emulator readback

Require attack/contact/damage/HIT/KO semantic events and frames, actor states/positions, render counts, canaries, asset failures, and stability.

## Human-review requirement

Required after AI self-review through `USER-03-COMBAT-FEEL-REVIEW`.

## Exclusions

- No new enemy AI, stage, audio, or authored approximation.

## Hard stops

- Source mismatch, approved actor regression, unsupported exact dependency, or exhausted correction cycle.

## Next eligible cards

- `USER-03-COMBAT-FEEL-REVIEW`.

## Accepted result

- Implementation commit: `cc5f6999e8dd15146b739285db264b4b2ea45bfb`.
- Technical status: `PASS`; fidelity status: `MEASURED`; user status:
  `AWAITING_USER_FEEDBACK` through `USER-03-COMBAT-FEEL-REVIEW`.
- Production interface: `src/port_v2/integration/combat/combat.h`.
- Four source-measured contacts at samples 5190, 5236, 5283, and 5329 apply
  exact hit values 8, 8, 10, and 12 and exact health transitions
  87 -> 63 -> 39 -> 8 -> -1.
- The first contact begins the promoted exact HIT transition and the final
  contact begins the promoted exact KO transition. The second and third
  reaction timings remain unpromoted and are represented only as measured
  damage events.
- Strict C90 host differential and deterministic repeat pass. No-contact,
  wrong-selector, and mutated HIT/KO writer controls reject.
- `CombatIntegrationBench` target build passes. Two normalized target builds
  and paired pinned Yaba Sanshiro readbacks agree at ISO SHA-256
  `94c1e5bab162504ceee7914b14c2beee313c32bcdbfb8e4e0f56959ed4cf7f40`.
- Exact emulator samples at combat frames 185 and 860 report the expected
  HIT and terminal KO states, four event-ledger entries, two negative-control
  rejections, zero diagnostic/asset/late-read/tile failures, intact canaries,
  and approved player/enemy render-order locks.
- The card-only 135-tile HIT/KO overlay is 17,900 bytes at SHA-256
  `070443fb8dd7c6791fd846fb95cce100e89eee301ba9ad6dffeea581f72cf40c`.
  The approved general street archive remains byte-identical at SHA-256
  `43d9707f2bcdb0d23f82db7169052bf21d29627d966a9990706ccc472eb3c1c3`.
- Fast passes. The active-worktree Oracle wrapper is `INCOMPLETE` only because
  ignored private V2-2B writer inputs are absent; its committed/focused checks
  and MAME `avspu` identity pass, and both omitted writer controls pass
  read-only in the preserved V2-2B evidence worktree.
- AI, general attack rules, general damage formula, the two unpromoted reaction
  timings, audio, normal release, a second emulator, user approval, and
  physical Saturn remain `UNRUN` or outside this bounded result. Capability
  Gate remains `0/12`.
