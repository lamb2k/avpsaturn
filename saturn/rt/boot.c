/* First read at 0x06004000: map the cart, load segments from disc, enter the runtime. Lifted code never sees GFS. */
#include "SEGA_GFS.H"
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
static void diag_takeover(void)
{
    V2R(0x20) = 0;                        /* BGON: no scroll screen */
    V2R(0xf0) = 0; V2R(0xf2) = 0; V2R(0xf4) = 0; V2R(0xf6) = 0;   /* PRISA-D: sprite priority 0 hides the logo's VDP1 sprites */
    V2R(0xec) = 0;                        /* CCCTL */
    V2R(0x10) = 0xffff; V2R(0x12) = 0xffff; V2R(0x14) = 0xffff; V2R(0x16) = 0xffff;   /* VRAM cycle patterns: no layer reads VRAM, so none can show (the runtime's init leaves its own) */
    V2R(0x18) = 0xffff; V2R(0x1a) = 0xffff; V2R(0x1c) = 0xffff; V2R(0x1e) = 0xffff;
    V2R(0x00) = 0x8000;                   /* TVMD: display on, 320 x 224 */
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
        V2R(0x00) = 0x8001; V2R(0xac) = 0; V2R(0xae) = 0xffff;
        V2R(0x10) = 0x012f; V2R(0x12) = 0xff6f; V2R(0x14) = 0x4444; V2R(0x16) = 0x4444;
        V2R(0x18) = 0x5555; V2R(0x1a) = 0x5555; V2R(0x1c) = 0x5555; V2R(0x1e) = 0x5555;
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
    for (i = 0; i < load_head[0]; i++) {
        Sint32 secs = (Sint32)(load_head[2 + i * 2] / 2048u);
        if (load_head[1 + i * 2] == 1) { mark(); continue; }
        if (vread(h, secs, (unsigned char *)load_head[1 + i * 2])) { GFS_Close(h); GFS_Reset(); return -4 - (long)i; }
        total += secs;
    }
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
#define ABUS_BIOS() do { *(volatile unsigned long *)0x25fe00b0 = 0x1ff01ff0; *(volatile unsigned long *)0x25fe00b8 = 0x0000001f; } while (0)
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
    *(volatile unsigned short *)0x257efffe = 1;          /* the BIOS's timing is still in force */
    id = *cart_id;
    diag_info(0x1000u | id);                            /* the cart's ID byte: 5c is a 4 MB RAM cart */
    cart[0] = 0x12345678; cart[1] = 0xedcba987;
    if (cart[0] != 0x12345678 || cart[1] != 0xedcba987) diag_fail(id == 0x5c ? 0xe0f0u : 0xe0f2u, C_RED, id);   /* red: e0f0 the cart did not answer, e0f2 no 4 MB cart ID either */
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
    diag_stage_k(0, 0); load("LW.BIN", (void *)0x00200000u, 0x100);
    diag_stage_k(0, 0); load("ROM.BIN", (void *)0x02400000u, 0x200);
    diag_stage_k(0, 0); load("OPX.BIN", (void *)0x02600000u, 0x300);
    diag_stage_k(0, 0); load("COLD1.BIN", (void *)COLD1_ADDR, 0x600);
    diag_stage_k(0, 0); load("HW.BIN", (void *)ENTRY, 0x400);
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
