/* Synthetic HOST regression. No ROM bytes or captured data are used here.
   Include the production guest implementation so the exercised clock is the
   shipped code, with generated synthetic tables supplied by the Python test. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "../saturn/guests/wolverine/wolverine.c"

u8 RAMB[65536];
u8 *PAGE[256];
u8 sat_guest_sel;
static u8 test_rom[65536];
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } TestCpu;
static TestCpu cpu;
TestCpu *R = &cpu;
extern void f_195ec(void);
static int native_calls, retire_after, enter_action, clobber_a6;
static int player_index;

static void state(int i, int a, int b, int c)
{
    R8(PL(i)) = 1;
    R8(PL(i) + WV_CHAR_OFF) = WV_CHAR_SCH;
    R8(PL(i) + 4) = (u8)a;
    R8(PL(i) + 5) = (u8)b;
    R8(PL(i) + 6) = (u8)c;
}

/* The native player update is deliberately tiny. It lets the test vary its
   actual lifetime independently of the guest's estimated native tick count. */
void lifted_195ec(void)
{
    native_calls++;
    if (enter_action) {
        state(player_index, 2, 0, enter_action);
        enter_action = 0;
    } else if (retire_after && native_calls == retire_after) {
        state(player_index, 2, 0, 0);
    }
    if (clobber_a6) R->a[6] = PL(1 - player_index);
}

static void update(void)
{
    R->a[6] = PL(player_index);
    f_195ec();
}

static void fresh(int action)
{
    memset(RAMB, 0, sizeof(RAMB));
    memset(&cpu, 0, sizeof(cpu));
    PAGE[0] = test_rom;
    PAGE[0xff] = RAMB;
    sat_guest_sel = 1;
    wv_reset(0); wv_reset(1);
    player_index = native_calls = retire_after = enter_action = clobber_a6 = 0;
    state(0, 2, 0, action);
}

static void test_length(int action, int move, int native_length, int expected)
{
    int frame, finished = 0;
    fresh(action);
    if (move == WV_HP) { chain_[0] = 2; landed_[0] = 1; }   /* the third attack of the chain */
    retire_after = native_length;
    for (frame = 1; frame <= expected; frame++) {
        update();
        assert(cur_[0] == move);
        assert(wall_[0] == frame);
        if (!R8(PL(0) + 6) && !finished) finished = frame;
        if (frame == 1) assert(step_[0] == 0);
        if (frame == 2) assert(step_[0] == 1);
    }
    assert(native_calls == native_length);
    assert(finished > 0 && finished <= expected);
    if (action == 6 && native_length == 15) assert(finished == 51);
    update();
    assert(cur_[0] == WV_IDLE && wall_[0] == 1);
    assert(native_calls == native_length + 1);
}

static void test_native_entry_and_register_clobber(void)
{
    fresh(0);
    enter_action = 6;
    clobber_a6 = 1;
    update();
    assert(cur_[0] == WV_LP && step_[0] == 0 && wall_[0] == 1);
    assert(cur_[1] == 255);
    update();
    assert(cur_[0] == WV_LP && step_[0] == 1 && wall_[0] == 2);
    assert(native_calls == 1);
}

static void test_interruptions(void)
{
    int before;
    fresh(0x0e);
    retire_after = 6;
    while (!recovery_[0]) update();
    before = native_calls;
    state(0, 2, 2, 6);
    R16(PL(0) + 0x40) = 17;
    update();
    assert(cur_[0] == WV_HIT_ETC && !recovery_[0]);
    assert(native_calls == before + 1 && R16(PL(0) + 0x40) == 17);
    state(0, 4, 0, 0);
    update();
    assert(cur_[0] == WV_KNOCKDOWN && !recovery_[0]);
    state(0, 2, 4, 0);
    update();
    assert(cur_[0] == WV_THROW && !recovery_[0]);
    state(0, 8, 0, 0);
    update();
    assert(cur_[0] == WV_WALK && !recovery_[0]);
}

