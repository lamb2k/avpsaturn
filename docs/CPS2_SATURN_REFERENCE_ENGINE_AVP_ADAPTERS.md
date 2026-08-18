# Reference-engine AvP adapter questions

This document records what the CPS2-to-Saturn reference engine would need in
order to accept AvP records, and what AvP must prove first. It is a question
set, not an integration plan.

## Snapshot provenance

Every AvP clue below was read from an **immutable committed snapshot**, never
from the AvP working tree:

- AvP checkout: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Branch at time of reading: `codex/avp-master-plan`
- Committed HEAD read: `79c313032791e99dd01c3217c4d148e23a36871b`
- Read method: `git show 79c313032791e99dd01c3217c4d148e23a36871b:<path>`

That checkout had uncommitted work in progress (a modified `CLAUDE.md` and
roughly two dozen untracked diagnostic tools and one untracked data file). None
of it was read, staged, committed, moved, or relied on. No file in the AvP
checkout was changed and neither branch was switched or merged.

Files read at that commit: `AGENTS.md`, `docs/AGENT_HANDOFF.md`,
`docs/PARITY_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/GOAL.md`,
`avsp_anim_script.h`, `avsp_anim_script.c`, `capability_model.h`,
`tools/decode_avsp_animation_scripts.py`, `data/avsp_animation_scripts.json`,
`data/round1_hitbox_geometry.json`, `data/stage1_route.json`.

Relative to this research branch's checkpoint `4b82653`, that commit differs in
exactly one of those files: `docs/ARCHITECTURE.md`, by a five-line preamble. The
other snapshots are byte-identical, so nothing here depends on a stale read.

## Standing rule

Nothing below is proven for AvP merely because the reference title does it, and
nothing below is proven for AvP because AvP happens to use a similar structure.
Each row names the AvP probe that must pass first.

## Mapping table

### 1. Animation-script records

| Field | Content |
|---|---|
| Reference-engine concept | `PoseRecord` + `JumpRecord` + `AnimationProgram.walk` |
| Reference-title evidence | None. The reference title's own animation tables are **not decoded**; only its Saturn output is measured. |
| AvP committed clue | `avsp_anim_script.h` defines the 16-byte record (duration u16, flags u16, assembly u32, 8-byte tail) and `avsp_anim_next_address` follows flags bit 15 to a u32 at record+16. `data/avsp_animation_scripts.json` holds 6 decoded programs, 29 script pointers, and labels tail bytes +8/+9 as interaction-table selectors with readers `0x1cf94` and `0x1cf88`. |
| Similarity | The engine's source layer was written directly against this record shape, so the adapter is a field rename, not a translation. |
| Important difference | The engine reads the **tracked decoded JSON**; the AvP runtime reads **raw ROM bytes**. The engine also never consumes tail bytes +10..+15, matching the C interpreter. |
| Required AvP validation probe | Decode a real AvP **attack** program for one actor, not only the boss walk loops and single-pose programs currently present, and confirm the walk reproduces the captured per-frame pose order and durations. |
| Intended AvP decision | Whether the proven host interpreter can drive pose *selection* in the native runtime, closing the open half of Gate 1 condition 1. |

### 2. Sprite and object assemblies

| Field | Content |
|---|---|
| Reference-engine concept | `SpriteAssembly` + ordered `ObjectPart` |
| Reference-title evidence | `MEASURED` on the Saturn side only: every drawn command is a 16x16 normal sprite in 16-colour bank mode, so the official port's assemblies reach VDP1 as per-tile commands. |
| AvP committed clue | The selector-6 format `selector, budget, count, offset-index, origin-x, origin-y, (code, attribute, layout-adjust)*count`, 28 decoded assemblies with `count` of 1, 3 or 4 and `budget` from 30 to 65. |
| Similarity | Both express a pose as an ordered list of parts anchored at a signed origin. |
| Important difference | The AvP assembly's `budget` field has no proven meaning. Computed independently here, **`budget` equals the summed 16x16 tile count for 27 of 28 assemblies**; `0x13E36E` declares 59 against an inferred 57. |
| Required AvP validation probe | Resolve the two-tile residual at `0x13E36E`, then confirm the tile-span reading against the existing 28/28 zero-differing-pixel pose gate rather than against the budget field alone. |
| Intended AvP decision | Whether `budget` can be trusted as a per-pose VDP1 command and tile-count predictor, which is what makes a command budget computable before the renderer is written. |

### 3. Actor-state transitions

