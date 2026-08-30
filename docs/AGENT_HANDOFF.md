# Active checkpoint
`project_state.yaml` is machine-readable truth and `docs/PARITY_PLAN.md` is the only roadmap. Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` on `codex/avp-playable-loop-pivot`; preserve private evidence and locks. The latest fully accepted candidate remains `d04a65a2253175c6e820140feefc35419e2cca07` until the complete Coffee Shop zero-gap gate passes.

## Workflow pivot / Preserved evidence work
Resume the AvP salvage Goal. Preserve `SALVAGE-00-OLD-BUILD-BASELINE`, `USER-01-PLAYER-BASELINE-REVIEW`, evidence candidate `597f4ed517d4e715d814ff841bd00d3977803f85`, and all accepted evidence.

## Preserved authority
- ORACLE-11/SPEC-02 remain accepted: 1,517 writers, zero gaps in the sole 94 x 10 matrix; `0x0abdd2` is packed-BCD score.
- Preserve the accepted player, scheduler, navigation/camera, first-encounter, presentation, collision, HUD, audio/loading, residency, background/palette/priority, and visual-QA locks. Native Round 1 is the sole first-encounter gameplay authority; retained code is presentation-only.
- Preserve the exact frame-2287 projectile prefix, damage-free frame 2288, source frame-2306 slot-`0x00ff8880` attack-`0x030cd2` damage write against `0x00ffa180`, natural frame-2307 class-`0x4e` impact, exact record-type-4 frames 2434..2500, and class-`0x1f` HIT/KO/return behavior.
- USER-09 is `CHANGES_REQUESTED`; SALVAGE-08 is inactive; physical Saturn is `UNRUN`; do not touch untracked `history.txt`.

## Current Coffee Shop checkpoint
Accepted progression evidence now binds the global phase at the native entry handoff: source frame 2072 carries `0xff8019 = 0x06`; each source scheduler invocation advances it before the encounter controller and actor pools. The first primary recurring spawn decrements controller index `9 -> 8` only after successful record-12 allocation and mirrors that value in the controller record.

Native frame 2510 is source-exact at phase `0xbf`, RNG `0xd21c`, living count 7, spawn index 9, and timer 3707. Frame 2511 is source-exact at phase `0xc0`, RNG `0x81a1`, living count 8, spawn index 8, and timer 3706. The recurring class-`0x1f` allocation at slot `0x00ffa3c0` preserves the reused record's low fixed-point words while overwriting its source-owned signed high position words. It now matches source `x/y` at frames 2511, 2514, and 2517: `0x02a08000/0x01489000`, `0x02a7e200/0x01470900`, and `0x02af4400/0x01458200`.

SPEC-02 is `51150e37e05d7e0199cec08725580630ef1a1890d3a63fdff68bf7e7c11c8cf2`; fixture is `e5ece146171b40172901c3ad58f3fc71af6109cdb938b18c91f08d117c895d78`; implementation checkpoint is `368bb391ff82c4b542b0fdfe0465c8be3d04e7e0`. Focused Oracle rejects 26 encounter and 82 enemy mutations, SPEC rejects 117, native host differential rejects 181, and the scene validator rejects 20. Fast, Oracle, 123 target-wiring suppressions, and both LiveEncounter Target profiles pass. The combat overlay's gameplay bytes, tile-code hash, palette, and archive hash remain unchanged; only its derived fixture identity advanced.

Two commit-bound 575-sample Coffee Shop Emulator ledgers are byte-identical at normalized ISO `94608db70794fa58bcd8c2d7e49fe0d6b2a8376423ebabe82f57f675ef8f6614`. Fresh window-only WGC covers visible frames 2510..2518: cadence sheet `e8946734278145e5e234bd731732fcc9cadc000354eadd1b5c9a84182fe3a93a`, clip `e7bfdbab252e2578cc6813fb0524f675aea03098025636a0cbd3aa855af80fe9`. Direct inspection preserves Predator/staff identity, coherent recurring-actor movement, P1-only HUD, and clean Coffee Shop planes, palette, and priority.

Whole-scene gaps improve from `319 / 1,274 / 3 / 94 / 3 / 281` to `295 / 1,259 / 3 / 94 / 3 / 281`. No category increases. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero.

## Exact next experiment
Continue the next earliest causal scene divergence at visible frame 2522 for player slot `0x00ff8380`: source enters substate `0x1a00` while native remains `0x0c00`, and animation first diverges at frame 2523. Recover the exact transition predicate, input/interruption guard, writes, presentation selection, and scheduler position from accepted Oracle/SPEC evidence. Apply the source rule rather than a frame exception while preserving every closed recurring-record, phase, RNG, spawn, collision, camera, HUD, audio, and rendering lock.
