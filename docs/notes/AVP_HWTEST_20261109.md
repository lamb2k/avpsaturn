# Console A/B for sprite combining and hardware clear: readout and test discs, 2026-11-09 (EMULATOR Yaba VideoCore 1 for the readout check only; hardware UNRUN)

Branch `lane/hwtest-20261109`, off `lane/fps-held-20261109` (457508b: FAST_LIST, NAMES_LAZY, PAL_KEEP). Evidence: `E:\AvP\learning\lane-hwtest`.
Packages for the ODE: `E:\AvP\package-hwtest-20261109\{1_off,2_hwclr,3_pair,4_both}` (this PC only; nothing is copied to a card).

## Build
Recipe of the Wolverine disc plus the readout and the three held-picture switches, one flag set per arm (assets v41/D):
`-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 -DSAT_PERF_HUD -DSAT_GUEST_FAST_LIST=1 -DSAT_GUEST_NAMES_LAZY=1 -DSAT_GUEST_PAL_KEEP=1`
then nothing (off), `-DSAT_VDP1_HW_ERASE=1` (hwclr), `-DSAT_GFX_PAIR_REUSE=1` (pair), both (both). The arm name on the readout comes from those two defines, so a disc cannot be mislabelled.

| Arm | rc | hw_free | lw_free |
| --- | ---: | ---: | ---: |
| off | 0 | 1,680 | 104 |
| hwclr | 0 | 668 | 104 |
| pair | 0 | 1,224 | 104 |
| both | 0 | 204 | 104 |

Without the readout the same flags leave 4,476 high bytes free, so SAT_PERF_HUD costs about 2.8 KB of high work RAM (code in Os, counters and two text lines); none in low work RAM.
The first version cost 4.3 KB and the both arm did not link; the formatting helpers are now `optimize("Os")` and out of line.
A PAL_KEEP defect is fixed on this branch (sat_gfx.c snapshot_begin): `pal0_same` was set at page 0 and never cleared, so while Wolverine's rows were kept, pages 1 and up (scroll 1 palette, the fades) were not recopied either. The keep now applies to page 0 only. The held lane should take this.
Gates: `tools/wolverine/fit.py` on the workdir, assets v41/D: `gate True fail []` (the stage files do not depend on KERNEL_CFLAGS). WSL `python3 -m unittest discover -s tests`: 91 run, 61 pass, 30 load errors (private MAME .deps), 0 failures, as the baseline.

## The readout (SAT_PERF_HUD, default off, needs SAT_HOME)
Two lines of home-font text at rows 24 and 25 on NBG3, a solid black band behind them, refreshed about once a second, frozen after `SAT_PERF_HUD_WINDOW` (3,600) counted vblanks. Reset: pad L + Z + R together.
Counting runs only while a stage is played (RAMB 0x8001 == 2, a character slot in use, no menu or load: `!sat_home_hold && !sat_home_mode`). The pause menu, the NOW LOADING card, continue screens and the title do not count.
Colours are the menus' (palette banks 62 and 63); the page is recopied from the game each frame with a marked sum, so the slave's palette scan sees no change. It takes the menu layer's set-up without the colour calculation, so the band is plain black.
Storage is all in high work RAM (about 240 B of data); no profile rings are used, so none of the VDP1_PROFILE cost is in the arms.

| Field | Written by | Meaning |
| --- | --- | --- |
| F | master vblank hook | counted vblanks |
| N / H / S / L | master vblank hook, `sat_gfx_vblank` | share of those vblanks that showed a new picture (shown serial moved), held the old picture (a plot started and not finished at the vblank), had nothing to show while the slave was still building (skip), had nothing to show and the slave idle (late). Same classifier as agg2_lib.py. |
| D mean/max | slave | FRT ticks from the PTMR write to the first time EDSR.CEF is seen set, see below |
| C | slave | sprite commands per submitted plot (`sat_gfx_stats.commands`) |
| B | slave | ticks of `draw_sprites` minus texture upload time, per plot |
| W mean/max | slave | ticks `plot_wait_end` waited at the start of a draw for the previous plot |
| P | slave | percent of D figures that are precise (idle poll or wait) and not a layer-pass bound |

What D is on a console: nothing modelled. The slave's FRT is read at the PTMR write. The first sight of CEF set gives the end: (1) at six points in the draw (after plot start, row scroll, layer wait and each layer pass), a bound by the segment; (2) in the slave's idle loop, which polls EDSR with about 40 empty iterations between reads (about 15 us, 5 percent bus duty), precise to a few ticks; (3) at the next draw start, when the plot outlasts the frame and `plot_wait_end` spins, exact (the slave's timer at its wake, `sat_gfx_hud_pre`, plus the wait). Values over 20,000 ticks are discarded (timer wrap guard). P is the share from (2) and (3).
The idle poll is a small extra bus load on every arm alike. Tick = 128 / 26.874 MHz = 4.76 us in the 352 wide mode; a field is 3,503 ticks. All of it is only as good as the EDSR CEF semantics the existing renderer already depends on (CEF clears when the next plot starts or the change is latched).
A figure from the readout is one console run of a fixed fight, not a distribution; the README asks for photos from the same stage position on all discs.

## Workload
The attract demo is not available: in this build the title waits indefinitely after the menu's 30 s idle (observed 13,500 vblanks, 225 s, at the title in Yaba with no demo gameplay), so there is no demo to count. The workload is a 60 s manual fight, Stage 02 (Round 1, Coffee Shop), ideally Wolverine (character select top right, the Schaefer slot). Counters start by themselves at the first controlled frame of the stage; L + Z + R restarts the window when the first aliens are on screen; DONE and frozen figures after 3,600 counted frames.
Wolverine replaces only the Schaefer slot, so a native character does not exercise the held-picture fixes; the README says to pick the top right box.

## Yaba (EMULATOR, proves the readout works, not timing)
Own Yaba copy, MCP port 9719, VideoCore 1. Each arm's disc boots, plays into stage 02 and shows and updates the readout (captures in `E:\AvP\learning\lane-hwtest\shots_*`, not committed). L + Z + R sent by PostMessage reset the counters (467 frames -> 79). A 900-vblank build froze with DONE. The readout does not render on the title and continue screens in Yaba VideoCore 1 (nor does the existing title menu on the discs I tried, including the owner's v4 disc), it does on the story, select and stage screens. Not understood; the stage is where it is needed.
Yaba's numbers (for example D about 750 with a flat model, W 4) are the model, not the console.
