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

`d04a65a2253175c6e820140feefc35419e2cca07` remains the latest fully accepted runtime candidate until the complete Coffee Shop zero-gap gate passes.

## Exact next experiment
After committing the current source-frame-2306 correction, bind the earliest remaining divergence at visible frame 2307: source slot `0x00ffa180` has already received the damage/state write but retains substate `0x0000` and animation `0x0012eb5c` until its next record-type-12 update; native prematurely exposes HIT substate `0x0002` and animation `0x0012dd50`. Preserve the accepted health write and class-`0x4e` impact while separating collision-time reaction state from next-scheduler presentation binding. Then rerun the whole Coffee Shop census.
