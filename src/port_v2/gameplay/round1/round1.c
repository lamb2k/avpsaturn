#include "round1.h"
#include "spec02_round1_entry_data.h"
#include "../../../../avsp_collision.h"

#include <string.h>

static const unsigned char avsp_round1_pool_types[AVSP_ROUND1_POOL_COUNT] =
    {12u, 16u, 20u, 24u};
static const unsigned char avsp_round1_pool_capacities[AVSP_ROUND1_POOL_COUNT] =
    {20u, 20u, 16u, 32u};
static const unsigned short avsp_round1_pool_strides[AVSP_ROUND1_POOL_COUNT] =
    {192u, 128u, 128u, 128u};
static const unsigned short avsp_round1_pool_bases[AVSP_ROUND1_POOL_COUNT] =
    {0x9580u, 0xA480u, 0xAE80u, 0xB680u};

static void avsp_round1_bind_animation_state(
    AvspRound1ActorCore *actor, const AvspRound1AnimationStateSpec *record);

static int avsp_round1_pool_metadata_valid(const AvspRound1Pool *pool,
                                           unsigned int index)
{
    return pool->record_type == avsp_round1_pool_types[index] &&
        pool->capacity == avsp_round1_pool_capacities[index] &&
        pool->stride == avsp_round1_pool_strides[index] &&
        pool->source_base == avsp_round1_pool_bases[index] &&
        pool->free_count <= pool->capacity;
}

static AvspRound1ActorCore *avsp_round1_allocate_pool_actor(
    AvspRound1Runtime *runtime, unsigned int pool_index)
{
    AvspRound1Pool *pool;
    AvspRound1ActorCore *actor;
    unsigned short slot;
    unsigned int index;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (pool->free_count == 0u)
        return 0;
    slot = pool->free_stack[pool->free_count - 1u];
    if (slot < pool->source_base ||
        ((unsigned int)(slot - pool->source_base) % pool->stride) != 0u)
        return 0;
    index = (unsigned int)(slot - pool->source_base) / pool->stride;
    if (index >= pool->capacity)
        return 0;
    --pool->free_count;
    actor = &pool->records[index];
    memset(actor, 0, sizeof(*actor));
    actor->active = 1u;
    actor->type = pool->record_type;
    actor->source_slot = slot;
    return actor;
}

static int avsp_round1_release_pool_actor(AvspRound1Pool *pool,
                                          AvspRound1ActorCore *actor)
{
    unsigned short slot;
    unsigned int index;
    if (pool == 0 || actor == 0 || actor->active == 0u ||
        actor->type != pool->record_type || pool->free_count >= pool->capacity)
        return 0;
    slot = (unsigned short)actor->source_slot;
    if (slot < pool->source_base ||
        ((unsigned int)(slot - pool->source_base) % pool->stride) != 0u)
        return 0;
    index = (unsigned int)(slot - pool->source_base) / pool->stride;
    if (index >= pool->capacity || actor != &pool->records[index])
        return 0;
    pool->free_stack[pool->free_count] = slot;
    ++pool->free_count;
    memset(actor, 0, sizeof(*actor));
    return 1;
}

static AvspRound1ActorCore *avsp_round1_allocate_record12(
    AvspRound1Runtime *runtime, const AvspRound1EntrySpawnSpec *spec)
{
    AvspRound1Pool *pool = &runtime->pools[0];
    unsigned short slot;
    unsigned int index;
    AvspRound1ActorCore *actor;
    if (pool->free_count == 0u || spec->record_type != pool->record_type)
        return 0;
    slot = pool->free_stack[pool->free_count - 1u];
    if (slot != (unsigned short)spec->source_slot || slot < pool->source_base ||
        ((unsigned int)(slot - pool->source_base) % pool->stride) != 0u)
        return 0;
    index = (unsigned int)(slot - pool->source_base) / pool->stride;
    if (index >= pool->capacity)
        return 0;
    --pool->free_count;
    actor = &pool->records[index];
    memset(actor, 0, sizeof(*actor));
    actor->active = 1u;
    actor->actor_class = (signed char)spec->actor_class;
    actor->state = spec->state;
    actor->substate = spec->substate;
    actor->type = spec->record_type;
    actor->facing = spec->facing;
    actor->variant = spec->variant;
    actor->source_action = spec->source_action;
    actor->source_slot = spec->source_slot;
    actor->x = spec->x;
    actor->y = spec->y;
    actor->z = spec->z;
    actor->health = spec->health;
    actor->animation_record = spec->animation_record;
    return actor;
}

static int avsp_round1_spawn_first_entry(AvspRound1Runtime *runtime)
{
    unsigned int index;
    if (runtime->entry.spawned)
        return 1;
    for (index = 0u; index < AVSP_ROUND1_FIRST_SPAWN_COUNT; ++index)
    {
        if (avsp_round1_allocate_record12(
                runtime, &avsp_round1_entry_spawns[index]) == 0)
        {
            ++runtime->failure_count;
            return 0;
        }
        ++runtime->entry.spawn_count;
    }
    runtime->entry.spawned = 1u;
    return 1;
}

static int avsp_round1_dispatch_supported(unsigned char record_type,
                                           signed char actor_class)
{
    unsigned int index;
    if (record_type == avsp_round1_weapon_impact.record_type &&
        actor_class == avsp_round1_weapon_impact.actor_class)
        return 1;
    if (record_type == 24u && actor_class == 0x44)
        return 1;
    for (index = 0u; index < AVSP_ROUND1_REQUIRED_DISPATCH_COUNT; ++index)
    {
        if (avsp_round1_required_dispatches[index].record_type == record_type &&
            avsp_round1_required_dispatches[index].actor_class == actor_class)
            return 1;
    }
    return 0;
}

static unsigned long avsp_round1_scheduler_hash_byte(unsigned long hash,
                                                     unsigned char value)
{
    return (hash ^ (unsigned long)value) * 16777619UL;
}

static const AvspRound1PresentationSpec *avsp_round1_find_class1f_presentation(
    unsigned long animation_record)
{
    unsigned int low = 0u;
    unsigned int high = AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT;
    while (low < high)
    {
        unsigned int middle = low + (high - low) / 2u;
        unsigned long candidate =
            avsp_round1_class1f_presentation[middle].animation_record;
        if (candidate < animation_record)
            low = middle + 1u;
        else if (candidate > animation_record)
            high = middle;
        else
            return &avsp_round1_class1f_presentation[middle];
    }
    return 0;
}

static int avsp_round1_class1f_state_context_supported(unsigned short state,
                                                       unsigned short substate)
{
    unsigned int low = 0u;
    unsigned int high = AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT;
    while (low < high)
    {
        unsigned int middle = low + (high - low) / 2u;
        const AvspRound1StateContextSpec *candidate =
            &avsp_round1_class1f_state_contexts[middle];
        if (candidate->state < state ||
            (candidate->state == state && candidate->substate < substate))
            low = middle + 1u;
        else if (candidate->state > state || candidate->substate > substate)
            high = middle;
        else
            return 1;
    }
    return 0;
}

static void avsp_round1_apply_player_global_bounds(AvspRound1Runtime *runtime)
{
    short x_min;
    short x_max;
    short z_min;
    short z_max;
    if (!runtime->navigation_bounds_active)
        return;
    x_min = (short)(runtime->navigation_bound_x + 0x20);
    x_max = (short)(runtime->navigation_bound_x + 0x160);
    z_min = (short)(runtime->navigation_bound_z + 0x10);
    z_max = (short)(runtime->navigation_bound_z + 0x90);
    ++runtime->navigation_applications;
    if (runtime->player_action.x < x_min)
    {
        runtime->player_action.x = x_min;
        ++runtime->navigation_clamps;
    }
    else if (runtime->player_action.x > x_max)
    {
        runtime->player_action.x = x_max;
        ++runtime->navigation_clamps;
    }
    if (runtime->player_action.lane < z_min)
    {
        runtime->player_action.lane = z_min;
        ++runtime->navigation_clamps;
    }
    else if (runtime->player_action.lane > z_max)
    {
        runtime->player_action.lane = z_max;
        ++runtime->navigation_clamps;
    }
}

static long avsp_round1_abs_long(const long value)
{
    return value < 0 ? -value : value;
}

static void avsp_round1_apply_coffee_shop_obstacle(
    AvspRound1Runtime *runtime)
{
    const AvspRound1ObstacleSpec *obstacle =
        &avsp_round1_coffee_shop_obstacle;
    long dx = (long)obstacle->x + obstacle->attack_box.x_center -
        runtime->player_action.x;
    long dz = (long)obstacle->z + obstacle->attack_box.z_center -
        runtime->player_action.lane;
    unsigned short x_penetration;
    unsigned short z_penetration;
    short signed_penetration;
    ++runtime->navigation_obstacle_tests;
    if (avsp_round1_abs_long(dx) >= obstacle->attack_box.x_half ||
        avsp_round1_abs_long(dz) >= obstacle->attack_box.z_half)
        return;
    x_penetration = (unsigned short)(obstacle->attack_box.x_half -
        avsp_round1_abs_long(dx));
    z_penetration = (unsigned short)(obstacle->attack_box.z_half -
        avsp_round1_abs_long(dz));
    if (z_penetration < x_penetration)
    {
        signed_penetration = (short)z_penetration;
        if (dz < 0)
            signed_penetration = (short)-signed_penetration;
        runtime->player_action.lane = (short)(
            runtime->player_action.lane - signed_penetration);
        runtime->player_action.lane_numerator = 0;
        runtime->navigation_contact_bits = (unsigned char)(
            runtime->navigation_contact_bits |
            (signed_penetration < 0 ? 0x02u : 0x01u));
    }
    else
    {
        signed_penetration = (short)x_penetration;
        if (dx < 0)
            signed_penetration = (short)-signed_penetration;
        runtime->player_action.x = (short)(
            runtime->player_action.x - signed_penetration);
        runtime->player_action.x_numerator = 0;
        runtime->navigation_contact_bits = (unsigned char)(
            runtime->navigation_contact_bits |
            (signed_penetration < 0 ? 0x08u : 0x04u));
    }
    ++runtime->navigation_obstacle_responses;
}

static const AvspRound1TerrainRecordSpec *avsp_round1_terrain_record(
    const unsigned char selector)
{
    switch (selector)
    {
    case 0u: return &avsp_round1_first_segment_terrain_records[0];
    case 8u: return &avsp_round1_first_segment_terrain_records[1];
    case 24u: return &avsp_round1_first_segment_terrain_records[2];
    case 56u: return &avsp_round1_first_segment_terrain_records[3];
    case 96u: return &avsp_round1_first_segment_terrain_records[4];
    case 100u: return &avsp_round1_first_segment_terrain_records[5];
    case 164u: return &avsp_round1_first_segment_terrain_records[6];
    default: return 0;
    }
}

static int avsp_round1_terrain_selector(const short world_x,
                                        const short world_z,
                                        unsigned char *selector)
{
    unsigned short column;
    unsigned short row;
    unsigned short index;
    unsigned char code;
    if (world_x < AVSP_ROUND1_TERRAIN_GRID_X_MIN ||
        world_x > AVSP_ROUND1_TERRAIN_GRID_X_MAX ||
        world_z < AVSP_ROUND1_TERRAIN_GRID_Z_MIN ||
        world_z > AVSP_ROUND1_TERRAIN_GRID_Z_MAX)
        return 0;
    column = (unsigned short)(
        (world_x - AVSP_ROUND1_TERRAIN_GRID_X_MIN) >> 4);
    row = (unsigned short)(
        (world_z - AVSP_ROUND1_TERRAIN_GRID_Z_MIN) >> 4);
    index = (unsigned short)(row * AVSP_ROUND1_TERRAIN_GRID_WIDTH + column);
    code = (unsigned char)((
        avsp_round1_first_segment_terrain_packed[index >> 2] >>
        ((index & 3u) * 2u)) & 3u);
    if (code == 0u)
        *selector = 0u;
    else if (code == 1u)
        *selector = 24u;
    else if (code == 2u)
        *selector = 56u;
    else
        return 0;
    return 1;
}

static int avsp_round1_apply_first_segment_terrain(
    AvspRound1Runtime *runtime)
{
    unsigned char retry;
    unsigned long responses_before = runtime->navigation_terrain_responses;
    runtime->navigation_contact_bits &= 0xf0u;
    do
    {
        const AvspRound1TerrainRecordSpec *record;
        unsigned char selector;
        unsigned short remainder;
        unsigned short penetration;
        retry = 0u;
        if (!avsp_round1_terrain_selector(runtime->player_action.x,
                                          runtime->player_action.lane,
                                          &selector))
            return 0;
        record = avsp_round1_terrain_record(selector);
        ++runtime->navigation_terrain_tests;
        if (record == 0)
            return 0;
        retry = record->retry_selector;
        if (retry == 0xffu)
            ++runtime->navigation_terrain_retries;
        if ((signed char)record->branch_selector >= 0 && record->kind != 8u)
            runtime->navigation_contact_bits = (unsigned char)(
                runtime->navigation_contact_bits |
                (1u << (record->branch_selector >> 1)));
        if (record->kind == 0u)
            continue;
        if (record->kind == 2u && record->branch_selector == 2u)
        {
            remainder = (unsigned short)(
                (~(unsigned short)runtime->player_action.lane) & 15u);
            if ((unsigned short)record->z_parameter > remainder)
            {
                penetration = (unsigned short)(record->z_parameter - remainder);
                runtime->player_action.lane = (short)(
                    runtime->player_action.lane - (short)penetration);
                runtime->player_action.lane_numerator = 0;
                ++runtime->navigation_terrain_responses;
            }
            continue;
        }
        if (record->kind == 4u && record->branch_selector == 2u)
        {
            unsigned short x_remainder;
            unsigned short candidate;
            if (record->orientation == 0u)
                continue;
            x_remainder = record->orientation == 2u ?
                (unsigned short)(runtime->player_action.x & 15) :
                (unsigned short)((~(unsigned short)runtime->player_action.x) & 15u);
            candidate = (unsigned short)((x_remainder >> record->shift) +
                record->z_parameter + 1u);
            remainder = (unsigned short)(
                (~(unsigned short)runtime->player_action.lane) & 15u);
            if (candidate > remainder)
            {
                penetration = (unsigned short)(candidate - remainder);
                runtime->player_action.lane = (short)(
                    runtime->player_action.lane - (short)penetration);
                runtime->player_action.lane_numerator = 0;
                ++runtime->navigation_terrain_responses;
            }
            continue;
        }
        if (record->kind == 6u && record->branch_selector == 4u)
        {
            short slope;
            unsigned short candidate;
            unsigned short x_remainder;
            if (record->orientation == 0u)
                continue;
            remainder = record->orientation == 1u ?
                (unsigned short)(runtime->player_action.lane & 15) :
                (unsigned short)((~(unsigned short)runtime->player_action.lane) & 15u);
            slope = (short)((short)remainder -
                            (short)(signed char)record->z_parameter);
            if (slope < 0)
            {
                penetration = (unsigned short)(
                    (runtime->player_action.x & 15) + 1);
                runtime->player_action.x = (short)(
                    runtime->player_action.x - (short)penetration);
                runtime->player_action.x_numerator = 0;
                retry = 0xffu;
                if (record->retry_selector != 0xffu)
                    ++runtime->navigation_terrain_retries;
                continue;
            }
            candidate = (unsigned short)((unsigned short)slope << record->shift);
            x_remainder = (unsigned short)(runtime->player_action.x & 15);
            if (x_remainder >= candidate)
            {
                penetration = (unsigned short)(x_remainder - candidate + 1u);
                runtime->player_action.x = (short)(
                    runtime->player_action.x - (short)penetration);
                runtime->player_action.x_numerator = 0;
                ++runtime->navigation_terrain_responses;
            }
            continue;
        }
        return 0;
    } while (retry == 0xffu);
    if (runtime->navigation_terrain_responses == responses_before)
        runtime->navigation_contact_bits &= 0xf0u;
    return 1;
}

