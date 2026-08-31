# Workflow pivot — REIMPLEMENT-13 paused agent handoff
Resume the AvP salvage Goal on `codex/avp-playable-loop-pivot`. The active
card remains `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`; accepted runtime candidate
`d04a65a2253175c6e820140feefc35419e2cca07` remains unchanged. This branch-head
checkpoint is unaccepted RED WIP. Read `project_state.yaml`, this handoff, the
active task card, and current SPEC-02 contract/fixtures completely before acting.
Do not create a workflow, roadmap, branch, task hierarchy, or coverage system.

Preserved evidence work includes `SALVAGE-00-OLD-BUILD-BASELINE` and `USER-01-PLAYER-BASELINE-REVIEW`; evidence candidate is `597f4ed517d4e715d814ff841bd00d3977803f85`.
Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, physical Saturn
`UNRUN`, all accepted locks, and the scheduler-visible camera X/Z binding. Do
not stage, reset, or overwrite user-owned `data/avsp_anim_records.json` or
`history.txt`; stage owned paths explicitly.

## Paused WIP
The source Button1 stage helper is bound in Oracle/SPEC/generated/native code:
caller `0x024094..0x024096`, helper `0x0179e2..0x017b74`, guard
`a5+0x01b0:u8`, progress `a5+0x0226:u16`, stage `a5+0x01ea:s16`, bounds
`a5+0x021a/+0x021c`, delta/threshold/mask 3/8/7, Coffee bounds 8..16, no RNG.
Oracle passes 56 mutations; SPEC passes 47 fields/162 mutations; contract SHA
is `37f8429a44a3d545b12d8242b0c8ab829e9ae2795cc1efa17f280fef7a9f6889` and
fixture SHA is `a151d33a9174710d353a52a1933b63ab459856d3c602f047ca211d786f50ce31`.

The committed chronology assertion is intentionally RED at source frame 2251:
expected/native calls 0/1, input `0x0010`, source/class-`0x02` updates 1/1,
weapon active/tick 1/1, action `0x0c00`, progress/stage 3/8. Physical Button1
is captured at 2250, native pipeline exposes it at 2251, and source action plus
helper first appear at 2252. Native begins and steps the weapon action in one
scheduler visit, one source-visible update early. This causes the later eighth
native helper call before frame 3525. Target/census/Emulator/WGC were not run.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head. Preserve
the chronology assertion and helper arithmetic. From accepted evidence, add
`action_dispatch_delay_updates_u8 = 1` to the existing Predator weapon
Oracle/SPEC source-input contract, its mutation, validator, generator, generated
native data, and runtime contract. On the pipelined Button1 edge, begin and hold
motion but preserve locomotion presentation; defer sufficient/empty Button1
step, projection, and helper until the next player update. Do not encode a frame
exception, direct stage value, arithmetic change, weakened comparison, or route
rebaseline.

Run Oracle, SPEC, generator, focused/full host, and real wrong-delay/delta/
threshold/omitted-call mutations. Require exact helper chronology/stage through
frame 3525 and slot `0x00ffa3c0` record `0x0012d488` with unchanged RNG. Finish
the route-reachable class-`0x1f` program family, then run Target, full Coffee
Shop census, paired Emulator, and WGC at the coherent body gate; commit, push,
verify private-origin, and continue the first-segment plan.
