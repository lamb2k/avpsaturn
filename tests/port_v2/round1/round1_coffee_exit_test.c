#include "round1.h"

#include <stdio.h>

static AvspRound1Runtime runtime;

static int player_anchor(unsigned int frame, unsigned long x_fp,
                         unsigned long y_fp, short z,
                         unsigned long animation_record,
                         unsigned short animation_timer,
                         unsigned char step, unsigned char mode,
                         unsigned char subhandler)
{
    if ((unsigned long)runtime.player.source_x_fp != x_fp ||
        (unsigned long)runtime.player.source_y_fp != y_fp ||
        runtime.player.z != z ||
        runtime.player.animation_record != animation_record ||
        runtime.player.animation_timer != animation_timer ||
        runtime.entry.exit_script_step != step ||
        runtime.entry.exit_script_mode != mode ||
        runtime.entry.exit_script_subhandler != subhandler)
    {
        fprintf(stderr,
                "exit anchor %u x=%08lx y=%08lx z=%d anim=%08lx/%u step=%u mode=%u sub=%u\n",
                frame, (unsigned long)runtime.player.source_x_fp,
                (unsigned long)runtime.player.source_y_fp, runtime.player.z,
                runtime.player.animation_record, runtime.player.animation_timer,
                runtime.entry.exit_script_step,
                runtime.entry.exit_script_mode,
                runtime.entry.exit_script_subhandler);
        return 0;
    }
    return 1;
}

static int validate_player_frame(unsigned int frame)
{
    if (frame == 5453u)
        return player_anchor(frame, 0x05509000UL, 0x013fa800UL, 319,
                             0x0015f1f4UL, 4095u, 1u, 2u, 0u);
    if (frame == 5454u)
        return player_anchor(frame, 0x05509000UL, 0x013fa800UL, 319,
                             0x0015f208UL, 4u, 1u, 4u, 0u);
    if (frame == 5475u)
        return player_anchor(frame, 0x04ecfe00UL, 0x0119c800UL, 281,
                             0x0015f1f4UL, 4095u, 2u, 0u, 0u);
    if (frame == 5476u)
        return player_anchor(frame, 0x04ecfe00UL, 0x0119c800UL, 281,
                             0x0015f1f4UL, 4095u, 4u, 2u, 0u) &&
            runtime.entry.exit_script_ticks == 90u;
    if (frame == 5505u)
        return player_anchor(frame, 0x04ecfe00UL, 0x0119c800UL, 281,
                             0x0015f2ccUL, 1u, 5u, 6u, 0u);
    if (frame == 5506u)
        return player_anchor(frame, 0x04f1fe00UL, 0x0121c800UL, 281,
                             0x0015f3b8UL, 1u, 5u, 6u, 2u);
    if (frame == 5519u)
        return player_anchor(frame, 0x058dde00UL, 0x01190800UL, 281,
                             0x0015f2ccUL, 1u, 5u, 6u, 4u);
    if (frame == 5520u)
        return player_anchor(frame, 0x05901e00UL, 0x01190800UL, 281,
                             0x0015f208UL, 3u, 6u, 4u, 0u);
    if (frame == 5522u)
        return player_anchor(frame, 0x059d9200UL, 0x0118d000UL, 280,
                             0x0015f1f4UL, 4095u, 7u, 0u, 0u);
    if (frame == 5523u)
        return runtime.route_state == 0 && runtime.entry.gate8236 == 0u &&
            runtime.entry.exit_script_step == 9u;
    return 1;
}

int main(void)
{
    unsigned int frame;
    avsp_round1_init(&runtime);
    runtime.entry.started = 1u;
    runtime.entry.dependencies_seeded = 1u;
    runtime.entry.exit_started = 1u;
    runtime.entry.exit_script_cursor = 0x00129b64UL;
    runtime.entry.gate8236 = 1u;
    runtime.entry.gate81af = 1u;
    runtime.route_state = 6;
    runtime.entry_controller.active = 1u;
    runtime.player.state = 0x0800u;
    runtime.player.substate = 0u;
    runtime.player.source_x_fp = 0x05509000L;
    runtime.player.source_y_fp = 0x013fa800L;
    runtime.player.x = 1360;
    runtime.player.y = 319;
    runtime.player.z = 319;
    runtime.player.facing = 1u;
    runtime.player.animation_record = 0x0015f218UL;
    runtime.player.animation_timer = 1u;

    for (frame = 5453u; frame <= 5523u; ++frame)
    {
        if (!avsp_round1_step_first_entry(&runtime) ||
            !validate_player_frame(frame) ||
            !avsp_round1_step_coffee_exit_display(&runtime))
            return (int)(frame - 5400u);
    }
    for (frame = 5524u; frame <= 5566u; ++frame)
    {
        if (!avsp_round1_step_coffee_exit_display(&runtime))
            return (int)(frame - 5400u);
        if (frame == 5550u &&
            (runtime.entry.exit_pool_teardowns != 1u ||
             runtime.entry.exit_route_substate != 2u))
            return 151;
        if (frame == 5560u && runtime.entry.exit_route_substate != 4u)
            return 152;
        if (frame == 5561u &&
            (runtime.route_state != 2 ||
             runtime.entry.exit_route_substate != 0u))
            return 153;
        if (frame == 5563u && runtime.entry.exit_route_substate != 2u)
            return 154;
        if (frame == 5565u && runtime.entry.exit_load_events != 1u)
            return 155;
        if (frame == 5566u &&
            (runtime.entry.exit_load_events != 2u ||
             !runtime.entry.exit_complete))
            return 156;
    }
    if (runtime.failure_count != 0u || runtime.fallback_count != 0u ||
        runtime.entry.exit_pool_teardowns != 1u ||
        runtime.entry.exit_load_events != 2u)
        return 157;
    return 0;
}
