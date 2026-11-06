/* Host tier: interactive tick rule from current input only.
 * argv[1]: idle | source | bot; argv[2]: frame count. Prints state rows. */
#include "round1.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static AvspRound1Runtime runtime;

static unsigned int alive(void)
{
    unsigned int pool, slot, n = 0u;
    for (pool = 0u; pool < AVSP_ROUND1_POOL_COUNT; ++pool)
        for (slot = 0u; slot < runtime.pools[pool].capacity; ++slot)
            if (runtime.pools[pool].records[slot].active != 0u)
                ++n;
    return n;
}

static unsigned short bot(unsigned int frame)
{
    unsigned short m = AVSP_PW_INPUT_RIGHT;
    if (frame % 11u == 0u)
        m = (unsigned short)(m | AVSP_PW_INPUT_ATTACK);
    if (frame % 240u < 40u)
        m = (unsigned short)((frame % 7u) == 0u ? AVSP_PW_INPUT_ATTACK : 0u);
    return m;
}

int main(int argc, char **argv)
{
    AvspRound1TickRule rule;
    unsigned int frame;
    const char *mode = argc > 1 ? argv[1] : "idle";
    unsigned int last = argc > 2 ? (unsigned int)atoi(argv[2]) : 7200u;
    int route = -99;
    avsp_round1_init(&runtime);
    avsp_round1_tick_rule_init(&rule);
    puts("frame\troute\tphase\tticks\tff\tplayer_x\thp\tcam_x\talive\tcursor");
    for (frame = 0u; frame < last; ++frame)
    {
        unsigned short input = 0u;
        if (strcmp(mode, "source") == 0)
            input = avsp_round1_coffee_shop_source_input(
                (unsigned short)(frame + 2040u));
        else if (strcmp(mode, "bot") == 0)
            input = bot(frame);
        if (!runtime.entry.started &&
            frame == 32u &&
            !avsp_round1_begin_first_entry(&runtime))
        {
            puts("begin failed");
            return 2;
        }
        if (!avsp_round1_step_interactive_frame(&runtime, &rule, input, input))
        {
            printf("FAILED frame=%u route=%d code=%u failures=%u slot=%lx state=%u\n",
                   frame, runtime.route_state,
                   (unsigned int)runtime.scheduler_failure_code,
                   (unsigned int)runtime.failure_count,
                   (unsigned long)runtime.scheduler_failure_source_slot,
                   (unsigned int)runtime.scheduler_failure_state);
            return 3;
        }
        ++runtime.frame;
        if (frame % 120u == 0u || runtime.route_state != route)
        {
            printf("%u\t%d\t%u\t%u\t%u\t%d\t%d\t%d\t%u\t%u\n", frame,
                   runtime.route_state,
                   (unsigned int)runtime.entry.exit_route_phase,
                   (unsigned int)rule.last_frame_ticks,
                   (unsigned int)rule.fast_forward, runtime.player.x,
                   (int)runtime.player.health, runtime.camera_x_position,
                   alive(), (unsigned int)runtime.coffee_scene_record_cursor);
            route = runtime.route_state;
        }
    }
    printf("END ticks=%lu ff=%lu held=%lu exit_complete=%u\n", rule.total_ticks,
           rule.fast_forward_frames, rule.held_frames,
           (unsigned int)runtime.entry.exit_complete);
    return 0;
}
