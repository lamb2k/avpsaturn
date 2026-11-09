/* HOST: real renderer and a small two-buffer erase/clear coverage model.
 * This checks register decisions and pixels cleared, not VDP1 raster timing.
 * gcc -std=c90 -pedantic -Wall -Wextra -Werror \
 *   tests/vdp1_hardware_erase_test.c -o /tmp/erase-test && /tmp/erase-test
 */
#define SAT_GFX_HOST
#define SAT_GFX_SYNC_TEST
#define SAT_VDP1_HW_ERASE 1
#define main old_graphics_host_main
#include "../saturn/gfx/host_test.c"
#undef main
#include "../saturn/gfx/sat_gfx.c"

volatile unsigned long sat_vlog[16 * 4];
volatile unsigned long sat_readout[3];
unsigned long sat_pad_raw = 0xffffUL;
static unsigned long clock_now, clock_step, test_vblank;
static int tick_calls, leave_blank_call;
static unsigned short reference_fb[2][SAT_GFX_SCREEN_W * SAT_GFX_SCREEN_H];
static unsigned short erase_fb[2][SAT_GFX_SCREEN_W * SAT_GFX_SCREEN_H];
static int front, back;
static unsigned short latched_ewlr, latched_ewrr, latched_ewdr;

unsigned long sat_vblanks_now(void) { return test_vblank; }
int sat_gfx_profile_busy(void) { return 0; }
unsigned long sat_gfx_host_ticks(void)
{
    unsigned long t = clock_now;
    clock_now = (clock_now + clock_step) & 0xffffUL;
    tick_calls++;
    if (leave_blank_call && tick_calls >= leave_blank_call)
        sat_gfx_host_vdp2r[0x04 / 2] = 0;
    return t;
}

static void reset_driver(unsigned char *pack)
{
    int i, b;
    for (i = 0; i < 256; i++) PAGE[i] = ZERO;
    PAGE[0x70] = OBJ; PAGE[0x90] = GFX0; PAGE[0x91] = GFX1; PAGE[0x92] = GFX2;
    memset(RAMB, 0, sizeof RAMB);
    set_state();
    CHECK(sat_gfx_init(pack));
    plot_started = plot_shown = plot_held = 0; plot_sync = 1;
    sat_gfx_plot_waits = 0;
    sat_gfx_host_vdp1r[0x10 / 2] = 0;
    sat_gfx_host_vdp2r[0x04 / 2] = 0;
    clock_now = 65530; clock_step = 1; test_vblank = 1;
    tick_calls = leave_blank_call = 0;
    front = 0; back = 1;
    latched_ewlr = 0; latched_ewrr = 0x0200; latched_ewdr = 0x5555;
    for (b = 0; b < 2; b++)
        for (i = 0; i < SAT_GFX_SCREEN_W * SAT_GFX_SCREEN_H; i++)
            reference_fb[b][i] = erase_fb[b][i] = (unsigned short)(i * 17 + 3 + b);
    set_list(1, 1, 1, 1, 1);
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0);
    CHECK(sat_gfx_host_vdp1r[EWDR / 2] == 0);
    CHECK((sat_gfx_host_vdp1r[EWRR / 2] & 511) == SAT_VDP1_ERASE_ROWS - 1);
    CHECK(((SAT_GFX_SCREEN_W / 8) + 1) * SAT_VDP1_ERASE_ROWS * 8 <= 63180);
}

static void boundary(unsigned short cef)
{
    sat_gfx_host_vdp1r[0x10 / 2] = cef;
    sat_gfx_host_vdp1r[FBCR / 2] = 2; /* distinguish a new change request */
    sat_gfx_host_vdp2r[0x04 / 2] = 8;
    sat_gfx_vblank();
    test_vblank++;
}

/* Decode the actual programmed erase rectangle, clear the old FRONT, then
 * switch the two physical buffers. Only the driver OUT hook certifies it. */
static void model_change(int run_out)
{
    unsigned int x, y;
    unsigned int left = (latched_ewlr >> 9) * 8;
    unsigned int top = latched_ewlr & 511;
    unsigned int right = (latched_ewrr >> 9) * 8 - 1;
    unsigned int bottom = latched_ewrr & 511;
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 3);
    if (sat_gfx_host_vdp1r[TVMR / 2] & 8)
    {
        CHECK(left == 0 && right == SAT_GFX_SCREEN_W - 1);
        CHECK(top == 0 && bottom == SAT_VDP1_ERASE_ROWS - 1);
        CHECK(latched_ewdr == 0);
        for (y = top; y <= bottom; y++)
            for (x = left; x <= right; x++)
                erase_fb[front][y * SAT_GFX_SCREEN_W + x] = latched_ewdr;
    }
    front ^= 1; back ^= 1;
    latched_ewlr = sat_gfx_host_vdp1r[EWLR / 2];
    latched_ewrr = sat_gfx_host_vdp1r[EWRR / 2];
    latched_ewdr = sat_gfx_host_vdp1r[EWDR / 2];
    CHECK(!memcmp(reference_fb[front], erase_fb[front], sizeof erase_fb[front]));
    sat_gfx_host_vdp2r[0x04 / 2] = 0;
    sat_gfx_host_vdp1r[0x10 / 2] = 0;
    if (run_out) sat_gfx_vblank_out();
}

