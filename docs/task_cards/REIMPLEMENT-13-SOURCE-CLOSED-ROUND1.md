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

The first projectile collision chronology is now source-correct. Native startup
begins at the accepted source frame 2072, each exceptional source update executes
entry, player, and scheduler in source order, and collision runs after record-type
`4` and record-type `12`. The exact parent/child prefix is preserved through
frame 2287; frame 2288 has zero damage; slot `0x00ff8880` writes damage at frame
2306 using current attack record `0x030cd2`; and class-`0x4e` allocates naturally
at frame 2307. No projectile variant is suppressed, no authored delay is used,
and the source input ledger is unchanged. Two pinned Emulator runs have identical
575-sample semantic ledgers at normalized ISO
`5cfc6e4e38a1052ed8fb684911826dc17747bd818e429dfc7f206036bf8f86cd`.
Fast, Oracle, Target, 161 real native mutations, 119 Target suppressions, eight
scene-census mutations, and four paired-emulator chronology mutations pass.

Real Windows Graphics Capture at source frames 2306/2307/2308 directly verifies
Predator Warrior identity and staff continuity, natural impact presentation,
P1-only HUD, coherent Coffee Shop planes, and unchanged palette/priority. The
whole-scene gate remains open at 387 missing source lifetimes, 1,391 unmapped
spawn/despawn edges, 37 unsupported states, 94 collision/damage, 3 route/camera,
and 281 audio/load gaps; unowned Saturn actors and retained gameplay authorities
remain zero. The edge count rises 15 because net missing lifetimes reduce the
missing-edge term by 24 while corrected source-aligned lifetime splits expose 39
additional boundary mismatches.

A corrective implementation-readiness pass closes the underlying first-contact
ordering that the earlier counters did not distinguish. Route-4 player eligibility
is sampled at scheduler-invocation entry; player locomotion/Button1 and record-type
`4` state projection match source actor records; newly allocated record-type `4`
actors enter collision registration on the next source scheduler invocation; and
class-`0x1f` collision boxes come from the current animation record without
overwriting actor `+0xa5/+0xa6`. The source/native prefix is empty of divergences
through frame 2287, frame 2288 remains damage-free, and source scheduler frame
2306 damages only `0x00ffa180` from 87 to 56 with `0x030cd2`; class-`0x4e` is
allocated naturally and visible at frame 2307. Focused SPEC/native/Target/scene
controls reject 89/161/119/8 real mutations. Fast, Oracle, and the normal
interactive LiveEncounter Target pass. Corrective commits `51a2e6032b088276b13aa4889626b2e817a0821f`
and `f4f4e339977f1eb39d60a478558672a87cdc77f4` are pushed and remote-equal.
Two commit-bound pinned Emulator runs have identical 575-sample ledgers at ISO
`c6a467bfe9453dd81c6383ae2992865b18017f334ca694107ee30053d4b9f2d3`, and four
chronology mutations reject. Window-only Windows Graphics Capture covers every
source-visible frame 2280..2310; direct inspection passes Predator identity,
staff continuity, natural projectile/impact presentation, P1-only HUD, both
Coffee Shop planes, palette and priority.

The refreshed whole-scene gate is 413 missing source lifetimes, 1,382 unmapped
spawn/despawn edges, 30 unsupported states, 94 collision/damage, 3 route/camera,
and 281 audio/load gaps; unowned Saturn actors, unidentified source pairs, and
retained gameplay authorities remain zero. Against `e24686b`, unsupported states
improve by seven and spawn/despawn by nine. Missing lifetime matches rise by 26
because the corrected damage target changes downstream reaction/lifecycle identity;
this is exposed work, not acceptance.

The collision-to-reaction scheduler boundary is now source-correct. Collision
writes the outer HIT state at source scheduler frame 2306 but does not bind the
reaction presentation early; visible frame 2307 retains substate `0x0000` and
animation `0x0012eb5c`, with the natural class-`0x4e` impact unchanged. Fast,
Oracle, LiveEncounter Target, two byte-identical 575-sample Emulator runs, and
real window-only frames 2280..2310 pass. The before/after scene gaps are
unchanged at 413 missing lifetimes, 1,382 spawn/despawn edges, 30 unsupported
states, 94 collision/damage, 3 route/camera and 281 audio/load events; unowned
Saturn actors, unidentified source pairs and retained gameplay authorities are
zero.

