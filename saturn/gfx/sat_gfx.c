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
#include "vdp1_profile.h"

extern unsigned char *PAGE[256];
extern unsigned char RAMB[];
#if SAT_GFX_FIT == 3
volatile int sat_fit_scale;
#endif

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
#define UNC32(v) (*(volatile u32 *)&(v))
#define UNC_PTR(type, p) ((volatile type *)(p))
/* Optional host timing seam for the actual presentation state machine. */
extern unsigned long sat_gfx_host_ticks(void);
#define GFX_TICKS() sat_gfx_host_ticks()
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
#define UNC32(v) (*(volatile u32 *)((u32)&(v) | 0x20000000UL))
#define UNC_PTR(type, p) ((volatile type *)((unsigned long)(p) | 0x20000000UL))
#define GFX_TICKS() (((u32)*(volatile u8 *)0xfffffe12UL << 8) | *(volatile u8 *)0xfffffe13UL)
#define be16(p) (*(const u16 *)(const void *)(p))
#define be32(p) (*(const u32 *)(const void *)(p))
#define put16(d, v) (*(volatile u16 *)(void *)(d) = (u16)(v))
#define put32(d, v) (*(volatile u32 *)(void *)(d) = (u32)(v))
#define get32(d) (*(const volatile u32 *)(const void *)(d))
#endif

#if !defined(SAT_GFX_HOST) || defined(SAT_GFX_SYNC_TEST) || defined(SAT_VLOG)
#define SAT_GFX_HAVE_SYNC
#endif

/* Game state, by address. */
#define RAM16(a) be16(RAMB + ((a) - 0xff0000UL))
/* Screen adjust (home options): the whole picture moves by this many pixels; layers by their scroll, sprites by the VDP1 local origin. */
#ifdef SAT_HOME
int sat_gfx_nudge_x, sat_gfx_nudge_y;
#define NUDGE_X sat_gfx_nudge_x
#define NUDGE_Y sat_gfx_nudge_y
#else
#define NUDGE_X 0
#define NUDGE_Y 0
#endif
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
#define BLANK_INDEX 0xffffffUL /* what pack_find returns for an empty tile */
#define KEY_SHIFT(s) ((s) == sections ? 16 : 14) /* sprite words are key << 16 | index, for more than 16K tiles; scroll keys need 18 bits */

typedef struct
{
    u32 count;
    int shift; /* key >> shift picks an index bucket */
    const u8 *keys; /* u32: key << KEY_SHIFT | payload index, ascending; an index of all ones marks a tile with no visible pen */
    const u8 *data;
    const u8 *spill; /* payload indexes from split on live in other stretches of the cart: count, then (first index, offset from the pack) pairs, ascending */
    u32 split;
} Section;

/* A set of VRAM slots holding pack tiles; a slot not drawn this frame can be taken. */
#define HASH_SIZE 1024   /* sprite tiles; the layer caches hold fewer slots and take smaller tables (high work RAM is the short resource) */
#ifndef HASH_SIZE_S1
#define HASH_SIZE_S1 512
#define HASH_SIZE_S2 512
#define HASH_SIZE_S3 256
#endif
typedef struct { u32 key; u16 stamp, next; } SlotRec;
typedef struct
{
    u8 *vram;
    u32 slot_bytes;
    u16 capacity;
    u16 hand;
    u16 first; /* slots below this are reserved */
    u16 used;  /* slots stamped this frame */
    int section;
    SlotRec *slots;   /* key, stamp and chain link of a slot in one 8 byte record: a lookup touches one cache line a node, not three */
    u16 *head;
    u16 hmask; /* hash table size - 1 */
    u32 memo_key[2]; /* last answer per column parity this frame: runs of one tile, mostly blank, skip the lookup */
    u16 memo_slot[2];
#ifdef SAT_VLOG
    u8 memo_cause[2];
#endif
} Cache;

#define NOSLOT 0xffffU
#define NOKEY 0xffffffffUL

#ifdef SAT_PROF
/* Test flag: the tile funnel of the frame with the most VDP1 commands, live banks, the keys the pack lacks. */
typedef struct
{
    u32 tiles, offscreen, empty, commands, runs, banks, banks_peak, peak_frame, missing_n, missing_key[32];
} SatGfxCensus;
SatGfxCensus sat_gfx_census;
static u32 c_tiles, c_off, c_empty, c_runs, c_bankmask[4];
#define CENSUS(x) x
static void census_bank(u32 b) { c_bankmask[b >> 5] |= 1UL << (b & 31); }
static u32 census_count(void)
{
    u32 n = 0, i, m;
    for (i = 0; i < 4; i++) for (m = c_bankmask[i]; m; m &= m - 1) n++;
    return n;
}
#else
#define CENSUS(x)
#endif

static Section sections[4];
static u16 stamp;
static u16 prev_stamp;   /* the frame before: its sprite slots may still be read by a plot an emulator renders late */
/* Two command tables, so the one VDP1 plots is never the one the slave writes: 0x20 to 0x8000 and 0x8020 to 0x10000, each local
   coordinates, clear polygon, sprites, end. The system clip at 0 jumps to the table of the plot being started. */
static u32 table_base;
#define TABLE_B 0x8000UL

static SlotRec spr_slots[SAT_GFX_SPRITE_SLOTS] __attribute__((aligned(8)));
static u16 spr_head[HASH_SIZE];
static SlotRec s1_slots[SAT_GFX_S1_SLOTS] __attribute__((aligned(8)));
static u16 s1_head[HASH_SIZE_S1];
static SlotRec s2_slots[SAT_GFX_S2_SLOTS] __attribute__((aligned(8)));
static u16 s2_head[HASH_SIZE_S2];
static SlotRec s3_slots[SAT_GFX_S3_SLOTS] __attribute__((aligned(8)));
static u16 s3_head[HASH_SIZE_S3];
static Cache spr_cache, s1_cache, s2_cache, s3_cache;
#if SAT_GFX_SLOT_HINTS
/* Indexed by the visible tile's position in the preceding build, including
 * blank/refused tiles. Object insertion, animation and eviction can make a
 * hint wrong; validating the live key makes those cases ordinary misses.
 * Only the slave reads or writes these hints and the sprite cache. */
static u16 sprite_slot_hints[SAT_GFX_SLOT_HINTS];
#ifdef SAT_GFX_SLOT_HINT_STATS
SatGfxSlotHintStats sat_gfx_slot_hint_stats;
#define HINT_STAT(x) x
#else
#define HINT_STAT(x)
#endif
#endif
static u16 cram_shadow[2048];
static u16 back_shadow;

SatGfxStats sat_gfx_stats;

static void cache_setup(Cache *c, u8 *vram, u32 slot_bytes, u16 capacity, u16 first, int section,
                        SlotRec *slots, u16 *head, u32 hsize)
{
    u32 i;
    c->vram = vram; c->slot_bytes = slot_bytes; c->capacity = capacity; c->hand = first; c->first = first; c->used = 0;
    c->memo_key[0] = c->memo_key[1] = NOKEY; c->memo_slot[0] = c->memo_slot[1] = NOSLOT;
    c->section = section; c->slots = slots; c->head = head; c->hmask = (u16)(hsize - 1);
    for (i = 0; i < capacity; i++) { slots[i].key = NOKEY; slots[i].stamp = 0; slots[i].next = NOSLOT; }
    for (i = 0; i < hsize; i++) head[i] = NOSLOT;
}

static const u8 *pack_start;

/* A coarse index in RAM over each section's keys on the cart: the search reads a handful of keys over the slow bus, not fourteen. */
#define INDEX_BUCKETS 256
static u16 pack_index[4][INDEX_BUCKETS + 1]
#ifndef SAT_GFX_HOST
    __attribute__((section(".lwgfx")))
#endif
    ;

static void index_section(Section *s, int which)
{
    u16 *index = pack_index[which];
    u32 top = s->count ? be32(s->keys + (s->count - 1) * 4) >> KEY_SHIFT(s) : 0, i, b = 0;
    s->shift = 0;
    while ((top >> s->shift) >= INDEX_BUCKETS) s->shift++;
    for (i = 0; i < s->count; i++)
    {
        u32 k = (be32(s->keys + i * 4) >> KEY_SHIFT(s)) >> s->shift;
        while (b <= k) index[b++] = (u16)i;
    }
    while (b <= INDEX_BUCKETS) index[b++] = (u16)s->count;
}

