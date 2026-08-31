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
class `0x1f`, to be active from source frame 2511 through 3975. The new lifetime
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

This is upstream of the later missing type-16 spawns at 3253/3258/3263, player
damage write at 3263, and visible HIT at 3264. Do not repair any downstream
symptom with authored damage, a fixed-frame spawn/release, slot substitution,
an actor-limit change, or a weakened comparison. The extra host diagnostics
committed at this pause print source cadence, encounter counters, the active
class-`0x1f` population, and the `0x00ffa180` active edge; they are diagnostic
WIP and may be narrowed or removed after the owning rule is corrected.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head. Preserve
the completed one-update Button1 dispatch contract, the source-lifetime
assertion, and the corrected finding that recurring allocation is already
source-bound. Start with slot `0x00ffa180`, whose accepted source lifetime ends
at frame 2415/despawn edge 2416 but which remains natively active at frame 2511
in `0x0202:0x020a`, record `0x0012de78`, thereby holding living count 8 and
blocking the otherwise-correct `0x00ffa3c0` recurring allocation.

Inspect the complete accepted class-`0x1f` HIT/KO/normal-return/release program,
especially the `phase_0x020a_terminal_animation` predicate and transition to
state `0x0600:0x0000`. Add targeted state/substate/record transition diagnostics
for `0x00ffa180` over frames 2306 through 2416 and identify the first native
departure from accepted Oracle/SPEC evidence. Compare the focused harness with
the parent checkpoint only as needed to determine whether the defect is a
runtime rule or a missing harness phase. Correct the entire Coffee Shop-
reachable owning program, not a frame, slot, or forced-release exception. The
expected causal result is natural release of `0x00ffa180`, living-count
decrement, and natural recurring allocation of `0x00ffa3c0` at frame 2511.

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
