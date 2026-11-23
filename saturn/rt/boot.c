/* First read at 0x06004000: map the cart, load segments from disc, enter the runtime. Lifted code never sees GFS. */
#include "SEGA_GFS.H"
#include "../gfx/sat_vdp2_cfg.h"
#ifdef SAT_WV_REVEAL   /* the post-credits reveal and the save record (saturn/rt/reveal.c); without it this file is the loader as it was */
#include "SEGA_BUP.H"
#include "unlock_save.h"
#endif
#define LOADER_DIAG ((volatile unsigned long *)0x06013fe0u)
#define LOADER_API ((volatile unsigned long *)0x06013fd0u)
#define ENTRY 0x06014000u
#ifdef AVP_VERIFY_ROUND
#if !defined(SECTOR_STORE) || !defined(AVP_VERIFY_ROUND_SUM)
#error AVP_VERIFY_ROUND requires SECTOR_STORE and the expected AVP_VERIFY_ROUND_SUM
#endif
#define ROUND_SUM_ERROR 0xe600u
#define ROUND_SUM_MISMATCH (-0x102)
#endif
extern unsigned char _bstart, _bend;
static unsigned char gfs_work[GFS_WORK_SIZE(1)];
static GfsDirTbl dir;
#ifdef SAT_LOAD_LZ
#define BOOT_NAMES 18   /* the disc has 13 root files (15 entries with . and ..; build.py checks the count): the 256 entry table's 6 KB pays for the decoder's buffers and the stop screen's font */
#else
#define BOOT_NAMES 256
#endif
static GfsDirName names[BOOT_NAMES];
/* ---- boot display (hardware bring-up, hwboot lane 2026-11-10) ----
   The BIOS leaves its SEGA logo up until the runtime's first picture, and a failure here used to spin with the logo still showing. From the first
   instruction of this file the screen is ours: VDP2's back screen in per-line mode shows one band per boot step (a white 2-line tick moves inside
   the current band while a file is read), the bottom stripes hold a 16 bit value (white = 1, black = 0, most significant bit on top), and a
   failure turns the current band red (exception: magenta) and flashes the whole screen with the code. The runtime reaches this through
   DIAG_API (stage, fatal, done) until its own first picture. No scroll screen, sprite or SGL is used; VDP2 registers are write-only, so none is saved. */
#define V2R(o) (*(volatile unsigned short *)(0x25f80000u + (o)))
#define DIAG_TAB ((volatile unsigned short *)0x25e7fe00u)   /* last 512 bytes of VDP2 VRAM: back screen table, one colour per line */
#define DIAG_API ((volatile unsigned long *)0x06013fa0u)    /* 0 stage, 1 fatal(code, detail, context), 2 done, 3 active, 4 reinit, 6-7 cart_soak result */
#define DIAG_LINES 224
#define DIAG_BANDS 22
#define DIAG_CODE_TOP 150
#define C_BLACK 0x0000u
#define C_GREY 0x4631u
#define C_RED 0x001fu
#define C_GREEN 0x03e0u
#define C_BLUE 0x7c00u
#define C_YELLOW 0x03ffu
#define C_CYAN 0x7fe0u
#define C_MAGENTA 0x7c1fu
#define C_WHITE 0x7fffu
/* Quiet boot uses a black loading screen. The stop screen, a yellow band (fast cart timing failed), and a cyan band (BIOS save library stuck) still show.
   AVP_BOOT_BANDS brings back the full bring-up display (grey screen, a band per step, the moving tick, the binary stripes) for test discs. */
#ifdef AVP_BOOT_BANDS
#define C_BG C_GREY
#define C_STEP(s) (((s) & 1) ? C_BLUE : C_GREEN)
#else
#define C_BG C_BLACK
#define C_STEP(s) C_BLACK
#endif
static unsigned short diag_col[DIAG_BANDS + 1];
static int diag_active, diag_seq, diag_cur, diag_ticks, diag_mark;
static unsigned diag_info_value;
#ifdef AVP_BOOT_ROM_RETRY
static unsigned long rom_retry_first_bytes, rom_retry_first_block;
#endif
static void diag_fill(int a, int b, unsigned short c) { for (; a < b && a < DIAG_LINES; a++) DIAG_TAB[a] = c; }
static void diag_band(int k, unsigned short c) { if (k < DIAG_BANDS) diag_fill(1 + 6 * k, 6 + 6 * k, c); }
static void diag_code(unsigned v)
{
    int i;
    diag_info_value = v;
#ifndef AVP_BOOT_BANDS
    return;
#endif
    for (i = 0; i < 16; i++) {
        diag_fill(DIAG_CODE_TOP + 4 * i, DIAG_CODE_TOP + 4 * i + 3, ((v >> (15 - i)) & 1) ? C_WHITE : C_BLACK);
        diag_fill(DIAG_CODE_TOP + 4 * i + 3, DIAG_CODE_TOP + 4 * i + 4, C_GREY);
    }
}
static void diag_render(unsigned code)
{
    int k;
    diag_fill(0, DIAG_LINES, C_BG);
    for (k = 0; k < diag_seq && k < DIAG_BANDS; k++) diag_band(k, diag_col[k]);
    diag_code(code);
}
static void diag_wait(int frames)
{
    while (frames-- > 0) { while (V2R(0x04) & 8) ; while (!(V2R(0x04) & 8)) ; }
}
static void diag_stage_k(unsigned long colour, unsigned long unused)
{
    unsigned short c = (unsigned short)colour;
    (void)unused;
    if (!diag_active) return;
    if (!c) c = C_STEP(diag_seq);
    diag_cur = diag_seq;
    if (diag_seq < DIAG_BANDS) diag_col[diag_seq] = c;
    diag_band(diag_seq, c);
    diag_seq++;
    diag_ticks = 0; diag_mark = -1;
}
static void diag_tick(void)
{
    int top, k = diag_cur;
#ifndef AVP_BOOT_BANDS
    return;
#endif
    if (!diag_active || k >= DIAG_BANDS) return;
    top = 1 + 6 * k;
    if (diag_mark >= 0) diag_fill(top + diag_mark, top + diag_mark + 2, diag_col[k]);
    diag_mark = 2 * (diag_ticks++ & 1);
    diag_fill(top + diag_mark, top + diag_mark + 2, C_WHITE);
}
static void diag_info(unsigned v) { if (diag_active) diag_code(v); }
static unsigned short diag_tvmd = 0x8000;   /* 320 wide until clock_352 */
static void diag_takeover(void)
{
    V2R(0x20) = 0;                        /* BGON: no scroll screen */
    V2R(0xf0) = 0; V2R(0xf2) = 0; V2R(0xf4) = 0; V2R(0xf6) = 0;   /* PRISA-D: sprite priority 0 hides the logo's VDP1 sprites */
    V2R(0xec) = 0;                        /* CCCTL */
    V2R(0x10) = 0xffff; V2R(0x12) = 0xffff; V2R(0x14) = 0xffff; V2R(0x16) = 0xffff;   /* VRAM cycle patterns: no layer reads VRAM, so none can show (the runtime's init leaves its own) */
    V2R(0x18) = 0xffff; V2R(0x1a) = 0xffff; V2R(0x1c) = 0xffff; V2R(0x1e) = 0xffff;
    V2R(0x00) = diag_tvmd;                /* TVMD: display on, 320 x 224 (352 x 224 after the clock change) */
    V2R(0xac) = 0x8003;                   /* BKTAU: per-line back screen, table at VRAM 0x7fe00 */
    V2R(0xae) = 0xff00;                   /* BKTAL */
}
static void diag_init(void)
{
    diag_takeover();
    diag_fill(0, DIAG_LINES, C_BG);
    diag_active = 1;
    DIAG_API[0] = (unsigned long)diag_stage_k;
    DIAG_API[3] = 1;
}
static void diag_slave_k(unsigned long which, unsigned long b)   /* marks between the bands and the stripes: 1 the slave runs (yellow block), 2 the master woke it (white block), 3.. one line each, first vblank only: 3 entered, 4 after sat_gfx_vblank, 5 held-path test, 6 wake sent, 7 layers done, 8 f_e0e done, 9 handler end */
{
    static const unsigned short col[11] = { 0, 0, 0, C_RED, C_GREEN, C_BLUE, C_CYAN, C_MAGENTA, C_YELLOW, C_WHITE, C_RED };
    (void)b;
    if (!diag_active) return;
    if (which == 1) diag_fill(134, 138, C_YELLOW);
    else if (which == 2) diag_fill(138, 142, C_WHITE);
    else if (which >= 3 && which < 10) diag_fill(140 + (int)which, 141 + (int)which, col[which]);
    else if (which == 10) diag_fill(132, 134, col[10]);
    else if (which == 11) diag_fill(128, 130, C_CYAN);
    else if (which == 12) diag_fill(126, 128, C_MAGENTA);
    else if (which == 13) diag_fill(124, 126, C_WHITE);
    else if (which == 14) diag_fill(122, 124, C_GREEN);
    else if (which == 15) diag_fill(120, 122, C_RED);
    else if (which == 16) diag_fill(118, 120, C_YELLOW);
    else if (which == 17) diag_fill(116, 118, C_CYAN);
    else if (which == 18) diag_fill(114, 116, C_MAGENTA);
}
static void diag_reinit_k(unsigned long a, unsigned long b)   /* the runtime's graphics init cleared VRAM and the registers: take the screen back, bands and stripes as they were */
{
    (void)a; (void)b;
    if (!diag_active) return;
    diag_takeover();
    diag_render(diag_info_value);
}
/* ---- stop screen in words (2026-11-16, owner: "make the diagnostic / error screen state the issue instead of relying on codes so users can report") ----
   A stop used to flash coloured bands and binary stripes that only the source could read. Now it says what went wrong, what to try and the codes in hex,
   on a dark screen that holds still for a photo. Text is NBG0, 16 colours, one-word names: cells in VRAM-A0 from 0 (cell n = ASCII 32 + n, the loader's own
   5x7 font from tools/boot_font.py, no game data: the game's font lives in the cart, which may be what is missing), map in VRAM-B0 at 0x40000 (plane 32).
   Access cycles: A0 T0 = NBG0 cells, B0 T0 = NBG0 names (Table 3.4: names at T0 allow cells at T0). The loader owns VRAM at boot and on a stop. */
