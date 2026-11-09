/* HOST: actual graphics driver, synthetic pack and programmable chip/clock.
 * No rasteriser or console timing is simulated by this fixture.
 * gcc -std=c90 -pedantic -Wall -Wextra -Werror \
 *   -DSAT_VDP1_PROFILE -DSAT_VLOG tests/vdp1_presentation_test.c -o test
 */
#define SAT_GFX_HOST
#define SAT_GFX_SYNC_TEST
#define main old_graphics_host_main
#include "../saturn/gfx/host_test.c"
#undef main
#include "../saturn/gfx/sat_gfx.c"

volatile unsigned long sat_vlog[16 * 4];
volatile unsigned long sat_readout[3];
unsigned long sat_pad_raw = 0xffffUL;
static unsigned long test_clock, test_vblank;
static int test_busy, clock_calls, clear_on_call;
static unsigned long clock_step = 1000;

unsigned long sat_vblanks_now(void) { return test_vblank; }
int sat_gfx_profile_busy(void) { return test_busy; }
unsigned long sat_gfx_host_ticks(void)
{
    unsigned long value = test_clock;
    test_clock = (test_clock + clock_step) & 0xffffUL;
    clock_calls++;
    if (clear_on_call && clock_calls >= clear_on_call)
        sat_gfx_host_vdp1r[0x10 / 2] &= (unsigned short)~2u;
    return value;
}

static void clock_reset(unsigned long start, unsigned long step, int clear_at)
{
    test_clock = start; clock_step = step;
    clock_calls = 0; clear_on_call = clear_at;
}
static void frame_boundary(void)
{
    sat_gfx_vblank();
    test_vblank++;
}
static void reset_driver(unsigned char *pack)
{
    int i;
    for (i = 0; i < 256; i++) PAGE[i] = ZERO;
    PAGE[0x70] = OBJ; PAGE[0x90] = GFX0; PAGE[0x91] = GFX1; PAGE[0x92] = GFX2;
    memset(RAMB, 0, sizeof RAMB);
    set_state();
    CHECK(sat_gfx_init(pack));
    plot_started = plot_shown = plot_held = plot_sync = 0;
    sat_gfx_plot_waits = 0;
    test_vblank = 1; test_busy = 0;
    clock_reset(0, 1, 0);
    set_list(1, 1, 1, 1, 1);
    sat_gfx_host_vdp1r[0x10 / 2] = 0;
    frame_boundary();
}

static void boundaries(unsigned char *pack)
{
    unsigned long end;
    int extra = 0;
    reset_driver(pack);
    set_list(1024, 3, 3, 0, 1);
#ifdef SAT_VLOG
    extra += 16;
#endif
#ifdef SAT_READOUT
    extra += 4;
#endif
    /* Both table ends are exercised, including all real marker/bar emitters. */
    memset(V1 + 0x8000, 0x5a, 0x20);
    clock_reset(0, 1, 0);
    sat_gfx_frame();
    CHECK(sat_gfx_stats.commands == SAT_GFX_MAX_COMMANDS);
    end = 0x60UL + (SAT_GFX_MAX_COMMANDS + (unsigned long)extra) * 32;
    CHECK(end <= 0x7fe0UL);
    CHECK(r16(V1 + end) == 0x8000);
    CHECK(r16(V1 + 0x8000) == 0x5a5a);
    CHECK(plot_started == 1 && table_base == TABLE_B);

    sat_gfx_host_vdp1r[0x10 / 2] = 2;
    frame_boundary();
    memset(V1 + TEX_BASE, 0x5a, 32);
    clock_reset(0, 1, 1);
    sat_gfx_frame();
    CHECK(r16(V1 + TABLE_B + end) == 0x8000);
    CHECK(r16(V1 + TEX_BASE) == 0x5a5a);
    CHECK(plot_started == 2 && table_base == 0);
}

