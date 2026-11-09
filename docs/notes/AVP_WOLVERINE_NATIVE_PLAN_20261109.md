# Wolverine native fighter: crossover design and implementation plan

Status: Draft. Revised 2026-11-09. Execution status belongs in [STATUS](../STATUS.md).

This revision replaces the design recommendations in the earlier version of this file. It preserves the owner decisions updated through `52beea8` and the implementation checkpoint supplied in chat: complete the host identity pass, proceed only to the agreed movement/timing pass if it succeeds, then report before further gameplay work. This document is a plan; it changes no gameplay and reports no new runtime result.

Source snapshot: `lane/wolverine-native-20261109` at `52beea8d3b8b4e08fdb812b3d16c6634662fb913`, following `459d5c6` and `1ff6db2`. The [original source census, 61-field discussion, measurement notes and updated owner decisions](https://github.com/lamb2k/avpsaturn/blob/52beea8d3b8b4e08fdb812b3d16c6634662fb913/docs/notes/AVP_WOLVERINE_NATIVE_PLAN_20261109.md) remain available at that immutable revision. The corrections below supersede its design, memory and validation claims where they disagree.

Evidence labels: **MAME (prior)** = results reported by the original lane under MAME 0.289 `avspu` USA 940520, not rerun for this revision; **READ** = source inspection; **MODELLED** = proposed tuning or arithmetic; **HOST**, **EMULATOR**, **HARDWARE** = results only when actually executed at that tier. No native build, new asset fit, emulator result or hardware result is claimed here. Private ROM-derived inputs and generated assets remain outside commits.

## 1. Character brief and scope

**Schaefer's deliberate approach, Linn-paced claw offense, and a committed Berserker Barrage.** Wolverine should be recognizable from the way a fight plays: close-range claw pressure, distinct slash contacts, a decisive finish, and a signature burst that costs health. The shared player engine remains the foundation.

The success test is a short encounter: a player can predict where his claws will connect, continue a deliberately spaced combo, recognize its ending, use Barrage intentionally, and understand when movement control returns. A name, palette and animation swap does not meet this test by itself.

### Confirmed choices and recommended answers

| Concern | Plan | Decision basis |
| --- | --- | --- |
| Character slot and base | Wolverine replaces Schaefer; retain the shared player engine and a small character-specific fork. No fifth slot. | Existing guest architecture and owner decision at `1ff6db2`. |
| Walking weight | Keep the agreed Schaefer movement profile in the first native pass: approximately 2.08 horizontal pixels/tick and 1.0 depth pixel/tick in the prior MAME sample. Make it an explicit Wolverine tuning entry. | Latest recorded owner decision. "Own walk speed" means an owned parameter here, not approval of the old x1.375 boost. |
| Attack rhythm | Aim for Linn-like opening responsiveness; author the actual startup, active and recovery intervals. | Owner decision; exact new timings remain MODELLED. |
| Special | **Berserker Barrage on attack+jump, costing 6 health per accepted activation.** | Owner decision. It replaces the previous Tornado specification throughout this plan. |
| Costume | **80s colourway, red-brown and gold** (owner change, 2026-11-09; supersedes red/yellow on navy). HUD, select and rank art is the artist's revision 3 as delivered, on a crimson backdrop (asset set `E:\AvP\learning\lane-wolverine-merge\D11`). His sprite gets an 'eighties' palette entry in `remap.json`, selected at build time with `WV_COLOUR=eighties`, and is compared against red/yellow before it becomes the default. | Owner decision; palettes are generated data, no code impact for this lane. |
| Guns and carried weapons | Recommend claws only. Keep food and score pickups; refused weapons remain available to partners. | Existing eligibility wrapper; recommendation for the open question. |
| Healing factor | Recommend defer. Keep ordinary healing and life/continue rules. Extra food healing is also a balance change, not a free substitute for a healing mechanic. | Recommendation for this scope. |
| Attack boxes | Wolverine-specific claw contact shapes and windows, using AvP's collision and depth rules. | Required for visual/mechanical agreement. |
| Hurt boxes | Exact Schaefer boxes for identity proof; use them as the first native baseline, then check their fit against Wolverine's visible body. Any adjustment is bounded and explicitly recorded. | Recommendation; stock collision rules do not require identical body dimensions. |
| Combo progression | Each accepted attack press advances the stock chain even on a miss; preserve the existing reset and input acceptance rules. | Recommendation consistent with the measured source behavior. |
| Minimal move set and finish | Walk, jump, LP/LP/HP chain into the forward finisher kick, one air attack and Barrage, plus shared reaction/lifecycle states. | Owner decision through `52beea8`; preserve the kick and strengthen the claw identity of the preceding attacks. |
| Grab escape | Preserve stock behavior now. Measure whether the source already responds to mashing before proposing an enhancement. | Recommendation; no new escape system in this pass. |
| Talk-box face | Crop the face from the current red/yellow portrait, then simplify and inspect it at the actual target size/palette. Ask the artist only if the crop fails readability or expression. | Recommended task for the existing art/menu lane. No new portrait is required to begin. |

The first implementation does not add a universal dash, player throw system, launcher/juggle system, meter, regeneration, target homing, phase-through, or new cancel rules. Character-specific data and behavior still have room to differ: claw geometry, move rhythm, contact feedback, finish and source-supported special motion. A faster walk is a separate design choice if the owner later revisits the confirmed weight.

## 2. Combat design

### 2.1 Movement and stance

Keep the shared walk, depth, jump, interruption and boundary handling. Retain the distance-driven walk animation so feet follow actual travel. A low ready stance, visible claws, immediate existing turn behavior and a clean return to that stance establish character identity without a speed multiplier.

Do not add displacement after the shared world movement has already clamped a position. If an attack needs travel, use a proved source movement path with the same wall, depth and script constraints. Knockback, grabbed positioning, scene placement and cutscene movement must not receive the walk multiplier.

### 2.2 Ground combo: three claw beats and a clear finish

The confirmed sequence remains **LP -> LP -> HP -> forward finisher kick**. Make the first three attacks carry the claw identity: a quick opening, a readable return and a heavier rake, followed by a decisive kick. These are design roles, not claims that new suitable poses already exist. Audit the actual `lp`, `hp`, `hk` and Barrage frames, favor existing claw-forward poses where appropriate, and align each contact to the art. If a retained pose is a punch or kick, label it honestly; renaming its animation ID cannot make it a claw strike. A separate claw-finisher alternative is outside this confirmed minimal set.

Retain the source's three attack steps and finisher state. The finisher uses an existing knockdown and does not introduce a launcher or promise an airborne follow-up. Its forward contact direction must match the visible kick instead of inheriting an unseen rear sweep.

Initial timing candidates below retain the previous proposal's rhythm for comparison. **Every Wolverine value in this table is MODELLED and must be measured in the native build.** They are not imported fighting-game frame data. Tick counts refer to simulation/move progression; report elapsed time with hitstop separately.

| Stage | Readable action | Startup / active / recovery candidate | Total candidate | Contact and outcome |
| --- | --- | --- | --- | --- |
| 1 | Quick opening claw | 2 / 4 / 6 | 12 ticks | One accepted contact per target; modest pushback; stock stagger. |
| 2 | Return claw, distinct from the first beat | 2 / 4 / 6 | 12 ticks | Continues against an appropriately spaced ordinary target; stock stagger. |
| 3 | Heavier rake | 3 / 5 / 8 | 16 ticks | Clear stronger contact; retain the enemy for the intended finish where its reaction rules permit. |
| 4 | Committed forward finisher kick | 4 / 6 / 12 | 22 ticks | One deliberate final hit, existing knockdown response and visible recovery. |

The nominal sum is 62 ticks, versus the original lane's 77-tick Schaefer chain. This is not a measured complete-combo duration or damage-equivalence claim: input acceptance, pauses, hitstop and transitions can change elapsed time. Record those separately.

For each stage, the move specification must contain: native action and chain-stage entry, startup/active/recovery intervals, input-acceptance interval, pose/anchor, attack-box index, hurt-box policy, contact eligibility, pushback, reaction, sound event and exit. Keep the existing button-driven progression on whiffs. A miss must still show the complete intended recovery; no accidental free reset or hit-confirm requirement.

**Tune spacing before damage.** From a valid opening distance, the intended chain should connect on a suitable ordinary enemy without pushback automatically moving it beyond the next claw. Verify near and far edges of that distance, both facings, a corner, and a target that legitimately resists the intended reaction. Do not solve connection problems by giving every slash a screen-wide box or silently sliding the target toward Wolverine.

### 2.3 Berserker Barrage: a defined special

The sequence is **startup -> bounded slash sequence -> terminal knockdown -> recovery**. Barrage must have actual contact opportunities synchronized to the visible claws. It cannot be the old gun burst with hidden bullets, or a Tornado name/pose swap whose collision behavior was never reviewed.

| Aspect | Required behavior and proof |
| --- | --- |
| Input and health | Attack+jump through the existing special entry. Charge 6 once when activation is accepted, using the stock drain path and its low-health behavior. Rejected input, held buttons and each animation/contact frame must not trigger additional charges. |
| Facing | Establish a deliberate facing at entry. No homing or automatic cross-up. A turn during the move is allowed only if the retained source behavior explicitly supports it. |
| Hit sequence | Define each damage window, the source re-hit mechanism, and a fixed maximum of accepted hits per target per activation. Start with the existing special's verified contact cadence; choose the final count after measuring it. Demonstrate repeated accepted contacts on one ordinary target. If source re-hit behavior cannot support that within scope, report the limitation before accepting a single-hit fallback. No unbounded mash extension. |
| Shape | Forward-facing claw pressure with enough spatial coverage for its intended emergency role. Review the inherited two-sided special behavior explicitly: do not retain invisible rear damage or assume a forward animation covers a surround. Use an appropriate source-supported arc/turn if required; otherwise document the reduced coverage as a balance tradeoff. |
| Travel | A short advancing sequence is the preferred feel **if** it can use a verified existing special/attack movement path and respect all world bounds. First inspect what `f_24f04` actually writes. If that path cannot support safe travel, record the limitation and evaluate a planted Barrage before adding new movement logic. No free-standing dash. |
| Finish | Existing knockdown on the terminal eligible hit. Earlier hits and hitstop must permit the intended next contact; a knockdown on the first hit must not silently prevent the rest of the move. Respect armour and boss-specific responses. |
| Protection and interruption | Measure and preserve the source special's actual defensive windows. Do not assume the whole animation is invulnerable. Retain source priority for death, scripted entry, grabs and valid interruptions; clear guest move state without replaying hits. |
| Recovery | Explicit visual and mechanical end. No hitbox after the last intended active window, no animation held after control has returned, and no repeat activation until the stock entry rules permit it. |
| Objects | No gun projectile or muzzle-flash allocation for native Wolverine. Confirm zero such spawns for this activation; hiding them is insufficient. Other players' weapons remain functional. |

The old Tornado's proposed `2 / 48 / 7`, both-side reach and damage index are **not** accepted Barrage tuning. Establish Barrage from the retained source mechanism and the chosen slash poses. The 6-health cost is settled; damage, contact count, coverage and travel are calibration work.

### 2.4 Air attack, feedback and body geometry

Retain the shared jump arc and landing lifecycle. Make the existing air attack read as a deliberate aerial claw where available art supports it; align its contact window to that pose. Do not label it Drill Claw or add an air dash without implementing that behavior. Landing must terminate aerial contact correctly and immediately yield to the source reaction/KO paths.

Attack boxes describe claws; hurt boxes describe Wolverine's body. Keep AvP's depth band, collision order, damage pipeline and knockback rules. Begin native play with the donor hurt boxes, overlay them against standing, attacking, airborne and hit poses, and identify visible overhang or unjustified protection. Use modest, documented adjustments if needed rather than wholesale MSHvSF hurt-box transplantation. Preserve getup and special invulnerability rules independently of geometry.

Use available slash/contact sounds and stock hitstop as the first feedback palette. Stronger attacks should have clearer contact accents and recovery, not simply longer screen freezes. The contact cue belongs to an accepted hit event; a whiff produces a swing cue only. Keep voice clips, new effects and screen shake out of the critical path unless existing assets/mechanisms make their cost demonstrably small.

## 3. One move timeline owns both combat and presentation

**READ:** repeated Schaefer chain stages can stay inside action `020006`. Resetting animation only when the action byte changes misses a repeated slash. The skin's 15-tick inference and hold/recovery machinery exist to work around donor timing; they must not remain as a second combat clock in native mode.

Use the native chain stage and animation-record transition, or an explicit move-start event produced by the fork, to distinguish each attack instance. One authoritative definition drives the pose, active box, contact eligibility, recovery and exit. Respect the source's hitstop and pause semantics. A render snapshot must never advance a move, spend health or create damage.

Preserve atomic publication of the emitted pose and corresponding box step. A held/skipped display frame must not cause additional contacts or speed up the animation. Remove skin timing/box overrides only after the native path covers their responsibilities; keep the skin available under the default-off native switch.

## 4. Fork and data architecture

### 4.1 Keep the small fork, prove its actual boundary

The prior source census identifies nine distinct Schaefer-private routines at about 18.5 KB. Its first candidates for shipping forks are attack `f_24454` (956 B in that lane's SH-2 objects) and special `f_24f04` (982 B). These **READ (prior)** sizes support starting small; they do not guarantee that a finished Barrage and forward finisher need exactly 1.9 KB.

| Concern | Implementation policy |
| --- | --- |
| Shared player machine `f_195ec` | Keep shared. Its unchanged code still consumes changed records, so invariants require verification. |
| Attack `f_24454` | Fork the character-private behavior; preserve input semantics and explicitly expose chain/move boundaries. |
| Special `f_24f04` | Fork for the agreed Barrage behavior and its source-supported state transitions. |
| Finisher `f_19b78` / `f_1a3e2` | Prefer existing state plus data. If a distinct contact direction or transition needs a wrapper, identify and budget it; do not force an incorrect animation to fit the two-routine estimate. |
| Jump, walk, damage, getup, grabbed, KO, continue | Share source behavior. Patch only audited character-owned data where needed. Retain the existing KO-lane fix when integrating. |
| Gun and pickup | Refuse unsupported weapon entry at a known eligibility boundary and prevent native Wolverine gun spawns. Preserve food/score behavior and other characters' paths. |
| Unobserved actions, pre-tick and held-item paths | Retain the original safe fallback until reachability and entry/exit contracts are understood. "Not seen in one run" does not justify an empty stub. |

Keep the all-nine identity work already underway as generator evidence. Before promotion, run identity again on the **actual shipping configuration** with identity/empty patch data. Passing a larger diagnostic fork does not prove the later wrappers, pruning or patch lifecycle.

**READ build issue:** `saturn/rt/build.py` currently forwards `SAT_GUESTS` and `SAT_WOLVERINE_DEBUG` to `game_bind.c`, but does not forward the proposed `SAT_WV_NATIVE` flag. Propagate native-mode selection consistently to all participating target and host translation units. Report fork-entry counts so a passing host run cannot silently be testing the original path. Make absent/disabled native mode unambiguous.

### 4.2 Gameplay patches require ownership and a simulation-safe lifecycle

An in-place patch to the cart-resident ROM image is conditional on proving every affected byte belongs to the globally replaced Schaefer slot. `sat_guest_sel` is global today; a data patch must not affect another character, an enemy, or an unrelated script that aliases a record.

Required before removing the temporary collision patch/restore path:

1. Record every patched address, length, purpose, expected source revision, replacement and owner. Check overlaps and all readers; distinguish character records from shared lookup tables. Generated original bytes stay private.
2. Capture originals from the pristine image once per valid image generation, never from an already patched table. Apply idempotently and restore exactly. Reject an unexpected source layout instead of partially patching it.
3. Apply after relevant page/round restoration and **before the first simulation reader**. The existing cosmetic `names()` reapplication during drawing is not a sufficient lifecycle for gameplay data.
4. Cover guest selection changes, new game, stage transition, death/continue, restart and save/load. Define whether restored snapshots contain original or patched bytes and how ownership/generation state is reconciled.
5. Verify Wolverine in either player position with each supported partner, including Mega Man. If both players may choose the same replaced slot, they must follow the same global guest mode while retaining separate move state. Do not assume simultaneous stock Schaefer plus Wolverine is supported by one globally patched table.
6. If exclusive ownership cannot be established, use a bounded per-character record block/pointer redirection or another proved scoped mechanism, and measure its cost before choosing it. Do not patch a shared damage/heal table globally for a Wolverine-only effect.

## 5. Memory and performance budget

### 5.1 Art priority and fit

Barrage is core. The first compact asset candidate removes Tornado's dedicated poses and the redundant heavy-hit presentation, reusing an appropriate remaining hit pose while preserving the actual heavy-hit/knockdown gameplay state and duration.

| Quantity | Status |
| --- | --- |
| Prior full set | 1,511 unique tiles; prior stage-24 comparison was approximately one tile inside its existing gate. Historical input set only. |
| Tornado-exclusive tiles | 107 in the original lane's reported set analysis. |
| Heavy-hit-exclusive tiles | 99 in that analysis. |
| Simple saving | 206 tiles, or 26,368 pixel bytes at 128 bytes/tile; simple remaining count 1,305. **MODELLED candidate**, not a regenerated pack or linked margin. |
| Descriptors, code, patch originals and working state | Recompute for the selected move set and final combined build. These are separate costs and can change the cart boundary. |

The exclusive-count arithmetic is not permission to promise a new stage-24 margin. Regenerate the union of retained poses/tiles and audit descriptor, palette, code and mutable-state placement. Two dropped moves may also change sharing. Do not double-count the same byte savings.

Preserve, in order: basic claw contact poses; Barrage's recognizable slash/finish poses; complete walk/jump silhouettes; landing, hit, grabbed, knockdown and KO readability. Remove redundant reactions and unused signature-move art before thinning the attacks that establish identity. Near-duplicate tile merging is a separately reviewed reserve, with contact-sheet inspection.

**READ integration issue:** `tools/wolverine/gen_c.py` currently requires all 14 runtime move keys, including `tornado` and `hit_h`; runtime constants also refer to them. Asset removal therefore needs a coherent retained-move/alias manifest and runtime mapping. Deleting dictionary entries alone is not a buildable pruning strategy. Test that every reachable state resolves to resident poses and matching boxes.

### 5.2 Correct the main-memory assumption

**READ:** in `saturn/rt/build.py`, guest `.text`, `.rodata` and `.data` are selected into `.cold1`, while ordinary guest `.bss` falls through to `.lwbss`. Putting an object in the guest/cart list does not put its mutable state in cart RAM.

The old estimate was about 260 B of native state plus about 300 B of saved originals, against 229 B of existing state and only 76 B of reported low-RAM headroom. That is roughly **331 B of incremental state before alignment**, which exceeds that historical margin unless removal or explicit placement pays for it. This is a concrete allocation risk, not a measured new link failure.

Replace "needs no main memory" with **"target no increase in main RAM, to be proved by the linked map."** Give each new or retained buffer its size, alignment, owner, placement and lifetime. Explicit cart-backed storage needs a reservation, initialization/reset/save-load contract and accounting against sprite room. Include stack use and initialization work; do not hide them inside the 600-byte patch-table estimate.

`GUEST_WRAP` retains the lifted original body. A Wolverine-only stub does not reclaim Schaefer's 2.2 KB gun handler or 6.1 KB held-item handler when the original game still needs them. Count only verified removal of existing guest code and actual linked section changes as savings.

Use one accounting sheet for code, constant tables, patch data, original-byte backup, per-player state, scratch/stack, sprite tiles and descriptors. Report high/low RAM, cart boundary, every stretch region and the worst stage. Historical `hw_free=4,616` / `lw_free=76` values are context, not the current combined-disc budget. The integration lane's pinned build is the release comparison.

### 5.3 Performance remains a separate gate

Attack/special handlers may execute every simulation tick while active; "a few calls per second" is not established. Measure calls and target cost before accepting cart placement as performance neutral. A correct host result and a tile fit do not establish Saturn speed.

The current guest renderer emits one-tile objects; the earlier ordinary-sprite pairing experiment does not automatically reduce Wolverine's command count. Measure the combined candidate's CPU cost, command count, uploads, display cadence and slow-frame tail in the same busy scenes. Retain atomic publication and the existing presentation fixes. Coordinate with the slowdown lane rather than opening another renderer optimization effort.

## 6. Damage and balance

The prior MAME sample reported 15-tick Schaefer taps, 12-13-tick Linn taps and a 6-health special cost for the two tested human characters. It did **not** establish Wolverine's damage. The original note explicitly says attack-record byte 9 indexes a lookup affected by enemy class/difficulty/armour; summing those indices and dividing by ticks cannot establish damage output or relative strength.

Measure actual target HP before/after each accepted contact, contact count, reaction, pushback, active-move elapsed time and recovery. Include normal, resistant/armoured and boss targets at documented settings, plus multiple-target scenes. Use isolated fixtures for calibration and normal gameplay for confirmation. Keep all candidate damage indices provisional until their effects are known.

Compare the full chain, repeated combat including repositioning/knockdowns, incoming damage, and Barrage's damage/control per 6 health spent. At equal damage and with all other time ignored, 77/62 is about 1.24: shortening a nominal chain that far could increase theoretical throughput by about 24%. That arithmetic motivates measurement; it is not a prediction of actual DPS.

Recommended initial balance intent: faster contact and stronger close pressure, paid for by short reach, committed recovery and normal positional vulnerability. Do not simultaneously increase speed, damage, reach and protection. Make each tuning change answer an observed problem. Check for corner lock, repeated-special abuse, excessive co-op hitstop and attacks that hit on every overlap tick.

## 7. Verification contracts

### 7.1 Exact identity and isolation

Use two explicit baselines: **native OFF matches the pre-native skin build at the same assets and equivalent flags; the identity fork matches unmodified Schaefer with guest gameplay policies disabled.** Within each comparison, use the same revision, inputs, seed and initial state. Compare the complete relevant player state, actual writes/outbound effects, routine call ordering and flags/registers required at adapter boundaries. Retain the 61-field interface as a checklist, not the entire observable state. Cover the complete relevant actor/projectile pools or track writes; a sampled prefix can miss leakage.

Identity mode must explicitly disable guest policy changes such as weapon refusal, movement scaling, altered boxes, custom timing and hidden-shot behavior; otherwise it is not an identity baseline. Presentation differences can be excluded only with a named boundary that still proves gameplay equality. Prove both the diagnostic fork and the final shipping fork/identity-data configuration actually run through the intended wrappers.

For global data patch ownership, assert exact bytes before/after apply/undo and test unmodified characters under equivalent independent setups. A partner's later fight outcome can legitimately change after Wolverine hits a shared enemy; that is different from a leaked character-table edit.

### 7.2 Deliberately different native combat

Once timing, reach or damage changes, same-input fights naturally diverge: enemies are hit earlier, retaliate differently, and may change later AI, player health and script timing. Do not require every unlisted field to remain equal every tick after that first intended interaction.

Use matched starting states for changed-routine tests, with explicit allowed writes, numerical bounds, valid transitions and expected contact/health events. In complete fights, check invariants and causal outcomes. State-entry alignment may help compare an isolated move; it cannot make two diverged encounters equivalent. Diagnose the first intentional difference and its consequences rather than enlarging an allowlist until a test passes.

### 7.3 Minimum native scenario matrix

| Scenario | Required observation |
| --- | --- |
| Single taps, slow taps, rapid presses, held attack, whiffs | Correct next stage and reset; complete recovery; repeated `020006` entries restart the right pose; no phantom finish. |
| Full chain, both facings, near/far valid range | Visible claw contact matches accepted damage; early pushback permits intended continuation; terminal knockdown occurs once. |
| Special in open space, edge/corner, surround, normal enemy and boss | One health charge per accepted activation; bounded accepted hits; reviewed coverage; valid motion/protection; no spawned bullets or wall escape. |
| Low-health special and input overlap | Retain the source's measured eligibility/drain behavior; no double action or charge from held attack+jump. |
| Jump attack and landing | Correct aerial contact and lift; no lingering box after landing; stock transitions. |
| Hit, grab, knockdown, getup, KO, continue, script entry | Valid priority and cleanup; visible body; no stale movement, invulnerability or move clock. |
| Food/score/weapon pickups | Stock food/score handling; weapon refusal leaves item intact; partner pickups and attacks remain functional. |
| Guest OFF/ON, stage changes and save/load during a move | Original data restored or native data reapplied before gameplay as appropriate; no duplicate backup, stale patch, replayed contact or stuck drawing. |
| Wolverine in P1/P2 with supported partners | No table leakage; separate per-player move clocks; source co-op collision policy; correct HUD and assets. Include Mega Man in the combined build. |
| Render hold/skip and busy multi-actor scene | Simulation timing and accepted-hit counts independent of picture cadence; no mixed pose/box publication. |

Retain the full 76-file fit/own-tile residency gate against the final assets, exact OFF comparison, Round 1 through boss-clear check, save/load cycles, and source full-route/reaction coverage. Each result names its commit, flags, asset revision, scenario and evidence tier. EMULATOR and HARDWARE remain separate gates; existing historical results do not qualify a new combined build.

## 8. Execution order and lane handoff

The user's current checkpoint takes precedence: **finish identity; if it passes, implement only the agreed movement and attack-timing pass; report before going beyond it.** The later stages below are the revised roadmap, not an instruction to run past that checkpoint.

| Step | Work | Exit / handoff |
| --- | --- | --- |
| 0. Preserve the active identity work | Continue the all-nine host diagnostic if already underway. Ensure host/target flags and wrapper counters are real. Audit mutable-state placement while this runs. | Exact gameplay-equivalence report, exercised paths and gaps; no claim that a diagnostic fork fits the shipping disc. |
| 1. Authorized timing checkpoint | Make the agreed movement profile explicit; retain Schaefer weight. Implement the intended attack-timing change. Test the final minimal fork with identity data as well. | Report measured timings, input/recovery behavior, linked resource budget and outstanding risks **before further gameplay changes**. |
| 2. First playable crossover slice | After that checkpoint, implement the claw chain and specified Barrage with provisional calibrated damage and the intended pose/contact timing. Use the existing jump/reaction behavior. | Short playable review against one ordinary enemy, a small crowd and a boundary, plus co-op spot checks. |
| 3. Feel and balance | Review contact honesty, connected spacing, distinguishable finish, Barrage commitment, control return and incoming-risk tradeoffs. Calibrate actual HP damage across target classes. | Move table filled with measured values; explain each difference from the source. No approval based solely on a video or a nominal tick count. |
| 4. Combined qualification | Integrate the existing menu/art, KO/Round 1, slowdown and memory-fit lanes at named commits. Repeat gates on the actual combined code/assets/flags. | Full fit and runtime evidence; owner visual review; hardware qualification separately recorded. |

The first playable review should answer five questions: do the claws hit where they look; can the intended chain stay connected; does the finish feel distinct; is Barrage a recognizable purposeful burst; and can the player predict when control returns? If these fail, revise the move definition before polishing presentation.

Keep one writer per implementation file. The native lane owns player behavior and patch/timeline integration; the existing art/menu lane owns palette/HUD/talk-box assets; the KO/Round 1 lane owns its fixes and run evidence; the slowdown lane owns renderer experiments; the combined-fit/integration lane owns final resource and build qualification. Confirm actual file assignments before touching shared `build.py` or `game_bind.c`. This plan does not launch duplicate lanes or supersede their fixes.

The earlier 12-15-working-day figure remains a historical estimate, not a renewed commitment. Re-estimate remaining work after the active identity pass exposes fork/host integration cost, the state allocation is proven, and the Barrage movement/re-hit mechanism is understood. Share useful playable evidence at the early slice rather than withholding it until all polish is complete.

## 9. Source references and reporting limits

- [Original plan and owner decisions through `52beea8`](https://github.com/lamb2k/avpsaturn/blob/52beea8d3b8b4e08fdb812b3d16c6634662fb913/docs/notes/AVP_WOLVERINE_NATIVE_PLAN_20261109.md): routine census, historical sizes, per-character MAME sample, exclusive-tile counts, minimal move set and red/yellow art with a navy backdrop.
- [Animation audit](AVP_WOLVERINE_ANIM_AUDIT_20261109.md): same-action chain transitions, pose thinning, jump correction, skin timing work and its limits. The native design must not recreate those clock conflicts.
- [Player interface](../guests/PLAYER_INTERFACE.md): field/reader census. Apply the original note's census caveats and this revision's identity/native distinction.
- [Runtime guest implementation](../../saturn/guests/wolverine/wolverine.c), [bindings](../../saturn/game/game_bind.c), [build/linker](../../saturn/rt/build.py), [asset generator](../../tools/wolverine/gen_c.py), [guest selector](../../saturn/rt/guests.c): the source boundaries inspected for this review.
- [Capcom Wolverine guide](https://static.capcom.com/mvc3/04ao_marvel_wolverine.pdf) and [Ultimate guide](https://static.capcom.com/umvc3/manuals/04Q_Wolverine.pdf): primary references for the vocabulary of claw pressure, Barrage, contact sequences and commitment. They are from later fighting games; their numerical frame data, invulnerability, cancels, assists and resource systems are not AvP specifications. The project's MSHvSF captures remain the pose reference.

This revision performs READ/design work only. Function census and source behavior-matching scores are unchanged; no new whole-game matched-frame count is claimed. The native damage curve, exact Barrage contact/travel behavior, final body geometry, actual memory margin and hardware performance remain implementation/qualification results to obtain, not conclusions of this document.

## 10. Owner constraints recorded during execution (2026-11-09)

These came from the owner while the identity and movement/timing checkpoint was running. They apply to Stage 1 and everything after it.

1. **Data rule: "the more of his game data we take the better he performs."** Anything about his body and animation comes from MSHvSF's own data (read from the MSHvSF reference lane where needed), not from Schaefer's: pose order and timing, hurt boxes and attack boxes, Berserker Barrage's hit sequence and frame data, the jump arc, active frames. Anything about the game's balance stays AvP-scaled: damage in HP, pushback against AvP enemies, the 6-health cost, walk speed (the owner set Schaefer's weight), getup and knockdown rules. Where Linn-speed attack timing (section 2.2) and MSHvSF timing conflict, the owner-approved current pacing is the reference and the options are reported, not chosen silently.
2. **Pacing reference.** "His combo looks pretty good now from a pacing perspective": the current skin chain (LP, LP, HP, HK; hold table, chain fixes `adb5840` and `d6235c1`). It is the reference for every attack-timing change, measured on the host harness (`docs/notes/AVP_WOLVERINE_NATIVE_STAGE01_20261109.md`, section 3). A stage that gets noticeably faster or slower is flagged; the pacing is not changed silently.
3. **Hurt boxes.** "He also takes damage pretty well from a hitbox perspective": the per-pose MSHvSF hurt boxes hooked into collision `f_1cf54` (`boxes.json`, `d7dd591`), not Schaefer's stock boxes. Section 1's "start from Schaefer's hurt boxes" is superseded: today's hurt boxes are the baseline and the reference. The fork and the patch layer do not touch them. Any later change goes to the owner with before/after evidence.
4. **Not frozen.** "I'm open to it moving, just want to compare and see how it feels first": pacing and hurt boxes may change, but each change must be playable side by side with the current behaviour (a switch or a second disc) plus clips before it becomes the default. `-DSAT_WV_NATIVE` stays default off; nothing here is a default.
5. **Merge note.** Another lane (`lane/wolverine-ground-20261109`) owns per-pose anchor offsets, `wv_lift` (jump apex) and box geometry in `gen_c.py`. This lane does not edit those and rebases on that branch when it merges.