static const unsigned char diag_font[59 * 7] = {
#include "boot_font.inc"
};
#define T_MAP ((volatile unsigned short *)0x25e40000u)
#define T_CEL ((volatile unsigned long *)0x25e00000u)
#define T_COLS 44
static int t_row;
static __attribute__((optimize("Os"), noinline)) int t_at(int row, int col, const char *s)
{
    volatile unsigned short *m = T_MAP + row * 64 + col;
    for (; *s && col < T_COLS; s++, col++) { unsigned c = (unsigned char)*s; *m++ = (unsigned short)(c >= 32 && c <= 90 ? c - 32 : 0); }
    return col;
}
static __attribute__((optimize("Os"), noinline)) void t_line(const char *s) { t_at(t_row++, 2, s); }
static __attribute__((optimize("Os"), noinline)) int t_hex(int row, int col, unsigned v, int n)
{
    char b[9]; int i;
    for (i = n - 1; i >= 0; i--, v >>= 4) b[i] = "0123456789ABCDEF"[v & 15];
    b[n] = 0;
    return t_at(row, col, b);
}
static __attribute__((optimize("Os"), noinline)) void diag_text_init(unsigned short bg)
{
    int g, r, j;
    diag_takeover();                      /* no layer, sprites hidden, display on, per-line back screen, every access cycle no access */
    diag_fill(0, DIAG_LINES, bg);
    V2R(0x0e) = 0x0300;                   /* RAMCTL: VRAM-A and VRAM-B split, CRAM mode 0 */
    V2R(0x10) = 0x4fff;                   /* CYCA0L: T0 NBG0 cells */
    V2R(0x18) = 0x0fff;                   /* CYCB0L: T0 NBG0 names */
    V2R(0x28) = 0; V2R(0x2a) = 0;         /* CHCTLA/B: NBG0 16 colours, cells 1x1 */
    V2R(0x30) = 0x8000;                   /* PNCN0: one-word names, cell number in the low 10 bits */
    V2R(0x3a) = 0; V2R(0x3c) = 0;         /* PLSZ, MPOFN */
    V2R(0x40) = 0x2020; V2R(0x42) = 0x2020;   /* MPABN0, MPCDN0: every plane at 0x40000 */
    for (r = 0x70; r <= 0x7e; r += 2) V2R(r) = 0;
    V2R(0x78) = 1; V2R(0x7c) = 1;         /* ZMXIN0, ZMYIN0: 1x */
    V2R(0x22) = 0; V2R(0x98) = 0; V2R(0x9a) = 0;   /* MZCTL, ZMCTL, SCRCTL */
    V2R(0xc0) = 0; V2R(0xe4) = 0; V2R(0xe8) = 0; V2R(0x110) = 0;   /* WCTLA, CRAOFA, LNCLEN, CLOFEN */
    V2R(0xf8) = 7;                        /* PRINA: NBG0 priority 7 */
    ((volatile unsigned short *)0x25f00000u)[1] = C_WHITE;
    for (r = 0; r < 64 * 32; r++) T_MAP[r] = 0;
    for (g = 0; g < 59; g++)
        for (r = 0; r < 8; r++) {
            unsigned bits = r < 7 ? diag_font[g * 7 + r] : 0, w = 0;
            for (j = 0; j < 8; j++) if (bits & (0x80u >> j)) w |= 1u << (28 - 4 * j);
            T_CEL[g * 8 + r] = w;
        }
    V2R(0x20) = 1;                        /* BGON: NBG0 on, colour 0 transparent */
}
static const char *const t_file[7] = { "", "LW.BIN", "ROM.BIN", "OPX.BIN", "HW.BIN", "", "COLD1.BIN" };
enum {
    LZ_SEEK_FAILED = 4,
    LZ_READ_FAILED,
    LZ_DECODE_FAILED,
    LZ_STREAM_FAILED,
    LZ_STREAM_TIMEOUT,
    LZ_TAIL_FAILED,
    LZ_SIZE_MISMATCH
};
#ifdef AVP_DIAG_BUILD
#define BUILD_TEXT_(id) #id
#define BUILD_TEXT(id) BUILD_TEXT_(id)
#endif
static __attribute__((optimize("Os"), noinline)) void diag_explain(unsigned code, unsigned extra)
{
    unsigned hi = code >> 8, k = code & 15;
    int c;
    t_row = 2; t_line("AVP SATURN STOPPED");
#ifdef AVP_DIAG_BUILD
#ifdef AVP_ABUS_SAFE
    t_line("BUILD " BUILD_TEXT(AVP_DIAG_BUILD) " SAFE");
#else
    t_line("BUILD " BUILD_TEXT(AVP_DIAG_BUILD));
#endif
#endif
    t_row = 5;
    if (code == 0xe0f2) {
        t_line("NO 4 MB RAM CART FOUND.");
        t_line("INSERT A 4 MB CART WITH POWER OFF.");
        t_line("SAROO OR EMULATOR: ENABLE 4 MB MODE.");
    } else if (code == 0xe0f0 || code == 0xe0f1) {
        t_line("4 MB RAM CART CHECK FAILED.");
        t_line("POWER OFF, THEN RESEAT THE CART.");
    } else if (code == 0xe001 || (code >= 0x100 && code < 0x700) || hi == 0xed) {
        if (code == 0xe001) t_line("THE CD SYSTEM DID NOT START.");
        else if (hi == 0xed) t_line("THE DISC COULD NOT BE READ.");
        else {
            c = t_at(t_row, 2, "FILE ");
            c = t_at(t_row, c, t_file[hi]);
            t_at(t_row++, c + 1, k == 1 ? "IS MISSING." : k == 2 ? "DID NOT OPEN." :
                 k == 4 ? "BAD LOAD HEADER." : k == 6 ? "SEEK FAILED." :
                 k == 5 ? "COMPRESSED LOAD FAILED." :
#if defined(AVP_BOOT_ROM_SUM) || defined(AVP_BOOT_FILE_CHECKS)
                 k == 7 ? "CHECKSUM FAILED." :
#endif
                 "READ FAILED.");
#ifdef AVP_BOOT_FILE_CHECKS
            if (k == 3) {
                c = t_hex(21, t_at(21, 2, "SECTOR "), (unsigned)LOADER_DIAG[3], 4);
                t_hex(21, t_at(21, c, "  EXPECTED BYTES "), (unsigned)LOADER_DIAG[4], 8);
            }
#endif
            if (k == 5) {
                c = t_hex(21, t_at(21, 2, "BLOCK "), (unsigned)LOADER_DIAG[3], 4);
                t_hex(21, t_at(21, c, "  BYTES "), (unsigned)LOADER_DIAG[4], 8);
#ifdef AVP_BOOT_ROM_RETRY
                if (hi == 2 && rom_retry_first_bytes) {
                    c = t_hex(22, t_at(22, 2, "FIRST BLOCK "), (unsigned)rom_retry_first_block, 4);
                    t_hex(22, t_at(22, c, "  BYTES "), (unsigned)rom_retry_first_bytes, 8);
                }
#endif
            }
        }
    }
#ifdef AVP_VERIFY_ROUND
    else if (code == ROUND_SUM_ERROR) {
        t_line("ROUND DATA CHECKSUM FAILED.");
        c = t_hex(21, t_at(21, 2, "ROUND "), AVP_VERIFY_ROUND, 4);
        t_hex(21, t_at(21, c, "  EXPECTED "), AVP_VERIFY_ROUND_SUM, 8);
    }
#endif
    else if (hi >= 0xf0) t_line("CPU EXCEPTION.");
    else if (hi == 0xeb) t_line("GRAPHICS SETUP FAILED.");
    else if (hi == 0xec) t_line("SOUND SETUP FAILED.");
    else if (hi == 0xef) t_line("PICTURE STALLED.");
    else if (hi == 0xe4) t_line("UNEXPECTED TASK RETURN.");
    else if (hi >= 0x80 && hi < 0xe0) t_line("GAME UPDATE STALLED.");
    else t_line("INTERNAL ERROR.");
    if (hi >= 0x80 && hi != 0xe0 && hi != 0xfe
#ifdef AVP_VERIFY_ROUND
        && code != ROUND_SUM_ERROR
#endif
    ) {
        unsigned context = (unsigned)LOADER_DIAG[4];
        c = t_hex(21, t_at(21, 2, "TASK "), context >> 16, 4);
        t_hex(21, t_at(21, c, "  STAGE "), context & 0xffffu, 4);
    }
    c = t_at(19, 2, "ERROR ");
    c = t_hex(19, c, code, 4);
    c = t_at(19, c, "  DETAIL ");
    c = t_hex(19, c, extra, 8);
    c = t_at(19, c, "  STEP ");
    t_hex(19, c, (unsigned)diag_cur, 2);
    t_row = 23;
    t_line("REPORT A PHOTO AT");
    t_line("GITHUB.COM/LAMB2K/AVPSATURN/ISSUES");
}
static __attribute__((noreturn)) void diag_fail(unsigned code, unsigned short colour, unsigned extra)
{
    LOADER_DIAG[0] = 0x4156504c; LOADER_DIAG[1] = code; LOADER_DIAG[2] = extra;
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));   /* also after the boot display has ended: a stop in play used to leave the last picture up, a silent freeze (SAROO report 11-17) */
    diag_text_init(colour == C_MAGENTA ? 0x2c0bu : 0x000bu);   /* dark magenta: exception, dark red: everything else */
    diag_explain(code, extra);
    for (;;) __asm__ volatile ("nop");
}
static void diag_fatal_k(unsigned long code, unsigned long detail, unsigned long context)
{
    LOADER_DIAG[4] = context;
    diag_fail((unsigned)((code & 0xff) << 8 | (detail & 0xff)), code >= 0xf0 ? C_MAGENTA : C_RED, (unsigned)detail);
}
static void diag_done_k(unsigned long restore, unsigned long b)   /* the boot display ends; restore != 0: after the runtime's graphics init, put back the two registers this file changed that it set (TVMD, back screen table); the rest it rewrites every frame */
{
    (void)b;
    if (restore) {   /* what sat_gfx_init set and diag_takeover changed (values from sat_gfx_init; BACKCOL 0x1fffe) */
        V2R(0x00) = 0x8101; V2R(0xac) = 0; V2R(0xae) = 0xffff;
        V2R(0x10) = SAT_CYC_A0L; V2R(0x12) = SAT_CYC_A0U; V2R(0x14) = SAT_CYC_A1L; V2R(0x16) = SAT_CYC_A1U;   /* the access cycles of saturn/gfx/sat_vdp2_cfg.h */
        V2R(0x18) = SAT_CYC_B0L; V2R(0x1a) = SAT_CYC_B0U; V2R(0x1c) = SAT_CYC_B1L; V2R(0x1e) = SAT_CYC_B1U;
    }
    diag_active = 0; DIAG_API[3] = 0;
}
static void diag_exc_c(unsigned long pc, unsigned long vec) { diag_fail(0xfe00u | (unsigned)vec, C_MAGENTA, (unsigned)pc); }
__asm__(".text\n.align 2\n"
        ".global _diag_exc4\n_diag_exc4: mov.l @r15,r4\n bra 9f\n mov #4,r5\n"
        ".global _diag_exc6\n_diag_exc6: mov.l @r15,r4\n bra 9f\n mov #6,r5\n"
        ".global _diag_exc9\n_diag_exc9: mov.l @r15,r4\n bra 9f\n mov #9,r5\n"
        ".global _diag_exc10\n_diag_exc10: mov.l @r15,r4\n mov #10,r5\n"
        "9: mov.l 1f,r0\n jmp @r0\n nop\n.align 2\n1: .long _diag_exc_tramp\n");
