# Hardware boot hang at the SEGA logo: lane notes, 2026-11-10 (EMULATOR evidence; hardware UNRUN)

Branch `lane/hwboot-20261110`. Disc B (and A, same loader) hung at the BIOS SEGA logo on a JP Saturn with a 4 MB cart (Fenrir).

Ruled out: IP.BIN/boot header/ISO/Fenrir layout (byte-identical to Brooklyn Bangout rc.47, which boots), uninitialised RAM (Yaba, real JP 1.01 BIOS, HLE off, cache on, HWRAM/LWRAM/cart filled with 0xA5 at 0.BIN entry: boots).
Yaba with the real BIOS does not reproduce it; Ymir (real JP 1.01 BIOS, 32 Mbit DRAM cart, SH-2 cache on) gets through the loader and stops after the first vblank (also with the original B disc).

Suspects (static review in learning/hwboot-review): BIOS backup library run from the 4 MB cart after the loader changed the cart timing (boot.c unlock_io), cart timing ASR0/AREF versus the BIOS defaults (JO never writes them), silent halt()/sat_fatal() with the logo still up, missing SLPROG section in 0.BIN.

Landed (all default): boot display from the first instruction (bands, tick, red/magenta stop codes, flashing), save read first in high work RAM, cart verified on the BIOS timing first, cart ID shown, SLPROG in boot.ld,
SMPC idle waits, 128-sector load chunks. Diagnosis switches in the loader build (BOOT_CFLAGS): AVP_BUP_LATE_CART (old place, cart scratch), AVP_BUP_NONE, AVP_CART_ORIG (ours-first timing), AVP_ABUS_BIOS (never switch).
Kernel analysis switch AVP_DIAG_SLAVEPOLL (KERNEL_CFLAGS). Discs: avp_hwdiag_D1 (late cart backup read, original cart order), avp_hwdiag_D2 (D1 without the backup read), avp_3h_A_fix1 (defaults).
