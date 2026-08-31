# Active checkpoint
`project_state.yaml` is machine-readable truth and `docs/PARITY_PLAN.md` is the
only roadmap. Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` on
`codex/avp-playable-loop-pivot`; preserve private evidence and all accepted
locks. The latest fully accepted candidate remains
`d04a65a2253175c6e820140feefc35419e2cca07` until the complete Coffee Shop
zero-gap gate passes. The current branch head is a deliberate WIP evidence
checkpoint and is not a candidate promotion.

## Preserved authority and workflow
- ORACLE-11/SPEC-02 remain accepted: 1,517 writers and zero gaps in the sole
  94 x 10 matrix; `0x0abdd2` is packed-BCD score authority.
- Native Round 1 remains the sole first-encounter gameplay authority. Retained
  code is presentation-only.
- Preserve the accepted player actions, class-`0x1f` identity/tracking,
  projectile/damage/impact chronology, scheduler, navigation/camera, collision,
  HUD/audio/loading, residency, background, palette, priority, and visual-QA
  locks.
- USER-09 remains `CHANGES_REQUESTED`; SALVAGE-08 remains inactive; physical
  Saturn remains `UNRUN`.
- Do not reset, clean, stash, rebase, broad-restore, force-push, use
  `git add -A`, stage `data/avsp_anim_records.json`, or touch untracked
  `history.txt`.

## Paused WIP program checkpoint
This checkpoint fixes the phase-exclusive HIT/KO scratch alias and partially
closes the complete class-`0x1f` inner-8 action-`0x04` dispatcher:

- `source_motion_fields[4]` is recognized as shared storage for HIT recovery
  and the action-`0x0c` plan. HIT recovery is active only for the accepted exact
  reaction kind/state pairs; a nonzero action plan alone no longer fabricates a
  HIT reaction. Oracle/SPEC include the negative control.
- The action-`0x04` program now performs the every-update player-proximity
  check first, applies the exact final action-2 guard arithmetic, clears the
  action, and steps the movement helper once in the same scheduler visit.
- This makes source/native frame 3524 slot `0x00ffa3c0` agree on animation
  record `0x0012d4f8` and timer 5. RNG state remains exact through frame 3525.
- The Coffee Shop terrain fixture/runtime now contains the complete 4096-entry
  selector map, selectors 4 and 20, exact branch-0/branch-2 arithmetic, and the
  mandatory class-`0x1f` movement tail call.

The program and scene are **not accepted**. The earliest causal scene
divergence is frame 3525, slot `0x00ffa3c0`: source binds record
`0x0012d488`, while native binds `0x0012d50c` and moves on the wrong direction
result. Source routine `0x041c36` computes the wander target from source global
fields at `a5+0x278` and `a5+0x27c` plus actor offsets. At frame 3524 the source
values are `camera_x=895`, `camera_z=256`, offsets `+144/+48`; the current native
mapping uses a different origin. This is not an RNG or action-selection gap.

The focused evidence state at pause is:

- Oracle enemy analyzer: PASS.
- Oracle enemy tests: PASS, including 104 mutations.
- SPEC-02 build/generation/tests: PASS, including 156 mutations.
- SPEC contract SHA-256:
  `43e16c1e3d6a233f7a86703aa68e546e4a2b3be69b5ce7d6f264f9b5b587c288`.
- Generated fixture SHA-256:
  `dd9126f34d9e4ee141239eee907a1405d8561da2cb1d7ebadf66e53a08e8fecd`.
- Full host entry lane: FAIL at frame 1757, code 15, slot
  `0x00ffa000`, state/substate `0x0208:0x0c04`, record `0x0012d8e0`.
- Full scene capture: FAIL at native frame 3653, code 29. Treat this as
  downstream until the earlier frame-3525 divergence is corrected.
- Target, Emulator, and WGC were not run because the focused host/scene gate is
  red. The last completed census remains `327 / 1,234 / 2 / 93 / 3 / 281` for
  actor lifetimes, spawn/despawn, active states, collision/damage,
  route/camera, and audio/load; it is not a current WIP recapture.

## Exact next experiment / resume prompt
Continue REIMPLEMENT-13 without changing the workflow. Resolve only the
earliest frame-3525 class-`0x1f` divergence by binding the source `0x041c36`
wander-target origin. Prove which source-owned scheduler-visible values map to
`a5+0x278` and `a5+0x27c`, including why source frame 3524 uses
`camera_x=895` and `camera_z=256` while native computes a different direction.
Preserve the exact RNG prefix, the action-`0x04` dispatcher, the terrain tail,
and the accepted render-camera behavior. Use accepted `cs50a/cs50b` evidence
and SPEC-02 first; run only the smallest bounded Oracle follow-up if the mapping
is genuinely absent. Add a mutation that rejects using the wrong current versus
scheduler-visible origin, then run the focused host differential, relevant
mutations, fixture validation, and Target. After the complete source program is
green, run one pinned scene capture and focused visual inspection, then rerun
the complete Coffee Shop census and reselect the earliest causal divergence.
Do not add a frame/slot exception, change the input route, fit the renderer, or
work on the downstream frame-3653 collision/action-`0x0c` failures first.
