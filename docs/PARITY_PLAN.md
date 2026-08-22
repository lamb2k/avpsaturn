# AvP salvage, promotion, and parity roadmap

This is the project's only roadmap and active backlog. `project_state.yaml`
owns machine-readable state; `data/port_v2_migration_map.yaml` owns subsystem
migration decisions; task cards own bounded work. None is a second roadmap.

## 1. Goal and method

Deliver a native, capture-faithful Sega Saturn port of *Alien vs. Predator*.
The first acceptance target is a normal-release physical capability slice; the
eventual target is the complete three-character, three-player port.

Development is an interactive human-in-the-loop loop:

```text
existing subsystem -> isolated salvage bench -> focused machine validation
-> Saturn diagnostic and emulator self-review -> human review when subjective
-> salvage decision -> port_v2 interface promotion
-> integration with one additional dependency -> repeat
```

The old mixed runtime and the playable-skeleton prototype are reusable sources,
not production gameplay authority. Lab or prototype success does not advance a
parity, emulator-acceptance, normal-release, or physical-capability gate.

## 2. AvP performance and evidence contract

AvP passes on its own measured workload. The integrated physical slice requires
stable NTSC cadence, deterministic input-visible behavior, no sustained skipped
or repeated fields, at least 15% measured VDP1 draw-end and total-frame margin
at the representative and 909-tile peak workloads, at least 15% usable memory
headroom with canaries, no combat-time data reads while CDDA owns the drive,
timed PCM and continuous CDDA, correct 352x224 framing, and a ten-minute soak
with no corruption, fallback, hang, missed field, or audio loss.

Machine validation, fidelity measurement, Saturn emulator review, human
approval, and physical proof are separate statuses. A passing emulator check is
not human approval or physical evidence. MSHvSF remains a non-gating,
post-slice quality calibration only.

## 3. Preserved baseline and paused work

The accepted Tranche 2A foundation, canonical artifact hashes, capability gate,
dirty primary worktree, playable-skeleton prototype, and dirty V2-2B
validator-correction worktree are preserved in `project_state.yaml`.

V2-2B remains unresolved with disposition `CORRECTIONS_REQUIRED`. It is a
dependency for exact HIT/KO production promotion, not for loading, controller
input, actor assets, actor rendering, actor animation, palette, stage, HUD, PCM,
or diagnostic salvage benches.

CURRENT_TASK: USER-02-ENEMY-BASELINE-REVIEW

## 4. Dependency-ordered active backlog

| Order | Card | Kind | Dependencies |
|---:|---|---|---|
| 1 | SALVAGE-00-OLD-BUILD-BASELINE | SALVAGE | None |
| 2 | SALVAGE-01-PLAYER-LOAD-RENDER-INPUT | SALVAGE | SALVAGE-00 |
| 3 | USER-01-PLAYER-BASELINE-REVIEW | USER_REVIEW | SALVAGE-01 |
| 4 | REPAIR-01-PLAYER-CROP-PIVOT | REPAIR | SALVAGE-01, USER-01 feedback |
| 5 | PROMOTE-01-PLAYER-PIPELINE | PROMOTE | SALVAGE-01, REPAIR-01, USER-01 |
| 6 | SALVAGE-02-ENEMY-RENDER-ANIMATION | SALVAGE | SALVAGE-00 |
| 7 | USER-02-ENEMY-BASELINE-REVIEW | USER_REVIEW | SALVAGE-02 |
| 8 | PROMOTE-02-ENEMY-PIPELINE | PROMOTE | SALVAGE-02, USER-02 |
| 9 | INTEGRATE-01-PLAYER-AND-ENEMY | INTEGRATE | PROMOTE-01, PROMOTE-02 |
| 10 | SALVAGE-03-COLLISION | SALVAGE | SALVAGE-00 |
| 11 | V2-2B | REPAIR | Paused; independent correction body |
| 12 | V2-B1 | PROMOTE | SALVAGE-03, accepted V2-2B |
| 13 | INTEGRATE-02-COMBAT | INTEGRATE | INTEGRATE-01, SALVAGE-03, V2-B1 |
| 14 | USER-03-COMBAT-FEEL-REVIEW | USER_REVIEW | INTEGRATE-02 |
| 15 | SALVAGE-04-CAMERA-STAGE-LAYERS | SALVAGE | SALVAGE-00 |
| 16 | USER-04-STAGE-REVIEW | USER_REVIEW | SALVAGE-04 |
| 17 | SALVAGE-05-HUD-PCM | SALVAGE | SALVAGE-00 |
| 18 | USER-05-HUD-PCM-REVIEW | USER_REVIEW | SALVAGE-05 |
| 19 | REPAIR-05-HUD-COLORS | REPAIR | SALVAGE-05, USER-05 feedback |
| 20 | SALVAGE-05B-PLAYER-2-HUD | SALVAGE | SALVAGE-05, REPAIR-05, USER-05 feedback |
| 21 | INTEGRATE-03-PLAYABLE-SLICE | INTEGRATE | combat, stage, HUD/PCM repairs and reviews |

