# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot

Future production cards continue sequentially from `production_head`.

## Preserved evidence work

- The dirty canonical and `prototype/avp-clean-playable-skeleton` worktrees
  remain untouched.
- V2-2B is accepted at evidence commit
  `597f4ed517d4e715d814ff841bd00d3977803f85`, merged into production continuity
  by `033be384bcc4e678408b465f102925841eab4333`, and remotely verified. This is
  host/static/MAME evidence only, not Saturn proof.
- `SALVAGE-00-OLD-BUILD-BASELINE` remains a technical baseline only.
- `USER-01-PLAYER-BASELINE-REVIEW` and later explicit approvals remain
  component-scoped regression locks.

## Current task and next action

REPAIR-09 is accepted at `417ed808e10f0f255948b1e6ecf0223399509c74`.
INTEGRATE-03 remains user `APPROVED` for
`SOURCE_BOUND_WITH_ADAPTED_INPUT` at candidate `82965ef80223a03937e0b527d16161ed68d874a0`
and exact ISO `4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`.
The active `QA` card is `HW-01-PROBE-3-VDP1-BUDGET-PRETEST`, status `READY`
(workflow vocabulary for `READY_FOR_PHYSICAL`), in the isolated
`AvPSaturnCapabilityTest-hw-01-probe3` worktree on
`codex/avp-hw-01-probe3`. Isolation was required because the continuity
worktree had an owned-path collision with generated tracked data.

Probe schedule `e892836d...abd84` binds committed AvP measurements: frame 5637
expands to 567 commands and frame 5776 expands exactly to 909. Strict Probe
image `b4410c8d...91c8` from implementation `78dc52c` passes two identical pinned-emulator semantic runs with
summary `0xe3241b49`; the overload control trips. The normal-release regression
remains exact at `4a142774...98ef`. Operator package is under
`build/feedback/HW-01-PROBE-3-VDP1-BUDGET-PRETEST/`. Read-only preflight found
no removable target, serial/debug device, capture device, or loader tool and
performed no write. Physical Saturn timing/scanout/soak remain `UNRUN`;
`SALVAGE-08-FRONTEND` remains inactive.

Resume prompt:

> Resume the AvP salvage Goal at HW-01-PROBE-3-VDP1-BUDGET-PRETEST `READY_FOR_PHYSICAL`; preserve Probe ISO b4410c8d74939903a253d391571720b3972f6253f77e599cd88a715e912591c8, approved INTEGRATE-03 ISO 4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef, and all locks; identify the connected Saturn/cart/boot/pad/capture setup, request explicit authorization for any exact target write, run representative, peak-909, overload, alternating soak, then the two cold-boot exact-image records and integrated soak; keep physical evidence UNRUN and SALVAGE-08 inactive until every physical condition passes.
