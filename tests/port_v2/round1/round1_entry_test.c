#include "round1.h"

#include <stdio.h>
#include <string.h>

static int initialize_jump(AvspRound1Runtime *runtime,
                           unsigned short direction_mask)
{
    unsigned short mask = (unsigned short)(
        AVSP_ROUND1_INPUT_BUTTON3 | direction_mask);
    return avsp_round1_step_player(runtime, mask, 0) &&
        avsp_round1_step_player(runtime, mask, 0) &&
        avsp_round1_step_player(runtime, mask, 0) &&
        avsp_round1_step_player(runtime, mask, 0);
}

static int enter_button1(AvspRound1Runtime *runtime,
                         unsigned short additional_mask)
{
    unsigned short mask = (unsigned short)(
        AVSP_ROUND1_INPUT_BUTTON1 | additional_mask);
    return avsp_round1_step_player(runtime, mask, 0) &&
        avsp_round1_step_player(runtime, mask, 0);
}

static int enter_ground_button1(AvspRound1Runtime *runtime,
                                unsigned short additional_mask)
{
    unsigned short mask = (unsigned short)(
        AVSP_ROUND1_INPUT_BUTTON1 | additional_mask);
    return avsp_round1_step_player(runtime, mask, 0) &&
        avsp_round1_step_player(runtime, mask, 0);
}

static unsigned long source_stage_progress_call_count(
    unsigned int source_frame)
{
    static const unsigned short call_frames[15] = {
        2252u, 2342u, 2432u, 2882u, 2927u,
        3332u, 3377u, 3827u, 3962u, 4052u,
        4127u, 4652u, 4696u, 5102u, 5147u
    };
    unsigned long count = 0u;
    while (count < 15u && call_frames[count] <= source_frame)
        ++count;
    return count;
}

static int class4e_variant0_source_frame_valid(
    const AvspRound1Runtime *runtime, unsigned int source_frame)
{
    const AvspRound1ActorCore *impact = &runtime->pools[3].records[25];
    if (source_frame < 2751u || source_frame > 2762u)
        return 1;
    if (source_frame == 2751u)
        return impact->active == 1u && impact->source_slot == 0x00ffc300UL &&
            impact->type == 24u && impact->actor_class == 0x4e &&
            impact->variant == 0u && impact->state == 0u &&
            impact->x == 1095 && impact->y == 369 && impact->z == 319 &&
            impact->facing == 1u &&
            impact->animation_record == 0x0007a12cUL &&
            impact->assembly == 0x0007a3a0UL;
    if (source_frame == 2752u)
        return impact->active == 1u && impact->state == 0x0200u &&
            impact->x == 1099 && impact->y == 373 && impact->z == 319 &&
            impact->animation_record == 0x000928e0UL &&
            impact->assembly == 0x00092be8UL &&
            impact->animation_timer == 4u &&
            runtime->rng_seed == 0xcb6eu;
    if (source_frame == 2759u)
        return runtime->pools[2].records[12].animation_record ==
                0x0006dbdaUL &&
            runtime->pools[2].records[13].animation_record ==
                0x0006dc6aUL;
    if (source_frame == 2761u)
        return impact->active == 1u && impact->state == 0x0400u &&
            impact->animation_record == 0x00092900UL;
    if (source_frame == 2762u)
        return impact->active == 0u;
    return impact->active == 1u;
}

static int player_hit_source_frame_valid(const AvspRound1Runtime *runtime,
                                         unsigned int source_frame)
{
    static const unsigned short motion_fraction[7] =
        {0xe000u, 0x0000u, 0xa000u, 0x0000u,
         0x6000u, 0xa000u, 0xc000u};
    long expected_x_fp;
    unsigned short expected_timer;
    if (!class4e_variant0_source_frame_valid(runtime, source_frame))
        return 0;
    if (source_frame < 2751u || source_frame > 2778u)
        return 1;
    if (runtime->player.health != 91 ||
        runtime->player_action.health != 91 ||
        runtime->player.y != 320 || runtime->player.z != 320 ||
        runtime->player.source_y_fp != 0x01400000L ||
        runtime->player.attack_selector != 0u)
        return 0;
    if (source_frame == 2751u)
        return runtime->player.state == 0x0202u &&
            runtime->player.substate == 0u &&
            runtime->player.source_x_fp == 0x04430000L &&
            runtime->player.facing == 1u &&
            runtime->player.animation_record == 0x0015f278UL &&
            runtime->player.assembly == 0x00160af2UL &&
            runtime->player.animation_timer == 1u &&
            runtime->player.hurt_selector == 17u &&
            runtime->first_encounter.pending_player_damage == 10u &&
            runtime->player_hit_entries == 1u &&
            runtime->player_hit_audio_events == 0u;
    if (source_frame >= 2752u && source_frame <= 2761u)
        return runtime->player.state == 0x0202u &&
            runtime->player.substate == 0x0200u &&
            runtime->player.source_x_fp == (long)(
                (source_frame & 1u) ? 0x04410000L : 0x04430000L) &&
            runtime->player.facing == 1u &&
            runtime->player.animation_record == 0x0015eee8UL &&
            runtime->player.assembly == 0x00160edeUL &&
            runtime->player.animation_timer == 8u &&
            runtime->player.animation_branch == (short)-32768 &&
            runtime->player.hurt_selector == 0u &&
            runtime->player_hit_audio_events == 1u &&
            runtime->player_hit_audio_command == 0x003bu;
    if (source_frame >= 2762u && source_frame <= 2769u)
    {
        expected_timer = (unsigned short)(2769u - source_frame);
        if (expected_timer == 0u)
            expected_timer = 8u;
        return runtime->player.state == 0x0202u &&
            runtime->player.substate == 0x0202u &&
            runtime->player.source_x_fp == 0x04430000L &&
            runtime->player.facing == 1u &&
            runtime->player.animation_record == 0x0015eee8UL &&
            runtime->player.animation_timer == expected_timer;
    }
    if (source_frame >= 2770u && source_frame <= 2776u)
    {
        expected_x_fp = 0x04430000L +
            motion_fraction[source_frame - 2770u];
        expected_timer = (unsigned short)(2777u - source_frame);
        return runtime->player.state == 0x0202u &&
            runtime->player.substate == 0x0202u &&
            runtime->player.source_x_fp == expected_x_fp &&
            runtime->player.facing == 1u &&
            runtime->player.animation_record == 0x0015eee8UL &&
            runtime->player.animation_timer == expected_timer;
    }
    if (source_frame == 2777u)
        return runtime->player.state == 0x0202u &&
            runtime->player.substate == 0x0204u &&
            runtime->player.source_x_fp == 0x0443c000L &&
            runtime->player.facing == 0u &&
            runtime->player.animation_record == 0x0015f1f4UL &&
            runtime->player.assembly == 0x001626a4UL &&
            runtime->player.animation_timer == 0x0fffu;
    return runtime->player.state == 0x0200u &&
        runtime->player.substate == 0u &&
        runtime->player.source_x_fp == 0x0443c000L &&
        runtime->player.facing == 0u &&
        runtime->player.animation_record == 0x0015f1f4UL &&
        runtime->player_hit_active == 0u &&
        runtime->player_hit_invulnerability == 1u &&
        runtime->player_hit_completions == 1u;
}

static int player_hit_type16_source_frame_valid(
    const AvspRound1Runtime *runtime, unsigned int source_frame)
{
    if (source_frame < 3264u || source_frame > 3314u)
        return 1;
    if (runtime->player.health != 78 ||
        runtime->player_action.health != 78 ||
        runtime->player_hit_reaction_index != 1u ||
        runtime->player_hit_kind != 9u ||
        runtime->player_hit_presentation_selector != 10u ||
        runtime->player_hit_active_body_selector != 0u)
        return 0;
    if (source_frame == 3264u)
        return runtime->player.state == 0x0202u &&
            runtime->player.substate == 0u &&
            runtime->player.source_x_fp == 0x04a08000L &&
            runtime->player.animation_record == 0x0015f248UL &&
            runtime->player.animation_timer == 1u &&
            runtime->player.hurt_selector == 17u &&
            runtime->first_encounter.pending_player_damage == 17u &&
            runtime->player_hit_phase == 1u;
    if (source_frame == 3265u)
        return runtime->player.substate == 0x0200u &&
            runtime->player.source_x_fp == 0x04a08000L &&
            runtime->player.animation_record == 0x0015ef24UL &&
            runtime->player.assembly == 0x00160f3cUL &&
            runtime->player_hit_shake_remaining == 20u;
    if (source_frame == 3284u)
        return runtime->player.substate == 0x0200u &&
            runtime->player.source_x_fp == 0x049e8000L &&
            runtime->player_hit_shake_remaining == 1u;
    if (source_frame == 3285u)
        return runtime->player.substate == 0x0202u &&
            runtime->player.source_x_fp == 0x04a08000L &&
            runtime->player_hit_phase == 3u &&
            runtime->player_hit_x_velocity == 0x00034000L &&
            runtime->player_hit_x_acceleration == -0x00002000L &&
            runtime->player.animation_timer == 7u;
    if (source_frame == 3312u)
        return runtime->player.substate == 0x0204u &&
            runtime->player.source_x_fp == 0x04a06000L &&
            runtime->player.animation_record == 0x0015f1f4UL &&
            runtime->player.facing == 0u;
    if (source_frame == 3313u)
        return runtime->player.state == 0x0200u &&
            runtime->player.substate == 0u &&
            runtime->player.source_x_fp == 0x04a06000L &&
            runtime->player_hit_active == 0u &&
            runtime->player_hit_invulnerability == 1u;
    if (source_frame == 3314u)
        return runtime->player.state == 0x0200u &&
            runtime->player.substate == 0x0200u &&
            runtime->player.source_x_fp == 0x04a0a000L &&
            runtime->player.animation_record == 0x0015f208UL &&
            runtime->player_hit_invulnerability == 0u;
    return 1;
}

static int player_weapon_fractional_latch_source_frame_valid(
    const AvspRound1Runtime *runtime, unsigned int source_frame)
{
    if (source_frame < 3331u || source_frame > 3333u)
        return 1;
    if (runtime->player.source_x_fp != 0x04a0e000L ||
        runtime->player.source_y_fp != 0x01400000L)
        return 0;
    if (source_frame == 3331u)
        return runtime->player.substate == 0x0202u;
    if (source_frame == 3332u)
        return runtime->player.substate == 0x0c00u;
    return runtime->player.substate == 0x0c02u;
}

