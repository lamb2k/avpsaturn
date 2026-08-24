# ORACLE-05-STREET-ALIEN-AI task card

TASK: ORACLE-05-STREET-ALIEN-AI
KIND: ORACLE
STATUS: READY
CHECKPOINT: oracle-street-alien-ai
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [ORACLE-06-ROUND1-ENCOUNTER-RULES]

## Objective

Capture one complete class-`0x1F` street-alien behavior loop: spawn/init,
one-player target selection, approach, lane adjustment, facing, attack
selection, startup/active/recovery/cooldown, player collision/damage,
repositioning, HIT/recovery, KO/removal, relevant timers and RNG consumption,
and actor scheduler/update order.

## Owned paths

- Card-scoped MAME inputs/capture tools, ignored raw evidence, derived AI
  fixtures/reports, coverage/migration fields, state, and this card only

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, accepted class-`0x1F` identity/HIT/KO evidence,
  and existing provenance and controlled-capture tooling.

## Systems deliberately disabled

- All production runtime, Saturn, Probe 3, physical evidence, frontend,
  `production_head`, other enemy archetypes, bosses, and multiplayer.

## Focused machine checks

- Two identical captures and controlled counterfactuals for player distance,
  lane difference, player attack timing, enemy health, AI timer, and consumed
  RNG state; bind scheduler order and reject appearance-derived behavior trees.

## Saturn build profile

None. Read-only MAME/host source research.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; later implementation and playability review remain separate.

## Exclusions

- No production-path write, invented behavior tree, generic AI engine,
  archetype expansion, authored fallback, or physical-status transition.

## Hard stops

- Missing private inputs, nondeterminism, unresolved scheduler/RNG ownership,
  inadequate counterfactual, production-path drift, or another Oracle writer.

## Next eligible cards

- `ORACLE-06-ROUND1-ENCOUNTER-RULES` after this card is accepted.

## Validated evidence

- Two 3,101-frame cold-boot captures are byte-identical across samples, RNG
  calls, scheduler fetches, and class-entry dispatches. The sample SHA-256 is
  `f65d127841ae23f4358cdc50dde5177252aeadb32e9e3ad46dc904a582d5741b`.
- Static opcode binding identifies class dispatch `0x060532`, init `0x060546`,
  nested dispatch `0x06075A`, the one-player target routine `0x017020`, and RNG
  routine `0x017C5E`. Live taps bind slot `0xFFA000` to the 15th of 20 executed
  scheduler slots; the extra loop-head fetch is a terminal, non-executed
  prefetch and is excluded.
- The measured loop initializes health 87 and target `0xFF8380`, approaches in
  action `0x1600`, selects action `0x1800` with a 120-frame timer, damages the
  player by 8 at offsets 48 and 119, clears at frame 4373, and re-enters
  approach at frame 4374.
- HIT contacts at 5190, 5236, 5283, and 5329 produce health 87 -> 63 -> 39 ->
  8 -> -1; the actor enters KO/death and is inactive at 5470. A forced health
  of 15 makes the first hit lethal and advances inactivity to frame 5327.
- RNG seed `0x7301` at the selection call advances to `0x595A` and selects timer
  120. The `0x0001` fixed-point control remains `0x0001`, selects timer 30,
  and advances attack clear from frame 4373 to 4283. A direct timer control
  independently advances clear to frame 4257 and exposes reposition state 8.
- Distance and lane writes spanning the next spawn do not reselect the target's
  already committed first action during the write window; later shared-route
  RNG divergence is recorded without generalizing target-relative lane choice.
  Suppressing the complete five-frame player attack pulse changes player state,
  then shared RNG, then the target timer in that causal order.
- `data/oracle05_street_alien_ai.json` is deterministic at SHA-256
  `8b7a9372555414ba0ecfb44b6e8e207d0b873499bc6f7dedb45e52b2fd677031`.
  Focused negative controls, `Fast`, and `Oracle` pass. Saturn emulator and
  physical Saturn remain `UNRUN`; other archetypes and live multiplayer remain
  out of scope.
