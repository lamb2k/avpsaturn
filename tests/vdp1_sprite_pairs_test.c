/* HOST, synthetic pack only. Compile the actual driver selected by
 * SAT_GFX_SOURCE. The Python runner compares framebuffer pixels with the
 * unbatched driver and exercises pair ownership under delayed presentation.
 * This integer raster oracle is not a Saturn timing or hardware proof. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define SAT_GFX_HOST
#define SAT_GFX_SYNC_TEST
#include "sat_gfx.h"
#if SAT_GFX_FIT == 3
#undef SAT_FIT_ON
#define SAT_FIT_ON (sat_fit_scale)
#endif
#ifndef SAT_GFX_SOURCE
#define SAT_GFX_SOURCE "../saturn/gfx/sat_gfx.c"
#endif
#include SAT_GFX_SOURCE

unsigned char *PAGE[256];
unsigned char RAMB[65536];
static unsigned char obj_ram[65536], gfx_ram[65536], zero_ram[65536];
static unsigned char v1[524288], v2[524288], cram[4096];
unsigned char *sat_gfx_host_vdp1 = v1, *sat_gfx_host_vdp2 = v2, *sat_gfx_host_cram = cram;
unsigned short sat_gfx_host_vdp1r[16], sat_gfx_host_vdp2r[144];
volatile unsigned long sat_vlog[16 * 4];
static unsigned short pixels[SAT_GFX_SCREEN_W * SAT_GFX_SCREEN_H];
static unsigned long ticks, tick_step = 1, vblanks;
static int clear_cef;
static unsigned int random_state = 92177U;
static unsigned long total_commands, total_uploads;

unsigned long sat_vblanks_now(void) { return vblanks; }
unsigned long sat_gfx_host_ticks(void)
{
    ticks = (ticks + tick_step) & 65535UL;
    if (clear_cef) sat_gfx_host_vdp1r[8] &= (unsigned short)~2U;
    return ticks;
}
int sat_gfx_profile_busy(void) { return 0; }

static unsigned int random_value(void)
{
    random_state = random_state * 1664525U + 1013904223U;
    return random_state;
}

#define TILE_COUNT 1024
static unsigned char *make_synthetic_pack(int blank)
{
    unsigned long data = 84 + TILE_COUNT * 4, i, j;
    unsigned char *p = (unsigned char *)calloc(data + TILE_COUNT * 128, 1);
    assert(p);
    put32(p, 0x53475031UL);
    put32(p + 4, TILE_COUNT); put32(p + 8, 84); put32(p + 12, data);
    for (i = 0; i < 4; i++)
    {
        put32(p + 52 + i * 8, TILE_COUNT);
        if (i) { put32(p + 8 + i * 12, 84); put32(p + 12 + i * 12, data); }
    }
    for (i = 0; i < TILE_COUNT; i++)
    {
        put32(p + 84 + i * 4, (i << 16) | ((blank && (i == 7 || i == 33)) ? 65535UL : i));
        for (j = 0; j < 128; j++)
        {
            /* Irregular corners, transparent holes, row/column-specific pens:
             * a wrong row order, flip or payload cannot hide in solid art. */
            unsigned int a = (unsigned int)((i * 7 + j * 3 + (j >> 3) + (i >> 4) * ((j & 7) + 1)) & 15);
            unsigned int b = (unsigned int)((i * 11 + j * 5 + (j >> 1) + (i >> 8) * ((j >> 3) + 1)) & 15);
            p[data + i * 128 + j] = (unsigned char)((a << 4) | b);
        }
    }
    return p;
}

static void reset_driver(unsigned char *pack)
{
    unsigned int i;
    memset(RAMB, 0, sizeof RAMB); memset(obj_ram, 0, sizeof obj_ram);
    for (i = 0; i < 256; i++) PAGE[i] = zero_ram;
    PAGE[0x70] = obj_ram; PAGE[0x90] = gfx_ram;
    put16(RAMB + 0x8024, 0x9000); put16(RAMB + 0x8026, 0x9040);
    put16(RAMB + 0x8028, 0x9080); put16(RAMB + 0x802a, 0x90e0);
    put16(RAMB + 0x802c, 0x90c0); put16(RAMB + 0x804a, 0x12c0);
    put16(RAMB + 0x804c, 0x3f); put16(RAMB + 0x8050, 0x2377);
    assert(sat_gfx_init(pack));
    memset(&sat_gfx_stats, 0, sizeof sat_gfx_stats);
    plot_started = plot_shown = plot_held = plot_sync = 0;
    ticks = 0; tick_step = 1; vblanks = 0; clear_cef = 1;
    sat_gfx_host_vdp1r[8] = 0;
}

