/* AvP Saturn graphics library, see sat_gfx.h. Bare metal: no Jo, no SGL, so lane avp-sat-rt can call it from vblank.
 *
 * VDP2 VRAM (512 KB, all accounted):
 *   A0 00000 scroll 2 map 16K, 04000 scroll 1 map 16K, 08000 scroll 3 map 64K, 18000 scroll 1 cells 31K,
 *      1fc00 row scroll 896 B, 1fffe back colour
 *   A1 20000 scroll 2 cells 128K (1024 tiles)    B0+B1 40000 scroll 3 cells 256K (512 tiles)
 * VDP1 VRAM (512 KB): 00000 commands 64K, 10000 textures 448K (3584 tiles).
 * CRAM mode 1, 2048 entries: page * 32 + bank gives one of 128 sixteen colour banks, pen p at entry p + 1, entry 0 clear.
 */
#include "sat_gfx.h"

extern unsigned char *PAGE[256];
extern unsigned char RAMB[];

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned long u32;

#ifdef SAT_GFX_HOST
/* Host test: plain big-endian memory in place of the chips. */
extern u8 *sat_gfx_host_vdp1, *sat_gfx_host_vdp2, *sat_gfx_host_cram;
extern u16 sat_gfx_host_vdp1r[], sat_gfx_host_vdp2r[];
#define VDP1_VRAM sat_gfx_host_vdp1
#define VDP2_VRAM sat_gfx_host_vdp2
#define CRAM_AT(e) (sat_gfx_host_cram + (u32)(e) * 2)
#define VDP1R(o) (sat_gfx_host_vdp1r[(o) / 2])
#define VDP2R(o) (sat_gfx_host_vdp2r[(o) / 2])
static u16 be16(const u8 *p) { return (u16)((p[0] << 8) | p[1]); }
static u32 be32(const u8 *p) { return ((u32)p[0] << 24) | ((u32)p[1] << 16) | ((u32)p[2] << 8) | p[3]; }
static void put16(u8 *p, u16 v) { p[0] = (u8)(v >> 8); p[1] = (u8)v; }
static void put32(u8 *p, u32 v) { p[0] = (u8)(v >> 24); p[1] = (u8)(v >> 16); p[2] = (u8)(v >> 8); p[3] = (u8)v; }
#define get32(p) be32(p)
#else
#define VDP1_VRAM ((u8 *)0x25C00000UL)
#define VDP2_VRAM ((u8 *)0x25E00000UL)
#define CRAM_AT(e) ((u8 *)0x25F00000UL + (u32)(e) * 2)
#define VDP1R(o) (*(volatile u16 *)(0x25D00000UL + (o)))
#define VDP2R(o) (*(volatile u16 *)(0x25F80000UL + (o)))
#define be16(p) (*(const u16 *)(const void *)(p))
#define be32(p) (*(const u32 *)(const void *)(p))
#define put16(d, v) (*(volatile u16 *)(void *)(d) = (u16)(v))
#define put32(d, v) (*(volatile u32 *)(void *)(d) = (u32)(v))
#define get32(d) (*(const volatile u32 *)(const void *)(d))
#endif

/* Game state, by address. */
#define RAM16(a) be16(RAMB + ((a) - 0xff0000UL))
#define SH_SCROLL1_BASE 0xff8024UL
#define SH_SCROLL2_BASE 0xff8026UL
#define SH_SCROLL3_BASE 0xff8028UL
#define SH_ROWSCROLL_BASE 0xff802aUL
#define SH_PALETTE_BASE 0xff802cUL
#define SH_VIDEO 0xff8044UL
#define SH_LAYERS 0xff804aUL
#define SH_PAL_PAGES 0xff804cUL
#define SH_PRIORITY 0xff8050UL
#define SH_S1X 0xffee1aUL
#define SH_S1Y 0xffee1cUL
#define SH_S2X 0xffee1eUL
#define SH_S2Y 0xffee20UL
#define SH_S3X 0xffee22UL
#define SH_S3Y 0xffee24UL
#define SH_ROWOFFS 0xffee2eUL

/* The game sets these once at boot (0x5cc, 0x5d4) and never moves them: object origin. */
#define OBJ_XOFFS 0x40
#define OBJ_YOFFS 0x10
#define CPS_LEFT 64
#define CPS_TOP 16

