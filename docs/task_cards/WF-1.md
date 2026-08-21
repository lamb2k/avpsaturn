# WF-1 task card

TASK: WF-1 workflow simplification activation
STATUS: ACCEPTED
CHECKPOINT: workflow-simplification
BASE: f2c9a4725dffdcb2e5689c70914511674fb3c9ef
BRANCH: codex/avp-workflow-simplification
TIER: 2
DEPENDENCIES: []
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: [Oracle, Full, Target, Emulator, Physical]

## Objective

Replace prompt-chain supervision with one roadmap, machine-readable state,
bounded task cards, risk-tiered verification, exact-tree review bundles, and a
safe worktree launcher.

## Owned paths

- Workflow policy, state, task cards, verification orchestration, reviewer
  profiles, launch/review tooling, and active roadmap/handoff documentation.

## Done

- The Fast lane and workflow policy checks pass on the clean committed tree.
- Independent semantic, provenance, and Saturn-scope workflow reviews accept
  the workflow change.
- Missing private writer inputs may leave optional Oracle evidence incomplete;
  they do not block this workflow-only task.

## Exclude

- No candidate HIT/KO acceptance claim.
- No gameplay, Saturn runtime, emulator, release, or physical-hardware claim.
- No modification of the dirty primary worktree during integration.

## Stop

Integrate through a clean canonical-line worktree. Do not clean, restore,
stash, or reset the dirty primary worktree.