| Field | Content |
|---|---|
| Reference-engine concept | `ActorState`, `StateTransition`, `ActorStateMachine` |
| Reference-title evidence | Four externally-observed anchors (idle, normal-active, impact, recovery) reproduced across two cold replays. Internal state fields are `UNRESOLVED`. |
| AvP committed clue | `capability_model.h` defines `CapAction` (idle, walk, dash, jump, attack, shoot, special, hit, KO) and `CapActor` with `action`, `action_frame`, `hit_latched`, `health`. |
| Similarity | Both separate a named state from the animation it plays and from the frame counter inside it. |
| Important difference | `CapActor` is a **hand-authored gameplay implementation carrying capture-derived constants** (`CAP_PLAYER_MAX_HEALTH 101`, `CAP_ENEMY_CONTACT_DAMAGE 8`, the Chrysalis 21/55/97 contact schedule). The engine's state machine carries no constant and binds no timing. It is not a replacement for `CapActor` and must not be treated as one. |
| Required AvP validation probe | Translate one real actor's state routine from the located writer PCs and show its transitions match `CapActor`'s observed trajectory, or show where they differ, on AvP evidence. |
| Intended AvP decision | Whether AvP's state trajectory can be validated independently of rendering, advancing Gate 1 conditions 3 and 5. |

### 4. Collision and hitbox records

| Field | Content |
|---|---|
| Reference-engine concept | `CollisionEvent` with **no extents** and an opaque damage token |
| Reference-title evidence | `UNRESOLVED`. Sound RAM and both work RAMs change at the impact anchor, which localises activity and identifies nothing. |
| AvP committed clue | `data/round1_hitbox_geometry.json` holds four capture-exact overlay observations with `screen_box` and `screen_pivot_marker`, classified as capture-exact geometry with native collision replacement still missing. Pose records carry two proven interaction-table selectors. |
| Similarity | Both treat contact as an event distinct from the animation that produced it. |
| Important difference | AvP has real box geometry from the game's own debug overlays; the engine has none and refuses to invent any. AvP is **ahead** here, and the reference title contributes no collision evidence at all. |
| Required AvP validation probe | Decode actor-local box records for every required pose, then run a controlled hit fixture **and an out-of-range whiff control**. Without the whiff control, a field that moves on contact is not shown to be a damage field. |
| Intended AvP decision | Whether the interaction-table selectors at tail +8/+9 index the box records, which would connect the animation script directly to collision and close Gate 1 condition 2. |

### 5. Object-list output

| Field | Content |
|---|---|
| Reference-engine concept | `NeutralPart` -> `emit_pose_commands` -> VDP1 command list |
| Reference-title evidence | `MEASURED`: flat jump-next list, 296-334 reachable slots, one 16x16 sprite per command, `CMDPMOD` 0x0880, flip in `CMDCTRL`, 12-14 colour banks, 772 stored non-zero slots of which most are residue. |
| AvP committed clue | The CPS2 chain is statically established: `0xA99DC` list builder with `A1=0x708000`, per-group emitters, `0xA9B48` common actor loop, `0xA9B80` actor-type jump table. `docs/PARITY_PLAN.md` already states the representation boundary: normalise each entry into semantic fields and let native code emit the VDP1 equivalent rather than copying the CPS2 four-word descriptor, 10-bit packing or bank flip. |
| Similarity | The engine implements exactly the normalisation that parity plan paragraph prescribes. This is the strongest alignment in the table, and it was arrived at from the opposite direction. |
| Important difference | AvP's current renderer emits **precomposed 192x192 and 288x192 palette-layer cels** (`docs/ARCHITECTURE.md`), one 27,648-byte VDP1 slot per actor. The reference port does the opposite: many small per-tile commands. These are genuinely different strategies with the same texture cost and very different command counts. |
| Required AvP validation probe | Capture AvP's own VDP1 command list at idle, attack-active, impact and recovery for one street wave and for Chrysalis, under both strategies, on the same route. Compare reachable command count, texture working set and colour-bank count. |
| Intended AvP decision | Whether to move AvP from precomposed cels to a per-tile command pipeline, which is Gate 1 milestone 6's tile-pipeline decision. **This is the row the reference engine exists to inform.** |

### 6. Stage and spawn records

| Field | Content |
|---|---|
| Reference-engine concept | `PhaseResidency` (`loads`, `retains`, `retires`) |
| Reference-title evidence | Weak. Cartridge DRAM and VDP2 VRAM are byte-identical through the combat window, which shows stable residency and says nothing about when loading happens. |
| AvP committed clue | `data/stage1_route.json` holds 15 required runtime phases and authored `native_timing` values; `docs/PARITY_PLAN.md` records Round 1 stage tables as not yet located. |
| Similarity | Both model a phase as something with a lifetime rather than as permanent residency. |
| Important difference | AvP's phases are **capture-derived authored constants**; the engine's phase record is an empty structure with no source. Neither side has extracted stage tables. |
| Required AvP validation probe | Capture loading transitions, not combat, and record cartridge writes, VDP2 changes, CD reads and DMA transfers across street, interior, boss room and the Round 2 boundary. |
| Intended AvP decision | Whether phase overlays can be reduced or removed, feeding Gate 1 conditions 4, 6 and 7. |