static int class1f_slot_a3c0_lifetime_source_frame_valid(
    const AvspRound1Runtime *runtime, unsigned int source_frame)
{
    const AvspRound1ActorCore *actor = &runtime->pools[0].records[19];
    if (source_frame < 2511u || source_frame > 3975u)
        return 1;
    return actor->active != 0u &&
        actor->source_slot == 0x00ffa3c0UL &&
        actor->type == 12u && actor->actor_class == 0x1f;
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
        runtime.navigation_bound_x != 648 || runtime.navigation_bound_z != 256 ||
        runtime.camera_x_position != 648 ||
        runtime.camera_x_target != 648 ||
        runtime.camera_x_lower != 640 || runtime.camera_x_upper != 832 ||
        runtime.camera_z_position != 256 ||
        runtime.camera_z_lower != 256 || runtime.camera_z_upper != 256 ||
        runtime.camera_scroll2_x != 584 ||
        runtime.camera_guard_countdown != 1200u ||
        runtime.pools[0].free_count != 10u ||
        runtime.pools[2].free_count != 12u ||
        runtime.pools[3].free_count != 30u ||
        runtime.scheduler_frames != 170u ||
        runtime.scheduler_dispatches != 2720u ||
        runtime.class1f_initializations != 10u ||
        runtime.class1f_initial_rng_calls != 10u ||
        runtime.class09_initializations != 2u ||
        runtime.class09_rng_calls != 42u ||
        runtime.class0a_initializations != 1u ||
        runtime.class0a_animation_steps != 169u ||
        runtime.rng_seed != 0x334fu ||
        runtime.player.source_target_low != 0xce00u ||
        runtime.source_stage_parameter != 8u ||
        runtime.coffee_stage_setup_complete != 1u ||
        runtime.coffee_stage_setup_calls != 1u ||
        !avsp_round1_entry_valid(&runtime))
    {
        fprintf(stderr, "entry final calls=%u route=%d state=%u spawn=%u dec=%u step=%u gates=%u/%u g8209=%u cursor=%08lx nav=%u/%d/%d cam=%d/%d/%d/%d/%d/%d/%d guard=%u free=%u/%u/%u sched=%lu/%lu init=%lu/%lu c09=%lu/%lu rng=%04x stage=%u stage_calls=%lu valid=%d\n",
                calls, runtime.route_state, runtime.player.state,
                runtime.entry.spawn_count, runtime.entry.timer_decrements,
                runtime.entry.step_index, runtime.entry.gate8236,
                runtime.entry.gate81af, runtime.entry.source_global_8209,
                runtime.entry.script_cursor, runtime.navigation_bounds_active,
                runtime.navigation_bound_x, runtime.navigation_bound_z,
                runtime.camera_x_position, runtime.camera_x_target,
                runtime.camera_x_lower, runtime.camera_x_upper,
                runtime.camera_z_position, runtime.camera_z_lower,
                runtime.camera_z_upper, runtime.camera_guard_countdown,
                runtime.pools[0].free_count, runtime.pools[2].free_count,
                runtime.pools[3].free_count, runtime.scheduler_frames,
                runtime.scheduler_dispatches, runtime.class1f_initializations,
                runtime.class1f_initial_rng_calls,
                runtime.class09_initializations, runtime.class09_rng_calls,
                runtime.rng_seed, runtime.source_stage_parameter,
                runtime.coffee_stage_setup_calls,
                avsp_round1_entry_valid(&runtime));
        return 5;
    }
    if (runtime.pools[0].records[10].coordinate_mode != 1u ||
        runtime.pools[0].records[10].palette != 16u ||
        runtime.pools[0].records[10].facing != 1u ||
        runtime.pools[0].records[10].object_or != 0x8000u ||
        runtime.pools[0].records[10].source_action_timer != 47u ||
        runtime.pools[0].records[10].transition_timer != 47u ||
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
    {
        AvspRound1Runtime walk_runtime = runtime;
        for (calls = 0u; calls < 46u; ++calls)
            if (!avsp_round1_step_player(&walk_runtime,
                    AVSP_PW_INPUT_RIGHT, 0))
                return 186;
        if (walk_runtime.player.animation_record != 0x0015f2b8UL ||
            walk_runtime.player.assembly != 0x00160b9eUL ||
            walk_runtime.player.animation_timer != 4u ||
            walk_runtime.player.animation_branch != (short)-32768 ||
            walk_runtime.player.hurt_selector != 17u ||
            walk_runtime.player.attack_selector != 0u)
            return 186;
        for (calls = 0u; calls < 4u; ++calls)
            if (!avsp_round1_step_player(&walk_runtime,
                    AVSP_PW_INPUT_RIGHT, 0))
                return 186;
        if (walk_runtime.player.animation_record != 0x0015f208UL ||
            walk_runtime.player.assembly != 0x00160a02UL ||
            walk_runtime.player.animation_timer != 4u ||
            walk_runtime.player.hurt_selector != 17u ||
            walk_runtime.player.attack_selector != 0u)
            return 186;
    }
    {
        AvspRound1Runtime fractional_walk_runtime = runtime;
        fractional_walk_runtime.player.source_x_fp = 0x03b09000L;
        fractional_walk_runtime.player.x = 944;
        fractional_walk_runtime.player_action.x = 944;
        fractional_walk_runtime.player_action.x_numerator = 15L;
        fractional_walk_runtime.player_action.direction_history[0] =
            AVSP_PW_INPUT_RIGHT;
        fractional_walk_runtime.player_action.direction_history[1] =
            AVSP_PW_INPUT_RIGHT;
        if (!avsp_round1_step_player(&fractional_walk_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            fractional_walk_runtime.player.source_x_fp != 0x03b2d000L ||
            fractional_walk_runtime.player.x != 946)
            return 186;
    }
    {
        AvspPwRuntime direction_queue_runtime;
        AvspPwInput direction_queue_input;
        short queue_start_x;
        avsp_pw_init(&direction_queue_runtime);
        direction_queue_runtime.direction_history[0] = AVSP_PW_INPUT_RIGHT;
        direction_queue_runtime.direction_history[1] = AVSP_PW_INPUT_LEFT;
        direction_queue_input.mask = AVSP_PW_INPUT_RIGHT;
        direction_queue_input.received_damage = 0;
        queue_start_x = direction_queue_runtime.x;
        avsp_pw_step_round1(&direction_queue_runtime, &direction_queue_input);
        if (direction_queue_runtime.x <= queue_start_x)
            return 186;
    }
    if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        runtime.player.source_x_fp != 0x03b00000L ||
        !avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        runtime.player.source_x_fp != 0x03b24000L ||
        runtime.player.substate != 0x0200u ||
        runtime.player.animation_record != 0x0015f208UL ||
        runtime.player.assembly != 0x00160a02UL ||
        runtime.player.animation_timer != 4u ||
        runtime.player.hurt_selector != 17u ||
        runtime.player.attack_selector != 0u ||
        !avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        runtime.player.source_x_fp != 0x03b48000L ||
        runtime.player.substate != 0x0202u ||
        runtime.player.animation_record != 0x0015f208UL ||
        runtime.player.assembly != 0x00160a02UL ||
        runtime.player.animation_timer != 3u ||
        runtime.player.hurt_selector != 17u ||
        runtime.player.attack_selector != 0u ||
        !avsp_round1_step_player(&runtime, 0u, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x <= 944 || runtime.player.z != 320 ||
        runtime.player.facing != 1u || runtime.player_controller_updates != 5u ||
        runtime.player.substate != 0x0204u ||
        runtime.player_locomotion_action != 0x0204u ||
        runtime.player_stop_ticks != 10u ||
        !avsp_round1_entry_valid(&runtime))
    {
        fprintf(stderr,
            "locomotion x=%d z=%d facing=%u updates=%lu substate=%04x action=%04x stop=%u failures=%lu\n",
            runtime.player.x, runtime.player.z, runtime.player.facing,
            runtime.player_controller_updates, runtime.player.substate,
            runtime.player_locomotion_action, runtime.player_stop_ticks,
            runtime.failure_count);
        return 6;
    }
    if (!avsp_round1_step_scheduler(&runtime) ||
        runtime.scheduler_trace_count != 17u ||
        runtime.scheduler_frames != 171u ||
        runtime.scheduler_dispatches != 2737u ||
        runtime.actor_handler_dispatches != 1710u ||
        runtime.presentation_bindings != 1710u ||
        runtime.state_context_bindings != 1710u ||
        runtime.pools[0].records[10].assembly != 0x0012FA2AUL ||
        runtime.pools[0].records[10].hurt_selector != 2u ||
        runtime.pools[0].records[10].attack_selector != 0u ||
        runtime.pools[0].records[16].assembly != 0x0012F9E4UL ||
        runtime.pools[0].records[16].hurt_selector != 1u ||
        runtime.pools[0].records[10].dispatch_entry != 0x00060532UL)
    {
        fprintf(stderr,
            "post-entry scheduler trace=%u frames=%lu dispatch=%lu handlers=%lu presentation=%lu context=%lu asm10=%08lx hurt10=%u attack10=%u asm16=%08lx hurt16=%u entry10=%08lx\n",
            runtime.scheduler_trace_count, runtime.scheduler_frames,
            runtime.scheduler_dispatches, runtime.actor_handler_dispatches,
            runtime.presentation_bindings, runtime.state_context_bindings,
            runtime.pools[0].records[10].assembly,
            runtime.pools[0].records[10].hurt_selector,
            runtime.pools[0].records[10].attack_selector,
            runtime.pools[0].records[16].assembly,
            runtime.pools[0].records[16].hurt_selector,
            runtime.pools[0].records[10].dispatch_entry);
        return 7;
    }
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
    runtime.pools[2].free_count = 11u;
    runtime.pools[3].records[0].active = 1u;
    runtime.pools[3].records[0].actor_class = 0x10;
    runtime.pools[3].records[0].type = 24u;
    runtime.pools[3].records[0].variant = 0u;
    runtime.pools[3].records[0].source_facing_selector = 1u;
    runtime.pools[3].records[0].source_slot = 0x00ffb680UL;
    runtime.pools[3].free_count = 2u;
    if (!avsp_round1_step_scheduler(&runtime) ||
        runtime.scheduler_trace_count != 20u ||
        runtime.scheduler_frames != 172u ||
        runtime.scheduler_dispatches != 2757u ||
        runtime.actor_handler_dispatches != 1720u ||
        runtime.presentation_bindings != 1720u ||
        runtime.state_context_bindings != 1720u ||
        runtime.scheduler_trace[10].record_type != 16u ||
        runtime.scheduler_trace[11].record_type != 20u ||
        runtime.scheduler_trace[12].record_type != 20u ||
        runtime.scheduler_trace[17].record_type != 24u ||
        runtime.scheduler_trace[18].actor_class != 0x44 ||
        runtime.pools[0].records[10].scheduler_updates != 172u ||
        runtime.pools[0].records[10].handler_updates != 172u ||
        runtime.pools[0].records[10].state_handler_updates != 172u)
    {
        fprintf(stderr,
            "mixed scheduler ok=%u trace=%u frames=%lu dispatch=%lu handlers=%lu presentation=%lu context=%lu types=%u/%u/%u/%u class15=%u updates=%lu/%lu/%lu code=%u\n",
            runtime.scheduler_failure_code == 0u,
            runtime.scheduler_trace_count, runtime.scheduler_frames,
            runtime.scheduler_dispatches, runtime.actor_handler_dispatches,
            runtime.presentation_bindings, runtime.state_context_bindings,
            runtime.scheduler_trace[10].record_type,
            runtime.scheduler_trace[11].record_type,
            runtime.scheduler_trace[12].record_type,
            runtime.scheduler_trace[14].record_type,
            runtime.scheduler_trace[15].actor_class,
            runtime.pools[0].records[10].scheduler_updates,
            runtime.pools[0].records[10].handler_updates,
            runtime.pools[0].records[10].state_handler_updates,
            runtime.scheduler_failure_code);
        return 9;
    }
    runtime.pools[3].records[0].active = 0u;
    runtime.pools[3].free_count = 30u;
    first = &runtime.pools[0].records[19];
    last = &runtime.pools[0].records[10];
    if (first->source_slot != 0x00FFA3C0UL || first->x != 713 ||
        first->z != 312 || first->variant != 0u ||
        first->source_action != 0x1400u || first->state != 0x0200u ||
        first->substate != 0x1404u || first->health != 87 ||
        last->source_slot != 0x00FF9D00UL || last->x != 632 ||
        last->z != 296 || last->variant != 0u ||
        last->substate != 4096u || last->transition_timer != 45u)
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
        runtime.player.x != 1034 || runtime.player.z != 327)
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
        runtime.player.x != 725 || runtime.player.z != 272 ||
        runtime.navigation_applications != 7u ||
        runtime.navigation_clamps != 4u)
    {
        fprintf(stderr,
                "low clamp x=%d z=%d action_x=%d lane=%d applications=%lu clamps=%lu camera=%d,%d phase=%u stream=%lu failures=%lu\n",
                runtime.player.x, runtime.player.z,
                runtime.player_action.x, runtime.player_action.lane,
                runtime.navigation_applications, runtime.navigation_clamps,
                runtime.camera_x_position, runtime.camera_z_position,
                runtime.terrain_stream_phase_x,
                runtime.terrain_stream_transactions,
                runtime.terrain_stream_failures);
        return 12;
    }
    for (calls = 0u; calls < 8u; ++calls)
        if (!avsp_round1_step_player(&runtime, 0u, 0))
        {
            fprintf(stderr,
                    "stop step=%u camera=%d,%d phase=%u stream=%lu last=%u failures=%lu\n",
                    calls, runtime.camera_x_position,
                    runtime.camera_z_position,
                    runtime.terrain_stream_phase_x,
                    runtime.terrain_stream_transactions,
                    runtime.terrain_stream_last_transaction,
                    runtime.terrain_stream_failures);
            return 13;
        }
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
        runtime.navigation_applications != 16u ||
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
        navigation_runtime.camera_x_previous = 832;
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
        if (!avsp_round1_step_scheduler(&navigation_runtime))
            return 76;
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
        navigation_runtime.camera_x_previous = 832;
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
        if (!avsp_round1_step_scheduler(&navigation_runtime))
            return 77;
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
        camera_runtime.first_encounter.source_field46 = 1200u;
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
        if (locked_steps != 1201u ||
            camera_runtime.camera_coffee_phase != 4u ||
            camera_runtime.camera_x_upper != 1008 ||
            camera_runtime.camera_unlocks != runtime.camera_unlocks + 1u)
        {
            fprintf(stderr, "camera locked=%u phase=%u upper=%d unlock=%lu base=%lu rng=%04x stage=%u failure=%lu\n",
                    locked_steps, camera_runtime.camera_coffee_phase,
                    camera_runtime.camera_x_upper,
                    camera_runtime.camera_unlocks, runtime.camera_unlocks,
                    camera_runtime.rng_seed,
                    camera_runtime.source_stage_parameter,
                    camera_runtime.failure_count);
            return 81;
        }
    }
    {
        AvspRound1Runtime jump_runtime = runtime;
        unsigned short mask = AVSP_ROUND1_INPUT_BUTTON3;
        if (!avsp_round1_step_player(&jump_runtime, mask, 0) ||
            jump_runtime.player_jump_active != 1u ||
            jump_runtime.player_jump_dispatch_delay != 1u ||
            jump_runtime.player_jump_entries != 0u ||
            jump_runtime.player.source_action == 0x0400u ||
            !avsp_round1_step_player(&jump_runtime, mask, 0) ||
            jump_runtime.player_jump_dispatch_delay != 0u ||
            jump_runtime.player_jump_entries != 1u ||
            jump_runtime.player.source_action != 0x0400u ||
            jump_runtime.player.animation_record != 0x0015f2ccUL ||
            !avsp_round1_step_player(&jump_runtime, mask, 0) ||
            jump_runtime.player.source_action != 0x0400u ||
            jump_runtime.player.animation_record != 0x0015f2dcUL ||
            !avsp_round1_step_player(&jump_runtime, mask, 0) ||
            jump_runtime.player.source_action != 0x0402u)
            return 82;
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
            {4u, 4u, 5u, 15u, 15u, 5u, 5u, 6u, 6u, 6u};
        static const unsigned char collisions[10] =
            {3u, 3u, 2u, 8u, 8u, 2u, 1u, 4u, 4u, 1u};
        static const unsigned long records[10] = {
            0x0015f2f0UL, 0x0015f2f0UL, 0x0015f344UL,
            0x0015f43cUL, 0x0015f43cUL, 0x0015f344UL,
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
        jump_runtime.player.source_y_fp =
            (long)jump_runtime.player_action.lane * 65536L + 0x3800L;
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
            jump_runtime.player.animation_timer != 0x0fffu ||
            jump_runtime.player.animation_branch != (short)0x8000 ||
            (jump_runtime.player.source_y_fp & 0xffffL) != 0x3800L ||
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
            !enter_button1(&air_runtime, AVSP_PW_INPUT_UP) ||
            air_runtime.player_jump_phase != 0x0406u ||
            air_runtime.player.source_action != 0x0406u ||
            air_runtime.player_jump_collision_selector != 9u ||
            air_runtime.player_jump_presentation_selector != 18u ||
            air_runtime.player.animation_record != 0x0015e9d8UL ||
            air_runtime.player.assembly != 0x00161dfcUL ||
            air_runtime.player_jump_animation_timer != 2u ||
            air_runtime.player.animation_timer != 2u ||
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
            !avsp_round1_step_scheduler(&air_runtime) ||
            air_runtime.player_air_weapon_motion_updates != 2u ||
            air_runtime.player_air_weapon_effect_requests != 1u ||
            air_runtime.player_air_weapon_effect_allocations != 1u ||
            air_runtime.pools[3].free_count != 29u ||
            effect->active != 1u || effect->actor_class != 0x49 ||
            effect->variant != 1u || effect->state != 2u ||
            effect->effect_timer != 7u ||
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
            effect->state != 2u || effect->effect_timer != 6u ||
            air_runtime.player_air_weapon_effect_requests != 1u)
        {
            fprintf(stderr,
                "air effect followup state=%u timer=%u requests=%lu branch=%d anim_timer=%d\n",
                effect->state, effect->effect_timer,
                air_runtime.player_air_weapon_effect_requests,
                effect->animation_branch, effect->animation_timer);
            return 97;
        }
    }
    {
        AvspRound1Runtime air_failure = runtime;
        air_failure.player_weapon_projectile_free_count = 0u;
        air_failure.player_weapon_allocations =
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
        if (!initialize_jump(&air_failure, AVSP_PW_INPUT_UP) ||
            !enter_button1(&air_failure, AVSP_PW_INPUT_UP) ||
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
    {
        AvspRound1Runtime contextual_motion = runtime;
        short entry_x;
        unsigned short mask = (unsigned short)(
            AVSP_PW_INPUT_ATTACK | AVSP_PW_INPUT_RIGHT);
        if (!avsp_round1_step_player(&contextual_motion, mask, 0))
            return 131;
        entry_x = contextual_motion.player_action.x;
        if (!avsp_round1_step_player(&contextual_motion, mask, 0) ||
            !avsp_round1_step_player(&contextual_motion, mask, 0) ||
            contextual_motion.player_action.x != entry_x)
            return 131;
    }
    {
        AvspRound1Runtime contextual = runtime;
        unsigned long seen = 0u;
        unsigned int steps = 0u;
        if (!avsp_round1_step_player(&contextual, AVSP_PW_INPUT_ATTACK, 0) ||
            contextual.player_contextual_melee_active != 1u ||
            contextual.player_contextual_melee_entries != 0u)
            return 124;
        if (!avsp_round1_step_player(&contextual, AVSP_PW_INPUT_ATTACK, 0) ||
            contextual.player.source_action != 0x1400u ||
            contextual.player.animation_record != 0x0015f1f4UL ||
            contextual.player.animation_timer != 4094u ||
            contextual.player_contextual_melee_entries != 1u ||
            contextual.player_contextual_melee_audio_events != 1u ||
            contextual.player_contextual_melee_audio_command != 0x0036u)
        {
            fprintf(stderr, "context entry active=%u action=%04x record=%08lx entries=%lu audio=%lu/%04x valid=%d\n",
                contextual.player_contextual_melee_active,
                contextual.player.source_action,
                contextual.player.animation_record,
                contextual.player_contextual_melee_entries,
                contextual.player_contextual_melee_audio_events,
                contextual.player_contextual_melee_audio_command,
                avsp_round1_entry_valid(&contextual));
            return 124;
        }
        if (!avsp_round1_step_player(&contextual, AVSP_PW_INPUT_ATTACK, 0) ||
            contextual.player.source_action != 0x1402u ||
            contextual.player.animation_record != 0x00160288UL ||
            contextual.player.animation_timer != 1u ||
            contextual.player.hurt_selector != 1u)
            return 124;
        seen = 1u;
        steps = 1u;
        while (contextual.player_contextual_melee_active && steps < 20u)
        {
            if (!avsp_round1_step_player(&contextual,
                    steps == 0u ? AVSP_PW_INPUT_ATTACK : 0u, 0))
            {
                fprintf(stderr, "context step failed step=%u active=%u index=%u timer=%u branch=%d action=%04x valid=%d failures=%lu\n",
                    steps, contextual.player_contextual_melee_active,
                    contextual.player_contextual_melee_animation_index,
                    contextual.player_contextual_melee_animation_timer,
                    contextual.player_contextual_melee_animation_branch,
                    contextual.player.source_action,
                    avsp_round1_entry_valid(&contextual),
                    contextual.failure_count);
                return 128;
            }
            if (contextual.player.animation_record >= 0x00160288UL &&
                contextual.player.animation_record <= 0x001602c8UL)
                seen |= 1UL << ((contextual.player.animation_record -
                                 0x00160288UL) >> 4);
            ++steps;
        }
        if (contextual.player_contextual_melee_active || steps != 12u ||
            seen != 0x1fUL ||
            contextual.player_contextual_melee_completions != 1u ||
            contextual.player_contextual_melee_toggle87 != 1u ||
            contextual.player.source_action != 0u)
        {
            fprintf(stderr, "context complete active=%u steps=%u seen=%lx completions=%lu toggle=%u action=%04x record=%08lx timer=%u branch=%d\n",
                contextual.player_contextual_melee_active, steps, seen,
                contextual.player_contextual_melee_completions,
                contextual.player_contextual_melee_toggle87,
                contextual.player.source_action,
                contextual.player.animation_record,
                contextual.player.animation_timer,
                contextual.player.animation_branch);
            return 124;
        }
        if (!avsp_round1_step_player(&contextual, AVSP_PW_INPUT_ATTACK, 0) ||
            !avsp_round1_step_player(&contextual, AVSP_PW_INPUT_ATTACK, 0) ||
            contextual.player_contextual_melee_entries != 2u ||
            contextual.player_contextual_melee_audio_command != 0x0101u)
            return 125;
        for (steps = 0u; steps < 8u; ++steps)
            if (!avsp_round1_step_player(&contextual,
                    steps == 0u ? AVSP_PW_INPUT_ATTACK : 0u, 0))
                return 125;
        contextual.player_resource = 0u;
        contextual.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&contextual,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            !avsp_round1_step_player(&contextual,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            contextual.player_contextual_melee_active != 0u ||
            contextual.player_contextual_melee_interruptions != 1u ||
            contextual.player.source_action != 0x1a00u ||
            contextual.player.animation_record != 0x001602b8UL ||
            contextual.player.animation_timer != 2u)
            return 125;
    }
    /* The legacy four-strike unit lane exercises the no-target dispatch. */
    runtime.player.source_target_low = 0u;
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
        AvspRound1Runtime empty_latch_runtime = runtime;
        AvspRound1Runtime empty_walk_runtime = runtime;
        short weapon_x;
        short weapon_z;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player.x == runtime.player.x)
            return 116;
        weapon_x = weapon_runtime.player.x;
        weapon_z = weapon_runtime.player.z;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player_weapon_active != 0u ||
            weapon_runtime.player.x == weapon_x)
            return 117;
        weapon_x = weapon_runtime.player.x;
        weapon_z = weapon_runtime.player.z;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 1u ||
            weapon_runtime.player_weapon_dispatch_delay != 0u ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player.substate != 0x0c00u ||
            weapon_runtime.player_weapon_entries != 1u ||
            weapon_runtime.player_weapon_attempts_total != 0u ||
            weapon_runtime.player_weapon_allocations != 0u ||
            weapon_runtime.player_weapon_resource_debits != 0u ||
            weapon_runtime.player_resource != 64u ||
            weapon_runtime.player_resource_recharge != 12u ||
            weapon_runtime.player_action.state != AVSP_PW_STATE_CONTROL ||
            weapon_runtime.player_weapon_interruptions != 0u ||
            weapon_runtime.player.x != weapon_x ||
            weapon_runtime.player.z != weapon_z)
        {
            fprintf(stderr,
                "Button1 dispatch hold mismatch active=%u tick=%u delay=%u action=%04x substate=%04x entries=%lu attempts=%lu allocations=%lu debits=%lu resource=%u recharge=%u player_state=%u interruptions=%lu position=%d/%d expected=%d/%d\n",
                weapon_runtime.player_weapon_active,
                weapon_runtime.player_weapon_tick,
                weapon_runtime.player_weapon_dispatch_delay,
                weapon_runtime.player.source_action,
                weapon_runtime.player.substate,
                weapon_runtime.player_weapon_entries,
                weapon_runtime.player_weapon_attempts_total,
                weapon_runtime.player_weapon_allocations,
                weapon_runtime.player_weapon_resource_debits,
                weapon_runtime.player_resource,
                weapon_runtime.player_resource_recharge,
                weapon_runtime.player_action.state,
                weapon_runtime.player_weapon_interruptions,
                weapon_runtime.player.x, weapon_runtime.player.z,
                weapon_x, weapon_z);
            return 118;
        }
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 2u ||
            weapon_runtime.player.source_action != 0x0c02u ||
            weapon_runtime.player.substate != 0x0c02u ||
            weapon_runtime.player.animation_record != 0x0015e594UL ||
            weapon_runtime.player.assembly != 0x0016179aUL ||
            weapon_runtime.player.animation_timer != 2u ||
            weapon_runtime.player.animation_branch != 0 ||
            weapon_runtime.player.hurt_selector != 1u ||
            weapon_runtime.player.attack_selector != 0u ||
            weapon_runtime.player_weapon_entries != 1u ||
            weapon_runtime.player_weapon_attempts_total != 0u ||
            weapon_runtime.player_weapon_allocations != 0u ||
            weapon_runtime.player_weapon_resource_debits != 0u ||
            weapon_runtime.player_resource != 64u ||
            weapon_runtime.player_resource_recharge != 12u ||
            weapon_runtime.player_action.state != AVSP_PW_STATE_CONTROL ||
            weapon_runtime.player_weapon_interruptions != 0u ||
            weapon_runtime.player.x != weapon_x ||
            weapon_runtime.player.z != weapon_z)
        {
            fprintf(stderr,
                "Button1 action entry mismatch active=%u tick=%u action=%04x substate=%04x animation=%08lx/%08lx assembly=%08lx/%08lx timer=%u/%u branch=%d/%d selectors=%u/%u:%u/%u entries=%lu attempts=%lu allocations=%lu debits=%lu resource=%u recharge=%u player_state=%u interruptions=%lu position=%d/%d expected=%d/%d\n",
                weapon_runtime.player_weapon_active,
                weapon_runtime.player_weapon_tick,
                weapon_runtime.player.source_action,
                weapon_runtime.player.substate,
                weapon_runtime.player.animation_record,
                0x0015e594UL,
                weapon_runtime.player.assembly,
                0x0016179aUL,
                weapon_runtime.player.animation_timer,
                2u,
                weapon_runtime.player.animation_branch,
                0,
                weapon_runtime.player.hurt_selector,
                1u,
                weapon_runtime.player.attack_selector,
                0u,
                weapon_runtime.player_weapon_entries,
                weapon_runtime.player_weapon_attempts_total,
                weapon_runtime.player_weapon_allocations,
                weapon_runtime.player_weapon_resource_debits,
                weapon_runtime.player_resource,
                weapon_runtime.player_resource_recharge,
                weapon_runtime.player_action.state,
                weapon_runtime.player_weapon_interruptions,
                weapon_runtime.player.x, weapon_runtime.player.z,
                weapon_x, weapon_z);
            return 118;
        }
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x0c02u ||
            weapon_runtime.player.animation_record != 0x0015e594UL ||
            weapon_runtime.player.assembly != 0x0016179aUL ||
            weapon_runtime.player_weapon_presentation_selector != 5u ||
            weapon_runtime.player_weapon_resource_debits != 1u ||
            weapon_runtime.player_resource != 24u ||
            weapon_runtime.player_weapon_attempts_total != 1u ||
            weapon_runtime.player_weapon_allocations != 1u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 27;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime,
                    AVSP_PW_INPUT_RIGHT, 0))
                return 28;
        weapon_x = weapon_runtime.player.x;
        if (weapon_runtime.player_weapon_tick != 20u ||
            weapon_runtime.player_weapon_cleanup_pending != 1u ||
            weapon_runtime.player.source_action != 0u ||
            weapon_runtime.player_weapon_completions != 1u ||
            weapon_runtime.player_weapon_allocations != 1u ||
            weapon_runtime.player_resource != 27u ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player.source_action != 0x0200u ||
            weapon_runtime.player.substate != 0x0200u ||
            weapon_runtime.player.animation_record != 0x0015f208UL ||
            weapon_runtime.player.assembly != 0x00160a02UL ||
            weapon_runtime.player.x <= weapon_x)
        {
            fprintf(stderr,
                "weapon completion tick=%u cleanup=%u action=%04x substate=%04x animation=%08lx assembly=%08lx completions=%lu allocations=%lu resource=%u x=%d prior_x=%d\n",
                weapon_runtime.player_weapon_tick,
                weapon_runtime.player_weapon_cleanup_pending,
                weapon_runtime.player.source_action,
                weapon_runtime.player.substate,
                weapon_runtime.player.animation_record,
                weapon_runtime.player.assembly,
                weapon_runtime.player_weapon_completions,
                weapon_runtime.player_weapon_allocations,
                weapon_runtime.player_resource,
                weapon_runtime.player.x, weapon_x);
            return 29;
        }
        weapon_runtime.player_resource = 10u;
        weapon_runtime.player_resource_recharge = 1u;
        weapon_runtime.player_resource_depleted = 0u;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player_resource != 11u ||
            weapon_runtime.player_resource_recharge != 3u)
            return 185;
        empty_latch_runtime.player_resource = 43u;
        empty_latch_runtime.player_resource_recharge = 5u;
        empty_latch_runtime.player_resource_depleted = 1u;
        if (!enter_ground_button1(&empty_latch_runtime, 0u) ||
            empty_latch_runtime.player_weapon_active != 1u ||
            empty_latch_runtime.player_weapon_empty != 1u ||
            empty_latch_runtime.player.source_action != 0x1a00u ||
            empty_latch_runtime.player_weapon_allocations != 0u ||
            empty_latch_runtime.player_resource != 43u)
            return 186;
        empty_latch_runtime.player_weapon_active = 0u;
        empty_latch_runtime.player_weapon_dispatch_delay = 0u;
        empty_latch_runtime.player_resource = 64u;
        empty_latch_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&empty_latch_runtime, 0u, 0) ||
            empty_latch_runtime.player_resource_depleted != 0u)
            return 187;
        if (!avsp_round1_step_player(&empty_walk_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            !avsp_round1_step_player(&empty_walk_runtime,
                AVSP_PW_INPUT_RIGHT, 0) ||
            !avsp_round1_step_player(&empty_walk_runtime,
                AVSP_PW_INPUT_RIGHT, 0))
            return 222;
        empty_walk_runtime.player_resource = 43u;
        empty_walk_runtime.player_resource_recharge = 5u;
        empty_walk_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&empty_walk_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0))
            return 223;
        {
            unsigned long entry_record;
            unsigned long entry_assembly;
            unsigned short entry_timer;
            short entry_branch;
            if (!avsp_round1_step_player(&empty_walk_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
                empty_walk_runtime.player_weapon_active != 1u ||
                empty_walk_runtime.player_weapon_tick != 1u ||
                empty_walk_runtime.player_weapon_dispatch_delay != 0u ||
                empty_walk_runtime.player.source_action != 0x1a00u)
                return 223;
            entry_record = empty_walk_runtime.player.animation_record;
            entry_assembly = empty_walk_runtime.player.assembly;
            entry_timer = empty_walk_runtime.player.animation_timer;
            entry_branch = empty_walk_runtime.player.animation_branch;
            if (entry_record == 0x0015f1f4UL ||
                empty_walk_runtime.player.source_action != 0x1a00u ||
                empty_walk_runtime.player.substate != 0x1a00u ||
                empty_walk_runtime.player.animation_record != entry_record ||
                empty_walk_runtime.player.assembly != entry_assembly ||
                empty_walk_runtime.player.animation_timer != entry_timer ||
                empty_walk_runtime.player.animation_branch != entry_branch ||
                empty_walk_runtime.player.hurt_selector != 17u ||
                empty_walk_runtime.player.attack_selector != 0u)
            {
                fprintf(stderr,
                    "empty walk entry record=%08lx/%08lx assembly=%08lx/%08lx timer=%u/%u branch=%d/%d action=%04x substate=%04x selectors=%u/%u\n",
                    entry_record, empty_walk_runtime.player.animation_record,
                    entry_assembly, empty_walk_runtime.player.assembly,
                    entry_timer, empty_walk_runtime.player.animation_timer,
                    entry_branch, empty_walk_runtime.player.animation_branch,
                    empty_walk_runtime.player.source_action,
                    empty_walk_runtime.player.substate,
                    empty_walk_runtime.player.hurt_selector,
                    empty_walk_runtime.player.attack_selector);
                return 224;
            }
        }
        if (!avsp_round1_step_player(&empty_walk_runtime, 0u, 0) ||
            empty_walk_runtime.player.source_action != 0x1a02u ||
            empty_walk_runtime.player.animation_record != 0x0015fcfcUL ||
            empty_walk_runtime.player.assembly != 0x00161772UL ||
            empty_walk_runtime.player.hurt_selector != 1u ||
            empty_walk_runtime.player.attack_selector != 0u)
            return 225;
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
            weapon_runtime.player_weapon_projectiles[0].angle < 17u ||
            weapon_runtime.player_weapon_projectiles[0].angle > 47u ||
            weapon_runtime.player_weapon_projectiles[0].x_fp !=
                (long)weapon_runtime.player_weapon_projectiles[0].x * 65536L)
            return 32;
        weapon_runtime.player_resource = 24u;
        weapon_runtime.player_resource_depleted = 1u;
        if (!enter_ground_button1(&weapon_runtime, 0u) ||
            weapon_runtime.player.source_action != 0x1a00u ||
            weapon_runtime.player_weapon_empty != 1u ||
            weapon_runtime.player_weapon_empty_auxiliary_requests != 0u ||
            weapon_runtime.player_weapon_allocations != 1u)
            return 33;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x1a02u ||
            weapon_runtime.player.animation_record != 0x0015fcfcUL ||
            weapon_runtime.player.assembly != 0x00161772UL ||
            weapon_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            weapon_runtime.player_weapon_empty_auxiliary_allocations != 1u)
            return 34;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 35;
        if (weapon_runtime.player_weapon_completions != 2u ||
            weapon_runtime.player.source_action != 0u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x0202u)
            return 36;
        weapon_runtime.player_resource = 64u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 0u;
        weapon_runtime.player_weapon_projectile_free_count = 0u;
        weapon_runtime.player_weapon_allocations =
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
        if (!enter_ground_button1(&weapon_runtime, 0u) ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player_weapon_empty != 0u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
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
        effect = &effect_runtime.pools[3].records[29];
        effect->z = 319;
        effect_runtime.player_resource = 0u;
        effect_runtime.player_resource_depleted = 1u;
        if (!enter_ground_button1(&effect_runtime, 0u) ||
            effect_runtime.player_weapon_empty_auxiliary_requests != 0u ||
            effect_runtime.player_weapon_empty_auxiliary_allocations != 0u ||
            effect_runtime.pools[3].free_count != 30u ||
            !avsp_round1_step_player(&effect_runtime, 0u, 0) ||
            effect_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            effect_runtime.player_weapon_empty_auxiliary_allocations != 1u ||
            effect_runtime.pools[3].free_count != 29u)
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
        if (!avsp_round1_step_scheduler(&effect_runtime) ||
            effect->state != 2u || effect->variant != 0u ||
            effect->x != effect_runtime.player.x ||
            effect->y != effect_runtime.player.y + 84 ||
            effect->z != 319 ||
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
        if (effect->y != effect_runtime.player.y + 116 ||
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
            effect_runtime.pools[3].free_count != 30u ||
            effect_runtime.player_weapon_empty_auxiliary_releases != 1u)
            return 48;
    }
    {
        AvspRound1Runtime projectile_runtime;
        AvspRound1ActorCore *target;
        AvspRound1ActorCore *impact;
        AvspRound1WeaponProjectileAllocation *projectile;
        AvspRound1WeaponProjectileAllocation *child;
        unsigned int entry_calls = 0u;
        unsigned int impact_index;
        unsigned int free_stack_index;
        unsigned short impact_source_slot;
        unsigned long expected_impact_animation = 0x0008df2cUL;
        unsigned long expected_impact_assembly = 0x0008df96UL;
        unsigned short expected_impact_timer = 4045u;
        short expected_impact_branch = -32768;
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
        target->state = 0x0200u;
        target->x = (short)(projectile_runtime.player.x - 343);
        target->y = projectile_runtime.player.y;
        target->z = (short)(projectile_runtime.player.z - 16);
        projectile_runtime.player_weapon_projectiles[0].x_fp = 0x00000a00L;
        projectile_runtime.player_weapon_projectiles[0].y_fp = 0x0000b800L;
        if (!enter_ground_button1(&projectile_runtime, 0u) ||
            !avsp_round1_step_player(&projectile_runtime, 0u, 0) ||
            !avsp_round1_step_player(&projectile_runtime, 0u, 0))
            return 51;
        projectile = &projectile_runtime.player_weapon_projectiles[0];
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->state != 2u || projectile->collision_result != 0 ||
            projectile->actor_class != 0 ||
            projectile->angle != 46u ||
            projectile->collision_identity != 0x26u ||
            projectile->attack_selector != 1u || target->health != -1 ||
            projectile->x != (short)(projectile_runtime.player.x +
                (projectile->facing ? -5 : 5)) ||
            projectile->y != (short)(projectile_runtime.player.y + 86) ||
            (unsigned short)projectile->x_fp != 0x0a00u ||
            (unsigned short)projectile->y_fp != 0xb800u ||
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
        {
            AvspRound1Runtime camera_bound_runtime = projectile_runtime;
            AvspRound1WeaponProjectileAllocation *camera_bound_parent =
                &camera_bound_runtime.player_weapon_projectiles[0];
            AvspRound1ActorCore *camera_bound_target =
                &camera_bound_runtime.pools[0].records[12];
            camera_bound_runtime.camera_x_position = 0;
            camera_bound_runtime.navigation_bound_x = 832;
            camera_bound_runtime.camera_z_position = camera_bound_parent->y;
            camera_bound_parent->x = 936;
            camera_bound_parent->x_fp = (long)camera_bound_parent->x * 65536L +
                (unsigned short)camera_bound_parent->x_fp;
            camera_bound_target->health = -1;
            camera_bound_target->hurt_selector = 0u;
            if (!avsp_round1_step_scheduler(&camera_bound_runtime) ||
                camera_bound_parent->state != 4u ||
                camera_bound_parent->child_cadence != 1u)
            {
                fprintf(stderr,
                    "camera-bound parent state=%u cadence=%u camera=%d navigation=%d x=%d\n",
                    camera_bound_parent->state,
                    camera_bound_parent->child_cadence,
                    camera_bound_runtime.camera_x_position,
                    camera_bound_runtime.navigation_bound_x,
                    camera_bound_parent->x);
                return 52;
            }
        }
        target->hurt_selector = 1u;
        target->health = 63;
        target->x = projectile->x;
        target->y = (short)(projectile->y - 8);
        target->z = projectile->z;
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->collision_result != -1 || target->health != -1 ||
            target->state != 0x0400u || target->substate != 0x0000u ||
            target->source_action_timer != 8u ||
            target->source_projectile_reaction_pending != 2u ||
            projectile_runtime.player_weapon_projectile_collision_writes != 1u ||
            projectile_runtime.player_weapon_projectile_damage_writes != 1u ||
            projectile_runtime.first_encounter.ko_events != 1u)
        {
            fprintf(stderr, "parent delayed collision p=%d/%d/%d target=%d/%d/%d health=%d target-state=%04x/%04x timer=%u result=%d projectile-state=%u counts=%lu/%lu ko=%lu code=%u failures=%lu registered=%u pending=%u target-visible=%u target-hurt=%u target-record=%08lx current=%u/%04x/%d/%d/%d/%d\n",
                projectile->x, projectile->y, projectile->z,
                target->x, target->y, target->z, target->health,
                target->state, target->substate, target->source_action_timer,
                projectile->collision_result, projectile->state,
                projectile_runtime.player_weapon_projectile_collision_writes,
                projectile_runtime.player_weapon_projectile_damage_writes,
                projectile_runtime.first_encounter.ko_events,
                projectile_runtime.scheduler_failure_code,
                projectile_runtime.failure_count,
                projectile->collision_registered,
                projectile->collision_registration_pending,
                target->source_field01, target->hurt_selector,
                target->animation_record,
                target->source_collision_current_active,
                target->source_collision_current_state,
                target->source_collision_current_x,
                target->source_collision_current_y,
                target->source_collision_current_z,
                target->source_collision_current_health);
            return 52;
        }
        impact = 0;
        for (impact_index = 0u;
             impact_index < projectile_runtime.pools[3].capacity;
             ++impact_index)
            if (projectile_runtime.pools[3].records[impact_index].active &&
                projectile_runtime.pools[3].records[impact_index].actor_class ==
                    0x4e &&
                projectile_runtime.pools[3].records[impact_index].variant ==
                    10u)
                impact = &projectile_runtime.pools[3].records[impact_index];
        if (!avsp_round1_is_weapon_impact_actor(impact) ||
            impact->variant != 10u || impact->state != 0u ||
            projectile_runtime.class4e_variant10_allocation_requests != 1u ||
            projectile_runtime.class4e_variant10_allocations != 1u ||
            projectile_runtime.class4e_variant10_allocation_failures != 0u)
            return 52;
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            projectile->state != 4u || target->state != 0x0402u ||
            target->substate != 0x0000u ||
            target->source_action_timer != 8u ||
            target->source_hit_recovery_active != 2u ||
            target->source_reaction_selector != 0x36u ||
            target->source_hit_mode != 0u ||
            target->source_hit_kind != 0x15u || target->active != 2u ||
            target->source_projectile_reaction_pending != 0u ||
            projectile_runtime.first_encounter.ko_events != 1u ||
            !avsp_round1_step_scheduler(&projectile_runtime))
            return 53;
        target->active = 1u;
        target->state = 0x0200u;
        target->substate = 0u;
        target->source_action = 0u;
        target->source_action_timer = 0u;
        target->source_hit_recovery_active = 0u;
        target->source_hit_mode = 0u;
        target->source_hit_kind = 0u;
        target->source_reaction_selector = 0u;
        child = &projectile_runtime.player_weapon_projectiles[1];
        if (!child->active || child->actor_class != 4 || child->variant != 1u ||
            child->collision_identity != 0x27u ||
            child->attack_table != 0x00030cb6UL || child->state != 2u ||
            child->animation_record != 0x000308a0UL ||
            child->assembly != 0x00030b36UL)
            return 54;
        {
            AvspRound1Runtime registration_runtime = projectile_runtime;
            AvspRound1WeaponProjectileAllocation *registration_child =
                &registration_runtime.player_weapon_projectiles[1];
            AvspRound1ActorCore *registration_target =
                &registration_runtime.pools[0].records[12];
            registration_runtime.camera_x_position = 1000;
            registration_runtime.camera_z_position = 320;
            registration_child->x = 936;
            registration_child->y = 310;
            registration_child->z = 320;
            registration_target->health = 63;
            registration_target->state = 0x0200u;
            registration_target->substate = 0u;
            registration_target->source_action = 0u;
            registration_target->source_action_timer = 0u;
            registration_target->hurt_selector = 1u;
            registration_target->x = 936;
            registration_target->y = 320;
            registration_target->z = 320;
            if (!avsp_round1_step_scheduler(&registration_runtime) ||
                registration_child->collision_registered != 1u ||
                registration_target->source_field01 != 1u ||
                registration_target->health != 32 ||
                registration_runtime.player_weapon_projectile_damage_writes !=
                    projectile_runtime.player_weapon_projectile_damage_writes +
                    1u)
                return 54;
        }
        {
            AvspRound1Runtime offscreen_runtime = projectile_runtime;
            AvspRound1WeaponProjectileAllocation *offscreen_child =
                &offscreen_runtime.player_weapon_projectiles[1];
            AvspRound1ActorCore *offscreen_target =
                &offscreen_runtime.pools[0].records[12];
            offscreen_runtime.camera_x_position = 0;
            offscreen_runtime.camera_z_position = offscreen_target->y;
            offscreen_target->health = 63;
            offscreen_target->state = 0x0200u;
            offscreen_target->substate = 0u;
            offscreen_target->source_action = 0u;
            offscreen_target->source_action_timer = 0u;
            offscreen_target->hurt_selector = 1u;
            offscreen_target->x = offscreen_child->x;
            offscreen_target->y = (short)(offscreen_child->y + 10);
            offscreen_target->z = offscreen_child->z;
            if (!avsp_round1_step_scheduler(&offscreen_runtime) ||
                offscreen_child->collision_registered != 0u ||
                offscreen_target->source_field01 != 0u ||
                offscreen_target->health != 63 ||
                offscreen_runtime.player_weapon_projectile_damage_writes !=
                    projectile_runtime.player_weapon_projectile_damage_writes)
                return 54;
        }
        {
            AvspRound1Runtime attacker_registration_runtime =
                projectile_runtime;
            AvspRound1WeaponProjectileAllocation *unregistered_child =
                &attacker_registration_runtime.player_weapon_projectiles[1];
            AvspRound1ActorCore *registered_target =
                &attacker_registration_runtime.pools[0].records[12];
            attacker_registration_runtime.camera_x_position = 1000;
            attacker_registration_runtime.camera_z_position = 320;
            unregistered_child->x = 935;
            unregistered_child->y = 310;
            unregistered_child->z = 320;
            registered_target->health = 63;
            registered_target->state = 0x0200u;
            registered_target->substate = 0u;
            registered_target->source_action = 0u;
            registered_target->source_action_timer = 0u;
            registered_target->hurt_selector = 1u;
            registered_target->x = 936;
            registered_target->y = 320;
            registered_target->z = 320;
            if (!avsp_round1_step_scheduler(&attacker_registration_runtime) ||
                unregistered_child->collision_registered != 0u ||
                registered_target->source_field01 != 1u ||
                registered_target->health != 63 ||
                attacker_registration_runtime.
                    player_weapon_projectile_damage_writes !=
                    projectile_runtime.player_weapon_projectile_damage_writes)
                return 54;
        }
        {
            AvspRound1Runtime defender_registration_runtime =
                projectile_runtime;
            AvspRound1WeaponProjectileAllocation *registered_child =
                &defender_registration_runtime.player_weapon_projectiles[1];
            AvspRound1ActorCore *unregistered_target =
                &defender_registration_runtime.pools[0].records[12];
            defender_registration_runtime.camera_x_position = 1000;
            defender_registration_runtime.camera_z_position = 320;
            registered_child->x = 936;
            registered_child->y = 310;
            registered_child->z = 320;
            unregistered_target->health = 63;
            unregistered_target->state = 0x0200u;
            unregistered_target->substate = 0u;
            unregistered_target->source_action = 0u;
            unregistered_target->source_action_timer = 0u;
            unregistered_target->hurt_selector = 1u;
            unregistered_target->x = 935;
            unregistered_target->y = 320;
            unregistered_target->z = 320;
            if (!avsp_round1_step_scheduler(&defender_registration_runtime) ||
                registered_child->collision_registered != 1u ||
                unregistered_target->source_field01 != 0u ||
                unregistered_target->health != 63 ||
                defender_registration_runtime.
                    player_weapon_projectile_damage_writes !=
                    projectile_runtime.player_weapon_projectile_damage_writes)
                return 54;
        }
        {
            AvspRound1Runtime latch_runtime = projectile_runtime;
            AvspRound1WeaponProjectileAllocation *latch_child =
                &latch_runtime.player_weapon_projectiles[1];
            AvspRound1ActorCore *latch_target =
                &latch_runtime.pools[0].records[12];
            latch_runtime.camera_x_position = latch_child->x;
            latch_runtime.camera_z_position = latch_child->y;
            latch_target->health = 63;
            latch_target->state = 0x0200u;
            latch_target->substate = 0u;
            latch_target->source_action = 0u;
            latch_target->source_action_timer = 0u;
            latch_target->hurt_selector = 1u;
            latch_target->x = latch_child->x;
            latch_target->y = (short)(latch_child->y + 10);
            latch_target->z = latch_child->z;
            latch_target->source_collision_latches[0] =
                latch_child->collision_identity;
            if (!avsp_round1_step_scheduler(&latch_runtime) ||
                latch_target->health != 63 ||
                latch_runtime.player_weapon_projectile_damage_writes !=
                    projectile_runtime.player_weapon_projectile_damage_writes)
                return 54;
        }
        target->health = 63;
        target->state = 0x0200u;
        target->substate = 0u;
        target->source_action = 0u;
        target->source_action_timer = 0u;
        target->hurt_selector = 1u;
        target->animation_record = 0x0012eb5cUL;
        target->assembly = 0x0012f762UL;
        target->x = child->x;
        target->y = (short)(child->y + 10);
        target->z = child->z;
        projectile->active_collision = 0u;
        if (projectile_runtime.pools[3].free_count == 0u)
            return 55;
        for (free_stack_index = 0u;
             free_stack_index < projectile_runtime.pools[3].free_count;
             ++free_stack_index)
        {
            impact_source_slot = projectile_runtime.pools[3].free_stack[
                free_stack_index];
            if (impact_source_slot < projectile_runtime.pools[3].source_base ||
                ((unsigned int)impact_source_slot -
                    projectile_runtime.pools[3].source_base) %
                    projectile_runtime.pools[3].stride != 0u)
                return 55;
            impact_index = ((unsigned int)impact_source_slot -
                projectile_runtime.pools[3].source_base) /
                projectile_runtime.pools[3].stride;
            if (impact_index >= projectile_runtime.pools[3].capacity)
                return 55;
            projectile_runtime.pools[3].records[impact_index]
                .animation_record = 0x0008df2cUL;
            projectile_runtime.pools[3].records[impact_index].assembly =
                0x0008df96UL;
            projectile_runtime.pools[3].records[impact_index]
                .animation_timer = 4045u;
            projectile_runtime.pools[3].records[impact_index]
                .animation_branch = -32768;
        }
        for (free_stack_index = 0u;
             free_stack_index < projectile_runtime.pools[3].capacity;
             ++free_stack_index)
        {
            AvspRound1ActorCore *releasing =
                &projectile_runtime.pools[3].records[free_stack_index];
            if (releasing->active && releasing->actor_class == 0x49 &&
                releasing->effect_timer == 1u)
            {
                expected_impact_animation = releasing->animation_record;
                expected_impact_assembly = releasing->assembly;
                expected_impact_timer = releasing->animation_timer;
                expected_impact_branch = releasing->animation_branch;
            }
        }
        if (!avsp_round1_step_scheduler(&projectile_runtime) ||
            target->health != 32 || target->state != 0x0202u ||
            target->substate != 0x0000u ||
            target->source_action_timer != 8u ||
            target->source_projectile_reaction_pending != 1u ||
            target->source_hit_kind != 0x15u ||
            target->source_prior_health != 63 ||
            child->collision_result != -1 ||
            target->source_collision_latches[0] !=
                child->collision_identity ||
            projectile_runtime.player_weapon_projectile_damage_writes != 2u ||
            projectile_runtime.first_encounter.hit_events != 1u)
        {
            fprintf(stderr,
                    "child collision failed code=%u slot=%04x health=%d state=%04x/%04x timer=%u result=%d writes=%lu hits=%lu impact=%lu/%lu failures=%lu\n",
                    projectile_runtime.scheduler_failure_code,
                    projectile_runtime.scheduler_failure_source_slot,
                    target->health, target->state, target->substate,
                    target->source_action_timer,
                    child->collision_result,
                    projectile_runtime.player_weapon_projectile_damage_writes,
                    projectile_runtime.first_encounter.hit_events,
                    projectile_runtime.class4e_variant1_allocation_requests,
                    projectile_runtime.class4e_variant1_allocations,
                    projectile_runtime.failure_count);
            return 55;
        }
        {
            AvspRound1Runtime late_registration_runtime = projectile_runtime;
            AvspRound1WeaponProjectileAllocation *late_parent =
                &late_registration_runtime.player_weapon_projectiles[5];
            AvspRound1WeaponProjectileAllocation *late_child =
                &late_registration_runtime.player_weapon_projectiles[0];
            AvspRound1ActorCore *late_target =
                &late_registration_runtime.pools[0].records[12];
            unsigned int pool_index;
            unsigned int projectile_index;
            for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT;
                 ++pool_index)
            {
                unsigned int actor_index;
                for (actor_index = 0u;
                     actor_index <
                        late_registration_runtime.pools[pool_index].capacity;
                     ++actor_index)
                    if (pool_index != 0u || actor_index != 12u)
                        late_registration_runtime.pools[pool_index].records[
                            actor_index].active = 0u;
            }
            for (projectile_index = 0u;
                 projectile_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
                 ++projectile_index)
                late_registration_runtime.player_weapon_projectiles[
                    projectile_index].active = 0u;
            late_registration_runtime.player_weapon_projectile_free_count = 1u;
            late_registration_runtime.player_weapon_projectile_free_stack[0] =
                0u;
            late_parent->active = 1u;
            late_parent->actor_class = 0;
            late_parent->source_slot = 0x8900u;
            late_parent->state = 4u;
            late_parent->substate = 2u;
            late_parent->child_count = 1u;
            late_parent->child_cadence = 1u;
            late_parent->collision_result = -1;
            late_parent->facing = 0u;
            late_parent->x = 936;
            late_parent->y = 310;
            late_parent->z = 320;
            late_parent->active_collision = 0u;
            late_parent->attack_selector = 0u;
            late_target->active = 1u;
            late_target->state = 0x0200u;
            late_target->substate = 0u;
            late_target->source_action = 0u;
            late_target->source_action_timer = 0u;
            late_target->source_hit_recovery_active = 0u;
            late_target->source_projectile_reaction_pending = 0u;
            late_target->source_a3 = 0u;
            late_target->source_a4 = 1u;
            late_target->source_a5 = 1u;
            late_target->source_a6 = 1u;
            late_target->source_style85 = 0u;
            late_target->source_b0 = 2u;
            late_target->facing = 1u;
            late_target->health = 63;
            late_target->x = 936;
            late_target->y = 320;
            late_target->z = 320;
            late_registration_runtime.camera_x_position = 1000;
            late_registration_runtime.camera_z_position = 320;
            if (!avsp_round1_step_scheduler(&late_registration_runtime) ||
                !late_child->active || late_child->state != 0u ||
                late_child->collision_registration_pending != 1u ||
                late_child->collision_registered != 0u)
                return 81;
            late_child->x = 936;
            late_child->y = 310;
            late_child->z = 320;
            late_child->x_fp = 936L * 65536L;
            late_child->y_fp = 310L * 65536L;
            late_child->z_fp = 320L * 65536L;
            late_target->x = 936;
            late_target->y = 320;
            late_target->z = 320;
            late_target->health = 63;
            if (!avsp_round1_step_scheduler(&late_registration_runtime) ||
                late_child->state != 2u ||
                late_child->collision_registration_pending != 0u ||
                late_child->collision_registered != 0u ||
                late_target->health != 63)
                return 81;
            late_child->x = 936;
            late_child->y = 310;
            late_child->z = 320;
            late_child->x_fp = 936L * 65536L;
            late_child->y_fp = 310L * 65536L;
            late_child->z_fp = 320L * 65536L;
            late_target->state = 0x0200u;
            late_target->substate = 0u;
            late_target->source_action = 0u;
            late_target->source_action_timer = 0u;
            late_target->source_hit_recovery_active = 0u;
            late_target->source_projectile_reaction_pending = 0u;
            late_target->health = 63;
            late_target->x = 936;
            late_target->y = 320;
            late_target->z = 320;
            if (!avsp_round1_step_scheduler(&late_registration_runtime) ||
                late_child->collision_registered != 1u ||
                late_child->collision_result != -1 ||
                late_target->health != 32)
                return 81;
        }
        {
            AvspRound1Runtime action16_rng_runtime = projectile_runtime;
            AvspRound1ActorCore *action16_actor =
                &action16_rng_runtime.pools[0].records[18];
            unsigned int pool_index;
            unsigned int projectile_index;
            for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT;
                 ++pool_index)
            {
                unsigned int actor_index;
                for (actor_index = 0u;
                     actor_index < action16_rng_runtime.pools[pool_index].capacity;
                     ++actor_index)
                    if (pool_index != 0u || actor_index != 18u)
                        action16_rng_runtime.pools[pool_index].records[
                            actor_index].active = 0u;
            }
            for (projectile_index = 0u;
                 projectile_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
                 ++projectile_index)
                action16_rng_runtime.player_weapon_projectiles[
                    projectile_index].active = 0u;
            action16_rng_runtime.rng_seed = 0xc9a2u;
            action16_rng_runtime.player_action.x = 944;
            action16_rng_runtime.player_action.lane = 320;
            action16_actor->active = 1u;
            action16_actor->type = 12u;
            action16_actor->actor_class = 0x1f;
            action16_actor->state = 0x0200u;
            action16_actor->substate = 0x1600u;
            action16_actor->source_action = 0x1600u;
            action16_actor->x = 1001;
            action16_actor->y = 296;
            action16_actor->z = 296;
            action16_actor->source_x_fp = 0x03e90000L;
            action16_actor->source_y_fp = 0x01280000L;
            action16_actor->source_z_fp = 0x01280000L;
            action16_actor->facing = 1u;
            action16_actor->source_facing_selector = 1u;
            action16_actor->source_a3 = 1u;
            action16_actor->source_a4 = 1u;
            action16_actor->source_a5 = 1u;
            action16_actor->source_a6 = 1u;
            action16_actor->source_style85 = 1u;
            action16_actor->source_b0 = 1u;
            action16_actor->source_direction = 8u;
            action16_actor->source_motion_flags = 0u;
            action16_actor->animation_record = 0x0012ec74UL;
            action16_actor->assembly = 0x0012f8b8UL;
            action16_actor->animation_timer = 2u;
            action16_actor->animation_branch = -32760;
            action16_actor->source_next_animation_record = 0x0012ec74UL;
            action16_actor->source_movement_table = 8u;
            if (!avsp_round1_step_scheduler(&action16_rng_runtime) ||
                action16_rng_runtime.rng_seed != 0x5cfeu ||
                action16_actor->state != 0x0200u ||
                action16_actor->substate != 0u ||
                action16_actor->source_a4 != 0u ||
                action16_actor->source_a6 != 2u ||
                action16_actor->attack_selector != 0u ||
                action16_actor->animation_record != 0x0012ec74UL ||
                !avsp_round1_step_scheduler(&action16_rng_runtime) ||
                action16_actor->substate != 0x1600u ||
                action16_actor->animation_record != 0x0012e78cUL ||
                action16_actor->attack_selector != 0u)
            {
                fprintf(stderr,
                    "action16 RNG reuse code=%u rng=%04x state=%04x/%04x a4=%u a6=%u attack=%u anim=%08lx failures=%lu\n",
                    action16_rng_runtime.scheduler_failure_code,
                    action16_rng_runtime.rng_seed,
                    action16_actor->state, action16_actor->substate,
                    action16_actor->source_a4, action16_actor->source_a6,
                    action16_actor->attack_selector,
                    action16_actor->animation_record,
                    action16_rng_runtime.failure_count);
                return 80;
            }
            {
                AvspRound1Runtime latched_retry_runtime =
                    action16_rng_runtime;
                AvspRound1ActorCore *latched_retry_actor =
                    &latched_retry_runtime.pools[0].records[18];
                latched_retry_runtime.rng_seed = 0x4bdfu;
                latched_retry_actor->state = 0x0200u;
                latched_retry_actor->substate = 0x1600u;
                latched_retry_actor->source_action = 0x1600u;
                latched_retry_actor->x = 1121;
                latched_retry_actor->source_x_fp = 0x04610000L;
                latched_retry_actor->facing = 1u;
                latched_retry_actor->source_a5 = 1u;
                latched_retry_actor->source_a6 = 2u;
                latched_retry_actor->source_style85 = 1u;
                latched_retry_actor->source_b0 = 1u;
                latched_retry_actor->source_motion_flags = 1u;
                latched_retry_actor->source_transition_latch_ae = 1u;
                latched_retry_actor->animation_record = 0x0012e7fcUL;
                latched_retry_actor->assembly = 0x0012f8b8UL;
                latched_retry_actor->animation_timer = 2u;
                latched_retry_actor->animation_branch = -32760;
                latched_retry_actor->source_next_animation_record =
                    0x0012e7fcUL;
                latched_retry_actor->source_movement_table = 8u;
                if (!avsp_round1_step_scheduler(&latched_retry_runtime) ||
                    latched_retry_runtime.rng_seed != 0xe3c2u ||
                    latched_retry_actor->state != 0x0200u ||
                    latched_retry_actor->substate != 0x1a00u ||
                    latched_retry_actor->source_action != 0x1a00u ||
                    latched_retry_actor->source_action_timer != 30u ||
                    latched_retry_actor->facing != 0u ||
                    latched_retry_actor->source_a6 != 2u ||
                    latched_retry_actor->source_motion_flags != 1u ||
                    latched_retry_actor->source_transition_latch_ae != 1u ||
                    latched_retry_actor->animation_record != 0x0012d5e4UL ||
                    latched_retry_actor->attack_selector != 0u)
                {
                    fprintf(stderr,
                        "action16 latched retry code=%u rng=%04x state=%04x/%04x timer=%u facing=%u a6=%u motion=%u latch=%u attack=%u anim=%08lx failures=%lu\n",
                        latched_retry_runtime.scheduler_failure_code,
                        latched_retry_runtime.rng_seed,
                        latched_retry_actor->state,
                        latched_retry_actor->substate,
                        latched_retry_actor->source_action_timer,
                        latched_retry_actor->facing,
                        latched_retry_actor->source_a6,
                        latched_retry_actor->source_motion_flags,
                        latched_retry_actor->source_transition_latch_ae,
                        latched_retry_actor->attack_selector,
                        latched_retry_actor->animation_record,
                        latched_retry_runtime.failure_count);
                    return 80;
                }
                for (entry_calls = 0u; entry_calls < 13u; ++entry_calls)
                    if (!avsp_round1_step_scheduler(
                            &latched_retry_runtime))
                        return 80;
                if (latched_retry_actor->state != 0x0200u ||
                    latched_retry_actor->substate != 0x1800u ||
                    latched_retry_actor->source_action != 0x1800u ||
                    latched_retry_actor->source_action_timer != 30u ||
                    latched_retry_actor->facing != 0u ||
                    latched_retry_actor->animation_record !=
                        0x0012e8ecUL ||
                    !avsp_round1_step_scheduler(&latched_retry_runtime) ||
                    latched_retry_actor->substate != 0x1800u ||
                    latched_retry_actor->source_action_timer != 29u)
                    return 80;
            }
        }
        {
            AvspRound1Runtime source_hit_runtime = projectile_runtime;
            AvspRound1ActorCore *source_hit_target =
                &source_hit_runtime.pools[0].records[12];
            unsigned int pool_index;
            unsigned int projectile_index;
            for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT;
                 ++pool_index)
            {
                unsigned int actor_index;
                for (actor_index = 0u;
                     actor_index < source_hit_runtime.pools[pool_index].capacity;
                     ++actor_index)
                    if (pool_index != 0u || actor_index != 12u)
                        source_hit_runtime.pools[pool_index].records[
                            actor_index].active = 0u;
            }
            for (projectile_index = 0u;
                 projectile_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
                 ++projectile_index)
                source_hit_runtime.player_weapon_projectiles[
                    projectile_index].active = 0u;
            source_hit_runtime.rng_seed = 0xedd9u;
            source_hit_runtime.source_global_hit_pause = 0u;
            source_hit_target->x = 684;
            source_hit_target->y = 310;
            source_hit_target->z = 310;
            source_hit_target->source_x_fp = 0x02ac4c00L;
            source_hit_target->source_y_fp = 0x0136d600L;
            source_hit_target->source_z_fp = 0x01360000L;
            source_hit_target->source_facing_selector = 0u;
            source_hit_target->source_collision_guard6d = 0u;
            /* Accepted source frame 2306 context preserved through 0x01efec. */
            source_hit_target->source_style85 = 0u;
            source_hit_target->source_a3 = 0u;
            source_hit_target->source_a4 = 1u;
            source_hit_target->source_a5 = 1u;
            source_hit_target->source_a6 = 1u;
            source_hit_target->source_b0 = 2u;
            source_hit_target->facing = 1u;
            if (!avsp_round1_step_scheduler(&source_hit_runtime) ||
                source_hit_target->state != 0x0202u ||
                source_hit_target->substate != 0x0002u ||
                source_hit_target->source_action_timer != 8u ||
                source_hit_target->source_hit_recovery_active != 1u ||
                source_hit_target->source_hit_mode != 2u ||
                source_hit_target->source_hit_kind != 0x15u ||
                source_hit_target->source_reaction_selector != 0x36u ||
                source_hit_target->source_hit_action_timer != 4u ||
                source_hit_target->source_prior_health != 32 ||
                source_hit_target->animation_record != 0x0012e04cUL ||
                source_hit_target->assembly != 0x001308a6UL ||
                source_hit_target->animation_timer != 1u ||
                source_hit_target->animation_branch != 0 ||
                source_hit_target->hurt_selector != 0u ||
                source_hit_target->attack_selector != 0u)
            {
                fprintf(stderr,
                    "source HIT entry code=%u state=%04x/%04x timer=%u active=%u mode=%u kind=%u selector=%u action-timer=%u prior=%d anim=%08lx assembly=%08lx anim-timer=%u branch=%d selectors=%u/%u\n",
                    source_hit_runtime.scheduler_failure_code,
                    source_hit_target->state, source_hit_target->substate,
                    source_hit_target->source_action_timer,
                    source_hit_target->source_hit_recovery_active,
                    source_hit_target->source_hit_mode,
                    source_hit_target->source_hit_kind,
                    source_hit_target->source_reaction_selector,
                    source_hit_target->source_hit_action_timer,
                    source_hit_target->source_prior_health,
                    source_hit_target->animation_record,
                    source_hit_target->assembly,
                    source_hit_target->animation_timer,
                    source_hit_target->animation_branch,
                    source_hit_target->hurt_selector,
                    source_hit_target->attack_selector);
                return 56;
            }
            for (entry_calls = 0u; entry_calls < 8u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_hit_runtime))
                    return 56;
            if (source_hit_target->source_action_timer != 0u ||
                source_hit_target->substate != 0x0002u ||
                !source_hit_target->source_hit_recovery_active ||
                !avsp_round1_step_scheduler(&source_hit_runtime) ||
                source_hit_target->substate != 0x0200u ||
                source_hit_target->source_x_fp != 0x02ac4c00L ||
                source_hit_target->source_y_fp != 0x0136d600L ||
                source_hit_target->animation_record != 0x0012e04cUL ||
                !avsp_round1_step_scheduler(&source_hit_runtime) ||
                source_hit_target->substate != 0x0202u ||
                source_hit_target->source_x_fp != 0x02aa8c00L ||
                source_hit_target->source_y_fp != 0x01425600L ||
                source_hit_target->source_x_velocity != -0x0001c000L ||
                source_hit_target->source_y_velocity != 0x000b0000L ||
                source_hit_target->animation_record != 0x0012e05cUL)
            {
                fprintf(stderr,
                    "source HIT launch code=%u state=%04x/%04x timer=%u active=%u action=%04x fp=%08lx/%08lx velocity=%08lx/%08lx anim=%08lx\n",
                    source_hit_runtime.scheduler_failure_code,
                    source_hit_target->state, source_hit_target->substate,
                    source_hit_target->source_action_timer,
                    source_hit_target->source_hit_recovery_active,
                    source_hit_target->source_action,
                    source_hit_target->source_x_fp,
                    source_hit_target->source_y_fp,
                    source_hit_target->source_x_velocity,
                    source_hit_target->source_y_velocity,
                    source_hit_target->animation_record);
                return 56;
            }
            for (entry_calls = 0u; entry_calls < 46u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_hit_runtime))
                    return 56;
            if (source_hit_target->substate != 0x0204u ||
                source_hit_target->source_x_fp != 0x025a0c00L ||
                source_hit_target->source_y_fp != 0x0136d600L ||
                source_hit_target->source_hit_action_timer != 3u ||
                source_hit_target->animation_record != 0x0012ddb0UL)
            {
                fprintf(stderr,
                    "source HIT first landing code=%u state=%04x/%04x action-timer=%u fp=%08lx/%08lx anim=%08lx\n",
                    source_hit_runtime.scheduler_failure_code,
                    source_hit_target->state, source_hit_target->substate,
                    source_hit_target->source_hit_action_timer,
                    source_hit_target->source_x_fp,
                    source_hit_target->source_y_fp,
                    source_hit_target->animation_record);
                return 56;
            }
            for (entry_calls = 0u; entry_calls < 3u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_hit_runtime))
                    return 56;
            if (source_hit_target->substate != 0x0206u ||
                source_hit_target->source_x_fp != 0x02580c00L ||
                source_hit_target->source_y_fp != 0x013ad600L ||
                source_hit_target->source_x_velocity != -0x0001f000L ||
                source_hit_target->source_y_velocity != 0x00034000L ||
                source_hit_target->animation_record != 0x0012dd9cUL)
                return 56;
            for (entry_calls = 0u; entry_calls < 11u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_hit_runtime))
                    return 56;
            if (source_hit_target->substate != 0x0208u ||
                source_hit_target->source_x_fp != 0x02462c00L ||
                source_hit_target->source_y_fp != 0x01365600L ||
                source_hit_target->source_hit_action_timer != 10u ||
                source_hit_target->animation_record != 0x0012ddb0UL ||
                source_hit_runtime.rng_seed != 0xc9a2u)
            {
                fprintf(stderr,
                    "source HIT RNG landing code=%u state=%04x/%04x action-timer=%u fp=%08lx/%08lx anim=%08lx rng=%04x\n",
                    source_hit_runtime.scheduler_failure_code,
                    source_hit_target->state, source_hit_target->substate,
                    source_hit_target->source_hit_action_timer,
                    source_hit_target->source_x_fp,
                    source_hit_target->source_y_fp,
                    source_hit_target->animation_record,
                    source_hit_runtime.rng_seed);
                return 56;
            }
            for (entry_calls = 0u; entry_calls < 10u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_hit_runtime))
                    return 56;
            if (source_hit_target->substate != 0x020au ||
                source_hit_target->animation_record != 0x0012de38UL ||
                source_hit_target->animation_timer != 3u)
                return 56;
            for (entry_calls = 0u; entry_calls < 24u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_hit_runtime))
                    return 56;
            if (source_hit_target->state != 0x0202u ||
                source_hit_target->substate != 0x020au ||
                !source_hit_target->source_hit_recovery_active ||
                source_hit_target->animation_record != 0x0012ded8UL ||
                source_hit_target->animation_timer != 8u)
            {
                fprintf(stderr,
                    "source HIT terminal code=%u state=%04x/%04x active=%u anim=%08lx index=%u timer=%u\n",
                    source_hit_runtime.scheduler_failure_code,
                    source_hit_target->state, source_hit_target->substate,
                    source_hit_target->source_hit_recovery_active,
                    source_hit_target->animation_record,
                    source_hit_target->animation_index,
                    source_hit_target->animation_timer);
                return 56;
            }
            if (!avsp_round1_step_scheduler(&source_hit_runtime) ||
                source_hit_target->state != 0x0200u ||
                source_hit_target->substate != 0x0000u ||
                source_hit_target->source_hit_recovery_active ||
                source_hit_target->source_style85 != 0u ||
                source_hit_target->animation_record != 0x0012ded8UL)
                return 56;
            if (!avsp_round1_step_scheduler(&source_hit_runtime) ||
                source_hit_target->substate != 0x1600u ||
                source_hit_target->animation_record != 0x0012eafcUL)
            {
                fprintf(stderr,
                    "source HIT return code=%u state=%04x/%04x active=%u anim=%08lx a3=%u a4=%u a5=%u a6=%u style85=%u facing=%u actor_x=%d player_x=%d\n",
                    source_hit_runtime.scheduler_failure_code,
                    source_hit_target->state, source_hit_target->substate,
                    source_hit_target->source_hit_recovery_active,
                    source_hit_target->animation_record,
                    source_hit_target->source_a3,
                    source_hit_target->source_a4,
                    source_hit_target->source_a5,
                    source_hit_target->source_a6,
                    source_hit_target->source_style85,
                    source_hit_target->facing,
                    source_hit_target->x,
                    source_hit_runtime.player_action.x);
                return 56;
            }
        }
        {
            AvspRound1Runtime source_ko_runtime = projectile_runtime;
            AvspRound1ActorCore *source_ko_target =
                &source_ko_runtime.pools[0].records[12];
            unsigned int pool_index;
            unsigned int projectile_index;
            unsigned short progress_before =
                source_ko_runtime.first_encounter.source_progress;
            unsigned char free_before;
            for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT;
                 ++pool_index)
            {
                unsigned int actor_index;
                for (actor_index = 0u;
                     actor_index < source_ko_runtime.pools[pool_index].capacity;
                     ++actor_index)
                    if (pool_index != 0u || actor_index != 12u)
                        source_ko_runtime.pools[pool_index].records[
                            actor_index].active = 0u;
            }
            for (projectile_index = 0u;
                 projectile_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
                 ++projectile_index)
                source_ko_runtime.player_weapon_projectiles[
                    projectile_index].active = 0u;
            source_ko_target->active = 1u;
            source_ko_target->state = 0x0400u;
            source_ko_target->substate = 0u;
            source_ko_target->source_action = 0u;
            source_ko_target->health = -1;
            source_ko_target->source_prior_health = 87;
            source_ko_target->source_action_timer = 8u;
            source_ko_target->source_hit_mode = 0u;
            source_ko_target->source_hit_kind = 0x15u;
            source_ko_target->source_reaction_selector = 0u;
            source_ko_target->source_hit_recovery_active = 0u;
            source_ko_target->source_projectile_reaction_pending = 2u;
            source_ko_target->source_facing_selector = 0u;
            source_ko_target->x = 833;
            source_ko_target->y = 312;
            source_ko_target->z = 312;
            source_ko_target->source_x_fp = 0x03410000L;
            source_ko_target->source_y_fp = 0x01380000L;
            source_ko_target->source_z_fp = 0x01380000L;
            source_ko_target->animation_record = 0x0012d638UL;
            source_ko_target->assembly = 0x0012f762UL;
            if (!avsp_round1_step_scheduler(&source_ko_runtime) ||
                source_ko_target->active != 2u ||
                source_ko_target->state != 0x0402u ||
                source_ko_target->substate != 0u ||
                source_ko_target->source_action_timer != 8u ||
                source_ko_target->source_hit_recovery_active != 2u ||
                source_ko_target->source_reaction_selector != 0x36u ||
                source_ko_target->animation_record != 0x0012e04cUL ||
                source_ko_runtime.first_encounter.source_progress !=
                    (unsigned short)(progress_before + 1u))
                return 57;
            for (entry_calls = 0u; entry_calls < 8u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_ko_runtime))
                    return 57;
            if (source_ko_target->source_action_timer != 0u ||
                source_ko_target->substate != 0u)
                return 57;
            if (!avsp_round1_step_scheduler(&source_ko_runtime) ||
                source_ko_target->substate != 0x0200u ||
                source_ko_target->source_x_fp != 0x033f4000L ||
                source_ko_target->source_y_fp != 0x01418000L ||
                source_ko_target->source_x_velocity != -0x0001c000L ||
                source_ko_target->source_y_velocity != 0x00093000L ||
                source_ko_target->animation_record != 0x0012e05cUL)
                return 57;
            for (entry_calls = 0u; entry_calls < 5u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_ko_runtime))
                    return 57;
            if (source_ko_target->substate != 0x0200u ||
                source_ko_target->animation_record != 0x0012e04cUL ||
                source_ko_target->animation_timer != 1u)
                return 57;
            for (entry_calls = 0u; entry_calls < 56u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_ko_runtime))
                    return 57;
            if (source_ko_target->substate != 0x0400u ||
                source_ko_target->source_x_fp != 0x02d48000L ||
                source_ko_target->source_y_fp != 0x01381000L ||
                source_ko_target->source_hit_action_timer != 3u ||
                source_ko_target->animation_record != 0x0012ddb0UL)
                return 57;
            for (entry_calls = 0u; entry_calls < 3u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_ko_runtime))
                    return 57;
            if (source_ko_target->substate != 0x0600u ||
                source_ko_target->source_x_fp != 0x02d28000L ||
                source_ko_target->source_y_fp != 0x013c1000L ||
                source_ko_target->animation_record != 0x0012dd9cUL)
                return 57;
            for (entry_calls = 0u; entry_calls < 11u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_ko_runtime))
                    return 57;
            if (source_ko_target->state != 0x0404u ||
                source_ko_target->substate != 0u ||
                source_ko_target->source_x_fp != 0x02bc8000L ||
                source_ko_target->source_y_fp != 0x01389000L ||
                source_ko_target->source_hit_action_timer != 60u ||
                source_ko_target->animation_record != 0x0012ddb0UL)
                return 57;
            for (entry_calls = 0u; entry_calls < 60u; ++entry_calls)
                if (!avsp_round1_step_scheduler(&source_ko_runtime))
                    return 57;
            if (source_ko_target->state != 0x0600u ||
                source_ko_target->source_hit_action_timer != 0u ||
                source_ko_target->source_hit_recovery_active != 0u ||
                source_ko_runtime.rng_seed != projectile_runtime.rng_seed)
                return 57;
            free_before = source_ko_runtime.pools[0].free_count;
            source_ko_runtime.first_encounter.source_living_count = 1u;
            if (!avsp_round1_step_scheduler(&source_ko_runtime) ||
                source_ko_target->active ||
                source_ko_runtime.pools[0].free_count !=
                    (unsigned char)(free_before + 1u))
                return 57;
        }
        {
            AvspRound1Runtime child_release_runtime = projectile_runtime;
            AvspRound1WeaponProjectileAllocation *release_child =
                &child_release_runtime.player_weapon_projectiles[1];
            unsigned char release_free_before =
                child_release_runtime.player_weapon_projectile_free_count;
            unsigned long release_count_before =
                child_release_runtime.player_weapon_projectile_releases;
            release_child->state = 4u;
            if (!avsp_round1_step_scheduler(&child_release_runtime) ||
                release_child->active ||
                child_release_runtime.player_weapon_projectile_free_count !=
                    (unsigned char)(release_free_before + 1u) ||
                child_release_runtime.player_weapon_projectile_releases !=
                    release_count_before + 1u)
                return 55;
        }
        impact = 0;
        for (impact_index = 0u;
             impact_index < projectile_runtime.pools[3].capacity;
             ++impact_index)
            if (projectile_runtime.pools[3].records[impact_index].active &&
                projectile_runtime.pools[3].records[impact_index].actor_class ==
                    0x4e &&
                projectile_runtime.pools[3].records[impact_index].variant ==
                    1u)
            {
                impact = &projectile_runtime.pools[3].records[impact_index];
                break;
            }
        if (impact == 0)
            return 55;
        if (!avsp_round1_is_weapon_impact_actor(impact) ||
            impact->source_slot != 0x00ffb680UL + impact_index * 128UL ||
            impact->state != 0u || impact->variant != 1u ||
            impact->animation_record != expected_impact_animation ||
            impact->assembly != expected_impact_assembly ||
            impact->animation_timer != expected_impact_timer ||
            impact->animation_branch != expected_impact_branch ||
            impact->facing != child->facing ||
            impact->x != 926 || impact->y != 337 || impact->z != 318 ||
            projectile_runtime.class4e_variant1_allocation_requests != 1u ||
            projectile_runtime.class4e_variant1_allocations != 1u ||
            projectile_runtime.class4e_variant1_allocation_failures != 0u)
        {
            fprintf(stderr,
                "variant1 impact active=%u class=%d variant=%u state=%04x slot=%08lx facing=%u child=%u xyz=%d/%d/%d expected=%d/%d/%d animation=%08lx/%08lx timer=%u branch=%d ownership=%d requests=%lu allocations=%lu failures=%lu\n",
                impact->active, impact->actor_class, impact->variant,
                impact->state, impact->source_slot, impact->facing,
                child->facing, impact->x, impact->y, impact->z,
                926, 337, 318,
                impact->animation_record, impact->assembly,
                impact->animation_timer, impact->animation_branch,
                avsp_round1_is_weapon_impact_actor(impact),
                projectile_runtime.class4e_variant1_allocation_requests,
                projectile_runtime.class4e_variant1_allocations,
                projectile_runtime.class4e_variant1_allocation_failures);
            return 55;
        }
        {
            AvspRound1Runtime terminal_runtime = projectile_runtime;
            AvspRound1ActorCore *terminal_impact =
                &terminal_runtime.pools[3].records[impact_index];
            terminal_impact->state = 0x0200u;
            terminal_impact->animation_timer = 4095u;
            terminal_impact->animation_branch = (short)-32768;
            if (!avsp_round1_step_scheduler(&terminal_runtime) ||
                terminal_impact->state != 0x0400u ||
                terminal_impact->animation_timer != 4094u)
            {
                fprintf(stderr,
                    "variant1 terminal state=%04x timer=%u branch=%d code=%u\n",
                    terminal_impact->state,
                    terminal_impact->animation_timer,
                    terminal_impact->animation_branch,
                    terminal_runtime.scheduler_failure_code);
                return 55;
            }
        }
        target->hurt_selector = 0u;
        target->state = 0x0600u;
        target->substate = 0u;
        target->source_projectile_reaction_pending = 0u;
        projectile_runtime.first_encounter.source_living_count = 1u;
        for (entry_calls = 0u; entry_calls < 4u; ++entry_calls)
        {
            if (!avsp_round1_step_scheduler(&projectile_runtime))
            {
                fprintf(stderr,
                        "child cadence scheduler failed i=%u code=%u slot=%04x failures=%lu\n",
                        entry_calls, projectile_runtime.scheduler_failure_code,
                        projectile_runtime.scheduler_failure_source_slot,
                        projectile_runtime.failure_count);
                return 55;
            }
            if (entry_calls == 0u &&
                (impact->state != 0x0200u ||
                 impact->animation_record != 0x00092914UL ||
                 impact->assembly != 0x00092c04UL ||
                 projectile_runtime.class4e_variant1_initializations != 1u))
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
        AvspRound1Runtime class43_tail_runtime;
        unsigned int class43_tail_ticks;
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
        /* This fixture isolates entry-transition authority, not contact. */
        transition_runtime.player_hit_invulnerability = 1u;
        if (transition_runtime.class1f_initializations != 10u ||
            transition_runtime.class1f_initial_rng_calls != 10u ||
            transition_runtime.class09_rng_calls != 42u ||
            transition_runtime.rng_seed != 0x334fu)
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
            if (tick == 8u &&
                (transition_runtime.class09_rng_calls != 44u ||
                 transition_runtime.rng_seed != 0xcdb5u))
            {
                fprintf(stderr, "transition tick8 c09rng=%lu seed=%04x\n",
                    transition_runtime.class09_rng_calls,
                    transition_runtime.rng_seed);
                return 64;
            }
            if (tick == 1u &&
                (transition_runtime.entry_controller.state != 0x0202u ||
                 transition_runtime.first_encounter.source_intro_gate !=
                    0xffu ||
                 transition_runtime.first_encounter.source_intro_timer != 60u))
            {
                fprintf(stderr, "transition tick1 controller=%04x gate=%u timer=%u\n",
                    transition_runtime.entry_controller.state,
                    transition_runtime.first_encounter.source_intro_gate,
                    transition_runtime.first_encounter.source_intro_timer);
                return 64;
            }
            if (tick == 12u &&
                (transition_runtime.class1f_effect_requests != 2u ||
                 transition_runtime.class1f_effect_allocations != 2u ||
                 transition_runtime.class4e_initializations != 2u ||
                 transition_runtime.class4e_rng_calls != 2u ||
                 transition_runtime.class1f_audio_events != 1u ||
                 transition_runtime.class1f_audio_command != 0x0118u ||
                 transition_runtime.pools[3].free_count != 28u ||
                 effect_a->x != 840 || effect_a->y != 432 ||
                 effect_b->x != 812 || effect_b->y != 388 ||
                 guard->state != 0x0400u))
                return 65;
            if (tick == 13u &&
                (transition_runtime.class44_guard_clears != 1u ||
                 transition_runtime.class1f_effect_guard != 0u ||
                 guard->state != 0x0402u || guard->substate != 0u ||
                 guard->effect_timer != 3u))
                return 66;
            if (tick == 16u &&
                (transition_runtime.first_encounter.source_intro_gate != 0u ||
                 transition_runtime.entry_controller.state != 0x0202u ||
                 transition_runtime.first_encounter.source_intro_timer != 60u ||
                 transition_runtime.class45_allocations != 28u ||
                 transition_runtime.pools[3].free_count != 0u ||
                 !transition_runtime.pools[3].records[0].active ||
                 transition_runtime.pools[3].records[0].actor_class != 0x45 ||
                 transition_runtime.pools[3].records[0].state != 0u ||
                 transition_runtime.pools[3].records[0].x != 840 ||
                 transition_runtime.pools[3].records[0].y != 360 ||
                 transition_runtime.pools[3].records[0].z != 295))
                return 66;
            if (tick == 17u &&
                (transition_runtime.first_encounter.source_intro_timer != 59u ||
                 transition_runtime.class45_initializations != 28u ||
                 transition_runtime.class45_rng_calls != 196u ||
                 transition_runtime.pools[3].records[0].state != 0x0200u ||
                 transition_runtime.pools[3].records[0].x != 805 ||
                 transition_runtime.pools[3].records[0].y != 307 ||
                 transition_runtime.pools[3].records[0].facing != 3u ||
                 transition_runtime.pools[3].records[0].animation_record !=
                    0x0008df18UL))
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
                    208u || transition_runtime.camera_z_lower != 208 ||
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
            transition_runtime.class45_releases != 28u ||
            transition_runtime.class43_spawn_requests != 8u ||
            transition_runtime.class43_allocations != 8u ||
            transition_runtime.class43_allocation_failures != 0u ||
            transition_runtime.class43_initializations != 8u ||
            transition_runtime.class43_rng_calls != 56u ||
            transition_runtime.pools[3].free_count != 22u ||
            transition_runtime.pools[3].records[0].actor_class != 0x43 ||
            transition_runtime.pools[3].records[0].state != 0x0202u ||
            transition_runtime.pools[3].records[0].x != 771 ||
            transition_runtime.pools[3].records[0].y != 332 ||
            transition_runtime.pools[3].records[0].z != 335 ||
            transition_runtime.pools[3].records[0].animation_record !=
                0x0008d31aUL ||
            transition_runtime.player_weapon_projectile_collision_writes != 0u ||
            transition_runtime.player_weapon_projectile_damage_writes != 0u ||
            transition_runtime.failure_count != 0u ||
            transition_runtime.fallback_count != 0u)
        {
            fprintf(stderr, "transition summary completions=%lu audio=%lu releases=%lu pool24=%u collisions=%lu damage=%lu failures=%lu fallback=%lu first=%u/%u/%lu class43first=%d/%04x/%d/%d/%d/%08lx\n",
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
                transition_runtime.first_encounter.scheduler_updates,
                transition_runtime.pools[3].records[0].actor_class,
                transition_runtime.pools[3].records[0].state,
                transition_runtime.pools[3].records[0].x,
                transition_runtime.pools[3].records[0].y,
                transition_runtime.pools[3].records[0].z,
                transition_runtime.pools[3].records[0].animation_record);
            return 68;
        }
        class43_tail_runtime = transition_runtime;
        for (class43_tail_ticks = 0u;
             class43_tail_runtime.pools[3].records[0].active &&
             class43_tail_ticks < 40u; ++class43_tail_ticks)
            if (!avsp_round1_step_scheduler(&class43_tail_runtime))
                return 68;
        if (class43_tail_ticks != 10u ||
            class43_tail_runtime.pools[3].records[0].active)
        {
            fprintf(stderr,
                "class43 tail ticks=%u active=%u state=%04x releases=%lu code=%u\n",
                class43_tail_ticks,
                class43_tail_runtime.pools[3].records[0].active,
                class43_tail_runtime.pools[3].records[0].state,
                class43_tail_runtime.class43_releases,
                class43_tail_runtime.scheduler_failure_code);
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
            transition_runtime.class1f_action_releases != 0u)
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
        {
            fprintf(stderr,
                "transition tail completions=%lu audio=%lu class4e=%lu guard=%lu failures=%lu fallback=%lu\n",
                transition_runtime.class1f_transition_completions,
                transition_runtime.class1f_audio_events,
                transition_runtime.class4e_releases,
                transition_runtime.class44_guard_clears,
                transition_runtime.failure_count,
                transition_runtime.fallback_count);
            return 71;
        }
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
        /* This synthetic selector-cycle lane remains the no-target control. */
        integrated_runtime.player.source_target_low = 0u;
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
            {
                fprintf(stderr, "encounter blocked gate free=%u/%u blocked=%u fail=%lu rng=%04x\n",
                        encounter_runtime.pools[0].free_count, free_before,
                        encounter_runtime.first_encounter.source_blocked_by_living_count,
                        encounter_runtime.failure_count,
                        encounter_runtime.rng_seed);
                return 81;
            }
        }
        {
            AvspRound1Pool *pool = &encounter_runtime.pools[0];
            AvspRound1ActorCore *bounded = &pool->records[14];
            unsigned char free_before = pool->free_count;
            if (!bounded->active ||
                (unsigned short)bounded->source_slot != 0xa000u)
                return 81;
            bounded->state = 0x0600u;
            bounded->substate = 0u;
            bounded->health = -1;
            if (!avsp_round1_step_scheduler(&encounter_runtime) ||
                bounded->active || pool->free_count != free_before + 1u ||
                pool->free_stack[pool->free_count - 1u] != 0xa000u)
                return 81;
        }
        /* Exercise the accepted 0x028a3e current-state spawn edge through the
           current source LIFO.  Do not force the historical 0xa000 harness
           slot: the corrected source RNG keeps that initial actor alive. */
        {
            AvspRound1Pool *pool = &encounter_runtime.pools[0];
            if (pool->free_count == 0u)
            {
                fprintf(stderr, "encounter source LIFO empty rng=%04x\n",
                        encounter_runtime.rng_seed);
                return 81;
            }
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
            {
                fprintf(stderr, "encounter init scheduler tick=%u code=%u slot=%04x fail=%lu rng=%04x\n",
                        tick, encounter_runtime.scheduler_failure_code,
                        encounter_runtime.scheduler_failure_source_slot,
                        encounter_runtime.failure_count,
                        encounter_runtime.rng_seed);
                return 81;
            }
            ++tick;
        }
        if (!encounter_runtime.first_encounter.initialized ||
            encounter_runtime.first_encounter.encounter_state !=
                AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE ||
            encounter_runtime.first_encounter.presentation.x != 960 ||
            encounter_runtime.first_encounter.presentation.lane != 343 ||
            encounter_runtime.first_encounter.presentation.animation_record == 0UL ||
            encounter_runtime.first_encounter.presentation.assembly == 0UL)
        {
            fprintf(stderr, "encounter init=%u state=%u slot=%04x pos=%d/%d anim=%08lx asm=%08lx tick=%u rng=%04x controller=%04x timer=%u phase=%u living=%u progress=%u free=%u dynamic=%u fail=%lu code=%u\n",
                    encounter_runtime.first_encounter.initialized,
                    encounter_runtime.first_encounter.encounter_state,
                    (unsigned short)encounter_runtime.first_encounter.actor_source_slot,
                    encounter_runtime.first_encounter.presentation.x,
                    encounter_runtime.first_encounter.presentation.lane,
                    encounter_runtime.first_encounter.presentation.animation_record,
                    encounter_runtime.first_encounter.presentation.assembly,
                    tick, encounter_runtime.rng_seed,
                    encounter_runtime.entry_controller.state,
                    encounter_runtime.first_encounter.source_spawn_timer,
                    encounter_runtime.first_encounter.source_phase_counter,
                    encounter_runtime.first_encounter.source_living_count,
                    encounter_runtime.first_encounter.source_progress,
                    encounter_runtime.pools[0].free_count,
                    encounter_runtime.first_encounter.dynamic_spawned,
                    encounter_runtime.failure_count,
                    encounter_runtime.scheduler_failure_code);
            return 82;
        }
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
    {
        AvspRound1Runtime component_runtime;
        AvspRound1ActorCore *class01;
        AvspRound1ActorCore *class02;
        AvspRound1ActorCore *jump_actor;
        unsigned int tick = 0u;
        unsigned char free_before;
        unsigned short living_before;
        unsigned short jump_rng_before;
        unsigned char jump_rng_high;
        unsigned char jump_rng_low;
        unsigned char jump_rng_index;
        long jump_expected_velocity;
        unsigned int free_index;
        avsp_round1_init(&component_runtime);
        if (!avsp_round1_begin_first_entry(&component_runtime))
            return 96;
        while (!component_runtime.entry.control_enabled && tick < 1000u)
        {
            if (!avsp_round1_step_first_entry(&component_runtime))
                return 96;
            if (component_runtime.entry.spawned &&
                !avsp_round1_step_scheduler(&component_runtime))
                return 96;
            ++tick;
        }
        class01 = &component_runtime.pools[2].records[14];
        class02 = &component_runtime.pools[2].records[15];
        if (component_runtime.coffee_scene_record_cursor != 2u ||
            component_runtime.coffee_scene_spawns != 2u ||
            !class01->active || class01->actor_class != 0x01 ||
            class01->source_slot != 0x00ffb580UL ||
            class01->state != 0x0202u || class01->active != 2u ||
            class01->transition_timer != 72u ||
            class01->animation_record != 0x0006b45aUL ||
            !class02->active || class02->actor_class != 0x02 ||
            class02->source_slot != 0x00ffb600UL ||
            class02->state != 0x0200u || class02->source_a4 != 5u ||
            class02->animation_record != 0x0006b66cUL)
        {
            fprintf(stderr, "component entry cursor=%u spawns=%lu c01=%u/%d/%08lx/%04x/%u/%08lx c02=%u/%d/%08lx/%04x/%u/%08lx\n",
                component_runtime.coffee_scene_record_cursor,
                component_runtime.coffee_scene_spawns,
                class01->active, class01->actor_class,
                class01->source_slot, class01->state,
                class01->transition_timer, class01->animation_record,
                class02->active, class02->actor_class,
                class02->source_slot, class02->state,
                class02->source_a4, class02->animation_record);
            return 97;
        }
        {
            AvspRound1Runtime camera_sample_runtime = component_runtime;
            camera_sample_runtime.coffee_shop_obstacle_released = 1u;
            camera_sample_runtime.camera_x_position = 672;
            camera_sample_runtime.camera_x_previous = 671;
            if (!avsp_round1_step_scheduler(&camera_sample_runtime) ||
                camera_sample_runtime.coffee_scene_record_cursor != 2u ||
                camera_sample_runtime.pools[2].records[11].active != 0u)
            {
                fprintf(stderr,
                    "stage camera sample current=%d previous=%d cursor=%u actor=%u\n",
                    camera_sample_runtime.camera_x_position,
                    camera_sample_runtime.camera_x_previous,
                    camera_sample_runtime.coffee_scene_record_cursor,
                    camera_sample_runtime.pools[2].records[11].active);
                return 97;
            }
        }
        component_runtime.coffee_shop_obstacle_released = 1u;
        component_runtime.camera_x_position = 672;
        component_runtime.camera_x_previous = 672;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            component_runtime.coffee_scene_record_cursor != 3u ||
            component_runtime.pools[2].records[11].actor_class != 0x01 ||
            component_runtime.pools[2].records[11].variant != 1u ||
            component_runtime.pools[2].records[11].source_slot !=
                0x00ffb400UL)
            return 97;
        component_runtime.camera_x_position = 736;
        component_runtime.camera_x_previous = 736;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            component_runtime.coffee_scene_record_cursor != 4u ||
            component_runtime.pools[2].records[9].actor_class != 0x02 ||
            component_runtime.pools[2].records[9].source_slot !=
                0x00ffb300UL)
            return 97;
        {
            AvspRound1Runtime class0f_runtime = component_runtime;
            AvspRound1ActorCore *class0f_actor;
            AvspRound1ActorCore *class09_child = 0;
            unsigned short rng_before;
            unsigned short expected_class11_slots[4];
            unsigned short expected_class09_slot;
            unsigned char free20_before;
            unsigned int class11_count = 0u;
            unsigned int class11_variants = 0u;
            unsigned int pool_slot;
            class0f_runtime.camera_x_position = 817;
            class0f_runtime.camera_x_previous = 817;
            if (!avsp_round1_step_scheduler(&class0f_runtime) ||
                class0f_runtime.coffee_scene_record_cursor != 7u)
                return 150;
            class0f_actor = &class0f_runtime.pools[2].records[5];
            if (!class0f_actor->active ||
                class0f_actor->source_slot != 0x00ffb100UL ||
                class0f_actor->actor_class != 0x0f ||
                class0f_actor->dispatch_entry != 0x0006ed3eUL ||
                class0f_actor->state != 0x0200u ||
                class0f_actor->substate != 0u ||
                class0f_actor->source_a4 != 2u ||
                class0f_actor->object_or != 0x8000u ||
                class0f_actor->source_flags != 0x1du ||
                class0f_actor->x != 1301 || class0f_actor->y != 240 ||
                class0f_actor->z != 240 ||
                class0f_actor->animation_record != 0x0006ee4aUL ||
                class0f_actor->assembly != 0x0006ee86UL ||
                class0f_actor->hurt_selector != 1u ||
                class0f_actor->attack_selector != 1u ||
                class0f_runtime.class0f_initializations != 1u ||
                class0f_runtime.class0f_collision_calls != 1u ||
                class0f_runtime.class0f_navigation_calls != 1u)
                return 151;
            class0f_runtime.frame = 5523u - 2040u;
            class0f_actor->source_action_timer = 2u;
            if (!avsp_round1_step_scheduler_post_player_source_differential(
                    &class0f_runtime, 0, 1, 0) ||
                class0f_actor->source_action_timer != 1u ||
                class0f_actor->state != 0x0200u ||
                class0f_actor->animation_record != 0x0006ee4aUL ||
                class0f_runtime.class0f_collision_calls != 2u ||
                class0f_runtime.class0f_navigation_calls != 2u)
                return 152;
            class0f_actor->state = 0x0400u;
            class0f_actor->source_facing_selector = 1u;
            rng_before = class0f_runtime.rng_seed;
            for (pool_slot = 0u; pool_slot < 4u; ++pool_slot)
                expected_class11_slots[pool_slot] =
                    class0f_runtime.pools[3].free_stack[
                        class0f_runtime.pools[3].free_count - 4u + pool_slot];
            if (!avsp_round1_step_scheduler_post_player_source_differential(
                    &class0f_runtime, 0, 1, 0))
                return 153;
            for (pool_slot = 0u;
                 pool_slot < class0f_runtime.pools[3].capacity; ++pool_slot)
            {
                const AvspRound1ActorCore *child =
                    &class0f_runtime.pools[3].records[pool_slot];
                if (child->active == 2u && child->actor_class == 0x11)
                {
                    ++class11_count;
                    class11_variants |= 1u << child->variant;
                    if ((unsigned short)child->source_slot !=
                            expected_class11_slots[child->variant] ||
                        child->x != 1301 || child->y != 240 ||
                        child->z != 239 || child->facing != 0u ||
                        child->source_facing_selector != 1u ||
                        child->source_primary_x_fp != 1301L * 65536L ||
                        child->source_primary_y_fp != 240L * 65536L ||
                        child->source_alternate_x_fp != 1301L * 65536L ||
                        child->source_alternate_y_fp != 240L * 65536L)
                        return 154;
                }
            }
            if (class0f_actor->state != 0x0200u ||
                class0f_actor->source_a4 != 1u ||
                class0f_actor->facing != 0u ||
                class0f_actor->animation_record != 0x0006ee5eUL ||
                class0f_actor->assembly != 0x0006eeaaUL ||
                class0f_actor->hurt_selector != 2u ||
                class0f_actor->attack_selector != 2u ||
                class0f_runtime.class0f_audio_events != 1u ||
                class0f_runtime.class0f_audio_command != 0x0077u ||
                class0f_runtime.class0f_audio_argument != 0x00002000UL ||
                class0f_runtime.class0f_class11_allocation_requests != 4u ||
                class0f_runtime.class0f_class11_allocations != 4u ||
                class0f_runtime.class0f_class11_allocation_failures != 0u ||
                class11_count != 4u || class11_variants != 0x0fu ||
                class0f_runtime.rng_seed != rng_before)
                return 155;
            class0f_actor->state = 0x0202u;
            expected_class09_slot = class0f_runtime.pools[4].free_stack[
                class0f_runtime.pools[4].free_count - 1u];
            if (!avsp_round1_step_scheduler_post_player_source_differential(
                    &class0f_runtime, 0, 1, 0))
                return 156;
            for (pool_slot = 0u;
                 pool_slot < class0f_runtime.pools[4].capacity; ++pool_slot)
            {
                AvspRound1ActorCore *child =
                    &class0f_runtime.pools[4].records[pool_slot];
                if (child->active == 2u && child->actor_class == 0x09)
                    class09_child = child;
            }
            if (class0f_actor->state != 0x0200u ||
                class0f_actor->source_a4 != 0u ||
                class0f_actor->animation_record != 0x0006ee72UL ||
                class0f_actor->assembly != 0x0006eec8UL ||
                class0f_actor->hurt_selector != 0u ||
                class0f_actor->attack_selector != 3u ||
                class0f_runtime.class0f_audio_events != 2u ||
                class0f_runtime.class0f_audio_command != 0x0142u ||
                class0f_runtime.class0f_class09_allocation_requests != 1u ||
                class0f_runtime.class0f_class09_allocations != 1u ||
                class0f_runtime.class0f_class09_allocation_failures != 0u ||
                class09_child == 0 ||
                (unsigned short)class09_child->source_slot !=
                    expected_class09_slot || class09_child->x != 1301 ||
                class09_child->y != 320 || class09_child->z != 232 ||
                class09_child->source_motion_flags != 1u ||
                class0f_runtime.rng_seed != rng_before)
                return 157;
            free20_before = class0f_runtime.pools[2].free_count;
            class0f_actor->state = 0x0600u;
            if (!avsp_round1_step_scheduler_post_player_source_differential(
                    &class0f_runtime, 0, 1, 0) || class0f_actor->active ||
                class0f_runtime.pools[2].free_count !=
                    (unsigned char)(free20_before + 1u) ||
                class0f_runtime.class0f_releases != 1u ||
                class0f_runtime.class0f_reaction_entries != 2u ||
                class0f_runtime.class0f_state_transitions != 2u)
                return 158;
        }
