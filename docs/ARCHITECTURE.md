# Port V2 production architecture

This document codifies the future title-to-credits production boundary. It
does not implement that boundary or change the accepted runtime. The complete
source-identity, alternatives, evidence, and stop conditions remain in
`docs/research/CPS2_TO_SATURN_RESET.md`; the ADRs under `docs/adr/` record the
forward decisions introduced by `ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN`.

## Development and evidence boundary

The interactive salvage-and-promotion loop established the accepted adapters;
do not repeat it for every R7C actor/program. Current implementation closes
complete source programs and playable scenes under `docs/PARITY_PLAN.md`.
Reuse the existing boundaries and preserve their locks. Lab/prototype results
do not advance production parity or physical capability gates. Host, MAME,
Saturn emulator, human-review and physical Saturn evidence remain distinct.

The normal interactive scheduler must consume current state/input and recovered
source guards, not source-frame cadence or packed observation-phase tables.
Those tables belong to the differential adapter. The 2026-09-07 live-callback
audit found this boundary violated; current state/card record it as blocked.
No architecture declaration or hardcoded zero is implementation proof.

## Target shape

```text
MAME oracle adapter       Host-test adapters       Saturn input adapter
          \                     |                         /
           +---------------- purposeful ports -----------+
                                  |
                    deterministic Port V2 game kernel
                                  |
                fixed-capacity semantic frame output
                                  |
       +--------------------------+-------------------------+
       |                          |                         |
Saturn VDP1/VDP2         Saturn SCSP/CDDA          Saturn disc/cart
adapter                   adapter                   adapter

Temporary migration edge:
legacy main.c systems -> bounded legacy adapters -> Port V2 ports
```

Ports are named by purpose rather than technology. Host recorders, scripted
MAME fixtures, Saturn devices, and temporary legacy implementations may satisfy
the same port without entering the game-domain core.

## Deterministic production kernel

The intended fixed-tick entry point is conceptual, not implemented by this
plan:

```c
void avsp_game_step(
    AvspGameState *game_state,
    const AvspInputFrame input_frames[AVSP_MAX_PLAYERS],
    AvspFrameOutput *frame_output
);
```

`AvspFrameOutput` owns fixed-capacity arrays of semantic render, audio, load
and release, route-transition, and telemetry events. Gameplay performs no
dynamic allocation during an active phase. Every result is deterministic from
game state, sampled input, deterministic RNG state, and measured or explicitly
adapted content.

The kernel owns:

- session and hierarchical route state;
- players, enemies, bosses, projectiles, pickups, and destructibles;
- collision, damage, action selection, and animation selection;
- encounters, stage progression, and camera state;
- score, credits, continues, game over, endings, and credits.

The kernel must not call or include Jo Engine, SGL, VDP1/VDP2, SCSP/CDDA,
filesystem, emulator, wall-clock, or legacy-authored gameplay APIs. It does not
emit presentation-specific sprite identifiers.

## Purposeful ports and adapters

The stable ports are `InputPort`, `RenderPort`, `AudioPort`, `AssetPort`,
`TelemetryPort`, and `PersistenceCreditPort`. Adapters include:

- scripted input and MAME differential fixtures;
- host input, render, audio, asset, and telemetry recorders;
- Saturn pads and multitap input;
- Saturn VDP1/VDP2 presentation;
- Saturn SCSP/CDDA audio;
- Saturn disc, work-RAM, cart-RAM, VRAM, and CRAM residency;
- temporary legacy player, enemy, stage, HUD, PCM, and frontend adapters.

Render adapters consume actor position, lane, facing, action, animation record,
pose, palette, priority, camera, stage-layer state, and semantic HUD state.
They never decide attacks, damage, wave completion, boss death, route
transition, or ending selection. Audio adapters submit semantic sound/music
events and never determine route progression.

## First live gameplay boundary

