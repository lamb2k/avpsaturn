# ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN task card

TASK: ARCH-01-TITLE-TO-CREDITS-PRODUCTION-PLAN
KIND: ARCHITECTURE
STATUS: ACCEPTED
CHECKPOINT: plan-title-to-credits-production
BASE: 4067765ed9f398223ad7c75127f91ad3d80f65c4
BRANCH: codex/avp-user-02-enemy-review
TIER: 0
DEPENDENCIES: [PROMOTE-02-ENEMY-PIPELINE]
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-01-PLAYER-AND-ENEMY]

## Objective

Initialize the four-character, three-player, cold-boot-to-credits production
architecture, roadmap, state roles, ADRs, coverage ledgers, and forward cards
without changing runtime behavior or advancing the active implementation card.

## Owned paths

- `docs/GOAL.md`, `docs/ARCHITECTURE.md`, `docs/PARITY_PLAN.md`
- `docs/TEST_PLAN.md`, `docs/AGENT_HANDOFF.md`, and `docs/adr/**`
- `project_state.yaml` and the three title-to-credits coverage ledgers
- New/revised forward task cards, workflow validators, and focused policy tests

## Existing systems to reuse

- Accepted salvage/promotion state, current active integration, measured
  frontend interaction, scene manifest, migration ledger, and protected heads.

## Systems deliberately disabled

- All runtime, gameplay, rendering, asset, loading, audio, instrumentation,
  emulator, Oracle-capture, Full, Target, and physical Saturn changes.

## Focused machine checks

- Task/state/roadmap consistency; JSON-compatible YAML schema; ADR structure;
  staged architecture policy; Fast workflow checks; `git diff --check`.

## Saturn build profile

None. Control-plane planning only.

## Emulator readback

None. Existing emulator evidence is neither rerun nor relabeled.

## Human-review requirement

None. Existing exact user responses and approved component locks are preserved.

## Exclusions

- No implementation of the documented architecture and no active-card advance.

## Hard stops

- Unsafe worktree drift, fabricated source facts, runtime-path changes, or a
  validator requiring accepted legacy code to satisfy an unactivated rule.

## Next eligible cards

- Resume only `INTEGRATE-01-PLAYER-AND-ENEMY` on the existing continuity line.
