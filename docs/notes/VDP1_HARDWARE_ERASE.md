# Partial hardware erase experiment

Evidence: **HOST**. Target compilation, emulator display/timing and **HARDWARE are UNRUN**. Default builds retain the existing full-screen polygon clear. This experiment has no measured FPS improvement.

## Selection and purpose

Add `-DSAT_VDP1_HW_ERASE` to `KERNEL_CFLAGS` on a separate test build. Compile both the kernel and graphics with the flag; the ordinary build script passes it to both. Omit the flag or set `-DSAT_VDP1_HW_ERASE=0` for the baseline. Start from the same source, ROM inputs, build flags and replay for each comparison.

The ordinary renderer clears 352 × 224 pixels with a VDP1 polygon before every submitted sprite list. The experiment uses manual vertical-blank erase for rows 0–159 and retains a clear polygon for rows 160–223. It still emits one clear command and does not change sprite textures, commands, colour modes or fitting. The polygon covers 22,528 pixels on an eligible plot, versus 78,848 on the baseline. This is a reduction in commanded clear area, not a prediction of time saved.

## Hardware basis

The primary source is Sega's [VDP1 User's Manual, ST-013-R3-061694](https://antime.kapsi.fi/sega/files/ST-013-R3-061694.pdf), printed pages 35–36, 40, 47–50. Its erase-and-change sequence enables VBE immediately at V-blank IN, changes buffers after the blank, and disables VBE after OUT. VBE otherwise repeats on later blanks. Erase registers become active on a framebuffer change. An incomplete erase needs polygon coverage. The NTSC 352 × 224 budget is 63,180 erase pixels; full-screen erase exceeds it. For EWRR X = 44, the manual's conservative area formula gives `(44 + 1) × 160 × 8 = 57,600`, within that budget. EWLR is zero, EWDR is zero, and EWRR's last row is 159. The implementation is restricted to the current 352 × 224 display mode.

The OUT entry uses GCC's SH [`interrupt_handler` attribute](https://gcc.gnu.org/onlinedocs/gcc-4.2.4/gcc/Function-Attributes.html). The target build must confirm the generated entry saves the interrupted registers and returns with RTE. No new assembly or build-script preprocessing is required.

## Ownership and fallbacks

The serial identifies the completed plot that becomes the new displayed buffer. The erase clears the **old displayed buffer**, which then becomes the drawing buffer. The first change after initialization or recovery leaves VBE off while the programmed erase registers become active. The next list remains full-clear; only matching OUT and cleared CEF establish that those registers are primed for a later erase. Thus the first two lists after initialization use full clear. The master enables VBE only alongside an existing CEF-confirmed change with primed registers. OUT clears VBE before publishing that change's serial. The slave reduces the clear only after CEF has cleared, the serial matches `plot_shown`, the erase state is primed and unsuppressed, and the command table's actual local origin is zero. A marker from an older change cannot certify another physical buffer.

Every list is initially built with a full clear. Only the inactive table is adjusted immediately before submitting it. The first plots, missing OUT, serial mismatch, zero serial at rollover, and either nonzero origin coordinate retain the full polygon. The short OUT entry raises the master interrupt mask to 15 until RTE, so higher-priority IN cannot rearm another serial halfway through cleanup. An OUT handler that runs during a newer blank cannot publish completion. At the next IN, an old armed erase is canceled before the decision to hold the displayed picture; it cannot remain enabled just because no new picture is ready.

The existing stuck-CEF recovery remains bounded. Any extra change request invalidates the erase state. Missing-end recovery replays the old list **without changing its command table or textures**; absence of CEF gives no ownership of those inputs. It then forces a full clear on the next newly built list with a confirmed latch. A save-state restore that replaced the chip's physical buffer contents may therefore show an imperfect replay before that new full-clear plot, just as the existing recovery cannot guarantee the restored chip's buffer parity. Do not treat the host test as proof that save states or faulty CEF timing are visually correct.

The stage loader masks interrupts and lets GFS replace the SCU vectors. Before a long load it now suspends the experiment: with master interrupts masked, it waits a bounded interval for active display, disables any armed VBE, and invalidates the ready serial and priming. If TVSTAT never leaves blank, it returns failure **without writing TVMR**. The kernel restores interrupts, rolls back the stage-load bookkeeping and loading indicator, and retries later. Home restart also suspends before waiting for the slave and jumping to `sat_main`, which clears the bookkeeping before loading the front-end file; failed suspension restores interrupts and leaves the current game running. The next normal IN can cancel the stale erase in its proper window. After a load, `irq_enable` installs both IN and OUT vectors again.

## Capture and acceptance

Read these exported 32-bit counters through their uncached addresses from the ELF/map file:

| Symbol | Meaning |
| --- | --- |
| `sat_gfx_erase_reduced` | Newly submitted lists using the remainder polygon |
| `sat_gfx_erase_full` | Newly submitted lists keeping the full polygon |
| `sat_gfx_erase_canceled` | Stale IN cleanup or explicit load suspension |

With `SAT_VDP1_PROFILE`, `VP_CLEAR_PIXELS` reports the polygon area actually submitted; it excludes the separate hardware erase. The existing raster upper bound is still an upper bound. For an isolated raster measurement, the existing `SAT_VLOG_VDP1` build polls CEF immediately after PTMR on the slave's own timer, at the cost of blocking that CPU. Do not compare that blocking build's cadence directly with a normal build. The post-layer `SAT_READOUT` Y-button wait only measures the remaining wait and is not total raster duration.

Use identical fight replays for baseline/experiment, repeat the captures, and record new-picture share, held/CPU/late shares, CPU and submit times, and these counters. Inspect trails on all four edges, horizontal and vertical screen adjustment, menus, stage loads, held refreshes and recovery. Validate both buffers over many alternations. A Saturn run is required to show that the OUT hook and erase timing meet the chip's deadlines and that the reduced raster work outweighs the added interrupt and register traffic. Yaba's flat modeled raster duration cannot establish that gain.

## Memory and validation

The flag adds seven 32-bit scalar words: four synchronization values and three counters, **28 declared bytes of ordinary BSS on the 32-bit target ABI**, before any linker padding. It adds no low-work-RAM section, command-table slot, texture slot or dedicated stack. The IRQ uses the interrupted master stack; its generated register-save space and total linked code size still require target validation. Profiling, if separately enabled, retains its own larger memory cost. Do not claim a combined guest build fits until the actual SH-2 link succeeds.

HOST commands:

```sh
python -m unittest discover -s tests -p test_vdp1_hardware_erase.py
gcc -std=c90 -pedantic -Wall -Wextra -Werror tests/vdp1_hardware_erase_test.c -o /tmp/vdp1-erase-test
/tmp/vdp1-erase-test
gcc -std=c90 -pedantic -Wall -Wextra -Werror -DSAT_VDP1_HW_ERASE -DSAT_VDP1_PROFILE -DSAT_VLOG tests/vdp1_presentation_test.c -o /tmp/vdp1-presentation-test
/tmp/vdp1-presentation-test
bash tests/host_gfx_layers_identity.sh /path/to/baseline-checkout
```

The dedicated test runs the actual renderer and decodes its erase rectangle and clear polygon into a small two-buffer coverage model. It distinguishes programmed and latched erase registers, starting with stale firmware values. It checks priming, normal alternation, a fully dirty buffer, held frames, stale/missing OUT, wrong/zero serials, both origin coordinates, abandoned builds, initialization, latch recovery, untouched old tables on replot, and bounded load suspension across timer wrap. This is not a VDP1 rasterizer or timing model. The default-off identity fixture compares all VDP1/VDP2 VRAM, CRAM and registers over 600 frames at FIT 1 and 0, sequentially and with delayed threaded handoff. Omitted and explicit-zero flags also produce byte-identical 32-bit HOST renderer objects to the baseline. The GFS rollback hook and SH-2 interrupt code still require a target build and run.
