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

Collision-time reaction ownership and the complete source HIT return are now native. The frame-2306 damage write changes only the source outer HIT state; visible frame 2307 retains substate `0x0000` and animation `0x0012eb5c`; frame 2308 binds the source selector-`0x36` reaction; phases `0x0200` through `0x020a`, motion, landing, bounce, RNG hold, terminal animation, and the guarded normal return execute in source order. The recovery transition now returns at visible frame 2317 with substate `0x0200`, animation `0x0012e04c`, and fixed-point position `0x02ac4c00/0x0136d600`; the following scheduler visit launches at frame 2318. The preserved frame-2413 fields select action `0x16`; the generic action-selector-`0x36` presentation is rejected in HIT context.

`d04a65a2253175c6e820140feefc35419e2cca07` remains the latest fully accepted runtime candidate until the complete Coffee Shop zero-gap gate passes.

The source projectile-parent effect boundary is now native. Source caller `0x02f94c`, allocator `0x08f0c6`, dispatcher `0x08f080`, phase-bit guard, type-24/class-`0x49`/variant-0 identity, state-0 fallthrough, timer, LIFO release, and record-type-4-before-record-type-12 order are fixture-bound. Variant-10 class-`0x4e` impact remains naturally produced from the frame-2306 `0x030cd2` damage write. No projectile suppression, authored delay, or choreography rebaseline is present.

Incremental implementation checkpoint `9a6c1010a72d57c7c6c5fabfb52a0e8ddd450d8b` closes the frame-2371 fixed-slot presentation divergence. Source allocators `0x01773e`/`0x017754` do not clear animation presentation on release/reuse: native now preserves animation record, assembly, timer, and signed branch until the reused actor's state-0 initialization. Slot `0x00ff8800`, record-type `4`, class `0x04`, variant `2` is source-exact at visible frame 2371 (`0x0003088c`, `0x00030b28`, timer `1`, branch `-32768`) and initializes naturally at frame 2372. No frame fit, suppression, or choreography change is present.

SPEC is `fd65f15e44695ccdc65c2e59516ddb11ccd7315fe327f63c20a34ab00a51169f`; fixture is `401253d2279846118b96c04b8c9ad6d41272102f3e3b203bb0d55ed3f25e9ff2`. Fast, Oracle, 110 SPEC mutations, 179 native mutations, nine scene mutations, 123 Target suppressions, LiveEncounterBench Target, and two commit-bound byte-identical 575-sample Coffee Shop Emulator ledgers pass. Normalized ISO is `4dda2cf243c5f0f715aa2610ea078784bd7a93f525ab44708c98c1534b80c7e6`; sample payload is `0afd341dd78d367adf5b323cb3b5e6d99b762d65844f36b64cfe330f6adce16a`.

Fresh window-only WGC covers frames 2368..2374. Sheet `9d76768c838f6a7af2c8fa45b7c7b1347ac2b6ca43a094139dbce64f68526bd3` and clip `c7faf1b5f585173fca90639557ea08ab5bdba4320e66c28bf889071355d22502` pass direct inspection with stable Predator identity, retained slot presentation through frame 2371, coherent Coffee Shop planes, palette, and priority, and no visible actor-family pop. The whole-scene gaps remain `335 / 1,293 / 3 / 94 / 3 / 281`; no category increases because the repaired per-frame presentation was already inside an exact actor lifetime. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero; the complete Coffee Shop gate remains open.

## Exact next experiment
Bind the next earliest causal scene divergence at record-type `12`, class `0x1f`, slot `0x00ffa300`, visible frame 2378. Source attack selector `2` differs from native selector `1` at frame 2378; animation diverges at frame 2379 and later motion/facing/state differences are downstream. Recover the accepted selector predicate, state/substate guard, animation/assembly write, facing, and scheduler ordering from SPEC-02; amend only the existing fixture if an implementation-required field is absent. Do not fit the frame or rebaseline input. Preserve the fixed-slot frame-2371 correction, exact frame-2287/2306/2307 chronology, and all player, class-`0x1f` identity, visual, HUD, audio, collision, and population locks.
