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

Checkpoint `d5bf091a014c8624c00111919a6c8efa69fe16ba` is pushed and
remote-equal. It is an incremental Coffee Shop evidence checkpoint, not
candidate promotion; the existing candidate pointer remains unchanged until
the complete zero-gap scene gate passes.

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

The projectile-parent population boundary is now source-bound. Routine
`0x02f94c` calls allocator `0x08f0c6` through dispatcher `0x08f080`; the
source guard is global phase byte `+0x19` bit 0 clear. Native record-type-4
execution now allocates type-24/class-`0x49`/variant-0 effects before
record-type-12 collision, preserves source LIFO pool ownership, and implements
the state-0 fallthrough into state-2 timer decrement. The exact phase
projection derives from the accepted Coffee Shop scheduler cadence, not an
authored frame delay. Variant-10 class-`0x4e` impact and attack record
`0x030cd2` remain source-bound.

Checkpoint `cc33807babf536c4f42bf204038091427c391a89` is pushed and
remote-equal. SPEC-02 contract
`bd838608397cbb895bc093163d2bd8de7d413ab2799a30f9419cd547002abf82`
and fixture
`d546a87696ec80e317325412398fc8f5455bf55536c60d3625baba630e19ff93`
bind the implementation. Fast, Oracle, 109 SPEC mutations, 178 native
mutations, 123 Target suppressions, LiveEncounterBench Target, and two
byte-identical 575-sample Coffee Shop Emulator ledgers pass. The paired ISO is
`8edf2901ddfa53c448678c91e839ee684fc04db46badf9b4bed3b878f10db2b8`;
the canonical sample payload is
`d204f743e1916c25b87900fd9aa573f40d36af60371dab884ff8bec125bd2a40`.
The target-only stale SPEC fingerprint found during paired Emulator was
corrected, and Target wiring now derives the expected fingerprint from the
current contract so future drift is rejected.

Fresh window-only WGC covers every frame 2280..2310. Cadence sheet
`dc162f011463e9f3f46847c939754265e42474fdb66800a1af35cb87f1e203b1`
and clip
`b2695152db316962ac45c3ca5ab9f9742eb3b933eb23e5e536167e8613ac535c`
pass direct inspection: Predator/staff identity, source scene population,
P1-only gameplay ownership, both Coffee Shop planes, palette/priority, no
frame-2288 damage, frame-2306 damage, and the natural frame-2307 impact remain
coherent. The measured `0x8d000` presentation carve contains the 559,252-byte
base archive and 16,712-byte combat overlay with 1,572 bytes headroom; live pin
exhaustion and overflow remain zero.

The scene gate improves from `392 / 1,360 / 30 / 94 / 3 / 281` to
`335 / 1,293 / 3 / 94 / 3 / 281` for source lifetimes, spawn/despawn, active
states, collision/damage, route/camera, and audio/load respectively. No
category increases. Unowned Saturn actors, unidentified source pairs, and
retained gameplay authorities remain zero. The gate is still open.

The next earliest causal scene divergence is record-type `4`, class `0x04`,
slot `0x00ff8800` at visible frame 2371: source animation record `0x0003088c`
is active while native remains zero. Bind the accepted child presentation and
lifecycle transition, including its state guard, scheduler position, and pool
ownership. Do not fit the frame, rebaseline input, or disturb the exact
frame-2287/2306/2307 chronology.

The fixed-slot presentation boundary is now source-bound. Accepted allocator
and release evidence for `0x01773e`/`0x017754` proves that the record-type-4
slot is not presentation-cleared at release or reallocation. Native preserves
the prior animation record, assembly, timer, and signed branch until state-0
initialization. At visible frame 2371 slot `0x00ff8800`, class `0x04`, variant
`2` now retains source record `0x0003088c`, assembly `0x00030b28`, timer `1`,
and branch `-32768`; source initialization replaces them naturally at frame
2372. No fixed-frame substitute, suppression, or input change is used.

Incremental implementation checkpoint
`9a6c1010a72d57c7c6c5fabfb52a0e8ddd450d8b` binds SPEC-02 contract
`fd65f15e44695ccdc65c2e59516ddb11ccd7315fe327f63c20a34ab00a51169f`
and fixture
`401253d2279846118b96c04b8c9ad6d41272102f3e3b203bb0d55ed3f25e9ff2`.
Fast, Oracle, 110 SPEC mutations, 179 native mutations, nine scene mutations,
123 Target suppressions, LiveEncounterBench Target, and two commit-bound
byte-identical 575-sample Emulator ledgers pass. The normalized ISO is
`4dda2cf243c5f0f715aa2610ea078784bd7a93f525ab44708c98c1534b80c7e6`;
the sample payload is
`0afd341dd78d367adf5b323cb3b5e6d99b762d65844f36b64cfe330f6adce16a`.

Fresh window-only WGC covers visible frames 2368..2374. Cadence sheet
`9d76768c838f6a7af2c8fa45b7c7b1347ac2b6ca43a094139dbce64f68526bd3`
and clip
`c7faf1b5f585173fca90639557ea08ab5bdba4320e66c28bf889071355d22502`
pass direct inspection with stable Predator identity, retained frame-2371
presentation, and coherent Coffee Shop planes, palette, and priority. The
scene gaps remain `335 / 1,293 / 3 / 94 / 3 / 281`; no category increases
because this repaired per-frame presentation was already inside an exact actor
lifetime. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero.

The frame-2378 selector divergence and its downstream frame-2306 chronology are
now source-bound. Class-`0x1f` action `0x16` performs one RNG transaction at
`0x017c5e` and shares the result across the inner-`0x08` guard, fallback branch,
and timer selection. The accepted frame-2377 transition `0xc9a2 -> 0x5cfe`
produces selector `2` and record `0x0012ec74` at frame 2378; a second call is a
real rejected mutation. Record-type-4 allocations that occur after their lower
slot has passed remain collision-registration-pending through state-0
initialization and register on the following scheduler invocation. Native
therefore has no frame-2288 damage, writes `0xffa180` health `87 -> 56` from
slot `0x00ff8880` and attack `0x030cd2` on source scheduler frame 2306, and
allocates the class-`0x4e` impact naturally for visible frame 2307.

Incremental implementation checkpoint
`9b6835c05a301de27bdb8b9e6bca0ba62e377d65` and validator checkpoint
`45f890d5458be5de57b31afd7e8adcdc78d8fb4c` bind SPEC-02 contract
`051d3047cd763f80da0e98e83e5c6d85ddc0b887ecf66334e7d279d1fb5a00ce`
and fixture
`4cf23d3b5c32649a8804acdcd3d740436a1490759c4d9bbb3550b49c0205d84f`.
Fast, Oracle, 112 SPEC mutations, 181 native mutations, eleven scene mutations,
123 Target suppressions, both LiveEncounter Target profiles, and paired
commit-bound 575-sample Coffee Shop Emulator ledgers pass. The validator now
derives class-`0x1f` presentation ownership from the accepted SPEC table rather
than an incomplete hardcoded subset. Normalized ISO is
`d7470bb606b91f142d8ea30098291d467b1e851582bc9415ab1046c07ad857c7`;
canonical sample payload is
`71c59a86a9c518c73ee432d6477c37b2736fa74afc566ca3cda3c7656559812e`.

Fresh window-only WGC covers every visible frame 2280..2310. Cadence sheet
`8ea5eb2c8a440b81fad5886f75caf5b806a5415cef3713587570816781b2235f`
and clip
`b2695152db316962ac45c3ca5ab9f9742eb3b933eb23e5e536167e8613ac535c`
pass direct inspection with no frame-2288 premature effect, the frame-2306
contact, natural frame-2307 impact, stable Predator/staff identity, and coherent
Coffee Shop planes, palette, and priority. Scene gaps improve from
`335 / 1,293 / 3 / 94 / 3 / 281` to
`316 / 1,293 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero. The complete scene gate remains open.

Incremental checkpoint `e0f3403a9db49e7e9d8f33931255df7cf8e408cc`
closes the complete slot-`0x00ffa300` action-`0x16` retry and recovery cadence.
The accepted frame-2409 latch (`+0xae = 1`, `+0xa6 = 2`) skips the inner-`0x08`
entry RNG branch, consumes exactly one `0x017c5e` result
`0x4bdf -> 0xe3c2`, indexes timer `30`, enters action `0x1a`, toggles facing,
and binds record `0x0012d5e4` for visible frame 2410. Action `0x1a` preserves
that timer when entering `0x18`. The source HIT terminal record
`0x0012ded8` remains visible for its complete source frame before normal return.
SPEC-02 contract is
`9a65b6d082e477898aa966ae06984b5d4807f2db7ddbdfb3d5552bc0c5ad2d56`;
fixture is
`f129e65004dcdd8da240ce7533318c1d6511b41f3df1aa5eecd1a3a19899c759`.
Fast, Oracle, both Target profiles, 113 SPEC mutations, 82 Oracle-enemy
mutations, 181 native mutations, twelve scene mutations, and two commit-bound
575-sample Emulator ledgers pass. The paired normalized ISO is
`ef5791f9254915d9cf2b878740e4b6b86a99d157c4f48b1227d0382f501e6816`;
canonical sample payload is
`a955f984a172c595f0ee788593cdd0e3113ab51b34d8978df4a749ad9a88a8e4`.

Fresh window-only WGC covers every visible frame 2408..2425. Cadence sheet
`a137ce6039b62620de494ee8db645404d5e71a5aa5451aea5fb5653ac28d7de6`
and clip
`d7493bf51d125852300863ddd8ed99f2e37513ce3f4f8add9f5cf72a5bc3ac6d`
pass direct inspection: Predator/staff identity is stable, the alien transition
and return have no stale pose, the `WARRIOR` row remains the P1 equipment meter,
no active P2 panel appears, and both Coffee Shop planes, palette, and priority
remain coherent. Scene gaps improve from
`316 / 1,293 / 3 / 94 / 3 / 281` to
`305 / 1,285 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero. The complete scene gate remains open.

Incremental checkpoint `c584e416ac25d4e579e8c66a4059304a7e947b6c`
closes the record-type-`4`, class-`0x00`, slot-`0x00ff8680` parent trajectory.
The fixed-slot allocator `0x01773e` replaces only the x/y high words, so native
now preserves the source slot's `0x0a00/0xb800` fractional residue. Target
selector `0x0241f0` starts its unsigned nearest distance from the sign-extended
`MOVEQ #$ff` value `0xffffffff`, not `0x00ff`; the route target at distance 343
therefore selects source angle 46. Terminal record `0x0002fbb8` loops to
`0x0002fba8`, and camera-relative bounds enter the source emitter/release path
instead of releasing immediately.

All 67 source/native rows from visible frame 2434 through 2500 now match at
fixed-point x/y, state, timer, animation, angle, and progress. Both row hashes
are `789cb79e083e0aa356989e67dbd6a0188a4eb58f794765c28d8bac0bd1544888`.
The narrow accepted static Oracle correction amends only the nearest-distance,
fixed-slot allocation, terminal-loop, and camera-bound implementation fields.
SPEC-02 is
`56f273bae8740ab294be897ab14831a727d1354116211e05ac64c97dfb536238`;
fixture is
`5a508062eed207eddb25d6351b5d6b08a3e0544ac2c9726e3877caea6a2832bd`.
Fast, Oracle, 113 SPEC mutations, 45 weapon mutations, 181 native mutations,
15 scene mutations, 123 Target suppressions, and both LiveEncounter Target
profiles pass. The combat overlay's tile set and archive hash remain unchanged;
only its derived SPEC fixture identity advanced.

Two commit-bound 575-sample Coffee Shop Emulator ledgers are byte-identical at
normalized ISO
`9e4544d34242e710148e9b4a13df034173097be3a1d171aad7ad2fd690ad5b1c`;
canonical sample payload is
`92bc7e467d17eb0149d3b8c1e67f922f32140ee2e88e3c02d98ac0d46f90c767`.
Fresh window-only Windows Graphics Capture covers every visible frame
2434..2500. Cadence sheet
`06c40976bceb749c62d62a1a05b2dbc0d193c4d25fdf8271eaee5db95ac2d937`
and clip
`624c3dc4ece7c881f49422cea59e8dd84b98c541116168728f781c9cfea7e1ef`
pass direct inspection: Predator/staff identity is stable, parent and emitted
effects move coherently, the P1-only HUD/equipment row remains intact, and both
Coffee Shop planes, palette, and priority are coherent.

