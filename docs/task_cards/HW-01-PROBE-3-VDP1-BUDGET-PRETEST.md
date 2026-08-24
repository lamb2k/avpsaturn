# HW-01-PROBE-3-VDP1-BUDGET-PRETEST task card

TASK: HW-01-PROBE-3-VDP1-BUDGET-PRETEST
KIND: QA
STATUS: READY
CHECKPOINT: hw-01-probe-3-vdp1-budget-pretest
BASE: project_state.candidate_head
BRANCH: codex/avp-hw-01-probe3
TIER: 2
DEPENDENCIES: [REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION]
REQUIRED_LANES: [Fast, Target, Emulator, Full, Physical]
OPTIONAL_LANES: [Oracle]
CLAUDE_ALLOWED: false
NEXT_ELIGIBLE_CARDS: [INTEGRATE-03-PLAYABLE-SLICE]

## Objective

Prepare the missing isolated Probe 3 physical pretest for the user-approved
INTEGRATE-03 capability slice. Measure the production per-tile VDP1 render and
transfer path with a representative AvP workload, the exact measured 909-tile
peak, and a deterministic overload detector control. Stop at
`READY_FOR_PHYSICAL`; physical evidence remains `UNRUN`.

## Owned paths

- `tests/hardware/probe3/**`
- `docs/task_cards/HW-01-PROBE-3-VDP1-BUDGET-PRETEST.md`
- Minimal `AVSP_PROBE3` build/profile/telemetry wiring in `main.c`,
  `makefile`, `build.ps1`, `verify.ps1`, and the existing AVTL generator
- Card-scoped state, handoff, and roadmap routing
- Ignored `build/hardware/probe3/**` and
  `build/feedback/HW-01-PROBE-3-VDP1-BUDGET-PRETEST/**`

## Existing systems to reuse

- `avsp_entry_tiles` CPS2 block expansion and per-tile VDP1 command path
- `AVTL` texture archive, cartridge carve, LRU VDP1 texture pool, CRAM palette
  ownership, 384-to-352 coordinate mapping, Jo/SGL submission, VDP1 EDSR,
  work-RAM diagnostics, canaries, and asset-failure counters
- Accepted INTEGRATE-03 image, locks, and physical procedure

## Systems deliberately disabled

- Gameplay, AI, frontend, route progression, multiplayer, audio playback,
  presentation substitution, a second renderer or asset system, and any
  general benchmark/profiling framework

## Focused machine checks

- Deterministic schedule generation and exact source hashes
- Representative identity and exact 909-tile identity/count/draw agreement
- Count and workload-identity mutations rejected
- Strict SH-2 compile, profile isolation, cartridge/archive bounds, canaries,
  legal cart-to-VDP1 copy direction, zero undeclared reads/fallbacks
- Paired pinned-emulator semantic repeat; overload must trip its declared
  zero-field deadline without hanging or corrupting the console
- Exact approved normal-release composition remains normalized SHA-256
  `4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`

## Saturn build profile

Dedicated `release-probe3` profile, separate image/cue/manifest under
`build/hardware/probe3/`. The image automatically runs representative for 120
schedule frames, peak-909 for 120 schedule frames, then one bounded overload
control before displaying the post-run checksum summary.

## Emulator readback

Read the fixed linker-visible `avsp_probe3_telemetry` work-RAM block. Require
567/567 representative commands, 909/909 peak commands, 909/909 overload
commands with `detector_tripped=1`, zero asset/canary/copy-direction failures,
and identical paired semantic state. Emulator timing is instrumentation
evidence only, never the 15% hardware margin.

## Human-review requirement

No subjective implementation review is required for this render/transfer
instrument. The physical operator must correlate the post-run screen checksum
with telemetry and record the declared console/cart/loader/pad/capture setup.

## Exclusions

- No modification to `src/port_v2` gameplay or presentation behavior
- No modification or reinterpretation of `417ed808`, `82965ef`, `edb02ee`,
  the approved normal image, or any user-approved lock
- No physical pass from host/emulator evidence and no `SALVAGE-08` activation
- No flash, burn, copy, or removable-target write without exact target, boot
  method, and explicit user authorization

## Hard stops

- Missing/mutated source artifact, non-909 peak, unresolved tile/palette,
  normal-release hash drift, canary/asset/copy-direction failure, overload that
  does not trip, unsafe approved-lock overlap, or required physical interaction

## Next eligible cards

- Resume `INTEGRATE-03-PLAYABLE-SLICE` physical execution only after the user
  connects and identifies the exact Saturn setup. `SALVAGE-08-FRONTEND` remains
  inactive until the entire physical capability procedure passes.

## READY_FOR_PHYSICAL boundary

- Repository, schedule, strict build, paired pinned-emulator, approved-image
  regression, operator-package, commit, push, and remote-SHA checks are owned
  by this card.
- Physical render margin, physical CPU/transfer timing, input latency, final
  scanout, and soak remain `UNRUN` until hardware is connected.

## Completed pre-physical evidence

- Schedule: `e892836d68ad143367153b80f7b19b22ca07354389ef5afe2a0de250f0aabd84`;
  generated header: `fb2e9e88a9284be1496a26ca86b171ab25794781954183b9fd95767a539e7804`.
  Both bind committed demand artifact `data/avsp_sprite_demand.json` SHA-256
  `9b3d110bb353b0103f7739b46dc37b6bf895d1b09952e7f6e2739fbab1f6e39b`.
- Representative source frame 5637 expands 57 measured objects to exactly 567
  reachable/drawn commands. Peak source frame 5776 expands 78 measured objects
  to exactly 909 reachable/drawn commands. Their workload SHA-256 values are
  `194cb70efb503a3277e9f1256b71f01bcf4393566aeed6f3a538018c0e385e68`
  and `92e468908f59a9c1ca3b6c5c7ccfbf5a98e38ccf464adb05393233db03f7966c`.
- Strict `release-probe3` compile passes from implementation commit
  `78dc52c1510fc600fa788c306f332105c87d9840`. Probe ISO SHA-256 is
  `b4410c8d74939903a253d391571720b3972f6253f77e599cd88a715e912591c8`;
  manifest SHA-256 is
  `5bd5f41b6f61ddc8cd807929405cb371080af68aa410f8950403dc9bd7f4c45d`;
  executable ELF/BIN hashes are respectively
  `02b431941f7075ea31275e08c6400e21649081fcb46e1a0fbcd2f37a76568380`
  and `9d7608d1df5c90cb22faa608f00bb8e012f8436dd398b186b2c006fd83dc1594`.
- Two pinned Yaba Sanshiro 1.20.37-2986eb semantic runs pass with identical
  post-run checksum `0xe3241b49`; overload safely trips its declared detector.
  These runs make no physical timing claim.
- Fast, Probe3 Target BUILD_ONLY, and clean-shadow Full lanes pass. Full records
  zero changed tracked artifacts.
- The rebuilt normal release normalizes to the locked exact ISO SHA-256
  `4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`.
- The ignored operator package is complete at
  `build/feedback/HW-01-PROBE-3-VDP1-BUDGET-PRETEST/`. Read-only preflight
  found no removable target, serial/debug device, capture device, or Saturn
  loader tool. No device write was attempted or authorized.
