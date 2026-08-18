# CPS2-to-Saturn reference engine

This is the architecture of a host-side, executable model that explains how a
CPS2 game's own data becomes work for native Sega Saturn hardware. It is an
investigative instrument and a specification for the eventual SH-2
implementation.

It is **not** a CPS2 emulator, not a 68000 interpreter running on Saturn, not an
attempt to reproduce CPS2 hardware behaviour, not screen-capture playback, not a
new AvP implementation branch, and not permission to import Marvel code, assets,
addresses, timing values or package sizes into AvP.

The boundary it exists to express:

```text
CPS2 semantic data and events
  -> platform-neutral actor / animation / object representation
    -> Saturn resource and rendering decisions
      -> VDP1 commands, VDP2 layer responsibilities, SH-2 gameplay work,
         cartridge and CD lifetimes, SCSP/CDDA event routing
```

Code lives in [`reference_engine/`](../reference_engine); the generated example
is [`data/reference_engine_normal_hit_report.json`](../data/reference_engine_normal_hit_report.json);
the AvP-facing question set is
[`CPS2_SATURN_REFERENCE_ENGINE_AVP_ADAPTERS.md`](CPS2_SATURN_REFERENCE_ENGINE_AVP_ADAPTERS.md).

## Evidence labelling

Every field the engine asserts carries exactly one label, enforced in code by
[`reference_engine/evidence.py`](../reference_engine/evidence.py):

| Label | Meaning | Structural requirement |
|---|---|---|
| `MEASURED` | Read from an instrument, or computed losslessly from such a reading | must name its source |
| `DECODED` | Produced by a validated decoder over private source data and recorded in a tracked artifact | must name its source |
| `INFERRED` | A hypothesis consistent with current evidence, not yet falsified | must name what would falsify it |
| `ADAPTED` | A deliberate choice made by this model; not a claim about any original program | must say why |
| `UNRESOLVED` | Named, required, and not known | must name the probe that resolves it |

`UNRESOLVED` is the only label allowed to carry no value; any other label with a
missing value raises. `INFERRED` without a falsification and `UNRESOLVED`
without a probe both raise. This is what keeps the model from quietly promoting
a guess.

## Why the model is reused rather than duplicated

The inventory below was taken before any new abstraction was written.

| Existing asset | What it already represents | Verdict |
|---|---|---|
| `tools/ref_interp.py` | Host reference interpreter for the 16-byte CPS2 pose record and its jump control flow | **Reused as the semantics of `AnimationProgram`.** The engine consumes the decoder's tracked JSON instead of the private ROM window, so it runs without ROM access. |
| `avsp_anim_script.h` / `.c` | The same walk in C, ready for SH-2 | **Reused as the target interface contract.** `AnimationProgram.walk` holds a pose for its duration then follows control flow, matching `avsp_anim_frame_tick`. |
| `data/avsp_animation_scripts.json` | Decoded pose records, jump records, and selector-6 assemblies with origins and ordered entries | **Reused as the source-layer input.** |
| `capability_model.h` / `.c` | `CapActor`, `CapAction`, `CapWorld`: a Round 1 lane/combat game model with route-specific constants | **AvP-specific, not reused.** It is a gameplay implementation with capture-derived constants, not a translation model. Duplicating it would import exactly the constants that must not cross. |
| `tools/analyze_mshvsf_saturn_memory.py` | Per-region hashes, non-zero and changed 4 KiB pages, and a sequential VDP1 summary | **Reused and extended.** Its VDP1 parser now calls the one traversal in `reference_engine/vdp1.py`, so there is a single implementation. |
| `data/mshvsf_cps2_semantic_model.json`, `..._saturn_semantic_model.json` | System-by-system prose models with explicit gaps | **Reused as narrative context.** They are not executable and were not re-expressed as code. |
| `templates/capcom_saturn_porting/*` | Record schemas for correspondence, differences, budgets | **Reused as the reporting vocabulary.** |

What was missing, and is what this engine adds: an executable path from a
decoded animation record to a costed Saturn command list, with separate
per-resource accounting and a deterministic semantic event trace.

## Layer 1 — source semantic layer

[`reference_engine/source_semantic.py`](../reference_engine/source_semantic.py).
Describes what the original game means. May not mention VDP1, VDP2, SCSP, or any
Saturn address.

### Animation script records

