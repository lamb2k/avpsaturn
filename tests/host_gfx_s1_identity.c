/* HOST identity of the scroll 1 switches (lane perf-reconcile, 2026-11-10): SAT_S1_MEMO, SAT_S1_BLANKROWS, SAT_HOME_FONT_COLD against the plain build, home build (FIT 1).
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

#ifdef S1HEAVY
#define NS1 4000   /* more distinct scroll 1 tiles than the cache has slots: refusals, evictions (SAT_S1_DIRTY test) */
#else
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

static unsigned long h;
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

static void edit_s1(int f)
{
    int i, r, c;
    unsigned blank = 0xfff0;   /* a code the pack does not hold: no tile */
    if (f == 0) for (i = 0; i < 0x1000; i++) set_layer_word(GFX0, i * 4, blank, 0);
#ifdef PLAYLIKE
    /* a play HUD: every picture a few words change in the top five and bottom rows, now and then a row of the whole width, a menu line, rarely a full clear; S1HEAVY adds bursts of random cells over the whole window */
    {
        int n = 1 + (int)(rnd() % 3), row;
        for (i = 0; i < n; i++)
        {
            row = (rnd() % 2) ? (int)(rnd() % 5) : 24 + (int)(rnd() % 5);
            c = (int)(rnd() % 60);
            set_layer_word(GFX0, (((row + 2) & 31) + ((c & 63) << 5)) * 4, (rnd() % 3) ? rnd() % (NS1 / 2) : blank, (rnd() % 3) ? (rnd() & 0x7f) : 0);
        }
        if (rnd() % 29 == 0) { unsigned code = rnd() % (NS1 / 2); row = (int)(rnd() % 32); for (c = 0; c < 64; c++) set_layer_word(GFX0, ((row & 31) + (c << 5)) * 4, code, 0); }
        if (rnd() % 97 == 0) { row = (int)(rnd() % 32); for (c = 0; c < 64; c++) set_layer_word(GFX0, ((row & 31) + (c << 5)) * 4, blank, 0); }
        if (rnd() % 400 == 0) for (i = 0; i < 0x1000; i++) set_layer_word(GFX0, i * 4, blank, 0);
#ifdef S1HEAVY
        if (rnd() % 5 == 0) for (i = 0; i < 40; i++) set_layer_word(GFX0, (((rnd() % 32) & 31) + ((rnd() % 64) << 5)) * 4, rnd() % (NS1 / 2), rnd() & 0x7f);
#endif
        return;
    }
#endif
    if (rnd() % 3 == 0)   /* HUD rows come and go: a few cells with real tiles, sometimes a whole row of one tile */
    {
        r = (int)(rnd() % 29); c = (int)(rnd() % 60);
        for (i = 0; i < (int)(1 + rnd() % 8); i++)
        {
            unsigned code = (rnd() % 4) ? blank : rnd() % (NS1 / 2);
            set_layer_word(GFX0, (((r + (int)(rnd() % 2)) & 31) + (((c + i) & 63) << 5)) * 4, code, rnd() & 0x7f);
        }
    }
    if (rnd() % 17 == 0) { unsigned code = (rnd() % 2) ? blank : rnd() % (NS1 / 2); r = (int)(rnd() % 32); for (c = 0; c < 64; c++) set_layer_word(GFX0, ((r & 31) + (c << 5)) * 4, code, 0); }
    if (rnd() % 11 == 0) for (i = 0; i < 0x1000; i++) set_layer_word(GFX0, i * 4, blank, 0);
}

