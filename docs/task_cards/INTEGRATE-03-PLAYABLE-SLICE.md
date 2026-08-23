# INTEGRATE-03-PLAYABLE-SLICE task card

TASK: INTEGRATE-03-PLAYABLE-SLICE
KIND: INTEGRATE
STATUS: READY
CHECKPOINT: integrate-playable-slice
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [INTEGRATE-02-COMBAT, USER-03-COMBAT-FEEL-REVIEW, PROMOTE-04-CAMERA-STAGE, PROMOTE-05-HUD, PROMOTE-06-PCM, PROMOTE-07-CDDA-RESIDENCY]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator, Full, Physical]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [SALVAGE-08-FRONTEND]

## Objective

Integrate promoted player, enemy, combat, camera/stage, HUD, PCM, CDDA, and
phase residency into the exact playable capability slice and close the required
physical Saturn capability conditions.

## Owned paths

- `src/port_v2/integration/slice/**`
- `tests/port_v2/integration/slice/**`
- Card-scoped release wiring/readback, migration ledger, state, and card

## Existing systems to reuse

- Only promoted components, exact source evidence, and accepted phase manifests.

## Systems deliberately disabled

- Frontend/full-route content, roster, multiplayer, and generalized engine work.

## Focused machine checks

- Strict compile; all approved locks; deterministic replay; illegal CDDA read,
  canary/asset, and dependency-order controls; Oracle, exact normal-release
  Target/emulator, Full, and the declared physical procedure.

## Saturn build profile

Dedicated integration profiles during iteration; exact `release-normal-release` for checkpoint acceptance.

## Emulator readback

Require semantic, resource, render, final-scanout, PCM/CDDA ownership, high-water/canary, fallback, frame-pacing, and stability domains bound to exact image/profile.

## Human-review requirement

Renew review for any approved component at risk. A final integrated subjective
checkpoint precedes physical testing; explicit user approval is not physical proof.

## Exclusions

- No physical claim from host/emulator results and no silent approval drift.

## Hard stops

- Any approved regression, illegal ownership, missing exact evidence, material architecture decision, or exhausted correction cycle.

## Next eligible cards

- `SALVAGE-08-FRONTEND` only after the physical capability slice is accepted.

## Current candidate checkpoint

- Candidate implementation: `dcd5daf12c4464e5f7982d87b18289519d357691`.
- Exact `release-normal-release` ISO repeat:
  `f1be594e8ceab37473333c46ff80b11a9a110c6969b7fc6c863638d042b2ba2b`.
- Host deterministic repeat, real negative controls, Fast, exact release build,
  and paired pinned-emulator semantic/readback review pass.
- Clean integrated HIT and KO frames retain the approved player/enemy alignment,
  camera/stage, P1/P2 HUD, PCM, and CDDA locks with zero fallback, late-read, or
  canary failures.
- Physical Saturn is `UNRUN`; emulator and user review are not physical proof.
- Required Full is blocked by generator drift in three artifacts outside this
  card's owned paths: `data/avsp_palette_coverage.json`,
  `data/avsp_translation_boundary.json`, and
  `data/avsp_vertical_slice_oracle_manifest.json`.
- The final integrated subjective checkpoint is pending. Do not activate
  `SALVAGE-08-FRONTEND` until the checkpoint, Full lane, and physical procedure
  are complete.

### Review correction 1

Exact user feedback:

> I don’t see a contact or hit just the alien and player loads camera pans
> animation of window breaking happens. They don’t engage in combat.

Disposition: `CHANGES_REQUESTED`. The semantic events passed, but the original
human-review presentation exposed each attack for only about 0.4 seconds and
then held the final KO indefinitely. Correct the Saturn review timeline to give
the approach, attack, HIT reaction, and KO durable visible holds without
changing the measured combat events or approved presentation/audio locks.

Correction candidate: `dcd5daf12c4464e5f7982d87b18289519d357691`.
The deterministic source events remain at the same four logical contacts, while
the review timeline now exposes the first approach/attack, a held alien HIT
reaction, three later contacts, and a durable KO. Paired exact-release emulator
sampling passed in the durable HIT (`605-839`), KO (`2480-2999`), and final
ownership (`3000-3059`) windows. The actual run-1 samples were `606`, `2481`,
and `3003`; run 2 sampled `607`, `2483`, and `3002`. Every sample preserved
three stage submissions per stability frame, zero fallback, zero late reads,
and intact canaries. Renewed integrated subjective review is pending.

### Review correction 2

Exact user feedback:

> The alien and player appear anchored incorrectly relative to the camera pan.
> The intended alien appears to change into a different stalker-like model. The
> combat exchange and its visible participants do not make sense.

Disposition: `CHANGES_REQUESTED`. These are objective scene-coherence defects,
not subjective polish. The current candidate proves that individual promoted
subsystems execute, but it does not prove a coherent gameplay scene. Do not
accept this candidate, activate `SALVAGE-08-FRONTEND`, run Full, or begin the
physical Saturn procedure.

The bounded correction must prove a shared world/camera transform, continuous
player and class-`0x1F` street-alien identity, causal attack/collision/damage
transitions, synchronized semantic and visual trace QA, and the declared
negative controls. If the source evidence does not bind the current HIT/KO
record/object/tile chain to the approved street-alien visual family, or if a
promoted interface outside this card's owned paths must change, stop at that
evidence or ownership boundary and propose one bounded repair card.

Correction candidate: `0d612401c874755acce62c25164ab9494dc967bd`.
The correction stayed inside INTEGRATE-03 ownership. Player and enemy now use
the declared shared transform `screen_x = world_x - camera_world_x +
aperture_origin_x`; the slice trace records both actor world/screen positions,
camera position, deltas, and both VDP2 scrolls on every sampled frame. At the
measured camera step from frame 45 to 46, both stationary actors move ten pixels
opposite the ten-pixel camera change. Omitted- and reversed-camera-term
controls fail as required.

The identity trace binds actor 31 to the class-`0x1F` street-alien
archetype/asset/animation family throughout walk, HIT, recovery, and KO. The
source actor slot `0xffa000` and table set `0x00130ac8` bind the observed walk
record `0x0012eb4c`, HIT record `0x0012dd50`, and KO records beginning at
`0x0012e214` to that actor. No stalker asset or animation set is selected; the
stalker-binding negative control fails.

Combat is now causal rather than presentation-time injected. Deterministic
attacks become active at frames 600, 1200, 1800, and 2400, use current on-screen
actor state, route damage from player 1 to enemy 31 exactly once per contact,
and produce health `87 -> 63 -> 39 -> 8 -> -1`, source-bound HIT, recovery,
and KO. No-overlap, pre-active, swapped-role, wrong-defender, enemy-versus-
enemy, damage-without-contact, and visual-HIT-without-semantic controls all
fail as required.

Paired pinned-emulator runs reproduce the normalized ISO SHA-256
`8699d5c642f7e3732de1d00c884ba4cd620e4e35bd036d8bacca8a74030ee8c4`
and an identical 271-sample synchronized semantic trace. Codex visual QA
correlated the continuous clip with the trace and found no camera reset,
identity substitution, unexpected actor, disconnected contact, wrong reactor,
or semantic/visual mismatch. This is emulator evidence only. Physical Saturn
is `UNRUN`; Full was not rerun under Review correction 2 as explicitly
directed. Renewed human review is pending, and INTEGRATE-03 remains unaccepted.
