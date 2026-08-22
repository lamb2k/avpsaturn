# USER-05-HUD-PCM-REVIEW task card

TASK: USER-05-HUD-PCM-REVIEW
KIND: USER_REVIEW
STATUS: CHANGES_REQUESTED
CHECKPOINT: review-hud-pcm
BASE: project_state.accepted_head
BRANCH: codex/avp-user-05-hud-pcm-review
TIER: 0
DEPENDENCIES: [SALVAGE-05-HUD-PCM]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [REPAIR-05-HUD-COLORS, SALVAGE-05B-PLAYER-2-HUD, INTEGRATE-03-PLAYABLE-SLICE]

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

- `REPAIR-05-HUD-COLORS` is required by the exact HUD-color feedback.
- `SALVAGE-05B-PLAYER-2-HUD` is required by the renewed exact Player 2 HUD priority.
- A bounded HUD/PCM `REPAIR` or promotion card after feedback.
- `INTEGRATE-03-PLAYABLE-SLICE` only after all its dependencies and approvals.

## Review result

- Exact response: `sound is great hud looks broken in terms of colors`
- Disposition: PCM `APPROVED`; HUD presentation `CHANGES_REQUESTED`.
- Approved component: the short Predator melee PCM cue presented in the USER-05 package.
- Requested change and first priority: correct the broken HUD color/palette presentation.
- The approved PCM payload, cue timing, and audible presentation are locked during repair.
- Next bounded card: `REPAIR-05-HUD-COLORS`.

## Renewed review after REPAIR-05

- Corrected package source: `949316331c7c12a9ae630ef5f5ebc846e4d2aef5`.
- Corrected screenshot SHA-256: `14c280bfb70ec86566cb394e0395383d4f6aeba1167c8aec8bc8b13e372edd2c`.
- Approved cue WAV SHA-256 remains `db539742a1cb77e2364055a26781c7bf0f1499f24fae1191c8b3f693e7b987d0`.
- Exact renewed response: `what about player 2 hud?`
- Exact priority response: `Let’s do that before we move on`
- Recorded observation: `HUDP2.BIN` is only the blinking `PRESS START` prompt; the frame-180 package captures its blink-off phase and does not present an active Player 2 HUD for review.
- Review status: `CHANGES_REQUESTED`; active Player 2 HUD presentation must be salvaged before continuing.
- Next bounded card: `SALVAGE-05B-PLAYER-2-HUD`.
- Corrected Player 1 HUD colors remain unapproved pending renewed review alongside the active Player 2 HUD; no approval is inferred.