extern void diag_exc4(void), diag_exc6(void), diag_exc9(void), diag_exc10(void);
void diag_exc_tramp(unsigned long pc, unsigned long vec) { diag_exc_c(pc, vec); }
static __attribute__((noreturn)) void halt(unsigned long s, unsigned long d)
{
    diag_fail((unsigned)s, C_RED, (unsigned)d);
}
#define LOAD_CHUNK 128   /* sectors per read, so the tick moves while a file loads */
static unsigned long load_head[512];
#if defined(SAT_LOAD_SUM) || defined(SAT_LOAD_SELFTEST) || defined(SAT_LZ_DBG)
#ifdef SAT_LZ_DBG
unsigned long sat_ld_diag[8 + 96];
#else
unsigned long sat_ld_diag[8 + 12];   /* words 8 to 19: the sum and byte count of each boot file as loaded, in load order (boot_note) */
#endif
/* (bss: the loader's image holds only .text) test words: 0 loads done, 1 last SAT_LOAD_SUM sum, 2 selftest fails, 3 first failing round, 4 rounds done, 5 rounds in the store, 7 the marker 'LZST' a Ymir route scans for */
#endif
#ifdef SAT_LOAD_LZ   /* lane loading, 2026-11-12: compressed boot files and tile regions (tools/lzstore.py, saturn/rt/lzdec.h) */
#include "lzdec.h"
#define LZ_MAXB 80
#define LZ_TMAX 7168   /* tail scratch bytes; tools/lzstore.py TMAX is the same (a file whose in-place decode needs more stays uncompressed; the shipped files need at most 7168) */
static LzCtx lz_ctx;
static lz32 lz_scr[(LZ_TMAX + 8) / 4 + 1];   /* the tail kept out of the way of the in-place decode (also the self test's sum table) */
#define CCR_B (*(volatile unsigned char *)0xfffffe92u)
static unsigned char lz_ccr;
/* The loader runs with the cache as the BIOS left it (off); the decoder is much faster with it on. It is switched on, purged, for each decoding step only: the CD transfer writes behind the cache. */
#define LZ_CACHE_ON() do { lz_ccr = CCR_B; CCR_B = 0x11; } while (0)
#define LZ_CACHE_OFF() do { CCR_B = (unsigned char)((lz_ccr & 1) ? (lz_ccr | 0x10) : 0x10); } while (0)
/* Read the streams of a unit into the end of its destination and decode them while they arrive (GFS non-blocking read, GFS_NwExecOne moves the data by CPU): the drive keeps reading while the CPU
   decodes, so the time is the CD's, not the CD's plus the decoder's. gsec/gcnt: ngrp groups of contiguous disc sectors, in the order of the streams; seek_first 0: the file position is already at the first. */
#ifdef SAT_LZ_DBG
lz32 dbg_ak, dbg_aoff;
lz32 dbg_now(void) { static lz32 T, last; lz32 f = *(volatile unsigned char *)0xfffffe12u; f = (f << 8) | *(volatile unsigned char *)0xfffffe13u; T += (f - last) & 0xffffu; last = f; return T; }
#endif
/* SAROO field report (2026-11-17: boots, freezes on the load into stage 2), a fix in advance of any capture. Two guards for every setup: a streamed read that reports an error
   or brings no new data for LZ_IDLE_MAX polls ends with an error code instead of spinning for ever (the loop had no way out), and load_regions retries a failed load twice
   from GFS_Init before the stop screen. On SAROO (load_saroo, set from the A-bus timing it leaves) the compressed streams are read with a plain blocking GFS_Fread, then
   decoded: no GFS non-blocking server between the drive and the decoder. */
#define LZ_IDLE_MAX 0x100000ul
static unsigned long load_saroo;
static lz32 lz_failed_block, lz_bytes_received;
static __attribute__((optimize("Os"), noinline)) long lz_error(const LzUnit *u, lz32 arrived, int reason)
{
    lz_failed_block = u->k;
    lz_bytes_received = arrived;
    return -reason;
}
static long lz_stream(GfsHn h, lz8 *dest, lz32 raw_total, lz32 nblk, const lz32 *blk, lz32 tail, const lz32 *gsec, const lz32 *gcnt, lz32 ngrp, int seek_first)
{
    LzUnit u; lz32 g, done = 0; int r = 0;
    lz_unit_begin(&lz_ctx, &u, dest, raw_total, nblk, blk, tail, (lz8 *)lz_scr);
    for (g = 0; g < ngrp; g++) {
        Sint32 am = 0, nd = 0, all = 2048 * (Sint32)gcnt[g], fin = 0;
        lz32 idle = 0, seen = 0;
        if (g > 0 || seek_first)
            if (GFS_Seek(h, (Sint32)gsec[g], GFS_SEEK_SET) < 0) return lz_error(&u, done, LZ_SEEK_FAILED);
        if (load_saroo) {
            nd = GFS_Fread(h, (Sint32)gcnt[g], u.base + done, all);
            if (nd != all) return lz_error(&u, done + (nd > 0 ? (lz32)nd : 0), LZ_READ_FAILED);
            fin = 1;
        } else if (GFS_NwFread(h, (Sint32)gcnt[g], u.base + done, all) < 0)
            return lz_error(&u, done, LZ_READ_FAILED);
        for (;;) {
            lz32 arrived;
            if (!fin) {
                if (GFS_NwExecOne(h) == GFS_SVR_ERROR) return lz_error(&u, done + seen, LZ_STREAM_FAILED);
                GFS_NwGetStat(h, &am, &nd);
                if ((lz32)nd != seen) { seen = (lz32)nd; idle = 0; }
                else if (++idle > LZ_IDLE_MAX) { GFS_NwStop(h); return lz_error(&u, done + (lz32)nd, LZ_STREAM_TIMEOUT); }
                fin = GFS_NwIsComplete(h);
            }
            arrived = done + (lz32)nd;
            if (fin) { arrived = done + (lz32)all; }
            LZ_CACHE_ON();
#ifdef SAT_LZ_DBG
            {   /* timing of the tile streams (FRT, phi/128 = 4.5 us per count): sat_ld_diag[8 + k] arrival, [33 + k] decode start, [58 + k] decode end (counts since the first stream's request) */
                extern lz32 dbg_now(void);
                lz32 tn = dbg_now();
                if (sat_ld_diag[5]) {
                    while (dbg_ak < nblk && dbg_aoff + ((blk[2 * dbg_ak + 1] + 2047ul) & ~2047ul) <= arrived) { if (dbg_ak < 25) sat_ld_diag[8 + dbg_ak] = tn; dbg_aoff += (blk[2 * dbg_ak + 1] + 2047ul) & ~2047ul; dbg_ak++; }
                    for (;;) {
                        lz32 kk = u.k, t0 = dbg_now();
                        r = lz_unit_step(&lz_ctx, &u, arrived, 0);
                        if (r <= 0) break;
                        if (kk < 25) { sat_ld_diag[33 + kk] = t0; sat_ld_diag[58 + kk] = dbg_now(); }
                    }
                } else while ((r = lz_unit_step(&lz_ctx, &u, arrived, 0)) > 0) ;
            }
#else
            while ((r = lz_unit_step(&lz_ctx, &u, arrived, 0)) > 0) ;
#endif
            LZ_CACHE_OFF();
            if (r < 0) return lz_error(&u, arrived, LZ_DECODE_FAILED);
            if (fin) break;
            diag_tick();
        }
        done += 2048ul * gcnt[g];
    }
    LZ_CACHE_ON();
#ifdef SAT_LZ_DBG
    { extern lz32 dbg_now(void); if (sat_ld_diag[5]) sat_ld_diag[83] = dbg_now(); }
#endif
    lz_unit_tailcopy(&lz_ctx, &u);
    while ((r = lz_unit_step(&lz_ctx, &u, u.padded, 1)) > 0) ;
#ifdef SAT_LZ_DBG
    { extern lz32 dbg_now(void); if (sat_ld_diag[5]) sat_ld_diag[84] = dbg_now(); }
#endif
    LZ_CACHE_OFF();
    if (r < 0) return lz_error(&u, done, LZ_TAIL_FAILED);
    if (u.k != u.nblk || u.out != raw_total) return lz_error(&u, done, LZ_SIZE_MISMATCH);
    return 0;
}
#endif
#if defined(SAT_LOAD_SUM) || defined(SAT_LOAD_SELFTEST)
static unsigned long boot_n;
/* test builds: the multiplicative sum (SAT_LOAD_SUM's) of each boot file as it lies in memory after load(), in load order: sat_ld_diag[8 + 2n] sum, [9 + 2n] bytes; the marker is set here so a route can find the array
   (tools/loading/bootsum.py compares them with the sums of the files as the plain build writes them). */
