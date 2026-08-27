#include "round1.h"

#include <stdio.h>

static int initialize_jump(AvspRound1Runtime *runtime,
                           unsigned short direction_mask)
{
    unsigned short mask = (unsigned short)(
        AVSP_ROUND1_INPUT_BUTTON3 | direction_mask);
    return avsp_round1_step_player(runtime, mask, 0) &&
        avsp_round1_step_player(runtime, mask, 0);
}

int main(void)
{
    AvspRound1Runtime runtime;
    unsigned int calls = 0u;
    unsigned short selector;
    const AvspRound1ActorCore *first;
    const AvspRound1ActorCore *last;
    avsp_round1_init(&runtime);
    if (!avsp_round1_entry_valid(&runtime))
    {
        return 1;
    }
    if (!avsp_round1_begin_first_entry(&runtime) ||
        runtime.player.state != AVSP_ROUND1_PLAYER_ENTRY_STATE ||
        runtime.entry.script_cursor != 0x00128FAAUL ||
        runtime.entry.gate8236 != 1u || runtime.entry.gate81af != 1u)
        return 2;
    while (!runtime.entry.control_enabled && calls < 1000u)
    {
        if (!avsp_round1_step_first_entry(&runtime))
        {
            fprintf(stderr,
                    "entry step failed calls=%u route=%u terminal=%u action=%u player_action=%u cleanup=%u player=%d/%d controller=%d/%d health=%d/%d nav=%u/%d/%d failures=%lu\n",
                    calls, runtime.route_state, runtime.entry.terminal_seen,
                    runtime.player_locomotion_action,
                    runtime.player.source_action,
                    runtime.player_cleanup_pending,
                    runtime.player.x, runtime.player.z,
                    runtime.player_action.x, runtime.player_action.lane,
                    runtime.player.health, runtime.player_action.health,
                    runtime.navigation_bounds_active,
                    runtime.navigation_bound_x, runtime.navigation_bound_z,
                    runtime.failure_count);
            return 3;
        }
        if (runtime.entry.spawned && !avsp_round1_step_scheduler(&runtime))
            return 3;
        ++calls;
        if (runtime.route_state == 4 && !runtime.entry.terminal_seen)
            return 4;
    }
    if (calls != 171u || runtime.route_state != 4 ||
        runtime.player.state != AVSP_ROUND1_PLAYER_CONTROL_STATE ||
        runtime.entry.spawn_count != AVSP_ROUND1_FIRST_SPAWN_COUNT ||
        runtime.entry.timer_decrements != 164u ||
        runtime.entry.step_index != AVSP_ROUND1_ENTRY_STEP_COUNT ||
        runtime.entry.gate8236 != 0u || runtime.entry.gate81af != 1u ||
        runtime.entry.source_global_8209 != 2u ||
        runtime.entry.script_cursor != 0x00128FC4UL ||
        runtime.navigation_bounds_active != 1u ||
        runtime.navigation_bound_x != 640 || runtime.navigation_bound_z != 256 ||
        runtime.camera_x_position != 640 ||
        runtime.camera_x_target != 640 ||
        runtime.camera_x_lower != 640 || runtime.camera_x_upper != 832 ||
        runtime.camera_z_position != 256 ||
        runtime.camera_z_lower != 256 || runtime.camera_z_upper != 256 ||
        runtime.camera_scroll2_x != 576 ||
        runtime.camera_guard_countdown != 1200u ||
        runtime.pools[0].free_count != 10u ||
        runtime.pools[2].free_count != 13u ||
        runtime.pools[3].free_count != 2u ||
        runtime.scheduler_frames != 171u ||
        runtime.scheduler_dispatches != 2394u ||
        runtime.class1f_initializations != 10u ||
        runtime.class1f_initial_rng_calls != 10u ||
        runtime.class09_initializations != 2u ||
        runtime.class09_rng_calls != 42u ||
        runtime.rng_seed != 0x111cu ||
        !avsp_round1_entry_valid(&runtime))
        return 5;
    if (runtime.pools[0].records[10].coordinate_mode != 1u ||
        runtime.pools[0].records[10].palette != 16u ||
        runtime.pools[0].records[10].object_or != 0x8000u ||
        runtime.pools[0].records[11].coordinate_mode != 1u ||
        runtime.pools[0].records[11].palette != 17u ||
        runtime.pools[0].records[11].object_or != 0x8000u ||
        runtime.pools[0].records[12].coordinate_mode != 1u ||
        runtime.pools[0].records[12].palette != 17u ||
        runtime.pools[0].records[12].object_or != 0x8000u ||
        runtime.pools[0].records[13].coordinate_mode != 1u ||
        runtime.pools[0].records[13].palette != 18u ||
        runtime.pools[0].records[13].object_or != 0x8000u ||
        runtime.pools[0].records[14].coordinate_mode != 1u ||
        runtime.pools[0].records[14].palette != 17u ||
        runtime.pools[0].records[14].object_or != 0x8000u ||
        runtime.pools[0].records[15].coordinate_mode != 1u ||
        runtime.pools[0].records[15].palette != 16u ||
        runtime.pools[0].records[15].object_or != 0x8000u ||
        runtime.pools[0].records[16].coordinate_mode != 1u ||
        runtime.pools[0].records[16].palette != 18u ||
        runtime.pools[0].records[16].object_or != 0x8000u ||
        runtime.pools[0].records[17].coordinate_mode != 1u ||
        runtime.pools[0].records[17].palette != 17u ||
        runtime.pools[0].records[17].object_or != 0x8000u ||
        runtime.pools[0].records[18].coordinate_mode != 1u ||
        runtime.pools[0].records[18].palette != 19u ||
        runtime.pools[0].records[18].object_or != 0x8000u ||
        runtime.pools[0].records[19].coordinate_mode != 1u ||
        runtime.pools[0].records[19].palette != 19u ||
        runtime.pools[0].records[19].object_or != 0x8000u)
        return 54;
    if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        !avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        !avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x <= 944 || runtime.player.z != 320 ||
        runtime.player.facing != 1u || runtime.player_controller_updates != 5u ||
        runtime.player.substate != 512u ||
        !avsp_round1_entry_valid(&runtime))
        return 6;
    if (!avsp_round1_step_scheduler(&runtime) ||
        runtime.scheduler_trace_count != 14u ||
        runtime.scheduler_frames != 172u ||
        runtime.scheduler_dispatches != 2408u ||
        runtime.actor_handler_dispatches != 1720u ||
        runtime.presentation_bindings != 1720u ||
        runtime.state_context_bindings != 1720u ||
        runtime.pools[0].records[10].assembly != 0x0012FA0CUL ||
        runtime.pools[0].records[10].hurt_selector != 2u ||
        runtime.pools[0].records[10].attack_selector != 0u ||
        runtime.pools[0].records[16].assembly != 0x0012F9BCUL ||
        runtime.pools[0].records[16].hurt_selector != 1u ||
        runtime.pools[0].records[10].dispatch_entry != 0x00060532UL)
        return 7;
    for (calls = 0u; calls < 10u; ++calls)
    {
        if (runtime.scheduler_trace[calls].record_type != 12u ||
            runtime.scheduler_trace[calls].actor_class != 0x1f ||
            runtime.scheduler_trace[calls].pool_slot != calls + 10u ||
            runtime.scheduler_trace[calls].source_slot !=
                0x00ff9d00UL + calls * 192u)
            return 8;
    }
    runtime.pools[1].records[0].active = 1u;
    runtime.pools[1].records[0].actor_class = 0x06;
    runtime.pools[1].records[0].type = 16u;
    runtime.pools[1].records[0].source_slot = 0x00ffa480UL;
    runtime.pools[1].free_count = 19u;
    runtime.pools[2].records[0].active = 1u;
    runtime.pools[2].records[0].actor_class = 0x07;
    runtime.pools[2].records[0].type = 20u;
    runtime.pools[2].records[0].source_slot = 0x00ffae80UL;
    runtime.pools[2].free_count = 12u;
    runtime.pools[3].records[0].active = 1u;
    runtime.pools[3].records[0].actor_class = 0x10;
    runtime.pools[3].records[0].type = 24u;
    runtime.pools[3].records[0].variant = 1u;
    runtime.pools[3].records[0].source_facing_selector = 1u;
    runtime.pools[3].records[0].source_slot = 0x00ffb680UL;
    runtime.pools[3].free_count = 2u;
    if (!avsp_round1_step_scheduler(&runtime) ||
        runtime.scheduler_trace_count != 17u ||
        runtime.scheduler_frames != 173u ||
        runtime.scheduler_dispatches != 2425u ||
        runtime.actor_handler_dispatches != 1730u ||
        runtime.presentation_bindings != 1730u ||
        runtime.state_context_bindings != 1730u ||
        runtime.scheduler_trace[10].record_type != 16u ||
        runtime.scheduler_trace[11].record_type != 20u ||
        runtime.scheduler_trace[12].record_type != 20u ||
        runtime.scheduler_trace[15].record_type != 24u ||
        runtime.scheduler_trace[16].actor_class != 0x44 ||
        runtime.pools[0].records[10].scheduler_updates != 173u ||
        runtime.pools[0].records[10].handler_updates != 173u ||
        runtime.pools[0].records[10].state_handler_updates != 173u)
        return 9;
    first = &runtime.pools[0].records[19];
    last = &runtime.pools[0].records[10];
    if (first->source_slot != 0x00FFA3C0UL || first->x != 713 ||
        first->z != 312 || first->variant != 8u ||
        first->source_action != 16u || first->state != 0x0200u ||
        first->substate != 0x1404u || first->health != 87 ||
        last->source_slot != 0x00FF9D00UL || last->x != 632 ||
        last->z != 296 || last->variant != 6u ||
        last->substate != 4096u || last->transition_timer != 44u)
        return 10;
    runtime.player_action.x = 2000;
    runtime.player_action.lane = 1000;
    if (!avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x != 1028 || runtime.player.z != 327)
    {
        fprintf(stderr,
                "high clamp x=%d z=%d action_x=%d lane=%d applications=%lu clamps=%lu\n",
                runtime.player.x, runtime.player.z,
                runtime.player_action.x, runtime.player_action.lane,
                runtime.navigation_applications, runtime.navigation_clamps);
        return 11;
    }
    runtime.player_action.x = -1000;
    runtime.player_action.lane = -1000;
    if (!avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x != 719 || runtime.player.z != 272 ||
        runtime.navigation_applications != 7u ||
        runtime.navigation_clamps != 4u)
    {
        fprintf(stderr,
                "low clamp x=%d z=%d action_x=%d lane=%d applications=%lu clamps=%lu\n",
                runtime.player.x, runtime.player.z,
                runtime.player_action.x, runtime.player_action.lane,
                runtime.navigation_applications, runtime.navigation_clamps);
        return 12;
    }
    for (calls = 0u; calls < 9u; ++calls)
        if (!avsp_round1_step_player(&runtime, 0u, 0))
            return 13;
    if (runtime.player_stop_ticks != 0u ||
        runtime.player.source_action != 512u ||
        runtime.player_cleanup_pending != 1u ||
        runtime.player_stop_entries != 1u ||
        runtime.player_stop_completions != 1u)
        return 14;
    if (!avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.source_action != 514u ||
        runtime.player_cleanup_pending != 0u ||
        runtime.player.facing != 1u ||
        runtime.navigation_applications != 17u ||
        runtime.navigation_clamps != 4u ||
        runtime.player_stop_motion_suppressions != 0u)
    {
        fprintf(stderr, "neutral action=%u cleanup=%u facing=%u apps=%lu clamps=%lu suppress=%lu failure=%lu\n",
                runtime.player.source_action, runtime.player_cleanup_pending,
                runtime.player.facing, runtime.navigation_applications,
                runtime.navigation_clamps,
                runtime.player_stop_motion_suppressions,
                runtime.failure_count);
        return 15;
    }
    {
        AvspRound1Runtime navigation_runtime = runtime;
        navigation_runtime.navigation_bound_x = 832;
        navigation_runtime.navigation_bound_z = 256;
        navigation_runtime.camera_x_position = 832;
        navigation_runtime.camera_x_target = 832;
        navigation_runtime.camera_x_lower = 832;
        navigation_runtime.camera_x_upper = 1008;
        navigation_runtime.camera_z_position = 256;
        navigation_runtime.camera_z_target = 256;
        navigation_runtime.camera_z_lower = 256;
        navigation_runtime.camera_z_upper = 256;
        navigation_runtime.camera_scroll2_x = 768;
        navigation_runtime.camera_coffee_phase = 4u;
        navigation_runtime.player_action.x = 1092;
        navigation_runtime.player_action.lane = 323;
        navigation_runtime.player_action.x_numerator = 0;
        navigation_runtime.player_action.lane_numerator = 0;
        navigation_runtime.player_action.direction_history[0] = 0u;
        navigation_runtime.player_action.direction_history[1] = 0u;
        if (!avsp_round1_step_player(&navigation_runtime, 0u, 0) ||
            navigation_runtime.player.x != 1091 ||
            navigation_runtime.player.z != 323 ||
            navigation_runtime.navigation_obstacle_responses !=
                runtime.navigation_obstacle_responses + 1u)
            return 76;
        navigation_runtime = runtime;
        navigation_runtime.navigation_bound_x = 832;
        navigation_runtime.navigation_bound_z = 256;
        navigation_runtime.camera_x_position = 832;
        navigation_runtime.camera_x_target = 832;
        navigation_runtime.camera_x_lower = 832;
        navigation_runtime.camera_x_upper = 1008;
        navigation_runtime.camera_z_position = 256;
        navigation_runtime.camera_z_target = 256;
        navigation_runtime.camera_z_lower = 256;
        navigation_runtime.camera_z_upper = 256;
        navigation_runtime.camera_scroll2_x = 768;
        navigation_runtime.camera_coffee_phase = 4u;
        navigation_runtime.player_action.x = 1093;
        navigation_runtime.player_action.lane = 319;
        navigation_runtime.player_action.x_numerator = 0;
        navigation_runtime.player_action.lane_numerator = 0;
        navigation_runtime.player_action.direction_history[0] = 0u;
        navigation_runtime.player_action.direction_history[1] = 0u;
        if (!avsp_round1_step_player(&navigation_runtime, 0u, 0) ||
            navigation_runtime.player.x != 1091 ||
            navigation_runtime.player.z != 319)
            return 77;
        navigation_runtime = runtime;
        navigation_runtime.navigation_bound_x = 832;
        navigation_runtime.navigation_bound_z = 256;
        navigation_runtime.camera_x_position = 832;
        navigation_runtime.camera_x_target = 832;
        navigation_runtime.camera_x_lower = 832;
        navigation_runtime.camera_x_upper = 1008;
        navigation_runtime.camera_z_position = 256;
        navigation_runtime.camera_z_target = 256;
        navigation_runtime.camera_z_lower = 256;
        navigation_runtime.camera_z_upper = 256;
        navigation_runtime.camera_scroll2_x = 768;
        navigation_runtime.camera_coffee_phase = 4u;
        navigation_runtime.player_action.x = 1028;
        navigation_runtime.player_action.lane = 400;
        navigation_runtime.player_action.x_numerator = 0;
        navigation_runtime.player_action.lane_numerator = 0;
        navigation_runtime.player_action.direction_history[0] = 0u;
        navigation_runtime.player_action.direction_history[1] = 0u;
        if (!avsp_round1_step_player(&navigation_runtime, 0u, 0) ||
            navigation_runtime.player.x != 1028 ||
            navigation_runtime.player.z != 327 ||
            navigation_runtime.navigation_terrain_retries ==
                runtime.navigation_terrain_retries)
            return 78;
    }
    {
        AvspRound1Runtime camera_runtime = runtime;
        unsigned int camera_steps = 0u;
        unsigned int locked_steps = 0u;
        camera_runtime.player_action.x = 944;
        camera_runtime.player_action.lane = 320;
        camera_runtime.player_action.x_numerator = 0;
        camera_runtime.player_action.lane_numerator = 0;
        camera_runtime.player_action.direction_history[0] = 0u;
        camera_runtime.player_action.direction_history[1] = 0u;
        camera_runtime.camera_x_previous = 640;
        camera_runtime.camera_x_position = 640;
        camera_runtime.camera_x_target = 640;
        camera_runtime.camera_x_target_previous = 640;
        camera_runtime.camera_x_lower = 640;
        camera_runtime.camera_x_upper = 832;
        camera_runtime.camera_z_position = 256;
        camera_runtime.camera_z_target = 256;
        camera_runtime.camera_z_lower = 256;
        camera_runtime.camera_z_upper = 256;
        camera_runtime.camera_scroll2_x = 576;
        camera_runtime.camera_coffee_phase = 0u;
        camera_runtime.camera_guard_counter = 0u;
        camera_runtime.camera_guard_snapshot = 0u;
        camera_runtime.camera_guard_countdown = 1200u;
        camera_runtime.navigation_bound_x = 640;
        camera_runtime.navigation_bound_z = 256;
        if (!avsp_round1_step_player(&camera_runtime, 0u, 0) ||
            camera_runtime.camera_x_position != 648 ||
            camera_runtime.camera_scroll2_x != 584)
            return 79;
        while (camera_runtime.camera_coffee_phase == 0u &&
               camera_steps < 500u)
        {
            if (!avsp_round1_step_player(&camera_runtime,
                    AVSP_PW_INPUT_RIGHT, 0))
                return 79;
            ++camera_steps;
        }
        if (camera_runtime.camera_coffee_phase != 2u ||
            camera_runtime.camera_x_position != 832 ||
            camera_runtime.camera_x_lower != 832 ||
            camera_runtime.camera_x_upper != 832 ||
            camera_runtime.camera_guard_countdown != 1200u ||
            camera_runtime.camera_locks != runtime.camera_locks + 1u)
        {
            fprintf(stderr, "camera lock phase=%u x=%d player=%d low=%d high=%d countdown=%u locks=%lu base=%lu steps=%u\n",
                    camera_runtime.camera_coffee_phase,
                    camera_runtime.camera_x_position,
                    camera_runtime.player_action.x,
                    camera_runtime.camera_x_lower,
                    camera_runtime.camera_x_upper,
                    camera_runtime.camera_guard_countdown,
                    camera_runtime.camera_locks, runtime.camera_locks,
                    camera_steps);
            return 80;
        }
        while (camera_runtime.camera_coffee_phase == 2u &&
               locked_steps < 1300u)
        {
            if (!avsp_round1_step_player(&camera_runtime, 0u, 0))
                return 80;
            ++locked_steps;
        }
        if (locked_steps != 1200u ||
            camera_runtime.camera_coffee_phase != 4u ||
            camera_runtime.camera_x_upper != 1008 ||
            camera_runtime.camera_unlocks != runtime.camera_unlocks + 1u)
            return 81;
    }
    {
        static const unsigned short masks[10] = {
            0u, AVSP_PW_INPUT_UP, AVSP_PW_INPUT_LEFT,
            AVSP_PW_INPUT_LEFT, AVSP_PW_INPUT_RIGHT,
            AVSP_PW_INPUT_RIGHT,
            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_LEFT,
            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_LEFT,
            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_RIGHT,
            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_RIGHT };
        static const unsigned char facings[10] =
            {0u, 0u, 0u, 1u, 0u, 1u, 0u, 1u, 0u, 1u};
        static const long x_velocity[10] = {
            0L, 0L, -0x000f0000L, -0x00090000L, 0x00090000L,
            0x000f0000L, -0x00090000L, -0x00088000L,
            0x00088000L, 0x00090000L };
        static const long x_acceleration[10] = {
            0L, 0L, 0x00006800L, 0x00002000L, -0x00002000L,
            -0x00006800L, 0x00002400L, 0x00002400L,
            -0x00002400L, -0x00002400L };
        static const long y_velocity[10] = {
            0x00088000L, 0x000c0000L, 0x00040000L, 0x00040000L,
            0x00040000L, 0x00040000L, 0x000c0000L, 0x000c0000L,
            0x000c0000L, 0x000c0000L };
        static const long y_acceleration[10] = {
            -0x00008000L, -0x00008000L, -0x00003800L, -0x00008000L,
            -0x00008000L, -0x00003800L, -0x00008800L, -0x00008800L,
            -0x00008800L, -0x00008800L };
        static const unsigned char selectors[10] =
            {4u, 4u, 5u, 15u, 15u, 6u, 5u, 6u, 6u, 6u};
        static const unsigned char collisions[10] =
            {3u, 3u, 2u, 8u, 8u, 2u, 1u, 4u, 4u, 1u};
        static const unsigned long records[10] = {
            0x0015f2f0UL, 0x0015f2f0UL, 0x0015f344UL,
            0x0015f43cUL, 0x0015f43cUL, 0x0015f3b8UL,
            0x0015f344UL, 0x0015f3b8UL, 0x0015f3b8UL,
            0x0015f3b8UL };
        unsigned int jump_index;
        for (jump_index = 0u; jump_index < 10u; ++jump_index)
        {
            AvspRound1Runtime jump_runtime = runtime;
            jump_runtime.player.x = 850;
            jump_runtime.player_action.x = 850;
            jump_runtime.player.facing = facings[jump_index];
            jump_runtime.player_action.facing = facings[jump_index];
            if (!initialize_jump(&jump_runtime, masks[jump_index]) ||
                jump_runtime.player_jump_phase != 0x0402u ||
                jump_runtime.player.source_action != 0x0402u ||
                jump_runtime.player_jump_x_velocity != x_velocity[jump_index] ||
                jump_runtime.player_jump_x_acceleration !=
                    x_acceleration[jump_index] ||
                jump_runtime.player_jump_y_velocity != y_velocity[jump_index] ||
                jump_runtime.player_jump_y_acceleration !=
                    y_acceleration[jump_index] ||
                jump_runtime.player_jump_presentation_selector !=
                    selectors[jump_index] ||
                jump_runtime.player_jump_collision_selector !=
                    collisions[jump_index] ||
                jump_runtime.player.animation_record != records[jump_index] ||
                jump_runtime.player_jump_airborne_latch != 1u ||
                jump_runtime.player_jump_entries != 1u ||
                jump_runtime.rng_seed != runtime.rng_seed ||
                !avsp_round1_entry_valid(&jump_runtime))
                return 82;
        }
    }
    {
        AvspRound1Runtime jump_runtime = runtime;
        unsigned int jump_calls = 2u;
        short maximum_height = 0;
        if (!initialize_jump(&jump_runtime, 0u) ||
            jump_runtime.player.animation_record != 0x0015f2f0UL ||
            jump_runtime.player_jump_animation_timer != 8u)
            return 83;
        while (jump_runtime.player_jump_active && jump_calls < 80u)
        {
            if (!avsp_round1_step_player(&jump_runtime, 0u, 0))
                return 83;
            if (jump_runtime.player_action.height > maximum_height)
                maximum_height = jump_runtime.player_action.height;
            ++jump_calls;
        }
        if (jump_calls != 39u || maximum_height != 76 ||
            jump_runtime.player_jump_completions != 1u ||
            jump_runtime.player_jump_landings != 1u ||
            jump_runtime.player_jump_motion_updates != 35u ||
            jump_runtime.rng_seed != runtime.rng_seed ||
            jump_runtime.player_jump_cleanup_pending != 1u ||
            jump_runtime.player.source_action != 0u ||
            jump_runtime.player.animation_record != 0x0015f1f4UL ||
            jump_runtime.player_action.height != 0 ||
            !avsp_round1_entry_valid(&jump_runtime) ||
            !avsp_round1_step_player(&jump_runtime, 0u, 0) ||
            jump_runtime.player_jump_cleanup_pending != 0u)
            return 84;
    }
    {
        AvspRound1Runtime jump_runtime = runtime;
        unsigned int down_calls = 2u;
        if (!initialize_jump(&jump_runtime, AVSP_PW_INPUT_DOWN) ||
            jump_runtime.player_jump_phase != 0x040au ||
            jump_runtime.player_jump_presentation_selector != 60u ||
            jump_runtime.player.attack_selector != 35u ||
            jump_runtime.player_jump_x_velocity != 0x00060000L ||
            jump_runtime.player_jump_x_acceleration != -0x00008000L)
            return 85;
        while (jump_runtime.player_jump_active)
        {
            if (!avsp_round1_step_player(&jump_runtime, 0u, 0))
                return 85;
            ++down_calls;
        }
        if (down_calls != 25u ||
            jump_runtime.player_jump_completions != 1u ||
            jump_runtime.player_jump_landings != 0u ||
            jump_runtime.player_jump_motion_updates != 13u)
            return 85;
    }
    {
        AvspRound1Runtime jump_runtime = runtime;
        if (!initialize_jump(&jump_runtime,
                             AVSP_PW_INPUT_DOWN | AVSP_PW_INPUT_RIGHT) ||
            jump_runtime.player.facing != 1u ||
            jump_runtime.player_jump_presentation_selector != 41u ||
            jump_runtime.player.attack_selector != 22u ||
            jump_runtime.player_jump_x_velocity != 0x000c0000L ||
            jump_runtime.player_jump_x_acceleration != -0x0000a000L)
            return 86;
    }
    {
        AvspRound1Runtime jump_runtime = runtime;
        if (!initialize_jump(&jump_runtime, AVSP_PW_INPUT_UP) ||
            !avsp_round1_step_player(&jump_runtime, 0u, 8) ||
            jump_runtime.player_jump_active != 0u ||
            jump_runtime.player_jump_interruptions != 1u ||
            jump_runtime.player_action.state != AVSP_PW_STATE_HIT ||
            jump_runtime.player_action.height != 0)
            return 87;
    }
    for (selector = 1u; selector <= AVSP_ROUND1_PLAYER_MELEE_COUNT;
         ++selector)
    {
        unsigned long entries = runtime.player_melee_entries;
        if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_ATTACK, 0) ||
            runtime.player_action.state != AVSP_PW_STATE_ATTACK ||
            runtime.player_action.selector != selector ||
            runtime.player_melee_entries != entries + 1u ||
            runtime.player_melee_selector_mask !=
                ((1UL << selector) - 1UL))
            return 16;
        if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_ATTACK, 0) ||
            runtime.player_melee_entries != entries + 1u ||
            runtime.player_action.action_elapsed != 1u)
            return 17;
        if (!avsp_round1_step_player(&runtime, 0u, 0) ||
            runtime.player.source_action != 1536u)
            return 18;
        while (!avsp_pw_can_control(&runtime.player_action))
            if (!avsp_round1_step_player(&runtime, 0u, 0))
                return 19;
        if (runtime.player_melee_completions != selector)
            return 20;
        while (runtime.player_action.combo_idle_frames < 20u)
            if (!avsp_round1_step_player(&runtime, 0u, 0))
                return 21;
    }
    if (runtime.player_melee_entries != 4u ||
        runtime.player_melee_completions != 4u ||
        runtime.player_melee_selector_mask != 0x0fUL ||
        runtime.player_melee_presentation_mask != 0x0fUL ||
        runtime.player_melee_interruptions != 0u)
        return 22;
    if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_ATTACK, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 8) ||
        runtime.player_action.state != AVSP_PW_STATE_HIT ||
        runtime.player_melee_entries != 5u ||
        runtime.player_melee_completions != 4u ||
        runtime.player_melee_interruptions != 1u)
        return 23;
    for (calls = 0u; calls < 16u; ++calls)
        if (!avsp_round1_step_player(&runtime, 0u, 0))
            return 24;
    if (!avsp_pw_can_control(&runtime.player_action) ||
        !avsp_round1_entry_valid(&runtime))
        return 25;
    {
        AvspRound1Runtime weapon_runtime = runtime;
        short weapon_x;
        short weapon_z;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player.x == runtime.player.x)
            return 26;
        weapon_x = weapon_runtime.player.x;
        weapon_z = weapon_runtime.player.z;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 1u ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player.substate != 0u ||
            weapon_runtime.player.animation_record != 0x0015f1f4UL ||
            weapon_runtime.player.assembly != 0x001626a4UL ||
            weapon_runtime.player_weapon_entries != 1u ||
            weapon_runtime.player_weapon_attempts_total != 1u ||
            weapon_runtime.player_weapon_allocations != 1u ||
            weapon_runtime.player_weapon_resource_debits != 1u ||
            weapon_runtime.player_resource != 24u ||
            weapon_runtime.player_resource_recharge != 11u ||
            weapon_runtime.player_action.state != AVSP_PW_STATE_CONTROL ||
            weapon_runtime.player_weapon_interruptions != 0u ||
            weapon_runtime.player.x != weapon_x ||
            weapon_runtime.player.z != weapon_z)
            return 26;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x0c02u ||
            weapon_runtime.player.animation_record != 0x0015e540UL ||
            weapon_runtime.player.assembly != 0x00161772UL)
            return 27;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 28;
        if (weapon_runtime.player_weapon_tick != 20u ||
            weapon_runtime.player_weapon_cleanup_pending != 1u ||
            weapon_runtime.player.source_action != 0u ||
            weapon_runtime.player_weapon_completions != 1u ||
            weapon_runtime.player_weapon_allocations != 1u ||
            weapon_runtime.player_resource != 29u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 2u ||
            weapon_runtime.player.animation_record != 0x0015f1f4UL ||
            weapon_runtime.player.assembly != 0x001626a4UL)
            return 29;
        if (weapon_runtime.player_weapon_projectile_free_count != 23u ||
            weapon_runtime.player_weapon_projectiles[0].actor_class != 0 ||
            weapon_runtime.player_weapon_projectiles[0].source_slot !=
                0x8680u ||
            weapon_runtime.player_weapon_projectiles[0].owner != 0x8380u ||
            weapon_runtime.player_weapon_projectiles[0].attack_table !=
                0x0002fc3cUL ||
            weapon_runtime.player_weapon_projectiles[0].state != 0u ||
            weapon_runtime.player_weapon_projectiles[0].
                parent_presentation_selector != 0u ||
            weapon_runtime.player_weapon_projectiles[0].angle !=
                (weapon_runtime.player_weapon_projectiles[0].facing ?
                    17u : 47u) ||
            weapon_runtime.player_weapon_projectiles[0].x_fp !=
                (long)weapon_runtime.player_weapon_projectiles[0].x * 65536L)
            return 32;
        weapon_runtime.player_resource = 24u;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player.source_action != 0x1a00u ||
            weapon_runtime.player_weapon_empty != 1u ||
            weapon_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            weapon_runtime.player_weapon_allocations != 1u)
            return 33;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x1a02u ||
            weapon_runtime.player.animation_record != 0x0015fcfcUL ||
            weapon_runtime.player.assembly != 0x00161772UL)
            return 34;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 35;
        if (weapon_runtime.player_weapon_completions != 2u ||
            weapon_runtime.player.source_action != 0u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 2u)
            return 36;
        weapon_runtime.player_resource = 64u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 0u;
        weapon_runtime.player_weapon_projectile_free_count = 0u;
        weapon_runtime.player_weapon_allocations =
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player_weapon_empty != 0u ||
            weapon_runtime.player_weapon_allocation_failures != 1u ||
            weapon_runtime.player_weapon_allocations !=
                AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY ||
            weapon_runtime.player_weapon_resource_debits != 2u ||
            weapon_runtime.player_resource != 24u)
            return 38;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 8) ||
            weapon_runtime.player_weapon_active != 0u ||
            weapon_runtime.player_weapon_interruptions != 1u ||
            weapon_runtime.player_action.state != AVSP_PW_STATE_HIT ||
            weapon_runtime.player.source_action != 514u ||
            !avsp_round1_entry_valid(&weapon_runtime))
            return 39;
    }
    {
        AvspRound1Runtime effect_runtime;
        AvspRound1ActorCore *effect;
        int index;
        unsigned int effect_entry_calls = 0u;
        avsp_round1_init(&effect_runtime);
        if (!avsp_round1_begin_first_entry(&effect_runtime))
            return 43;
        while (!effect_runtime.entry.control_enabled &&
               effect_entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&effect_runtime))
                return 43;
            if (effect_runtime.entry.spawned &&
                !avsp_round1_step_scheduler(&effect_runtime))
                return 43;
            ++effect_entry_calls;
        }
        if (effect_runtime.route_state != 4)
            return 43;
        for (index = 17; index < 20; ++index)
        {
            effect_runtime.pools[0].records[index].state = 0u;
            effect_runtime.pools[0].records[index].substate = 0u;
        }
        effect_runtime.player_resource = 0u;
        effect_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&effect_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            effect_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            effect_runtime.player_weapon_empty_auxiliary_allocations != 1u ||
            effect_runtime.pools[3].free_count != 1u)
            return 43;
        effect = &effect_runtime.pools[3].records[29];
        if (!avsp_round1_step_scheduler(&effect_runtime) ||
            effect->state != 2u || effect->variant != 1u ||
            effect->x != effect_runtime.player.x ||
            effect->y != effect_runtime.player.y + 78 ||
            effect->animation_record != 0x0007a09cUL ||
            effect->animation_timer != 1u || effect->animation_branch != 0)
            return 44;
        for (index = 0; index < 8; ++index)
            if (!avsp_round1_step_scheduler(&effect_runtime))
                return 45;
        if (effect->y != effect_runtime.player.y + 110 ||
            effect->animation_index != 8u ||
            effect->animation_record != 0x0007a11cUL ||
            effect->animation_timer != 8u || effect->animation_branch != 1)
            return 46;
        for (index = 0; index < 8; ++index)
            if (!avsp_round1_step_scheduler(&effect_runtime))
                return 47;
        if (effect->animation_index != 9u ||
            effect->animation_record != 0x0007a12cUL ||
            effect->animation_branch != -32767 ||
            !avsp_round1_step_scheduler(&effect_runtime) ||
            effect->state != 4u ||
            !avsp_round1_step_scheduler(&effect_runtime) ||
            effect_runtime.pools[3].free_count != 2u ||
            effect_runtime.player_weapon_empty_auxiliary_releases != 1u)
            return 48;
    }
    {
        AvspRound1Runtime projectile_runtime;
        AvspRound1ActorCore *target;
        AvspRound1WeaponProjectileAllocation *projectile;
        AvspRound1WeaponProjectileAllocation *child;
        unsigned int entry_calls = 0u;
        short parent_spawn_x;
        short parent_spawn_y;
        avsp_round1_init(&projectile_runtime);
        if (!avsp_round1_begin_first_entry(&projectile_runtime))
            return 50;
        while (!projectile_runtime.entry.control_enabled && entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&projectile_runtime))
                return 50;
            if (projectile_runtime.entry.spawned &&
                !avsp_round1_step_scheduler(&projectile_runtime))
                return 50;
            ++entry_calls;
        }
        for (entry_calls = 17u; entry_calls < 20u; ++entry_calls)
        {
            projectile_runtime.pools[0].records[entry_calls].state = 0u;
            projectile_runtime.pools[0].records[entry_calls].substate = 0u;
        }
        for (entry_calls = 0u;
             entry_calls < projectile_runtime.pools[0].capacity; ++entry_calls)
        {
            projectile_runtime.pools[0].records[entry_calls].hurt_selector = 0u;
            projectile_runtime.pools[0].records[entry_calls].x = 2000;
            projectile_runtime.pools[0].records[entry_calls].health = -1;
        }
        target = &projectile_runtime.pools[0].records[12];
        target->health = -1;
        target->hurt_selector = 0u;
        target->facing = 0u;
        target->x = (short)(projectile_runtime.player.x +
            (projectile_runtime.player.facing ? 5 : -5));
        target->y = (short)(projectile_runtime.player.y + 78);
        target->z = (short)(projectile_runtime.player.z - 1);
        if (!avsp_round1_step_player(&projectile_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0))
            return 51;
        projectile = &projectile_runtime.player_weapon_projectiles[0];
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->state != 2u || projectile->collision_result != 0 ||
            projectile->actor_class != 0 ||
            projectile->attack_selector != 1u || target->health != -1 ||
            projectile->x != (short)(projectile_runtime.player.x +
                (projectile->facing ? 5 : -5)) ||
            projectile->y != (short)(projectile_runtime.player.y + 86) ||
            projectile->z != (short)(projectile_runtime.player.z - 1) ||
            projectile->coordinate_mode != 0u ||
            projectile->palette != 0u ||
            projectile->object_or != 0x8000u ||
            projectile->animation_record != 0x0002fb48UL ||
            projectile->assembly != 0x0002fbccUL ||
            projectile_runtime.player_weapon_projectile_initializations != 1u ||
            projectile_runtime.player_weapon_projectile_collision_writes != 0u ||
            projectile_runtime.player_weapon_projectile_damage_writes != 0u)
        {
            fprintf(stderr, "projectile collision state=%u result=%d selector=%u target=%d/%u counts=%lu/%lu failures=%lu p=%d/%d/%d t=%d/%d/%d facing=%u\n",
                projectile->state, projectile->collision_result,
                projectile->attack_selector, target->health, target->substate,
                projectile_runtime.player_weapon_projectile_collision_writes,
                projectile_runtime.player_weapon_projectile_damage_writes,
                projectile_runtime.failure_count, projectile->x, projectile->y,
                projectile->z, target->x, target->y, target->z,
                projectile->facing);
            return 52;
        }
        parent_spawn_x = projectile->x;
        parent_spawn_y = projectile->y;
        for (entry_calls = 0u; entry_calls < 4u; ++entry_calls)
            if (!avsp_round1_step_scheduler(&projectile_runtime))
                return 52;
        if (projectile->x == parent_spawn_x || projectile->y >= parent_spawn_y)
        {
            fprintf(stderr, "parent motion spawn=%d/%d now=%d/%d/%d progress=%u state=%u collision=%d bounds=%d/%d\n",
                parent_spawn_x, parent_spawn_y, projectile->x, projectile->y,
                projectile->z, projectile->progress, projectile->state,
                projectile->collision_result,
                projectile_runtime.navigation_bound_x,
                projectile_runtime.navigation_bound_z);
            return 52;
        }
        target->hurt_selector = 1u;
        target->health = 63;
        target->x = projectile->x;
        target->y = (short)(projectile->y - 8);
        target->z = projectile->z;
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->collision_result != -1 || target->health != -1 ||
            target->substate != 0x0200u ||
            projectile_runtime.player_weapon_projectile_collision_writes != 1u ||
            projectile_runtime.player_weapon_projectile_damage_writes != 1u)
        {
            fprintf(stderr, "parent delayed collision p=%d/%d/%d target=%d/%d/%d health=%d result=%d state=%u counts=%lu/%lu\n",
                projectile->x, projectile->y, projectile->z,
                target->x, target->y, target->z, target->health,
                projectile->collision_result, projectile->state,
                projectile_runtime.player_weapon_projectile_collision_writes,
                projectile_runtime.player_weapon_projectile_damage_writes);
            return 52;
        }
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->state != 4u ||
            !avsp_round1_step_scheduler(&projectile_runtime))
            return 53;
        child = &projectile_runtime.player_weapon_projectiles[1];
        if (!child->active || child->actor_class != 4 || child->variant != 1u ||
            child->attack_table != 0x00030cb6UL || child->state != 2u ||
            child->animation_record != 0x000308a0UL ||
            child->assembly != 0x00030b36UL)
            return 54;
        target->health = 63;
        target->substate = 0u;
        target->hurt_selector = 1u;
        target->x = child->x;
        target->y = (short)(child->y + 10);
        target->z = child->z;
        projectile->active_collision = 0u;
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            target->health != 32 || target->substate != 0x0200u ||
            child->collision_result != -1 ||
            projectile_runtime.player_weapon_projectile_damage_writes != 2u)
            return 55;
        target->hurt_selector = 0u;
        for (entry_calls = 0u; entry_calls < 4u; ++entry_calls)
            if (!avsp_round1_step_scheduler(&projectile_runtime))
                return 55;
        if (projectile_runtime.player_weapon_allocations != 2u ||
            !avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile_runtime.player_weapon_allocations != 3u)
            return 55;
        for (entry_calls = 0u; entry_calls < 100u; ++entry_calls)
            if (!avsp_round1_step_scheduler(&projectile_runtime))
                return 56;
        if (projectile_runtime.player_weapon_allocations != 6u ||
            projectile_runtime.player_weapon_projectile_releases != 6u ||
            projectile_runtime.player_weapon_projectile_free_count != 24u ||
            projectile_runtime.player_weapon_impact_requests != 0u ||
            projectile_runtime.player_weapon_impact_audio_events != 0u)
            return 57;
    }
    {
        AvspRound1Runtime transition_runtime;
        unsigned int entry_calls = 0u;
        unsigned int tick;
        AvspRound1ActorCore *effect_a;
        AvspRound1ActorCore *effect_b;
        AvspRound1ActorCore *guard;
        avsp_round1_init(&transition_runtime);
        if (!avsp_round1_begin_first_entry(&transition_runtime))
            return 61;
        while (!transition_runtime.entry.control_enabled && entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&transition_runtime) ||
                (transition_runtime.entry.spawned &&
                 !avsp_round1_step_scheduler(&transition_runtime)))
                return 61;
            ++entry_calls;
        }
        if (transition_runtime.class1f_initializations != 10u ||
            transition_runtime.class1f_initial_rng_calls != 10u ||
            transition_runtime.class09_rng_calls != 42u ||
            transition_runtime.rng_seed != 0x111cu)
            return 62;
        effect_a = &transition_runtime.pools[3].records[28];
        effect_b = &transition_runtime.pools[3].records[29];
        guard = &transition_runtime.pools[3].records[30];
        if (guard->coordinate_mode != 0u || guard->palette != 0u ||
            guard->facing != 0u || guard->object_or != 0x8000u)
            return 75;
        for (tick = 1u; tick <= 130u; ++tick)
        {
            if (!avsp_round1_step_scheduler(&transition_runtime))
                return 63;
            if (tick == 6u &&
                (transition_runtime.class09_rng_calls != 44u ||
                 transition_runtime.rng_seed != 0x99e8u))
                return 64;
            if (tick == 12u &&
                (transition_runtime.class1f_effect_requests != 2u ||
                 transition_runtime.class1f_effect_allocations != 2u ||
                 transition_runtime.class4e_initializations != 2u ||
                 transition_runtime.class4e_rng_calls != 2u ||
                 transition_runtime.class1f_audio_events != 1u ||
                 transition_runtime.class1f_audio_command != 0x0118u ||
                 transition_runtime.pools[3].free_count != 0u ||
                 effect_a->x != 840 || effect_a->y != 432 ||
                 effect_b->x != 812 || effect_b->y != 388 ||
                 guard->state != 0x0400u))
                return 65;
            if (tick == 13u &&
                (transition_runtime.class44_guard_clears != 1u ||
                 transition_runtime.class1f_effect_guard != 0u ||
                 guard->substate != 0x0402u || guard->effect_timer != 3u))
                return 66;
            if (tick == 18u &&
                (transition_runtime.class1f_audio_events != 2u ||
                 transition_runtime.class1f_audio_command != 0x004du ||
                 transition_runtime.class1f_effect_requests != 4u ||
                 transition_runtime.class1f_effect_allocations != 2u ||
                 transition_runtime.class1f_effect_allocation_failures != 2u ||
                 transition_runtime.class1f_effect_guard != 1u))
                return 67;
        }
        if (transition_runtime.class1f_transition_completions != 10u ||
            transition_runtime.class1f_audio_events != 2u ||
            transition_runtime.class4e_releases != 2u ||
            transition_runtime.pools[3].free_count != 2u ||
            transition_runtime.player_weapon_projectile_collision_writes != 0u ||
            transition_runtime.player_weapon_projectile_damage_writes != 0u ||
            transition_runtime.failure_count != 0u ||
            transition_runtime.fallback_count != 0u)
        {
            fprintf(stderr, "transition summary completions=%lu audio=%lu releases=%lu pool24=%u collisions=%lu damage=%lu failures=%lu fallback=%lu first=%u/%u/%lu\n",
                transition_runtime.class1f_transition_completions,
                transition_runtime.class1f_audio_events,
                transition_runtime.class4e_releases,
                transition_runtime.pools[3].free_count,
                transition_runtime.player_weapon_projectile_collision_writes,
                transition_runtime.player_weapon_projectile_damage_writes,
                transition_runtime.failure_count,
                transition_runtime.fallback_count,
                transition_runtime.first_encounter.initialized,
                transition_runtime.first_encounter.encounter_state,
                transition_runtime.first_encounter.scheduler_updates);
            return 68;
        }
        for (tick = 10u; tick < 20u; ++tick)
            if (transition_runtime.pools[0].records[tick].state != 0x0200u ||
                (tick == 14u ?
                    transition_runtime.pools[0].records[tick].substate !=
                        0x1600u :
                    transition_runtime.pools[0].records[tick].substate != 0u))
                return 69;
        for (tick = 131u; tick <= 467u; ++tick)
        {
            if (!avsp_round1_step_scheduler(&transition_runtime))
            {
                fprintf(stderr,
                    "transition tail failed tick=%u scheduler=%lu dispatch=%lu seed=%04x class09=%lu failures=%lu\n",
                    tick, transition_runtime.scheduler_frames,
                    transition_runtime.scheduler_dispatches,
                    transition_runtime.rng_seed,
                    transition_runtime.class09_rng_calls,
                    transition_runtime.failure_count);
                return 70;
            }
        }
        if (transition_runtime.class1f_transition_completions != 10u ||
            transition_runtime.class1f_audio_events != 2u ||
            transition_runtime.class4e_releases != 2u ||
            transition_runtime.class44_guard_clears != 1u ||
            transition_runtime.failure_count != 0u ||
            transition_runtime.fallback_count != 0u)
            return 71;
    }
    {
        AvspRound1Runtime integrated_runtime;
        unsigned int entry_calls = 0u;
        unsigned int tick;
        avsp_round1_init(&integrated_runtime);
        if (!avsp_round1_begin_first_entry(&integrated_runtime))
            return 72;
        while (!integrated_runtime.entry.control_enabled && entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&integrated_runtime) ||
                (integrated_runtime.entry.spawned &&
                 !avsp_round1_step_scheduler(&integrated_runtime)))
                return 72;
            ++entry_calls;
        }
        for (tick = 0u; tick < 467u; ++tick)
        {
            unsigned short mask = 0u;
            if (integrated_runtime.player_controller_updates < 15u)
                mask = integrated_runtime.player_controller_updates != 2u ?
                    AVSP_PW_INPUT_RIGHT : 0u;
            else if (integrated_runtime.player_controller_updates == 30u ||
                     integrated_runtime.player_controller_updates == 72u ||
                     integrated_runtime.player_controller_updates == 114u ||
                     integrated_runtime.player_controller_updates == 161u)
                mask = AVSP_PW_INPUT_ATTACK;
            if (integrated_runtime.player_controller_updates == 210u)
                mask = AVSP_ROUND1_INPUT_BUTTON1;
            if (integrated_runtime.player_controller_updates == 270u)
            {
                integrated_runtime.player_resource = 0u;
                integrated_runtime.player_resource_recharge = 12u;
                integrated_runtime.player_resource_depleted = 1u;
                mask = AVSP_ROUND1_INPUT_BUTTON1;
            }
            if (!avsp_round1_step_player(&integrated_runtime, mask, 0) ||
                !avsp_round1_step_scheduler(&integrated_runtime))
            {
                fprintf(stderr,
                    "integrated tail failed tick=%u player=%lu scheduler=%lu dispatch=%lu seed=%04x pool24=%u failures=%lu\n",
                    tick, integrated_runtime.player_controller_updates,
                    integrated_runtime.scheduler_frames,
                    integrated_runtime.scheduler_dispatches,
                    integrated_runtime.rng_seed,
                    integrated_runtime.pools[3].free_count,
                    integrated_runtime.failure_count);
                return 73;
            }
        }
        if (integrated_runtime.failure_count != 0u ||
            integrated_runtime.fallback_count != 0u)
            return 74;
    }
    {
        AvspRound1Runtime encounter_runtime;
        unsigned int entry_calls = 0u;
        unsigned int tick = 0u;
        unsigned int selector;
        avsp_round1_init(&encounter_runtime);
        if (!avsp_round1_begin_first_entry(&encounter_runtime))
            return 80;
        while (!encounter_runtime.entry.control_enabled && entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&encounter_runtime) ||
                (encounter_runtime.entry.spawned &&
                 !avsp_round1_step_scheduler(&encounter_runtime)))
                return 80;
            ++entry_calls;
        }
        encounter_runtime.player_action.x =
            AVSP_ROUND1_FIRST_ENCOUNTER_ENTRY_X;
        encounter_runtime.player_action.lane = 320;
        encounter_runtime.player.x = encounter_runtime.player_action.x;
        encounter_runtime.player.y = encounter_runtime.player_action.lane;
        encounter_runtime.player.z = encounter_runtime.player_action.lane;
        while (!encounter_runtime.first_encounter.initialized && tick < 300u)
        {
            if (!avsp_round1_step_scheduler(&encounter_runtime))
                return 81;
            ++tick;
        }
        if (!encounter_runtime.first_encounter.initialized ||
            encounter_runtime.first_encounter.encounter_state !=
                AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE ||
            encounter_runtime.first_encounter.alien.x != 962 ||
            encounter_runtime.first_encounter.alien.lane != 343)
            return 82;
        while (encounter_runtime.first_encounter.alien.state !=
                   AVSP_ALIEN_STATE_ATTACK && tick < 400u)
        {
            if (!avsp_round1_step_player(&encounter_runtime, 0u, 0) ||
                !avsp_round1_step_scheduler(&encounter_runtime))
                return 83;
            ++tick;
        }
        if (encounter_runtime.first_encounter.alien.x != 1071 ||
            encounter_runtime.first_encounter.alien.lane != 320 ||
            encounter_runtime.first_encounter.alien.rng_seed != 0x595au ||
            encounter_runtime.first_encounter.alien.attack_timer != 120u)
            return 84;
        while (encounter_runtime.first_encounter.alien_contacts < 2u &&
               tick < 600u)
        {
            if (!avsp_round1_step_player(&encounter_runtime, 0u, 0))
                return 85;
            encounter_runtime.player_action.x = (short)(
                encounter_runtime.first_encounter.alien.x - 68);
            encounter_runtime.player_action.lane =
                encounter_runtime.first_encounter.alien.lane;
            encounter_runtime.player.x = encounter_runtime.player_action.x;
            encounter_runtime.player.y = encounter_runtime.player_action.lane;
            encounter_runtime.player.z = encounter_runtime.player_action.lane;
            if (!avsp_round1_step_scheduler(&encounter_runtime))
                return 85;
            ++tick;
        }
        if (encounter_runtime.first_encounter.alien_contacts != 2u ||
            encounter_runtime.first_encounter.player_damage_events != 1u ||
            encounter_runtime.player.health != 93)
        {
            fprintf(stderr, "contact summary contacts=%lu damage-events=%lu health=%d pending=%u tick=%u attack=%u elapsed=%u\n",
                encounter_runtime.first_encounter.alien_contacts,
                encounter_runtime.first_encounter.player_damage_events,
                encounter_runtime.player.health,
                encounter_runtime.first_encounter.pending_player_damage,
                tick,
                encounter_runtime.first_encounter.alien.state,
                encounter_runtime.first_encounter.alien.attack_elapsed);
            return 86;
        }
        if (!avsp_round1_step_player(&encounter_runtime, 0u, 0))
            return 87;
        if (encounter_runtime.first_encounter.player_damage_events != 2u ||
            encounter_runtime.player.health != 85)
            return 87;
        while (!avsp_pw_can_control(&encounter_runtime.player_action) &&
               tick < 700u)
        {
            if (!avsp_round1_step_player(&encounter_runtime, 0u, 0) ||
                !avsp_round1_step_scheduler(&encounter_runtime))
                return 88;
            ++tick;
        }
        for (selector = 1u; selector <= 4u; ++selector)
        {
            while (encounter_runtime.first_encounter.alien.state ==
                       AVSP_ALIEN_STATE_HIT && tick < 1000u)
            {
                if (!avsp_round1_step_player(&encounter_runtime, 0u, 0) ||
                    !avsp_round1_step_scheduler(&encounter_runtime))
                    return 89;
                ++tick;
            }
            encounter_runtime.player_action.x =
                encounter_runtime.first_encounter.alien.x;
            encounter_runtime.player_action.lane =
                encounter_runtime.first_encounter.alien.lane;
            encounter_runtime.player.x = encounter_runtime.player_action.x;
            encounter_runtime.player.y = encounter_runtime.player_action.lane;
            encounter_runtime.player.z = encounter_runtime.player_action.lane;
            encounter_runtime.player_action.state = AVSP_PW_STATE_ATTACK;
            encounter_runtime.player_action.selector =
                (unsigned short)selector;
            encounter_runtime.player_action.attack_active = 1u;
            if (!avsp_round1_step_scheduler(&encounter_runtime))
            {
                fprintf(stderr, "strike failed selector=%u code=%u failure=%lu state=%u/%u alien=%u health=%d record=%08lx\n",
                    selector, encounter_runtime.scheduler_failure_code,
                    encounter_runtime.failure_count,
                    encounter_runtime.pools[0].records[14].state,
                    encounter_runtime.pools[0].records[14].substate,
                    encounter_runtime.first_encounter.alien.state,
                    encounter_runtime.first_encounter.alien.health,
                    encounter_runtime.pools[0].records[14].animation_record);
                return 90;
            }
            if ((selector < 4u &&
                 (encounter_runtime.pools[0].records[14].animation_record !=
                      AVSP_PORT_V2_HIT_ANIM_RECORD ||
                  encounter_runtime.pools[0].records[14].assembly !=
                      0x00130248UL ||
                  encounter_runtime.pools[0].records[14].hurt_selector != 1u ||
                  encounter_runtime.pools[0].records[14].attack_selector != 0u)) ||
                (selector == 4u &&
                 (encounter_runtime.pools[0].records[14].animation_record !=
                      AVSP_PORT_V2_KO_ANIM_RECORD ||
                  encounter_runtime.pools[0].records[14].assembly !=
                      0x0013020CUL ||
                  encounter_runtime.pools[0].records[14].hurt_selector != 14u ||
                  encounter_runtime.pools[0].records[14].attack_selector != 0u)))
                return 93;
            encounter_runtime.player_action.attack_active = 0u;
            encounter_runtime.player_action.state = AVSP_PW_STATE_CONTROL;
            encounter_runtime.player_action.selector = 0u;
            if (!avsp_round1_step_scheduler(&encounter_runtime))
                return 90;
        }
        while (!encounter_runtime.first_encounter.route_unlocked &&
               tick < 1300u)
        {
            if (!avsp_round1_step_player(&encounter_runtime, 0u, 0) ||
                !avsp_round1_step_scheduler(&encounter_runtime))
                return 91;
            ++tick;
        }
        if (encounter_runtime.first_encounter.hit_events != 3u ||
            encounter_runtime.first_encounter.ko_events != 1u ||
            encounter_runtime.first_encounter.alien_damage_events != 4u ||
            encounter_runtime.first_encounter.alien.health != -1 ||
            encounter_runtime.first_encounter.alien.state !=
                AVSP_ALIEN_STATE_INACTIVE ||
            encounter_runtime.first_encounter.lifecycle_releases != 1u ||
            encounter_runtime.first_encounter.clear_events != 1u ||
            encounter_runtime.first_encounter.encounter_state !=
                AVSP_ROUND1_FIRST_ENCOUNTER_CLEARED ||
            encounter_runtime.first_encounter.reaction.active != 0u ||
            encounter_runtime.pools[0].records[14].active != 0u ||
            encounter_runtime.pools[0].free_count != 11u ||
            encounter_runtime.failure_count != 0u ||
            encounter_runtime.fallback_count != 0u)
        {
            fprintf(stderr, "clear summary hit=%lu ko=%lu damage=%lu health=%d release=%lu clear=%lu estate=%u active=%u free=%u failure=%lu fallback=%lu tick=%u alien-state=%u reaction-active=%u reaction-elapsed=%u\n",
                encounter_runtime.first_encounter.hit_events,
                encounter_runtime.first_encounter.ko_events,
                encounter_runtime.first_encounter.alien_damage_events,
                encounter_runtime.first_encounter.alien.health,
                encounter_runtime.first_encounter.lifecycle_releases,
                encounter_runtime.first_encounter.clear_events,
                encounter_runtime.first_encounter.encounter_state,
                encounter_runtime.pools[0].records[14].active,
                encounter_runtime.pools[0].free_count,
                encounter_runtime.failure_count,
                encounter_runtime.fallback_count, tick,
                encounter_runtime.first_encounter.alien.state,
                encounter_runtime.first_encounter.reaction.active,
                encounter_runtime.first_encounter.reaction.elapsed);
            return 92;
        }
    }
    runtime.entry.gate8236 = 1u;
    if (avsp_round1_entry_valid(&runtime))
        return 49;
    puts("REIMPLEMENT-13 native entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Predator-Button1-parent-child-damage: PASS");
    return 0;
}
