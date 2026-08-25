# ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION task card

TASK: ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION
KIND: ORACLE
STATUS: ACCEPTED
CHECKPOINT: oracle-alien-state-facing-presentation
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT]

## Objective

Source-close class-`0x1F` state/substate dispatch, target/approach/lane steering,
facing and crossing, attack/presentation selection, cooldown/reposition,
HIT/KO/removal, RNG, and scheduler ordering so one source actor state owns
facing, animation record, and rendered assembly.

## Owned paths

- Card-scoped MAME inputs/capture/analyzer tools
- Ignored private traces, captures, disassembly, and actor crops
- Tracked derived reports and fixtures under `data/oracle09_*`
- Coverage/migration/state fields and this card

## Existing systems to reuse

- Pinned MAME 0.289 `avspu`, ORACLE-05 route evidence, accepted enemy assets,
  HIT/KO writer maps, and deterministic class-`0x1F` tooling.

## Systems deliberately disabled

- All production runtime, route-only rule generalization, disconnected
  presentation adapters, frontend, Saturn/physical acceptance, and generic AI.

## Focused machine checks

- Counterfactual player placement left/right/above/below, target crossing,
  motion during approach/attack, attacking during approach/attack, and
  inside/outside range. Bind state/facing/animation/assembly from one source
  tick; reject facing, assembly, lane-rule, RNG, and scheduler mutations.

## Saturn build profile

None. This is read-only source closure.

## Emulator readback

No Saturn emulator or physical-Saturn acceptance evidence.

## Human-review requirement

None; the source-closed implementation must later pass QA-12 and renewed
USER-09.

## Exclusions

- No production-path write, generic behavior tree, other alien archetype,
  multiplayer targeting, frontend activation, or physical claim.

## Hard stops

- A bounded state uses unresolved source authority, the experiments cannot
  discriminate target-relative behavior, or state/facing/assembly identity
  remains disconnected.

## Next eligible cards

- `SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT` after acceptance.

## Validated evidence

- Two independently launched MAME captures are byte-identical across 701
  samples, actor writes, class-entry samples, and target RNG calls.
- The opening class-`0x1F`, type-12 actor at `0xffa000` targets P1
  `0xff8380`. Its action `0x1600` is an authored route state: placing P1 left
  of the actor leaves source facing `1`, so an every-frame face-target rule is
  explicitly rejected.
- In the right-to-left crossing control, source tick 4284 writes action
  `0x1a00`, facing `0`, animation record `0x12d5e4`, and assembly
  `0x12fae8` through the measured writer set. The next actor sample retains
  that single state-owned identity. This is a bounded delayed route response,
  not a universal immediate crossing flip.
- The bounded approach state owns an eight-record `0x12ec04..0x12ec74`
  presentation cycle. The RNG-owned attack state `0x1800` owns a four-record
  `0x12e8ec..0x12e91c` cycle and timer 120 in the committed control. Player
  motion or attack input during the active attack does not independently flip,
  reroll, or replace the actor presentation.
- Above/below, crossing, inside/outside range, movement, and player-attack
  counterfactuals discriminate state ownership. Inside placement exercises a
  contact/HIT/death/removal lifecycle; outside placement leaves the opening
  route schedule unchanged. No guessed Euclidean attack threshold is allowed.
- Accepted ORACLE-05 identity supplies the 20-slot scheduler, target pool index
  14, RNG recurrence, two attack contacts, and HIT/KO/removal sequence. The
  accepted source-combat artifact binds source actor state, facing, animation,
  assembly, emitted object identity, tile identity, and palette for the four
  HIT/KO events.
- The public report is
  `data/oracle09_street_alien_state_facing_presentation.json`, SHA-256
  `a3027c3ffcd19af2656c515e0dfc0e9c56086b1bf3dd029e854d74be372c847f`,
  at evidence commit `d530820ba87b3cc530c485c38bc046a4d942e801`.
  `Fast` and `Oracle` pass. Saturn emulator and physical Saturn remain `UNRUN`;
  no production gameplay path changed.