static int avsp_round1_camera_x_speed(const short delta,
                                      unsigned short *speed)
{
    unsigned short magnitude = (unsigned short)avsp_round1_abs_long(delta);
    unsigned short byte_offset = (unsigned short)(
        ((magnitude + 7u) & 0x00f8u) >> 2);
    unsigned short index = (unsigned short)(byte_offset >> 1);
    if (index >= AVSP_ROUND1_CAMERA_SPEED_COUNT)
        return 0;
    *speed = avsp_round1_coffee_shop_camera.x_speed[index] & 0x000fu;
    return 1;
}

static int avsp_round1_step_coffee_shop_camera(AvspRound1Runtime *runtime)
{
    short delta;
    unsigned short speed;
    if (runtime->camera_coffee_phase == 0u &&
        (unsigned short)runtime->camera_x_position >= 0x0340u)
    {
        runtime->camera_x_lower = 0x0340;
        runtime->camera_x_upper = 0x0340;
        runtime->camera_guard_snapshot = runtime->camera_guard_counter;
        runtime->camera_coffee_phase = 2u;
        ++runtime->camera_locks;
    }
    else if (runtime->camera_coffee_phase == 2u)
    {
        unsigned short elapsed = (unsigned short)(
            runtime->camera_guard_counter - runtime->camera_guard_snapshot);
        int unlock = elapsed >= (unsigned short)(
            avsp_round1_coffee_shop_camera.guard_threshold_byte << 4);
        if (!unlock && runtime->camera_guard_countdown != 0u)
        {
            --runtime->camera_guard_countdown;
            unlock = runtime->camera_guard_countdown == 0u;
        }
        if (unlock)
        {
            runtime->camera_x_upper = 0x03f0;
            runtime->camera_coffee_phase = 4u;
            ++runtime->camera_unlocks;
        }
    }
    else if (runtime->camera_coffee_phase == 4u)
    {
        runtime->camera_x_lower = runtime->camera_x_position;
        if (runtime->camera_x_lower >= 0x03f0)
            runtime->camera_x_lower = 0x03f0;
    }

    runtime->camera_x_previous = runtime->camera_x_position;
    runtime->camera_x_target_previous = runtime->camera_x_target;
    delta = (short)(runtime->player_action.x - runtime->camera_x_target -
                    avsp_round1_coffee_shop_camera.x_right_offset);
    if (delta < 0)
    {
        delta = (short)(runtime->player_action.x - runtime->camera_x_target -
                        avsp_round1_coffee_shop_camera.x_left_offset);
        if (delta > 0)
            delta = 0;
    }
    if (delta != 0)
    {
        if (!avsp_round1_camera_x_speed(delta, &speed))
            return 0;
        if (delta < 0)
            runtime->camera_x_target = (short)(runtime->camera_x_target - speed);
        else
            runtime->camera_x_target = (short)(runtime->camera_x_target + speed);
    }
    if (runtime->camera_x_target > runtime->camera_x_upper)
        runtime->camera_x_target = runtime->camera_x_upper;
    if (runtime->camera_x_target < runtime->camera_x_lower)
        runtime->camera_x_target = runtime->camera_x_lower;
    runtime->camera_x_position = runtime->camera_x_target;

    runtime->camera_z_target_previous = runtime->camera_z_target;
    delta = (short)(runtime->player_action.lane - runtime->camera_z_target -
                    avsp_round1_coffee_shop_camera.z_upper_offset);
    if (delta < 0)
    {
        delta = (short)(runtime->player_action.lane - runtime->camera_z_target -
                        avsp_round1_coffee_shop_camera.z_lower_offset);
        if (delta > 0)
            delta = 0;
    }
    if (delta > 1)
        delta = 1;
    else if (delta < -1)
        delta = -1;
    runtime->camera_z_target = (short)(runtime->camera_z_target + delta);
    if (runtime->camera_z_target > runtime->camera_z_upper)
        runtime->camera_z_target = runtime->camera_z_upper;
    if (runtime->camera_z_target < runtime->camera_z_lower)
        runtime->camera_z_target = runtime->camera_z_lower;
    runtime->camera_z_position = runtime->camera_z_target;
    runtime->navigation_bound_x = runtime->camera_x_position;
    runtime->navigation_bound_z = runtime->camera_z_position;
    runtime->camera_scroll2_x = (short)(runtime->camera_x_position - 0x40);
    ++runtime->camera_updates;
    return 1;
}

static unsigned char avsp_round1_source_direction(
    const unsigned short direction_mask)
{
    unsigned int index = 0u;
    if ((direction_mask & AVSP_PW_INPUT_RIGHT) != 0u)
        index |= 1u;
    if ((direction_mask & AVSP_PW_INPUT_LEFT) != 0u)
        index |= 2u;
    if ((direction_mask & AVSP_PW_INPUT_DOWN) != 0u)
        index |= 4u;
    if ((direction_mask & AVSP_PW_INPUT_UP) != 0u)
        index |= 8u;
    return avsp_round1_player_locomotion.direction_resolver[index];
}

static void avsp_round1_update_player_locomotion(
    AvspRound1Runtime *runtime,
    const unsigned short applied_direction,
    const unsigned char was_stopping,
    const AvspPwView *view)
{
    unsigned char direction;
    if (view->state != AVSP_PW_STATE_CONTROL)
    {
        runtime->player_stop_ticks = 0u;
        runtime->player_was_directional = 0u;
        runtime->player_cleanup_pending = 0u;
        runtime->player_locomotion_action = view->source_action;
        return;
    }
    direction = avsp_round1_source_direction(applied_direction);
    if (was_stopping)
    {
        if (runtime->player_stop_ticks == 0u)
        {
            ++runtime->failure_count;
            return;
        }
        --runtime->player_stop_ticks;
        if (runtime->player_stop_ticks == 0u)
        {
            runtime->player_locomotion_action =
                avsp_round1_player_locomotion.cleanup_action;
            runtime->player.source_action =
                avsp_round1_player_locomotion.cleanup_action;
            runtime->player_cleanup_pending = 1u;
            ++runtime->player_stop_completions;
        }
        else
            runtime->player_locomotion_action =
                avsp_round1_player_locomotion.stop_action;
        return;
    }
    if (runtime->player_cleanup_pending)
    {
        runtime->player_cleanup_pending = 0u;
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.walking_action;
        runtime->player_was_directional = (unsigned char)(direction != 255u);
        return;
    }
    if (direction != 255u)
    {
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.walking_action;
        runtime->player_was_directional = 1u;
    }
    else if (runtime->player_was_directional)
    {
        runtime->player_was_directional = 0u;
        runtime->player_stop_ticks = avsp_round1_player_locomotion.stop_ticks;
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.stop_action;
        ++runtime->player_stop_entries;
    }
    else
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.walking_action;
}

static int avsp_round1_player_melee_contract_valid(void)
{
    unsigned int index;
    if (!avsp_pw_action_defs_valid(avsp_pw_action_defs,
                                   AVSP_PW_ACTION_COUNT) ||
        avsp_round1_player_melee.common_action != 1536u ||
        avsp_round1_player_melee.target_context_action != 5120u ||
        avsp_round1_player_melee.followup_ticks != 30u ||
        avsp_round1_player_melee.selector_count !=
            AVSP_ROUND1_PLAYER_MELEE_COUNT)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_PLAYER_MELEE_COUNT; ++index)
    {
        const AvspRound1PresentationSpec *strike =
            &avsp_round1_player_melee_strikes[index];
        if (avsp_round1_player_melee.selectors[index] != index + 1u ||
            avsp_round1_player_melee.step_values[index] != index ||
            strike->attack_selector != index + 1u ||
            strike->assembly !=
                avsp_pw_assembly_for_record(strike->animation_record))
            return 0;
    }
    return 1;
}

static void avsp_round1_observe_player_melee(AvspRound1Runtime *runtime,
                                              unsigned short prior_state,
                                              unsigned short prior_selector,
                                              unsigned long prior_edges)
{
    unsigned short selector = runtime->player_action.selector;
    unsigned int index;
    if (runtime->player_action.accepted_attack_edges != prior_edges)
    {
        if (runtime->player_action.accepted_attack_edges != prior_edges + 1u ||
            selector < 1u || selector > AVSP_ROUND1_PLAYER_MELEE_COUNT)
        {
            ++runtime->failure_count;
            return;
        }
        if (prior_state == AVSP_PW_STATE_ATTACK)
            ++runtime->player_melee_completions;
        ++runtime->player_melee_entries;
        runtime->player_melee_selector_mask |= 1UL << (selector - 1u);
    }
    if (prior_state == AVSP_PW_STATE_ATTACK &&
        runtime->player_action.state == AVSP_PW_STATE_CONTROL)
        ++runtime->player_melee_completions;
    else if (prior_state == AVSP_PW_STATE_ATTACK &&
             (runtime->player_action.state == AVSP_PW_STATE_HIT ||
              runtime->player_action.state == AVSP_PW_STATE_KO))
        ++runtime->player_melee_interruptions;
    if (runtime->player_action.state != AVSP_PW_STATE_ATTACK)
        return;
    for (index = 0u; index < AVSP_ROUND1_PLAYER_MELEE_COUNT; ++index)
    {
        const AvspRound1PresentationSpec *strike =
            &avsp_round1_player_melee_strikes[index];
        if (runtime->player_action.animation_record ==
                strike->animation_record &&
            runtime->player_action.assembly == strike->assembly &&
            selector == strike->attack_selector)
            runtime->player_melee_presentation_mask |= 1UL << index;
    }
    if (prior_selector > AVSP_ROUND1_PLAYER_MELEE_COUNT)
        ++runtime->failure_count;
}

static int avsp_round1_player_weapon_contract_valid(void)
{
    unsigned int index;
    if (avsp_round1_player_weapon.sufficient_entry_action != 0x0c00u ||
        avsp_round1_player_weapon.sufficient_active_action != 0x0c02u ||
        avsp_round1_player_weapon.empty_entry_action != 0x1a00u ||
        avsp_round1_player_weapon.empty_active_action != 0x1a02u ||
        avsp_round1_player_weapon.cleanup_action != 0u ||
        avsp_round1_player_weapon.return_action != 2u ||
        avsp_round1_player_weapon.attempt_initial != 12 ||
        avsp_round1_player_weapon.cadence_initial != 1u ||
        avsp_round1_player_weapon.cadence_reload != 4u ||
        avsp_round1_player_weapon.empty_timer_initial != 16u ||
        avsp_round1_player_weapon.resource_capacity != 64u ||
        avsp_round1_player_weapon.resource_debit != 3u ||
        avsp_round1_player_weapon.recharge_after_success != 12u ||
        avsp_round1_player_weapon.normal_recharge_reload != 2u ||
        avsp_round1_player_weapon.depleted_recharge_reload != 6u ||
        avsp_round1_player_weapon.projectile_class != 0x05 ||
        avsp_round1_player_weapon.projectile_source_base != 0x8680u ||
        avsp_round1_player_weapon.projectile_stride != 0x0080u ||
        avsp_round1_player_weapon.player_owner != 0x8380u ||
        avsp_round1_player_weapon.projectile_attack_table != 0x03136aUL ||
        avsp_round1_player_weapon_return_frame.action != 2u ||
        avsp_round1_player_weapon_return_frame.substate != 2u ||
        avsp_round1_player_weapon_return_frame.animation_record !=
            0x00163158UL ||
        avsp_round1_player_weapon_return_frame.assembly != 0x00165488UL ||
        avsp_round1_weapon_projectile_angles_facing0[0] != 40u ||
        avsp_round1_weapon_projectile_angles_facing0[11] != 40u ||
        avsp_round1_weapon_projectile_angles_facing1[0] != 24u ||
        avsp_round1_weapon_projectile_angles_facing1[11] != 24u ||
        avsp_round1_weapon_projectile_player_selectors[0] != 6u ||
        avsp_round1_weapon_projectile_player_selectors[11] != 6u ||
        avsp_round1_weapon_projectile.initial_state != 0u ||
        avsp_round1_weapon_projectile.active_state != 2u ||
        avsp_round1_weapon_projectile.impact_state != 4u ||
        avsp_round1_weapon_projectile.release_state != 6u ||
        avsp_round1_weapon_projectile_attack_boxes[1].x_center != 16 ||
        avsp_round1_weapon_projectile_attack_boxes[1].x_half != 18u ||
        avsp_round1_weapon_projectile_attack_boxes[1].damage_selector != 6u ||
        avsp_round1_weapon_projectile.coordinate_mode != 0u ||
        avsp_round1_weapon_projectile.palette != 0u ||
        avsp_round1_weapon_projectile.object_or != 0x8000u ||
        avsp_round1_weapon_damage_offense[0].value != 0u ||
        avsp_round1_weapon_damage_offense[1].value != 4u ||
        avsp_round1_weapon_damage_defense[0].value != 33u ||
        avsp_round1_weapon_damage_matrix[0].damage != 24u ||
        avsp_round1_weapon_damage_matrix[1].damage != 31u ||
        avsp_round1_weapon_impact.actor_class != 0x3a ||
        avsp_round1_weapon_impact.coordinate_mode != 0u ||
        avsp_round1_weapon_impact.palette != 0u ||
        avsp_round1_weapon_impact.object_or != 0x8000u ||
        avsp_round1_weapon_impact.audio_commands[0] != 0x007eu ||
        avsp_round1_weapon_impact.audio_commands[1] != 0x0148u ||
        avsp_round1_weapon_impact_variant0_records[0].timer != 2u ||
        avsp_round1_weapon_impact_variant0_records[4].branch != -32768 ||
        avsp_round1_empty_effect_variant_offsets[1].x != 0 ||
        avsp_round1_empty_effect_variant_offsets[1].y != 78 ||
        avsp_round1_empty_effect_variant1_records[0].timer != 1u ||
        avsp_round1_empty_effect_variant1_records[9].timer != 4095u ||
        avsp_round1_empty_effect_variant1_records[9].branch != -32767)
        return 0;
    for (index = 0u;
         index < AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT; ++index)
    {
        const AvspRound1PlayerWeaponFrameSpec *frame =
            &avsp_round1_player_weapon_frames[index];
        if ((index == 0u && frame->action != 0x0c00u) ||
            (index > 0u && index < 49u && frame->action != 0x0c02u) ||
            (index == 49u && frame->action != 0u))
            return 0;
    }
    for (index = 0u;
         index < AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT; ++index)
    {
        const AvspRound1PlayerWeaponFrameSpec *frame =
            &avsp_round1_player_empty_frames[index];
        if ((index == 0u && frame->action != 0x1a00u) ||
            (index > 0u && index < 17u && frame->action != 0x1a02u) ||
            (index == 17u && frame->action != 0u))
            return 0;
    }
    return 1;
}

