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

CURRENT_TASK: INTEGRATE-03-PLAYABLE-SLICE

## 4. Current salvage queue and production extension

The accepted player, enemy, combat, camera/stage, P1/P2 HUD, PCM, CDDA, and
phase-residency results remain regression locks. INTEGRATE-03 is the active
production body; ARCH-01 itself did not change runtime behavior.

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
| 11 | `INTEGRATE-03-PLAYABLE-SLICE` | Integrate and physically prove the capability slice |
| 12 | `SALVAGE-08-FRONTEND` -> `QA-08-FRONTEND` -> `USER-08-FRONTEND` -> `PROMOTE-08-FRONTEND` | Promote title and four-character select |
| 13 | `INTEGRATE-04-COLD-BOOT-TO-ROUND1` | Cold boot through Round 1 gameplay |
| 14 | `ORACLE-01`, `ORACLE-02`, `ORACLE-03` | Complete title-to-credits and four-character source evidence |
| 15 | stage-segment templates -> `INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME` | Complete one reference character through credits |
| 16 | character templates -> `INTEGRATE-06-FOUR-CHARACTER-ROSTER` | Add the remaining three characters through one runtime |
| 17 | multiplayer templates -> `INTEGRATE-07-THREE-PLAYER-MULTIPLAYER` | Add input, joins, camera, combat, and resource peaks |
| 18 | `QA-09-RELEASE-HARDENING` | Repeatable build and soak hardening |
| 19 | `QA-10-FINAL-TITLE-TO-CREDITS-ACCEPTANCE` | Exact release acceptance for every character and multiplayer scope |

Exact dependencies, statuses, and predeclared successors are machine-checked
from the cards and `project_state.yaml`.

## 5. Nonblocking full-game evidence lane

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

### R7 — Integrated playable capability slice

Integrate combat, camera/stage, HUD, PCM, CDDA, and residency in the exact
normal-release composition.

**Exit:** all 12 capability conditions close through the required physical
Saturn procedure; emulator or user evidence is not substituted.

### R8 — Frontend and cold boot through Round 1

Promote presentation-only frontend scenes, measured input semantics, four
selectable identities, loading ownership, and the route transition into Round
1. A versioned line-scroll scene operation is added only where source capture
requires it.

**Exit:** cold boot reaches title, credit/start, four-character select, confirm,
and Round 1 gameplay.

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
