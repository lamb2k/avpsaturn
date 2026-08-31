# Workflow pivot — active handoff
User-requested pause refreshed 2026-08-30. Resume the AvP salvage Goal on
`codex/avp-playable-loop-pivot`; active card is
`REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`. Read `project_state.yaml`, the active
task card, and current SPEC-02 contract/fixtures completely before acting.
`docs/PARITY_PLAN.md` remains the only roadmap.

## Preserved evidence work
ORACLE-11/SPEC-02, the 1,517 reconciled writers, the sole 94 x 10 matrix, and
all accepted player, enemy, scheduler, navigation/camera, collision, HUD,
audio/loading, rendering, residency, palette, priority, and visual-QA locks
remain unchanged. Evidence candidate is
`597f4ed517d4e715d814ff841bd00d3977803f85`. Latest fully accepted runtime
candidate remains `d04a65a2253175c6e820140feefc35419e2cca07`; WIP
`efcfebcec559c1827998698d47234d2b00552f91` is not promoted. Historical cards
`SALVAGE-00-OLD-BUILD-BASELINE` and `USER-01-PLAYER-BASELINE-REVIEW` remain
preserved. USER-09 is CHANGES_REQUESTED, SALVAGE-08 inactive, Saturn UNRUN.

Current WIP: frame 3524 slot `0x00ffa3c0` matches source record `0x0012d4f8`,
timer 5, with exact RNG through 3525. At 3525 source selects `0x0012d488`,
native `0x0012d50c`. Full host is red at frame 1757/code 15/slot
`0x00ffa000`/`0x0208:0x0c04`; scene capture is red at native 3653/code 29.
Target, Emulator, and WGC were not run at this red boundary.

Read-only mapping now proves routine `0x041c36` reads signed camera X from
`a5+0x278` at `0x041cb0` and Z from `a5+0x27c` at `0x041cb8`, then adds actor
offsets and calls `0x016484`. X writers are `0x0b04ca`/`0x0b06fa`; Z writers
are `0x0b04f4`/`0x0b081c`. The source scheduler samples these before the
same-frame camera update, so native must use preserved pre-update X/Z. No
runtime, fixture, capture, or acceptance state changed during this mapping.

## Exact next experiment
1. Extend the existing SPEC-02 globals fixture with those two signed fields,
   addresses, writers, readers, owners, and native pre-update bindings. Add the
   missing pre-update Z field and make wander read X/Z only through the table.
   Mutate pre-update to current and require failure; require frame 3525 record
   `0x0012d488` with unchanged RNG. Do not alter render-camera behavior.
2. Rerun full host. If frame 1757 persists, isolate the WIP HIT-recovery versus
   action-`0x04` regression and fix it before scene advancement.
3. Close the entire route-reachable class-`0x1f` program family as one body,
   then run Target, pinned scene/census, paired Emulator, and WGC at the body
   boundary and select the fresh earliest causal divergence.

No frame/slot exceptions, route changes, renderer fitting, or downstream 3653
work first. Preserve dirty `data/avsp_anim_records.json` and `history.txt`;
stage explicit paths only, push normally, and verify private-origin SHA.