static void avsp_round1_bind_player_weapon_frame(
    AvspRound1Runtime *runtime,
    const AvspRound1PlayerWeaponFrameSpec *frame)
{
    runtime->player.source_action = frame->action;
    runtime->player.substate = frame->substate;
    runtime->player.animation_record = frame->animation_record;
    runtime->player.assembly = frame->assembly;
    runtime->player.hurt_selector = frame->hurt_selector;
    runtime->player.attack_selector = frame->attack_selector;
    runtime->player_locomotion_action = frame->action;
    ++runtime->player_weapon_presentation_bindings;
}

static int avsp_round1_allocate_player_weapon_projectile(
    AvspRound1Runtime *runtime)
{
    unsigned int index;
    AvspRound1WeaponProjectileAllocation *projectile;
    if (runtime->player_weapon_projectile_free_count == 0u)
    {
        ++runtime->player_weapon_allocation_failures;
        return 0;
    }
    --runtime->player_weapon_projectile_free_count;
    index = runtime->player_weapon_projectile_free_stack[
        runtime->player_weapon_projectile_free_count];
    if (index >= AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY)
    {
        ++runtime->failure_count;
        return 0;
    }
    projectile = &runtime->player_weapon_projectiles[index];
    memset(projectile, 0, sizeof(*projectile));
    projectile->active = 1u;
    projectile->actor_class =
        avsp_round1_player_weapon.projectile_class;
    projectile->variant =
        (unsigned char)(runtime->player_weapon_attempts == 4 ? 1u : 0u);
    projectile->facing = runtime->player.facing;
    projectile->source_slot = (unsigned short)(
        avsp_round1_player_weapon.projectile_source_base +
        index * avsp_round1_player_weapon.projectile_stride);
    projectile->owner = avsp_round1_player_weapon.player_owner;
    projectile->x = runtime->player.x;
    projectile->y = runtime->player.y;
    projectile->z = runtime->player.z;
    projectile->attack_table =
        avsp_round1_player_weapon.projectile_attack_table;
    projectile->state = 0u;
    projectile->damage_class_index = 0u;
    projectile->angle = runtime->player.facing ?
        avsp_round1_weapon_projectile_angles_facing1[
            (unsigned char)runtime->player_weapon_attempts] :
        avsp_round1_weapon_projectile_angles_facing0[
            (unsigned char)runtime->player_weapon_attempts];
    projectile->parent_presentation_selector =
        avsp_round1_weapon_projectile_player_selectors[
            (unsigned char)runtime->player_weapon_attempts];
    projectile->x_fp = (long)runtime->player.x * 65536L;
    projectile->y_fp = (long)runtime->player.y * 65536L;
    projectile->z_fp = (long)runtime->player.z * 65536L;
    ++runtime->player_weapon_allocations;
    return 1;
}

static short avsp_round1_fixed_high_word(long value)
{
    if (value >= 0L)
        return (short)(value / 65536L);
    return (short)-(((-value) + 65535L) / 65536L);
}

static unsigned char avsp_round1_source_rng(AvspRound1Runtime *runtime)
{
    unsigned short old_seed = runtime->rng_seed;
    unsigned char high = (unsigned char)(((unsigned long)old_seed * 3UL &
                                           0xffffUL) >> 8);
    unsigned char low = (unsigned char)((old_seed & 0x00ffu) + high);
    runtime->rng_seed = (unsigned short)(((unsigned short)high << 8) | low);
    return low;
}

static const AvspRound1PlayerJumpSequenceSpec *
avsp_round1_find_player_jump_sequence(unsigned char selector)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_COUNT; ++index)
        if (avsp_round1_player_jump_sequences[index].selector == selector)
            return &avsp_round1_player_jump_sequences[index];
    return 0;
}

static int avsp_round1_bind_player_jump_sequence(AvspRound1Runtime *runtime,
                                                  unsigned char selector)
{
    const AvspRound1PlayerJumpSequenceSpec *sequence =
        avsp_round1_find_player_jump_sequence(selector);
    const AvspRound1AnimationStateSpec *record;
    if (sequence == 0 || sequence->record_count == 0u)
        return 0;
    record = &sequence->records[0];
    runtime->player_jump_presentation_selector = selector;
    runtime->player_jump_animation_index = 0u;
    runtime->player_jump_animation_timer = record->timer;
    runtime->player_jump_animation_branch = record->branch;
    runtime->player.animation_record = record->animation_record;
    runtime->player.assembly = record->assembly;
    runtime->player.hurt_selector = record->hurt_selector;
    runtime->player.attack_selector = record->attack_selector;
    ++runtime->player_jump_presentation_bindings;
    return 1;
}

static int avsp_round1_step_player_jump_animation(AvspRound1Runtime *runtime)
{
    const AvspRound1PlayerJumpSequenceSpec *sequence =
        avsp_round1_find_player_jump_sequence(
            runtime->player_jump_presentation_selector);
    const AvspRound1AnimationStateSpec *record;
    unsigned char next;
    if (sequence == 0 || runtime->player_jump_animation_index >=
            sequence->record_count || runtime->player_jump_animation_timer == 0u)
        return 0;
    --runtime->player_jump_animation_timer;
    if (runtime->player_jump_animation_timer != 0u)
        return 1;
    if (runtime->player_jump_animation_branch < 0)
    {
        record = &sequence->records[runtime->player_jump_animation_index];
        runtime->player_jump_animation_timer = record->timer;
        return 1;
    }
    next = (unsigned char)(runtime->player_jump_animation_index + 1u);
    if (next >= sequence->record_count)
        return 0;
    runtime->player_jump_animation_index = next;
    record = &sequence->records[next];
    runtime->player_jump_animation_timer = record->timer;
    runtime->player_jump_animation_branch = record->branch;
    runtime->player.animation_record = record->animation_record;
    runtime->player.assembly = record->assembly;
    runtime->player.hurt_selector = record->hurt_selector;
    runtime->player.attack_selector = record->attack_selector;
    ++runtime->player_jump_presentation_bindings;
    return 1;
}

static void avsp_round1_finish_player_jump(AvspRound1Runtime *runtime)
{
    runtime->player_jump_active = 0u;
    runtime->player_jump_cleanup_pending = 1u;
    runtime->player_jump_phase = 0u;
    runtime->player_jump_airborne_latch = 0u;
    runtime->player_action.height = 0;
    runtime->player.source_action = 0u;
    runtime->player.substate = 0u;
    runtime->player.animation_record = 0x0015f1f4UL;
    runtime->player.assembly = 0x001626a4UL;
    runtime->player.hurt_selector = 1u;
    runtime->player.attack_selector = 0u;
    runtime->player_action.x_numerator = 0L;
    ++runtime->player_jump_completions;
}

static void avsp_round1_interrupt_player_jump(AvspRound1Runtime *runtime)
{
    runtime->player_jump_active = 0u;
    runtime->player_jump_cleanup_pending = 0u;
    runtime->player_jump_phase = 0u;
    runtime->player_jump_airborne_latch = 0u;
    runtime->player_action.height = 0;
    runtime->player_action.x_numerator = 0L;
    ++runtime->player_jump_interruptions;
}

static int avsp_round1_begin_player_jump(AvspRound1Runtime *runtime)
{
    runtime->player_jump_active = 1u;
    runtime->player_jump_cleanup_pending = 0u;
    runtime->player_jump_phase = 0x0400u;
    runtime->player_jump_phase_timer = 0u;
    runtime->player_jump_direction_class = 0u;
    runtime->player_jump_collision_selector = 0u;
    runtime->player_jump_airborne_latch = 0u;
    runtime->player_jump_x_fp = (long)runtime->player_action.x * 65536L;
    runtime->player_jump_y_fp = (long)runtime->player_action.lane * 65536L;
    runtime->player_jump_x_velocity = 0L;
    runtime->player_jump_y_velocity = 0L;
    runtime->player_jump_x_acceleration = 0L;
    runtime->player_jump_y_acceleration = 0L;
    runtime->player_stop_ticks = 0u;
    runtime->player_was_directional = 0u;
    runtime->player_cleanup_pending = 0u;
    runtime->player.source_action = 0x0400u;
    runtime->player.substate = 0u;
    runtime->player.coordinate_mode =
        avsp_round1_player_jump_actor.coordinate_mode;
    runtime->player.palette = avsp_round1_player_jump_actor.palette;
    runtime->player.object_or = avsp_round1_player_jump_actor.object_or;
    ++runtime->player_jump_entries;
    return avsp_round1_bind_player_jump_sequence(runtime, 3u);
}

static int avsp_round1_initialize_player_jump(AvspRound1Runtime *runtime,
                                               unsigned short input_mask)
{
    unsigned char right = (unsigned char)(
        (input_mask & AVSP_PW_INPUT_RIGHT) != 0u);
    unsigned char horizontal = (unsigned char)(
        (input_mask & (AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT)) != 0u);
    unsigned char down = (unsigned char)(
        (input_mask & AVSP_PW_INPUT_DOWN) != 0u);
    unsigned char up = (unsigned char)(
        (input_mask & AVSP_PW_INPUT_UP) != 0u);
    unsigned char facing = runtime->player.facing;
    if (down)
    {
        const AvspRound1PlayerJumpVectorSpec *vector =
            &avsp_round1_player_jump_down_vectors[horizontal ? 1u : 0u];
        if (horizontal)
        {
            facing = right;
            runtime->player.facing = facing;
            runtime->player_action.facing = facing;
        }
        runtime->player_jump_x_velocity = vector->x_velocity;
        runtime->player_jump_x_acceleration = vector->x_acceleration;
        runtime->player_jump_phase = 0x040au;
        runtime->player_jump_airborne_latch = 0u;
        runtime->player_jump_collision_selector = 7u;
        runtime->player.source_action = 0x040au;
        return avsp_round1_bind_player_jump_sequence(
            runtime, horizontal ? 41u : 60u);
    }
    else
    {
        unsigned int index = 0u;
        unsigned char selector = 4u;
        const AvspRound1PlayerJumpVectorSpec *vector;
        if (up)
            index += 1u;
        if (horizontal)
        {
            index = 2u + (up ? 1u : 0u);
            runtime->player_jump_direction_class = right ? 2u : 1u;
            if ((unsigned char)(right ^ facing) != 0u)
                index += 2u;
        }
        vector = &avsp_round1_player_jump_vectors[index];
        runtime->player_jump_x_velocity = vector->x_velocity;
        runtime->player_jump_x_acceleration = vector->x_acceleration;
        runtime->player_jump_y_velocity = vector->y_velocity;
        runtime->player_jump_y_acceleration = vector->y_acceleration;
        if (facing != 0u)
        {
            runtime->player_jump_x_velocity =
                -runtime->player_jump_x_velocity;
            runtime->player_jump_x_acceleration =
                -runtime->player_jump_x_acceleration;
        }
        runtime->player_jump_phase = 0x0402u;
        runtime->player_jump_airborne_latch = 1u;
        runtime->player_jump_collision_selector = 3u;
        if (horizontal)
        {
            if ((unsigned char)(right ^ facing) == 0u)
            {
                runtime->player_jump_collision_selector = up ? 1u : 2u;
                selector = (unsigned char)(facing + 5u);
            }
            else
            {
                runtime->player_jump_collision_selector = up ? 4u : 8u;
                selector = up ? 6u : 15u;
            }
        }
        runtime->player.source_action = 0x0402u;
        return avsp_round1_bind_player_jump_sequence(runtime, selector);
    }
}

static int avsp_round1_step_player_jump(AvspRound1Runtime *runtime,
                                        unsigned short input_mask)
{
    if (!runtime->player_jump_active)
        return 1;
    if (runtime->player_jump_phase == 0x0400u)
    {
        if (runtime->player_jump_animation_branch >= 0)
            return avsp_round1_step_player_jump_animation(runtime);
        return avsp_round1_initialize_player_jump(runtime, input_mask);
    }
    if (runtime->player_jump_phase == 0x0402u)
    {
        long prior_velocity = runtime->player_jump_x_velocity;
        runtime->player_jump_x_fp += prior_velocity;
        runtime->player_jump_x_velocity += runtime->player_jump_x_acceleration;
        if ((prior_velocity < 0L) !=
            (runtime->player_jump_x_velocity < 0L))
        {
            runtime->player_jump_x_velocity = 0L;
            runtime->player_jump_x_acceleration = 0L;
        }
        runtime->player_jump_y_fp += runtime->player_jump_y_velocity;
        runtime->player_jump_y_velocity += runtime->player_jump_y_acceleration;
        runtime->player_action.x = avsp_round1_fixed_high_word(
            runtime->player_jump_x_fp);
        runtime->player_action.height = (short)(
            avsp_round1_fixed_high_word(runtime->player_jump_y_fp) -
            runtime->player_action.lane);
        ++runtime->player_jump_motion_updates;
        if (avsp_round1_fixed_high_word(runtime->player_jump_y_fp) <=
            runtime->player_action.lane)
        {
            runtime->player_jump_y_fp =
                (long)runtime->player_action.lane * 65536L;
            runtime->player_action.height = 0;
            runtime->player_jump_phase = 0x0404u;
            runtime->player_jump_airborne_latch = 0u;
            runtime->player.source_action = 0x0404u;
            ++runtime->player_jump_landings;
            return avsp_round1_bind_player_jump_sequence(runtime, 10u);
        }
        return avsp_round1_step_player_jump_animation(runtime);
    }
    if (runtime->player_jump_phase == 0x0404u)
    {
        if (runtime->player_jump_animation_branch < 0)
        {
            avsp_round1_finish_player_jump(runtime);
            return 1;
        }
        return avsp_round1_step_player_jump_animation(runtime);
    }
    if (runtime->player_jump_phase == 0x040au)
    {
        long delta = runtime->player_jump_x_velocity;
        if (runtime->player.facing == 0u)
            delta = -delta;
        runtime->player_jump_x_fp += delta;
        runtime->player_jump_x_velocity += runtime->player_jump_x_acceleration;
        runtime->player_action.x = avsp_round1_fixed_high_word(
            runtime->player_jump_x_fp);
        ++runtime->player_jump_motion_updates;
        if (runtime->player_jump_x_velocity < 0L)
        {
            runtime->player_jump_phase = 0x040cu;
            runtime->player_jump_phase_timer = 10u;
            runtime->player.source_action = 0x040cu;
            return avsp_round1_bind_player_jump_sequence(runtime, 42u);
        }
        return avsp_round1_step_player_jump_animation(runtime);
    }
    if (runtime->player_jump_phase == 0x040cu)
    {
        if (runtime->player_jump_phase_timer == 0u)
            return 0;
        --runtime->player_jump_phase_timer;
        if (runtime->player_jump_phase_timer == 0u)
        {
            avsp_round1_finish_player_jump(runtime);
            return 1;
        }
        return avsp_round1_step_player_jump_animation(runtime);
    }
    return 0;
}

