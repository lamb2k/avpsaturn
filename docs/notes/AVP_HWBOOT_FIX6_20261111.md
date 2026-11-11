# fix6: first console run of fix5, decoded; VDP2 timing fixes (2026-11-11)

Branch `lane/hwboot-20261110`. fix5 (`c0e4074`) was the first disc to reach the AvP title on the owner's JP Saturn (Fenrir, 4 MB cart). Photos and measurements below are CONSOLE; the Ymir results are EMULATOR.

## Console observations (fix5)
- Title, character select, stage 1 all draw. Vertical column dropouts on all VDP2 scroll art (logo, backdrop, HUD text), VDP1 sprites and the NBG3 menu text are clean.
- Doubled HUD in stage 1 (HUD, PRESS START, dialogue box, ROUND banner each twice, second copy ~16 to 157 lines lower, different every picture); character select shows PRESS START twice.
- Readout, stage 1 start, 1P Schaefer, CONSOLE: `PIC 25 GAME 60 MISS 39 SKIP 35 HELD 25`; second photo `PIC 23 GAME 60 MISS 38 SKIP 38 HELD 11`; character select `PIC 55 GAME 60 SKIP 5`. Emulator (strict Ymir) stage 1: PIC 54 to 58, SKIP 4 to 6.
- No sound was the owner's audio cables (retracted).

## The "stop screen" photo is a normal loading screen
Row geometry in `saturn/rt/boot.c` (`diag_code`): 16 bits, white = 1, MSB on top, one bit = 3 lines + 1 grey line, first bit at line 150. Measured on the photo (line pitch 20.6 px): bits 0001 0000 0101 1100 = **0x105C**. That is `diag_info(0x1000 | cart ID)`: cart ID 0x5C, the value the fix5 README lists as expected. No FE04/FE06/FE09/FE0A, no whole-screen red/magenta flash (a stop is always preceded by the flash and shows the code, then the PC). The diagonal split and colour changes are the camera's shutter against the CRT scan. So this photo is the loader's progress display, not an exception; no crash was decoded. (Confidence: high on the bit value, medium that it was taken during the load rather than at a hang; the owner should say if it stayed there for more than ~2 minutes.)

## Doubled HUD: found, reproduced, fixed (EMULATOR)
Reproduced in strict Ymir on fix5 (see settings below). Evidence chain: NBG2 off (`SAT_GFX_BGMASK=0xB`) removes both HUD copies, so both are the scroll-1 layer; a VDP2 VRAM write log (patched Ymir, shadow dumped every 20 pictures) shows the scroll 1 name table holds ONE HUD (rows 2 to 5); the register log shows SCYN2 always 0x10. What varies is *when* the slave writes it: `sat_gfx_draw` wrote BGON, all scroll and priority registers at the end of each picture, at any beam line. Ymir (`vdp_renderer_sw.cpp`, case 0x092/0x096) resets the NBG2/NBG3 vertical counter on a SCYN2/SCYN3 write, so the layer restarts from its top at that line: the HUD shows again at the line of the write. The console does the same. Fix: `sat_gfx_vdp2_latch()`; every VDP2 register the draw (and the readout setup) writes goes into a table, the master writes the table to the chip at the start of `sat_gfx_vblank` (V-blank IN). SGL's own rule. Cost: 272 B high work RAM (hw_free 2,056 to 1,640), about 140 uncached reads and ~28 register writes per vblank.

## Stripes: inferred cause (CONSOLE test needed)
Not reproducible in any emulator tried (Yaba, Ymir strict; Ymir models some cycle-pattern rules, `CalcAccessPatterns` in vdp_state.hpp, but not this). Which layers striped: NBG0 (scroll 2) and NBG1 (scroll 3). Which were clean: NBG2 (scroll 1 cells) and NBG3 (menu, readout), each with exactly one cell read slot after its name slot, in the name bank.