/* A graphics RAM base as the game writes it: 0x90c0 is 0x90c000. */
#define GFX(reg) (PAGE[((reg) >> 8) & 0xff] + (((u32)(reg) << 8) & 0xffffUL))

/* VDP2 layout */
#define MAP_S2 0x00000UL
#define MAP_S1 0x04000UL
#define MAP_S3 0x08000UL
#define CELL_S1 0x18000UL
#define ROWTAB 0x1fc00UL
#define BACKCOL 0x1fffeUL
#define CLEAR_NAME (CELL_S1 >> 5) /* four clear cells at the start of the scroll 1 slab */
#define CELL_S2 0x20000UL
#define CELL_S3 0x40000UL
/* VDP1 layout */
#define TEX_BASE 0x10000UL

/* VDP1 registers */
#define TVMR 0x00
#define FBCR 0x02
#define PTMR 0x04
#define EWDR 0x06
#define EWLR 0x08
#define EWRR 0x0a

#define SEC_SPRITE 0
#define SEC_S1 1
#define SEC_S2 2
#define SEC_S3 3
#define BLANK_INDEX 0x1fffUL
#define KEY_SHIFT 13

typedef struct
{
    u32 count;
    const u8 *keys; /* u32: key << 13 | payload index, ascending; BLANK_INDEX marks a tile with no visible pen */
    const u8 *data;
} Section;

/* A set of VRAM slots holding pack tiles; a slot not drawn this frame can be taken. */
#define HASH_SIZE 1024
typedef struct
{
    u8 *vram;
    u32 slot_bytes;
    u16 capacity;
    u16 hand;
    u16 first; /* slots below this are reserved */
    u16 used;  /* slots stamped this frame */
    int section;
    u32 *slot_key;
    u16 *slot_stamp;
    u16 *slot_next;
    u16 *head;
} Cache;

#define NOSLOT 0xffffU
#define NOKEY 0xffffffffUL

static Section sections[4];
static u16 stamp;

static u32 spr_key[SAT_GFX_SPRITE_SLOTS];
static u16 spr_stamp[SAT_GFX_SPRITE_SLOTS], spr_next[SAT_GFX_SPRITE_SLOTS], spr_head[HASH_SIZE];
static u32 s1_key[SAT_GFX_S1_SLOTS];
static u16 s1_stamp[SAT_GFX_S1_SLOTS], s1_next[SAT_GFX_S1_SLOTS], s1_head[HASH_SIZE];
static u32 s2_key[SAT_GFX_S2_SLOTS];
static u16 s2_stamp[SAT_GFX_S2_SLOTS], s2_next[SAT_GFX_S2_SLOTS], s2_head[HASH_SIZE];
static u32 s3_key[SAT_GFX_S3_SLOTS];
static u16 s3_stamp[SAT_GFX_S3_SLOTS], s3_next[SAT_GFX_S3_SLOTS], s3_head[HASH_SIZE];
static Cache spr_cache, s1_cache, s2_cache, s3_cache;
static u16 cram_shadow[2048];
static u16 back_shadow;

SatGfxStats sat_gfx_stats;

static void cache_setup(Cache *c, u8 *vram, u32 slot_bytes, u16 capacity, u16 first, int section,
                        u32 *key, u16 *st, u16 *next, u16 *head)
{
    u32 i;
    c->vram = vram; c->slot_bytes = slot_bytes; c->capacity = capacity; c->hand = first; c->first = first; c->used = 0;
    c->section = section; c->slot_key = key; c->slot_stamp = st; c->slot_next = next; c->head = head;
    for (i = 0; i < capacity; i++) { key[i] = NOKEY; st[i] = 0; next[i] = NOSLOT; }
    for (i = 0; i < HASH_SIZE; i++) head[i] = NOSLOT;
}

