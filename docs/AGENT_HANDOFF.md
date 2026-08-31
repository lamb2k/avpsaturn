# REIMPLEMENT-13 paused agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot` from the
branch head. The active card remains
`REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`. The accepted runtime candidate
`d04a65a2253175c6e820140feefc35419e2cca07` intentionally remains unchanged:
this branch head is a committed RED implementation checkpoint, not Coffee Shop
scene acceptance or candidate promotion.

Read `project_state.yaml`, this handoff, the active task card, and the current
SPEC-02 contract/generated fixtures completely before acting. Do not create a
new Goal, roadmap, workflow, branch, task hierarchy, coverage system, or
parallel writer. Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive,
physical Saturn `UNRUN`, and every accepted gameplay/presentation lock. Do not
stage, reset, or overwrite user-owned `data/avsp_anim_records.json` or
`history.txt`; stage owned paths explicitly.

## Committed pause boundary

The Coffee Shop recurring-controller scheduler-phase correction is implemented.
The existing scheduler is split into a pre-player recurring-controller phase
and a post-player fixed-pool/current-state-collision phase. Production and both
full-scene host paths now execute:

`entry -> pre-player controller -> player -> post-player pools/collision`

The combined scheduler APIs remain for focused callers. Collision snapshotting
remains in the post-player phase. A real mutation moves the controller back
after the player and reproduces return 117, proving the corrected order owns
the frame-2679/2680 boundary. The accepted current-camera sample is unchanged.

The pending shared Button1 chronology mutations are also complete. They reject:

- tick 0 instead of tick 1;
- removal of the one-update dispatch hold;
- suppression of immediate entry-action projection;
- removal of dispatch offsets from stage-progress, resource-debit, and parent
  allocation;
- allocating the empty effect during the dispatch hold;
- generated `resource_debit_tick` 0 instead of 1.

Focused results at the pause:

- controller-edge lane: PASS, 3 real mutations;
- Button1 timing lane: PASS, 8 real mutations;
- generated SPEC-02 entry fixture check: PASS;
- SPEC-02 contract lane: PASS, 167 mutations;
- Target `LiveEncounterBench` BUILD_ONLY: PASS, GAME.BIN 411136 bytes,
  BSS end `0x060be4c0`, ISO `/GAME.BIN` SHA-256
  `1f02795e3fed11bc6dab75ccf394400edf2260d313bed7355b7c33438b28f018`.

The full Oracle lane is not accepted. It now passes the corrected controller
edge and stops at the next existing host differential, return 123 at source
frame 4052: native has nine stage-progress calls versus ten in source. Do not
claim Oracle PASS.

A fresh complete Coffee Shop census was then attempted. Native stops earlier,
at frame 3653, with scheduler failure code 29 and source slot 0. That code is a
downstream failure from `avsp_round1_step_class1f_player_collision`; it must not
be patched in isolation. At frames 3650-3654 the source player is in state
`0x0204`, substate/action `0x0600`, while native remains in state `0x0200`,
substate/action `0x0202`. Native is walking when source is executing a player
action, so the collision failure and later frame-4052 stage-progress mismatch
are downstream until proven otherwise.

Fresh ignored diagnostic outputs are:

- `.deps/reimplement13_coffee_native_failure.tsv`;
- `.deps/reimplement13_coffee_native_failure.stderr`;
- source comparison:
  `.deps/mame/oracle11_progression_lifecycle_cs21a/coffee_shop_scene_frames.tsv`.

No Emulator or WGC acceptance was run for this RED checkpoint. The protected
`data/avsp_anim_records.json` has the same blob hash as HEAD/index
(`a80189857223c89aa20759dc0a6940f9cd83adba`) despite its stat-only worktree
status; never stage it. `history.txt` also remains user-owned and untracked.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head. Preserve
the committed pre-player recurring-controller/post-player pools-and-collision
scheduler split and all eight accepted Button1 timing controls. Do not reopen
the scheduler phase or patch collision failure code 29 unless new accepted
source evidence contradicts the causal trace.

First identify the earliest source/native Predator Warrior action divergence
between the accepted empty-Button1 anchor at frames 2522-2523 and the native
frame-3653 census failure. Use the existing Coffee Shop source and native TSVs
and the parsing/comparison helpers already present in
`tools/capture_reimplement13_coffee_shop_scene.py`. Compare player state,
substate/action, input projection, animation, world position, and update phase;
find the owning reusable player action/input program rather than treating frame
3653 as an isolated event. In particular, determine why source is in
`0x0204/0x0600` while native is in `0x0200/0x0202` at frames 3650-3654.

Inspect `avsp_round1_step_class1f_player_collision` only to explain how the
earlier player-action divergence produces code 29. Do not suppress the
collision, add an authored delay, rebaseline inputs, or guess an invulnerability
guard. Once the first divergent player program is identified, close every
Coffee Shop-reachable branch it owns from accepted Oracle/SPEC evidence, amend
the existing SPEC fixture only if an implementation-required field is absent,
and add real discriminating mutations.

Then rerun the focused differential, relevant mutations, fixture validation,
and Target. Regenerate the complete Coffee Shop census and continue from the
next earliest causal source/native divergence. Reserve paired cold Emulator
and full WGC for a coherent program checkpoint or the scene gate, as required
by the task card. Coffee Shop must not advance while unexplained gameplay gaps
or retained gameplay authority remain.