static void object(unsigned int n, int x, int y, unsigned int key,
                   unsigned int width, unsigned int height, unsigned int flips,
                   unsigned int palette, unsigned int origin)
{
    unsigned char *p = obj_ram + 0x8000 + n * 8;
    put16(p, (u16)((x & 1023) | ((palette & 7) << 13)));
    put16(p + 2, (u16)(y & 1023)); put16(p + 4, (u16)key);
    put16(p + 6, (u16)(((height - 1) << 12) | ((width - 1) << 8) |
                      ((flips & 3) << 5) | (palette & 31) | (origin ? 0x80 : 0)));
}

static void end_objects(unsigned int n)
{
    put16(obj_ram + 0x8000 + n * 8 + 2, 0x8000);
}

static int signed_word(const unsigned char *p)
{
    unsigned int value = be16(p);
    return value >= 32768 ? (int)value - 65536 : (int)value;
}

static unsigned int pixel_hash(unsigned long base)
{
    unsigned long at = base + 0x60, i;
    unsigned int hash = 2166136261U;
    memset(pixels, 0, sizeof pixels);
    for (;; at += 32)
    {
        const unsigned char *cmd = v1 + at;
        unsigned int ctrl = be16(cmd), colr = be16(cmd + 6), size = be16(cmd + 10);
        unsigned int sw = ((size >> 8) & 63) * 8, sh = size & 255;
        unsigned long tex = (unsigned long)be16(cmd + 8) * 8;
        int x = signed_word(cmd + 12), y = signed_word(cmd + 14), dw, dh, xx, yy;
        if (ctrl & 0x8000) break;
        assert(at + 32 <= base + 0x8000);
        assert((ctrl & 15) <= 1 && (sw == 16 || sw == 8));
        dw = (ctrl & 1) ? signed_word(cmd + 20) - x + 1 : (int)sw;
        dh = (ctrl & 1) ? signed_word(cmd + 22) - y + 1 : (int)sh;
        assert(dw > 0 && dh > 0 && dh == (int)sh);
        assert(tex + sw * sh / 2 <= sizeof v1);
        for (yy = 0; yy < dh; yy++) for (xx = 0; xx < dw; xx++)
        {
            unsigned int sx = (unsigned int)xx * sw / (unsigned int)dw;
            unsigned int sy = (unsigned int)yy;
            unsigned int pen;
            int dx = x + xx, dy = y + yy;
            if (ctrl & 0x10) sx = sw - 1 - sx;
            if (ctrl & 0x20) sy = sh - 1 - sy;
            pen = v1[tex + sy * sw / 2 + sx / 2];
            pen = (sx & 1) ? pen & 15 : pen >> 4;
            if (pen && dx >= 0 && dx < SAT_GFX_SCREEN_W && dy >= 0 && dy < SAT_GFX_SCREEN_H)
                pixels[dy * SAT_GFX_SCREEN_W + dx] = (unsigned short)(colr | pen);
        }
    }
    for (i = 0; i < sizeof pixels / sizeof pixels[0]; i++) hash = (hash ^ pixels[i]) * 16777619U;
    return hash;
}

static void emit_frame(unsigned int serial)
{
    unsigned long base = table_base;
    sat_gfx_host_vdp1r[8] = 2; sat_gfx_vblank(); vblanks++;
    clear_cef = 1; tick_step = 1;
    sat_gfx_frame();
    assert(!sat_gfx_stats.refused_commands && !sat_gfx_stats.refused_sprite);
    printf("%u %08x\n", serial, pixel_hash(base));
    total_commands += sat_gfx_stats.commands; total_uploads += sat_gfx_stats.uploads;
}