static void test_restart_and_reset(void)
{
    u16 pad = 0xffff;
    int k;
    fresh(6);
    update();
    assert(cur_[0] == WV_LP);   /* the chain starts with the light punch */
    state(0, 2, 0, 0);  /* external state change, not a native retirement */
    update();
    landed_[0] = 1;   /* every attack lands (SAT_WV_NATIVE_TIMING: the chain goes on only from a landed hit) */
    state(0, 2, 0, 6);
    update();
    assert(cur_[0] == WV_LP && step_[0] == 0 && wall_[0] == 1);   /* light, light */
    state(0, 2, 0, 0);
    update();
    landed_[0] = 1;   /* every attack lands (SAT_WV_NATIVE_TIMING: the chain goes on only from a landed hit) */
    state(0, 2, 0, 6);
    update();
    assert(cur_[0] == WV_HP && step_[0] == 0 && wall_[0] == 1);   /* then the heavy punch */
    state(0, 2, 0, 0);
    update();
    landed_[0] = 1;   /* every attack lands (SAT_WV_NATIVE_TIMING: the chain goes on only from a landed hit) */
    state(0, 2, 0, 6);
    update();
    assert(cur_[0] == WV_HK && step_[0] == 0 && wall_[0] == 1);   /* then the kick finisher */
    state(0, 2, 0, 0);
    update();
    landed_[0] = 1;   /* every attack lands (SAT_WV_NATIVE_TIMING: the chain goes on only from a landed hit) */
    state(0, 2, 0, 6);
    update();
    assert(cur_[0] == WV_LP && chain_[0] == 1);   /* and round again */
    for (k = 0; k < 4; k++) { state(0, 2, 0, 0); update(); landed_[0] = 1; state(0, 2, 0, 6); update(); }
    state(0, 2, 0, 0);
    for (k = 0; k < WV_CHAIN_GAP + 2; k++) update();
    landed_[0] = 1;   /* every attack lands (SAT_WV_NATIVE_TIMING: the chain goes on only from a landed hit) */
    state(0, 2, 0, 6);
    update();
    assert(cur_[0] == WV_LP && chain_[0] == 1);   /* a pause starts the chain over */
    atk_cache[0][3] = 9;
    dir_hist[0][0] = 2;
    R8(PL(0)) = 0;
    sat_guest_wolverine_pad(&pad);
    assert(cur_[0] == 255 && !atk_cache[0][3] && !dir_hist[0][0]);
    landed_[0] = 1;   /* every attack lands (SAT_WV_NATIVE_TIMING: the chain goes on only from a landed hit) */
    state(0, 2, 0, 6);
    update();
    assert(cur_[0] == WV_LP && wall_[0] == 1);
    sat_guest_sel = 0;
    sat_guest_wolverine_pad(&pad);
    assert(cur_[0] == 255 && wv_step_now[0] == 0xffff && pad == 0xffff);
    sat_guest_sel = 1;
    update();
    assert(cur_[0] == WV_LP && wall_[0] == 1);
}


/* Schaefer's attack state does not leave 020006 while the button is tapped: each 15 native ticks of it is the next attack of the chain. */
static void test_continuous_chain(void)
{
    static const u8 want[5] = {WV_LP, WV_LP, WV_HP, WV_HK, WV_LP};
    int k, n = 0;
    u16 last = 0;
    fresh(0);
    enter_action = 6;
    for (k = 0; k < 600 && n < 5; k++) {
        landed_[0] = 1;
        update();
        if (wall_[0] == 1 && last != 1) assert(cur_[0] == want[n++]);
        last = wall_[0];
    }
    assert(n == 5);
}


#ifdef SAT_WV_NATIVE_TIMING
/* the chain goes on only from a landed hit: a whiff starts it over with the light punch */
static void test_chain_on_hit(void)
{
    fresh(6);
    update();
    assert(cur_[0] == WV_LP && chain_[0] == 1);
    landed_[0] = 1; state(0, 2, 0, 0); update(); state(0, 2, 0, 6); update();
    assert(cur_[0] == WV_LP && chain_[0] == 2);
    landed_[0] = 1; state(0, 2, 0, 0); update(); state(0, 2, 0, 6); update();
    assert(cur_[0] == WV_HP && chain_[0] == 3);
    state(0, 2, 0, 0); update(); state(0, 2, 0, 6); update();   /* the heavy punch whiffed */
    assert(cur_[0] == WV_LP && chain_[0] == 1);
}
#endif
/* KO: the game's death blink toggles the block's byte +1 every frame in state 04. The clock must run through it, once, and the blank frames must not
   restart it or draw his body. */
