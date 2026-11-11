/* HOST exactness test of SAT_S1_DIRTY (lane perf2, 2026-11-11), the incremental scroll 1 redraw, against the same build without it (SAT_S1_MEMO + SAT_S1_BLANKROWS).
 * The two builds are not byte identical in VDP2 VRAM (a full redraw may evict a tile and upload it again in another slot, an incremental one cannot), so each frame prints
 *   hash A: the resolved scroll 1 layer: every visible name table entry followed to its 8x8 cell contents, palette bank and flips (the picture), only on frames that draw scroll 1;
 *   hash B: VDP1 VRAM, CRAM, the register mirrors and VDP2 VRAM outside scroll 1's name table and cell slab (everything else the frame wrote).
 * Both must match frame for frame. The generator makes HUD-like play content with dirty-row patterns: single cell edits, rows cleared to a blank word or set to one tile, runs of
 * repeated tiles (rows that are fully droppable yet hold tiles), banners of 2 to 4 rows that join and split blocks, the story box rows, position moves, play flag and character select
 * flags toggling, scroll 1 switched off for some frames, bursts of many new tiles (cache pressure, evictions with a pack of 1800 tiles in a 764 slot cache) and frames with more
 * distinct tiles than slots (refusals: the next picture must take the full path). In the incremental build the in-draw verify pass recomputes every kept row and counts the ones whose names
 * differ from what a full redraw would write; the count must be 0. stderr: totals. Build with -DNS1=1800 for pressure, -DTHR for the two thread mode. Run tests/host_gfx_s1_dirty.sh.
 * Based on host_gfx_s1_identity.c: 
 * Scroll 1 is HUD-like: mostly one blank word (no tile in the pack), a few rows with real tiles that come and go, a position that mostly holds, menu modes and
 * the play flag toggling. VDP1 VRAM, VDP2 VRAM, CRAM and register hashes must match frame for frame. Built on host_gfx_layers_identity.c. Run tests/host_gfx_s1_identity.sh.
 * Original header: Host identity harness with the scroll layers ON (the older ident.c has them off). Synthetic data, no ROM.
 * Random objects, random layer cell words with real pack tiles in all four sections, scrolls, row scroll, palette changes, still frames (sums unchanged).
 * Output: per frame commands, uploads, and an FNV hash of VDP1 VRAM, VDP2 VRAM, CRAM and the VDP register mirrors.
 * Modes (argv[1]): seq = sat_gfx_frame; thr = master thread runs sat_gfx_snapshot_begin, wakes the slave thread, sleeps a random time, runs
 * sat_gfx_snapshot_layers; the slave thread runs sat_gfx_draw. Same inputs, so a torn layer read changes a hash. Build with -DTHR for thr.
 * Run with tests/host_gfx_layers_identity.sh. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sat_gfx.h"
#ifdef THR
#include <pthread.h>
#include <unistd.h>
#include <time.h>
extern unsigned long sat_gfx_layers_late, sat_gfx_layers_timeout;
#endif
#ifdef SAT_S1_DIRTY
extern unsigned long sat_s1d[8]; extern unsigned char sat_s1d_verify;
#endif

unsigned char *PAGE[256];
volatile int sat_home_mode, sat_home_hold; volatile unsigned long sat_home_seq; char sat_home_shown[28][44], sat_home_text[28][44];
#ifdef SAT_HOME_FONT_COLD
const unsigned char sat_home_font[58 * 32] = {
#include "home_font.inc"
};
const unsigned char sat_home_pal[64] = {
#include "home_pal.inc"
};
#endif
unsigned char RAMB[0x10000];
static unsigned char OBJ[0x10000], GFX0[0x10000], GFX1[0x10000], GFX2[0x10000], ZERO[0x10000];
static unsigned char V1[0x80000], V2[0x80000], CR[0x1000];
unsigned char *sat_gfx_host_vdp1 = V1, *sat_gfx_host_vdp2 = V2, *sat_gfx_host_cram = CR;
unsigned short sat_gfx_host_vdp1r[0x10], sat_gfx_host_vdp2r[0x90];
unsigned long sat_gfx_host_ticks(void) { static unsigned long t; return (t += 3) & 0xffff; }

static void w16(unsigned char *p, unsigned v) { p[0] = (unsigned char)(v >> 8); p[1] = (unsigned char)v; }
static void w32(unsigned char *p, unsigned long v) { w16(p, (unsigned)(v >> 16)); w16(p + 2, (unsigned)(v & 0xffff)); }

#ifndef NS1
#define NS1 700
#endif
#define NS2 300
#define NS3 300
#define NSP 4000
static unsigned long rs = 777;
static unsigned rnd(void) { rs = rs * 1103515245UL + 12345UL; return (unsigned)(rs >> 16) & 0x7fff; }

/* Pack: 4 sections of keys 0..n-1, payload i = bytes from a generator so every tile differs. */
static unsigned char *make_pack(void)
{
    unsigned long counts[4] = { NSP, NS1, NS2, NS3 }, slot[4] = { 128, 32, 128, 512 }, shift[4] = { 16, 14, 14, 14 };
    unsigned long hdr = 84, off = hdr, keyoff[4], dataoff[4], i, k;
    unsigned char *p;
    for (i = 0; i < 4; i++) { keyoff[i] = off; off += counts[i] * 4; }
    for (i = 0; i < 4; i++) { dataoff[i] = off; off += counts[i] * slot[i]; }
    p = (unsigned char *)calloc(off, 1);
    w32(p, 0x53475031UL);
    for (i = 0; i < 4; i++)
    {
        w32(p + 4 + i * 12, counts[i]); w32(p + 8 + i * 12, keyoff[i]); w32(p + 12 + i * 12, dataoff[i]);
        w32(p + 52 + i * 8, counts[i]); w32(p + 56 + i * 8, hdr);   /* split past the end: no spill */
        for (k = 0; k < counts[i]; k++)
        {
            unsigned long j;
            w32(p + keyoff[i] + k * 4, (k << shift[i]) | k);
            for (j = 0; j < slot[i]; j++) p[dataoff[i] + k * slot[i] + j] = (unsigned char)((k * 31 + j * 7 + i) & 0xff) | (j == 0 ? 0x11 : 0);
        }
    }
    return p;
}

