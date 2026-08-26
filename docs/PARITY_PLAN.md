# AvP title-to-credits production roadmap

This is the project's only roadmap and active backlog. `project_state.yaml`
owns machine-readable state; `data/port_v2_migration_map.yaml` owns subsystem
migration decisions; task cards own bounded work. None is a second roadmap.

## 1. Release target and method

Deliver a native, capture-faithful Sega Saturn port of MAME set `avspu` from
cold boot through title, four-character select, every stage and boss, ending,
and credits. The playable roster is Predator Warrior, Major Schaefer, Predator
Hunter, and Linn Kurosawa. The multiplayer target is up to three simultaneous
local players through a proven Saturn controller/multitap topology.

Development remains an interactive human-in-the-loop loop:

```text
existing subsystem -> isolated salvage bench -> focused machine validation
-> Saturn diagnostic and emulator self-review -> human review when subjective
-> salvage decision -> port_v2 interface promotion
-> integration with one additional dependency -> repeat
```

The old mixed runtime and playable-skeleton prototype are reusable sources, not
production gameplay authority. Lab, host, MAME, emulator, and human-review
success does not advance a physical Saturn or release gate.

## 2. Evidence and performance contract

AvP passes on its measured workload. The integrated physical capability slice
requires stable NTSC cadence, deterministic input-visible behavior, no
sustained skipped/repeated fields, at least 15% measured VDP1 draw-end and
total-frame margin at representative and 909-tile peaks, at least 15% usable
memory headroom with canaries, no combat-time data reads while CDDA owns the
drive, timed PCM and continuous CDDA, correct 352x224 framing, and a ten-minute
soak without corruption, fallback, hang, missed field, or audio loss.

Machine validation, source fidelity, Saturn emulator review, human approval,
and physical proof are independent statuses. No result is promoted to a
stronger evidence tier by wording.

## 3. Continuity and preserved work

`project_state.yaml` separates four commit roles:

- `foundation_head`: accepted reverse-engineering and architecture foundation;
- `production_head`: latest accepted Port V2 production continuity result;
- `candidate_head`: active implementation candidate;
- `evidence_candidate_head`: preserved V2-2B writer/evidence candidate.

Future production cards base from `production_head`. The already-active card
retains its historical base metadata. The current existing continuity branch is
designated as the production line; no branch or worktree is created merely
because a tranche changes.

The dirty canonical worktree, dirty playable-skeleton prototype, accepted
V2-2B evidence worktree, accepted commits, private evidence, recovery patches,
and ignored feedback packages remain preserved.

V2-2B is accepted at the bounded MAME/static/host evidence tiers. V2-B1 has
promoted only the accepted exact class `0x1F` HIT/KO traces behind a narrow
production interface with host, Saturn diagnostic, and one-emulator evidence.
It does not promote attack, contact, damage, AI, normal release, or physical
Saturn proof. It is HIT/KO only, not loading, controller input, actor rendering,
stage, palette, HUD, PCM, diagnostics, or the read-only Oracle cards. Goal Mode
has now advanced through the dependency-safe presentation promotions.

CURRENT_TASK: REIMPLEMENT-13-SOURCE-CLOSED-ROUND1

ACTIVE_SOFTWARE_TASK: SOURCE_CLOSED_ROUND1_NATIVE_C

## 4. Current salvage queue and production extension