static void compare_pixels(unsigned char *pack)
{
    unsigned int serial = 0, flip, phase, nx, ny, n, j;
    static const int edges[] = { -31, -16, -15, -1, 0, 1, 15, 16, 192, 207, 208, 223, 224, 255, 1008, 1023 };
    reset_driver(pack);
    /* Every scaling phase, both mirrors, odd/even source starts and arbitrary
     * object widths/heights. One cache-hot repeat after every frame. */
    for (flip = 0; flip < 4; flip++) for (phase = 0; phase < 12; phase++)
        for (nx = 1; nx <= 16; nx *= 2) for (ny = 1; ny <= 16; ny++)
        {
            object(0, (int)phase + 100, 48, 64 + (ny & 15), nx, ny, flip, 3, 0);
            end_objects(1); emit_frame(serial++); emit_frame(serial++);
        }
    /* Screen edges and ten-bit wrap, including partial X and Y clipping,
     * origin offsets and overlapping objects with different palettes. */
    for (flip = 0; flip < 4; flip++) for (n = 0; n < sizeof edges / sizeof edges[0]; n++)
    {
        object(0, edges[n] + 64 + SAT_GFX_CROP_X, 60, 7, 4, 7, flip, 2, 0);
        object(1, 100, edges[n] + 16, 33, 7, 4, flip, 5, 0);
        object(2, 105, edges[n], 96, 3, 8, flip ^ 3, 12, 1);
        object(3, 130, 80, 64000, 2, 3, flip, 9, 0);
        end_objects(4); emit_frame(serial++);
    }
    for (n = 0; n < 300; n++)
    {
        for (j = 0; j < 20; j++)
        {
            unsigned int r = random_value(), r2 = random_value();
            object(j, (int)(r & 511), (int)((r >> 10) & 1023), (r2 >> 12) % 700,
                   1 + ((r >> 18) & 7), 1 + ((r >> 21) & 7), r >> 24, r2 >> 16, r >> 30);
        }
        end_objects(20); emit_frame(serial++);
    }
    fprintf(stderr, "frames=%u commands=%lu uploads=%lu\n", serial, total_commands, total_uploads);
#if (SAT_GFX_SPRITE_PAIRS || SAT_GFX_PAIR_REUSE) && defined(SAT_GFX_PAIR_STATS)
    fprintf(stderr, "pair_hits=%lu pair_uploads=%lu pair_fallbacks=%lu saved=%lu\n",
            sat_gfx_pair_hits, sat_gfx_pair_uploads, sat_gfx_pair_fallbacks, sat_gfx_pair_saved);
#endif
}

