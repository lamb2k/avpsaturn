# Round 1 presentation execution plan

This file is the granular execution map for the active Round 1 presentation
work. It sits below the full-game direction in `docs/PARITY_PLAN.md` and above
the single immediate task in `docs/NEXT_AGENT_PROMPT.md`.

Document ownership:

- `docs/GOAL.md`: complete-game destination and acceptance conditions;
- `docs/PARITY_PLAN.md`: overall S1-S6 and full-game order;
- this file: Round 1 work packages, dependencies, agent ownership, and status;
- `docs/NEXT_AGENT_PROMPT.md`: only the first executable task;
- `docs/AGENT_HANDOFF.md`: volatile HEAD, hashes, failures, and resume state.

This is a private native-port plan. It does not authorize publication or
distribution. Capability Gate 1 remains **0/7** and the full-game conditions
remain **0/9**.

Current evidence baseline: branch `codex/avp-master-plan`, committed HEAD
`8fd75b31c1ed6708de5fbd32ccaa2b98042d9654`. RP0-RP3 are committed package
checkpoints. RP4 has committed evidence and bundle-generation steps through
this SHA, but its live Saturn renderer remains **IN PROGRESS** and unaccepted.

## Delivery checks

### Continuous-route integration check

This is an internal integration check, not an acceptance gate and not a claim
of parity or hardware readiness.

It passes when:

- a digital controller can traverse cold boot through the held Round 2 title;
- every required presentation scene appears in source order;
- all presentation runtime content is ROM-derived;
- no captured screenshot or RLE framebuffer is selected at runtime;
- title/select/scene input works, and Predator Warrior reaches gameplay;
- no crash, black screen, missing scene asset, major palette corruption, crop,
  black bar, unsafe allocation, or late data-track read occurs;
- every known scene-specific mismatch is present in the variance ledger.

Existing approximate combat may remain only where explicitly labelled
`ADAPTED`. Passing this check does not close any Capability Gate 1 condition
by itself.

### Round 1 presentation parity check

This passes only after every classified presentation variance is closed:

- natural scene duration and input windows match;
- palette animation, fades, masks, and transitions match;
- scroll, row scroll, layer insertion, and dynamic priorities match;
- presentation audio cues and CDDA ownership match;
- cadence-1 reconstruction has zero unexplained changed frames;
- complete emulator and physical-hardware presentation routes pass.

Gameplay S2-S5 conditions remain independently open until their own complete
checks pass.

## Shared-primitives check

Do not scale scene content past representative fixtures until every applicable
item below is green. A defect here invalidates all dependent batch checks.

| ID | Primitive | Current status | Required evidence |
|---|---|---|---|
| SP1 | Frontend palette ownership | **PASS** at `b681c04` | One-based 1..255 indices, canaries, live CRAM, zero adjacent-boundary writes |
| SP2 | Frontend VDP1 geometry/colour/order | **PASS** through RP0 | 25 schedules/44 objects exact; four negative controls fail |
| SP3 | Confirmation shutter | **PASS** at `e728c9b` | Complete source interval 1860-1970 explained by the band model (first mask 1886, closure 1908); live NBG1 rows match the band at held frames with a one-row-shift live control; 4 offline controls fail |
| SP4 | Round 1 title composition | **PASS** at `aa0d671` | Text is scroll1 tilemap (48 tiles, bank 0x26) with a 16-step measured fade; ROM-derived cels drawn as VDP1 objects over the native street; R1TITLE.RLE removed; held text/street/cleared holds exact |
| SP5 | Resolution transform | **PASS** at `671eca8` | Endpoint 384->352 rule shared by both planes and street VDP1 objects; 113 page-boundary frames exact offline; live MPABN0/1, PNCN0/1, PLSZ readback; aliased-page control detects |
| SP6 | Input/state propagation | **PASS for frontend** | Non-wrapping 2x2, three-frame response, A/B/C confirm, no cancel, selected ID persists |
| SP7 | Memory bounds and diagnostics | **PASS (interim review)** at `6ac45b3` | Four-profile __bend ledger under 0x060C0000, carve arithmetic, VDP1/VDP2/CRAM usage recorded and gated in test.ps1; route-wide VDP1 command and allocator/SCSP high-water instruments remain GAP entries inside the ledger |
| SP8 | Late-read enforcement | **PASS (interim review)** at `6ac45b3` | Guard on every avsp_fs_read_into; host test with negative controls; live EncounterTest COMPLETE with one declared windowed read and zero late reads; live CDDA playback still disabled (ADAPTED skeleton) |
| SP9 | Two-plane scrolling/priority | **PASS (interim review)** at `671eca8` | Offline reconstruction exact (0 px both planes, 12,118 objects, 8 controls); NBG0 ownership root-caused (SGL ASCII map at VDP2_VRAM_B0) and resolved; live PNCN/MPABN/PRIS/SPCTL readback; VDP1 command classes present |
| SP10 | Row-scroll requirement | **PASS (interim review)** at classification | Complete-route classification over the private capture: 6 scenes require line scroll (0x8012, 0x8013, 0x8015, 0x8016, 0x8019, 0x801a - all opening/character-select), no gameplay scene does, street group constant-zero route-wide; implementing line scroll for those six scenes is Batch A (RP8) scope |

