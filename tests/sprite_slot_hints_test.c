/* HOST safety and useful-work checks for the actual optional lookup path.
 * Synthetic tiles only. This is not a Saturn timing benchmark. */
#define SAT_GFX_HOST
#define SAT_GFX_SYNC_TEST
#define main original_graphics_host_main
#include "../saturn/gfx/host_test.c"
#undef main
#include "../saturn/gfx/sat_gfx.c"

volatile unsigned long sat_vlog[16 * 4];
volatile unsigned long sat_readout[3];
unsigned long sat_pad_raw = 0xffffUL;
unsigned long sat_vblanks_now(void) { return 1; }
int sat_gfx_profile_busy(void) { return 0; }
unsigned long sat_gfx_host_ticks(void)
{
    static unsigned long ticks;
    ticks = (ticks + 1) & 0xffffUL;
    return ticks;
}

#if !SAT_GFX_SLOT_HINTS || !defined(SAT_GFX_SLOT_HINT_STATS)
#error This fixture needs slot hints and their diagnostic counters
#endif

static void fresh(unsigned char *pack)
{
    int i;
    for (i = 0; i < 256; i++) PAGE[i] = ZERO;
    PAGE[0x70] = OBJ; PAGE[0x90] = GFX0; PAGE[0x91] = GFX1; PAGE[0x92] = GFX2;
    memset(RAMB, 0, sizeof RAMB);
    set_state();
    CHECK(sat_gfx_init(pack));
    plot_started = plot_shown = plot_sync = 0;
    sat_gfx_host_vdp1r[0x10 / 2] = 0;
}

static void repeated_list(unsigned char *pack)
{
    unsigned long hits, covered = SAT_GFX_SLOT_HINTS < 32 ? SAT_GFX_SLOT_HINTS : 32;
    fresh(pack);
    set_list(32, 1, 1, 1, 1);
    sat_gfx_frame();
    CHECK(sat_gfx_stats.uploads == 32);
    hits = sat_gfx_slot_hint_stats.hits;
    sat_gfx_frame();
    CHECK(sat_gfx_slot_hint_stats.hits - hits == covered);
    CHECK(sat_gfx_stats.uploads == 0);
    CHECK(sat_gfx_stats.sprite_slots_used == 32);
    CHECK(sat_gfx_stats.commands == 32);
    CHECK(sat_gfx_slot_hint_stats.queries == 64);
    CHECK(sat_gfx_slot_hint_stats.beyond_limit == (32 - covered) * 2);
}

static void eviction_and_bounds(unsigned char *pack)
{
    u16 old, replacement, result;
    unsigned long hits;
    fresh(pack);
    stamp = 1;
    cache_frame(&spr_cache);
    old = sprite_lookup(10, 0);
    CHECK(old != NOSLOT);
    stamp = 2; prev_stamp = 0;
    cache_frame(&spr_cache);
    spr_cache.hand = old;
    replacement = cache_get(&spr_cache, 20, &sat_gfx_stats.refused_sprite);
    CHECK(replacement == old && spr_cache.slots[old].key == 20);
    stamp = 3;
    cache_frame(&spr_cache);
    hits = sat_gfx_slot_hint_stats.hits;
    result = sprite_lookup(10, 0);
    CHECK(result != old && result != NOSLOT);
    CHECK(spr_cache.slots[result].key == 10);
    CHECK(sat_gfx_slot_hint_stats.hits == hits);

    /* An out-of-range stored slot is a miss, never a memory read. */
    sprite_slot_hints[0] = (u16)SAT_GFX_SPRITE_SLOTS;
    CHECK(sprite_lookup(10, 0) == result);
    sprite_slot_hints[0] = NOSLOT;
    CHECK(sprite_lookup(10, 0) == result);
    CHECK(sprite_lookup(10, SAT_GFX_SLOT_HINTS) == result);
    CHECK(sat_gfx_slot_hint_stats.beyond_limit == 1);
}

static void invalid_tiles_and_reinit(unsigned char *pack)
{
    unsigned int i;
    u16 slot;
    fresh(pack);
    stamp = 1;
    CHECK(sprite_lookup(60000, 0) == NOSLOT);
    CHECK(sprite_slot_hints[0] == NOSLOT);
    CHECK(sat_gfx_stats.missing == 1);
    CHECK(sprite_lookup(60000, 0) == NOSLOT);
    CHECK(sat_gfx_stats.missing == 1);
    CHECK(sprite_lookup(123, 0) == NOSLOT); /* explicitly blank pack entry */
    CHECK(sat_gfx_slot_hint_stats.hits == 0);
    slot = sprite_lookup(10, 0);
    CHECK(slot != NOSLOT);
    CHECK(sat_gfx_swap_pack(pack));
    cache_frame(&spr_cache); stamp = 2;
    CHECK(sprite_lookup(10, 0) == slot);
    CHECK(sat_gfx_slot_hint_stats.hits == 1);
    CHECK(sat_gfx_init(pack));
    for (i = 0; i < SAT_GFX_SLOT_HINTS; i++) CHECK(sprite_slot_hints[i] == NOSLOT);
    CHECK(sat_gfx_slot_hint_stats.queries == 0 && sat_gfx_slot_hint_stats.hits == 0);
}

static void abandoned_hit_and_wrap(unsigned char *pack)
{
    u16 live, replacement;
    fresh(pack);
    stamp = 65535U;
    live = sprite_lookup(10, 0);
    prev_stamp = stamp;
    stamp = 1;
    cache_frame(&spr_cache);
    CHECK(sprite_lookup(10, 0) == live);
    CHECK(spr_cache.slots[live].stamp == 1 && spr_cache.used == 1);
    CHECK(sprite_lookup(10, 0) == live && spr_cache.used == 1);
    plot_abandon_build();
    CHECK(spr_cache.slots[live].stamp == 65535U);
    stamp = 2;
    cache_frame(&spr_cache);
    spr_cache.hand = live;
    replacement = sprite_lookup(20, 0);
    CHECK(replacement != live && replacement != NOSLOT);
    CHECK(spr_cache.slots[live].key == 10 && spr_cache.slots[live].stamp == 65535U);
}

int main(void)
{
    unsigned char *pack = make_pack(8000);
    w32(pack + 52 + 123 * 4, (123UL << 16) | 0xffffUL);
    repeated_list(pack);
    eviction_and_bounds(pack);
    invalid_tiles_and_reinit(pack);
    abandoned_hit_and_wrap(pack);
    free(pack);
    printf(fails ? "FAILED %d\n" : "Sprite slot hints HOST tests passed\n", fails);
    return fails != 0;
}