static void boot_note(const void *dest, unsigned long bytes)
{
    const volatile unsigned long *p = (const volatile unsigned long *)dest; unsigned long s = 0, q;
    volatile unsigned long ka = 0x6b7c9a21ul, kb = 0x2726c975ul;
    for (q = 0; q < bytes / 4; q++) s = s * 0x9e3779b1ul + p[q];
    sat_ld_diag[7] = ka ^ kb;
    if (boot_n < 6) { sat_ld_diag[8 + 2 * boot_n] = s; sat_ld_diag[9 + 2 * boot_n] = bytes; boot_n++; }
}
#define BOOT_NOTE(d, n) boot_note((d), (n))
#else
#define BOOT_NOTE(d, n) ((void)0)
#endif
#if defined(AVP_BOOT_ROM_SUM) || defined(AVP_BOOT_FILE_CHECKS)
static __attribute__((optimize("Os"))) unsigned long boot_readback_sum(const void *dest, unsigned long bytes)
{
    const volatile unsigned long *data = (const volatile unsigned long *)((unsigned long)dest | 0x20000000u);
    unsigned long sum = 0;
    while (bytes >= 4) {
        sum = sum * 0x9e3779b1u + *data++;
        bytes -= 4;
    }
#ifdef AVP_BOOT_FILE_CHECKS
    {
        const volatile unsigned char *tail = (const volatile unsigned char *)data;
        for (; bytes; bytes--) sum = sum * 0x9e3779b1u + *tail++;
    }
#endif
    return sum;
}
#endif
static void boot_loaded(const void *dest, unsigned long code, unsigned long bytes)
{
#ifdef AVP_BOOT_FILE_CHECKS
    /* Indexed by the file number in the stop code. The builder records the bytes before compression. */
    static const unsigned long checks[][2] = { AVP_BOOT_FILE_CHECKS };
    const unsigned long *expected = checks[code >> 8];
    unsigned long sum;
    if (bytes != expected[0]) halt(code | 4, bytes);
    sum = boot_readback_sum(dest, bytes);
    if (sum != expected[1]) halt(code | 7, sum);
#endif
    LOADER_DIAG[3] = code;
    LOADER_DIAG[4] = bytes;
    BOOT_NOTE(dest, bytes);
}
static __attribute__((noreturn)) void boot_read_failed(GfsHn h, unsigned long code, Sint32 sector, Sint32 expected, Sint32 got)
{
    GFS_Close(h);
#ifdef AVP_BOOT_FILE_CHECKS
    LOADER_DIAG[3] = sector;
    LOADER_DIAG[4] = expected;
#endif
    halt(code | 3, (unsigned long)got);
}
static __attribute__((optimize("Os"))) void load(const char *name, void *dest, unsigned long code)
{
    Sint32 id = GFS_NameToId((Sint8 *)name), ss, n, last, got, total = 0, left;
    unsigned char *d = (unsigned char *)dest;
    GfsHn h;
    if (id < 0) halt(code | 1, (unsigned long)id);
    h = GFS_Open(id);
    if (!h) halt(code | 2, 0);
    GFS_GetFileSize(h, &ss, &n, &last);
    if (n <= 0 || ss != 2048 || last <= 0 || last > 2048) { GFS_Close(h); halt(code | 4, 3); }
    GFS_SetTmode(h, GFS_TMODE_CPU);
#ifdef SAT_LOAD_LZ
    /* A compressed boot file: header sector 'LZB1', raw_total, tail, nblk, (raw, compressed) pairs, then each stream padded to whole sectors. Read into the end of the destination, decode forward in place. */
    if (n > 1) {
        got = GFS_Fread(h, 1, load_head, 2048);
        if (got != 2048) boot_read_failed(h, code, 0, 2048, got);
        if (load_head[0] == 0x4c5a4231ul) {
            lz32 raw_total = load_head[1], tail = load_head[2], nblk = load_head[3], k, padded = 0;
            lz32 gs = 0, gc;
            if (nblk == 0 || nblk > 250 || tail > LZ_TMAX || tail > raw_total) { GFS_Close(h); halt(code | 4, 1); }
            for (k = 0; k < nblk; k++) padded += (load_head[5 + 2 * k] + 2047ul) & ~2047ul;
            gc = padded >> 11;
            if (padded > raw_total || gc != (lz32)(n - 1)) { GFS_Close(h); halt(code | 4, 2); }
            got = lz_stream(h, (lz8 *)dest, raw_total, nblk, load_head + 4, tail, &gs, &gc, 1, 0);
#ifdef AVP_BOOT_ROM_RETRY
            /* Try the same ROM again with a blocking read after a streaming decode failure. */
            if (code == 0x200 && got == -LZ_DECODE_FAILED && !load_saroo && GFS_NwStop(h) >= 0) {
                rom_retry_first_block = lz_failed_block;
                rom_retry_first_bytes = lz_bytes_received;
                gs = 1;   /* skip the header sector already held in load_head */
                load_saroo = 1;
                got = lz_stream(h, (lz8 *)dest, raw_total, nblk, load_head + 4, tail, &gs, &gc, 1, 1);
                load_saroo = 0;
            }
#endif
            if (got < 0) {
                GFS_Close(h);
                LOADER_DIAG[3] = lz_failed_block;
                LOADER_DIAG[4] = lz_bytes_received;
                halt(code | 5, (unsigned long)-got);
            }
            GFS_Close(h);
            boot_loaded(dest, code, raw_total);
            return;
        }
        if (GFS_Seek(h, 0, GFS_SEEK_SET) < 0) { GFS_Close(h); halt(code | 6, 0); }
    }
#endif
    for (left = n; left > 0; ) {
        Sint32 c = left > LOAD_CHUNK ? LOAD_CHUNK : left;
        Sint32 expected = 2048 * (c - 1) + (c == left ? last : 2048);
        got = GFS_Fread(h, c, d, expected);
        if (got != expected) boot_read_failed(h, code, n - left, expected, got);
        total += got; d += got; left -= c;
        diag_tick();
    }
    GFS_Close(h);
    boot_loaded(dest, code, (unsigned long)total);
}
/* Between rounds the runtime calls this through LOADER_API (lifted code never does): one file of whole sectors, its first sector a list of
   u32 count, then count pairs of u32 destination, u32 bytes (multiples of 2048), destination 1 being a call to mark. The caller has masked interrupts and stopped the slave. Returns sectors read, or a negative stage. */
#ifdef SECTOR_STORE
/* SECTOR_STORE (tools/sector_store.py): the round files live as runs of one shared STORE.BIN. RNNN.BIN names round NNN; its runs, read in order,
   are that file's sectors, so the walk below sees the same stream and the cart gets the same bytes. Adjacent runs were joined when packed. */
#ifdef STORE_HEAD2   /* guest builds: more than 255 rounds, a two-sector directory */
static unsigned long store_dir[1024], store_run[512];
#define STORE_HS (store_dir[1] > 255 ? 2 : 1)
#else
static unsigned long store_dir[512], store_run[512];
#define STORE_HS 1
#endif
static Sint32 run_at, run_left, run_sec = -1, run_next, run_end, run_reseek;   /* run_reseek: another read moved the file pointer (the compressed tile region): seek to run_at before the next read */
#ifdef SAT_LOAD_COALESCE
static unsigned long coal_big;   /* set once a region larger than COAL_MAX has been read after the mark */
#define COAL_MAX 64u   /* sectors; every restore region of the stage files and the front end file is below this, the tile and sound regions are not */
#endif
#if defined(SAT_LOAD_SUM) || defined(AVP_VERIFY_ROUND)
/* Match tools/lzstore.py: sum the final bytes in each destination, in
   region order. Read through the uncached alias after all writes. */
static unsigned long round_readback_sum(void)
{
    unsigned long k, q, sum = 0;
    for (k = 0; k < load_head[0]; k++) {
        unsigned long dst = load_head[1 + k * 2], n = (load_head[2 + k * 2] & ~1ul) / 4u;
        volatile unsigned long *d = (volatile unsigned long *)(dst | 0x20000000u);
        if (dst == 1) continue;
        for (q = 0; q < n; q++) sum = sum * 0x9e3779b1u + d[q];
    }
    return sum;
}
#endif
static Sint32 vread(GfsHn h, Sint32 secs, unsigned char *dest)
{
    while (secs) {
        Sint32 take, got;
        if (!run_left) {
            Sint32 s;
            if (run_next >= run_end) return -1;
            s = STORE_HS + run_next / 512;
            if (s != run_sec) {
                if (GFS_Seek(h, s, GFS_SEEK_SET) < 0 || GFS_Fread(h, 1, store_run, 2048) != 2048) return -2;
                run_sec = s;
            }
            run_at = (Sint32)(store_run[run_next % 512] >> 14); run_left = (Sint32)(store_run[run_next % 512] & 0x3fff); run_next++;
            if (GFS_Seek(h, run_at, GFS_SEEK_SET) < 0) return -3;
        } else if (run_reseek) {
            if (GFS_Seek(h, run_at, GFS_SEEK_SET) < 0) return -3;
        }
        run_reseek = 0;
        take = secs < run_left ? secs : run_left;
        if (take > LOAD_CHUNK) take = LOAD_CHUNK;
        got = GFS_Fread(h, take, dest, take * 2048);
        if (got != take * 2048) return -4;
        diag_tick();
        run_at += take; run_left -= take; secs -= take; dest += take * 2048;
    }
    return 0;
}
#ifdef SAT_LOAD_LZ
static unsigned long lz_blob_base;
/* Region i of the head has bit 0 of its byte count set: its tile data is stored compressed (tools/lzstore.py). The unit table sits at byte 1024 of the head sector: 'LZ01', raw_total, tail, nblk,
   nblk pairs (raw bytes, compressed bytes), nblk blob sectors (relative to the blob area). The blobs are read into the END of the region's destination, each padded to whole sectors, and decoded
   forward in place (lzdec.h lz_unit): the first sectors of the destination are free while the blobs sit behind them. Returns 0 or a negative code. */
static long lz_tile(GfsHn h, unsigned long i)
{
    static lz32 blk[2 * LZ_MAXB], gsec[LZ_MAXB], gcnt[LZ_MAXB];
    lz32 *info = load_head + 256, nblk, raw_total, tail, k, padded = 0, ngrp = 0;
    lz8 *dest = (lz8 *)load_head[1 + i * 2];
    if (info[0] != 0x4c5a3031ul) return -1;
    raw_total = info[1]; tail = info[2]; nblk = info[3];
    if (nblk > LZ_MAXB || tail > LZ_TMAX) return -2;
    for (k = 0; k < nblk; k++) {
        lz32 sec = lz_blob_base + info[4 + 2 * nblk + k], n = (info[5 + 2 * k] + 2047ul) >> 11;
        blk[2 * k] = info[4 + 2 * k]; blk[2 * k + 1] = info[5 + 2 * k]; padded += n << 11;
        if (ngrp && gsec[ngrp - 1] + gcnt[ngrp - 1] == sec) gcnt[ngrp - 1] += n;   /* neighbouring streams on the disc: one read */
        else { gsec[ngrp] = sec; gcnt[ngrp] = n; ngrp++; }
    }
    if (padded > raw_total) return -3;
    run_reseek = 1;
#ifdef SAT_LZ_DBG
    { int q; volatile unsigned long ka = 0x6b7c9a21ul, kb = 0x2726c975ul; extern lz32 dbg_now(void); for (q = 8; q < 104; q++) sat_ld_diag[q] = 0; sat_ld_diag[7] = ka ^ kb; *(volatile unsigned char *)0xfffffe16u = 2; (void)dbg_now(); sat_ld_diag[5] = 1; sat_ld_diag[8 + 90] = dbg_now(); dbg_ak = 0; dbg_aoff = 0; }
#endif
    return lz_stream(h, dest, raw_total, nblk, blk, tail, gsec, gcnt, ngrp, 1);
}
#endif
/* With the raw ROM checksum, keep the round dispatcher within loader RAM.
   The LZ decoder keeps its existing optimization settings. */
