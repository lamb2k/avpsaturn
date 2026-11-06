# ORACLE-01-FULL-REFERENCE-ROUTE task card

TASK: ORACLE-01-FULL-REFERENCE-ROUTE
KIND: ORACLE
STATUS: BLOCKED
CHECKPOINT: oracle-full-reference-route
BASE: project_state.foundation_head
BRANCH: project_state.production_branch
TIER: 2
DEPENDENCIES: [ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN]
REQUIRED_LANES: [Fast, Oracle]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME]

## Objective

Capture two identical deterministic `avspu` cold-boot-to-credits runs plus one
real perturbation control, without changing production runtime behavior.

## Owned paths

- Card-scoped MAME capture tools/fixtures, private raw evidence, derived route
  manifests, coverage ledger fields, state, and card only

## Existing systems to reuse

- Pinned MAME 0.289 source identity, existing input/capture tooling, scene
  manifest, and provenance rules.

## Systems deliberately disabled

- All Saturn runtime, assets, gameplay, presentation, loading, and audio changes.

## Focused machine checks

- Two-run identity; input-independent perturbation rejection; actor, spawn,
  collision/damage, animation, object, layer/palette/line-scroll, audio, route,
  continue/game-over, ending, and credits schema/provenance.

## Saturn build profile

None. MAME/host evidence only.

## Emulator readback

No Saturn emulator readback and no physical Saturn claim.

## Human-review requirement

None; source capture labels are technical evidence, not subjective approval.

## Exclusions

- No fabricated route facts, runtime writes, or complete claim from the current
  18,000-frame partial capture.

## Hard stops

- Missing private ROM/evidence, nondeterminism, inadequate perturbation, or
  required physical interaction.

## Next eligible cards

- `INTEGRATE-05-REFERENCE-CHARACTER-FULL-GAME` after its other dependencies.
