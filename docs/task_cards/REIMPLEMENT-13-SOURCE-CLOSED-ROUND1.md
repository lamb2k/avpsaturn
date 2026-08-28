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

## Objective

Translate only SPEC-02 and its generated fixtures into portable native C so
Predator Warrior can play from direct Round 1 entry through boss defeat, stage
clear, and stable Round 2 handoff with no fixed-frame, counter, scene, snapshot,
or authored-fallback gameplay authority.

## Owned paths

- Bounded Round 1 native gameplay and source-derived content data named by
  SPEC-02; focused host/Target/Emulator tests; state and control ledgers

## Existing systems to reuse

- Accepted Port V2 rendering, VDP1/VDP2, camera adapters, HUD, PCM/CDDA,
  loading/residency, collision, HIT/KO, readback, and visual-QA infrastructure.

## Systems deliberately disabled

- Raw trace/disassembly implementation, runtime 68000 interpretation, frontend,
  other characters, multiplayer, later-stage gameplay, and physical status.

## Focused machine checks

- Preserve source actor-pool semantics, scheduler order, signedness,
  state/substate, arithmetic/branch order, RNG call order, and table indexing
  where supported. Build vertically through each segment, encounter, actor,
  event, boss, clear, and handoff; after each body run host differential, real
  mutations, Target, paired Emulator, rendered inspection, correction, commit,
  push, and remote-SHA verification.

## Saturn build profile

Direct diagnostic Round 1 boot plus normal interactive image, built only from
SPEC-02, generated fixtures, accepted interfaces, and approved assets.

## Emulator readback

Paired cold deterministic progression plus rendered inspection after every
added body; require zero fallback, canary failure, unsupported result, or
candidate/spec identity mismatch.

## Human-review requirement

No per-segment review. QA-13 must pass before USER-10.

## Exclusions

- No frontend/title/select, four-character work, multiplayer, full-game engine,
  raw source-note implementation, visual guesses, or physical claim.

## Hard stops

- SPEC-02 violation, required UNKNOWN, guessed behavior, objective discrepancy,
  target/emulator failure, nondeterminism, fallback, or approved-lock regression.

## Active vertical checkpoint