#if defined(AVP_BOOT_ROM_SUM) && !defined(AVP_BOOT_ROM_RETRY)
__attribute__((optimize("Os")))
#endif
static long load_once(const char *name, void (*mark)(void))
{
    Sint32 id, total = 1, r = (name[1] - '0') * 100 + (name[2] - '0') * 10 + (name[3] - '0');
    GfsHn h;
    unsigned long i;
    if (GFS_Init(1, gfs_work, &dir) < 0) return -1;
    id = GFS_NameToId((Sint8 *)"STORE.BIN");
    if (id < 0) { GFS_Reset(); return -2; }
    h = GFS_Open(id);
    if (!h) { GFS_Reset(); return -3; }
    GFS_SetTmode(h, GFS_TMODE_CPU);
    /* The directory is read once and kept (the loader stays resident); so is a one-sector run table, so a load seeks only to its own runs. */
    if (store_dir[0] != 0x53535431u) {
        if (GFS_Fread(h, 1, store_dir, 2048) != 2048 || store_dir[0] != 0x53535431u) { store_dir[0] = 0; GFS_Close(h); GFS_Reset(); return -0x100; }
#ifdef STORE_HEAD2
        if (STORE_HS == 2 && GFS_Fread(h, 1, store_dir + 512, 2048) != 2048) { store_dir[0] = 0; GFS_Close(h); GFS_Reset(); return -0x100; }
#endif
        run_sec = -1;
    }
#ifdef SAT_LOAD_LZ
    lz_blob_base = store_dir[2 + 2 * store_dir[1]];
#endif
    if ((unsigned long)r >= store_dir[1]) { GFS_Close(h); GFS_Reset(); return -0x100; }
    run_next = (Sint32)store_dir[2 + r * 2]; run_end = run_next + (Sint32)store_dir[3 + r * 2]; run_left = 0;
    if (vread(h, 1, (unsigned char *)load_head)) { GFS_Close(h); GFS_Reset(); return -0x101; }
#ifdef SAT_LOAD_COALESCE
    coal_big = 0;
#endif
    for (i = 0; i < load_head[0]; i++) {
        Sint32 secs = (Sint32)(load_head[2 + i * 2] / 2048u);
        if (load_head[1 + i * 2] == 1) { mark(); continue; }
#ifdef SAT_LOAD_LZ
        if (load_head[2 + i * 2] & 1u) {
            if (lz_tile(h, i)) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
            total += (Sint32)(load_head[2 + i * 2] / 2048u);
#ifdef SAT_LOAD_COALESCE
            coal_big = 1;
#endif
            continue;
        }
#endif
#ifdef SAT_LOAD_COALESCE
        /* lane loading, 2026-11-12 (default off): the file lists dozens of regions of one to a few sectors (the ROM pages a stage restores, ~35 in a stage file, ~70 in the front end file), each its own
           GFS read, and each read is its own play command: the CD block seeks and the drive loses a turn between two reads of neighbouring sectors (Ymir: 37 ms each; a console is probably worse). They lie
           one after another in the file, so a group of them is read in one go into the pack room (region 0's address, whose sound data the mark() call above has already taken and which the big
           tile region overwrites after) and each region is then copied to its address. Same bytes at the same addresses; fewer commands. Only regions of up to COAL_MAX sectors, groups up to
           the size of region 0, and only once region 0 (the pack room) has been read. */
        if (i >= 2 && !coal_big && secs <= COAL_MAX && secs > 0 && load_head[1] != 1 && load_head[3] == 1 && load_head[2] >= 65536u) {   /* region 1 is the mark: the sound part in region 0 has been taken */
            unsigned long room = load_head[2] / 2048u, tot = 0;
            unsigned long j = i;
            while (j < load_head[0] && load_head[1 + j * 2] != 1 && (load_head[1 + j * 2] & 3u) == 0 && (load_head[2 + j * 2] % 2048u) == 0 && (load_head[2 + j * 2] / 2048u) <= COAL_MAX && (load_head[2 + j * 2] / 2048u) > 0 && tot + load_head[2 + j * 2] / 2048u <= room) { tot += load_head[2 + j * 2] / 2048u; j++; }
            if (j - i >= 2) {
                unsigned char *stage = (unsigned char *)load_head[1], *p = stage;
                unsigned long k;
                if (vread(h, (Sint32)tot, stage)) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
                for (k = i; k < j; k++) {
                    unsigned long n = load_head[2 + k * 2] / 4u, *d = (unsigned long *)load_head[1 + k * 2], *sp = (unsigned long *)((unsigned long)p | 0x20000000u), q;   /* the staged bytes are read through the cache-through alias: the CD block transfer wrote them behind the cache */
                    for (q = 0; q < n; q++) d[q] = sp[q];
                    p += load_head[2 + k * 2];
                }
                total += (Sint32)tot; i = j - 1;
                continue;
            }
        }
#endif
        if (vread(h, secs, (unsigned char *)load_head[1 + i * 2])) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
        total += secs;
#ifdef SAT_LOAD_COALESCE
        if (i >= 2 && secs > COAL_MAX) coal_big = 1;   /* the tile region is in the pack room: nothing may be staged there any more (regions after it are read one by one; 11-12: staging them over the first 130 sectors of the tile region corrupted 157 of the 287 files) */
#endif
    }
#ifdef SAT_LOAD_SUM
    sat_ld_diag[0]++; sat_ld_diag[1] = round_readback_sum();
#endif
#ifdef AVP_VERIFY_ROUND
    if (r == AVP_VERIFY_ROUND) {
#ifdef SAT_LOAD_SUM
        unsigned long sum = sat_ld_diag[1];
#else
        unsigned long sum = round_readback_sum();
#endif
        if (sum != AVP_VERIFY_ROUND_SUM) {
            LOADER_DIAG[2] = sum;
            total = ROUND_SUM_MISMATCH;
        }
    }
#endif
    GFS_Close(h);
    GFS_Reset();
    return total;
}
static long load_regions(const char *name, void (*mark)(void))
{
    long got = 0;
    int t;
    for (t = 0; t < 3; t++) {
        got = load_once(name, mark);
        if (got >= 0) break;
        store_dir[0] = 0; run_sec = -1;   /* read the directory and run table again */
    }
#ifdef AVP_VERIFY_ROUND
    if (got == ROUND_SUM_MISMATCH) halt(ROUND_SUM_ERROR, LOADER_DIAG[2]);
#endif
    return got;
}
#else
static long load_regions(const char *name, void (*mark)(void))
{
    Sint32 id, ss, n, last, got, total = 1;
    GfsHn h;
    unsigned long i;
    if (GFS_Init(1, gfs_work, &dir) < 0) return -1;
    id = GFS_NameToId((Sint8 *)name);
    if (id < 0) { GFS_Reset(); return -2; }
    h = GFS_Open(id);
    if (!h) { GFS_Reset(); return -3; }
    GFS_GetFileSize(h, &ss, &n, &last);
    GFS_SetTmode(h, GFS_TMODE_CPU);
    GFS_Fread(h, 1, load_head, 2048);
    for (i = 0; i < load_head[0]; i++) {
        Sint32 secs = (Sint32)(load_head[2 + i * 2] / 2048u);
        if (load_head[1 + i * 2] == 1) { mark(); continue; }   /* destination 1: what came before is ready, the caller takes it before later regions overwrite it */
        got = GFS_Fread(h, secs, (void *)load_head[1 + i * 2], secs * 2048);
        if (got != secs * 2048) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
        total += secs;
    }
    GFS_Close(h);
    GFS_Reset();
    return total;
}
#endif
#ifdef SAT_WV_REVEAL
/* Any one file of the disc into RAM (the post-credits reveal reads its code, art and voice this way at the ending, guests.c sat_reveal_call). The caller has masked interrupts and stopped the slave. Returns bytes read, or a negative stage. */
static long load_file(const char *name, void *dest)
{
    Sint32 id, ss, n, last, got;
    GfsHn h;
    if (GFS_Init(1, gfs_work, &dir) < 0) return -1;
    id = GFS_NameToId((Sint8 *)name);
    if (id < 0) { GFS_Reset(); return -2; }
    h = GFS_Open(id);
    if (!h) { GFS_Reset(); return -3; }
    GFS_GetFileSize(h, &ss, &n, &last);
    GFS_SetTmode(h, GFS_TMODE_CPU);
    got = GFS_Fread(h, n, dest, ss * n);
    GFS_Close(h);
    GFS_Reset();
    return got > 0 ? got : -4;
}
/* The port's save record in the Saturn's internal backup RAM, one 64 byte file through the BIOS backup library (unlock_save.h has the format and the rules).
   op 0 reads. op 1 sets flag bits (bits 0 to 7) and, when bit 10 is set, stores the bonus-character setting in bits 8 and 9. op 2 clears flag bits (bits 0 to 7).
   scratch: 24 KB of RAM nobody uses at that moment, 4 byte aligned (the library copies itself into the first 16 KB and keeps its work in the next 8 KB).
   The flags word LOADER_API[3] is what the runtime reads: bit 31 once read, bit 0 the reveal has turned Wolverine on, bit 8 a setting is saved, bits 9 and 10 that setting.
   A write is in the word before it is tried, so a full or missing backup RAM still holds the change for this power-on. A failed read leaves the word clear (nothing saved).
   The device is only formatted when the library says it is unformatted, never for any other state. Returns 0, or a negative stage. */