The earliest remaining complete-scene divergence is slot `0x00ffa180` at visible
frame 2308. Source enters `0x0202:0x0002` with class-`0x1f` animation
`0x0012e04c`; native enters the same state/substate with generic Port V2 HIT
animation `0x0012dd50`. Bind the source class-`0x1f` HIT action/presentation
program from accepted Oracle/SPEC evidence, using the smallest bounded Oracle
follow-up only if its implementation rules are absent. Do not implement from
the observational frame trajectory, and do not leave Coffee Shop until its
zero-gap gate passes.

The complete class-`0x1f` source HIT program is now implemented through normal
return. Recovery, phases `0x0200`..`0x020a`, movement, landing, bounce, RNG,
terminal presentation and the guarded action-`0x16` resume are fixture-bound;
generic selector-`0x36` action presentation is forbidden in HIT context.
Checkpoint `58bfeacb88360c48ec309a5bb057ca8e17724f92` is pushed and remote-equal.
Fast, Oracle, Target, 100 SPEC mutations, 161 native mutations, 119 Target
suppressions, eight scene mutations, and two commit-bound identical 575-sample
Emulator ledgers pass at ISO
`f2d0ec57fe4d9b02d6a7e578145039c3080ef450ce9a3801fdcba6b90b1df287`.
The sparse ROM decoder was extended for every source HIT/return assembly while
the measured tile archive and overlay remain within the existing carve.

Correctly aligned window-only WGC covers source-visible frames 2280..2310;
cadence sheet `82fb9fed7b16671ddcb77ae10734bc864998770d6ad0c503470e49005e65b8e6`
passes direct inspection. The refreshed whole-scene gate is 404 missing source
lifetimes, 1,379 unmapped spawn/despawn edges, 30 unsupported states, 94
collision/damage, 3 route/camera, and 281 audio/load gaps; unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero. Missing lifetimes improve by nine and spawn/despawn by three; no gap
category increases.

The class-`0x4e` fixed-slot reuse boundary is now source-correct. Visible frame
2307 retains the released class-`0x45` presentation (`0x0008df2c` /
`0x0008df96`, timer 4045, branch -32768), then the class-`0x4e` state-0 scheduler
visit binds `0x00092914` / `0x00092c04` for visible frame 2308. The sparse
decoder admits this accepted record for both source-reachable facings while all
`*-window` entries remain excluded from tile-content generation. The street tile
archive is unchanged.

Checkpoints `d27c2eef36a43a8bd1ff3c8cb061cbafe73dda62` and
`ee03bf4e5d2782ae6e2dff4005379f425c8b432e` are pushed and remote-equal. Fast,
Oracle, LiveEncounter Target, 101 SPEC mutations, 162 native mutations, 119
Target suppressions, eight scene mutations, and paired Coffee Shop Emulator
pass. Both Emulator ledgers are byte-identical at normalized ISO
`9d89bf114d80e354878fff2d7d35e7f8214dc4df0917d8ec328a235c38a0fa93`;
presentation decode failures are zero. Real window-only WGC covers source-visible
frames 2280..2310 with cadence sheet
`82fb9fed7b16671ddcb77ae10734bc864998770d6ad0c503470e49005e65b8e6`.
Direct inspection preserves Predator/staff identity, natural impact, P1-only
HUD, both planes, palette and priority.

The before/after scene gaps are unchanged at 404 missing lifetimes, 1,379
spawn/despawn edges, 30 states, 94 collision/damage events, 3 route/camera
events, and 281 audio/load events. Unowned Saturn actors, unidentified source
pairs, and retained gameplay authorities remain zero.

The next earliest causal divergence is class-`0x1f` slot `0x00ffa180` at visible
frame 2317. Source is substate `0x0200`, animation `0x0012e04c`, and position
`(684,310)`; native is substate `0x0202`, animation `0x0012e05c`, and position
`(682,322)`. Bind the exact accepted HIT transition/timer/branch/movement program
without fitting the observed trajectory or adding authored timing.

The class-`0x1f` recovery-to-launch scheduler boundary is now source-correct.
Accepted Oracle evidence proves that the recovery transition reaches substate
`0x0200`, animation `0x0012e04c`, and fixed-point position
`0x02ac4c00/0x0136d600` at visible frame 2317, then returns before the action
dispatcher. The following scheduler visit performs the launch and exposes
substate `0x0202`, animation `0x0012e05c`, and position
`0x02aa8c00/0x01425600` at frame 2318. The existing SPEC fixture now binds this
boundary and rejects same-visit launch as a real mutation.

