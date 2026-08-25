# QA-13-ROUND1-END-TO-END-DIFFERENTIAL task card

TASK: QA-13-ROUND1-END-TO-END-DIFFERENTIAL
KIND: QA
STATUS: BLOCKED
CHECKPOINT: qa-round1-end-to-end-differential
BASE: project_state.production_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [REIMPLEMENT-13-SOURCE-CLOSED-ROUND1]
REQUIRED_LANES: [Fast, Oracle, Target, Emulator]
OPTIONAL_LANES: [Full]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [USER-10-ROUND1-PLAYTHROUGH-REVIEW]

## Objective

Freeze the exact REIMPLEMENT-13 candidate and differentially verify the entire
Round 1 completion route, perturbed completion, permitted failure/continue,
and targeted counterfactuals without changing gameplay during acceptance.

## Owned paths

- QA-13 scenarios, differential/readback tools, reports, ignored continuous
  clips/strips/overlays/timelines, state, coverage, migration, and this card

## Existing systems to reuse

- Accepted ORACLE-10/11, SPEC-02, exact REIMPLEMENT-13 candidate, pinned source
  and Saturn environments, and existing continuous visual-QA infrastructure.

## Systems deliberately disabled

- Gameplay implementation or repair, frontend, other characters, multiplayer,
  later stages, candidate substitution, and physical status.

## Focused machine checks

- Compare input, route/encounter state, actor population/scheduler, states,
  positions/facing/navigation, equipment/resources, animation/assembly,
  lifecycle, collision/damage/HIT/KO, RNG, camera/layers, scripts, audio/load,
  boss phases, stage clear, and Round 2 transition across two identical source
  routes, two identical Saturn routes, a perturbed completion, failure/continue,
  and authority-family counterfactuals.
- Directly inspect continuous full-speed playthroughs, segment contact sheets,
  cadence-1 transitions, facing/equipment strips, navigation/collision overlays,
  lifecycle/encounter/boss/route/loading timelines. One screenshot or ledger is
  insufficient.

## Saturn build profile

Reuse the exact frozen direct-entry and interactive REIMPLEMENT-13 images; do
not rebuild gameplay during acceptance.

## Emulator readback

Automatically fail wrong neutral-facing, geometry traversal, wrong sprite
family, equipment discontinuity, state/animation disagreement, unsourced
lifecycle/clear, stale pose, unsupported collision/damage, RNG mismatch,
background corruption, route divergence, missing boss/clear/handoff, or fallback.

## Human-review requirement

After technical acceptance activate USER-10 and ask its exact required question.

## Exclusions

- No inferred approval, gameplay change, frontend, physical proof, or acceptance
  from a single screenshot/ledger.

## Hard stops

- Any automatic-fail condition, unresolved objective discrepancy, missing
  continuous evidence, nondeterminism, or candidate identity mismatch.

## Next eligible cards

- `USER-10-ROUND1-PLAYTHROUGH-REVIEW` after full technical and visual acceptance.