static __attribute__((optimize("Os"))) long unlock_io(unsigned op, unsigned bits, unsigned char *scratch)
{
    static const Uint8 name[12] = { 'A', 'V', 'P', 'S', 'A', 'T', '_', 'S', 'A', 'V', 'E', 0 };
    BupConfig cfg[3];
    BupStat st;
    BupDir bd;
    BupDate when;
    unsigned char old[SAVE_SIZE], rec[SAVE_SIZE];
    unsigned have = 0;
    long r;
    unsigned long init = *(volatile unsigned long *)0x6000358;
    if (op == 1) {
        LOADER_API[3] |= 0x80000000u | (bits & 0xffu);
        if (bits & 0x400u) LOADER_API[3] = (LOADER_API[3] & ~0x600u) | 0x100u | ((bits & 0x300u) << 1);
    } else if (op == 2) LOADER_API[3] &= ~(bits & 0xffu);
    if (init < 0x100 || init >= 0x80000) return -1;   /* the BIOS's library entry; the function table pointer at 0x6000354 is set by BUP_Init itself */
    BUP_Init((volatile Uint32 *)scratch, (Uint32 *)(scratch + 0x4000), cfg);
    if (!*(volatile unsigned long *)0x6000354) return -1;
    r = BUP_Stat(0, SAVE_SIZE, &st);
    if (r == BUP_UNFORMAT && op) { if (BUP_Format(0)) return -2; r = BUP_Stat(0, SAVE_SIZE, &st); }
    if (r) return -3;
    if (BUP_Dir(0, (Uint8 *)name, 1, &bd) > 0 && !BUP_Read(0, (Uint8 *)name, old)) have = SAVE_SIZE;
    if (!op) {
        int sel = save_sel(old, have);
        LOADER_API[3] = 0x80000000u | save_flags(old, have) | (sel >= 0 ? 0x100u | (unsigned)sel << 9 : 0);
        return 0;
    }
    save_merge2(rec, old, have, op == 1 ? bits & 0xffu : 0, op == 2 ? bits & 0xffu : 0, op == 1 && (bits & 0x400u) ? (int)(bits >> 8 & 3u) : -1);
    for (r = 0; r < 12; r++) bd.filename[r] = name[r];
    for (r = 0; r < 11; r++) bd.comment[r] = "AVP SAVE   "[r];
    bd.comment[10] = 0;
    bd.language = BUP_ENGLISH;
    when.year = 17; when.month = 1; when.day = 1; when.time = 0; when.min = 0; when.week = 0;
    bd.date = BUP_SetDate(&when);
    bd.datasize = SAVE_SIZE;
    bd.blocksize = 0;
    return BUP_Write(0, &bd, rec, 0) ? -4 : 0;
}
/* The one entry the runtime calls (LOADER_API[1]): which 1 load_file(name, dest), else unlock_io(op, bits, scratch). */
static long reveal_io(int which, unsigned a, unsigned b, unsigned c)
{
    return which == 1 ? load_file((const char *)a, (void *)b) : unlock_io(a, b, (unsigned char *)c);
}
#endif
/* The game runs the VDP2 in its 352 wide mode (sat_gfx_init writes TVMD HRESO = 1). That mode needs the system clock change: the BIOS runs the 320 clock, and a 352 mode on the
   320 dot clock gives timing the TV cannot lock on (rolling white noise on the console; Yaba and Ymir show a picture regardless). This is the BIOS's own service, SYS_CHGSYSCK(1)
   (SEGA_SYS.H: the function pointer at 0x06000320; 0 = 26 MHz, 320/640 modes, 1 = 28 MHz, 352/704 modes), exactly what SGL's slInitSystem calls for a 352 mode. It does the SMPC
   command, the NMI wait and the reset of the SCU, A-bus (ASR0/ASR1 = 0x1ff01ff0, AREF = 0x1f), SCU timers and DMA, which are therefore at the BIOS defaults afterwards: the cart is
   brought up after it, never before. Done once, first thing in the loader (before the cart is enabled and anything is loaded), then the boot display is taken again in the 352 mode. */
/* The cart at the timing just set: 4 blocks of 64 KB from 0x700000 (nothing is loaded yet), each filled with i * 0x9e3779b9 XOR 0, 0x55555555, 0xaaaaaaaa, 0xffffffff,
   written through the cache-through alias and read back through the cached one, as the game reads the cart (line fills of lines never fetched before; plain reads if the cache
   is still off). The cache is purged after, so no line of this test outlives it. Nonzero: some word came back wrong. */
static int __attribute__((optimize("Os"), noinline)) cart_soak(void)
{
    unsigned long bad = 0, x = 0, i;
    volatile unsigned long *u = (volatile unsigned long *)0x22700000u;
    for (;;) {
        for (i = 0; i < 0x4000; i++) u[i] = (i * 0x9e3779b9u) ^ x;
        for (i = 0; i < 0x4000; i++) bad |= ((volatile unsigned long *)((unsigned long)u - 0x20000000u))[i] ^ (i * 0x9e3779b9u) ^ x;
        if (x == 0xffffffffu) break;
        x += 0x55555555u; u += 0x4000;
    }
    *(volatile unsigned char *)0xfffffe92 |= 0x10;   /* CCR.CP */
    DIAG_API[6] = bad; DIAG_API[7] = (unsigned long)u;   /* for test runs: the wrong bits, and the block it ended on (0x22730000 = all four ran) */
    return bad != 0;
}
static void clock_352(void)
{
    void (*chgsysck)(unsigned long) = *(void (**)(unsigned long))0x06000320u;
    unsigned o;
    chgsysck(1);
    /* SGL's slInitSystem writes every VDP2 register (all zero but the ones it uses); the runtime sets only what it uses and relies on the rest being zero, which the
       clock change's reset gives on the console only if it really resets them: write the zeros (not TVMD, the read-only status registers, or EXTEN/VRSIZE kept at 0). */
    V2R(0x02) = 0; V2R(0x06) = 0;
    for (o = 0x0e; o < 0x120; o += 2) V2R(o) = 0;
    diag_tvmd = 0x8101;                                 /* SGL's TVMD for 352 x 224 NTSC */
#ifdef AVP_BOOT_BANDS
    diag_reinit_k(0, 0);                                /* the chips were reset: the display again, 352 wide */
#else
    diag_text_init(C_BLACK);
    t_at(DIAG_LINES / 16, (T_COLS - (sizeof "NOW LOADING" - 1)) / 2, "NOW LOADING");
#endif
    diag_info(0x4001u);                                 /* 4001: the BIOS clock change returned */
}
/* The save record read (BIOS backup library). Where it runs is a build choice, because on the console the library is BIOS code that Yaba's HLE never executes:
   default           first thing, before the cart bus timing changes and before any disc read, with the library copied into high work RAM (0x060C0000, 24 KB; HW.BIN loads over it later);
   AVP_BUP_LATE_CART the original place: after the loads, library run from the 4 MB cart at 0x02754000 (hardware diagnosis disc D1);
   AVP_BUP_NONE      no read at boot (the save reads as empty; diagnosis disc D2). */
#ifdef SAT_WV_REVEAL
static void boot_save_read(unsigned char *scratch)
{
#ifdef AVP_BUP_NONE
    (void)scratch;
    diag_stage_k(C_CYAN, 0); diag_stage_k(0, 0); diag_info(0x30ffu);
#else
    long r;
    diag_stage_k(C_CYAN, 0);              /* a cyan band that is the last one means the BIOS library did not return */
    r = unlock_io(0, 0, scratch);
#ifndef AVP_BOOT_BANDS
    diag_col[diag_cur] = C_BLACK; diag_band(diag_cur, C_BLACK);   /* it returned: the cyan band goes */
#endif
    diag_stage_k(0, 0);
    diag_info(0x3000u | ((unsigned)r & 0xffu));   /* 0 read ok; ff -1 no library, fe -2 format, fd -3 stat */
#endif
}
#endif
static void spin(unsigned long n) { while (n--) __asm__ volatile ("nop"); }

#ifdef AVP_CYC_DIAG
/* ---- VDP2 access cycle diagnostic (hwboot lane fix6d, 2026-11-11), -DAVP_CYC_DIAG in BOOT_CFLAGS ----
   The loader never loads the game: after the clock change it builds a frozen numbered-tile picture with the game's VDP2 layer set-up (352 x 224, NBG0/NBG1 2 x 2 character 16 colour
   with 2 word names and the half-reduction fit ZMCTL 0x0101 / increment 1 + 23/256, NBG2 1 x 1 2 word names, NBG3 1 x 1 1 word names, the game's map, cell and palette addresses) and lets
   the pad change, at V-blank IN only, (A) the VRAM access cycle pattern, (B) the layer isolation, (C) the fit on or off. Nothing is written to VRAM after the set-up.
   Every character holds its column number in hex (white digits) over a 14 colour gradient across its dots, so a lost dot column or a shifted cell shows. Bands: NBG0 lines 0 to 47,
   NBG1 48 to 95, NBG2 96 to 119, NBG3 120 to 143; the stripes at the bottom show 0xDsly: s = pattern set, l = layer (0 all, 1..4 = NBG0..3), y = fit (1 on).
   Pattern sets (CYCA0L A0U A1L A1U B0L B0U, B1 as B0): 0 as fix5 ran in play and menus, 1 fix6, 2 the super agent's schedule (two names per reduced layer), 3 one name, one cell per layer
   with CPU slots (meant for the fit off). */
static const unsigned short cd_cyc[4][6] = {
    { 0x0123, 0xff67, 0x4444, 0x4444, 0x5555, 0x5555 },
    { 0x0123, 0xee67, 0xeeee, 0x44ee, 0xeeee, 0xe55e },
    { 0x0167, 0x0123, 0x44ff, 0xffff, 0xf55f, 0xeeee },
    { 0x0123, 0xfe67, 0x4fff, 0xfeff, 0xf5fe, 0xeeee } };
