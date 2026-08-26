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
  now-`SOURCE_CLOSED` player family in
  `data/oracle11_predator_warrior_authority.json`. Source input decode,
  signed fixed-point vectors, facing writers, ten-tick stop transition,
  stop-to-idle presentation, and facing retention are bound. Source Up maps to
  positive world Y/Z and Down maps to negative world Y/Z; screen conversion is
  a later executable-contract concern. The subsequent checkpoints below close
  the formerly outstanding player bodies without changing this contract.
- `predator-warrior-route-melee`: `SOURCE_CLOSED` inside the
  now-`SOURCE_CLOSED`
  player family. Button-2 edge dispatch, target-context override, four-step
  selector/assembly ownership, the 30-tick follow-up window, recovery-edge
  chaining, and non-random state-owned presentation are bound in
  `data/oracle11_predator_warrior_authority.json`. The confirmed selector
  timing and attack assemblies remain locked.
- `predator-warrior-normal-jump-air-landing`: `SOURCE_CLOSED` inside the
  now-`SOURCE_CLOSED` player family. Two independent byte-identical source runs
  bind Button-3 edge dispatch, fixed-point vector setup and integration,
  neutral jump presentation, landing guard/snap, facing retention, and return
  to control. Its earlier direction-plus-jump HIT capture is retained as the
  unmodified interruption witness for the broader checkpoint below.
- `predator-warrior-directional-airborne-interruption`: `SOURCE_CLOSED` inside
  the now-`SOURCE_CLOSED` player family. The baseline, perturbed, and
  failure/continue universe reaches `0x0400/02/04/06`; input-only targeted
  routes additionally bind `0x040a/0c/0e/10` across every direction lane,
  airborne Button-1 and Button-2 guards, landing, HIT cancellation, and return
  to control. `0x0408/12/14` have no route or input-only witness and are
  explicitly `NOT_REQUIRED_FOR_ROUND1`, with a witness-reopens-family control.
  Evidence and mutation controls are in
  `data/oracle11_predator_air_authority.json` and the sole route-segment x
  authority-family matrix remains in `data/round1_system_coverage.yaml`.
- `predator-warrior-weapon-projectile-resource`: `SOURCE_CLOSED` inside the
  now-`SOURCE_CLOSED` player family. Two independently launched byte-identical
  captures plus twelve causal counterfactual classes bind Button-1 edge/held
  dispatch, the twelve-attempt class-`0x05` volley, record-type-4 allocation
  and lifecycle, current-state collision/removal, the presentation-only empty
  fallback, B1+B2 health-funded special, meter debit/recharge/depleted state,
  temporary resource-award timer, class-`0x54` display ownership, facing,
  gameplay-audio boundaries, and RNG/order. Evidence is in
  `data/oracle11_predator_weapon_projectile_resource.json` and
  `data/oracle11_predator_warrior_authority.json`. The later HIT/KO/continue
  and route-ownership checkpoints below complete its dependent player edges.
- `predator-warrior-hit-ko-failure-continue-respawn-return`: `SOURCE_CLOSED`
  inside the now-`SOURCE_CLOSED` player family. Two independently launched
  byte-identical captures bind signed-health lethal KO, the full source-owned
  KO phase sequence and 60-tick removal countdown, nonlethal HIT recovery and
  one-tick invulnerability, failure state, packed-BCD credit debit, credited
  Start, gameplay-button confirmation, respawn initialization, and return to
  control. Coin-only, no-continue, delayed-Start, health-threshold,
  input-suppression, isolated Button1/Button2/Button3, and direction-only
  counterfactuals reject fixed-frame or cursor-owned respawn. Evidence is in
  `data/oracle11_predator_hitko_continue.json` and the integrated player
  artifact.
- `predator-warrior-route-pickup-resource-player-audio-ownership`:
  `SOURCE_CLOSED`. Two independent route-event
  controls and two independent natural-interaction controls map every observed
  player action phase. Health/max-health, record24 effect removal, natural
  interaction completion/button interruption, and native class-`0x0e` target
  acquisition/resource-grant controls separate gameplay state from display
  actors. Static and dynamic source evidence proves that `0x0abdd2` is a
  four-byte packed-BCD score-award routine, not QSound authority; the separate
  score-only routine at `0x0abe2a..0x0abf16` is also rejected as audio
  provenance. Two independently launched completion captures are byte
  identical. Their 378 player-origin dispatches reduce to 38 distinct
  caller/command trigger edges across 47 player state/action/substate contexts.
  One bounded suppression per edge preserves score, health, damage, resource,
  projectile, and route state while producing a discriminating downstream
  QSound-bus difference. Exact callers, return sites, arguments, shared wrapper
  `0x003a88`, queue entry `0x001922`, and queue writers `0x00193c/40/44` are
  bound in `data/oracle11_predator_player_audio.json`. Shared drain
  `0x001880` and dispatcher-to-QSound transport remain assigned to the global
  gameplay-audio/load/release family. Load/release, pickup-actor lifecycle,
  stage-clear phases, and HUD/route presentation remain explicit external
  authority edges. ORACLE-11 remains active and SPEC-02 remains blocked by the
  complete matrix zero-gap gate.