/* Payload index of a key, BLANK_INDEX for an empty tile, or -1 when the pack lacks it. */
static long pack_find(const Section *s, u32 key)
{
    long lo = 0, hi = (long)s->count - 1;
    while (lo <= hi)
    {
        long mid = (lo + hi) >> 1;
        u32 v = be32(s->keys + (u32)mid * 4);
        u32 k = v >> KEY_SHIFT;
        if (k == key) return (long)(v & BLANK_INDEX);
        if (k < key) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}

static void vram_copy(u8 *dest, const u8 *src, u32 bytes)
{
    u32 i;
#ifdef SAT_GFX_HOST
    for (i = 0; i < bytes; i++) dest[i] = src[i];
#else
    volatile u32 *d = (volatile u32 *)(void *)dest;
    const u32 *s = (const u32 *)(const void *)src;
    for (i = 0; i < bytes / 4; i++) d[i] = s[i];
#endif
}

#define HASH(k) (((k) ^ ((k) >> 10)) & (HASH_SIZE - 1))

/* Slot holding a tile, uploading it on a miss. NOSLOT for a blank, missing or refused tile. */
static u16 cache_get(Cache *c, u32 key, unsigned long *refused)
{
    u32 h = HASH(key);
    u16 s = c->head[h];
    u16 n = NOSLOT;
    u32 scan;
    long idx;
    while (s != NOSLOT)
    {
        if (c->slot_key[s] == key)
        {
            if (c->slot_stamp[s] != stamp) { c->slot_stamp[s] = stamp; c->used++; }
            return s;
        }
        s = c->slot_next[s];
    }
    idx = pack_find(&sections[c->section], key);
    if (idx < 0) { sat_gfx_stats.missing++; return NOSLOT; }
    if ((u32)idx == BLANK_INDEX) return NOSLOT;
    for (scan = c->first; scan < c->capacity; scan++)
    {
        u16 t = c->hand;
        c->hand = (u16)(t + 1U >= c->capacity ? c->first : t + 1U);
        if (c->slot_stamp[t] != stamp) { n = t; break; }
    }
    if (n == NOSLOT) { (*refused)++; return NOSLOT; }
    if (c->slot_key[n] != NOKEY)
    {
        u16 *link = &c->head[HASH(c->slot_key[n])];
        while (*link != n) link = &c->slot_next[*link];
        *link = c->slot_next[n];
    }
    c->slot_key[n] = key; c->slot_stamp[n] = stamp; c->used++;
    c->slot_next[n] = c->head[h]; c->head[h] = n;
    vram_copy(c->vram + (u32)n * c->slot_bytes, sections[c->section].data + (u32)idx * c->slot_bytes, c->slot_bytes);
    if (c == &spr_cache) sat_gfx_stats.uploads++; else sat_gfx_stats.layer_uploads++;
    return n;
}

int sat_gfx_bank(int page, int bank)
{
    if (page < 0 || page >= SAT_GFX_PAGES || bank < 0 || bank >= SAT_GFX_BANKS_PER_PAGE)
    {
        sat_gfx_stats.refused_bank++;
        return -1;
    }
    if (bank > (int)sat_gfx_stats.top_bank) sat_gfx_stats.top_bank = (u16)bank;
    return page * SAT_GFX_BANKS_PER_PAGE + bank;
}

unsigned short sat_gfx_colour(unsigned short cps)
{
    /* The board's brightness scale, to 5 bits. */
    u32 bright = 0x0f + (u32)((cps >> 12) << 1);
    u32 r = ((u32)((cps >> 8) & 15) * 0x11 * bright / 0x2d) >> 3;
    u32 g = ((u32)((cps >> 4) & 15) * 0x11 * bright / 0x2d) >> 3;
    u32 b = ((u32)(cps & 15) * 0x11 * bright / 0x2d) >> 3;
    return (u16)(0x8000U | (b << 10) | (g << 5) | r);
}

/* Pages present in graphics RAM follow the enable mask; once one was present, a skipped page still takes room. */
static const u8 *palette_page(const u8 *base, u16 mask, int page)
{
    int at = 0, i, seen = 0;
    for (i = 0; i < page; i++)
    {
        if ((mask >> i) & 1) { seen = 1; at++; }
        else if (seen) at++;
    }
    if (!((mask >> page) & 1)) return 0;
    return base + (u32)at * 0x400;
}

static void update_palette(void)
{
    u16 reg = RAM16(SH_PALETTE_BASE);
    u16 mask = RAM16(SH_PAL_PAGES);
    const u8 *base = GFX(reg);
    const u8 *last;
    int page;
    u16 written = 0;
    for (page = 0; page < SAT_GFX_PAGES; page++)
    {
        const u8 *src = palette_page(base, mask, page);
        int i;
        if (!src) continue;
        for (i = 0; i < SAT_GFX_BANKS_PER_PAGE * 16; i++)
        {
            /* Pen p at entry p + 1 of its bank; pen 15 is clear on the board and has no entry. */
            u16 c;
            int e;
            if ((i & 15) == 15) continue;
            c = be16(src + (u32)i * 2);
            e = page * SAT_GFX_BANKS_PER_PAGE * 16 + i + 1;
            if (cram_shadow[e] != c)
            {
                cram_shadow[e] = c;
                put16(CRAM_AT(e), sat_gfx_colour(c));
                written++;
            }
        }
    }
    /* The board fills with pen 0xbff: page 5, bank 31, pen 15. */
    last = palette_page(base, mask, 5);
    if (last)
    {
        u16 c = be16(last + 0x3feUL);
        if (c != back_shadow)
        {
            back_shadow = c;
            put16(VDP2_VRAM + BACKCOL, sat_gfx_colour(c));
        }
    }
    sat_gfx_stats.colours_written = written;
}

/* Layer maps: only the words the picture can show are looked at, and only changed words are written. */
static void write_name(u8 *addr, u32 name)
{
    if (get32(addr) != name)
    {
        put32(addr, name);
        sat_gfx_stats.layer_writes++;
    }
}

#define PN_VFLIP 0x80000000UL
#define PN_HFLIP 0x40000000UL

static u32 name_of(u16 attr, int page, u32 charno)
{
    int bank = sat_gfx_bank(page, attr & 31);
    u32 n = ((u32)(bank < 0 ? 0 : bank) << 16) | charno;
    if (attr & 0x20) n |= PN_HFLIP;
    if (attr & 0x40) n |= PN_VFLIP;
    return n;
}

static void draw_scroll1(u16 base, u16 sx, u16 sy)
{
    const u8 *map = GFX(base & 0xffc0U);
    u32 x0 = (u32)sx + CPS_LEFT + SAT_GFX_CROP_X, y0 = (u32)sy + CPS_TOP;
    u32 row, col;
    for (row = 0; row <= SAT_GFX_SCREEN_H / 8; row++)
        for (col = 0; col <= SAT_GFX_SCREEN_W / 8; col++)
        {
            u32 c = ((x0 >> 3) + col) & 63, r = ((y0 >> 3) + row) & 63;
            u32 idx = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6);
            u16 code = be16(map + idx * 4), attr = be16(map + idx * 4 + 2);
            /* Odd columns read the right half of the 16 pixel row. */
            u16 slot = cache_get(&s1_cache, ((u32)code << 1) | ((idx >> 5) & 1), &sat_gfx_stats.refused_layer);
            u32 name = CLEAR_NAME;
            if (slot != NOSLOT) name = name_of(attr, 1, (CELL_S1 + (u32)slot * 32) >> 5);
            write_name(VDP2_VRAM + MAP_S1 + (r * 64 + c) * 4, name);
        }
}

