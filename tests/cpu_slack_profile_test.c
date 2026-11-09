/* HOST synthetic: actual recorder and the kernel's extracted idle sampler. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned int u32;
#include "../saturn/rt/cpu_slack_profile.h"

static struct { u32 vblanks; } sat_dbg;
static volatile int game_done;
static u32 gfx_handed, gfx_done, test_tick;
static unsigned char test_ftcsr;
static int interrupt_in_read;
#define FTCSR test_ftcsr
#define UNCACHED(v) (v)
static u32 frt(void)
{
    if (interrupt_in_read) {
        sat_dbg.vblanks++;
        game_done = 0;
    }
    return test_tick;
}
/* Python extracts the production function body, without rewriting it. */
#include "cpu_slack_mark_idle.inc"

static void start(unsigned int vblank)
{
    sat_dbg.vblanks = vblank;
    game_done = 0;
    cpu_slack_begin(vblank, 0, 0xff010002u);
    cpu_slack_handoff(12, 300);
    cpu_slack_layers(800);
    cpu_slack_irq(900, 0);
}

int main(int argc, char **argv)
{
    volatile unsigned int *row;
    FILE *out;
    unsigned int tag;
    memset((void *)sat_cpu_slack, 0, sizeof sat_cpu_slack);
    assert(sizeof(unsigned int) == 4);

    start(1);
    gfx_handed = 12; gfx_done = 11; test_tick = 2200;
    game_done = 1; cpu_slack_mark_idle();
    cpu_slack_close(3495, game_done, 0, 12, 11);
    row = sat_cpu_slack[1 & (SAT_CPU_SLACK_DEPTH - 1)];
    assert(row[CS_VBLANK] == 1 && row[CS_DONE] == 2200);
    assert(row[CS_FLAGS] == (CS_FINISHED | CS_HANDED | CS_BUSY_DONE | CS_BUSY_END));
    assert(row[CS_PERIOD] - row[CS_DONE] == 1295);

    start(2);
    cpu_slack_close(3495, 0, 0, 12, 12);
    row = sat_cpu_slack[2 & (SAT_CPU_SLACK_DEPTH - 1)];
    assert((row[CS_FLAGS] & CS_OVERRUN) && !(row[CS_FLAGS] & CS_FINISHED));
    assert(row[CS_DONE] == CS_UNKNOWN);

    /* An IRQ inside the timer read cannot label an old completion as new. */
    start(3);
    game_done = 1; interrupt_in_read = 1; test_tick = 10;
    tag = cpu_slack_done[0]; cpu_slack_mark_idle();
    assert(cpu_slack_done[0] == tag);
    interrupt_in_read = 0;
    cpu_slack_close(3495, 1, 0, 12, 12);
    assert(sat_cpu_slack[3 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_UNPAIRED_DONE);

    /* Mid-publication: new fields with an invalid tag never count as idle. */
    start(4);
    cpu_slack_done[0] = 0; cpu_slack_done[1] = 1; cpu_slack_done[2] = 0;
    cpu_slack_close(3495, 1, 0, 12, 12);
    assert(sat_cpu_slack[4 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_UNPAIRED_DONE);
    /* A stale publication resumed after the IRQ is equally unusable. */
    cpu_slack_publish_done(4, 3400, 0);
    start(5);
    cpu_slack_close(3495, 1, 0, 12, 12);
    assert(sat_cpu_slack[5 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_UNPAIRED_DONE);

    start(6);
    game_done = 1; test_tick = 1300; test_ftcsr = 2;
    cpu_slack_mark_idle(); cpu_slack_close(3400, 1, 0, 12, 12);
    assert(sat_cpu_slack[6 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_TIMER_WRAP);
    test_ftcsr = 0;
    start(7);
    cpu_slack_publish_done(7, 1000, 0);
    cpu_slack_close(50, 1, CS_TIMER_WRAP, 12, 12);
    assert(sat_cpu_slack[7 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_BAD_ORDER);

    start(8);
    cpu_slack_publish_done(8, 800, 0);
    cpu_slack_close(3495, 1, 0, 12, 12);
    assert(sat_cpu_slack[8 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_BAD_ORDER);

    start(9);
    cpu_slack_irq(1000, 1);
    cpu_slack_close(3495, 1, 0, 12, 12);
    assert(sat_cpu_slack[9 & (SAT_CPU_SLACK_DEPTH - 1)][CS_FLAGS] & CS_HOME);
    assert(sat_cpu_slack[9 & (SAT_CPU_SLACK_DEPTH - 1)][CS_DONE] == 1000);

    if (argc == 2) {
        out = fopen(argv[1], "wb");
        assert(out);
        assert(fwrite((const void *)sat_cpu_slack, sizeof sat_cpu_slack, 1, out) == 1);
        assert(fclose(out) == 0);
    }
    printf("CPU slack HOST PASS; declared state %lu bytes\n",
        (unsigned long)(sizeof sat_cpu_slack + sizeof cpu_slack_current + sizeof cpu_slack_done));
    return 0;
}
