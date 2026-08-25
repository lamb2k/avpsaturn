# ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE task card

TASK: ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE
KIND: ORACLE
STATUS: READY
CHECKPOINT: oracle-round1-reachable-logic-closure
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [SPEC-02-ROUND1-EXECUTABLE-CONTRACT]

## Objective

Use the ORACLE-10 census as the backlog and close every reachable gameplay
authority required to complete Round 1 with Predator Warrior. Process one
authority family at a time with coherent evidence checkpoints; create a child
card only for a genuinely independent body or source-evidence hard stop.

## Evidence checkpoints

- `actor-scheduler-allocation-lifecycle`: `SOURCE_CLOSED` in
  `data/oracle11_actor_scheduler_lifecycle.json`. The exact required pool
  topology, fixed frame order, active/class dispatch, low-word LIFO allocation
  and release rules, required Round 1 dispatch entries, deterministic controls,
  and route-wide class-removal counterfactuals are bound. Player update
  authority remains deliberately assigned to the player family.
- `predator-warrior-locomotion-neutral-facing`: `SOURCE_CLOSED` inside the
  still-`PARTIAL` player family in
  `data/oracle11_predator_warrior_authority.json`. Source input decode,
  signed fixed-point vectors, facing writers, ten-tick stop transition,
  stop-to-idle presentation, and facing retention are bound. Source Up maps to
  positive world Y/Z and Down maps to negative world Y/Z; screen conversion is
  a later executable-contract concern. Remaining actions, equipment,
  projectile/resource ownership, HIT/KO/continue, and return-to-control bodies
  remain active backlog.
- `predator-warrior-route-melee`: `SOURCE_CLOSED` inside the still-`PARTIAL`
  player family. Button-2 edge dispatch, target-context override, four-step
  selector/assembly ownership, the 30-tick follow-up window, recovery-edge
  chaining, and non-random state-owned presentation are bound in
  `data/oracle11_predator_warrior_authority.json`. The confirmed selector
  timing and attack assemblies remain locked.
- `predator-warrior-normal-jump-air-landing`: `SOURCE_CLOSED` inside the
  still-`PARTIAL` player family. Two independent byte-identical source runs
  bind Button-3 edge dispatch, fixed-point vector setup and integration,
  neutral jump presentation, landing guard/snap, facing retention, and return
  to control. Its earlier direction-plus-jump HIT capture is retained as the
  unmodified interruption witness for the broader checkpoint below.
- `predator-warrior-directional-airborne-interruption`: `SOURCE_CLOSED` inside
  the still-`PARTIAL` player family. The baseline, perturbed, and
  failure/continue universe reaches `0x0400/02/04/06`; input-only targeted
  routes additionally bind `0x040a/0c/0e/10` across every direction lane,
  airborne Button-1 and Button-2 guards, landing, HIT cancellation, and return
  to control. `0x0408/12/14` have no route or input-only witness and are
  explicitly `NOT_REQUIRED_FOR_ROUND1`, with a witness-reopens-family control.
  Evidence and mutation controls are in
  `data/oracle11_predator_air_authority.json` and the sole route-segment x
  authority-family matrix remains in `data/round1_system_coverage.yaml`.
- `predator-warrior-weapon-projectile-resource`: `SOURCE_CLOSED` inside the
  still-`PARTIAL` player family. Two independently launched byte-identical
  captures plus twelve causal counterfactual classes bind Button-1 edge/held
  dispatch, the twelve-attempt class-`0x05` volley, record-type-4 allocation
  and lifecycle, current-state collision/removal, the presentation-only empty
  fallback, B1+B2 health-funded special, meter debit/recharge/depleted state,
  temporary resource-award timer, class-`0x54` display ownership, facing,
  gameplay-audio boundaries, and RNG/order. Evidence is in
  `data/oracle11_predator_weapon_projectile_resource.json` and
  `data/oracle11_predator_warrior_authority.json`. The player HIT/KO and
  continue checkpoint below consumes the next dependency; route-wide
  pickup/resource/audio/load/release ownership remains active afterward.
- `predator-warrior-hit-ko-failure-continue-respawn-return`: `SOURCE_CLOSED`
  inside the still-`PARTIAL` player family. Two independently launched
  byte-identical captures bind signed-health lethal KO, the full source-owned
  KO phase sequence and 60-tick removal countdown, nonlethal HIT recovery and
  one-tick invulnerability, failure state, packed-BCD credit debit, credited
  Start, gameplay-button confirmation, respawn initialization, and return to
  control. Coin-only, no-continue, delayed-Start, health-threshold,
  input-suppression, isolated Button1/Button2/Button3, and direction-only
  counterfactuals reject fixed-frame or cursor-owned respawn. Evidence is in
  `data/oracle11_predator_hitko_continue.json` and the integrated player
  artifact. Route-wide pickup/resource/audio/load/release ownership is the
  sole remaining Predator Warrior backlog; the family remains `PARTIAL`.

## Owned paths

- Card-scoped static analysis, deterministic captures, counterfactuals,
  evidence, tests, census closure fields, and state/roadmap ledgers

## Existing systems to reuse

- ORACLE-10 census, accepted Oracle evidence, source routines/tables, pinned
  reference captures, and deterministic mutation infrastructure.

## Systems deliberately disabled

- All production runtime writes, generalized engines, behavior-tree/ECS/script
  frameworks, whole-program recompilation, frontend, other characters,
  multiplayer, later stages, and physical status.

## Focused machine checks

- Recover entry/exit states, dispatch, guards, types/signedness, reads/writes,
  timers, arithmetic, facing, actions, animations/assemblies, collision,
  damage/resources, RNG/order, scheduler position, and route interactions for
  player authority; navigation; scheduler/lifecycle; every required enemy;
  equipment/projectiles/pickups/hazards; encounters; scripts; boss; clear,
  continue, handoff; and gameplay-owned audio/load triggers.
- Prefer bounded source routines over frame fitting. Continue independent
  families around blockers. Complete only when every completion-route behavior
  is `SOURCE_CLOSED` or narrowly `ADAPTED` with rule and mutation controls.

## Saturn build profile

None. Read-only source closure; no production or Target build.

## Emulator readback

Reference MAME evidence only. All production Saturn and Yaba execution is
disabled.

## Human-review requirement

None; this card cannot infer or grant user approval.

## Exclusions

- No production implementation, visual guessing, plausible fallback, generic
  CPS-2 engine, all-four-character work, multiplayer, or whole-game closure.

## Hard stops

- Completion-route authority remains `UNKNOWN` with no dependency-safe work
  remaining, or source identity/mutation evidence cannot be established.

## Next eligible cards

- `SPEC-02-ROUND1-EXECUTABLE-CONTRACT` after required Round 1 authority reaches
  zero UNKNOWN.
