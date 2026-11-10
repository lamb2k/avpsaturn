/* Host test of the stage select names and the ENDING entry (SAT_HOME): the arcade's stage/area numbering, the boss rows, and the ending poll
   (home.c ending_poll) that clears the stage 24 boss for the arcade's own ending.
   Build: gcc -DSAT_HOME -w tests/home_stage_menu_test.c -o home_stage_menu_test && ./home_stage_menu_test */
#include <stdio.h>
#include <string.h>
#include "../saturn/rt/home.c"
#include "../saturn/rt/home_cold.c"
u8 RAMB[0x10000];
u32 sat_pad_raw = 0xffff;
volatile u32 sat_duel_on;
__typeof__(sat_rounds) sat_rounds;
int sat_gfx_nudge_x, sat_gfx_nudge_y;
void sat_home_restart(void) { }
static u32 now;
u32 sat_vblanks_now(void) { return now; }
void sat_audio_io_write8(unsigned long a, unsigned long v) { (void)a; (void)v; }
int sat_home_get(int o) { (void)o; return 0; }
void sat_home_set(int o, int v) { (void)o; (void)v; }
static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL %s: ", #c); printf(__VA_ARGS__); printf("\n"); } } while (0)
int main(void)
{
    /* The game's own tables: round of each stage word (0xcca0, word 02 to 24), boss names (0xac6c8). */
    static const char *const want[STAGES] = { "1-1", "1-2", "2-1", "2-2", "3-1", "4-1", "4-2", "5-1", "6-1", "6-2", "6-3", "6-4", "6-5", "7-1", "7-2", "7-3", "7-4", "7-5" };
    static const char *const row2[STAGES] = { "1 OF 2", "CHRYSALIS", "1 OF 2", "RAZOR CLAWS", "ARACHNOID", "1 OF 2", "ALIEN QUEEN", "POWER LOADER", "1 OF 5", "SPECIAL STAGE", "3 OF 5", "4 OF 5", "MAD PREDATOR", "1 OF 5", "2 OF 5", "3 OF 5", "4 OF 5", "ALIEN QUEEN" };
    int st, i;
    for (st = 1; st <= STAGES; st++) {
        char b[8], nb[8];
        const char *tag, *name;
        stage_label(st, b, nb, &tag, &name);
        CHECK(!strcmp(b, want[st - 1]), "stage %d is %s, want %s", st, b, want[st - 1]);
        CHECK(name && !strcmp(name, row2[st - 1]), "row 2 of stage %d is %s", st, name ? name : "none");
        CHECK(strlen(b) == 3 && (!name || strlen(name) <= 13), "fits");
    }
    /* Round numbers climb by at most one and end at 7: the seven STAGEs. */
    for (i = 1; i < STAGES; i++) CHECK(stage_round[i] == stage_round[i - 1] || stage_round[i] == stage_round[i - 1] + 1, "round step %d", i);
    CHECK(stage_round[STAGES - 1] == 6, "seven rounds");

    /* ENDING poll: nothing until the arena 24 file has loaded and the game is in its play state (ff8004 = 4, ff8008 = 4); then boss-down and stage clear. */
    sat_rounds.loads = 5; sat_home_arm_ending();     /* armed at the stage select with 5 loads behind it */
    CHECK(sat_home_ending == 6, "armed with the load count");
    G(0xff81b0) = 1; ending_poll();                 /* start path still in attract: waits */
    CHECK(sat_home_ending == 6 && !G(0xff81f3), "waits in attract");
    G(0xff81b0) = 0; G(0xff81e9) = 0x24; G(0xff8001) = 2; G(0xff8380) = 1; G(0xff8005) = 4; G(0xff8009) = 4;
    ending_poll();                                   /* the arena file has not loaded yet */
    CHECK(!G(0xff81f3), "no clear before the arena file loads");
    sat_rounds.loads = 6; G(0xff8009) = 0; ending_poll();
    CHECK(!G(0xff81f3), "no clear during the arena setup");
    G(0xff8009) = 4; G(0xff81e9) = 0x22; ending_poll();
    CHECK(!G(0xff81f3), "only stage 24");
    G(0xff81e9) = 0x24; ending_poll();
    CHECK(G(0xff81f3) == 1 && G(0xff822a) == 1, "boss down and stage clear in the play state");
    G(0xff81f3) = 0; G(0xff822a) = 0; G(0xff8009) = 6; G(0xff81e9) = 0x26; ending_poll();   /* the clear is running / the word moved on */
    CHECK(!G(0xff81f3), "stops once the game left its play state");
    G(0xff81b0) = 1; ending_poll();                  /* game over, back at the title */
    CHECK(sat_home_ending == 0, "ends with the game");
    printf("%s (%d failures)\n", fails ? "FAIL" : "PASS", fails);
    return fails != 0;
}