Whole-scene gaps improve from `305 / 1,285 / 3 / 94 / 3 / 281` to
`305 / 1,272 / 3 / 94 / 3 / 281` for actor lifetime, spawn/despawn, active
state, collision/damage, route/camera, and audio/load respectively. No category
increases. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero; the complete Coffee Shop gate remains open.

Incremental checkpoint `a54b4567c87bbed611b1aeb675df2aa9b4bc3ca0`
closes the slot-`0x00ff9d00` HIT-return and source-bounds phase boundary. The
accepted common return tail clears actor `+0x85`; routine `0x060c2e` then reads
the scheduler-entry phase bit before the recurring controller advances it.
Odd phase uses player-proximity helper `0x060e94` and continues when the player
is not near; even phase performs the unsigned camera-relative test. Native now
preserves action `0x16` through visible frames 2469 and 2470 and enters release
state `0x0600` at frame 2471 exactly as the source does. The exact
frame-2287/2306/2307 collision chronology and all 67 record-type-`4` rows stay
locked.

SPEC-02 contract is
`41791464584f88d98b550c73c763fcdbd13c5e2a0d7750d2b975e11e9e49a287`;
fixture is
`fd643801590a2bab1094f84b5fd658cd7d11753d5527f77b758bc76efa433149`.
Fast, Oracle, 115 SPEC mutations, 82 Oracle-enemy mutations, 181 native
mutations, 15 scene mutations, 123 Target suppressions, both LiveEncounter
Target profiles, and two commit-bound byte-identical 575-sample Emulator
ledgers pass. Normalized ISO is
`4f36929763215ac62cef93297412e06afeb46cbedcf4b8465d3e166aef8c5a2f`;
canonical sample payload is
`0384c57f25723a4e411f1a13db2c3b45b45020099aaf36af904a87e5a73c85f9`.

Fresh window-only WGC covers visible frames 2468..2472. Cadence sheet
`f7eafa69d9d87682a4e97a8bf228522256a09f1f309fdc3070f53668ea2cb837`
and clip
`9ceefe633829db7f20eeb1cf6b2092d400f1a9b74bf23782d72cafd4ebd0ec98`
pass direct inspection with stable Predator/staff identity, coherent
class-`0x1f` held pose and release, P1-only HUD/equipment, and coherent Coffee
Shop planes, palette, and priority.

Whole-scene gaps change from `305 / 1,272 / 3 / 94 / 3 / 281` to
`319 / 1,274 / 3 / 94 / 3 / 281`. The actor-lifetime count rises by 14 because
the exact phase chronology invalidates 47 downstream false lifetime matches
while resolving 33 genuine mismatches; spawn/despawn rises by two from the same
downstream pool churn. Active-state, collision/damage, route/camera, and
audio/load categories do not increase. Unowned Saturn actors, unidentified
source pairs, and retained gameplay authorities remain zero. The complete
Coffee Shop scene gate remains open.

The next earliest causal divergence is visible frame 2511. Record-type `20`,
class `0x09`, slots `0x00ffb480` and `0x00ffb500` remain on source animation
`0x0006dbda` while native advances to `0x0006dbfe` and `0x0006dc22`;
record-type `32`, class `0x01`, entry-controller x is source `8` versus native
`9` on the same frame. Recover the accepted counter, guard, presentation
cadence, and scheduler order and determine whether both discrepancies share one
source writer. Do not fit the frame or disturb any accepted chronology or
presentation lock.

Incremental checkpoint `f3bd0c438e2c6de78f727c9cec04a353532423cc`
closes that shared recurring-phase boundary. Accepted evidence proves source
global phase `0xff8019` is `0x06` at native-entry handoff frame 2072 and
increments before the recurring controller and actor-pool scheduler. Native
frame 2510 now matches phase `0xbf`, RNG `0xd21c`, living count 7, spawn index
9, and timer 3707. Frame 2511 matches phase `0xc0`, RNG `0x81a1`, living count
8, spawn index 8, and timer 3706. Both class-`0x09` actors retain their
frame-2510 terminals and select source record `0x0006dbda` at 2511. The first
recurring class-`0x1f` actor allocates naturally at slot `0x00ffa3c0`, position
`672/328/328`, state `0x0200:0000`, and health 87. No projectile variant,
damage delay, or input rebaseline was introduced.

SPEC-02 is
`b1b967ea0f023aa4236437591bc55579d481be897300631dc5b23277013f451d`;
fixture is
`308c65f081447dda52a6eb26e89aa260c339a71a18db65debaaa253243ba389a`.
Fast, Oracle, 115 SPEC mutations, 82 Oracle-enemy mutations, 181 native
mutations, 17 scene mutations, 123 Target suppressions, and both LiveEncounter
Target profiles pass. The combat tile overlay content is unchanged; only its
derived fixture identity advanced.

Two commit-bound 575-sample Emulator ledgers are byte-identical at normalized
ISO `e9a6542deb30c82e175f9500f6d5c10904035f90a1d7ab6f7bc285bdc1ad3a30`;
canonical sample payload is
`c1b9f52236fc987635d7536264288267e2db6821e69a86c5a48323cb2b5e05c9`.
Fresh window-only WGC covers every visible frame 2280..2310. Cadence sheet
`dc162f011463e9f3f46847c939754265e42474fdb66800a1af35cb87f1e203b1`
and clip
`b2695152db316962ac45c3ca5ab9f9742eb3b933eb23e5e536167e8613ac535c`
pass direct inspection with stable Predator/staff identity, coherent projectile
and impact presentation, clean Coffee Shop planes, palette and priority. The
lower `WARRIOR` strip is source-owned P1 `HUDTOP` content; the separate P2 panel
is absent.

Whole-scene gaps improve from `319 / 1,274 / 3 / 94 / 3 / 281` to
`295 / 1,259 / 3 / 94 / 3 / 281` for actor lifetime, spawn/despawn, active
state, collision/damage, route/camera, and audio/load respectively. No category
increases. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero; the complete Coffee Shop gate remains open.

The next earliest causal divergence is visible frame 2511 at newly allocated
slot `0x00ffa3c0`: source already owns animation `0x0012ddb0` in state
`0x0200:0000`, while native has the correct allocation, state, position and
health but animation `0x00000000` until the next scheduler visit. Bind the
accepted same-frame state-0 presentation initialization without authoring a
delay or disturbing the corrected phase, RNG, spawn-index, class-`0x09`,
collision, player, camera, HUD, audio, or rendering locks.

Incremental checkpoint `24670a6dab40770a2cbe1fb60d1400dc0ac95784`
closes that same-frame presentation boundary. The recurring actor now matches
source animation `0x0012ddb0`, assembly `0x00130346`, timer `0x0fff`, branch
`-0x8000`, and hurt/attack selectors `1/1` on frame 2511. SPEC-02 is
`f6711c3d69fe9dc5527bc905ef2a1e3c2ec32d7207ad4b1ca6b316a36527dfab`;
fixture is
`6124a16d3aed20e1bf5c284cf5e721a4586432ddb869fd6f1d947e1706f6d335`.
Fast, Oracle, 116 SPEC mutations, 26 encounter mutations, 82 enemy mutations,
181 native mutations, 18 scene mutations, 123 Target suppressions, both
LiveEncounter Target profiles, and two byte-identical 575-sample Emulator
ledgers pass. Normalized ISO is
`ff89cf06ed4f72bc31ab690e71e92b68c2b610b79934c4bc415c86564f2c41da`;
canonical sample payload is
`624345e3a23442e212baa06bf670145876b2028b2888ae09b8aa767cb2164d27`.