The accepted player, enemy, combat, camera/stage, P1/P2 HUD, PCM, CDDA, and
phase-residency results remain regression locks. REPAIR-09 is accepted at
implementation `417ed80`: the player/combat
interface now binds each selector-specific player presentation, collision,
damage, and class-`0x1F` alien reaction to one independent MAME source event.
INTEGRATE-03 is user `APPROVED` for `SOURCE_BOUND_WITH_ADAPTED_INPUT` at exact
candidate `82965ef` and normalized ISO SHA-256 `4a142774...`. PROMOTE-10 and
PROMOTE-11 provide bounded production player-action and class-`0x1F` AI
interfaces. INTEGRATE-04A now binds them to real controller input, current-
state collision/damage, HIT/KO, the adapted target-KO-then-inactivity clear,
route unlock, and continued movement at `d902196`. Its paired 448-frame Yaba
ledgers and intact visual capture pass, and exact interactive ISO
`ae653596...a7a8a` was reviewed at `USER-09`. The user reported inverted player
facing, incoherent weapon/no-weapon attack presentation, off AI, and off
player/alien collision. `REPAIR-10-LIVE-PLAYER-PRESENTATION` is technically
accepted at `4ea7c18`: it fixes the facing-sign boundary and the unsourced
two-tick legacy attack flash before each selector-owned source sequence. Paired
448-sample emulator state and visual QA pass; renewed interactive ISO
`4b73b534...e0f5f` was reviewed again and remains useful only as a
`TECHNICAL_PROTOTYPE` / `ADAPTED_GAMEPLAY_SCAFFOLD`; it is
`NOT_SOURCE_CLOSED` and `NOT_USER_APPROVED`. The renewed feedback identifies
alien state-facing errors, player equipment/assembly discontinuity,
non-walkable wall traversal, and disconnected player/AI/animation/navigation
authority. The active path is a specification firewall: read-only
ORACLE-07/08/09 source closure, reviewed SPEC-01 executable contracts,
SPEC-only REIMPLEMENT-12, complete QA-12 source/Saturn differential, then
renewed USER-09. That serial firewall has reached renewed USER-09: QA-12 is
accepted at `f99df5e` against corrected gameplay candidate `e237335` and
diagnostic ISO SHA-256 `8e20cb7e...86bea8`. The first visual QA pass rejected
the prior candidate because its source screen-Y projection placed both actors
outside the viewport; the corrected bridge passed the restarted 34-scenario,
471-frame semantic and visual matrix. Existing rendering, HUD, camera, audio,
collision, readback, emulator, and visual-QA infrastructure remains the
diagnostic harness. The
slice remains physically `UNRUN`. The bounded QA prerequisite
`HW-01-PROBE-3-VDP1-BUDGET-PRETEST` has prepared its representative, exact
909-tile, and overload-control hardware package. Host checks, strict build,
paired pinned-emulator semantics, overload detection, and the exact approved
normal-ISO regression pass. It is `READY_FOR_PHYSICAL`; physical timing and
soak remain `UNRUN`, and `SALVAGE-08` remains inactive.

Renewed USER-09 remains `CHANGES_REQUESTED`; no approval is inferred. REPAIR-11
is accepted at production correction `236eef0` and evidence commit `35d527e`.
Direct Yaba inspection confirms coherent opening and post-unlock views, both
VDP2 planes at both visible edges, measured unequal relative scroll, and no raw
PNT displacement. Player/alien camera coherence, the reviewed attack sequence,
class-`0x1F` tracking, HUD, audio, palettes, priorities, residency, gameplay,
and canaries remain locked. The neutral-facing reversal after directional
release remains unresolved for Round 1 player authority.

R7C — `SOURCE-CLOSED ROUND 1 END-TO-END PLAYABLE SLICE` is now the milestone
before frontend. The first-live-encounter harness remains reusable technical
substrate, not final Round 1 gameplay authority. One Predator Warrior,
one-player route is in scope from direct Round 1 diagnostic entry through boss
defeat, stage clear, and stable Round 2 handoff. Other characters, multiplayer,
frontend, and complete-game work are excluded. The exact dependency sequence is
`REPAIR-11` -> `ORACLE-10` -> `ORACLE-11` -> `SPEC-02` -> `REIMPLEMENT-13` ->
`QA-13` -> `USER-10` -> `SALVAGE-08`. Frontend depends on explicit USER-10
acceptance, never the current USER-09 result.

The accepted bounded predecessor firewall remains recorded as
`ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT` ->
`ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS` ->
`ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION` ->
`SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT` ->
`REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER` ->
`QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL` -> USER-09 changes requested.

ORACLE-10 is accepted. Two independent 18,000-frame source completions are
byte-identical; a route-wide input perturbation reaches the exact Round 2
underpass signature at frame 16,425 and continues in rendered Round 2 gameplay.
The bounded source route includes continue/failure evidence. Thirteen detected
counterfactuals cover ten authority families, including the negative controls
that suppress continue and forcibly remove the boss; neither can fabricate a
completion. The census records 94 route bodies, 427 actor lifetimes, 20
class/type archetypes, 26 route events, route/camera/RNG state, and actor,
audio, and load writer evidence. ORACLE-11 now uses that census as its sole
backlog and closes one authority family at a time. No production runtime changed.

