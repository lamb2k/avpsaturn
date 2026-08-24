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

### Review hardening 3

Exact user feedback:

> The cleanup is substantially better. Preserve the shared camera transform,
> class-0x1F street-alien identity, causal attack/contact/damage sequence,
> camera/stage presentation, both HUDs, PCM, and CDDA.
>
> INTEGRATE-03 is not accepted yet.
>
> Before final approval, make two bounded hardening checks:
>
> 1. Pin the exact rendered street-alien identity across WALK, HIT, recovery, and
> KO. Validate the expected animation record family, palette, emitted object
> identity, and emitted tile identity for each phase. Nonzero render identities
> and matching archetype metadata alone are insufficient. Add a mutation that
> substitutes a wrong but nonzero object/tile family and require rejection.
>
> 2. Review the post-KO final framing. The host replay currently ends with player
> screen X at 260, outside the centered 352-pixel aperture. Determine whether
> this is an intentional exit. If it is intentional, capture and document it.
> If not, correct the bounded post-KO movement and recapture it.
>
> Keep the scene explicitly labeled ADAPTED: its movement and four attacks are a
> deterministic capability-slice choreography, not production player control or
> enemy AI.
>
> After those checks:
>
> - refresh the continuous before/after package;
> - repeat the paired emulator trace;
> - present the final clip for renewed human review;
> - resolve the three Full-lane generator drifts under their correct ownership;
> - rerun Full;
> - keep physical Saturn as a separate required procedure.
>
> Do not activate SALVAGE-08 until human review, Full, and the physical capability
> procedure are complete.

Disposition: `CHANGES_REQUESTED`. Preserve all named regression locks and keep
the scene `ADAPTED`.

Hardening candidate: `509cb20d9c8867e869ca3ade90c62ede57540571`.
The 322-sample exact identity contract pins WALK record `0x0012eb4c` on palette
`0x11`, HIT record `0x0012dd50` on palette `0x13`, recovery record
`0x0012eb4c` on palette `0x11`, and the KO record family `0x0012e214`,
`0x0012e244`, `0x0012e254`, and `0x0012e268` on palette `0x10`, together with
the exact emitted object/tile sequence for every sampled phase. Replacing the
valid HIT object/tile identity with the wrong but nonzero WALK family is
rejected.

The host X `260` result was not an intentional exit. Its fixture stopped the
camera at X `10` while the approved stage/emulator camera reaches X `161`.
Correcting that fixture produces the emulator-proven final contract: player
world X `446`, camera world X `161`, aperture origin X `-176`, player screen X
`109`, and a visible post-KO hold. No Saturn runtime movement changed.

Paired pinned-emulator runs bind commit `509cb20d9c8867e869ca3ade90c62ede57540571`
to normalized ISO SHA-256
`8699d5c642f7e3732de1d00c884ba4cd620e4e35bd036d8bacca8a74030ee8c4`
and identical 322-sample semantic/render traces. A foreground-pinned recapture
removed an occluded draft clip; Codex inspected the clean HIT, recovery, KO,
and final-hold frames and records `PASS_PENDING_HUMAN_REVIEW`. The three
generator-owned Full drifts were regenerated by their authoritative tools and
Full passes in its detached shadow worktree. Physical Saturn remains `UNRUN`.
INTEGRATE-03 remains unaccepted pending renewed human review and the separate
physical capability procedure; `SALVAGE-08-FRONTEND` remains inactive.

### Review correction 4

Exact user feedback:

> On the first player attack, the alien sprite still switches. The second
> recorded hit has no credible visible collision and the distance looks wrong.
> The third player attack is too far away and appears not to make contact. The
> fourth hit causes the player to lose grounding/anchor and the alien sprite
> switches again. The death animation works and should remain unchanged.

Disposition: `CHANGES_REQUESTED`. These are objective source-fidelity,
collision-coherence, identity, and grounding defects. The hardening hashes pin
only the current Saturn output and are not independent proof of source fidelity.
Do not accept or advance this candidate, begin physical Saturn, or activate
`SALVAGE-08-FRONTEND`.

Promoted-interface hard stop: the version-1 player contract exposes directional
input and IDLE/WALK presentation only. INTEGRATE-03 reduces player attack to a
boolean, chooses the next contact fixture by event count, and maps all four
attacks to one generic `CAP_ACT_ATTACK` presentation. It cannot carry the
required source selector, player action/substate, animation record, pose,
pivot, or selector-owned active window inside this card's owned paths.

Activate `REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION` on the existing
continuity branch. That bounded repair must establish independent cadence-1
MAME truth around samples 5190, 5236, 5283, and 5329 and extend only the
player/combat presentation interface needed to carry selector, action, pose,
pivot, grounding, and active-window state. INTEGRATE-03 may resume only after
REPAIR-09 is accepted, and must then replace the stitched choreography,
recapture source-versus-Saturn visual QA, rerun Full, and stop for renewed human
review. Preserve the working death/KO animation and every other approved lock.