/* Payload index of a key, BLANK_INDEX for an empty tile, or -1 when the pack lacks it. */
static long pack_find(const Section *s, u32 key)
{
    u32 bucket = key >> s->shift;
    const u16 *index = pack_index[s - sections];
    long lo, hi;
    int ks = KEY_SHIFT(s);
    if (bucket >= INDEX_BUCKETS) return -1;
    lo = index[bucket]; hi = (long)index[bucket + 1] - 1;
    while (lo <= hi)
    {
        long mid = (lo + hi) >> 1;
        u32 v = be32(s->keys + (u32)mid * 4);
        u32 k = v >> ks;
        if (k == key) { u32 i = v & ((1UL << ks) - 1); return i == (1UL << ks) - 1 ? (long)BLANK_INDEX : (long)i; }
        if (k < key) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}

#ifdef SAT_PROF
/* Test flag: costs on the drawing side over the window. Upload time, and sprite stage time on frames with no upload, which leaves lookups and command writes. */
typedef struct { u32 frames, upload_ticks, uploads, layer_uploads, missing, clean_frames, clean_ticks, clean_commands, dirty_ticks, commands, peak_upload_ticks, peak_total, peak_vblank, peak_stage[6], peak_uploads, peak_layer_uploads, peak_commands, verify_checked, verify_bad; } SatSpeed;
SatSpeed sat_speed;
static int speed_on;
extern u32 sat_vblanks_now(void);
#define FRT_NOW() (((u32)*(volatile u8 *)0xfffffe12UL << 8) | *(volatile u8 *)0xfffffe13UL)
#endif

#ifdef SAT_VDP1_PROFILE
/* Measurement storage is entirely absent in a normal image. With depth 16 the
   two exported rings take 1984 bytes; current-row and snapshot state add 132.
   This diagnostic build still has to pass the normal linker memory limits. */
#ifdef SAT_GFX_HOST
#define VP_RAM
#else
#define VP_RAM __attribute__((section(".lwgfx"), aligned(4)))
#endif
volatile unsigned int sat_vdp1_plots[SAT_VDP1_PROFILE_DEPTH][VP_PLOT_WORDS] VP_RAM;
volatile unsigned int sat_vdp1_frames[SAT_VDP1_PROFILE_DEPTH][VF_FRAME_WORDS] VP_RAM;
static unsigned int vp_current[VP_PLOT_WORDS] VP_RAM;
static unsigned int vp_attempt, vp_active, vp_sprite_start, vp_layer_start;
extern u32 sat_vblanks_now(void);
#define VP(x) x
static unsigned int vp_elapsed(unsigned int start)
{
    return (unsigned int)((GFX_TICKS() - start) & 0xffffUL);
}
static void vp_finish(unsigned int flags)
{
    unsigned int i, id = vp_current[VP_ATTEMPT];
    volatile unsigned int *out = UNC_PTR(unsigned int, sat_vdp1_plots[id & (SAT_VDP1_PROFILE_DEPTH - 1)]);
    vp_current[VP_FLAGS] |= flags;
    vp_current[VP_CPU_TICKS] = vp_elapsed(vp_current[VP_CPU_TICKS]);
    out[0] = 0;
    for (i = 1; i < VP_PLOT_WORDS; i++) out[i] = vp_current[i];
    out[0] = id;
    vp_active = 0;
}
/* Bounding-box area clipped to the system clip, not opaque pixels or a fill
   time estimate. Transparent texels and overdraw still cost the VDP1 work. */
static void vp_sprite(int x, int y, int w, int h, unsigned int pmod,
                      unsigned int source_texels)
{
    int right = x + w, bottom = y + h;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (right > SAT_GFX_SCREEN_W) right = SAT_GFX_SCREEN_W;
    if (bottom > SAT_GFX_SCREEN_H) bottom = SAT_GFX_SCREEN_H;
    if (right > x && bottom > y)
        vp_current[VP_SPRITE_PIXELS] += (unsigned int)((right - x) * (bottom - y));
    vp_current[VP_SOURCE_TEXELS] += source_texels;
    vp_current[VP_COLOUR_MODES] |= 1u << ((pmod >> 3) & 7u);
    if ((pmod & 3u) == 3u) vp_current[VP_HALF_TRANSPARENT]++;
}
#else
#define VP(x)
#endif

static void vram_copy(u8 *dest, const u8 *src, u32 bytes)
{
    u32 i;
    VP(unsigned int vp_upload_start = (unsigned int)GFX_TICKS();)
#ifdef SAT_PROF
    u32 t0 = FRT_NOW();
#endif
#if defined(SAT_TILE_DMA) && !defined(SAT_GFX_HOST)
    /* Experiment: SCU DMA level 0, direct mode, longs read, words written, waiting for the end. */
    {
        volatile u32 *scu = (volatile u32 *)0x25fe0000UL;
        scu[0] = (u32)src & 0x0fffffffUL; scu[1] = (u32)dest & 0x0fffffffUL; scu[2] = bytes; scu[3] = 0x101; scu[5] = 7; scu[4] = 0x101;
        while (*(volatile u32 *)0x25fe007cUL & 0x10) ;
    }
    (void)i;
#else
#ifdef SAT_GFX_HOST
    for (i = 0; i < bytes; i++) dest[i] = src[i];
#else
    volatile u32 *d = (volatile u32 *)(void *)dest;
    const u32 *s = (const u32 *)(const void *)src;
    for (i = 0; i < bytes / 4; i++) d[i] = s[i];
#endif
#endif
    VP(if (vp_active && (u32)dest >= (u32)(VDP1_VRAM + TEX_BASE) &&
          (u32)dest < (u32)(VDP1_VRAM + 0x80000UL)) {
        vp_current[VP_UPLOAD_TICKS] += vp_elapsed(vp_upload_start);
        vp_current[VP_UPLOAD_BYTES] += (unsigned int)bytes;
    })
#ifdef SAT_PROF
    if (speed_on) { u32 t = FRT_NOW() - t0; sat_speed.upload_ticks += t; if (t > sat_speed.peak_upload_ticks) sat_speed.peak_upload_ticks = t; }
#endif
}

#ifdef SAT_READOUT
extern u32 sat_pad_raw;
static u32 readout_pad(void) { return *UNC_PTR(u32, &sat_pad_raw); }
#endif
#define HASH(c, k) (((k) ^ ((k) >> 10)) & (c)->hmask)
/* The per-frame snapshot: everything drawing reads from the game, copied once by the game's CPU. The two sides never share a structure: the
   master owns game RAM, object RAM and graphics RAM; the drawing side owns VDP1, VDP2, CRAM, the caches and the shadows. */
#define S1_ROWS (SAT_GFX_SCREEN_H / 8 + 1)
#if SAT_GFX_FIT
#define S1_COLS (384 / 8 + 1)
#define S1_REG_CROP 16 /* scroll 1 text never scales: it stays 1:1 over the 16 pixel crop */
#define S1_READ_X 0
#else
#define S1_COLS (SAT_GFX_SCREEN_W / 8 + 1)
#define S1_REG_CROP SAT_GFX_CROP_X
#define S1_READ_X SAT_GFX_CROP_X
#endif
#define S2_ROWS (SAT_GFX_SCREEN_H / 16 + 1)
#define S2_COLS (SAT_GFX_SRC_W / 16 + 1)
#define S3_ROWS (SAT_GFX_SCREEN_H / 32 + 1)
#define S3_COLS (SAT_GFX_SRC_W / 32 + 1)
#define MAX_OBJECTS 0x400
typedef struct
{
    u16 layers, priority, pal_pages, back_valid, back, row_active, objects, pad, whole;   /* pad: unused here (a pack generation in builds that add one). whole: scroll 2 read as a whole page (row scroll on), taken before a menu clears row_active */
    u16 s1x, s1y, s2x, s2y, s3x, s3y;
    u16 row[SAT_GFX_SCREEN_H];
    u8 palette[SAT_GFX_PAGES][0x400];
    u8 obj[MAX_OBJECTS * 8];
    u32 pal_sum[SAT_GFX_PAGES]; /* change detection: every palette word */
#ifdef SAT_VDP1_PROFILE
    unsigned int profile_vblank, profile_stage_chars, profile_snapshot_ticks, profile_handoff_tick;
#endif
#ifdef SAT_HOME
    u16 home; /* menu text on its own layer (NBG3) */
#endif
    /* Second half of the handoff (frame chain lane): the layer cells and their sums are written by the master after it has woken the slave, so
       nothing of the first half shares a cache line with them (group aligned to 16, structure size a multiple of 16) and the slave reads them
       only once snap_layers_ready is set. */
    u32 s1[S1_ROWS * S1_COLS] __attribute__((aligned(16)));
    u32 s2[S2_ROWS * 64], s3[S3_ROWS * (384 / 32 + 1)]; /* code << 16 | attribute, visible cells only */
    u32 s1_sum, s2_sum, s3_sum; /* change detection: position and every visible word */
    u16 hud_flush;
#ifdef SAT_VDP1_PROFILE
    unsigned int profile_layer_ticks;
#endif
} Snapshot __attribute__((aligned(16)));
#define SNAP_BARRIER() __asm__ volatile ("" : : : "memory")
static u32 snap_layers_ready;   /* master writes 0 before the handoff and 1 when the layer half is complete; slave reads it uncached */
#ifndef SAT_LAYERS_WAIT_SPINS
#define SAT_LAYERS_WAIT_SPINS 90000UL   /* about two frames of uncached reads: a stalled master cannot hold the slave for ever */
#endif
#if defined(SAT_VLOG) || defined(SAT_VDP1_PROFILE) || defined(SAT_GFX_HOST) || defined(SAT_LAYERS_COUNT)
u32 sat_gfx_layers_late;     /* diagnostic: pictures whose slave reached the layers before the master had finished them */
u32 sat_gfx_layers_timeout;  /* diagnostic: waits abandoned at SAT_LAYERS_WAIT_SPINS (must stay 0) */
#endif

/* Polynomial, not rotate and xor: a palette fade changes every long by one mask, and with 256 longs a rotate cancels it out. */
#define MIX(sum, w) ((((sum) << 5) + (sum)) + (w))

#ifdef SAT_GFX_HOST
static Snapshot snap;
#else
static Snapshot snap __attribute__((section(".lwgfx"), aligned(16)));
#endif

#ifdef SAT_VDP1_PROFILE
static void vp_begin(void)
{
    unsigned int i;
    for (i = 0; i < VP_PLOT_WORDS; i++) vp_current[i] = 0;
    if (++vp_attempt == 0) vp_attempt = 1;
    vp_current[VP_ATTEMPT] = vp_attempt;
    vp_current[VP_SOURCE_VBLANK] = snap.profile_vblank;
    vp_current[VP_STAGE_CHARACTERS] = snap.profile_stage_chars;
    vp_current[VP_SNAPSHOT_TICKS] = snap.profile_snapshot_ticks;
    vp_current[VP_HANDOFF_TICK] = snap.profile_handoff_tick;
    vp_current[VP_RASTER_UPPER_TICKS] = 0xffffffffu;
    vp_current[VP_CPU_TICKS] = (unsigned int)GFX_TICKS(); /* start, replaced by elapsed duration at commit */
    vp_active = 1;
}
#endif

#ifdef SAT_GFX_HOST
#define put32_ram(p, v) put32((p), (v))
#else
#define put32_ram(p, v) (*(u32 *)(void *)(p) = (v))
#endif

/* Blank tiles fill most layers and never get a slot, so without this each one means a binary search of the pack on the cart, every frame. */
#define BLANK_WAYS 2048
#ifdef SAT_GFX_HOST
static u32 blank_seen[BLANK_WAYS];
#else
static u32 blank_seen[BLANK_WAYS] __attribute__((section(".lwgfx")));
#endif

#ifdef SAT_VLOG
/* Diagnostic (lane avp-vanish): why the last lookup returned what it did. 0 slot, 1 blank tile, 2 key not in the pack, 3 no free slot. */
static u8 vl_cause;
#define VL_CAUSE(c) (vl_cause = (c))
#define BLANK_MISS_BIT 0x80000000UL
#else
#define VL_CAUSE(c)
#define BLANK_MISS_BIT 0
#endif
/* Slot holding a tile, uploading it on a miss. NOSLOT for a blank, missing or refused tile. */
static u16 cache_find(Cache *c, u32 key, unsigned long *refused)
{
    u32 h = HASH(c, key);
    u16 s = c->head[h];
    u16 n = NOSLOT;
    u32 scan;
    long idx;
    while (s != NOSLOT)
    {
        SlotRec *r = &c->slots[s];
        if (r->key == key)
        {
            if (r->stamp != stamp) { r->stamp = stamp; c->used++; }
            VL_CAUSE(0);
            return s;
        }
        s = r->next;
    }
    {
        u32 tag = (key << 2) | (u32)c->section, way = (tag ^ (tag >> 11)) & (BLANK_WAYS - 1);
#ifdef SAT_VLOG
        if ((blank_seen[way] & ~BLANK_MISS_BIT) == tag) { VL_CAUSE(blank_seen[way] & BLANK_MISS_BIT ? 2 : 1); return NOSLOT; }
#else
        if (blank_seen[way] == tag) return NOSLOT;
#endif
#ifdef SAT_KEYLOG
        {   /* Test build only: every key the running game asks for, as bits in spare SCSP RAM, read back over MCP to size the tile pack by real play. */
            static const u32 base[4] = { 0x25A70000UL, 0x25A78000UL, 0x25A7C000UL, 0x25A7E000UL };
            *(volatile u8 *)(base[c->section] + (key >> 3)) |= (u8)(1u << (key & 7));
        }
#endif
        idx = pack_find(&sections[c->section], key);
        if (idx < 0)
        {
            sat_gfx_stats.missing++; blank_seen[way] = tag | BLANK_MISS_BIT; VL_CAUSE(2);
            CENSUS(if (sat_gfx_census.missing_n < 32) sat_gfx_census.missing_key[sat_gfx_census.missing_n++] = key | ((u32)c->section << 28);)
            return NOSLOT;
        }
        if ((u32)idx == BLANK_INDEX) { blank_seen[way] = tag; VL_CAUSE(1); return NOSLOT; }
    }
    for (scan = c->first; scan < c->capacity; scan++)
    {
        u16 t = c->hand;
        c->hand = (u16)(t + 1U >= c->capacity ? c->first : t + 1U);
        if (c->slots[t].stamp != stamp && !(c->section == SEC_SPRITE && prev_stamp && c->slots[t].stamp == prev_stamp)) { n = t; break; }
    }
    if (n == NOSLOT) { (*refused)++; VL_CAUSE(3); return NOSLOT; }
    if (c->slots[n].key != NOKEY)
    {
        u16 *link = &c->head[HASH(c, c->slots[n].key)];
        while (*link != n) link = &c->slots[*link].next;
        *link = c->slots[n].next;
    }
    c->slots[n].key = key; c->slots[n].stamp = stamp; c->used++;
    c->slots[n].next = c->head[h]; c->head[h] = n;
    {
        const Section *sec = &sections[c->section];
        const u8 *from = sec->data + (u32)idx * c->slot_bytes;
        if ((u32)idx >= sec->split)
        {
            u32 k = be32(sec->spill);
            while (k-- > 0)
            {
                u32 first = be32(sec->spill + 4 + k * 8);
                if ((u32)idx >= first) { from = pack_start + be32(sec->spill + 8 + k * 8) + ((u32)idx - first) * c->slot_bytes; break; }
            }
        }
        vram_copy(c->vram + (u32)n * c->slot_bytes, from, c->slot_bytes);
    }
    if (c == &spr_cache) sat_gfx_stats.uploads++; else sat_gfx_stats.layer_uploads++;
    VL_CAUSE(0);
    return n;
}

static u16 cache_get(Cache *c, u32 key, unsigned long *refused)
{
    u32 way = key & 1;
    if (c->memo_key[way] != key)
    {
        c->memo_key[way] = key;
        c->memo_slot[way] = cache_find(c, key, refused);
#ifdef SAT_VLOG
        c->memo_cause[way] = vl_cause;
    }
    vl_cause = c->memo_cause[way];
#else
    }
#endif
    return c->memo_slot[way];
}

