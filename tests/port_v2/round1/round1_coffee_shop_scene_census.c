#include <stdio.h>

#include "round1.h"

static void emit_actor(unsigned int frame, const char *pool,
                       const AvspRound1ActorCore *actor)
{
    long x_fp;
    long y_fp;
    unsigned short source_state;
    if (actor->active == 0u)
        return;
    x_fp = actor->actor_class == 0x45 ? (long)actor->x * 65536L :
        actor->source_x_fp != 0L ? actor->source_x_fp :
        (long)actor->x * 65536L;
    y_fp = actor->actor_class == 0x45 ? (long)actor->y * 65536L :
        actor->source_y_fp != 0L ? actor->source_y_fp :
        (long)actor->y * 65536L;
    source_state = actor->state;
    if (actor->type == 24u &&
        (actor->actor_class == 0x10 || actor->actor_class == 0x49) &&
        source_state != 0u && source_state <= 6u)
        source_state = (unsigned short)(source_state << 8);
    printf("%u\t%s\t%08lx\t%u\t%02x\t%04x\t%04x\t%ld\t%ld\t%d\t%u\t%08lx\t%08lx\t%d\t%u\t%u\t%d\t%d\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t0\t0\t0\t0\t0\t0\t0\t%d\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t%u\n",
           frame, pool, actor->source_slot, actor->type,
           (unsigned int)(unsigned char)actor->actor_class,
           source_state, actor->substate, x_fp, y_fp, actor->z,
           actor->facing, actor->animation_record, actor->assembly,
           actor->health,
           actor->hurt_selector, actor->attack_selector, actor->x, actor->y,
           actor->source_a3, actor->source_a4, actor->source_a5,
           actor->source_a6, actor->source_style85, actor->source_b0,
           actor->source_direction, actor->source_player_guard,
           actor->animation_timer, actor->animation_branch,
           actor->source_field01, actor->source_collision_guard6d,
           actor->source_collision_suppress70,
           actor->source_hit_recovery_active,
           actor->source_transition_latch_ae,
           actor->source_action_timer,
           actor->variant, actor->source_target_low,
           actor->source_field09, actor->source_field2b);
}

static void emit_projectile(unsigned int frame,
                            const AvspRound1WeaponProjectileAllocation *actor)
{
    unsigned short source_state;
    if (actor->active == 0u)
        return;
    source_state = actor->state == 0u ? 0u : (unsigned short)(
        ((unsigned short)actor->state << 8) | actor->substate);
    printf("%u\trecord4\t00ff%04x\t4\t%02x\t%04x\t%04x\t%ld\t%ld\t%d\t%u\t%08lx\t%08lx\t%d\t0\t%u\t%d\t%d\t0\t0\t0\t0\t0\t0\t0\t0\t%u\t%08lx\t%08lx\t%d\t%u\t%u\t%u\t%u\t%d\n",
           frame, actor->source_slot,
           (unsigned int)(unsigned char)actor->actor_class,
           (unsigned int)source_state, 0u,
           actor->x_fp, actor->y_fp, actor->z, actor->facing,
           actor->animation_record, actor->assembly, actor->health,
           actor->attack_selector, (short)(actor->x_fp >> 16),
           (short)(actor->y_fp >> 16), actor->animation_timer,
           actor->attack_table,
           avsp_round1_weapon_current_attack_record(actor),
           actor->collision_result,
           actor->collision_identity, actor->collision_registered,
           actor->angle, actor->progress, actor->animation_branch);
}

