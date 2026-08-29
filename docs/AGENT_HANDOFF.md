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

Incremental implementation checkpoint `9b6835c05a301de27bdb8b9e6bca0ba62e377d65` closes the selector/timing boundary that followed the fixed-slot correction. Class-`0x1f` action `0x16` now performs the single accepted RNG transaction at `0x017c5e` and reuses that result across the inner-`0x08` guard, fallback branch, and timer selection. The accepted frame-2377 seed transition `0xc9a2 -> 0x5cfe` produces selector `2` and record `0x0012ec74` at frame 2378; a second RNG call is rejected. Record-type-4 actors allocated after a lower scheduler slot has already passed also remain collision-registration-pending through state-0 initialization and register on the next source scheduler invocation. This prevents the premature frame-2288 write while preserving the source frame-2306 `0x030cd2` damage write and natural frame-2307 class-`0x4e` impact.

SPEC is `051d3047cd763f80da0e98e83e5c6d85ddc0b887ecf66334e7d279d1fb5a00ce`; fixture is `4cf23d3b5c32649a8804acdcd3d740436a1490759c4d9bbb3550b49c0205d84f`. Fast, Oracle, 112 SPEC mutations, 181 native mutations, eleven scene mutations, 123 Target suppressions, both LiveEncounter Target profiles, and two commit-bound byte-identical 575-sample Coffee Shop Emulator ledgers pass. Validator checkpoint `45f890d5458be5de57b31afd7e8adcdc78d8fb4c` replaces its incomplete hardcoded class-`0x1f` presentation subset with the accepted SPEC record/assembly table. Normalized ISO is `d7470bb606b91f142d8ea30098291d467b1e851582bc9415ab1046c07ad857c7`; canonical sample payload is `71c59a86a9c518c73ee432d6477c37b2736fa74afc566ca3cda3c7656559812e`.

Fresh window-only WGC covers every visible frame 2280..2310. Sheet `8ea5eb2c8a440b81fad5886f75caf5b806a5415cef3713587570816781b2235f` and clip `b2695152db316962ac45c3ca5ab9f9742eb3b933eb23e5e536167e8613ac535c` pass direct inspection: frame 2288 has no premature damage effect, frame 2306 contains the source contact, frame 2307 contains the natural impact, Predator/staff identity remains stable, and both Coffee Shop planes, palette, and priority remain coherent. The whole-scene gaps improve from `335 / 1,293 / 3 / 94 / 3 / 281` to `316 / 1,293 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero; the complete Coffee Shop gate remains open.

Incremental checkpoint `e0f3403a9db49e7e9d8f33931255df7cf8e408cc` closes the slot-`0x00ffa300` class-`0x1f` action-`0x16` retry and return cadence. Accepted frame 2409 latch fields route one RNG result `0x4bdf -> 0xe3c2` into timer 30, action `0x1a`, facing 0, selector 2, and animation `0x0012d5e4` at visible frame 2410; action `0x1a` preserves the timer into `0x18`, and the final HIT terminal record remains visible for one complete source frame before normal return. SPEC is `9a65b6d082e477898aa966ae06984b5d4807f2db7ddbdfb3d5552bc0c5ad2d56`; fixture is `f129e65004dcdd8da240ce7533318c1d6511b41f3df1aa5eecd1a3a19899c759`. Fast, Oracle, both Target profiles, 113 SPEC mutations, 82 Oracle-enemy mutations, 181 native mutations, twelve scene mutations, and two byte-identical 575-sample Emulator ledgers pass. Paired normalized ISO is `ef5791f9254915d9cf2b878740e4b6b86a99d157c4f48b1227d0382f501e6816`; sample payload is `a955f984a172c595f0ee788593cdd0e3113ab51b34d8978df4a749ad9a88a8e4`.

Window-only WGC frames 2408..2425 pass direct inspection. Cadence sheet `a137ce6039b62620de494ee8db645404d5e71a5aa5451aea5fb5653ac28d7de6` and clip `d7493bf51d125852300863ddd8ed99f2e37513ce3f4f8add9f5cf72a5bc3ac6d` preserve Predator/staff identity, coherent alien transition/return, the P1 `WARRIOR` equipment row with no active P2 panel, both planes, palette, and priority. Scene gaps improve from `316 / 1,293 / 3 / 94 / 3 / 281` to `305 / 1,285 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero. `d04a65a2253175c6e820140feefc35419e2cca07` intentionally remains the last fully accepted candidate until the zero-gap scene gate passes.