| Field | Offset | Label | Note |
|---|---|---|---|
| `duration` | +0 (u16) | `DECODED` | frames the pose is held |
| `flags` | +2 (u16) | `DECODED` | bit 15 redirects control flow; bits 14-8 sequence index; bits 7-0 parameter byte |
| `assembly` | +4 (u32) | `DECODED` | absolute address of the sprite assembly |
| `interaction_selector_a` | +8 (u8) | `DECODED` | interaction-table selector, reader established in the source disassembly |
| `interaction_selector_b` | +9 (u8) | `DECODED` | second interaction-table selector |
| tail +10..+15 | | `UNRESOLVED` | no proven consumer; deliberately not interpreted |
| jump record | 4 bytes | `DECODED` | pointer that closes or redirects the program |

Control flow is executable, not descriptive: `AnimationProgram.walk(frames)`
returns the pose shown on each frame, holding each pose for exactly its
duration, following the jump record, and treating a zero-duration pose as a
consumed slot that produces no frame. A program that can never produce a frame
raises rather than spinning.

### Sprite assemblies and ordered object parts

Assembly layout is `selector, budget, count, offset-index, origin-x, origin-y,
then count x (code, attribute, layout-adjust)`, all `DECODED`.

`order` is load-bearing. The source machine draws parts in list order and the
target has no per-command priority field, so order is the only ordering
information that exists.

Two readings of the CPS2 attribute word are `INFERRED`, and the engine reports
its own agreement rate rather than asserting them:

| Reading | Bits | Falsification | Current agreement |
|---|---|---|---|
| tile span | 8-11 horizontal, 12-15 vertical, each +1 | an assembly whose declared `budget` does not equal the summed tile count | **27 of 28 assemblies agree exactly; `0x13E36E` disagrees by two tiles** |
| palette index | 0-4 | a pose whose observed colour bank does not follow these five bits | every decoded part yields palette 27, consistent but not discriminating |
| per-part flip | 5, 6 | a mirrored part whose bits are clear | present in the data, not yet paired to an oracle |

That 27-of-28 result is why command pressure is reported as a **range** rather
than a number. It is a genuinely useful lead — the `budget` field is very likely
a 16x16 tile count — and it is not yet a decoded field definition.

### Actor state and events

`ActorState` binds a state name to an animation program. `StateTransition` is a
directed edge with a named trigger. `ActorStateMachine` rejects a transition
that names an undefined state.

`CollisionEvent` deliberately carries **no box extents and no damage number**.
Damage crosses as the opaque token `UNRESOLVED_DAMAGE_MAGNITUDE`. Inventing
either value is the exact error this engine exists to prevent, so the type
system makes it impossible rather than discouraged.

## Layer 2 — translation layer

[`reference_engine/translation.py`](../reference_engine/translation.py). Turns
source records into platform-neutral draw items. Decides no register value.

| Concern | Rule | Label |
|---|---|---|
| signed coordinates | `unwrap_signed(value, bits)` sign-extends narrow packed fields before use; the source packs object coordinates into 10-bit fields, and reading them unsigned wraps sprites at screen edges | `ADAPTED` |
| position | `part.x = actor_x + assembly.origin_x + part.layout_x` when facing right | `ADAPTED` |
| mirroring | facing left mirrors the whole pose about the actor origin, so `x = actor_x - offset - width`; `y` never moves | `ADAPTED` |
| flip combination | actor facing and the part's own source flip combine by exclusive or, because flipping twice restores the original orientation | `ADAPTED` |
| ordering | source order is preserved exactly and becomes target list position; sorting is stable on `order` alone | `ADAPTED` |
| palette identity | palettes cross as an index plus an entry count, never as a target colour address | `ADAPTED` |

`order_is_preserved(source, pose)` is asserted on every frame of every run, so a
reordering regression fails the model rather than silently changing draw order.
`mirror_pose` deliberately raises: mirroring an already-normalised pose has lost
the actor origin, so the correct operation is to re-normalise from the source.

## Layer 3 — Saturn backend layer

[`reference_engine/saturn_backend.py`](../reference_engine/saturn_backend.py)
and [`reference_engine/vdp1.py`](../reference_engine/vdp1.py).

### VDP1 command generation and traversal

One command model serves both directions, so a generated list and a captured
list are read by the same code. Command-word layout follows Sega's published
VDP1 command table format.

