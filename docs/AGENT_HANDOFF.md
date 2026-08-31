# REIMPLEMENT-13 paused agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot` from the branch
head. The active card remains `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`; runtime checkpoint `5d09b9b` is a
verified partial implementation, not Coffee Shop acceptance. The accepted candidate intentionally remains `d04a65a2253175c6e820140feefc35419e2cca07`.
Workflow pivot / Preserved evidence work: Resume the AvP salvage Goal; retain SALVAGE-00-OLD-BUILD-BASELINE, USER-01-PLAYER-BASELINE-REVIEW, and evidence candidate `597f4ed517d4e715d814ff841bd00d3977803f85`.

Read `project_state.yaml`, this handoff, the active task card, and current SPEC-02 contract/generated fixtures completely. Do not create another Goal,
roadmap, workflow, branch, task hierarchy, coverage system, or writer. Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, physical Saturn `UNRUN`, and all accepted locks. Never stage/reset/overwrite user-owned
`data/avsp_anim_records.json` or `history.txt`; stage owned paths explicitly.

## Verified pause boundary

The shared Predator Warrior HIT program now enters from the actor's signed 16.16
source X, distinguishes global-bound clamping from obstacle/terrain
ownership, and preserves the low word when only the high word is bounded. Its
return-to-control bridge preserves the source actor position and applies the
controller adapter's measured delta, so inherited fractions survive normal
locomotion. Obstacle/terrain writes still clear the fraction they own.

`python tests/port_v2/round1/test_entry.py --player-hit-only` passes with nine real mutations. The lane binds type-16 HIT frames 3264-3313 and the frame-3314
return to control at X `0x04a0a000`; mutations reject entry truncation, wrong
bound ownership, unconditional truncation, source-position zeroing, and the
old absolute-twentieths reconstruction. Generated SPEC fixture check passes.

Target `LiveEncounterBench` BUILD_ONLY passes: GAME.BIN 411488 bytes, BSS end `0x060be620`, ISO `/GAME.BIN` SHA-256
`a41feb01186d6b7f630656e865f2235d4688c8a0b33d0d3463827d0dd59bf911`.
No Emulator/WGC acceptance was run. Oracle remains intentionally RED at the
later return-123/frame-4052 stage-progress mismatch. The complete scene census
has not been regenerated after this return-to-control correction.

Ignored diagnostics remain `.deps/reimplement13_coffee_native_failure.tsv`, its
`.stderr`, and `.deps/mame/oracle11_progression_lifecycle_cs21a/coffee_shop_scene_actors.tsv`.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head after runtime checkpoint `5d09b9b`. First regenerate the Coffee Shop census and use
`tools/capture_reimplement13_coffee_shop_scene.py` to prove the player X 16.16
first mismatch moved beyond frame 3314. Do not reopen the accepted scheduler,
Button1, HIT, or return-to-control programs unless that evidence contradicts them. Then close the next earliest reusable player program: source input
`0x0028` at frames 3410-3416 enters contextual Button2 action `0x1400`, active
`0x1402`, records `0x160288..0x1602c8`, selectors 21/20, while native previously
selected the generic close-combo path. Bind the target-context guard, entry
timing, records, selectors, movement/collision, exit, and every Coffee
Shop-reachable branch only from accepted Oracle/SPEC evidence; if a required
field is absent, record the exact SPEC blocker and perform only the smallest
bounded evidence amendment. Add real mutations, then run focused differential,
fixture validation, Target, and the complete scene census. Keep the scene RED
until zero unexplained gameplay gaps and no retained gameplay authority remain.
