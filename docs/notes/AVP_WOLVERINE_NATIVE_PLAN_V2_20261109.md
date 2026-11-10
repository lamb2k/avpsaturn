# Native Wolverine plan, revision 2 (owner, 2026-11-09)

Owner direction: "There shouldn't be any replacement Wolverine should be a native character." No more work on the skin (sprite replacement) except blockers; all Wolverine effort goes to this plan. Supersedes the execution order of AVP_WOLVERINE_NATIVE_PLAN_20261109.md (lane/wolverine-native-20261109); its owner answers (section 10) still apply.

**Next milestone: one complete native Wolverine attack** (his own animation records, his own collision data, sprites emitted through the normal drawing path). It proves the architecture before committing to the full move set.

Corrections to earlier reporting:
- 11.4% and 2.9% are held-picture percentages, not all missed frames. Keep the measured rendering overhead separate from Yaba's host slowdown (AVP_FPS_HELD_20261109.md).
- 36-37 hits versus 2 (AVP_WOLVERINE_GATE_20261109.md) is an investigation trigger. Those runs were non-deterministic and assisted; they do not establish how much worse his defense is or which change caused it.
- The sprite-dropout finding (13e63b5): Yaba's dynarec recompiles cart-resident code; SH-2 cache emulation off restored 60 vblanks/s in that test; dropout reproduced under host load while stepped captures stayed intact. A package still needs normal-play qualification; frame-by-frame captures alone do not establish readiness.

## Goal

Wolverine is a native participant in AvP's existing player, collision and drawing systems: recognisable claw attacks, a deliberate Berserker move, reliable inputs and matching visual contact. Movement, damage reactions, enemy interactions, pickups, KO and continue stay integrated with the shared engine. The first milestone is a small playable demonstration that proves data, timing, collision, drawing and memory together.

## 1. Preserve the work that already passed

- The native host runner, fork generator and field-comparison harness (272,171 host frames matched the stock route; HOST evidence only).
- The shared player engine and the smallest necessary character-specific handlers.
- The KO fix and the verified rendering/palette corrections.
- The approved sprite size, red/yellow appearance and reusable animation assets (D11).
- A reproducible build of the current skin for comparison and fallback.

## 2. One clear implementation per responsibility

| Responsibility | Native design | Workaround it replaces |
|---|---|---|
| Animation and move progression | Wolverine-owned records advanced by the existing game update, honouring normal hitstop and pause | Stretching Schaefer's updates; separate recovery clock |
| Drawing | Emit his current pose once, in the normal actor draw order | Draw Schaefer, find and remove his sprites, insert Wolverine |
| Attack and hurt boxes | Persistent character-owned collision records consumed by the shared collision system | Overwriting donor data around collision checks |
| Berserker | Explicit native action: input, contacts, resource policy, sound, recovery | Entering the gun action and blocking its projectile allocation |
| Palette and presentation | Defined init/update rules for selection, stage loads, fades, flashes | Rewriting unchanged palette rows every snapshot |
| Character identity | Stable identity per player slot through attacks, damage, grabs, KO | Inferring identity from a field that changes during death blinking |

The shared engine keeps world movement, depth rules, damage resolution, enemy reactions and player lifecycle.

## 3. Trustworthy baseline

Record the exact commit, asset set, build flags, emulator version and settings. Measure separately:
- host execution speed (emulated vblanks per wall-clock second);
- game work (emulated CPU timing, update overruns);
- presentation (new, held, skipped, late pictures);
- animation (pose changes and move progression per game tick).

Input scheduled by emulated ticks; one controlled emulator session for measurements. The dropout-lane guards are a partial improvement; hot-code relocation is still proposed; the cache setting is a documented emulator workaround until qualified.

**Exit:** the reference build is reproducible, and slow host emulation, missed presentation, missing sprites and slow animation can be told apart.

## 4. Memory placement and native data access first

A build-generated Wolverine data block: animation records, sprite assemblies, collision records and their links. It must:
- stay available through every stage, including stage 26;
- use valid game addresses and checked offsets, with the required byte order and alignment;
- survive restart, stage transitions and supported save/load;
- be counted in full in the combined build's memory report.