/* A 2x2 page plane of 16 pixel characters. */
static u8 *s2_name(u32 r, u32 c)
{
    return VDP2_VRAM + MAP_S2 + (((r >> 5) * 2 + (c >> 5)) * 0x1000) + (((r & 31) * 32 + (c & 31)) * 4);
}

static void draw_scroll2(u16 base, u16 sx, u16 sy, int full_row)
{
    const u8 *map = GFX(base & 0xffc0U);
    u32 x0 = (u32)sx + CPS_LEFT + SAT_GFX_CROP_X, y0 = (u32)sy + CPS_TOP;
    u32 row, col, cols = full_row ? 64 : SAT_GFX_SCREEN_W / 16 + 1;
    for (row = 0; row <= SAT_GFX_SCREEN_H / 16; row++)
        for (col = 0; col < cols; col++)
        {
            u32 c = ((full_row ? 0 : x0 >> 4) + col) & 63, r = ((y0 >> 4) + row) & 63;
            u32 idx = (r & 0x0f) + (c << 4) + ((r & 0x30) << 6);
            u16 code = be16(map + idx * 4), attr = be16(map + idx * 4 + 2);
            u16 slot = cache_get(&s2_cache, code, &sat_gfx_stats.refused_layer);
            u32 name = CLEAR_NAME;
            if (slot != NOSLOT) name = name_of(attr, 2, (CELL_S2 + (u32)slot * 128) >> 5);
            write_name(s2_name(r, c), name);
        }
}

