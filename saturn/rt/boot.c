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
extern unsigned char _bstart, _bend;
static unsigned char gfs_work[GFS_WORK_SIZE(1)];
static GfsDirTbl dir;
static GfsDirName names[256];
/* ---- boot display (hardware bring-up, hwboot lane 2026-11-10) ----
   The BIOS leaves its SEGA logo up until the runtime's first picture, and a failure here used to spin with the logo still showing. From the first
   instruction of this file the screen is ours: VDP2's back screen in per-line mode shows one band per boot step (a white 2-line tick moves inside
   the current band while a file is read), the bottom stripes hold a 16 bit value (white = 1, black = 0, most significant bit on top), and a
   failure turns the current band red (exception: magenta) and flashes the whole screen with the code. The runtime reaches this through
   DIAG_API (stage, fatal, done) until its own first picture. No scroll screen, sprite or SGL is used; VDP2 registers are write-only, so none is saved. */
#define V2R(o) (*(volatile unsigned short *)(0x25f80000u + (o)))
#define DIAG_TAB ((volatile unsigned short *)0x25e7fe00u)   /* last 512 bytes of VDP2 VRAM: back screen table, one colour per line */
#define DIAG_API ((volatile unsigned long *)0x06013fa0u)    /* 0 stage(colour or 0), 1 fatal(code, detail), 2 done(restore), 3 active, 4 reinit (after the runtime's VRAM clear) */
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
static unsigned short diag_col[DIAG_BANDS + 1];
static int diag_active, diag_seq, diag_cur, diag_ticks, diag_mark;
static unsigned diag_info_value;
static void diag_fill(int a, int b, unsigned short c) { for (; a < b && a < DIAG_LINES; a++) DIAG_TAB[a] = c; }
static void diag_band(int k, unsigned short c) { if (k < DIAG_BANDS) diag_fill(1 + 6 * k, 6 + 6 * k, c); }
static void diag_code(unsigned v)
{
    int i;
    diag_info_value = v;
    for (i = 0; i < 16; i++) {
        diag_fill(DIAG_CODE_TOP + 4 * i, DIAG_CODE_TOP + 4 * i + 3, ((v >> (15 - i)) & 1) ? C_WHITE : C_BLACK);
        diag_fill(DIAG_CODE_TOP + 4 * i + 3, DIAG_CODE_TOP + 4 * i + 4, C_GREY);
    }
}
static void diag_render(unsigned code)
{
    int k;
    diag_fill(0, DIAG_LINES, C_GREY);
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
    if (!c) c = (diag_seq & 1) ? C_BLUE : C_GREEN;
    diag_cur = diag_seq;
    if (diag_seq < DIAG_BANDS) diag_col[diag_seq] = c;
    diag_band(diag_seq, c);
    diag_seq++;
    diag_ticks = 0; diag_mark = -1;
}
static void diag_tick(void)
{
    int top, k = diag_cur;
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
    diag_fill(0, DIAG_LINES, C_GREY);
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
static void diag_fail(unsigned code, unsigned short colour, unsigned extra)
{
    LOADER_DIAG[0] = 0x4156504c; LOADER_DIAG[1] = code; LOADER_DIAG[2] = extra;
    if (!diag_active) for (;;) __asm__ volatile ("nop");
    __asm__ volatile ("ldc %0,sr" : : "r"(0xf0));
    if (diag_cur < DIAG_BANDS) diag_col[diag_cur] = colour;
    for (;;) {
        diag_fill(0, DIAG_LINES, colour);
        diag_wait(30);
        diag_render(code);
        diag_wait(60);
        if (extra) { diag_render(extra & 0xffffu); diag_wait(60); }
    }
}
static void diag_fatal_k(unsigned long code, unsigned long detail)   /* the runtime's sat_fatal, before its first picture */
{
    diag_fail((unsigned)((code & 0xff) << 8 | (detail & 0xff)), code >= 0xf0 ? C_MAGENTA : C_RED, (unsigned)detail & 0xffffu);
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
static void diag_exc_c(unsigned long pc, unsigned long vec) { diag_fail(0xfe00u | (unsigned)vec, C_MAGENTA, (unsigned)pc & 0xffffu); }
__asm__(".text\n.align 2\n"
        ".global _diag_exc4\n_diag_exc4: mov.l @r15,r4\n bra 9f\n mov #4,r5\n"
        ".global _diag_exc6\n_diag_exc6: mov.l @r15,r4\n bra 9f\n mov #6,r5\n"
        ".global _diag_exc9\n_diag_exc9: mov.l @r15,r4\n bra 9f\n mov #9,r5\n"
        ".global _diag_exc10\n_diag_exc10: mov.l @r15,r4\n mov #10,r5\n"
        "9: mov.l 1f,r0\n jmp @r0\n nop\n.align 2\n1: .long _diag_exc_tramp\n");
extern void diag_exc4(void), diag_exc6(void), diag_exc9(void), diag_exc10(void);
void diag_exc_tramp(unsigned long pc, unsigned long vec) { diag_exc_c(pc, vec); }
static void halt(unsigned long s, unsigned long d)
{
    diag_fail((unsigned)s, C_RED, (unsigned)d & 0xffffu);
}
#define LOAD_CHUNK 128   /* sectors per read, so the tick moves while a file loads */
static void load(const char *name, void *dest, unsigned long code)
{
    Sint32 id = GFS_NameToId((Sint8 *)name), ss, n, last, got, total = 0, left;
    unsigned char *d = (unsigned char *)dest;
    GfsHn h;
    if (id < 0) halt(code | 1, (unsigned long)id);
    h = GFS_Open(id);
    if (!h) halt(code | 2, 0);
    GFS_GetFileSize(h, &ss, &n, &last);
    GFS_SetTmode(h, GFS_TMODE_CPU);
    for (left = n; left > 0; ) {
        Sint32 c = left > LOAD_CHUNK ? LOAD_CHUNK : left;
        got = GFS_Fread(h, c, d, ss * c);
        if (got <= 0) { GFS_Close(h); halt(code | 3, (unsigned long)got); }
        total += got; d += ss * c; left -= c;
        diag_tick();
    }
    GFS_Close(h);
    LOADER_DIAG[3] = code; LOADER_DIAG[4] = (unsigned long)total;
}
/* Between rounds the runtime calls this through LOADER_API (lifted code never does): one file of whole sectors, its first sector a list of
   u32 count, then count pairs of u32 destination, u32 bytes (multiples of 2048), destination 1 being a call to mark. The caller has masked interrupts and stopped the slave. Returns sectors read, or a negative stage. */
static unsigned long load_head[512];
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
static Sint32 run_at, run_left, run_sec = -1, run_next, run_end;
#ifdef SAT_LOAD_COALESCE
#define COAL_MAX 64u   /* sectors; every restore region of the stage files and the front end file is below this, the tile and sound regions are not */
#endif
#ifdef SAT_LOAD_SUM
static unsigned long load_sum;
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
        }
        take = secs < run_left ? secs : run_left;
        if (take > LOAD_CHUNK) take = LOAD_CHUNK;
        got = GFS_Fread(h, take, dest, take * 2048);
        if (got != take * 2048) return -4;
        diag_tick();
        run_at += take; run_left -= take; secs -= take; dest += take * 2048;
    }
    return 0;
}
static long load_regions(const char *name, void (*mark)(void))
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
    if ((unsigned long)r >= store_dir[1]) { GFS_Close(h); GFS_Reset(); return -0x100; }
    run_next = (Sint32)store_dir[2 + r * 2]; run_end = run_next + (Sint32)store_dir[3 + r * 2]; run_left = 0;
    if (vread(h, 1, (unsigned char *)load_head)) { GFS_Close(h); GFS_Reset(); return -0x101; }