- `global-gameplay-audio-load-release`: `SOURCE_CLOSED`. The shared main-CPU queue
  drain `0x001880..0x001914` is `SOURCE_CLOSED`: both byte-identical completion
  captures contain 1,161 enqueues, and all twelve shared-RAM payload writers
  execute exactly 1,161 times with the source queue guards, 16-byte entry,
  `0x03f0` pointer wrap, ready-byte handshake, and consumer advance bound.
  Two additional byte-identical full-route captures source-close the audio-CPU
  16-byte shared-command ingress at audio ROM `0x0038..0x0074` and the guarded
  three-port QSound write primitive at `0x0abc..0x0adb`; the former processes
  1,161 commands and the latter writes 489,834 exact low/high/register triples
  per completion. Two further byte-identical detailed completions and two
  byte-identical compact completions source-close the intervening audio-CPU
  dispatcher/table/handler boundary at `0x01bd..0x0294`: all 1,161 copied
  16-byte payloads are preserved, all 72 route-reachable command identities
  resolve through the 909-entry command table, and the 29 accepted player
  command controls plus 43 new global controls produce discriminating grouped
  QSound transaction differences. Null table entries retain their measured
  dispatch-timing effect. Individual low/high/register writes are not treated
  as logical events, and there are zero orphan shared commands, command
  identities, handler paths, or QSound transaction groups. Evidence is in
  `data/oracle11_global_audio_handlers.json`.
  Two byte-identical origin-census completions bind all 783 non-player
  dispatches and all 175 exact origin-A6/shared-return/command groups to their
  live class/type/state/substate owner contexts, 50 exact source callsites,
  local guard tails, arguments, and accepted command-handler transaction
  controls. Enemy, projectile, pickup, route, encounter, boss, and presentation
  owners are source-derived rather than appearance-inferred, with zero orphan
  groups, callers, or handler transactions. Evidence is in
  `data/oracle11_global_audio_trigger_owners.json`. Only the four route
  load/release boundaries at frames 5,565, 5,566, 6,200, and 12,799 remain in
  this family. Two byte-identical load completions and one full-route
  suppression for each boundary bind the route guards, exact graphics-RAM
  writer/caller chains, package snapshot and transaction hashes, destination
  ownership, legal read windows, completion state, failure-state package
  mismatch, and next route state. The gameplay/route projection remains
  unchanged under each presentation-package suppression. Evidence is in
  `data/oracle11_global_load_release_boundaries.json`. The combined family has
  zero orphan trigger groups, shared commands, handler paths, QSound
  transactions, route guards, packages, destinations, legal windows, or load
  callers. No semantic sound or package names are inferred, and the packed-BCD
  score routines remain rejected as audio owners.
- `round1-navigation-terrain-obstacle-camera`: `SOURCE_CLOSED`. Two independently
  launched route completions are byte-identical and a post-frame-4200
  Up/Down perturbation completes Round 1 while discriminating navigation state.
  The source `0x01b000..0x01b05e` global-bound routine, signed A5 bound fields,
  every captured bound run, `0x0b1baa..0x0b1c70` terrain resolver, all six
  route-reachable terrain records, record-type-20 scheduler ownership, four
  type-20 navigation bodies, `0x01d930..0x01d99a` minimum-penetration obstacle
  response, `0xff8032` camera target, exact writer/call chains, and all 19
  route camera lock/unlock runs are bound in
  `data/oracle11_round1_navigation.json`. ORACLE-08 directional and obstacle
  removals plus ORACLE-10 hold-navigation/remove-navigation-body completions
  remain accepted counterfactuals. No guessed x-only, kill-count, or fixed-frame
  camera guard is admitted. Type-20 damage, destruction, pickup/hazard, and
  presentation edges remain explicitly assigned to their existing families;
  the navigation checkpoint does not silently close those actor edges.
- `round1-enemy-archetypes`: `SOURCE_CLOSED`. Two independently launched full
  route captures are byte-identical across 48,156 live samples, 47,341 exact
  class entries, 326,632 actor writes, 893 enemy-owned RNG calls, and 19
  enemy-origin player-damage writes. Every route-reachable state/phase, facing,
  target pointer, writer/caller, animation record, assembly, hurt/attack
  selector, health transition, HIT/KO transition, and RNG caller for type-12
  classes `0x00`, `0x01`, `0x06`, and `0x1f` is bound to source bytes in
  `data/oracle11_round1_enemy_archetypes.json`. Class-removal and
  offense-suppression controls discriminate every archetype; the accepted
  ORACLE-09 class-`0x1f` counterfactuals remain locked. The boss actor contract
  is closed here, while boss encounter orchestration and encounter spawn/wave
  guards remain explicitly assigned to their separate families. No generic
  enemy behavior tree, independent assembly selection, shared player/enemy
  clamp, semantic sound name, or fixed-frame attack/death substitute is used.
- `round1-pickups-equipment-weapons-projectiles-hazards-destructibles`:
  `SOURCE_CLOSED`. Two full-route auxiliary captures are byte-identical across
  120,620 samples, 59,865 exact class entries, 428,764 actor writes, 1,348 RNG
  calls, and two source-owned player-health effects. Twelve corrected full-route
  suppressions each remove a distinct source-dispatched type-16, type-20, or
  type-24 class and preserve the resulting native completion state. The first
  suppression attempt is explicitly rejected because a local notifier handle
  was garbage-collected and removed zero actors; those captures are preserved
  but excluded. Exact state/phase, writer, RNG, presentation, collision
  selector, player effect, lifecycle, and corrected suppression evidence is in
  `data/oracle11_round1_auxiliary_authority.json`. Four ORACLE-10 generic-census
  class/type pairs are proven player or half-stride aliases with no scheduler
  dispatch and are `NOT_REQUIRED_FOR_ROUND1`. Player-side weapon/projectile/
  resource and type-20 navigation geometry contracts remain consumed from
  their accepted evidence rather than reopened.

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