static int avsp_round1_player_jump_contract_valid(void)
{
    const AvspRound1PlayerJumpSequenceSpec *sequence6 =
        avsp_round1_find_player_jump_sequence(6u);
    const AvspRound1PlayerJumpSequenceSpec *sequence41 =
        avsp_round1_find_player_jump_sequence(41u);
    const AvspRound1PlayerJumpSequenceSpec *sequence60 =
        avsp_round1_find_player_jump_sequence(60u);
    return avsp_round1_player_jump_vectors[2].x_velocity == -0x000f0000L &&
        avsp_round1_player_jump_vectors[4].x_acceleration == -0x00002000L &&
        avsp_round1_player_jump_vectors[5].y_velocity == 0x000c0000L &&
        avsp_round1_player_jump_down_vectors[0].x_velocity == 0x00060000L &&
        avsp_round1_player_jump_down_vectors[1].x_acceleration == -0x0000a000L &&
        sequence6 != 0 && sequence6->record_count == 8u &&
        sequence6->records[0].animation_record == 0x0015f3b8UL &&
        sequence41 != 0 && sequence41->record_count == 2u &&
        sequence41->records[0].attack_selector == 22u &&
        sequence41->records[1].attack_selector == 23u &&
        sequence60 != 0 && sequence60->record_count == 1u &&
        sequence60->records[0].attack_selector == 35u;
}

static const AvspRound1AnimationSequenceSpec *
avsp_round1_find_initial_class1f_sequence(unsigned char selector)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_INITIAL_SEQUENCE_COUNT;
         ++index)
        if (avsp_round1_class1f_initial_sequences[index].selector == selector)
            return &avsp_round1_class1f_initial_sequences[index];
    return 0;
}

static int avsp_round1_bind_class1f_sequence(AvspRound1ActorCore *actor,
                                             unsigned char selector)
{
    const AvspRound1AnimationSequenceSpec *sequence =
        avsp_round1_find_initial_class1f_sequence(selector);
    if (sequence == 0 || sequence->record_count == 0u)
        return 0;
    actor->animation_index = 0u;
    avsp_round1_bind_animation_state(actor, &sequence->records[0]);
    return 1;
}

static int avsp_round1_step_class1f_animation(AvspRound1ActorCore *actor,
                                              unsigned char selector)
{
    const AvspRound1AnimationSequenceSpec *sequence =
        avsp_round1_find_initial_class1f_sequence(selector);
    unsigned char next;
    if (sequence == 0 || actor->animation_index >= sequence->record_count ||
        actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    next = (unsigned char)(actor->animation_index + 1u);
    if (actor->animation_branch < 0)
    {
        if (sequence->terminal_policy ==
            AVSP_ROUND1_ANIMATION_TERMINAL_LOOP_FIRST)
            next = 0u;
        else if (sequence->terminal_policy ==
                 AVSP_ROUND1_ANIMATION_TERMINAL_SELF_LOOP)
            next = actor->animation_index;
        else
            return 1;
    }
    if (next >= sequence->record_count)
        return 0;
    actor->animation_index = next;
    avsp_round1_bind_animation_state(actor, &sequence->records[next]);
    return 1;
}

static AvspRound1Class1fTransitionRuntime *
avsp_round1_find_class1f_transition(AvspRound1Runtime *runtime,
                                    unsigned long source_slot)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT;
         ++index)
        if (runtime->class1f_transition[index].source_slot == source_slot)
            return &runtime->class1f_transition[index];
    return 0;
}

static int avsp_round1_allocate_class4e_effects(AvspRound1Runtime *runtime)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT; ++index)
    {
        const AvspRound1Class4eSpawnSpec *spec =
            &avsp_round1_class4e_initial_spawns[index];
        AvspRound1ActorCore *actor;
        ++runtime->class1f_effect_requests;
        actor = avsp_round1_allocate_pool_actor(runtime, 3u);
        if (actor == 0)
        {
            ++runtime->class1f_effect_allocation_failures;
            continue;
        }
        if ((unsigned short)actor->source_slot !=
            (unsigned short)spec->source_slot)
            return 0;
        actor->actor_class = 0x4e;
        actor->variant = 4u;
        actor->state = 0u;
        actor->x = spec->x;
        actor->y = spec->y;
        actor->z = spec->z;
        ++runtime->class1f_effect_allocations;
    }
    return 1;
}

static int avsp_round1_initialize_class1f(AvspRound1Runtime *runtime,
                                          AvspRound1ActorCore *actor)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_INITIAL_ACTOR_COUNT; ++index)
    {
        const AvspRound1Class1fInitialSpec *spec =
            &avsp_round1_class1f_initial_actors[index];
        if (spec->source_slot != actor->source_slot)
            continue;
        if (actor->state != spec->state || actor->substate != spec->substate ||
            actor->x != spec->x || actor->y != spec->y || actor->z != spec->z ||
            actor->facing != spec->facing)
            return 0;
        (void)avsp_round1_source_rng(runtime);
        ++runtime->class1f_initial_rng_calls;
        actor->source_flags = spec->source_flags;
        actor->coordinate_mode = spec->coordinate_mode;
        actor->palette = spec->palette;
        actor->object_or = spec->object_or;
        actor->transition_timer = spec->transition_timer_initial;
        if (!avsp_round1_bind_class1f_sequence(actor,
                                               spec->animation_selector))
            return 0;
        if (index >= AVSP_ROUND1_CLASS1F_INITIAL_ACTOR_COUNT -
                     AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT)
        {
            unsigned int transition_index = index -
                (AVSP_ROUND1_CLASS1F_INITIAL_ACTOR_COUNT -
                 AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT);
            runtime->class1f_transition[transition_index].source_slot =
                actor->source_slot;
            runtime->class1f_transition[transition_index].active = 1u;
        }
        ++runtime->class1f_initializations;
        return 1;
    }
    return 0;
}

static int avsp_round1_step_initial_class1f(AvspRound1Runtime *runtime,
                                            AvspRound1ActorCore *actor)
{
    AvspRound1Class1fTransitionRuntime *transition;
    unsigned short phase = actor->substate;
    if (actor->handler_updates == 0u)
        return avsp_round1_initialize_class1f(runtime, actor);
    ++runtime->class1f_transition_updates;
    if (phase == 0x1000u || phase == 0x1200u)
    {
        unsigned char selector = phase == 0x1000u ? 1u : 0u;
        if (actor->transition_timer == 0u)
            return 0;
        --actor->transition_timer;
        if (actor->transition_timer == 0u)
        {
            actor->substate = 0u;
            ++runtime->class1f_transition_completions;
            return 1;
        }
        return avsp_round1_step_class1f_animation(actor, selector);
    }
    transition = avsp_round1_find_class1f_transition(runtime,
                                                     actor->source_slot);
    if (transition == 0 || !transition->active)
        return 0;
    if (phase == 0x1400u)
    {
        if (runtime->entry.source_global_8209 != 2u)
            return avsp_round1_step_class1f_animation(actor, 1u);
        if (actor->transition_timer == 0u)
            return 0;
        --actor->transition_timer;
        if (actor->transition_timer != 0u)
            return avsp_round1_step_class1f_animation(actor, 1u);
        actor->substate = 0x1402u;
        return avsp_round1_bind_class1f_sequence(actor, 60u);
    }
    if (phase == 0x1402u)
    {
        if (actor->animation_branch >= 0)
            return avsp_round1_step_class1f_animation(actor, 60u);
        actor->substate = 0x1404u;
        actor->coordinate_mode = 1u;
        actor->effect_timer = 42u;
        transition->x_fp = (long)actor->x * 65536L;
        transition->y_fp = (long)actor->y * 65536L;
        transition->x_velocity = actor->facing == 0u ? -0x00030000L :
            0x00030000L;
        transition->y_velocity = 0x00091000L;
        transition->y_acceleration = -0x00005000L;
        return avsp_round1_bind_class1f_sequence(actor, 76u);
    }
    if (phase == 0x1404u)
    {
        actor->effect_timer = (unsigned char)(actor->effect_timer - 1u);
        if (actor->effect_timer == 0u && runtime->class1f_effect_guard == 0u)
        {
            unsigned int index;
            runtime->class1f_effect_guard = 1u;
            for (index = 0u; index < AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT;
                 ++index)
                if (runtime->class1f_transition[index].source_slot ==
                        actor->source_slot)
                {
                    unsigned short command =
                        avsp_round1_class1f_initial_audio_commands[index];
                    if (command != 0u)
                    {
                        runtime->class1f_audio_command = command;
                        ++runtime->class1f_audio_events;
                    }
                    break;
                }
            if (!avsp_round1_allocate_class4e_effects(runtime))
                return 0;
        }
        transition->x_fp += transition->x_velocity;
        transition->y_fp += transition->y_velocity;
        transition->y_velocity += transition->y_acceleration;
        actor->x = avsp_round1_fixed_high_word(transition->x_fp);
        actor->y = avsp_round1_fixed_high_word(transition->y_fp);
        if ((unsigned short)actor->z < (unsigned short)actor->y)
            return avsp_round1_step_class1f_animation(actor, 76u);
        actor->y = actor->z;
        transition->y_fp = (long)actor->z * 65536L;
        actor->coordinate_mode = 0u;
        actor->substate = 0x1406u;
        return avsp_round1_bind_class1f_sequence(actor, 62u);
    }
    if (phase == 0x1406u)
    {
        if (actor->animation_branch >= 0)
            return avsp_round1_step_class1f_animation(actor, 62u);
        actor->transition_timer = 64u;
        actor->substate = 0x1408u;
        return avsp_round1_bind_class1f_sequence(actor, 52u);
    }
    if (phase == 0x1408u)
    {
        if (actor->transition_timer == 0u)
            return 0;
        --actor->transition_timer;
        if (actor->transition_timer == 0u)
        {
            actor->substate = 0u;
            transition->active = 0u;
            ++runtime->class1f_transition_completions;
            return 1;
        }
        return avsp_round1_step_class1f_animation(actor, 52u);
    }
    return 0;
}

static int avsp_round1_find_class09_sequence(unsigned char selector)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS09_SEQUENCE_COUNT; ++index)
        if (avsp_round1_class09_sequence_selectors[index] == selector)
            return (int)index;
    return -1;
}

static int avsp_round1_step_class09(AvspRound1Runtime *runtime,
                                    AvspRound1ActorCore *actor)
{
    int sequence_index = avsp_round1_find_class09_sequence(
        actor->source_action == 0u ? 0u : (unsigned char)actor->source_action);
    if (actor->state != 0x0200u || sequence_index < 0)
        return 0;
    if (actor->animation_branch < 0)
    {
        unsigned char random = avsp_round1_source_rng(runtime);
        unsigned char selector = avsp_round1_class09_selector_table[
            (random & 0x0eu) >> 1];
        sequence_index = avsp_round1_find_class09_sequence(selector);
        if (sequence_index < 0)
            return 0;
        actor->source_action = selector;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_class09_sequences[sequence_index][0]);
        ++runtime->class09_rng_calls;
    }
    if (actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer == 0u && actor->animation_branch >= 0)
    {
        if (actor->animation_index + 1u >=
            AVSP_ROUND1_CLASS09_SEQUENCE_RECORDS)
            return 0;
        ++actor->animation_index;
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_class09_sequences[sequence_index]
                [actor->animation_index]);
    }
    return 1;
}

static int avsp_round1_step_class4e(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor)
{
    if (actor->variant != 4u)
        return 0;
    if (actor->state == 0u)
    {
        unsigned char random = avsp_round1_source_rng(runtime);
        unsigned char table_offset;
        unsigned char jitter_index;
        const AvspRound1VecS16 *jitter;
        if (actor->source_slot == 0xc480u)
            table_offset = 28u;
        else if (actor->source_slot == 0xc500u)
            table_offset = 24u;
        else
            return 0;
        if ((actor->source_slot == 0xc480u && runtime->rng_seed != 0xcdb5u) ||
            (actor->source_slot == 0xc500u && runtime->rng_seed != 0x691eu))
            return 0;
        (void)random;
        jitter_index = (unsigned char)(table_offset >> 2);
        jitter = &avsp_round1_class4e_jitter[jitter_index];
        actor->x = (short)(actor->x + jitter->x);
        actor->y = (short)(actor->y + jitter->y);
        actor->state = 0x0200u;
        actor->coordinate_mode = 2u;
        actor->object_or = 0x8000u;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
                                         &avsp_round1_class4e_records[0]);
        ++runtime->class4e_initializations;
        ++runtime->class4e_rng_calls;
        return 1;
    }
    if (actor->state == 0x0200u)
    {
        if (actor->animation_branch < 0)
        {
            actor->state = 0x0400u;
            return 1;
        }
        if (actor->animation_timer == 0u)
            return 0;
        --actor->animation_timer;
        if (actor->animation_timer == 0u)
        {
            if (actor->animation_index + 1u >=
                AVSP_ROUND1_CLASS4E_PRESENTATION_COUNT)
                return 0;
            ++actor->animation_index;
            avsp_round1_bind_animation_state(actor,
                &avsp_round1_class4e_records[actor->animation_index]);
        }
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class4e_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_step_class44_guard(AvspRound1Runtime *runtime,
                                          AvspRound1ActorCore *actor)
{
    if (actor->source_slot != (unsigned short)avsp_round1_class44_guard.source_slot ||
        actor->dispatch_entry != avsp_round1_class44_guard.dispatch)
        return 0;
    ++runtime->class44_guard_updates;
    if (actor->state == 0x0200u)
    {
        if (runtime->class1f_effect_guard != 0u)
            actor->state = 0x0400u;
        return 1;
    }
    if (actor->state == 0x0400u && actor->substate == 0u)
    {
        runtime->class1f_effect_guard = 0u;
        actor->substate = 0x0402u;
        actor->effect_timer = 3u;
        ++runtime->class44_guard_clears;
        return 1;
    }
    if (actor->state == 0x0400u && actor->substate == 0x0402u)
    {
        if (actor->effect_timer == 0u)
            return 0;
        --actor->effect_timer;
        if (actor->effect_timer == 0u)
        {
            actor->substate = 0x0404u;
            actor->animation_index = 1u;
            avsp_round1_bind_animation_state(actor,
                                             &avsp_round1_class44_records[1]);
        }
        return 1;
    }
    if (actor->state == 0x0400u && actor->substate == 0x0404u)
        return 1;
    return 0;
}

static int avsp_round1_seed_first_segment_dependencies(
    AvspRound1Runtime *runtime)
{
    AvspRound1Pool *pool20 = &runtime->pools[2];
    AvspRound1Pool *pool24 = &runtime->pools[3];
    unsigned int spec_index;
    unsigned int slot_index;
    unsigned int free_index = 0u;
    for (spec_index = 0u; spec_index < AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT;
         ++spec_index)
    {
        const AvspRound1Class09InitialSpec *spec =
            &avsp_round1_class09_initial_actors[spec_index];
        unsigned short slot = (unsigned short)spec->source_slot;
        unsigned int index;
        AvspRound1ActorCore *actor;
        if (slot < pool20->source_base ||
            ((unsigned int)(slot - pool20->source_base) % pool20->stride) != 0u)
            return 0;
        index = (unsigned int)(slot - pool20->source_base) / pool20->stride;
        if (index >= pool20->capacity)
            return 0;
        actor = &pool20->records[index];
        memset(actor, 0, sizeof(*actor));
        actor->active = 1u;
        actor->actor_class = 0x09;
        actor->type = 20u;
        actor->source_slot = spec->source_slot;
        actor->x = spec->x;
        actor->y = spec->y;
        actor->z = spec->z;
        actor->state = spec->state;
        actor->substate = spec->substate;
        actor->facing = spec->facing;
        actor->source_action = 0u;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_class09_sequences[0][0]);
        if (actor->animation_record != spec->animation_record)
            return 0;
        ++runtime->class09_initializations;
    }
    {
        const AvspRound1ObstacleSpec *spec =
            &avsp_round1_coffee_shop_obstacle;
        unsigned short slot = (unsigned short)spec->source_slot;
        unsigned int index;
        AvspRound1ActorCore *actor;
        if (slot < pool20->source_base ||
            ((unsigned int)(slot - pool20->source_base) % pool20->stride) != 0u)
            return 0;
        index = (unsigned int)(slot - pool20->source_base) / pool20->stride;
        if (index >= pool20->capacity)
            return 0;
        actor = &pool20->records[index];
        memset(actor, 0, sizeof(*actor));
        actor->active = 1u;
        actor->actor_class = spec->actor_class;
        actor->type = spec->type;
        actor->source_slot = spec->source_slot;
        actor->state = spec->state;
        actor->substate = spec->substate;
        actor->x = spec->x;
        actor->y = spec->y;
        actor->z = spec->z;
        actor->facing = spec->facing;
        actor->animation_record = spec->animation_record;
        actor->assembly = spec->assembly;
        actor->hurt_selector = spec->hurt_selector;
        actor->attack_selector = spec->attack_selector;
    }
    for (slot_index = 0u; slot_index < pool20->capacity; ++slot_index)
    {
        unsigned short slot = (unsigned short)(pool20->source_base +
                                               slot_index * pool20->stride);
        if (slot == (unsigned short)avsp_round1_class09_initial_actors[0].source_slot ||
            slot == (unsigned short)avsp_round1_class09_initial_actors[1].source_slot ||
            slot == (unsigned short)avsp_round1_coffee_shop_obstacle.source_slot)
            continue;
        pool20->free_stack[free_index++] = slot;
    }
    pool20->free_count = (unsigned char)free_index;
    {
        unsigned short slot = (unsigned short)avsp_round1_class44_guard.source_slot;
        unsigned int index = (unsigned int)(slot - pool24->source_base) /
            pool24->stride;
        AvspRound1ActorCore *actor;
        if (slot < pool24->source_base || index >= pool24->capacity)
            return 0;
        actor = &pool24->records[index];
        memset(actor, 0, sizeof(*actor));
        actor->active = 1u;
        actor->actor_class = 0x44;
        actor->type = 24u;
        actor->source_slot = slot;
        actor->x = avsp_round1_class44_guard.x;
        actor->y = avsp_round1_class44_guard.y;
        actor->z = avsp_round1_class44_guard.z;
        actor->state = avsp_round1_class44_guard.state;
        actor->substate = avsp_round1_class44_guard.substate;
        actor->dispatch_entry = avsp_round1_class44_guard.dispatch;
        actor->coordinate_mode = avsp_round1_class44_guard.coordinate_mode;
        actor->palette = avsp_round1_class44_guard.palette;
        actor->facing = avsp_round1_class44_guard.facing;
        actor->object_or = avsp_round1_class44_guard.object_or;
        avsp_round1_bind_animation_state(actor, &avsp_round1_class44_records[0]);
    }
    pool24->free_stack[0] = 0xc480u;
    pool24->free_stack[1] = 0xc500u;
    pool24->free_count = 2u;
    return 1;
}