The lifted game reads dynamic addresses through its page table (saturn/rt/lift_target.h). A raw SH-2 cart pointer cannot be written into an animation or collision field: reserve and audit a valid mapping, or a small resolver at the proven access points. Separate hot code from large immutable tables; profile which routines benefit from work-RAM placement and budget it explicitly. The 108-byte margin belonged to one D6 native build, not the current combined disc; crossing a 4 KB tail boundary costs 32 sprite tiles, so budget code, records and sprite storage together.

**Exit:** the data image and hot code fit the current combined build with explicit remaining headroom.

## 5. One complete native attack

Idle, walk, one claw attack and the return to idle on the new data path. First candidate format: the sprite-assembly format documented in tools/decode_avsp_animation_scripts.py (explicit tile offsets), proved on the actual target path.

- The existing game progression advances the move.
- Displayed pose and active collision record agree.
- The player stays responsive under the engine's normal acceptance rules.
- Emitted once, with correct facing, ground position, clipping and depth order.
- A hit interrupts the attack correctly.
- Re-rendering the same picture cannot advance the move, repeat damage or replay sound.

First test relocated records holding donor-equivalent data: only the named pointer-address changes allowed; compare referenced content, non-pointer player state, emitted objects and effects on other actors. Then substitute Wolverine's art and combat data.

**Exit:** a short playable encounter proves the complete path with no sprite-replacement pass or attack-stretching for that move.

## 6. Extend across the character

Remaining combo stages, finisher, air attack, Berserker, all reaction/lifecycle poses. One specification per move: input and acceptance; startup, active, recovery; pose, attack box and hurt-box selection; damage, pushback, reaction, repeat-hit limits; sound, resource use, interruption, exit. Keep the approved reference behaviour during migration; compare faster timing candidates separately once native works.

Stage 1 findings carried forward:
- The combo latches follow-up input; it does not need one new press per stage.
- The stock special charges 6 health on contact, nothing on a whiff (owner: keep consistent with the game).
- Measured native timing candidate 12 / 12 / 16 / 28 ticks; the kick is not yet the proposed 22-tick finisher.

Berserker: route the approved input straight into its native action before any gun side effect. Define acceptance, cost, repeat rate, contacts and recovery independently of the gun routine (removing heat must not make it unlimited). Explicit swing and hit sounds. Zero Wolverine projectile and muzzle-flash allocation while a co-op partner's weapons keep working. The projectile-pool suppression (62d16f7, fedd907) is a temporary compatibility measure.

Defense: short repeatable incoming-attack tests isolating hurt-box geometry, depth overlap, hitstun and recovery, getup and special invulnerability, grab entry and escape. One cause at a time; full rounds afterwards for overall playability.

**Exit:** all required states use consistent native data, with documented contact and interruption behaviour.

## 7. Retire the old machinery and qualify

Remove: donor sprite removal/reinsertion, the attack hold/recovery scheduler, collision patch-and-restore, in-place changes to Schaefer's records, projectile-pool manipulation. Credit memory savings only when they are absent from the linked native build; keep the legacy skin as a separate build if carrying both costs needed memory. In parallel: grounded feet, jump appearance, grabbed and KO poses, HUD/name art, talk-box face from the approved portrait.

## Release gates

| Area | Evidence |
|---|---|
| Gameplay integrity | Other characters keep baseline behaviour; both player slots and mixed co-op work |
| Character behaviour | Reliable inputs, visual/mechanical contact agreement, bounded combos and specials, correct interruption |
| Lifecycle | Damage, grabs, KO, continue, restart, stage transitions, save/load |
| Visual correctness | Inspected frame sequences for contact and transitions, plus normal-speed play with no disappearing sprites |
| Performance | Total frame cost and presentation cadence vs the reference; emulator wall-clock speed reported separately |
| Memory | Current combined link map and all 76 stage fits, no missing keys or unplanned tile loss |
| Playability | An unassisted Round 1 run; assisted bot completion is a separate result |
| Hardware | Real Saturn measurements before claiming console frame-rate parity |

Paused captures and free-running play must both pass.

**First deliverable:** the one-attack native build, its memory map, a short inspected clip and a controlled performance comparison. That result sets the estimate for the remaining move set.