ORACLE-11 retains one generated 94-segment x 10-family coverage matrix
in `data/round1_system_coverage.yaml`. Predator Warrior locomotion,
melee, weapon/projectile/resource, and all route-reachable directional and
airborne phases are source closed. Unwitnessed air-table phases
`0x0408/12/14` are explicit `NOT_REQUIRED_FOR_ROUND1`. Nonlethal HIT, lethal
KO, failure/continue, respawn, return-to-control, natural health pickup,
source temporary-resource grant, interaction interruption, packed-BCD score
award, and the player-to-route load/release edges are also source closed. Every
route-observed player phase is mapped. Static and dynamic source evidence
corrected `0x0abdd2` from an audio label to score authority. Two byte-identical
completion captures plus one causal suppression for each of 38 distinct
player-origin caller/command edges close the player-to-shared-dispatch boundary
without changing score, health, damage, resource, projectile, or route state.
Predator Warrior is now `SOURCE_CLOSED`. The global gameplay-audio/load/release
family is also `SOURCE_CLOSED`. Its first global subcheckpoint source-closes the data-independent
main-CPU queue drain to QSound shared RAM across all 1,161 captured route
transactions. Two additional byte-identical captures source-close the
audio-CPU 16-byte shared-command ingress and its guarded low/high/register
QSound write primitive. Two detailed and two compact byte-identical completions
source-close the intervening audio-CPU dispatcher, 909-entry command table,
route-reachable handler paths, and grouped QSound transaction effects for all
1,161 commands and 72 identities. The accepted 29 player command controls and
43 global command controls leave zero orphan shared commands, handler paths, or
QSound transaction groups. Two byte-identical origin-census completions then
bind all 783 non-player dispatches and 175 trigger groups to live owner
class/type/state/substate contexts, 50 exact source callsites, guard tails, and
accepted command-handler controls with zero orphans. Semantic sound names
remain `UNKNOWN`. Two byte-identical load captures and four full-route
destination suppressions source-close the remaining graphics-package
boundaries, including route guards, exact callers, package identities,
destination ownership, legal windows, completion/failure state, and next route
state. Global gameplay-audio/load/release is now `SOURCE_CLOSED` with zero
orphan triggers, commands, handlers, QSound transactions, or load callers. The
Round 1 navigation/terrain/obstacle/camera family is now `SOURCE_CLOSED` from
two byte-identical completions, one completing directional perturbation, and
the accepted route-wide counterfactuals. Source routines bind every observed
dynamic bound run, all six route-reachable terrain records, four type-20
navigation bodies, obstacle response, and all 19 camera lock/unlock runs. No
guessed x-only, kill-count, or fixed-frame camera guard is admitted. Type-20
damage/destruction and presentation edges remain in their declared families.
All four route-reachable type-12 enemy classes are also `SOURCE_CLOSED` from
two byte-identical completions plus class-removal, offense-suppression, and
accepted ORACLE-09 controls. The source contract covers class entries, every
live state/phase and writer, RNG, animation/assembly/collision selectors,
damage, HIT, and KO. Boss encounter orchestration stays separate from the
closed class-`0x06` actor. The pickup/equipment/weapon/projectile/hazard/
destructible family is also `SOURCE_CLOSED`: two byte-identical completions and
twelve real class/type suppressions bind all source-dispatched auxiliary
actors. A zero-removal notifier attempt is rejected and preserved outside
acceptance; four generic census aliases are `NOT_REQUIRED_FOR_ROUND1`. The
encounter/wave/scripted-trigger family is now `SOURCE_CLOSED`: two
byte-identical completions bind all 94 route segments, 14 route-state edges,
609 route-writer transactions, 451 route-writer PCs, and 56 enemy spawns. The
accepted route perturbation and four targeted offense/class-removal controls
leave zero orphan route edges, route writers, or enemy spawns and reject
fixed-frame or actor-count clear substitutes. Round 1 boss
orchestration is now also `SOURCE_CLOSED`: two byte-identical completions bind
the class-`0x06` actor to 11 controller phases, eight exact boss-room spawns,
216 boss RNG calls, and the terminal `0xff81f3` clear writer. Suppressing that
single source write holds the defeated boss route in Round 1; removing
class-`0x06` also cannot fabricate completion. Stage-clear/failure/continue and
the stable Round 2 handoff are `SOURCE_CLOSED`: the three player stage-clear
phases and four route edges `4->6->0->2->4` are bound to source guards and
writers, the four accepted load/release boundaries retain ownership, and the
capture continues under interactive Round 2 state. Presentation labels and
fixed frames are not authoritative. Global RNG is also `SOURCE_CLOSED`: two
byte-identical ledgers bind the exact
`0x017c5e` recurrence and all 2,280 calls on 1,023 seed-change frames to enemy,
auxiliary/transient-child, and global route/controller owners with no gaps.
The final writer reconciliation binds the complete 1,517-PC baseline universe
and assigns each of the 374 residual PCs individually to one accepted authority
and source window; 262 are required `SOURCE_CLOSED` writers and 112 begin only
after stable Round 2 entry and are `NOT_REQUIRED_FOR_ROUND1`. The matrix now has
zero required `OBSERVED`, `PARTIAL`, or `UNKNOWN`, zero unmapped actor pairs or
route edges, zero unowned events, and zero orphan authoritative writers.
ORACLE-11 is accepted and its zero-gap gate remains locked.
SPEC-02 is now accepted. Its 27 required field contracts cover all ten
authority families with zero required UNKNOWN or adapted fields, and its
generated fixtures contain the source-derived Round 1 content plus accepted
Port V2 interface identities. The corrected entry fixture binds the exact
ten-row table, 26-byte player animation program, three timer loads, 164 source
scheduler decrements, and animation-terminator gate; suppressing only its source
writer holds route state 2, so neither a frame nor presentation can own the
first edge. REIMPLEMENT-13 has implemented and validated the
native stable-entry state and exact fixed actor pools. The direct diagnostic
boot and target readback now expose the exact state with paired-emulator
agreement and zero fallback. The first source-derived Round 1 title view renders
through the accepted presentation adapter. The first executable entry body now
also owns the exact ten-row spawn, semantic player-entry sequence, 164 source
scheduler decrements, signed terminator, selected gate clear, route state
`2 -> 4`, and control enable. Direct inspection proves coherent post-unlock and
controller-moved street frames with intact camera, both VDP2 planes, HUD,
palette, and priority. The accepted Predator Warrior controller now consumes
current Saturn input after route state 4 and preserves neutral facing. Paired
471-frame ledgers bind native frame 470 to x 1049, z 320, facing right, neutral
source action, and 301 controller updates. The SPEC-02-bound scheduler now
visits active records in pool order 12/16/20/24 and ascending source-slot order;
paired frame 470 has 3010 visits, ten active class-0x1F actors, and hash
`0x836e161c`. Those ten records now dispatch exact SPEC-02 presentation bindings:
all 190 class-0x1F animation records map to their assembly, hurt selector, and
attack selector with zero orphans, and paired frame 470 reports 3010 bindings.
Source entry `0x060532` and all 59 route-reachable state/substate contexts are
also exact-bound with 3010 target validations. Initial transition execution is
blocked because SPEC-02 omits its predicates, timer guards, writes, movement
arithmetic, and RNG order. The first stable route-4 global rectangle is now
native and source-bound: bound x/z `720/256`, x `752..1072`, z `272..400`,
with 301 paired applications. The Predator Warrior source locomotion bridge now
implements walk, the exact 10-tick stop, cleanup, and neutral return while
preserving the last directional facing. A discovered duplicate Track-2 start
at the native route-4 handoff is corrected; normal and paired emulator images
continue with coherent actors, audio ownership, camera, HUD, and both planes.
Coffee Shop minimum
penetration, the terrain-record interpreter, and camera target arithmetic are
separately blocked because the accepted SPEC-02 fixture omits their required
geometry and update rules. The neutral Button3 jump is blocked independently:
SPEC-02 names vector table `0x0243d2` and route witnesses but omits the exact
numeric signed 16.16 vectors, selector mapping, and branch order. Commit
`882b15b` implements the source-owned Button2 melee sequence with selectors
1..4, exact strike presentations, the 30-tick follow-up window, held-edge
rejection, and interruption preservation. Thirty-two host mutations, 26 Target
suppressions, paired Emulator, and direct selector-2/4 inspection pass. The
next vertical body is the source-complete portion of Predator Warrior Button1
weapon/projectile/resource authority; omitted projectile fields must remain
blocked rather than guessed. Enemy movement, damage, and dynamic spawn remain
pending; frame 2328 is not gameplay authority.

