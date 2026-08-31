# REIMPLEMENT-13 paused agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot`. The active
card remains `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`; the accepted runtime
candidate remains `d04a65a2253175c6e820140feefc35419e2cca07`. This branch-head
checkpoint is unaccepted WIP. Read `project_state.yaml`, this file, the active
task card, and the current SPEC-02 contract/fixtures completely before acting.
Do not create a new workflow, roadmap, branch, task hierarchy, or coverage
system.

Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, physical Saturn
`UNRUN`, all accepted gameplay/presentation locks, and the scheduler-visible
camera X/Z binding. Never stage, reset, or overwrite the user-owned dirty files
`data/avsp_anim_records.json` and `history.txt`; stage owned paths explicitly.

## Paused WIP

The complete source Button1 stage-progress helper is now bound in the existing
Predator weapon Oracle artifact, SPEC-02, generated native data, and native
runtime. Source provenance is caller `0x024094..0x024096`, helper
`0x0179e2..0x017b74`, guard `a5+0x01b0:u8 == 0`, accumulator
`a5+0x0226:u16`, stage `a5+0x01ea:s16`, route bounds at `a5+0x021a/+0x021c`,
delta 3, threshold 8, mask 7, signed domain clamp/mask, Coffee Shop bounds
8..16, no RNG, and player action-entry ordering before resource/projectile and
actor scheduling. Accepted route A/B ledgers contain 15 byte-identical calls;
the first three at source frames 2252/2342/2432 produce stage 8/8/9.

Oracle player-weapon validation passes with 56 mutations. SPEC-02 passes with
47 fields and 162 mutations. Contract SHA is
`37f8429a44a3d545b12d8242b0c8ab829e9ae2795cc1efa17f280fef7a9f6889`;
fixture SHA is
`a151d33a9174710d353a52a1933b63ab459856d3c602f047ca211d786f50ce31`.
The generator is current. The SPEC builder was made idempotent for the already
accepted empty-resource entry projection, which had previously existed only in
the checked-in generated fixture.

The full host differential is still intentionally RED. At scheduler frame
1757/code 15, slot `0x00ffa000`, state/substate `0x0208:0x0c04`, native stage
is 11 with accumulator 0, 8 stage-helper calls, 3 carries, 22 total weapon
entries, and RNG `0x1908`. The corresponding source route has only seven
stage-helper calls before the frame-3525 class-`0x1f` comparison (the eighth is
at source frame 3827). The native helper is therefore entered once too often;
do not change its arithmetic, initialize stage 9/10/11 directly, add a
frame/slot delay, weaken the comparison, or rebaseline the input route.
Target, scene census, Emulator, and WGC were not run at this red WIP boundary.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the current branch head.
Keep the bound Button1 stage-progress source program and all accepted evidence
unchanged. Compare native sufficient-Button1 action-entry calls against the 15
accepted source calls, beginning with source frames
2252/2342/2432/2882/2927/3332/3377/3827. Add focused host assertions or a
diagnostic ledger that identifies the first extra native helper invocation and
its owning input/action/recovery transition. Repair that smallest call-edge or
source-update-cadence boundary; do not alter helper arithmetic or source route
data.

Then add real native wrong-delta, wrong-threshold, wrong-action-entry-timing,
and omitted-call mutations; rerun Oracle, SPEC, generator, focused host, and the
full host differential. Require the helper-call chronology and stage value to
match source through frame 3525, then require slot `0x00ffa3c0` record
`0x0012d488` with unchanged RNG. Continue the complete route-reachable
class-`0x1f` program family. Run Target, the complete Coffee Shop census, paired
Emulator, and WGC only at the coherent class-family/body boundary, then commit,
push, verify private-origin SHA, and continue the existing first-segment plan.