SP1-SP4 must pass before Batch A expands. SP5-SP10 must pass before Batch B
expands beyond its representative street fixture.

## Work-package status

| ID | Work package | Status | Depends on | Primary output |
|---|---|---|---|---|
| RP0 | Finish frontend shared primitives | **PASSED** at `e728c9b` | none | SP1-SP4 passed; see docs/AGENT_HANDOFF.md |
| RP1 | Preserve baseline and commit shared contracts | **PASSED** at `dddd19a` | RP0 | AvspSceneDef v0, scene-ID policy, player/route/diagnostic interfaces, 11 negative controls, SH-2 link |
| RP2 | Full-route cadence-1 capture and automatic grouping | **PASSED** at `82bb47e` | preserved baseline | Raw private capture plus tracked machine manifest |
| RP3 | Minimal scene runtime and route controller | **PASSED** at `a28f5df` | RP1 | `AvspSceneDef v0`, player, synthetic host fixtures |
| RP4 | Representative two-plane renderer | **PASS (interim review)** at `671eca8` | RP1, capture fixture | Offline reconstruction exact (0 px both planes, 12,118 objects, 8 controls); live registers/canaries/priority classes proven; fixture StreetTest-only with test.ps1 gate; Codex ratification pending |
| RP5 | Pessimistic G0/CDDA residency experiment | **PASS (interim review)** at `6ac45b3` | RP1 | Four-profile work-RAM ledger (release 2368 / street 220784 / encounter 320 / frontend 2016 bytes headroom), carve/VDP1/VDP2/CRAM/PCM ledger, disc-read guard host-tested and live-proven (one windowed read, zero late reads over EncounterTest COMPLETE); live CDDA playback itself still disabled (ADAPTED) |
| RP6 | Finalize semantic scene IDs | **PASS (interim review)** at `254719b` | RP1, RP2 | 122-scene manifest with content-addressed stable IDs, transition chain, 23 evidence-bound labels (99 flagged needs-label), test.ps1 gate with 4 controls |
| RP7 | Shared-primitives check | **PASS (interim review)** | RP0, RP3-RP6 | SP1-SP10 green on interim review (SP7/SP8 carry explicit GAP ledger entries for route-wide high-water instruments; SP10 defers line-scroll implementation for six frontend scenes to RP8) |
| RP8 | Batch A: frontend and Round 1 title | **PENDING** | RP7 frontend subset | Controller-driven legal/opening/story/title/select/R1 title |
| RP9 | Batch B: street and interior presentation | **PENDING** | RP7 | Barricade through interior transition |
| RP10 | Batch C: boss ending and Round 2 title | **PENDING** | RP7 | Boss presentation through held Round 2 title |
| RP11 | Continuous-route integration check | **PENDING** | RP8-RP10 | Clean normal route plus bounded variance ledger |
| RP12 | Round 1 presentation parity closure | **PENDING** | RP11 | Zero unexplained presentation variances |

