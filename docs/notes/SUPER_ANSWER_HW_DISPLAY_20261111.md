# Super agent answer: hardware display question (pasted by owner 2026-11-11)

Source: owner pasted the summary below. The linked full handoff (SUPER_ANSWER_HW_DISPLAY.md in the super agent's sandbox) was not on disk, so only this summary is saved. Review of F5 at 1319602 / b7b463f. Read-only; nothing built or tested on hardware.

## 1. Wrong settings
Scaled backgrounds have too few pattern-NAME fetches and the schedule leaves no qualifying CPU slot during active display.
- SAT_GFX_FIT=1 enables half-reduction on NBG0 and NBG1 (ZMCTL=0x0101). That needs TWO pattern-name fetches per layer; the F5 schedule gives one. Extra character-data fetches do not make up for it. (sat_gfx.c L3124-3154)
- Needs: NBG0 2, NBG1 2, NBG2 (HUD) 1, NBG3 (menu text) 1. Supplied: 1, 1, 1, 1.
- 352x224 keeps all eight timing slots (T6/T7 available). This is not "352 disables half the slots".
- Keep RAMCTL=0x1300 (SGL's 0x1327 only differs in unused rotation-bank bits). Clock change and TVMD now match the SGL reference.
- Split banks need matching CPU slots in both halves with a preceding idle slot. F5's 4444/4444 and 5555/5555 character schedules give none while those layers are on. The slave still writes VDP2 during drawing, so transfer stalls are a serious performance suspect.

First diagnostic schedule (same memory layout, full fit; derived and cross-checked, NOT hardware-tested; leaves no active-display CPU access to VRAM-A, so use with a preloaded frozen view or bounded blank-period transfers):
| Reg | Low | High |
|---|---|---|
| CYCA0 | 0x0167 | 0x0123 |
| CYCA1 | 0x44FF | 0xFFFF |
| CYCB0 | 0xF55F | 0xEEEE |
| CYCB1 | 0xF55F | 0xEEEE |
| RAMCTL | 0x1300 | |

Live-transfer candidate (not drop-in): move NBG0 map to A1 at 0x3C000, MPABN0=MPCDN0=0x3C3C, init the moved map, cut S2 tile cache 1024 to 896 entries:
| Reg | Low | High |
|---|---|---|
| CYCA0 | 0x2311 | 0x67FE |
| CYCA1 | 0x004F | 0xF4FE |
| CYCB0 | 0x55FF | 0xEEEE |
| CYCB1 | 0x55FF | 0xEEEE |

## 2. Doubled HUD
Slave rewrote SCYN2 (0x25F80092) at the end of sat_gfx_draw with no VBlank gate. Ymir resets NBG2's running vertical position on any write to that register, even an unchanged value, so the HUD restarts partway down. Map geometry (64x64, 8x8 cells, two-word names at 0x4000) looks right. Fix: prepare scroll state in RAM, commit once in VBlank.

## 3. Why Ymir shows the HUD bug but not the stripes
Different emulator parts. Upstream Ymir has its reduction-related access-count multipliers commented out (vdp_state.hpp L525-540) and later checks accept pattern-name access by slot presence without validating the count needed for reduction. So it can reproduce the register-timing bug and let an invalid schedule look clean. Check the local patched Ymir against upstream before treating this as definitive.
NBG2's own fetch pair is legal: if isolated NBG2 still loses columns, NBG0/NBG1 shortage does not explain it.
Diagnostic: a frozen numbered-tile view with layer isolation and a VDP1 status overlay, preloaded, no tile/map/palette updates, with a VBlank-latched toggle between the F5 cycle words and the corrected schedule; same graphics, fit, scroll origins and memory placement.

## 4. 23-25 pictures/s
The readout is misleading. GAME 60 counts writes to the object-bank selector, not completed game frames. PIC/GAME are normalised to 60 vblanks; MISS/SKIP/HELD are raw counts over the real window; do not add them. HELD can count one plot repeatedly.
Ranked: (1) VDP2 access stalls from live writes, (2) master/slave work and sync, (3) VDP1 submit/completion timing (PTMR vs next vblank), (4) cart/low-RAM/shared-bus cost, (5) tile-upload volume and cache churn.
Next console capture: scheduler completions, master/slave stage times, upload bytes and time, VDP1 submit/complete timing, recovery counters. No evidence yet that the display fix alone restores 60.

## 5. Minimal fix
1. Centralise VDP2 display state: slave prepares a pending record, the VBlank owner commits it (explicit ownership, cache-through handoff).
2. Make the memory schedule and transfer policy agree: prove the display with the frozen diagnostic first, then budget live updates in blanking or adopt a validated allocation with CPU slots.
3. Update every register writer: init, menus, FPS/perf HUDs, fit-mode transitions use one coherent profile.
4. Retest with corrected counters: one HUD, clean isolated backgrounds, no active-display scroll writes, clear attribution of remaining missed deadlines.