/* Four planes of 2x2 pages: 128 x 128 sixteen pixel characters, each CPS tile four of them. */
static u8 *s3_name(u32 r, u32 c)
{
    u32 plane = (r >> 6) * 2 + (c >> 6);
    u32 rr = r & 63, cc = c & 63;
    return VDP2_VRAM + MAP_S3 + plane * 0x4000 + ((rr >> 5) * 2 + (cc >> 5)) * 0x1000 + ((rr & 31) * 32 + (cc & 31)) * 4;
}

static void draw_scroll3(u16 base, u16 sx, u16 sy)
{
    const u8 *map = GFX(base & 0xffc0U);
    u32 x0 = (u32)sx + CPS_LEFT + SAT_GFX_CROP_X, y0 = (u32)sy + CPS_TOP;
    u32 row, col;
    for (row = 0; row <= SAT_GFX_SCREEN_H / 32; row++)
        for (col = 0; col <= SAT_GFX_SCREEN_W / 32; col++)
        {
            u32 c = ((x0 >> 5) + col) & 63, r = ((y0 >> 5) + row) & 63;
            u32 idx = (r & 7) + (c << 3) + ((r & 0x38) << 6);
            u16 code = (u16)(be16(map + idx * 4) & 0x3fff), attr = be16(map + idx * 4 + 2);
            u16 slot = cache_get(&s3_cache, code, &sat_gfx_stats.refused_layer);
            u32 sub;
            for (sub = 0; sub < 4; sub++)
            {
                u32 name = CLEAR_NAME;
                if (slot != NOSLOT)
                {
                    /* A flipped tile also swaps its characters. */
                    u32 use = sub ^ ((attr & 0x20) ? 1U : 0U) ^ ((attr & 0x40) ? 2U : 0U);
                    name = name_of(attr, 3, (CELL_S3 + (u32)slot * 512 + use * 128) >> 5);
                }
                write_name(s3_name(r * 2 + (sub >> 1), c * 2 + (sub & 1)), name);
            }
        }
}

/* Row scroll: returns 1 when any visible line moves. Only offsets are stored; VDP2 adds them to the layer's scroll. */
static int update_rowscroll(u16 base, u16 offs)
{
    const u8 *tab = GFX(base);
    u32 line;
    int any = 0;
    for (line = 0; line < SAT_GFX_SCREEN_H; line++)
    {
        u16 v = be16(tab + (((line + CPS_TOP + offs) & 0x3ff) * 2));
        if (v) any = 1;
        write_name(VDP2_VRAM + ROWTAB + line * 4, (u32)v << 16);
    }
    return any;
}

/* Layer order and the priority table. VDP2 levels: layers 2, 4, 6; a sprite level sits just under the highest layer it hides behind. */
static void update_priority(u16 layers, u16 pri)
{
    int order[3], lp[3], n = 0, i, p;
    u16 prin[3], s[8];
    for (i = 0; i < 4; i++)
    {
        int l = (layers >> (6 + 2 * i)) & 3;
        if (l && n < 3) { order[n] = l; lp[n] = (pri >> (4 * l)) & 15; n++; }
    }
    prin[0] = prin[1] = prin[2] = 0;
    for (i = 0; i < n; i++) prin[order[i] - 1] = (u16)(2 + 2 * i);
    VDP2R(0xf8) = (u16)(prin[1] | (prin[2] << 8)); /* NBG0 = scroll 2, NBG1 = scroll 3 */
    VDP2R(0xfa) = prin[0];                          /* NBG2 = scroll 1 */
    for (p = 0; p < 8; p++)
    {
        int level = 7, below = -1;
        for (i = 0; i < n; i++) if (p <= lp[i]) below = i;
        if (below >= 0)
        {
            level = 1 + 2 * below;
            for (i = 0; i < below; i++) if (p > lp[i]) { sat_gfx_stats.nonmonotone++; break; }
        }
        s[p] = (u16)level;
    }
    VDP2R(0xf0) = (u16)(s[0] | (s[1] << 8));
    VDP2R(0xf2) = (u16)(s[2] | (s[3] << 8));
    VDP2R(0xf4) = (u16)(s[4] | (s[5] << 8));
    VDP2R(0xf6) = (u16)(s[6] | (s[7] << 8));
}