| Sequence | Card or card family | Result |
|---:|---|---|
| 1 | `INTEGRATE-01-PLAYER-AND-ENEMY` | Accepted player/enemy co-residency and ordering |
| 2 | `SALVAGE-03-COLLISION` | Isolate and promote collision evidence |
| 3 | `V2-2B` | Finish only the bounded writer-closure correction |
| 4 | `V2-B1` | Promote exact class `0x1F` HIT/KO |
| 5 | `INTEGRATE-02-COMBAT` | Integrate attack, contact, damage, HIT, and KO |
| 6 | `USER-03-COMBAT-FEEL-REVIEW` -> `REPAIR-03-COMBAT-ACTOR-ALIGNMENT` -> renewed `USER-03` | Correct the requested durable actor alignment before promotion |
| 7 | `PROMOTE-04-CAMERA-STAGE` | Promote approved camera/stage presentation |
| 8 | `PROMOTE-05-HUD` | Promote approved P1/P2 HUD presentation |
| 9 | `PROMOTE-06-PCM` | Promote approved PCM cue path |
| 10 | `SALVAGE-07-CDDA-RESIDENCY` -> `USER-07-CDDA-RESIDENCY-REVIEW` -> `PROMOTE-07-CDDA-RESIDENCY` | Prove audio/load ownership and manifests, then require explicit audible review |
| 11 | `REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION` -> corrected `INTEGRATE-03-PLAYABLE-SLICE` -> `HW-01-PROBE-3-VDP1-BUDGET-PRETEST` | Preserve the approved source-bound slice and prepare its isolated representative/909/overload physical prerequisite before physical execution |
| 12 | `ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS` -> `ORACLE-05-STREET-ALIEN-AI` -> `ORACLE-06-ROUND1-ENCOUNTER-RULES` | Read-only source research for the first live encounter; these may run serially while HW-01 remains at its physical hard stop |
| 13 | `SALVAGE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER` -> `PROMOTE-10-PREDATOR-WARRIOR-ACTION-CONTROLLER` | Build the bounded production player-action authority |
| 14 | `SALVAGE-11-STREET-ALIEN-AI` -> `PROMOTE-11-STREET-ALIEN-AI` | Build the bounded autonomous class-`0x1F` authority |
| 15 | `INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER` -> `REPAIR-10` -> first/renewed `USER-09` | Preserve the useful technical harness while recording that it is adapted, not source-closed or user-approved |
| 16 | `ORACLE-07` -> `ORACLE-08` -> `ORACLE-09` -> `SPEC-01` -> `REIMPLEMENT-12` -> `QA-12` -> renewed `USER-09` | Source-close and explicitly review `FIRST LIVE GAMEPLAY ENCOUNTER` behind the specification firewall |
| 17 | `REPAIR-11` -> `ORACLE-10` -> `ORACLE-11` -> `SPEC-02` -> `REIMPLEMENT-13` -> `QA-13` -> `USER-10` | R7C source-closes and implements the complete Predator Warrior Round 1 route through stable Round 2 handoff |
| 18 | `SALVAGE-08-FRONTEND` -> `QA-08-FRONTEND` -> `USER-08-FRONTEND` -> `PROMOTE-08-FRONTEND` | Promote title and four-character select only after explicit USER-10 acceptance |
| 19 | `INTEGRATE-04-COLD-BOOT-TO-ROUND1` | Integrate frontend into the already playable Round 1 route; direct diagnostic boot is acceptable during R7C |
| 20 | `ORACLE-01`, `ORACLE-02`, `ORACLE-03` | Complete title-to-credits and four-character source evidence |
| 21 | stage-segment templates -> `INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME` | Complete one reference character through credits |
| 22 | character templates -> `INTEGRATE-06-FOUR-CHARACTER-ROSTER` | Add the remaining three characters through one runtime |
| 23 | multiplayer templates -> `INTEGRATE-07-THREE-PLAYER-MULTIPLAYER` | Add input, joins, camera, combat, and resource peaks |
| 24 | `QA-09-RELEASE-HARDENING` | Repeatable build and soak hardening |
| 25 | `QA-10-FINAL-TITLE-TO-CREDITS-ACCEPTANCE` | Exact release acceptance for every character and multiplayer scope |