static void test_ko_blink(void)
{
    int k, hidden = 0;
    u16 pad = 0xffff;
    u8 objects[512], palette[1024];
    void *rom = mmap((void *)0x02400000u, 0x200000, PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    assert(rom != MAP_FAILED);
    fresh(0);
    state(0, 2, 0, 2); update();
    state(0, 4, 0, 0); update();
    assert(cur_[0] == WV_KNOCKDOWN && wall_[0] >= 1);
    for (k = 0; k < 90; k++) {
        u16 w = wall_[0];
        R8(PL(0) + 5) = (u8)(k < 10 ? 2 : 4);
        R8(PL(0) + WV_CHAR_OFF) = (u8)((k & 1) ? WV_CHAR_SCH : 0);   /* the blink */
        sat_guest_wolverine_pad(&pad);
        update();
        assert(cur_[0] == WV_KNOCKDOWN && wall_[0] == w + 1);
        memset(objects, 0, sizeof(objects));
        if (!(k & 1)) { assert(wv_blank(0)); hidden++; assert(sat_guest_objects(objects, 0, 64, palette) == 0); }
        else assert(sat_guest_objects(objects, 0, 64, palette) > 0);
    }
    assert(hidden == 45);
    R8(PL(0)) = 0;   /* the slot is cleared after the KO: his clock resets */
    sat_guest_wolverine_pad(&pad);
    assert(cur_[0] == 255 && !wvid_[0]);
    assert(munmap(rom, 0x200000) == 0);
}
static void test_draws_do_not_tick(void)
{
    u8 objects[512], palette[1024];
    u16 wall, published;
    u8 move, step, age;
    int k;
    void *rom = mmap((void *)0x02400000u, 0x200000, PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    assert(rom != MAP_FAILED);
    fresh(6);
    memset(objects, 0, sizeof(objects));
    sat_guest_objects(objects, 0, 64, palette);
    assert(cur_[0] == 255 && !wall_[0] && !chain_[0]);
    update();
    wall = wall_[0]; move = cur_[0]; step = step_[0]; age = left_[0];
    published = wv_step_now[0];
    for (k = 0; k < 17; k++) sat_guest_objects(objects, 0, 64, palette);
    assert(wall_[0] == wall && step_[0] == step && left_[0] == age);
    assert(wv_step_now[0] == published);
    /* A vblank can interrupt wv_begin_move between changing cur_ and resetting
       step_. Deliberately make that partial pair invalid: render must consume
       the last published aligned word, not either mutable clock field. */
    cur_[0] = WV_CROUCH; step_[0] = 255;
    sat_guest_objects(objects, 0, 64, palette);
    assert((objects[4] << 8 | objects[5]) == 107);
    assert(wv_step_now[0] == published);
    cur_[0] = move; step_[0] = step;
    assert(munmap(rom, 0x200000) == 0);
}

int main(void)
{
#ifdef WV_MEASURE
    fresh(0x0e);
    retire_after = 6;
    while (native_calls < 6) update();
    assert(!recovery_[0] && cur_[0] == WV_IDLE);
    puts("Wolverine clock: HOST synthetic PASS (WV_MEASURE has no holds)");
    return 0;
#endif
    test_length(6, WV_HP, 15, 51);
    test_length(6, WV_HP, 10, 51);
    test_length(0x0e, WV_HK, 6, 28);
    test_length(0x0e, WV_HK, 32, 32);
    test_native_entry_and_register_clobber();
    test_interruptions();
    test_restart_and_reset();
    test_continuous_chain();
#ifdef SAT_WV_NATIVE_TIMING
    test_chain_on_hit();
#endif
    test_draws_do_not_tick();
    test_ko_blink();
    puts("Wolverine clock: HOST synthetic PASS (lengths, poses, interrupts, reset, draw independence)");
    return 0;
}
