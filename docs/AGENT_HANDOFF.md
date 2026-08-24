# Active checkpoint
`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap.

## Workflow pivot
Future production cards continue sequentially on `codex/avp-playable-loop-pivot`.
HW-01 is parked `READY_FOR_PHYSICAL` / `WAITING_FOR_EXTERNAL_HARDWARE`; do not
wait on it and do not activate SALVAGE-08.

## Preserved evidence work
- The dirty canonical and `prototype/avp-clean-playable-skeleton` worktrees
  remain untouched.
- V2-2B evidence `597f4ed517d4e715d814ff841bd00d3977803f85` remains
  bounded host/static/MAME evidence only.
- `SALVAGE-00-OLD-BUILD-BASELINE` remains a technical baseline only.
- `USER-01-PLAYER-BASELINE-REVIEW` and later explicit approvals remain
  component-scoped regression locks.

## Current task and next action
REPAIR-09 remains accepted at `417ed808e10f0f255948b1e6ecf0223399509c74`.
INTEGRATE-03 remains user `APPROVED` for `SOURCE_BOUND_WITH_ADAPTED_INPUT` at
candidate `82965ef80223a03937e0b527d16161ed68d874a0` and exact ISO
`4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`.
Physical Saturn remains `UNRUN`.

Probe image `82c3a86c...ef50` passes two 36,000-field emulator soaks. The exact
workload counts are 567 and 909, each plus one auxiliary SGL sentinel, three
state commands, and one terminator; the overload control trips and the minimum
emulator-only margin is 66.12%. Preserve the operator package and private data.

ORACLE-04, ORACLE-05, and ORACLE-06 are accepted. ORACLE-06 report
`data/oracle06_round1_encounter.json` proves that the source opening is a
withdrawal set piece, not a kill clear. The live-loop contract is explicitly
adapted to one ORACLE-05 alien and clears only after target KO then inactivity;
timers and presentation flags cannot clear it.

PROMOTE-10 is accepted at `6b943ea`; PROMOTE-11 is accepted at `b75d8c8`.
The production alien core proves the one-target 38-update approach, source RNG
timer branch, current-state contacts, HIT recovery, and KO removal in two
identical post-commit 576-sample cold Yaba reads; ISO `4172b359...326fc1`.
Generic AI, route progression, subjective feel, and physical Saturn remain
outside acceptance.

The sole software writer is `INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER`.
Resume prompt:
> Resume the AvP salvage Goal by executing only INTEGRATE-04A on codex/avp-playable-loop-pivot; preserve accepted PROMOTE-10 at 6b943ead3db9ad5cb50bff3bca3884125b973a78, PROMOTE-11 at b75d8c8758073b01d7ea657ed9640c7f48c0f190, ORACLE-04/05/06 evidence, approved INTEGRATE-03 ISO 4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef, Probe ISO 82c3a86c34b79626bf2cda7c2da4174ab1ee3603b3341f5091b141b740b4ef50, all component locks, dirty/private evidence, and physical Saturn UNRUN; integrate real input, current-state player/AI/collision/damage/HIT/KO, adapted target-KO-then-inactivity clear, unlock, and continued movement, then stop at USER-09.