### 7. Sprite colour ownership

| Field | Content |
|---|---|
| Reference-engine concept | `PaletteIdentity` -> `Vdp1Calibration.color_bank_for` -> `vdp2_color_ram` region |
| Reference-title evidence | `MEASURED`: every VDP1 sprite colour bank at every anchor resolves into a populated VDP2 colour-RAM bank; 12-14 banks live per anchor, 16 entries apart; colour RAM changes during combat while VDP2 VRAM does not. |
| AvP committed clue | `docs/ARCHITECTURE.md` maps CPS2 pens 0-14 to Saturn indices 1-15 with index 0 transparent, and allocates four alien variants, three player-layer palettes and the boss palette into eight 16-colour banks inside one 256-colour CRAM allocation. |
| Similarity | Both spend colour in 16-colour banks and both keep palette identity separate from texture storage. |
| Important difference | AvP currently budgets **eight** banks in a 256-colour allocation. The reference port has **all 128 colour-RAM banks populated** and 12-14 live per frame for a two-character fighting scene. A per-tile pipeline with many source subpalettes pushes colour-RAM use up, not texture use. |
| Required AvP validation probe | Count distinct live colour banks per frame for one street wave plus Chrysalis, and confirm AvP's eight-bank allocation still holds once poses are emitted per tile rather than as precomposed per-palette cels. |
| Intended AvP decision | Whether the per-tile strategy in row 5 is affordable in **colour RAM**, which is the constraint it actually pressures. This row exists because row 5 cannot be decided without it. |

### 8. Audio event routing

| Field | Content |
|---|---|
| Reference-engine concept | `AudioEvent` -> `AudioRouter` -> `SCSP_MIXED_STREAM` / `CDDA` / `UNRESOLVED` |
| Reference-title evidence | `MEASURED`: only three of thirty-two SCSP slots hold register content and their registers are byte-identical across idle, normal-active, impact and recovery, while sound RAM changes ~16 KiB across five pages per transition and exactly one SCSP register byte moves. `INFERRED`: audio is a mixed stream, not one keyed slot per event. |
| AvP committed clue | `docs/ARCHITECTURE.md` routes the QSound reference mix to a Saturn CDDA track and integrates selected Round 1 PCM events; `docs/PARITY_PLAN.md` keeps complete audio ownership open. |
| Similarity | Both separate streamed music from event sounds. |
| Important difference | AvP's plan implies event PCM playback; the reference port's event audio does **not** appear as per-event slot key-on in this window. If AvP adopts a slot-per-event design it will differ from the reference port, which may be fine, but it should be a chosen difference. |
| Required AvP validation probe | Capture AvP's SCSP slot registers and sound RAM at the same four anchors and record whether a slot is keyed per event or a buffer is refilled. Add a whiff control so a refill is not attributed to a hit that did not land. |
| Intended AvP decision | Whether AvP's Round 1 event audio should be SCSP slot playback or a mixed stream, feeding the Gate 1 audio-path and final audible-route conditions. |

## What the reference engine does not offer AvP

- No timing value, health value, damage value, hitbox extent or contact schedule.
- No cartridge, work-RAM, VDP1, VDP2 or SCSP byte budget.
- No claim that the reference port's per-tile strategy is correct for AvP; only
  the measurement that it is what one shipped Capcom Saturn port did.
- No VDP2 layer assignment, priority, plane map or scroll value: the reference
  title's VDP2 register block is not readable through this instrument.
- No attribution of any sound-RAM refill region to a specific cue.
- No replacement for `capability_model.*`, which remains AvP's own gameplay
  implementation.

## Decision standard

Applied to the one row that is ready to move:

> **This will decide whether AvP should** emit one VDP1 command per 16x16 tile in
> colour-bank mode with source assembly order as list order, instead of
> precomposing poses into large per-palette cels.
>
> **Before AvP adopts it, the AvP lane must verify** its own per-frame reachable
> VDP1 command count, texture working set and colour-bank count for a real AvP
> actor at idle, attack-active, impact and recovery, measured on AvP evidence
> alone, under both strategies on the same deterministic route.

Rows 1, 2, 3, 4, 6, 7 and 8 cannot yet complete both sentences with AvP evidence
and are retained as research context, not inserted into the AvP action plan. Row
7 is the nearest to ready: it is the measurement that decides whether row 5's
strategy is affordable at all, so it should be run in the same AvP probe.
