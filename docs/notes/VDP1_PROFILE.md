# VDP1 deadline and submission diagnostics

Evidence for this change: **HOST synthetic tests only**. Saturn target build,
MAME comparison, emulator capture and physical Saturn run remain **UNRUN**.
The source-function census is unchanged; this changes the graphics adapter.

## Correctness fixes

- `SAT_VLOG` reserves its sixteen plot-serial polygons in each 32 KB command
  table. Sprite capacity is 1000 with that flag, 1016 otherwise; the existing
  four-readout-bar reserve remains. Both tables are checked at maximum capacity.
- A late VDP1 never triggers a forced framebuffer change. The slave's bounded
  waits return without submitting when completion, change acknowledgement or
  the CEF-clear latch is absent. The next graphics handoff retries; game logic
  continues. An emulator that never produces CEF will retain the last complete
  picture rather than present an unfinished one.
- The completion wait precedes palette, cache and command writes. Only a
  successfully submitted plot flips the command table and owns the previous
  texture stamp. Abandoned builds cannot release the last plot's texture slots.
  A failure-only scan restores prior-stamp protection to every sprite slot
  touched by the abandoned build, including shared hits and new uploads.
- The first plot has no previous change to await, so a CEF value left by boot
  firmware cannot prevent the first submission.

These changes do not establish a frame-rate improvement. They remove unsafe
fallbacks and make the next measurement attributable.

## Diagnostic build

Add `-DSAT_VDP1_PROFILE` to `KERNEL_CFLAGS`, which this build passes to both
`saturn/rt/kernel.c` and `saturn/gfx/sat_gfx.c`. This is off by default and adds
no default storage or instrumentation calls. Do not enable `SAT_VLOG_VDP1` for
the normal scheduling measurement: that older probe deliberately waits for
VDP1 and changes the slave's schedule.

Declared storage under a 32-bit target ABI:

| Configuration | Rings | Current row, counters and snapshot | Total, before linker padding |
| --- | ---: | ---: | ---: |
| Off | 0 | 0 | 0 bytes |
| Default depth 16 | 1,984 | 132 | 2,116 bytes |
| `-DSAT_VDP1_PROFILE_DEPTH=2` | 248 | 132 | 380 bytes |

Depth must be a power of two, at least two. Respect the existing linker limits.
The zero-slack Wolverine image has **not** been shown to fit either enabled
configuration; use a separate nonguest diagnostic build unless its target link
proves otherwise. Do not enlarge the memory arenas for this probe.

## Capture and interpretation

Pause the target, locate symbols in its ELF/map, and dump both arrays through
the uncached alias:

- `sat_vdp1_plots`: `depth * 100` bytes, written by the slave, one row per draw
  attempt. A row includes its successful plot serial or an explicit timeout,
  source vblank, stage and arcade character slots, snapshot duration, command
  build duration, VDP1 texture upload bytes/time, separate previous-end,
  frame-change and latch waits, submission point, layer work and CPU finish.
- `sat_vdp1_frames`: `depth * 24` bytes, written by the master, one row per
  vblank. Includes started/shown serials, raw EDSR and slave-busy status.

Example decoder, for big-endian target words:

```sh
python tools/vdp1_profile.py --plots plots.bin --frames frames.bin
```

These are bounded rings, not whole-run totals. Collect repeatedly for a long
route or raise depth only when the target fits it. Row word zero is committed
last; zero means unused/in-progress. The decoder handles counter rollover and
reports gaps. Keep the ELF, flags, stage, input route and capture tier with the
readback. Arcade slot 1 in a guest build can mean Wolverine; retain the guest
flags because the capture reports the underlying slot.

Work counters record source texels and clipped destination **bounding-box**
pixels, including overdraw and transparent texels. The current sprite writer
uses 4bpp colour-bank mode and no half-transparency; the mode bitset and
half-transparency count make this explicit. The full-screen clear is reported
separately as 78,848 pixels. No clear is removed by this patch.

Master snapshot/handoff ticks and slave draw ticks are different clocks.
Never subtract their raw values. Durations within each clock are modulo 16 bits;
keep captures inside that timer's wrap period. If CEF is already set after the
layer work, `raster_upper_ticks` is only an **upper bound** measured on the slave
from submission to that observation. Otherwise it is `0xffffffff`; vblank EDSR
samples show which deadlines were missed, without inventing a drawing duration.

A framebuffer-change request does not prove the display showed that picture.
Use `SAT_VLOG` picture serials when actual displayed-frame cadence is required.
Slave-busy samples overlap the presentation classes and must not be added to
their percentages. Yaba's recorded flat timing model is not hardware fill proof.

## Host checks

```sh
gcc -std=c90 -pedantic -Wall -Wextra -Werror -DSAT_GFX_HOST \
  saturn/gfx/host_test.c saturn/gfx/sat_gfx.c -o /tmp/gfx-test
/tmp/gfx-test
gcc -std=c90 -pedantic -Wall -Wextra -Werror -DSAT_VDP1_PROFILE \
  -DSAT_VLOG tests/vdp1_presentation_test.c -o /tmp/presentation-test
/tmp/presentation-test
python -m unittest discover -s tests -p test_vdp1_profile.py
```

The presentation fixture compiles the real driver with a synthetic tile pack,
emulated register storage and programmable clock. It tests both table bounds,
wait timeouts across timer rollover, unchanged resources while a plot is busy,
change/latch retries, first-plot CEF and texture ownership. It is not a Saturn
rasterizer and makes no timing or visual-fidelity claim.