static void late_completion(unsigned char *pack)
{
    static unsigned char before_v1[sizeof V1], before_cr[sizeof CR];
    unsigned short saved_stamp, saved_previous;
    unsigned long saved_table, saved_frames;
    int i;
    reset_driver(pack);
    sat_gfx_frame();
    saved_stamp = stamp; saved_previous = prev_stamp;
    saved_table = table_base; saved_frames = sat_gfx_stats.frames;
    memcpy(before_v1, V1, sizeof V1); memcpy(before_cr, CR, sizeof CR);
    sat_gfx_host_vdp1r[FBCR / 2] = 2;
    sat_gfx_host_vdp1r[PTMR / 2] = 0;
    /* Missing CEF for longer than the old forced-swap budget. */
    for (i = 0; i < 5; i++) frame_boundary();
    CHECK(plot_shown == 0 && plot_started == 1);
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 2);
    CHECK(sat_gfx_plot_waits == 5);
    w16(GFX0 + 0xc000 + (1 * 16 + 3) * 2, 0xffff);
    sat_gfx_snapshot();
    /* Exercise timeout arithmetic across FRT wrap. */
    clock_reset(65530, 1000, 0);
    sat_gfx_draw();
    CHECK(clock_calls < 40);   /* two bounds: the lost plot is started again once, then the wait ends */
    CHECK(stamp == saved_stamp && prev_stamp == saved_previous);
    CHECK(table_base == saved_table && sat_gfx_stats.frames == saved_frames);
    CHECK(sat_gfx_host_vdp1r[PTMR / 2] == 1 && sat_gfx_replots == 1);   /* the plot whose end never came is started again once */
    sat_gfx_host_vdp1r[PTMR / 2] = 0;
    CHECK(!memcmp(before_v1, V1, sizeof V1));
    CHECK(!memcmp(before_cr, CR, sizeof CR));
#ifdef SAT_VDP1_PROFILE
    CHECK(vp_current[VP_FLAGS] == VP_END_TIMEOUT);
#endif
    /* Completion followed by an acknowledged change can recover next handoff. */
    sat_gfx_host_vdp1r[0x10 / 2] = 2;
    frame_boundary();
    clock_reset(0, 1, 1);
    sat_gfx_draw();
    CHECK(plot_started == 2 && plot_shown == 1);
    CHECK(table_base != saved_table && prev_stamp == stamp);
}

static void late_change(unsigned char *pack)
{
    unsigned short live_stamp;
    unsigned long saved_table;
    reset_driver(pack);
    sat_gfx_frame();
    live_stamp = prev_stamp; saved_table = table_base;
    sat_gfx_host_vdp1r[0x10 / 2] = 2; /* done, but no master vblank yet */
    sat_gfx_host_vdp1r[FBCR / 2] = 2;
    sat_gfx_host_vdp1r[PTMR / 2] = 0;
    clock_reset(65530, 1000, 0);
    sat_gfx_draw();
    CHECK(plot_started == 1 && plot_shown == 0);
    CHECK(prev_stamp == live_stamp && table_base == saved_table);
    CHECK(spr_slots[0].stamp == live_stamp); /* this build hit a texture shared with the prior plot */
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 2);
    CHECK(sat_gfx_host_vdp1r[PTMR / 2] == 0);
#ifdef SAT_VDP1_PROFILE
    CHECK(vp_current[VP_FLAGS] == VP_CHANGE_TIMEOUT);
#endif
    frame_boundary(); /* change requested, CEF still set until latch */
    /* CEF stays set and every plot started has been shown, so no change is pending: the flag is stuck (a load_state, the VideoCore 2 core).
       The slave asks for the change itself, waits one more bound, then plots anyway: it must not wait for ever. */
    clock_reset(65530, 1000, 0);
    sat_gfx_host_vdp1r[FBCR / 2] = 2;
    sat_gfx_draw();
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 3);   /* asked */
    CHECK(sat_gfx_host_vdp1r[PTMR / 2] == 1);   /* and started */
    CHECK(plot_started == 2 && plot_shown == 1);
    CHECK(prev_stamp == stamp && table_base != saved_table);
    CHECK(sat_gfx_cef_asked == 1 && sat_gfx_cef_forced == 1);