extern unsigned long sat_gfx_s1_draws;
static unsigned long h, tot_lu, tot_up, max_lu, refused_before, draws_before;
static void mix(const unsigned char *p, unsigned long n) { unsigned long i; for (i = 0; i < n; i++) h = (h ^ p[i]) * 16777619UL; }

static void set_layer_word(unsigned char *base, unsigned off, unsigned code, unsigned attr) { w16(base + off, code); w16(base + off + 2, attr); }

/* Scroll map cells: s1 row_bits 5 ((r&31) + (c<<5) + ((r&32)<<6)) words of 4 bytes; s2 row_bits 4; s3 row_bits 3 (see snap_layer). Random cell edits cover all of them. */
static void edit_layers(int heavy)
{
    int i, n = heavy ? 400 : 6;
    for (i = 0; i < n; i++)
    {
        unsigned off = (rnd() * 3 % 0x1000) * 4;   /* within the first 16 KB of a map */
        set_layer_word(GFX0, 0x4000 + (rnd() * 3 % 0x1000) * 4 % 0x4000, rnd() % NS2, rnd() & 0x7f);
        set_layer_word(GFX0, 0x8000 + (rnd() * 3 % 0x1000) * 4 % 0x4000, rnd() % NS3, rnd() & 0x7f);
    }
}

