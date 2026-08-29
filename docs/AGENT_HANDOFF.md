# Active checkpoint
`project_state.yaml` is machine-readable truth and `docs/PARITY_PLAN.md` is the only roadmap. Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` on `codex/avp-playable-loop-pivot`; preserve private evidence and locks.

## Workflow pivot / Preserved evidence work
Resume the AvP salvage Goal; preserve `SALVAGE-00-OLD-BUILD-BASELINE`, `USER-01-PLAYER-BASELINE-REVIEW`, `597f4ed517d4e715d814ff841bd00d3977803f85`, and all accepted evidence.

## Preserved authority
- ORACLE-11/SPEC-02 remain accepted: 1,517 writers, zero gaps in the sole 94 x 10 matrix; `0x0abdd2` is packed-BCD score.
- Preserve accepted native player, scheduler, Coffee Shop navigation/camera, presentation, collision, audio/loading, startup, P1-only HUD, one Track-2 start, background/palette/priority, and visual-QA locks.
- Native Round 1 solely owns first-encounter gameplay; retained code is presentation-only. Preserve the accepted 575-sample authority checkpoint, Predator identity, Button1/Button3, and tile residency locks.
- USER-09 is `CHANGES_REQUESTED`; SALVAGE-08 inactive; physical Saturn `UNRUN`.

## Coffee Shop scene-population gate
The first Button1 collision is now source-ordered. Route-4 eligibility is sampled at scheduler-invocation entry; player locomotion/weapon actor fields use source state projection; record-type `4` executes before record-type `12`; new allocations enter collision registration on the next source scheduler invocation; and collision boxes come from the current animation record while source actor `+0xa5/+0xa6` fields remain intact.

The parent/child trajectory is exact through source frame 2287. Frame 2288 has no damage. On source scheduler frame 2306 slot `0x00ff8880` uses attack record `0x030cd2`, leaves `0xff9d00` untouched, writes `0xffa180` from 87 to 56, and naturally allocates class-`0x4e`, visible at frame 2307. No projectile variant, authored delay, or input rebaseline is used.

Focused SPEC and host checks reject 89 and 161 real mutations; target wiring rejects 119 suppressions; the scene census rejects eight mutations. The full-scene gaps are: missing lifetimes 413, spawn/despawn 1,382, unsupported states 30, collision/damage 94, route/camera 3, audio/load 281, unowned Saturn actors 0, unidentified class/type pairs 0, retained gameplay authorities 0. Against `e24686b`, unsupported states improve by seven; missing lifetime matches rise by 26 because the corrected target changes downstream reaction/lifecycle identity; spawn/despawn improves by nine.

Collision-time reaction ownership and the complete source HIT return are now native. The frame-2306 damage write changes only the source outer HIT state; visible frame 2307 retains substate `0x0000` and animation `0x0012eb5c`; frame 2308 binds the source selector-`0x36` reaction; phases `0x0200` through `0x020a`, motion, landing, bounce, RNG hold, terminal animation, and the guarded normal return execute in source order. The preserved frame-2413 fields select action `0x16`; the generic action-selector-`0x36` presentation is rejected in HIT context.

Implementation checkpoint `58bfeacb88360c48ec309a5bb057ca8e17724f92` is pushed and remote-equal. Fast, Oracle, LiveEncounter Target, 100 SPEC mutations, 161 native mutations, 119 Target suppressions, eight scene mutations, and the fixture-driven tile-residency refusal control pass. Two commit-bound pinned Emulator runs produce identical 575-sample ledgers at ISO `f2d0ec57fe4d9b02d6a7e578145039c3080ef450ce9a3801fdcba6b90b1df287`; four chronology mutations reject and presentation decode failures are zero. The sparse decoder now includes every reachable HIT/return assembly without widening the measured tile carve.

Window-only Windows Graphics Capture covers the correctly aligned source-visible frames 2280..2310; cadence sheet `82fb9fed7b16671ddcb77ae10734bc864998770d6ad0c503470e49005e65b8e6`. Direct inspection passes Predator identity, staff continuity, natural projectile/impact presentation, P1-only HUD, both planes, palette and priority. The prior helper's diagnostic/source frame conflation was corrected against the paired ledger. The apparent second row labelled `WARRIOR` is the source P1 equipment meter; no `Maj.Schaefer` P2 panel is present.

The refreshed scene gaps are: missing lifetimes 404, spawn/despawn 1,379, unsupported states 30, collision/damage 94, route/camera 3, audio/load 281, unowned Saturn actors 0, unidentified class/type pairs 0, retained gameplay authorities 0. Missing lifetimes improve by nine and spawn/despawn by three; no gap count increases.

`d04a65a2253175c6e820140feefc35419e2cca07` remains the latest fully accepted runtime candidate until the complete Coffee Shop zero-gap gate passes.

## Exact next experiment
Bind the earliest remaining divergence at visible frame 2307 for class-`0x4e` slot `0x00ffbd80`. Source allocates and presents variant 1 in the same visible frame with animation `0x0008df2c`; native allocates in frame 2307 with animation zero and initializes in frame 2308 as `0x00092914`. Use the accepted class-`0x4e` variant-1 Oracle/SPEC contract to make allocation and presentation initialization source-ordered in the owning scheduler transaction. Preserve the accepted frame-2306 collision/damage and complete class-`0x1f` HIT return. Do not add an authored frame delay or relabel a later generic effect.