After RP12, return to the S5/S3/S4/S6 order in `docs/PARITY_PLAN.md`.

## RP0: finish the current frontend proof

Status: **PASSED** at `aa0d671` (Round 1 title) and `e728c9b` (shutter),
under the user's autonomous interim-supervisor authorization recorded in
`docs/AGENT_HANDOFF.md`. Bounded substitution on record: the source
implements the shutter as 360 sliding mask objects; the Saturn NBG1 row
blackout reproduces the same pixels and is proven against every source
frame of the complete interval (ADAPTED). Ambient street-actor animation
behind the Round 1 title remains RP4/RP9 scope.

Completed:

- one-based Jo palette contract and bounded-copy canaries;
- 25-hold live CRAM/register chain with 22 exact surface comparisons;
- 25 VDP1 schedules and 44 objects exact;
- select animation clock and confirmation blink latency corrections.

RP0 has no remaining executable work. Complete story scenes and ambient street
animation are later content/renderer packages, not unfinished RP0 primitives.
The exact executable contract now targets RP4 in `docs/NEXT_AGENT_PROMPT.md`.

## RP1: shared contracts and ownership boundary

Commit a versioned interface baseline:

- `AvspSceneDef v0` envelope and schema version;
- scene-ID namespace width and provisional-ID policy;
- explicit unknown-scene behavior that fails diagnostically, never skips;
- generated bundle header and member-manifest interface;
- `AvspScenePlayer` load/activate/step/draw/release interface;
- `AvspRouteController` explicit state-machine interface;
- presentation diagnostic and variance interfaces.

Do not freeze the final semantic scene list here. RP2 evidence finalizes it in
RP6. Operations are additive within the v0 envelope; incompatible changes
require a version increment and migration check.

Preserve the current dirty tree in coherent explicit-path commits before
creating additional worktrees. Never use a branch switch, reset, stash, or
binary patch as a substitute for understanding mixed ownership.

## RP2-RP5: independent workstreams

After RP1 is committed, these packages may run concurrently in separate clean
worktrees. Evidence-only RP2 probes may begin earlier once the current state is
preserved because they do not modify shared runtime files.

### RP2: capture and conversion

- Capture the complete no-skip route at cadence 1.
- Record source state, input, CPS-A/B registers, relevant work RAM, gfxram,
  object RAM, palette RAM, QSound state, and screenshots.
- Generate a raw machine manifest of hashes and write deltas.
- Group consecutive frames automatically by state, maps, palettes, objects,
  scroll/priority, input acceptance, and audio changes.
- Assign provisional scene IDs. Human review focuses on transitions,
  unexplained full-frame changes, object insertion/removal, priority/palette
  changes, input windows, audio, and nonconstant row-scroll intervals.
- Keep raw captures ignored; tracked output contains semantics, addresses,
  counts, ranges, and hashes only.

Zero unclassified intervals is required by RP12, not before the first batch can
integrate.

### RP3: minimal scene runtime

`AvspSceneDef v0` initially supports only evidence-backed operations:

- hold/duration and input mask;
- layer-page selection;
- scroll update;
- palette-range update or fade;
- object add/update/remove;
- sparse map-cell patch;
- audio event;
- scene transition.

Add line-scroll or complex priority operations only when RP2/RP4 evidence
requires them. Do not build a general scripting language, dynamic scene
allocator, universal asset cache, or deferred attract/continue/service routes.
The route controller remains an explicit state machine.

### RP4: representative stage renderer

Use one street interval containing independent scroll2/scroll3 motion, a moving
actor, a foreground insertion, a priority change, and source-enabled row
scroll.

Prove:

- scroll3 -> NBG1 and scroll2 -> NBG0;
- objects -> VDP1 and only source-proven foreground -> NBG2/bounded VDP1;
- common plane-level 384-to-352 transform with independent scroll;
- normalized source row table and VDP2 line-scroll use only if nonconstant;
- priority at deliberate overlaps;
- exact VRAM/CRAM/register state and bounded command cost;
- zoom, row, palette, and priority negative controls.

Current checkpoint at `8fd75b3`:

- selected source interval is frames 3474-3674 (201 frames);
- both complete planes use the endpoint-aligned 384-to-352 transform;
- scroll2/NBG0 is 527x240 with 1,596 cells and 197 colours;
- scroll3/NBG1 is 528x256 with 879 cells and 15 colours;
- `STRIPS.BIN` is 267,350 bytes with two map patches and a serialized 201-frame
  strip/object schedule;
- source scroll2 span is 176, scroll3 span is 154, proving unequal motion;
- visible normalized row offsets are constant zero for this interval only;
- captured source object priorities 1 and 4 are present.

The captured 12,118-entry object schedule is a focused RP4 validation fixture,
not a production gameplay data source. The live prototype must still:

1. give NBG0 exclusively to the presentation manager instead of Jo printf;
2. map both generated PNT pages explicitly and pass a boundary crossing;
3. encode/read back real per-object sprite priority relative to NBG0/NBG1;
4. keep the fixture absent from the normal production route;
5. validate all bundle bounds, use checked frame offsets or a monotonic cursor,
   upload immutable data only on activation/page changes, and remain within the
   measured 624-byte high-work-RAM margin unless memory is deliberately moved.

Latest dirty-prototype note: `build.ps1` now stages `STRIPS.BIN` only for
StreetTest, `main.c` builds an O(1) object-frame index, and a candidate sprite
priority encoding exists. These reduce implementation work but are not accepted
until production-member exclusion, complete bounds, SH-2 map, register readback,
and deliberate overlap controls pass. The candidate index/revert arrays exceed
the previous 624-byte margin unless relocated or proven safe in the focused
link.

### RP5: memory, CDDA, and residency

Create a deliberately pessimistic G0 package using measured or explicit
upper-bound sizes. Measure:

- high/low work RAM and `__bend`;
- both cartridge banks and fragmentation;
- VDP1 textures and commands;
- VDP2 banks/maps/line tables;
- CRAM and SCSP RAM;
- PCM ownership;
- data reads and CDDA lock.

Prove that late data reads are rejected while CDDA is active. An early physical
smoke test may establish boot, cartridge, controller, VDP mode, and CDDA
feasibility, but it is not Capability Gate 1 condition 7.

## RP6: semantic scene IDs

Use RP2's grouped full route to finalize the authoritative scene manifest.
Record source state/range, provisional ID, final stable ID, input dependency,
layer/object composition, audio events, and transition target.

Unknown IDs remain hard diagnostic errors. Do not silently coerce them to a
nearby scene or skip them.

## Vertical content batches

### RP8 / Batch A

- legal and QSound/Capcom/opening;
- all story panels;
- title wait and Start transition;
- character select and confirmation;
- Round 1 title.

This proves the scene player, timed transitions, input masks, palette handling,
and route controller.

### RP9 / Batch B

- barricade hold;
- withdraw dialogue;
- breach/explosion and GO prompt;
- street presentation;
- door exit and dialogue;
- interior loading transition.

This proves the stage renderer, independent scrolling, foreground ordering,
HUD interaction, and gameplay-to-scene transitions.

### RP10 / Batch C

- Chrysalis entrance and boss introduction;
- boss defeat progression and player victory;
- Stage Clear, results/tally, and exit;
- intermission and Round 2 title.

This proves score/state-driven presentation, late-stage residency, audio
sequencing, and the final route hold.

Each batch ends in a runnable controller-driven route. Existing RLE scenes stay
as ignored oracles and never as fallback runtime decisions.

## Variance ledger

RP2 establishes a tracked semantic ledger, recommended path
`data/round1_variances.json`. Each open variance records:

- stable scene ID and source frame interval;
- approved category: timing, priority, row scroll, palette animation, audio,
  geometry, input, or another explicitly reviewed category;
- expected source behavior and current native behavior;
- measured delta and supporting capture/hash;
- dependency on a shared primitive;
- owner, closing test, and current evidence label;
- whether it blocks the continuous-route check;
- whether it blocks the Round 1 presentation parity check.

A variance caused by a shared primitive cannot be accepted as scene-specific.
Fixing a shared primitive invalidates and reruns every dependent batch check.
The ledger is not a parking lot: each entry requires an owner and closing test.