#ifdef SAT_LOAD_SUM
    load_sum = 0;
#endif
    for (i = 0; i < load_head[0]; i++) {
        Sint32 secs = (Sint32)(load_head[2 + i * 2] / 2048u);
        if (load_head[1 + i * 2] == 1) { mark(); continue; }
#ifdef SAT_LOAD_COALESCE
        /* lane loading, 2026-11-12 (default off): the file lists dozens of regions of one to a few sectors (the ROM pages a stage restores, ~35 in a stage file, ~70 in the front end file), each its own
           GFS read, and each read is its own play command: the CD block seeks and the drive loses a turn between two reads of neighbouring sectors (Ymir: 37 ms each; a console is probably worse). They lie
           one after another in the file, so a group of them is read in one go into the pack room (region 0's address, whose sound data the mark() call above has already taken and which the big
           tile region overwrites after) and each region is then copied to its address. Same bytes at the same addresses; fewer commands. Only regions of up to COAL_MAX sectors, groups up to
           the size of region 0, and only once region 0 (the pack room) has been read. */
        if (i >= 2 && secs <= COAL_MAX && secs > 0 && load_head[1] != 1 && load_head[3] == 1 && load_head[2] >= 65536u) {   /* region 1 is the mark: the sound part in region 0 has been taken */
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
    }
#ifdef SAT_LOAD_SUM   /* test flag: a rotating sum of every byte the regions wrote, read back from their addresses, so two builds' loads of one file can be compared: 0x06013ff8 counts the loads, 0x06013ffc holds the last sum (LOADER_DIAG[6] and [7], the reveal's state words, which a test run does not reach) */
    {
        unsigned long k, q, sum = 0;
        for (k = 0; k < load_head[0]; k++) {
            unsigned long dst = load_head[1 + k * 2], n = load_head[2 + k * 2] / 4u;
            volatile unsigned long *d = (volatile unsigned long *)(dst | 0x20000000u);
            if (dst == 1) continue;
            for (q = 0; q < n; q++) sum = (sum << 1 | sum >> 31) ^ d[q];
        }
        ((volatile unsigned long *)0x06013ff8u)[0]++; ((volatile unsigned long *)0x06013ff8u)[1] = sum;
    }
#endif
    GFS_Close(h);
    GFS_Reset();
    return total;
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
static long unlock_io(unsigned op, unsigned bits, unsigned char *scratch)
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
    diag_reinit_k(0, 0);                                /* the chips were reset: the display again, 352 wide */
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

int main(void)
{
    unsigned char *c;
    volatile unsigned long *cart = (volatile unsigned long *)0x22700000u;   /* the cache-through alias: a cached read could not tell a missing cart */
    volatile unsigned char *cart_id = (volatile unsigned char *)0x24ffffffu;
    unsigned id, tried = 0;
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
    ABUS_BIOS();                                         /* the clock change service leaves the A-bus at these values; written again so nothing depends on how a console's SCU reset left them */
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
#ifndef AVP_ABUS_BIOS
    ABUS_OURS();
    *(volatile unsigned short *)0x257efffe = 1;
    cart[0] = 0x87654321; cart[1] = 0x0123456f;
    if (cart[0] != 0x87654321 || cart[1] != 0x0123456f) {
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
    GFS_DIRTBL_NDIR(&dir) = 256;
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
    GFS_Reset();
#ifdef SAT_WV_REVEAL
#if defined(AVP_BUP_LATE_CART)
    boot_save_read((unsigned char *)0x02754000u);   /* the original: scratch in the cart's pack room, which the first round file fills later */
#endif
#ifdef GUEST_SEL_ADDR   /* a saved BONUS CHARACTERS setting replaces the build default in the cart data (guests.c sat_guest_sel), so no runtime code has to apply it */
    if (LOADER_API[3] & 0x100u) *(volatile unsigned char *)GUEST_SEL_ADDR = (unsigned char)(LOADER_API[3] >> 9 & 3u);
#endif
#endif
    LOADER_API[0] = (unsigned long)load_regions;
    diag_stage_k(0, 0);                                 /* the runtime is entered next */
    *(volatile unsigned char *)0xfffffe92 = 0x10;
    *(volatile unsigned char *)0xfffffe92 = 0x01;
    ((void (*)(void))ENTRY)();
    return 0;
}
