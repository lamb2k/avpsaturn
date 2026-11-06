/* Host test for sat_gfx: the paths the Yaba scenes cannot reach. Synthetic data only, no ROM.
 * gcc -std=c90 -Wall -Wextra -Werror -DSAT_GFX_HOST host_test.c sat_gfx.c -o host_test && ./host_test   Tier HOST. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sat_gfx.h"

unsigned char *PAGE[256];
unsigned char RAMB[0x10000];
static unsigned char OBJ[0x10000], GFX0[0x10000], GFX1[0x10000], GFX2[0x10000], ZERO[0x10000];
static unsigned char V1[0x80000], V2[0x80000], CR[0x1000];
unsigned char *sat_gfx_host_vdp1 = V1, *sat_gfx_host_vdp2 = V2, *sat_gfx_host_cram = CR;
unsigned short sat_gfx_host_vdp1r[0x10], sat_gfx_host_vdp2r[0x90];
static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

static void w16(unsigned char *p, unsigned v) { p[0] = (unsigned char)(v >> 8); p[1] = (unsigned char)v; }
static void w32(unsigned char *p, unsigned long v) { w16(p, (unsigned)(v >> 16)); w16(p + 2, (unsigned)(v & 0xffff)); }
static unsigned r16(const unsigned char *p) { return (unsigned)(p[0] << 8 | p[1]); }

/* Pack with n sprite tiles, keys 0..n-1, each payload its own. */
static unsigned char *make_pack(unsigned long n)
{
    unsigned long hdr = 52, size = hdr + n * 4 + n * 128, i;
    unsigned char *p = (unsigned char *)calloc(size, 1);
    w32(p, 0x53475031UL);
    w32(p + 4, n); w32(p + 8, hdr); w32(p + 12, hdr + n * 4);
    for (i = 1; i < 4; i++) { w32(p + 4 + i * 12, 0); w32(p + 8 + i * 12, hdr); w32(p + 12 + i * 12, hdr); }
    for (i = 0; i < n; i++) { w32(p + hdr + i * 4, i << 14 | (i & 0x3fff)); p[hdr + n * 4 + i * 128] = 0x11; }
    return p;
}

static void set_state(void)
{
    w16(RAMB + 0x8024, 0x9000); w16(RAMB + 0x8026, 0x9040); w16(RAMB + 0x8028, 0x9080);
    w16(RAMB + 0x802a, 0x90e0); w16(RAMB + 0x802c, 0x90c0); w16(RAMB + 0x804a, 0x12c0); /* layers off */
    w16(RAMB + 0x804c, 0x3f); w16(RAMB + 0x8050, 0x2377);
}

/* n objects, each size w x h tiles, codes rising, palette bank. */
static void set_list(int n, int w, int h, int step, int bank)
{
    int i;
    memset(OBJ, 0, sizeof OBJ);
    for (i = 0; i < n; i++)
    {
        unsigned char *o = OBJ + 0x8000 + i * 8;
        w16(o, 100 | (4U << 13)); w16(o + 2, 50);
        w16(o + 4, (unsigned)(i * step)); w16(o + 6, (unsigned)((h - 1) << 12 | (w - 1) << 8 | bank));
    }
    w16(OBJ + 0x8000 + n * 8 + 2, 0x8000);
}

int main(void)
{
    int i;
    unsigned char *pack;
    for (i = 0; i < 256; i++) PAGE[i] = ZERO;
    PAGE[0x70] = OBJ; PAGE[0x90] = GFX0; PAGE[0x91] = GFX1; PAGE[0x92] = GFX2;
    set_state();

    CHECK(!sat_gfx_init(0));
    w32(ZERO, 0);
    CHECK(!sat_gfx_init(ZERO));

    /* The CRAM map: every bank of four pages, and the refusal just outside. */
    pack = make_pack(8000);
    CHECK(sat_gfx_init(pack));
    CHECK(sat_gfx_bank(0, 0) == 0);
    CHECK(sat_gfx_bank(0, 16) == 16);
    CHECK(sat_gfx_bank(3, 31) == 127);
    CHECK(sat_gfx_stats.refused_bank == 0);
    CHECK(sat_gfx_bank(0, 32) == -1);
    CHECK(sat_gfx_bank(4, 0) == -1);
    CHECK(sat_gfx_stats.refused_bank == 2);

    /* Colours: full white at full brightness, and the dark floor the board gives brightness 0. */
    CHECK(sat_gfx_colour(0xffff) == 0xffff);
    CHECK(sat_gfx_colour(0x0000) == 0x8000);
    CHECK((sat_gfx_colour(0x0f00) & 31) == (255U * 15 / 45) >> 3);

    /* A palette above 16 reaches CRAM and the sprite command. */
    set_list(1, 1, 1, 1, 23);
    w16(GFX0 + 0xc000 + (23 * 16 + 3) * 2, 0xf123);
    sat_gfx_frame();
    CHECK(sat_gfx_stats.commands == 1);
    CHECK(sat_gfx_stats.top_bank == 23);
    CHECK(r16(V1 + 0x60 + 6) == ((4U << 13) | (23U << 4)));
    CHECK(r16(CR + (23 * 16 + 3 + 1) * 2) == sat_gfx_colour(0xf123));

    /* Texture refusal: 15 x 15 blocks, 14 rows on screen, all different: 4200 tiles against 3584 slots. */
    CHECK(sat_gfx_init(pack));
    set_list(20, 15, 15, 256, 1);
    for (i = 0; i < 20; i++) w16(OBJ + 0x8000 + i * 8 + 2, 0);
    sat_gfx_frame();
    printf("texture case: commands %u slots %u refused %lu\n", sat_gfx_stats.commands, sat_gfx_stats.sprite_slots_used, sat_gfx_stats.refused_sprite);
    CHECK(sat_gfx_stats.sprite_slots_used == SAT_GFX_SPRITE_SLOTS);
    CHECK(sat_gfx_stats.commands == SAT_GFX_MAX_COMMANDS);
    CHECK(sat_gfx_stats.refused_sprite == 4200 - SAT_GFX_SPRITE_SLOTS);

    /* Command refusal: the same one tile, more blocks than the table holds. */
    CHECK(sat_gfx_init(pack));
    set_list(1024, 3, 3, 0, 1);
    sat_gfx_stats.refused_commands = 0;
    sat_gfx_frame();
    printf("command case: commands %u refused %lu uploads %u\n", sat_gfx_stats.commands, sat_gfx_stats.refused_commands, sat_gfx_stats.uploads);
    CHECK(sat_gfx_stats.commands == SAT_GFX_MAX_COMMANDS);
    CHECK(sat_gfx_stats.refused_commands == 1024UL * 9 - SAT_GFX_MAX_COMMANDS);
    CHECK(r16(V1 + 0x60 + 32 * SAT_GFX_MAX_COMMANDS) == 0x8000);

    /* Reuse: a second frame on the same list copies nothing; a new list takes slots no longer drawn. */
    sat_gfx_frame();
    CHECK(sat_gfx_stats.uploads == 0);
    set_list(1, 1, 1, 1, 1);
    w16(OBJ + 0x8000 + 4, 77);
    sat_gfx_frame();
    CHECK(sat_gfx_stats.uploads == 1);

    /* A tile not in the pack draws nothing and is counted. */
    w16(OBJ + 0x8000 + 4, 60000);
    sat_gfx_stats.missing = 0;
    sat_gfx_frame();
    CHECK(sat_gfx_stats.commands == 0);
    CHECK(sat_gfx_stats.missing == 1);

    printf(fails ? "FAILED %d\n" : "host test ok\n", fails);
    return fails != 0;
}