### REPAIR-09 accepted interface checkpoint

REPAIR-09 implementation `417ed808e10f0f255948b1e6ecf0223399509c74`
accepts player/combat interface version 2. One independently captured MAME
source event now owns the attack selector, source player action/substate,
animation record, pose, pivot, height, active window, collision selector,
damage, and the corresponding class-`0x1F` alien reaction identity.

The four source contacts remain at relative offsets `0/46/93/139`. Paired
pinned-emulator readbacks and two independent 297-frame cadence captures pass;
valid nonzero wrong player/alien object and tile families, a wrong palette, and
a wrong selector are rejected. Codex directly inspected all four collision
overlays, the alien-family comparison, and the temporal strips. Attack 3's
silhouette gap is source-supported box reach; attack 4 is a source-supported
airborne pose with its own pivot and height. The death/KO sequence remains
unchanged.

Resume this card by replacing its stitched slice choreography with the accepted
source-bound interface. Then rebuild the complete `release-normal-release`
scene, rerun Full, and stop for renewed explicit human review before the
separate physical Saturn procedure. `SALVAGE-08-FRONTEND` remains inactive.

### Source-bound correction candidate

Candidate implementation `82965ef80223a03937e0b527d16161ed68d874a0`
replaces the stitched slice choreography with the accepted REPAIR-09 event
pipeline. The same measured event now supplies the attack selector, rendered
player record/pose/pivot/height, active collision box, damage, and matching
class-`0x1F` alien contact/reaction identity. Only deterministic input
choreography remains `ADAPTED`; production player control and enemy AI remain
`UNKNOWN`.

The exact `release-normal-release` image repeats at SHA-256
`4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`.
Paired pinned Yaba Sanshiro runs reproduce identical 577-sample traces,
including every frame from slice 583 through 879. Contacts occur at slice
frames `600/646/693/739`, source samples `5190/5236/5283/5329`, and selectors
`1/2/3/4`. Candidate-derived render hashes are explicitly superseded as
fidelity evidence; valid wrong player/alien object and tile families, wrong
palette, and wrong selector reject against the independent MAME source
contract.

Codex directly inspected all four exact-release contact frames, the cadence-1
reaction/death sequence, source collision overlays, alien-family comparison,
and grounding trace. Attack 3 retains the source-supported silhouette gap and
box overlap; attack 4 uses its measured airborne height/pivot only for that
pose. The accepted death/KO sequence and its late leftward source motion remain
unchanged. Camera/stage, P1/P2 HUD, PCM, CDDA, residency, canaries, and the
post-KO player hold at screen X `103` remain locked. Full passes in the
detached shadow worktree.

The ignored review package is
`build/feedback/INTEGRATE-03-PLAYABLE-SLICE`. INTEGRATE-03 remains unaccepted
and `CHANGES_REQUESTED` pending renewed explicit human review. Physical Saturn
is `UNRUN`; do not activate `SALVAGE-08-FRONTEND` before human approval and the
separate physical capability procedure.

### Actor-image evidence hardening

The complete candidate is `SOURCE_BOUND_WITH_ADAPTED_INPUT`; its task-level
workflow fidelity is therefore `ADAPTED`, not `MEASURED`. The independently
measured portions are selector/player presentation, active-window timing,
collision geometry, damage, class-`0x1F` reaction identity/timing, and the
KO/death sequence. Deterministic input choreography remains the adaptation.

The minimal cadence-1 comparator uses independent MAME actor layers and the
exact Saturn `PCMBT.RLE`, `TILES.BIN`, and `COMBAT.BIN` layers selected by the
paired trace, then corroborates their edges against all 390 applicable retained
Saturn framebuffer actor crops. It pivot-normalizes the 384-to-352 mapping and
calculates bounds, area, silhouette IoU, centroid, lowest visible baseline,
component count, edge similarity, and adjacent-frame change across all 297
frames. A valid wrong alien crop, one-frame Y offset, stale pose, skipped
reaction, and pivot jump all reject.

Seven source record changes intentionally reuse the same visible assembly:
player frames `5204/5249/5299/5350` and alien frames `5343/5345/5350`. Codex
directly inspected every automatically flagged MAME/Saturn pair. The layers
are silhouette-identical, and the record pairs resolve to the same source
assembly; no runtime correction is justified. Calculated metrics live in
`actor-image-metrics.json`, with dispositions in
`actor-image-direct-inspection.json`. Physical Saturn remains `UNRUN`, and
renewed human review is still required.