Only one implementation card is active. A pending `USER_REVIEW` card may be
bypassed only by a card it predeclares as dependency-safe and incapable of
altering the reviewed result. Exact dependencies live in the cards and are
machine-checked; abbreviations in this table are descriptive.

## 5. Delivery roadmap

### R0 — Preserve old-build baseline and inventory systems

Record reproducible old-build identity, compile state, profiles, assets,
diagnostics, emulator readback, and worktree safety without changing production
behavior. Retain neutral initial decisions for unexercised subsystems and record
SALVAGE-00 evidence only for the subsystems it exercised.

**Exit:** baseline evidence and inventory are reproducible; no dirty worktree or
private artifact was altered.

### R1 — Isolated salvage benches

Run bounded benches for:

- loading and memory ownership;
- controller input;
- player assets, rendering, and animation;
- enemy assets, rendering, and animation;
- palette and CRAM;
- VDP2 background and stage layers;
- HUD;
- PCM;
- diagnostics and emulator readback.

Collision and camera receive their own later bounded cards before integration.
Every bench performs DEV checks plus a dedicated Saturn diagnostic and emulator
self-review. Visible or audible output receives a human checkpoint.

**Exit:** each inventoried system has independent technical, fidelity, user,
salvage-decision, blocker, and exact-next-experiment state.

### R2 — Define production interfaces and promote systems

Define clean, narrow `port_v2` interfaces and promote only systems whose bench
and required human review support `SALVAGE_AS_IS`,
`SALVAGE_WITH_ADAPTER`, or completed `REPAIR`. A `REPLACE` decision creates
a new bounded task card; it does not authorize a broad rewrite.

**Exit:** promoted subsystems are isolated from authored-controller coupling and
carry regression locks for approved behavior.

### R3 — Production player loop

Combine promoted loading, controller input, player assets, player animation,
player rendering, and one promoted background behind production interfaces.

**Exit:** the player loop passes focused deterministic checks, emulator
self-review, and its approved visual/feel contract.

### R4 — Enemy rendering and animation

Add promoted enemy assets, rendering, and animation first as a stationary actor,
then with one deterministic movement behavior. Integrate only with the promoted
player pipeline.

**Exit:** player and enemy coexist without regressing either approved component.

### R5 — Combat one behavior at a time

Salvage collision, then add attack, collision selection, contact, damage, HIT,
and KO as separate bounded behaviors. Resume and accept V2-2B before exact
HIT/KO promotion; earlier player/enemy/stage/diagnostic work does not wait for
it. V2-B1 promotes the accepted exact HIT/KO boundary behind a production
interface before combat integration.

**Exit:** deterministic attack-to-KO behavior passes source differential,
negative controls, emulator self-review, and explicit combat-feel review.

### R6 — Camera, stage layers, priority, palette, and framing

Salvage and promote camera behavior, VDP2 scroll3/scroll2 layers, priority,
palette ownership, and 384-to-352 framing one component at a time.

**Exit:** approved stage composition and camera behavior pass readback and
regression checks without altering approved actor presentation silently.

### R7 — HUD, PCM, loading, CDDA, residency, and canaries

