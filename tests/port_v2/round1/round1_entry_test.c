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

static void stage_class1f_release(AvspRound1Runtime *runtime,
                                  int keep_index)
{
    unsigned int index;
    unsigned short release_count = 0u;
    for (index = 0u; index < runtime->pools[0].capacity; ++index)
    {
        AvspRound1ActorCore *actor = &runtime->pools[0].records[index];
        if (!actor->active || actor->actor_class != 0x1f)
            continue;
        if ((int)index == keep_index)
        {
            actor->state = 0x0200u;
            actor->substate = 0x1000u;
            actor->source_action = 0x1000u;
            actor->source_action_timer = 0xffu;
            actor->transition_timer = 0xffu;
            continue;
        }
        actor->state = 0x0600u;
        actor->substate = 0u;
        ++release_count;
    }
    runtime->first_encounter.source_living_count = release_count;
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
        {
            fprintf(stderr,
                    "entry scheduler failed calls=%u code=%u slot=%04x route=%u source8209=%u failures=%lu\n",
                    calls, runtime.scheduler_failure_code,
                    runtime.scheduler_failure_source_slot, runtime.route_state,
                    runtime.entry.source_global_8209, runtime.failure_count);
            return 3;
        }
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
        runtime.pools[0].records[10].facing != 1u ||
        runtime.pools[0].records[10].object_or != 0x8000u ||
        runtime.pools[0].records[10].source_action_timer != 46u ||
        runtime.pools[0].records[10].transition_timer != 46u ||
        runtime.pools[0].records[10].source_flags != 0x0fu ||
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
    {
        fprintf(stderr,
            "initial record10 facing=%u timer=%u/%u flags=%02x selector=%u palette=%u object=%04x\n",
            runtime.pools[0].records[10].facing,
            runtime.pools[0].records[10].source_action_timer,
            runtime.pools[0].records[10].transition_timer,
            runtime.pools[0].records[10].source_flags,
            runtime.pools[0].records[10].source_selector83,
            runtime.pools[0].records[10].palette,
            runtime.pools[0].records[10].object_or);
        return 54;
    }
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
        first->source_action != 0x1400u || first->state != 0x0200u ||
        first->substate != 0x1404u || first->health != 87 ||
        last->source_slot != 0x00FF9D00UL || last->x != 632 ||
        last->z != 296 || last->variant != 6u ||
        last->substate != 4096u || last->transition_timer != 44u)
    {
        fprintf(stderr,
                "class1f checkpoint first slot=%08lx x=%d z=%d variant=%u action=%u state=%04x substate=%04x health=%d last slot=%08lx x=%d z=%d variant=%u substate=%04x timer=%u\n",
                first->source_slot, first->x, first->z, first->variant,
                first->source_action, first->state, first->substate,
                first->health, last->source_slot, last->x, last->z,
                last->variant, last->substate, last->transition_timer);
        return 10;
    }
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
    {
        AvspRound1Runtime air_runtime = runtime;
        AvspRound1WeaponProjectileAllocation *projectile =
            &air_runtime.player_weapon_projectiles[0];
        AvspRound1ActorCore *effect = &air_runtime.pools[3].records[29];
        if (!initialize_jump(&air_runtime, AVSP_PW_INPUT_UP) ||
            air_runtime.player_jump_phase != 0x0402u ||
            !avsp_round1_step_player(&air_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_UP, 0) ||
            air_runtime.player_jump_phase != 0x0406u ||
            air_runtime.player.source_action != 0x0406u ||
            air_runtime.player_jump_collision_selector != 9u ||
            air_runtime.player_jump_presentation_selector != 18u ||
            air_runtime.player.animation_record != 0x0015e9d8UL ||
            air_runtime.player.assembly != 0x00161dfcUL ||
            air_runtime.player_resource != 24u ||
            air_runtime.player_resource_recharge != 11u ||
            air_runtime.player_air_weapon_entries != 1u ||
            air_runtime.player_air_weapon_allocations != 1u ||
            air_runtime.player_weapon_resource_debits != 1u ||
            projectile->active != 1u || projectile->actor_class != 3 ||
            projectile->state != 0u || projectile->angle != 3u ||
            projectile->attack_table != 0x0002fc3cUL ||
            projectile->active_collision != 1u ||
            air_runtime.player_air_weapon_effect_x_delta != 0)
        {
            fprintf(stderr,
                "air start phase=%04x action=%04x coll=%u selector=%u anim=%08lx assembly=%08lx resource=%u recharge=%u entries=%lu alloc=%lu debit=%lu pactive=%u class=%d pstate=%u angle=%u attack=%08lx collision=%u xdelta=%d\n",
                air_runtime.player_jump_phase,
                air_runtime.player.source_action,
                air_runtime.player_jump_collision_selector,
                air_runtime.player_jump_presentation_selector,
                air_runtime.player.animation_record,
                air_runtime.player.assembly,
                air_runtime.player_resource,
                air_runtime.player_resource_recharge,
                air_runtime.player_air_weapon_entries,
                air_runtime.player_air_weapon_allocations,
                air_runtime.player_weapon_resource_debits,
                projectile->active, projectile->actor_class,
                projectile->state, projectile->angle,
                projectile->attack_table, projectile->active_collision,
                air_runtime.player_air_weapon_effect_x_delta);
            return 94;
        }
        if (!avsp_round1_step_scheduler(&air_runtime) ||
            projectile->state != 2u || projectile->substate != 0u ||
            projectile->presentation_count != 8u ||
            projectile->animation_record != 0x0002fb48UL ||
            projectile->assembly != 0x0002fbccUL ||
            projectile->attack_selector != 1u)
            return 95;
        if (!avsp_round1_step_scheduler(&air_runtime) ||
            air_runtime.player_air_weapon_motion_updates != 1u ||
            air_runtime.player_air_weapon_effect_requests != 1u ||
            air_runtime.player_air_weapon_effect_allocations != 1u ||
            air_runtime.pools[3].free_count != 1u ||
            effect->active != 1u || effect->actor_class != 0x49 ||
            effect->variant != 1u || effect->state != 2u ||
            effect->effect_timer != 8u ||
            effect->animation_record != projectile->animation_record ||
            effect->assembly != projectile->assembly)
        {
            fprintf(stderr,
                "air motion updates=%lu requests=%lu allocations=%lu pool=%u effect=%u/%d/%u/%u timer=%u anim=%08lx/%08lx assembly=%08lx/%08lx scheduler=%lu\n",
                air_runtime.player_air_weapon_motion_updates,
                air_runtime.player_air_weapon_effect_requests,
                air_runtime.player_air_weapon_effect_allocations,
                air_runtime.pools[3].free_count,
                effect->active, effect->actor_class, effect->variant,
                effect->state, effect->effect_timer,
                effect->animation_record, projectile->animation_record,
                effect->assembly, projectile->assembly,
                air_runtime.scheduler_frames);
            return 96;
        }
        if (!avsp_round1_step_scheduler(&air_runtime) ||
            effect->state != 2u || effect->effect_timer != 7u ||
            air_runtime.player_air_weapon_effect_requests != 1u)
            return 97;
    }
    {
        AvspRound1Runtime air_failure = runtime;
        air_failure.player_weapon_projectile_free_count = 0u;
        air_failure.player_weapon_allocations =
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
        if (!initialize_jump(&air_failure, AVSP_PW_INPUT_UP) ||
            !avsp_round1_step_player(&air_failure,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_UP, 0) ||
            air_failure.player_jump_phase != 0x0406u ||
            air_failure.player_jump_presentation_selector != 18u ||
            air_failure.player_resource != 64u ||
            air_failure.player_weapon_resource_debits != 0u ||
            air_failure.player_air_weapon_entries != 1u ||
            air_failure.player_air_weapon_allocations != 0u ||
            air_failure.player_air_weapon_allocation_failures != 1u ||
            !avsp_round1_entry_valid(&air_failure))
            return 98;
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
        stage_class1f_release(&effect_runtime, -1);
        effect_runtime.player_resource = 0u;
        effect_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&effect_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            effect_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            effect_runtime.player_weapon_empty_auxiliary_allocations != 1u ||
            effect_runtime.pools[3].free_count != 1u)
        {
            fprintf(stderr,
                    "empty effect start requests=%lu allocations=%lu pool3=%u failures=%lu player-valid=%d pool0=%u\n",
                    effect_runtime.player_weapon_empty_auxiliary_requests,
                    effect_runtime.player_weapon_empty_auxiliary_allocations,
                    effect_runtime.pools[3].free_count,
                    effect_runtime.failure_count,
                    avsp_round1_entry_valid(&effect_runtime),
                    effect_runtime.pools[0].free_count);
            return 43;
        }
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
            {
                AvspRound1ActorCore *failed_actor = 0;
                int failed_index;
                for (failed_index = 0; failed_index < 20; ++failed_index)
                    if ((unsigned short)effect_runtime.pools[0].records[
                            failed_index].source_slot ==
                        effect_runtime.scheduler_failure_source_slot)
                        failed_actor = &effect_runtime.pools[0].records[
                            failed_index];
                fprintf(stderr,
                        "empty effect scheduler failure index=%d code=%u slot=%04x failures=%lu pool3=%u airfx=%lu/%lu actor=%04x/%04x action=%04x anim-index=%u timer=%u branch=%d x=%d y=%d z=%d effect=%u action-timer=%u transition-timer=%u\n",
                        index, effect_runtime.scheduler_failure_code,
                        effect_runtime.scheduler_failure_source_slot,
                        effect_runtime.failure_count,
                        effect_runtime.pools[3].free_count,
                        effect_runtime.player_air_weapon_effect_allocations,
                        effect_runtime.player_air_weapon_effect_releases,
                        failed_actor ? failed_actor->state : 0u,
                        failed_actor ? failed_actor->substate : 0u,
                        failed_actor ? failed_actor->source_action : 0u,
                        failed_actor ? failed_actor->animation_index : 0u,
                        failed_actor ? failed_actor->animation_timer : 0u,
                        failed_actor ? failed_actor->animation_branch : 0,
                        failed_actor ? failed_actor->x : 0,
                        failed_actor ? failed_actor->y : 0,
                        failed_actor ? failed_actor->z : 0,
                        failed_actor ? failed_actor->effect_timer : 0u,
                        failed_actor ? failed_actor->source_action_timer : 0u,
                        failed_actor ? failed_actor->transition_timer : 0u);
                return 45;
            }
        if (effect->y != effect_runtime.player.y + 110 ||
            effect->animation_index != 8u ||
            effect->animation_record != 0x0007a11cUL ||
            effect->animation_timer != 8u || effect->animation_branch != 1)
            return 46;
        for (index = 0; index < 8; ++index)
            if (!avsp_round1_step_scheduler(&effect_runtime))
            {
                AvspRound1ActorCore *failed_actor = 0;
                int failed_index;
                for (failed_index = 0; failed_index < 20; ++failed_index)
                    if ((unsigned short)effect_runtime.pools[0].records[
                            failed_index].source_slot ==
                        effect_runtime.scheduler_failure_source_slot)
                        failed_actor = &effect_runtime.pools[0].records[
                            failed_index];
                fprintf(stderr,
                        "empty effect tail scheduler failure index=%d code=%u slot=%04x failures=%lu actor=%04x/%04x action=%04x timer=%u branch=%d action-timer=%u transition=%u\n",
                        index, effect_runtime.scheduler_failure_code,
                        effect_runtime.scheduler_failure_source_slot,
                        effect_runtime.failure_count,
                        failed_actor ? failed_actor->state : 0u,
                        failed_actor ? failed_actor->substate : 0u,
                        failed_actor ? failed_actor->source_action : 0u,
                        failed_actor ? failed_actor->animation_timer : 0u,
                        failed_actor ? failed_actor->animation_branch : 0,
                        failed_actor ? failed_actor->source_action_timer : 0u,
                        failed_actor ? failed_actor->transition_timer : 0u);
                return 47;
            }
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
        stage_class1f_release(&projectile_runtime, 12);
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
            target->state != 0x0402u || target->substate != 0x0000u ||
            target->source_action_timer != 140u ||
            projectile_runtime.player_weapon_projectile_collision_writes != 1u ||
            projectile_runtime.player_weapon_projectile_damage_writes != 1u ||
            projectile_runtime.first_encounter.ko_events != 1u)
        {
            fprintf(stderr, "parent delayed collision p=%d/%d/%d target=%d/%d/%d health=%d substate=%04x result=%d state=%u counts=%lu/%lu code=%u failures=%lu\n",
                projectile->x, projectile->y, projectile->z,
                target->x, target->y, target->z, target->health,
                target->substate, projectile->collision_result, projectile->state,
                projectile_runtime.player_weapon_projectile_collision_writes,
                projectile_runtime.player_weapon_projectile_damage_writes,
                projectile_runtime.scheduler_failure_code,
                projectile_runtime.failure_count);
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
        target->state = 0x0200u;
        target->substate = 0u;
        target->source_action = 0u;
        target->source_action_timer = 0u;
        target->hurt_selector = 1u;
        target->x = child->x;
        target->y = (short)(child->y + 10);
        target->z = child->z;
        projectile->active_collision = 0u;
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            target->health != 32 || target->state != 0x0202u ||
            target->substate != 0x0002u ||
            target->source_action_timer != 38u ||
            child->collision_result != -1 ||
            projectile_runtime.player_weapon_projectile_damage_writes != 2u ||
            projectile_runtime.first_encounter.hit_events != 1u)
        {
            fprintf(stderr,
                    "child collision failed code=%u slot=%04x health=%d substate=%04x result=%d writes=%lu failures=%lu\n",
                    projectile_runtime.scheduler_failure_code,
                    projectile_runtime.scheduler_failure_source_slot,
                    target->health, target->substate,
                    child->collision_result,
                    projectile_runtime.player_weapon_projectile_damage_writes,
                    projectile_runtime.failure_count);
            return 55;
        }
        target->hurt_selector = 0u;
        target->state = 0x0600u;
        target->substate = 0u;
        projectile_runtime.first_encounter.source_living_count = 1u;
        for (entry_calls = 0u; entry_calls < 4u; ++entry_calls)
            if (!avsp_round1_step_scheduler(&projectile_runtime))
            {
                fprintf(stderr,
                        "child cadence scheduler failed i=%u code=%u slot=%04x failures=%lu\n",
                        entry_calls, projectile_runtime.scheduler_failure_code,
                        projectile_runtime.scheduler_failure_source_slot,
                        projectile_runtime.failure_count);
                return 55;
            }
        if (projectile_runtime.player_weapon_allocations != 2u ||
            !avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile_runtime.player_weapon_allocations != 3u)
        {
            fprintf(stderr,
                    "child allocation cadence failed allocations=%lu code=%u slot=%04x failures=%lu\n",
                    projectile_runtime.player_weapon_allocations,
                    projectile_runtime.scheduler_failure_code,
                    projectile_runtime.scheduler_failure_source_slot,
                    projectile_runtime.failure_count);
            return 55;
        }
        for (entry_calls = 0u; entry_calls < 100u; ++entry_calls)
            if (!avsp_round1_step_scheduler(&projectile_runtime))
            {
                fprintf(stderr, "projectile tail scheduler failed i=%u code=%u slot=%u state=%u/%u record=%08lx failures=%lu\n",
                    entry_calls, projectile_runtime.scheduler_failure_code,
                    projectile_runtime.scheduler_failure_source_slot,
                    projectile_runtime.scheduler_failure_state,
                    projectile_runtime.scheduler_failure_substate,
                    projectile_runtime.scheduler_failure_animation_record,
                    projectile_runtime.failure_count);
                return 56;
            }
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
            {
                fprintf(stderr,
                        "transition scheduler failed tick=%u code=%u slot=%04x state=%04x/%04x record=%08lx failures=%lu\n",
                        tick, transition_runtime.scheduler_failure_code,
                        transition_runtime.scheduler_failure_source_slot,
                        transition_runtime.scheduler_failure_state,
                        transition_runtime.scheduler_failure_substate,
                        transition_runtime.scheduler_failure_animation_record,
                        transition_runtime.failure_count);
                return 63;
            }
            if (tick == 6u &&
                (transition_runtime.class09_rng_calls != 44u ||
                 transition_runtime.rng_seed != 0x99e8u))
                return 64;
            if (tick == 1u &&
                (transition_runtime.entry_controller.state != 0x0202u ||
                 transition_runtime.first_encounter.source_intro_gate !=
                    0xffu ||
                 transition_runtime.first_encounter.source_intro_timer != 60u))
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
            if (tick == 16u &&
                (transition_runtime.first_encounter.source_intro_gate != 0u ||
                 transition_runtime.entry_controller.state != 0x0202u ||
                 transition_runtime.first_encounter.source_intro_timer != 60u))
                return 66;
            if (tick == 17u &&
                transition_runtime.first_encounter.source_intro_timer != 59u)
                return 66;
            if (tick == 18u &&
                (transition_runtime.class1f_audio_events != 2u ||
                 transition_runtime.class1f_audio_command != 0x004du ||
                 transition_runtime.class1f_effect_requests != 4u ||
                 transition_runtime.class1f_effect_allocations != 2u ||
                 transition_runtime.class1f_effect_allocation_failures != 2u ||
                 transition_runtime.class1f_effect_guard != 1u))
                return 67;
            if (tick == 77u &&
                (transition_runtime.entry_controller.state != 0x0204u ||
                 transition_runtime.first_encounter.source_intro_timer !=
                    0xffffu ||
                 transition_runtime.first_encounter.source_camera_target !=
                    208u ||
                 transition_runtime.first_encounter.source_living_count !=
                    10u))
                return 67;
            if (tick == 78u &&
                transition_runtime.first_encounter.
                    source_blocked_by_living_count != 1u)
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
            if ((transition_runtime.pools[0].records[tick].active &&
                 (transition_runtime.pools[0].records[tick].state != 0x0200u ||
                  transition_runtime.pools[0].records[tick].actor_class !=
                    0x1f ||
                  !transition_runtime.pools[0].records[tick].
                    source_action_initialized ||
                  transition_runtime.pools[0].records[tick].animation_record ==
                    0u)) ||
                (!transition_runtime.pools[0].records[tick].active &&
                 (transition_runtime.pools[0].records[tick].actor_class != 0 ||
                  transition_runtime.pools[0].records[tick].state != 0u ||
                  transition_runtime.pools[0].records[tick].animation_record !=
                    0u)))
            {
                AvspRound1ActorCore *actor =
                    &transition_runtime.pools[0].records[tick];
                fprintf(stderr,
                        "post-transition actor index=%u active=%u class=%d state=%04x/%04x action=%04x initialized=%u record=%08lx\n",
                        tick, actor->active, actor->actor_class,
                        actor->state, actor->substate, actor->source_action,
                        actor->source_action_initialized,
                        actor->animation_record);
                return 69;
            }
        if (transition_runtime.class1f_action_dispatches == 0u ||
            transition_runtime.class1f_action_releases == 0u)
            return 69;
        if (transition_runtime.first_encounter.dynamic_spawned ||
            transition_runtime.first_encounter.actor_source_slot != 0u)
            return 69;
        for (tick = 131u; tick <= 467u; ++tick)
        {
            if (!avsp_round1_step_scheduler(&transition_runtime))
            {
                fprintf(stderr,
                    "transition tail failed tick=%u scheduler=%lu dispatch=%lu seed=%04x class09=%lu code=%u slot=%04x state=%04x/%04x record=%08lx failures=%lu\n",
                    tick, transition_runtime.scheduler_frames,
                    transition_runtime.scheduler_dispatches,
                    transition_runtime.rng_seed,
                    transition_runtime.class09_rng_calls,
                    transition_runtime.scheduler_failure_code,
                    transition_runtime.scheduler_failure_source_slot,
                    transition_runtime.scheduler_failure_state,
                    transition_runtime.scheduler_failure_substate,
                    transition_runtime.scheduler_failure_animation_record,
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
            int player_step_ok;
            int scheduler_step_ok = 0;
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
            player_step_ok = avsp_round1_step_player(
                &integrated_runtime, mask, 0);
            if (player_step_ok)
                scheduler_step_ok = avsp_round1_step_scheduler(
                    &integrated_runtime);
            if (!player_step_ok || !scheduler_step_ok)
            {
                fprintf(stderr,
                    "integrated tail failed tick=%u player_ok=%d scheduler_ok=%d player=%lu scheduler=%lu dispatch=%lu seed=%04x pool24=%u code=%u slot=%04x state=%04x/%04x valid=%d failures=%lu\n",
                    tick, player_step_ok, scheduler_step_ok,
                    integrated_runtime.player_controller_updates,
                    integrated_runtime.scheduler_frames,
                    integrated_runtime.scheduler_dispatches,
                    integrated_runtime.rng_seed,
                    integrated_runtime.pools[3].free_count,
                    integrated_runtime.scheduler_failure_code,
                    integrated_runtime.scheduler_failure_source_slot,
                    integrated_runtime.scheduler_failure_state,
                    integrated_runtime.scheduler_failure_substate,
                    avsp_round1_entry_valid(&integrated_runtime),
                    integrated_runtime.failure_count);
                fprintf(stderr,
                    "player core=%04x/%04x source_action=%04x action_state=%u loco=%04x stop=%u cleanup=%u jump=%u/%04x weapon=%u/%u return=%u pos=%d/%d action_pos=%d/%d camera=%d/%d target=%d/%d bounds=%d/%d\n",
                    integrated_runtime.player.state,
                    integrated_runtime.player.substate,
                    integrated_runtime.player.source_action,
                    integrated_runtime.player_action.state,
                    integrated_runtime.player_locomotion_action,
                    integrated_runtime.player_stop_ticks,
                    integrated_runtime.player_cleanup_pending,
                    integrated_runtime.player_jump_active,
                    integrated_runtime.player_jump_phase,
                    integrated_runtime.player_weapon_active,
                    integrated_runtime.player_weapon_cleanup_pending,
                    integrated_runtime.player_weapon_return_pending,
                    integrated_runtime.player.x,
                    integrated_runtime.player.z,
                    integrated_runtime.player_action.x,
                    integrated_runtime.player_action.lane,
                    integrated_runtime.camera_x_position,
                    integrated_runtime.camera_z_position,
                    integrated_runtime.camera_x_target,
                    integrated_runtime.camera_z_target,
                    integrated_runtime.navigation_bound_x,
                    integrated_runtime.navigation_bound_z);
                fprintf(stderr,
                    "pools=%u/%u/%u/%u life_release=%lu life_spawn=%u encounter=%u unlock=%u scroll2=%d nav=%u entry=%u/%u/%u/%u timer=%u route=%u\n",
                    integrated_runtime.pools[0].free_count,
                    integrated_runtime.pools[1].free_count,
                    integrated_runtime.pools[2].free_count,
                    integrated_runtime.pools[3].free_count,
                    integrated_runtime.first_encounter.lifecycle_releases,
                    integrated_runtime.first_encounter.dynamic_spawned,
                    integrated_runtime.first_encounter.encounter_state,
                    integrated_runtime.first_encounter.route_unlocked,
                    integrated_runtime.camera_scroll2_x,
                    integrated_runtime.navigation_bounds_active,
                    integrated_runtime.entry.terminal_seen,
                    integrated_runtime.entry.control_enabled,
                    integrated_runtime.entry.gate8236,
                    integrated_runtime.entry.step_index,
                    integrated_runtime.entry.timer_decrements,
                    integrated_runtime.route_state);
                {
                    unsigned int actor_index;
                    for (actor_index = 0u;
                         actor_index < integrated_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *actor =
                            &integrated_runtime.pools[0].records[actor_index];
                        if (actor->active)
                            fprintf(stderr,
                                "pool12[%u] slot=%04x class=%02x updates=%lu state=%04x/%04x action=%04x anim=%08lx\n",
                                actor_index, (unsigned short)actor->source_slot,
                                (unsigned char)actor->actor_class,
                                actor->handler_updates, actor->state,
                                actor->substate, actor->source_action,
                                actor->animation_record);
                    }
                }
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
        for (tick = 0u; tick < 130u; ++tick)
            if (!avsp_round1_step_scheduler(&encounter_runtime))
                return 80;
        tick = 0u;
        {
            unsigned int actor_index;
            unsigned char free_before = encounter_runtime.pools[0].free_count;
            for (actor_index = 0u;
                 actor_index < encounter_runtime.pools[0].capacity;
                 ++actor_index)
            {
                AvspRound1ActorCore *actor =
                    &encounter_runtime.pools[0].records[actor_index];
                if (!actor->active || actor->actor_class != 0x1f)
                    continue;
                actor->state = 0x0200u;
                actor->substate = 0x1000u;
                actor->source_action = 0x1000u;
                actor->source_action_timer = 0xffu;
                actor->transition_timer = 0xffu;
            }
            encounter_runtime.first_encounter.source_living_count = 8u;
            encounter_runtime.first_encounter.source_progress = 0u;
            encounter_runtime.first_encounter.source_spawn_timer = 3900u;
            encounter_runtime.entry_controller.state = 0x0204u;
            if (!avsp_round1_step_scheduler(&encounter_runtime) ||
                encounter_runtime.pools[0].free_count != free_before ||
                !encounter_runtime.first_encounter.source_blocked_by_living_count)
                return 81;
        }
        /* Exercise the accepted 0x028a3e current-state spawn edge without
           inventing production lifecycle releases that are not implemented
           yet: this is the source-supported pre-writer state from the
           bounded counterfactual fixture. */
        {
            AvspRound1Pool *pool = &encounter_runtime.pools[0];
            unsigned int free_index;
            if (pool->records[14].active || pool->free_count == 0u)
                return 81;
            for (free_index = 0u; free_index < pool->free_count; ++free_index)
                if (pool->free_stack[free_index] == 0xa000u)
                    break;
            if (free_index == pool->free_count)
                return 81;
            pool->free_stack[free_index] =
                pool->free_stack[pool->free_count - 1u];
            pool->free_stack[pool->free_count - 1u] = 0xa000u;
        }
        encounter_runtime.first_encounter.source_living_count = 7u;
        encounter_runtime.first_encounter.source_progress = 0u;
        encounter_runtime.first_encounter.source_spawn_timer = 3900u;
        encounter_runtime.first_encounter.source_phase_counter = 7u;
        encounter_runtime.entry_controller.state = 0x0204u;
        encounter_runtime.camera_x_position = 1008;
        encounter_runtime.camera_z_position = 271;
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
            encounter_runtime.first_encounter.presentation.x != 960 ||
            encounter_runtime.first_encounter.presentation.lane != 343 ||
            encounter_runtime.first_encounter.presentation.animation_record == 0UL ||
            encounter_runtime.first_encounter.presentation.assembly == 0UL)
            return 82;
        {
            unsigned long dispatches_before =
                encounter_runtime.class1f_action_dispatches;
            unsigned long movement_before =
                encounter_runtime.class1f_action_movement_steps;
            unsigned long releases_before =
                encounter_runtime.class1f_action_releases;
            for (tick = 0u; tick < 300u; ++tick)
                if (!avsp_round1_step_player(&encounter_runtime, 0u, 0) ||
                    !avsp_round1_step_scheduler(&encounter_runtime))
                    return 83;
            if (!encounter_runtime.first_encounter.dynamic_spawned ||
                encounter_runtime.first_encounter.actor_source_slot !=
                    0x00ffa000UL ||
                encounter_runtime.class1f_action_dispatches <=
                    dispatches_before ||
                encounter_runtime.class1f_action_movement_steps <=
                    movement_before ||
                encounter_runtime.class1f_action_releases < releases_before ||
                encounter_runtime.failure_count != 0u ||
                encounter_runtime.fallback_count != 0u ||
                !avsp_round1_entry_valid(&encounter_runtime))
                return 84;
        }
    }
    {
        AvspRound1Runtime collision_runtime;
        AvspRound1ActorCore *target;
        unsigned int tick = 0u;
        unsigned char free_before;
        avsp_round1_init(&collision_runtime);
        if (!avsp_round1_begin_first_entry(&collision_runtime))
            return 85;
        while (!collision_runtime.entry.control_enabled && tick < 1000u)
        {
            if (!avsp_round1_step_first_entry(&collision_runtime) ||
                (collision_runtime.entry.spawned &&
                 !avsp_round1_step_scheduler(&collision_runtime)))
                return 85;
            ++tick;
        }
        stage_class1f_release(&collision_runtime, 12);
        if (!avsp_round1_step_scheduler(&collision_runtime))
            return 85;
        target = &collision_runtime.pools[0].records[12];
        target->state = 0x0200u;
        target->substate = 0u;
        target->source_action = 0u;
        target->source_action_initialized = 1u;
        target->health = 20;
        target->hurt_selector = 1u;
        target->x = collision_runtime.player_action.x;
        target->y = (short)(collision_runtime.player_action.lane +
            collision_runtime.player_action.height);
        target->z = collision_runtime.player_action.lane;
        collision_runtime.player_action.selector = 4u;
        collision_runtime.player_action.attack_active = 1u;
        if (!avsp_round1_step_scheduler(&collision_runtime) ||
            target->health != 8 || target->state != 0x0202u ||
            target->substate != 2u || target->source_action_timer != 39u ||
            collision_runtime.first_encounter.player_contacts != 1u ||
            collision_runtime.first_encounter.alien_damage_events != 1u ||
            collision_runtime.first_encounter.hit_events != 1u)
        {
            fprintf(stderr,
                    "melee HIT failed health=%d state=%04x/%04x timer=%u tests=%lu contacts=%lu damage=%lu hit=%lu code=%u\n",
                    target->health, target->state, target->substate,
                    target->source_action_timer,
                    collision_runtime.first_encounter.player_contacts,
                    collision_runtime.first_encounter.alien_damage_events,
                    collision_runtime.first_encounter.alien_damage_events,
                    collision_runtime.first_encounter.hit_events,
                    collision_runtime.scheduler_failure_code);
            return 85;
        }
        collision_runtime.player_action.attack_active = 0u;
        for (tick = 0u; tick < 39u; ++tick)
            if (!avsp_round1_step_scheduler(&collision_runtime))
                return 86;
        if (target->source_action_timer != 0u ||
            target->state != 0x0200u || target->substate != 0u ||
            !target->active)
            return 86;
        target->hurt_selector = 1u;
        target->x = collision_runtime.player_action.x;
        target->y = (short)(collision_runtime.player_action.lane +
            collision_runtime.player_action.height);
        target->z = collision_runtime.player_action.lane;
        collision_runtime.player_action.attack_active = 1u;
        if (!avsp_round1_step_scheduler(&collision_runtime) ||
            target->health != -1 || target->state != 0x0402u ||
            target->substate != 0u || target->source_action_timer != 141u ||
            collision_runtime.first_encounter.ko_events != 1u)
            return 87;
        collision_runtime.player_action.attack_active = 0u;
        for (tick = 0u; tick < 141u; ++tick)
            if (!avsp_round1_step_scheduler(&collision_runtime))
                return 88;
        if (!target->active || target->state != 0x0600u ||
            target->source_action_timer != 0u)
            return 88;
        free_before = collision_runtime.pools[0].free_count;
        collision_runtime.first_encounter.source_living_count = 1u;
        if (!avsp_round1_step_scheduler(&collision_runtime) || target->active ||
            collision_runtime.pools[0].free_count !=
                (unsigned char)(free_before + 1u) ||
            collision_runtime.class1f_action_releases == 0u)
            return 89;
    }
    runtime.entry.gate8236 = 1u;
    if (avsp_round1_entry_valid(&runtime))
        return 49;
    puts("REIMPLEMENT-13 native entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Predator-Button1-parent-child-damage: PASS");
    return 0;
}