static void avsp_round1_bind_projectile_animation(
    AvspRound1WeaponProjectileAllocation *projectile)
{
    unsigned char sequence =
        avsp_round1_weapon_projectile_animation_selectors[
            projectile->parent_presentation_selector];
    const AvspRound1AnimationStateSpec *record =
        &avsp_round1_weapon_projectile_presentations[sequence]
            [projectile->presentation_index];
    projectile->animation_timer = record->timer;
    projectile->animation_branch = record->branch;
    projectile->animation_record = record->animation_record;
    projectile->assembly = record->assembly;
    projectile->attack_selector = record->attack_selector;
}

static int avsp_round1_release_player_weapon_projectile(
    AvspRound1Runtime *runtime, unsigned int index)
{
    AvspRound1WeaponProjectileAllocation *projectile;
    if (index >= AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY ||
        runtime->player_weapon_projectile_free_count >=
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY)
        return 0;
    projectile = &runtime->player_weapon_projectiles[index];
    if (!projectile->active)
        return 0;
    runtime->player_weapon_projectile_free_stack[
        runtime->player_weapon_projectile_free_count] = (unsigned char)index;
    ++runtime->player_weapon_projectile_free_count;
    memset(projectile, 0, sizeof(*projectile));
    ++runtime->player_weapon_projectile_releases;
    return 1;
}

static int avsp_round1_begin_weapon_impact(AvspRound1Runtime *runtime,
                                           short x, short y, short z)
{
    AvspRound1ActorCore *actor;
    ++runtime->player_weapon_impact_requests;
    actor = avsp_round1_allocate_pool_actor(runtime, 3u);
    if (actor == 0)
    {
        ++runtime->player_weapon_impact_allocation_failures;
        return 0;
    }
    actor->actor_class = avsp_round1_weapon_impact.actor_class;
    actor->variant = avsp_round1_weapon_impact.variant;
    actor->state = avsp_round1_weapon_impact.initial_state;
    actor->substate = 0u;
    actor->x = x;
    actor->y = y;
    actor->z = z;
    ++runtime->player_weapon_impact_allocations;
    return 1;
}

static int avsp_round1_step_weapon_projectile(
    AvspRound1Runtime *runtime, unsigned int index)
{
    AvspRound1WeaponProjectileAllocation *projectile =
        &runtime->player_weapon_projectiles[index];
    const AvspRound1VecS16 *motion;
    unsigned short x_distance;
    unsigned short y_distance;
    if (projectile->state == avsp_round1_weapon_projectile.initial_state)
    {
        const AvspRound1VecS16 *offset;
        if (projectile->parent_presentation_selector >=
            AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT)
            return 0;
        offset = &avsp_round1_weapon_projectile_spawn_offsets[
            projectile->parent_presentation_selector];
        projectile->x = (short)(projectile->x +
            (projectile->facing == 0u ? -offset->x : offset->x));
        projectile->y = (short)(projectile->y + offset->y);
        projectile->z = (short)(projectile->z + 1);
        projectile->x_fp = (long)projectile->x * 65536L;
        projectile->y_fp = (long)projectile->y * 65536L;
        projectile->z_fp = (long)projectile->z * 65536L;
        projectile->collision_result = 0;
        projectile->active_collision = 1u;
        projectile->coordinate_mode =
            avsp_round1_weapon_projectile.coordinate_mode;
        projectile->palette = avsp_round1_weapon_projectile.palette;
        projectile->object_or = avsp_round1_weapon_projectile.object_or;
        projectile->presentation_index = 0u;
        avsp_round1_bind_projectile_animation(projectile);
        projectile->state = avsp_round1_weapon_projectile.active_state;
        ++runtime->player_weapon_projectile_initializations;
        return 1;
    }
    if (projectile->state == avsp_round1_weapon_projectile.active_state)
    {
        if (projectile->collision_result < 0)
        {
            projectile->state = avsp_round1_weapon_projectile.release_state;
            return 1;
        }
        x_distance = (unsigned short)(projectile->x -
            runtime->navigation_bound_x +
            avsp_round1_weapon_projectile.x_bound_bias);
        if (x_distance > avsp_round1_weapon_projectile.x_bound_span)
            return avsp_round1_release_player_weapon_projectile(runtime,
                                                                 index);
        y_distance = (unsigned short)(projectile->y -
            runtime->navigation_bound_z +
            avsp_round1_weapon_projectile.y_bound_bias);
        if (y_distance > avsp_round1_weapon_projectile.y_bound_span)
            return avsp_round1_release_player_weapon_projectile(runtime,
                                                                 index);
        if ((unsigned short)projectile->y < (unsigned short)projectile->z)
        {
            projectile->state = avsp_round1_weapon_projectile.impact_state;
            avsp_round1_begin_weapon_impact(runtime, projectile->x,
                projectile->y, projectile->z);
            projectile->state = avsp_round1_weapon_projectile.release_state;
            return 1;
        }
        motion = &avsp_round1_weapon_projectile_motion[projectile->angle & 0x3fu];
        projectile->x_fp += (long)motion->x * 256L;
        projectile->y_fp += (long)motion->y * 256L;
        projectile->x = avsp_round1_fixed_high_word(projectile->x_fp);
        projectile->y = avsp_round1_fixed_high_word(projectile->y_fp);
        ++runtime->player_weapon_projectile_motion_updates;
        if (projectile->animation_timer > 0u)
            --projectile->animation_timer;
        if (projectile->animation_timer == 0u &&
            projectile->presentation_index == 0u)
        {
            projectile->presentation_index = 1u;
            avsp_round1_bind_projectile_animation(projectile);
        }
        return 1;
    }
    if (projectile->state == avsp_round1_weapon_projectile.impact_state)
    {
        avsp_round1_begin_weapon_impact(runtime, projectile->x,
            projectile->y, projectile->z);
        projectile->state = avsp_round1_weapon_projectile.release_state;
        return 1;
    }
    if (projectile->state == avsp_round1_weapon_projectile.release_state)
        return avsp_round1_release_player_weapon_projectile(runtime, index);
    return 0;
}

static int avsp_round1_damage_value(unsigned char attacker_class_index,
                                    unsigned char defender_class_index,
                                    unsigned short route_index,
                                    unsigned char attack_selector,
                                    unsigned char *damage)
{
    unsigned int index;
    int offense = -1;
    int defense = -1;
    for (index = 0u; index < AVSP_ROUND1_WEAPON_DAMAGE_OFFENSE_COUNT; ++index)
        if (avsp_round1_weapon_damage_offense[index].class_index ==
                attacker_class_index &&
            avsp_round1_weapon_damage_offense[index].route_index == route_index)
            offense = avsp_round1_weapon_damage_offense[index].value;
    for (index = 0u; index < AVSP_ROUND1_WEAPON_DAMAGE_DEFENSE_COUNT; ++index)
        if (avsp_round1_weapon_damage_defense[index].class_index ==
                defender_class_index &&
            avsp_round1_weapon_damage_defense[index].route_index == route_index)
            defense = avsp_round1_weapon_damage_defense[index].value;
    if (offense < 0 || defense < 0)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_WEAPON_DAMAGE_MATRIX_COUNT; ++index)
        if (avsp_round1_weapon_damage_matrix[index].defense ==
                (unsigned char)defense &&
            avsp_round1_weapon_damage_matrix[index].damage_index ==
                (unsigned char)(offense + attack_selector))
        {
            *damage = avsp_round1_weapon_damage_matrix[index].damage;
            return 1;
        }
    return 0;
}

static int avsp_round1_projectile_collision_pass(
    AvspRound1Runtime *runtime,
    AvspRound1WeaponProjectileAllocation *projectile)
{
    AvspAttackBox attack;
    AvspBox hurt;
    AvspActor attacker;
    AvspActor defender;
    unsigned int index;
    unsigned char damage;
    const AvspRound1CollisionBoxSpec *box;
    if (projectile->state != avsp_round1_weapon_projectile.active_state ||
        !projectile->active_collision || projectile->attack_selector == 0u ||
        projectile->attack_selector >=
            AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT)
        return 1;
    box = &avsp_round1_weapon_projectile_attack_boxes[
        projectile->attack_selector];
    memset(&attack, 0, sizeof(attack));
    attack.box.x_center = box->x_center;
    attack.box.y_center = box->y_center;
    attack.box.x_half = box->x_half;
    attack.box.y_half = box->y_half;
    attack.box.z_center = box->z_center;
    attack.box.z_half = box->z_half;
    attack.hit_value = box->hit_value;
    attack.knockback_mode = box->knockback_mode;
    memset(&attacker, 0, sizeof(attacker));
    attacker.world_x = (unsigned short)projectile->x;
    attacker.world_y = (unsigned short)projectile->y;
    attacker.world_z = (unsigned short)projectile->z;
    attacker.facing = projectile->facing;
    for (index = 0u; index < runtime->pools[0].capacity; ++index)
    {
        AvspRound1ActorCore *target = &runtime->pools[0].records[index];
        short health;
        if (!target->active || target->actor_class != 0x1f ||
            target->hurt_selector == 0u || target->health < 0)
            continue;
        if (!avsp_collision_hurt_box(0x00130ac8UL,
                                     target->hurt_selector, &hurt))
            return 0;
        memset(&defender, 0, sizeof(defender));
        defender.world_x = (unsigned short)target->x;
        defender.world_y = (unsigned short)target->y;
        defender.world_z = (unsigned short)target->z;
        defender.facing = target->facing;
        if (!avsp_collision_overlap_boxes(&attacker, &attack, &defender,
                                          &hurt, 0))
            continue;
        if (!avsp_round1_damage_value(projectile->damage_class_index, 16u,
                                      10u, box->damage_selector, &damage))
            return 0;
        projectile->collision_result = -1;
        ++runtime->player_weapon_projectile_collision_writes;
        health = (short)(target->health - (short)damage);
        target->health = health < 0 ? -1 : health;
        target->substate = 0x0200u;
        ++runtime->player_weapon_projectile_damage_writes;
        return 1;
    }
    return 1;
}

static int avsp_round1_begin_empty_effect(AvspRound1Runtime *runtime)
{
    AvspRound1ActorCore *actor = avsp_round1_allocate_pool_actor(runtime, 3u);
    if (actor == 0)
    {
        ++runtime->player_weapon_empty_auxiliary_allocation_failures;
        return 0;
    }
    actor->actor_class = 0x10;
    actor->variant = 1u;
    actor->state = 0u;
    actor->substate = 0u;
    actor->x = runtime->player.x;
    actor->y = runtime->player.y;
    actor->source_facing_selector = runtime->player.facing;
    ++runtime->player_weapon_empty_auxiliary_allocations;
    return 1;
}

static void avsp_round1_bind_animation_state(
    AvspRound1ActorCore *actor, const AvspRound1AnimationStateSpec *record)
{
    actor->animation_timer = record->timer;
    actor->animation_branch = record->branch;
    actor->animation_record = record->animation_record;
    actor->assembly = record->assembly;
    actor->hurt_selector = record->hurt_selector;
    actor->attack_selector = record->attack_selector;
}