Checkpoint `40d653e076ca9632964fae9dbf5f03e148548b04` is pushed and remote-equal.
Fast, Oracle, both LiveEncounter Target profiles, 102 SPEC mutations, 162 native
mutations, 119 Target suppressions, eight scene mutations, and paired Coffee
Shop Emulator pass. The paired ledgers are byte-identical at normalized ISO
`eb8ba9d6cc3e73d8cca8de0734d58b6662389cbc74f92598eccb7b4668bdf224`.
Fresh window-only WGC covers every source-visible frame 2280..2310; cadence
sheet `82fb9fed7b16671ddcb77ae10734bc864998770d6ad0c503470e49005e65b8e6`
and clip `792664b5e3a20dbb88a28d9c8de2f2188db70a053d23c6796147cace4bdbd2f4`
pass direct inspection. Predator identity, staff continuity, the natural
frame-2307 impact, P1-only HUD, both planes, palette and priority remain intact.

The before/after scene gaps are 404 / 1,379 / 30 / 94 / 3 / 281 and
404 / 1,377 / 30 / 94 / 3 / 281 for source lifetimes, spawn/despawn edges,
active states, collision/damage, route/camera and audio/load respectively.
Spawn/despawn improves by two; no category increases. Unowned Saturn actors,
unidentified source pairs and retained gameplay authorities remain zero.

The next earliest causal divergence is the dynamically allocated class-`0x1f`
slot `0x00ff9c40` at visible frame 2330: source hurt/attack selectors are `1/1`
while native remains `0/0`. Bind the accepted dynamic-spawn initializer and its
ordering; do not fit the observed frame or copy selectors from another actor.
Frame 2328 remains evidence, not gameplay authority.

That dynamic initializer boundary and the following complete source-owned
class-`0x43`/type-24 population are now native. Two four-actor groups preserve
their exact spawn order, seven RNG calls per actor, state, presentation,
lifetime, scheduler and release rules. Checkpoints
`9fd1e12d08905532c1f7ca6e209b8577b415dd86`,
`b3a20e3e1e9dd0bee0939aa1ea6a662f1dfaf876`,
`2f890be98dc6f8a8f236870a810cae2bd3fe6e88`, and
`019d291855a799d918abe3460eef9726219f2e1d` are pushed and remote-equal. The
bounded presentation carve is `0x89000`: the prior `0x87000` carve was proven
4,128 bytes short after the source population became render-reachable.

Fast, Oracle, 165 native mutations, 122 Target suppressions, both
LiveEncounter Target profiles, and two byte-identical 575-sample Coffee Shop
Emulator runs pass at normalized ISO
`70087b97966b4d3e5ad18052ebadb78e2adc8e2e592db8abd51684b56592c2ce`.
The Coffee Shop chronology rejects four real mutations. Fresh window-only WGC
covers frames 2280..2310; direct inspection preserves Predator/staff identity,
frame-2306 damage, frame-2307 impact, P1-only HUD, both planes, palette and
priority. Sheet `82fb9fed7b16671ddcb77ae10734bc864998770d6ad0c503470e49005e65b8e6`
and clip `792664b5e3a20dbb88a28d9c8de2f2188db70a053d23c6796147cace4bdbd2f4`
remain exact.

Scene gaps change from 404 / 1,377 / 30 / 94 / 3 / 281 to
405 / 1,358 / 30 / 94 / 3 / 281. Spawn/despawn improves by 19. Missing
lifetime rises by one because the corrected source RNG sequence exposes a
distinct downstream source lifetime rather than the prior false identity
match; this remains open work. Unowned Saturn actors, unidentified source pairs
and retained gameplay authorities remain zero.

The next earliest causal divergence is class-`0x1f` slot `0x00ffa3c0` at
visible frame 2363: source remains in state `0x0400`, while native advances to
`0x0402`. Bind the accepted transition predicate, timer/animation guard, RNG
ordering and scheduler position. Do not fit the frame or add authored delay.
Evidence: `data/reimplement13_round1_stable_entry.json` and
`data/reimplement13_startup_authority.json`.

That class-`0x1f` projectile-KO lifecycle is now native through release. Source
scheduler frame 2362 writes health `87 -> -1` and outer state `0x0400`; visible
frame 2363 preserves that state and performs the source-owned progress handoff;
visible frame 2364 enters `0x0402` with selector `0x36`, hit-kind `0x15`,
recovery `8`, and animation `0x0012e04c`. Recovery, launch, landing, bounce,
hold, and fixed-pool release match through frame 2508 without target-owned RNG.

