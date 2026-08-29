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
    printf("%u\t%s\t%08lx\t%u\t%02x\t%04x\t%04x\t%ld\t%ld\t%d\t%u\t%08lx\t%08lx\t%d\t%u\t%u\t%d\t%d\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t%u\t0\t0\t0\t0\t0\t0\t0\t%d\n",
           frame, pool, actor->source_slot, actor->type,
           (unsigned int)(unsigned char)actor->actor_class,
           source_state, actor->substate, x_fp, y_fp, actor->z,
           actor->facing, actor->animation_record, actor->assembly,
           actor->health,
           actor->hurt_selector, actor->attack_selector, actor->x, actor->y,
           actor->source_a3, actor->source_a4, actor->source_a5,
           actor->source_a6, actor->source_style85, actor->source_b0,
           actor->source_direction, actor->animation_timer,
           actor->animation_branch);
}

static void emit_projectile(unsigned int frame,
                            const AvspRound1WeaponProjectileAllocation *actor)
{
    unsigned short source_state;
    if (actor->active == 0u)
        return;
    source_state = actor->state == 0u ? 0u : (unsigned short)(
        ((unsigned short)actor->state << 8) | actor->substate);
    printf("%u\trecord4\t00ff%04x\t4\t%02x\t%04x\t%04x\t%ld\t%ld\t%d\t%u\t%08lx\t%08lx\t%d\t0\t%u\t%d\t%d\t0\t0\t0\t0\t0\t0\t0\t%u\t%08lx\t%08lx\t%d\t%u\t%u\t%u\t%u\t%d\n",
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
    puts("frame\tpool\tsource_slot\ttype\tclass\tstate\tsubstate\tx_fp\ty_fp\tz\tfacing\tanimation_record\tassembly\thealth\thurt_selector\tattack_selector\tx\ty\tsource_a3\tsource_a4\tsource_a5\tsource_a6\tsource_style85\tsource_b0\tsource_direction\tanimation_timer\tattack_table\tcurrent_attack_record\tcollision_result\tcollision_identity\tcollision_registered\tangle\tprogress\tanimation_branch");
    for (source_frame = 1972u; source_frame <= 5566u; ++source_frame)
    {
        unsigned short input = avsp_round1_coffee_shop_source_input(
            (unsigned short)source_frame);
        unsigned int tick;
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
            (source_frame >= 2249u && source_frame <= 2294u) ||
            (source_frame >= 2348u && source_frame <= 2380u) ||
            (source_frame >= 2329u && source_frame <= 2330u))
            fprintf(stderr,
                    "rng_checkpoint frame=%u seed=%04x scheduler=%lu phase=%u living=%u spawn_index=%u timer=%u\n",
                    source_frame, runtime.rng_seed,
                    runtime.scheduler_frames,
                    runtime.first_encounter.source_phase_counter,
                    runtime.first_encounter.source_living_count,
                    runtime.first_encounter.source_spawn_index,
                    runtime.first_encounter.source_spawn_timer);
        if (source_frame == 2377u || source_frame == 2378u ||
            source_frame == 2409u || source_frame == 2410u)
        {
            const AvspRound1ActorCore *retry_actor =
                &runtime.pools[0].records[18];
            fprintf(stderr,
                    "class1f_retry_checkpoint frame=%u state=%04x substate=%04x latch=%u a6=%u b0=%u timer=%u branch=%d rng=%04x\n",
                    source_frame, retry_actor->state,
                    retry_actor->substate, retry_actor->source_motion_flags,
                    retry_actor->source_a6, retry_actor->source_b0,
                    retry_actor->animation_timer,
                    retry_actor->animation_branch, runtime.rng_seed);
        }
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
        runtime.frame = source_frame >= 2040u ? source_frame - 2040u : 0u;
        for (tick = 0u;
             tick < avsp_round1_coffee_shop_source_updates(
                 (unsigned short)source_frame);
             ++tick)
        {
            player_authority_enabled_at_tick_start = runtime.route_state == 4;
            if (runtime.entry.started && runtime.route_state != 4 &&
                !avsp_round1_step_first_entry(&runtime))
                return 3;
            if (player_authority_enabled_at_tick_start &&
                !avsp_round1_step_player(&runtime, input, 0))
                return 4;
            if (runtime.entry.dependencies_seeded &&
                !avsp_round1_step_scheduler(&runtime))
            {
                fprintf(stderr,
                        "scheduler_failure frame=%u code=%u slot=%08lx state=%04x substate=%04x animation=%08lx failures=%lu\n",
                        source_frame, runtime.scheduler_failure_code,
                        (unsigned long)
                            runtime.scheduler_failure_source_slot,
                        runtime.scheduler_failure_state,
                        runtime.scheduler_failure_substate,
                        runtime.scheduler_failure_animation_record,
                        runtime.failure_count);
                return 5;
            }
        }
    }
    fprintf(stderr,
            "native_scene route=%d progress=%u living=%u releases=%lu damage=%lu collisions=%lu obstacle_spawns=%lu obstacle_damage=%lu obstacle_transitions=%lu obstacle_releases=%lu child_releases=%lu special_entries=%lu special_contacts=%lu camera=%d player_x=%d player_z=%d failures=%lu fallback=%lu\n",
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
            runtime.failure_count, runtime.fallback_count);
    return 0;
}
