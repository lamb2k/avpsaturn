/* Synthetic HOST regression for the native Wolverine pieces in wolverine.c (SAT_WV_NATIVE). No ROM bytes or captured data: the data patch table,
   the move tables and the memory are synthetic. It includes wolverine.c itself, so the shipped code is what runs. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../saturn/guests/wolverine/wolverine.c"

u8 RAMB[65536];
u8 *PAGE[256];
u8 sat_guest_sel;
static u8 test_rom[0x200000];
u8 *const wv_host_rom = test_rom;

static void fresh(void)
{
    memset(RAMB, 0, sizeof RAMB);
    memset(test_rom, 0, sizeof test_rom);
    PAGE[0xff] = RAMB;
    sat_guest_sel = 1;
    wv_reset(0); wv_reset(1);
    wv_patch_bad = 0;
}

static void set_rom(int now)
{
    int k;
    for (k = 0; k < WV_PATCHES; k++) {
        u16 v = now ? wv_patch_tab[k].now : wv_patch_tab[k].orig;
        test_rom[wv_patch_tab[k].addr] = (u8)(v >> 8); test_rom[wv_patch_tab[k].addr + 1] = (u8)v;
    }
}

static int rom_is(int now)
{
    int k;
    for (k = 0; k < WV_PATCHES; k++) {
        u16 v = now ? wv_patch_tab[k].now : wv_patch_tab[k].orig;
        if (test_rom[wv_patch_tab[k].addr] != (u8)(v >> 8) || test_rom[wv_patch_tab[k].addr + 1] != (u8)v) return 0;
    }
    return 1;
}

static void test_patch(void)
{
    fresh();
    set_rom(0);
    wv_patch_sync(1);
    assert(rom_is(1));
    wv_patch_sync(1);   /* idempotent */
    assert(rom_is(1) && wv_patch_bad == 0);
    wv_patch_sync(0);   /* exact restore */
    assert(rom_is(0));
    wv_patch_sync(0);
    assert(rom_is(0) && wv_patch_bad == 0);
    /* a stage load restores the page: patched again before the next read */
    wv_patch_sync(1);
    test_rom[wv_patch_tab[0].addr] = (u8)(wv_patch_tab[0].orig >> 8); test_rom[wv_patch_tab[0].addr + 1] = (u8)wv_patch_tab[0].orig;
    wv_patch_sync(1);
    assert(rom_is(1));
    /* an unexpected layout is refused, not patched */
    test_rom[wv_patch_tab[1].addr] = 0x77;
    wv_patch_sync(1);
    assert(wv_patch_bad == 1 && test_rom[wv_patch_tab[1].addr] == 0x77);
    wv_patch_sync(0);
    assert(test_rom[wv_patch_tab[1].addr] == 0x77);
    /* the tick hook patches for the selected guest and undoes it when the guest is off */
    fresh();
    set_rom(0);
    (void)sat_guest_wolverine_tick(PL(0));
    assert(rom_is(1));
    sat_guest_sel = 0;
    (void)sat_guest_wolverine_tick(PL(0));
    assert(rom_is(0));
}

static void test_warp(void)
{
    /* synthetic lp: pose 7 for 1 frame, the hit pose for 6, pose 9 for 21, then the stance. Agreed 2 / 4 / 6. */
    static const int want[12] = {0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2};
    int w, s, a, r, t, shown[12];
    assert(wv_native_sar(WV_LP, &s, &a, &r) && s == 2 && a == 4 && r == 6);
    assert(wv_move_len(WV_LP) == 12 && wv_move_len_capture(WV_LP) == 28);
    assert(wv_native_sar(WV_HP, &s, &a, &r) && s + a + r == 16);
    assert(!wv_native_sar(WV_HK, &s, &a, &r) && wv_move_len(WV_HK) == wv_move_len_capture(WV_HK));
    for (w = 0; w < 12; w++) assert(wv_warp_step(WV_LP, w) == want[w]);
    assert(wv_warp_step(WV_LP, 12) == 3 && wv_warp_step(WV_LP, 40) == 3);   /* past its length: the ready stance */
    /* the published step advances once per call, over the agreed length */
    fresh();
    wv_begin_move(0, WV_LP);
    for (t = 0; t < 12; t++) { wv_advance(0); shown[t] = (int)wv_step_now[0] - (int)wv_move_start[WV_LP]; }
    for (t = 0; t < 12; t++) assert(shown[t] == want[t]);
    assert(wall_[0] == 12);
    /* no hit box while the agreed startup runs */
    cur_[0] = WV_LP; wall_[0] = 1; assert(wv_in_startup(0));
    wall_[0] = 2; assert(wv_in_startup(0));
    wall_[0] = 3; assert(!wv_in_startup(0));
    cur_[0] = WV_HK; wall_[0] = 1; assert(!wv_in_startup(0));
}

static void test_fork_and_walk(void)
{
    fresh();
    R8(PL(0)) = 1; R8(PL(0) + 1) = WV_CHAR_SCH;
    assert(sat_wv_fork_on(PL(0), 0) && sat_wv_fork_on(PL(0), 1));
    R8(PL(0) + 1) = 2;                       /* another character: the stock routine */
    assert(!sat_wv_fork_on(PL(0), 0));
    R8(PL(0) + 1) = WV_CHAR_SCH; sat_guest_sel = 0;
    assert(!sat_wv_fork_on(PL(0), 0));
    assert(!sat_wv_fork_on(0xff9a00u, 0));   /* an enemy block is never a Wolverine player */
    /* his walk weight is Schaefer's: the post-update hook adds nothing to the native step */
    fresh();
    R8(PL(0)) = 1; R8(PL(0) + 1) = WV_CHAR_SCH; R8(PL(0) + 4) = 2; R8(PL(0) + 6) = 2;
    xb_[0] = 100; zb_[0] = 50;
    R16W(PL(0) + 0x10, 110); R16W(PL(0) + 0x14, 50); R16W(PL(0) + 0x18, 50);
    wv_speed(0);
    assert(R16(PL(0) + 0x10) == 110 && R16(PL(0) + 0x18) == 50 && sx_[0] == 0);
}

int main(void)
{
    test_patch();
    test_warp();
    test_fork_and_walk();
    printf("wolverine native test ok\n");
    return 0;
}