int main(void)
{
    AvspRound1Runtime runtime;
    unsigned int source_frame;
    unsigned int index;
    int player_authority_enabled_at_tick_start;
    avsp_round1_init(&runtime);
    fputs("frame\tpool\tsource_slot\ttype\tclass\tstate\tsubstate\tx_fp\ty_fp\tz\tfacing\tanimation_record\tassembly\thealth\thurt_selector\tattack_selector\tx\ty\tsource_a3\tsource_a4\tsource_a5\tsource_a6\tsource_style85\tsource_b0\tsource_direction\tsource_player_guard\tanimation_timer\tattack_table\tcurrent_attack_record\tcollision_result\tcollision_identity\tcollision_registered\tangle\tprogress\tanimation_branch\tsource_field01\tsource_collision_guard6d\tsource_collision_suppress70\tsource_hit_recovery_active",
          stdout);
    puts("\tsource_transition_latch_ae\tsource_action_timer\tsource_variant\tsource_target_low\tsource_field09\tsource_field2b");
    for (source_frame = 1972u; source_frame <= 5566u; ++source_frame)
    {
        unsigned short input = avsp_round1_coffee_shop_source_input(
            (unsigned short)source_frame);
        unsigned int tick;
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
        unsigned int class0a_updates =
            avsp_round1_coffee_shop_class0a_source_updates(
                (unsigned short)source_frame);
        unsigned int class00_updates =
            avsp_round1_coffee_shop_class00_source_updates(
                (unsigned short)source_frame);
        unsigned int exit_player_updates =
            avsp_round1_coffee_exit_player_source_updates(
                (unsigned short)source_frame);
        unsigned int phase_updates = source_updates > scheduler_updates ?
            source_updates : scheduler_updates;
        int exit_source_phase = exit_player_updates != 0u &&
            runtime.entry.exit_started && runtime.route_state != 4;
        if (record20_prefix_updates > phase_updates)
            phase_updates = record20_prefix_updates;
        if (class02_updates > phase_updates)
            phase_updates = class02_updates;
        if (class0a_updates > phase_updates)
            phase_updates = class0a_updates;
        if (class00_updates > phase_updates)
            phase_updates = class00_updates;
        if (exit_player_updates > phase_updates)
            phase_updates = exit_player_updates;
        if (source_frame == 2072u &&
            !avsp_round1_begin_first_entry(&runtime))
            return 2;
        emit_actor(source_frame, "player", &runtime.player);
        emit_actor(source_frame, "record32", &runtime.entry_controller);
        for (index = 0u; index < AVSP_ROUND1_POOL_COUNT; ++index)
        {
            unsigned int record_index;
            char name[16];
            sprintf(name, "record%u", runtime.pools[index].record_type);
            for (record_index = 0u;
                 record_index < runtime.pools[index].capacity; ++record_index)
                emit_actor(source_frame, name,
                           &runtime.pools[index].records[record_index]);
        }
        for (index = 0u; index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
             ++index)
            emit_projectile(source_frame,
                            &runtime.player_weapon_projectiles[index]);
#if defined(AVSP_COFFEE_SCENE_RNG_TRACE) && AVSP_COFFEE_SCENE_RNG_TRACE
        fprintf(stderr, "scene_rng frame=%u seed=%04x\n",
                source_frame, runtime.rng_seed);
#endif
        if (source_frame >= 2467u && source_frame <= 2501u)
        {
            const AvspRound1WeaponProjectileAllocation *parent =
                &runtime.player_weapon_projectiles[0];
            const AvspRound1ActorCore *hit_return_actor =
                &runtime.pools[0].records[10];
            fprintf(stderr,
                    "record4_trajectory frame=%u active=%u state=%u x=%d y=%d z=%d camera=%d/%d navigation=%d/%d phase=%u class1f=%04x/%04x field01=%u a2=%u\n",
                    source_frame, parent->active, parent->state,
                    parent->x, parent->y, parent->z,
                    runtime.camera_x_position, runtime.camera_z_position,
                    runtime.navigation_bound_x, runtime.navigation_bound_z,
                    runtime.first_encounter.source_phase_counter,
                    hit_return_actor->state, hit_return_actor->substate,
                    hit_return_actor->source_field01,
                    hit_return_actor->source_a2);
        }
        if (source_frame == 2072u || source_frame == 2073u ||
            source_frame == 2510u || source_frame == 2511u ||
            (source_frame >= 4088u && source_frame <= 4095u) ||
            (source_frame >= 2239u && source_frame <= 2244u) ||
            (source_frame >= 2749u && source_frame <= 2759u) ||
            (source_frame >= 2249u && source_frame <= 2294u) ||
            (source_frame >= 2614u && source_frame <= 2619u) ||
            (source_frame >= 2348u && source_frame <= 2380u) ||
            (source_frame >= 2329u && source_frame <= 2330u))
            fprintf(stderr,
                    "rng_checkpoint frame=%u seed=%04x scheduler=%lu phase=%u living=%u spawn_index=%u timer=%u camera=%d previous=%d scene_cursor=%u\n",
                    source_frame, runtime.rng_seed,
                    runtime.scheduler_frames,
                    runtime.first_encounter.source_phase_counter,
                    runtime.first_encounter.source_living_count,
                    runtime.first_encounter.source_spawn_index,
                    runtime.first_encounter.source_spawn_timer,
                    runtime.camera_x_position,
                    runtime.camera_x_previous,
                    runtime.coffee_scene_record_cursor);
        if (source_frame == 2377u || source_frame == 2378u ||
            source_frame == 2409u || source_frame == 2410u)
        {
            const AvspRound1ActorCore *retry_actor =
                &runtime.pools[0].records[18];
            fprintf(stderr,
                    "class1f_retry_checkpoint frame=%u state=%04x substate=%04x latch=%u a6=%u b0=%u timer=%u branch=%d rng=%04x\n",
                    source_frame, retry_actor->state,
                    retry_actor->substate,
                    retry_actor->source_transition_latch_ae,
                    retry_actor->source_a6, retry_actor->source_b0,
                    retry_actor->animation_timer,
                    retry_actor->animation_branch, runtime.rng_seed);
        }
        if (source_frame >= 4029u && source_frame <= 4033u)
            fprintf(stderr,
                    "hit_interaction_guard frame=%u input=%04x current=%04x previous=%04x edges=%04x action_facing=%d core_facing=%u source_facing=%u hit=%u/%u pending=%u active=%u\n",
                    source_frame, input,
                    runtime.player_action.current_mask,
                    runtime.player_action.previous_mask,
                    runtime.player_action.input_edges,
                    runtime.player_action.facing, runtime.player.facing,
                    runtime.player.source_facing_selector,
                    runtime.player_hit_active, runtime.player_hit_phase,
                    runtime.player_hit_interaction_pending,
                    runtime.player_hit_interaction_active);
        if (source_frame >= 2918u && source_frame <= 2920u)
        {
            const AvspRound1ActorCore *recurring_actor =
                &runtime.pools[0].records[17];
            fprintf(stderr,
                    "recurring_checkpoint frame=%u seed=%04x state=%04x/%04x a3=%u a4=%u a5=%u a6=%u style=%u selector83=%u direction=%u\n",
                    source_frame, runtime.rng_seed,
                    recurring_actor->state, recurring_actor->substate,
                    recurring_actor->source_a3, recurring_actor->source_a4,
                    recurring_actor->source_a5, recurring_actor->source_a6,
                    recurring_actor->source_style85,
                    recurring_actor->source_selector83,
                    recurring_actor->source_direction);
        }
        if ((source_frame >= 2998u && source_frame <= 3010u) ||
            (source_frame >= 3088u && source_frame <= 3093u) ||
            (source_frame >= 3153u && source_frame <= 3156u))
        {
            const AvspRound1ActorCore *inner8_actor = source_frame >= 3153u ?
                &runtime.pools[0].records[14] :
                &runtime.pools[0].records[19];
            fprintf(stderr,
                    "inner8_checkpoint frame=%u camera=%d/%d seed=%04x state=%04x/%04x direction=%u facing=%u special_ad=%u transition_ae=%u b0=%u band=%d group=%d cursor=%u membership=%u offsets=%d/%d populations=%u/%u/%u/%u xfp=%ld yfp=%ld timer=%u branch=%d\n",
                    source_frame, runtime.camera_x_position,
                    runtime.camera_z_position, runtime.rng_seed,
                    inner8_actor->state, inner8_actor->substate,
                    inner8_actor->source_direction,
                    inner8_actor->facing,
                    inner8_actor->source_special_latch_ad,
                    inner8_actor->source_transition_latch_ae,
                    inner8_actor->source_b0,
                    inner8_actor->source_inner8_band,
                    inner8_actor->source_inner8_group,
                    inner8_actor->source_inner8_cursor,
                    inner8_actor->source_inner8_membership,
                    inner8_actor->source_inner8_x_offset,
                    inner8_actor->source_inner8_z_offset,
                    runtime.class1f_inner8_group_population[0],
                    runtime.class1f_inner8_group_population[1],
                    runtime.class1f_inner8_group_population[2],
                    runtime.class1f_inner8_group_population[3],
                    inner8_actor->source_x_fp, inner8_actor->source_y_fp,
                    inner8_actor->animation_timer,
                        inner8_actor->animation_branch);
        }
        if ((source_frame >= 3574u && source_frame <= 3582u) ||
            (source_frame >= 3644u && source_frame <= 3647u))
        {
            const AvspRound1ActorCore *actor =
                &runtime.pools[0].records[14];
            fprintf(stderr,
                    "inner8_late_checkpoint frame=%u camera=%d/%d previous=%d/%d rng=%04x slot=%04x state=%04x/%04x xfp=%08lx yfp=%08lx z=%d band=%d group=%d cursor=%u member=%u prior=%u/%u offsets=%d/%d direction=%u style=%u populations=%u/%u/%u/%u\n",
                    source_frame, runtime.camera_x_position,
                    runtime.camera_z_position, runtime.camera_x_previous,
                    runtime.camera_z_previous, runtime.rng_seed,
                    (unsigned short)actor->source_slot, actor->state,
                    actor->substate, (unsigned long)actor->source_x_fp,
                    (unsigned long)actor->source_y_fp, actor->z,
                    actor->source_inner8_band,
                    actor->source_inner8_group,
                    actor->source_inner8_cursor,
                    actor->source_inner8_membership,
                    actor->source_inner8_prior_membership,
                    actor->source_inner8_prior_group,
                    actor->source_inner8_x_offset,
                    actor->source_inner8_z_offset,
                    actor->source_direction, actor->source_style85,
                    runtime.class1f_inner8_group_population[0],
                    runtime.class1f_inner8_group_population[1],
                    runtime.class1f_inner8_group_population[2],
                    runtime.class1f_inner8_group_population[3]);
        }
        if (source_frame >= 3653u && source_frame <= 3655u)
        {
            const AvspRound1ActorCore *actor =
                &runtime.pools[0].records[19];
            fprintf(stderr,
                    "inner8_action10_transition frame=%u rng=%04x state=%04x/%04x xfp=%08lx yfp=%08lx z=%d band=%d group=%d cursor=%u member=%u prior=%u/%u offsets=%d/%d direction=%u style=%u a3=%u a4=%u a5=%u a6=%u b0=%u populations=%u/%u/%u/%u\n",
                    source_frame, runtime.rng_seed, actor->state,
                    actor->substate, (unsigned long)actor->source_x_fp,
                    (unsigned long)actor->source_y_fp, actor->z,
                    actor->source_inner8_band, actor->source_inner8_group,
                    actor->source_inner8_cursor,
                    actor->source_inner8_membership,
                    actor->source_inner8_prior_membership,
                    actor->source_inner8_prior_group,
                    actor->source_inner8_x_offset,
                    actor->source_inner8_z_offset,
                    actor->source_direction, actor->source_style85,
                    actor->source_a3, actor->source_a4, actor->source_a5,
                    actor->source_a6, actor->source_b0,
                    runtime.class1f_inner8_group_population[0],
                    runtime.class1f_inner8_group_population[1],
                    runtime.class1f_inner8_group_population[2],
                    runtime.class1f_inner8_group_population[3]);
        }
        if ((source_frame >= 2780u && source_frame <= 2920u) ||
            (source_frame >= 3268u && source_frame <= 3280u) ||
            (source_frame >= 3505u && source_frame <= 3525u))
        {
            fprintf(stderr, "rng_frame frame=%u seed=%04x\n",
                    source_frame, runtime.rng_seed);
            if (source_frame >= 3268u)
                fprintf(stderr,
                        "rng_owner frame=%u class09=%lu class4e=%lu initial1f=%lu action4=%lu action4_timer=%lu action0c_timer=%lu action0e=%lu\n",
                        source_frame, runtime.class09_rng_calls,
                        runtime.class4e_rng_calls,
                        runtime.class1f_initial_rng_calls,
                        runtime.class1f_action4_rng_calls,
                        runtime.class1f_action4_timer_rng_calls,
                        runtime.class1f_action0c_timer_rng_calls,
                        runtime.class1f_action0e_rng_calls);
        }
        if (source_frame >= 2805u && source_frame <= 2807u)
            fprintf(stderr,
                    "impact_rng_checkpoint frame=%u class47_init=%lu class47_rng=%lu class4e_init=%lu class4e_rng=%lu variant1_init=%lu\n",
                    source_frame, runtime.class47_initializations,
                    runtime.class47_rng_calls,
                    runtime.class4e_initializations,
                    runtime.class4e_rng_calls,
                    runtime.class4e_variant1_initializations);
        if ((input & (AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_ATTACK |
                      AVSP_ROUND1_INPUT_BUTTON3)) != 0u ||
            runtime.player_special_attack_active)
            fprintf(stderr,
                    "special_trace frame=%u input=%04x pipeline=%02x previous=%02x active=%u phase=%04x action_state=%u health=%d contact=%u entries=%lu\n",
                    source_frame, input,
                    runtime.player_special_input_pipeline,
                    runtime.player_special_previous_buttons,
                    runtime.player_special_attack_active,
                    runtime.player_special_phase,
                    runtime.player_action.state,
                    runtime.player_action.health,
                    runtime.player_special_owner_contact,
                    runtime.player_special_attack_entries);
        if (source_frame >= 2518u && source_frame <= 2541u)
            fprintf(stderr,
                    "player_resource_checkpoint frame=%u resource=%u recharge=%u depleted=%u weapon=%u empty=%u tick=%u substate=%04x animation=%08lx\n",
                    source_frame, runtime.player_resource,
                    runtime.player_resource_recharge,
                    runtime.player_resource_depleted,
                    runtime.player_weapon_active,
                    runtime.player_weapon_empty,
                    runtime.player_weapon_tick,
                    runtime.player.substate,
                    (unsigned long)runtime.player.animation_record);
        if (source_frame == 3282u)
        {
            const AvspRound1ActorCore *a = &runtime.pools[0].records[19];
            fprintf(stderr,
                    "inner8_pre_frame frame=%u slot=%04x state=%04x substate=%04x style=%u action_timer=%u rng=%04x\n",
                    source_frame, (unsigned short)a->source_slot, a->state,
                    a->substate, a->source_style85,
                    a->source_action_timer, runtime.rng_seed);
        }
        runtime.frame = source_frame >= 2040u ? source_frame - 2040u : 0u;
        if (exit_source_phase)
        {
            if (!avsp_round1_step_coffee_exit_source_phase_program(
                    &runtime, (unsigned short)source_frame))
            {
                fprintf(stderr,
                        "exit_phase_failure frame=%u code=%u slot=%04x state=%04x substate=%04x animation=%08lx route=%d exit_updates=%lu script_step=%u script_cursor=%08lx failures=%lu\n",
                        source_frame, runtime.scheduler_failure_code,
                        runtime.scheduler_failure_source_slot,
                        runtime.scheduler_failure_state,
                        runtime.scheduler_failure_substate,
                        runtime.scheduler_failure_animation_record,
                        runtime.route_state,
                        runtime.entry.exit_route_updates,
                        runtime.entry.exit_script_step,
                        runtime.entry.exit_script_cursor,
                        runtime.failure_count);
                return 3;
            }
        }
        else
        {
            for (tick = 1u; tick <= phase_updates; ++tick)
            {
                unsigned int phase_tick = tick == phase_updates ? 0u : tick;
                int source_update_enabled = phase_tick == 0u ?
                    source_updates != 0u : phase_tick < source_updates;
                int scheduler_update_enabled = phase_tick == 0u ?
                    scheduler_updates != 0u : phase_tick < scheduler_updates;
                int record20_prefix_update_enabled = phase_tick == 0u ?
                    record20_prefix_updates != 0u :
                    phase_tick < record20_prefix_updates;
                int class02_update_enabled = phase_tick == 0u ?
                    class02_updates != 0u : phase_tick < class02_updates;
                int class0a_update_enabled = phase_tick == 0u ?
                    class0a_updates != 0u : phase_tick < class0a_updates;
                int class00_update_enabled = phase_tick == 0u ?
                    class00_updates != 0u : phase_tick < class00_updates;
                player_authority_enabled_at_tick_start =
                    runtime.route_state == 4;
                if (source_update_enabled && runtime.entry.started &&
                    runtime.route_state != 4 &&
                    !avsp_round1_step_first_entry(&runtime))
                    return 3;
                if (runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_pre_player_source_differential(
                        &runtime, source_update_enabled))
                    return 5;
                if (source_update_enabled &&
                    player_authority_enabled_at_tick_start &&
                    runtime.route_state == 4 &&
                    !avsp_round1_step_player(&runtime, input, 0))
                    return 4;
                if (runtime.entry.dependencies_seeded &&
                    !avsp_round1_step_scheduler_post_player_source_differential_scene(
                        &runtime, scheduler_update_enabled,
                        record20_prefix_update_enabled,
                        class02_update_enabled, class0a_update_enabled,
                        class00_update_enabled))
                    return 5;
            }
        }
        if (!avsp_round1_step_coffee_exit_display(&runtime))
            return 6;
        if ((source_frame >= 3003u && source_frame <= 3005u) ||
            (source_frame >= 3089u && source_frame <= 3092u) ||
            (source_frame >= 3130u && source_frame <= 3190u) ||
            (source_frame >= 3270u && source_frame <= 3284u) ||
            (source_frame >= 3890u && source_frame <= 3927u))
        {
            unsigned int pool_index;
            for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT;
                 ++pool_index)
            {
                unsigned int record_index;
                for (record_index = 0u;
                     record_index < runtime.pools[pool_index].capacity;
                     ++record_index)
                {
                    const AvspRound1ActorCore *a =
                        &runtime.pools[pool_index].records[record_index];
                    if ((unsigned short)a->source_slot != 0xa3c0u &&
                        (unsigned short)a->source_slot != 0xa000u)
                        continue;
                    fprintf(stderr,
                            "inner8_action10_probe frame=%u slot=%04x pool=%u record=%u active=%u state=%04x substate=%04x xfp=%08lx yfp=%08lx z=%d facing=%u style=%u direction=%u band=%d group=%d cursor=%u membership=%u prior_group=%u prior_membership=%u anim=%08lx timer=%u branch=%d action_timer=%u lifetime=%u target_x=%d target_z=%d rng=%04x\n",
                            source_frame, (unsigned short)a->source_slot,
                            pool_index, record_index, a->active,
                            a->state, a->substate,
                            (unsigned long)a->source_x_fp,
                            (unsigned long)a->source_y_fp, a->z, a->facing,
                            a->source_style85, a->source_direction,
                            a->source_inner8_band,
                            a->source_inner8_group, a->source_inner8_cursor,
                            a->source_inner8_membership,
                            a->source_inner8_prior_group,
                            a->source_inner8_prior_membership,
                            (unsigned long)a->animation_record,
                            a->animation_timer, a->animation_branch,
                            a->source_action_timer, a->effect_timer,
                            runtime.player_action.x, runtime.player_action.lane,
                            runtime.rng_seed);
                }
            }
        }
        if (source_frame == 2829u || source_frame == 2831u)
        {
            const AvspRound1ActorCore *a = source_frame == 2829u ?
                &runtime.pools[0].records[11] :
                &runtime.pools[0].records[15];
            fprintf(stderr,
                    "special_collision_probe frame=%u player_x=%d lane=%d height=%d attack=%u ready=%u hitstop=%u target=%08lx active=%u x=%d y=%d z=%d facing=%u hurt=%u health=%d guard01=%u guard6d=%u suppress70=%u reaction=%d tests=%lu contacts=%lu\n",
                    source_frame, runtime.player_action.x,
                    runtime.player_action.lane, runtime.player_action.height,
                    runtime.player.attack_selector,
                    runtime.player_special_attack_contact_ready,
                    runtime.player.source_hitstop, a->source_slot, a->active,
                    a->x, a->y, a->z, a->facing, a->hurt_selector,
                    a->health, a->source_field01,
                    a->source_collision_guard6d,
                    a->source_collision_suppress70,
                    a->source_hit_recovery_active != 0,
                    runtime.player_special_class1f_collision_tests,
                    runtime.player_special_attack_contacts);
        }
    }
    fprintf(stderr,
            "class0a_init=%lu class0a_animation=%lu class0a_guards=%lu class0a_releases=%lu class0a_next=%lu\n",
            runtime.class0a_initializations,
            runtime.class0a_animation_steps,
            runtime.class0a_guard_transitions,
            runtime.class0a_releases,
            runtime.class0a_next_entry_spawns);
    fprintf(stderr,
            "class00_alloc_requests=%lu class00_allocations=%lu class00_init=%lu class00_init_substates=%lu class00_projection=%lu class00_bindings=%lu class00_helpers=%lu\n",
            runtime.class00_companion_allocation_requests,
            runtime.class00_companion_allocations,
            runtime.class00_companion_initializations,
            runtime.class00_companion_init_substates,
            runtime.class00_companion_parent_projections,
            runtime.class00_companion_animation_bindings,
            runtime.class00_companion_helper_calls);
    fprintf(stderr,
            "class03_alloc_requests=%lu class03_allocations=%lu class03_alloc_failures=%lu class03_init=%lu class03_motion=%lu class03_animation=%lu class03_transitions=%lu class03_rng=%lu class03_releases=%lu\n",
            runtime.type36_class03_allocation_requests,
            runtime.type36_class03_allocations,
            runtime.type36_class03_allocation_failures,
            runtime.type36_class03_initializations,
            runtime.type36_class03_motion_steps,
            runtime.type36_class03_animation_steps,
            runtime.type36_class03_state_transitions,
            runtime.type36_class03_rng_calls,
            runtime.type36_class03_releases);
    fprintf(stderr,
            "class04_alloc_requests=%lu class04_allocations=%lu class04_alloc_failures=%lu class04_init=%lu class04_animation=%lu class04_transitions=%lu class04_global_moves=%lu class04_rng=%lu class04_releases=%lu\n",
            runtime.type36_class04_allocation_requests,
            runtime.type36_class04_allocations,
            runtime.type36_class04_allocation_failures,
            runtime.type36_class04_initializations,
            runtime.type36_class04_animation_steps,
            runtime.type36_class04_state_transitions,
            runtime.type36_class04_global_moves,
            runtime.type36_class04_rng_calls,
            runtime.type36_class04_releases);
    fprintf(stderr,
            "class0e_allocations=%lu class0e_alloc_failures=%lu class0e_init=%lu class0e_attachment=%lu class0e_transitions=%lu class0e_alias=%lu class0e_releases=%lu class0e_aux=%lu\n",
            runtime.type36_class0e_allocations,
            runtime.type36_class0e_allocation_failures,
            runtime.type36_class0e_initializations,
            runtime.type36_class0e_attachment_steps,
            runtime.type36_class0e_transitions,
            runtime.type36_class0e_alias_writes,
            runtime.type36_class0e_releases,
            runtime.source_aux_ffe29c);
    fprintf(stderr,
            "native_scene route=%d progress=%u living=%u releases=%lu damage=%lu collisions=%lu obstacle_spawns=%lu obstacle_damage=%lu obstacle_transitions=%lu obstacle_releases=%lu child_releases=%lu special_entries=%lu special_contacts=%lu camera=%d player_x=%d player_z=%d failures=%lu fallback=%lu class0f_init=%lu class0f_collision=%lu class0f_navigation=%lu class0f_reactions=%lu class0f_audio=%lu class0f_class11=%lu class0f_class09=%lu class0f_releases=%lu\n",
            runtime.route_state, runtime.first_encounter.source_progress,
            runtime.first_encounter.source_living_count,
            runtime.class1f_action_releases,
            runtime.player_weapon_projectile_damage_writes,
            runtime.player_weapon_projectile_collision_writes,
            runtime.coffee_shop_obstacle_spawns,
            runtime.coffee_shop_obstacle_damage_events,
            runtime.coffee_shop_obstacle_state_transitions,
            runtime.coffee_shop_obstacle_releases,
            runtime.coffee_shop_obstacle_child_releases,
            runtime.player_special_attack_entries,
            runtime.player_special_attack_contacts,
            runtime.camera_x_position,
            runtime.player_action.x,
            runtime.player_action.lane,
            runtime.failure_count, runtime.fallback_count,
            runtime.class0f_initializations,
            runtime.class0f_collision_calls,
            runtime.class0f_navigation_calls,
            runtime.class0f_reaction_entries,
            runtime.class0f_audio_events,
            runtime.class0f_class11_allocations,
            runtime.class0f_class09_allocations,
            runtime.class0f_releases);
    return 0;
}
