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
Incremental checkpoint `5b40fd75c41e36c1c3c344e53882df1ed129466b` binds the source class-`0x02` current-animation step in state `0x0200`. The native slot `0x00ffb600` now has source record `0x0006b66c` and timer 4094 at frame 2074. The native change is guarded by a real mutation that removes the call; it cannot pass through relabeling or a fixed-frame substitute.

The smallest bounded Oracle follow-up is two independent captures, `cs39a` and `cs39b`. Their scene actors, component-20 dispatch, progression transactions, and result files are byte-identical. Exact frames 2073..2077 dispatch class-`0x02` at `0x06b534` with counts `1,1,2,2,1`, while recurring controller entry `0x0288e2` has counts `0,1,3,1,1`. Therefore the existing diagnostic assumption that recurring-controller count is the full-scheduler cadence is false. The remaining frame-2076 timer mismatch (native 4090, source 4091) is a diagnostic scheduler-phase blocker; it is not permission to add a gameplay frame exception or undo the source-correct animation step.

SPEC-02 is `d0d7762ade3d0f1cbb986d6c1135172e24017515c73ce30ccc39ec24b4385710`; fixture is `bf5a207ae4f83fca8683ebf9a64e8c93f8cef1674b1a3ae9691464d58f8136af`. Fast, Oracle, 80 bounded-Oracle mutations, 133 SPEC mutations, 209 native mutations, 20 scene mutations, 123 Target suppressions, and both LiveEncounter Target profiles pass. The exact runtime remains `0x148e8` bytes inside the `0x19000` carve, leaving `0x4718`. Two 575-sample Coffee Shop Emulator ledgers are byte-identical at payload `d6ce01333843b273432e965efde266f8a95c53c195a910e41602cc103d9a71d9`, VDP1 cache `15235569ad91027a6f9cf6d00c5b88b9c13539895a9259036a1ecdde48ad6504`, and normalized ISO `949fbc89c4a6e5703d2af6d14e38d610631217da099004222da1175924fbfbe0`.

Window-only WGC frames 2280..2310 pass at contact sheet `43e803cd593e1eb9f10aeaf52c1791b86ef3ab735077102af4e05389a90a2e09` and clip `f0bdf52684d9d3fab1446f2a932fe26e8b67c094206b357b3b64fa7f0603f8a2`. Direct inspection preserves the damage-free frame 2288, natural frame-2306/2307 damage-impact progression, Predator/staff identity, both Coffee Shop planes, palette, and priority.

Whole-scene gaps remain `331 / 1,241 / 2 / 93 / 3 / 281` for actor lifetimes, spawn/despawn, active states, collision/damage, route/camera, and audio/load. No category increased. Unowned Saturn actors, unidentified source pairs, and retained gameplay authorities remain zero. The next dependency-safe divergence is player slot `0x00ff8380` animation timer at frame 2239 (native 4095, source 4094); obstacle class-`0x0a` follows at 2247 and type-24/class-`0x4e` at 2259.

## Exact next experiment
Keep REIMPLEMENT-13 active. Preserve the source-correct class-`0x02` animation step and keep its frame-2076 diagnostic blocker explicit until source-owned per-phase scheduler invocation order is bound. Continue the dependency-safe player slot `0x00ff8380` animation timer at frame 2239 by binding the accepted player animation dispatch and its scheduler phase; use only the smallest bounded Oracle follow-up if accepted evidence lacks exact invocation ownership. Do not add frame exceptions, treat controller cadence as full-scheduler cadence, weaken the comparison, or change the input route. Rerun the complete Coffee Shop scene and return to the class-`0x02` blocker when the phase model is source-bound.
