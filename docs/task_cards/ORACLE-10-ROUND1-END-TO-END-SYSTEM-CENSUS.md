# ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS task card

TASK: ORACLE-10-ROUND1-END-TO-END-SYSTEM-CENSUS
KIND: ORACLE
STATUS: ACCEPTED
CHECKPOINT: oracle-round1-end-to-end-system-census
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [REPAIR-11-LIVE-BACKGROUND-PRESENTATION]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
READ_ONLY: true
NEXT_ELIGIBLE_CARDS: [ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE]

## Objective

Capture Round 1 from its first stable entry through stable Round 2 handoff and
inventory every gameplay authority required for a one-player Predator Warrior
completion route. Produce two independently launched byte-identical reference
completions, one completing route-wide input perturbation, targeted
counterfactuals for every discovered authority, and one bounded
failure/continue path where the source route permits it.

## Owned paths

- `data/round1_system_coverage.yaml`
- `data/oracle10_round1_route.json`
- Card-scoped source capture, analysis, focused tests, ignored evidence, state,
  coverage, migration, roadmap, and handoff updates

## Existing systems to reuse

- Pinned `avspu` reference environment, existing Oracle capture tooling,
  accepted actor/animation/collision/route evidence, and the first-live-
  encounter harness only as a technical substrate.

## Systems deliberately disabled

- All production runtime implementation or repair, frontend, other playable
  characters, multiplayer, later-stage implementation, and physical status.

## Focused machine checks

- Enumerate every route state/substate, segment, camera lock/unlock, navigation
  body, actor class/type, action, enemy, projectile, pickup/equipment state,
  hazard/destructible, lifecycle event, encounter, gameplay trigger, audio/load
  event, boss phase, clear/failure/continue condition, and Round 2 transition.
- For every body bind source frame range, actors/classes, routine/table where
  known, reads/writes, transitions, RNG, scheduler order, animation/assembly,
  collision, presentation dependency, closure status, and exact next experiment.
- Classify only as `SOURCE_CLOSED`, `PARTIAL`, `OBSERVED`, `ADAPTED`, `UNKNOWN`,
  or `NOT_REQUIRED_FOR_ROUND1`; never infer behavior from appearance alone.

## Saturn build profile

None. This card is read-only source research; no production or Target build is
authorized.

## Emulator readback

Reference MAME capture only. Preserve independent-launch identity, deterministic
route hashes, perturbation identity, counterfactual results, and failure/continue
evidence. All production Saturn and Yaba execution is disabled for this card.

## Human-review requirement

None. This census is evidence for ORACLE-11 and cannot approve USER-09 or
USER-10.

## Exclusions

- No production C, speculative behavior, authored fallback, snapshot teleport,
  fixed-frame gameplay result, generalized CPS-2 engine, or complete-game claim.

## Hard stops

- Missing stable Round 2 handoff, non-independent control captures, unresolved
  capture identity, guessed authority, or any production runtime write.

## Next eligible cards

- `ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE` after the complete census and its
  mutation evidence are accepted.

## Accepted result

Accepted with `data/oracle10_round1_route.json` SHA-256
`d690678aec4a419d736a69a381f9f3dd6d16d33c0245e3168a3d5b844314fe13`
and `data/round1_system_coverage.yaml` SHA-256
`df8b9ba4918db2e6a195d551b0d3c9f3a85d8efa76af58a6ebbfc58356c05b16`.
Two independently launched 18,000-frame source completions are byte-identical
across captured regions and cadence-1 screenshots. A route-wide input
perturbation reaches the exact Round 2 underpass signature at frame 16,425 and
continues in rendered Round 2 gameplay. Thirteen counterfactual variants cover
all ten discovered authority families; the no-continue path does not complete,
and forced boss removal does not create an unsourced clear. The census records
94 route bodies, 427 actor lifetimes, 20 class/type archetypes, route/camera/RNG,
audio/load writers, source route events, and exact next experiments. Fast and
Oracle pass with six tracked mutation rejects. Production runtime writes remain
zero; USER-09 remains `CHANGES_REQUESTED`, frontend remains inactive, and
physical Saturn remains `UNRUN`.