static void put_sprite(u8 *cmd, u16 flip, u16 colr, u32 tex, int x, int y)
{
    put16(cmd + 0, flip);          /* normal sprite, jump next */
    put16(cmd + 4, 0x0880);        /* pre-clip off, end codes off, pen 0 clear, 16 colour bank */
    put16(cmd + 6, colr);
    put16(cmd + 8, (u16)(tex >> 3));
    put16(cmd + 10, 0x0210);       /* 16 x 16 */
    put16(cmd + 12, (u16)x);
    put16(cmd + 14, (u16)y);
}

/* Object list at 0x708000. The board keeps the first pixel down, drawing from the end of the list, so later entries win: VDP1 paints in
   list order, tiles of a block last to first. Each 16 pixel tile is one command. */
static void draw_sprites(void)
{
    const u8 *list = PAGE[0x70] + 0x8000;
    u8 *cmd = VDP1_VRAM + 0x40; /* after clip and local */
    int count = 0, i;
    u16 commands = 0;
    while (count < 0x400 && be16(list + count * 8 + 2) < 0x8000 && be16(list + count * 8 + 6) < 0xff00) count++;
    sat_gfx_stats.objects = (u16)count;
    for (i = 0; i < count; i++)
    {
        const u8 *o = list + i * 8;
        u16 xw = be16(o), yw = be16(o + 2), cw = be16(o + 4), aw = be16(o + 6);
        u32 code = (u32)cw + (((u32)yw & 0x6000UL) << 3);
        int nx = ((aw >> 8) & 15) + 1, ny = ((aw >> 12) & 15) + 1;
        int fx = (aw >> 5) & 1, fy = (aw >> 6) & 1;
        int x = xw, y = yw, tx, ty;
        int bank = sat_gfx_bank(0, aw & 31);
        u16 colr;
        u16 flip = (u16)((fx ? 0x10 : 0) | (fy ? 0x20 : 0));
        if (bank < 0) continue;
        colr = (u16)((xw & 0xe000U) | ((u32)bank << 4));
        if (aw & 0x80) { x += OBJ_XOFFS; y += OBJ_YOFFS; }
        x += CPS_LEFT - OBJ_XOFFS;
        y += CPS_TOP - OBJ_YOFFS;
        for (ty = ny - 1; ty >= 0; ty--)
            for (tx = nx - 1; tx >= 0; tx--)
            {
                int sx = ((x + tx * 16) & 0x3ff) - CPS_LEFT - SAT_GFX_CROP_X;
                int sy = ((y + ty * 16) & 0x3ff) - CPS_TOP;
                u32 tile;
                u16 slot;
                if (sx <= -16 || sx >= SAT_GFX_SCREEN_W || sy <= -16 || sy >= SAT_GFX_SCREEN_H) continue;
                if (fx || fy)
                    tile = code + (u32)(fx ? nx - 1 - tx : tx) + 0x10UL * (u32)(fy ? ny - 1 - ty : ty);
                else
                    tile = (code & ~0xfUL) + ((code + (u32)tx) & 0xfUL) + 0x10UL * (u32)ty;
                slot = cache_get(&spr_cache, tile, &sat_gfx_stats.refused_sprite);
                if (slot == NOSLOT) continue;
                if (commands >= SAT_GFX_MAX_COMMANDS) { sat_gfx_stats.refused_commands++; continue; }
                put_sprite(cmd, flip, colr, TEX_BASE + (u32)slot * 128, sx, sy);
                cmd += 32;
                commands++;
            }
    }
    put16(cmd, 0x8000); /* end */
    sat_gfx_stats.commands = commands;
    if (commands > sat_gfx_stats.commands_peak) sat_gfx_stats.commands_peak = commands;
}

static void note_slots(void)
{
    SatGfxStats *t = &sat_gfx_stats;
    t->sprite_slots_used = spr_cache.used;
    if (spr_cache.used > t->sprite_slots_peak) t->sprite_slots_peak = spr_cache.used;
    if (t->uploads > t->uploads_peak) t->uploads_peak = t->uploads;
    if (s1_cache.used > t->layer_slots_peak[0]) t->layer_slots_peak[0] = s1_cache.used;
    if (s2_cache.used > t->layer_slots_peak[1]) t->layer_slots_peak[1] = s2_cache.used;
    if (s3_cache.used > t->layer_slots_peak[2]) t->layer_slots_peak[2] = s3_cache.used;
}

