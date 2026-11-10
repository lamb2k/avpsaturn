/* Host test of the home LIVES option (SAT_HOME): menu values, the arcade default shown, and the stock the start routine wrapper writes
   (kernel.c f_212f8: lifted body, then sat_home_start_stock() >= 0 is written to the player's +0xf1).
   Build: gcc -DSAT_HOME -w tests/home_lives_test.c -o home_lives_test && ./home_lives_test */
#include <stdio.h>
#include "../saturn/rt/home.c"
#include "../saturn/rt/home_cold.c"
u8 RAMB[0x10000];
u16 snap[16];   /* sat_gfx.c's snapshot, for sat_home_snap_frame (home_cold.c) */
u32 sat_pad_raw = 0xffff;
volatile u32 sat_duel_on;
__typeof__(sat_rounds) sat_rounds;
int sat_gfx_nudge_x, sat_gfx_nudge_y;
static u8 block[128];
int sat_home_get(int o) { return block[o]; }
void sat_home_set(int o, int v) { block[o] = (u8)v; block[o + 0x30] = (u8)v; }
void sat_home_restart(void) { }
u32 sat_vblanks_now(void) { static u32 v; return v++; }
void sat_audio_io_write8(unsigned long a, unsigned long v) { (void)a; (void)v; }
static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL %s: ", #c); printf(__VA_ARGS__); printf("\n"); } } while (0)
/* The arcade routine as the ROM has it (0x212f8, lifted c4.c), for the stock only: table at 0x21330 by ff81d1, +1 for 4..7 with +0xff set. */
static u8 arcade_stock(int lives_byte, int flag) { u8 s = start_stock[lives_byte & 7]; if (lives_byte >= 4 && flag) s++; return s; }
/* kernel.c's wrapper over it. */
static u8 started(int lives_byte, int flag) { u8 s = arcade_stock(lives_byte, flag); int o = sat_home_start_stock(); return o >= 0 ? (u8)o : s; }
int main(void)
{
    const Opt *lives = 0;
    int i, b, f;
    for (i = 0; i < OPTS; i++) if (opts[i].off == 0xff) lives = &opts[i];
    CHECK(lives && lives->n == 9, "LIVES row with 9 values");
    /* Default: nothing chosen, the start stock is the arcade's for every lives byte and flag. */
    for (b = 0; b < 8; b++) for (f = 0; f < 2; f++) CHECK(started(b, f) == arcade_stock(b, f), "default b=%d f=%d", b, f);
    /* The row shows the arcade's lives (stock + 1) until one is chosen. */
    for (b = 0; b < 8; b++) { sat_home_set(0x12, b); CHECK(opt_get(lives) + 1 == start_stock[b] + 1, "shown b=%d", b); }
    sat_home_set(0x12, 0);
    CHECK(opt_get(lives) == 0, "arcade default shows LIVES 1");
    /* Choosing 1 to 9 writes stock 0 to 8 in arcade and boss rush, nothing in the duel. */
    for (i = 0; i < 9; i++) {
        opt_set(lives, i);
        CHECK(sat_home_cfg.lives == i + 1 && opt_get(lives) == i, "set %d", i + 1);
        for (b = 0; b < 8; b++) CHECK(started(b, 1) == i, "LIVES %d b=%d", i + 1, b);
        sat_duel_on = 1; CHECK(started(3, 0) == arcade_stock(3, 0), "duel untouched LIVES %d", i + 1); sat_duel_on = 0;
    }
    /* The game's own settings bytes are not touched by LIVES. */
    for (i = 0; i < 128; i++) if (i != 0x12 && i != 0x42) CHECK(block[i] == 0, "block byte %d", i);
    printf("%s (%d failures)\n", fails ? "FAIL" : "PASS", fails);
    return fails != 0;
}