Exact dependencies, statuses, and predeclared successors are machine-checked
from the cards and `project_state.yaml`.

## 5. Nonblocking source-research lanes

The first-live-encounter Oracle cards are read-only, serial bodies. Goal Mode
may execute one at a time while `HW-01-PROBE-3-VDP1-BUDGET-PRETEST` remains
`READY_FOR_PHYSICAL`, using the predeclared `independent_read_only_cards`
mechanism. They may change only card-scoped source research, derived evidence,
coverage/migration state, and their own cards. They cannot change the approved
runtime, Probe 3 result, physical evidence, exact INTEGRATE-03 ISO,
`production_head`, or `SALVAGE-08`; they cannot advance physical status.

- `ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS` measures real input, movement,
  facing, four bounded attacks, timing, boxes, health, HIT/KO, interruption,
  and relevant RNG without claiming the complete move set.
- `ORACLE-05-STREET-ALIEN-AI` measures one complete class-`0x1F` behavior loop,
  scheduler order, timers, collision/damage, HIT/KO, and consumed RNG through
  controlled counterfactuals.
- `ORACLE-06-ROUND1-ENCOUNTER-RULES` separates measured encounter entry,
  spawn, bounds/lock, active/clear guards, unlock, and continuation from actor
  AI and presentation events.