#if SAT_GFX_SPRITE_PAIRS
static void cache_ownership(unsigned char *pack)
{
    unsigned char saved[SAT_GFX_SPRITE_PAIRS * 256], before[256];
    unsigned char *full_pack, *spilled_pack;
    unsigned int key, collision;
    u16 slot, saved_stamp;
    unsigned long uploads;
    reset_driver(pack);
    assert(spr_cache.first == SAT_GFX_SPRITE_PAIRS * 2);
    stamp = 1; slot = sprite_pair(64); assert(slot != NOSLOT);
    assert(slot < spr_cache.first && spr_slots[slot].stamp == 1 && spr_slots[slot + 1].stamp == 1);
    uploads = sat_gfx_stats.uploads;
    assert(sprite_pair(64) == slot && sat_gfx_stats.uploads == uploads);
    memcpy(before, v1 + TEX_BASE + (unsigned long)slot * 128, sizeof before);
    collision = 0;
    for (key = 65; key < 700; key++)
        if ((((key ^ (key >> 5)) & (SAT_GFX_SPRITE_PAIRS - 1)) * 2) == slot) { collision = key; break; }
    assert(collision);
    assert(sprite_pair(collision) == NOSLOT); /* protected by current build */
    prev_stamp = stamp; stamp = 2;
    assert(sprite_pair(collision) == NOSLOT); /* protected by previous plot */
    assert(!memcmp(before, v1 + TEX_BASE + (unsigned long)slot * 128, sizeof before));
    assert(sprite_pair(64) == slot && spr_slots[slot].stamp == 2);
    plot_abandon_build();
    assert(spr_slots[slot].stamp == 1 && spr_slots[slot + 1].stamp == 1);
    stamp = 3;
    assert(sprite_pair(collision) == NOSLOT); /* abandoned hit did not release old pixels */
    prev_stamp = 0;
    assert(sprite_pair(collision) == slot);
    assert(memcmp(before, v1 + TEX_BASE + (unsigned long)slot * 128, sizeof before));

    /* Stamp wrap uses the same guard and cannot release the preceding plot. */
    reset_driver(pack); stamp = 65535; slot = sprite_pair(64); prev_stamp = stamp; stamp = 1;
    assert(sprite_pair(collision) == NOSLOT);
    assert(sprite_pair(64) == slot); plot_abandon_build();
    assert(spr_slots[slot].stamp == 65535 && spr_slots[slot + 1].stamp == 65535);

    /* A cached failed pair must be reconsidered on a round-pack change. */
    reset_driver(pack); stamp = 1; assert(sprite_pair(7) == NOSLOT);
    full_pack = make_synthetic_pack(0); assert(sat_gfx_swap_pack(full_pack));
    assert(sprite_pair(7) != NOSLOT); free(full_pack);
    reset_driver(pack); assert(spr_slots[slot].key == NOKEY && spr_slots[slot].stamp == 0);

    /* One member in main storage, the other in a spill segment. Poison the
     * unused inline copy so ignoring the segment table cannot pass. */
    {
        unsigned long data = 84 + TILE_COUNT * 4;
        unsigned long old_size = data + TILE_COUNT * 128, spilled_bytes = (TILE_COUNT - 64) * 128;
        spilled_pack = (unsigned char *)malloc(old_size + 12 + spilled_bytes);
        assert(spilled_pack);
        memcpy(spilled_pack, pack, old_size);
        put32(spilled_pack + 52, 64); put32(spilled_pack + 56, old_size);
        put32(spilled_pack + old_size, 1); put32(spilled_pack + old_size + 4, 64);
        put32(spilled_pack + old_size + 8, old_size + 12);
        memcpy(spilled_pack + old_size + 12, pack + data + 64 * 128, spilled_bytes);
        memset(spilled_pack + data + 64 * 128, 0, spilled_bytes);
        reset_driver(spilled_pack); stamp = 1; slot = sprite_pair(48); assert(slot != NOSLOT);
        assert(!memcmp(v1 + TEX_BASE + (unsigned long)slot * 128, pack + data + 48 * 128, 128));
        assert(!memcmp(v1 + TEX_BASE + (unsigned long)(slot + 1) * 128, pack + data + 64 * 128, 128));
    }
    reset_driver(pack); free(spilled_pack);

    /* A submitted pair remains byte-identical when CEF never arrives. The
     * full draw must return before stamps or texture writes, not only before
     * submitting a second command list. */
    object(0, 120, 64, 64, 1, 2, 0, 3, 0); end_objects(1);
    sat_gfx_vblank();
    sat_gfx_frame(); assert(sat_gfx_stats.commands == 1);
    saved_stamp = prev_stamp;
    memcpy(saved, v1 + TEX_BASE, sizeof saved);
    object(0, 120, 64, collision, 1, 2, 0, 3, 0); end_objects(1);
    sat_gfx_host_vdp1r[8] = 0; clear_cef = 0; tick_step = 1000;
    sat_gfx_snapshot(); sat_gfx_draw();
    assert(prev_stamp == saved_stamp && stamp == saved_stamp);
    assert(!memcmp(saved, v1 + TEX_BASE, sizeof saved));
    puts("pair cache ownership ok");
}