#ifdef AVSP_CLASS0A_FOCUSED_TEST
        {
            AvspRound1Runtime class0a_runtime = component_runtime;
            AvspRound1ActorCore *class0a_actor =
                &class0a_runtime.pools[3].records[31];
            unsigned short rng_before = class0a_runtime.rng_seed;
            unsigned char free24_before;
            if (!class0a_actor->active || class0a_actor->type != 24u ||
                class0a_actor->actor_class != 0x0a ||
                class0a_actor->source_slot != 0x00ffc600UL ||
                class0a_actor->variant != 0x26u ||
                class0a_actor->state != 0x0200u ||
                class0a_actor->x != 0 || class0a_actor->y != 0 ||
                class0a_actor->z != 0 || class0a_actor->facing != 0u ||
                class0a_runtime.class0a_initializations != 1u ||
                (class0a_actor->animation_record != 0x000782a4UL &&
                 class0a_actor->animation_record != 0x000782acUL) ||
                class0a_actor->hurt_selector != 0u ||
                (class0a_actor->attack_selector != 4u &&
                 class0a_actor->attack_selector != 7u))
                return 159;
            class0a_actor->state = 0x0200u;
            class0a_actor->variant = 0x0au;
            class0a_runtime.camera_x_previous = (short)0x0920u;
            if (!avsp_round1_step_scheduler_post_player_source_differential(
                    &class0a_runtime, 1, 1, 1) ||
                class0a_actor->state != 0x0400u ||
                class0a_runtime.class0a_guard_transitions != 1u ||
                class0a_runtime.rng_seed != rng_before)
                return 160;
            free24_before = class0a_runtime.pools[3].free_count;
            if (!avsp_round1_step_scheduler_post_player_source_differential(
                    &class0a_runtime, 1, 1, 1) || class0a_actor->active ||
                class0a_runtime.pools[3].free_count !=
                    (unsigned char)(free24_before + 1u) ||
                class0a_runtime.class0a_releases != 1u ||
                class0a_runtime.rng_seed != rng_before)
                return 161;
        }
        {
            AvspRound1Runtime next_entry_runtime = component_runtime;
            AvspRound1ActorCore *class0a_actor;
            unsigned int index = (unsigned int)(0xc580u -
                next_entry_runtime.pools[3].source_base) /
                next_entry_runtime.pools[3].stride;
            memset(&next_entry_runtime.pools[3].records[index], 0,
                   sizeof(next_entry_runtime.pools[3].records[index]));
            next_entry_runtime.pools[3].free_stack[0] = 0xc580u;
            next_entry_runtime.pools[3].free_count = 1u;
            next_entry_runtime.entry.exit_started = 1u;
            next_entry_runtime.entry.exit_complete = 0u;
            next_entry_runtime.entry.exit_route_phase = 5u;
            next_entry_runtime.entry.exit_stall_remaining = 0u;
            next_entry_runtime.entry.exit_load_index = 0u;
            next_entry_runtime.route_state = 2;
            if (!avsp_round1_step_coffee_exit_display(&next_entry_runtime))
                return 162;
            class0a_actor = &next_entry_runtime.pools[3].records[index];
            if (!class0a_actor->active ||
                class0a_actor->source_slot != 0x00ffc580UL ||
                class0a_actor->actor_class != 0x0a ||
                class0a_actor->variant != 0x06u ||
                class0a_actor->state != 0x0200u ||
                class0a_actor->animation_record != 0x00077e54UL ||
                class0a_actor->assembly != 0x00078ba2UL ||
                class0a_actor->animation_timer != 16u ||
                class0a_actor->attack_selector != 16u ||
                next_entry_runtime.class0a_next_entry_spawns != 1u ||
                next_entry_runtime.entry.exit_load_index != 1u)
                return 162;
        }