Window-only WGC frames 2509..2513 pass direct inspection. Cadence sheet
`ca6110ec4506116f7fef1cbb7550f3865e2bf4aaa8a29fcc24bac8ae5d51060a`
and clip
`aac56eeb841854b3ad72a9b0aba0e56074fe9ed53745ddf37c5316566c58911a`
preserve Predator/staff identity, coherent alien presentation, P1-only HUD,
and both Coffee Shop planes, palette, and priority. Whole-scene gaps remain
`295 / 1,259 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero.

The next earliest causal divergence is visible frame 2330 at class-`0x1f`
slot `0x00ff9c40`: source animation is zero while native binds `0x0012ddb0`.
Recover the exact source dynamic-allocation presentation guard and scheduler
position and distinguish this earlier allocation from the now-closed recurring
spawn at frame 2511. Apply the source rule, not a slot/frame exception, while
preserving the already-closed selectors `1/1` and all accepted locks.

Incremental checkpoint `8b1600473c77f2459ea1ccc554d94dc01ffddcbe`
closes that owner guard. Accepted Oracle/SPEC evidence identifies slot
`0x00ffb580` as a type-20/class-`0x01` controller that allocates record-12
variant 5 for next-tick dispatch; only recurring-controller variants 3 and 4
receive the accepted same-frame presentation. Frame 2330 slot `0x00ff9c40`
now matches source state `0x0200:0e00`, animation/timer/branch zero, with its
already-closed selectors `1/1` intact. The scene validator rejects 19 real
mutations, including generic dynamic-spawn presentation.

Fast, Oracle, 116 SPEC mutations, 25 encounter mutations, 82 enemy mutations,
181 native mutations, 123 Target suppressions, both LiveEncounter Target
profiles, and two byte-identical 575-sample Coffee Shop Emulator ledgers pass.
Normalized ISO is
`a14217a3af6834f53c95524fd815251f843855802e7ab27fee361846b4a58fbf`.
Window-only WGC frames 2328..2332 pass direct inspection: cadence sheet
`9272526bd5352dec72ed8ddfe337079ef1bd2d774bb9516b78e4814dde599fb6`
and clip
`fa8f054e5dd0510f937ad85ea7307ab8740ca4bfbeebc07d48b0db9507aa57c3`
preserve Predator/staff identity, P1-only HUD, coherent actor presentation,
and both Coffee Shop planes, palette, and priority.

Whole-scene gaps remain `295 / 1,259 / 3 / 94 / 3 / 281`; no category
increases. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero. The next earliest causal divergence is
visible frame 2514 for recurring slot `0x00ffa3c0`: source `y/z` are `327/327`
while native is `326/326`; `x` first differs at frame 2517 (`687` versus
`686`). Recover the exact accepted movement arithmetic, signedness, scheduler
position, and subpixel carry, then apply the source rule without a frame/slot
exception.

Incremental checkpoint `368bb391ff82c4b542b0fdfe0465c8be3d04e7e0`
closes the recurring fixed-point record-reuse boundary. Accepted Oracle evidence
proves that the recurring record-12 writer replaces the signed high position
words while preserving the allocated record's low `u16` fractions. Native now
matches source at frames 2511, 2514, and 2517: `x/y`
`0x02a08000/0x01489000`, `0x02a7e200/0x01470900`, and
`0x02af4400/0x01458200`. The allocator and state-0 seed use that source rule;
there is no frame or slot exception.

SPEC-02 contract is
`51150e37e05d7e0199cec08725580630ef1a1890d3a63fdff68bf7e7c11c8cf2`;
fixture is
`e5ece146171b40172901c3ad58f3fc71af6109cdb938b18c91f08d117c895d78`.
Fast, Oracle, 117 SPEC mutations, 26 encounter mutations, 82 enemy mutations,
181 native mutations, 20 scene mutations, 123 Target suppressions, both
LiveEncounter Target profiles, and two byte-identical 575-sample Coffee Shop
Emulator ledgers pass. Normalized ISO is
`94608db70794fa58bcd8c2d7e49fe0d6b2a8376423ebabe82f57f675ef8f6614`.

Window-only WGC frames 2510..2518 pass direct inspection. Cadence sheet
`e8946734278145e5e234bd731732fcc9cadc000354eadd1b5c9a84182fe3a93a`
and clip
`e7bfdbab252e2578cc6813fb0524f675aea03098025636a0cbd3aa855af80fe9`
preserve Predator/staff identity, coherent recurring movement, P1-only HUD,
and clean Coffee Shop planes, palette, and priority. Whole-scene gaps remain
`295 / 1,259 / 3 / 94 / 3 / 281`; no category increases. Unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero.

The next earliest causal divergence is visible frame 2522 at player slot
`0x00ff8380`: source substate is `0x1a00` while native remains `0x0c00`, with
the first animation divergence at frame 2523. Recover the exact accepted
transition predicate, input/interruption guard, writes, presentation selection,
and scheduler position, then apply the source rule without a frame exception.

Incremental checkpoint `ec41b2bc70e4b5212cb8f9b586305b34ab3fba05`
closes that depleted-resource dispatch. Source dispatch `0x01a6f4` tests the
persistent player `+0x8b` depleted latch and enters action `0x1a00` at visible
frame 2522. Normal recharge (`0x0adf06`, reload 3) and depleted recharge
(`0x0adfc0`, reload 6) retain their distinct decrement, reload, increment, and
later latch-clear ordering. Two source captures are byte-identical at
`af67295b879521e0aba388ebe4b1bd9e8698c21c86e9d5b837da14efe086b4cb`;
the increment-suppression control proves the action remains latch-owned.

SPEC-02 is
`e709b7bd616ecdb118e61459dbbc7677c9d0e13dd932f5bd4cf856a25f6d61ac`;
fixture is
`f726c7ae09f3edad2fb93fc853cf3851eb618449e72a64ad89a7b9974e2098e8`.
Fast, Oracle, 119 SPEC mutations, 45 weapon controls, 82 enemy mutations, 181
native mutations, the scene validator, 123 Target suppressions, both
LiveEncounter Target profiles, and two byte-identical 575-sample Emulator
ledgers pass. Normalized ISO is
`be01ec7dfe1a002ec5bda0807e945e6d59544ea59e772a9f8f82f75edbc6cbaa`;
canonical samples hash to
`aab911fae523eb13b79969cf5a0d99ce002400577e3dd6016f416a6c6f60e099`.

Window-only WGC frames 2520..2540 pass direct inspection. Cadence sheet
`8788ae5739323986ef83f3734154acf0c71c27bd18680b07afe36327410ed83e`
and clip
`65651d2fb214185f4a548607cb89ad4ffc39d5cac9faf18157ec4fc4e4bcb242`
preserve Predator/staff identity, source-timed empty-resource presentation,
P1-only HUD and weapon meter, and clean Coffee Shop planes, palette, and
priority.

Whole-scene gaps change from `295 / 1,259 / 3 / 94 / 3 / 281` to
`322 / 1,262 / 2 / 94 / 3 / 281`. The lifetime and spawn-edge counts rise by
27 and 3 because the corrected depleted branch changes downstream type-24
fixed-pool reuse and invalidates earlier false lifetime/edge matches; active
state improves by one. The source capture is unchanged, the other categories
do not increase, and unowned Saturn actors, unidentified source pairs, and
retained gameplay authorities remain zero.

The next earliest causal divergence is visible frame 2523 at source slot
`0x00ffc300`: source owns type-24/class-`0x4e` on animation `0x0007a09c`,
`y=404`, `z=319`, while native has reused the slot and presents `0x0007a0ac`,
`y=402`, `z=0`. Bind the exact type-24 lifetime, release/reuse order, scheduler
position, class/variant ownership, state initialization, coordinate writes,
and presentation cadence. Apply the source rule, not a frame or slot exception.

Incremental checkpoint `e352c265f45b114da040774e5fb9a53598e08117`
corrects that report and closes the actual source type-24/class-`0x10`
empty-resource effect. The scene reporter now keys lifetimes by slot, type, and
class, preventing slot reuse from inheriting an earlier class-`0x4e` label.
Accepted Oracle/SPEC evidence places allocation one player update after the
depleted action entry, copies Predator variant zero, applies source offset
`[0,84]`, writes the source position high words, and preserves the reused pool
record's `x/y` low fractions and `z`. Actor `coffee-shop-actor-134` exactly
matches source frames 2523..2540 and animations `0x0007a09c` through
`0x0007a12c`. Real controls reject immediate allocation, Major variant one,
cleared allocation residue, and wrong vertical offset.

SPEC-02 is
`4c52813c7f36e7094cae51bbd9d07c9d51001afcce3300455b67fcc645f5f723`;
fixture is
`2f05a0ef5a107403a4a74f06208ffec9fadb3f856ce13510efb185be4971fe5c`.
Fast, Oracle, 121 SPEC mutations, 45 weapon controls, 82 enemy mutations, 181
native mutations, 20 scene mutations, 123 Target suppressions, both
LiveEncounter Target profiles, and two byte-identical 575-sample Emulator
ledgers pass. Normalized ISO is
`b15add08e7267ffe7f2d81d0aa3d423acd787bac3fdb1ebc9d7199670d37b152`;
canonical samples hash to
`0351745eb6c89a5378b245548609c220834fbb5e73c0a97bf5884ce98fc5799a`.

Window-only WGC frames 2520..2540 pass direct inspection. Cadence sheet
`8788ae5739323986ef83f3734154acf0c71c27bd18680b07afe36327410ed83e`
and clip
`65651d2fb214185f4a548607cb89ad4ffc39d5cac9faf18157ec4fc4e4bcb242`
preserve Predator/staff identity, the source-timed empty-resource
presentation, P1-only HUD and weapon meter, and clean Coffee Shop planes,
palette, and priority.

Whole-scene gaps improve from `322 / 1,262 / 2 / 94 / 3 / 281` to
`322 / 1,256 / 2 / 94 / 3 / 281`. Six spawn/despawn gaps close; no category
increases. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero.

The next earliest causal divergence is visible frame 2572 at type-12/
class-`0x1f` slot `0x00ffa240`: source animation is `0x0012e778` while native
selects `0x0012ddb0`. Recover the accepted animation/state transition guard,
timer, and scheduler order that owns this first mismatch. Apply the source
rule without a slot/frame exception and preserve every closed lock.

Incremental checkpoint `ce829c774f21f2a25069e9b5ae3ffbf4e092345f`
closes that recurring class-`0x1f` residue boundary. Source fixed-pool
allocation preserves the reused record's animation, assembly, timer, branch,
and position fractions. It no longer forces synthetic animation `0x0012ddb0`.
The source action-`0x0c` selectors are numeric 53 and 54. Slot `0x00ffa240`
now follows the measured frame-2567 release, frame-2572 residue-preserving
allocation, and frame-2573 action-`0x0c` presentation without a frame or slot
exception.

SPEC-02 is
`75689cc3c7bc11a6178c621c004f58cca041ffc174f7df8354aeb4b83b4a9293`;
fixture is
`8554c61db6b1b4e8e64ab6b726c66f2e87539f29084d43c529e119fddc37dcd8`.
Fast, Oracle, 124 SPEC mutations, 45 weapon controls, 83 enemy mutations, 183
native mutations, scene mutations, 123 Target suppressions, both
LiveEncounter Target profiles, tile-residency controls, and two commit-bound
575-sample Coffee Shop Emulator ledgers pass. The normalized ISO is
`2a09a79404cbe23b757ada94eafe5413e443588cb7fd5430438af635accc50bb`;
canonical samples hash to
`2bb6c0321215d15d92b7a26a59e5a375b4bb9ea8ca003de93c6db8aba391e949`.
The action-`0x0c` source-table union adds 18 assemblies and 253 tiles; the
592,648-byte scene archive remains inside the bounded 614,400-byte residency
carve.

Window-only WGC frames 2567..2574 pass direct inspection. Cadence sheet
`f66e267cad887423c8668034b02382352a2e680befff8277537ab525b668dd5a`
and clip
`5bd777c522b5c545773d4922a45639197b72afc20548919c86405efe70f85bba`
show the corrected action-`0x0c` actor without a decoder failure, coherent
source scene population, and clean Coffee Shop planes, palette, and priority.
The source-scene Warrior status presentation remains source-owned; this
checkpoint does not infer that it is a P2 gameplay actor.

Whole-scene gaps improve from `322 / 1,256 / 2 / 94 / 3 / 281` to
`308 / 1,253 / 3 / 94 / 3 / 281`. Actor lifetime improves by 14 and
spawn/despawn by three. Active-state gaps increase by one because the corrected
earlier trajectory exposes three later mismatches: class-`0x1f` slot
`0x00ff9dc0` at `0x0200:0406`, and type-4/class-`0x03` slots `0x00ff8980` and
`0x00ff8780` at `0x0604:0000`. Other categories do not increase. Unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero.

The next earliest causal divergence is visible frame 2752 at type-12/
class-`0x1f` slot `0x00ffa240`: source animation is `0x0012d8a0` while native
selects `0x0012d8b0`. Bind the accepted transition writer, animation guard,
timer, selector, fields, and scheduler order that own this first mismatch.
Apply the source rule without a frame/slot exception and preserve every closed
lock.

Incremental checkpoint `ec4294e698600052062fb483de6f1e5b31e6a3c0`
closes the earlier class-`0x1f` current-state collision writer that the whole-
scene comparison exposed. Accepted Oracle/SPEC evidence binds attack table
`0x130ac8`, attack record `0x130b5c`, selector 1 against player defender table
`0x11ae02`, hurt record `0x11ae8e`, selector 17. Writer `0x01d5ee` performs
the source frame-2750 health write `101 -> 91`; the attacker then holds its
source animation for exactly ten ticks. There is no authored delay, projectile
suppression, slot exception, or retained gameplay authority.

SPEC-02 is
`b1b81b9a3525a4b0220332f75187e33384bab8903fc092580efc2260c61a648d`;
fixture is
`eb8fb469f8f978696b746b12b07d84c163c28750db803f8ab9b75993d6728886`.
Fast, Oracle, 126 SPEC mutations, 45 player-weapon controls, 87 enemy
mutations, 184 native mutations, 20 scene mutations, 123 Target suppressions,
and both LiveEncounter Target profiles pass. The target runtime is 84,144
bytes inside the existing `0x19000` carve, leaving 18,256 bytes. Two
commit-bound 575-sample Emulator ledgers are byte-identical at normalized ISO
`2d4d93d2981cfc8fdf95820a9d47a457df413afc55ef2310c3a69200d3473c18`;
canonical samples remain
`2bb6c0321215d15d92b7a26a59e5a375b4bb9ea8ca003de93c6db8aba391e949`.

Window-only WGC source frames 2280..2310 pass direct inspection. Cadence
sheet `651383577cc72d80e9c9cae7a67790aee6a4a68046ec2611de1117f128273a3`
and clip `f0bdf52684d9d3fab1446f2a932fe26e8b67c094206b357b3b64fa7f0603f8a2`
preserve the frame-2287 projectile prefix, damage-free frame 2288, source
frame-2306 damage, natural frame-2307 class-`0x4e` impact, Predator/staff
identity, P1-only HUD, and both Coffee Shop planes, palette, and priority.
Frames 2750..2762 produce cadence sheet
`6e9920ede83450d18aa3ac2b975011d4229746717fdac7fb42cd0dfe64d0699c`
and clip `1e7230ea28a63567ca46b26eadc7d49ed6aa31ded66c51f4a9f4c1d69b6dc8c5`;
they preserve the health correction and expose the next player HIT-state/
presentation gap rather than hiding it.

Whole-scene gaps change from `308 / 1,253 / 3 / 94 / 3 / 281` to
`339 / 1,248 / 2 / 93 / 3 / 281`. Actor lifetimes increase by 31 because
the corrected damage/hitstop trajectory invalidates downstream false matches;
spawn/despawn improves by five, active states by one, and collision/damage by
one. The source capture is unchanged; route/camera and audio/load do not
increase. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero.

The next earliest causal divergence at that checkpoint was visible frame 2751
at player slot `0x00ff8380`: source entered HIT state `0x0202` after the
frame-2750 health write while native remained state `0x0200` with idle
animation `0x0015f1f4`.

Incremental checkpoint `b711281161305e5f193ef0b184bf0d9c9e5abc83`
closes the complete nonlethal player HIT body. Accepted evidence binds entry,
carried frame, eight-tick HIT presentation, sixteen-step shake, fixed-point
motion, return-to-control, and one-frame post-return invulnerability through
routines `0x1a96e`, `0x1a982`, `0x1aad0`, `0x1ab1a`, `0x1ab2c`, `0x1ab52`,
and `0x1abb8`; shake table `0x1aa90`; motion row 2 at `0x1f892`; and audio
command `0x003b`. Source and native player state, substate, position, facing,
animation, assembly, timer, health, and invulnerability are exact for visible
frames 2751..2778. Health remains owned solely by the accepted frame-2750
collision write.

SPEC-02 is
`45496c15cf6bef7176146e9530ffc6bc04bdb152c9892f3b7b1f10aeef97b5b7`;
fixture is
`15584fcaf6749b8f4be7240a91936c57154d898ec987854e6651e27916d8fa9d`.
Fast, Oracle, 15 Oracle-HIT mutations, 21 player-authority mutations, 127 SPEC
mutations, 189 native mutations, 123 Target suppressions, and both
LiveEncounter Target profiles pass. The exact SH-2 runtime is `0x148e0` bytes
inside the unchanged `0x19000` carve, leaving `0x4720` bytes.

Two commit-bound 575-sample Coffee Shop Emulator ledgers are byte-identical at
normalized ISO
`0e560acc57e0e16315114158f006c6d584599f772c771d1b9c37113347a54b6f`;
canonical samples remain
`2bb6c0321215d15d92b7a26a59e5a375b4bb9ea8ca003de93c6db8aba391e949`.
Window-only WGC frames 2750..2780 pass direct inspection. Cadence sheet
`4b16d25a9dfa674c97542859b1f567fc52fcb20e50fe6fc8bf06bd2b0d3ea929`
and clip
`82f492f003f7f6d17c79af293eb514f7dae33fc50674503d3d6f2bb1eac330bf`
preserve dark-Predator P1 identity, the separate source-owned white Major
actor, P1 weapon/resource presentation with the actual P2 slot hidden,
coherent HIT/return presentation, staff continuity, both Coffee Shop planes,
palette, and priority.

Whole-scene gaps remain `339 / 1,248 / 2 / 93 / 3 / 281`; no category
increases. Unowned Saturn actors, unidentified source pairs, and retained
gameplay authorities remain zero. The regenerated complete scene exposes an
earlier causal divergence at visible frame 2602: source player slot
`0x00ff8380` samples rightward input before its update and enters
`0x0200:0200`, facing 1, x `0x03b24000`, animation `0x0015f208`, assembly
`0x00160a02`, timer 4. Native remains one update late at `0x0200:0002`,
facing 0, x `0x03b00000`, idle `0x0015f1f4`. Bind the accepted controller and
player scheduler order plus the directional transition rule without
rebaselining input or adding a frame exception. Preserve the exact HIT body.

Incremental checkpoint `26f41cf0ff1b1abab0d19ef74be781ba0ff86ba4`
closes that controller/player update-order divergence and the complete twelve-
record Predator Warrior walk loop. Visible frame 2602 now matches source at
`0x0200:0200`, facing 1, x `0x03b24000`, record `0x0015f208`, assembly
`0x00160a02`, and timer 4; the fixed `0x24000` 16.16 movement delta and record
cadence remain exact. The Button1 body returns naturally to the source walk
entry at frame 2630 without an input rebaseline, frame exception, or authored
return delay. The accepted player HIT body at frames 2751..2778 is unchanged.

SPEC-02 is
`bb48c1976641d0afa01ed621c1dbbf9d71eac2337dd00ebf4da1e4f4fabc632f`;
fixture is
`03f2c96366fded74bb94e3bbf57883a8c967e18908d0eedb963ce85ef65afa5b`.
Fast, Oracle, 127 SPEC mutations, 198 native mutations, 20 scene mutations,
123 Target suppressions, and both LiveEncounter Target profiles pass. Exact
runtime size is `0x148e4` inside the `0x19000` carve, leaving `0x471c` bytes.
Two commit-bound 575-sample Emulator runs have byte-identical sample payload
`8d239f8a9187ad034c5793fa3eb932380f8784d6e761b51eec7d04b993747eb7`
at normalized ISO
`97be8a7019449f2e65066cc4416a6517f610c482a572d255be308e48cd57e9ee`.

Real window-only WGC covers every visible frame 2598..2633. Cadence sheet
`9525bf6e93004726d462f3e0b95d8e157e956fb7d685ff15651281222653a801`
and clip
`d15f9d2cb0a352c063092e70eee5f58048df0b7c985ddd2ea47d5d80288f5473`
pass direct inspection: source-bound P1 Predator presentation, the independent
intro actor, weapon-to-locomotion transition, P1-only HUD, both Coffee Shop
planes, palette, and priority remain coherent.

Whole-scene gaps improve from `339 / 1,248 / 2 / 93 / 3 / 281` to
`323 / 1,243 / 2 / 93 / 3 / 281`. No category increases. Unowned Saturn
actors, unidentified source pairs, and retained gameplay authorities remain
zero. The corrected trajectory exposes the next fixed-slot mismatch one frame
earlier (`2917 -> 2916`), but does not increase a gap category.

The next earliest causal divergence is player slot `0x00ff8380` at visible
frame 2602: source hurt selector is 0 while native still exposes selector 17.
Bind its accepted current-state collision-selector writer, transition guard,
reads/writes, and scheduler order. Do not add a frame/slot exception and do not
weaken the comparison. Preserve the corrected locomotion and HIT locks; the
next animation divergence remains visible frame 2612.

Incremental implementation checkpoint
`9d0181a730394a83f374ec5a1f43459c6dc80e92` closes the source controller
camera-edge transition at visible frame 2680. Accepted source routine
`0x028910..0x02895e` runs after the recurring-spawn body returns to the
controller dispatcher, predecrements field `0x46` when fields `0x48` and
`0x46` are nonzero, compares the pre-player-update camera x unsigned with 832,
then writes substate `0x0200`, bound/target 832, and progress snapshot 1. Native
uses the accepted previous-camera sample because its combined frame calls
player/camera before the fixed-pool controller. Source-write suppression
retries and changes downstream population. There is no fixed-frame substitute,
spawn suppression, authored delay, or input change.

SPEC-02 is
`9b16789689fca8d9c1c6b1b8db05f952822fbea011872d5b0c458ca1ca1d5c99`;
fixture is
`ea742cce53ba88baa3ae2e5669bee1b49c6c553c5735416f048ce7f60fb7489e`.
Fast, Oracle, 128 SPEC mutations, 201 native mutations, 20 scene mutations,
123 Target suppressions, and both LiveEncounter Target profiles pass. Exact
runtime size is `0x148e8` inside the `0x19000` carve, leaving `0x4718` bytes.
Two commit-bound 575-sample Emulator runs have byte-identical canonical payload
`d6ce01333843b273432e965efde266f8a95c53c195a910e41602cc103d9a71d9`,
VDP1 cache
`15235569ad91027a6f9cf6d00c5b88b9c13539895a9259036a1ecdde48ad6504`,
and normalized ISO
`0b3ef70519e125923ff4c5d2679d5dd3a498e698fff59ee58b19de2399c30b7f`.

Real window-only WGC covers every visible frame 2280..2310. Contact sheet
`651383577cc72d80e9c9cae7a67790aee6a4a68046ec2611de1117f128273a3a`
and clip
`f0bdf52684d9d3fab1446f2a932fe26e8b67c094206b357b3b64fa7f0603f8a2`
pass direct inspection: no premature hit is visible at frame 2288; frame-2306
damage and the natural frame-2307 class-`0x4e` impact evolve coherently; P1
remains the Predator; both Coffee Shop planes, palette, and priority remain
coherent.

Whole-scene gaps remain `323 / 1,243 / 2 / 93 / 3 / 281` before and after
this correction for actor lifetimes, spawn/despawn, active states,
collision/damage, route/camera, and audio/load. No category increases. Unowned
Saturn actors, unidentified source pairs, and retained gameplay authorities
remain zero. The controller mismatch at frame 2680 is closed. The next earliest
causal divergence is visible frame 2759: type-20/class-`0x09` slot
`0x00ffb480` carries native record `0x0006dc6a` versus source `0x0006dbda`,
while slot `0x00ffb500` carries native `0x0006dbda` versus source `0x0006dc6a`.
Bind the accepted spawn/update/presentation selection order without a frame or
slot exception, weakened identity comparison, or input-route change.

Incremental implementation checkpoint
`db03e92d74aa5310ab9c4931bcad71bbd2612245` closes the frame-2750
class-`0x1f` player-contact impact transaction. Accepted Oracle evidence binds
the natural type-24/class-`0x4e` variant-0 allocation at slot `0x00ffc300`:
visible frame 2751 position `1095,369,319`, facing 1, RNG
`0xeea3 -> 0xcb6e`, jitter `+4,+4`, retained presentation
`0x0007a12c/0x0007a3a0`, subsequent records
`0x000928e0/0x000928f0/0x00092900`, terminal state at 2761, and release at
2762. The source and native lifetime is exact. No fixed-frame allocation,
authored delay, projectile suppression, input change, or retained gameplay
authority was added.

SPEC-02 is
`6426ee3442ed459e74bfb3136c83589f9900d40589ac32f7beaf44a442153c3e`;
fixture is
`487ab920865c20ecafb054a31b17bc7af3ac2064956a63589d7bc90d3a5a5796`.
Fast, Oracle, 80 bounded-Oracle mutations, 132 SPEC mutations, 207 native
mutations, 20 scene mutations, 123 Target suppressions, and both LiveEncounter
Target profiles pass. Exact runtime size remains `0x148e8` inside the
unchanged `0x19000` carve, leaving `0x4718` bytes. Two 575-sample Emulator
runs are byte-identical at normalized ISO
`b3fc97654498a8f82636b3b0840476065f0cdcf24f32e757744ea69dccc0613a`,
canonical payload
`d6ce01333843b273432e965efde266f8a95c53c195a910e41602cc103d9a71d9`,
and VDP1 cache
`15235569ad91027a6f9cf6d00c5b88b9c13539895a9259036a1ecdde48ad6504`.

Fresh window-only WGC frames 2280..2310 retain cadence sheet
`651383577cc72d80e9c9cae7a67790aee6a4a68046ec2611de1117f128273a3a`
and clip
`f0bdf52684d9d3fab1446f2a932fe26e8b67c094206b357b3b64fa7f0603f8a2`.
Direct inspection preserves the damage-free frame 2288, natural frame-2306/
2307 damage-impact chronology, Predator/staff identity, P1-only HUD, and both
Coffee Shop planes, palette, and priority. A capture-only extended diagnostic
window records frames 2750..2762 at sheet
`1a13eb065987273f55175952b0ba4e22f85f47a1a48c215830407e9aa45cef1b`
and clip
`dd1b32a5934c84a63f87fa1e81d954fd7ffe042388d270d51227c02dcff1c498`;
the normal 575-sample limit was restored afterward.

Whole-scene gaps change from `323 / 1,243 / 2 / 93 / 3 / 281` to
`331 / 1,241 / 2 / 93 / 3 / 281`. The actor-lifetime increase of eight is
explained by the restored RNG consumption invalidating later false matches;
the corrected class-`0x4e` lifetime itself is exact, and spawn/despawn improves
by two. Unowned Saturn actors, unidentified source pairs, and retained gameplay
authorities remain zero.

The next earliest causal divergence is player slot `0x00ff8380` at visible
frame 2793: source hurt selector 1 versus native 0 in state `0x0200`, substate
`0x0802`. Bind the accepted current-state selector writer, guard, reads/writes,
and scheduler order without a frame exception, weakened comparison, or input
change. Preserve the exact impact/RNG, player HIT, HUD/audio, and rendering
locks. The next dependent divergence is class-`0x1f` slot `0x00ffa240` at
frame 2798, source substate `0x0404` versus native `0x0000`.

Incremental implementation checkpoint
`5b40fd75c41e36c1c3c344e53882df1ed129466b` binds the source class-`0x02`
current-animation step in state `0x0200`. At source frame 2074, native fixed
slot `0x00ffb600` now carries record `0x0006b66c` with timer 4094. A real
native mutation removes the step call and is rejected; no frame exception,
input change, authored delay, or retained gameplay authority was introduced.

The smallest bounded corrective Oracle consists of byte-identical `cs39a` and
`cs39b` captures. Their scene-actor, component-20 dispatch, progression-
transaction, and result identities match. Frames 2073..2077 call class-`0x02`
entry `0x06b534` at counts `1,1,2,2,1`, while recurring-controller entry
`0x0288e2` is called `0,1,3,1,1`. This proves recurring-controller cadence is
not a full-scheduler cadence proxy. The residual frame-2076 class-`0x02`
timer difference (native 4090, source 4091) is an exact diagnostic scheduler-
phase blocker. Do not undo the source-correct native step or add a gameplay
frame exception; unblock it only by binding per-phase scheduler invocation
ownership.

SPEC-02 is
`d0d7762ade3d0f1cbb986d6c1135172e24017515c73ce30ccc39ec24b4385710`;
fixture is
`bf5a207ae4f83fca8683ebf9a64e8c93f8cef1674b1a3ae9691464d58f8136af`.
Fast, Oracle, 80 bounded-Oracle mutations, 133 SPEC mutations, 209 native
mutations, 20 scene mutations, 123 Target suppressions, and both LiveEncounter
Target profiles pass. Exact runtime remains `0x148e8` bytes inside the
`0x19000` carve, leaving `0x4718`. Two 575-sample Coffee Shop Emulator runs
are byte-identical at normalized ISO
`949fbc89c4a6e5703d2af6d14e38d610631217da099004222da1175924fbfbe0`,
sample payload
`d6ce01333843b273432e965efde266f8a95c53c195a910e41602cc103d9a71d9`,
and VDP1 cache
`15235569ad91027a6f9cf6d00c5b88b9c13539895a9259036a1ecdde48ad6504`.

Real window-only WGC frames 2280..2310 pass direct inspection. Contact sheet
`43e803cd593e1eb9f10aeaf52c1791b86ef3ab735077102af4e05389a90a2e09`
and clip
`f0bdf52684d9d3fab1446f2a932fe26e8b67c094206b357b3b64fa7f0603f8a2`
preserve the damage-free frame 2288, natural frame-2306/2307 damage-impact
progression, Predator/staff identity, both Coffee Shop planes, palette, and
priority.

Whole-scene gaps remain `331 / 1,241 / 2 / 93 / 3 / 281` for actor
lifetimes, spawn/despawn, active states, collision/damage, route/camera, and
audio/load. No category increases. Unowned Saturn actors, unidentified source
pairs, and retained gameplay authorities remain zero. Continue the next
dependency-safe divergence at player slot `0x00ff8380`, frame 2239, where the
source animation timer is 4094 and native is 4095. Bind source player-animation
dispatch plus its scheduler phase, using the smallest bounded Oracle follow-up
only if accepted evidence lacks invocation ownership, then rerun the entire
Coffee Shop scene and return to the class-`0x02` phase blocker.

Incremental implementation checkpoint
`06500692bba48c724ca00436751e1f2b7597f8d3` closes that dependency-safe
player-animation body together with the source camera/stage activation sample,
Coffee Shop obstacle parent animation, class-`0x49` retained fixed-slot
presentation state, class-`0x4e` terminal timer order, and the exact Predator
Button1 presentation sequence. Source record activation now samples the
scheduler-visible prior camera position; the route-2 to route-4 handoff consumes
its first camera update exactly once. Real mutations reject the prior post-player
camera sample and the prior class-`0x4e` branch order.

SPEC-02 is
`6aa35860d5854c77fb54e5174659a1cf546defdfb703d734b2f617276a0872b1`;
fixture is
`94a9a551fa08a5f28174906436e8c38f45fc877779aa50c84aa294a77b59c313`.
Fast, Oracle, 80 bounded-Oracle mutations, 133 SPEC mutations, 209 native
mutations, 20 scene mutations, 123 Target suppressions, and both LiveEncounter
Target profiles pass. Two 575-sample Coffee Shop Emulator runs are
byte-identical at normalized ISO
`4c3a2014cfb3b1d542a3c871b6920f37dd770e4e4906c1a5c7e23341a0552313`
and VDP1 cache
`15235569ad91027a6f9cf6d00c5b88b9c13539895a9259036a1ecdde48ad6504`;
five chronology/cache mutations are rejected.

Fresh real window-only WGC covers source-visible frames 2280..2310. Contact
sheet
`651383577cc72d80e9c9cae7a67790aee6a4a68046ec2611de1117f128273a3a`
and clip
`f0bdf52684d9d3fab1446f2a932fe26e8b67c094206b357b3b64fa7f0603f8a2`
pass direct inspection. Frame 2288 remains damage-free, frame 2306 carries the
accepted slot-`0x00ff8880` attack-`0x030cd2` damage write, frame 2307 carries
the natural class-`0x4e` impact, Predator and Major remain distinct source-scene
actors, and the two Coffee Shop planes, palette, and priority remain intact.
The second `WARRIOR` HUD line is the Predator weapon/resource meter, not an
active P2 slot.

Whole-scene gaps improve from `331 / 1,241 / 2 / 93 / 3 / 281` to
`327 / 1,234 / 2 / 93 / 3 / 281` for actor lifetimes, spawn/despawn, active
states, collision/damage, route/camera, and audio/load. No category increases.
Unowned Saturn actors, unidentified source pairs, and retained gameplay
authorities remain zero.

The earliest remaining causal divergence is class-`0x02` slot `0x00ffb600`
at visible frame 2076: native animation timer 4090 versus source 4091. The next
is class-`0x02` slot `0x00ffb300` at frame 2619: native 4094 versus source
4095. Bind the accepted source per-phase scheduler invocation order, using only
the smallest bounded Oracle follow-up needed to identify the owning phase or
caller. Do not add a frame/slot exception, use recurring-controller cadence as
a full-scheduler proxy, weaken identity comparison, or change the input route.

## Paused WIP evidence checkpoint

The current unaccepted WIP fixes the phase-exclusive HIT/KO scratch alias and
partially closes the class-`0x1f` inner-8 action-`0x04` dispatcher. HIT recovery
now requires the accepted exact reaction kind/state pairs, so the shared
`source_motion_fields[4]` action-`0x0c` plan cannot fabricate a HIT reaction.
The action-`0x04` program now performs its player-proximity test first, uses the
exact final action-2 guard, clears the action, and steps the movement helper once
in the same scheduler visit. The Coffee Shop terrain program includes the full
4096-entry selector map and exact selector-4/20 branch arithmetic.

This closes the frame-3524 slot-`0x00ffa3c0` animation mismatch: source and
native now use record `0x0012d4f8`, timer 5, with identical RNG through frame
3525. The next earliest causal divergence is frame 3525 at that same slot:
source uses record `0x0012d488`, native uses `0x0012d50c`, because the native
wander-direction helper has not yet bound the source scheduler-visible
`a5+0x278`/`a5+0x27c` target origin used by routine `0x041c36`.

Oracle enemy analysis and tests pass with 104 mutations. SPEC-02 build,
generation, and tests pass with 156 mutations. The contract SHA is
`43e16c1e3d6a233f7a86703aa68e546e4a2b3be69b5ce7d6f264f9b5b587c288`;
the fixture SHA is
`dd9126f34d9e4ee141239eee907a1405d8561da2cb1d7ebadf66e53a08e8fecd`.
The program checkpoint is not accepted: the full host lane fails at frame 1757
with code 15, slot `0x00ffa000`, state/substate `0x0208:0x0c04`, and the scene
capture fails at native frame 3653 with code 29. Target, Emulator, and WGC were
therefore not run. The prior completed scene census is retained but is not a
current WIP recapture.

The prior single-divergence resume experiment is superseded by the execution
plan amendment below. The live chaptered resume prompt is maintained in
`docs/AGENT_HANDOFF.md`; it applies this amendment starting at the frame-3525
wander-origin fix and the frame-1757 host-lane classification.

Pause addendum (read-only source mapping, 2026-08-30): decrypted-opcode
inspection proves that routine `0x041c36` reads signed 16-bit camera position
X at `0x041cb0` from `a5+0x278` and Z at `0x041cb8` from `a5+0x27c`, then adds
the actor's `+0x60`/`+0x62` offsets before calling `0x016484`. Accepted camera
evidence binds source writers `0x0b04ca`/`0x0b06fa` for X and
`0x0b04f4`/`0x0b081c` for Z, and establishes that this scheduler sample
precedes the same-frame player/camera update. The next implementation step is
therefore the existing globals-table fixture plus native pre-update X/Z
binding and a current-sample negative control. No runtime, fixture, capture,
lane, or acceptance state changed during this mapping.

## Execution plan amendment (2026-08-30)

Owner-approved amendment to this card's execution method. Evidence standards
are unchanged: earliest-causal-divergence selection, exact RNG call order,
two-run identity for any new capture, real per-branch mutations, no frame/slot
exceptions, no fixed-frame/counter/presentation authority, and every accepted
lock. Only granularity, spec-completion strategy, ceremony frequency, and
recording change:

- A body is a whole routine program, actor-class family, or segment, per this
  card's own body definition under "Focused machine checks" — never a single
  observed branch or timer tick. When a divergence lands inside a dispatcher,
  the body is the complete route-reachable program family containing it.
- Complete the remaining SPEC-02 executable semantics in batches per actor
  class: decode the bounded route-reachable routine set from the decrypted
  opcode image and validate the decoded semantics against the existing
  byte-identical capture ledgers (`cs50a/cs50b` and predecessors). Run a new
  bounded Oracle capture only when the existing ledgers cannot witness the
  behavior. Amend SPEC-02 and regenerate fixtures once per family, not per
  branch. The reachable action set is exactly the one enumerated by the
  accepted ORACLE-11 contracts; nothing outside it.
- Emit the scheduler-visible `a5`-relative globals table (address, width,
  writers, readers, semantic owner) for Round-1-reachable routines as a
  SPEC-02 fixture, derived from the accepted 1,517-PC writer reconciliation by
  extending an existing analyzer. Native code reads source globals only
  through that table.
- Ceremony per granularity: focused host differential and fixture validation
  per step; real mutations, Target, one pinned scene capture, and the complete
  Coffee Shop census once per body; paired Emulator and WGC at the body
  boundary when the census is green or strictly improved. The full census is
  never rerun for an intermediate branch.
- Recording: one checkpoint entry in this card per body (counters, hashes,
  next resume line); `project_state.yaml` keeps pointers and counters;
  `docs/AGENT_HANDOFF.md` keeps only the active-checkpoint summary and the
  live resume prompt. Do not duplicate evidence prose across the three
  documents.
- Do not build a general lifter or translator, a new capture framework, new
  dashboards, or parallel worktree orchestration under this amendment.

## Paused scheduler-globals checkpoint (2026-08-31)

The existing navigation/SPEC pipeline now emits and validates the two signed
scheduler-visible camera globals consumed by class-`0x1f` routine `0x041c36`:
X at `a5+0x0278` and Z at `a5+0x027c`, including their exact absolute
addresses, source readers, four source writers, widths, ownership, and native
pre-update bindings. Native wander reads both fields only through the generated
table; camera stepping preserves pre-update X and Z without changing the render
camera. The current-Sample X mutation and the action-`0x0c` zero-timer shortcut
mutation are rejected.

Focused Oracle navigation passes with 37 mutations. SPEC-02 passes with 46
fields and 158 mutations. Contract SHA is
`6eb601e055bf9a59aaf7c1a10fea2cae1a351ca49324b22285c5faa82f30f60a`;
fixture SHA is
`bf1b080ddd8c045884b194f3ac0d4975d9888f746d3fec2bb512214a21313fec`.

This remains unaccepted WIP. The full host lane fails at frame 1757/code 15,
slot `0x00ffa000`, state/substate `0x0208:0x0c04`, action timer 0 and source
stage parameter 8. The accepted action-`0x0c` phase-2 timer table requires the
Coffee Shop transition to stage parameter 9. Its exact source writer, guard,
scheduler phase, reads, and writes are not yet bound. Do not substitute a
constant-9 initialization or a frame/slot exception. Target, scene census,
Emulator, and WGC remain deferred at this red intermediate boundary.

Resume by binding that smallest source-owned stage-parameter transition from
accepted Oracle/writer evidence, using a bounded corrective Oracle only if the
required implementation fields are genuinely absent. Amend the existing
SPEC-02 fixture, add a real wrong-transition mutation, and rerun focused lanes
plus full host. Then require frame 3525 slot `0x00ffa3c0` record `0x0012d488`
with unchanged RNG and finish the complete route-reachable class-`0x1f`
program family before its body-boundary Target/scene/Emulator/WGC ceremony.

### Pause handoff addendum: source stage-progress program mapped

Read-only accepted-evidence inspection closes the previously missing source
provenance without a new capture. Predator Button1 routine `0x024060` loads
D0=3 at `0x024094` and calls `0x0179e2` at `0x024096`. When
`a5+0x01b0:u8 == 0`, the helper adds D0 to `a5+0x0226:u16`, derives a
single carry from threshold 8, masks the accumulator with 7, adds the carry to
`a5+0x01ea:s16`, applies the signed zero/31 domain clamp and 5-bit mask, then
the Coffee Shop 8..16 route bounds. The accepted byte-identical route A/B
ledgers show Coffee Shop calls at frames 2252, 2342, and 2432 progressing
`0->3`, `3->6`, and `6->9->1`; the third call changes stage 8 to 9. The
source stage setup at frame 2072 remains 8.

This is mapping only: Oracle/SPEC/native artifacts and lane status are
unchanged. Resume by amending the existing Predator weapon contract and
SPEC-02 fixture for the complete route-reachable helper program, generating
its native table/state, binding its source action-entry scheduler phase, and
adding wrong-delta, wrong-threshold, and wrong-timing mutations. No direct
stage-9 assignment, initialization change, frame/slot exception, or bounded
Oracle recapture is justified by the currently accepted evidence.

### Paused Button1 stage-progress implementation checkpoint (2026-08-31)

The complete route-reachable helper is now represented in the existing
Predator weapon Oracle artifact, SPEC-02, generated fixture/header, and native
runtime. The bound source contract includes caller `0x024094..0x024096`, helper
`0x0179e2..0x017b74`, the exact guard and five global fields, signedness,
arithmetic and branch order, Coffee Shop bounds, 15 accepted route calls, no
RNG, and action-entry scheduler ordering. The SPEC builder now regenerates the
already accepted empty-resource entry projection instead of dropping it.

Oracle player-weapon validation passes with 56 mutations. SPEC-02 passes with
47 fields and 162 mutations; contract SHA is
`37f8429a44a3d545b12d8242b0c8ab829e9ae2795cc1efa17f280fef7a9f6889`
and fixture SHA is
`a151d33a9174710d353a52a1933b63ab459856d3c602f047ca211d786f50ce31`.
The generator check passes. Native baseline compilation reaches the existing
Coffee Shop differential but remains RED at scheduler frame 1757/code 15,
slot `0x00ffa000`: stage 11, accumulator 0, eight helper calls, three carries,
22 total weapon entries, RNG `0x1908`.

The accepted source route has seven helper calls before the frame-3525
class-`0x1f` comparison and its eighth only at source frame 3827. The exact
next body is therefore the sufficient-Button1 call edge or source-update
cadence, not the proven helper arithmetic. Locate the first extra native call
against source frames 2252/2342/2432/2882/2927/3332/3377/3827 and repair its
owning input/action/recovery transition. Do not assign a stage constant, change
the helper arithmetic, add a frame/slot exception, weaken the differential, or
rebaseline the input. Native mutation execution, Target, scene census,
Emulator, and WGC remain deferred at this red WIP boundary.

### Paused Button1 action-dispatch chronology checkpoint (2026-08-31)

A focused native chronology assertion now checks cumulative helper calls against
all 15 accepted source call frames. It moves the first causal mismatch forward
from the later frame-3525 class-`0x1f` comparison to source frame 2251:
expected calls 0, native calls 1, input `0x0010`, source/class-`0x02` updates
1/1, weapon active 1, weapon tick 1, source action `0x0c00`, progress 3, stage
8. Accepted chronology captures physical Button1 at frame 2250, exposes the
native one-update input pipeline at frame 2251, and first exposes source action
`0x0c00` plus helper `0x0179e2` at frame 2252. The owning defect is therefore
the native begin-and-step-in-one-visit boundary, not the helper arithmetic.

This checkpoint is intentionally RED and unaccepted. The exact resume body is
to add the implementation-required one-update action-dispatch delay to the
existing Oracle/SPEC source-input contract from accepted evidence, regenerate
the existing fixture/native table, and defer the first weapon action step and
projection by one player update for both sufficient and empty Button1. Preserve
the begin-update locomotion presentation and source-owned motion hold. Add a
wrong-dispatch-delay mutation and keep the committed chronology assertion. Do
not add a frame exception, change helper arithmetic, or promote the accepted
runtime candidate. Target, census, Emulator, and WGC remain deferred until the
complete class-family/body boundary.

### Paused Button1 chronology correction and class-0x1f lifetime checkpoint (2026-08-31)

The accepted source-input chronology is now represented end to end as
`action_dispatch_delay_updates_u8 = 1`. Oracle, SPEC-02, the generated fixture
and header, and native runtime defer the sufficient/empty Button1 action step,
projection, and stage helper from pipeline frame 2251 to source-visible frame
2252. The begin update retains locomotion presentation and motion hold without
advancing the direction-history queue. Oracle passes 57 mutations, SPEC-02
passes 163 mutations, and the generator is current. Contract SHA is
`59ff3a9922e0b65617bf3cfeb0cb460134491a6d5f97ca8f163d12e11f4e8279`;
fixture SHA is
`15aff4079e2690936ccd4346ee3f28d01698c9e2f5080bc0ca5eed6fabffb84e`.

The focused/full Coffee Shop host differential remains intentionally RED and
now fails earlier and more causally at source frame 2511. The accepted scene
manifest requires record-type-12/class-`0x1f` slot `0x00ffa3c0` to be active
from frame 2511 through 3975; native has no matching actor at its first frame.
This missing lifetime is upstream of the absent inner-state
`0x0208:0x0e02` type-16 effects at 3253/3258/3263, attack-record `0x03589e`
damage at 3263, and player HIT at 3264. The next body is the complete source
spawn/scheduler program owning this actor and all Coffee Shop-reachable
instances/branches, not a frame, slot, or downstream damage patch. Target,
scene census, Emulator, and WGC remain deferred at this red intermediate
boundary. The exact continuation is in `docs/AGENT_HANDOFF.md`.

### Paused class-0x1f terminal-lifecycle diagnosis (2026-08-31)

The frame-2511 absence of recurring slot `0x00ffa3c0` is not a missing spawn
program. The accepted recurring controller `0x0288e2`, writers `0x028a3e` and
`0x028b7e`, guard, and pool allocation are already implemented. Mirroring the
accepted source/class-`0x02` phase cadence in the focused host leaves the same
failure: native has living count 8 because slot `0x00ffa180` remains active at
frame 2511 in `0x0202:0x020a`, record `0x0012de78`, health 56. Source owns this
actor through frame 2415 with its despawn edge at 2416; state `0x0600:0x0000`
must decrement the encounter living count and release it. Its missing terminal
transition/release is therefore the first known causal gap and blocks the
otherwise-natural `0x00ffa3c0` allocation.

The focused/full host remains intentionally RED, return 116. Added diagnostics
report source cadence, encounter spawn/living counters, active class-`0x1f`
actors, and the `0x00ffa180` active edge. The next experiment is to trace that
actor's state/substate/record changes over frames 2306-2416, bind the first
departure against the accepted HIT/KO/normal-return/release contract, and
correct the complete owning program or missing harness phase. No fixed-frame
release/spawn, actor-limit change, slot substitution, or downstream damage
patch is permitted. Target, census, Emulator, and WGC remain deferred at this
RED intermediate boundary.

### Paused record-type-4 same-update collision diagnosis (2026-08-31)

Targeted source/native transition and RNG diagnostics correct the preceding
terminal-lifecycle hypothesis. Source record-type-4/class-`0x04` slot
`0x00ff8880`, attack record `0x030cd2`, damages class-`0x1f` slot
`0x00ffa180` during scheduler frame 2306. Source therefore exposes the outer
HIT state at frame 2307 and reaches normal return at 2413, release state
`0x0600:0x0000` at 2415, and despawn at 2416. Native allocates the child during
processing frame 2306 but leaves collision registration pending until the next
scheduler update, making every visible HIT substate one frame late.

The phase error changes source-owned RNG consumption. Source frame 2377 gives
`0x00ffa180` call `0xedd9 -> 0xc9a2`, low nibble 2, hold timer 10, then gives
`0x00ffa300` call `0xc9a2 -> 0x5cfe`. Native lets `0x00ffa300` consume the first
call and makes `0x00ffa180` consume the second one update late, selecting hold
timer 120. The stale frame-2511 lifetime and blocked `0x00ffa3c0` allocation are
downstream; the RNG algorithm, terminal predicate, recurring controller, and
actor limit are not the first defect.

A diagnostic experiment moving all record-type-4 collisions before all
record-type-12 updates broke the delayed-parent collision control and was
restored. The complete owning body is the Coffee Shop-reachable same-update
child allocation, registration, current-state collision, and reaction-dispatch
scheduler rule. Resume from `docs/AGENT_HANDOFF.md`; add a mutation rejecting a
one-update child deferral and require the exact 2288/2306/2307 chronology,
frame-2377 RNG ordering, natural 2416 release, and natural frame-2511 recurring
allocation. Focused/full host remains intentionally RED, return 116. Target,
scene census, Emulator, and WGC remain deferred.

### Pause correction: parent allocation is the earliest phase defect (2026-08-31)

The pause audit corrects the preceding same-update-collision diagnosis. The
accepted fixture explicitly requires a newly initialized record-type-4 child
to receive identity immediately but enter the attacker list on the next source
scheduler invocation. Slot `0x00ff8880` receives identity at frame 2305 and is
visible and collision-eligible at 2306, so `collision_registration_pending =
1` is source-correct.

The earliest mismatch is instead the parent lifetime. Source parent
`0x00ff8680` receives identity at 2253, is first visible at 2254, reaches its
last state-2 position at 2286, enters `0x0400` at 2287, and exposes its first
child at 2288. Native is one visible frame late throughout that trajectory.
The existing accepted fixture value `parent_allocation_tick = 2` conflicts
with action entry at 2252 and the accepted writer/visibility chronology; the
source-required value is tick 1.

Resume by amending only that field through the existing Oracle/SPEC/generated
native pipeline, emitting it in the native weapon table, and adding a real
mutation that defers allocation back to tick 2. Preserve the one-update action
dispatch and next-invocation child registration. Require the aligned parent
and child trajectory, natural frame-2306 damage and frame-2307 impact/HIT,
frame-2377 RNG ownership, frame-2416 release, and frame-2511 recurring spawn
before body-boundary lanes. No new Oracle capture is required unless the
accepted evidence proves insufficient. Focused/full host remains intentionally
RED, return 116; Target, census, Emulator, and WGC remain deferred.

### Paused parent-allocation timing correction (2026-08-31)

The accepted parent chronology is now executable through the existing Oracle,
SPEC-02, generated-header, native-table, and mutation pipeline. Parent
allocation is tick 1; Button1 dispatch remains delayed one update and child
collision registration remains next-invocation. Oracle passes 57 mutations,
SPEC-02 passes 164 mutations, the generated header is current, and the focused
host lane rejects a real tick-2 deferral. Contract SHA is
`8460d848dbe75564bbea988a585e44e7261f9799e9464f98f86b19ba1fad56de`;
fixture SHA is
`7d85d8c85f8b48ba1713acd49e578382c0226f13cd42abd34adea5fc40c7ffe5`.

The full host differential now passes the parent/child, frame-2306 collision,
frame-2307 impact/HIT, frame-2377 RNG ownership, frame-2416 release, and natural
frame-2511 recurring-allocation chain. It advances to return 117 at source
frame 2680: source enters recurring-controller substate `0x0200`, snapshots
progress 1, and sets camera bound 832 while native still sees the prior camera
sample 830 and remains in substate `0x0000` with bound 640. The next body is the
complete source controller program and its scheduler-visible camera sample,
not a frame exception. Target was attempted but stopped at the VDP1
actor-working-set budget guard; Emulator, census, and WGC remain unclaimed.

### Paused recurring-controller current-camera checkpoint (2026-08-31)

The Coffee Shop recurring-controller program at source routine
`0x028910..0x02895e` is now bound through the existing Oracle, SPEC-02,
generated-header, native-table, and mutation path. Source writer frame 2679
reads current camera position 832; previous camera position 830 is an explicit
rejected sample. Native uses the generated ownership field for both the target
and camera-edge guard. The separate class-`0x1f` previous-camera presentation
binding remains unchanged.

Oracle encounter validation passes with 94 segments, 14 edges, 609
route-writer transactions, 56 spawns, and zero orphan authority. SPEC-02 passes
165 mutations. Contract SHA is
`4f593a2628eb35042d995addb633d1bb88cfc74226c1cd894ebea2efa1b57f36`;
fixture SHA is
`4e4b3706666430fe2caacaeaadfcba3f31c76463f46f5fa1d948c3a44d72e616`.
The generated header is current and the focused controller-edge lane passes
two real mutations, including the wrong previous-camera sample.

Target `LiveEncounterBench` BUILD_ONLY passes. The measured
`AvspRound1Runtime` size is `0x173b8` inside the unchanged `0x19000` arena,
leaving `0x1c48` bytes headroom. ISO SHA is
`4566957f85ac53b770f3c34e809503b3cc33baa188a9dab4eab0bf75be9e14f6`.

The full host differential no longer returns 117 at source frame 2680. It
advances to intentional return 94 at source frame 3827 for class-`0x1f` slot
`0x00ffa000`, state `0x0208`, action/substate `0x0c04`. The next body is the
complete Coffee Shop-reachable inner-state-`0x08` action-`0x0c` program,
including phase-4 cursor/selector handling, immediate phase-0 re-entry, audio
entry ownership, and phase-exclusive scratch semantics for slots
`0x00ffa000`, `0x00ff9e80`, and `0x00ff9dc0`. It is a high-fan-out,
gameplay-authoritative class-`0x1f` program reused later in Round 1.

At this boundary the proven unresolved metrics are one source program, zero
scene/encounter controllers, one actor class, zero audio owners, and zero load
owners. The raw scene-gap counters remain the last completed 327 actor-lifetime,
1234 spawn/despawn, 2 active-state, 93 collision/damage, 3 route/camera, and
281 audio/load rows; no current census claim is made. Paired Emulator, full
census, and WGC remain deferred at this intentional RED next-program boundary.

## Next eligible cards

### Paused class-0x1F action-0x0C timer-table checkpoint (2026-08-31)

The Coffee Shop-reachable class-`0x1f` inner-state-`0x08`, action-`0x0c`
timer-selection boundary is now executable through the existing Oracle,
SPEC-02, generated-header, native-table, and mutation pipeline. The prior
native fixed-stage-9 guard is rejected. Accepted decrypted program bytes bind
the complete five-row by 32-column timer table at `0x0bc55a..0x0bc5fa` and
the stage-offset selector at `0x0bc53a..0x0bc55a`; stage 11 selects row 1,
consumes one source RNG value, and indexes it by `rng & 31`.

The focused action-`0x0c` lane passes one discriminating fixed-stage mutation,
Oracle enemy validation passes 104 mutations, SPEC-02 passes 167 mutations,
and the generated header is current. Contract SHA is
`790da00bd00deacf085fef6426cea606587355b3f828fbdbf72cd753f059840a`;
fixture SHA is
`42ec4f39a49a565c958924866ebac8d03f365ae283f499ee06d660ab03f1045e`.
Target `LiveEncounterBench` BUILD_ONLY passes; ISO SHA is
`0bc362062eea3cc4c7b2e15ceee0a7c1b9c04b5123956a9cc3192b6c445862f1`.
The combat overlay remains byte-identical at 126 tiles/16712 bytes with SHA
`171f0dfa25d8a1fe94d2889f89c78e71bd3b1cfffa9fd5ff11964b1fc23815fe`.

The full host differential advances past the old return-94/frame-3827 boundary
to intentional return 123 at source frame 4052. Source player slot
`0x00ff8380` enters HIT state `0x0202` at frame 4007, returns to outer state
`0x0200`/substate `0x0e00` at frame 4032, and accepts Button1 into substate
`0x0c00` at frame 4052. Native remains in source action/state `0x0202` and is
one stage-progress call behind. The next owning body is the complete Predator
Warrior HIT/return-to-control/action-entry program. Paired Emulator, complete
scene census, and WGC remain deferred at this intentional next-program
boundary.

### Paused shared Button1 entry-projection correction (2026-08-31)

Fresh source/native comparison corrects the preceding frame-4052 hypothesis.
Native had completed only one of five source player HITs, so the later stuck-HIT
appearance was downstream. The earliest player mismatch is source frame 2252:
source exposes sufficient Button1 entry `0x0c00` there and active `0x0c02` at
2253, while native was one visible frame late. The empty-resource path has the
same defect at source frames 2522-2523. The accepted SPEC-02 fixture already
binds physical edge 2250, one input-pipeline update, immediate entry-action
projection, active presentation on the following update, tick-1
stage/resource/parent operations, parent visibility 2254, and empty-effect
visibility 2523.

The paused implementation now begins the shared weapon program at tick 1,
projects only the sufficient/empty entry action while preserving entry
presentation, retains the one-update dispatch hold as action ownership, emits
and validates `resource_debit_tick`, applies the dispatch offset to
stage-progress/resource/parent operations, and moves empty-effect allocation
after the hold. The generated header check passes. Direct focused expectations
are aligned to the accepted entry, active, and directional-return sequence.

The host differential is intentionally RED with return 117 at source frame
2679, where the existing controller-edge check reports controller substate
`0x0200`, progress snapshot 1, bound 832, current camera 832, previous camera
830, and living count 8. The bounded comparison recorded below subsequently
classified this as a real scheduler-phase defect, not a stale assertion. Do not
change its frame without accepted source evidence. Oracle, SPEC mutation,
Target, Emulator, complete census, and WGC remain deferred at this RED
checkpoint. The exact continuation is in `docs/AGENT_HANDOFF.md`.

### Paused recurring-controller scheduler-phase diagnosis (2026-08-31)

The frame-2679 precheck is not stale. A bounded source/native trace proves
identical player and camera chronology through the edge: frames 2677, 2678,
and 2679 use camera 828, 830, and 832 with player X `0x04328000`,
`0x0434c000`, and `0x04370000`. Source controller substate remains 0 at frame
2679 and becomes `0x0200` with progress snapshot 1 and bound 832 at frame 2680;
native exposes the same writes one visible frame early at 2679.

The owning defect is the native orchestration boundary. The accepted fixture
orders the recurring entry controller before player update and before fixed
actor pools. Production and both full-scene host paths currently update the
player before a combined scheduler that contains the controller, fixed pools,
and collision. Resume by splitting the existing scheduler into a pre-player
recurring-controller phase and a post-player fixed-pool/current-state-collision
phase, then update production and scene harness call order. Preserve combined
focused-call compatibility where useful. Add a mutation rejecting post-player
controller execution. Do not change the accepted current-camera sample, move
the expected edge, or add a frame delay. After the frame-2679/2680 invariant
passes naturally, complete the pending Button1 timing mutations and required
generator, focused differential, fixture, Oracle, and Target lanes before
regenerating the scene census. No acceptance or candidate promotion is claimed
at this paused RED checkpoint.

### Paused scheduler-phase implementation and player-action diagnosis (2026-08-31)

The recurring-controller scheduler-phase defect is corrected through one
reusable orchestration boundary. Production and both full-scene host paths now
execute entry, pre-player recurring controller, player, then post-player fixed
pools and current-state collision. Combined APIs remain for focused callers,
and collision snapshotting remains post-player. A real mutation moves the
controller after the player and recreates return 117. The focused controller
lane passes three real mutations.

The shared sufficient/empty Button1 program is also locked with eight real
timing mutations covering tick-1 entry, one-update dispatch hold, immediate
entry-action projection, stage/resource/parent dispatch offsets, post-hold
empty-effect allocation, and generated `resource_debit_tick`. The generator
check passes and SPEC-02 passes 167 mutations. Target `LiveEncounterBench`
BUILD_ONLY passes with GAME.BIN 411136 bytes, BSS end `0x060be4c0`, and ISO
member SHA-256
`1f02795e3fed11bc6dab75ccf394400edf2260d313bed7355b7c33438b28f018`.

Oracle now advances beyond frame 2679 but remains RED at the later return-123
frame-4052 stage-progress mismatch; it is not accepted. A fresh full Coffee
Shop census exposes an earlier causal failure at native frame 3653, scheduler
code 29. Source is executing Predator Warrior state `0x0204`,
substate/action `0x0600` at frames 3650-3654 while native remains walking in
`0x0200/0x0202`. The code-29 class-`0x1f` player-collision failure is therefore
downstream until the earlier player action/input chronology is reconciled.

Resume by comparing the existing source/native scene TSVs from the accepted
empty-Button1 anchor at frames 2522-2523 through frame 3653, using the existing
capture-tool parsers. Identify and close the earliest reusable Predator Warrior
action/input program divergence, not the isolated collision row. Do not suppress
collision, add a delay, or rebaseline input. Paired Emulator and WGC remain
unclaimed at this RED checkpoint; the accepted runtime candidate remains
`d04a65a2253175c6e820140feefc35419e2cca07`.

- `QA-13-ROUND1-END-TO-END-DIFFERENTIAL` after the complete stable Round 2
  handoff candidate is committed and frozen.

### Paused player HIT-to-control fixed-point checkpoint (2026-08-31)

Runtime checkpoint `5d09b9b` closes the Coffee Shop-reachable type-16 player
HIT and return-to-control fractional-position boundary without changing the
accepted runtime candidate. HIT entry now preserves the actor's signed 16.16 X;
global-bound clamping preserves its low word, while obstacle/terrain ownership
clears it. Normal control applies its measured delta to the inherited source
position instead of rebuilding an absolute position from the twentieths input
adapter. The focused player-HIT lane passes nine real mutations, the generated
SPEC fixture check passes, and `LiveEncounterBench` Target BUILD_ONLY passes
with GAME.BIN 411488 bytes and ISO member SHA-256
`a41feb01186d6b7f630656e865f2235d4688c8a0b33d0d3463827d0dd59bf911`.

The full census, Emulator, and WGC remain unaccepted/unrun after this change.
Resume by regenerating the census, proving the first player-position mismatch
moves beyond frame 3314, then closing the contextual Button2 `0x1400/0x1402`
program at source frames 3410-3416 from accepted Oracle/SPEC evidence. The
complete instructions remain in `docs/AGENT_HANDOFF.md`.

### Contextual Button2 and exact Coffee Shop Button3 checkpoint (2026-08-31)

The contextual Button2 program is now bound through its source target-context
guard, `0x1400/0x1402` transition, records `0x160288..0x1602c8`, selectors
21/20, movement, collision, exit, and eight real mutations. The shared Button1
fractional-position latch is preserved and its focused lane passes nine real
mutations.

The normal right-facing Coffee Shop Button3 route is executable from the
accepted Oracle/SPEC trace: physical input frame 3440, pipeline edge 3441,
dispatch 3442, active air 3444, landing 3482, and neutral 3484. Native consumes
generated timing and selector values, performs the source signed 16.16 arc,
preserves the landing low word, and returns with the source neutral timer and
branch. The jump lane passes 11 real mutations. Oracle and SPEC analyzers plus
the generated-header check pass.

Target `LiveEncounterBench` BUILD_ONLY passes with GAME.BIN 402704 bytes, BSS
end `0x060bc390`, and ISO `/GAME.BIN` SHA-256
`8cf0f975f6ca4f7ac62795e3dd193dd1ce5e0dfc92edacacf04a6cfe76ce4e3b`.
The combat overlay is byte-identical at SHA-256
`171f0dfa25d8a1fe94d2889f89c78e71bd3b1cfffa9fd5ff11964b1fc23815fe`.

The full Coffee Shop scene remains intentionally RED at the later scheduler
code-29 boundary. The corrected player state, action, animation, and signed
16.16 position match the source through frame 3529. The next earliest causal
divergence is frame 3530: source advances to X `0x04a2d000`, while native stays
globally clamped at X high word `0x04a0`. Resume by comparing source/native
camera chronology and closing the owning reusable global-bounds/camera phase
program across all Coffee Shop-reachable branches. Do not add a frame-specific
exception, authored delay, or guessed unlock. Paired cold Emulator, complete
scene acceptance, and full WGC remain unclaimed.

### Type-16 current-hurt-selector checkpoint (2026-08-31)

The complete scene exposed a fabricated native type-16 player hit at visible
frame 3878. Accepted source contacts at frames 3263 and 3855 both require the
current player hurt selector 17; the frame-3878 player record has selector 0.
The auxiliary Oracle/SPEC/generated/native path now binds and enforces selector
17, with a negative mutation for the prior fixed-box behavior. The false hit is
gone while the legitimate frame-3877 HIT, frame-3878 special entry, frame-3891
selector-11 contact, and class-`0x1f` special-KO release through frame 4002 are
unchanged. The focused lane passes nine real mutations.

The SPEC fingerprint sentinel was refreshed without changing the 126-tile,
16712-byte combat overlay (`171f0dfa25d8a1fe94d2889f89c78e71bd3b1cfffa9fd5ff11964b1fc23815fe`).
The 4096-byte source terrain selector map is now represented in Target data by
383 deterministic runs and reconstructed exactly at initialization. Target
`LiveEncounterBench` BUILD_ONLY passes with GAME.BIN 417840 bytes and BSS end
`0x060bfef0`, preserving JO_MAX_SPRITE 255 and the existing memory carve.

The scene remains intentionally RED. The earliest newly exposed causal gap is
the complete Coffee Shop-reachable record-type-20/class-`0x05` program: source
slots `0x00ffb180` and `0x00ffb280` enter at frame 2673; `0x00ffb280` receives
the frame-3891 special contact, consumes source RNG, transitions through
`0x0200/0x0400/0x0402/0x0404/0x0604`, allocates the second class-`0x4e`
variant-1 impact at `0x00ffc200`, and releases at frame 3931. Native omission
leaves RNG two calls behind and causes the later class-`0x1f` action/collision
divergence. Close this whole reusable program from existing evidence, using only
the smallest bounded MAME Oracle follow-up if exact implementation fields are
absent. Fast and Oracle pass every preceding check and stop at the intentional
full-host frame-3782 stage-progress mismatch (eight native calls versus seven
source calls). Paired Emulator, complete census acceptance, and WGC remain
unclaimed.

### Coffee Shop record-type-20/class-0x05 program checkpoint (2026-08-31)

The complete Coffee Shop-reachable record-type-20/class-`0x05` program is
implemented as one reusable source program rather than frame or slot patches.
Source slots `0x00ffb180` and `0x00ffb280` execute states
`0x0200/0x0400/0x0402/0x0404/0x0604`, current selector-11 contact, RNG
`0xcb46 -> 0x61a7`, audio command `0x0074`, both trajectories, the natural
class-`0x4e` variant-1 impact allocation in `0x00ffc200`, and release at source
frame 3931. The focused differential passes four real mutations. Oracle
auxiliary validation passes 114 mutations; SPEC-02 passes 180 mutations; the
generated header is current. Contract and fixture SHA-256 values are
`bcba36794f1aa4e21012fda54d61745302a71ae33fa0d3480bc68d06a04156a3`
and `be1aba966091941aba3de87e7d8574908b850f3529733b7e610e1b45fe38fc31`.

Target `LiveEncounterBench` BUILD_ONLY passes with GAME.BIN 408704 bytes, BSS
end `0x060bad80`, and `/GAME.BIN` SHA-256
`84fc1c479ecebef8b1f608fae3d2e7472adacba28fe4e1883711288797ff8bb8`.
The runtime measures `0x18410` bytes in its `0x19000` cartridge carve.

The in-flight size correction exposed a Saturn platform defect: Jo's sprite
upload path uses `jo_dma_copy`, which is unconditionally `slDMACopy`. Because
the composite scratch is in cartridge A-bus space and VDP1 VRAM is on B-bus,
that SCU DMA transfer is unsupported even though current emulators allow it.
Boot pool creation now reserves VDP1 storage with no A-bus source upload, and
each runtime composite replacement uses an explicit SH-2 CPU longword copy.
Four real platform mutations reject boot or runtime SCU-DMA/A-bus endpoints
and loss of the cart scratch binding. Platform rule: no SCU DMA transfer may
have an A-bus endpoint; cart-sourced VDP1 uploads are CPU-mediated. This remains
physical-tier-only and physical Saturn is `UNRUN`.

The required paired cold pinned-emulator lane passes deterministically with
normalized ISO SHA-256
`47775bf876d2f6e3328f9452ea076ba73728ea6b5efcf28ef0badeb6916fe409`.
The required window-only WGC covers cadence-1 source frames 2280..2310. Direct
inspection confirms Predator identity, P1-only HUD, coherent impact/explosion
cadence, class-`0x1f` presentation, both VDP2 planes, palette, and priority.
The full-speed WebP and contact-sheet SHA-256 values are
`7c1e6e3bafd379ef1a611d76a21d2f33bf6a61418ba6a1e10297585a63b967a8`
and `45560cc804fb1ad226d55aa1ade170bde1a6c13c57f9976dd09d05b409c4a4dc`.

The complete scene remains intentionally RED at native frame 4006, scheduler
code 29, after the class-`0x05` program and release are exact. Raw unexplained
scene counters remain 327 actor-lifetime, 1234 spawn/despawn, 2 active-state,
93 collision/damage, 3 route/camera, and 281 audio/load rows until the next
full census. No accepted-candidate promotion is made.

Before further scene expansion, execute one bounded complete-Round-1 memory
program: document the linked work-RAM limit and all cartridge carves; size them
from the accepted ORACLE-11 complete-route census; add per-region build-time
assertions; and place generated read-only SPEC terrain, timer/selector,
animation-record, and collision tables into a deterministic hashed cart archive
loaded at the existing boot seam. Mutable per-frame state prefers work RAM and
read-only content prefers cartridge. Later loads may occur only at the Round
1-to-Round 2 boundary (`ADAPTED` for USER-10) or a census-proven camera-locked,
CDDA-safe, never-mid-combat source seam. All later size pressure routes to this
program rather than ad-hoc squeezing.

### Complete-Round-1 memory-plan checkpoint (2026-08-31)

The bounded memory program is complete without changing the workflow or
creating another ledger. `data/reimplement13_round1_memory_plan.json` records
the linked work-RAM limit and every contiguous cartridge carve with base, size,
owner, required bytes, and load phase. Its capacity basis is the accepted
ORACLE-11 census: 94 route segments and 1,517 authoritative writer PCs. The
complete generated read-only SPEC set (terrain, timer/selector,
animation-record, collision, route, and actor contract tables) is 152 tables
inside one deterministic SH-2 big-endian archive. The archive is 46,564 bytes,
has SHA-256
`b2bae49f6182dcde3ced8d47342d5689c48b5095793ae4ec0ead61323c64d587`,
and resides in a census-sized `0x40000` cartridge region beginning at
`0x22711000`.

Target loads the archive only through the existing boot seam, validates its
magic/version/byte count, and binds the generated tables before native Round 1
initialization. Per-region compile-time assertions cover the runtime,
diagnostic, content, scratch, and complete DRAM1 layout. The Round 1-to-Round 2
load is inactive and reserved as `ADAPTED_PRESENTATION_FOR_USER_10` if later
needed. Intra-round loading remains inactive unless the census proves it is
necessary at a camera-locked, CDDA-safe, never-mid-combat source seam. Future
size pressure returns to this memory program; it does not authorize ad-hoc
squeezes.

The archive double-build is byte-identical. Focused memory, Target wiring,
cart-to-VDP1 CPU upload, class-`0x05`, Oracle auxiliary, SPEC-02, and generator
lanes pass 18/130/4/4/114/180 real mutations or suppressions. The mechanically
regenerated player-air artifact changes only its embedded accepted-auxiliary
SHA. The regenerated SPEC contract and fixture identities are
`7a0db579d3751541d374444ebae60a009f9afedf75840457661b60de1fa93b3a` and
`ae84a21f139fc86d820b22a2e6277e838cd2b31e9f17519619e799418a5eb76b`.
Target passes with GAME.BIN 371,408 bytes, BSS end `0x060b1be0`, and
GAME.BIN SHA-256
`857ffe7c695add3f38f82f5cea68ee303635e6919fd82982435bb47dbe2095de`.
Two cold pinned-emulator runs pass byte-identically at normalized ISO SHA-256
`9a6ccf084933397826ae1a4d7128bbc1d3254a6b862e91d7291c8bc958a68e60`.
Both report `round1_spec_bound=1`; that diagnostic now requires the archive's
boot-load completion as well as the accepted contract identity, and a real
mutation rejects removing the load predicate.
Direct window-only WGC inspection confirms Predator identity, P1-only HUD,
coherent actors, both VDP2 planes, palette, and priority. The emulator remains
blind to the SCU-DMA A-bus restriction; physical Saturn is `UNRUN`.
Fast and Oracle pass the focused memory, SPEC, and Oracle bodies before both
reach the preserved full-host frame-3782 Coffee Shop chronology RED. That
failure remains part of the active scene closure and is not reclassified as a
memory-program pass.

The complete Coffee Shop scene remains intentionally RED at native frame 4006,
scheduler code 29. Resume by regenerating the complete source/native census,
identifying the owning reusable player-collision program, and closing all
Coffee Shop-reachable branches from accepted Oracle/SPEC evidence. Do not add a
frame exception, authored delay, guessed rule, or further ad-hoc size squeeze.

### Coffee Shop reusable-runtime closure checkpoint (2026-08-31)

Four source programs exposed by the complete scene are now closed without
reopening class-`0x05` or changing the accepted runtime candidate. Type-16
terminal animation uses its separate two-tick action timer before release;
class-`0x1f` selector-4 contact preserves source hitstop 10 and damage 15 as
separate values; presentation and current collision accept all 54 accepted
inner-state records through one shared lookup; and simultaneous right +
Button1 + Button2 + Button3 input remains in the source special-input pipeline
instead of beginning Button3 immediately. Focused lanes pass 1/11/15/1 real
mutations.

The complete host census now advances through the prior frame-4006 boundary to
source frame 5566. Its code-11 slot `0x00ff9e80`, state/substate
`0x0208:0x1004`, appears only after the source has already replaced the Coffee
Shop population and traversed route edges 4->6->0->2. It is therefore tracked
as downstream of the still-unimplemented exit/teardown program; adding that
state as an isolated context is forbidden.

Release `LiveEncounterBench` Target passes with GAME.BIN 371,440 bytes, BSS end
`0x060b1c00`, and GAME.BIN SHA-256
`6c5d58cfc019f4530976c388167e769f0dfc534b60af74521b99a4104ea75b0d`.
Two cold pinned-emulator Coffee Shop runs pass the existing paired five-mutation
evidence check at normalized ISO SHA-256
`3293a604ed84a0062ec50e1fe16ead762646789e4a407f6f659f41a9e5c99bdc`.
Focused window-only WGC at valid source-aligned frames 2280, 2287, 2306, 2307,
and 2310 preserves the prior gameplay aperture, Predator identity, impact
cadence, both VDP2 planes, palette, and priority. Later host source frames are
outside the current emulator ledger, which stops at diagnostic frame 574 /
source-visible frame 2615; no later WGC claim is made.

Fast and Oracle pass every focused authority and all 180 SPEC mutations, then
stop at the preserved full-host frame-3782 stage-progress chronology RED. The
scene remains unaccepted. The next implementation body is the complete Coffee
Shop exit controller: encounter clear, actor teardown/replacement, route edges
at 5453/5524/5562, and load boundaries at 5565/5566. Use accepted Oracle/SPEC
evidence or the smallest required fixture amendment; do not add an authored
delay, fixed-frame teardown, isolated state context, or ad-hoc size squeeze.