The SPEC-02-bound first entry is implemented in portable C: exact fixed pools,
the ten-row LIFO spawn table, the 26-byte command-derived semantic program,
`60, 60, 44` dwell loads, 164 source scheduler decrements, signed terminator,
selected gate clear, route state `2 -> 4`, and control enable. No raw 68000 is
interpreted at runtime. The accepted Port V2 Predator Warrior controller now
consumes current Saturn input after route state 4 and preserves source neutral
facing. Eleven host mutations and twelve target-wiring suppressions are
rejected; Target, paired Emulator, Fast, and Oracle pass with zero fallback
or failure. Direct inspection at post-unlock frame 190 and after real controller
movement shows coherent player/alien presentation, camera, both VDP2 planes,
HUD, palette, and priority. Paired 471-frame ledgers bind native frame 470 to
player x 1072, z 320, facing right, neutral source action, and 301 controller
updates. This is not the complete first encounter: the retained live-encounter
actor handoff is still technical substrate. The SPEC-02-bound fixed-pool
scheduler now visits active records in pool order 12/16/20/24 and ascending
source-slot order, rejects unsupported route-reachable class dispatches, and
produces 3010 deterministic visits through evidence frame 470. Each of those
ten initial class-0x1F records now binds its exact SPEC-02 animation record to
assembly, hurt selector, and attack selector: 190 source records, zero orphans,
3010 paired target bindings. Seventeen host mutations, fifteen target
suppressions, Target, paired Emulator, Fast, Oracle, and direct frame-191
inspection pass. This does not yet implement class-0x1F movement, damage,
state transitions, or dynamic spawn. The source dispatch entry `0x060532` and
all 59 route-reachable state/substate contexts are now exact-bound and reject
unsupported contexts; nineteen host mutations, sixteen target suppressions,
paired Emulator, Fast, Oracle, and direct frame-191 inspection pass. Execution
of the initial `0200:1000/1200/1400` transitions is blocked because SPEC-02 does
not provide their predicates, timer guards, writes, movement arithmetic, or RNG
order. Preserve that blocker and implement the dependency-safe first-segment
global bounds first. Commit `45a1aaf` binds the stable route-4 bounds directly
from SPEC-02: bound x/z `720/256`, world x `752..1072`, world z `272..400`,
and the source up/down z signs. They activate on the entry terminal guard,
compose after the accepted encounter resolver, and produce 301 paired
applications with one x-max clamp at frame 470. Twenty-one host mutations,
seventeen Target suppressions, paired Emulator, Fast, Oracle, and direct
frame-191 inspection pass. Coffee Shop minimum penetration, terrain-record
interpretation, and camera target updates are blocked because SPEC-02 omits
their required box geometry and branch/update arithmetic. Preserve both
blockers. Commit `888732d` implements the SPEC-02 walk-to-stop transition:
action `0x0202`, exact 10-tick `0x0204` motion/facing hold, `0x0200` cleanup,
and neutral return with the last directional facing preserved. A discovered
normal-profile duplicate CDDA start at native route state 4 is corrected by
preserving the already-active Track 2 owner. Twenty-three host mutations,
21 Target suppressions, normal and paired Emulator, Fast, Oracle, and direct
frames 180/182/472 inspection pass. The neutral Button3 jump is blocked because
SPEC-02 omits the exact numeric signed 16.16 vectors, input/facing selector
mapping, and branch order behind table `0x0243d2`. Commit `882b15b` implements
the dependency-safe Button2 melee body: exact source edge, selectors 1..4,
strike records/assemblies/collision selectors, 30-tick follow-up, held-edge
rejection, and HIT/KO interruption preservation. Thirty-two host mutations,
26 Target suppressions, paired Emulator, and direct selector-2/4 inspection
pass with continuous staff ownership and zero regression. Commits `f6cab22`
and `09c8a28` then implemented a Button1/class-0x05 body that was internally
consistent but later proven to be character 1 Major Schaefer evidence. It is
retained only as a negative control. The corrected source/SPEC/native body
requires character 0 Predator Warrior, records `0x15e540..0x15e580`, one
40-resource debit, one type-4/class-0 parent and five type-4/class-4 children.
Character plus normalized emitted-object identity are asserted per frame.
Fast, Oracle, 123 real host mutations, 131 Target suppressions, and two
byte-identical paired-emulator runs pass at ISO
`9db09d765122a56e9bdefac73e762cefcfb379d9be92933fd1d4281d6bbb9ffc`.
Exact Windows cadence-1 frames 177..196 preserve Predator through Button1 and
neutral. The renderer correction pins each referenced tile for the complete
frame, clips wholly offscreen entries before allocation, and gates the measured
first-segment residency at 21 composites plus 218 tile slots. Peak unique tile
use is 170; pin exhaustion, overflow and texture mismatches are zero; sprite
high-water is 242/255. STRIPS.BIN remains a hybrid source-derived stage package:
background/scroll presentation is retained, while the captured foreground
schedule remains excluded from playable gameplay authority.
The initial class-0x1F blocker is closed in the same source-bound body: all ten
source slots initialize in scheduler order with ten RNG calls; `0x1000` and
`0x1200` use the exact predecrement timer/animation guards; `0x1400` proceeds
through `0x1402/1404/1406/1408` with signed 16.16 motion, facing, landing,
collision-selector, class-0x4e effect-allocation, class-0x44 guard, class-0x09
RNG, exact command-identity, and return-to-`0x0200:0000` rules. Paired Target
readbacks record ten completions, two effect allocations/releases, two refused
allocations, one guard clear, two audio commands, 158 class-0x09 RNG calls, and
zero scheduler failure or fallback. Preserve the Coffee Shop and Button3
blockers. The startup-authority
correction binds source frames
2040/2072/2075/2238/2520 to title, P1 HUD/player initialization, player
visibility, control, and one Track-2 start. Retained gameplay is not initialized
or stepped before route state 4, active P2 HUD visibility is false, retained
contact cannot trigger gameplay PCM, and native state owns P1 HUD. Paired
startup traces have zero hidden contact/damage, orphan PCM, duplicate CDDA,
fallback, or failure; direct scanout review matches the source P1 top and
weapon-meter assets. Fast, Oracle, release Target, and paired Emulator pass.
The Coffee Shop obstacle, terrain, and camera blocker is now closed. Accepted
Oracle evidence plus the bounded corrective capture bind the type-20 attack box
and point-probe minimum-penetration arithmetic, seven required eight-byte
terrain records and exact kind-0/2/4/6 interpreter/retry behavior, camera
target/speed/phase guards, and world-to-plane ordering. The bounded 46 x 9
selector projection is losslessly packed into 104 source-derived bytes for the
Target. Host rejects 93 real mutations and Target wiring rejects 67
suppressions. A clean rebuild exposed stale Jo Engine configuration objects;
the bounded disc-stream burst was reduced from 31 to 24 sectors without
changing byte order or ownership. The clean debug Target ends at `0x060be7d0`
and release Target at `0x060bbe60`; two byte-identical pinned emulator runs
normalize to
`f40d51362371d59866ea4283704880b56272e446d91b1db7b8acbdaa7e02fbf2`
with dynamic camera/bound x 801, scroll2 737, zero fallback/failure, and P1-only
HUD. Direct live frames 31 and 205 preserve both Coffee Shop planes, visible
edges, actors, projectiles, palette, and priority. Current scanout disproves the
stale pre-checkpoint images that still showed an active P2 panel.

