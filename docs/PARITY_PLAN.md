# AvP native Saturn roadmap

This is the project's only roadmap. State is `project_state.yaml`; subsystem
decisions remain in `data/port_v2_migration_map.yaml`; the existing task cards
own bounded execution. No new controller, coverage system or task hierarchy.

CURRENT_TASK: REIMPLEMENT-13-SOURCE-CLOSED-ROUND1

## Current delivery: R7C

One-player Predator Warrior from direct Round 1 entry through the full stage,
boss defeat, stage clear and stable Round 2 handoff. Source is `avspu`,
USA 940520. No frontend, other characters, multiplayer or Round 2 gameplay.
A faithful first scene is a delivery checkpoint, not the requested full level.

The owner requests a playable arcade-faithful level on 2026-09-07. This is a
delivery target, not permission to waive fidelity, visual, audio or physical
gates. At the current audit it is AT RISK, not a defensible completion promise.

## Evidence-based assessment (2026-09-07)

- P2 source census covers frames 1972..15193, including the stable Round 2 seam.
  P3 specifications are recorded complete. Preserve both; neither proves native
  completion or that every implementation field is executable.
- P4 Coffee Shop is RED. The checked report covers source frames 1972..5566.
  Its native diagnostic sequence has 90,178 actor rows after class0e; not a
  verified full native Round1. Missing lifetimes103; unowned health events93;
  unowned audio/load279. Class0e resolves pool gaps, not the independent tick rule.
- Normal controller input is real, but main's live callback uses captured-frame
  update-count and phase tables to dispatch gameplay. This is an interactive
  authority defect, not a cosmetic mismatch. Details and gates are on the card.
- The scene generator hardcodes retained authority to zero. That field does not
  audit captured-schedule authority; no acceptance may rely on that literal.
- Latest native work lacks a current accepted Target image. Target and transition
  Emulator/WGC gates are exhausted, separately from older passing evidence.
- The old workflow privileged row matching and long instruction histories.
  Current work must retire interactive-program and playable-scene risks first.

## Delivery sequence inside the existing REIMPLEMENT-13 card

1. Close the interactive scheduler/route-authority boundary from source rules.
   Isolate captured cadence as diagnostic projection. Prove identical current
   state/input with shifted observation labels has identical gameplay, while
   source-supported changed input changes outcomes. Preserve legitimate timers.
2. Establish a current build and normal interactive capture path when its
   exhausted gates are explicitly reopened. First use read-only provenance/
   packaging preflight; no repeated blind boot attempts. Keep exact hashes.
3. Close Coffee Shop's remaining complete gameplay programs and event owners.
   Repair the earliest causal mismatch by owning program, not one event row.
   Complete remaining source-owned presentation programs in the same scene;
   do not silently omit actors or normalize gameplay consequences.
4. Pass the complete Coffee Shop gate with real varied input and entry-to-exit
   visual/audio evidence. Rerun completed scenes for shared-system changes.
5. Continue in accepted source-scene order, reusing the proven title-specific
   systems and P2/P3 content. Implement later enemy/boss, route and clear/handoff
   families through their full reachable branches, not new per-frame cards.
6. Freeze exact full-round candidate -> QA-13 -> explicit USER-10. Only accepted
   USER-10 unlocks SALVAGE-08. No scene/body checkpoint self-approves a review.

Prioritize bodies by gameplay authority, current gaps explained and reuse in
later scenes. Keep the current raw categories AND unresolved program/controller/
actor/audio/load owners visible; do not treat event count as effort estimate.

## Same-day decisions, not a promise of unmeasured throughput

Use the first bounded delivery pass (at most 90 minutes) to resolve or precisely
block interactive scheduler separation and build readiness. Produce a current
interactive smoke image only if source rules and gate authority permit it.
Do not spend that pass polishing independent presentation rows.

After that pass report the actually playable extent and the remaining reusable
programs. If normal interactive Coffee Shop is not demonstrably progressing,
state that full Round 1 today is not supported; do not lower the finish line.
Continue dependency-safe implementation, not another planning cycle.

Before end of day deliver the best verified interactive package available with
exact scope and discrepancies. A partial Coffee Shop build must be labelled
partial, and a source/MAME reference must never be presented as the Saturn port.
Full-level delivery requires the actual complete route and QA, however long it
takes. A status/package deadline is not a substitute for a quality gate.

## Quality and architecture locks

Independent source evidence -> executable SPEC/fixtures -> native C -> differential.
No fixed-frame outcome, actor teleport, authored clear, trace-owned scheduler,
visual guess, fallback or runtime 68000 interpretation. Preserve real controls,
Predator identity and neutral facing, reviewed melee/staff, Button1/3, native
class-0x1F tracking, collision/HIT/KO, navigation/camera, P1-only startup, native
PCM and one source-owned Track-2 start, background bridge/palette/priority.

Follow TEST_PLAN risk-based cadence. Full source/static/host, paired emulator,
continuous visual/audio and explicit human feedback are different evidence tiers.
The production_head, frozen candidate_head and pushed HEAD remain distinct.
Physical Saturn is UNRUN; HW-01 READY_FOR_PHYSICAL does not block software work.

No memory-map revision or asset squeeze to meet a deadline. Existing runtime,
tile, scratch, SPEC, VDP1 and linked-image budgets are separate. Hardware acceptance
still requires representative and 909-tile peaks, 15% measured timing/memory
margins where the physical contract requires them, final scanout, control,
PCM/CDDA, normal release and soak. Host/emulator results are not that proof.

## Milestone index (historical and future, not today's queue)

### R0 - Preserved old-build baseline
### R1 - Isolated salvage benches
### R2 - Production interfaces and accepted promotions
### R3 - Production player/enemy integration
### R4 - Collision, damage, HIT and KO
### R5 - Reviewed presentation, camera, HUD and PCM
### R6 - CDDA, loading and residency

Accepted scope remains in state, migration ledger, evidence and original cards.
Do not repeat those promotions. V2-2B remains bounded source/host evidence, not
an acceptance of the whole game's loading, controller input or physical behavior.

### R7A - Physical capability proof

Parked at the existing pretest boundary; consult HARDWARE_TEST for real work.

### R7B - First live encounter

Technical substrate only. USER-09 is CHANGES_REQUESTED; it does not unlock frontend.

### R7C - SOURCE-CLOSED ROUND 1 END-TO-END PLAYABLE SLICE

Active sequence:
ORACLE-10 -> ORACLE-11 -> SPEC-02 (recorded accepted, bounded amendments allowed)
-> REIMPLEMENT-13 (active, Coffee Shop RED)
-> QA-13-ROUND1-END-TO-END-DIFFERENTIAL
-> USER-10-ROUND1-PLAYTHROUGH-REVIEW.

### R8 - Frontend after accepted USER-10
### R9 - Remaining full-game source coverage
### R10 - Complete one-reference-character game
### R11 - All four playable characters
### R12 - Up to three simultaneous local players
### R13 - Full title-to-credits release acceptance

R8..R13 are later work, not part of R7C. Their existing cards/ledgers retain
the earlier plan; no new hierarchy is authorized.

## History

Superseded running narratives remain in Git. The last pre-delivery-focus
version can be read with `git show HEAD~1:docs/PARITY_PLAN.md` at this change,
or by finding the "Focus R7C delivery on interactive authority" commit's parent.
Historical next-step prose is not current authority.