Add promoted HUD and PCM, then loading phases, CDDA ownership, residency,
high-water telemetry, and canaries one component at a time. Visible and audible
results require explicit user review; source timing and ownership remain machine
claims.

**Exit:** exact normal-release emulator readback shows no missing asset, illegal
drive overlap, canary damage, fallback, or unmeasured required counter.

### R8 — Integrated physical capability slice

Build the exact normal `release-normal-release` image and test controller,
player, class `0x1F` enemy, movement, animation, attacks, collision, damage,
HIT/KO, camera/stage, VDP1/VDP2, palettes, HUD, PCM, CDDA, residency, timing,
latency, scanout, and ten-minute soak on physical Saturn.

**Exit:** all 12 capability conditions close against the exact image with no
authored or diagnostic fallback.

### R9 — Round 1 with one character

Expand encounter by encounter through all Round 1 enemies, interactions, boss,
stage clear, continue, and failure paths. Each new system or workload class
re-enters the salvage/promotion loop.

**Exit:** Round 1 is fully playable on normal release with no authored gameplay
fallback.

### R10 — Complete single-player game

Apply the production pipeline across all stages and transitions for one
character. Run physical coverage for every new sprite, VDP2, loading, audio,
boss, collision, or AI workload class.

**Exit:** cold boot reaches the ending with stable pacing, complete audio, all
transitions, and no diagnostic content or authored fallback.

### R11 — Roster and multiplayer

Add all three original playable characters and three simultaneous local players
through a documented Saturn multitap/controller topology. Any reduced scope
requires an explicit user decision.

**Exit:** complete character and player-count parity for the selected release
scope with physical multiplayer soak.

### R12 — Release-candidate hardening

Produce repeatable clean builds and the final manifest; run cold boots,
full-route, worst-encounter, audio, controller, loader, and long soak coverage.

**Exit:** zero crash, fallback, canary, draw-end, late-read, missed-field, or
audio-loss failures over the declared matrix.

### R13 — Release acceptance

Repeat the full acceptance matrix on the exact release image and archive hashes,
commands, environment, captures, provenance, user approvals, and physical
evidence.

**Exit:** the complete release scope is reproducible, evidence-complete,
physically stable, and all declared conditions are closed.

## 6. Capability slice conditions

| # | Condition |
|---:|---|
| 1 | Exact `avspu` identity and deterministic package provenance |
| 2 | Two identical cold-boot MAME gameplay oracle runs plus perturbation control |
| 3 | Controller input and one playable actor match semantic oracle |
| 4 | One class `0x1F` enemy update/animation matches, including HIT/KO repoints |
| 5 | Source collision, damage, hit response, and KO match |
| 6 | Camera/stage progression and 352 crop/framing contract match |
| 7 | VDP1 objects and VDP2 layers/priority/palette/final scanout match |
| 8 | SCSP PCM event path is audible and correctly timed |
| 9 | CDDA music is audible with no illegal data-read overlap |
| 10 | Live work-RAM/cart/VDP1/VDP2/SCSP high-water and canaries pass |
| 11 | Physical VDP1 draw-end, CPU/transfer timing, and input latency pass |
| 12 | Normal-release cold boot and ten-minute physical soak pass |

No partial condition advances the count. Record exact image/profile hashes,
commands, environment, evidence tier, and artifacts in the evidence ledger.

## 7. Full-port completion conditions

Completion requires cold boot through the full game and ending, every selected
character and player count, all stages and transitions, complete audio and
ownership, no authored fallback, passing performance for every workload class,
long physical soaks, and deterministic release builds with archived provenance.

## 8. Update rules

1. Goal Mode activates one dependency-ready implementation card at a time.
2. `project_state.yaml` owns volatile state and preserved-worktree records.
3. This file is the only roadmap.
4. Task cards are the work queue and predeclare every eligible successor.
5. The migration map records independent technical, fidelity, and user status.
6. New mapping is demand-driven by a failing experiment.
7. Approved components are locked until renewed review identifies the risk.
8. Structural, MAME, emulator, user, normal-release, and physical claims remain
   separately labeled.
