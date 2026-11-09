# Master CPU availability probe

Base: frame-chain `37c5b4a`. Evidence for this probe: **HOST synthetic only**.
Target link, emulator capture and physical Saturn measurement are **UNRUN**.
This adds no parallel rendering and makes no frame-rate claim.

## Question and existing evidence

The proposed two-CPU command builder needs evidence that the master has time
available when that work is needed. Frame-chain already overlaps the master
layer snapshot with the slave command builder. The master also runs the game.
The existing `SAT_PROF` records separate fixed-window histograms in low RAM;
it cannot pair one frame's master idle time with that frame's slave backlog.
This probe supplies the missing pairing, independently of `SAT_PROF`.

The default build is unchanged. `SAT_CPU_SLACK_PROFILE` adds a master-only
recorder in ordinary kernel BSS (high work RAM). It reads existing handoff
counters; it never writes them, changes task scheduling, or shares graphics
cache/VRAM ownership.

## Build and memory

Append `-DSAT_CPU_SLACK_PROFILE -DSAT_CPU_SLACK_DEPTH=4` to the existing
`KERNEL_CFLAGS` for a separate diagnostic image. Keep the exact original build
flags, asset selection, scene, inputs, emulator/core and frame-skip settings in
the capture record. The flag is off by default. `SAT_PROF` is not required.
Avoid combining with the PC-sampling interrupt profiler when measuring slack;
its interrupts add work to the quantity being measured.

| Depth | Exported ring | Current row and completion mailbox | Declared high BSS | Added low BSS |
| --- | ---: | ---: | ---: | ---: |
| Off | 0 | 0 | 0 | 0 |
| 2 | 88 | 56 | 144 bytes | 0 |
| 4 | 176 | 56 | 232 bytes | 0 |
| 16 (default) | 704 | 56 | 760 bytes | 0 |

Depth must be a power of two, at least two. These are declared data sizes,
before code, padding and the target link; they are not a fit proof. The low-RAM
limit must remain intact. Keep profiling disabled in the release comparison.
Instrumentation itself changes the workload, so compare its cadence with the
same build without the probe before trusting a small margin.

## What one row means

The IRQ closes the previous refresh window before its existing FRT reset,
then starts a new row. All phase readings come from the **master FRT**.

- `vblank`: source vblank; join to VDP1 plots using `source_vblank`.
- `period_ticks`: previous timer reset to the next IRQ entry. This excludes
  that next IRQ's prologue; it is deliberately not a claimed full field period.
- `handoff_tick`, `layers_done_tick`, `irq_done_tick`: wake of the slave,
  completion of layer copying, and the end of the master vblank handler.
- `game_done_tick`: the first completed task walk's observation, after
  `game_done` is set and before `f_11ec`. It includes the preceding IRQ and
  task work; it does not establish that all subsequent cycles are idle.
- `handoff_serial`: existing handoff counter for this source frame, or zero
  when no snapshot was handed over.
- `gfx_handed_end`, `gfx_done_end`: raw counters sampled in the next IRQ.
- `stage_characters`: stage in the low 16 bits; arcade character bytes above
  it, with 255 for inactive slots. Record guest flags separately.

Flags retain master overrun, preceding overrun, home hold, slave busy at the
start/idle/end observations, and invalid completion/clock samples. Slave busy
at IRQ entry is an observation, not proof the later handoff check will skip.

The main-thread completion mailbox commits its vblank tag last. A vblank that
interrupts its writes sees an invalid or old tag. The idle sampler also checks
the volatile vblank and `game_done` after reading the timer: an IRQ in the
sample cannot attribute an old completion to a new frame. If a boundary lands
between setting `game_done` and completing the diagnostic sample, the row is
explicitly unpaired; it never becomes invented idle time.

FTCSR overflow bit 1 is sampled and cleared alongside the existing master FRT
reset. Overflow makes the row unusable for slack; modulo subtraction cannot
turn a long stall into apparent spare time. Reversed/missing phases are also
rejected. This follows the SH7604 manual's FRT register access and OVF
read-then-write-zero rules ([Renesas, sections 11.2.5 and 11.3](https://www.renesas.com/ja/document/mah/superh-risc-engine-sh7604)).
The vblank counter may wrap; the decoder sorts modulo 32 bits. Tag zero is
reserved for uncommitted rows, so that one wrap window is omitted and reported
as a gap.

## Capture and decode

Pause the target and dump `sat_cpu_slack`, `44 * depth` bytes, through the
uncached alias. Locate its address and size in this exact image's ELF/map.
Only completed rows are exported, with the vblank written last; a zero tag is
ignored. Rings overwrite quickly. Capture repeated windows for a representative
route; do not interpret one retained ring as whole-run statistics.

```sh
python tools/cpu_slack_profile.py cpu_slack.bin \
  --tier EMULATOR --build-ref <exact-commit-and-flags> --scene stage02-warrior \
  --candidate-ticks 128 --reserve-ticks 128
```

The two 128-tick values are example hypotheses, not measured costs or prescribed
safety margins. Use the measured cost and chosen reserve for the proposed work.
The decoder prints raw rows, phase distributions, low-tail completion windows,
overruns and separate subsets where the slave was still busy. Invalid and
home-menu rows never supply a completion window.

If a `SAT_VDP1_PROFILE` image also fits, dump its rings in the same pause and
decode them with `tools/vdp1_profile.py`. Supply that JSON as
`--vdp1-report vdp1.json` to attach plots with the same source vblank and the
following vblank's presentation record. The two clocks remain separate;
the tool does not subtract slave timestamps from master timestamps.

## Decision before splitting work

The scheduler completion window is `period_ticks - game_done_tick` for a valid
completed gameplay window. This is an **upper bound on usable slack**, not a
measurement of free master cycles. The sample occurs before the lifted
`f_11ec` call. Its waiting behavior and any later `round_check`, `home_poll` or
`duel_step` iterations must be traced on the measured image before treating
the remainder as available work time. Candidate-fit fields explicitly test
only this upper bound.

Inspect the minimum and p05, overruns, and the rows paired with slow graphics;
a large average does not establish a usable budget on heavy frames.
Slave-busy at master completion does **not** say the slave is still building sprite
commands: it may already be drawing layers or waiting on VDP1. Source-frame
pairing narrows the question but cannot establish an unmeasured phase offset.

Only propose moving bounded work once its measured cost plus reserve fits the
relevant windows and its dependencies are ready in time. A future experiment
must keep a single owner for cache residency and VRAM writes, preserve command
order, and recheck whole-frame tails, game overruns, host graphics identity,
and target memory. This probe alone cannot justify a parallel command builder.

## Host checks

```sh
python -m unittest discover -s tests -p test_cpu_slack_profile.py -v
```

The suite compiles the actual recorder and extracted kernel idle sampler under
strict C90 at depths 2, 4 and 16. It checks interrupts during sampling,
incomplete/stale publication, wraps, overrun exclusion, ring ordering, corrupt
dumps, source-vblank joins, and disabled symbols/storage. The implementation
was also checked against the base kernel with profiling off: preprocessed
kernel tokens were unchanged in four flag configurations. These are HOST
checks, not a target link or timing measurement.