#endif
        class01->state = 0x0204u;
        class01->animation_index = 2u;
        class01->animation_branch = (short)0x8000u;
        free_before = component_runtime.pools[0].free_count;
        living_before = component_runtime.first_encounter.source_living_count;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            class01->state != 0x0206u ||
            component_runtime.pools[0].free_count !=
                (unsigned char)(free_before - 1u) ||
            component_runtime.first_encounter.source_living_count !=
                (unsigned short)(living_before + 1u) ||
            component_runtime.class01_spawn_allocations != 1u ||
            component_runtime.class01_effect_requests != 8u ||
            component_runtime.class01_audio_events != 1u ||
            component_runtime.class01_audio_command != 0x006du)
            return 98;
        jump_actor = &component_runtime.pools[0].records[9];
        free_index = 0u;
        for (tick = 0u; tick < component_runtime.pools[0].capacity; ++tick)
        {
            if (tick == 9u)
                continue;
            component_runtime.pools[0].records[tick].active = 0u;
            component_runtime.pools[0].free_stack[free_index++] =
                (unsigned short)(component_runtime.pools[0].source_base +
                    tick * component_runtime.pools[0].stride);
        }
        component_runtime.pools[0].free_count = (unsigned char)free_index;
        component_runtime.first_encounter.source_living_count = 1u;
        jump_actor->state = 0x0200u;
        jump_actor->substate = 0x0e00u;
        jump_actor->source_action = 0x0e00u;
        jump_actor->source_action_initialized = 1u;
        jump_actor->handler_updates = 1u;
        jump_actor->x = 1000;
        jump_actor->y = 300;
        jump_actor->z = 300;
        jump_actor->source_x_fp = 1000L * 65536L;
        jump_actor->source_y_fp = 300L * 65536L;
        jump_actor->source_z_fp = 300L * 65536L;
        for (tick = 0u; tick < component_runtime.pools[3].capacity; ++tick)
            if (component_runtime.pools[3].records[tick].actor_class == 0x4e)
                component_runtime.pools[3].records[tick].active = 0u;
        jump_rng_before = component_runtime.rng_seed;
        jump_rng_high = (unsigned char)(((unsigned long)jump_rng_before *
            3UL & 0xffffUL) >> 8);
        jump_rng_low = (unsigned char)((jump_rng_before & 0x00ffu) +
                                       jump_rng_high);
        jump_rng_index = (unsigned char)((jump_rng_low & 0x0cu) >> 2);
        jump_expected_velocity = jump_rng_index == 0u ? -65536L :
            (jump_rng_index == 1u ? -81920L :
             (jump_rng_index == 2u ? -98304L : -131072L));
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            jump_actor->substate != 0x0e02u || jump_actor->x != 1000 ||
            jump_actor->y != 332 || jump_actor->z != 300 ||
            jump_actor->source_z_velocity != jump_expected_velocity ||
            component_runtime.class1f_action0e_rng_calls != 1u)
        {
            fprintf(stderr, "action0e entry state=%04x/%04x xyz=%d/%d/%d zvel=%ld rng=%lu code=%u\n",
                jump_actor->state, jump_actor->substate, jump_actor->x,
                jump_actor->y, jump_actor->z,
                jump_actor->source_z_velocity,
                component_runtime.class1f_action0e_rng_calls,
                component_runtime.scheduler_failure_code);
            return 98;
        }
        for (tick = 0u; tick < 64u && jump_actor->substate != 0u; ++tick)
            if (!avsp_round1_step_scheduler(&component_runtime))
            {
                fprintf(stderr, "action0e scheduler tick=%u state=%04x/%04x anim=%08lx timer=%u branch=%d code=%u slot=%04x failures=%lu\n",
                    tick, jump_actor->state, jump_actor->substate,
                    jump_actor->animation_record,
                    jump_actor->animation_timer,
                    jump_actor->animation_branch,
                    component_runtime.scheduler_failure_code,
                    component_runtime.scheduler_failure_source_slot,
                    component_runtime.failure_count);
                return 98;
            }
        if (jump_actor->substate != 0u || jump_actor->x != 1000 ||
            jump_actor->z >= 300 || jump_actor->y != jump_actor->z ||
            jump_actor->coordinate_mode != 0u ||
            jump_actor->source_style85 != 1u)
        {
            fprintf(stderr, "action0e exit tick=%u state=%04x/%04x xyz=%d/%d/%d mode=%u style=%u code=%u\n",
                tick, jump_actor->state, jump_actor->substate,
                jump_actor->x, jump_actor->y, jump_actor->z,
                jump_actor->coordinate_mode, jump_actor->source_style85,
                component_runtime.scheduler_failure_code);
            return 98;
        }
        jump_actor->state = 0x0200u;
        jump_actor->substate = 0x0200u;
        jump_actor->source_action = 0x0200u;
        jump_actor->source_action_initialized = 1u;
        jump_actor->source_a2 = 0u;
        jump_actor->source_field01 = 0u;
        jump_actor->x = 1000;
        component_runtime.camera_x_position = 0;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            jump_actor->state == 0x0600u || jump_actor->source_a2 != 0u)
            return 98;
        class02 = &component_runtime.pools[2].records[9];
        component_runtime.camera_x_position = 832;
        component_runtime.camera_x_previous = 832;
        component_runtime.player_action.x = 1091;
        component_runtime.player_action.lane = 320;
        component_runtime.player_action.height = 0;
        component_runtime.player_special_attack_active = 1u;
        component_runtime.player_special_attack_contact_ready = 1u;
        component_runtime.player.attack_selector = 11u;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            class02->health != -1 || class02->state != 0x0400u ||
            component_runtime.class02_damage_writes != 1u)
        {
            fprintf(stderr, "class02 damage health=%d state=%04x writes=%lu tests=%lu flags=%u special=%u code=%u\n",
                class02->health, class02->state,
                component_runtime.class02_damage_writes,
                component_runtime.class02_collision_tests,
                class02->source_flags,
                component_runtime.player_special_attack_contact_ready,
                component_runtime.scheduler_failure_code);
            return 99;
        }
        for (tick = 0u; tick < component_runtime.pools[2].capacity; ++tick)
            if (tick != 9u)
                component_runtime.pools[2].records[tick].active = 0u;
        for (tick = 0u; tick < component_runtime.pools[3].capacity; ++tick)
            component_runtime.pools[3].records[tick].active = 0u;
        component_runtime.pools[3].free_stack[0] = 0xbd80u;
        component_runtime.pools[3].free_stack[1] = 0xc180u;
        component_runtime.pools[3].free_stack[2] = 0xc200u;
        component_runtime.pools[3].free_stack[3] = 0xc380u;
        component_runtime.pools[3].free_count = 4u;
        component_runtime.rng_seed = 0x327fu;
        component_runtime.frame = 2805u;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            class02->state != 0x0200u || class02->source_a4 != 4u ||
            class02->animation_record != 0x0006b680UL ||
            component_runtime.class02_effect_requests != 4u ||
            component_runtime.class02_audio_events != 1u ||
            component_runtime.class02_audio_command != 0x0077u ||
            component_runtime.class47_spawn_requests != 4u ||
            component_runtime.class47_allocations != 4u ||
            component_runtime.class47_allocation_failures != 0u ||
            component_runtime.class47_initializations != 4u ||
            component_runtime.class47_rng_calls != 28u ||
            component_runtime.pools[3].records[14].active != 2u ||
            component_runtime.pools[3].records[14].actor_class != 0x47 ||
            component_runtime.pools[3].records[14].state != 0x0200u ||
            component_runtime.pools[3].records[14].x != 1150 ||
            component_runtime.pools[3].records[14].y != 438 ||
            component_runtime.pools[3].records[14].z != 335 ||
            component_runtime.pools[3].records[14].animation_record !=
                0x0008ee88UL)
        {
            fprintf(stderr, "class02 reaction state=%04x effects=%u record=%08lx requests=%lu audio=%lu/%04x class47=%lu/%lu/%lu init=%lu rng=%lu first=%u/%d/%04x/%d/%d/%d/%08lx code=%u\n",
                class02->state, class02->source_a4,
                class02->animation_record,
                component_runtime.class02_effect_requests,
                component_runtime.class02_audio_events,
                component_runtime.class02_audio_command,
                component_runtime.class47_spawn_requests,
                component_runtime.class47_allocations,
                component_runtime.class47_allocation_failures,
                component_runtime.class47_initializations,
                component_runtime.class47_rng_calls,
                component_runtime.pools[3].records[14].active,
                component_runtime.pools[3].records[14].actor_class,
                component_runtime.pools[3].records[14].state,
                component_runtime.pools[3].records[14].x,
                component_runtime.pools[3].records[14].y,
                component_runtime.pools[3].records[14].z,
                component_runtime.pools[3].records[14].animation_record,
                component_runtime.scheduler_failure_code);
            return 99;
        }
        class02->health = 63;
        class02->state = 0x0200u;
        class02->source_player_guard = 0u;
        component_runtime.player_special_attack_contact_ready = 1u;
        if (!avsp_round1_step_scheduler(&component_runtime) ||
            class02->health != 38 || class02->state != 0x0400u ||
            component_runtime.class02_damage_writes != 2u)
            return 99;
    }
    {
        AvspRound1Runtime type16_runtime;
        AvspRound1ActorCore *parent;
        AvspRound1ActorCore *projectile;
        unsigned int entry_ticks = 0u;
        avsp_round1_init(&type16_runtime);
        if (!avsp_round1_begin_first_entry(&type16_runtime))
            return 100;
        while (!type16_runtime.entry.control_enabled && entry_ticks < 1000u)
        {
            if (!avsp_round1_step_first_entry(&type16_runtime) ||
                (type16_runtime.entry.spawned &&
                 !avsp_round1_step_scheduler(&type16_runtime)))
                return 101;
            ++entry_ticks;
        }
        parent = &type16_runtime.pools[0].records[19];
        parent->state = 0x0208u;
        parent->substate = 0x0e02u;
        parent->source_action = 0x0e02u;
        parent->source_projectile_enable = 1u;
        parent->animation_record = 0x0012e580UL;
        parent->animation_timer = 1u;
        parent->animation_branch = 1;
        parent->animation_index = 3u;
        parent->facing = 1u;
        parent->x = 1022;
        parent->y = 320;
        parent->z = 320;
        if (!avsp_round1_step_scheduler(&type16_runtime) ||
            type16_runtime.type16_spawn_requests != 1u ||
            type16_runtime.type16_allocations != 1u ||
            type16_runtime.pools[1].free_count != 19u)
            return 102;
        projectile = &type16_runtime.pools[1].records[19];
        if (!projectile->active || projectile->type != 16u ||
            projectile->actor_class != 0x06 ||
            projectile->source_slot != 0x00ffae00UL ||
            projectile->state != 0x0200u || projectile->substate != 0u ||
            projectile->facing != 1u || projectile->variant != 0u ||
            projectile->x != 1081 || projectile->y != 384 ||
            projectile->z != 320 ||
            projectile->coordinate_mode != 1u ||
            projectile->object_or != 0x8000u ||
            projectile->source_x_velocity != 0x00080000L ||
            projectile->source_x_acceleration != -0x00002000L ||
            projectile->source_y_velocity != 0x00040000L ||
            projectile->source_y_acceleration != -0x00004000L ||
            projectile->animation_record != 0x000355dcUL ||
            projectile->assembly != 0x0003570cUL ||
            projectile->attack_selector != 1u ||
            parent->animation_record != 0x0012e590UL ||
            parent->animation_timer != 4u)
            return 103;

        parent->source_projectile_enable = 0u;
        stage_class1f_release(&type16_runtime, -1);
        if (!avsp_round1_step_scheduler(&type16_runtime))
            return 107;
        {
            AvspRound1Runtime terminal_runtime = type16_runtime;
            AvspRound1ActorCore *terminal_projectile =
                &terminal_runtime.pools[1].records[19];
            terminal_projectile->state = 0x0400u;
            terminal_projectile->animation_index = 6u;
            terminal_projectile->animation_record = 0x00035680UL;
            terminal_projectile->assembly = 0x00035824UL;
            terminal_projectile->animation_timer = 4095u;
            terminal_projectile->animation_branch = -32768;
            terminal_projectile->transition_timer = 2u;
            if (!avsp_round1_step_scheduler(&terminal_runtime) ||
                terminal_projectile->state != 0x0400u ||
                terminal_projectile->transition_timer != 1u ||
                terminal_projectile->animation_timer != 4094u ||
                !avsp_round1_step_scheduler(&terminal_runtime) ||
                terminal_projectile->state != 0x0600u ||
                terminal_projectile->transition_timer != 0u ||
                terminal_projectile->animation_timer != 4094u ||
                !avsp_round1_step_scheduler(&terminal_runtime) ||
                terminal_projectile->active != 0u ||
                terminal_runtime.type16_releases != 1u)
            {
                fprintf(stderr,
                    "type16 terminal action-timer state=%04x timer=%u animation_timer=%u active=%u releases=%lu code=%u\n",
                    terminal_projectile->state,
                    terminal_projectile->transition_timer,
                    terminal_projectile->animation_timer,
                    terminal_projectile->active,
                    terminal_runtime.type16_releases,
                    terminal_runtime.scheduler_failure_code);
                return 108;
            }
        }
        projectile->state = 0x0200u;
        projectile->health = 0;
        projectile->x = 800;
        projectile->y = 400;
        projectile->z = 320;
        projectile->source_x_fp = 800L * 65536L;
        projectile->source_y_fp = 400L * 65536L;
        projectile->source_z_fp = 320L * 65536L;
        projectile->source_x_velocity = 0L;
        projectile->source_x_acceleration = 0L;
        projectile->source_y_velocity = 0L;
        projectile->source_y_acceleration = 0L;
        projectile->source_z_velocity = 0L;
        projectile->animation_index = 3u;
        projectile->animation_record = 0x0003560cUL;
        projectile->assembly = 0x00035736UL;
        projectile->animation_timer = 3u;
        projectile->animation_branch = -32768;
        projectile->attack_selector = 1u;
        type16_runtime.player.x = 800;
        type16_runtime.player.y = 355;
        type16_runtime.player.z = 320;
        type16_runtime.player.hurt_selector = 17u;
        type16_runtime.player.health = 95;
        type16_runtime.player_action.x = 800;
        type16_runtime.player_action.lane = 320;
        type16_runtime.player_action.health = 95;
        type16_runtime.first_encounter.pending_player_damage = 0u;
        if (!avsp_round1_step_scheduler(&type16_runtime) ||
            projectile->health != -1 ||
            type16_runtime.first_encounter.pending_player_damage != 17u ||
            type16_runtime.type16_collision_writes != 1u ||
            type16_runtime.type16_damage_writes != 1u)
        {
            fprintf(stderr,
                "type16 collision health=%d pending=%u writes=%lu/%lu position=%d/%d/%d player=%d/%d/%d selector=%u state=%04x code=%u failure=%lu\n",
                projectile->health,
                type16_runtime.first_encounter.pending_player_damage,
                type16_runtime.type16_collision_writes,
                type16_runtime.type16_damage_writes,
                projectile->x, projectile->y, projectile->z,
                type16_runtime.player.x, type16_runtime.player.y,
                type16_runtime.player.z, projectile->attack_selector,
                projectile->state,
                type16_runtime.scheduler_failure_code,
                type16_runtime.failure_count);
            return 104;
        }
        if (!avsp_round1_step_player(&type16_runtime, 0u, 0) ||
            type16_runtime.player.health != 78 ||
            type16_runtime.player_action.health != 78 ||
            type16_runtime.first_encounter.player_damage_events != 1u)
        {
            fprintf(stderr,
                "type16 damage health=%d/%d pending=%u damage=%u events=%lu state=%04x/%04x failures=%lu\n",
                type16_runtime.player.health,
                type16_runtime.player_action.health,
                type16_runtime.first_encounter.pending_player_damage,
                type16_runtime.first_encounter.player_damage,
                type16_runtime.first_encounter.player_damage_events,
                type16_runtime.player.state,
                type16_runtime.player.substate,
                type16_runtime.failure_count);
            return 105;
        }
        if (!avsp_round1_step_scheduler(&type16_runtime) ||
            projectile->state != 0x0600u ||
            !avsp_round1_step_scheduler(&type16_runtime) ||
            projectile->active != 0u ||
            type16_runtime.type16_releases != 1u ||
            type16_runtime.pools[1].free_count != 20u)
            return 106;
    }
    {
        AvspRound1Runtime inner_runtime;
        AvspRound1ActorCore *parent;
        unsigned int entry_ticks = 0u;
        unsigned int ticks = 0u;
        avsp_round1_init(&inner_runtime);
        if (!avsp_round1_begin_first_entry(&inner_runtime))
            return 109;
        while (!inner_runtime.entry.control_enabled && entry_ticks < 1000u)
        {
            if (!avsp_round1_step_first_entry(&inner_runtime) ||
                (inner_runtime.entry.spawned &&
                 !avsp_round1_step_scheduler(&inner_runtime)))
            {
                fprintf(stderr,
                    "inner8 entry failure tick=%u code=%u slot=%04x state=%04x/%04x failures=%lu\n",
                    entry_ticks, inner_runtime.scheduler_failure_code,
                    inner_runtime.scheduler_failure_source_slot,
                    inner_runtime.scheduler_failure_state,
                    inner_runtime.scheduler_failure_substate,
                    inner_runtime.failure_count);
                return 109;
            }
            ++entry_ticks;
        }
        for (ticks = 0u; ticks < inner_runtime.pools[2].capacity; ++ticks)
        {
            AvspRound1ActorCore *scene_actor =
                &inner_runtime.pools[2].records[ticks];
            if (scene_actor->active && scene_actor->actor_class == 0x01)
            {
                scene_actor->active = 0u;
                inner_runtime.pools[2].free_stack[
                    inner_runtime.pools[2].free_count++] =
                    (unsigned short)(scene_actor->source_slot & 0xffffu);
            }
        }
        inner_runtime.coffee_scene_record_cursor =
            AVSP_ROUND1_COFFEE_SCENE_RECORD_COUNT;
        for (ticks = 0u; ticks < inner_runtime.pools[3].capacity; ++ticks)
        {
            AvspRound1ActorCore *scene_actor =
                &inner_runtime.pools[3].records[ticks];
            if (scene_actor->active && scene_actor->actor_class == 0x43)
            {
                scene_actor->active = 0u;
                inner_runtime.pools[3].free_stack[
                    inner_runtime.pools[3].free_count++] =
                    (unsigned short)(scene_actor->source_slot & 0xffffu);
            }
        }
        ticks = 0u;
        stage_class1f_release(&inner_runtime, 19);
        if (!avsp_round1_step_scheduler(&inner_runtime))
            return 109;
        parent = &inner_runtime.pools[0].records[19];
        parent->state = 0x0200u;
        parent->substate = 0x1600u;
        parent->source_action = 0x1600u;
        parent->source_field01 = 0u;
        parent->source_b0 = 1u;
        parent->source_motion_flags = 0u;
        parent->source_style85 = 1u;
        parent->facing = 1u;
        parent->x = 1226;
        parent->y = 247;
        parent->z = 247;
        parent->source_x_fp = 1226L * 65536L;
        parent->source_y_fp = 247L * 65536L;
        parent->source_z_fp = 247L * 65536L;
        parent->animation_record = 0x0012ec44UL;
        parent->animation_timer = 2u;
        parent->animation_branch = -32768;
        inner_runtime.player_action.x = 1064;
        inner_runtime.player_action.lane = 320;
        inner_runtime.rng_seed = 0x44eau;
        if (!avsp_round1_step_scheduler(&inner_runtime) ||
            parent->state != 0x0208u || parent->substate != 0x0600u ||
            parent->facing != 0u || parent->transition_timer != 600u ||
            parent->source_motion_flags != 0u ||
            parent->source_motion_fields[2] != 0 ||
            parent->source_target_low != 0x8380u ||
            inner_runtime.rng_seed != 0xceb8u)
        {
            fprintf(stderr,
                "inner8 transition code=%u slot=%04x state=%04x/%04x facing=%u timer=%u flags=%u motion2=%d target=%04x rng=%04x field01=%u failures=%lu\n",
                inner_runtime.scheduler_failure_code,
                inner_runtime.scheduler_failure_source_slot,
                parent->state, parent->substate, parent->facing,
                parent->transition_timer, parent->source_motion_flags,
                parent->source_motion_fields[2], parent->source_target_low,
                inner_runtime.rng_seed, parent->source_field01,
                inner_runtime.failure_count);
            return 109;
        }
        {
            AvspRound1Runtime terrain_turn_runtime = inner_runtime;
            AvspRound1ActorCore *terrain_actor =
                &terrain_turn_runtime.pools[0].records[19];
            unsigned int pool_index;
            for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT;
                 ++pool_index)
            {
                unsigned int actor_index;
                for (actor_index = 0u;
                     actor_index <
                        terrain_turn_runtime.pools[pool_index].capacity;
                     ++actor_index)
                    if (pool_index != 0u || actor_index != 19u)
                        terrain_turn_runtime.pools[pool_index].records[
                            actor_index].active = 0u;
            }
            terrain_turn_runtime.route_state = 4;
            terrain_turn_runtime.player_action.x = 0;
            terrain_turn_runtime.player_action.lane = 0;
            terrain_actor->active = 1u;
            terrain_actor->type = 12u;
            terrain_actor->actor_class = 0x1f;
            terrain_actor->state = 0x0208u;
            terrain_actor->substate = 0x0400u;
            terrain_actor->source_action = 0x0400u;
            terrain_actor->source_style85 = 1u;
            terrain_actor->source_direction = 14u;
            terrain_actor->source_primary_animation_record = 0x0012d488UL;
            terrain_actor->source_x_fp = 0x045cf200L;
            terrain_actor->source_y_fp = 0x00e0ef00L;
            terrain_actor->x = 1116;
            terrain_actor->y = 224;
            terrain_actor->z = 224;
            terrain_actor->animation_record = 0x0012d4e8UL;
            terrain_actor->assembly = 0x0012f890UL;
            terrain_actor->animation_timer = 1u;
            terrain_actor->animation_branch = 1540;
            terrain_actor->source_next_animation_record = 0x0012d4f8UL;
            terrain_actor->source_movement_table = 4u;
            terrain_actor->hurt_selector = 2u;
            terrain_actor->attack_selector = 0u;
            if (!avsp_round1_step_scheduler(&terrain_turn_runtime) ||
                terrain_actor->animation_record != 0x0012d4f8UL ||
                terrain_actor->source_x_fp != 0x0463d100L ||
                terrain_actor->source_y_fp != 0x00e0a100L ||
                terrain_actor->z != 224 ||
                terrain_actor->source_navigation_contact_bits == 0u ||
                terrain_actor->source_direction != 30u)
            {
                fprintf(stderr,
                    "inner8 terrain direction code=%u state=%04x/%04x anim=%08lx xfp=%08lx yfp=%08lx z=%d contact=%u direction=%u failures=%lu\n",
                    terrain_turn_runtime.scheduler_failure_code,
                    terrain_actor->state, terrain_actor->substate,
                    terrain_actor->animation_record,
                    terrain_actor->source_x_fp,
                    terrain_actor->source_y_fp,
                    terrain_actor->z,
                    terrain_actor->source_navigation_contact_bits,
                    terrain_actor->source_direction,
                    terrain_turn_runtime.failure_count);
                return 110;
            }
            terrain_actor->state = 0x0208u;
            terrain_actor->substate = 0x0400u;
            terrain_actor->source_action = 0x0400u;
            terrain_actor->source_style85 = 1u;
            terrain_actor->source_direction = 14u;
            terrain_actor->source_motion_fields[3] = 2;
            terrain_actor->source_primary_animation_record = 0x0012d488UL;
            terrain_actor->source_x_fp = 0x04335500L;
            terrain_actor->source_y_fp = 0x00e53700L;
            terrain_actor->x = 1075;
            terrain_actor->y = 229;
            terrain_actor->z = 229;
            terrain_actor->animation_record = 0x0012d4f8UL;
            terrain_actor->assembly = 0x0012f8b8UL;
            terrain_actor->animation_timer = 1u;
            terrain_actor->animation_branch = -30958;
            terrain_actor->source_next_animation_record = 0x0012d488UL;
            terrain_actor->source_movement_table = 18u;
            if (!avsp_round1_step_scheduler(&terrain_turn_runtime) ||
                terrain_actor->animation_record != 0x0012d488UL ||
                terrain_actor->source_x_fp != 0x043a9600L ||
                terrain_actor->source_y_fp != 0x00e07300L ||
                terrain_actor->z != 224 ||
                terrain_actor->source_navigation_contact_bits == 0u ||
                terrain_actor->source_direction != 30u)
            {
                fprintf(stderr,
                    "inner8 terrain rebind direction code=%u state=%04x/%04x anim=%08lx xfp=%08lx yfp=%08lx z=%d contact=%u direction=%u failures=%lu\n",
                    terrain_turn_runtime.scheduler_failure_code,
                    terrain_actor->state, terrain_actor->substate,
                    terrain_actor->animation_record,
                    terrain_actor->source_x_fp,
                    terrain_actor->source_y_fp,
                    terrain_actor->z,
                    terrain_actor->source_navigation_contact_bits,
                    terrain_actor->source_direction,
                    terrain_turn_runtime.failure_count);
                return 110;
            }
            terrain_actor->state = 0x0208u;
            terrain_actor->substate = 0x1006u;
            terrain_actor->source_action = 0x1006u;
            terrain_actor->source_style85 = 0u;
            terrain_actor->source_direction = 6u;
            terrain_actor->facing = 1u;
            terrain_actor->source_navigation_contact_bits = 0u;
            terrain_actor->source_x_fp = 0x04183700L;
            terrain_actor->source_y_fp = 0x011e9f00L;
            terrain_actor->x = 1048;
            terrain_actor->y = 286;
            terrain_actor->z = 286;
            terrain_actor->animation_record = 0x0012e68cUL;
            terrain_actor->assembly = 0x0012f5deUL;
            terrain_actor->animation_timer = 6u;
            terrain_actor->animation_branch = -32768;
            terrain_actor->source_next_animation_record = 0x0012e68cUL;
            terrain_actor->source_movement_table = 0u;
            if (!avsp_round1_step_scheduler(&terrain_turn_runtime) ||
                terrain_actor->state != 0x0208u ||
                terrain_actor->substate != 0x1000u ||
                terrain_actor->source_style85 != 1u ||
                terrain_actor->source_direction != 6u ||
                terrain_actor->animation_record != 0x0012ee98UL ||
                terrain_actor->animation_timer != 4u ||
                terrain_actor->animation_branch != 19 ||
                terrain_actor->source_x_fp != 0x0429bf00L ||
                terrain_actor->source_y_fp != 0x01223f00L ||
                terrain_actor->z != 290)
            {
                fprintf(stderr,
                    "inner8 action10 terminal binding code=%u state=%04x/%04x style=%u direction=%u anim=%08lx timer=%u branch=%d xfp=%08lx yfp=%08lx z=%d failures=%lu\n",
                    terrain_turn_runtime.scheduler_failure_code,
                    terrain_actor->state, terrain_actor->substate,
                    terrain_actor->source_style85,
                    terrain_actor->source_direction,
                    terrain_actor->animation_record,
                    terrain_actor->animation_timer,
                    terrain_actor->animation_branch,
                    terrain_actor->source_x_fp,
                    terrain_actor->source_y_fp,
                    terrain_actor->z,
                    terrain_turn_runtime.failure_count);
                return 110;
            }
            terrain_turn_runtime.player_action.x = 1360;
            terrain_turn_runtime.player_action.lane = 319;
            terrain_actor->state = 0x0208u;
            terrain_actor->substate = 0x1000u;
            terrain_actor->source_action = 0x1000u;
            terrain_actor->source_style85 = 1u;
            terrain_actor->source_direction = 6u;
            terrain_actor->facing = 1u;
            terrain_actor->source_inner8_x_offset = -208;
            terrain_actor->source_inner8_z_offset = 0;
            terrain_actor->effect_timer = 149u;
            terrain_actor->source_action_timer = 4u;
            terrain_actor->source_navigation_contact_bits = 0u;
            terrain_actor->source_x_fp = 0x04726c00L;
            terrain_actor->source_y_fp = 0x013b3800L;
            terrain_actor->x = 1138;
            terrain_actor->y = 315;
            terrain_actor->z = 315;
            terrain_actor->animation_record = 0x0012eef8UL;
            terrain_actor->assembly = 0x0012f890UL;
            terrain_actor->animation_timer = 4u;
            terrain_actor->animation_branch = 1540;
            terrain_actor->source_next_animation_record = 0x0012ef08UL;
            terrain_actor->source_movement_table = 4u;
            if (!avsp_round1_step_scheduler(&terrain_turn_runtime) ||
                terrain_actor->state != 0x0208u ||
                terrain_actor->substate != 0x0802u ||
                terrain_actor->source_style85 != 1u ||
                terrain_actor->animation_record != 0x0012d628UL ||
                terrain_actor->animation_timer != 6u ||
                terrain_actor->animation_branch != 0 ||
                terrain_actor->source_x_fp != 0x04726c00L ||
                terrain_actor->source_y_fp != 0x013b3800L ||
                terrain_actor->z != 315)
            {
                fprintf(stderr,
                    "inner8 action10 overlap override code=%u state=%04x/%04x style=%u anim=%08lx timer=%u branch=%d xfp=%08lx yfp=%08lx z=%d failures=%lu\n",
                    terrain_turn_runtime.scheduler_failure_code,
                    terrain_actor->state, terrain_actor->substate,
                    terrain_actor->source_style85,
                    terrain_actor->animation_record,
                    terrain_actor->animation_timer,
                    terrain_actor->animation_branch,
                    terrain_actor->source_x_fp,
                    terrain_actor->source_y_fp,
                    terrain_actor->z,
                    terrain_turn_runtime.failure_count);
                return 110;
            }
            terrain_actor->animation_record = 0x0012d678UL;
            terrain_actor->assembly = 0x0012f5acUL;
            terrain_actor->animation_timer = 4u;
            terrain_actor->animation_branch = -32768;
            terrain_actor->source_next_animation_record = 0x0012d678UL;
            if (!avsp_round1_step_scheduler(&terrain_turn_runtime) ||
                terrain_actor->state != 0x0208u ||
                terrain_actor->substate != 0x0e00u ||
                terrain_actor->source_style85 != 0u ||
                terrain_actor->animation_record != 0x0012d678UL ||
                terrain_actor->animation_timer != 3u ||
                terrain_actor->animation_branch != -32768 ||
                terrain_actor->source_x_fp != 0x04726c00L ||
                terrain_actor->source_y_fp != 0x013b3800L ||
                terrain_actor->z != 315)
            {
                fprintf(stderr,
                    "inner8 action8 phase2 terminal code=%u state=%04x/%04x style=%u anim=%08lx timer=%u branch=%d xfp=%08lx yfp=%08lx z=%d failures=%lu\n",
                    terrain_turn_runtime.scheduler_failure_code,
                    terrain_actor->state, terrain_actor->substate,
                    terrain_actor->source_style85,
                    terrain_actor->animation_record,
                    terrain_actor->animation_timer,
                    terrain_actor->animation_branch,
                    terrain_actor->source_x_fp,
                    terrain_actor->source_y_fp,
                    terrain_actor->z,
                    terrain_turn_runtime.failure_count);
                return 110;
            }
            terrain_actor->state = 0x0208u;
            terrain_actor->substate = 0x0e02u;
            terrain_actor->source_action = 0x0e02u;
            terrain_actor->source_motion_fields[0] = 4;
            terrain_actor->source_style85 = 0u;
            terrain_actor->source_airborne = 1u;
            terrain_actor->facing = 1u;
            terrain_actor->source_x_fp = 0x04496c00L;
            terrain_actor->source_y_fp = 0x0146c000L;
            terrain_actor->source_x_velocity = -0x00010000L;
            terrain_actor->source_x_acceleration = 0L;
            terrain_actor->source_y_velocity = -0x000c0600L;
            terrain_actor->source_y_acceleration = -0x00009600L;
            terrain_actor->x = 1097;
            terrain_actor->y = 326;
            terrain_actor->z = 315;
            terrain_actor->animation_record = 0x0012e638UL;
            terrain_actor->assembly = 0x0012f97cUL;
            terrain_actor->animation_timer = 3u;
            terrain_actor->animation_branch = 0;
            terrain_actor->source_next_animation_record = 0x0012e648UL;
            if (!avsp_round1_step_scheduler(&terrain_turn_runtime) ||
                terrain_actor->state != 0x0208u ||
                terrain_actor->substate != 0x0e02u ||
                terrain_actor->source_motion_fields[0] != 6 ||
                terrain_actor->source_airborne != 0u ||
                terrain_actor->source_x_fp != 0x04486c00L ||
                terrain_actor->source_y_fp != 0x013aba00L ||
                terrain_actor->y != 314 || terrain_actor->z != 315 ||
                terrain_actor->animation_record != 0x0012e550UL ||
                terrain_actor->animation_timer != 6u)
            {
                fprintf(stderr,
                    "inner8 action0e landing code=%u state=%04x/%04x phase=%d airborne=%u anim=%08lx timer=%u xfp=%08lx yfp=%08lx y=%d z=%d failures=%lu\n",
                    terrain_turn_runtime.scheduler_failure_code,
                    terrain_actor->state, terrain_actor->substate,
                    terrain_actor->source_motion_fields[0],
                    terrain_actor->source_airborne,
                    terrain_actor->animation_record,
                    terrain_actor->animation_timer,
                    terrain_actor->source_x_fp,
                    terrain_actor->source_y_fp,
                    terrain_actor->y, terrain_actor->z,
                    terrain_turn_runtime.failure_count);
                return 110;
            }
        }
        parent->state = 0x0208u;
        parent->substate = 0x0e00u;
        parent->source_action = 0x0e00u;
        parent->source_motion_fields[0] = 0;
        parent->source_projectile_enable = 0u;
        parent->facing = 1u;
        parent->x = 1064;
        parent->y = 320;
        parent->z = 320;
        parent->source_x_fp = 1064L * 65536L;
        parent->source_y_fp = 320L * 65536L;
        parent->source_z_fp = 320L * 65536L;
        inner_runtime.rng_seed = 0xb069u;
        while (inner_runtime.type16_spawn_requests < 3u && ticks < 300u)
        {
            if (!avsp_round1_step_scheduler(&inner_runtime))
                return 109;
            ++ticks;
        }
        while (parent->source_motion_fields[0] != 8 && ticks < 400u)
        {
            if (!avsp_round1_step_scheduler(&inner_runtime))
                return 109;
            ++ticks;
        }
        if (inner_runtime.rng_seed != 0xd00bu ||
            inner_runtime.type16_spawn_requests != 3u ||
            inner_runtime.type16_allocations != 3u ||
            parent->source_motion_fields[0] != 8 ||
            parent->x == 1064 ||
            parent->source_projectile_enable != 0u)
        {
            fprintf(stderr,
                "inner8 motion seed=%04x type16=%lu/%lu phase=%d x=%d emit=%u ticks=%u class43=%lu/%lu c01=%lu\n",
                inner_runtime.rng_seed,
                inner_runtime.type16_spawn_requests,
                inner_runtime.type16_allocations,
                parent->source_motion_fields[0],
                parent->x,
                parent->source_projectile_enable,
                ticks,
                inner_runtime.class43_allocations,
                inner_runtime.class43_rng_calls,
                inner_runtime.class01_spawn_allocations);
            return 109;
        }
    }
    {
        AvspRound1Runtime reuse_runtime;
        unsigned int source_frame;
        avsp_round1_init(&reuse_runtime);
        for (source_frame = 1972u; source_frame <= 2573u; ++source_frame)
        {
            unsigned short input = avsp_round1_coffee_shop_source_input(
                (unsigned short)source_frame);
            unsigned int tick;
            if (source_frame == 2072u &&
                !avsp_round1_begin_first_entry(&reuse_runtime))
                return 114;
            if (source_frame == 2572u || source_frame == 2573u)
            {
                const AvspRound1ActorCore *reused =
                    &reuse_runtime.pools[0].records[17];
                unsigned long expected_record = source_frame == 2572u ?
                    0x0012e778UL : 0x0012e38cUL;
                unsigned long expected_assembly = source_frame == 2572u ?
                    0x0012f794UL : 0x0013065eUL;
                unsigned short expected_substate = source_frame == 2572u ?
                    0x0c00u : 0x0c02u;
                unsigned short expected_timer = source_frame == 2572u ?
                    1u : 8u;
                short expected_branch = source_frame == 2572u ?
                    (short)-32760 : 0;
                if (!reused->active || reused->actor_class != 0x1f ||
                    reused->state != 0x0200u ||
                    reused->substate != expected_substate ||
                    reused->animation_record != expected_record ||
                    reused->assembly != expected_assembly ||
                    reused->animation_timer != expected_timer ||
                    reused->animation_branch != expected_branch)
                {
                    fprintf(stderr,
                        "Coffee Shop recurring presentation reuse failed frame=%u active=%u class=%02x state=%04x/%04x animation=%08lx assembly=%08lx timer=%u branch=%d\n",
                        source_frame, reused->active,
                        (unsigned int)(unsigned char)reused->actor_class,
                        reused->state, reused->substate,
                        reused->animation_record, reused->assembly,
                        reused->animation_timer, reused->animation_branch);
                    return 114;
                }
            }
            reuse_runtime.frame = source_frame >= 2040u ?
                source_frame - 2040u : 0u;
            for (tick = 0u;
                 tick < avsp_round1_coffee_shop_source_updates(
                    (unsigned short)source_frame); ++tick)
            {
                int player_authority_enabled_at_tick_start =
                    reuse_runtime.route_state == 4;
                if (reuse_runtime.entry.started &&
                    reuse_runtime.route_state != 4 &&
                    !avsp_round1_step_first_entry(&reuse_runtime))
                    return 115;
                if (player_authority_enabled_at_tick_start &&
                    reuse_runtime.route_state == 4 &&
                    !avsp_round1_step_player(&reuse_runtime, input, 0))
                    return 115;
                if (reuse_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler(&reuse_runtime))
                    return 115;
            }
        }
    }
    {
        AvspRound1Runtime hit_runtime;
        unsigned int source_frame;
        unsigned int actor_index;
        unsigned char tracked_active = 0xffu;
        unsigned short tracked_state = 0xffffu;
        unsigned short tracked_substate = 0xffffu;
        unsigned long tracked_record = 0xffffffffUL;
        unsigned char tracked_animation_index = 0xffu;
        unsigned char tracked_recovery = 0xffu;
        avsp_round1_init(&hit_runtime);
        for (source_frame = 1972u; source_frame <= 3313u; ++source_frame)
        {
            unsigned short input = avsp_round1_coffee_shop_source_input(
                (unsigned short)source_frame);
            unsigned int source_updates =
                avsp_round1_coffee_shop_source_updates(
                    (unsigned short)source_frame);
            unsigned int class02_updates =
                avsp_round1_coffee_shop_class02_source_updates(
                    (unsigned short)source_frame);
            unsigned int phase_updates = source_updates > class02_updates ?
                source_updates : class02_updates;
            unsigned int source_tick;
            if (source_frame >= 2304u && source_frame <= 2308u)
            {
                const AvspRound1WeaponProjectileAllocation *projectile =
                    &hit_runtime.player_weapon_projectiles[4];
                const AvspRound1ActorCore *tracked =
                    &hit_runtime.pools[0].records[16];
                fprintf(stderr,
                    "record4/A180 frame=%u p=%u/%u/%u %d/%d/%d record=%08lx timer=%u collision=%d registered=%u t=%u %04x/%04x %d/%d/%d record=%08lx health=%d pending=%u\n",
                    source_frame, projectile->active,
                    projectile->actor_class, projectile->state,
                    projectile->x, projectile->y, projectile->z,
                    projectile->animation_record,
                    projectile->animation_timer,
                    projectile->collision_result,
                    projectile->collision_registered,
                    tracked->active, tracked->state, tracked->substate,
                    tracked->x, tracked->y, tracked->z,
                    tracked->animation_record, tracked->health,
                    tracked->source_projectile_reaction_pending);
            }
            if (hit_runtime.pools[0].records[16].active != tracked_active)
            {
                const AvspRound1ActorCore *tracked =
                    &hit_runtime.pools[0].records[16];
                fprintf(stderr,
                    "A180 active edge frame=%u active=%u state=%04x/%04x action=%04x record=%08lx health=%d living=%u progress=%u\n",
                    source_frame, tracked->active, tracked->state,
                    tracked->substate, tracked->source_action,
                    tracked->animation_record, tracked->health,
                    hit_runtime.first_encounter.source_living_count,
                    hit_runtime.first_encounter.source_progress);
                tracked_active = tracked->active;
            }
            if (source_frame >= 2300u && source_frame <= 2420u)
            {
                const AvspRound1ActorCore *tracked =
                    &hit_runtime.pools[0].records[16];
                if (source_frame >= 2373u && source_frame <= 2380u)
                    fprintf(stderr,
                        "A180 RNG window frame=%u state=%04x/%04x hit_timer=%u guard6d=%u rng=%04x\n",
                        source_frame, tracked->state, tracked->substate,
                        tracked->source_hit_action_timer,
                        tracked->source_collision_guard6d,
                        hit_runtime.rng_seed);
                if (tracked->state != tracked_state ||
                    tracked->substate != tracked_substate ||
                    tracked->animation_record != tracked_record ||
                    tracked->animation_index != tracked_animation_index ||
                    tracked->source_hit_recovery_active != tracked_recovery)
                {
                    fprintf(stderr,
                        "A180 transition frame=%u active=%u state=%04x/%04x action=%04x recovery=%u record=%08lx index=%u animation=%u/%d action_timer=%u hit_timer=%u health=%d rng=%04x updates=%lu\n",
                        source_frame, tracked->active, tracked->state,
                        tracked->substate, tracked->source_action,
                        tracked->source_hit_recovery_active,
                        tracked->animation_record,
                        tracked->animation_index,
                        tracked->animation_timer,
                        tracked->animation_branch,
                        tracked->source_action_timer,
                        tracked->source_hit_action_timer,
                        tracked->health, hit_runtime.rng_seed,
                        tracked->handler_updates);
                    tracked_state = tracked->state;
                    tracked_substate = tracked->substate;
                    tracked_record = tracked->animation_record;
                    tracked_animation_index = tracked->animation_index;
                    tracked_recovery =
                        tracked->source_hit_recovery_active;
                }
            }
            if (source_frame == 2072u &&
                !avsp_round1_begin_first_entry(&hit_runtime))
                return 116;
            if (!class1f_slot_a3c0_lifetime_source_frame_valid(
                    &hit_runtime, source_frame) ||
                !player_hit_source_frame_valid(&hit_runtime, source_frame) ||
                !player_hit_type16_source_frame_valid(
                    &hit_runtime, source_frame) ||
                !player_weapon_fractional_latch_source_frame_valid(
                    &hit_runtime, source_frame))
            {
                fprintf(stderr,
                    "Coffee Shop player HIT chronology failed frame=%u state=%04x/%04x xfp=%08lx facing=%u animation=%08lx assembly=%08lx timer=%u branch=%d health=%d hurt=%u active=%u phase=%u invulnerability=%u entries=%lu completions=%lu audio=%lu/%04x type16=%lu/%lu/%lu/%lu/%lu living=%u progress=%u spawn=%u/%u phase19=%u blocked=%u pool12_free=%u\n",
                    source_frame, hit_runtime.player.state,
                    hit_runtime.player.substate,
                    (unsigned long)hit_runtime.player.source_x_fp,
                    hit_runtime.player.facing,
                    hit_runtime.player.animation_record,
                    hit_runtime.player.assembly,
                    hit_runtime.player.animation_timer,
                    hit_runtime.player.animation_branch,
                    hit_runtime.player.health,
                    hit_runtime.player.hurt_selector,
                    hit_runtime.player_hit_active,
                    hit_runtime.player_hit_phase,
                    hit_runtime.player_hit_invulnerability,
                    hit_runtime.player_hit_entries,
                    hit_runtime.player_hit_completions,
                    hit_runtime.player_hit_audio_events,
                    hit_runtime.player_hit_audio_command,
                    hit_runtime.type16_spawn_requests,
                    hit_runtime.type16_allocations,
                    hit_runtime.type16_movement_steps,
                    hit_runtime.type16_collision_writes,
                    hit_runtime.type16_damage_writes,
                    hit_runtime.first_encounter.source_living_count,
                    hit_runtime.first_encounter.source_progress,
                    hit_runtime.first_encounter.source_spawn_timer,
                    hit_runtime.first_encounter.source_spawn_limit,
                    hit_runtime.first_encounter.source_phase_counter,
                    hit_runtime.first_encounter.source_blocked_by_living_count,
                    hit_runtime.pools[0].free_count);
                for (actor_index = 0u;
                     actor_index < hit_runtime.pools[0].capacity;
                     ++actor_index)
                {
                    const AvspRound1ActorCore *actor =
                        &hit_runtime.pools[0].records[actor_index];
                    if (actor->active && actor->actor_class == 0x1f)
                        fprintf(stderr,
                            " class1f index=%u slot=%08lx state=%04x/%04x action=%04x inner=%u timer=%u record=%08lx x=%d z=%d health=%d\n",
                            actor_index, actor->source_slot, actor->state,
                            actor->substate, actor->source_action,
                            actor->source_motion_fields[0],
                            actor->source_action_timer,
                            actor->animation_record, actor->x, actor->z,
                            actor->health);
                }
                return 116;
            }
            hit_runtime.frame = source_frame >= 2040u ?
                source_frame - 2040u : 0u;
            for (source_tick = 1u; source_tick < phase_updates; ++source_tick)
            {
                int player_authority_enabled_at_tick_start =
                    hit_runtime.route_state == 4;
                if (source_tick < source_updates &&
                    hit_runtime.entry.started &&
                    hit_runtime.route_state != 4 &&
                    !avsp_round1_step_first_entry(&hit_runtime))
                    return 116;
                if (hit_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_pre_player_source_differential(
                        &hit_runtime, source_tick < source_updates))
                    return 116;
                if (source_tick < source_updates &&
                    player_authority_enabled_at_tick_start &&
                    hit_runtime.route_state == 4 &&
                    !avsp_round1_step_player(&hit_runtime, input, 0))
                    return 116;
                if (hit_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_post_player_source_differential(
                        &hit_runtime, source_tick < source_updates,
                        source_tick < class02_updates,
                        source_tick < class02_updates))
                    return 116;
            }
            {
                int player_authority_enabled_at_tick_start =
                    hit_runtime.route_state == 4;
                if (source_updates != 0u && hit_runtime.entry.started &&
                    hit_runtime.route_state != 4 &&
                    !avsp_round1_step_first_entry(&hit_runtime))
                    return 116;
                if (phase_updates != 0u &&
                    hit_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_pre_player_source_differential(
                        &hit_runtime, source_updates != 0u))
                    return 116;
                if (source_updates != 0u &&
                    player_authority_enabled_at_tick_start &&
                    hit_runtime.route_state == 4 &&
                    !avsp_round1_step_player(&hit_runtime, input, 0))
                    return 116;
                if (phase_updates != 0u &&
                    hit_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_post_player_source_differential(
                        &hit_runtime, source_updates != 0u,
                        class02_updates != 0u,
                        class02_updates != 0u))
                    return 116;
            }
        }
    }
    {
        AvspRound1Runtime scene_runtime;
        unsigned int source_frame;
        unsigned int actor_index;
        unsigned int source_tick;
        int player_authority_enabled_at_tick_start;
        int inner8_seen = 0;
        avsp_round1_init(&scene_runtime);
        if (avsp_round1_coffee_shop_source_input(2600u) !=
                AVSP_PW_INPUT_RIGHT ||
            avsp_round1_coffee_shop_source_input(2790u) !=
                (AVSP_PW_INPUT_RIGHT | AVSP_ROUND1_INPUT_BUTTON1 |
                 AVSP_PW_INPUT_ATTACK) ||
            avsp_round1_coffee_shop_source_updates(2074u) != 1u ||
            avsp_round1_coffee_shop_source_updates(2075u) != 3u ||
            avsp_round1_coffee_shop_source_updates(2165u) != 4u ||
            avsp_round1_coffee_shop_source_updates(2260u) != 0u ||
            avsp_round1_coffee_shop_source_updates(2265u) != 0u ||
            avsp_round1_coffee_shop_source_updates(2266u) != 1u ||
            avsp_round1_coffee_shop_source_updates(5458u) != 1u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5453u) != 1u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5458u) != 3u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5460u) != 3u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5461u) != 3u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5469u) != 3u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5470u) != 4u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5523u) != 1u ||
            avsp_round1_coffee_shop_scheduler_source_updates(5524u) != 1u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5453u) !=
                1u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5458u) !=
                3u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5468u) !=
                4u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5469u) !=
                3u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5470u) !=
                3u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5484u) !=
                4u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5517u) !=
                4u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5523u) !=
                1u ||
            avsp_round1_coffee_shop_record20_prefix_source_updates(5524u) !=
                0u)
            return 91;
        for (source_frame = 2040u; source_frame <= 5566u; ++source_frame)
        {
            unsigned short input =
                avsp_round1_coffee_shop_source_input(
                    (unsigned short)source_frame);
            unsigned int source_updates =
                avsp_round1_coffee_shop_source_updates(
                    (unsigned short)source_frame);
            unsigned int scheduler_updates =
                avsp_round1_coffee_shop_scheduler_source_updates(
                    (unsigned short)source_frame);
            unsigned int record20_prefix_updates =
                avsp_round1_coffee_shop_record20_prefix_source_updates(
                    (unsigned short)source_frame);
            unsigned int class02_updates =
                avsp_round1_coffee_shop_class02_source_updates(
                    (unsigned short)source_frame);
            unsigned int phase_updates = source_updates > scheduler_updates ?
                source_updates : scheduler_updates;
            if (record20_prefix_updates > phase_updates)
                phase_updates = record20_prefix_updates;
            if (class02_updates > phase_updates)
                phase_updates = class02_updates;
            if (source_frame == 2072u &&
                !avsp_round1_begin_first_entry(&scene_runtime))
                return 90;
            if (source_frame == 2073u &&
                (!scene_runtime.entry.dependencies_seeded ||
                 scene_runtime.scheduler_frames != 1u ||
                 scene_runtime.first_encounter.source_phase_counter != 7u ||
                 scene_runtime.class1f_phase_guard_counter != 7u))
                return 124;
            if ((source_frame == 2679u &&
                 scene_runtime.entry_controller.substate != 0u) ||
                (source_frame == 2680u &&
                 (scene_runtime.entry_controller.substate != 0x0200u ||
                  scene_runtime.first_encounter.source_progress_snapshot != 1u ||
                  scene_runtime.first_encounter.source_camera_bound != 832u)))
            {
                fprintf(stderr,
                    "Coffee Shop controller camera edge failed frame=%u substate=%04x snapshot=%u bound=%u camera=%d previous=%d living=%u\n",
                    source_frame, scene_runtime.entry_controller.substate,
                    scene_runtime.first_encounter.source_progress_snapshot,
                    scene_runtime.first_encounter.source_camera_bound,
                    scene_runtime.camera_x_position,
                    scene_runtime.camera_x_previous,
                    scene_runtime.first_encounter.source_living_count);
                return 117;
            }
            if ((source_frame == 5151u &&
                 (scene_runtime.entry_controller.state != 0x0204u ||
                  scene_runtime.entry_controller.substate != 0x0600u ||
                  scene_runtime.first_encounter.source_progress != 20u ||
                  scene_runtime.first_encounter.source_intro_timer != 0xffffu)) ||
                (source_frame == 5152u &&
                 (scene_runtime.entry_controller.state != 0x0400u ||
                  scene_runtime.entry_controller.substate != 0u ||
                  scene_runtime.first_encounter.source_intro_timer != 300u ||
                  scene_runtime.route_state != 4)))
            {
                fprintf(stderr,
                    "Coffee Shop withdrawal visibility failed frame=%u controller=%04x/%04x progress=%u timer=%u route=%d\n",
                    source_frame, scene_runtime.entry_controller.state,
                    scene_runtime.entry_controller.substate,
                    scene_runtime.first_encounter.source_progress,
                    scene_runtime.first_encounter.source_intro_timer,
                    scene_runtime.route_state);
                return 125;
            }
            if (source_frame == 5155u)
            {
                const AvspRound1ActorCore *scene_clear_actor = 0;
                for (actor_index = 0u;
                     actor_index < scene_runtime.pools[0].capacity;
                     ++actor_index)
                {
                    const AvspRound1ActorCore *candidate =
                        &scene_runtime.pools[0].records[actor_index];
                    if (candidate->source_slot == 0x00ff9f40UL)
                    {
                        scene_clear_actor = candidate;
                        break;
                    }
                }
                if (scene_clear_actor == 0 || !scene_clear_actor->active ||
                    scene_clear_actor->state != 0x0200u ||
                    scene_clear_actor->substate != 0x1e00u ||
                    scene_clear_actor->source_special_latch_ad != 0u ||
                    scene_clear_actor->transition_timer != 0u ||
                    scene_clear_actor->source_direction != 8u ||
                    scene_clear_actor->facing != 0u ||
                    scene_clear_actor->source_x_fp != 0x05a03e00L ||
                    scene_clear_actor->source_y_fp != 0x01174700L ||
                    scene_clear_actor->z != 279 ||
                    scene_clear_actor->animation_record != 0x0012e8a8UL ||
                    scene_clear_actor->animation_timer != 9u ||
                    scene_clear_actor->animation_branch != 0)
                {
                    fprintf(stderr,
                        "Coffee Shop inner-state scene-clear interruption failed frame=%u active=%u state=%04x/%04x latch=%u inner_timer=%u direction=%u facing=%u fp=%08lx/%08lx z=%d animation=%08lx/%u/%d\n",
                        source_frame,
                        scene_clear_actor != 0 ? scene_clear_actor->active : 0u,
                        scene_clear_actor != 0 ? scene_clear_actor->state : 0u,
                        scene_clear_actor != 0 ? scene_clear_actor->substate : 0u,
                        scene_clear_actor != 0 ?
                            scene_clear_actor->source_special_latch_ad : 0u,
                        scene_clear_actor != 0 ?
                            scene_clear_actor->transition_timer : 0u,
                        scene_clear_actor != 0 ?
                            scene_clear_actor->source_direction : 0u,
                        scene_clear_actor != 0 ? scene_clear_actor->facing : 0u,
                        scene_clear_actor != 0 ?
                            (unsigned long)scene_clear_actor->source_x_fp : 0UL,
                        scene_clear_actor != 0 ?
                            (unsigned long)scene_clear_actor->source_y_fp : 0UL,
                        scene_clear_actor != 0 ? scene_clear_actor->z : 0,
                        scene_clear_actor != 0 ?
                            scene_clear_actor->animation_record : 0UL,
                        scene_clear_actor != 0 ?
                            scene_clear_actor->animation_timer : 0u,
                        scene_clear_actor != 0 ?
                            scene_clear_actor->animation_branch : 0);
                    return 135;
                }
            }
            if ((source_frame == 5451u &&
                 (scene_runtime.route_state != 4 ||
                  scene_runtime.entry_controller.state != 0x0400u ||
                  scene_runtime.first_encounter.source_intro_timer != 1u ||
                  scene_runtime.entry.gate81f3 != 0u ||
                  scene_runtime.entry.exit_started != 0u ||
                  scene_runtime.player.state != 0x0200u ||
                  scene_runtime.player.substate != 0x0202u ||
                  scene_runtime.player.source_x_fp != 0x05509000L ||
                  scene_runtime.player.source_y_fp != 0x013fa800L ||
                  scene_runtime.player.animation_record != 0x0015f218UL ||
                  scene_runtime.player.animation_timer != 2u ||
                  scene_runtime.player.animation_branch != 0 ||
                  scene_runtime.player.facing != 1u)) ||
                (source_frame == 5452u &&
                 (scene_runtime.route_state != 4 ||
                  scene_runtime.entry_controller.state != 0x0400u ||
                  scene_runtime.first_encounter.source_intro_timer != 0u ||
                  scene_runtime.entry.gate81f3 != 1u ||
                  scene_runtime.entry.exit_started != 0u ||
                  scene_runtime.player.state != 0x0200u ||
                  scene_runtime.player.substate != 0x0204u ||
                  scene_runtime.player.source_x_fp != 0x05509000L ||
                  scene_runtime.player.source_y_fp != 0x013fa800L ||
                  scene_runtime.player.animation_record != 0x0015f218UL ||
                  scene_runtime.player.animation_timer != 1u ||
                  scene_runtime.player.animation_branch != 0 ||
                  scene_runtime.player.facing != 1u ||
                  scene_runtime.camera_x_upper != 1152)) ||
                (source_frame == 5453u &&
                 (scene_runtime.route_state != 6 ||
                  scene_runtime.entry.gate81f3 != 1u ||
                  scene_runtime.entry.exit_started != 1u ||
                  scene_runtime.player.state != 0x0800u ||
                  scene_runtime.player.substate != 0u ||
                  scene_runtime.player.source_x_fp != 0x05509000L ||
                  scene_runtime.player.source_y_fp != 0x013fa800L ||
                  scene_runtime.player.animation_record != 0x0015f218UL ||
                  scene_runtime.player.animation_timer != 1u ||
                  scene_runtime.player.animation_branch != 0 ||
                  scene_runtime.player.facing != 1u)))
            {
                fprintf(stderr,
                    "Coffee Shop clear-route scheduler handoff failed frame=%u controller=%04x/%04x timer=%u gate81f3=%u route=%d exit=%u player=%04x/%04x fp=%08lx/%08lx anim=%08lx/%u/%d facing=%u camera_upper=%d\n",
                    source_frame, scene_runtime.entry_controller.state,
                    scene_runtime.entry_controller.substate,
                    scene_runtime.first_encounter.source_intro_timer,
                    scene_runtime.entry.gate81f3,
                    scene_runtime.route_state,
                    scene_runtime.entry.exit_started,
                    scene_runtime.player.state,
                    scene_runtime.player.substate,
                    scene_runtime.player.source_x_fp,
                    scene_runtime.player.source_y_fp,
                    scene_runtime.player.animation_record,
                    scene_runtime.player.animation_timer,
                    scene_runtime.player.animation_branch,
                    scene_runtime.player.facing,
                    scene_runtime.camera_x_upper);
                return 126;
            }
            if (source_frame == 5459u)
            {
                const AvspRound1ActorCore *class1f =
                    &scene_runtime.pools[0].records[11];
                const AvspRound1ActorCore *class09 =
                    &scene_runtime.pools[2].records[12];
                if (!class1f->active || class1f->source_slot != 0x00ff9dc0UL ||
                    class1f->animation_record != 0x0012e8fcUL ||
                    class1f->animation_timer != 1u ||
                    !class09->active || class09->source_slot != 0x00ffb480UL ||
                    class09->actor_class != 0x09 ||
                    class09->animation_timer != 1u)
                {
                    fprintf(stderr,
                        "Coffee Shop exit scheduler cadence failed frame=%u class1f=%08lx/%u class09=%08lx/%u\n",
                        source_frame, class1f->animation_record,
                        class1f->animation_timer, class09->animation_record,
                        class09->animation_timer);
                    return 134;
                }
            }
            if (source_frame == 2371u)
            {
                const AvspRound1WeaponProjectileAllocation *child =
                    &scene_runtime.player_weapon_projectiles[3];
                if (!child->active || child->source_slot != 0x8800u ||
                    child->actor_class != 0x04 || child->variant != 2u ||
                    child->state != 0u || child->substate != 0u ||
                    child->animation_record != 0x0003088cUL ||
                    child->assembly != 0x00030b28UL ||
                    child->animation_timer != 1u ||
                    child->animation_branch != (short)-32768)
                {
                    fprintf(stderr,
                        "Coffee Shop fixed-slot retention failed frame=%u active=%u slot=%04x class=%02x variant=%u state=%02x/%02x animation=%08lx assembly=%08lx timer=%u branch=%d\n",
                        source_frame, child->active, child->source_slot,
                        (unsigned int)(unsigned char)child->actor_class,
                        child->variant, child->state, child->substate,
                        child->animation_record, child->assembly,
                        child->animation_timer, child->animation_branch);
                    return 113;
                }
            }
            scene_runtime.frame = source_frame - 2040u;
            for (source_tick = 1u; source_tick < phase_updates;
                 ++source_tick)
            {
                player_authority_enabled_at_tick_start =
                    scene_runtime.route_state == 4;
                if (source_tick < source_updates &&
                    scene_runtime.frame >= 32u &&
                    scene_runtime.route_state != 4 &&
                    !avsp_round1_step_first_entry(&scene_runtime))
                    return 110;
                if (scene_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_pre_player_source_differential(
                        &scene_runtime, source_tick < source_updates))
                    return 112;
                if (source_tick < source_updates &&
                    player_authority_enabled_at_tick_start &&
                    scene_runtime.route_state == 4 &&
                    !avsp_round1_step_player(&scene_runtime, input, 0))
                    return 111;
                if (scene_runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_post_player_source_differential(
                        &scene_runtime, source_tick < scheduler_updates,
                        source_tick < record20_prefix_updates,
                        source_tick < class02_updates))
                    return 112;
            }
            player_authority_enabled_at_tick_start =
                scene_runtime.route_state == 4;
            if (source_updates != 0u && scene_runtime.frame >= 32u &&
                scene_runtime.route_state != 4 &&
                !avsp_round1_step_first_entry(&scene_runtime))
            {
                fprintf(stderr,
                    "Coffee Shop entry validation failed source=%u route=%d player=%04x/%04x action=%u failures=%lu fallback=%lu\n",
                    source_frame, scene_runtime.route_state,
                    scene_runtime.player.state, scene_runtime.player.substate,
                    scene_runtime.player_action.state,
                    scene_runtime.failure_count, scene_runtime.fallback_count);
                return 92;
            }
            if (phase_updates != 0u &&
                scene_runtime.entry.dependencies_seeded &&
                !avsp_round1_step_scheduler_pre_player_source_differential(
                    &scene_runtime, source_updates != 0u))
                return 112;
            if (source_updates != 0u &&
                player_authority_enabled_at_tick_start &&
                scene_runtime.route_state == 4 &&
                !avsp_round1_step_player(&scene_runtime, input, 0))
            {
                fprintf(stderr,
                    "Coffee Shop player failed source=%u input=%04x core=%04x/%04x action=%u weapon=%u weapon_tick=%u weapon_selector=%u cleanup=%u recovery=%u return=%u jump=%u jump_cleanup=%u jump_latch=%u stop=%u player_cleanup=%u locomotion=%u source_action=%u animation=%08lx/%u/%d position=%d/%d action_position=%d/%d health=%d/%d resource=%u recharge=%u weapon_counts=%lu/%lu alloc=%lu release=%lu free=%u air=%lu empty=%lu/%lu/%lu failure=%lu fallback=%lu\n",
                    source_frame, input, scene_runtime.player.state,
                    scene_runtime.player.substate,
                    scene_runtime.player_action.state,
                    scene_runtime.player_weapon_active,
                    scene_runtime.player_weapon_tick,
                    scene_runtime.player_weapon_presentation_selector,
                    scene_runtime.player_weapon_cleanup_pending,
                    scene_runtime.player_weapon_recovery_pending,
                    scene_runtime.player_weapon_return_pending,
                    scene_runtime.player_jump_active,
                    scene_runtime.player_jump_cleanup_pending,
                    scene_runtime.player_jump_airborne_latch,
                    scene_runtime.player_stop_ticks,
                    scene_runtime.player_cleanup_pending,
                    scene_runtime.player_locomotion_action,
                    scene_runtime.player.source_action,
                    scene_runtime.player.animation_record,
                    scene_runtime.player.animation_timer,
                    scene_runtime.player.animation_branch,
                    scene_runtime.player.x, scene_runtime.player.z,
                    scene_runtime.player_action.x,
                    scene_runtime.player_action.lane,
                    scene_runtime.player.health,
                    scene_runtime.player_action.health,
                    scene_runtime.player_resource,
                    scene_runtime.player_resource_recharge,
                    scene_runtime.player_weapon_entries,
                    scene_runtime.player_weapon_completions,
                    scene_runtime.player_weapon_allocations,
                    scene_runtime.player_weapon_projectile_releases,
                    scene_runtime.player_weapon_projectile_free_count,
                    scene_runtime.player_air_weapon_entries,
                    scene_runtime.player_weapon_empty_auxiliary_requests,
                    scene_runtime.player_weapon_empty_auxiliary_allocations,
                    scene_runtime.player_weapon_empty_auxiliary_allocation_failures,
                    scene_runtime.failure_count,
                    scene_runtime.fallback_count);
                fprintf(stderr,
                    "Coffee Shop camera=%d/%d target=%d/%d scroll2=%d bounds=%d/%d active=%u lower=%d/%d upper=%d/%d terminal=%u control=%u gate=%u decrements=%u step=%u failures=%lu\n",
                    scene_runtime.camera_x_position,
                    scene_runtime.camera_z_position,
                    scene_runtime.camera_x_target,
                    scene_runtime.camera_z_target,
                    scene_runtime.camera_scroll2_x,
                    scene_runtime.navigation_bound_x,
                    scene_runtime.navigation_bound_z,
                    scene_runtime.navigation_bounds_active,
                    scene_runtime.camera_x_lower,
                    scene_runtime.camera_z_lower,
                    scene_runtime.camera_x_upper,
                    scene_runtime.camera_z_upper,
                    scene_runtime.entry.terminal_seen,
                    scene_runtime.entry.control_enabled,
                    scene_runtime.entry.gate8236,
                    scene_runtime.entry.timer_decrements,
                    scene_runtime.entry.step_index,
                    scene_runtime.failure_count);
                fprintf(stderr,
                    "Coffee Shop pool0 free=%u source_living=%u class1f_releases=%lu controller=%04x progress=%u timer=%u\n",
                    scene_runtime.pools[0].free_count,
                    scene_runtime.first_encounter.source_living_count,
                    scene_runtime.class1f_action_releases,
                    scene_runtime.entry_controller.state,
                    scene_runtime.first_encounter.source_progress,
                    scene_runtime.first_encounter.source_spawn_timer);
                fprintf(stderr,
                    "Coffee Shop debits=%lu entries_plus_air=%lu empty_release=%lu air_effect=%lu/%lu/%lu/%lu completions=%lu entries=%lu jump_counts=%lu/%lu/%lu canaries=%08lx/%08lx\n",
                    scene_runtime.player_weapon_resource_debits,
                    scene_runtime.player_weapon_entries +
                        scene_runtime.player_air_weapon_entries,
                    scene_runtime.player_weapon_empty_auxiliary_releases,
                    scene_runtime.player_air_weapon_effect_requests,
                    scene_runtime.player_air_weapon_effect_allocations,
                    scene_runtime.player_air_weapon_effect_allocation_failures,
                    scene_runtime.player_air_weapon_effect_releases,
                    scene_runtime.player_weapon_completions,
                    scene_runtime.player_weapon_entries,
                    scene_runtime.player_jump_entries,
                    scene_runtime.player_jump_completions,
                    scene_runtime.player_jump_interruptions,
                    scene_runtime.head_canary,
                    scene_runtime.tail_canary);
                return 93;
            }
            if (source_frame == 4051u &&
                (scene_runtime.player_weapon_stage_progress_pending != 1u ||
                 scene_runtime.player_weapon_stage_progress_applied != 0u ||
                 scene_runtime.player_stage_progress_calls != 9u ||
                 scene_runtime.source_stage_progress_accumulator != 3u ||
                 scene_runtime.player_weapon_active != 1u ||
                 scene_runtime.player_weapon_tick != 1u ||
                 scene_runtime.player_weapon_dispatch_delay != 0u ||
                 scene_runtime.player_hit_interaction_active != 0u ||
                 scene_runtime.player_hit_interaction_input_pending != 0u))
            {
                fprintf(stderr,
                    "Coffee Shop HIT-interruption pending witness failed source=%u pending=%u applied=%u calls=%lu progress=%u weapon=%u tick=%u delay=%u interaction=%u input_pending=%u\n",
                    source_frame,
                    scene_runtime.player_weapon_stage_progress_pending,
                    scene_runtime.player_weapon_stage_progress_applied,
                    scene_runtime.player_stage_progress_calls,
                    scene_runtime.source_stage_progress_accumulator,
                    scene_runtime.player_weapon_active,
                    scene_runtime.player_weapon_tick,
                    scene_runtime.player_weapon_dispatch_delay,
                    scene_runtime.player_hit_interaction_active,
                    scene_runtime.player_hit_interaction_input_pending);
                return 127;
            }
            if (source_frame == 3578u &&
                scene_runtime.player.source_y_fp != 0x013f3800L)
            {
                fprintf(stderr,
                    "Coffee Shop player terrain fixed-point sync failed source=%u yfp=%08lx z=%d\n",
                    source_frame, scene_runtime.player.source_y_fp,
                    scene_runtime.player.z);
                return 131;
            }
            if (source_frame == 3772u &&
                scene_runtime.player.source_y_fp != 0x013f3800L)
            {
                fprintf(stderr,
                    "Coffee Shop player HIT fixed-point carry failed source=%u yfp=%08lx z=%d\n",
                    source_frame, scene_runtime.player.source_y_fp,
                    scene_runtime.player.z);
                return 132;
            }
            if (source_frame == 3879u &&
                (scene_runtime.player.source_x_fp != 0x0550f000L ||
                 scene_runtime.player.source_y_fp != 0x013f3800L))
            {
                fprintf(stderr,
                    "Coffee Shop player special-entry fixed-point carry failed source=%u xfp=%08lx yfp=%08lx\n",
                    source_frame, scene_runtime.player.source_x_fp,
                    scene_runtime.player.source_y_fp);
                return 133;
            }
            if (source_frame == 3606u)
            {
                const AvspRound1ActorCore *reused_actor =
                    &scene_runtime.pools[0].records[18];
                if (!reused_actor->active ||
                    reused_actor->source_slot != 0x00ffa300UL ||
                    reused_actor->actor_class != 0x1f ||
                    reused_actor->variant != 5u ||
                    reused_actor->state != 0u ||
                    reused_actor->substate != 0u ||
                    reused_actor->source_x_fp != 0x04500000L ||
                    reused_actor->source_y_fp != 0x01500000L ||
                    reused_actor->z != 336 ||
                    reused_actor->facing != 0u ||
                    reused_actor->animation_record != 0x0012e7ccUL ||
                    reused_actor->assembly != 0x0012f82cUL ||
                    reused_actor->animation_timer != 2u ||
                    reused_actor->animation_branch != 8 ||
                    reused_actor->health != 87 ||
                    reused_actor->hurt_selector != 2u ||
                    reused_actor->attack_selector != 0u)
                {
                    fprintf(stderr,
                        "Coffee Shop class01 fixed-slot reuse failed source=%u active=%u slot=%08lx class=%02x variant=%u state=%04x/%04x fp=%08lx/%08lx z=%d facing=%u anim=%08lx assembly=%08lx timer=%u branch=%d health=%d hurt=%u attack=%u\n",
                        source_frame, reused_actor->active,
                        reused_actor->source_slot,
                        (unsigned int)(unsigned char)
                            reused_actor->actor_class,
                        reused_actor->variant, reused_actor->state,
                        reused_actor->substate,
                        reused_actor->source_x_fp,
                        reused_actor->source_y_fp, reused_actor->z,
                        reused_actor->facing,
                        reused_actor->animation_record,
                        reused_actor->assembly,
                        reused_actor->animation_timer,
                        reused_actor->animation_branch,
                        reused_actor->health,
                        reused_actor->hurt_selector,
                        reused_actor->attack_selector);
                    return 130;
                }
            }
            if (phase_updates != 0u &&
                scene_runtime.entry.dependencies_seeded)
            {
                if (!avsp_round1_step_scheduler_post_player_source_differential(
                        &scene_runtime, scheduler_updates != 0u,
                        record20_prefix_updates != 0u,
                        class02_updates != 0u))
                {
                    const AvspRound1ActorCore *failed_actor = 0;
                    for (actor_index = 0u;
                         actor_index < scene_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[0].records[actor_index];
                        if ((unsigned short)candidate->source_slot ==
                                scene_runtime.scheduler_failure_source_slot)
                        {
                            failed_actor = candidate;
                            break;
                        }
                    }
                    fprintf(stderr,
                        "Coffee Shop scheduler failure source=%u code=%u slot=%04x state=%04x substate=%04x record=%08lx frame=%lu action_timer=%u animation_timer=%u branch=%d plan=%d cursor=%d selector=%d selector_phase=%d field95=%u guard=%u style=%u audio=%04x/%lu action0c=%lu/%lu/%lu stage=%u progress=%u stage_calls=%lu stage_carries=%lu weapon_entries=%lu rng=%04x\n",
                        source_frame,
                        scene_runtime.scheduler_failure_code,
                        scene_runtime.scheduler_failure_source_slot,
                        scene_runtime.scheduler_failure_state,
                        scene_runtime.scheduler_failure_substate,
                        scene_runtime.scheduler_failure_animation_record,
                        scene_runtime.scheduler_frames,
                        failed_actor != 0 ?
                            failed_actor->source_action_timer : 0u,
                        failed_actor != 0 ? failed_actor->animation_timer : 0u,
                        failed_actor != 0 ? failed_actor->animation_branch : 0,
                        failed_actor != 0 ?
                            failed_actor->source_action0c_plan : 0,
                        failed_actor != 0 ?
                            failed_actor->source_action0c_cursor : 0,
                        failed_actor != 0 ?
                            failed_actor->source_action0c_selector : 0,
                        failed_actor != 0 ?
                            failed_actor->source_action0c_selector_phase : 0,
                        failed_actor != 0 ?
                            failed_actor->source_action0c_field95 : 0u,
                        failed_actor != 0 ?
                            failed_actor->source_player_guard : 0u,
                        failed_actor != 0 ? failed_actor->source_style85 : 0u,
                        scene_runtime.class1f_audio_command,
                        scene_runtime.class1f_audio_events,
                        scene_runtime.class1f_action0c_entries,
                        scene_runtime.class1f_action0c_plan_bindings,
                        scene_runtime.class1f_action0c_timer_rng_calls,
                        scene_runtime.source_stage_parameter,
                        scene_runtime.source_stage_progress_accumulator,
                        scene_runtime.player_stage_progress_calls,
                        scene_runtime.player_stage_progress_carries,
                        scene_runtime.player_weapon_entries,
                        scene_runtime.rng_seed);
                    return 94;
                }
                /* The post-update state for frame 5207 is the source row at 5208. */
                if (source_frame == 5207u)
                {
                    const AvspRound1ActorCore *scene_exit_actor = 0;
                    for (actor_index = 0u;
                         actor_index < scene_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[0].records[actor_index];
                        if (candidate->source_slot == 0x00ffa240UL)
                        {
                            scene_exit_actor = candidate;
                            break;
                        }
                    }
                    if (scene_runtime.coffee_scene_active_flag != 0u ||
                        scene_exit_actor == 0 ||
                        scene_exit_actor->active == 0u ||
                        scene_exit_actor->state != 0x020au ||
                        scene_exit_actor->substate != 0u ||
                        scene_exit_actor->animation_record != 0x0012e8ecUL ||
                        scene_exit_actor->animation_timer != 9u ||
                        scene_exit_actor->animation_branch != 0 ||
                        scene_exit_actor->facing != 1u ||
                        scene_exit_actor->health != 87 ||
                        scene_exit_actor->source_x_fp != 0x042f9200UL ||
                        scene_exit_actor->source_y_fp != 0x0130b300UL ||
                        scene_exit_actor->z != 304)
                    {
                        fprintf(stderr,
                            "Coffee Shop class1f scene-active transition failed source=%u flag=%u active=%u state=%04x/%04x anim=%08lx timer=%u branch=%d facing=%u health=%d fp=%08lx/%08lx z=%d\n",
                            source_frame,
                            scene_runtime.coffee_scene_active_flag,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->active : 0u,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->state : 0u,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->substate : 0u,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->animation_record : 0UL,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->animation_timer : 0u,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->animation_branch : 0,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->facing : 0u,
                            scene_exit_actor != 0 ?
                                scene_exit_actor->health : 0,
                            scene_exit_actor != 0 ?
                                (unsigned long)scene_exit_actor->source_x_fp : 0UL,
                            scene_exit_actor != 0 ?
                                (unsigned long)scene_exit_actor->source_y_fp : 0UL,
                            scene_exit_actor != 0 ? scene_exit_actor->z : 0);
                        return 134;
                    }
                }
                if (source_frame == 5523u)
                {
                    const AvspRound1ActorCore *interrupted_actor = 0;
                    for (actor_index = 0u;
                         actor_index < scene_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[0].records[actor_index];
                        if (candidate->source_slot == 0x00ff9dc0UL)
                        {
                            interrupted_actor = candidate;
                            break;
                        }
                    }
                    if (scene_runtime.route_state != 0 ||
                        interrupted_actor == 0 ||
                        interrupted_actor->state != 0x020au)
                    {
                        fprintf(stderr,
                            "Coffee Shop class1f state-0 interruption failed source=%u route=%d active=%u state=%04x/%04x anim=%08lx facing=%u\n",
                            source_frame, scene_runtime.route_state,
                            interrupted_actor != 0 ?
                                interrupted_actor->active : 0u,
                            interrupted_actor != 0 ?
                                interrupted_actor->state : 0u,
                            interrupted_actor != 0 ?
                                interrupted_actor->substate : 0u,
                            interrupted_actor != 0 ?
                                interrupted_actor->animation_record : 0UL,
                            interrupted_actor != 0 ?
                                interrupted_actor->facing : 0u);
                        return 126;
                    }
                }
                if (source_frame == 5461u)
                {
                    const AvspRound1ActorCore *tail_actor = 0;
                    for (actor_index = 0u;
                         actor_index < scene_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[0].records[actor_index];
                        if (candidate->source_slot == 0x00ff9f40UL)
                        {
                            tail_actor = candidate;
                            break;
                        }
                    }
                    if (tail_actor == 0 || tail_actor->active == 0u ||
                        tail_actor->state != 0x020au ||
                        tail_actor->substate != 0u ||
                        tail_actor->animation_record != 0x0012e8a8UL ||
                        tail_actor->animation_timer != 8u ||
                        tail_actor->animation_branch != 0 ||
                        tail_actor->facing != 1u ||
                        tail_actor->health != 87 ||
                        tail_actor->source_x_fp != 0x05a03e00UL ||
                        tail_actor->source_y_fp != 0x01174700UL ||
                        tail_actor->z != 279)
                    {
                        fprintf(stderr,
                            "Coffee Shop class1f route-interruption tail failed source=%u active=%u state=%04x/%04x anim=%08lx timer=%u branch=%d facing=%u health=%d fp=%08lx/%08lx z=%d\n",
                            source_frame,
                            tail_actor != 0 ? tail_actor->active : 0u,
                            tail_actor != 0 ? tail_actor->state : 0u,
                            tail_actor != 0 ? tail_actor->substate : 0u,
                            tail_actor != 0 ?
                                tail_actor->animation_record : 0UL,
                            tail_actor != 0 ?
                                tail_actor->animation_timer : 0u,
                            tail_actor != 0 ?
                                tail_actor->animation_branch : 0,
                            tail_actor != 0 ? tail_actor->facing : 0u,
                            tail_actor != 0 ? tail_actor->health : 0,
                            tail_actor != 0 ?
                                (unsigned long)tail_actor->source_x_fp : 0UL,
                            tail_actor != 0 ?
                                (unsigned long)tail_actor->source_y_fp : 0UL,
                            tail_actor != 0 ? tail_actor->z : 0);
                        return 136;
                    }
                }
                if ((source_frame == 5563u &&
                     (scene_runtime.route_state != 2 ||
                      scene_runtime.player.source_x_fp != 0x059d9200L ||
                      scene_runtime.player.source_y_fp != 0x0118d000L ||
                      scene_runtime.player.z != 280 ||
                      scene_runtime.player.facing != 1u ||
                      scene_runtime.camera_x_position != 0 ||
                      scene_runtime.camera_z_position != 0 ||
                      scene_runtime.camera_x_target != 128 ||
                      scene_runtime.entry_controller.active != 0u)) ||
                    ((source_frame == 5564u || source_frame == 5565u) &&
                     (scene_runtime.route_state != 2 ||
                      scene_runtime.player.state != 0x0800u ||
                      scene_runtime.player.substate != 0u ||
                      scene_runtime.player.source_x_fp != 0x04009200L ||
                      scene_runtime.player.source_y_fp != 0x0120d000L ||
                      scene_runtime.player.x != 1024 ||
                      scene_runtime.player.y != 288 ||
                      scene_runtime.player.z != 288 ||
                      scene_runtime.player.facing != 1u ||
                      scene_runtime.camera_x_position != 776 ||
                      scene_runtime.camera_z_position != 224 ||
                      scene_runtime.camera_x_target != 776 ||
                      scene_runtime.entry_controller.active != 0u)) ||
                    (source_frame == 5566u &&
                     (scene_runtime.route_state != 2 ||
                      scene_runtime.player.source_x_fp != 0x04009200L ||
                      scene_runtime.player.source_y_fp != 0x0120d000L ||
                      scene_runtime.player.z != 288 ||
                      scene_runtime.player.facing != 0u ||
                      scene_runtime.entry_controller.active != 1u ||
                      scene_runtime.entry_controller.state != 0x0200u ||
                      scene_runtime.entry_controller.substate != 0u)))
                {
                    fprintf(stderr,
                        "Coffee Shop next-entry reinitialization failed source=%u route=%d player=%04x/%04x fp=%08lx/%08lx xyz=%d/%d/%d facing=%u camera=%d/%d target=%d controller=%u/%04x/%04x\n",
                        source_frame, scene_runtime.route_state,
                        scene_runtime.player.state,
                        scene_runtime.player.substate,
                        scene_runtime.player.source_x_fp,
                        scene_runtime.player.source_y_fp,
                        scene_runtime.player.x, scene_runtime.player.y,
                        scene_runtime.player.z,
                        scene_runtime.player.facing,
                        scene_runtime.camera_x_position,
                        scene_runtime.camera_z_position,
                        scene_runtime.camera_x_target,
                        scene_runtime.entry_controller.active,
                        scene_runtime.entry_controller.state,
                        scene_runtime.entry_controller.substate);
                    return 135;
                }
                for (actor_index = 0u;
                     actor_index < scene_runtime.pools[0].capacity;
                     ++actor_index)
                {
                    const AvspRound1ActorCore *actor =
                        &scene_runtime.pools[0].records[actor_index];
                    if (actor->active && actor->actor_class == 0x1f &&
                        actor->state == 0x0208u)
                        inner8_seen = 1;
                }
                if (source_frame == 4034u &&
                    scene_runtime.class1f_audio_command != 0x003du)
                {
                    fprintf(stderr,
                        "Coffee Shop HIT-interaction audio witness failed source=%u command=%04x events=%lu\n",
                        source_frame,
                        scene_runtime.class1f_audio_command,
                        scene_runtime.class1f_audio_events);
                    return 129;
                }
                if (source_frame == 3830u)
                {
                    const AvspRound1ActorCore *reaction_target = 0;
                    for (actor_index = 0u;
                         actor_index < scene_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[0].records[actor_index];
                        if (candidate->source_slot == 0x00ffa000UL)
                        {
                            reaction_target = candidate;
                            break;
                        }
                    }
                    if (reaction_target == 0 || !reaction_target->active ||
                        reaction_target->state != 0x0402u ||
                        reaction_target->health != -1 ||
                        reaction_target->source_facing_selector != 1u ||
                        reaction_target->facing != 0u)
                    {
                        fprintf(stderr,
                            "Coffee Shop collision reaction-facing failed source=%u active=%u state=%04x health=%d reaction=%u facing=%u\n",
                            source_frame,
                            reaction_target != 0 ? reaction_target->active : 0u,
                            reaction_target != 0 ? reaction_target->state : 0u,
                            reaction_target != 0 ? reaction_target->health : 0,
                            reaction_target != 0 ?
                                reaction_target->source_facing_selector : 0u,
                            reaction_target != 0 ? reaction_target->facing : 0u);
                        return 124;
                    }
                }
                if (source_frame == 3881u)
                {
                    const AvspRound1ActorCore *timeout_actor = 0;
                    for (actor_index = 0u;
                         actor_index < scene_runtime.pools[0].capacity;
                         ++actor_index)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[0].records[actor_index];
                        if (candidate->source_slot == 0x00ffa3c0UL)
                        {
                            timeout_actor = candidate;
                            break;
                        }
                    }
                    if (timeout_actor == 0 || !timeout_actor->active ||
                        timeout_actor->state != 0x0200u ||
                        timeout_actor->substate != 0x0800u ||
                        timeout_actor->transition_timer != 0u ||
                        timeout_actor->source_special_latch_ad != 0u ||
                        timeout_actor->source_x_fp != 0x04530300L ||
                        timeout_actor->source_y_fp != 0x0134bb00L ||
                        timeout_actor->z != 309 || timeout_actor->facing != 1u ||
                        timeout_actor->animation_record != 0x0012e65cUL)
                    {
                        fprintf(stderr,
                            "Coffee Shop inner timeout return failed source=%u active=%u state=%04x/%04x timer=%u latch=%u fp=%08lx/%08lx z=%d facing=%u anim=%08lx\n",
                            source_frame,
                            timeout_actor != 0 ? timeout_actor->active : 0u,
                            timeout_actor != 0 ? timeout_actor->state : 0u,
                            timeout_actor != 0 ? timeout_actor->substate : 0u,
                            timeout_actor != 0 ?
                                timeout_actor->transition_timer : 0u,
                            timeout_actor != 0 ?
                                timeout_actor->source_special_latch_ad : 0u,
                            timeout_actor != 0 ?
                                timeout_actor->source_x_fp : 0L,
                            timeout_actor != 0 ?
                                timeout_actor->source_y_fp : 0L,
                            timeout_actor != 0 ? timeout_actor->z : 0,
                            timeout_actor != 0 ? timeout_actor->facing : 0u,
                            timeout_actor != 0 ?
                                timeout_actor->animation_record : 0UL);
                        return 125;
                    }
                }
            }
            if (source_frame == 2750u || source_frame == 3263u ||
                source_frame == 3771u || source_frame == 3855u ||
                source_frame == 4006u || source_frame == 4007u ||
                source_frame == 4032u || source_frame == 4052u)
            {
                const AvspRound1ActorCore *attack_actor = 0;
                unsigned long wanted_slot = source_frame >= 4006u ?
                    0x00ff9dc0UL : source_frame >= 3855u ?
                    0x00ffad00UL : source_frame >= 3771u ?
                    0x00ffa000UL : source_frame >= 3263u ?
                    0x00ffae00UL : 0x00ffa240UL;
                unsigned int pool_i;
                for (pool_i = 0u; pool_i < AVSP_ROUND1_POOL_COUNT;
                     ++pool_i)
                {
                    unsigned int slot_i;
                    for (slot_i = 0u;
                         slot_i < scene_runtime.pools[pool_i].capacity;
                         ++slot_i)
                    {
                        const AvspRound1ActorCore *candidate =
                            &scene_runtime.pools[pool_i].records[slot_i];
                        if (candidate->source_slot == wanted_slot)
                            attack_actor = candidate;
                    }
                }
                fprintf(stderr,
                    "player_hit_scene_probe frame=%u player=%04x/%04x x=%d z=%d facing=%u anim=%08lx timer=%u health=%d hurt=%u input=%04x hit=%u/%u reaction=%u entries=%lu completions=%lu collision=%lu damage=%lu pending=%u actor=%08lx active=%u type=%u class=%02x state=%04x/%04x x=%d z=%d facing=%u anim=%08lx attack=%u field01=%u hitstop=%u guard=%u latch=%u xvel=%ld yvel=%ld recovery=%u projectile_pending=%u\n",
                    source_frame, scene_runtime.player.state,
                    scene_runtime.player.substate,
                    scene_runtime.player.x, scene_runtime.player.z,
                    scene_runtime.player.facing,
                    scene_runtime.player.animation_record,
                    scene_runtime.player.animation_timer,
                    scene_runtime.player_action.health,
                    scene_runtime.player.hurt_selector, input,
                    scene_runtime.player_hit_active,
                    scene_runtime.player_hit_phase,
                    scene_runtime.player_hit_reaction_index,
                    scene_runtime.player_hit_entries,
                    scene_runtime.player_hit_completions,
                    scene_runtime.class1f_player_collision_writes +
                        scene_runtime.type16_collision_writes,
                    scene_runtime.class1f_player_damage_writes +
                        scene_runtime.type16_damage_writes,
                    scene_runtime.first_encounter.pending_player_damage,
                    attack_actor != 0 ? attack_actor->source_slot : 0UL,
                    attack_actor != 0 ? attack_actor->active : 0u,
                    attack_actor != 0 ? attack_actor->type : 0u,
                    attack_actor != 0 ?
                        (unsigned int)(unsigned char)
                            attack_actor->actor_class : 0u,
                    attack_actor != 0 ? attack_actor->state : 0u,
                    attack_actor != 0 ? attack_actor->substate : 0u,
                    attack_actor != 0 ? attack_actor->x : 0,
                    attack_actor != 0 ? attack_actor->z : 0,
                    attack_actor != 0 ? attack_actor->facing : 0u,
                    attack_actor != 0 ?
                        attack_actor->animation_record : 0UL,
                    attack_actor != 0 ? attack_actor->attack_selector : 0u,
                    attack_actor != 0 ? attack_actor->source_field01 : 0u,
                    attack_actor != 0 ? attack_actor->source_hitstop : 0u,
                    attack_actor != 0 ?
                        attack_actor->source_player_guard : 0u,
                    attack_actor != 0 ?
                        attack_actor->source_player_collision_latched : 0u,
                    attack_actor != 0 ?
                        attack_actor->source_x_velocity : 0L,
                    attack_actor != 0 ?
                        attack_actor->source_y_velocity : 0L,
                    attack_actor != 0 ?
                        (unsigned int)attack_actor->source_hit_recovery_active :
                        0u,
                    attack_actor != 0 ?
                        attack_actor->source_projectile_reaction_pending : 0u);
                if (source_frame == 4052u &&
                    (attack_actor == 0 || !attack_actor->active ||
                     attack_actor->state != 0x0202u ||
                     attack_actor->substate != 0x0202u ||
                     attack_actor->source_hit_recovery_active != 4u ||
                     attack_actor->source_projectile_reaction_pending != 0u ||
                     attack_actor->source_x_velocity != -0x00030000L ||
                     attack_actor->source_y_velocity != 0x00032000L ||
                     attack_actor->animation_record != 0x0012dd78UL))
                {
                    fprintf(stderr,
                        "Coffee Shop HIT-interaction launch witness failed source=%u state=%04x/%04x recovery=%u pending=%u velocity=%ld/%ld animation=%08lx\n",
                        source_frame,
                        attack_actor != 0 ? attack_actor->state : 0u,
                        attack_actor != 0 ? attack_actor->substate : 0u,
                        attack_actor != 0 ?
                            (unsigned int)
                                attack_actor->source_hit_recovery_active : 0u,
                        attack_actor != 0 ?
                            attack_actor->source_projectile_reaction_pending :
                            0u,
                        attack_actor != 0 ?
                            attack_actor->source_x_velocity : 0L,
                        attack_actor != 0 ?
                            attack_actor->source_y_velocity : 0L,
                        attack_actor != 0 ?
                            attack_actor->animation_record : 0UL);
                    return 128;
                }
            }
            if (source_frame == 3827u || source_frame == 3830u ||
                source_frame == 3850u || source_frame == 3875u ||
                source_frame == 3900u || source_frame == 3925u ||
                source_frame == 3950u || source_frame == 3975u ||
                source_frame == 3987u || source_frame == 4002u ||
                source_frame == 4006u)
            {
                unsigned int slot_i;
                for (slot_i = 0u;
                     slot_i < scene_runtime.pools[0].capacity; ++slot_i)
                {
                    const AvspRound1ActorCore *actor =
                        &scene_runtime.pools[0].records[slot_i];
                    if (actor->source_slot != 0x00ffa000UL &&
                        actor->source_slot != 0x00ff9dc0UL)
                        continue;
                    fprintf(stderr,
                        "class1f_post_action0c_probe frame=%u slot=%04x state=%04x/%04x xfp=%08lx yfp=%08lx z=%d facing=%u anim=%08lx timer=%u branch=%d attack=%u plan=%d cursor=%d selector=%d phase=%d action_timer=%u rng=%04x\n",
                        source_frame, (unsigned short)actor->source_slot,
                        actor->state, actor->substate,
                        (unsigned long)actor->source_x_fp,
                        (unsigned long)actor->source_y_fp,
                        actor->z, actor->facing,
                        actor->animation_record, actor->animation_timer,
                        actor->animation_branch, actor->attack_selector,
                        actor->source_action0c_plan,
                        actor->source_action0c_cursor,
                        actor->source_action0c_selector,
                        actor->source_action0c_selector_phase,
                        actor->source_action_timer,
                        scene_runtime.rng_seed);
                }
            }
            if (scene_runtime.player_stage_progress_calls !=
                    source_stage_progress_call_count(source_frame))
            {
                fprintf(stderr,
                    "Coffee Shop stage-progress chronology failed source=%u expected_calls=%lu native_calls=%lu input=%04x source_updates=%u class02_updates=%u weapon_active=%u weapon_empty=%u weapon_tick=%u weapon_entries=%lu weapon_completions=%lu cleanup=%u recovery=%u return=%u source_action=%04x pipeline=%u previous=%u progress=%u stage=%u hit=%u/%u reaction=%u kind=%u presentation=%u shake=%u xvel=%ld xacc=%ld entries=%lu completions=%lu player=%04x/%04x anim=%08lx timer=%u facing=%u health=%d invuln=%u\n",
                    source_frame,
                    source_stage_progress_call_count(source_frame),
                    scene_runtime.player_stage_progress_calls,
                    input, source_updates, class02_updates,
                    scene_runtime.player_weapon_active,
                    scene_runtime.player_weapon_empty,
                    scene_runtime.player_weapon_tick,
                    scene_runtime.player_weapon_entries,
                    scene_runtime.player_weapon_completions,
                    scene_runtime.player_weapon_cleanup_pending,
                    scene_runtime.player_weapon_recovery_pending,
                    scene_runtime.player_weapon_return_pending,
                    scene_runtime.player.source_action,
                    scene_runtime.player_weapon_input_pipeline,
                    scene_runtime.player_weapon_previous_pressed,
                    scene_runtime.source_stage_progress_accumulator,
                    scene_runtime.source_stage_parameter,
                    scene_runtime.player_hit_active,
                    scene_runtime.player_hit_phase,
                    scene_runtime.player_hit_reaction_index,
                    scene_runtime.player_hit_kind,
                    scene_runtime.player_hit_presentation_selector,
                    scene_runtime.player_hit_shake_remaining,
                    scene_runtime.player_hit_x_velocity,
                    scene_runtime.player_hit_x_acceleration,
                    scene_runtime.player_hit_entries,
                    scene_runtime.player_hit_completions,
                    scene_runtime.player.state,
                    scene_runtime.player.substate,
                    scene_runtime.player.animation_record,
                    scene_runtime.player.animation_timer,
                    scene_runtime.player.facing,
                    scene_runtime.player_action.health,
                    scene_runtime.player_hit_invulnerability);
                return 123;
            }
            if (source_frame == 2793u &&
                (scene_runtime.player.animation_record != 0x0015fd10UL ||
                 scene_runtime.player.animation_timer != 3u ||
                 scene_runtime.player.animation_branch != 1 ||
                 scene_runtime.player.hurt_selector != 0u ||
                 scene_runtime.player.attack_selector != 0u))
                return 118;
            if (source_frame == 2074u &&
                (scene_runtime.pools[2].records[15].source_slot !=
                     0x00ffb600UL ||
                 scene_runtime.pools[2].records[15].actor_class != 0x02 ||
                  scene_runtime.pools[2].records[15].animation_record !=
                      0x0006b66cUL ||
                  scene_runtime.pools[2].records[15].animation_timer !=
                      4093u))
                return 119;
            if (source_frame == 2238u &&
                (scene_runtime.player.animation_record != 0x0015f1f4UL ||
                 scene_runtime.player.animation_timer != 4094u ||
                 scene_runtime.player.animation_branch != (short)-32768))
            {
                fprintf(stderr,
                    "Coffee Shop player idle animation failed frame=%u record=%08lx timer=%u branch=%d updates=%u\n",
                    source_frame, scene_runtime.player.animation_record,
                    scene_runtime.player.animation_timer,
                    scene_runtime.player.animation_branch, source_updates);
                return 120;
            }
            if (source_frame == 2246u &&
                (scene_runtime.pools[2].records[10].source_slot !=
                     0x00ffb380UL ||
                 scene_runtime.pools[2].records[10].actor_class != 0x0a ||
                 scene_runtime.pools[2].records[10].animation_record !=
                      0x0006e136UL ||
                  scene_runtime.pools[2].records[10].animation_timer !=
                      4094u))
                return 121;
            if (!avsp_round1_step_coffee_exit_display(&scene_runtime))
                return 136;
        }
        if (scene_runtime.coffee_shop_obstacle_rng_calls != 1u ||
            scene_runtime.coffee_shop_obstacle_audio_events != 1u ||
            scene_runtime.coffee_shop_obstacle_audio_command != 0x0142u)
        {
            fprintf(stderr,
                "Coffee Shop obstacle break side effects failed rng=%lu audio=%lu command=%04x\n",
                scene_runtime.coffee_shop_obstacle_rng_calls,
                scene_runtime.coffee_shop_obstacle_audio_events,
                scene_runtime.coffee_shop_obstacle_audio_command);
            return 122;
        }
        if (!scene_runtime.first_encounter.initialized)
        {
            fprintf(stderr,
                "Coffee Shop ledger did not reach encounter: route=%d living=%u free=%u progress=%u timer=%u controller=%04x blocked=%u releases=%lu contacts=%lu ko=%lu\n",
                scene_runtime.route_state,
                scene_runtime.first_encounter.source_living_count,
                scene_runtime.pools[0].free_count,
                scene_runtime.first_encounter.source_progress,
                scene_runtime.first_encounter.source_spawn_timer,
                scene_runtime.entry_controller.state,
                scene_runtime.first_encounter.source_blocked_by_living_count,
                scene_runtime.class1f_action_releases,
                scene_runtime.first_encounter.player_contacts,
                scene_runtime.first_encounter.ko_events);
            return 95;
        }
        if (!inner8_seen)
        {
            fprintf(stderr,
                "Coffee Shop inner8 source state was never observed type16=%lu\n",
                scene_runtime.type16_spawn_requests);
            return 108;
        }
    }
    runtime.entry.gate8236 = 1u;
    if (avsp_round1_entry_valid(&runtime))
        return 49;
    puts("REIMPLEMENT-13 native entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Predator-Button1-parent-child-damage: PASS");
    return 0;
}