The bounded regression audit then froze `ac126c0`, compared it with parent
`0a3fe67` under identical clean builds, and expanded backward only because both
showed the objective right-edge background corruption. The symptom is present
at requested oldest baseline `52714b` and first appears in `62f3fa5`, where the
retained live-encounter camera began overriding source-owned `s2x/s3x` before
native route-state-4 handoff. Commit `fe49adc` preserves captured source plane
positions before handoff and enables native camera-to-plane ownership only at
route state 4. Two real mutations reject an unconditional native camera and a
restored retained camera. Fast, Oracle, release/debug/bench Target, and two
byte-identical 467-sample Emulator passes succeed at normalized ISO
`69a6a39679840ba1a4e819cc829681abd301fc330ac6e71957d9e532f07ebecc`.
The normal interactive ISO is
`79ad385d3449c093d873c4e535a700b4b4f7836fd96a684623d2ff7f258644a5`.
Windows Graphics Capture directly verifies the corrected startup frame, a
60-frame full-speed action strip, and the navigation endpoint with coherent
planes, visible edges, actors, HUD, palette, and priority. Two exact navigation
runs have identical semantic endpoints: obstacle responses 7, terrain responses
6, terrain retries 5, camera locks/unlocks 1/1, phase 4, target/position 1008,
scroll2 944, and final terrain z 327. The auxiliary wall-clock driver varies
only final x and elapsed frame; authoritative counters/state and the paired
cadence-1 emulator ledger are deterministic. Button3 remained paused and was
not staged into this correction.

The preserved Button3 blocker is now closed. Accepted Oracle evidence amends
the existing SPEC fixture with table `0x0243d2`, all signed 16.16 vector pairs,
exact input/facing mapping, branch and interruption order, phases
`0x0400/0402/0404/040a/040c`, landing, presentation records/assemblies,
collision selectors, and zero RNG consumption. The native body produces one
entry, 35 motion updates, one landing, one completion, final selectors `3/10`,
and 38 source-rendered frames in each of two byte-identical 467-sample cold
runs. Host rejects 113 real mutations and Target rejects 78 suppressions.
Fast, Oracle, debug/release Target, and paired Emulator pass at normalized ISO
`48e76ef310f0832344290656912565dbfa292ddc0d1ea134fde5dcc23568a080`.
Direct Windows Graphics Capture found and corrected one objective integration
defect: the source-actor emit origin had canceled native jump height at screen
projection. The bounded bridge now applies height exactly once. Thirteen real
frames verify takeoff, apex, descent, landing and neutral return with unchanged
source assemblies, staff continuity, P1-only HUD, Coffee Shop planes, camera,
palette and priority.

The objective Button1 player-family regression is corrected. Direct inspection
had shown Major Schaefer because the earlier Oracle selection input changed
source actor `+0xd2` from character `0` to `1`; the analyzer had not asserted
that field. Two independent corrected source captures are byte-identical with
character `0`, Predator records `0x15e540..0x15e580`, one 40-resource debit,
one record-type-4 class-`0x00` parent, and five class-`0x04` children. Character
identity and normalized emitted-object identity are now mandatory per-frame
differentials, and the Major class-`0x05`/type-24-class-`0x3a` path is a
negative control. Native C, SPEC-02, and generated fixtures bind that corrected
body. A renderer defect exposed by the correction is also closed: live VDP1
tiles are pinned for their entire frame, wholly offscreen objects are clipped
before texture allocation, and the measured first-segment residency is 21
composites plus 218 tile slots. Paired runs are byte-identical at normalized
ISO `9db09d765122a56e9bdefac73e762cefcfb379d9be92933fd1d4281d6bbb9ffc`;
tile-union peak is 170, pin exhaustion/overflow/texture mismatches are zero,
and sprite high-water is 242/255. Exact real Windows frames 177..196 preserve
Predator identity through action and neutral. Fast, Oracle, Target, paired
Emulator, host mutations, target suppressions, and visual inspection pass.