static int avsp_round1_step_empty_effect(AvspRound1Runtime *runtime,
                                         AvspRound1Pool *pool,
                                         AvspRound1ActorCore *actor)
{
    const AvspRound1AnimationStateSpec *record;
    if (actor->variant != 1u)
        return 0;
    if (actor->state == 0u)
    {
        const AvspRound1VecS16 *offset =
            &avsp_round1_empty_effect_variant_offsets[actor->variant];
        actor->state = 2u;
        actor->facing = 0u;
        actor->x = (short)(actor->x +
            (actor->source_facing_selector == 0u ? -offset->x : offset->x));
        actor->y = (short)(actor->y + offset->y);
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_empty_effect_variant1_records[0]);
        ++runtime->player_weapon_empty_auxiliary_presentation_bindings;
        return 1;
    }
    if (actor->state == 2u)
    {
        if (actor->animation_branch < 0)
            actor->state = 4u;
        if ((actor->animation_branch & 0x00ff) == 0)
            actor->y = (short)(actor->y + 4);
        if (actor->animation_timer == 0u)
            return 0;
        --actor->animation_timer;
        if (actor->animation_timer == 0u)
        {
            if (actor->animation_index + 1u >=
                AVSP_ROUND1_EMPTY_EFFECT_PRESENTATION_COUNT)
                return 0;
            ++actor->animation_index;
            record = &avsp_round1_empty_effect_variant1_records[
                actor->animation_index];
            avsp_round1_bind_animation_state(actor, record);
            ++runtime->player_weapon_empty_auxiliary_presentation_bindings;
        }
        return 1;
    }
    if (actor->state == 4u || actor->state == 6u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->player_weapon_empty_auxiliary_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_step_weapon_impact(AvspRound1Runtime *runtime,
                                          AvspRound1Pool *pool,
                                          AvspRound1ActorCore *actor)
{
    const AvspRound1AnimationStateSpec *record;
    if (actor->variant != avsp_round1_weapon_impact.variant)
        return 0;
    if (actor->state == avsp_round1_weapon_impact.initial_state)
    {
        unsigned char command_index =
            (unsigned char)(runtime->player_weapon_impact_audio_selector >> 1);
        if (command_index >= AVSP_ROUND1_WEAPON_IMPACT_AUDIO_COMMAND_COUNT)
            return 0;
        actor->state = avsp_round1_weapon_impact.active_state;
        actor->substate = 0u;
        actor->facing = 0u;
        actor->coordinate_mode = avsp_round1_weapon_impact.coordinate_mode;
        actor->palette = avsp_round1_weapon_impact.palette;
        actor->object_or = avsp_round1_weapon_impact.object_or;
        actor->dispatch_entry = avsp_round1_weapon_impact.dispatch;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_weapon_impact_variant0_records[0]);
        runtime->player_weapon_impact_audio_command =
            avsp_round1_weapon_impact.audio_commands[command_index];
        runtime->player_weapon_impact_audio_selector = (unsigned char)(
            (runtime->player_weapon_impact_audio_selector + 2u) & 2u);
        ++runtime->player_weapon_impact_audio_events;
        ++runtime->player_weapon_impact_presentation_bindings;
    }
    if (actor->state == avsp_round1_weapon_impact.active_state)
    {
        if (actor->animation_branch < 0)
            actor->state = avsp_round1_weapon_impact.release_state;
        if (actor->animation_timer > 0u)
            --actor->animation_timer;
        if (actor->animation_timer == 0u &&
            actor->animation_index + 1u <
                AVSP_ROUND1_WEAPON_IMPACT_PRESENTATION_COUNT)
        {
            ++actor->animation_index;
            record = &avsp_round1_weapon_impact_variant0_records[
                actor->animation_index];
            avsp_round1_bind_animation_state(actor, record);
            ++runtime->player_weapon_impact_presentation_bindings;
        }
        return 1;
    }
    if (actor->state == avsp_round1_weapon_impact.release_state ||
        actor->state == 6u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->player_weapon_impact_releases;
        return 1;
    }
    return 0;
}

int avsp_round1_is_weapon_impact_actor(const AvspRound1ActorCore *actor)
{
    return actor != 0 && actor->active &&
        actor->type == avsp_round1_weapon_impact.record_type &&
        actor->actor_class == avsp_round1_weapon_impact.actor_class;
}

static void avsp_round1_tick_player_resource(AvspRound1Runtime *runtime)
{
    if (runtime->player_resource >=
        avsp_round1_player_weapon.resource_capacity)
        return;
    if (runtime->player_resource_recharge > 0u)
        --runtime->player_resource_recharge;
    if (runtime->player_resource_recharge == 0u)
    {
        ++runtime->player_resource;
        ++runtime->player_resource_recharges;
        runtime->player_resource_recharge = runtime->player_resource_depleted ?
            avsp_round1_player_weapon.depleted_recharge_reload :
            avsp_round1_player_weapon.normal_recharge_reload;
        if (runtime->player_resource >=
            avsp_round1_player_weapon.resource_capacity)
        {
            runtime->player_resource =
                avsp_round1_player_weapon.resource_capacity;
            runtime->player_resource_depleted = 0u;
        }
    }
}

static void avsp_round1_begin_player_weapon(AvspRound1Runtime *runtime)
{
    runtime->player_weapon_active = 1u;
    runtime->player_weapon_empty =
        (unsigned char)(runtime->player_resource == 0u);
    runtime->player_weapon_tick = 0u;
    runtime->player_weapon_cadence =
        avsp_round1_player_weapon.cadence_initial;
    runtime->player_weapon_attempts =
        avsp_round1_player_weapon.attempt_initial;
    runtime->player_weapon_empty_timer =
        avsp_round1_player_weapon.empty_timer_initial;
    runtime->player_weapon_cleanup_pending = 0u;
    runtime->player_stop_ticks = 0u;
    runtime->player_was_directional = 0u;
    runtime->player_cleanup_pending = 0u;
    ++runtime->player_weapon_entries;
    if (runtime->player_weapon_empty)
    {
        runtime->player_resource_depleted = 1u;
        ++runtime->player_weapon_empty_auxiliary_requests;
        avsp_round1_begin_empty_effect(runtime);
    }
}

static int avsp_round1_step_player_weapon(AvspRound1Runtime *runtime,
                                          unsigned char weapon_pressed,
                                          unsigned char weapon_edge)
{
    const AvspRound1PlayerWeaponFrameSpec *frame;
    if (!runtime->player_weapon_active)
        return 0;
    if (runtime->player_action.state != AVSP_PW_STATE_CONTROL)
    {
        runtime->player_weapon_active = 0u;
        runtime->player_weapon_cleanup_pending = 0u;
        runtime->player_weapon_recovery_pending = 0u;
        ++runtime->player_weapon_interruptions;
        return 0;
    }
    if (weapon_edge && runtime->player_weapon_tick != 0u)
    {
        if (!runtime->player_weapon_empty && runtime->player_weapon_tick == 48u)
            runtime->player_weapon_recovery_pending = 1u;
        else
            ++runtime->player_weapon_held_suppressions;
    }
    else if (weapon_pressed && runtime->player_weapon_tick != 0u)
        ++runtime->player_weapon_held_suppressions;
    if (runtime->player_weapon_empty)
    {
        if (runtime->player_weapon_tick >=
            AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT)
        {
            ++runtime->failure_count;
            return 0;
        }
        frame = &avsp_round1_player_empty_frames[
            runtime->player_weapon_tick];
        avsp_round1_bind_player_weapon_frame(runtime, frame);
        if (runtime->player_weapon_tick > 0u &&
            runtime->player_weapon_tick < 17u &&
            runtime->player_weapon_empty_timer > 0u)
            --runtime->player_weapon_empty_timer;
        if (runtime->player_weapon_tick == 17u)
        {
            if (runtime->player_weapon_empty_timer != 0u)
                ++runtime->failure_count;
            runtime->player_weapon_active = 0u;
            runtime->player_weapon_cleanup_pending = 1u;
            ++runtime->player_weapon_completions;
        }
    }
    else
    {
        if (runtime->player_weapon_tick >=
            AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT)
        {
            ++runtime->failure_count;
            return 0;
        }
        frame = &avsp_round1_player_weapon_frames[
            runtime->player_weapon_tick];
        avsp_round1_bind_player_weapon_frame(runtime, frame);
        if (runtime->player_weapon_tick == 49u)
        {
            if (runtime->player_weapon_attempts >= 0)
                ++runtime->failure_count;
            runtime->player_weapon_active = 0u;
            runtime->player_weapon_cleanup_pending = 1u;
            ++runtime->player_weapon_completions;
        }
        else
        {
            if (runtime->player_weapon_cadence > 0u)
                --runtime->player_weapon_cadence;
            if (runtime->player_weapon_cadence == 0u)
            {
                runtime->player_weapon_cadence =
                    avsp_round1_player_weapon.cadence_reload;
                --runtime->player_weapon_attempts;
                if (runtime->player_weapon_attempts >= 0)
                {
                    ++runtime->player_weapon_attempts_total;
                    if (avsp_round1_allocate_player_weapon_projectile(runtime))
                    {
                        if (runtime->player_resource >
                            avsp_round1_player_weapon.resource_debit)
                            runtime->player_resource = (unsigned char)(
                                runtime->player_resource -
                                avsp_round1_player_weapon.resource_debit);
                        else
                        {
                            runtime->player_resource = 0u;
                            runtime->player_resource_depleted = 1u;
                        }
                        runtime->player_resource_recharge =
                            avsp_round1_player_weapon.recharge_after_success;
                        ++runtime->player_weapon_resource_debits;
                    }
                }
            }
        }
    }
    ++runtime->player_weapon_tick;
    return 1;
}

int avsp_round1_step_scheduler(AvspRound1Runtime *runtime)
{
    unsigned int order_index;
    unsigned int pool_index;
    unsigned int slot_index;
    unsigned long hash = 2166136261UL;
    if (runtime == 0 ||
        (runtime->route_state != 4 &&
         !(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&
           runtime->entry.spawned)) ||
        !avsp_round1_canaries_ok(runtime) || runtime->failure_count != 0u ||
        runtime->fallback_count != 0u)
    {
        if (runtime != 0)
            runtime->scheduler_failure_code = 14u;
        return 0;
    }
    runtime->scheduler_failure_code = 0u;
    runtime->scheduler_failure_source_slot = 0u;
    runtime->scheduler_failure_state = 0u;
    runtime->scheduler_failure_substate = 0u;
    runtime->scheduler_failure_animation_record = 0u;
    runtime->scheduler_trace_count = 0u;
    for (slot_index = 0u;
         slot_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++slot_index)
    {
        AvspRound1WeaponProjectileAllocation *projectile =
            &runtime->player_weapon_projectiles[slot_index];
        AvspRound1SchedulerVisit *visit;
        if (!projectile->active)
            continue;
        if (projectile->actor_class !=
                avsp_round1_player_weapon.projectile_class ||
            projectile->source_slot != (unsigned short)(
                avsp_round1_player_weapon.projectile_source_base +
                slot_index * avsp_round1_player_weapon.projectile_stride) ||
            runtime->scheduler_trace_count >=
                AVSP_ROUND1_SCHEDULER_TRACE_CAPACITY)
        {
            runtime->scheduler_failure_code = 1u;
            ++runtime->failure_count;
            return 0;
        }
        visit = &runtime->scheduler_trace[runtime->scheduler_trace_count++];
        visit->record_type = 4u;
        visit->actor_class = projectile->actor_class;
        visit->pool_slot = (unsigned short)slot_index;
        visit->source_slot = projectile->source_slot;
        hash = avsp_round1_scheduler_hash_byte(hash, 4u);
        hash = avsp_round1_scheduler_hash_byte(hash,
            (unsigned char)projectile->actor_class);
        hash = avsp_round1_scheduler_hash_byte(hash,
            (unsigned char)slot_index);
        ++runtime->player_weapon_projectile_scheduler_updates;
        ++runtime->scheduler_dispatches;
        if (!avsp_round1_step_weapon_projectile(runtime, slot_index))
        {
            runtime->scheduler_failure_code = 2u;
            ++runtime->failure_count;
            return 0;
        }
        if (projectile->active &&
            !avsp_round1_projectile_collision_pass(runtime, projectile))
        {
            runtime->scheduler_failure_code = 3u;
            ++runtime->failure_count;
            return 0;
        }
    }
    for (order_index = 0u; order_index < AVSP_ROUND1_SCHEDULER_POOL_COUNT;
         ++order_index)
    {
        pool_index = order_index;
        if (runtime->pools[pool_index].record_type !=
            avsp_round1_scheduler_pool_order[order_index] ||
            !avsp_round1_pool_metadata_valid(&runtime->pools[pool_index],
                                              pool_index))
        {
            runtime->scheduler_failure_code = 12u;
            ++runtime->failure_count;
            return 0;
        }
        for (slot_index = 0u;
             slot_index < runtime->pools[pool_index].capacity; ++slot_index)
        {
            AvspRound1ActorCore *actor =
                &runtime->pools[pool_index].records[slot_index];
            AvspRound1SchedulerVisit *visit;
            const AvspRound1PresentationSpec *presentation;
            unsigned short expected_slot;
            if (actor->active == 0u)
                continue;
            expected_slot = (unsigned short)(
                runtime->pools[pool_index].source_base +
                slot_index * runtime->pools[pool_index].stride);
            if (actor->type != runtime->pools[pool_index].record_type ||
                (unsigned short)actor->source_slot != expected_slot ||
                !avsp_round1_dispatch_supported(actor->type,
                                                actor->actor_class) ||
                runtime->scheduler_trace_count >=
                    AVSP_ROUND1_SCHEDULER_TRACE_CAPACITY)
            {
                runtime->scheduler_failure_code = 4u;
                ++runtime->failure_count;
                return 0;
            }
            visit = &runtime->scheduler_trace[
                runtime->scheduler_trace_count++];
            visit->record_type = actor->type;
            visit->actor_class = actor->actor_class;
            visit->pool_slot = (unsigned short)slot_index;
            visit->source_slot = actor->source_slot;
            hash = avsp_round1_scheduler_hash_byte(hash, actor->type);
            hash = avsp_round1_scheduler_hash_byte(hash,
                (unsigned char)actor->actor_class);
            hash = avsp_round1_scheduler_hash_byte(hash,
                (unsigned char)slot_index);
            if (actor->type == 24u && actor->actor_class == 0x10)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_empty_effect(runtime,
                        &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 5u;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 20u && actor->actor_class == 0x09)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class09(runtime, actor))
                {
                    runtime->scheduler_failure_code = 6u;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 24u && actor->actor_class == 0x4e)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class4e(runtime,
                        &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 7u;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 24u && actor->actor_class == 0x44)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class44_guard(runtime, actor))
                {
                    runtime->scheduler_failure_code = 8u;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == avsp_round1_weapon_impact.record_type &&
                actor->actor_class == avsp_round1_weapon_impact.actor_class)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_weapon_impact(runtime,
                        &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 13u;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 12u && actor->actor_class == 0x1f)
            {
                if (actor->handler_updates == 0u ||
                    actor->substate == 0x1000u || actor->substate == 0x1200u ||
                    actor->substate == 0x1400u || actor->substate == 0x1402u ||
                    actor->substate == 0x1404u || actor->substate == 0x1406u ||
                    actor->substate == 0x1408u)
                {
                    if (!avsp_round1_step_initial_class1f(runtime, actor))
                    {
                        runtime->scheduler_failure_code = 9u;
                        ++runtime->failure_count;
                        return 0;
                    }
                }
                presentation = avsp_round1_find_class1f_presentation(
                    actor->animation_record);
                if (presentation == 0)
                {
                    runtime->scheduler_failure_code = 10u;
                    ++runtime->failure_count;
                    return 0;
                }
                actor->assembly = presentation->assembly;
                actor->hurt_selector = presentation->hurt_selector;
                actor->attack_selector = presentation->attack_selector;
                if (!avsp_round1_class1f_state_context_supported(
                        actor->state, actor->substate))
                {
                    runtime->scheduler_failure_code = 11u;
                    runtime->scheduler_failure_source_slot = actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    runtime->scheduler_failure_substate = actor->substate;
                    runtime->scheduler_failure_animation_record =
                        actor->animation_record;
                    ++runtime->failure_count;
                    return 0;
                }
                actor->dispatch_entry = AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY;
                ++actor->handler_updates;
                ++actor->state_handler_updates;
                ++runtime->actor_handler_dispatches;
                ++runtime->presentation_bindings;
                ++runtime->state_context_bindings;
            }
            ++actor->scheduler_updates;
            ++runtime->scheduler_dispatches;
        }
    }
    runtime->scheduler_order_hash = hash;
    ++runtime->scheduler_frames;
    return 1;
}