static void frame_state(int f)
{
    int i, n = 20 + (int)(rnd() % 120), still = (rnd() % 4) == 0, mask = (int)(rnd() % 8) << 1;   /* layers bits 2 4 8 */
    unsigned s;
    if (f < 3) mask = 14;
#ifdef PLAYLIKE
    mask = 14; still = 0;
#endif
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
#ifdef PLAYLIKE
        if (rnd() % 300 == 0) { s1x = rnd() % 600; s1y = rnd() % 300; }
#elif defined(STICKY)
        if (rnd() % 40 == 0) { s1x = rnd() % 600; s1y = rnd() % 300; }
#else
        if (rnd() % 6 == 0) { s1x = rnd() % 600; s1y = rnd() % 300; }
#endif
        w16(RAMB + 0xee1a, s1x); w16(RAMB + 0xee1c, s1y);
#ifdef PLAYLIKE
        if (f == 0 || rnd() % 150 == 0) { RAMB[0x8001] = 2; RAMB[0x8380] = (rnd() % 8) ? 1 : 0; }
#elif defined(STICKY)
        if (f == 0 || rnd() % 25 == 0) { RAMB[0x8001] = (rnd() % 4) ? 2 : 0; RAMB[0x8380] = (rnd() % 5) ? 1 : 0; }   /* play flags and menu state hold for a while, as in play */
#else
        RAMB[0x8001] = (rnd() % 4) ? 2 : 0; RAMB[0x8380] = (rnd() % 5) ? 1 : 0;
#endif
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
    int i, f, frames = getenv("FRAMES") ? atoi(getenv("FRAMES")) : 600;
    unsigned char *pack;
#ifdef THR
    pthread_t th; struct timespec ts;
    int delayus = argc > 1 ? atoi(argv[1]) : 300;
#endif
    (void)argc; (void)argv;
    for (i = 0; i < 256; i++) PAGE[i] = ZERO;
    PAGE[0x70] = OBJ; PAGE[0x90] = GFX0; PAGE[0x91] = GFX1; PAGE[0x92] = GFX2;
    w16(RAMB + 0x8024, 0x9000); w16(RAMB + 0x8026, 0x9040); w16(RAMB + 0x8028, 0x9080);
    w16(RAMB + 0x802a, 0x90e0); w16(RAMB + 0x802c, 0x90c0); w16(RAMB + 0x804c, 0x3f);
    pack = make_pack();
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
        h = 2166136261UL;
#ifdef RESOLVED_S1
        /* SAT_S1_DIRTY: VDP2 VRAM is the same picture but not the same bytes (slot choice differs). Hash scroll 1 as the chip resolves it: every name of the visible 29 x 45 window,
           followed to its cell with its flip and bank bits; the rest of VDP2 VRAM (outside the scroll 1 map and the scroll 1 cell slab) raw. layer_uploads is not compared. */
        {
            unsigned long mapa = SAT_V2_MAP_S1, cella = SAT_V2_CELL_S1, slab = (unsigned long)SAT_GFX_S1_SLOTS * 32; int row, col;
            extern unsigned long sat_gfx_host_s1x0, sat_gfx_host_s1y0;
            mix(V1, 0x80000); mix(V2, mapa); mix(V2 + mapa + 0x4000, cella - mapa - 0x4000); mix(V2 + cella + slab, 0x80000 - cella - slab);
            for (row = 0; row < 29; row++) for (col = 0; col < 45; col++)
            {
                unsigned long nm; unsigned r = (unsigned)(sat_gfx_host_s1y0 + (unsigned long)row) & 63, c = (unsigned)(sat_gfx_host_s1x0 + (unsigned long)col) & 63;
                const unsigned char *q = V2 + mapa + (r * 64 + c) * 4;
                nm = ((unsigned long)q[0] << 24) | ((unsigned long)q[1] << 16) | ((unsigned long)q[2] << 8) | q[3];
                mix(q, 2);   /* flips and bank */
                mix(V2 + ((nm & 0xffff) << 5), 32);
            }
            mix(CR, 0x1000);
            mix((const unsigned char *)sat_gfx_host_vdp1r, sizeof sat_gfx_host_vdp1r);
            mix((const unsigned char *)sat_gfx_host_vdp2r, sizeof sat_gfx_host_vdp2r);
            printf("%d %u %u %lx\n", f, sat_gfx_stats.commands, sat_gfx_stats.uploads, h);
#ifdef PRINT_REF
            fprintf(stderr, "R %d %lu\n", f, (unsigned long)sat_gfx_stats.refused_layer);
#endif
        }
#else
        mix(V1, 0x80000); mix(V2, 0x80000); mix(CR, 0x1000);
        mix((const unsigned char *)sat_gfx_host_vdp1r, sizeof sat_gfx_host_vdp1r);
        mix((const unsigned char *)sat_gfx_host_vdp2r, sizeof sat_gfx_host_vdp2r);
        printf("%d %u %u %u %lx\n", f, sat_gfx_stats.commands, sat_gfx_stats.uploads, sat_gfx_stats.layer_uploads, h);
#endif
    }
#if defined(SAT_S1_DIRTY) && defined(RESOLVED_S1)
    { extern unsigned long sat_gfx_host_s1d[4]; fprintf(stderr, "s1 dirty: partial draws %lu, full draws %lu, rows redrawn %lu of dirty rows %lu\n", sat_gfx_host_s1d[0], sat_gfx_host_s1d[1], sat_gfx_host_s1d[2], sat_gfx_host_s1d[3]); }
#endif
#ifdef THR
    pthread_mutex_lock(&mu); quit = 1; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&mu); pthread_join(th, 0);
    fprintf(stderr, "layers_late %lu layers_timeout %lu\n", sat_gfx_layers_late, sat_gfx_layers_timeout);
#endif
    return 0;
}