The retained first-encounter class-`0x1f` gameplay boundary is now replaced.
Native Round 1 owns its AI, targeting, movement/lane, facing, state/substate
transitions, attack timing, current-state collision/damage, HIT/KO, effect
allocation, dynamic spawn, removal, fixed-pool release, encounter clear, and
route unlock. The retained shell is presentation-only and is never stepped as
gameplay authority. Two byte-identical 575-sample pinned-emulator runs at ISO
`ff8f0a288aa1e75dca47983ec3c3a799e32edad16a7b8106a5e9c73f2da27847`
record 469 native updates, three HITs, one KO, one lifecycle release, one clear,
continued play, and zero fallback/failure/decode error. Fast, Oracle, Target,
123 host mutations, and 131 target suppressions pass.

Direct window-targeted Graphics Capture at native frames 38/254/329/469/470
verifies coherent Predator and class-0x1F presentation through attack, HIT, KO,
and removal. MAME source frame 2078 confirms that the crowded alien and gray
prop population is the source intro composition rather than background or VDP1
corruption. The `WARRIOR` row is the P1 equipment meter; the separate
`Maj.Schaefer` P2 panel remains absent. The current-state class-0x1F assembly
union is now included in the Saturn emit/tile working set, with omission locked
by a real mutation control.

The source scene-population gate is now active before encounter-clear or the
next scene. Incremental commit `874ce2b3e0800554cc087d3b7fd40fb3d13de359`
preserves the complete source census; it is evidence, not promotion of the
runtime candidate. The focused class-`0x1f` type-`16`/class-`0x06` projectile
body is source-bound through SPEC-02 and native C and rejects 150 real host
mutations. It binds the exact fixed-pool allocation, three-row signed 16.16
motion table, current attack record `0x03589e`, player hurt record `0x11ae8e`,
17-point damage write, presentation records, lifetime and release rules.
Fast, Oracle and LiveEncounter Target BUILD_ONLY pass. The SH-2 runtime is
measured at `0x135e4` and guarded inside a policy-compliant `0x18000` cartridge
arena with 19.3% headroom; the residency ledger and readback base are bound to
that exact layout.

Whole-scene parity remains open: 399 source lifetimes are missing; 1,376 source
spawn/despawn edges, 40 active states,
94 collision/damage events, 3 route/camera events and 281 audio/load events
remain unmapped or unowned. Zero retained gameplay authorities and zero unowned
Saturn actors are preserved.

Incremental checkpoint `a6f434539b98369c10c0b4e65125d9683a95a7ec`
implements the accepted class-`0x1f` inner state `0x0208` program: actions
`0x00/04/06/08/0a/0e/10`, 54 source animation records, eight movement tables,
target-side/facing branches, source RNG order, movement, and type-`16` parent
emission. The focused host differential and 154 real mutations, Fast, Oracle,
and release Target pass. A stale SPEC fingerprint sentinel and omitted
class-`0x4e` variant-1 impact presentation residency were found by Emulator and
corrected from the accepted fixture; the rerun records zero decode, fallback,
failure, or canary errors.

The next bounded correction binds class-`0x1f` live collision selectors to the
source actor `+0xa5/+0xa6` fields instead of presentation-record selector bytes.
Its focused Oracle/SPEC checks, 156 real host mutations, Fast, Oracle, and release
Target pass; five additional source lifetimes now match naturally.

Paired Emulator acceptance remains blocked, not rebaselined. The old 575-sample
choreography begins after native recurring-encounter initialization, which now
occurs 182 scheduler ticks later and therefore sees a different prefix of the
source input ledger. The first remaining actor divergence is now exact: at source
frame 2288 native record-type-`4` child collision damages class-`0x1f` slot
`0x00ffa180`, while the source first writes that damage at frame 2306 from slot
`0x00ff8880` using attack record `0x030cd2`, then allocates the class-`0x4e`
variant-1 impact at frame 2307. The exact next body is the accepted record-type-`4`
before-type-`12` scheduler/current-state collision chronology. Do not guess a
variant suppression. Do not leave Coffee Shop until its zero-gap gate passes.
Frame 2328 remains evidence, not gameplay authority.
Evidence: `data/reimplement13_round1_stable_entry.json` and
`data/reimplement13_startup_authority.json`.

## Next eligible cards

- `QA-13-ROUND1-END-TO-END-DIFFERENTIAL` after the complete stable Round 2
  handoff candidate is committed and frozen.