/* Clear exactly the polygon emitted into the submitted table. The reference
 * clears the whole back buffer. Dirty every pixel after comparing so either a
 * missed top-band erase or an incomplete bottom polygon fails next time. */
static void model_plot(int expected_row)
{
    unsigned long base = table_base ^ TABLE_B;
    unsigned int x, y, first = r16(V1 + base + 0x40 + 14);
    CHECK(r16(V1 + base + 0x40) == 4);
    CHECK(r16(V1 + base + 0x40 + 6) == 0);
    CHECK(first == (unsigned int)expected_row);
    CHECK(r16(V1 + base + 0x40 + 18) == first);
    CHECK(r16(V1 + base + 0x40 + 20) == SAT_GFX_SCREEN_W - 1);
    CHECK(r16(V1 + base + 0x40 + 22) == SAT_GFX_SCREEN_H - 1);
    memset(reference_fb[back], 0, sizeof reference_fb[back]);
    for (y = first; y < SAT_GFX_SCREEN_H; y++)
        for (x = 0; x < SAT_GFX_SCREEN_W; x++)
            erase_fb[back][y * SAT_GFX_SCREEN_W + x] = 0;
    CHECK(!memcmp(reference_fb[back], erase_fb[back], sizeof erase_fb[back]));
    for (y = 0; y < SAT_GFX_SCREEN_H; y++)
        for (x = 0; x < SAT_GFX_SCREEN_W; x++)
            reference_fb[back][y * SAT_GFX_SCREEN_W + x] =
                erase_fb[back][y * SAT_GFX_SCREEN_W + x] =
                (unsigned short)(1 + (x * 13 + y * 19 + plot_started * 7) % 65535);
}

static void submit(int expected_row)
{
    unsigned long before = plot_started;
    sat_gfx_host_vdp1r[PTMR / 2] = 0;
    sat_gfx_frame();
    CHECK(plot_started == before + 1);
    CHECK(sat_gfx_host_vdp1r[PTMR / 2] == 1);
    model_plot(expected_row);
#ifdef SAT_VDP1_PROFILE
    CHECK(vp_current[VP_CLEAR_PIXELS] == (unsigned int)(SAT_GFX_SCREEN_W * (SAT_GFX_SCREEN_H - expected_row)));
#endif
}

static void warmup(void)
{
    submit(0);
    boundary(2);
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0 && !erase_primed);
    model_change(1);
    CHECK(!erase_primed); /* OUT alone is insufficient; require CEF clear too */
    submit(0);
    CHECK(erase_primed);
}

static void alternating_buffers(unsigned char *pack)
{
    int n;
    reset_driver(pack);
    warmup(); /* boot buffers and previously latched erase registers are unknown */
    for (n = 0; n < 8; n++)
    {
        boundary(2);
        CHECK(erase_armed == plot_started && erase_ready == 0);
        /* A stale pending out interrupt during blank cannot certify erase. */
        sat_gfx_vblank_out();
        CHECK(erase_armed == plot_started && erase_ready == 0);
        CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 8);
        model_change(1);
        CHECK(erase_ready == plot_shown && erase_armed == 0);
        CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0);
        submit(SAT_VDP1_ERASE_ROWS);
    }
    CHECK(sat_gfx_erase_full == 2 && sat_gfx_erase_reduced == 8);
}

static void held_and_missing_out(unsigned char *pack)
{
    static unsigned short held[SAT_GFX_SCREEN_W * SAT_GFX_SCREEN_H];
    reset_driver(pack);
    warmup();
    memcpy(held, erase_fb[front], sizeof held);
    boundary(0);
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 2);
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0 && erase_armed == 0);
    CHECK(!memcmp(held, erase_fb[front], sizeof held));
    boundary(2);
    model_change(0); /* out IRQ lost: hardware changed, CPU cannot certify it */
    CHECK(erase_armed == plot_started && erase_ready == 0);
    memcpy(held, erase_fb[front], sizeof held);
    boundary(0); /* no new plot; IN must turn VBE off before another erase */
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0 && erase_armed == 0);
    CHECK(erase_ready == 0 && erase_suppressed && sat_gfx_erase_canceled == 1);
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 2);
    sat_gfx_host_vdp2r[0x04 / 2] = 0;
    sat_gfx_vblank_out(); /* late OUT cannot resurrect the stale certificate */
    CHECK(erase_ready == 0);
    CHECK(!memcmp(held, erase_fb[front], sizeof held));
    submit(0);
    boundary(2); model_change(1); submit(0);
    boundary(2); model_change(1); submit(SAT_VDP1_ERASE_ROWS);
}