The first production gameplay milestone is intentionally title-specific and
bounded to Predator Warrior, one class `0x1F` street alien, and one measured
Round 1 encounter. Its domain core contains three separate authorities:

- a Predator Warrior action controller consuming sampled controller state and
  owning movement, lanes, facing, action selection, startup/active/recovery,
  action movement, health, HIT, KO, and return to control;
- a class-`0x1F` AI controller owning one-player target selection, approach,
  lane adjustment, facing, attack selection/execution, cooldown, contact,
  damage, HIT, KO, and source-required RNG consumption order;
- a Round 1 encounter controller owning entry, spawn, bounds/camera lock,
  encounter-active and clear guards, unlock, and continued stage progression.

These machines consume current state. Fixed-frame contact injection,
event-count attack selection, damage without current overlap, teleported
contact, and presentation snapshots overriding gameplay positions are
prohibited. Deterministic input ledgers drive machine tests; real controller
input drives human playability review. Presentation and `AvspSceneDef` may
display events but may not choose attacks, AI decisions, damage, encounter
clear, or route progression.

## Hierarchical route model

```text
GameSession
+- Boot
+- Frontend
|  +- LegalAndLogos
|  +- Attract
|  +- Title
|  +- CreditWait
|  +- CharacterSelect
|  `- CharacterConfirm
+- Loading
+- Gameplay
|  +- StageIntro
|  +- Stage
|  |  +- Segment
|  |  +- Traversal
|  |  +- Encounter
|  |  +- Transition
|  |  +- BossIntro
|  |  +- BossBattle
|  |  `- StageClear
|  `- Results
+- Continue
+- GameOver
+- Ending
`- Credits
```

Each transition declares current state/substate, event or guard, next state,
source-evidence anchor, and load/release, audio, and scene effects. Separate
bounded machines coordinate route progression, disc/load ownership, audio
ownership, and credits/continue handling. Scattered magic timers in `main.c`
must not determine production route progression.

## Common player runtime and four character definitions

One common player runtime is configured by `PortV2CharacterDef`. A character
definition binds character ID, assets, actions, animation and collision sets,
HUD, weapons/projectiles, audio, bounded character-specific rules, and ending
route. Four duplicated player engines are prohibited.

The promoted player interface is an accepted early subset. A later card must
expand it—without changing it during ARCH-01—to carry `character_id`, all
gameplay buttons, attacks, weapons/projectiles, health and character resources,
HIT/KO, character-specific behavior, and ending selection. Unmeasured
differences remain `UNKNOWN` in `data/four_character_action_matrix.yaml`.

## Presentation scenes and title-specific content

`AvspSceneDef` remains presentation-only for logos, attract, title, character
select, round titles, story panels, continue, game over, endings, credits, and
noninteractive transitions. It does not encode enemy AI, collision, damage,
boss logic, player actions, or wave completion. Add a versioned line-scroll
operation only for source scenes where capture proves the requirement.

Forward content definitions are title-specific:

- `PortV2CharacterDef`, `PortV2EnemyDef`, and `PortV2BossDef`;
- `PortV2StageDef`, `PortV2SegmentDef`, and `PortV2EncounterDef`;
- `PortV2EndingDef` and `PortV2PhaseManifest`.

No general CPS-2 engine, generalized Capcom framework, whole-program
recompiler, speculative scene language, or general ECS is permitted.

## Phase-scoped residency

Every gameplay phase must obtain an explicit manifest before release. It
declares loaded and released assets, cart allocation, work-RAM allocation,
VDP1 allocation, VDP2 character and pattern-name allocation, CRAM banks, SCSP
allocation, CDDA track, legal data-read windows, expected high-water, and
canary locations. Load ownership and audio ownership must reject illegal data
reads while CDDA owns the drive.

## Temporary legacy adapters

These are migration scaffolding, not permanent architecture:

