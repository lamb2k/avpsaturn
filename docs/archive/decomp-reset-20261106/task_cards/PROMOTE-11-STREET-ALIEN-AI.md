# PROMOTE-11-STREET-ALIEN-AI task card

TASK: PROMOTE-11-STREET-ALIEN-AI
KIND: PROMOTE
STATUS: ACCEPTED
CHECKPOINT: promote-street-alien-ai
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 1
DEPENDENCIES: [SALVAGE-11-STREET-ALIEN-AI]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER]

## Objective

Promote the accepted measured class-`0x1F` AI loop behind a class-specific
production interface with no authored fallback.

## Owned paths

- Future class-specific production AI interface/implementation and tests
- Card-scoped Saturn adapter/readback, migration/coverage state, and this card

## Existing systems to reuse

- Accepted SALVAGE-11 loop, class-`0x1F` presentation, exact collision/HIT/KO,
  deterministic RNG/scheduler fixtures, and all approved locks.

## Systems deliberately disabled

- Generic behavior trees/scripting, other enemy classes, bosses, multiplayer
  targeting, frontend, and full route.

## Focused machine checks

- Host differentials; source counterfactual controls; deterministic repeat;
  wrong-state/RNG/timer/fallback mutations; Target diagnostic and paired
  emulator evidence; exact approved presentation locks.

## Saturn build profile

Dedicated `StreetAlienAiPromotionBench` diagnostic.

## Emulator readback

Require exact AI state/decision/RNG trace, actor/contact/damage/HIT/KO outputs,
interface/fallback locks, canaries, failures, and bounded stability.

## Human-review requirement

No renewed review if presentation is unchanged; USER-09 judges live behavior.

## Exclusions

- No authored fallback, generic AI engine, extra archetype, multiplayer, or
  physical claim from emulator evidence.

## Hard stops

- Source differential/counterfactual failure, fallback, nondeterminism,
  approved regression, or class-specific interface cannot remain bounded.

## Next eligible cards

- `INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER`.
