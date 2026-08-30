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
Incremental checkpoint `ec41b2bc70e4b5212cb8f9b586305b34ab3fba05` closes the frame-2522 depleted Button1 dispatch. The source predicate is the persistent player `+0x8b` depleted latch, not an instantaneous resource comparison. Dispatch `0x01a6f4` therefore enters action `0x1a00` at frame 2522. Normal recharge (`0x0adf06`, reload 3) and depleted recharge (`0x0adfc0`, reload 6) preserve their separate decrement, reload, increment, and later latch-clear ordering. Two accepted source captures are byte-identical at `af67295b879521e0aba388ebe4b1bd9e8698c21c86e9d5b837da14efe086b4cb`; suppressing the normal increment proves the frame-2522 action remains latch-owned.

SPEC-02 is `e709b7bd616ecdb118e61459dbbc7677c9d0e13dd932f5bd4cf856a25f6d61ac`; fixture is `f726c7ae09f3edad2fb93fc853cf3851eb618449e72a64ad89a7b9974e2098e8`. Fast, Oracle, 119 SPEC mutations, 45 player-weapon controls, 82 enemy mutations, 181 native mutations, the Coffee Shop scene validator, 123 Target suppressions, and both LiveEncounter Target profiles pass. Two 575-sample Emulator ledgers are byte-identical at normalized ISO `be01ec7dfe1a002ec5bda0807e945e6d59544ea59e772a9f8f82f75edbc6cbaa`; canonical samples hash to `aab911fae523eb13b79969cf5a0d99ce002400577e3dd6016f416a6c6f60e099`.

Fresh window-only WGC covers every visible frame 2520..2540. Cadence sheet `8788ae5739323986ef83f3734154acf0c71c27bd18680b07afe36327410ed83e` and clip `65651d2fb214185f4a548607cb89ad4ffc39d5cac9faf18157ec4fc4e4bcb242` pass direct inspection with stable Predator/staff identity, source-timed empty-resource presentation, P1-only HUD and weapon meter, and clean Coffee Shop planes, palette, and priority.

Whole-scene gaps change from `295 / 1,259 / 3 / 94 / 3 / 281` to `322 / 1,262 / 2 / 94 / 3 / 281`. Actor-lifetime and spawn/despawn counts rise by 27 and 3 because the corrected depleted branch changes downstream type-24 fixed-pool reuse and invalidates earlier false lifetime/edge matches; active-state gaps improve by one. The source capture is unchanged, and collision/damage, route/camera, and audio/load do not increase. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero.

## Exact next experiment
Continue the next earliest causal scene divergence at visible frame 2523 for source slot `0x00ffc300`. Source still owns type-24/class-`0x4e` at animation `0x0007a09c`, `y=404`, `z=319`; native has reused the slot and presents `0x0007a0ac`, `y=402`, `z=0`. Bind the exact type-24 lifetime, release/reuse order, scheduler position, class/variant ownership, state initialization, coordinate writes, and presentation cadence. Apply the accepted source rule rather than a slot/frame exception while preserving the corrected depleted latch and every other closed lock.
