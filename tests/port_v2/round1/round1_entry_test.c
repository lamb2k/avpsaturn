#include "round1.h"

#include <stdio.h>

int main(void)
{
    AvspRound1Runtime runtime;
    unsigned int calls = 0u;
    unsigned short selector;
    const AvspRound1ActorCore *first;
    const AvspRound1ActorCore *last;
    avsp_round1_init(&runtime);
    if (!avsp_round1_entry_valid(&runtime))
        return 1;
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
        short weapon_x = weapon_runtime.player.x;
        short weapon_z = weapon_runtime.player.z;
        unsigned long debit_count;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 1u ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player.substate != 0u ||
            weapon_runtime.player.animation_record != 0x001642f4UL ||
            weapon_runtime.player.assembly != 0x00165694UL ||
            weapon_runtime.player_weapon_entries != 1u ||
            weapon_runtime.player_weapon_attempts_total != 1u ||
            weapon_runtime.player_weapon_allocations != 1u ||
            weapon_runtime.player_weapon_resource_debits != 1u ||
            weapon_runtime.player_resource != 61u ||
            weapon_runtime.player_resource_recharge != 11u ||
            weapon_runtime.player.x != weapon_x ||
            weapon_runtime.player.z != weapon_z)
            return 26;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x0c02u ||
            weapon_runtime.player.animation_record != 0x00165400UL)
            return 27;
        while (weapon_runtime.player_weapon_tick < 48u)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 28;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player_weapon_recovery_pending != 1u ||
            weapon_runtime.player_weapon_tick != 49u ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player_weapon_active != 0u ||
            weapon_runtime.player_weapon_cleanup_pending != 1u ||
            weapon_runtime.player.source_action != 0u ||
            weapon_runtime.player_weapon_completions != 1u ||
            weapon_runtime.player_weapon_allocations != 12u ||
            weapon_runtime.player_resource != 28u ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 1u ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player_weapon_entries != 2u)
            return 29;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 30;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 31;
        if (weapon_runtime.player_weapon_completions != 2u ||
            weapon_runtime.player_weapon_allocations != 24u ||
            weapon_runtime.player_weapon_projectile_free_count != 0u ||
            weapon_runtime.player_weapon_projectiles[7].variant != 1u ||
            weapon_runtime.player_weapon_projectiles[19].variant != 1u ||
            weapon_runtime.player_weapon_projectiles[23].source_slot !=
                0x9200u ||
            weapon_runtime.player_weapon_projectiles[23].owner != 0x8380u ||
            weapon_runtime.player_weapon_projectiles[23].attack_table !=
                0x03136aUL ||
            weapon_runtime.player_weapon_projectiles[0].state != 0u ||
            weapon_runtime.player_weapon_projectiles[0].
                parent_presentation_selector != 6u ||
            weapon_runtime.player_weapon_projectiles[0].angle !=
                (weapon_runtime.player_weapon_projectiles[0].facing ?
                    24u : 40u) ||
            weapon_runtime.player_weapon_projectiles[0].x_fp !=
                (long)weapon_runtime.player_weapon_projectiles[0].x * 65536L)
            return 32;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 33;
        weapon_runtime.player_resource = 64u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 0u;
        debit_count = weapon_runtime.player_weapon_resource_debits;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 34;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 35;
        if (weapon_runtime.player_weapon_attempts_total != 36u ||
            weapon_runtime.player_weapon_allocation_failures != 12u ||
            weapon_runtime.player_weapon_allocations != 24u ||
            weapon_runtime.player_weapon_resource_debits != debit_count ||
            weapon_runtime.player_resource != 64u)
            return 36;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 37;
        weapon_runtime.player_resource = 0u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player.source_action != 0x1a00u ||
            weapon_runtime.player_weapon_empty != 1u ||
            weapon_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            weapon_runtime.player_weapon_allocations != 24u)
            return 38;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x1a02u ||
            weapon_runtime.player.animation_record != 0x001645d4UL ||
            weapon_runtime.player.assembly != 0x00166bf8UL)
            return 39;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 40;
        if (weapon_runtime.player_weapon_completions != 4u ||
            weapon_runtime.player.source_action != 0u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 2u)
            return 41;
        weapon_runtime.player_resource = 64u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 0u;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 8) ||
            weapon_runtime.player_weapon_active != 0u ||
            weapon_runtime.player_weapon_interruptions != 1u ||
            weapon_runtime.player_action.state != AVSP_PW_STATE_HIT ||
            weapon_runtime.player.source_action != 514u ||
            !avsp_round1_entry_valid(&weapon_runtime))
            return 42;
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
        unsigned int entry_calls = 0u;
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
        target = &projectile_runtime.pools[0].records[12];
        target->health = 63;
        target->hurt_selector = 1u;
        target->facing = 0u;
        target->x = (short)(projectile_runtime.player.x +
            (projectile_runtime.player.facing ? 16 : -16));
        target->y = (short)(projectile_runtime.player.y + 16);
        target->z = (short)(projectile_runtime.player.z + 1);
        if (!avsp_round1_step_player(&projectile_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0))
            return 51;
        projectile = &projectile_runtime.player_weapon_projectiles[0];
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->state != 2u || projectile->collision_result != -1 ||
            projectile->attack_selector != 2u || target->health != 39 ||
            target->substate != 0x0200u ||
            projectile->coordinate_mode != 0u ||
            projectile->palette != 0u ||
            projectile->object_or != 0x8000u ||
            projectile->animation_record != 0x000310aeUL ||
            projectile->assembly != 0x00031228UL ||
            projectile_runtime.player_weapon_projectile_initializations != 1u ||
            projectile_runtime.player_weapon_projectile_collision_writes != 1u ||
            projectile_runtime.player_weapon_projectile_damage_writes != 1u)
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
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->state != 6u ||
            !avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->active != 0u ||
            projectile_runtime.player_weapon_projectile_free_count != 24u ||
            projectile_runtime.player_weapon_projectile_releases != 1u)
            return 53;
    }
    {
        AvspRound1Runtime mutation_runtime;
        AvspRound1ActorCore *target;
        AvspRound1WeaponProjectileAllocation *projectile;
        unsigned int entry_calls = 0u;
        avsp_round1_init(&mutation_runtime);
        if (!avsp_round1_begin_first_entry(&mutation_runtime))
            return 54;
        while (!mutation_runtime.entry.control_enabled && entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&mutation_runtime))
                return 54;
            if (mutation_runtime.entry.spawned &&
                !avsp_round1_step_scheduler(&mutation_runtime))
                return 54;
            ++entry_calls;
        }
        for (entry_calls = 17u; entry_calls < 20u; ++entry_calls)
        {
            mutation_runtime.pools[0].records[entry_calls].state = 0u;
            mutation_runtime.pools[0].records[entry_calls].substate = 0u;
        }
        target = &mutation_runtime.pools[0].records[12];
        target->health = 39;
        target->hurt_selector = 1u;
        target->facing = 0u;
        target->x = (short)(mutation_runtime.player.x +
            (mutation_runtime.player.facing ? 16 : -16));
        target->y = (short)(mutation_runtime.player.y + 16);
        target->z = (short)(mutation_runtime.player.z + 1);
        if (!avsp_round1_step_player(&mutation_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0))
            return 55;
        projectile = &mutation_runtime.player_weapon_projectiles[0];
        projectile->damage_class_index = 2u;
        if (!avsp_round1_step_scheduler(&mutation_runtime) ||
            target->health != 8 || projectile->collision_result != -1)
            return 56;
    }
    {
        AvspRound1Runtime impact_runtime;
        unsigned int entry_calls = 0u;
        unsigned int index;
        int saw_source_impact_presentation = 0;
        avsp_round1_init(&impact_runtime);
        if (!avsp_round1_begin_first_entry(&impact_runtime))
            return 57;
        while (!impact_runtime.entry.control_enabled && entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&impact_runtime))
                return 57;
            if (impact_runtime.entry.spawned &&
                !avsp_round1_step_scheduler(&impact_runtime))
                return 57;
            ++entry_calls;
        }
        for (index = 17u; index < 20u; ++index)
        {
            impact_runtime.pools[0].records[index].state = 0u;
            impact_runtime.pools[0].records[index].substate = 0u;
        }
        impact_runtime.pools[3].free_count = impact_runtime.pools[3].capacity;
        for (index = 0u; index < impact_runtime.pools[3].capacity; ++index)
        {
            impact_runtime.pools[3].records[index].active = 0u;
            impact_runtime.pools[3].free_stack[index] = (unsigned short)
                (impact_runtime.pools[3].source_base +
                 index * impact_runtime.pools[3].stride);
        }
        for (index = 0u; index < impact_runtime.pools[0].capacity; ++index)
        {
            impact_runtime.pools[0].records[index].hurt_selector = 0u;
            impact_runtime.pools[0].records[index].x = 2000;
        }
        if (!avsp_round1_step_player(&impact_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0))
            return 58;
        for (index = 0u; index < 90u; ++index)
        {
            int player_ok = avsp_round1_step_player(&impact_runtime, 0u, 0);
            int scheduler_ok = player_ok ?
                avsp_round1_step_scheduler(&impact_runtime) : 0;
            if (!player_ok || !scheduler_ok)
            {
                fprintf(stderr, "impact loop index=%u ok=%d/%d valid=%d failure=%lu alloc=%lu debits=%lu projfree=%u prelease=%lu requests=%lu ialloc=%lu iaudio=%lu irelease=%lu pool24=%u weapon=%u tick=%u action=%u/%u/%lu/%lu/%u/%u locomotion=%u resource=%u recharge=%u player=%d/%d/%d actionpos=%d/%d health=%d/%d\n",
                    index, player_ok, scheduler_ok,
                    avsp_round1_entry_valid(&impact_runtime),
                    impact_runtime.failure_count,
                    impact_runtime.player_weapon_allocations,
                    impact_runtime.player_weapon_resource_debits,
                    impact_runtime.player_weapon_projectile_free_count,
                    impact_runtime.player_weapon_projectile_releases,
                    impact_runtime.player_weapon_impact_requests,
                    impact_runtime.player_weapon_impact_allocations,
                    impact_runtime.player_weapon_impact_audio_events,
                    impact_runtime.player_weapon_impact_releases,
                    impact_runtime.pools[3].free_count,
                    impact_runtime.player_weapon_active,
                    impact_runtime.player_weapon_tick,
                    impact_runtime.player.source_action,
                    impact_runtime.player.substate,
                    impact_runtime.player.animation_record,
                    impact_runtime.player.assembly,
                    impact_runtime.player.hurt_selector,
                    impact_runtime.player.attack_selector,
                    impact_runtime.player_locomotion_action,
                    impact_runtime.player_resource,
                    impact_runtime.player_resource_recharge,
                    impact_runtime.player.x, impact_runtime.player.y,
                    impact_runtime.player.z, impact_runtime.player_action.x,
                    impact_runtime.player_action.lane,
                    impact_runtime.player.health,
                    impact_runtime.player_action.health);
                {
                    unsigned int diagnostic_index;
                    for (diagnostic_index = 0u;
                         diagnostic_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
                         ++diagnostic_index)
                    {
                        const AvspRound1WeaponProjectileAllocation *diagnostic =
                            &impact_runtime.player_weapon_projectiles[diagnostic_index];
                        if (diagnostic->active)
                            fprintf(stderr, " active[%u] slot=%04x class=%d state=%u pos=%d/%d/%d\n",
                                diagnostic_index, diagnostic->source_slot,
                                diagnostic->actor_class, diagnostic->state,
                                diagnostic->x, diagnostic->y, diagnostic->z);
                    }
                }
                return 59;
            }
            {
                unsigned int impact_index;
                for (impact_index = 0u;
                     impact_index < impact_runtime.pools[3].capacity;
                     ++impact_index)
                {
                    const AvspRound1ActorCore *impact =
                        &impact_runtime.pools[3].records[impact_index];
                    if (!avsp_round1_is_weapon_impact_actor(impact))
                        continue;
                    if (impact->coordinate_mode != 0u ||
                        impact->palette != 0u ||
                        impact->object_or != 0x8000u ||
                        impact->animation_record < 0x00086fdcUL ||
                        impact->animation_record > 0x0008701cUL ||
                        impact->assembly < 0x00087180UL ||
                        impact->assembly > 0x000871aaUL)
                        return 60;
                    saw_source_impact_presentation = 1;
                }
            }
        }
        if (impact_runtime.player_weapon_allocations != 12u ||
            impact_runtime.player_weapon_impact_requests != 8u ||
            impact_runtime.player_weapon_impact_allocations != 8u ||
            impact_runtime.player_weapon_impact_allocation_failures != 0u ||
            impact_runtime.player_weapon_impact_audio_events != 8u ||
            impact_runtime.player_weapon_impact_audio_command != 0x0148u ||
            impact_runtime.player_weapon_impact_audio_selector != 0u ||
            impact_runtime.player_weapon_projectile_free_count != 24u ||
            impact_runtime.player_weapon_projectile_releases != 12u ||
            impact_runtime.player_weapon_impact_releases != 8u ||
            impact_runtime.pools[3].free_count != 32u ||
            impact_runtime.player_weapon_projectile_damage_writes != 0u ||
            !saw_source_impact_presentation)
        {
            fprintf(stderr, "impact final alloc=%lu request=%lu ialloc=%lu ifail=%lu audio=%lu command=%04x selector=%u pfree=%u prelease=%lu irelease=%lu pool=%u damage=%lu\n",
                impact_runtime.player_weapon_allocations,
                impact_runtime.player_weapon_impact_requests,
                impact_runtime.player_weapon_impact_allocations,
                impact_runtime.player_weapon_impact_allocation_failures,
                impact_runtime.player_weapon_impact_audio_events,
                impact_runtime.player_weapon_impact_audio_command,
                impact_runtime.player_weapon_impact_audio_selector,
                impact_runtime.player_weapon_projectile_free_count,
                impact_runtime.player_weapon_projectile_releases,
                impact_runtime.player_weapon_impact_releases,
                impact_runtime.pools[3].free_count,
                impact_runtime.player_weapon_projectile_damage_writes);
            return 60;
        }
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
            return 68;
        for (tick = 10u; tick < 20u; ++tick)
            if (transition_runtime.pools[0].records[tick].state != 0x0200u ||
                transition_runtime.pools[0].records[tick].substate != 0u)
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
    runtime.entry.gate8236 = 1u;
    if (avsp_round1_entry_valid(&runtime))
        return 49;
    puts("REIMPLEMENT-13 native entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Button1-projectile-damage-impact: PASS");
    return 0;
}
