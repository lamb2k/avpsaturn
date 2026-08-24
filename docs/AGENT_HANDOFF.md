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

Probe schedule `e892836d...abd84` binds frame 5637 to 567 workload draws and
frame 5776 to 909; census composition is recorded separately in state. Probe
image `82c3a86c...ef50` from `cdfae46e` passes two independent 36,000-field
soaks with 4,560 alternating submissions, zero missed/late lists, checksum
`0xf032955f`, 66.12% emulator-only minimum margin, and a tripped overload
control. Normal ISO remains exact at `4a142774...98ef`. Operator package is at
`build/feedback/HW-01-PROBE-3-VDP1-BUDGET-PRETEST/`. Read-only preflight found
no removable target, serial/debug device, capture device, or loader tool and
performed no write. Physical Saturn timing/scanout/soak remain `UNRUN`;
`SALVAGE-08-FRONTEND` remains inactive.
ORACLE-04 is accepted at `c3124b8c4ed71416e9b85d7acb0626c7068f0a41` and
ORACLE-05 at `ace786d45df40d538ddd88b797cb81c2604a7476`; their bounded
unknowns remain explicit. The sole software writer is read-only
`ORACLE-06-ROUND1-ENCOUNTER-RULES`.
HW-01 is parked `WAITING_FOR_EXTERNAL_HARDWARE`; do not wait on it.
Resume prompt:

> Resume the AvP salvage Goal by continuing only ORACLE-06 read-only source research on the canonical playable-loop line; preserve accepted ORACLE-04 commit c3124b8c4ed71416e9b85d7acb0626c7068f0a41, accepted ORACLE-05 commit ace786d45df40d538ddd88b797cb81c2604a7476, Probe ISO 82c3a86c34b79626bf2cda7c2da4174ab1ee3603b3341f5091b141b740b4ef50, approved INTEGRATE-03 ISO 4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef, all locks, and physical Saturn UNRUN; capture one bounded Round 1 encounter with entry, spawn, camera lock/bounds, controller/AI/presentation ownership, clear, unlock, and continuation plus a real perturbation, then accept it before activating SALVAGE-10.