Incremental checkpoint `c584e416ac25d4e579e8c66a4059304a7e947b6c` closes record-type-`4`, class-`0x00`, slot-`0x00ff8680` from visible frame 2434 through 2500. Allocator `0x01773e` preserves x/y fractional residue, target selector `0x0241f0` uses unsigned nearest `0xffff`, terminal `0x0002fbb8` loops to `0x0002fba8`, and camera-relative bounds enter the source emitter path. All 67 fixed-point/state/timer/animation/angle/progress rows are exact; source/native hashes both equal `789cb79e083e0aa356989e67dbd6a0188a4eb58f794765c28d8bac0bd1544888`. SPEC is `56f273bae8740ab294be897ab14831a727d1354116211e05ac64c97dfb536238`; fixture is `5a508062eed207eddb25d6351b5d6b08a3e0544ac2c9726e3877caea6a2832bd`. Fast, Oracle, both Target profiles, 113 SPEC mutations, 45 weapon mutations, 181 native mutations, 15 scene mutations, and paired commit-bound 575-sample Emulator ledgers pass. Normalized ISO is `9e4544d34242e710148e9b4a13df034173097be3a1d171aad7ad2fd690ad5b1c`; sample payload is `92bc7e467d17eb0149d3b8c1e67f922f32140ee2e88e3c02d98ac0d46f90c767`.

Window-only WGC frames 2434..2500 pass direct inspection. Cadence sheet `06c40976bceb749c62d62a1a05b2dbc0d193c4d25fdf8271eaee5db95ac2d937` and clip `624c3dc4ece7c881f49422cea59e8dd84b98c541116168728f781c9cfea7e1ef` preserve Predator/staff identity, coherent projectile/effect movement, P1-only HUD/equipment, and both Coffee Shop planes, palette, and priority. Scene gaps improve from `305 / 1,285 / 3 / 94 / 3 / 281` to `305 / 1,272 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero. `d04a65a2253175c6e820140feefc35419e2cca07` intentionally remains the last fully accepted candidate until the zero-gap scene gate passes.

The slot-`0x00ff9d00` HIT-return and bounds boundary is now source-bound at
incremental checkpoint `a54b4567c87bbed611b1aeb675df2aa9b4bc3ca0`. The complete
normal-return tail clears actor `+0x85`; the subsequent `0x060c2e` bounds
routine reads the scheduler-entry phase bit before the recurring controller
advances it. Odd phase uses the `0x060e94` player-proximity path and continues
when the player is not near; even phase performs the source unsigned
camera-relative test. Native now preserves action `0x16` through visible frames
2469 and 2470 and enters release state `0x0600` at frame 2471 exactly as the
source does. The accepted frame-2287/2306/2307 chronology and all 67 exact
record-type-`4` rows remain unchanged.

SPEC-02 is
`41791464584f88d98b550c73c763fcdbd13c5e2a0d7750d2b975e11e9e49a287`;
fixture is
`fd643801590a2bab1094f84b5fd658cd7d11753d5527f77b758bc76efa433149`.
Fast, Oracle, 115 SPEC mutations, 82 Oracle-enemy mutations, 181 native
mutations, 15 scene mutations, 123 Target suppressions, both LiveEncounter
Target profiles, and two commit-bound byte-identical 575-sample Emulator
ledgers pass. Normalized ISO is
`4f36929763215ac62cef93297412e06afeb46cbedcf4b8465d3e166aef8c5a2f`;
sample payload is
`0384c57f25723a4e411f1a13db2c3b45b45020099aaf36af904a87e5a73c85f9`.

Fresh window-only Windows Graphics Capture covers visible frames 2468..2472.
Cadence sheet
`f7eafa69d9d87682a4e97a8bf228522256a09f1f309fdc3070f53668ea2cb837`
and clip
`9ceefe633829db7f20eeb1cf6b2092d400f1a9b74bf23782d72cafd4ebd0ec98`
pass direct inspection: Predator/staff identity is stable, the source-held
class-`0x1f` pose and release are coherent, the P1-only HUD/equipment row is
intact, and both Coffee Shop planes, palette, and priority remain correct.

Whole-scene gaps change from `305 / 1,272 / 3 / 94 / 3 / 281` to
`319 / 1,274 / 3 / 94 / 3 / 281`. Actor-lifetime gaps increase by 14 because
the corrected class-`0x1f` phase/release chronology invalidates 47 downstream
false lifetime matches while resolving 33 real mismatches. Spawn/despawn gaps
increase by two from the same fixed-pool lifecycle churn. Active-state,
collision/damage, route/camera, and audio/load gaps do not increase. Unowned
Saturn actors, unidentified source pairs, and retained gameplay authorities
remain zero; the complete Coffee Shop gate remains open.

## Exact next experiment
Bind the next earliest causal scene divergence at visible frame 2511.
Record-type `20`, class `0x09`, slots `0x00ffb480` and `0x00ffb500` remain on
source animation `0x0006dbda` while native advances to `0x0006dbfe` and
`0x0006dc22`; record-type `32`, class `0x01`, entry-controller x is source `8`
versus native `9` on the same frame. Recover the accepted counter, guard,
presentation cadence, and scheduler order from SPEC-02 and determine whether
the two discrepancies share one source writer. Do not fit the frame or disturb
the exact frame-2287/2306/2307 chronology, record-type-`4` trajectory,
class-`0x1f` phase-return cadence, or current player, visual, HUD, audio,
collision, and population locks.