static const unsigned short cd_hue[14] = { 0x001f, 0x01bf, 0x037f, 0x03f6, 0x03e9, 0x13e0, 0x4be0, 0x7fe0, 0x7e40, 0x7c80, 0x7c09, 0x7c16, 0x6c1f, 0x341f };
static const unsigned short cd_font[16] = { 0x7b6f, 0x2c97, 0x73e7, 0x73cf, 0x5bc9, 0x79cf, 0x79ef, 0x7249, 0x7bef, 0x7bcf, 0x7bed, 0x6bae, 0x7927, 0x6b6e, 0x79e7, 0x79e4 };
#define CD_VW32(a, v) (*(volatile unsigned long *)(0x25e00000u + (a)) = (unsigned long)(v))
static void cd_cell(unsigned a, int xoff, int glyph)   /* one 8 x 8, 16 colour cell: pens 1..14 across the dots, the column number in pen 15 (glyph >= 0) */
{
    int y, x;
    for (y = 0; y < 8; y++) {
        unsigned long w = 0;
        for (x = 0; x < 8; x++) {
            unsigned pen = (unsigned)(xoff + x);
            while (pen >= 14) pen -= 14;
            pen++;
            if (glyph >= 0 && y >= 1 && y <= 5) {
                int gy = y - 1;
                if (x < 3 && ((cd_font[glyph >> 4] >> (14 - (gy * 3 + x))) & 1)) pen = 15;
                else if (x >= 4 && x < 7 && ((cd_font[glyph & 15] >> (14 - (gy * 3 + x - 4))) & 1)) pen = 15;
            }
            w = (w << 4) | pen;
        }
        CD_VW32(a + (unsigned)y * 4, w);
    }
}
static void cd_zero(unsigned a, unsigned bytes) { unsigned i; for (i = 0; i < bytes; i += 4) CD_VW32(a + i, 0); }
static void cd_apply(unsigned set, unsigned lay, unsigned fit)   /* only at V-blank IN */
{
    V2R(0x10) = cd_cyc[set][0]; V2R(0x12) = cd_cyc[set][1];
    V2R(0x14) = cd_cyc[set][2]; V2R(0x16) = cd_cyc[set][3];
    V2R(0x18) = cd_cyc[set][4]; V2R(0x1a) = cd_cyc[set][5];
    V2R(0x1c) = cd_cyc[set][4]; V2R(0x1e) = cd_cyc[set][5];
    V2R(0x20) = (unsigned short)(lay ? 1u << (lay - 1) : 0xfu);
    V2R(0x7a) = fit ? 0x1700 : 0; V2R(0x8a) = fit ? 0x1700 : 0; V2R(0x98) = fit ? 0x0101 : 0;
    diag_code(0xd000u | set << 8 | lay << 4 | fit);
}
static unsigned cd_pad(void)   /* the SMPC pad word, active low as saturn/rt/pad.c reads it; one INTBACK per call, SF written before the command */
{
    static unsigned raw = 0xffff;
    volatile unsigned char *m = (volatile unsigned char *)0x20100000u;
    if (!(m[0x63] & 1)) {
        unsigned st = m[0x21], id = m[0x23];
        if (st == 0xf1 && (id >> 4) == 0) raw = ((unsigned)m[0x25] << 8) | m[0x27];
        else if (st == 0xf0) raw = 0xffff;
        if (m[0x61] & 0x20) { m[1] = 0x40; m[0x63] = 1; }
        else { m[1] = 0x00; m[3] = 0x0a; m[5] = 0xf0; m[0x63] = 1; m[0x1f] = 0x10; }
    }
    return raw;
}
static void cyc_diag(void)
{
    unsigned c, r, e, set = 0, lay = 0, fit = 1, prev = 0, raw;
    V2R(0x00) = 0x0101;                 /* display off while the picture is built */
    V2R(0x20) = 0;
    V2R(0x0e) = 0x1300;                 /* four VRAM banks, CRAM mode 1 */
    for (e = 0x10; e <= 0x1e; e += 2) V2R(e) = 0xeeee;
    /* palettes: bank 0 NBG0, 1 NBG1, 2 NBG2, 62 NBG3 (supplement 3), each the same gradient rotated */
    {
        static const unsigned short bk[4] = { 0, 1, 2, 62 };
        unsigned b, p;
        for (b = 0; b < 4; b++) {
            volatile unsigned short *pal = (volatile unsigned short *)(0x25f00000u + (unsigned)bk[b] * 32u);
            pal[0] = 0;
            for (p = 0; p < 14; p++) { unsigned h = p + b * 4; while (h >= 14) h -= 14; pal[p + 1] = cd_hue[h]; }
            pal[15] = 0x7fff;
        }
    }
    /* cells: NBG0 0x20000, NBG1 0x40000 (2 x 2 characters of 128 bytes, one per column 0..23, the 25th blank); NBG2 0x18000, NBG3 0x1c000 (8 x 8 cells, one per column 0..43, the 45th blank) */
    for (c = 0; c < 24; c++) {
        unsigned a0 = 0x20000u + c * 128u, a1 = 0x40000u + c * 128u;
        cd_cell(a0, 0, (int)c); cd_cell(a0 + 32, 8, -1); cd_cell(a0 + 64, 0, -1); cd_cell(a0 + 96, 8, -1);
        cd_cell(a1, 0, (int)c); cd_cell(a1 + 32, 8, -1); cd_cell(a1 + 64, 0, -1); cd_cell(a1 + 96, 8, -1);
    }
    cd_zero(0x20000u + 24 * 128u, 128); cd_zero(0x40000u + 24 * 128u, 128);
    for (c = 0; c < 44; c++) {
        unsigned x8 = c * 8u;
        while (x8 >= 14) x8 -= 14;
        cd_cell(0x18000u + c * 32u, (int)x8, (int)c); cd_cell(0x1c000u + c * 32u, (int)x8, (int)c);
    }
    cd_zero(0x18000u + 44 * 32u, 32); cd_zero(0x1c000u + 44 * 32u, 32);
    /* names: NBG0 page at 0 (32 x 32 characters, 2 words), NBG1 page at 0x8000, NBG2 page at 0x4000 (64 x 64, 2 words), NBG3 page at 0x1e000 (64 x 64, 1 word) */
    for (r = 0; r < 32; r++) for (c = 0; c < 32; c++) {
        unsigned b0 = r < 3 && c < 24, b1 = r >= 3 && r < 6 && c < 24;
        CD_VW32(0x0000u + (r * 32 + c) * 4, (0x1000u + (b0 ? c : 24) * 4));
        CD_VW32(0x8000u + (r * 32 + c) * 4, (1ul << 16) | (0x2000u + (b1 ? c : 24) * 4));
    }
    for (r = 0; r < 64; r++) for (c = 0; c < 64; c++) {
        unsigned b2 = r >= 12 && r < 15 && c < 44, b3 = r >= 15 && r < 18 && c < 44;
        CD_VW32(0x4000u + (r * 64 + c) * 4, (2ul << 16) | (0xc00u + (b2 ? c : 44)));
        *(volatile unsigned short *)(0x25e00000u + 0x1e000u + (r * 64 + c) * 2) = (unsigned short)((14u << 12) | (0x200u + (b3 ? c : 44)));
    }
    /* registers as sat_gfx_init sets them (the fit part is applied at V-blank IN) */
    V2R(0x22) = 0; V2R(0x24) = 0; V2R(0x26) = 0; V2R(0x28) = 0x0101; V2R(0x2a) = 0; V2R(0x2c) = 0; V2R(0x2e) = 0;
    V2R(0x30) = 0; V2R(0x32) = 0; V2R(0x34) = 0; V2R(0x36) = 0x8063; V2R(0x38) = 0; V2R(0x3a) = 0x000f; V2R(0x3c) = 0;
    V2R(0x40) = 0; V2R(0x42) = 0; V2R(0x44) = (unsigned short)(8 | (12 << 8)); V2R(0x46) = (unsigned short)(16 | (20 << 8));
    V2R(0x48) = 0x0101; V2R(0x4a) = 0x0101; V2R(0x4c) = 0x0f0f; V2R(0x4e) = 0x0f0f;
    V2R(0x70) = 0; V2R(0x72) = 0; V2R(0x74) = 0; V2R(0x76) = 0; V2R(0x78) = 1; V2R(0x7c) = 1; V2R(0x7e) = 0;
    V2R(0x80) = 0; V2R(0x82) = 0; V2R(0x84) = 0; V2R(0x86) = 0; V2R(0x88) = 1; V2R(0x8c) = 1; V2R(0x8e) = 0;
    V2R(0x90) = 0; V2R(0x92) = 0; V2R(0x94) = 0; V2R(0x96) = 0; V2R(0x9a) = 0;
    V2R(0xe0) = 0x0001; V2R(0xec) = 0; V2R(0xee) = 0; V2R(0x10a) = 0;
    V2R(0xf0) = 0; V2R(0xf2) = 0; V2R(0xf4) = 0; V2R(0xf6) = 0; V2R(0xf8) = 0x0302; V2R(0xfa) = 0x0504;
    diag_fill(0, DIAG_LINES, C_BLACK);
    cd_apply(set, lay, fit);
    V2R(0x00) = diag_tvmd;              /* display on, 352 x 224 */
    for (;;) {
        unsigned now, edge;
        while (V2R(0x04) & 8) ;
        while (!(V2R(0x04) & 8)) ;      /* V-blank IN */
        raw = cd_pad(); now = ~raw & 0xffffu; edge = now & ~prev; prev = now;
        if (edge & 0x0400u) set = (set + 1) & 3;          /* A: access cycle pattern */
        if (edge & 0x0100u) lay = lay >= 4 ? 0 : lay + 1; /* B: layer isolation */
        if (edge & 0x0200u) fit ^= 1;                     /* C: fit (half reduction) on / off */
        cd_apply(set, lay, fit);
    }
}
#endif