#ifdef SAT_VDP1_PROFILE
    CHECK(vp_current[VP_FLAGS] == (VP_LATCH_TIMEOUT | VP_SUBMITTED | VP_CEF_AT_CPU_DONE));
#endif
    /* The next attempt submits after a real latch, as before. */
    frame_boundary();
    CHECK(plot_shown == 2);
    saved_table = table_base;
    clock_reset(0, 1, 1);
    sat_gfx_host_vdp1r[PTMR / 2] = 0;
    sat_gfx_draw();
    CHECK(plot_started == 3 && prev_stamp == stamp && table_base != saved_table);
    CHECK(sat_gfx_cef_asked == 1 && sat_gfx_cef_forced == 1);
#ifdef SAT_VDP1_PROFILE
    CHECK(vp_current[VP_FLAGS] == VP_SUBMITTED);
    CHECK(vp_current[VP_SERIAL] == 3);
    CHECK(vp_current[VP_SOURCE_TEXELS] == 256);
    CHECK(vp_current[VP_SPRITE_PIXELS] > 0 && vp_current[VP_SPRITE_PIXELS] <= 256);
    CHECK(vp_current[VP_CLEAR_PIXELS] == 352u * 224u);
    CHECK(vp_current[VP_COLOUR_MODES] == 1);
    CHECK(vp_current[VP_HALF_TRANSPARENT] == 0);
    CHECK(sat_vdp1_plots[vp_attempt & (SAT_VDP1_PROFILE_DEPTH - 1)][VP_ATTEMPT] == vp_attempt);
#endif
}

static void first_plot_stale_cef(unsigned char *pack)
{
    reset_driver(pack);
    sat_gfx_host_vdp1r[0x10 / 2] = 2;
    clock_reset(0, 1, 0);
    sat_gfx_frame();
    CHECK(plot_started == 1 && prev_stamp != 0 && table_base == TABLE_B);
}

static void abandoned_shared_texture(unsigned char *pack)
{
    u16 slot, live_stamp;
    reset_driver(pack);
    sat_gfx_frame();
    live_stamp = prev_stamp;
    CHECK(spr_slots[0].key == 0 && spr_slots[0].stamp == live_stamp);
    sat_gfx_host_vdp1r[0x10 / 2] = 2;
    clock_reset(0, 1000, 0);
    sat_gfx_draw(); /* hits key 0, then times out waiting for the master */
    CHECK(prev_stamp == live_stamp && spr_slots[0].stamp == live_stamp);
    stamp++;
    cache_frame(&spr_cache);
    spr_cache.hand = 0; /* the next miss tries to evict the prior plot's texture */
    slot = cache_get(&spr_cache, 77, &sat_gfx_stats.refused_sprite);
    CHECK(slot != 0 && slot != NOSLOT);
    CHECK(spr_slots[0].key == 0 && spr_slots[0].stamp == live_stamp);
}

#ifdef SAT_VDP1_PROFILE
static void profile_elapsed_clock(unsigned char *pack)
{
    unsigned int duration;
    reset_driver(pack);
    sat_gfx_snapshot();
    clock_reset(12345, 1, 0);
    sat_gfx_draw();
    duration = vp_current[VP_CPU_TICKS];
    CHECK(duration > 0 && duration < 1000); /* elapsed work, never raw FRT phase */
    reset_driver(pack);
    sat_gfx_snapshot();
    clock_reset(65530, 1, 0); /* same work straddles the 16-bit timer wrap */
    sat_gfx_draw();
    CHECK(vp_current[VP_CPU_TICKS] == duration);
}
#endif

int main(void)
{
    unsigned char *pack = make_pack(8000);
    boundaries(pack);
    first_plot_stale_cef(pack);
    late_completion(pack);
    late_change(pack);
    abandoned_shared_texture(pack);
#ifdef SAT_VDP1_PROFILE
    profile_elapsed_clock(pack);
#endif
    free(pack);
    printf(fails ? "FAILED %d\n" : "VDP1 presentation HOST tests passed\n", fails);
    return fails != 0;
}
