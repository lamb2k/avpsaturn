# Workflow pivot — REIMPLEMENT-13 paused agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot`. The active
card remains `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`. Accepted runtime candidate
`d04a65a2253175c6e820140feefc35419e2cca07` remains unchanged; this branch-head
checkpoint is intentionally RED WIP and must not be promoted. Read
`project_state.yaml`, this handoff, the active task card, and the current
SPEC-02 contract/generated fixtures completely before acting. Do not create a
workflow, roadmap, branch, task hierarchy, coverage system, or parallel writer.

Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, physical Saturn
`UNRUN`, and all accepted rendering, camera, HUD, audio, loading, collision,
HIT/KO, player-action, navigation, and first-encounter locks. Do not stage,
reset, or overwrite user-owned `data/avsp_anim_records.json` or `history.txt`;
stage owned paths explicitly.

## Paused WIP

The source Button1 stage helper and its source-input chronology are now bound
through Oracle, SPEC-02, generated native data, and runtime. The accepted
implementation field is `action_dispatch_delay_updates_u8 = 1`: physical
Button1 is captured at source frame 2250, reaches the native input pipeline at
2251, and first performs the source action/helper at 2252. The begin update
holds motion while preserving locomotion presentation and direction history;
the sufficient/empty action step, projection, and helper wait one player
update. No frame exception or helper-arithmetic change was introduced.

Current validation:

- Oracle Predator weapon: PASS, 57 mutations rejected.
- SPEC-02: PASS, 163 mutations rejected.
- Contract SHA-256:
  `59ff3a9922e0b65617bf3cfeb0cb460134491a6d5f97ca8f163d12e11f4e8279`.
- Generated fixture SHA-256:
  `15aff4079e2690936ccd4346ee3f28d01698c9e2f5080bc0ca5eed6fabffb84e`.
- Generator current: PASS.
- Focused native/full Coffee Shop host: intentionally RED, return 116.
- Target, scene census, Emulator, and WGC were not run at this red boundary.

The chronology fix exposes the next earlier class-`0x1f` program-family gap.
The source scene manifest requires slot `0x00ffa3c0`, record type 12,
class `0x1f`, to be active from source frame 2511 through 3975. The lifetime
assertion fails immediately at frame 2511: native has eight active class-`0x1f`
actors but no `0x00ffa3c0`.

The recurring spawn program is already implemented and source-bound. Its
accepted controller `0x0288e2`, primary writer `0x028a3e`, auxiliary writer
`0x028b7e`, living-count guard, and fixed-pool allocation are not the missing
authority. The focused host was changed to use the accepted source/class-`0x02`
phase cadence and still fails. At frame 2511 its recurring controller is
naturally blocked with living count 8 because slot `0x00ffa180` remains active
in state `0x0202:0x020a`, animation record `0x0012de78`, health 56. Source owns
that actor only through frame 2415 and emits its despawn edge at 2416. The
accepted class-`0x1f` release boundary is state `0x0600:0x0000`, which decrements
the living count and releases the fixed-pool record. Therefore the missing
`0x00ffa3c0` allocation is downstream of the earlier `0x00ffa180` terminal
HIT/return/release failure, not evidence for a new spawn implementation.

The terminal trace now identifies an earlier cause. Source slot `0x00ff8880`,
record type 4/class `0x04`, is active during source scheduler frame 2306 and
writes damage to `0x00ffa180` from attack record `0x030cd2` in that update.
Source `0x00ffa180` is therefore visible in `0x0202:0x0000` at frame 2307 and
advances through `0x0202:0x0002`, `0x0200`, `0x0202`, `0x0204`, `0x0206`,
`0x0208`, and `0x020a` before normal return at 2413, state `0x0200:0x1600` at
2414, release state `0x0600:0x0000` at 2415, and despawn at 2416.

Native allocates the same child during processing frame 2306, but
`collision_registration_pending = 1` prevents it from colliding until the next
scheduler update. Every visible `0x00ffa180` HIT transition is consequently one
frame late. The source RNG order at frame 2377 is `0xedd9 -> 0xc9a2` for
`0x00ffa180` (low nibble 2, timer 10), followed by `0xc9a2 -> 0x5cfe` for
`0x00ffa300`. Native lets `0x00ffa300` consume the first call, then
`0x00ffa180` consumes `0xc9a2 -> 0x5cfe` one update late and selects timer 120.
That downstream hold leaves the actor active at 2511. The terminal predicate,
RNG algorithm, recurring spawn controller, and fixed-pool capacity are not the
first defect.

A temporary experiment moving every record-type-4 collision before all
record-type-12 actors was too broad and broke the existing delayed-parent
collision control; it was restored. The remaining owned diff is diagnostic
test instrumentation only. It records the projectile registration edge,
`0x00ffa180` transitions, and the RNG window. This is upstream of the later
missing type-16 spawns at 3253/3258/3263, player damage write at 3263, and
visible HIT at 3264. Do not repair any downstream symptom with authored damage,
a fixed-frame spawn/release, slot substitution, an actor-limit change, or a
weakened comparison.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head. Preserve
the completed one-update Button1 dispatch contract, the source-lifetime
assertion, and the corrected findings that recurring allocation is already
source-bound and the stale `0x00ffa180` lifetime is downstream of a one-update
record-type-4 child collision delay. Start at source scheduler frame 2306 with
slot `0x00ff8880`, attack record `0x030cd2`.

Bind the complete Coffee Shop-reachable scheduler rule for a record-type-4
child allocated during its parent's update: allocation/slot visitation,
collision-registration eligibility, current-state snapshot ownership,
collision phase, reaction queueing, and ordering before the affected
record-type-12 actor dispatch. Use accepted Oracle/SPEC evidence and inspect the
existing child allocator, record-type-4 pool loop, collision-registration
refresh, and collision pass. Do not move every projectile collision globally:
the existing delayed-parent collision control proves that broad ordering is
not equivalent. Do not add a frame, slot, or actor-specific exception.

Add a real mutation that rejects deferring a newly allocated eligible child by
one scheduler update. Require no premature frame-2288 damage; damage from
`0x00ff8880`/`0x030cd2` at source frame 2306; the natural class-`0x4e` impact at
2307; `0x00ffa180` visible in `0x0202:0x0000` at 2307; source RNG
`0xedd9 -> 0xc9a2` for its frame-2377 hold selection followed by
`0xc9a2 -> 0x5cfe` for `0x00ffa300`; and the accepted return/release/despawn at
2413/2415/2416. The causal result must be the natural living-count decrement
and recurring allocation of `0x00ffa3c0` at frame 2511.

If an implementation-required field is absent, record the exact field, amend
the existing SPEC-02 fixture from accepted Oracle evidence, and run only the
smallest bounded Oracle follow-up if that evidence genuinely lacks it. Do not
guess. Require `0x00ffa180` to follow its source lifetime and the resulting
`0x00ffa3c0` actor to remain source-valid through frame 3975 and naturally
produce the accepted `0x0208:0x0e02` type-16 effects at 3253/3258/3263, the
attack-record `0x03589e` damage write at 3263, and player HIT at 3264. Add real
mutations for the dispatch delay and the completed source program; rerun
Oracle, SPEC, generator, focused/full host, and Target. At the coherent
class-family boundary run the complete Coffee Shop census, paired Emulator,
focused WGC, commit, push, verify private-origin, and continue the existing
first-segment plan.
