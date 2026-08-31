# Workflow pivot — REIMPLEMENT-13 paused agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot`. The active
card remains `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`. The accepted runtime
candidate `d04a65a2253175c6e820140feefc35419e2cca07` intentionally remains
unchanged because Coffee Shop has not passed its zero-gap scene gate. The
branch head is a committed RED implementation checkpoint, not a promoted
candidate.

Read `project_state.yaml`, this handoff, the active task card, and the current
SPEC-02 contract/generated fixtures completely before acting. Do not create
another Goal, workflow, roadmap, branch, task hierarchy, coverage system, or
parallel writer. Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive,
physical Saturn `UNRUN`, and every accepted gameplay/presentation lock. Do not
stage, reset, or overwrite user-owned `data/avsp_anim_records.json` or
`history.txt`; stage owned paths explicitly.

## Paused checkpoint

The accepted class-`0x1f` action-`0x0c` five-row timer-table checkpoint remains
unchanged. Investigation of its later frame-4052 symptom proved that native had
completed only one of the source route's five player HITs; the missing later
HITs were downstream of an earlier shared player Button1 projection mismatch,
not a stuck HIT-return program.

Fresh source/native comparison identified the first player mismatch at source
frame 2252. The accepted SPEC-02 player weapon fixture already requires the
physical edge at 2250, one native input-pipeline update, visible entry action
`0x0c00` at 2252, active `0x0c02` presentation at 2253, parent visibility at
2254, stage-progress/resource/parent tick 1, and the corresponding empty path
`0x1a00` at 2522 with active presentation plus its class-`0x10` effect at 2523.
Native was projecting both sufficient and empty Button1 one visible frame late.

The paused native correction now starts the weapon program at tick 1, projects
the sufficient or empty entry action immediately while preserving the current
entry presentation, keeps the one-update dispatch hold authoritative, binds
resource debit through the generated `resource_debit_tick`, offsets the
stage-progress/resource/parent operations by the dispatch delay, and allocates
the empty effect only after that hold. The generated entry header is current.
Focused direct expectations were updated to the accepted entry/active/return
sequence. Diagnostic player-HIT and class-`0x1f` probes remain in the host test
to locate the downstream causal chain.

The generator check passes. The baseline host differential is intentionally
RED with return 117 at source frame 2679:

`substate=0x0200 snapshot=1 bound=832 camera=832 previous=830 living=8`

This is the existing hard-coded Coffee Shop controller/camera-edge precheck.
Do not change its expected frame merely to make the lane green. The Button1
correction changed upstream chronology, so the next agent must compare the
accepted source controller rows and the fresh native state at frames 2677-2682
to determine whether the precheck is stale or whether a real controller
scheduler/camera-sample defect remains. The earlier record-type-4 parent/child,
frame-2306 damage, frame-2307 impact/HIT, frame-2377 RNG ownership, frame-2416
release, and natural frame-2511 recurring allocation still execute before this
boundary.

No new Oracle capture was required. Oracle, SPEC mutation, Target, Emulator,
complete scene census, and WGC were not rerun for this incomplete body. The
existing `test_entry.py` weapon mutations still refer to the old parent timing
expression and must be updated before the correction can be accepted. Do not
claim this checkpoint as scene parity or candidate promotion.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head. Preserve
the accepted class-`0x1f` action-`0x0c` timer-table checkpoint and the paused
SPEC-bound shared Button1 entry-projection correction. Do not reopen the later
frame-4052 HIT-return symptom unless it remains after the earlier chronology is
closed.

First reconcile the Coffee Shop recurring-controller/camera-edge precheck at
source frames 2677-2682. Compare the accepted source actor/controller rows,
route state, living count, progress snapshot, current camera 832, previous
camera 830, controller substate, and camera bound against a fresh native trace.
Determine whether the host assertion is checking before or after the owning
scheduler update, or whether native has a genuine controller-phase divergence.
Repair only the complete owning source program or correct the stale diagnostic
assertion when source evidence proves it stale; do not patch frame 2679, delay
an event, rebaseline input, or change the accepted camera-current-sample rule.

Then update the existing Button1 mutation controls for the generated
`resource_debit_tick`, immediate entry projection, dispatch-hold ownership,
post-hold empty-effect allocation, and dispatch-delay offsets on
stage-progress/resource/parent operations. Require mutations that reject the
old one-frame-late sufficient and empty paths. Rerun the generator check,
focused host differential, relevant real mutations, fixture validation, and
Target. Once the complete Button1 program is green, regenerate the Coffee Shop
census and continue from its next earliest causal source/native divergence.
Reserve paired cold Emulator and full WGC for the coherent program checkpoint
or scene gate, as required by the task card.
