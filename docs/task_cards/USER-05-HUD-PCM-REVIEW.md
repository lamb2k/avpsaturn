# USER-05-HUD-PCM-REVIEW task card

TASK: USER-05-HUD-PCM-REVIEW
KIND: USER_REVIEW
STATUS: BLOCKED
CHECKPOINT: review-hud-pcm
BASE: project_state.accepted_head
BRANCH: codex/avp-user-05-hud-pcm-review
TIER: 0
DEPENDENCIES: [SALVAGE-05-HUD-PCM]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-03-PLAYABLE-SLICE]

## Objective

Present the self-reviewed HUD/PCM bench and wait for explicit visual/audio feedback. Perform no implementation.

## Owned paths

- Ignored `build/feedback/USER-05-HUD-PCM-REVIEW/**`
- HUD/PCM user-feedback migration fields and review state only

## Existing systems to reuse

- Exact SALVAGE-05 screenshot/clip/audio clip, readback, profile/commit, systems, adaptations, and stability notes.

## Systems deliberately disabled

- All HUD, palette, PCM, audio, and integration changes.

## Focused machine checks

- Verify package identity, machine timing claims, and completeness.

## Saturn build profile

Reuse exact `HudPcmSalvageBench` image.

## Emulator readback

Reuse SALVAGE-05 readback only.

## Human-review requirement

Ask exactly: "What should remain unchanged, what looks or feels wrong, and which issue should be fixed first?" Record exact response and derived approvals/changes/priority.

## Exclusions

- No implementation or inferred approval.

## Hard stops

- Missing evidence or feedback; set `AWAITING_USER_FEEDBACK` and wait.

## Next eligible cards

- A bounded HUD/PCM `REPAIR` or promotion card after feedback.
- `INTEGRATE-03-PLAYABLE-SLICE` only after all its dependencies and approvals.
