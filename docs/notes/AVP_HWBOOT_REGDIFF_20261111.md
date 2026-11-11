# Hardware start-up parity with SGL / Jo (Brooklyn): register-write comparison, 2026-11-11

EMULATOR evidence (strict Ymir, real JP 1.01 BIOS, 4 MB DRAM cart, SH-2 cache on); hardware UNRUN. Branch `lane/hwboot-20261110`.

## Method
- A patched copy of Ymir (`E:\AvP\learning\lane-hwboot\sh2p`, baseline tree untouched) logs every CPU write to the SMPC, SCU (incl. IMS/IST, ASR0/AREF, DMA, timers), VDP1 and VDP2 registers, the SCSP and
  CD-block registers, the cart enable and SINIT/MINIT, and the SH-2 on-chip registers, with CPU, PC, width and value, plus every interrupt/exception entry. Also logs misaligned accesses and exceptions.
- Runs (all: JP 1.01 BIOS, 4 MB cart): **sgl352** = a Jo/SGL program built here with `slInitSystem(TV_352x224)` (Jo's own init, `sgl_ref/`), **brooklyn** = Brooklyn Bangout rc.47 (TV_320x240),
  **ours** = fix4 (7b4c259 with SAT_BOOT_DIAG) and the default build.
- Phase anchor: the BIOS phase is byte-identical across all runs up to the CD read of the boot sector; the app starts at the SGL startup's cache purge (`SH2.092 = 0x11` at PC 0x06004012) or, for ours,
  the loader's first VDP2 write. Tools: `regdiff.py`, `phasecmp.py`.

## The standard SGL path, as logged (sgl352)
`SYS_CHGSYSCK(1)` is the BIOS service behind slInitSystem's clock change (`SEGA_SYS.H`: function pointer at 0x06000320; 0 = 26 MHz / 320-640 modes, 1 = 28 MHz / 352-704 modes). Its log, all from BIOS ROM:
SMPC RESDISA (1A), SCU AIACK/AREF = 0, WDT/NMI set-up, **SMPC CKCHG352 (0E)**, the NMI, SMPC MSHON (00), SCU RSEL = 1, VDP2 TVMD = 1, SCU DMA channels 0-2 zeroed and mode 7, DSTP = 0,
**ASR0 = ASR1 = 0x1FF01FF0, AREF = 0x1F**, timers T0C = 0x3FF, T1S = 0x1FF, T1MD = 0, IMS/IST = 0xFFFFFFFF, SMPC RESENAB (19). Then slInitSystem: SSHOFF (03), SSHON (02), VDP1 (FBCR, TVMR, PTMR = 2,
EWDR/EWLR = 0, EWRR), then **every VDP2 register** (TVMD = 0x0101 then 0x8101, RAMCTL = 0x1327, CYC*, BGON, CHCTL*, PNC*, MPxx, scroll/zoom, window, line, colour calc, priorities, colour offset), the vblank
vector, IMS = 0xFFFFF17C.

## Diff table (first 10 pictures; sgl352 / brooklyn / ours fix4 and fix5)
| Phase | Register | SGL | Brooklyn (320x240) | Ours | Verdict |
|---|---|---|---|---|---|
| BIOS hand-off | all | identical in all runs up to the boot-sector read | same | same | none |
| clock change | SMPC commands 1A, 0E, 00, 19 | yes (BIOS service) | none (stays 320) | **fix3: none (the bug); fix4: hand-written 0E; fix5: BIOS service, same 1A,0E,00,19** | fixed: required for 352 on the console |
| clock change | SCU DMA/ASR/AREF/timers reset | by the BIOS service | n/a | by the BIOS service (fix5) | ours now equal; the cart is brought up after it |
| cart / A-bus | ASR0 / AREF / 0x257EFFFE | Jo writes 0x25FE0080 / 0x25FE0033 (wrong addresses, so BIOS defaults stay) | same as sgl | BIOS defaults first, enable + verify, then ASR0 = 0x23301FF0, AREF = 0x13, re-verify, fall back to defaults | deviation (ours is the documented ST-TECH-47 timing; verified with fall-back) |
| sound start | SMPC SNDOFF/SNDON (07, 06) | in the BIOS before the app | same | kernel sat_audio_init after the clock change (the change resets the SCSP) | equal sequence; order matters and is respected |
| slave start | SMPC 03, 02 | right after the clock change | n/a | kernel `slave_start`, after the VDP init | deviation: the slave is ours (renders VDP1/VDP2), started when the runtime is ready |
| VDP2 | TVMD | 0x0101, then 0x8101 | 0x0110, 0x8110 | 0x0001 (display off, 352), 0x8001 | BDCLMD = 0 (black border) and the 224-line mode: harmless deviation |
| VDP2 | all other registers | written explicitly (zeros and its values) | same | fix5: zeros written after the clock change; then only what the runtime uses | equal for the unused ones; used ones are ours (below) |
| VDP2 | RAMCTL | 0x1327 | 0x1327 | 0x1300 | rotation-bank bits unused here; deviation |
| VDP2 | CYCxx, CHCTL, PNC, MPxx, PLSZ, scroll/zoom, BGON | SGL's two-layer set-up | same | our layout (NBG0/1/2/3, 16-colour cells, row scroll) | by design: the game's own layers |
| VDP2 | SPCTL | 0x0023 | 0x0023 | 0x0001 (type 1, 3 priority bits) | our sprite format |
| VDP2 | PRISx / PRINx | 0x0506.. / 0x0307, 0x0102 | same | set per frame by the runtime | by design |
| VDP1 | TVMR, EWDR, EWLR, EWRR | 0, 0, 0, 0x58FF | same | 0, 0, 0, 0x58DF (352 x 224 erase) | ours is the exact 352 x 224 size |
| SCU | IMS | 0xFFFFF17C... | same | 0xFFFFFFFE (vblank-in only), rewritten in every vblank handler | deviation; the rewrite is required (the SCU masks everything on acceptance) |
| SCU | DMA | SGL uses D0/D1 for its own copies | same | ours: CPU copies | by design |
| SH-2 | DMAC (0x180..), FRT | SGL sets channel 0/1 | same | not used | by design |
| display | TVMD writes | in the vblank handler | same | `sat_gfx_init` writes TVMD while not in vblank | tolerated by the VDP2 (a display-on mid-frame can glitch one frame); not changed |

## Real divergences found and fixed
1. **No clock change at all for a 352-wide mode** (fix4, fix5: BIOS service SYS_CHGSYSCK(1) as SGL does).
2. **VDP2 registers left to the BIOS logo's values** (fix5: the full register block is zeroed after the clock change, as SGL's init does, before our display is set).
3. SCU mask rewrite (fix2), library relocation (fix3) were found earlier by other means; the log confirms the SGL path never relies on them.

## Not changed, with the reason
- Writing TVMD outside vblank: the register accepts it; SGL's switch happens in the vblank handler. Our picture is dark/black until the first frame anyway.
- Our own vblank, slave and layer set-up replace SGL's by design; calling slInitSystem itself would also install SGL's interrupt vectors, its work area at 0x06000000.. and its slave usage, which conflict with the runtime.
