/* Host identity harness with the scroll layers ON (the older ident.c has them off). Synthetic data, no ROM.
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
unsigned char RAMB[0x10000];
static unsigned char OBJ[0x10000], GFX0[0x10000], GFX1[0x10000], GFX2[0x10000], ZERO[0x10000];
static unsigned char V1[0x80000], V2[0x80000], CR[0x1000];
unsigned char *sat_gfx_host_vdp1 = V1, *sat_gfx_host_vdp2 = V2, *sat_gfx_host_cram = CR;
unsigned short sat_gfx_host_vdp1r[0x10], sat_gfx_host_vdp2r[0x90];
unsigned long sat_gfx_host_ticks(void) { static unsigned long t; return (t += 3) & 0xffff; }

static void w16(unsigned char *p, unsigned v) { p[0] = (unsigned char)(v >> 8); p[1] = (unsigned char)v; }
static void w32(unsigned char *p, unsigned long v) { w16(p, (unsigned)(v >> 16)); w16(p + 2, (unsigned)(v & 0xffff)); }

#define NS1 700
#define NS2 300
#define NS3 300
#define NSP 4000
static unsigned long rs = 777;
static unsigned rnd(void) { rs = rs * 1103515245UL + 12345UL; return (unsigned)(rs >> 16) & 0x7fff; }

/* Pack: 4 sections of keys 0..n-1, payload i = bytes from a generator so every tile differs; some rows of a sprite tile are all zero (transparent).
 * -DRT builds the sprite section as SGP2 row masked records (the layout of tools/rounds_pack.py assemble_rowtrim), the last third of them in a spill area
 * after the pack, so rowtrim_load's main and spill paths both run. Without -DRT the SGP1 pack. Same pixels either way: every frame's VRAM hash must match. */
static unsigned char sprite_byte(unsigned long k, unsigned long j)
{
    unsigned long row = j / 8;
    if ((k * 7 + row * 3) % 5 == 0) return 0;   /* a transparent row */
    return (unsigned char)((k * 31 + j * 7) & 0xff) | (j == 0 ? 0x11 : 0) | 0x01;
}