- `ORACLE-07-PREDATOR-WARRIOR-ACTION-GRAPH-AND-EQUIPMENT` source-closes the
  bounded player controller: edge-owned close-combo advance, the 30-frame
  follow-up counter, held/startup/recovery behavior, contextual action
  selection, action-local equipment flag writers, facing latch, HIT
  cancellation, animation records, assemblies, and exact close-contact
  presentation identity.
- `ORACLE-08-ROUND1-NAVIGATION-AND-BOUNDS` source-closes the bounded Coffee
  Shop navigation authority: dynamic world-space player bounds, a
  non-rectangular obstacle/terrain route, player-versus-class-`0x1F` boundary
  separation, and the measured camera lock/unlock/next-lock sequence.
- `ORACLE-09-STREET-ALIEN-STATE-FACING-AND-PRESENTATION` source-closes the
  bounded type-12 class-`0x1F` actor: one-player target, authored approach,
  asymmetric crossing/lane state responses, state-owned facing/animation/
  assembly identity, attack RNG/timer, rendered HIT identity, scheduler, and
  HIT/KO/removal. Generic face-target, independent assembly cycling, and a
  guessed range threshold are explicitly forbidden.

Two identical captures and real perturbations were required for each body.
ORACLE-04 through ORACLE-09, SPEC-01, REIMPLEMENT-12, and QA-12 are technically
accepted. Corrected REIMPLEMENT-12 candidate `e237335` and QA-12 evidence
`f99df5e` pass Fast, Oracle, target build-only, two cold pinned-emulator runs
with exact 471-frame semantic equality, six rejecting mutations, and direct
visual review of the complete encounter. Renewed USER-09 is active; no user
approval is inferred.
ORACLE-06 proved that
the source opening is a withdrawal set piece, so the first live implementation
uses a source-bound, adapted one-alien KO/inactive clear. Facts not captured
remain `UNKNOWN` or `UNRUN`.

The later full-game Oracle cards remain read-only source research:

The three Oracle cards are read-only source research. They may be activated only
by Goal Mode and never write production runtime paths. They do not block the
current player/enemy integration:

- `ORACLE-01-FULL-REFERENCE-ROUTE`: two identical cold-boot-to-credits runs
  plus one input-independent perturbation control, including route, actors,
  spawns, collision/damage, animation, object stream, layers, palette,
  line-scroll, audio, continue/game-over, ending, and credits.
- `ORACLE-02-FOUR-CHARACTER-ACTION-MATRIX`: measure each character's movement,
  attacks, weapons/projectiles, special behavior, pickups/throws, HIT/KO,
  continues, and character resources.
- `ORACLE-03-ENDING-CREDITS-DELTAS`: measure final boss through credits for
  each character and classify common, Predator-shared, human-shared, and
  character-specific content.

Two deterministic runs and one real perturbation control are mandatory. Facts
not captured remain `UNKNOWN` or `UNRUN`.

## 6. Delivery roadmap

### R0 — Preserve old-build baseline and inventory systems

Record reproducible old-build identity, compile state, assets, diagnostics,
emulator readback, and worktree safety without changing production behavior.