int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime)
{
    return runtime != 0 && runtime->head_canary == AVSP_ROUND1_CANARY_HEAD &&
        runtime->tail_canary == AVSP_ROUND1_CANARY_TAIL;
}

void avsp_round1_init(AvspRound1Runtime *runtime)
{
    unsigned int pool_index;
    unsigned int slot_index;
    AvspRound1Pool *pool;

    if (runtime == 0)
        return;
    memset(runtime, 0, sizeof(*runtime));
    runtime->head_canary = AVSP_ROUND1_CANARY_HEAD;
    runtime->tail_canary = AVSP_ROUND1_CANARY_TAIL;
    runtime->route_state = AVSP_ROUND1_ROUTE_ENTRY_STATE;
    runtime->rng_seed = AVSP_ROUND1_INITIAL_RNG;
    runtime->player.active = 1u;
    runtime->player.actor_class = 0;
    runtime->player.type = 0u;
    runtime->player.state = 0u;
    runtime->player.substate = 0u;
    runtime->player.health = AVSP_ROUND1_PLAYER_HEALTH;
    runtime->player.source_slot = 0x00ff8380UL;
    runtime->player_resource = 64u;
    runtime->player_resource_recharge = 12u;
    runtime->player_weapon_projectile_free_count =
        AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
    for (slot_index = 0u;
         slot_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++slot_index)
        runtime->player_weapon_projectile_free_stack[slot_index] =
            (unsigned char)(AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY -
                            1u - slot_index);

    for (pool_index = 0u; pool_index < AVSP_ROUND1_POOL_COUNT; ++pool_index)
    {
        pool = &runtime->pools[pool_index];
        pool->record_type = avsp_round1_pool_types[pool_index];
        pool->capacity = avsp_round1_pool_capacities[pool_index];
        pool->stride = avsp_round1_pool_strides[pool_index];
        pool->source_base = avsp_round1_pool_bases[pool_index];
        pool->free_count = pool->capacity;
        for (slot_index = 0u; slot_index < pool->capacity; ++slot_index)
            pool->free_stack[slot_index] = (unsigned short)
                (pool->source_base + slot_index * pool->stride);
    }
}

int avsp_round1_begin_first_entry(AvspRound1Runtime *runtime)
{
    if (!avsp_round1_entry_valid(runtime) || runtime->entry.started)
        return 0;
    if (!avsp_round1_seed_first_segment_dependencies(runtime))
    {
        ++runtime->failure_count;
        return 0;
    }
    runtime->entry_controller.active = 1u;
    runtime->entry_controller.actor_class = 1;
    runtime->entry_controller.type = 32u;
    runtime->entry_controller.state = 514u;
    runtime->entry_controller.substate = 0u;
    runtime->entry_controller.source_slot = 0x00ffd180UL;
    runtime->entry.started = 1u;
    runtime->entry.gate8236 = 1u;
    runtime->entry.gate81af = 1u;
    runtime->entry.script_cursor = 0x00128FAAUL;
    runtime->player.state = AVSP_ROUND1_PLAYER_ENTRY_STATE;
    runtime->player.substate = 0u;
    runtime->player.x = 0;
    runtime->player.y = 0;
    runtime->player.z = 0;
    runtime->player.animation_record = 0x0015F1F4UL;
    return avsp_round1_entry_valid(runtime);
}

int avsp_round1_step_first_entry(AvspRound1Runtime *runtime)
{
    const AvspRound1EntryStepSpec *step;
    if (runtime == 0 || !runtime->entry.started ||
        !avsp_round1_canaries_ok(runtime) || runtime->failure_count != 0u ||
        runtime->fallback_count != 0u)
        return 0;
    if (runtime->route_state == 4)
        return avsp_round1_entry_valid(runtime);
    if (runtime->route_state != AVSP_ROUND1_ROUTE_ENTRY_STATE ||
        !avsp_round1_spawn_first_entry(runtime))
        return 0;

    if (runtime->entry.terminal_seen)
    {
        if ((runtime->entry.gate8236 & runtime->entry.gate81af) == 0u)
        {
            avsp_pw_init(&runtime->player_action);
            runtime->player_action.x = runtime->player.x;
            runtime->player_action.lane = runtime->player.z;
            runtime->player_action.health = runtime->player.health;
            runtime->player_action.facing = runtime->player.facing;
            runtime->route_state = 4;
            runtime->player.state = AVSP_ROUND1_PLAYER_CONTROL_STATE;
            runtime->entry.control_enabled = 1u;
            runtime->navigation_bounds_active = 1u;
            runtime->camera_x_previous =
                avsp_round1_coffee_shop_camera.initial_x;
            runtime->camera_x_position =
                avsp_round1_coffee_shop_camera.initial_x;
            runtime->camera_z_position =
                avsp_round1_coffee_shop_camera.initial_z;
            runtime->camera_x_target =
                avsp_round1_coffee_shop_camera.initial_x;
            runtime->camera_z_target =
                avsp_round1_coffee_shop_camera.initial_z;
            runtime->camera_x_target_previous =
                avsp_round1_coffee_shop_camera.initial_x;
            runtime->camera_z_target_previous =
                avsp_round1_coffee_shop_camera.initial_z;
            runtime->camera_x_lower =
                avsp_round1_coffee_shop_camera.initial_x_lower;
            runtime->camera_x_upper =
                avsp_round1_coffee_shop_camera.initial_x_upper;
            runtime->camera_z_upper =
                avsp_round1_coffee_shop_camera.initial_z_upper;
            runtime->camera_z_lower =
                avsp_round1_coffee_shop_camera.initial_z_lower;
            runtime->camera_guard_countdown =
                avsp_round1_coffee_shop_camera.guard_countdown;
            runtime->camera_scroll2_x = (short)(
                runtime->camera_x_position - 0x40);
            runtime->navigation_bound_x = runtime->camera_x_position;
            runtime->navigation_bound_z = runtime->camera_z_position;
            runtime->player_locomotion_action =
                avsp_round1_player_locomotion.cleanup_action;
            runtime->player.source_action =
                avsp_round1_player_locomotion.cleanup_action;
            runtime->player_cleanup_pending = 1u;
        }
        return avsp_round1_entry_valid(runtime);
    }
    if (runtime->entry.animation_c1 == 8u)
    {
        runtime->entry.animation_c1 = 0u;
        runtime->entry.animation_c2 = 0u;
        return avsp_round1_entry_valid(runtime);
    }
    if (runtime->entry.animation_c1 == 2u)
    {
        if (runtime->entry.animation_c8 == 0u)
        {
            ++runtime->failure_count;
            return 0;
        }
        --runtime->entry.animation_c8;
        ++runtime->entry.timer_decrements;
        if (runtime->entry.animation_c8 == 0u)
        {
            runtime->entry.animation_c1 = 0u;
            runtime->entry.animation_c2 = 0u;
        }
        return avsp_round1_entry_valid(runtime);
    }

    while (runtime->entry.step_index < AVSP_ROUND1_ENTRY_STEP_COUNT)
    {
        step = &avsp_round1_entry_steps[runtime->entry.step_index];
        if (runtime->entry.script_cursor != step->cursor)
        {
            ++runtime->failure_count;
            return 0;
        }
        runtime->entry.script_cursor = step->next_cursor;
        ++runtime->entry.step_index;
        if (step->kind == AVSP_ROUND1_ENTRY_SET_POSITION)
        {
            runtime->player.x = (short)step->arg0;
            runtime->player.y = (short)step->arg1;
            runtime->player.z = (short)step->arg1;
            runtime->entry.animation_c0 = 2u;
        }
        else if (step->kind == AVSP_ROUND1_ENTRY_SET_SUBHANDLER)
        {
            runtime->entry.animation_c1 = (unsigned char)step->arg0;
            runtime->entry.animation_c2 = 0u;
            return avsp_round1_entry_valid(runtime);
        }
        else if (step->kind == AVSP_ROUND1_ENTRY_SOURCE_18)
            runtime->entry.source18_argument = step->arg0;
        else if (step->kind == AVSP_ROUND1_ENTRY_DWELL)
        {
            runtime->entry.animation_c1 = 2u;
            runtime->entry.animation_c2 = (unsigned char)step->arg0;
            runtime->entry.animation_c8 = step->arg1;
            return avsp_round1_entry_valid(runtime);
        }
        else if (step->kind == AVSP_ROUND1_ENTRY_SOURCE_16)
            runtime->entry.source_global_8209 = (unsigned char)step->arg0;
        else if (step->kind == AVSP_ROUND1_ENTRY_TERMINATE)
        {
            runtime->entry.animation_c0 =
                (unsigned char)(runtime->entry.animation_c0 + 2u);
            runtime->entry.animation_c1 = 0u;
            runtime->entry.animation_c2 = 0u;
            runtime->entry.gate8236 = (unsigned char)
                (runtime->entry.gate8236 & (unsigned char)~1u);
            runtime->entry.terminal_seen = 1u;
            return avsp_round1_entry_valid(runtime);
        }
        else
        {
            ++runtime->failure_count;
            return 0;
        }
    }
    ++runtime->failure_count;
    return 0;
}

int avsp_round1_step_player(AvspRound1Runtime *runtime,
                            unsigned short input_mask,
                            short received_damage)
{
    AvspPwInput input;
    AvspPwView view;
    unsigned short applied_direction;
    unsigned char was_stopping;
    long prior_x_numerator;
    long prior_lane_numerator;
    short prior_x;
    short prior_lane;
    short prior_facing;
    unsigned short prior_state;
    unsigned short prior_selector;
    unsigned long prior_attack_edges;
    unsigned char weapon_pressed;
    unsigned char weapon_edge;
    unsigned char weapon_motion_hold;
    unsigned char weapon_owned;
    unsigned char recovery_start;
    unsigned char weapon_return_owned;
    unsigned char jump_pressed;
    unsigned char jump_edge;
    unsigned char jump_owned;
    if (runtime == 0 || runtime->route_state != 4 ||
        runtime->entry.control_enabled != 1u ||
        !avsp_round1_canaries_ok(runtime) || runtime->failure_count != 0u ||
        runtime->fallback_count != 0u)
        return 0;
    jump_pressed = (unsigned char)(
        (input_mask & AVSP_ROUND1_INPUT_BUTTON3) != 0u);
    jump_edge = (unsigned char)(jump_pressed &&
        !runtime->player_jump_previous_pressed);
    if (runtime->player_jump_cleanup_pending)
        runtime->player_jump_cleanup_pending = 0u;
    if (runtime->player_jump_active && received_damage > 0)
        avsp_round1_interrupt_player_jump(runtime);
    if (!runtime->player_jump_active && received_damage <= 0 && jump_edge &&
        runtime->player_action.state == AVSP_PW_STATE_CONTROL)
    {
        if (!avsp_round1_begin_player_jump(runtime))
        {
            ++runtime->failure_count;
            return 0;
        }
    }
    jump_owned = runtime->player_jump_active;
    weapon_pressed = (unsigned char)(
        (input_mask & AVSP_ROUND1_INPUT_BUTTON1) != 0u);
    weapon_edge = (unsigned char)(weapon_pressed &&
        !runtime->player_weapon_previous_pressed);
    recovery_start = (unsigned char)(
        runtime->player_weapon_cleanup_pending &&
        runtime->player_weapon_recovery_pending);
    weapon_return_owned = 0u;
    if (runtime->player_weapon_return_pending)
        runtime->player_weapon_return_pending = 0u;
    if (runtime->player_weapon_cleanup_pending && !recovery_start)
    {
        runtime->player_weapon_cleanup_pending = 0u;
        runtime->player_weapon_return_pending = 1u;
        weapon_return_owned = 1u;
        runtime->player_locomotion_action =
            avsp_round1_player_weapon.return_action;
    }
    if (!jump_owned && !runtime->player_weapon_active &&
        runtime->player_action.state == AVSP_PW_STATE_CONTROL &&
        (recovery_start ||
         (weapon_edge && (input_mask & AVSP_PW_INPUT_ATTACK) == 0u)))
    {
        runtime->player_weapon_recovery_pending = 0u;
        runtime->player_weapon_return_pending = 0u;
        weapon_return_owned = 0u;
        avsp_round1_begin_player_weapon(runtime);
    }
    weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||
        weapon_return_owned || jump_owned);
    input.mask = (unsigned short)(input_mask &
        (unsigned short)~(AVSP_ROUND1_INPUT_BUTTON1 |
                          AVSP_ROUND1_INPUT_BUTTON3));
    if (weapon_motion_hold)
        input.mask = (unsigned short)(input.mask & (unsigned short)~(
            AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT |
            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_DOWN |
            AVSP_PW_INPUT_ATTACK));
    input.received_damage = received_damage;
    applied_direction = runtime->player_action.direction_history[
        AVSP_PW_DIRECTION_LATENCY - 1];
    was_stopping = (unsigned char)(runtime->player_stop_ticks != 0u);
    prior_x_numerator = runtime->player_action.x_numerator;
    prior_lane_numerator = runtime->player_action.lane_numerator;
    prior_x = runtime->player_action.x;
    prior_lane = runtime->player_action.lane;
    prior_facing = runtime->player_action.facing;
    prior_state = runtime->player_action.state;
    prior_selector = runtime->player_action.selector;
    prior_attack_edges = runtime->player_action.accepted_attack_edges;
    avsp_pw_step_round1(&runtime->player_action, &input);
    avsp_round1_observe_player_melee(runtime, prior_state, prior_selector,
                                    prior_attack_edges);
    if (was_stopping || weapon_motion_hold)
    {
        if (runtime->player_action.x != prior_x ||
            runtime->player_action.lane != prior_lane ||
            runtime->player_action.facing != prior_facing ||
            runtime->player_action.x_numerator != prior_x_numerator ||
            runtime->player_action.lane_numerator != prior_lane_numerator)
        {
            if (was_stopping)
                ++runtime->player_stop_motion_suppressions;
            if (runtime->player_weapon_active || weapon_return_owned)
                ++runtime->player_weapon_motion_suppressions;
        }
        runtime->player_action.x_numerator = prior_x_numerator;
        runtime->player_action.lane_numerator = prior_lane_numerator;
        runtime->player_action.x = prior_x;
        runtime->player_action.lane = prior_lane;
        runtime->player_action.facing = prior_facing;
    }
    if (jump_owned && !avsp_round1_step_player_jump(runtime, input_mask))
    {
        ++runtime->failure_count;
        return 0;
    }
    weapon_owned = (unsigned char)avsp_round1_step_player_weapon(
        runtime, weapon_pressed, weapon_edge);
    avsp_round1_tick_player_resource(runtime);
    avsp_round1_apply_player_global_bounds(runtime);
    avsp_round1_apply_coffee_shop_obstacle(runtime);
    if (!avsp_round1_apply_first_segment_terrain(runtime) ||
        !avsp_round1_step_coffee_shop_camera(runtime))
    {
        ++runtime->failure_count;
        return 0;
    }
    if (jump_owned)
    {
        short jump_x = avsp_round1_fixed_high_word(runtime->player_jump_x_fp);
        if (jump_x != runtime->player_action.x)
            runtime->player_jump_x_fp =
                (long)runtime->player_action.x * 65536L;
    }
    avsp_pw_view(&runtime->player_action, &view);
    if (!jump_owned && !weapon_owned && !weapon_return_owned)
        avsp_round1_update_player_locomotion(runtime, applied_direction,
                                            was_stopping, &view);
    if (runtime->failure_count != 0u)
        return 0;
    runtime->player.state = AVSP_ROUND1_PLAYER_CONTROL_STATE;
    runtime->player.facing = (unsigned char)view.facing;
    runtime->player.x = view.x;
    runtime->player.y = (short)(view.lane + view.height);
    runtime->player.z = view.lane;
    runtime->player.health = view.health;
    if (jump_owned)
    {
        runtime->player.source_action = runtime->player_jump_phase;
        if (!runtime->player_jump_active &&
            runtime->player_jump_cleanup_pending)
            runtime->player.source_action = 0u;
    }
    else if (weapon_return_owned)
        avsp_round1_bind_player_weapon_frame(runtime,
            &avsp_round1_player_weapon_return_frame);
    else if (!weapon_owned)
    {
        runtime->player.substate = view.source_substate;
        runtime->player.source_action = runtime->player_locomotion_action;
        runtime->player.animation_record = view.animation_record;
        runtime->player.assembly = view.assembly;
    }
    runtime->player_weapon_previous_pressed = weapon_pressed;
    runtime->player_jump_previous_pressed = jump_pressed;
    ++runtime->player_controller_updates;
    return avsp_round1_entry_valid(runtime);
}