Generated lists reproduce the shape the reference capture measures: a system
clipping command, a local coordinate command, the ordered sprite commands, then
a draw-end command, all linked by jump-next.

Two emission strategies are costed on every frame:

| Strategy | Commands per pose | Meaning |
|---|---|---|
| `per_part` | one per source object part, at the part's full block size | the floor |
| `per_tile` | one per 16x16 tile | the ceiling, and the granularity the reference capture measures |

Both strategies allocate the **same texture bytes** for a pose. Only the command
count differs. That is the substantive architectural result: choosing per-tile
costs command-table slots and SH-2 list-building work, not texture memory.

### What the reference capture measures

From [`data/mshvsf_saturn_vdp1_control_flow.json`](../data/mshvsf_saturn_vdp1_control_flow.json),
all `MEASURED`, all on the reference title only:

| Finding | Evidence | Falsification |
|---|---|---|
| Every reachable command uses jump-next; the list is a flat run to a draw-end | 296 / 334 / 308 / 307 reachable slots at idle, normal-active, impact, recovery; jump-mode histogram is `{JUMP_NEXT: n}` at all four | any anchor with another jump mode, or a reachable set differing from the stored set |
| The stored non-zero extent is **772 slots at all four anchors**, far more than any anchor reaches | residual 476 / 438 / 464 / 465 slots past the terminator | a capture whose non-zero extent equals its reachable count while list length varies |
| Every drawn command is a 16x16 normal sprite | 1,233 drawn commands across four anchors, size histogram `{16x16: 1233}` | any other size, or a scaled or distorted sprite in the reachable set |
| Every drawn command uses `CMDPMOD` 0x0880: colour-bank mode, 16 colours | uniform across all four anchors; 12-14 distinct colour banks in use, 16 entries apart | a drawn command with a different colour mode |
| Horizontal flip is expressed in `CMDCTRL`, not by storing mirrored art | 101-107 `FLIP_X` commands per anchor, plus `FLIP_Y` and `FLIP_XY` at normal-active | a visibly mirrored actor with the direction bits clear |

The reachable-versus-stored distinction is the point of the rewrite. The earlier
analysis read stored order and stopped at the first draw-end bit, which is only
correct if every reachable command uses jump-next — true here, but previously
assumed rather than shown. The traversal now honours jump, call, return and skip
modes, the single hardware return-address register, and reports unmatched
returns, unaligned links, out-of-range targets and revisited slots as anomalies
instead of guessing past them.

`VDP1 registers read back as zero` through the debug interface, so the real
draw-start address and frame-buffer state remain `UNRESOLVED`.

### What the reference capture measures about VDP2 and SCSP

From [`data/mshvsf_saturn_vdp2_scsp.json`](../data/mshvsf_saturn_vdp2_scsp.json).
Two of these are negative results, and the negatives are the load-bearing part.

| Finding | Evidence | Label |
|---|---|---|
| The VDP2 **register block reads back as all zeros** at every anchor, so layer enables, plane maps, priorities and scroll values cannot be decoded from this capture at all | 0 non-zero bytes of 288, all four anchors | `MEASURED` |
| Every VDP1 sprite colour bank resolves into a **populated** VDP2 colour-RAM bank | 12-14 referenced banks per anchor, all resolving; all 128 colour-RAM banks populated | `MEASURED` |
| Colour RAM changes **inside** the combat window while VDP2 VRAM does not | 16 bytes in one bank at attack start; 35 bytes across three banks at recovery; VRAM byte-identical throughout | `MEASURED` |
| Only **three of thirty-two** SCSP slots hold any register content, and their registers are byte-identical across the whole window | one changing SCSP register byte per transition, the same byte every time | `MEASURED` |
| Gameplay audio therefore reaches the DAC as a **mixed stream**, not one keyed slot per event | slots static while sound RAM moves ~16 KiB across five pages per transition | `INFERRED` |

The colour finding matters for budgeting: colour-bank mode sprites spend a
**VDP2 colour-RAM** budget, not a VDP1 texture budget. The audio finding matters
for the adapter: `AudioRouter` routes gameplay cues to `SCSP_MIXED_STREAM`
rather than to a per-event slot, because a slot-per-event route would contradict
the measurement.

VDP2 layer assignment stays `UNRESOLVED`, but its probe changed: it now names a
**different instrument** (a register write watchpoint) rather than a better
parser, because the register block is not readable at all. That distinction is
the difference between work that would help and work that cannot.