#if SAT_GFX_SLOT_HINTS
static u16 sprite_lookup(u32 key, unsigned int position)
{
    u16 slot;
    HINT_STAT(sat_gfx_slot_hint_stats.queries++;)
    if (position < SAT_GFX_SLOT_HINTS)
    {
        slot = sprite_slot_hints[position];
        if (slot >= spr_cache.first && slot < spr_cache.capacity)
        {
            SlotRec *r = &spr_cache.slots[slot];
            if (r->key == key)
            {
                u32 way = key & 1;
                if (r->stamp != stamp) { r->stamp = stamp; spr_cache.used++; }
                /* Preserve the ordinary two-entry memo and diagnostic cause.
                 * The usual abort path also restores this slot's live stamp. */
                spr_cache.memo_key[way] = key;
                spr_cache.memo_slot[way] = slot;
#ifdef SAT_VLOG
                spr_cache.memo_cause[way] = 0;
#endif
                VL_CAUSE(0);
                HINT_STAT(sat_gfx_slot_hint_stats.hits++;)
                return slot;
            }
        }
        HINT_STAT(sat_gfx_slot_hint_stats.fallbacks++;)
        slot = cache_get(&spr_cache, key, &sat_gfx_stats.refused_sprite);
        sprite_slot_hints[position] = slot;
        return slot;
    }
    HINT_STAT(sat_gfx_slot_hint_stats.beyond_limit++;)
    return cache_get(&spr_cache, key, &sat_gfx_stats.refused_sprite);
}
#endif