## Agent ownership and integration

Only the integration owner edits shared runtime and build surfaces:

```text
main.c
capability_model.c/.h
build.ps1
makefile
shared scene IDs and common generated headers
docs/ROUND1_EXECUTION_PLAN.md status table
```

Suggested isolated ownership:

| Workstream | Primary files |
|---|---|
| Capture/conversion | new or existing `tools/mame_*`, analyzers, semantic manifests |
| Scene runtime | new `avsp_scene.*`, `avsp_route.*`, isolated host tests |
| Stage renderer | new `avsp_stage_renderer.*`, renderer fixtures and focused profile |
| Audio/residency | analyzers, ledgers, focused test support; integration hunks submitted separately |
| Integration/frontend | shared files, ISO layout, route enums, final runtime wiring |

Agents:

1. start from an exact committed SHA in a separate worktree;
2. claim one package and list owned files before editing;
3. do not modify another lane's shared interface without a dedicated interface
   commit;
4. commit coherent results and report exact checks/UNRUN items;
5. never merge or cherry-pick themselves into the integration branch unless
   explicitly assigned as integration owner.

Every package report starts with this machine-readable summary so the
integration owner can update status without interpreting prose:

```text
PACKAGE: RP<n>
BASE_SHA: <40 hex>
COMMIT_SHA: <40 hex or UNCOMMITTED>
OWNED_PATHS: <explicit paths>
STATUS: PASS | PARTIAL | BLOCKED
CHECKS: <command=result list>
UNRUN: <exact checks>
DEPENDENCY_CHANGES: <none or explicit proposal>
GAPS: <MEASURED/ADAPTED/GAP list>
```

The integration owner reviews explicit commit SHAs, runs shared tests, updates
this status table, and advances the first executable task.

## Verification lanes

### Per-commit fast lane

- deterministic generation and schema checks;
- asset bounds, palette count, and memory assertions;
- scene-state and route-controller host tests;
- targeted reconstruction and negative controls for changed content;
- `git diff --check`.

### Per-batch integration lane

- full `test.ps1`;
- clean focused Saturn build and member hashes;
- controller route from cold boot to the batch endpoint;
- no missing scene IDs or captured runtime payloads;
- live diagnostics and memory high-water report.

### Continuous-route lane

- clean normal-release route through the Round 2 title;
- every required scene visited;
- no screenshot/RLE fallback, major corruption, missing asset, or late read;
- variance ledger complete for every known difference;
- early hardware feasibility result clearly separated from acceptance.

### Round 1 presentation parity lane

- zero unclassified cadence-1 intervals;
- full negative-control suite;
- zero unexplained host/live presentation differences;
- exact scroll/priority/timing/audio;
- complete physical NTSC Saturn presentation route.

Shared runtime changes run full `test.ps1` even if their local fast lane is
green. Focused success never substitutes for the normal route.

## Status and handoff automation

Before RP7, add a deterministic status generator whose canonical structured
output contains HEAD, package states, manifest/member hashes, memory peaks,
scene coverage, checks, variances, and `ADAPTED`/`GAP` items. Recommended
tracked outputs:

- `data/round1_status.json`;
- generated `docs/ROUND1_STATUS.md`.

Until that generator exists, this file's status table is authoritative and is
updated only by the integration owner. Other agents report their commit SHA and
checks without editing the shared status table.

## Ordered critical path

1. Finish and supervisor-accept RP4: NBG0 ownership, explicit PNT paging,
   per-object priority, fixture isolation, bounds, resource readback, and
   regression lanes.
2. Run RP5 G0/CDDA residency and RP6 semantic-scene finalization in isolated
   ownership lanes after RP4 acceptance.
3. Pass RP7 shared-primitives check.
4. Integrate Batches A, B, and C.
5. Pass the continuous-route integration check and populate the variance
   ledger.
6. Close every presentation variance and pass the Round 1 presentation parity
   check.
7. Resume S5 Room 1 behavior, complete S3/S4 stage/gameplay work, then S6
   complete Capability Gate 1 validation.
8. Continue stage by stage through the complete game plan.
