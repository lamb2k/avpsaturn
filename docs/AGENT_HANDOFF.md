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
actors but no `0x00ffa3c0`. This is upstream of the later missing type-16
spawns at 3253/3258/3263, player damage write at 3263, and visible HIT at 3264.
Do not repair the downstream HIT with authored damage, a fixed-frame spawn,
slot substitution, or a weakened comparison.

## Exact resume prompt

Continue `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1` from the branch head. Preserve
the completed one-update Button1 dispatch contract and the new source-lifetime
assertion. Start at the first failing source frame 2511 and identify the owning
source program for the missing record-type-12/class-`0x1f` slot
`0x00ffa3c0`. Use the existing Coffee Shop actor-lifetime/spawn evidence and
accepted Oracle/SPEC fixtures to bind its spawn guard, scheduler phase, initial
state/substate, record, position/facing, and fixed-pool allocation. Then close
every Coffee Shop-reachable branch and actor instance owned by that same
program, not a single frame or slot exception.

If an implementation-required field is absent, record the exact field, amend
the existing SPEC-02 fixture from accepted Oracle evidence, and run only the
smallest bounded Oracle follow-up if that evidence genuinely lacks it. Do not
guess. Require the actor to remain source-valid through frame 3975 and naturally
produce the accepted `0x0208:0x0e02` type-16 effects at 3253/3258/3263, the
attack-record `0x03589e` damage write at 3263, and player HIT at 3264. Add real
mutations for the dispatch delay and the completed source program; rerun
Oracle, SPEC, generator, focused/full host, and Target. At the coherent
class-family boundary run the complete Coffee Shop census, paired Emulator,
focused WGC, commit, push, verify private-origin, and continue the existing
first-segment plan.