void sat_gfx_frame(void)
{
    u16 layers = RAM16(SH_LAYERS);
    u16 video = RAM16(SH_VIDEO);
    u16 s1x = RAM16(SH_S1X), s1y = RAM16(SH_S1Y), s2x = RAM16(SH_S2X), s2y = RAM16(SH_S2Y), s3x = RAM16(SH_S3X), s3y = RAM16(SH_S3Y);
    u16 bgon = 0;
    int row_active = 0;

    stamp = (u16)(stamp + 1U == 0x10000UL ? 1U : stamp + 1U);
    spr_cache.used = s1_cache.used = s2_cache.used = s3_cache.used = 0;
    sat_gfx_stats.uploads = 0;
    sat_gfx_stats.layer_uploads = 0;
    sat_gfx_stats.layer_writes = 0;
    sat_gfx_stats.top_bank = 0;

    update_palette();
    update_priority(layers, RAM16(SH_PRIORITY));
    if (video & 1) row_active = update_rowscroll(RAM16(SH_ROWSCROLL_BASE), RAM16(SH_ROWOFFS));
    VDP2R(0x9a) = (u16)(row_active ? 0x0002 : 0);

    if (layers & 4) { bgon |= 1; draw_scroll2(RAM16(SH_SCROLL2_BASE), s2x, s2y, row_active); }
    if (layers & 8) { bgon |= 2; draw_scroll3(RAM16(SH_SCROLL3_BASE), s3x, s3y); }
    if (layers & 2) { bgon |= 4; draw_scroll1(RAM16(SH_SCROLL1_BASE), s1x, s1y); }
    #ifdef SAT_GFX_BGMASK
    bgon &= SAT_GFX_BGMASK;
#endif
    VDP2R(0x20) = bgon;
    VDP2R(0x70) = (u16)((s2x + CPS_LEFT + SAT_GFX_CROP_X) & 0x7ff);
    VDP2R(0x74) = (u16)((s2y + CPS_TOP) & 0x7ff);
    VDP2R(0x80) = (u16)((s3x + CPS_LEFT + SAT_GFX_CROP_X) & 0x7ff);
    VDP2R(0x84) = (u16)((s3y + CPS_TOP) & 0x7ff);
    VDP2R(0x90) = (u16)((s1x + CPS_LEFT + SAT_GFX_CROP_X) & 0x7ff);
    VDP2R(0x92) = (u16)((s1y + CPS_TOP) & 0x7ff);

    draw_sprites();
    note_slots();

    /* Plot into the back buffer now; the swap comes with the next vblank. */
    VDP1R(FBCR) = 3;
    VDP1R(PTMR) = 1;
    sat_gfx_stats.frames++;
}

static int open_pack(const u8 *p)
{
    int i;
    if (be32(p) != 0x53475031UL) return 0; /* SGP1 */
    for (i = 0; i < 4; i++)
    {
        sections[i].count = be32(p + 4 + i * 12);
        sections[i].keys = p + be32(p + 8 + i * 12);
        sections[i].data = p + be32(p + 12 + i * 12);
    }
    return 1;
}

static void clear_vram(u8 *p, u32 bytes)
{
    u32 i;
    for (i = 0; i < bytes; i += 4) put32(p + i, 0);
}