static int cur_layers, cur_sx, cur_sy;
/* index of the scroll 1 word of map row r, column c (see snap_layer: row_bits 5) */
static unsigned s1i(int r, int c) { return (unsigned)(((r & 31) + ((c & 63) << 5) + ((r & 32) << 6)) * 4); }
static unsigned blank_word_code(void) { return (rnd() % 3) ? 0xfff0 : 0xffe0 + rnd() % 8; }   /* codes the pack does not hold: no tile (a few different blanks) */
static unsigned vocab(int wide) { return wide ? rnd() % (NS1 / 2) : 2 + rnd() % 40; }
static void s1set(int r, int c, unsigned code, unsigned attr) { set_layer_word(GFX0, s1i(r, c), code, attr); }
static int visible_row0(void) { return (cur_sy + 16) >> 3; }   /* y0 >> 3 of the slave, see draw_scroll1 */
static int visible_col0(void) { return (cur_sx + 64 + 16) >> 3; }

static void edit_s1(int f)
{
    int i, r, c, k, v0 = visible_row0(), c0 = visible_col0();
    static int wide_mode, boxes;
    unsigned blank = 0xfff0, t = rnd() % 100;
    if (f == 0) for (i = 0; i < 0x1000; i++) set_layer_word(GFX0, i * 4, blank, 0);
    if (f == 1) for (r = 0; r < 4; r++) for (c = 0; c < 44; c++) s1set(v0 + r, c0 + c, vocab(0), (unsigned)(rnd() & 0x7f) & 0x3f);   /* a first HUD */
    if (t < 38) return;                                                       /* still: the sum does not move */
    if (t < 62)
    {   /* HUD rows: a few cells of a top or bottom row change (a score digit, a bar) */
        static const int hud[] = { 0, 1, 2, 3, 4, 5, 25, 26, 27, 28 };
        r = hud[rnd() % 10]; k = 1 + (int)(rnd() % 6);
        for (i = 0; i < k; i++) s1set(v0 + r, c0 + (int)(rnd() % 46), (rnd() % 4) ? vocab(wide_mode) : blank_word_code(), (rnd() & 0x7f) & 0x3f);
    }
    else if (t < 68) { r = (int)(rnd() % 29); k = (int)blank_word_code(); for (c = 0; c < 64; c++) s1set(v0 + r, c, (unsigned)k, 0); }       /* a row cleared to a blank word */
    else if (t < 72) { r = (int)(rnd() % 29); k = (int)vocab(0); for (c = 0; c < 64; c++) s1set(v0 + r, c, (unsigned)k, 0); }               /* a row of one tile: all droppable, yet drawn */
    else if (t < 77)
    {   /* runs of repeated tiles with gaps: a fully droppable row with different tiles, or a row with a lone cell */
        r = (int)(rnd() % 29);
        for (c = 0; c < 64; c++) s1set(v0 + r, c, ((c / 3) % 2) ? vocab(0) : blank_word_code(), 0);
        if (rnd() % 2) s1set(v0 + r, c0 + (int)(rnd() % 44), vocab(0), 0);
    }
    else if (t < 84)
    {   /* a banner of 2 to 4 rows with content over a span of columns, or cleared again: blocks join and split */
        int n = 2 + (int)(rnd() % 3), cs = (int)(rnd() % 20), cl = 6 + (int)(rnd() % 20), on = (int)(rnd() % 3);
        r = (int)(rnd() % 26);
        for (i = 0; i < n; i++) for (c = 0; c < cl; c++) s1set(v0 + r + i, c0 + cs + c, on ? vocab(wide_mode) : blank_word_code(), 0);
    }
    else if (t < 88)
    {   /* the story box: face and text on rows 8 to 10 or 11, blanks at the sides */
        int n = 3 + (int)(rnd() % 2), on = (int)(rnd() % 3);
        boxes++;
        for (i = 0; i < n; i++) for (c = 0; c < 64; c++) s1set(v0 + 8 + i, c, (on && c >= c0 + 5 && c < c0 + 40) ? vocab(0) : blank_word_code(), 0);
    }
    else if (t < 92)
    {   /* a new screen of tiles from a pool of codes: at most 2 keys a code (column parity), so well under the 764 slots in view, but over many screens the pack's 1800 keys wear the cache (evictions);
           one in 6 uses a pool of 500 codes (about 1000 keys): more distinct tiles than slots, so the draw refuses some (the next picture must be a full one; its victims differ from the reference's, so those frames are not compared) */
        int pool = (rnd() % 6) ? 40 + (int)(rnd() % 200) : 760, base = (int)(rnd() % (NS1 / 2 > pool ? NS1 / 2 - pool : 1)), q;
        wide_mode = 1;
        for (r = 0; r < 29; r++) for (q = 0; q < 45; q++) s1set(v0 + r, c0 + q, (rnd() % 12) ? (unsigned)(base + (int)(rnd() % pool)) % (NS1 / 2) : blank_word_code(), (rnd() & 0x7f) & 0x3f);
    }
    else if (t < 95) { wide_mode = 0; for (i = 0; i < 0x1000; i++) set_layer_word(GFX0, i * 4, blank, 0); }   /* everything blank again */
    else
    {   /* rows swap content: a word changes only in attribute (palette/flip) */
        r = (int)(rnd() % 29);
        for (c = 0; c < 20; c++) { unsigned a = (unsigned)(rnd() & 0x7f) & 0x3f; unsigned code = (rnd() % 2) ? vocab(0) : blank_word_code(); s1set(v0 + r, c0 + c, code, a); }
    }
}