#ifdef SAT_LOAD_SELFTEST
static void st_mark(void) {}
#endif
int main(void)
{
    unsigned char *c;
    volatile unsigned long *cart = (volatile unsigned long *)0x22700000u;   /* the cache-through alias: a cached read could not tell a missing cart */
    volatile unsigned char *cart_id = (volatile unsigned char *)0x24ffffffu;
    unsigned id, tried = 0, saroo = 0;
    volatile unsigned long **vt = (volatile unsigned long **)0x06000000u;
    for (c = &_bstart; c < &_bend; c++) *c = 0;
    diag_init();                                        /* grey screen: the BIOS ran 0.BIN */
    vt[4] = (volatile unsigned long *)diag_exc4; vt[6] = (volatile unsigned long *)diag_exc6;
    vt[9] = (volatile unsigned long *)diag_exc9; vt[10] = (volatile unsigned long *)diag_exc10;
    DIAG_API[1] = (unsigned long)diag_fatal_k; DIAG_API[2] = (unsigned long)diag_done_k; DIAG_API[4] = (unsigned long)diag_reinit_k; DIAG_API[5] = (unsigned long)diag_slave_k;
    diag_stage_k(0, 0);                                 /* band 1: the loader runs */
    clock_352();                                        /* first: it resets the chips and, in Ymir, the cart RAM, so nothing is loaded yet */
#ifdef AVP_CYC_DIAG
    if (V2R(0x04) != 0x1234) cyc_diag();   /* always taken (TVSTAT never reads 0x1234); the test keeps the loader's disc code linked for the build's gates */
#endif
    diag_stage_k(0, 0);                                 /* the clock change is done */
#ifdef SAT_WV_REVEAL
    LOADER_API[1] = (unsigned long)reveal_io;
    LOADER_API[2] = 0;
    LOADER_API[3] = 0;
    LOADER_DIAG[5] = 0; LOADER_DIAG[6] = 0; LOADER_DIAG[7] = 0;   /* the reveal's takeover flag and state (reveal.c) */
#if !defined(AVP_BUP_LATE_CART)
    boot_save_read((unsigned char *)0x060c0000u);
#endif
#endif
    /* The 4 MB cart (ST-TECH-47: ASR0, AREF, then a WORD write of 1 to 0x257efffe). The BIOS's own timing is ASR0 = ASR1 = 0x1ff01ff0, AREF = 0x1f; the working JO disc runs the
       cart on it and never writes ASR0/AREF. Default build: enable the cart on the BIOS timing and verify it, only then switch to ours (0x23301ff0 / 0x13), verify again and go
       back to the BIOS timing if that fails (yellow band). AVP_CART_ORIG (diagnosis discs): ours first, the BIOS's as the fallback. */
#define ABUS_BIOS() do { *(volatile unsigned long *)0x25fe00b0 = 0x1ff01ff0; *(volatile unsigned long *)0x25fe00b4 = 0x1ff01ff0; *(volatile unsigned long *)0x25fe00b8 = 0x0000001f; } while (0)
#define ABUS_OURS() do { *(volatile unsigned long *)0x25fe00b0 = 0x23301ff0; *(volatile unsigned long *)0x25fe00b8 = 0x00000013; } while (0)
#ifdef AVP_CART_ORIG
    for (;;) {
        if (!tried) ABUS_OURS(); else ABUS_BIOS();
        *(volatile unsigned short *)0x257efffe = 1;
        id = *cart_id;
        diag_info(0x1000u | id);                        /* the cart's ID byte: 5c is a 4 MB RAM cart */
        cart[0] = 0x12345678; cart[1] = 0xedcba987;
        if (cart[0] == 0x12345678 && cart[1] == 0xedcba987) break;
        if (tried) diag_fail(id == 0x5c ? 0xe0f0u : 0xe0f2u, C_RED, id);   /* e0f0 the cart did not answer, e0f2 and no 4 MB cart ID either */
        tried = 1;
    }
#else
    /* SAROO (cartridge-slot ODE, firmware tpunix/SAROO Firm_Saturn/game_load.c): its 4 MB RAM cart mode runs on its own A-bus timing, ASR0 = 0x38803880, which its hook on the
       BIOS clock change service (clock_352 above) sets, and it patches retail games' own ASR0 = 0x23301ff0 writes out (game_patch.c). Our writes below undid it, a likely
       cause of the Saroo boot reports (2026-11-16). When the clock change left exactly that value, keep it: no BIOS timing, no faster timing; the cart test still runs.
       Any other value (a console, Fenrir, emulators) takes the old path unchanged. */
    saroo = *(volatile unsigned long *)0x25fe00b0 == 0x38803880u;
    load_saroo = saroo;
#ifdef AVP_TEST_SAROO_LOAD
    load_saroo = 1;   /* test discs: the SAROO read path on any setup */
#endif
    if (!saroo) ABUS_BIOS();                             /* the clock change service leaves the A-bus at these values; written again so nothing depends on how a console's SCU reset left them */
    *(volatile unsigned short *)0x257efffe = 1;
    spin(300000);                                        /* a few ms for the cart after the reset */
    {
        int k;
        for (k = 0; k < 4; k++) {
            id = *cart_id;
            cart[0] = 0x12345678; cart[1] = 0xedcba987;
            if (cart[0] == 0x12345678 && cart[1] == 0xedcba987) break;
            spin(300000);
            *(volatile unsigned short *)0x257efffe = 1;
        }
        diag_info(0x1000u | id);                        /* the cart's ID byte: 5c is a 4 MB RAM cart */
        if (cart[0] != 0x12345678 || cart[1] != 0xedcba987) diag_fail(id == 0x5c ? 0xe0f0u : 0xe0f2u, C_RED, id);   /* red: e0f0 the cart did not answer, e0f2 no 4 MB cart ID either */
    }
#ifndef AVP_ABUS_SAFE   /* AVP_ABUS_SAFE: never try the faster timing */
    /* Fenrir report 11-16 (speckled menus, garbled sprites on a console): two words written once passed on a cart too marginal for our faster timing. Now the faster timing
       has to pass cart_soak (256 KB, four bit patterns, read back through the cache as the game reads) or the cart goes back to the BIOS timing (yellow band, info 2001). A cart
       that keeps up keeps the faster timing; nothing needs a reset, it is one register write either way. */
    if (!saroo) ABUS_OURS();
    *(volatile unsigned short *)0x257efffe = 1;
    if (!saroo && cart_soak()) {
        ABUS_BIOS();
        *(volatile unsigned short *)0x257efffe = 1;
        cart[0] = 0x12345678; cart[1] = 0xedcba987;
        if (cart[0] != 0x12345678 || cart[1] != 0xedcba987) diag_fail(0xe0f1u, C_RED, id);
        tried = 1;
    }
#endif
#endif
    diag_stage_k(tried ? C_YELLOW : 0, 0);              /* yellow: only the BIOS's timing worked, not ours */
    if (tried) diag_info(0x2001u);
    GFS_DIRTBL_TYPE(&dir) = GFS_DIR_NAME;
    GFS_DIRTBL_DIRNAME(&dir) = names;
    GFS_DIRTBL_NDIR(&dir) = BOOT_NAMES;
    if (GFS_Init(1, gfs_work, &dir) < 0) halt(0xe001, 0);
    diag_stage_k(0, 0);                                 /* GFS_Init passed */
#ifdef SAT_BOOT_DISC_ORDER   /* lane loading, 2026-11-12: the five files in the order they lie on the disc (COLD1 43, HW 109, LW 385, OPX 896, ROM 1106), so the drive sweeps forward once instead of jumping back four times. Same bytes to the same addresses. */
    diag_stage_k(0, 0); load("COLD1.BIN", (void *)COLD1_ADDR, 0x600);
    diag_stage_k(0, 0); load("HW.BIN", (void *)ENTRY, 0x400);
    diag_stage_k(0, 0); load("LW.BIN", (void *)0x00200000u, 0x100);
    diag_stage_k(0, 0); load("OPX.BIN", (void *)0x02600000u, 0x300);
    diag_stage_k(0, 0); load("ROM.BIN", (void *)0x02400000u, 0x200);
#else
    diag_stage_k(0, 0); load("LW.BIN", (void *)0x00200000u, 0x100);
    diag_stage_k(0, 0); load("ROM.BIN", (void *)0x02400000u, 0x200);
    diag_stage_k(0, 0); load("OPX.BIN", (void *)0x02600000u, 0x300);
    diag_stage_k(0, 0); load("COLD1.BIN", (void *)COLD1_ADDR, 0x600);
    diag_stage_k(0, 0); load("HW.BIN", (void *)ENTRY, 0x400);
#endif
#ifdef AVP_BOOT_ROM_SUM
    {
        unsigned long sum = boot_readback_sum((const void *)0x02400000u, 0x200000u);
        if (sum != AVP_BOOT_ROM_SUM) halt(0x207, sum);
    }
#endif
    GFS_Reset();
#ifdef SAT_WV_REVEAL
#if defined(AVP_BUP_LATE_CART)
    boot_save_read((unsigned char *)0x02754000u);   /* the original: scratch in the cart's pack room, which the first round file fills later */
#endif
#ifdef GUEST_SEL_ADDR   /* a saved BONUS CHARACTERS setting replaces the build default in the cart data (guests.c sat_guest_sel), so no runtime code has to apply it */
    if (LOADER_API[3] & 0x100u) *(volatile unsigned char *)GUEST_SEL_ADDR = (unsigned char)(LOADER_API[3] >> 9 & 3u);
#endif
#endif
#ifdef SAT_LOAD_SELFTEST   /* test build only: load every round file in turn and compare the SAT_LOAD_SUM sum of its regions with the expected sums the builder put in the store header (tools/lzstore.py, from the original round files). Never enters the game.
                              Results in sat_ld_diag (words 2 fails, 3 first failing round, 4 rounds done, 5 rounds in the store, 7 the marker). The boot display's stripes show 0xAnnn while running, 0xFnnn at the end (nnn = fails). */
    {
        volatile unsigned long *res = sat_ld_diag + 2, *sum = sat_ld_diag;
        { volatile unsigned long ka = 0x6b7c9a21ul, kb = 0x2726c975ul; sat_ld_diag[7] = ka ^ kb; }   /* 0x4c5a5354, 'LZST', built at run time so the literal is not in the code image the route also finds */
        unsigned long r, nr = 0, fails = 0, first = 0xffffffffu;
        char nm[] = "R000.BIN";
        res[0] = 0; res[1] = 0xffffffffu; res[2] = 0;
        for (r = 0; r < 512; r++) {
            long got;
            nm[1] = (char)('0' + r / 100); nm[2] = (char)('0' + r / 10 % 10); nm[3] = (char)('0' + r % 10);
            got = load_regions(nm, st_mark);
            if (r == 0) nr = store_dir[1];
            if (got < 0 || sum[1] != store_dir[3 + 2 * nr + r])   /* the builder put the expected sums after the blob base word of the store header */ { fails++; if (first == 0xffffffffu) first = r; }
            res[0] = fails; res[1] = first; res[2] = r + 1; res[3] = nr;
            if ((r & 7) == 0) diag_info(0xa000u | (unsigned)r);
            if (r + 1 >= nr) break;
        }
        diag_info(0xf000u | (unsigned)(fails & 0xfff));
        for (;;) __asm__ volatile ("nop");
    }
#endif
    LOADER_API[0] = (unsigned long)load_regions;
    diag_stage_k(0, 0);                                 /* the runtime is entered next */
    *(volatile unsigned char *)0xfffffe92 = 0x10;
    *(volatile unsigned char *)0xfffffe92 = 0x01;
    ((void (*)(void))ENTRY)();
    return 0;
}