The SCSP gap also moved. Cue attribution is `UNRESOLVED` with the probe pointing
at **sound-RAM refill regions**, not at slot registers, because slot registers
cannot attribute a cue when they never change.

### VDP2, work RAM, cartridge, SCSP

`ResourceLedger` keeps every region separate and **deliberately offers no
combined total**: work RAM, cartridge DRAM, VDP1 VRAM, VDP2 VRAM, colour RAM and
sound RAM are physically distinct, and summing them produces a number that
describes no real constraint.

| Region | Owner | Responsibility | Label |
|---|---|---|---|
| `vdp1_command_table` | VDP1 | one 32-byte slot per drawn part, rebuilt per frame | `MEASURED` |
| `vdp1_texture` | VDP1 | character pixels referenced by `CMDSRCA`, shared across frames; shares 512 KiB with the command table | `MEASURED` |
| `vdp2_vram` | VDP2 | scrolling backgrounds; byte-identical across the combat window | `MEASURED` |
| `vdp2_color_ram` | VDP2 | 16-colour banks addressed by `CMDCOLR`; every referenced bank is populated | `MEASURED` |
| `work_ram_low` | SH-2 | small per-frame mutation, 2-8 changed pages per transition | `MEASURED` |
| `work_ram_high` | SH-2 | principal gameplay state, 39-42 changed pages per transition | `MEASURED` |
| `cartridge_dram` | expansion cartridge | byte-identical through the whole combat window | `MEASURED` |
| `sound_ram` | SCSP | a refilled mixed-audio buffer: five changed pages per transition while slot registers stay identical | `MEASURED` |

Which structures live in those pages, which VDP2 layer owns what, how the two
SH-2s divide work, when the cartridge is written, and which sound-RAM refill
region carries which cue are all `UNRESOLVED`, each with its probe recorded in
`backend_claims()`.

### Phase loading and retirement

`PhaseResidency` records `loads`, `retains` and `retires` separately, so the
eventual runtime has somewhere to state lifetimes instead of implying that
everything is permanently resident. A byte-stable combat window cannot answer
load-time ownership; capturing team and stage loading is the named probe.

### Audio event routing

`AudioRouter` maps an abstract cue category to a Saturn transport and returns
`UNRESOLVED` for any category not explicitly routed, so an unrouted cue is
visible in the report rather than silently defaulted.

## Deterministic semantic traces

[`reference_engine/trace.py`](../reference_engine/trace.py). A trace is the unit
a future MAME-versus-native parity harness would compare, so its order must be
total and independent of insertion order.

Events sort by `(frame, priority, kind, subject, detail)`, where priority
encodes within-frame causality: input, state exit, state enter, pose, collision,
damage, audio, render. `is_totally_ordered()` reports whether any two events
share a sort key, so a genuinely ambiguous trace is detectable rather than
silently order-dependent.

## Determinism contract

Reports contain no timestamps, no absolute paths, no dictionary iteration order
and no unrounded floating point. Serialisation is sorted-key JSON written as
explicit LF bytes, so the recorded SHA-256 matches the file on any host. The
generator runs the model twice internally and fails if the two disagree;
`--check` re-runs it and compares against the tracked file without rewriting it.

## Reproducing

```bash
cd "C:/Game Dev/BrooklynBangoutX/AvPSaturnCapabilityTest-MSHvSF"
PY="$USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
"$PY" tools/analyze_mshvsf_saturn_vdp1.py
"$PY" tools/analyze_mshvsf_saturn_video_audio.py
"$PY" tools/build_reference_engine_report.py
"$PY" tools/run_reference_engine_tests.py
"$PY" tools/validate_mshvsf_training_package.py
```

The two analyzers need the private captures under `.deps/mshvsf_saturn_state`;
everything else runs from tracked JSON alone.

## Standing prohibitions

- No count, address, span, page total or command count measured on the reference
  title is a budget for any other title.
- A program's role in a scenario is a modelling choice, never evidence that the
  program is an attack, impact or recovery animation.
- Scenario trigger frames are not any game's startup, active or recovery timing.
- A stable cartridge or VDP2 region during one combat window does not prove
  load-time ownership or full-match residency.
- Similar record shapes across two Capcom titles do not make one title's
  structure mandatory for the other.
- A static SCSP slot set across four sampled frames does not prove that no slot
  is ever keyed per event; only a write trace can.