static void frame_state(int f)
{
    int i, n = 20 + (int)(rnd() % 120), still = (rnd() % 4) == 0, mask = (int)(rnd() % 8) << 1;   /* layers bits 2 4 8 */
    unsigned s;
    if (f < 3) mask = 14;
    if (rnd() % 4) mask |= 2;   /* scroll 1 mostly on */
    cur_layers = mask;
    w16(RAMB + 0x804a, 0x12c0 | mask);
    w16(RAMB + 0x8044, (rnd() % 3) ? 0 : 1);   /* video bit 0: row scroll */
    w16(RAMB + 0x8050, 0x2377 ^ (rnd() % 5 ? 0 : 0x0110));   /* priority word */
    if (!still)
    {
        for (s = 0; s < 3; s++)
        {
            /* scroll registers at 0xffee1a.. = RAMB + 0xee1a: s1x s1y s2x s2y s3x s3y */
            w16(RAMB + 0xee1a + s * 4, (unsigned)(rnd() % 600)); w16(RAMB + 0xee1c + s * 4, (unsigned)(rnd() % 300));
        }
        edit_layers((rnd() % 5) == 0);
        w16(RAMB + 0xee2e, (unsigned)(rnd() % 64));
        for (i = 0; i < 0x400; i++) w16(GFX0 + 0xe000 + i * 2 % 0x1000, (unsigned)((rnd() % 7) ? 0 : rnd() % 9));
    }
    edit_s1(f);
    {   /* scroll 1 holds its position most frames; the play flag and menu modes toggle */
        static unsigned s1x = 40, s1y = 20;
        static int mode = 2, hud = 1;
        if (rnd() % 25 == 0) { s1x = rnd() % 600; s1y = rnd() % 300; }
        else if (rnd() % 40 == 0) { s1x += 1 + rnd() % 3; }   /* sub-cell moves (the low three bits) keep the tile position, a carry moves it */
        cur_sx = (int)s1x; cur_sy = (int)s1y;
        w16(RAMB + 0xee1a, s1x); w16(RAMB + 0xee1c, s1y);
        if (rnd() % 30 == 0) mode = (rnd() % 4) ? 2 : 0;
        if (rnd() % 20 == 0) hud = (rnd() % 5) ? 1 : 0;   /* hud 0 with mode 2 = the character select can be up (sel_ok) */
        RAMB[0x8001] = (unsigned char)mode; RAMB[0x8380] = (unsigned char)hud;
        (void)0;   /* menu modes are not host-safe (draw_home reads the target uncached alias): sat_home_mode stays 0 */
    }
    /* palette: change a little most frames, a lot sometimes */
    for (i = 0; i < ((rnd() % 6) == 0 ? 0x200 : 4); i++) w16(GFX0 + 0xc000 + (rnd() % 0x800) * 2 % 0x1000 * 1, (unsigned)(rnd() * 3));
    memset(OBJ, 0, sizeof OBJ);
    for (i = 0; i < n; i++)
    {
        unsigned char *o = OBJ + 0x8000 + i * 8;
        int w = 1 + (int)(rnd() % 4), hh = 1 + (int)(rnd() % 4);
        w16(o, (unsigned)(rnd() % 380) | (unsigned)((rnd() % 7) << 13)); w16(o + 2, (unsigned)(rnd() % 240));
        w16(o + 4, (unsigned)((f / 3 * 7 + rnd() % 300) % (NSP - 200))); w16(o + 6, (unsigned)((hh - 1) << 12 | (w - 1) << 8 | (rnd() % 20) | ((rnd() % 4) << 5) | ((rnd() % 3 == 0) ? 0x80 : 0)));
    }
    w16(OBJ + 0x8000 + n * 8 + 2, 0x8000);
}