int sat_gfx_init(const void *pack)
{
    int i;
    u32 n;
    u8 *c;
    if (!pack || !open_pack((const u8 *)pack)) return 0;

    VDP2R(0x00) = 0x0001;                         /* display off, 352 x 224 */
    clear_vram(VDP2_VRAM, 0x80000UL);
    clear_vram(VDP1_VRAM, 0x80000UL);
    for (i = 0; i < 2048; i++) { put16(CRAM_AT(i), 0); cram_shadow[i] = 0; }
    back_shadow = 0;

    for (n = 0; n < CELL_S1; n += 4) put32(VDP2_VRAM + n, CLEAR_NAME);
    cache_setup(&spr_cache, VDP1_VRAM + TEX_BASE, 128, SAT_GFX_SPRITE_SLOTS, 0, SEC_SPRITE, spr_key, spr_stamp, spr_next, spr_head);
    cache_setup(&s1_cache, VDP2_VRAM + CELL_S1, 32, SAT_GFX_S1_SLOTS, 4, SEC_S1, s1_key, s1_stamp, s1_next, s1_head);
    cache_setup(&s2_cache, VDP2_VRAM + CELL_S2, 128, SAT_GFX_S2_SLOTS, 0, SEC_S2, s2_key, s2_stamp, s2_next, s2_head);
    cache_setup(&s3_cache, VDP2_VRAM + CELL_S3, 512, SAT_GFX_S3_SLOTS, 0, SEC_S3, s3_key, s3_stamp, s3_next, s3_head);
    stamp = 0;

    /* VRAM split into four banks, CRAM mode 1. */
    VDP2R(0x0e) = 0x1300;
    /* Reads: A0 names for all three plus scroll 1 cells, A1 scroll 2 cells, B0 and B1 scroll 3 cells. */
    VDP2R(0x10) = 0x012f; VDP2R(0x12) = 0xff6f;
    VDP2R(0x14) = 0x4444; VDP2R(0x16) = 0x4444;
    VDP2R(0x18) = 0x5555; VDP2R(0x1a) = 0x5555;
    VDP2R(0x1c) = 0x5555; VDP2R(0x1e) = 0x5555;
    VDP2R(0x22) = 0; VDP2R(0x24) = 0; VDP2R(0x26) = 0;
    VDP2R(0x28) = 0x0101;                         /* NBG0, NBG1: 16 colour, 2 x 2 cell characters */
    VDP2R(0x2a) = 0;                              /* NBG2: 16 colour, 1 cell */
    VDP2R(0x30) = 0; VDP2R(0x32) = 0; VDP2R(0x34) = 0; /* two word names */
    VDP2R(0x38) = 0;
    VDP2R(0x3a) = 0x000f;                         /* NBG0, NBG1 planes 2 x 2 pages; NBG2 1 page */
    VDP2R(0x3c) = 0;                              /* map offsets 0 */
    /* Map values count pages: 4K for 2 x 2 characters, 16K for 1 cell. */
    VDP2R(0x40) = 0x0000; VDP2R(0x42) = 0x0000;   /* NBG0, scroll 2: every plane at 0 */
    VDP2R(0x44) = (u16)(8 | (12 << 8));           /* NBG1, scroll 3: four planes from 0x8000 */
    VDP2R(0x46) = (u16)(16 | (20 << 8));
    VDP2R(0x48) = 0x0101; VDP2R(0x4a) = 0x0101;   /* NBG2, scroll 1: one page at 0x4000 */
    VDP2R(0x72) = 0; VDP2R(0x76) = 0; VDP2R(0x82) = 0; VDP2R(0x86) = 0;
    VDP2R(0x78) = 1; VDP2R(0x7a) = 0; VDP2R(0x7c) = 1; VDP2R(0x7e) = 0;
    VDP2R(0x88) = 1; VDP2R(0x8a) = 0; VDP2R(0x8c) = 1; VDP2R(0x8e) = 0;
    VDP2R(0x98) = 0;
    VDP2R(0xa0) = 0; VDP2R(0xa2) = (u16)(ROWTAB >> 1);
    VDP2R(0xac) = (u16)(BACKCOL >> 17); VDP2R(0xae) = (u16)((BACKCOL >> 1) & 0xffff);
    VDP2R(0xe0) = 0x0001;                         /* sprite type 1: 3 priority bits, 11 colour bits */
    VDP2R(0xe2) = 0; VDP2R(0xe4) = 0; VDP2R(0xe6) = 0; VDP2R(0xe8) = 0; VDP2R(0xea) = 0; VDP2R(0xec) = 0; VDP2R(0xee) = 0;
    VDP2R(0xf8) = 0; VDP2R(0xfa) = 0;

    /* VDP1: 16 bit, plot by hand, erase to clear. */
    VDP1R(TVMR) = 0;
    VDP1R(EWDR) = 0;
    VDP1R(EWLR) = 0;
    VDP1R(EWRR) = (u16)(((SAT_GFX_SCREEN_W >> 3) << 9) | (SAT_GFX_SCREEN_H - 1));
    c = VDP1_VRAM;
    put16(c + 0, 0x0009);                         /* system clip */
    put16(c + 20, SAT_GFX_SCREEN_W - 1);
    put16(c + 22, SAT_GFX_SCREEN_H - 1);
    put16(c + 32, 0x000a);                        /* local origin 0, 0 */
    put16(c + 64, 0x8000);
    VDP1R(PTMR) = 0;

    VDP2R(0x00) = 0x8001;                         /* display on */
    return 1;
}
