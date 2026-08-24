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
567/909/909 requested and submitted AvP workload tile draws; one separately
reported SGL scaled-sprite sentinel per table; 568/910/910 total reachable
hardware draws; three reachable state commands; one terminator; and
572/914/914 total reachable table entries. Record stored nonzero slots as a
separate residue/extent measurement. Overload must report
`detector_tripped=1`; asset, canary, copy-path, traversal, and production-mode
deadline failures must remain zero. Paired semantic state must be identical.
Emulator timing is instrumentation evidence only, never the 15% hardware
margin.

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

## Bounded correction contract (2026-08-24)

- The Probe-only SCU sprite-draw-end interrupt is reliable in pinned Yaba and
  produces an intra-field FRC timestamp; next-field EDSR is no longer used to
  estimate margin.
- The model-equivalent live VDP1 census found that SGL prepends one reachable
  8x1 `SCALED_SPRITE` Z-sort sentinel (`CMDCTRL 0x0501`, texture source
  `0x07ff00`) before the three state commands and the AvP workload tile draws.
  The sentinel remains in the production-facing path and is classified and
  reported separately rather than suppressed.
- Schema 3 distinguishes requested workload tile draws, submitted workload
  draw calls, the auxiliary sentinel, total reachable hardware draws,
  reachable state commands, the terminator, total reachable table entries,
  and stored nonzero slots. The 567 and 909 workload figures are never
  described as complete VDP1 hardware command counts.
- Reliable SCU draw-end timestamps govern the shared deadline predicate when
  present; VBlank span remains the unreliable/missing-timestamp fallback. The
  ten-minute soak is measured by the independent elapsed VBlank clock and
  alternates in 60-elapsed-field blocks; completed workloads remain a separate
  count.
- The corrected Target, paired emulator soak, Full, and approved-image
  regression gates pass. `READY_FOR_PHYSICAL` becomes publishable only when
  these commits are pushed and the remote branch SHA is verified.

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
  AvP workload tile draws. Peak source frame 5776 expands 78 measured objects
  to exactly 909 AvP workload tile draws. Their workload SHA-256 values are
  `194cb70efb503a3277e9f1256b71f01bcf4393566aeed6f3a538018c0e385e68`
  and `92e468908f59a9c1ca3b6c5c7ccfbf5a98e38ccf464adb05393233db03f7966c`.
- Strict `release-probe3` compile passes from corrected implementation commit
  `cdfae46e440a64ae9bfc503d024b3e46b58223ac`; canonical generated-data hygiene
  is fixed at `85654aa4d94f8805a315f672207b3a8e747e9a8b`. Probe ISO SHA-256 is
  `82c3a86c34b79626bf2cda7c2da4174ab1ee3603b3341f5091b141b740b4ef50`;
  manifest SHA-256 is
  `b36b63fc4324c31eeb680814a5ac120b484e23575f8817d847555d00f9dc0d48`;
  executable ELF/BIN hashes are respectively
  `106a1366c8f07a4904592299e52eb9502678a952d4ec5b0cced097dcd1bfdba1`
  and `719df77e0ca7705dbeedd69c4370bea197bf0997a4d5402deff49cd1ded2eb7e`.
- Two pinned Yaba Sanshiro 1.20.37-2986eb semantic runs pass with identical
  post-run checksum `0xf032955f`; overload safely trips its declared detector.
  Each run reaches 36,000 independent elapsed VBlank fields while alternating
  4,560 workload submissions, with zero missed/late workload lists, zero soak
  skips, zero asset/canary/copy-path failures, and a 66.12% minimum measured
  emulator margin. These runs make no physical timing claim.
- Both command censuses preserve the exact measured composition. Representative
  mode records 567 requested/submitted/workload draws, one auxiliary SGL
  sentinel, 568 total reachable draws, three state commands, one terminator,
  572 reachable entries, and 572 stored nonzero slots. Peak and overload each
  record 909 requested/submitted/workload draws, one auxiliary sentinel, 910
  total reachable draws, three state commands, one terminator, 914 reachable
  entries, and 914 stored nonzero slots.
- Fast, Probe3 Target BUILD_ONLY, and clean-shadow Full lanes pass. Full records
  zero changed tracked artifacts.
- The rebuilt normal release normalizes to the locked exact ISO SHA-256
  `4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`.
- The ignored operator package is complete at
  `build/feedback/HW-01-PROBE-3-VDP1-BUDGET-PRETEST/`. Read-only preflight
  found no removable target, serial/debug device, capture device, or Saturn
  loader tool. No device write was attempted or authorized.