static void admission_and_command_limits(unsigned char *pack)
{
    unsigned int n;
    unsigned long end;
    reset_driver(pack);
    /* A cold wide block asks for sixteen distinct pairs. Pair construction
     * cannot consume more uploads than its explicit per-build budget. */
    object(0, 80, 48, 64, 16, 2, 0, 3, 0); end_objects(1);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(spr_slots[1].next == SAT_GFX_PAIR_UPLOAD_BUDGET);
    assert(sat_gfx_stats.commands == 32 - SAT_GFX_PAIR_UPLOAD_BUDGET);
    assert(sat_gfx_stats.uploads == 32);
    sat_gfx_host_vdp1r[8] = 2; sat_gfx_vblank(); sat_gfx_frame();
    assert(spr_slots[1].next <= SAT_GFX_PAIR_UPLOAD_BUDGET);
    assert(sat_gfx_stats.uploads <= SAT_GFX_PAIR_UPLOAD_BUDGET * 2);

    /* The two-command-table boundary remains hard even when there are more
     * commands than fit. A pair is one command refusal, not two lost tiles;
     * the below-capacity pixel oracle deliberately tests identity separately. */
    reset_driver(pack);
    for (n = 0; n < 1024; n++) object(n, 120, 64, 64, 2, 2, n & 3, n & 31, 0);
    end_objects(1024);
    memset(v1 + 0x8000, 0x5a, 32);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == SAT_GFX_MAX_COMMANDS);
    assert(sat_gfx_stats.refused_commands);
    end = 0x60UL + SAT_GFX_MAX_COMMANDS * 32;
    assert(end <= 0x7fe0UL && be16(v1 + end) == 0x8000);
    for (n = 0; n < 32; n++) assert(v1[0x8000 + n] == 0x5a);
    memset(v1 + TEX_BASE, 0x5a, 32); /* these two pair keys use later slots */
    sat_gfx_host_vdp1r[8] = 2; sat_gfx_vblank(); sat_gfx_frame();
    end += TABLE_B;
    assert(end <= TEX_BASE - 32 && be16(v1 + end) == 0x8000);
    for (n = 0; n < 32; n++) assert(v1[TEX_BASE + n] == 0x5a);

    /* Missing and transparent pair members fall through to individual tiles;
     * missing is counted once for each original requested tile, as before. */
    reset_driver(pack);
    object(0, 120, 64, 64000, 1, 2, 0, 3, 0); end_objects(1);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == 0 && sat_gfx_stats.missing == 2);
    reset_driver(pack);
    object(0, 120, 64, 7, 1, 2, 0, 3, 0); end_objects(1);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == 1 && sat_gfx_stats.missing == 0);
    puts("pair admission and command limits ok");
}
#endif