| Adapter | Existing implementation wrapped | Production interface | Preserved locks | Remaining authored coupling | Exact deletion condition |
|---|---|---|---|---|---|
| `LegacyPlayerRenderAdapter` | promoted player package plus current Saturn bench wiring | `RenderPort` actor events | approved asset hashes, full-visible pivot, palette, idle/walk, input/movement | composition and profile wiring outside the future kernel | Saturn actor adapter reproduces every approved player lock under the production integration profile |
| `LegacyEnemyRenderAdapter` | promoted class `0x1F` enemy package and bench wiring | `RenderPort` actor events | class/palette, 5-object/32-tile composition, grounding, facing, 39-frame/19-pose walk | current semantic test driver rather than production enemy state | Saturn actor adapter reproduces the approved enemy contract from kernel events |
| `LegacyStageAdapter` | approved adapted two-plane stage/camera bench | `RenderPort` stage and camera events | framing, priorities, palette, plane/PNT canaries, reviewed camera/stage result | uncaptured source row-scroll and bench-owned camera state | production route/camera plus VDP2 adapter pass renewed regression review including measured scroll requirements |
| `LegacyHudAdapter` | approved P1/P2 HUD presentation bench | `RenderPort` HUD events | corrected P1 colors and active P2 presentation | P2 gameplay/join state is not yet production-owned | semantic HUD for all active players reproduces approved locks under integrated multiplayer state |
| `LegacyPcmAdapter` | approved short Predator melee cue path | `AudioPort` effects events | cue bytes and approved timing 147/150/200 | bench-triggered cue and no complete mixer ownership | SCSP adapter reproduces cue identity/timing from kernel audio events with residency/canary proof |
| `LegacyFrontendAdapter` | measured `AvspSceneDef` frontend and character-select fixtures | route/render/input ports | measured four identities, 2x2/no-wrap/3-frame/confirm semantics only | frontend route and load ownership remain outside the production kernel | cold boot through four-character confirm and Round 1 passes source differential, emulator, and explicit human review |

Every new temporary adapter must record the same six fields in the migration
ledger before use.

## Eventual `main.c`

The final `main.c` only initializes the Saturn platform, constructs adapters,
loads the initial phase, initializes game state, samples input, calls
`avsp_game_step`, and submits semantic output. Game rules must not remain there.

## Staged mechanical enforcement

The following rules activate only when their named future production paths are
created; ARCH-01 does not fail accepted legacy code for not yet having the new
layout:

1. `src/port_v2/core/**` may not include Jo or SGL headers.
2. New game-domain code may not load assets directly.
3. Render adapters may not choose gameplay outcomes.
4. Audio adapters may not determine route progression.
5. Game steps must be deterministic from state, input, and content data.
6. Each release gameplay phase must have a residency manifest.
7. Active gameplay phases may not dynamically allocate.
8. Each temporary adapter must declare a deletion condition.
9. Behavioral claims remain `MEASURED`, `ADAPTED`, or `UNKNOWN`.
10. Character differences are tracked in the four-character matrix.
11. Every title-to-credits body appears in the coverage ledger.
12. Host, MAME, emulator, salvage, or user evidence may not be relabeled as
    physical Saturn proof.

Activation conditions and current enforcement state are validated by the Fast
workflow lane.

## Repository continuity heads

`foundation_head` pins the accepted reverse-engineering/architecture
foundation. `production_head` pins the latest accepted integrated Port V2
continuity result. `candidate_head` pins the active implementation candidate.
`evidence_candidate_head` pins the preserved V2-2B evidence candidate. Future
production cards base from `production_head`; the already-active INTEGRATE-01
card retains its historical base metadata unchanged.

## Concept references

- [Hexagonal Architecture / Ports and Adapters](https://alistair.cockburn.us/hexagonal-architecture)
- [Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html)
- [Presentation Domain Separation](https://martinfowler.com/bliki/PresentationDomainSeparation.html)
- [Architecture Decision Record](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html)

These references define architectural vocabulary only. Repository evidence is
authoritative for AvP behavior and Saturn constraints.
