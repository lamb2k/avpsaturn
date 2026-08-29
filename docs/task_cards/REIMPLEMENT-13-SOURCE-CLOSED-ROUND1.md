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

## Next eligible cards

- `QA-13-ROUND1-END-TO-END-DIFFERENTIAL` after the complete stable Round 2
  handoff candidate is committed and frozen.