**Exit:** baseline and inventory are reproducible; protected worktrees and
private artifacts are unchanged.

### R1 — Isolated salvage benches

Isolated salvage benches cover loading, input, actors, palettes, VDP2 stage,
HUD, PCM, diagnostics, collision, camera, CDDA, and residency. Every bench runs
DEV checks, a dedicated diagnostic, pinned-emulator self-review when target
facing, and human review when subjective.

**Exit:** each exercised subsystem has technical, fidelity, user, salvage,
blocker, interface, commit, and exact-next-experiment state.

### R2 — Define production interfaces and promote systems

Define production interfaces and promote only accepted, repaired, or explicitly
adapted behavior. Temporary adapters record wrapped implementation, interface,
regression locks, coupling, and deletion condition.

**Exit:** selected systems sit behind bounded Port V2 interfaces without losing
approved locks.

### R3 — Production player and enemy loop

Combine promoted player and enemy assets, animation, rendering, input, and one
background. Add no combat until co-residency and render ordering are proven.

**Exit:** player and class `0x1F` enemy coexist deterministically.

### R4 — Exact collision and combat

Salvage collision, finish the narrow V2-2B correction, promote exact HIT/KO,
then integrate attack, contact, damage, HIT, and KO one behavior at a time.

**Exit:** source differential, negative controls, emulator review, and explicit
combat-feel review pass.

### R5 — Promote approved presentation and audio

Promote approved camera/stage, P1/P2 HUD, and PCM behind production interfaces
without altering reviewed output.

**Exit:** production adapters reproduce every approved presentation/audio lock.

### R6 — CDDA, loading, and phase residency

Salvage and promote load ownership, CDDA ownership, phase manifests, legal
read windows, high-water, and canaries.

**Exit:** exact emulator readback rejects illegal overlap, fallback, missing
assets, and canary damage.

### R7A — Physical capability proof

First repair the promoted player/combat presentation boundary so selectors 1-4
carry their measured source action, animation, pose, pivot, grounding, and
active-window state. Then integrate combat, camera/stage, HUD, PCM, CDDA, and
residency in the exact normal-release composition. Expected visual identity
must originate from MAME/source evidence, never from the current Saturn
candidate's hashes.

**Exit:** all 12 capability conditions close through the required physical
Saturn procedure; emulator or user evidence is not substituted. This proves
the technical capability slice, not production control, AI, encounter clear,
or a playable Round 1 loop.

### R7B — First live gameplay encounter

Measure and implement only the Predator Warrior subset, one autonomous
class-`0x1F` street-alien loop, and one Round 1 encounter controller. Integrate
real controller input, current-state action/AI decisions, live overlap/damage,
player and alien HIT/KO, encounter clear, restored stage progression, and
continued movement. Machine tests use deterministic input ledgers; the human
checkpoint uses real interactive input.

The current live encounter is retained only as a technical prototype and
diagnostic harness. R7B now requires ORACLE-07 player action/equipment closure,
ORACLE-08 Coffee Shop navigation closure, ORACLE-09 class-`0x1F`
state/facing/presentation closure, SPEC-01 executable contracts, implementation
only from those contracts, and QA-12 cadence-1 semantic plus visual
differential review. This is an engineering clean-room boundary, not a formal
legal clean-room claim.

**Exit:** the player can approach or retreat, change lanes, choose when to
attack, miss, make contact, receive an enemy attack, KO the alien, clear the
encounter, and move afterward; no result is injected merely because a
fixed-frame or review-event count was reached. `USER-09-LIVE-ENCOUNTER-REVIEW` is
explicitly accepted.

### R8 — Frontend and cold boot into playable Round 1

Promote presentation-only frontend scenes, measured input semantics, four
selectable identities, loading ownership, and the route transition into Round
1. A versioned line-scroll scene operation is added only where source capture
requires it.

**Exit:** cold boot reaches title, credit/start, four-character select, confirm,
loading, and the real controller-driven Round 1 encounter. Loading the scripted
INTEGRATE-03 capability demonstration cannot satisfy this milestone.

### R9 — Complete source route and coverage ledgers

Extend the source route beyond the current 18,000-frame partial capture through
every boss, ending, and credits. Keep
`data/full_game_content_coverage.yaml`,
`data/four_character_action_matrix.yaml`, and
`data/ending_credits_matrix.yaml` authoritative for unknowns and coverage.