static unsigned char *make_pack(void)
{
    unsigned long counts[4] = { NSP, NS1, NS2, NS3 }, slot[4] = { 128, 32, 128, 512 }, shift[4] = { 16, 14, 14, 14 };
    unsigned long hdr = 84, off = hdr, keyoff[4], dataoff[4], i, k;
    unsigned char *p;
#ifdef RT
    unsigned long j, pos = 0, bases_at, offs_at, stream_at, spill_at, total, firstspill = NSP * 2 / 3, spillpos = 0;
    static unsigned long recpos[NSP + 1];
    hdr = 92; off = hdr;
#endif
    for (i = 0; i < 4; i++) { keyoff[i] = off; off += counts[i] * 4; }
#ifdef RT
    off += 16;   /* spill table: count and one (first, offset) pair */
    for (k = 0; k < NSP; k++)
    {
        unsigned long rows = 0;
        recpos[k] = pos;
        for (j = 0; j < 16; j++) if (sprite_byte(k, j * 8)) rows++;
        pos += 4 + 8 * rows;
        if (k == firstspill) spillpos = recpos[k];
    }
    recpos[NSP] = pos;
    bases_at = off; off += ((NSP + 1023) / 1024) * 4;
    offs_at = off; off += NSP * 2; off = (off + 3) & ~3UL;
    dataoff[0] = off; off += 0;
    for (i = 1; i < 4; i++) { dataoff[i] = off; off += counts[i] * slot[i]; }
    stream_at = off; off += spillpos;   /* the first 2/3 of the records live in main */
    dataoff[0] = stream_at;
    spill_at = off; off += pos - spillpos;
    total = off;
    p = (unsigned char *)calloc(total, 1);
    w32(p, 0x53475032UL);
    w32(p + 84, bases_at); w32(p + 88, offs_at);
#else
    for (i = 0; i < 4; i++) { dataoff[i] = off; off += counts[i] * slot[i]; }
    p = (unsigned char *)calloc(off, 1);
    w32(p, 0x53475031UL);
#endif
    for (i = 0; i < 4; i++)
    {
        w32(p + 4 + i * 12, counts[i]); w32(p + 8 + i * 12, keyoff[i]); w32(p + 12 + i * 12, dataoff[i]);
#ifdef RT
        if (i == 0) { w32(p + 52, firstspill); w32(p + 56, keyoff[3] + counts[3] * 4); }
        else
#endif
        { w32(p + 52 + i * 8, counts[i]); w32(p + 56 + i * 8, hdr); }   /* split past the end: no spill */
        for (k = 0; k < counts[i]; k++)
        {
            unsigned long j2;
            w32(p + keyoff[i] + k * 4, (k << shift[i]) | k);
#ifdef RT
            if (i == 0) continue;
#endif
            for (j2 = 0; j2 < slot[i]; j2++)
            {
                if (i == 0) p[dataoff[i] + k * slot[i] + j2] = sprite_byte(k, j2);
                else p[dataoff[i] + k * slot[i] + j2] = (unsigned char)((k * 31 + j2 * 7 + i) & 0xff) | (j2 == 0 ? 0x11 : 0);
            }
        }
    }
#ifdef RT
    {
        unsigned long tab = keyoff[3] + counts[3] * 4;
        w32(p + tab, 1); w32(p + tab + 4, firstspill); w32(p + tab + 8, spill_at - 0);   /* offset from the pack start (pack_start + offset) */
        for (k = 0; k < (NSP + 1023) / 1024; k++) w32(p + bases_at + k * 4, recpos[k << 10]);
        for (k = 0; k < NSP; k++)
        {
            unsigned long d = recpos[k] - recpos[(k >> 10) << 10];
            w16(p + offs_at + k * 2, (unsigned)(d >> 2));
        }
        for (k = 0; k < NSP; k++)
        {
            unsigned char *dst = k < firstspill ? p + stream_at + recpos[k] : p + spill_at + (recpos[k] - spillpos);
            unsigned mask = 0, r = 0;
            for (j = 0; j < 16; j++) if (sprite_byte(k, j * 8)) mask |= 0x8000u >> j;
            w16(dst, mask);
            for (j = 0; j < 16; j++) if (mask & (0x8000u >> j)) { unsigned long b; for (b = 0; b < 8; b++) dst[4 + r * 8 + b] = sprite_byte(k, j * 8 + b); r++; }
        }
    }
#endif
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
        set_layer_word(GFX0, off, rnd() % (NS1 / 2), rnd() & 0x7f);
        set_layer_word(GFX0, 0x4000 + (rnd() * 3 % 0x1000) * 4 % 0x4000, rnd() % NS2, rnd() & 0x7f);
        set_layer_word(GFX0, 0x8000 + (rnd() * 3 % 0x1000) * 4 % 0x4000, rnd() % NS3, rnd() & 0x7f);
    }
}

static void frame_state(int f)
{
    int i, n = 20 + (int)(rnd() % 120), still = (rnd() % 4) == 0, mask = (int)(rnd() % 8) << 1;   /* layers bits 2 4 8 */
    unsigned s;
    if (f < 3) mask = 14;
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
        h = 2166136261UL;
        mix(V1, 0x80000); mix(V2, 0x80000); mix(CR, 0x1000);
        mix((const unsigned char *)sat_gfx_host_vdp1r, sizeof sat_gfx_host_vdp1r);
        mix((const unsigned char *)sat_gfx_host_vdp2r, sizeof sat_gfx_host_vdp2r);
        printf("%d %u %u %u %lx\n", f, sat_gfx_stats.commands, sat_gfx_stats.uploads, sat_gfx_stats.layer_uploads, h);
    }
#ifdef THR
    pthread_mutex_lock(&mu); quit = 1; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&mu); pthread_join(th, 0);
    fprintf(stderr, "layers_late %lu layers_timeout %lu\n", sat_gfx_layers_late, sat_gfx_layers_timeout);
#endif
    return 0;
}
