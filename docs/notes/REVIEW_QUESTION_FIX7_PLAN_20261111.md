# Question for the super agent: is the fix7 plan right before we build it?

The owner will only test on the Saturn when confidence is high and does not want to diagnose by hand. So please challenge this plan before the lane builds fix7. Read-only: no builds, pushes, SD card or focus-stealing. No ROM or BIOS data off the PC.

## Where things stand (2026-11-11)
- **Disc F5** (b7b463f) boots on the real Saturn (JP, region-unlocked, Fenrir, 4 MB cart, CRT). It reached title, select and stage 1.
- **Console symptoms on F5:** vertical column stripes over all VDP2 layers (sprites clean); doubled HUD; PIC 23-25 per 60 vblanks with MISS 38-39 (completed frames about 21-22 per 60 vblanks).
- **Strict Ymir** reproduces the doubled HUD but not the stripes.
- **fix6** (lane/hwboot-20261110, e0d1490): all VDP2 register writes latched and committed once at V-blank IN (doubled HUD gone in 15 of 15 Ymir screenshots); pad SF/COMREG order fixed; new cycle pattern A0 `0123 EE67`, A1 `EEEE 44EE`, B0/B1 `EEEE E55E`.
- **Your earlier answer** (SUPER_ANSWER_HW_DISPLAY.md) said NBG0/NBG1 need two pattern-name reads each with ZMCTL=0x0101. The hwboot lane checked the Sega VDP2 manual chapter 3 (infochunk mirror p03_31, p03_33, p03_34, Tables 3.2-3.4) and agrees: fix6 is wrong. It also says the manual requires the access count to match exactly, and that Ymir never checks name counts (reduction multipliers commented out in vdp_state.hpp).
- **Decoded words** (low = T0-T3, high = T4-T7; 0-3 NBG names, 4-7 cells, E CPU, F none):
  - F5 in play: A0 `0123 FF67`, A1 `4444 4444`, B0/B1 `5555 5555`.
  - fix6: as above.
  - Your set: A0 `0167 0123`, A1 `44FF FFFF`, B0/B1 `F55F EEEE`.
- **fix6d** (diagnostic, shelved) lets the owner step four sets on a frozen view; the owner does not want to run that.

## Planned fix7 (one game disc)
1. Use the manual-correct pattern (your set or better).
2. Decide a CPU/transfer policy, because that set fills all 8 slots of A0, so VRAM-A has no CPU access during display: either move NBG0's map to A1 (MPABN0/MPCDN0 change, S2 tile cache 1024 to 896) or bound every VRAM-A write to blanking.
3. Keep the V-blank latch and the pad fix.
4. Add a manual-rule validator as a build gate (name counts, cell counts, legal slots, CPU slot pairs), plus try to make a private Ymir copy enforce the same rules so the stripes reproduce on F5 and not fix7.
5. Relabel the HUD's GAME as completed frames.

## Questions
1. **Is the plan right, and is there a better one?** In particular: is half-reduction (SAT_GFX_FIT=1, ZMCTL=0x0101, increment 1.09, i.e. 384 CPS2 columns shown on a 352 screen) the right way to fit the picture? Could we avoid reduction entirely (crop 352 of 384, or another standard approach) so every layer needs one name and one cell read? State what each option costs in look, VRAM slots and CPU time, and which has the highest chance of working on first test.
2. **Is "exactly the required number of reads" really what hardware needs?** Cite the manual precisely. Is there any evidence from shipped games, SGL source, libyaul or Saturn test ROMs, or hardware notes (not emulators) of what the chip does when a layer is short of name reads, and does it match "dropped columns"? How sure are you that this is the stripe cause, as a percentage, and what else could produce column dropouts on hardware but not in Ymir (VDP1 framebuffer, colour RAM mode, reduction pixel pairing, CRT/scaler)?
3. **CPU policy.** Given the packing, which is safer: moving the NBG0 map to A1, or blanking-only writes to VRAM-A? What does the game write to VRAM-A during display today (tile uploads, map rows, scroll data), how many bytes per frame, and does it fit in the blanking window? Does the split-bank CPU-slot rule (matching slot in both halves with a preceding no-access slot) apply to us at all with this RAMCTL?
4. **Speed.** With MISS 38-39 and about 21 completed frames per 60 vblanks, what share could VDP2 stalls explain versus master or slave work? What one extra console measurement would separate them, and can the readout capture it without the owner reading anything off the screen (e.g. a logged summary)? Tell us what not to claim about speed before a clean reading.
5. **Confidence plan.** What off-hardware evidence would justify telling the owner "test now" for fix7, and what residual risk remains? Give a go/no-go checklist the lane can run, with a probability that fix7 clears the stripes on first test.
6. **What are we missing?** Any other VDP2/VDP1 setup difference from SGL, bus-contention, or timing issue that could cause these symptoms, that the lane hasn't looked at?

## Constraints
Measure first; label emulated and console figures separately; every approximation is its own switch; no one-off patches where a standard method exists; fix7 stays one disc.

Write the answer to E:\AvP\learning\hwboot-review\SUPER_ANSWER_FIX7_PLAN.md.