#ifdef THR
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
static int go, done, quit;
static void *slave(void *arg)
{
    (void)arg;
    for (;;)
    {
        pthread_mutex_lock(&mu);
        while (!go && !quit) pthread_cond_wait(&cv, &mu);
        if (quit) { pthread_mutex_unlock(&mu); return 0; }
        go = 0; pthread_mutex_unlock(&mu);
        sat_gfx_draw();
        pthread_mutex_lock(&mu); done = 1; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&mu);
    }
}
#endif

int main(int argc, char **argv)
{
    int i, f, frames = 600;
    unsigned char *pack;
#ifdef THR
    pthread_t th; struct timespec ts;
    int delayus = argc > 1 ? atoi(argv[1]) : 300;
#endif
    (void)argc; (void)argv;
    if (getenv("SEED")) rs = (unsigned long)atol(getenv("SEED"));
    if (getenv("FRAMES")) frames = atoi(getenv("FRAMES"));
    for (i = 0; i < 256; i++) PAGE[i] = ZERO;
    PAGE[0x70] = OBJ; PAGE[0x90] = GFX0; PAGE[0x91] = GFX1; PAGE[0x92] = GFX2;
    w16(RAMB + 0x8024, 0x9000); w16(RAMB + 0x8026, 0x9040); w16(RAMB + 0x8028, 0x9080);
    w16(RAMB + 0x802a, 0x90e0); w16(RAMB + 0x802c, 0x90c0); w16(RAMB + 0x804c, 0x3f);
    pack = make_pack();
#ifdef SAT_S1_DIRTY
    sat_s1d_verify = getenv("NOVERIFY") ? 0 : 1;
#endif
    if (!sat_gfx_init(pack)) return 2;
#ifdef THR
    pthread_create(&th, 0, slave, 0);
#endif
    for (f = 0; f < frames; f++)
    {
        frame_state(f);
#ifdef THR
        sat_gfx_snapshot_begin();
        pthread_mutex_lock(&mu); go = 1; done = 0; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&mu);
        ts.tv_sec = 0; ts.tv_nsec = (long)(rand() % (delayus + 1)) * 1000L; if (ts.tv_nsec) nanosleep(&ts, 0);
        /* scribble over nothing: the layer half writes only its own words */
        sat_gfx_snapshot_layers();
        pthread_mutex_lock(&mu); while (!done) pthread_cond_wait(&cv, &mu); pthread_mutex_unlock(&mu);
#else
        sat_gfx_frame();
#endif
        if (getenv("DUMPF") && f == atoi(getenv("DUMPF"))) { FILE *fp = fopen(getenv("DUMPTO"), "wb"); fwrite(V2, 1, 0x80000, fp); fclose(fp); }
        {
            unsigned long ha = 2166136261UL;
            h = 2166136261UL;
            mix(V1, 0x80000); mix(V2, 0x4000); mix(V2 + 0x8000, 0x10000); mix(V2 + 0x1e000, 0x80000 - 0x1e000); mix(CR, 0x1000);
            mix((const unsigned char *)sat_gfx_host_vdp1r, sizeof sat_gfx_host_vdp1r);
            mix((const unsigned char *)sat_gfx_host_vdp2r, sizeof sat_gfx_host_vdp2r);
            if (cur_layers & 2)
            {   /* the picture of scroll 1: names followed to bank, flips and the 32 bytes of the cell */
                int row, col, r0 = visible_row0(), c0 = visible_col0(); unsigned long hs = h; unsigned long nlay = 0;
                h = ha;
                for (row = 0; row < 29; row++) for (col = 0; col < 45; col++)
                {
                    unsigned off = 0x4000 + (unsigned)((((r0 + row) & 63) * 64 + ((c0 + col) & 63)) * 4);
                    unsigned long name = ((unsigned long)V2[off] << 24) | ((unsigned long)V2[off + 1] << 16) | ((unsigned long)V2[off + 2] << 8) | V2[off + 3];
                    unsigned ch = (unsigned)(name & 0xffff);
                    unsigned char tag[4];
                    tag[0] = (unsigned char)(name >> 24); tag[1] = (unsigned char)(name >> 16); tag[2] = (unsigned char)(row * 45 + col); tag[3] = (unsigned char)((row * 45 + col) >> 8);
                    mix(tag, 4); mix(V2 + (unsigned long)ch * 32, 32); nlay++;
                    if (getenv("DUMPRES") && f == atoi(getenv("DUMPRES")))
                    {   unsigned long cs = 2166136261UL; int z; for (z = 0; z < 32; z++) cs = (cs ^ V2[(unsigned long)ch * 32 + z]) * 16777619UL;
                        fprintf(stderr, "R %d %d name %lx ch %x cell %lx\n", row, col, name & 0xffff0000UL, ch, cs & 0xffffffUL); }
                }
                ha = h; h = hs;
            }
            else ha = 0;
            printf("%d %u %lx %lx %lu %lu\n", f, sat_gfx_stats.commands, ha, h, sat_gfx_stats.refused_layer - refused_before, sat_gfx_s1_draws - draws_before);
            refused_before = sat_gfx_stats.refused_layer; draws_before = sat_gfx_s1_draws;
            tot_lu += sat_gfx_stats.layer_uploads; tot_up += sat_gfx_stats.uploads;
            if (sat_gfx_stats.layer_uploads > max_lu) max_lu = sat_gfx_stats.layer_uploads;
        }
    }
#ifdef SAT_S1_DIRTY
    fprintf(stderr, "s1d: incremental draws %lu, full draws %lu, rows redrawn %lu, rows kept %lu, verify rows %lu, verify DIFFERENT rows %lu, empty masks %lu, draws with a refusal %lu\n",
            (unsigned long)sat_s1d[0], (unsigned long)sat_s1d[1], (unsigned long)sat_s1d[2], (unsigned long)sat_s1d[3], (unsigned long)sat_s1d[4], (unsigned long)sat_s1d[5], (unsigned long)sat_s1d[6], (unsigned long)sat_s1d[7]);
    if (sat_s1d[5]) return 3;
#endif
    fprintf(stderr, "layer uploads %lu (max in a frame %lu), sprite uploads %lu\n", tot_lu, max_lu, tot_up);
#ifdef THR
    pthread_mutex_lock(&mu); quit = 1; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&mu); pthread_join(th, 0);
    fprintf(stderr, "layers_late %lu layers_timeout %lu\n", sat_gfx_layers_late, sat_gfx_layers_timeout);
#endif
    return 0;
}
