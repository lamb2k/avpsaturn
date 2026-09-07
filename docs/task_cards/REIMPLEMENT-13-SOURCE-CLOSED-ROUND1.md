# REIMPLEMENT-13-SOURCE-CLOSED-ROUND1 task card

TASK: REIMPLEMENT-13-SOURCE-CLOSED-ROUND1
KIND: INTEGRATE
STATUS: READY
CHECKPOINT: reimplement-source-closed-round1
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SPEC-02-ROUND1-EXECUTABLE-CONTRACT]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: [Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [QA-13-ROUND1-END-TO-END-DIFFERENTIAL]

## Current assignment (owner delivery correction, 2026-09-07)

R7C is incomplete. P2 reaches source frame 15193 and P3 is recorded complete.
Native Coffee Shop is RED; no native full-round or current Target acceptance.
Do not restart Oracle/SPEC, revert completed programs or create another card.
This concise card replaces its 4,241-line running history; all old text is
preserved in Git at checkpoint `2e446d4303fa50bac14ec3c00222635066a7712c`.

Scheduler audit: BLOCKED_MISSING_EXECUTABLE_TICK_CONTRACT; accepted pool order
does not bind loop00808a, tail008140, trap3/001060 or interrupt-owned guards.
Run analyzer --interactive-readiness for exact fields; four identity controls PASS.
Continue type36/class0e (16 lifetimes, 0x09d440..0x09d60e) through existing SPEC.
Source09d464's +0x5c alias bound: paired a3/b3,16 raw-changing suppressions;7 scene ledgers identical, no omission waiver;12 Oracle +5 SPEC controls.
Next bind allocation, attachment/data-space tables, selector and release.
Return to scheduler with bounded source evidence; scene and candidate stay RED/frozen.

## Objective

Translate accepted executable SPEC and generated fixtures into native portable C:
real Predator Warrior input from Round 1 entry through boss defeat, clear and
stable Round 2 handoff. Not a MAME video, captured-route replay or another demo.

## Owning defect and exact next experiment

Audit base: `2e446d4303fa50bac14ec3c00222635066a7712c`.

- `main.c:live_encounter_frame_callback` calculates source_frame from runtime.frame,
  calls seven `coffee_shop_*source_updates` / exit-player cadence helpers outside
  AVSP_LIVE_ENCOUNTER_AUTOTEST, and selects gameplay dispatch from those counts.
  Only source input versus real input is conditionally compiled.
- `round1.c:avsp_round1_step_coffee_exit_source_phase_program` uses packed captured
  phase events; `step_scheduler_post_player_mask` also derives prefix phase from
  source-frame ranges. Fix the transitive path, not just one call in main.
- SPEC's `scheduler.coffee_shop_source_update_cadence` binds captured controller
  invocations. This is legitimate differential observation evidence, not an
  independent rule for normal interactive scheduling.
- `tools/capture_reimplement13_coffee_shop_scene.py` sets
  `retained_gameplay_authorities: 0` literally. Do not treat it as a measured
  absence of either retained shell or captured-schedule authority.

Use accepted scheduler 0x00849e..0x0084ce and pool guards/order, plus source
entry/exit/hitstop ownership, to bind the production invocation rule in existing
SPEC. Identify any genuinely missing top-level tick/phase guard explicitly;
do not replace the tables with a guessed one-update-per-video-frame loop.

Keep capture projection in the host/autotest adapter. The normal call graph
must consume state, current input and source program/content only. Add an
attributable boundary control that rejects production access to capture cadence
and packed phase-event arrays, including transitive scheduler helpers.
Diagnostic labels may change observation, never simulation.

Required causal checks: same initialized state/input with shifted diagnostic
frame labels; idle/late-input and rapid reversal routes; late encounter clear;
hitstop/interruption; allocation/order/RNG; source-supported changed input changes
outcomes. A trace-exact fixed route alone cannot pass. Keep narrow raw/normalized
witnesses; do not rebaseline source traces to the new implementation.

First bounded pass is at most 90 minutes: either source-bound separation and
focused proof, or exact missing field/owner/unblock condition. No invented pass.
If blocked, preserve work and continue the next safe program; do not reopen a
three-attempt capture gate under a renamed attempt.

## Current scene evidence, not percentages

`data/reimplement13_coffee_shop_scene_parity.json` covers 1972..5566:
747 source lifetimes / 95,149 source rows; 692 native lifetimes / 88,402 rows.
The report computes matching occurrences and classifications, not bug counts.

| Raw category | Current gaps | Compared population |
| --- | ---: | --- |
| Source actor population missing on Saturn | 144 | 747 source lifetimes |
| Unowned Saturn actors | 1 | 692 native lifetimes |
| Unidentified source class/type pairs | 0 | 38 source pairs |
| Unmapped source spawn/despawn edges | 633 | 1,494 source lifetime endpoints |
| Unsupported active states | 1 | 692 native lifetime records tested |
| Unowned collision/damage events | 93 | 149 source health-write events |
| Unowned route/camera events | 0 | 4 route + 7 camera records |
| Unowned audio/load events | 279 | 279 audio + 2 load records |
| Retained gameplay authorities | 0 reported | hardcoded; not an authority audit |

These categories overlap; do not sum them or infer completion percentage.
Some component classifications are stale versus later program-level evidence.
Reconcile from actual implementations and source owners, not appearance or labels.

Closed program comparisons include type20/class0f 2,878 rows raw/normalized0;
type24/class0a 3,479 rows raw/normalized0; type28/class00 3,476 rows raw/normalized0;
type36/class04 197 normalized rows0 with156 raw differences; type36/class03
1,700 normalized rows0 with1,360 raw differences and38 fixed-pool projections.
Class09 frame5493 normalization remains narrow. Preserve all raw differences.
These are host/program results, not full-scene, current Target or physical passes.

Source/native scene gate stays RED until every required body/event is accounted
for, all gameplay differences explained by source programs, raw normalization
scope mutation-tested, no unowned actor/event or retained/capture authority,
and complete real visual/audio evidence passes. Do not put new rows on ignore lists.

## Remaining program work and prioritization

Use the existing report/fixtures as inventory, not a new ledger. Prioritize:
production scheduler/exit ownership; player HIT/interruption and airborne
record4/class03 full lifecycle; type12/class06 and type16/class06 interactions;
scene controllers/props (type20/classes05,07,08 and type32/class02);
remaining pickups/interaction and unowned type24/class20 effects; native command
ownership for audio/load; then complete pending presentation populations.

For each body identify present implementation versus missing branch/event binding,
current gap fan-out and later scene reuse before coding. The report's labels alone
are insufficient to call an existing program unimplemented. Type28/class0c remains
BLOCKED_MISSING_SPEC_FIELDS with an exhausted non-causal witness; evidence:
`data/reimplement13_class0c_oracle_followup.json`. No retry without owner ruling.
Class0e/type36 is the already-declared independent whole program, not a new task.

After Coffee Shop passes, reuse the existing title-specific pool/scheduler,
animation, combat, projectile/effect, navigation/camera and route boundaries.
Keep scene-specific tables generated. Do not start another engine or restructure
round1.c speculatively. Complete later class12 families00/01/06, required effects,
route/result/failure/boss/audio/load programs from accepted P2/P3 in scene order.

## Owned paths

Existing Round 1 C and generated content; applicable SPEC/Oracle evidence and
generators; focused host/wiring/scene tests; main's bounded authority adapter;
existing state, roadmap, this card and handoff. Do not touch unrelated systems.

## Existing systems to reuse

Accepted VDP1/VDP2, palette/grounding, input, collision/HIT/KO, navigation/camera,
HUD, PCM/CDDA, loading, fixed-pool/residency, readback and visual-QA adapters.
Preserve Predator identity/neutral/melee/staff/Button1/3, class1f tracking,
P1-only native HUD, zero pre-handoff retained gameplay/contact PCM and one Track2.

## Systems deliberately disabled

Raw trace/disassembly implementation, frontend, other playable characters,
multiplayer, Round2 gameplay, physical work, generic lifter, emulator/recompiler,
trace-owned gameplay and authored fallback are disabled.

## Focused machine checks

Use TEST_PLAN: strict C90 compile/link before behavior, focused differential,
deterministic repeat and attributable mutations each iteration. Preserve survivor,
invalid, timeout and environment classifications. No compile failure is a kill.
Historical causal evidence records356 behavioral rejections and2 equivalent
survivors; not rerun or re-credited by a docs checkpoint.

Whole-program checkpoint: complete host scene plus relevant regressions/Oracle,
Target and focused rendering at their authorized risk boundaries. Scheduler,
memory, audio or rendering changes require paired cold Emulator and continuous
visual evidence; do not wait for scene green to test platform-visible changes.
Blocked lanes remain incomplete, not silently waived. No per-frame full ceremony.

## Saturn build profile

Normal interactive Round 1 with real input, plus separate deterministic AUTOTEST
adapter for comparison. Do not describe an AUTOTEST image as interactive proof.
Pinned private assets must have declared provenance/hashes; no arbitrary media copy.
No current Target artifact exists for latest runtime/fixtures; do not reuse old hashes.

Memory: runtime99,616/102,400 (2,784 free); tile612,720/614,400;
scratch11,648/12,288; SPEC50,504/262,144 (census floor243,848).
182 SPEC tables SHA6427526c2951abeda35655545edf17152f2ba7cbf6dd8b8e47521c1ad9dee3ba.
Existing map/asserts remain binding. No resize, squeeze or mid-combat read.
Last historical class0a GAME.BIN380,176, BSS0x060b3e20, SHA
8ffb54a957b2c6d2e08798bc5bf787fd40ffd5acfa035e9cb2b7d37bbc15a1c8 is NOT current.

## Emulator readback

Target and transition Emulator/WGC budgets remain exhausted at three attempts.
Preparation only until explicit reopening: read-only asset/toolchain/package
preflight using `data/reimplement13_emulator_mcp_capture.json`.
Two distinct blockers: clean packaging lacks ignored SPR4/BACT.RLE; transition
runtime-readiness capture never reaches its requested observation boundary.
BACT.RLE has known private provenance; persistent presence is not clean-package proof.
Minimum ruling: one bounded current-Target validation and one transition-gate
attempt using verified provenance provisioning and a reachable state-based window.
Follow EMULATOR_MCP_CAPTURE pinned EXE, cold pre-roll/save/fresh interpreter legs,
load-relative alignment/exclusions, negative controls and configuration restore.
No launch here is authorized by documentation cleanup. Technical SoundCore0
captures cannot establish audible output; normal audio and WGC are required for USER.

## Human-review requirement

No per-body/per-scene subjective stop. QA-13 precedes USER-10, with actual complete
route, controls, paired/perturbed/failure routes, full-speed source/Saturn clips,
adaptations and physical status. Never infer acceptance. USER-09 CHANGES_REQUESTED;
frozen candidate d04a65a2253175c6e820140feefc35419e2cca07 remains unchanged.

## Exclusions

No gameplay guesses, snapshot playback, capture-frame scheduling, missing actors,
blanket normalization, new workflow, protected user-file writes or media commits.

## Hard stops

Unsafe ownership; destructive/physical action; missing legal authority;
material architecture choice; exhausted gate or required source field with no safe
independent body. Physical Saturn remains UNRUN; HW-01 READY_FOR_PHYSICAL.

## Next eligible cards

QA-13-ROUND1-END-TO-END-DIFFERENTIAL only after full native R7C implementation
and declared acceptance, then explicit USER-10. SALVAGE-08 stays inactive.
Checkpoint and push completed bodies with remote equality; ordinary transitions
do not require owner confirmation and are not stopping points.