**Exit:** two matching full-route captures plus perturbation control are labeled
and every route body has a next experiment.

### R10 — Complete one reference-character game

For each stage segment run capture, package, behavior, integration, and QA cards
from the stage template. Re-enter physical testing only for a new workload
class: sprite peak, VDP2 effect, line scroll, boss scale, loading pattern, audio
ownership pattern, or AI/collision peak.

**Exit:** one character completes title through ending and credits with no
authored fallback.

### R11 — Four-character roster

Add Predator Warrior, Major Schaefer, Predator Hunter, and Linn Kurosawa through
one common player runtime and measured `PortV2CharacterDef` differences. Do
not duplicate the player engine.

**Exit:** each of all four playable characters completes an independent
title-to-credits acceptance route.

### R12 — Three-player multiplayer and release hardening

Prove Saturn controller/multitap topology, joins, credits/continues, multi-actor
camera, collision/combat, resource peaks, and physical soak for up to three
simultaneous local players. Then produce repeatable clean builds and run cold
boots, full routes, worst encounters, audio, controller, loader, and long soak
coverage.

**Exit:** declared roster/player-count parity and the release-hardening matrix
pass on physical hardware.

### R13 — Final title-to-credits release acceptance

Repeat the complete matrix on the exact release image for every playable
character and the declared multiplayer cases. Archive hashes, commands,
environment, provenance, captures, user approvals, and physical evidence.

**Exit:** the complete four-character title-to-credits release is reproducible,
evidence-complete, physically stable, and all declared conditions are closed.

## 7. Reusable later-card patterns

`docs/task_cards/templates/STAGE-SEGMENT-TEMPLATE.md` expands one measured
segment into capture, package, behavior, integration, and QA bodies.
`CHARACTER-EXPANSION-TEMPLATE.md` binds one measured character definition,
actions, collision, HUD/audio, ending, full route, and user review.
`MULTIPLAYER-TEMPLATE.md` covers topology, joins, camera, combat, resource
peaks, and physical soak. Goal Mode instantiates only the next evidence-backed
body; hundreds of speculative cards are prohibited.

## 8. Capability-slice conditions

| # | Condition |
|---:|---|
| 1 | Exact `avspu` identity and deterministic package provenance |
| 2 | Two identical MAME gameplay-oracle runs plus perturbation control |
| 3 | Controller input and one playable actor match semantic oracle |
| 4 | One class `0x1F` enemy update/animation matches, including HIT/KO |
| 5 | Source collision, damage, hit response, and KO match |
| 6 | Camera/stage progression and 352 crop/framing contract match |
| 7 | VDP1/VDP2 objects, layers, priority, palette, and scanout match |
| 8 | SCSP PCM event path is audible and correctly timed |
| 9 | CDDA music is audible with no illegal data-read overlap |
| 10 | Work-RAM/cart/VDP1/VDP2/SCSP high-water and canaries pass |
| 11 | Physical draw-end, CPU/transfer timing, and input latency pass |
| 12 | Normal-release cold boot and ten-minute physical soak pass |

No partial condition advances the count.

## 9. Full-game completion conditions

Completion requires cold boot through credits for all four characters, every
stage and transition, up to three local players for the declared multiplayer
matrix, complete audio/load ownership, no authored fallback, physical proof for
every workload class, long soaks, and deterministic release provenance.

## 10. Update rules

1. Goal Mode activates one dependency-ready implementation card at a time.
2. `project_state.yaml` owns volatile state and protected-worktree records.
3. This file is the only roadmap.
4. Task cards predeclare every eligible successor.
5. The migration map records independent technical, fidelity, and user state.
6. Coverage and character claims remain `MEASURED`, `ADAPTED`, or `UNKNOWN`.
7. Approved components stay locked until renewed review identifies risk.
8. Structural, host, MAME, emulator, user, normal-release, and physical claims
   remain separately labeled.
9. Close each approved implementation card with a coherent commit, push to
   `private-origin`, and verify the exact remote SHA before successor activation.
10. Reuse the dependency-continuous existing branch/worktree by default. Create
    isolation only for actual parallelism, incompatible dependencies, unsafe
    dirty state, or a genuinely separate development line.
11. Never reset, clean, stash, rebase, broadly restore, force-push, broad-stage,
    discard private evidence, or infer human approval from silence.
