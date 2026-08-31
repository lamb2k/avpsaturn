# Workflow pivot - REIMPLEMENT-13 paused agent handoff

Resume the AvP salvage Goal on `codex/avp-playable-loop-pivot`; active card is
`REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`. Completely read `project_state.yaml`,
this handoff, the active card, and SPEC-02. Create no new workflow or branch.

## Preserved evidence work
Preserve evidence candidate `597f4ed517d4e715d814ff841bd00d3977803f85`,
historical `SALVAGE-00-OLD-BUILD-BASELINE` and `USER-01-PLAYER-BASELINE-REVIEW`,
all accepted locks, USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, Saturn `UNRUN`.
Accepted runtime candidate remains `d04a65a2253175c6e820140feefc35419e2cca07`;
this checkpoint is unaccepted WIP. Never stage/reset/overwrite user-owned
`data/avsp_anim_records.json` or `history.txt`; stage explicit owned paths.
Completed WIP: existing navigation/SPEC fixtures bind signed scheduler-visible
camera X (`a5+0x0278`, `0xff8278`, reader `0x041cb0`, writers
`0x0b04ca/0x0b06fa`) and Z (`a5+0x027c`, `0xff827c`, reader `0x041cb8`,
writers `0x0b04f4/0x0b081c`). Native wander uses only preserved pre-update X/Z;
the render camera is unchanged. Navigation PASS/37 mutations; SPEC PASS/46
fields/158 mutations. SPEC SHA `6eb601e055bf9a59aaf7c1a10fea2cae1a351ca49324b22285c5faa82f30f60a`;
fixture SHA `bf1b080ddd8c045884b194f3ac0d4975d9888f746d3fec2bb512214a21313fec`.

Full host remains intentionally RED at frame 1757/code 15, slot `0x00ffa000`,
`0x0208:0x0c04`, action timer 0, animation timer 8, motion4 4, guard 1,
style 0, stage parameter 8, RNG `0x1908`. This is not the old HIT/KO alias:
motion field 4 is the accepted phase-shared action-`0x0c` plan. Phase-2 timer
lookup requires Coffee Shop stage parameter 9. Target/census/Emulator/WGC were
not run at this red intermediate boundary.

Read-only pause mapping closes the missing provenance. Player Button1 routine
`0x024060` calls helper `0x0179e2` at `0x024096` with D0=3 loaded at
`0x024094`. Guard `a5+0x01b0:u8 == 0`; progress is `a5+0x0226:u16`, delta
3, threshold 8, mask 7; stage is `a5+0x01ea:s16`, clamped to the 5-bit domain
and Coffee bounds 8..16. Accepted route A/B ledgers match: frames
2252/2342/2432 produce progress `0->3`, `3->6`, `6->9->1` and stage
`8->8->9`. Source frame-2072 setup remains 8. No new capture is required.

## Exact resume prompt

Close the complete route-reachable Button1-owned stage-progress helper program
using the mapping above. Amend the existing Predator weapon Oracle contract and
SPEC-02 fixture with provenance, guard, field types, arithmetic/branch order,
bounds, timing, and mutations. Generate native table/state and invoke it at the
source action-entry phase. Never assign/initialize 9 directly, add a frame/slot
exception, weaken comparison, or undo the scheduler-visible X/Z binding.

Regenerate deterministically; add a wrong-transition mutation; rerun focused
Oracle/SPEC/generator and full host. Require frame 3525 slot `0x00ffa3c0`
record `0x0012d488` with unchanged RNG. Finish the route-reachable class-`0x1f`
family, then run Target, scene census, paired Emulator, and WGC before commit.