Checkpoint `7b93a82f058d9fbfb236e35fa64682d9d4e12c25` is pushed and remote-equal.
Fast, Oracle, 105 SPEC mutations, 173 native mutations, 122 Target suppressions,
LiveEncounterBench Target, and paired 575-sample Coffee Shop Emulator evidence
pass. The normalized ISO is
`36c022aabc3b1ac7fae5598a6b74246e4d7a891c09ea8d07596daecbd12ac1d2` and
the canonical sample ledger is
`f41ac7b2f0287a096a4cd527291ee3c59620338d4d151e1ca887462fc114a148`.
Fresh window-only WGC covers frames 2280..2310; cadence sheet
`49cf96e5806daca5f04377e4b0ba563dd4e5d0890834a9e44f39d261661c680e`
and clip `792664b5e3a20dbb88a28d9c8de2f2188db70a053d23c6796147cace4bdbd2f4`
match the prior visual lock and pass direct inspection.

The before/after scene gaps are `405 / 1,358 / 30 / 94 / 3 / 281` and
`484 / 1,356 / 10 / 94 / 3 / 281`. Spawn/despawn improves by two and
unsupported states by twenty. Missing lifetimes rise by 79 because the
source-correct KO lifecycle changes downstream incomplete-native identity and
exposes additional source lifetimes without exact native matches. The increase
is open work, not acceptance. Unowned Saturn actors, unidentified source pairs,
and retained gameplay authorities remain zero.

The next earliest causal scene divergence is Predator Warrior slot
`0x00ff8380` at visible frame 2343: native animation record `0x0015e540`
differs from source `0x0015e594`. Bind the accepted player action/substate
transition, animation guard, and scheduler ordering. Do not fit the frame or
rebaseline input, and preserve the exact class-`0x1f` KO lifecycle through
frame 2508.

The frame-2343 Button1 divergence is now source-bound. Routine `0x0241f0`
scans eligible type-12 targets at action entry, table `0x024100` maps the
measured distance bucket to presentation selector `4..7`, and native code
latches the matching projectile angle from the same scan. There is no
fixed-frame selection, authored delay, projectile suppression, or later target
rescan. SPEC-02 contract
`79c5fd6a775a3b68d2b0145fed60acd16e2f0668356c48f7ff20fad2a6844625`
and fixture
`2a94f940406212a2d0c22267c686faa1a8f440d465800abf82606d07d5cb1cce`
bind the implementation.

Fast, Oracle, 105 SPEC mutations, 173 native mutations, 123 Target
suppressions, LiveEncounterBench Target, and two byte-identical 575-sample
Coffee Shop Emulator ledgers pass. The normalized ISO is
`4baa310d670328f496154d6e5682074d4b45cfb37973909d71744582ef6577b7`;
the canonical sample ledger remains
`f41ac7b2f0287a096a4cd527291ee3c59620338d4d151e1ca887462fc114a148`.
The measured `0x8d000` presentation carve leaves 7,380 bytes after the
553,444-byte base archive and 16,712-byte combat overlay; live overflow and
pin exhaustion are zero. Fresh window-only WGC covers frames 2280..2310;
cadence sheet
`82fb9fed7b16671ddcb77ae10734bc864998770d6ad0c503470e49005e65b8e6`
and clip
`792664b5e3a20dbb88a28d9c8de2f2188db70a053d23c6796147cace4bdbd2f4`
pass direct inspection with stable Predator/staff identity, P1-only HUD,
coherent backgrounds, frame-2306 damage, and frame-2307 impact.

The scene gate changes from `484 / 1,356 / 10 / 94 / 3 / 281` to
`392 / 1,360 / 30 / 94 / 3 / 281`. Missing source lifetimes improve by 92.
Spawn/despawn rises by four and unsupported states by twenty because the
source-correct selector and angle expose unmatched downstream class-`0x03`
state `0x0604` and class-`0x49` state `0x0002` lifecycle identities. Those are
explicit open gaps, not acceptance. Unowned Saturn actors, unidentified source
pairs, and retained gameplay authorities remain zero.

The next earliest causal scene divergence is class `0x09`, type `20`, slot
`0x00ffb500` at visible frame 2367: source animation record `0x0006dbfe`
differs from native `0x0006dc46`. Bind its accepted transition predicate,
timer/animation guard, RNG ordering, and scheduler position. Do not fit the
frame or rebaseline input, and preserve all current first-segment locks.

## Next eligible cards

- `QA-13-ROUND1-END-TO-END-DIFFERENTIAL` after the complete stable Round 2
  handoff candidate is committed and frozen.