static int avsp_round1_player_weapon_runtime_valid(
    const AvspRound1Runtime *runtime)
{
    unsigned int index;
    const AvspRound1PlayerWeaponFrameSpec *frame = 0;
    if (runtime->player_resource >
            avsp_round1_player_weapon.resource_capacity ||
        runtime->player_resource_recharge >
            avsp_round1_player_weapon.recharge_after_success ||
        runtime->player_weapon_projectile_free_count >
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY ||
        runtime->player_weapon_allocations -
            runtime->player_weapon_projectile_releases +
            runtime->player_weapon_projectile_free_count !=
            AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY ||
        runtime->player_weapon_resource_debits !=
            runtime->player_weapon_allocations ||
        runtime->player_weapon_empty_auxiliary_requests !=
            runtime->player_weapon_empty_auxiliary_allocations +
            runtime->player_weapon_empty_auxiliary_allocation_failures ||
        runtime->player_weapon_empty_auxiliary_releases >
            runtime->player_weapon_empty_auxiliary_allocations ||
        runtime->player_weapon_completions > runtime->player_weapon_entries)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++index)
    {
        const AvspRound1WeaponProjectileAllocation *projectile =
            &runtime->player_weapon_projectiles[index];
        if (!projectile->active)
            continue;
        if (projectile->active != 1u ||
            projectile->actor_class !=
                avsp_round1_player_weapon.projectile_class ||
            projectile->source_slot != (unsigned short)(
                avsp_round1_player_weapon.projectile_source_base +
                index * avsp_round1_player_weapon.projectile_stride) ||
            projectile->owner != avsp_round1_player_weapon.player_owner ||
            projectile->attack_table !=
                avsp_round1_player_weapon.projectile_attack_table)
            return 0;
    }
    if (runtime->player_weapon_active)
    {
        if (runtime->player_action.state != AVSP_PW_STATE_CONTROL ||
            runtime->player_weapon_tick == 0u)
            return 0;
        if (runtime->player_weapon_empty)
        {
            if (runtime->player_weapon_tick >
                AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT)
                return 0;
            frame = &avsp_round1_player_empty_frames[
                runtime->player_weapon_tick - 1u];
        }
        else
        {
            if (runtime->player_weapon_tick >
                AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT)
                return 0;
            frame = &avsp_round1_player_weapon_frames[
                runtime->player_weapon_tick - 1u];
        }
        if (runtime->player.source_action != frame->action ||
            runtime->player.substate != frame->substate ||
            runtime->player.animation_record != frame->animation_record ||
            runtime->player.assembly != frame->assembly ||
            runtime->player.hurt_selector != frame->hurt_selector ||
            runtime->player.attack_selector != frame->attack_selector)
            return 0;
    }
    else if (runtime->player_weapon_cleanup_pending)
    {
        if (runtime->player.source_action !=
                avsp_round1_player_weapon.cleanup_action ||
            runtime->player_locomotion_action !=
                avsp_round1_player_weapon.cleanup_action)
            return 0;
    }
    else if (runtime->player_weapon_return_pending)
    {
        frame = &avsp_round1_player_weapon_return_frame;
        if (runtime->player.source_action != frame->action ||
            runtime->player.substate != frame->substate ||
            runtime->player.animation_record != frame->animation_record ||
            runtime->player.assembly != frame->assembly ||
            runtime->player.hurt_selector != frame->hurt_selector ||
            runtime->player.attack_selector != frame->attack_selector ||
            runtime->player_locomotion_action != frame->action)
            return 0;
    }
    return 1;
}

static int avsp_round1_player_jump_runtime_valid(
    const AvspRound1Runtime *runtime)
{
    const AvspRound1PlayerJumpSequenceSpec *sequence;
    const AvspRound1AnimationStateSpec *record;
    if (runtime->player_jump_entries < runtime->player_jump_completions +
            runtime->player_jump_interruptions ||
        runtime->player_jump_landings > runtime->player_jump_completions +
            runtime->player_jump_interruptions +
            (runtime->player_jump_active &&
             runtime->player_jump_phase == 0x0404u ? 1u : 0u) ||
        runtime->player_jump_previous_pressed > 1u)
        return 0;
    if (!runtime->player_jump_active)
        return runtime->player_jump_airborne_latch == 0u &&
            (!runtime->player_jump_cleanup_pending ||
             (runtime->player_action.height == 0 &&
              runtime->player.source_action == 0u &&
              runtime->player.animation_record == 0x0015f1f4UL));
    if (runtime->player_jump_phase != 0x0400u &&
        runtime->player_jump_phase != 0x0402u &&
        runtime->player_jump_phase != 0x0404u &&
        runtime->player_jump_phase != 0x040au &&
        runtime->player_jump_phase != 0x040cu)
        return 0;
    if (runtime->player.source_action != runtime->player_jump_phase ||
        runtime->player_jump_animation_timer == 0u)
        return 0;
    sequence = avsp_round1_find_player_jump_sequence(
        runtime->player_jump_presentation_selector);
    if (sequence == 0 || runtime->player_jump_animation_index >=
            sequence->record_count)
        return 0;
    record = &sequence->records[runtime->player_jump_animation_index];
    if (runtime->player.animation_record != record->animation_record ||
        runtime->player.assembly != record->assembly ||
        runtime->player.hurt_selector != record->hurt_selector ||
        runtime->player.attack_selector != record->attack_selector ||
        runtime->player_jump_animation_branch != record->branch)
        return 0;
    if (runtime->player_jump_phase == 0x0402u)
        return runtime->player_jump_airborne_latch == 1u &&
            runtime->player_jump_collision_selector >= 1u &&
            runtime->player_jump_collision_selector <= 8u &&
            runtime->player_action.height >= 0;
    if (runtime->player_jump_phase == 0x040au)
        return runtime->player_jump_collision_selector == 7u &&
            runtime->player_jump_airborne_latch == 0u;
    if (runtime->player_jump_phase == 0x040cu)
        return runtime->player_jump_phase_timer <= 10u &&
            runtime->player_jump_phase_timer > 0u &&
            runtime->player_jump_presentation_selector == 42u;
    return 1;
}

int avsp_round1_entry_valid(const AvspRound1Runtime *runtime)
{
    unsigned int index;
    unsigned int spawn_index;
    static const unsigned short last_slots[AVSP_ROUND1_POOL_COUNT] =
        {0xA3C0u, 0xAE00u, 0xB600u, 0xC600u};

    if (!avsp_round1_canaries_ok(runtime) ||
        avsp_round1_entry_program[0] != 0x0Au ||
        avsp_round1_entry_program[AVSP_ROUND1_ENTRY_PROGRAM_BYTES - 2u] != 0xFFu ||
        avsp_round1_entry_program[AVSP_ROUND1_ENTRY_PROGRAM_BYTES - 1u] != 0xFFu ||
        (runtime->route_state != AVSP_ROUND1_ROUTE_ENTRY_STATE &&
         runtime->route_state != 4) ||
        (!runtime->entry.started &&
         runtime->rng_seed != AVSP_ROUND1_INITIAL_RNG) ||
        runtime->player.active != 1u || runtime->player.actor_class != 0 ||
        runtime->player.type != 0u ||
        runtime->player.health > AVSP_ROUND1_PLAYER_HEALTH ||
        runtime->fallback_count != 0u || runtime->failure_count != 0u ||
        !avsp_round1_player_melee_contract_valid() ||
        !avsp_round1_player_jump_contract_valid() ||
        !avsp_round1_player_jump_runtime_valid(runtime) ||
        !avsp_round1_player_weapon_contract_valid() ||
        !avsp_round1_player_weapon_runtime_valid(runtime))
        return 0;
    for (index = 0u; index < AVSP_ROUND1_POOL_COUNT; ++index)
    {
        const AvspRound1Pool *pool = &runtime->pools[index];
        if (!avsp_round1_pool_metadata_valid(pool, index) ||
            (!runtime->entry.started &&
             pool->free_stack[pool->capacity - 1u] != last_slots[index]))
            return 0;
    }
    if (!runtime->entry.started)
        return runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&
            runtime->player.state == 0u && runtime->player.substate == 0u &&
            runtime->player.health == AVSP_ROUND1_PLAYER_HEALTH &&
            runtime->pools[0].free_count == 20u;
    if (runtime->entry_controller.active != 1u ||
        runtime->entry_controller.actor_class != 1 ||
        runtime->entry_controller.type != 32u ||
        runtime->entry_controller.state != 514u ||
        runtime->entry_controller.source_slot != 0x00ffd180UL ||
        runtime->entry.gate81af != 1u ||
        runtime->entry.step_index > AVSP_ROUND1_ENTRY_STEP_COUNT ||
        runtime->entry.timer_decrements > 164u)
        return 0;
    if (!runtime->entry.spawned)
        return runtime->pools[0].free_count == 20u &&
            runtime->entry.spawn_count == 0u &&
            runtime->player.state == AVSP_ROUND1_PLAYER_ENTRY_STATE &&
            runtime->pools[2].free_count == 13u &&
            runtime->pools[3].free_count == 2u &&
            runtime->class09_initializations == 2u;
    if (runtime->pools[0].free_count != 10u ||
        runtime->entry.spawn_count != AVSP_ROUND1_FIRST_SPAWN_COUNT)
        return 0;
    for (spawn_index = 0u; spawn_index < AVSP_ROUND1_FIRST_SPAWN_COUNT;
         ++spawn_index)
    {
        const AvspRound1EntrySpawnSpec *spec =
            &avsp_round1_entry_spawns[spawn_index];
        unsigned short slot = (unsigned short)spec->source_slot;
        unsigned int record_index =
            (unsigned int)(slot - runtime->pools[0].source_base) /
            runtime->pools[0].stride;
        const AvspRound1ActorCore *actor =
            &runtime->pools[0].records[record_index];
        if (actor->active != 1u || actor->actor_class != (signed char)spec->actor_class ||
            actor->type != spec->record_type || actor->source_slot != spec->source_slot)
            return 0;
        if (actor->handler_updates == 0u &&
            (actor->x != spec->x || actor->y != spec->y ||
             actor->z != spec->z || actor->variant != spec->variant ||
             actor->source_action != spec->source_action ||
             actor->state != spec->state || actor->substate != spec->substate ||
             actor->facing != spec->facing ||
             actor->animation_record != spec->animation_record ||
             actor->health != spec->health))
            return 0;
    }
    if (runtime->route_state == 4)
    {
        int locomotion_valid = 1;
        if (runtime->player_jump_active ||
            runtime->player_jump_cleanup_pending ||
            runtime->player_weapon_active ||
            runtime->player_weapon_cleanup_pending ||
            runtime->player_weapon_return_pending)
            locomotion_valid = runtime->player_stop_ticks == 0u &&
                runtime->player_cleanup_pending == 0u;
        else if (runtime->player_action.state == AVSP_PW_STATE_CONTROL)
        {
            if (runtime->player_stop_ticks != 0u)
                locomotion_valid = runtime->player_locomotion_action ==
                    avsp_round1_player_locomotion.stop_action &&
                    runtime->player_cleanup_pending == 0u &&
                    runtime->player_stop_ticks <=
                        avsp_round1_player_locomotion.stop_ticks;
            else if (runtime->player_cleanup_pending)
                locomotion_valid = runtime->player_locomotion_action ==
                    avsp_round1_player_locomotion.cleanup_action;
            else
                locomotion_valid = runtime->player_locomotion_action ==
                    avsp_round1_player_locomotion.walking_action;
        }
        else if (runtime->player_stop_ticks != 0u ||
                 runtime->player_cleanup_pending)
            locomotion_valid = 0;
        return runtime->entry.terminal_seen == 1u &&
            runtime->entry.control_enabled == 1u &&
            runtime->entry.gate8236 == 0u &&
            runtime->entry.timer_decrements == 164u &&
            runtime->entry.step_index == AVSP_ROUND1_ENTRY_STEP_COUNT &&
            runtime->navigation_bounds_active == 1u &&
            runtime->navigation_bound_x == runtime->camera_x_position &&
            runtime->navigation_bound_z == runtime->camera_z_position &&
            runtime->camera_x_position == runtime->camera_x_target &&
            runtime->camera_z_position == runtime->camera_z_target &&
            runtime->camera_scroll2_x ==
                (short)(runtime->camera_x_position - 0x40) &&
            runtime->camera_x_lower <= runtime->camera_x_position &&
            runtime->camera_x_position <= runtime->camera_x_upper &&
            runtime->camera_z_lower <= runtime->camera_z_position &&
            runtime->camera_z_position <= runtime->camera_z_upper &&
            runtime->player.state == AVSP_ROUND1_PLAYER_CONTROL_STATE &&
            runtime->player_action.health == runtime->player.health &&
            runtime->player_action.x == runtime->player.x &&
            runtime->player_action.lane == runtime->player.z &&
            (runtime->player_jump_active ||
             runtime->player_jump_cleanup_pending ||
             runtime->player_weapon_active ||
             runtime->player_weapon_cleanup_pending ||
             runtime->player_weapon_return_pending ||
             runtime->player.source_action ==
                runtime->player_locomotion_action) && locomotion_valid;
    }
    if (runtime->entry.control_enabled ||
        runtime->player.state != AVSP_ROUND1_PLAYER_ENTRY_STATE)
        return 0;
    return 1;
}