static void conservative_fallbacks(unsigned char *pack)
{
    reset_driver(pack);
    warmup(); boundary(2); model_change(1);
    erase_ready = plot_shown + 1; /* correct physical buffer needs correct serial */
    submit(0);
    boundary(2); model_change(1);
    erase_ready = 0; /* also the conservative serial rollover representation */
    submit(0);
    boundary(2); model_change(1);
    /* Actual command local origin, not a later copy of the menu variable. */
    w16(V1 + table_base + 32 + 12, 1);
    submit(0);
    w16(V1 + (table_base ^ TABLE_B) + 32 + 12, 0);
    boundary(2); model_change(1);
    w16(V1 + table_base + 32 + 14, 1);
    submit(0);
    w16(V1 + (table_base ^ TABLE_B) + 32 + 14, 0);
}

static void latch_recovery(unsigned char *pack)
{
    reset_driver(pack);
    warmup(); boundary(2); model_change(1);
    /* Restored chip state reports stale CEF after the certificate was made. */
    sat_gfx_host_vdp1r[0x10 / 2] = 2;
    clock_now = 65530; clock_step = 1000;
    submit(0);
    CHECK(erase_ready == 0 && erase_suppressed);
    CHECK(sat_gfx_host_vdp1r[FBCR / 2] == 3);
    /* A later complete erase/change can establish ownership afresh. */
    clock_step = 1;
    boundary(2); model_change(1); submit(0);
    boundary(2); model_change(1); submit(SAT_VDP1_ERASE_ROWS);
}

static void missing_end_replot(unsigned char *pack)
{
    unsigned long prior_base;
    unsigned long before, next_table;
    static unsigned char prior_table[0x8000];
    reset_driver(pack);
    warmup(); boundary(2); model_change(1); submit(SAT_VDP1_ERASE_ROWS);
    prior_base = table_base ^ TABLE_B;
    before = plot_started; next_table = table_base;
    memcpy(prior_table, V1 + prior_base, sizeof prior_table);
    boundary(0);
    clock_now = 65530; clock_step = 1000;
    sat_gfx_draw(); /* bounded retry of the same submitted list */
    CHECK(plot_started == before && table_base == next_table);
    CHECK(sat_gfx_host_vdp1r[PTMR / 2] == 1);
    CHECK(!memcmp(prior_table, V1 + prior_base, sizeof prior_table));
    CHECK(erase_ready == 0 && erase_suppressed);
    clock_step = 1;
    boundary(2); model_change(1); submit(0);
    boundary(2); model_change(1); submit(SAT_VDP1_ERASE_ROWS);
}

static void abandoned_build_and_reinit(unsigned char *pack)
{
    unsigned long before;
    reset_driver(pack);
    warmup();
    before = table_base;
    sat_gfx_host_vdp1r[0x10 / 2] = 2; /* done, not yet shown */
    sat_gfx_host_vdp1r[PTMR / 2] = 0;
    clock_step = 1000;
    sat_gfx_draw();
    CHECK(plot_started == 2 && table_base == before);
    CHECK(sat_gfx_host_vdp1r[PTMR / 2] == 0 && erase_ready == 0);
    clock_step = 1;
    boundary(2); model_change(1); submit(SAT_VDP1_ERASE_ROWS);
    boundary(2); /* reinitialization with an erase armed must clear VBE */
    CHECK(erase_armed != 0);
    CHECK(sat_gfx_init(pack));
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0);
    CHECK(erase_armed == 0 && erase_ready == 0 && erase_suppressed == 0 && erase_primed == 0);
}

static void suspend_for_disc_load(unsigned char *pack)
{
    reset_driver(pack);
    warmup(); boundary(2);
    CHECK(erase_armed && sat_gfx_host_vdp1r[TVMR / 2] == 8);
    clock_now = 65530; clock_step = 2;
    tick_calls = 0; leave_blank_call = 4;
    CHECK(sat_gfx_erase_suspend());
    CHECK(tick_calls == 4 && sat_gfx_host_vdp2r[0x04 / 2] == 0);
    CHECK(!erase_armed && !erase_ready && erase_suppressed);
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0);
    reset_driver(pack);
    warmup(); boundary(2);
    clock_now = 65530; clock_step = 1000; tick_calls = 0;
    CHECK(!sat_gfx_erase_suspend()); /* stuck TVSTAT and 16-bit clock wrap */
    CHECK(tick_calls < 12 && tick_calls > 1);
    CHECK(erase_armed && !erase_ready);
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 8); /* no write in an unknown window */
    boundary(0); /* caller restores IRQs; next IN safely cancels the old erase */
    CHECK(!erase_armed && !erase_ready && erase_suppressed);
    CHECK(sat_gfx_host_vdp1r[TVMR / 2] == 0);
}

int main(void)
{
    unsigned char *pack = make_pack(8000);
    alternating_buffers(pack);
    held_and_missing_out(pack);
    conservative_fallbacks(pack);
    latch_recovery(pack);
    missing_end_replot(pack);
    abandoned_build_and_reinit(pack);
    suspend_for_disc_load(pack);
    free(pack);
    printf(fails ? "FAILED %d\n" : "VDP1 hardware erase HOST coverage tests passed\n", fails);
    return fails != 0;
}