fix5 pattern (CYCA0..B1): A0 `012f ff6f` (names T0 T1 T2, NBG2 cells T6, T3 T4 T5 T7 no access), A1 `4444 4444` (NBG0 cells in all 8 slots), B0 and B1 `5555 5555` (NBG1 cells in all 8 slots), and the menus/readout wrote A0 `0123 ff67`. Problems:
1. NBG0 has names at T0 and cells at T0 to T7; NBG1 has names at T1 and cells at T0 to T7. Ymir's rule table (from console tests of shipped games) lists which cell slots are legal for a name slot: names T0 allows all but T3; names T1 allows all but T4 (and Ymir's NBG0/NBG1-at-T0 shortcut). Slots T0..T4 for NBG1 are at or before the name read. Shipped games use ONE cell slot per bank per layer (Cyberbots, X-Men vs. SF cases in the Ymir comments). Eight cell reads per bank is the one thing this layout did that none of those did.
2. No bank has a CPU slot (E). SGL's slInitSystem pattern (logged from a Jo/SGL 352x224 program in Ymir): A0, A1, B0 `FEEE EEEE`, B1 `0441 55FE`: everything nobody reads is E. With no CPU slot, SH-2 VRAM writes can only complete in blanking: this probably also costs frame time (PIC 23 to 25).
Not changed: RAMCTL stays 0x1300 (SGL writes 0x1327; the low bits assign rotation data banks and only matter with RBG0 on). Zoom (ZMCTL 0x0101, NBG0/NBG1 half reduction for the 384 on 352 fit) stays, with two cell reads per bank for the doubled demand (Ymir's disabled `expectedCount *= 2` hint).

fix6 pattern: A0 `0123 ee67` (names NBG0..3 T0..T3, T4 T5 E, NBG2 cells T6, NBG3 cells T7); A1 `eeee 44ee` (NBG0 cells T4 T5); B0, B1 `eeee e55e` (NBG1 cells T5 T6). Legal for every name slot by Ymir's masks. NBG3's slots are always present (no more toggling per picture). If the stripes remain, the next candidate is the half-reduction mode itself (FIT 1): a build with SAT_GFX_FIT 0 or 2 removes zoom; and the VDP2 layers with a 1x1 cell/ 1 word name set-up like NBG3's.

## Other fix: SMPC pad poll order (EMULATOR)
`sat_pad_tick` wrote COMREG (INTBACK) and then SF=1. In strict Ymir, once the V-blank handler was slightly longer (the latch) the command finished before the SF write and SF stayed set for good: INTBACK count stopped at 429 and the pad never answered. Now SF is written first, then COMREG (SMPC manual order). Deterministic; found by the INTBACK count in the register log.

## Verification (EMULATOR, strict Ymir)
- Settings: `E:\AvP\learning\lane-hwboot\ymir_strict\ymir-sdl3.exe` (Ymir 0.4.0-dev baseline a9f0cdae + register/exception logging patch, `sh2p`), profile `ymir_prof`: JP IPL 1.01 (profile roms/ipl), auto region Japan first, 32 Mbit (4 MB) DRAM cart, EmulateSH2Cache on, SMPC pad from `ymir_pad.txt`, window SW_SHOWNOACTIVATE. Disc: `avp_3h_A_fix6.cue` (staged) and the same ISO.
- fix5 reproduces the doubled HUD (about two thirds of stage-1 shots) and PIC dips with SKIP; fix6: 0 of 15 stage-1 shots doubled (HUD, dialogue, ROUND banner single), pad works through title, menu, character select, stage 1.
- Register log (fix6): vectors 4/6/9/10/12 never entered, 0 misaligned data accesses, the slave writes no display register directly, access cycles end at the new values, latched registers written once per V-blank at one PC.
- Loader data check `boot data addresses: ok` (build gate `check_boot_data.py`). RAM: hw_free 1,640 (was 2,056), lw_free 96.
- Yaba: NOT run this time (the shared Yaba profile/ini is the owner's; no separate Yaba install was configured for this lane). The earlier lane Yaba runs (real BIOS) ran the same loader.
- NOT verified without the console: the stripes (cycle pattern change), the PIC rate effect of the CPU slots.
