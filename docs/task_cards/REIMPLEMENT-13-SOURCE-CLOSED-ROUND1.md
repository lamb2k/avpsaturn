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
pass with continuous staff ownership and zero regression. Commit `f6cab22`
implements the source-complete Button1 boundary: exact sufficient/empty action
states, signed 12-attempt volley, four-tick cadence, recovery-edge timing,
50-frame presentation, successful-allocation resource debit/recharge ordering,
and the known type-4/class-5 allocation writes. Forty-three host mutations,
38 Target suppressions, Target, paired Emulator, Fast, Oracle, and direct
pinned-window inspection pass. Commit `09c8a28` amends only the existing
SPEC-02 fixture from accepted Oracle evidence and implements the executable
type-24/class-0x10 empty-request effect: exact variant-1 allocation, offset,
ten presentation records, timers/branches, low-byte movement guard, and pool
release. The same fixture binds class-0x05 allocation angle/selector tables,
all 64 signed motion pairs, presentation records, state-2 arithmetic/bounds,
state-4 impact allocation, and state-6 release. The current checkpoint
implements that body plus the exact type-24/class-0x3a state 0/2/4 five-record
impact presentation/release handler and current-state collision/damage writer
for attack table `0x03136a`. Sixty-four host mutations, release Target, paired
Emulator, Fast, and Oracle pass. Byte-identical target runs record 49 projectile
render frames, 40 impact render frames, three collision writes, three damage
writes, and zero fallback, decode failure, or gameplay PCM. Direct paused
scanout inspection at native controller updates 212 and about 253 preserves the
source projectile/impact assemblies, coherent actors, P1-only HUD, camera, both
VDP2 planes, palette, and priority. Audio command identities `0x007e` and
`0x0148` remain semantic-name unknown telemetry; no PCM mapping is inferred.
The build explicitly depends on the SPEC header, and the focused lane checks
the complete hash, preventing stale target binding after fixture regeneration.
The renderer-integrity checkpoint then corrected an objective Target-only
defect without changing gameplay authority: Jo Engine `sprites.o` and `3d.o`
had retained 128-entry sprite arrays while callers used `JO_MAX_SPRITE=255`, so
`__jo_sprite_pic` overlapped `__jo_sprite_def` and produced horizontal texture
stripes. Those objects now explicitly depend on the project makefile, the link
rejects less than 2,040 bytes of array separation, and the standard Jo DMA
upload path remains in use. Two cold release-live runs normalize to ISO
`059b7b3422eedd19f47761d01d88e0a6e082db85ad9eeb6142928b165e77ebf5`
and compare all 208 live cache textures with zero mismatches; sprite high-water
is 225/255. Direct reset/run/pause inspection is clean across both Coffee Shop
planes, visible edges, actors, staff, projectile/impact population, P1-only HUD,
palette, and priority. Fast, Oracle, Target, paired Emulator, and 82 focused
mutations pass. STRIPS.BIN is now accurately classified as a hybrid
source-derived stage package: background/scroll presentation is retained, while
the captured foreground schedule remains compile-time excluded from playable
gameplay authority.
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

Close the preserved Button3 vector/branch blocker next. Bind table `0x0243d2`
numeric signed 16.16 vectors, input/facing selector mapping, branch order,
landing/interruption guards, presentation, collision selectors, and mutations
by amending only the existing SPEC fixture. Use the smallest bounded Oracle
follow-up only if accepted evidence genuinely lacks an exact required field.
Do not leave the first segment.
Frame 2328 remains evidence, not gameplay authority.
Evidence: `data/reimplement13_round1_stable_entry.json` and
`data/reimplement13_startup_authority.json`.

## Next eligible cards

- `QA-13-ROUND1-END-TO-END-DIFFERENTIAL` after the complete stable Round 2
  handoff candidate is committed and frozen.