#if SAT_GFX_PAIR_REUSE
static void reuse_fallbacks(unsigned char *pack)
{
    unsigned int fy, side, kind, i;
    u16 lo, hi;
    unsigned char saved[256];
    unsigned long live_stamp, table_end;
    for (fy = 0; fy < 2; fy++)
    {
        reset_driver(pack); assert(spr_cache.first == 0);
        stamp = 1;
        lo = cache_get(&spr_cache, 64, &sat_gfx_stats.refused_sprite);
        (void)cache_get(&spr_cache, 200, &sat_gfx_stats.refused_sprite);
        hi = cache_get(&spr_cache, 80, &sat_gfx_stats.refused_sprite);
        assert(hi != lo + 1);
        object(0, 120, 64, 64, 1, 2, fy * 2, 3, 0); end_objects(1);
        sat_gfx_vblank(); sat_gfx_frame();
        assert(sat_gfx_stats.commands == 2 && sat_gfx_stats.uploads == 0);
        assert(be16(v1 + 0x60 + 10) == 0x0210 && be16(v1 + 0x80 + 10) == 0x0210);
        assert((unsigned long)be16(v1 + 0x60 + 8) * 8 == TEX_BASE + (unsigned long)(fy ? lo : hi) * 128);
        assert((unsigned long)be16(v1 + 0x80 + 8) * 8 == TEX_BASE + (unsigned long)(fy ? hi : lo) * 128);
    }
    /* Blank, missing and protected-cache refusal, for either source member
     * and either Y mirror. Saved upper answers must not be looked up twice
     * or lose their own diagnostic cause after the lower lookup. */
    for (kind = 0; kind < 3; kind++) for (side = 0; side < 2; side++) for (fy = 0; fy < 2; fy++)
    {
        unsigned char *input = make_synthetic_pack(0);
        unsigned int absent = side ? 80 : 64, valid = side ? 64 : 80;
        int expected_y = side ? (fy ? 64 : 48) : (fy ? 48 : 64);
        if (kind == 0) put32(input + 84 + absent * 4, ((unsigned long)absent << 16) | 65535UL);
        if (kind == 1)
        {
            memmove(input + 84 + absent * 4, input + 84 + (absent + 1) * 4, (TILE_COUNT - absent - 1) * 4);
            put32(input + 4, TILE_COUNT - 1);
        }
        reset_driver(input);
        if (kind == 2)
        {
            stamp = 1;
            assert(cache_get(&spr_cache, valid, &sat_gfx_stats.refused_sprite) == 0);
            for (i = 0; i < SAT_GFX_SPRITE_SLOTS; i++) spr_slots[i].stamp = 1;
            prev_stamp = 1;
        }
        object(0, 120, 64, 64, 1, 2, fy * 2, 3, 0); end_objects(1);
        sat_gfx_vblank(); sat_gfx_frame();
        assert(sat_gfx_stats.commands == 1);
        assert(signed_word(v1 + 0x60 + 14) == expected_y);
        assert(sat_gfx_stats.missing == (unsigned long)(kind == 1));
        assert(sat_gfx_stats.refused_sprite == (unsigned long)(kind == 2));
#ifdef SAT_VLOG
        assert(vl_miss == (kind == 1) && vl_refslot == (kind == 2) && vl_blank == (kind == 0));
#endif
        free(input);
    }
    reset_driver(pack);
    object(0, 120, 64, 64, 3, 2, 0, 3, 0); end_objects(1);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == 3 && sat_gfx_stats.uploads == 6);
    sat_gfx_host_vdp1r[8] = 2; sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == 3 && sat_gfx_stats.uploads == 0);

    /* Full presentation path, including a never-completing previous plot. */
    reset_driver(pack);
    object(0, 120, 64, 64, 1, 2, 0, 3, 0); end_objects(1);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == 1);
    live_stamp = prev_stamp; memcpy(saved, v1 + TEX_BASE, sizeof saved);
    object(0, 120, 64, 96, 1, 2, 0, 3, 0); end_objects(1);
    sat_gfx_host_vdp1r[8] = 0; clear_cef = 0; tick_step = 1000;
    sat_gfx_snapshot(); sat_gfx_draw();
    assert(stamp == live_stamp && prev_stamp == live_stamp);
    assert(!memcmp(saved, v1 + TEX_BASE, sizeof saved));

    reset_driver(pack);
    for (i = 0; i < 1024; i++) object(i, 120, 64, 64, 2, 2, i & 3, i & 31, 0);
    end_objects(1024); memset(v1 + TABLE_B, 0x5a, 32);
    sat_gfx_vblank(); sat_gfx_frame();
    assert(sat_gfx_stats.commands == SAT_GFX_MAX_COMMANDS && sat_gfx_stats.refused_commands);
    table_end = 0x60UL + SAT_GFX_MAX_COMMANDS * 32;
#ifdef SAT_VLOG
    table_end += 16 * 32;
#endif
    assert(table_end <= TABLE_B - 32 && be16(v1 + table_end) == 0x8000);
    for (i = 0; i < 32; i++) assert(v1[TABLE_B + i] == 0x5a);
    memcpy(saved, v1 + TEX_BASE, sizeof saved);
    sat_gfx_host_vdp1r[8] = 2; sat_gfx_vblank(); sat_gfx_frame();
    assert(be16(v1 + TABLE_B + table_end) == 0x8000);
    assert(!memcmp(saved, v1 + TEX_BASE, sizeof saved));
    puts("zero-copy reuse fallbacks and ownership ok");
}
#endif

int main(int argc, char **argv)
{
    unsigned char *pack = make_synthetic_pack(1);
#if SAT_GFX_FIT == 3
    sat_fit_scale = argc > 2 ? atoi(argv[2]) : 1;
#endif
    if (argc > 1 && !strcmp(argv[1], "cache"))
    {
#if SAT_GFX_SPRITE_PAIRS
        cache_ownership(pack);
#else
        assert(!"cache mode needs SAT_GFX_SPRITE_PAIRS");
#endif
    }
    else if (argc > 1 && !strcmp(argv[1], "limits"))
    {
#if SAT_GFX_SPRITE_PAIRS
        admission_and_command_limits(pack);
#else
        assert(!"limits mode needs SAT_GFX_SPRITE_PAIRS");
#endif
    }
    else if (argc > 1 && !strcmp(argv[1], "reuse"))
    {
#if SAT_GFX_PAIR_REUSE
        reuse_fallbacks(pack);
#else
        assert(!"reuse mode needs SAT_GFX_PAIR_REUSE");
#endif
    }
    else compare_pixels(pack);
    free(pack);
    return 0;
}