static void cache_frame(Cache *c)
{
    c->used = 0;
    c->memo_key[0] = c->memo_key[1] = NOKEY;
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

/* What the chips already show: a layer whose words and position are unchanged does no lookups, so its cache sees no upload and can't lose a slot. */
static u32 drawn_pal[SAT_GFX_PAGES], drawn_s1, drawn_s2, drawn_s3;
static int drawn_valid;

static void update_palette(void)
{
    int page;
    u16 written = 0;
    for (page = 0; page < SAT_GFX_PAGES; page++)
    {
        const u8 *src = snap.palette[page];
        int i;
        if (!((snap.pal_pages >> page) & 1)) continue;
        if (drawn_valid && snap.pal_sum[page] == drawn_pal[page]) continue;
        drawn_pal[page] = snap.pal_sum[page];
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
    if (snap.back_valid)
    {
        u16 c = snap.back;
        if (c != back_shadow)
        {
            back_shadow = c;
            put16(VDP2_VRAM + BACKCOL, sat_gfx_colour(c));
        }
    }
    sat_gfx_stats.colours_written = written;
}

/* Layer maps: only the words the picture can show are looked at, and only changed words are written. The comparison is against shadows in
   work RAM: a read from VDP2 VRAM stalls the CPU, and these loops touch over 2000 words a frame. */
#ifdef SAT_GFX_HOST
#define LOW_RAM
#else
#define LOW_RAM __attribute__((section(".lwgfx")))
#endif
static u32 sh_s1[64 * 64] LOW_RAM, sh_s2[64 * 64] LOW_RAM, sh_s3[64 * 64] LOW_RAM, sh_row[SAT_GFX_SCREEN_H] LOW_RAM;

static void write_name(u8 *addr, u32 name, u32 *shadow)
{
    if (*shadow != name)
    {
        *shadow = name;
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

#ifdef SAT_HOME
extern volatile int sat_home_mode;
extern char sat_home_text[28][44];
#ifndef SAT_HOME_RATIO
#define SAT_HOME_RATIO 11   /* logo kept at about 0.45 of its brightness, as MSHvSF OPTION MODE keeps its own (0.47); measured from stills at 2, 5, 8 (lane-home overlay/dark_sheet.png) */
#endif
volatile unsigned short sat_home_ratio = SAT_HOME_RATIO; /* panel colour calculation ratio (CCRNB NBG3), 0 to 31 */
static const u8 home_font[58 * 32] __attribute__((aligned(4))) = {
#include "home_font.inc"
};
static const u8 home_pal[64] __attribute__((aligned(2))) = {
#include "home_pal.inc"
};
#endif
#define HUD_ROWS_TOP 5   /* rows 0..4: names, health bars, the enemy label and its bar (row 4 was centre-cropped, 16 px off the rest) */
#define HUD_ROWS_BOT 26
static void draw_scroll1(u16 sx, u16 sy)
{
    const u32 *cell = snap.s1;
    u32 x0 = (u32)sx + CPS_LEFT + S1_REG_CROP, y0 = (u32)sy + CPS_TOP;
    u32 row, col;
    for (row = 0; row <= SAT_GFX_SCREEN_H / 8; row++)
        for (col = 0; col <= SAT_GFX_SCREEN_W / 8; col++)
        {
            u32 c = ((x0 >> 3) + col) & 63, r = ((y0 >> 3) + row) & 63;
#if SAT_GFX_FIT
            /* The arcade's 48 columns on 44: the HUD rows lose four empty columns at the middle, so it sits flush at both edges; other rows are the centre crop. */
            u32 src = (snap.hud_flush && (row < HUD_ROWS_TOP || row >= HUD_ROWS_BOT)) ? (col < 22 ? col : col + 4) : col + 2;
            u32 c_src = (((x0 - S1_REG_CROP) >> 3) + src) & 63;
            u32 idx = (r & 0x1f) + (c_src << 5) + ((r & 0x20) << 6);
            u32 word = cell[row * S1_COLS + src];
#else
            u32 idx = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6);
            u32 word = *cell++;
#endif
            u16 code = (u16)(word >> 16), attr = (u16)word;
            /* Odd columns read the right half of the 16 pixel row. */
            u16 slot = cache_get(&s1_cache, ((u32)code << 1) | ((idx >> 5) & 1), &sat_gfx_stats.refused_layer);
            u32 name = CLEAR_NAME;
            if (slot != NOSLOT) name = name_of(attr, 1, (CELL_S1 + (u32)slot * 32) >> 5);
#ifdef SAT_HOME
            if (snap.home >= 3 && row >= 19) name = CLEAR_NAME;   /* the game's start and credits lines under the menus; its logo stays */
#endif
            write_name(VDP2_VRAM + MAP_S1 + (r * 64 + c) * 4, name, &sh_s1[r * 64 + c]);
        }
}

#ifdef SAT_HOME
/* The menu layer: NBG3, one page of 1-word names at MAP_HOME (rows 0 to 27 used; the rest of the page is never shown), font and panel cells after it.
   Palette supplement 3 and character supplement 3 (reg 0x36) make name bank 14/15 = banks 62/63 (scroll 1 page banks 30/31) and cells 0xc00 up. */
#define MAP_HOME 0x1e000UL
static u16 sh_home[28 * 44] LOW_RAM;
extern char sat_home_shown[28][44];
extern volatile u32 sat_home_seq;
static void draw_home(int fresh)
{
    u32 row, col;
    if (*(volatile u32 *)((unsigned long)&sat_home_seq | 0x20000000UL) & 1) return;   /* the master is copying a new screen: next frame */
    for (row = 0; row < 28; row++)
        for (col = 0; col < 44; col++)
        {
            u32 ch = *(volatile u8 *)((unsigned long)&sat_home_shown[row][col] | 0x20000000UL);
            u16 name = 0;                                                       /* cell 0xc00: clear */
            if (ch == 1) name = (u16)(14u << 12 | ((SAT_GFX_HOME_FONT + 58) & 0x3ff));   /* the translucent panel */
            else if ((ch >= 2 && ch <= 0x20) || (ch >= 0x81 && ch <= 0xa0))   /* a large letter's half (sat_home_big) */
                name = (u16)(15u << 12 | ((SAT_GFX_HOME_FONT + 59 + (ch <= 0x20 ? ch - 2 : ch - 0x81 + 31)) & 0x3ff));
            else if (ch & 0x7f) name = (u16)(((ch & 0x80) ? 15u : 14u) << 12 | ((SAT_GFX_HOME_FONT + (ch & 0x7f) - 33) & 0x3ff));
            if (fresh || sh_home[row * 44 + col] != name)
            {
                sh_home[row * 44 + col] = name;
                put16(VDP2_VRAM + MAP_HOME + (row * 64 + col) * 2, name);
            }
        }
}
#endif

/* A 2x2 page plane of 16 pixel characters. */
static u8 *s2_name(u32 r, u32 c)
{
    return VDP2_VRAM + MAP_S2 + (((r >> 5) * 2 + (c >> 5)) * 0x1000) + (((r & 31) * 32 + (c & 31)) * 4);
}

static void draw_scroll2(u16 sx, u16 sy, int full_row)
{
    const u32 *cell = snap.s2;
    u32 x0 = (u32)sx + CPS_LEFT + SAT_GFX_CROP_X, y0 = (u32)sy + CPS_TOP;
    u32 row, col, cols = full_row ? 64 : SAT_GFX_SRC_W / 16 + 1;
    for (row = 0; row <= SAT_GFX_SCREEN_H / 16; row++)
        for (col = 0; col < cols; col++)
        {
            u32 c = ((full_row ? 0 : x0 >> 4) + col) & 63, r = ((y0 >> 4) + row) & 63;
            u32 word = *cell++;
            u16 code = (u16)(word >> 16), attr = (u16)word;
            u16 slot = cache_get(&s2_cache, code, &sat_gfx_stats.refused_layer);
            u32 name = CLEAR_NAME;
            if (slot != NOSLOT) name = name_of(attr, 2, (CELL_S2 + (u32)slot * 128) >> 5);
            write_name(s2_name(r, c), name, &sh_s2[r * 64 + c]);
        }
}

/* Four planes of 2x2 pages: 128 x 128 sixteen pixel characters, each CPS tile four of them. */
static u8 *s3_name(u32 r, u32 c)
{
    u32 plane = (r >> 6) * 2 + (c >> 6);
    u32 rr = r & 63, cc = c & 63;
    return VDP2_VRAM + MAP_S3 + plane * 0x4000 + ((rr >> 5) * 2 + (cc >> 5)) * 0x1000 + ((rr & 31) * 32 + (cc & 31)) * 4;
}

static void draw_scroll3(u16 sx, u16 sy)
{
    const u32 *cell = snap.s3;
    u32 x0 = (u32)sx + CPS_LEFT + SAT_GFX_CROP_X, y0 = (u32)sy + CPS_TOP;
    u32 row, col;
    for (row = 0; row <= SAT_GFX_SCREEN_H / 32; row++)
        for (col = 0; col <= SAT_GFX_SRC_W / 32; col++)
        {
            u32 c = ((x0 >> 5) + col) & 63, r = ((y0 >> 5) + row) & 63;
            u32 word = *cell++;
            u16 code = (u16)((word >> 16) & 0x3fff), attr = (u16)word;
            u16 slot = cache_get(&s3_cache, code, &sat_gfx_stats.refused_layer);
            u32 sub, id = ((u32)attr << 16) | slot;
            if (sh_s3[r * 64 + c] == id) continue;
            sh_s3[r * 64 + c] = id;
            for (sub = 0; sub < 4; sub++)
            {
                u32 name = CLEAR_NAME;
                if (slot != NOSLOT)
                {
                    /* A flipped tile also swaps its characters. */
                    u32 use = sub ^ ((attr & 0x20) ? 1U : 0U) ^ ((attr & 0x40) ? 2U : 0U);
                    name = name_of(attr, 3, (CELL_S3 + (u32)slot * 512 + use * 128) >> 5);
                }
                put32(s3_name(r * 2 + (sub >> 1), c * 2 + (sub & 1)), name);
                sat_gfx_stats.layer_writes++;
            }
        }
}

/* Row scroll: only offsets are stored; VDP2 adds them to the layer's scroll. */
static void update_rowscroll(void)
{
    u32 line;
    for (line = 0; line < SAT_GFX_SCREEN_H; line++)
        write_name(VDP2_VRAM + ROWTAB + line * 4, (u32)snap.row[line] << 16, &sh_row[line]);
}

static u16 prinb_last; /* VDP2 registers are write-only: what update_priority last put in PRINB */
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
    prinb_last = prin[0];
    for (p = 0; p < 8; p++)
    {
        int level = 7, below = -1;
        for (i = 0; i < n; i++) if (p <= lp[i]) below = i;
        if (below >= 0)
        {
            level = 1 + 2 * below;
            for (i = 0; i < below; i++) if (p > lp[i]) { sat_gfx_stats.nonmonotone++; break; }
        }
#ifdef SAT_HOME
        if (snap.home && level > 6) level = 6;   /* the menu layer (NBG3, 7) in front of sprites too; a sprite wins ties, so 7 would hide it */
#endif
        s[p] = (u16)level;
    }
    VDP2R(0xf0) = (u16)(s[0] | (s[1] << 8));
    VDP2R(0xf2) = (u16)(s[2] | (s[3] << 8));
    VDP2R(0xf4) = (u16)(s[4] | (s[5] << 8));
    VDP2R(0xf6) = (u16)(s[6] | (s[7] << 8));
}

#if SAT_GFX_FIT != 1
static void put_sprite(u8 *cmd, u16 flip, u16 colr, u32 tex, int x, int y)
{
#ifdef SAT_READOUT
    u16 size = (u16)(readout_pad() & 0x0010 ? 0x0210 : 0x0101);
#else
    u16 size = 0x0210;
#endif
    VP(vp_sprite(x + NUDGE_X, y + NUDGE_Y, ((size >> 8) & 63) * 8, size & 255, 0x0880,
                 (unsigned int)(((size >> 8) & 63) * 8 * (size & 255)));)
    /* Long writes: four fewer bus writes per command than sixteen-bit stores; the link word is never written elsewhere and stays 0 (jump next). */
    put32(cmd + 0, (u32)flip << 16);                          /* normal sprite, jump next */
    put32(cmd + 4, (0x0880UL << 16) | colr);                  /* pre-clip off, end codes off, pen 0 clear, 16 colour bank */
    put32(cmd + 8, ((u32)(u16)(tex >> 3) << 16) | size);      /* 16 x 16; SAT_READOUT pad Z selects the existing 8 x 1 fill probe */
    put32(cmd + 12, ((u32)(u16)x << 16) | (u16)y);
}
#endif

#if SAT_GFX_FIT == 1 || SAT_GFX_FIT == 3
/* sx + 16 in, source column out at 11/12. Each tile its two end columns, so neighbours meet. */
static u16 fit_x[417];
static void put_sprite_fit(u8 *cmd, u16 flip, u16 colr, u32 tex, int x, int y)
{
    int a = (int)fit_x[x + 16] - 14, b = (int)fit_x[x + 32] - 15; /* fit_x[16] = 14 is screen 0 */
    VP(vp_sprite(a + NUDGE_X, y + NUDGE_Y, b - a + 1, 16, 0x0880, 256);)
    /* Long writes (five bus writes a command, was nine); the link word stays 0 (jump next). */
    put32(cmd + 0, (u32)(u16)(flip | 1) << 16);                /* scaled sprite, two corners */
    put32(cmd + 4, (0x0880UL << 16) | colr);
    put32(cmd + 8, ((u32)(u16)(tex >> 3) << 16) | 0x0210U);
    put32(cmd + 12, ((u32)(u16)a << 16) | (u16)y);
    put32(cmd + 20, ((u32)(u16)b << 16) | (u16)(y + 15));
}
#endif
#ifdef SAT_READOUT
/* Frame-cost bars for a real console, where no debugger reads the timers: 8 pixels per ms from the left, top bar game on the master, second bar drawing on the slave, white tick at 16.7 ms.
   Values come from the kernel through the uncached alias. Physical numbers are read from a capture of the screen. */
extern volatile unsigned long sat_readout[3];
static u8 *bar(u8 *cmd, int w, int y, u16 rgb)
{
    if (w > SAT_GFX_SCREEN_W - 1) w = SAT_GFX_SCREEN_W - 1;
    put16(cmd + 0, 0x0004); put16(cmd + 4, 0x00c0); put16(cmd + 6, rgb);
    put16(cmd + 12, 0); put16(cmd + 14, y);
    put16(cmd + 16, w); put16(cmd + 18, y);
    put16(cmd + 20, w); put16(cmd + 22, y + 2);
    put16(cmd + 24, 0); put16(cmd + 26, y + 2);
    return cmd + 32;
}
#endif
/* Object list at 0x708000. The board keeps the first pixel down, drawing from the end of the list, so later entries win: VDP1 paints in
   list order, tiles of a block last to first. Each 16 pixel tile is one command. */
#ifdef SAT_VLOG
extern unsigned long sat_vl_sforced;
/* Per plot, for the diagnostic ring sat_plog (one entry per plot serial, 16 deep): tiles seen, culled off screen, lost by cause, and the first three lost tiles
   (cause 3 bits, palette 5, screen x 12, screen y 12). Lost = key not in the pack (2), no free slot (3), command table full (4). */
static u16 vl_tiles, vl_off, vl_blank, vl_miss, vl_refslot, vl_refcmd;
static u32 vl_lost[3];
static u8 vl_nlost;
static u16 vl_serial;   /* serial of the plot being built: drawn into its picture as 16 cells (top row, 4 pixels each, white 1 / green 0) so a screenshot says which plot it shows */
/* Distinct sprite tile keys the pack lacks (tile number | palette << 20), first 40 seen; sat_vl_mkn counts lookups that missed. */
volatile unsigned long sat_vl_mk[40] __attribute__((section(".lwgfx"), aligned(4)));
unsigned long sat_vl_mkn, sat_vl_mku;
static void vl_note_key(u32 tile, int pal)
{
    u32 k = tile | ((u32)(pal & 31) << 20), i;
    sat_vl_mkn++;
    for (i = 0; i < sat_vl_mku; i++) if (sat_vl_mk[i] == k) return;
    if (sat_vl_mku < 40) sat_vl_mk[sat_vl_mku++] = k;
}
static void vl_note(u32 cause, int pal, int sx, int sy)
{
    if (vl_nlost < 3) vl_lost[vl_nlost] = (cause << 29) | ((u32)(pal & 31) << 24) | (((u32)sx & 0xfff) << 12) | ((u32)sy & 0xfff);
    if (vl_nlost < 255) vl_nlost++;
}
#define VLN(x) x
#else
#define VLN(x)
#endif
static void draw_sprites(void)
{
    const u8 *list = snap.obj;
    u8 *cmd = VDP1_VRAM + table_base + 0x40; /* after clip and this table's local */
    int count = snap.objects, i;
    u16 commands = 0;
#if SAT_GFX_SLOT_HINTS
    unsigned int hint_position = 0;
#endif
    VP(vp_current[VP_CLEAR_PIXELS] = SAT_GFX_SCREEN_W * SAT_GFX_SCREEN_H;)
    /* Clear the buffer: plotting by hand gives no automatic erase, and old sprites otherwise pile up as trails. A polygon in colour 0 reads as clear. */
    put16(cmd + 0, 0x0004);
    put16(cmd + 4, 0x00c0);
    put16(cmd + 6, 0);
    put16(cmd + 12, 0); put16(cmd + 14, 0);
    put16(cmd + 16, SAT_GFX_SCREEN_W - 1); put16(cmd + 18, 0);
    put16(cmd + 20, SAT_GFX_SCREEN_W - 1); put16(cmd + 22, SAT_GFX_SCREEN_H - 1);
    put16(cmd + 24, 0); put16(cmd + 26, SAT_GFX_SCREEN_H - 1);
    cmd += 32;
    sat_gfx_stats.objects = (u16)count;
    VLN(vl_tiles = vl_off = vl_blank = vl_miss = vl_refslot = vl_refcmd = 0; vl_nlost = 0;)
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
        {
            /* Per row, once: the screen row, whether it is on screen at all, and the row's part of the tile code. */
            int sy = ((y + ty * 16) & 0x3ff) - CPS_TOP;
            u32 rowcode = (fx || fy) ? code + 0x10UL * (u32)(fy ? ny - 1 - ty : ty) : (code & ~0xfUL) + 0x10UL * (u32)ty;
            CENSUS(int prev = -2;)
            if (sy <= -16 || sy >= SAT_GFX_SCREEN_H) { CENSUS(c_tiles += (u32)nx; c_off += (u32)nx;) VLN(vl_tiles += (u16)nx; vl_off += (u16)nx;) continue; }
            for (tx = nx - 1; tx >= 0; tx--)
            {
                int sx = ((x + tx * 16) & 0x3ff) - CPS_LEFT - SAT_GFX_CROP_X;
                u32 tile;
                u16 slot;
                CENSUS(c_tiles++;)
                VLN(vl_tiles++;)
                if (sx <= -16 || sx >= SAT_GFX_SRC_W) { CENSUS(c_off++;) VLN(vl_off++;) continue; }
                if (fx || fy)
                    tile = rowcode + (u32)(fx ? nx - 1 - tx : tx);
                else
                    tile = rowcode + ((code + (u32)tx) & 0xfUL);
#if defined(SAT_ABL) && (SAT_ABL & 2)
                slot = (u16)(tile & 0x7ff);   /* measurement only: no lookup, no upload */
#if SAT_GFX_SLOT_HINTS
                hint_position++;
#endif
#elif SAT_GFX_SLOT_HINTS
                slot = sprite_lookup(tile, hint_position++);
#else
                slot = cache_get(&spr_cache, tile, &sat_gfx_stats.refused_sprite);
#endif
                if (slot == NOSLOT)
                {
                    CENSUS(c_empty++;)
#ifdef SAT_VLOG
                    if (vl_cause == 2) { vl_miss++; vl_note(2, bank & 31, sx, sy); vl_note_key(tile, bank & 31); }
                    else if (vl_cause == 3) { vl_refslot++; vl_note(3, bank & 31, sx, sy); }
                    else vl_blank++;
#endif
                    continue;
                }
                CENSUS(if (prev != tx + 1) c_runs++; prev = tx; census_bank((u32)bank);)
                if (commands >= SAT_GFX_MAX_COMMANDS) { sat_gfx_stats.refused_commands++; VLN(vl_refcmd++; vl_note(4, bank & 31, sx, sy);) continue; }
#if SAT_GFX_FIT == 3
                if (SAT_FIT_ON) put_sprite_fit(cmd, flip, colr, TEX_BASE + (u32)slot * 128, sx, sy);
                else put_sprite(cmd, flip, colr, TEX_BASE + (u32)slot * 128, sx, sy);
#elif SAT_GFX_FIT == 1
#if defined(SAT_ABL) && (SAT_ABL & 1)
                (void)flip; (void)colr;   /* measurement only: no command writes */
#else
                put_sprite_fit(cmd, flip, colr, TEX_BASE + (u32)slot * 128, sx, sy);
#endif
#else
                put_sprite(cmd, flip, colr, TEX_BASE + (u32)slot * 128, sx, sy);
#endif
                cmd += 32;
                commands++;
            }
        }
    }
#ifdef SAT_VLOG
    {
        int b;
        put16(CRAM_AT(2041), 0x83e0); put16(CRAM_AT(2043), 0xffff);
        for (b = 0; b < 16; b++)
        {
            int x = SAT_GFX_SCREEN_W - 68 + b * 4;
            put16(cmd + 0, 0x0004); put16(cmd + 4, 0x00c0); put16(cmd + 6, 0xe000 | ((vl_serial >> (15 - b)) & 1 ? 2043 : 2041));
            put16(cmd + 12, x); put16(cmd + 14, 0); put16(cmd + 16, x + 3); put16(cmd + 18, 0);
            put16(cmd + 20, x + 3); put16(cmd + 22, 3); put16(cmd + 24, x); put16(cmd + 26, 3);
            cmd += 32;
        }
    }
#endif
#ifdef SAT_READOUT
    {
        volatile unsigned long *r = UNC_PTR(unsigned long, sat_readout);
        /* Four colours at the top of CRAM, past any palette page in use; sprite priority 7 so they sit over every layer. */
        put16(CRAM_AT(2041), 0x83e0); put16(CRAM_AT(2042), 0xfc00); put16(CRAM_AT(2043), 0xffff); put16(CRAM_AT(2044), 0xfc1f);
        cmd = bar(cmd, (int)(r[0] / 26), 0, 0xe000 | 2041);
        cmd = bar(cmd, (int)(r[1] / 26), 3, 0xe000 | 2042);
        cmd = bar(cmd, 133, 6, 0xe000 | 2043);
        cmd = bar(cmd, (int)(r[2] / 26), 9, 0xe000 | 2044);
    }
#endif
    put16(cmd, 0x8000); /* end */
    sat_gfx_stats.commands = commands;
    VP(vp_current[VP_COMMANDS] = commands; vp_current[VP_OBJECTS] = (unsigned int)count;)
#ifdef SAT_PROF
    {
        u32 live = census_count();
        if (live > sat_gfx_census.banks_peak) sat_gfx_census.banks_peak = live;
        if (commands > sat_gfx_census.commands)
        {
            sat_gfx_census.commands = commands; sat_gfx_census.tiles = c_tiles; sat_gfx_census.offscreen = c_off; sat_gfx_census.empty = c_empty;
            sat_gfx_census.runs = c_runs; sat_gfx_census.banks = live; sat_gfx_census.peak_frame = sat_gfx_stats.frames;
        }
        c_tiles = c_off = c_empty = c_runs = 0;
        c_bankmask[0] = c_bankmask[1] = c_bankmask[2] = c_bankmask[3] = 0;
    }
#endif
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

#ifdef SAT_GFX_HOST
#define STAGE(i)
#else
/* Timer at each stage, for the frame profile. The kernel owns and restarts the timer. */
unsigned long sat_gfx_stage[6];
#define STAGE(i) (sat_gfx_stage[i] = ((u32)*(volatile u8 *)0xfffffe12UL << 8) | *(volatile u8 *)0xfffffe13UL)
#endif

/* One scroll layer's visible cells. Most frames nothing changed, so the first pass only sums and the copy runs when the sum moved: the drawing side
   skips an unchanged sum, and the snapshot still holds those words. The game's maps run down columns, so the reads stay on cache lines. */
static u32 snap_layer(u32 *dest, const u8 *map, u32 xc, u32 yc, u32 rows, u32 cols, u32 row_bits, u32 sum, u32 old)
{
    u32 row_off[S1_ROWS], col, row, low = (1UL << row_bits) - 1;
    for (row = 0; row < rows; row++)
    {
        u32 r = (yc + row) & 63;
        row_off[row] = ((r & low) + ((r & (63UL & ~low)) << 6)) * 4;
    }
    for (col = 0; col < cols; col++)
    {
        const u8 *base = map + ((((xc + col) & 63) << row_bits) * 4);
        for (row = 0; row < rows; row++) sum = MIX(sum, be32(base + row_off[row]));
    }
#ifdef SAT_SNAP_VERIFY
    /* Test flag: an unchanged sum must mean unchanged words, or the trim would draw stale cells. */
    if (sum == old)
        for (col = 0; col < cols; col++)
        {
            const u8 *base = map + ((((xc + col) & 63) << row_bits) * 4);
            u32 *cell = dest + col;
            for (row = 0; row < rows; row++, cell += cols) { sat_speed.verify_checked++; if (*cell != be32(base + row_off[row])) sat_speed.verify_bad++; }
        }
#endif
#ifndef SAT_SNAP_ALWAYS
    if (sum == old) return sum;
#endif
    for (col = 0; col < cols; col++)
    {
        const u8 *base = map + ((((xc + col) & 63) << row_bits) * 4);
        u32 *cell = dest + col;
        for (row = 0; row < rows; row++, cell += cols) *cell = be32(base + row_off[row]);
    }
    return sum;
}

static int rows_clear;

/* Master side, first half: registers, palette, row scroll and the object list, everything the slave's command build needs. The caller then wakes
   the slave and runs sat_gfx_snapshot_layers (visible layer cells, the long part: about 2500 words hashed). Visible cells only, at the point the game's level 2 IRQ would start. */
void sat_gfx_snapshot_begin(void)
{
    u16 layers = RAM16(SH_LAYERS), video = RAM16(SH_VIDEO), pal_reg = RAM16(SH_PALETTE_BASE), pal_mask = RAM16(SH_PAL_PAGES);
    const u8 *pal = GFX(pal_reg);
    const u8 *list = PAGE[0x70] + 0x8000;
    const u8 *last;
    u32 n;
    int page, count = 0;
    VP(unsigned int vp_snapshot_start = (unsigned int)GFX_TICKS();)
    UNC32(snap_layers_ready) = 0;

    VP(snap.profile_vblank = (unsigned int)sat_vblanks_now();
       snap.profile_stage_chars = (unsigned int)RAM16(0xff81e8UL) |
           (unsigned int)(RAMB[0x8380] ? RAMB[0x8381] : 255) << 16 |
           (unsigned int)(RAMB[0x8480] ? RAMB[0x8481] : 255) << 24;)

    snap.layers = layers;
    snap.priority = RAM16(SH_PRIORITY);
    snap.s1x = RAM16(SH_S1X); snap.s1y = RAM16(SH_S1Y);
    snap.s2x = RAM16(SH_S2X); snap.s2y = RAM16(SH_S2Y);
    snap.s3x = RAM16(SH_S3X); snap.s3y = RAM16(SH_S3Y);

    snap.pal_pages = 0;
    for (page = 0; page < SAT_GFX_PAGES; page++)
    {
        const u8 *src = palette_page(pal, pal_mask, page);
        u32 sum = 0;
        if (!src) continue;
        snap.pal_pages |= (u16)(1U << page);
        for (n = 0; n < 0x400; n += 4) sum = MIX(sum, be32(src + n));
#ifdef SAT_SNAP_VERIFY
        if (sum == snap.pal_sum[page])
            for (n = 0; n < 0x400; n += 4) { sat_speed.verify_checked++; if (*(u32 *)(void *)(snap.palette[page] + n) != be32(src + n)) sat_speed.verify_bad++; }
#endif
#ifdef SAT_SNAP_ALWAYS
        if (1)
#else
        if (sum != snap.pal_sum[page])
#endif
        {
            for (n = 0; n < 0x400; n += 4) put32_ram(snap.palette[page] + n, be32(src + n));
            snap.pal_sum[page] = sum;
        }
    }
    /* The board fills with pen 0xbff: page 5, bank 31, pen 15. */
    last = palette_page(pal, pal_mask, 5);
    snap.back_valid = (u16)(last != 0);
    if (last) snap.back = be16(last + 0x3feUL);

    snap.row_active = 0;
    if (video & 1)
    {
        const u8 *tab = GFX(RAM16(SH_ROWSCROLL_BASE));
        u16 offs = RAM16(SH_ROWOFFS), any = 0;
        for (n = 0; n < SAT_GFX_SCREEN_H; n++)
        {
            u16 v = be16(tab + (((n + CPS_TOP + offs) & 0x3ff) * 2));
            snap.row[n] = v;
            any |= v;
        }
        snap.row_active = (u16)(any != 0);
        rows_clear = 0;
    }
    else if (!rows_clear)
    {
        for (n = 0; n < SAT_GFX_SCREEN_H; n++) snap.row[n] = 0;
        rows_clear = 1;
    }
    snap.whole = (u16)(snap.row_active != 0);   /* before a menu clears row_active: the layer half still reads scroll 2 as the game has it */

    {
        u8 *out = snap.obj;
        for (; count < MAX_OBJECTS; count++, list += 8, out += 8)
        {
            u32 first = be32(list), second = be32(list + 4);
            if ((first & 0xffffUL) >= 0x8000UL || (second & 0xffffUL) >= 0xff00UL) break;
            put32_ram(out, first);
            put32_ram(out + 4, second);
        }
    }
    snap.objects = (u16)count;
#ifdef SAT_HOME
    snap.home = (u16)sat_home_mode;
    if (snap.home)
    {
        if (snap.home == 4) snap.objects = 0;   /* sub-screens: the logo's sprites (its "vs.") off, nothing beside the values */
        if (snap.home == 2)
        {
            snap.layers &= (u16)~0xeU;
            snap.objects = 0;
            snap.back_valid = 1; snap.back = 0xf000;
            snap.s1x = (u16)-(CPS_LEFT + S1_REG_CROP); snap.s1y = (u16)-CPS_TOP;
            snap.row_active = 0;
        }
        /* Banks 30 and 31 of the scroll 1 page, white and yellow; the next normal snapshot sees a changed sum and restores them. */
        snap.pal_pages |= 2;
        for (n = 0; n < 64; n++) snap.palette[1][30 * 32 + n] = home_pal[n];
        snap.pal_sum[1]++;
    }
#endif
    VP(snap.profile_snapshot_ticks = vp_elapsed(vp_snapshot_start);
       snap.profile_handoff_tick = (unsigned int)GFX_TICKS();)
}

/* Master side, second half, after the slave has been woken. The game is stopped inside the vblank hook, so the layer mask read here is the one the
   first half read. Positions come from the first half's copies (a menu moves only scroll 1's, and masks the layers it hides: the sums carry the position, so
   a later normal frame sees a changed sum and copies afresh). Writes the layer cells and sums, then sets the flag the slave waits on. */
void sat_gfx_snapshot_layers(void)
{
    u16 layers = RAM16(SH_LAYERS);
    u32 x0, y0;
    VP(unsigned int vp_layers_start = (unsigned int)GFX_TICKS();)
    if (layers & 2)
    {
#if SAT_GFX_FIT
        snap.hud_flush = RAMB[0x8001] == 2 && RAMB[0x8380] != 0;
#endif
        x0 = (u32)snap.s1x + CPS_LEFT + S1_READ_X; y0 = (u32)snap.s1y + CPS_TOP;
        snap.s1_sum = snap_layer(snap.s1, GFX(RAM16(SH_SCROLL1_BASE) & 0xffc0U), x0 >> 3, y0 >> 3, S1_ROWS, S1_COLS, 5, (x0 >> 3) | ((y0 >> 3) << 16) | ((u32)snap.hud_flush << 31), snap.s1_sum);
    }
    if (layers & 4)
    {
        u32 whole = snap.whole;
        x0 = (u32)snap.s2x + CPS_LEFT + SAT_GFX_CROP_X; y0 = (u32)snap.s2y + CPS_TOP;
        snap.s2_sum = snap_layer(snap.s2, GFX(RAM16(SH_SCROLL2_BASE) & 0xffc0U), whole ? 0 : x0 >> 4, y0 >> 4, S2_ROWS, whole ? 64 : S2_COLS, 4,
                                 (whole ? 0x80000000UL : (x0 >> 4)) | ((y0 >> 4) << 16), snap.s2_sum);
    }
    if (layers & 8)
    {
        x0 = (u32)snap.s3x + CPS_LEFT + SAT_GFX_CROP_X; y0 = (u32)snap.s3y + CPS_TOP;
        snap.s3_sum = snap_layer(snap.s3, GFX(RAM16(SH_SCROLL3_BASE) & 0xffc0U), x0 >> 5, y0 >> 5, S3_ROWS, S3_COLS, 3, (x0 >> 5) | ((y0 >> 5) << 16), snap.s3_sum);
    }
#ifdef SAT_HOME
    if (snap.home >= 3) snap.s1_sum++;    /* scroll 1 redrawn on the title menus (its bottom rows hidden) */
#endif
    VP(snap.profile_layer_ticks = vp_elapsed(vp_layers_start);)
    SNAP_BARRIER();   /* every layer word is stored before the flag */
    UNC32(snap_layers_ready) = 1;
}

/* Slave side: the layer half is in place. Normally already so by the time the command build and the plot start are done. */
static void snap_layers_wait(void)
{
#if defined(SAT_VLOG) || defined(SAT_VDP1_PROFILE) || defined(SAT_GFX_HOST) || defined(SAT_LAYERS_COUNT)
    if (!UNC32(snap_layers_ready))
    {
        u32 spin = 0;
        VP(unsigned int vp_wait_start = (unsigned int)GFX_TICKS();)
        sat_gfx_layers_late++;
        while (!UNC32(snap_layers_ready))
            if (++spin > SAT_LAYERS_WAIT_SPINS) { sat_gfx_layers_timeout++; break; }
        VP(vp_current[VP_FLAGS] |= vp_elapsed(vp_wait_start) << 16;)
    }
#else
    while (!UNC32(snap_layers_ready)) ;   /* the master finishes the layer half within the same vblank hook that woke the slave */
#endif
    SNAP_BARRIER();   /* no layer word is read before the flag */
}

/* Drawing side: everything from the snapshot. On the Saturn this runs on the slave SH-2. */
/* VDP1 frame change, safe against a list still plotting (lane avp-vanish, 11-08). Two alternating command tables:
   the slave starts a plot (PTMR) and counts it in plot_started; the master, first thing in each vblank-in, asks for the frame change
   (FBCR) only when VDP1 reports the end of that plot (EDSR CEF) and counts it in plot_shown. The slave touches the table again only
   once the last plot is shown, and starts the next plot only after the vblank in which the change happens. A list that is still
   plotting at a vblank keeps the last whole picture on screen one more frame, as a dropped frame, never a half-drawn one.
   Before the master's first vblank hook (standalone and host builds) the old path runs: change asked for at the plot. */
#ifdef SAT_GFX_HAVE_SYNC
#define EDSR_CEF 2
#define TVSTAT_VBLANK 8
static u32 plot_started, plot_shown, plot_held, plot_sync;   /* started: slave; shown, held, sync: master */
u32 sat_gfx_plot_waits;   /* frames the master held the last picture because VDP1 had not finished (diagnostic) */
#if defined(SAT_VLOG) || defined(SAT_VDP1_PROFILE) || defined(SAT_GFX_HOST) || defined(SAT_LAYERS_COUNT)
u32 sat_gfx_cef_asked, sat_gfx_cef_forced, sat_gfx_replots;   /* diagnostic: stuck-CEF recoveries (plot_start): change asked by the slave, plot started without the flag clearing */
#define CEF_COUNT(x) x
#else
#define CEF_COUNT(x)
#endif
#define SLAVE_WAIT_MAX 7000UL   /* about two frames of slave FRT ticks: a master with interrupts off (restart) cannot hold the slave */
#ifdef SAT_VLOG
extern u32 sat_vblanks_now(void);
/* Per vblank-in, 16 deep, written by the master at the frame change decision: word 0 vblank<<16 | EDSR, 1 plots started<<16 | plots shown before,
   2 plots shown after<<16 | action<<8 | held count (action 0 none to show, 1 change with CEF, 3 held for the end of the plot;
   old action 2 is reserved and is no longer emitted). */
volatile unsigned long sat_vb[16 * 4] __attribute__((section(".lwgfx"), aligned(4)));
volatile unsigned long sat_plog[16 * 8] __attribute__((section(".lwgfx"), aligned(4)));
unsigned long sat_vl_sforced;   /* retained SAT_VLOG ABI counter, always zero: unsafe forced changes were removed */
#endif
void sat_gfx_vblank(void)
{
    u32 s = UNC32(plot_started);
#ifdef SAT_VDP1_PROFILE
    unsigned int vp_before = (unsigned int)UNC32(plot_shown);
    unsigned int vp_edsr = VDP1R(0x10), vp_vblank = (unsigned int)sat_vblanks_now() + 1;
#endif
#ifdef SAT_VLOG
    u32 act = 0, before = UNC32(plot_shown), edsr = VDP1R(0x10), vbv = sat_vblanks_now() + 1;
#endif
    UNC32(plot_sync) = 1;
    if (s != UNC32(plot_shown))
    {
        if (VDP1R(0x10) & EDSR_CEF)
        {
#ifdef SAT_VLOG
            act = 1;
#endif
            VDP1R(FBCR) = 3;
            UNC32(plot_shown) = s;
            UNC32(plot_held) = 0;
        }
        else
        {
#ifdef SAT_VLOG
            act = 3;
#endif
            UNC32(plot_held) = UNC32(plot_held) + 1;
            UNC32(sat_gfx_plot_waits) = UNC32(sat_gfx_plot_waits) + 1;
        }
    }
#ifdef SAT_VLOG
    {
        volatile unsigned long *e = UNC_PTR(unsigned long, &sat_vb[(vbv & 15) * 4]);
        e[0] = (vbv & 0xffff) << 16 | (edsr & 0xffff); e[1] = (s & 0xffff) << 16 | (before & 0xffff);
        e[2] = (UNC32(plot_shown) & 0xffff) << 16 | act << 8 | (UNC32(plot_held) & 0xff); e[3] = 0;
    }
#endif
#ifdef SAT_VDP1_PROFILE
    {
        volatile unsigned int *row = UNC_PTR(unsigned int, sat_vdp1_frames[vp_vblank & (SAT_VDP1_PROFILE_DEPTH - 1)]);
        row[VF_VBLANK] = 0;
        row[VF_STARTED] = (unsigned int)s;
        row[VF_SHOWN_BEFORE] = vp_before;
        row[VF_SHOWN_AFTER] = (unsigned int)UNC32(plot_shown);
        row[VF_EDSR] = vp_edsr;
        row[VF_CPU_BUSY] = (unsigned int)sat_gfx_profile_busy();
        row[VF_VBLANK] = vp_vblank;
    }
#endif
}
static u32 slave_ticks(void) { return GFX_TICKS(); }
/* Before the table and the texture slots are touched: the last plot has ended (its change may still be pending; only PTMR waits for that). */
static int plot_wait_end(void)
{
    u32 t0 = slave_ticks();
    static u32 kicked;   /* serial of the plot already started again once */
    if (!UNC32(plot_sync)) return 1;
    while (UNC32(plot_started) != UNC32(plot_shown) && !(VDP1R(0x10) & EDSR_CEF))
        if (((slave_ticks() - t0) & 0xffffUL) > SLAVE_WAIT_MAX) {
            /* A plot was started and its end flag never came for two frames: VDP1's state was replaced under it (a Yaba load_state, a core that lost the plot).
               The master asks for the change only after the end flag, so the slave would abandon every picture from here on and sprites stop for good
               (found by the Wolverine lane). Start the same list again, once for each plot (its table and textures are untouched: this slave has not
               written since), and wait one more bound. A plot that is only slow is not started over a second time, so it still finishes. */
            if (kicked != UNC32(plot_started)) { kicked = UNC32(plot_started); VDP1R(PTMR) = 1; t0 = slave_ticks(); CEF_COUNT(sat_gfx_replots++;) continue; }
            VP(vp_current[VP_WAIT_END_TICKS] = vp_elapsed((unsigned int)t0);)
            return 0;
        }
    VP(vp_current[VP_WAIT_END_TICKS] = vp_elapsed((unsigned int)t0);)
    return 1;
}
/* Before PTMR: the change for the last plot has been asked for, so the new plot goes into the other buffer. */
static int plot_wait_shown(void)
{
    u32 t0 = slave_ticks();
    while (UNC32(plot_started) != UNC32(plot_shown))
        if (((slave_ticks() - t0) & 0xffffUL) > SLAVE_WAIT_MAX) {
            VP(vp_current[VP_WAIT_CHANGE_TICKS] = vp_elapsed((unsigned int)t0);)
            return 0;
        }
    VP(vp_current[VP_WAIT_CHANGE_TICKS] = vp_elapsed((unsigned int)t0);)
    return 1;
}
static int plot_start(void)
{
    if (!UNC32(plot_sync)) { VDP1R(FBCR) = 3; VDP1R(PTMR) = 1; return 1; }
    if (!plot_wait_shown()) { VP(vp_current[VP_FLAGS] |= VP_CHANGE_TIMEOUT;) return 0; }
    /* The plot goes into the back buffer only once the change has really happened. The change shifts EDSR (end flag of the current frame becomes the previous
       frame's), so CEF going clear is the sign, on the console and in Yaba alike. Waiting for the end of vblank instead raced the emulator's own latch of the
       change (a few lines after vblank-out): a plot that won the race drew into the buffer about to be shown, which put the buffer parity out of step and
       showed old pictures every few frames (lane avp-vanish, stepped capture: 11 % of pictures went back to an older plot). */
    if (prev_stamp)   /* first plot has no earlier change to latch; firmware may leave CEF set */
    {
        u32 t0 = slave_ticks();
        int asked = 0;
        while (VDP1R(0x10) & EDSR_CEF)
            if (((slave_ticks() - t0) & 0xffffUL) >= SLAVE_WAIT_MAX) {
                /* CEF is still set and no change is pending (every plot started has been shown, so the master asked for its change): the change was
                   never latched or the chip state was replaced (a load_state; the VideoCore 2 core's end flag). Without a way out the slave waits
                   here every frame, never starts a plot and sprites stop for good (found by the Wolverine lane). Ask for the change ourselves once and wait one
                   more bound; then plot anyway, a lost or one-off wrong picture instead of a stalled slave. */
                if (!asked) { asked = 1; VDP1R(FBCR) = 3; t0 = slave_ticks(); CEF_COUNT(sat_gfx_cef_asked++;) continue; }
                CEF_COUNT(sat_gfx_cef_forced++;)
                VP(vp_current[VP_FLAGS] |= VP_LATCH_TIMEOUT;)
                break;
            }
        VP(vp_current[VP_WAIT_LATCH_TICKS] = vp_elapsed((unsigned int)t0);)
    }
    VP(vp_current[VP_SUBMIT_TICK] = (unsigned int)GFX_TICKS();
       vp_current[VP_START_VBLANK] = (unsigned int)sat_vblanks_now();)
    VDP1R(PTMR) = 1;
    UNC32(plot_started) = UNC32(plot_started) + 1;
    VP(vp_current[VP_SERIAL] = (unsigned int)UNC32(plot_started);)
    return 1;
}
static void plot_abandon_build(void)
{
    u16 i;
    /* A hit restamps even a texture used by the previous plot. If submission
       times out, restore protection for every touched slot, including new
       uploads. This conservative scan runs only on failure and needs no list
       or new RAM. It preserves the late-render emulator guard as well as the
       hardware end-of-plot rule. */
    for (i = 0; i < SAT_GFX_SPRITE_SLOTS; i++)
        if (spr_slots[i].stamp == stamp) spr_slots[i].stamp = prev_stamp;
}
#endif

#ifdef SAT_VLOG
extern volatile unsigned long sat_vlog[16 * 4];
#define VLOG(v) UNC_PTR(unsigned long, &sat_vlog[((v) & 15) * 4])
#define SFRT() GFX_TICKS()
#endif
void sat_gfx_draw(void)
{
    u16 layers = snap.layers;
    u16 s1x = snap.s1x, s1y = snap.s1y, s2x = snap.s2x, s2y = snap.s2y, s3x = snap.s3x, s3y = snap.s3y;
    u16 bgon = 0;
    int row_active = snap.row_active;
#ifdef SAT_VLOG
    u32 vlog_v = sat_vblanks_now();
    VLOG(vlog_v)[1] = (unsigned long)VDP1R(0x10) << 16 | (SFRT() & 0xffff);
#endif
    VP(vp_begin();)

#ifdef SAT_GFX_HAVE_SYNC
    /* A timeout abandons this presentation, never the running game. Do this
       before palette, texture, cache-stamp or command-table writes. A late plot
       must keep all of its inputs intact until its end flag really arrives. */
    if (!plot_wait_end()) { VP(vp_finish(VP_END_TIMEOUT);) return; }
#endif
    stamp = (u16)(stamp + 1U == 0x10000UL ? 1U : stamp + 1U);
    cache_frame(&spr_cache); cache_frame(&s1_cache); cache_frame(&s2_cache); cache_frame(&s3_cache);
    sat_gfx_stats.uploads = 0;
    sat_gfx_stats.layer_uploads = 0;
    sat_gfx_stats.layer_writes = 0;
    sat_gfx_stats.top_bank = 0;

#if SAT_GFX_FIT == 3
    {
        static int was;
        if (was != SAT_FIT_ON)
        {
            was = SAT_FIT_ON; drawn_valid = 0;
            VDP2R(0x7a) = VDP2R(0x8a) = (u16)(was ? 0x1700 : 0); VDP2R(0x98) = (u16)(was ? 0x0101 : 0);
        }
    }
#endif
    STAGE(0);
    update_palette();
    update_priority(layers, snap.priority);
    /* Sprites first, then the plot starts: VDP1 draws while the slave does the layers below, instead of only in what is left of the
       frame after them (lane avp-vanish: heavy layer frames left VDP1 too little time and the change came mid-plot). */
#ifdef SAT_HOME
    put16(VDP1_VRAM + table_base + 32 + 12, (u16)NUDGE_X); put16(VDP1_VRAM + table_base + 32 + 14, (u16)NUDGE_Y);   /* local origin follows the screen adjust */
#endif

    STAGE(4);
#ifdef SAT_VLOG
    VLOG(vlog_v)[2] = (unsigned long)VDP1R(0x10) << 16 | (SFRT() & 0xffff);
#endif
#ifdef SAT_PROF
    { u32 v = sat_vblanks_now(); speed_on = v >= 1000 && v < 1650; }
#endif
    VLN(vl_serial = (u16)(UNC32(plot_started) + 1);)
    VP(vp_sprite_start = (unsigned int)GFX_TICKS();)
    draw_sprites();
    VP(vp_current[VP_SPRITE_TICKS] = vp_elapsed(vp_sprite_start);)
    note_slots();
#ifdef SAT_VLOG
    {   /* the plot about to start has serial plot_started + 1 */
        volatile unsigned long *e = UNC_PTR(unsigned long, &sat_plog[((UNC32(plot_started) + 1) & 15) * 8]);
        e[0] = 0;
        e[1] = (unsigned long)sat_gfx_stats.objects << 16 | sat_gfx_stats.commands;
        e[2] = (unsigned long)vl_tiles << 16 | vl_off;
        e[3] = (unsigned long)vl_miss << 24 | (unsigned long)vl_refslot << 16 | (unsigned long)vl_refcmd << 8 | vl_nlost;
        e[4] = (unsigned long)sat_gfx_stats.uploads << 16 | vl_blank;
        e[5] = vl_lost[0]; e[6] = vl_lost[1]; e[7] = vl_lost[2];
        e[0] = (UNC32(plot_started) + 1) << 16 | (vlog_v & 0xffff);   /* serial last: a reader that sees its serial sees the rest */
    }
#endif
    STAGE(5);
    put16(VDP1_VRAM + 0, 0x1009);   /* system clip, then jump (assign) to this table */
    put16(VDP1_VRAM + 2, (u16)((table_base + 0x20) >> 3));
#ifndef SAT_GFX_HAVE_SYNC
    VDP1R(FBCR) = 3;
    VDP1R(PTMR) = 1;
#else
    if (!plot_start()) { plot_abandon_build(); VP(vp_finish(0);) return; }
#endif
    VP(vp_current[VP_FLAGS] |= VP_SUBMITTED; vp_layer_start = (unsigned int)GFX_TICKS();)
    /* Only a submitted plot owns the protected previous texture stamp. An
       abandoned build must not release the last submitted plot's textures. */
    prev_stamp = stamp;
    table_base ^= TABLE_B;
#ifdef SAT_VLOG
    VLOG(vlog_v)[3] |= (sat_vblanks_now() - vlog_v) << 28 | (unsigned long)sat_gfx_stats.commands << 16 | (SFRT() & 0xffff) << 0;
#endif
#ifdef SAT_VLOG_VDP1
    /* Measurement build only: the slave waits for VDP1's end flag and logs plot time in FRT ticks (costs the slave that wait). */
    { u32 a = SFRT(), t = 0; while (!(VDP1R(0x10) & 2) && t < 30000u) t = (SFRT() - a) & 0xffffUL; VLOG(vlog_v)[2] = (VLOG(vlog_v)[2] & 0xffff0000UL) | (t & 0xffff); }
#endif
#ifdef SAT_HOME
    /* The menus on NBG3, in front of everything: panel cells (dot code 15) blend with the picture under them by colour calculation in MSB mode
       (only the panel colour, dot 15 of banks 62-63, has the MSB; per-dot mode drew opaque grey in Yaba); the font's dots stay solid. NBG3 gets cycle slots T3 (names) and T7 (cells) of bank A0 only while the menus are up;
       leaving restores play's pattern, colour calculation and priority (update_priority writes 0xfa every frame). */
    {
        static int home_was;
        if (snap.home)
        {
            VDP2R(0x10) = 0x0123; VDP2R(0x12) = 0xff67;
            VDP2R(0x36) = 0x8063; VDP2R(0x4c) = 0x0f0f; VDP2R(0x4e) = 0x0f0f; VDP2R(0x94) = 0; VDP2R(0x96) = 0;
            VDP2R(0xfa) = (u16)(prinb_last | 0x0700);
            VDP2R(0x24) = 0; VDP2R(0x26) = 0x0080; VDP2R(0xee) = 0x00c0; VDP2R(0x10a) = (u16)(sat_home_ratio << 8); VDP2R(0xec) = 0x0008;
            draw_home(!home_was);
            /* Colour calculation by the colour's MSB (SFCCMD NBG3 mode 3): banks 62 and 63 written here with the MSB only on dot 15, the panel's. */
            { int e; for (e = 62 * 16 + 1; e < 64 * 16; e++) if (e & 15) put16(CRAM_AT(e), (u16)((sat_gfx_colour(cram_shadow[e]) & 0x7fffU) | ((e & 15) == 15 ? 0x8000U : 0))); }
        }
        else if (home_was)
        {
            VDP2R(0x10) = 0x012f; VDP2R(0x12) = 0xff6f;
            VDP2R(0xec) = 0; VDP2R(0xee) = 0; VDP2R(0x10a) = 0;
            { int e; for (e = 62 * 16 + 1; e < 64 * 16; e++) put16(CRAM_AT(e), sat_gfx_colour(cram_shadow[e])); }   /* the game's colours back, MSB as everywhere */
        }
        home_was = snap.home;
    }
#endif
    STAGE(1);
    update_rowscroll();
    VDP2R(0x9a) = (u16)(row_active ? 0x0002 : 0);

    STAGE(2);
    snap_layers_wait();
    VP(vp_current[VP_SNAPSHOT_TICKS] |= snap.profile_layer_ticks << 16;)
    if (layers & 4)
    {
        bgon |= 1;
        if (!drawn_valid || snap.s2_sum != drawn_s2) { draw_scroll2(s2x, s2y, row_active); drawn_s2 = snap.s2_sum; }
    }
    if (layers & 8)
    {
        bgon |= 2;
        if (!drawn_valid || snap.s3_sum != drawn_s3) { draw_scroll3(s3x, s3y); drawn_s3 = snap.s3_sum; }
    }
    if (layers & 2)
    {
        bgon |= 4;
        if (!drawn_valid || snap.s1_sum != drawn_s1) { draw_scroll1(s1x, s1y); drawn_s1 = snap.s1_sum; }
    }
    drawn_valid = 1;
    STAGE(3);
    #ifdef SAT_GFX_BGMASK
    bgon &= SAT_GFX_BGMASK;
#endif
#ifdef SAT_HOME
    if (snap.home) bgon |= 8;
#endif
    VDP2R(0x20) = bgon;
    VDP2R(0x70) = (u16)((s2x + CPS_LEFT + SAT_GFX_CROP_X - NUDGE_X) & 0x7ff);
    VDP2R(0x74) = (u16)((s2y + CPS_TOP - NUDGE_Y) & 0x7ff);
    VDP2R(0x80) = (u16)((s3x + CPS_LEFT + SAT_GFX_CROP_X - NUDGE_X) & 0x7ff);
    VDP2R(0x84) = (u16)((s3y + CPS_TOP - NUDGE_Y) & 0x7ff);
    VDP2R(0x90) = (u16)((s1x + CPS_LEFT + S1_REG_CROP - NUDGE_X) & 0x7ff);
    VDP2R(0x92) = (u16)((s1y + CPS_TOP - NUDGE_Y) & 0x7ff);
#ifdef SAT_PROF
    if (speed_on)
    {
        u32 t = sat_gfx_stage[5] - sat_gfx_stage[4];
        sat_speed.frames++;
        sat_speed.uploads += sat_gfx_stats.uploads; sat_speed.layer_uploads += sat_gfx_stats.layer_uploads; sat_speed.missing = sat_gfx_stats.missing;
        sat_speed.commands += sat_gfx_stats.commands;
        if (sat_gfx_stats.uploads == 0) { sat_speed.clean_frames++; sat_speed.clean_ticks += t; sat_speed.clean_commands += sat_gfx_stats.commands; }
        else sat_speed.dirty_ticks += t;
        if (sat_gfx_stage[5] > sat_speed.peak_total)
        {
            int k;
            sat_speed.peak_total = sat_gfx_stage[5]; sat_speed.peak_vblank = sat_vblanks_now();
            for (k = 0; k < 6; k++) sat_speed.peak_stage[k] = sat_gfx_stage[k];
            sat_speed.peak_uploads = sat_gfx_stats.uploads; sat_speed.peak_layer_uploads = sat_gfx_stats.layer_uploads; sat_speed.peak_commands = sat_gfx_stats.commands;
        }
    }
#endif

#ifdef SAT_READOUT
    if (!(readout_pad() & 0x0020))   /* pad Y held: wait here for the list's end and show VDP1's time as the fourth bar. It costs the slave that wait. */
    {
        u32 t0 = ((u32)*(volatile u8 *)0xfffffe12u << 8) | *(volatile u8 *)0xfffffe13u, t = 0;
        while (!(*(volatile u16 *)0x25D00010UL & 2) && t < 8000u) t = (((u32)*(volatile u8 *)0xfffffe12u << 8 | *(volatile u8 *)0xfffffe13u) - t0) & 0xffffu;
        *(volatile unsigned long *)((unsigned long)&sat_readout[2] | 0x20000000UL) = t;
    }
#endif
    sat_gfx_stats.frames++;
    VP(vp_current[VP_LAYER_TICKS] = vp_elapsed(vp_layer_start);
       if (VDP1R(0x10) & 2) {
           vp_current[VP_FLAGS] |= VP_CEF_AT_CPU_DONE;
           vp_current[VP_RASTER_UPPER_TICKS] = vp_elapsed(vp_current[VP_SUBMIT_TICK]);
       }
       vp_finish(0);)
}

void sat_gfx_frame(void)
{
    sat_gfx_snapshot_begin();
    sat_gfx_snapshot_layers();
    sat_gfx_draw();
}

#define COLD_OS __attribute__((optimize("Os")))   /* load-time code, once per round: built for size, high work RAM is what is short */
static COLD_OS int open_pack(const u8 *p)
{
    int i;
    pack_start = p;
    if (be32(p) != 0x53475031UL) return 0; /* SGP1 */
    for (i = 0; i < 4; i++)
    {
        sections[i].count = be32(p + 4 + i * 12);
        sections[i].keys = p + be32(p + 8 + i * 12);
        sections[i].data = p + be32(p + 12 + i * 12);
        sections[i].split = be32(p + 52 + i * 8);
        sections[i].spill = p + be32(p + 56 + i * 8);
        index_section(&sections[i], i);
    }
    return 1;
}

static void clear_vram(u8 *p, u32 bytes)
{
    u32 i;
    for (i = 0; i < bytes; i += 4) put32(p + i, 0);
}

int sat_gfx_swap_pack(const void *pack)
{
    u32 n;
    if (!pack || !open_pack((const u8 *)pack)) return 0;
    for (n = 0; n < BLANK_WAYS; n++) blank_seen[n] = NOKEY;
    return 1;
}

void sat_gfx_display(int on) { VDP2R(0x00) = on ? 0x8001 : 0x0001; }

COLD_OS int sat_gfx_init(const void *pack)
{
#ifdef SAT_KEYLOG
    { u32 i; for (i = 0; i < 0x10000; i += 2) *(volatile u16 *)(0x25A70000UL + i) = 0; }
#endif
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
    for (n = 0; n < 64 * 64; n++) { sh_s1[n] = CLEAR_NAME; sh_s2[n] = CLEAR_NAME; sh_s3[n] = NOKEY; }
    for (n = 0; n < SAT_GFX_SCREEN_H; n++) sh_row[n] = 0;
    for (n = 0; n < BLANK_WAYS; n++) blank_seen[n] = NOKEY;
    cache_setup(&spr_cache, VDP1_VRAM + TEX_BASE, 128, SAT_GFX_SPRITE_SLOTS, 0, SEC_SPRITE, spr_slots, spr_head, HASH_SIZE);
    cache_setup(&s1_cache, VDP2_VRAM + CELL_S1, 32, SAT_GFX_S1_SLOTS, 4, SEC_S1, s1_slots, s1_head, HASH_SIZE_S1);
    cache_setup(&s2_cache, VDP2_VRAM + CELL_S2, 128, SAT_GFX_S2_SLOTS, 0, SEC_S2, s2_slots, s2_head, HASH_SIZE_S2);
    cache_setup(&s3_cache, VDP2_VRAM + CELL_S3, 512, SAT_GFX_S3_SLOTS, 0, SEC_S3, s3_slots, s3_head, HASH_SIZE_S3);
#if SAT_GFX_SLOT_HINTS
    for (n = 0; n < SAT_GFX_SLOT_HINTS; n++) sprite_slot_hints[n] = NOSLOT;
#ifdef SAT_GFX_SLOT_HINT_STATS
    sat_gfx_slot_hint_stats.queries = sat_gfx_slot_hint_stats.hits = 0;
    sat_gfx_slot_hint_stats.fallbacks = sat_gfx_slot_hint_stats.beyond_limit = 0;
#endif
#endif
    stamp = 0;
    prev_stamp = 0;
    table_base = 0;
    drawn_valid = 0;

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
#if SAT_GFX_FIT == 1
    /* 384 source pixels on 352: increment 1 + 23/256 (the register keeps 8 fraction bits), half-reduction mode; NBG0 and NBG1 already have two character reads a slot. */
    VDP2R(0x78) = 1; VDP2R(0x7a) = 0x1700; VDP2R(0x88) = 1; VDP2R(0x8a) = 0x1700;
    VDP2R(0x98) = 0x0101;
#elif SAT_GFX_FIT == 3
    VDP2R(0x98) = 0;
#else
    VDP2R(0x98) = 0;
#endif
#if SAT_GFX_FIT == 1 || SAT_GFX_FIT == 3
    { int i2; for (i2 = 0; i2 <= 416; i2++) fit_x[i2] = (u16)(i2 * 11 / 12); }
#endif
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
    put16(c + TABLE_B + 32, 0x000a);              /* the second table's */
    put16(c + TABLE_B + 64, 0x8000);
    put16(c + 64, 0x8000);
    VDP1R(PTMR) = 0;

    VDP2R(0x00) = 0x8001;                         /* display on */
    #ifdef SAT_HOME
    /* The font with its clear dots as dot code 15, the panel's: letters sit on the translucent panel, not in holes through it. */
    { u32 n; for (n = 0; n < sizeof home_font; n += 4) { u32 w = (u32)home_font[n] << 24 | (u32)home_font[n + 1] << 16 | (u32)home_font[n + 2] << 8 | home_font[n + 3], o = 0; int k;
        for (k = 0; k < 32; k += 4) o |= (((w >> k) & 15) ? ((w >> k) & 15) : 15u) << k;
        put32(VDP2_VRAM + CELL_S1 + (u32)SAT_GFX_HOME_FONT * 32 + n, o); } }
    { u32 n; for (n = 0; n < 32; n += 4) put32(VDP2_VRAM + CELL_S1 + (u32)(SAT_GFX_HOME_FONT + 58) * 32 + n, 0xffffffffUL); }   /* the menu panel: every dot code 15 (pen 14, near black) */
    /* Screen names in large letters, as MSHvSF's OPTION MODE header: A to Z from the same font, each row doubled (8 x 16, two cells) and
       thickened by one dot to the right; clear dots are the panel's. 52 cells after the panel, up to 0x1fbe0 (the row table is at 0x1fc00). */
    { int L, h, y; for (L = 0; L < 26; L++) for (h = 0; h < 2; h++) for (y = 0; y < 8; y++) {
        const u8 *f = home_font + (32 + L) * 32 + (h * 4 + y / 2) * 4;
        u32 w = (u32)f[0] << 24 | (u32)f[1] << 16 | (u32)f[2] << 8 | f[3], o = 0; int k;
        for (k = 28; k >= 0; k -= 4) { u32 d = (w >> k) & 15, l = k < 28 ? (w >> (k + 4)) & 15 : 0; d = d ? d : l; o |= (d ? d : 15u) << k; }
        put32(VDP2_VRAM + CELL_S1 + (u32)(SAT_GFX_HOME_FONT + 59 + L * 2 + h) * 32 + (u32)y * 4, o); } }
#endif
    return 1;
}
