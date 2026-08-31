# Active checkpoint
`project_state.yaml` is machine-readable truth and `docs/PARITY_PLAN.md` is the
only roadmap. Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` on
`codex/avp-playable-loop-pivot`; preserve private evidence and all accepted
locks. The latest fully accepted candidate remains
`d04a65a2253175c6e820140feefc35419e2cca07` until the complete Coffee Shop
zero-gap gate passes. Commit `efcfebcec559c1827998698d47234d2b00552f91` is a
deliberate WIP evidence checkpoint, not a candidate promotion; commits after
it on this branch are documentation and plan-amendment only.

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

## Execution plan amendment (2026-08-30)
An owner-approved amendment governs the remainder of REIMPLEMENT-13: bodies
are whole routine programs, actor-class families, or segments; remaining
SPEC-02 executable semantics are completed in batches per actor class from the
decrypted opcode image validated against the existing byte-identical ledgers;
a scheduler-visible `a5`-relative globals table becomes a SPEC-02 fixture;
full ceremony runs once per body; checkpoint evidence is recorded once in the
task card. Evidence standards are unchanged. The authoritative amendment text
is in `docs/task_cards/REIMPLEMENT-13-SOURCE-CLOSED-ROUND1.md` under
"Execution plan amendment (2026-08-30)". Interactive implementation runs on
Codex `gpt-5.6-sol` at `medium` reasoning (owner decision, 2026-08-30).

## Paused WIP program checkpoint (summary)
Full evidence lives in the task card's "Paused WIP evidence checkpoint"
section. Key facts: the WIP fixes the phase-exclusive HIT/KO scratch alias and
partially closes the class-`0x1f` inner-8 action-`0x04` dispatcher; source and
native agree at frame 3524 slot `0x00ffa3c0` (record `0x0012d4f8`, timer 5)
with exact RNG through frame 3525. The earliest causal scene divergence is
frame 3525 at that slot: source binds record `0x0012d488`, native binds
`0x0012d50c`, because the native wander helper has not bound the source
`0x041c36` scheduler-visible target origin `a5+0x278`/`a5+0x27c` (source frame
3524 sees `camera_x=895`, `camera_z=256`). Oracle enemy analysis (104
mutations) and SPEC-02 build/generation/tests (156 mutations) pass; SPEC
contract SHA-256
`43e16c1e3d6a233f7a86703aa68e546e4a2b3be69b5ce7d6f264f9b5b587c288`; fixture
SHA-256
`dd9126f34d9e4ee141239eee907a1405d8561da2cb1d7ebadf66e53a08e8fecd`. Red
lanes: full host entry lane FAIL at frame 1757, code 15, slot `0x00ffa000`,
state/substate `0x0208:0x0c04`; full scene capture FAIL at native frame 3653,
code 29. Target, Emulator, and WGC were not run at this red boundary. The
retained census `327 / 1,234 / 2 / 93 / 3 / 281` is not a current WIP
recapture.

## Exact next experiment / resume prompt
Continue REIMPLEMENT-13 under the 2026-08-30 execution plan amendment.

1. Wander origin (unchanged narrow fix). Prove which source-owned
   scheduler-visible values map to `a5+0x278` and `a5+0x27c` in routine
   `0x041c36`, including why source frame 3524 uses `camera_x=895` and
   `camera_z=256`, and bind the native wander helper to that origin. Use
   accepted `cs50a/cs50b` evidence and SPEC-02 first; run the smallest bounded
   Oracle follow-up only if the mapping is genuinely absent. Add a mutation
   rejecting current-versus-scheduler-visible origin confusion and confirm
   frame 3525 slot `0x00ffa3c0` binds record `0x0012d488`. Preserve the exact
   RNG prefix, the action-`0x04` dispatcher, the terrain tail, and the
   accepted render-camera behavior.
2. Classify frame 1757 before advancing past it. Rerun the full host entry
   lane. If frame 1757 (code 15, slot `0x00ffa000`, `0x0208:0x0c04`) clears,
   record that it shared the wander-origin root cause. If it persists, it
   precedes frame 3525 on its own lane: determine whether the WIP HIT-recovery
   gating or action-`0x04` change regressed it, and fix it before any further
   scene advancement. Do not defer it silently.
3. Complete the class-`0x1f` program family as one body. Decode every
   route-reachable action of the inner-8 dispatcher and its movement, wander,
   and terrain helpers — exactly the set enumerated by the accepted ORACLE-11
   enemy contract, nothing outside it — from the decrypted opcode image,
   validated against the existing byte-identical ledgers; capture new Oracle
   evidence only for behavior those ledgers cannot witness. Amend SPEC-02 and
   regenerate fixtures once for the whole family, emit the scheduler-visible
   `a5`-global table fixture, and implement all actions with per-branch
   mutations.
4. Consolidated body-boundary verification. Focused host differentials and
   fixture validation per step. At the body boundary run Target, one pinned
   scene capture, and the complete Coffee Shop census; run paired Emulator and
   WGC when the census is green or strictly improved. Reselect the earliest
   causal divergence from the fresh census and record one task-card checkpoint
   entry containing counters, hashes, and the next resume line.

Do not add a frame/slot exception, change the input route, fit the renderer,
or work on the downstream frame-3653 failure before its upstream causes are
closed. Stage explicit paths only; never stage `data/avsp_anim_records.json`
or touch `history.txt`; push once at completion or a declared hard stop and
verify the exact `private-origin` SHA.