---
## Update 2026-11-11 (after fix7 was built): review the build that would actually be tested
- **Candidate:** `lane/hwboot-20261110` at `32616ad` (code commit before the notes: see docs/notes/AVP_HWBOOT_FIX7_20261111.md). Staged disc `E:\AvP\package-integration\fenrir\avp_3h_A_fix7`. Build flags: defaults, SAT_GFX_FIT=1 (full picture, 384 to 352 half-reduction); SAT_GFX_FIT=0 builds the native crop with its own words from the same header. FIT 3 is an #error.
- **Single config source:** `saturn/gfx/sat_vdp2_cfg.h`. RAMCTL 0x1300, ZMCTL 0x0101 (fit 1) or 0x0000 (fit 0). NBG0 map moved to bank A1 at 0x3C000 (MPAB0=MPCD0=0x3C3C). Scroll 2 cache 895 tiles (was 1024), scroll 3 510 (was 512). hw_free 2,608, lw_free 96.
- **Final cycle words** (low = T0..T3, high = T4..T7):
  - fit 1: A0 `2311 67fe`, A1 `004f f4fe`, B0 and B1 `55ff eeee`.
  - fit 0: A0 `231f 67fe`, A1 `0f4f fffe`, B0 and B1 `5fff eeee`.
- **Gates:** tools/vdp2_cycle_check.py (build gate), tools/vdp2_trace_check.py (register trace of a strict-Ymir run), tests/vdp2_cycle_check_test.py. F5 and fix6 fail, fix7 passes. Ymir was NOT made to drop columns (it would encode a guess).
- **Changes since the first version of this question:** CPU policy chosen = moved map (live-transfer), not blanking-only. GAME relabelled DONE (vblanks minus MISS) with a raw FLIP/VBL line.
- **Open and added by the owner/orchestrator:** (a) CPS2 ports research (what MSHvSF and other CPS2 Saturn ports do about the 384 width) is running; results will be appended. (b) A previous review suggests a native 1:1 crop build (SAT_GFX_FIT=0 or 2) as the first hardware control and a coherent VBlank publication of the latched display state (the latch is per-register, and 0xFFFF is treated as "unset"). Please judge both.

---
## Update 2 2026-11-11: measured results on how the Saturn MSHvSF port and our game fit 384 columns (CPS2_PORTS_FIT_20261111.md)
All emulator (strict Ymir, own patched copy) measurements from logged VDP2 register WRITES; positive controls pass (Jo/SGL 352 reference logs TVMD 8101 + RAMCTL 1327, Brooklyn Bangout rc.47 logs TVMD 8110 + RAMCTL 1327, our G7 disc logs exactly sat_vdp2_cfg.h). Nothing here is console-measured.
- **Our game:** TVMD 0x8101 (352x224, no interlace), no black bars (edge to edge). NBG0/NBG1 and VDP1 sprites scaled (ZMCTL 0x0101, increment 1.0898, sprites 11/12); NBG2 HUD/text layer is NOT scaled (up to ~15 px out of register with the scaled art; HUD rows drop the middle 4 cells to stay flush).
- **MSHvSF Saturn (retail disc):** TVMD 0x8001 (352x224), no hi-res/interlace, ZMCTL 0 and zoom increments 1.0 over ~1.1M register writes (NO reduction, NO scaling), all four NBG layers on (16 colours, mixed 8x8/2x2 cells), RAMCTL 0x1300 same as ours. Steady cycles: A0/A1/B0 `6745 FFFE` (all four layers' characters T0-T3), B1 `CD01 23FE` (all four name reads), CPU slots wide open (T5-T7 on A0/A1/B0, T7 on B1). Visual comparison suggests a centre crop with the HUD re-placed for 352, not a squeeze (inference, +-4 px).
- **Other CPS2 Saturn ports:** none on this PC (only arcade zips for sfa3, xmen); anything else is unverified memory.
- **Crop cost (AvP):** 352 crop loses 16 px per side (outer 16 px of background is ~99-100% picture), plus HUD corners (1P tag, left 12 px of portrait, last 12 px of the 2P bar, end of PRESS START); full-width screens (character select panels, 48-column continue line, ranking, CREDITS) need a per-screen remap list. 320 crop loses 32 px per side and is not what MSHvSF does.
- **Research recommendation:** next console disc changes only the fit mode to the crop build (SAT_GFX_FIT=2); if stripes vanish the reduction schedule was the cause; if they stay, it's elsewhere. Lean: 352 crop as the product choice (removes scaled sprites and reduction reads, one pixel grid).

### Questions added
7. Given MSHvSF runs a no-reduction 352 four-NBG layout on retail hardware with those cycle words, is that a stronger basis than the manual-derived reduction schedule? Do its words (characters of all four layers in T0-T3 of A0/A1/B0, names in B1) suggest a pattern we should copy for the native build instead of our fit-0 words (`231f 67fe / 0f4f fffe / 5fff eeee`)? Please check ours against the manual and against MSHvSF's.
8. Which is the better first console disc: fix7 (full fit, corrected schedule), fix7n (native crop, FIT 0 or 2) or both, and what evidence would let the owner skip comparing them by eye?
9. Is the unscaled HUD layer (NBG2) misregistering up to ~15 px against scaled art a visible product problem that argues for the crop, and does the crop's per-screen remap list look tractable?
