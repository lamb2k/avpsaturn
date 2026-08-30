#include "round1.h"
#include "spec02_round1_entry_data.h"
#include "../../integration/combat/combat.h"
#include "../../../../avsp_actor.h"
#include "../../../../avsp_collision.h"

#include <string.h>

static const unsigned char avsp_round1_pool_types[AVSP_ROUND1_POOL_COUNT] =
    {12u, 16u, 20u, 24u, 28u, 36u};
static const unsigned char avsp_round1_pool_capacities[AVSP_ROUND1_POOL_COUNT] =
    {20u, 20u, 16u, 32u, 16u, 64u};
static const unsigned short avsp_round1_pool_strides[AVSP_ROUND1_POOL_COUNT] =
    {192u, 128u, 128u, 128u, 128u, 64u};
static const unsigned short avsp_round1_pool_bases[AVSP_ROUND1_POOL_COUNT] =
    {0x9580u, 0xA480u, 0xAE80u, 0xB680u, 0xC680u, 0xD280u};

static void avsp_round1_bind_animation_state(
    AvspRound1ActorCore *actor, const AvspRound1AnimationStateSpec *record);
static unsigned char avsp_round1_source_rng(AvspRound1Runtime *runtime);
static short avsp_round1_fixed_high_word(long value);
static unsigned char avsp_round1_next_collision_identity(
    AvspRound1Runtime *runtime);
static void avsp_round1_player_weapon_target(
    const AvspRound1Runtime *runtime, unsigned char *presentation_selector,
    unsigned char *angle);
static int avsp_round1_bind_class1f_action_selector(
    AvspRound1ActorCore *actor, unsigned char selector);
static int avsp_round1_step_class1f_action_animation(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    int apply_movement);
static void avsp_round1_interrupt_player_jump(AvspRound1Runtime *runtime);

#define AVSP_ROUND1_PLAYER_HIT_ENTRY 1u
#define AVSP_ROUND1_PLAYER_HIT_SHAKE 2u
#define AVSP_ROUND1_PLAYER_HIT_MOTION 3u
#define AVSP_ROUND1_PLAYER_HIT_RETURN 4u
#define AVSP_ROUND1_PLAYER_HIT_SETTLE 5u

unsigned short avsp_round1_coffee_shop_source_input(
    unsigned short source_frame)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_COFFEE_SHOP_INPUT_RUN_COUNT;
         ++index)
    {
        const AvspRound1SceneInputRun *run =
            &avsp_round1_coffee_shop_input_runs[index];
        if (source_frame >= run->first_source_frame &&
            source_frame <= run->last_source_frame)
            return run->input_mask;
    }
    return 0u;
}

unsigned int avsp_round1_coffee_shop_source_updates(
    unsigned short source_frame)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_COFFEE_SHOP_UPDATE_CADENCE_COUNT;
         ++index)
    {
        const AvspRound1SceneUpdateCadence *entry =
            &avsp_round1_coffee_shop_update_cadence[index];
        if (source_frame == entry->source_frame)
            return entry->updates;
    }
    return AVSP_ROUND1_COFFEE_SHOP_DEFAULT_SOURCE_UPDATES;
}

static int avsp_round1_pool_metadata_valid(const AvspRound1Pool *pool,
                                           unsigned int index)
{
    return pool->record_type == avsp_round1_pool_types[index] &&
        pool->capacity == avsp_round1_pool_capacities[index] &&
        pool->stride == avsp_round1_pool_strides[index] &&
        pool->source_base == avsp_round1_pool_bases[index] &&
        pool->free_count <= pool->capacity;
}

static int avsp_round1_pool_active_free_valid(const AvspRound1Pool *pool)
{
    unsigned int record_index;
    unsigned int active_count = 0u;
    for (record_index = 0u; record_index < pool->capacity; ++record_index)
    {
        const AvspRound1ActorCore *actor = &pool->records[record_index];
        if (!actor->active)
            continue;
        if ((actor->active != 1u &&
             !(pool->record_type == 12u && actor->actor_class == 0x1f &&
               actor->active == 2u) &&
             !(pool->record_type == 36u && actor->active == 2u) &&
             !(pool->record_type == 20u && actor->actor_class == 0x01 &&
               actor->active == 2u) &&
             !(pool->record_type == 24u && actor->actor_class == 0x43 &&
               actor->active == 2u) &&
             !(pool->record_type == 24u && actor->actor_class == 0x47 &&
               actor->active == 2u)) ||
            actor->type != pool->record_type ||
            actor->source_slot != (0x00ff0000UL |
                (unsigned long)(pool->source_base +
                    record_index * pool->stride)))
            return 0;
        ++active_count;
    }
    if (active_count + pool->free_count != pool->capacity)
        return 0;
    for (record_index = 0u; record_index < pool->free_count; ++record_index)
    {
        unsigned short slot = pool->free_stack[record_index];
        unsigned int free_index;
        unsigned int prior_index;
        if (slot < pool->source_base ||
            ((unsigned int)(slot - pool->source_base) % pool->stride) != 0u)
            return 0;
        free_index = (unsigned int)(slot - pool->source_base) / pool->stride;
        if (free_index >= pool->capacity || pool->records[free_index].active)
            return 0;
        for (prior_index = 0u; prior_index < record_index; ++prior_index)
            if (pool->free_stack[prior_index] == slot)
                return 0;
    }
    return 1;
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
    actor->source_slot = 0x00ff0000UL | (unsigned long)slot;
    return actor;
}

static AvspRound1ActorCore *
avsp_round1_allocate_pool_actor_preserve_position_fraction(
    AvspRound1Runtime *runtime, unsigned int pool_index)
{
    AvspRound1Pool *pool;
    unsigned short source_slot;
    unsigned int actor_index;
    unsigned short x_fraction;
    unsigned short y_fraction;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned short animation_timer;
    short animation_branch;
    AvspRound1ActorCore *actor;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (pool->free_count == 0u)
        return 0;
    source_slot = pool->free_stack[pool->free_count - 1u];
    actor_index = (unsigned int)(source_slot - pool->source_base) /
        pool->stride;
    if (actor_index >= pool->capacity)
        return 0;
    x_fraction = (unsigned short)pool->records[actor_index].source_x_fp;
    y_fraction = (unsigned short)pool->records[actor_index].source_y_fp;
    animation_record = pool->records[actor_index].animation_record;
    assembly = pool->records[actor_index].assembly;
    animation_timer = pool->records[actor_index].animation_timer;
    animation_branch = pool->records[actor_index].animation_branch;
    actor = avsp_round1_allocate_pool_actor(runtime, pool_index);
    if (actor != 0)
    {
        actor->source_x_fp = (long)x_fraction;
        actor->source_y_fp = (long)y_fraction;
        if (avsp_round1_recurring_spawn.preserve_reused_presentation != 0u)
        {
            actor->animation_record = animation_record;
            actor->assembly = assembly;
            actor->animation_timer = animation_timer;
            actor->animation_branch = animation_branch;
        }
    }
    return actor;
}

static AvspRound1ActorCore *avsp_round1_allocate_pool_actor_preserve_y(
    AvspRound1Runtime *runtime, unsigned int pool_index)
{
    AvspRound1Pool *pool;
    unsigned short source_slot;
    unsigned int actor_index;
    short retained_y;
    AvspRound1ActorCore *actor;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (pool->free_count == 0u)
        return 0;
    source_slot = pool->free_stack[pool->free_count - 1u];
    actor_index = (unsigned int)(source_slot - pool->source_base) /
        pool->stride;
    if (actor_index >= pool->capacity)
        return 0;
    retained_y = pool->records[actor_index].y;
    actor = avsp_round1_allocate_pool_actor(runtime, pool_index);
    if (actor != 0)
        actor->y = retained_y;
    return actor;
}

static AvspRound1ActorCore *
avsp_round1_allocate_pool_actor_preserve_position_residue(
    AvspRound1Runtime *runtime, unsigned int pool_index)
{
    AvspRound1Pool *pool;
    unsigned short source_slot;
    unsigned int actor_index;
    unsigned short x_fraction;
    unsigned short y_fraction;
    short retained_z;
    AvspRound1ActorCore *actor;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (pool->free_count == 0u)
        return 0;
    source_slot = pool->free_stack[pool->free_count - 1u];
    actor_index = (unsigned int)(source_slot - pool->source_base) /
        pool->stride;
    if (actor_index >= pool->capacity)
        return 0;
    x_fraction = (unsigned short)pool->records[actor_index].source_x_fp;
    y_fraction = (unsigned short)pool->records[actor_index].source_y_fp;
    retained_z = pool->records[actor_index].z;
    actor = avsp_round1_allocate_pool_actor(runtime, pool_index);
    if (actor != 0)
    {
        actor->source_x_fp = (long)x_fraction;
        actor->source_y_fp = (long)y_fraction;
        actor->z = retained_z;
    }
    return actor;
}

static AvspRound1ActorCore *
avsp_round1_allocate_pool_actor_preserve_presentation(
    AvspRound1Runtime *runtime, unsigned int pool_index)
{
    AvspRound1Pool *pool;
    unsigned short source_slot;
    unsigned int actor_index;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned short animation_timer;
    short animation_branch;
    AvspRound1ActorCore *actor;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (pool->free_count == 0u)
        return 0;
    source_slot = pool->free_stack[pool->free_count - 1u];
    actor_index = (unsigned int)(source_slot - pool->source_base) /
        pool->stride;
    if (actor_index >= pool->capacity)
        return 0;
    animation_record = pool->records[actor_index].animation_record;
    assembly = pool->records[actor_index].assembly;
    animation_timer = pool->records[actor_index].animation_timer;
    animation_branch = pool->records[actor_index].animation_branch;
    actor = avsp_round1_allocate_pool_actor(runtime, pool_index);
    if (actor != 0)
    {
        actor->animation_record = animation_record;
        actor->assembly = assembly;
        actor->animation_timer = animation_timer;
        actor->animation_branch = animation_branch;
    }
    return actor;
}

static AvspRound1ActorCore *avsp_round1_allocate_pool_source_slot(
    AvspRound1Runtime *runtime, unsigned int pool_index,
    unsigned short source_slot)
{
    AvspRound1Pool *pool;
    AvspRound1ActorCore *actor;
    unsigned int free_index;
    unsigned int actor_index;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (source_slot < pool->source_base ||
        ((unsigned int)(source_slot - pool->source_base) % pool->stride) != 0u)
        return 0;
    actor_index = (unsigned int)(source_slot - pool->source_base) /
        pool->stride;
    if (actor_index >= pool->capacity || pool->records[actor_index].active)
        return 0;
    for (free_index = 0u; free_index < pool->free_count; ++free_index)
        if (pool->free_stack[free_index] == source_slot)
            break;
    if (free_index >= pool->free_count)
        return 0;
    for (; free_index + 1u < pool->free_count; ++free_index)
        pool->free_stack[free_index] = pool->free_stack[free_index + 1u];
    --pool->free_count;
    actor = &pool->records[actor_index];
    memset(actor, 0, sizeof(*actor));
    actor->active = 1u;
    actor->type = pool->record_type;
    actor->source_slot = 0x00ff0000UL | (unsigned long)source_slot;
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
    /* The source free-list clears ownership through the active byte while the
     * fixed record retains unwritten fields. Normal allocations still clear
     * their record; source bodies such as class-0x3d can explicitly retain a
     * field that their allocation writer never touches. */
    actor->active = 0u;
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
        ++runtime->first_encounter.source_living_count;
    }
    runtime->entry.spawned = 1u;
    runtime->first_encounter.source_initial_spawn_complete = 1u;
    runtime->entry_controller.state = avsp_round1_recurring_spawn.wait_state;
    return 1;
}

static int avsp_round1_dispatch_supported(unsigned char record_type,
                                           signed char actor_class)
{
    unsigned int index;
    if (record_type == 24u && actor_class == 0x43)
        return 1;
    if (record_type == 24u && actor_class == 0x44)
        return 1;
    if (record_type == 24u && actor_class == 0x47)
        return 1;
    if (record_type == 24u &&
        (actor_class == 0x4b || actor_class == 0x3d))
        return 1;
    if (record_type == 36u && actor_class == 0x05)
        return 1;
    if (record_type == 20u &&
        (actor_class == 0x01 || actor_class == 0x02))
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

static short avsp_round1_class1f_player_damage(
    const unsigned short selector)
{
    if (selector < 1u || selector > AVSP_ROUND1_PLAYER_MELEE_COUNT)
        return 0;
    return avsp_round1_class1f_current.player_damage[selector - 1u];
}

static int avsp_round1_class1f_melee_overlap(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *actor,
    unsigned char *hit_value)
{
    AvspActor player;
    AvspActor alien;
    memset(&player, 0, sizeof(player));
    memset(&alien, 0, sizeof(alien));
    player.state = 1u;
    player.table_set = AVSP_PORT_V2_COMBAT_PLAYER_TABLE_SET;
    player.sel_attack = (unsigned char)runtime->player_action.selector;
    player.facing = (unsigned char)runtime->player_action.facing;
    player.world_x = (unsigned short)runtime->player_action.x;
    player.world_y = (unsigned short)(runtime->player_action.lane +
        runtime->player_action.height);
    player.world_z = (unsigned short)runtime->player_action.lane;
    player.attacker_id = 155u;
    player.latch_index = 0u;
    alien.state = 1u;
    alien.table_set = AVSP_PORT_V2_COMBAT_ENEMY_TABLE_SET;
    alien.sel_hurt = AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR;
    alien.facing = actor->facing;
    alien.world_x = (unsigned short)actor->x;
    alien.world_y = (unsigned short)actor->y;
    alien.world_z = (unsigned short)actor->z;
    return avsp_collision_overlap(&player, &alien, hit_value) &&
        !avsp_collision_guarded(&player, &alien);
}

#if 0
static short avsp_round1_class1f_abs(short value)
{
    return value < 0 ? (short)-value : value;
}
#endif

#if 0
static void avsp_round1_class1f_fraction(long *numerator, short *position,
                                         int amount)
{
    long before = *numerator /
        (long)avsp_round1_class1f_current.approach_ticks;
    long after;
    *numerator += amount;
    after = *numerator /
        (long)avsp_round1_class1f_current.approach_ticks;
    *position = (short)(*position + (short)(after - before));
}
#endif

static void avsp_round1_first_encounter_cache_presentation(
    AvspRound1FirstEncounterRuntime *encounter,
    const AvspRound1ActorCore *actor)
{
    AvspAlienView *view = &encounter->presentation;
    memset(view, 0, sizeof(*view));
    if (actor == 0 || !actor->active)
        return;
    view->class_id = (unsigned short)(unsigned char)actor->actor_class;
    view->state = actor->state;
    view->inner_state = actor->substate;
    view->target_id = encounter->target_id;
    view->x = actor->x;
    view->lane = actor->z;
    view->health = actor->health;
    view->facing = actor->facing;
    view->approach_elapsed = encounter->approach_elapsed;
    view->attack_elapsed = encounter->attack_elapsed;
    view->attack_timer = encounter->attack_timer;
    view->rng_seed = encounter->rng_seed;
    view->rng_cursor = encounter->rng_cursor;
    view->contact = encounter->alien_contact;
    view->contact_damage = encounter->pending_player_damage;
    view->removed = 0u;
    view->source_action = actor->source_action;
    view->presentation_index = encounter->presentation_index;
    view->animation_record = actor->animation_record;
    view->assembly = actor->assembly;
}

static int avsp_round1_class1f_bind_record(AvspRound1ActorCore *actor,
                                           unsigned long record)
{
    const AvspRound1PresentationSpec *presentation =
        avsp_round1_find_class1f_presentation(record);
    if (presentation == 0)
        return 0;
    actor->animation_record = record;
    actor->assembly = presentation->assembly;
    actor->hurt_selector = presentation->hurt_selector;
    actor->attack_selector = presentation->attack_selector;
    return 1;
}

static int avsp_round1_class1f_rebuild_reaction(
    const AvspRound1ActorCore *actor, AvspPortV2HitKoRuntime *reaction)
{
    unsigned int index;
    unsigned int elapsed;
    AvspPortV2HitKoKind kind;
    const AvspPortV2HitKoActorState *before;
    if (actor->health >= 0)
    {
        kind = AVSP_PORT_V2_HIT_KO_HIT;
        before = &avsp_port_v2_hit_source_before;
        elapsed = avsp_round1_class1f_current.hit_ticks -
            actor->source_action_timer;
    }
    else
    {
        kind = AVSP_PORT_V2_HIT_KO_KO;
        before = &avsp_port_v2_ko_source_before;
        elapsed = avsp_round1_class1f_current.ko_ticks -
            actor->source_action_timer;
    }
    memset(reaction, 0, sizeof(*reaction));
    if (!avsp_port_v2_hit_ko_begin(reaction, kind, before))
        return 0;
    for (index = 0u; index < elapsed; ++index)
    {
        if (!reaction->active)
            break;
        if (!avsp_port_v2_hit_ko_step(reaction))
            return 0;
    }
    return 1;
}

static int avsp_round1_class1f_sync_reaction(
    AvspRound1ActorCore *actor,
    const AvspPortV2HitKoRuntime *reaction)
{
    if (!avsp_round1_class1f_bind_record(
            actor, reaction->actor.anim_record))
        return 0;
    actor->state = reaction->actor.sub_state;
    actor->substate = reaction->actor.action;
    actor->source_action = actor->substate;
    actor->animation_timer = reaction->actor.anim_timer;
    return avsp_round1_class1f_state_context_supported(
        actor->state, actor->substate);
}

static int avsp_round1_class1f_begin_reaction(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor, const int ko)
{
    AvspPortV2HitKoRuntime reaction;
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    actor->source_action_timer = (unsigned char)(ko ?
        avsp_round1_class1f_current.ko_ticks :
        avsp_round1_class1f_current.hit_ticks);
    if (!avsp_round1_class1f_rebuild_reaction(actor, &reaction))
        return 0;
    if (ko)
    {
        ++encounter->ko_events;
        encounter->semantic_ko = 1u;
        encounter->source_progress = (unsigned short)(
            encounter->source_progress +
            avsp_round1_recurring_spawn.progress_increment);
    }
    else
    {
        ++encounter->hit_events;
        encounter->semantic_hit = 1u;
    }
    return avsp_round1_class1f_sync_reaction(actor, &reaction);
}

static void avsp_round1_class1f_queue_projectile_reaction(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor, const int ko,
    const short prior_health)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    actor->state = ko ? avsp_round1_class1f_source_ko.collision_state :
        avsp_round1_class1f_source_hit.state;
    actor->substate = 0u;
    actor->source_action = 0u;
    actor->source_action_timer = ko ?
        avsp_round1_class1f_source_ko.recovery_timer :
        avsp_round1_class1f_source_hit.recovery_timer;
    actor->source_prior_health = prior_health;
    actor->source_hit_recovery_active = 0u;
    actor->source_hit_mode = 0u;
    actor->source_hit_kind = ko ? avsp_round1_class1f_source_ko.hit_kind :
        avsp_round1_class1f_source_hit.hit_kind;
    actor->source_reaction_selector = 0u;
    actor->source_hit_action_timer = 0u;
    actor->source_projectile_reaction_pending =
        (unsigned char)(ko ? 2u : 1u);
    if (ko)
    {
        ++encounter->ko_events;
        encounter->semantic_ko = 1u;
    }
    else
    {
        ++encounter->hit_events;
        encounter->semantic_hit = 1u;
    }
}

static int avsp_round1_class1f_consume_projectile_reaction(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    const unsigned char pending)
{
    if (pending == 1u)
    {
        if (actor->state != avsp_round1_class1f_source_hit.state ||
            actor->substate != 0u ||
            actor->source_action_timer !=
                avsp_round1_class1f_source_hit.recovery_timer ||
            actor->source_hit_kind != avsp_round1_class1f_source_hit.hit_kind ||
            actor->source_prior_health < actor->health)
            return 0;
        actor->substate = avsp_round1_class1f_source_hit.entry_action_phase;
        actor->source_action = actor->substate;
        actor->source_hit_mode = avsp_round1_class1f_source_hit.hit_mode;
        actor->source_reaction_selector =
            avsp_round1_class1f_source_hit.reaction_selector;
        actor->source_hit_action_timer =
            avsp_round1_class1f_source_hit.action_timer;
        actor->source_prior_health = actor->health;
        actor->source_hit_recovery_active = 1u;
        actor->animation_timer = 1u;
        actor->animation_branch = 0;
        if (!avsp_round1_class1f_bind_record(
                actor, avsp_round1_class1f_source_hit.animation_record) ||
            actor->assembly != avsp_round1_class1f_source_hit.assembly ||
            actor->hurt_selector !=
                avsp_round1_class1f_source_hit.hurt_selector ||
            actor->attack_selector !=
                avsp_round1_class1f_source_hit.attack_selector)
            return 0;
        return avsp_round1_class1f_state_context_supported(
            actor->state, actor->substate);
    }
    if (pending != 2u)
        return 0;
    if (actor->state != avsp_round1_class1f_source_ko.collision_state ||
        actor->substate != 0u || actor->health >= 0 ||
        actor->source_action_timer !=
            avsp_round1_class1f_source_ko.recovery_timer ||
        actor->source_hit_kind != avsp_round1_class1f_source_ko.hit_kind ||
        actor->source_prior_health < 0)
        return 0;
    actor->active = avsp_round1_class1f_source_ko.dispatch_active;
    actor->state = avsp_round1_class1f_source_ko.dispatch_state;
    actor->source_hit_mode = avsp_round1_class1f_source_ko.hit_mode;
    actor->source_reaction_selector =
        avsp_round1_class1f_source_ko.reaction_selector;
    actor->source_hit_recovery_active = 2u;
    actor->animation_timer = 1u;
    actor->animation_branch = 0;
    if (!avsp_round1_class1f_bind_record(
            actor,
            avsp_round1_class1f_source_ko.reaction_records[0]
                .animation_record))
        return 0;
    actor->animation_index = 0u;
    runtime->first_encounter.source_progress = (unsigned short)(
        runtime->first_encounter.source_progress +
        avsp_round1_recurring_spawn.progress_increment);
    return avsp_round1_class1f_state_context_supported(
        actor->state, actor->substate);
}

static int avsp_round1_class1f_reaction_active(
    const AvspRound1ActorCore *actor)
{
    unsigned long record = actor->animation_record;
    return actor->source_hit_recovery_active != 0 ||
        (actor->source_action_timer != 0u &&
        (record == AVSP_PORT_V2_HIT_ANIM_RECORD ||
         record == AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD ||
         record == AVSP_PORT_V2_KO_ANIM_RECORD ||
         record == AVSP_PORT_V2_KO_ANIM_RECORD_1 ||
         record == AVSP_PORT_V2_KO_ANIM_RECORD_2 ||
         record == AVSP_PORT_V2_KO_ANIM_RECORD_3 ||
         record == AVSP_PORT_V2_KO_ANIM_RECORD_4 ||
         record == AVSP_PORT_V2_KO_ANIM_RECORD_5));
}

static void avsp_round1_class1f_hit_clamp_y(AvspRound1ActorCore *actor)
{
    actor->source_y_fp = (long)(
        ((unsigned long)actor->source_y_fp & 0x0000ffffUL) |
        ((unsigned long)(unsigned short)actor->z << 16));
    actor->y = actor->z;
}

static void avsp_round1_class1f_hit_clear_motion(
    AvspRound1ActorCore *actor)
{
    actor->source_x_velocity = 0L;
    actor->source_x_acceleration = 0L;
    actor->source_y_velocity = 0L;
    actor->source_y_acceleration = 0L;
}

static void avsp_round1_class1f_bind_source_hit_record(
    AvspRound1ActorCore *actor,
    const AvspRound1AnimationStateSpec *record,
    const unsigned char index)
{
    actor->animation_index = index;
    avsp_round1_bind_animation_state(actor, record);
}

static int avsp_round1_class1f_step_source_hit_reaction_animation(
    AvspRound1ActorCore *actor)
{
    unsigned char next;
    if (actor->animation_index >=
            avsp_round1_class1f_source_hit.reaction_record_count ||
        actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    next = (unsigned char)(actor->animation_index + 1u);
    if (next >= avsp_round1_class1f_source_hit.reaction_record_count)
        next = 0u;
    avsp_round1_class1f_bind_source_hit_record(
        actor, &avsp_round1_class1f_source_hit.reaction_records[next], next);
    return 1;
}

static int avsp_round1_class1f_step_source_ko_reaction_animation(
    AvspRound1ActorCore *actor)
{
    unsigned char next;
    if (actor->animation_index >=
            avsp_round1_class1f_source_ko.reaction_record_count ||
        actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    next = (unsigned char)(actor->animation_index + 1u);
    if (next >= avsp_round1_class1f_source_ko.reaction_record_count)
        next = 0u;
    avsp_round1_class1f_bind_source_hit_record(
        actor, &avsp_round1_class1f_source_ko.reaction_records[next], next);
    return 1;
}

static int avsp_round1_class1f_step_source_hit_loop_record(
    AvspRound1ActorCore *actor,
    const AvspRound1AnimationStateSpec *record)
{
    if (actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer == 0u)
        avsp_round1_class1f_bind_source_hit_record(actor, record, 0u);
    return 1;
}

static int avsp_round1_class1f_hit_step_motion(
    AvspRound1ActorCore *actor)
{
    actor->source_x_fp += actor->source_x_velocity;
    actor->source_x_velocity += actor->source_x_acceleration;
    actor->source_y_fp += actor->source_y_velocity;
    actor->source_y_velocity += actor->source_y_acceleration;
    actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
    actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
    return (unsigned short)actor->z < (unsigned short)actor->y;
}

static void avsp_round1_class1f_bind_source_hit_terminal(
    AvspRound1ActorCore *actor, const unsigned char index)
{
    actor->animation_index = index;
    avsp_round1_bind_animation_state(
        actor, &avsp_round1_class1f_source_hit.terminal_records[index]);
}

static int avsp_round1_class1f_source_hit_normal_return(
    AvspRound1ActorCore *actor)
{
    actor->active = 1u;
    actor->state = avsp_round1_class1f_source_hit.normal_return_state;
    actor->substate = avsp_round1_class1f_source_hit.normal_return_substate;
    actor->source_action = actor->substate;
    actor->source_hit_recovery_active = 0u;
    actor->source_hit_mode = 0u;
    actor->source_hit_kind = 0u;
    actor->source_reaction_selector = 0u;
    actor->source_hit_action_timer = 0u;
    actor->source_airborne = 0u;
    actor->source_motion_flags = 0u;
    actor->source_collision_guard6d = 0u;
    actor->source_collision_suppress70 = 0u;
    actor->source_style85 =
        avsp_round1_class1f_source_hit.normal_return_style85;
    avsp_round1_class1f_hit_clear_motion(actor);
    return avsp_round1_class1f_state_context_supported(
        actor->state, actor->substate);
}

static int avsp_round1_class1f_step_source_hit_terminal(
    AvspRound1ActorCore *actor)
{
    unsigned char next;
    if (actor->animation_index >=
            avsp_round1_class1f_source_hit.terminal_record_count ||
        actor->animation_timer == 0u)
        return 0;
    if (avsp_round1_class1f_source_hit.
            terminal_records[actor->animation_index].branch < 0)
        return avsp_round1_class1f_source_hit_normal_return(actor);
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    next = (unsigned char)(actor->animation_index + 1u);
    if (next >= avsp_round1_class1f_source_hit.terminal_record_count)
        return 0;
    avsp_round1_class1f_bind_source_hit_terminal(actor, next);
    return 1;
}

static int avsp_round1_class1f_step_source_ko(
    AvspRound1ActorCore *actor)
{
    if (actor->source_hit_recovery_active != 2u)
        return 0;
    if (actor->state == avsp_round1_class1f_source_ko.dispatch_state)
    {
        if (actor->source_hit_mode != avsp_round1_class1f_source_ko.hit_mode ||
            actor->source_hit_kind != avsp_round1_class1f_source_ko.hit_kind ||
            actor->source_reaction_selector !=
                avsp_round1_class1f_source_ko.reaction_selector)
            return 0;
        if (actor->substate ==
                avsp_round1_class1f_source_ko.action_phases[0])
        {
            if (actor->source_action_timer != 0u)
            {
                --actor->source_action_timer;
                return 1;
            }
            actor->substate =
                avsp_round1_class1f_source_ko.action_phases[1];
            actor->source_action = actor->substate;
            actor->source_airborne = 0xffu;
            actor->source_x_velocity =
                avsp_round1_class1f_source_ko.
                    launch_x_velocity_before_facing;
            actor->source_x_acceleration =
                avsp_round1_class1f_source_ko.
                    launch_x_acceleration_before_facing;
            if (actor->source_facing_selector == 0u)
            {
                actor->source_x_velocity = -actor->source_x_velocity;
                actor->source_x_acceleration = -actor->source_x_acceleration;
            }
            actor->source_y_velocity =
                avsp_round1_class1f_source_ko.launch_y_velocity;
            actor->source_y_acceleration =
                avsp_round1_class1f_source_ko.launch_y_acceleration;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_ko.reaction_records[0],
                0u);
        }
        if (actor->substate ==
                avsp_round1_class1f_source_ko.action_phases[1])
        {
            if (avsp_round1_class1f_hit_step_motion(actor))
                return avsp_round1_class1f_step_source_ko_reaction_animation(
                    actor);
            avsp_round1_class1f_hit_clamp_y(actor);
            actor->substate =
                avsp_round1_class1f_source_ko.action_phases[2];
            actor->source_action = actor->substate;
            actor->source_airborne = 0u;
            actor->source_motion_flags = 1u;
            actor->source_hit_action_timer =
                avsp_round1_class1f_source_ko.landing_hold_timer;
            if (actor->palette != 0u)
                actor->coordinate_mode = 1u;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_ko.landing_hold_record,
                0u);
            return 1;
        }
        if (actor->substate ==
                avsp_round1_class1f_source_ko.action_phases[2])
        {
            if (actor->source_hit_action_timer == 0u)
                return 0;
            --actor->source_hit_action_timer;
            if (actor->source_hit_action_timer != 0u)
                return avsp_round1_class1f_step_source_hit_loop_record(
                    actor,
                    &avsp_round1_class1f_source_ko.landing_hold_record);
            actor->substate =
                avsp_round1_class1f_source_ko.action_phases[3];
            actor->source_action = actor->substate;
            actor->source_airborne = 1u;
            actor->source_motion_flags = 0u;
            actor->source_x_velocity =
                avsp_round1_class1f_source_ko.
                    bounce_x_velocity_before_facing;
            actor->source_x_acceleration =
                avsp_round1_class1f_source_ko.
                    bounce_x_acceleration_before_facing;
            if (actor->source_facing_selector == 0u)
            {
                actor->source_x_velocity = -actor->source_x_velocity;
                actor->source_x_acceleration = -actor->source_x_acceleration;
            }
            actor->source_y_velocity =
                avsp_round1_class1f_source_ko.bounce_y_velocity;
            actor->source_y_acceleration =
                avsp_round1_class1f_source_ko.bounce_y_acceleration;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_ko.bounce_record, 0u);
        }
        if (actor->substate ==
                avsp_round1_class1f_source_ko.action_phases[3])
        {
            if (avsp_round1_class1f_hit_step_motion(actor))
                return avsp_round1_class1f_step_source_hit_loop_record(
                    actor, &avsp_round1_class1f_source_ko.bounce_record);
            avsp_round1_class1f_hit_clamp_y(actor);
            actor->state = avsp_round1_class1f_source_ko.hold_state;
            actor->substate = 0u;
            actor->source_action = 0u;
            actor->source_airborne = 0u;
            actor->source_motion_flags = 1u;
            actor->source_hit_action_timer =
                avsp_round1_class1f_source_ko.removal_hold_timer;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_ko.landing_hold_record,
                0u);
            return 1;
        }
        return 0;
    }
    if (actor->state != avsp_round1_class1f_source_ko.hold_state ||
        actor->substate != 0u || actor->source_hit_action_timer == 0u)
        return 0;
    --actor->source_hit_action_timer;
    if (actor->source_hit_action_timer == 0u)
    {
        actor->state = avsp_round1_class1f_source_ko.release_state;
        actor->source_action_timer = 0u;
        actor->source_hit_recovery_active = 0u;
    }
    return 1;
}

static int avsp_round1_class1f_step_reaction(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    AvspPortV2HitKoRuntime reaction;
    unsigned short random;
    unsigned int timer_index;
    if (!avsp_round1_class1f_reaction_active(actor))
        return 1;
    if (actor->source_hit_recovery_active == 2u)
        return avsp_round1_class1f_step_source_ko(actor);
    if (actor->source_hit_recovery_active)
    {
        if (actor->state != avsp_round1_class1f_source_hit.state ||
            actor->source_hit_mode != avsp_round1_class1f_source_hit.hit_mode ||
            actor->source_reaction_selector !=
                avsp_round1_class1f_source_hit.reaction_selector)
            return 0;
        if (actor->substate ==
                avsp_round1_class1f_source_hit.entry_action_phase)
        {
            if (actor->animation_record !=
                    avsp_round1_class1f_source_hit.animation_record)
                return 0;
            if (actor->source_action_timer != 0u)
            {
                --actor->source_action_timer;
                return 1;
            }
            actor->substate = avsp_round1_class1f_source_hit.next_action_phase;
            actor->source_action = actor->substate;
            if (!avsp_round1_class1f_source_hit.
                    recovery_transition_returns)
                return 0;
            return 1;
        }
        if (actor->substate == avsp_round1_class1f_source_hit.phases[0])
        {
            actor->substate = avsp_round1_class1f_source_hit.phases[1];
            actor->source_action = actor->substate;
            actor->source_airborne = 0xffu;
            actor->source_x_velocity =
                avsp_round1_class1f_source_hit.
                    launch_x_velocity_before_facing;
            actor->source_x_acceleration =
                avsp_round1_class1f_source_hit.
                    launch_x_acceleration_before_facing;
            if (actor->source_facing_selector == 0u)
            {
                actor->source_x_velocity = -actor->source_x_velocity;
                actor->source_x_acceleration = -actor->source_x_acceleration;
            }
            actor->source_y_velocity =
                avsp_round1_class1f_source_hit.launch_y_velocity;
            actor->source_y_acceleration =
                avsp_round1_class1f_source_hit.launch_y_acceleration;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_hit.reaction_records[0],
                0u);
        }
        if (actor->substate == avsp_round1_class1f_source_hit.phases[1])
        {
            if (avsp_round1_class1f_hit_step_motion(actor))
                return avsp_round1_class1f_step_source_hit_reaction_animation(
                    actor);
            avsp_round1_class1f_hit_clamp_y(actor);
            actor->substate = avsp_round1_class1f_source_hit.phases[2];
            actor->source_action = actor->substate;
            actor->source_airborne = 0u;
            actor->source_motion_flags = 1u;
            avsp_round1_class1f_hit_clear_motion(actor);
            actor->source_hit_action_timer =
                avsp_round1_class1f_source_hit.landing_hold_timer;
            if (actor->palette != 0u)
                actor->coordinate_mode = 1u;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_hit.landing_hold_record,
                0u);
            return 1;
        }
        if (actor->substate == avsp_round1_class1f_source_hit.phases[2])
        {
            if (actor->source_hit_action_timer == 0u)
                return 0;
            --actor->source_hit_action_timer;
            if (actor->source_hit_action_timer != 0u)
                return avsp_round1_class1f_step_source_hit_loop_record(
                    actor, &avsp_round1_class1f_source_hit.landing_hold_record);
            actor->substate = avsp_round1_class1f_source_hit.phases[3];
            actor->source_action = actor->substate;
            actor->source_airborne = 0xffu;
            actor->source_motion_flags = 0u;
            actor->source_x_velocity =
                avsp_round1_class1f_source_hit.
                    bounce_x_velocity_before_facing;
            actor->source_x_acceleration =
                avsp_round1_class1f_source_hit.
                    bounce_x_acceleration_before_facing;
            if (actor->source_facing_selector == 0u)
            {
                actor->source_x_velocity = -actor->source_x_velocity;
                actor->source_x_acceleration = -actor->source_x_acceleration;
            }
            actor->source_y_velocity =
                avsp_round1_class1f_source_hit.bounce_y_velocity;
            actor->source_y_acceleration =
                avsp_round1_class1f_source_hit.bounce_y_acceleration;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_hit.bounce_record, 0u);
        }
        if (actor->substate == avsp_round1_class1f_source_hit.phases[3])
        {
            if (avsp_round1_class1f_hit_step_motion(actor))
                return avsp_round1_class1f_step_source_hit_loop_record(
                    actor, &avsp_round1_class1f_source_hit.bounce_record);
            avsp_round1_class1f_hit_clamp_y(actor);
            if (actor->health < 0)
                return 0;
            actor->substate = avsp_round1_class1f_source_hit.phases[4];
            actor->source_action = actor->substate;
            actor->source_airborne = 0u;
            actor->source_motion_flags = 1u;
            avsp_round1_class1f_hit_clear_motion(actor);
            random = avsp_round1_source_rng(runtime);
            timer_index = (unsigned int)(random & 0x000fu) +
                ((unsigned int)actor->source_collision_guard6d << 4);
            if (timer_index >=
                    AVSP_ROUND1_CLASS1F_SOURCE_HIT_RNG_TIMER_COUNT)
                return 0;
            actor->source_hit_action_timer =
                avsp_round1_class1f_source_hit.rng_timer_row[timer_index];
            if (actor->source_hit_action_timer == 0u)
                return 0;
            avsp_round1_class1f_bind_source_hit_record(
                actor, &avsp_round1_class1f_source_hit.rng_hold_record, 0u);
            return 1;
        }
        if (actor->substate == avsp_round1_class1f_source_hit.phases[4])
        {
            if (runtime->source_global_hit_pause !=
                    avsp_round1_class1f_source_hit.global_pause_guard_zero)
                return 1;
            if (actor->source_hit_action_timer == 0u)
                return 0;
            --actor->source_hit_action_timer;
            if (actor->source_hit_action_timer != 0u)
                return avsp_round1_class1f_step_source_hit_loop_record(
                    actor, &avsp_round1_class1f_source_hit.rng_hold_record);
            actor->substate = avsp_round1_class1f_source_hit.phases[5];
            actor->source_action = actor->substate;
            actor->source_collision_guard6d = 0u;
            avsp_round1_class1f_bind_source_hit_terminal(actor, 0u);
            return 1;
        }
        if (actor->substate == avsp_round1_class1f_source_hit.phases[5])
            return avsp_round1_class1f_step_source_hit_terminal(actor);
        return 0;
    }
    if (!avsp_round1_class1f_rebuild_reaction(actor, &reaction))
        return 0;
    if (reaction.active)
    {
        if (!avsp_port_v2_hit_ko_step(&reaction))
            return 0;
    }
    --actor->source_action_timer;
    return avsp_round1_class1f_sync_reaction(actor, &reaction);
}

static int avsp_round1_class1f_melee_collision(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned char hit_value = 0u;
    short damage;
    short health;
    if (!runtime->player_action.attack_active)
    {
        runtime->first_encounter.attack_latched = 0u;
        return 1;
    }
    if (runtime->first_encounter.attack_latched ||
        avsp_round1_class1f_reaction_active(actor) ||
        actor->health < 0)
        return 1;
    if (!avsp_round1_class1f_melee_overlap(runtime, actor, &hit_value))
        return 1;
    runtime->first_encounter.attack_latched = 1u;
    damage = avsp_round1_class1f_player_damage(
        runtime->player_action.selector);
    if (damage <= 0 ||
        hit_value != (unsigned char)avsp_pw_action_defs[
            runtime->player_action.selector - 1u].box.hit_value)
        return 0;
    ++runtime->first_encounter.player_contacts;
    ++runtime->first_encounter.alien_damage_events;
    health = (short)(actor->health - damage);
    actor->health = health < 0 ? -1 : health;
    avsp_pw_report_contact(&runtime->player_action);
    return avsp_round1_class1f_begin_reaction(runtime, actor,
                                               actor->health < 0);
}

static const AvspRound1Class1fActionVariantSpec *
avsp_round1_find_class1f_action_variant(unsigned char variant)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_ACTION_VARIANT_COUNT;
         ++index)
        if (avsp_round1_class1f_action_variants[index].variant == variant)
            return &avsp_round1_class1f_action_variants[index];
    return 0;
}

static const AvspRound1Class1fActionSelectorSpec *
avsp_round1_find_class1f_action_selector(unsigned char selector)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_ACTION_SELECTOR_COUNT;
         ++index)
        if (avsp_round1_class1f_action_selectors[index].selector == selector)
            return &avsp_round1_class1f_action_selectors[index];
    return 0;
}

static const AvspRound1Class1fActionRecordSpec *
avsp_round1_find_class1f_action_record(unsigned long address)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_ACTION_RECORD_COUNT;
         ++index)
        if (avsp_round1_class1f_action_records[index].animation_record ==
                address)
            return &avsp_round1_class1f_action_records[index];
    return 0;
}

static const AvspRound1Class1fMovementTableSpec *
avsp_round1_find_class1f_movement_table(unsigned char table_index)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_MOVEMENT_TABLE_COUNT;
         ++index)
        if (avsp_round1_class1f_movement_tables[index].table_index ==
                table_index)
            return &avsp_round1_class1f_movement_tables[index];
    return 0;
}

static const AvspRound1Class1fActionRecordSpec *
avsp_round1_find_class1f_inner8_record(unsigned long address)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS1F_INNER8_RECORD_COUNT;
         ++index)
        if (avsp_round1_class1f_inner8_records[index].animation_record ==
                address)
            return &avsp_round1_class1f_inner8_records[index];
    return 0;
}

static const AvspRound1Class1fMovementTableSpec *
avsp_round1_find_class1f_inner8_movement_table(unsigned char table_index)
{
    unsigned int index;
    for (index = 0u;
         index < AVSP_ROUND1_CLASS1F_INNER8_MOVEMENT_TABLE_COUNT; ++index)
        if (avsp_round1_class1f_inner8_movement_tables[index].table_index ==
                table_index)
            return &avsp_round1_class1f_inner8_movement_tables[index];
    return 0;
}

static void avsp_round1_bind_class1f_action_record(
    AvspRound1ActorCore *actor,
    const AvspRound1Class1fActionRecordSpec *record)
{
    actor->animation_record = record->animation_record;
    actor->source_next_animation_record = record->next_animation_record;
    actor->assembly = record->assembly;
    actor->animation_timer = record->timer;
    actor->animation_branch = record->branch;
    actor->source_movement_table = record->movement_table;
}

static int avsp_round1_bind_class1f_inner8_record(
    AvspRound1ActorCore *actor, unsigned long address)
{
    const AvspRound1Class1fActionRecordSpec *record =
        avsp_round1_find_class1f_inner8_record(address);
    if (record == 0)
        return 0;
    avsp_round1_bind_class1f_action_record(actor, record);
    return 1;
}

static int avsp_round1_step_class1f_inner8_animation(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    int apply_movement)
{
    const AvspRound1Class1fActionRecordSpec *next;
    if (actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    ++runtime->class1f_action_animation_steps;
    if (actor->animation_timer != 0u)
        return 1;
    next = avsp_round1_find_class1f_inner8_record(
        actor->source_next_animation_record);
    if (next == 0)
        return 0;
    avsp_round1_bind_class1f_action_record(actor, next);
    if (apply_movement && actor->source_movement_table != 0u)
    {
        const AvspRound1Class1fMovementTableSpec *table =
            avsp_round1_find_class1f_inner8_movement_table(
                actor->source_movement_table);
        const AvspRound1Class1fMovementVectorSpec *vector;
        if (table == 0 || actor->source_direction >=
                AVSP_ROUND1_CLASS1F_MOVEMENT_DIRECTION_COUNT)
            return 0;
        vector = &table->vectors[actor->source_direction];
        actor->source_x_fp += (long)vector->x_delta * 256L;
        actor->source_y_fp += (long)vector->y_delta * 256L;
        actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        actor->z = actor->y;
        ++runtime->class1f_action_movement_steps;
    }
    return 1;
}

static int avsp_round1_bind_class1f_action_selector(
    AvspRound1ActorCore *actor, unsigned char selector)
{
    const AvspRound1Class1fActionSelectorSpec *sequence =
        avsp_round1_find_class1f_action_selector(selector);
    if (sequence == 0 || sequence->record_count == 0u ||
        sequence->first_record >= AVSP_ROUND1_CLASS1F_ACTION_RECORD_COUNT)
        return 0;
    actor->animation_index = 0u;
    avsp_round1_bind_class1f_action_record(actor,
        &avsp_round1_class1f_action_records[sequence->first_record]);
    return 1;
}

static int avsp_round1_step_class1f_action_animation(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    int apply_movement)
{
    const AvspRound1Class1fActionRecordSpec *next;
    if (actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    ++runtime->class1f_action_animation_steps;
    if (actor->animation_timer != 0u)
        return 1;
    next = avsp_round1_find_class1f_action_record(
        actor->source_next_animation_record);
    if (next == 0)
        return 0;
    avsp_round1_bind_class1f_action_record(actor, next);
    if (apply_movement && actor->source_movement_table != 0u)
    {
        const AvspRound1Class1fMovementTableSpec *table =
            avsp_round1_find_class1f_movement_table(
                actor->source_movement_table);
        const AvspRound1Class1fMovementVectorSpec *vector;
        if (table == 0 || actor->source_direction >=
                AVSP_ROUND1_CLASS1F_MOVEMENT_DIRECTION_COUNT)
            return 0;
        vector = &table->vectors[actor->source_direction];
        actor->source_x_fp += (long)vector->x_delta * 256L;
        actor->source_y_fp += (long)vector->y_delta * 256L;
        actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        ++runtime->class1f_action_movement_steps;
    }
    return 1;
}

static int avsp_round1_set_class1f_action(AvspRound1ActorCore *actor,
                                          unsigned char action,
                                          int selector)
{
    actor->state = 0x0200u;
    actor->substate = (unsigned short)action << 8;
    actor->source_action = actor->substate;
    actor->source_action_initialized = 1u;
    if (selector < 0)
        return 1;
    return avsp_round1_bind_class1f_action_selector(actor,
                                                     (unsigned char)selector);
}

static int avsp_round1_seed_class1f_action_fields(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    unsigned short random, unsigned char entry_delay, int bind_selector)
{
    const AvspRound1Class1fActionVariantSpec *spec =
        avsp_round1_find_class1f_action_variant(actor->variant);
    unsigned char selector = spec != 0 ? spec->animation_selector : 0u;
    if (spec == 0)
        return 0;
    if (actor->source_dynamic_spawn != 0u &&
        avsp_round1_recurring_spawn.preserve_reused_position_fraction != 0u)
    {
        actor->source_x_fp = (long)(((unsigned long)(unsigned short)actor->x <<
            16) | ((unsigned long)actor->source_x_fp & 0x0000ffffUL));
        actor->source_y_fp = (long)(((unsigned long)(unsigned short)actor->y <<
            16) | ((unsigned long)actor->source_y_fp & 0x0000ffffUL));
    }
    else
    {
        actor->source_x_fp = (long)actor->x * 65536L;
        actor->source_y_fp = (long)actor->y * 65536L;
    }
    actor->source_z_fp = (long)actor->z * 65536L;
    actor->source_a3 = (unsigned char)((random >> 2) & 1u);
    actor->source_a4 = spec->a4;
    actor->source_a5 = spec->a5;
    actor->source_a6 = spec->a6;
    actor->source_airborne = spec->airborne;
    actor->source_style85 = (spec->rule_flags & 0x04u) != 0u ?
        spec->style85 : 1u;
    if (spec->variant == 9u)
        actor->source_style85 = (unsigned char)((random >> 2) & 1u);
    actor->source_action_timer = (spec->rule_flags & 0x20u) != 0u ?
        entry_delay : spec->timer_aa;
    actor->source_bound_b2 = (spec->rule_flags & 0x80u) != 0u ?
        (unsigned short)(spec->bound_b2_base + (random & 0x007fu)) : 0u;
    actor->facing = actor->source_a5;
    actor->source_direction = (unsigned char)(
        ((actor->source_a5 ^ 1u) << 4) + 8u);
    if ((spec->rule_flags & 0x40u) != 0u)
        selector = (unsigned char)((actor->source_style85 ? 0x48u : 0x44u) +
            actor->source_a4);
    if (!avsp_round1_set_class1f_action(actor,
            (spec->rule_flags & 0x01u) != 0u ? spec->action : 0u,
            bind_selector && ((spec->rule_flags & (0x08u | 0x40u)) != 0u) ?
                (int)selector : -1))
        return 0;
    ++runtime->class1f_action_initializations;
    return 1;
}

#if 0
static int avsp_round1_first_encounter_sync_reaction(
    AvspRound1ActorCore *actor,
    const AvspRound1FirstEncounterRuntime *encounter)
{
    if (!avsp_round1_class1f_bind_record(
            actor, encounter->reaction.actor.anim_record))
        return 0;
    actor->state = encounter->reaction.actor.sub_state;
    actor->substate = encounter->reaction.actor.action;
    return avsp_round1_class1f_state_context_supported(
        actor->state, actor->substate);
}
#endif

static void avsp_round1_mark_first_encounter_current(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    if ((unsigned short)actor->source_slot !=
            (unsigned short)avsp_round1_class1f_current.
                bounded_dynamic_source_slot)
        return;
    encounter->actor_source_slot = actor->source_slot;
    encounter->dynamic_spawned = 1u;
    encounter->encounter_state = AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE;
}

static void avsp_round1_initialize_recurring_actor(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    short x, short y, short z, unsigned char variant,
    unsigned char selector)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    actor->active = 0u;
    ++encounter->source_living_count;
    actor->active = 1u;
    actor->actor_class = 0x1f;
    actor->variant = variant;
    actor->state = 0u;
    actor->substate = 0u;
    actor->x = x;
    actor->y = y;
    actor->z = z;
    actor->source_x_fp = (long)(((unsigned long)(unsigned short)x << 16) |
        ((unsigned long)actor->source_x_fp & 0x0000ffffUL));
    actor->source_y_fp = (long)(((unsigned long)(unsigned short)y << 16) |
        ((unsigned long)actor->source_y_fp & 0x0000ffffUL));
    actor->source_z_fp = (long)z * 65536L;
    actor->transition_timer = 0u;
    actor->source_selector83 = selector;
    actor->source_dynamic_spawn = 1u;
    avsp_round1_mark_first_encounter_current(runtime, actor);
}

static void avsp_round1_spawn_recurring_auxiliary(AvspRound1Runtime *runtime)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    AvspRound1ActorCore *actor;
    unsigned char phase = (unsigned char)(encounter->source_phase_counter +
        avsp_round1_recurring_spawn.auxiliary_phase_add);
    if (runtime->camera_x_position >=
            avsp_round1_recurring_spawn.auxiliary_camera_x_limit ||
        (phase & avsp_round1_recurring_spawn.auxiliary_phase_mask) != 0u)
        return;
    actor = avsp_round1_allocate_pool_actor_preserve_position_fraction(
        runtime, 0u);
    if (actor != 0)
        avsp_round1_initialize_recurring_actor(runtime, actor,
            avsp_round1_recurring_spawn.auxiliary_x,
            avsp_round1_recurring_spawn.auxiliary_y,
            avsp_round1_recurring_spawn.auxiliary_z,
            avsp_round1_recurring_spawn.auxiliary_variant,
            avsp_round1_recurring_spawn.auxiliary_selector);
}

static void avsp_round1_spawn_recurring_primary(AvspRound1Runtime *runtime)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    AvspRound1ActorCore *actor;
    unsigned short random;
    unsigned short lane_index;
    unsigned short variant_index;
    unsigned char lane_bucket;
    unsigned char selector;
    short lane;
    if ((encounter->source_phase_counter &
            avsp_round1_recurring_spawn.primary_phase_mask) != 0u)
        return;
    actor = avsp_round1_allocate_pool_actor_preserve_position_fraction(
        runtime, 0u);
    if (actor == 0)
        return;
    (void)avsp_round1_source_rng(runtime);
    random = runtime->rng_seed;
    lane_index = (unsigned short)((((unsigned short)(
        runtime->camera_z_position - 208)) & 0x00f0u) +
        (random & 0x000fu));
    if (lane_index >= AVSP_ROUND1_RECURRING_LANE_BUCKET_COUNT)
    {
        ++runtime->failure_count;
        return;
    }
    lane_bucket = avsp_round1_recurring_lane_buckets[lane_index];
    variant_index = (unsigned short)(((unsigned short)lane_bucket << 4) +
        ((random >> 4) & 0x000fu));
    if (lane_bucket >= AVSP_ROUND1_RECURRING_LANE_OFFSET_COUNT ||
        variant_index >= AVSP_ROUND1_RECURRING_VARIANT_COUNT ||
        encounter->source_spawn_index >= AVSP_ROUND1_RECURRING_SELECTOR_COUNT)
    {
        ++runtime->failure_count;
        return;
    }
    lane = (short)(runtime->camera_z_position +
        avsp_round1_recurring_lane_offsets[lane_bucket]);
    selector = avsp_round1_recurring_selector_cycle[
        encounter->source_spawn_index];
    avsp_round1_initialize_recurring_actor(runtime, actor,
        (short)(runtime->camera_x_position +
            avsp_round1_recurring_spawn.primary_x_offset),
        lane, lane, avsp_round1_recurring_variants[variant_index], selector);
    if (encounter->source_spawn_index == 0u)
        encounter->source_spawn_index =
            AVSP_ROUND1_RECURRING_SELECTOR_COUNT - 1u;
    else
        --encounter->source_spawn_index;
    runtime->entry_controller.x = (short)encounter->source_spawn_index;
}

static int avsp_round1_step_recurring_controller(AvspRound1Runtime *runtime)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    encounter->source_phase_counter = (unsigned char)(
        encounter->source_phase_counter + 1u);
    if (!encounter->source_controller_initialized ||
        !encounter->source_initial_spawn_complete)
        return 1;
    ++encounter->source_controller_updates;
    if (runtime->entry_controller.state ==
            avsp_round1_recurring_spawn.wait_state)
    {
        if (encounter->source_intro_gate != 0u)
            return 1;
        encounter->source_intro_timer = (unsigned short)(
            encounter->source_intro_timer - 1u);
        if ((short)encounter->source_intro_timer >= 0)
            return 1;
        runtime->entry_controller.state =
            avsp_round1_recurring_spawn.current_state;
        encounter->source_camera_target =
            avsp_round1_recurring_spawn.source_camera_target_current;
        if (runtime->camera_x_position <=
                avsp_round1_recurring_spawn.source_camera_call_threshold)
        {
            encounter->source_phase =
                avsp_round1_recurring_spawn.conditional_phase;
            encounter->source_local =
                avsp_round1_recurring_spawn.conditional_local;
        }
        return 1;
    }
    if (runtime->entry_controller.state !=
            avsp_round1_recurring_spawn.current_state)
        return 1;
    if (encounter->source_progress >= encounter->source_spawn_limit)
        return 1;
    encounter->source_spawn_timer = (unsigned short)(
        encounter->source_spawn_timer - 1u);
    if ((short)encounter->source_spawn_timer < 0)
        return 1;
    if (encounter->source_living_count >=
            avsp_round1_recurring_spawn.maximum_living)
    {
        encounter->source_blocked_by_living_count = 1u;
        return 1;
    }
    encounter->source_blocked_by_living_count = 0u;
    avsp_round1_spawn_recurring_auxiliary(runtime);
    avsp_round1_spawn_recurring_primary(runtime);
    return 1;
}

static int avsp_round1_class1f_player_near(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *actor)
{
    short dx = (short)(runtime->player_action.x - actor->x);
    short dz = (short)(runtime->player_action.lane - actor->z);
    return runtime->player.active != 0u &&
        runtime->player_action.state != AVSP_PW_STATE_KO &&
        (unsigned short)(dx + (short)
            avsp_round1_class1f_action_program.near_x_bias) <=
            avsp_round1_class1f_action_program.near_x_span &&
        (unsigned short)(dz + (short)
            avsp_round1_class1f_action_program.near_z_bias) <=
            avsp_round1_class1f_action_program.near_z_span;
}

static int avsp_round1_class1f_enter_near_action4(
    AvspRound1ActorCore *actor, short player_x)
{
    unsigned char desired = player_x < actor->x ? 0u : 1u;
    int selector;
    actor->source_a5 = desired;
    if (desired != actor->facing)
    {
        actor->facing = desired;
        actor->substate = 0x0406u;
        actor->source_action = actor->substate;
        selector = avsp_round1_class1f_action_program.turn_selectors[
            actor->source_style85 ? 1u : 0u];
    }
    else if (actor->source_style85)
    {
        actor->substate = 0x0408u;
        actor->source_action = actor->substate;
        selector = avsp_round1_class1f_action_program.idle_selectors[0];
    }
    else
    {
        actor->substate = 0x0400u;
        actor->source_action = actor->substate;
        return 1;
    }
    return avsp_round1_bind_class1f_action_selector(
        actor, (unsigned char)selector);
}

/* 0 releases, 1 continues, 2 entered action 0x04, -1 is a bind failure. */
static int avsp_round1_class1f_source_bounds(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned short relative;
    if (actor->source_a2 == 0u)
    {
        if ((unsigned short)actor->x >
                avsp_round1_class1f_action_program.x_max)
            return 0;
        if (actor->source_field01 == 0u)
            return 1;
        actor->source_a2 = 1u;
    }
    if ((runtime->class1f_phase_guard_counter &
            avsp_round1_class1f_action_program.phase_guard_mask) != 0u)
    {
        if (!avsp_round1_class1f_player_near(runtime, actor))
            return 1;
        return avsp_round1_class1f_enter_near_action4(
            actor, runtime->player_action.x) ? 2 : -1;
    }
    relative = (unsigned short)((unsigned short)actor->x -
        (unsigned short)runtime->camera_x_position +
        avsp_round1_class1f_action_program.camera_relative_bias);
    return relative <=
        avsp_round1_class1f_action_program.camera_relative_span;
}

static void avsp_round1_class1f_derive_direction(AvspRound1ActorCore *actor)
{
    unsigned char right;
    unsigned char left;
    if ((unsigned short)actor->z >=
            avsp_round1_class1f_action_program.upper_lane)
    {
        right = avsp_round1_class1f_action_program.upper_directions[0];
        left = avsp_round1_class1f_action_program.upper_directions[1];
    }
    else if ((unsigned short)actor->z <
             avsp_round1_class1f_action_program.lower_lane)
    {
        right = avsp_round1_class1f_action_program.lower_directions[0];
        left = avsp_round1_class1f_action_program.lower_directions[1];
    }
    else
        return;
    actor->source_direction = actor->source_a5 ? left : right;
}

static int avsp_round1_step_class1f_action_zero(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    int selector;
    if (runtime->route_state == 0)
        return 0;
    if (avsp_round1_class1f_player_near(runtime, actor))
        return avsp_round1_class1f_enter_near_action4(
            actor, runtime->player_action.x);
    if (actor->source_a5 != actor->facing)
    {
        actor->facing ^= 1u;
        return avsp_round1_set_class1f_action(actor, 0x0au,
            avsp_round1_class1f_action_program.turn_selectors[
                actor->source_style85 ? 1u : 0u]);
    }
    if (actor->source_a3 == actor->source_style85)
    {
        unsigned char action = actor->source_a6 != 0u ? 0x16u : 0x02u;
        if (actor->source_a6 != 0u)
            actor->source_b0 = 2u;
        selector = avsp_round1_class1f_action_program.
            movement_selector_bases[actor->source_style85 ? 1u : 0u] +
            actor->source_a4;
        return avsp_round1_set_class1f_action(actor, action, selector);
    }
    if (actor->source_a3 != 0u)
        return avsp_round1_set_class1f_action(actor, 0x08u,
            avsp_round1_class1f_action_program.idle_selectors[1]);
    return avsp_round1_set_class1f_action(actor, 0x06u,
        avsp_round1_class1f_action_program.idle_selectors[0]);
}

static int avsp_round1_class1f_action4_bind_group_selector(
    AvspRound1ActorCore *actor)
{
    unsigned char group = actor->source_action_group;
    unsigned char cursor = actor->source_action_group_cursor;
    unsigned short first;
    if (group >= AVSP_ROUND1_CLASS1F_ACTION4_GROUP_COUNT ||
        cursor >= avsp_round1_class1f_action_program.action4_group_count[group])
        return 0;
    first = avsp_round1_class1f_action_program.action4_group_first[group];
    return avsp_round1_bind_class1f_action_selector(actor,
        (unsigned char)avsp_round1_class1f_action_program.action4_selectors[
            first + cursor]);
}

static int avsp_round1_class1f_action4_begin_group(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned short random = avsp_round1_source_rng(runtime);
    unsigned short table_offset =
        avsp_round1_class1f_action_program.action4_random_groups[
            random & 0x001fu];
    if ((table_offset & 1u) != 0u ||
        table_offset / 2u >= AVSP_ROUND1_CLASS1F_ACTION4_GROUP_COUNT)
        return 0;
    ++runtime->class1f_action4_rng_calls;
    actor->substate = 0x0402u;
    actor->source_action = actor->substate;
    actor->source_action_group = (unsigned char)(table_offset / 2u);
    actor->source_action_group_cursor = 0u;
    actor->source_player_guard = 0u;
    return avsp_round1_class1f_action4_bind_group_selector(actor);
}

static unsigned char avsp_round1_class1f_action4_timer(
    AvspRound1Runtime *runtime)
{
    unsigned short random = avsp_round1_source_rng(runtime);
    unsigned short stage = runtime->source_stage_parameter;
    unsigned char offset;
    unsigned char row;
    ++runtime->class1f_action4_timer_rng_calls;
    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT)
        stage = AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT - 1u;
    offset = avsp_round1_class1f_action_program.action4_stage_offsets[stage];
    row = (unsigned char)(offset / AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT);
    if (row >= AVSP_ROUND1_CLASS1F_ACTION4_TIMER_ROW_COUNT)
        return 0u;
    return avsp_round1_class1f_action_program.action4_timer_rows[row]
        [random & 0x001fu];
}

static int avsp_round1_step_class1f_action4(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned char phase = (unsigned char)actor->substate;
    if (phase == 0u)
        return avsp_round1_class1f_action4_begin_group(runtime, actor);
    if (phase == 2u)
    {
        if (actor->animation_branch >= 0)
            return avsp_round1_step_class1f_action_animation(runtime,
                                                              actor, 0);
        actor->substate = 0x0404u;
        actor->source_action = actor->substate;
        actor->source_action_timer = avsp_round1_class1f_action4_timer(runtime);
        if (actor->source_action_timer == 0u)
            return 0;
        if (actor->source_player_guard == 0u)
            return avsp_round1_set_class1f_action(actor, 0u, -1);
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    }
    if (phase == 4u)
    {
        if (actor->source_action_timer == 0u)
            return 0;
        --actor->source_action_timer;
        if (actor->source_action_timer != 0u)
            return 1;
        actor->substate = 0x0402u;
        actor->source_action = actor->substate;
        ++actor->source_action_group_cursor;
        if (actor->source_action_group_cursor <
            avsp_round1_class1f_action_program.action4_group_count[
                actor->source_action_group])
            return avsp_round1_class1f_action4_bind_group_selector(actor);
        actor->substate = 0x0400u;
        actor->source_action = actor->substate;
        return avsp_round1_class1f_action4_begin_group(runtime, actor);
    }
    if (phase == 6u || phase == 8u)
    {
        if (actor->animation_branch < 0)
        {
            actor->substate = 0x0400u;
            actor->source_action = actor->substate;
            if (phase == 8u)
                actor->source_style85 = 0u;
            return 1;
        }
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    }
    return 0;
}

static unsigned char avsp_round1_class1f_inner8_direction(
    const AvspRound1ActorCore *actor, short target_x, short target_z)
{
    unsigned short dx;
    unsigned short dz;
    unsigned short larger;
    unsigned short smaller;
    unsigned short accumulator;
    unsigned char d6 = 0u;
    unsigned char carry;
    unsigned char ratio = 0u;
    unsigned char base;
    unsigned char table_index;
    unsigned int iterations;
    dz = (unsigned short)((unsigned short)(target_z + 64) -
                          (unsigned short)(actor->y + 64));
    if (dz == 0u)
        return (short)(target_x - actor->x) < 0 ? 24u : 8u;
    carry = (unsigned char)((dz & 0x8000u) != 0u);
    dz = (unsigned short)(dz << 1);
    d6 = (unsigned char)(carry << 7);
    if ((d6 & 0x80u) != 0u)
        dz = (unsigned short)(0u - dz);
    dx = (unsigned short)((unsigned short)(target_x + 0x1000) -
                          (unsigned short)(actor->x + 0x1000));
    if (dx == 0u)
        return (unsigned char)(d6 >> 3);
    carry = (unsigned char)((unsigned short)(target_x + 0x1000) <
                            (unsigned short)(actor->x + 0x1000));
    d6 = (unsigned char)((carry << 7) | (d6 >> 1));
    if ((d6 & 0x80u) != 0u)
        dx = (unsigned short)(0u - dx);
    if (dz == dx)
    {
        table_index = (unsigned char)(((d6 << 2) | (d6 >> 6)) & 3u);
        return avsp_round1_class1f_inner8_program.direction_axis_equal[
            table_index];
    }
    carry = (unsigned char)(dz < dx);
    if (!carry)
    {
        larger = dz;
        smaller = dx;
    }
    else
    {
        larger = dx;
        smaller = dz;
    }
    d6 = (unsigned char)((carry << 7) | (d6 >> 1));
    larger = (unsigned short)(larger << 1);
    accumulator = (unsigned short)(smaller << 4);
    for (iterations = 0u; iterations < 8u; ++iterations)
    {
        if (accumulator < larger)
            break;
        accumulator = (unsigned short)(accumulator - larger);
        ++ratio;
    }
    table_index = (unsigned char)(((d6 << 3) | (d6 >> 5)) & 7u);
    base = avsp_round1_class1f_inner8_program.direction_octant_base[
        table_index];
    if ((base & 1u) == 0u)
        base = (unsigned char)(base + ratio + 1u);
    else
    {
        base = (unsigned char)(base & 0xfeu);
        if (ratio != 0u)
            ++ratio;
        base = (unsigned char)(base - ratio);
    }
    return (unsigned char)((base & 0x3fu) >> 1);
}

static int avsp_round1_class1f_inner8_wander(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned char random;
    unsigned char offset_index;
    unsigned char direction_delta;
    short target_x;
    short target_z;
    if (actor->source_player_guard != 0u)
        actor->source_player_guard = 0u;
    if (actor->source_action_group_cursor == 0u)
    {
        (void)avsp_round1_source_rng(runtime);
        if ((signed char)actor->source_action_group < 0)
            return 0;
        offset_index = (unsigned char)(actor->source_action_group & 6u);
    }
    else
        offset_index = (unsigned char)(actor->source_action_group & 6u);
    actor->source_action_group_cursor = (unsigned char)(
        actor->source_action_group_cursor + 1u);
    if (actor->source_action_group_cursor >= 15u)
        actor->source_action_group_cursor = 0u;
    target_x = (short)(runtime->player_action.x +
        avsp_round1_class1f_inner8_program.wander_target_offsets[
            offset_index >> 1]);
    target_z = (short)(runtime->player_action.lane + 48);
    actor->source_direction = avsp_round1_class1f_inner8_direction(
        actor, target_x, target_z);
    random = avsp_round1_source_rng(runtime);
    if ((actor->source_action_group >> 1) == actor->source_a3)
        direction_delta = avsp_round1_class1f_inner8_program.
            wander_direction_delta_same_style[random & 0x1fu];
    else
        direction_delta = avsp_round1_class1f_inner8_program.
            wander_direction_delta_other_style[random & 0x1fu];
    actor->source_direction = (unsigned char)(
        (actor->source_direction - direction_delta) & 0x1fu);
    actor->source_player_guard = 1u;
    return 1;
}

static int avsp_round1_class1f_inner8_bind_movement(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned long record = actor->source_style85 ?
        avsp_round1_class1f_inner8_program.style_one_record :
        avsp_round1_class1f_inner8_program.style_zero_record;
    if (!avsp_round1_class1f_inner8_wander(runtime, actor))
        return 0;
    actor->source_primary_animation_record = record;
    return avsp_round1_bind_class1f_inner8_record(actor, record);
}

static int avsp_round1_class1f_inner8_player_near(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *actor,
    unsigned short x_span, unsigned short z_span)
{
    short dx = (short)(runtime->player_action.x - actor->x);
    short dz = (short)(runtime->player_action.lane - actor->z);
    unsigned short abs_x = (unsigned short)(dx < 0 ? -dx : dx);
    unsigned short abs_z = (unsigned short)(dz < 0 ? -dz : dz);
    return abs_x <= x_span && abs_z <= z_span;
}

static int avsp_round1_class1f_enter_inner8(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor,
    unsigned short *random_out, unsigned char *rng_consumed)
{
    unsigned char target_side;
    if (actor->animation_branch >= 0 || actor->animation_timer != 1u ||
        actor->source_b0 != 0u)
        return 0;
    target_side = runtime->player_action.x < actor->x ? 0u : 1u;
    if (target_side == actor->facing || actor->source_motion_flags != 0u)
        return 0;
    actor->source_motion_flags = 1u;
    (void)avsp_round1_source_rng(runtime);
    *random_out = runtime->rng_seed;
    *rng_consumed = 1u;
    if ((*random_out & 3u) != 0u)
        return 0;
    actor->source_motion_fields[2] = 1;
    actor->transition_timer =
        avsp_round1_class1f_inner8_program.inner_timer;
    actor->source_target_low = 0x8380u;
    actor->facing ^= 1u;
    actor->state = 0x0208u;
    actor->substate = 0x0600u;
    actor->source_action = actor->substate;
    actor->source_motion_fields[0] = 0;
    if (!avsp_round1_bind_class1f_inner8_record(actor,
            avsp_round1_class1f_inner8_program.turn_record))
        return -1;
    return 1;
}

static int avsp_round1_step_class1f_inner8(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    unsigned char action = (unsigned char)(actor->substate >> 8);
    unsigned char random;
    unsigned char selected_style;
    unsigned char target_side;
    if (actor->transition_timer != 0u)
        --actor->transition_timer;
    if (action == 0u)
    {
        if (runtime->route_state == 0)
            return 0;
        random = avsp_round1_source_rng(runtime);
        selected_style = (unsigned char)((
            avsp_round1_class1f_inner8_program.action0_style_bits >>
            (random & 15u)) & 1u);
        if (selected_style != actor->source_style85)
        {
            if (actor->source_style85 != 0u)
            {
                actor->substate = 0x0800u;
                actor->source_action = actor->substate;
                return avsp_round1_bind_class1f_inner8_record(actor,
                    avsp_round1_class1f_inner8_program.idle_record);
            }
            actor->substate = 0x0a00u;
            actor->source_action = actor->substate;
            return avsp_round1_bind_class1f_inner8_record(actor,
                avsp_round1_class1f_inner8_program.mismatch_zero_record);
        }
        random = avsp_round1_source_rng(runtime);
        actor->source_motion_fields[3] = avsp_round1_class1f_inner8_program.
            field88_table[random & 15u];
        actor->substate = 0x0400u;
        actor->source_action = actor->substate;
        actor->source_action_group_cursor = 0u;
        return avsp_round1_class1f_inner8_bind_movement(runtime, actor);
    }
    if (action == 0x06u)
    {
        if (actor->animation_branch < 0)
        {
            actor->substate = 0u;
            actor->source_action = 0u;
            return 1;
        }
        return avsp_round1_step_class1f_inner8_animation(runtime, actor, 0);
    }
    if (action == 0x08u)
    {
        if (actor->animation_branch < 0)
        {
            actor->source_style85 = 0u;
            actor->substate = 0x0400u;
            actor->source_action = actor->substate;
            random = avsp_round1_source_rng(runtime);
            actor->source_motion_fields[3] = avsp_round1_class1f_inner8_program.
                field88_table[random & 15u];
            actor->source_action_group_cursor = 0u;
            return avsp_round1_class1f_inner8_bind_movement(runtime, actor);
        }
        return avsp_round1_step_class1f_inner8_animation(runtime, actor, 0);
    }
    if (action == 0x0au)
    {
        if (actor->animation_branch < 0)
        {
            actor->source_style85 = 1u;
            actor->substate = 0x0400u;
            actor->source_action = actor->substate;
            random = avsp_round1_source_rng(runtime);
            actor->source_motion_fields[3] = avsp_round1_class1f_inner8_program.
                field88_table[random & 15u];
            actor->source_action_group_cursor = 0u;
            if (!avsp_round1_class1f_inner8_wander(runtime, actor))
                return 0;
            actor->source_primary_animation_record =
                avsp_round1_class1f_inner8_program.
                    mismatch_zero_follow_record;
            return avsp_round1_bind_class1f_inner8_record(actor,
                actor->source_primary_animation_record);
        }
        return avsp_round1_step_class1f_inner8_animation(runtime, actor, 0);
    }
    if (action == 0x04u)
    {
        if (actor->animation_branch < 0)
        {
            target_side = runtime->player_action.x < actor->x ? 0u : 1u;
            if (target_side != actor->facing)
            {
                actor->facing ^= 1u;
                actor->substate = 0x0600u;
                actor->source_action = actor->substate;
                return avsp_round1_bind_class1f_inner8_record(actor,
                    avsp_round1_class1f_inner8_program.turn_record);
            }
            if (actor->source_motion_fields[3] != 0)
                --actor->source_motion_fields[3];
            if (actor->source_motion_fields[3] != 0)
                return avsp_round1_bind_class1f_inner8_record(actor,
                    actor->source_primary_animation_record);
            random = avsp_round1_source_rng(runtime);
            if (((avsp_round1_class1f_inner8_program.action4_choice_bits >>
                    (random & 15u)) & 1u) != 0u)
            {
                actor->substate = 0x1000u;
                actor->source_action = actor->substate;
                actor->effect_timer = 240u;
                actor->source_action_timer = 4u;
                actor->source_action_group_cursor = 0u;
                return avsp_round1_class1f_inner8_bind_movement(runtime,
                                                                 actor);
            }
            actor->substate = 0u;
            actor->source_action = 0u;
            return 1;
        }
        return avsp_round1_step_class1f_inner8_animation(runtime, actor, 1);
    }
    if (action == 0x10u)
    {
        if (avsp_round1_class1f_inner8_player_near(runtime, actor,
                avsp_round1_class1f_inner8_program.attack_x_span,
                avsp_round1_class1f_inner8_program.attack_z_span))
        {
            actor->substate = 0x0e00u;
            actor->source_action = actor->substate;
            actor->source_motion_fields[0] = 0;
            return 1;
        }
        if (actor->effect_timer != 0u)
            --actor->effect_timer;
        if (actor->source_action_timer != 0u)
            --actor->source_action_timer;
        if (actor->source_action_timer == 0u)
        {
            actor->source_action_timer = 4u;
            actor->source_action_group_cursor = 0u;
            if (!avsp_round1_class1f_inner8_wander(runtime, actor))
                return 0;
        }
        return avsp_round1_step_class1f_inner8_animation(runtime, actor, 1);
    }
    if (action == 0x0eu)
    {
        if (actor->source_motion_fields[0] == 0)
        {
            (void)avsp_round1_source_rng(runtime);
            actor->source_motion_fields[1] =
                avsp_round1_class1f_inner8_program.motion_selector;
            actor->source_motion_fields[0] = 2;
            actor->substate = 0x0e02u;
            actor->source_action = actor->substate;
            actor->source_style85 = 0u;
            return avsp_round1_bind_class1f_inner8_record(actor,
                avsp_round1_class1f_inner8_program.motion_record);
        }
        if (actor->source_motion_fields[0] == 2)
        {
            if (actor->animation_branch < 0)
            {
                actor->source_x_velocity =
                    avsp_round1_class1f_inner8_program.
                        x_velocity_by_facing[actor->facing ? 1u : 0u];
                actor->source_x_acceleration =
                    avsp_round1_class1f_inner8_program.x_acceleration;
                actor->source_y_velocity =
                    avsp_round1_class1f_inner8_program.y_velocity;
                actor->source_y_acceleration =
                    avsp_round1_class1f_inner8_program.y_acceleration;
                actor->source_airborne = 1u;
                actor->source_motion_fields[0] = 4;
                return avsp_round1_bind_class1f_inner8_record(actor,
                    avsp_round1_class1f_inner8_program.airborne_record);
            }
            return avsp_round1_step_class1f_inner8_animation(runtime,
                                                              actor, 0);
        }
        if (actor->source_motion_fields[0] == 4)
        {
            actor->source_x_fp += actor->source_x_velocity;
            actor->source_x_velocity += actor->source_x_acceleration;
            actor->source_y_fp += actor->source_y_velocity;
            actor->source_y_velocity += actor->source_y_acceleration;
            actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
            actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
            if ((unsigned short)actor->z < (unsigned short)actor->y)
                return avsp_round1_step_class1f_inner8_animation(runtime,
                                                                  actor, 0);
            actor->y = actor->z;
            actor->source_y_fp = actor->source_z_fp;
            actor->source_airborne = 0u;
            actor->source_motion_fields[0] = 6;
            actor->source_projectile_enable = 1u;
            return avsp_round1_bind_class1f_inner8_record(actor,
                avsp_round1_class1f_inner8_program.parent_record);
        }
        if (actor->source_motion_fields[0] == 8)
        {
            if (actor->source_action_timer != 0u)
                --actor->source_action_timer;
            if (actor->source_action_timer == 0u)
            {
                actor->substate = 0u;
                actor->source_action = 0u;
            }
            return 1;
        }
        return 0;
    }
    return 0;
}

static int avsp_round1_type16_parent_record_index(unsigned long record)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_TYPE16_PARENT_PRESENTATION_COUNT;
         ++index)
        if (avsp_round1_type16_parent_records[index].animation_record == record)
            return (int)index;
    return -1;
}

static int avsp_round1_allocate_type16_projectile(
    AvspRound1Runtime *runtime, const AvspRound1ActorCore *parent,
    unsigned char event)
{
    AvspRound1ActorCore *projectile;
    short x_offset;
    unsigned short camera_delta;
    if (event < 1u || event > AVSP_ROUND1_TYPE16_MOTION_COUNT)
        return 0;
    ++runtime->type16_spawn_requests;
    camera_delta = (unsigned short)(parent->x - runtime->camera_x_position +
                                     avsp_round1_type16.camera_bias);
    if (camera_delta > avsp_round1_type16.camera_limit)
        return 1;
    projectile = avsp_round1_allocate_pool_actor(runtime, 1u);
    if (projectile == 0)
        return 1;
    x_offset = avsp_round1_type16.spawn_x_offset;
    if (parent->facing != 0u)
        x_offset = (short)-x_offset;
    projectile->actor_class = avsp_round1_type16.actor_class;
    projectile->variant = (unsigned char)(event - 1u);
    projectile->state = 0u;
    projectile->substate = 0u;
    projectile->facing = parent->facing;
    projectile->x = (short)(parent->x + x_offset);
    projectile->y = (short)(parent->y + avsp_round1_type16.spawn_y_offset);
    projectile->z = parent->z;
    projectile->dispatch_entry = avsp_round1_type16.dispatch;
    ++runtime->type16_allocations;
    return 1;
}

static int avsp_round1_step_class1f_type16_emitter(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *actor)
{
    int current;
    const AvspRound1AnimationStateSpec *record;
    unsigned char event;
    if (actor->state != 0x0208u || actor->substate != 0x0e02u ||
        actor->source_projectile_enable == 0u)
        return 0;
    current = avsp_round1_type16_parent_record_index(actor->animation_record);
    if (current < 0 || actor->animation_timer == 0u)
        return -1;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    record = &avsp_round1_type16_parent_records[current];
    event = record->branch > 0 && record->branch <= 3 ?
        (unsigned char)record->branch : 0u;
    if (event != 0u &&
        !avsp_round1_allocate_type16_projectile(runtime, actor, event))
        return -1;
    if (record->branch < 0)
    {
        actor->source_projectile_enable = 0u;
        actor->source_motion_fields[0] = 8;
        actor->source_action_timer =
            avsp_round1_class1f_inner8_program.terminal_delay;
        return 1;
    }
    ++current;
    if ((unsigned int)current >=
            AVSP_ROUND1_TYPE16_PARENT_PRESENTATION_COUNT)
        return -1;
    actor->animation_index = (unsigned char)current;
    avsp_round1_bind_animation_state(
        actor, &avsp_round1_type16_parent_records[current]);
    return 1;
}

static int avsp_round1_type16_overlap_player(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *projectile)
{
    AvspAttackBox attack;
    AvspBox hurt;
    AvspActor attacker;
    AvspActor defender;
    memset(&attack, 0, sizeof(attack));
    memset(&hurt, 0, sizeof(hurt));
    memset(&attacker, 0, sizeof(attacker));
    memset(&defender, 0, sizeof(defender));
    attack.box.x_center = avsp_round1_type16.attack_box.x_center;
    attack.box.y_center = avsp_round1_type16.attack_box.y_center;
    attack.box.x_half = avsp_round1_type16.attack_box.x_half;
    attack.box.y_half = avsp_round1_type16.attack_box.y_half;
    attack.box.z_center = avsp_round1_type16.attack_box.z_center;
    attack.box.z_half = avsp_round1_type16.attack_box.z_half;
    attack.hit_value = avsp_round1_type16.attack_box.hit_value;
    attack.knockback_mode = avsp_round1_type16.attack_box.knockback_mode;
    hurt.x_center = avsp_round1_type16.player_hurt_box.x_center;
    hurt.y_center = avsp_round1_type16.player_hurt_box.y_center;
    hurt.x_half = avsp_round1_type16.player_hurt_box.x_half;
    hurt.y_half = avsp_round1_type16.player_hurt_box.y_half;
    hurt.z_center = avsp_round1_type16.player_hurt_box.z_center;
    hurt.z_half = avsp_round1_type16.player_hurt_box.z_half;
    attacker.world_x = (unsigned short)projectile->x;
    attacker.world_y = (unsigned short)projectile->y;
    attacker.world_z = (unsigned short)projectile->z;
    attacker.facing = projectile->facing;
    defender.world_x = (unsigned short)runtime->player.x;
    defender.world_y = (unsigned short)runtime->player.y;
    defender.world_z = (unsigned short)runtime->player.z;
    defender.facing = runtime->player.facing;
    return avsp_collision_overlap_boxes(&attacker, &attack, &defender,
                                        &hurt, 0);
}

static int avsp_round1_step_type16_projectile(
    AvspRound1Runtime *runtime, AvspRound1Pool *pool,
    AvspRound1ActorCore *projectile)
{
    const AvspRound1Type16MotionSpec *motion;
    unsigned char next;
    if (projectile->state == 0u)
    {
        if (projectile->variant >= AVSP_ROUND1_TYPE16_MOTION_COUNT)
            return 0;
        motion = &avsp_round1_type16_motion[projectile->variant];
        projectile->state = 0x0200u;
        projectile->coordinate_mode = 1u;
        projectile->object_or = 0x8000u;
        projectile->health = 0;
        projectile->source_x_fp = (long)projectile->x * 65536L;
        projectile->source_y_fp = (long)projectile->y * 65536L;
        projectile->source_z_fp = (long)projectile->z * 65536L;
        if (projectile->facing != 0u)
        {
            projectile->source_x_velocity = motion->x_velocity;
            projectile->source_x_acceleration = motion->x_acceleration;
            projectile->source_y_velocity = motion->y_velocity;
            projectile->source_y_acceleration = motion->y_acceleration;
            projectile->source_z_velocity = motion->z_velocity;
        }
        else
        {
            projectile->source_x_velocity = -motion->x_velocity;
            projectile->source_x_acceleration = -motion->x_acceleration;
            projectile->source_y_velocity = -motion->y_velocity;
            projectile->source_y_acceleration = -motion->y_acceleration;
            projectile->source_z_velocity = -motion->z_velocity;
        }
        projectile->animation_index = 0u;
        avsp_round1_bind_animation_state(projectile,
                                         &avsp_round1_type16_records[0]);
        return 1;
    }
    if (projectile->state == 0x0600u)
    {
        if (!avsp_round1_release_pool_actor(pool, projectile))
            return 0;
        ++runtime->type16_releases;
        return 2;
    }
    if (projectile->state == 0x0200u)
    {
        unsigned short screen_x;
        unsigned short screen_y;
        if (projectile->health < 0)
        {
            projectile->state = 0x0600u;
            return 1;
        }
        screen_x = (unsigned short)(projectile->x -
            runtime->camera_x_position + 32);
        screen_y = (unsigned short)(projectile->y -
            runtime->camera_z_position + 16);
        if (screen_x > 0x01c0u || screen_y > 0x0120u)
        {
            projectile->state = 0x0600u;
            return 1;
        }
        projectile->source_x_fp += projectile->source_x_velocity;
        projectile->source_x_velocity += projectile->source_x_acceleration;
        projectile->source_y_fp += projectile->source_y_velocity;
        projectile->source_y_velocity += projectile->source_y_acceleration;
        projectile->source_z_fp += projectile->source_z_velocity;
        projectile->x = avsp_round1_fixed_high_word(projectile->source_x_fp);
        projectile->y = avsp_round1_fixed_high_word(projectile->source_y_fp);
        projectile->z = avsp_round1_fixed_high_word(projectile->source_z_fp);
        ++runtime->type16_movement_steps;
        if ((unsigned short)projectile->z >= (unsigned short)projectile->y)
        {
            projectile->y = projectile->z;
            projectile->source_y_fp = projectile->source_z_fp;
            projectile->coordinate_mode = 0u;
            projectile->state = 0x0400u;
            projectile->transition_timer = 2u;
            projectile->animation_index = 4u;
            avsp_round1_bind_animation_state(
                projectile, &avsp_round1_type16_records[4]);
            return 1;
        }
        if (projectile->animation_timer == 0u)
            return 0;
        --projectile->animation_timer;
        if (projectile->animation_timer == 0u)
        {
            next = (unsigned char)(projectile->animation_index + 1u);
            if (next < 4u)
            {
                projectile->animation_index = next;
                avsp_round1_bind_animation_state(
                    projectile, &avsp_round1_type16_records[next]);
            }
            else
                projectile->animation_timer =
                    avsp_round1_type16_records[3].timer;
        }
        if (projectile->attack_selector ==
                avsp_round1_type16.attack_selector &&
            runtime->first_encounter.pending_player_damage == 0u &&
            runtime->player.health > 0 &&
            avsp_round1_type16_overlap_player(runtime, projectile))
        {
            projectile->health = -1;
            runtime->first_encounter.pending_player_damage =
                (unsigned char)avsp_round1_type16.damage;
            ++runtime->type16_collision_writes;
            ++runtime->type16_damage_writes;
        }
        return 1;
    }
    if (projectile->state == 0x0400u)
    {
        if (projectile->animation_timer == 0u)
            return 0;
        --projectile->animation_timer;
        if (projectile->animation_timer != 0u)
            return 1;
        if (projectile->animation_branch < 0)
        {
            if (projectile->transition_timer != 0u)
                --projectile->transition_timer;
            if (projectile->transition_timer == 0u)
                projectile->state = 0x0600u;
            else
                projectile->animation_timer =
                    avsp_round1_type16_records[
                        projectile->animation_index].timer;
            return 1;
        }
        next = (unsigned char)(projectile->animation_index + 1u);
        if (next >= AVSP_ROUND1_TYPE16_PRESENTATION_COUNT)
            return 0;
        projectile->animation_index = next;
        avsp_round1_bind_animation_state(
            projectile, &avsp_round1_type16_records[next]);
        return 1;
    }
    return 0;
}

static int avsp_round1_step_class1f_source_action(
    AvspRound1Runtime *runtime, AvspRound1Pool *pool,
    AvspRound1ActorCore *actor)
{
    unsigned char action;
    int emitter_result = avsp_round1_step_class1f_type16_emitter(
        runtime, actor);
    if (emitter_result != 0)
        return emitter_result > 0 ? 1 : 0;
    if (actor->state == 0x0600u)
    {
        if (runtime->first_encounter.source_living_count == 0u)
            return 0;
        --runtime->first_encounter.source_living_count;
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->first_encounter.lifecycle_releases;
        ++runtime->class1f_action_releases;
        return 2;
    }
    if (actor->state == 0u)
    {
        (void)avsp_round1_source_rng(runtime);
        actor->coordinate_mode = 1u;
        actor->object_or = 0x8000u;
        actor->palette = (unsigned char)(0x10u + (runtime->rng_seed & 3u));
        actor->health = avsp_round1_class1f_current.start_health;
        if (!avsp_round1_seed_class1f_action_fields(runtime, actor,
                runtime->rng_seed, (unsigned char)actor->source_action, 1))
            return 0;
        actor->hurt_selector = actor->source_a5;
        actor->attack_selector = actor->source_a6;
        return 3;
    }
    if (actor->state == 0x0208u)
        return avsp_round1_step_class1f_inner8(runtime, actor);
    if (actor->state != 0x0200u)
        return 0;
    action = (unsigned char)(actor->substate >> 8);
    ++runtime->class1f_action_dispatches;
    if (action == 0x00u)
        return avsp_round1_step_class1f_action_zero(runtime, actor);
    if (action == 0x04u)
        return avsp_round1_step_class1f_action4(runtime, actor);
    if (action == 0x02u)
    {
        int bounds_result = avsp_round1_class1f_source_bounds(runtime, actor);
        if (bounds_result < 0)
            return 0;
        if (bounds_result == 0)
        {
            actor->state = avsp_round1_class1f_action_program.release_state;
            actor->substate = 0u;
            return 1;
        }
        if (bounds_result == 2)
            return 1;
        avsp_round1_class1f_derive_direction(actor);
        if (!avsp_round1_step_class1f_action_animation(runtime, actor, 1))
            return 0;
        actor->z = actor->y;
        return 1;
    }
    if (action == 0x06u || action == 0x08u || action == 0x0au)
    {
        if (actor->animation_branch < 0)
        {
            if (action == 0x06u)
                actor->source_style85 = 0u;
            else if (action == 0x08u)
                actor->source_style85 = 1u;
            return avsp_round1_set_class1f_action(actor, 0u, -1);
        }
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    }
    if (action == 0x0cu)
    {
        unsigned char phase = (unsigned char)actor->substate;
        if (phase == 0u)
        {
            actor->substate = 0x0c02u;
            actor->source_action = actor->substate;
            actor->source_style85 = 0u;
            return avsp_round1_bind_class1f_action_selector(actor,
                avsp_round1_class1f_action_program.fall_initial_selector);
        }
        actor->source_y_fp +=
            avsp_round1_class1f_action_program.fall_y_delta;
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        actor->z = actor->y;
        if (phase == 2u)
        {
            if (actor->animation_branch < 0)
            {
                actor->substate = 0x0c04u;
                actor->source_action = actor->substate;
                return avsp_round1_bind_class1f_action_selector(actor,
                    avsp_round1_class1f_action_program.fall_middle_selector);
            }
            return avsp_round1_step_class1f_action_animation(runtime,
                                                              actor, 0);
        }
        if (phase == 4u)
        {
            if (actor->animation_branch < 0)
                return avsp_round1_set_class1f_action(actor, 0u, -1);
            return avsp_round1_step_class1f_action_animation(runtime,
                                                              actor, 0);
        }
        return 0;
    }
    if (action == 0x0eu)
    {
        unsigned char phase = (unsigned char)actor->substate;
        if (phase == 0u)
        {
            unsigned short random = avsp_round1_source_rng(runtime);
            actor->substate = 0x0e02u;
            actor->source_action = actor->substate;
            actor->source_z_velocity =
                avsp_round1_class1f_action_program.jump_z_velocity[
                    (random & 0x000cu) >> 2];
            actor->source_y_velocity =
                avsp_round1_class1f_action_program.jump_y_velocity;
            actor->source_y_acceleration =
                avsp_round1_class1f_action_program.jump_y_acceleration;
            actor->source_y_fp +=
                (long)avsp_round1_class1f_action_program.jump_initial_y_add *
                65536L;
            actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
            ++runtime->class1f_action0e_rng_calls;
            return avsp_round1_bind_class1f_action_selector(
                actor,
                avsp_round1_class1f_action_program.jump_initial_selector);
        }
        if (phase == 2u)
        {
            actor->source_z_fp += actor->source_z_velocity;
            actor->source_y_fp += actor->source_y_velocity;
            actor->source_y_velocity += actor->source_y_acceleration;
            actor->z = avsp_round1_fixed_high_word(actor->source_z_fp);
            actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
            if ((unsigned short)actor->z < (unsigned short)actor->y)
                return avsp_round1_step_class1f_action_animation(
                    runtime, actor, 0);
            actor->y = actor->z;
            actor->source_y_fp = actor->source_z_fp;
            actor->coordinate_mode = 0u;
            actor->substate = 0x0e04u;
            actor->source_action = actor->substate;
            return avsp_round1_bind_class1f_action_selector(
                actor,
                avsp_round1_class1f_action_program.jump_landing_selector);
        }
        if (phase == 4u)
        {
            actor->source_style85 =
                avsp_round1_class1f_action_program.jump_terminal_style;
            return avsp_round1_set_class1f_action(actor, 0u, -1);
        }
        return 0;
    }
    if (action == 0x10u || action == 0x12u)
    {
        if (actor->source_action_timer == 0u)
            return 0;
        --actor->source_action_timer;
        if (actor->source_action_timer == 0u)
            return avsp_round1_set_class1f_action(actor, 0u, -1);
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    }
    if (action == 0x16u)
    {
        int inner8_result;
        int bounds_result;
        unsigned short random;
        unsigned char rng_consumed = 0u;
        bounds_result = avsp_round1_class1f_source_bounds(runtime, actor);
        if (bounds_result < 0)
            return 0;
        if (bounds_result == 0)
        {
            actor->state = avsp_round1_class1f_action_program.release_state;
            actor->substate = 0u;
            return 1;
        }
        if (bounds_result == 2)
            return 1;
        avsp_round1_class1f_derive_direction(actor);
        if (!avsp_round1_step_class1f_action_animation(runtime, actor, 1))
            return 0;
        actor->z = actor->y;
        if (actor->animation_branch < 0 && actor->animation_timer == 1u &&
            actor->source_b0 != 0u)
            --actor->source_b0;
        if (actor->source_b0 != 0u)
            return 1;
        inner8_result = avsp_round1_class1f_enter_inner8(
            runtime, actor, &random, &rng_consumed);
        if (inner8_result != 0)
            return inner8_result > 0 ? 1 : 0;
        if (rng_consumed != 0u)
        {
            unsigned char branch = (unsigned char)(random & 3u);
            if (branch == 1u)
            {
                actor->source_a6 = 0u;
                actor->source_a3 = 1u;
                actor->source_style85 = 1u;
                actor->source_a4 = 0u;
            }
            else if (branch != 0u)
            {
                actor->source_a4 = 0u;
                ++actor->source_a6;
            }
            return avsp_round1_set_class1f_action(actor, 0u, -1);
        }
        (void)avsp_round1_source_rng(runtime);
        random = runtime->rng_seed;
        actor->source_action_timer = avsp_round1_class1f_attack_timers[
            random & 0x000fu];
        if (actor->source_a6 == 2u)
        {
            actor->facing ^= 1u;
            return avsp_round1_set_class1f_action(actor, 0x1au,
                actor->source_style85 ? 35 : 34);
        }
        return avsp_round1_set_class1f_action(actor, 0x18u,
            actor->source_style85 ? 1 : 0);
    }
    if (action == 0x18u)
    {
        if (actor->source_action_timer == 0u)
            return 0;
        --actor->source_action_timer;
        if (actor->source_action_timer == 0u)
            return avsp_round1_set_class1f_action(actor, 0u, -1);
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    }
    if (action == 0x1au)
    {
        if (actor->animation_branch < 0)
            return avsp_round1_set_class1f_action(actor, 0x18u,
                actor->source_style85 ? 1 : 0);
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    }
    if (action == 0x1cu)
    {
        int bounds_result = avsp_round1_class1f_source_bounds(runtime, actor);
        if (bounds_result < 0)
            return 0;
        if (bounds_result == 0)
        {
            actor->state = avsp_round1_class1f_action_program.release_state;
            actor->substate = 0u;
            return 1;
        }
        if (bounds_result == 2)
            return 1;
        if (!avsp_round1_step_class1f_action_animation(runtime, actor, 1))
            return 0;
        actor->z = actor->y;
        if (actor->animation_branch < 0 && actor->animation_timer == 1u &&
            actor->source_bound_b2 <= (unsigned short)actor->x)
            return avsp_round1_set_class1f_action(actor, 0x1eu,
                actor->source_style85 ? 1 : 0);
        return 1;
    }
    if (action == 0x1eu)
        return avsp_round1_step_class1f_action_animation(runtime, actor, 0);
    return 0;
}

/* Retired bounded single-actor compatibility body.  Kept outside the build
   until the accepted presentation adapter is deleted with its old tests. */
#if 0
static int avsp_round1_step_first_encounter_actor(
    AvspRound1Runtime *runtime, AvspRound1Pool *pool,
    AvspRound1ActorCore *actor)
{
    AvspRound1FirstEncounterRuntime *encounter = &runtime->first_encounter;
    unsigned char hit_value = 0u;
    short damage = 0;
    short health_before;
    int overlap;
    if (!encounter->initialized)
    {
        actor->state = 0x0200u;
        actor->substate = 0x1600u;
        actor->source_action = 0x1600u;
        actor->health = avsp_round1_class1f_current.start_health;
        actor->facing = 1u;
        encounter->target_id = 1u;
        encounter->rng_seed = 0x7301u;
        encounter->actor_source_slot = actor->source_slot;
        encounter->initialized = 1u;
        encounter->encounter_state = AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE;
        if (!avsp_round1_class1f_bind_record(actor, 0x0012ddb0UL))
            return 0;
        avsp_round1_first_encounter_cache_presentation(encounter, actor);
        return 1;
    }
    encounter->player_contact = 0u;
    encounter->alien_contact = 0u;
    encounter->alien_damage = 0u;
    encounter->semantic_hit = 0u;
    encounter->semantic_ko = 0u;
    encounter->health_before = actor->health;
    encounter->health_after = actor->health;
    if (encounter->encounter_state == AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE &&
        runtime->player_action.attack_active && !encounter->attack_latched &&
        actor->state != 0x0600u)
    {
        overlap = avsp_round1_first_encounter_overlap(runtime, actor,
                                                       &hit_value);
        encounter->attack_latched = 1u;
        if (overlap && runtime->player_action.selector >= 1u &&
            runtime->player_action.selector <= AVSP_PW_ACTION_COUNT &&
            hit_value == (unsigned char)avsp_pw_action_defs[
                runtime->player_action.selector - 1u].box.hit_value)
        {
            damage = avsp_round1_first_encounter_damage(
                runtime->player_action.selector);
            if (damage <= 0)
                return 0;
            encounter->player_contact = 1u;
            encounter->alien_damage = (unsigned char)damage;
            encounter->health_before = actor->health;
            actor->health = (short)(actor->health - damage);
            encounter->health_after = actor->health;
            ++encounter->player_contacts;
            ++encounter->alien_damage_events;
            avsp_pw_report_contact(&runtime->player_action);
        }
    }
    if (!runtime->player_action.attack_active)
        encounter->attack_latched = 0u;
    health_before = encounter->health_before;
    if (damage > 0)
    {
        encounter->approach_elapsed = 0u;
        encounter->attack_elapsed = 0u;
        encounter->attack_timer = 0u;
        encounter->x_numerator = 0L;
        encounter->lane_numerator = 0L;
        if (actor->health <= 0)
        {
            encounter->target_ko_observed = 1u;
            encounter->semantic_ko = 1u;
            encounter->ko_timer = avsp_round1_class1f_current.ko_ticks;
            ++encounter->ko_events;
            if (!avsp_round1_first_encounter_begin_reaction(encounter, 1))
                return 0;
        }
        else
        {
            encounter->semantic_hit = 1u;
            encounter->hit_timer = avsp_round1_class1f_current.hit_ticks;
            ++encounter->hit_events;
            if (!avsp_round1_first_encounter_begin_reaction(encounter, 0))
                return 0;
        }
    }
    if (encounter->reaction.active &&
        !avsp_port_v2_hit_ko_step(&encounter->reaction))
        return 0;
    if (encounter->ko_timer != 0u)
    {
        --encounter->ko_timer;
        if (!avsp_round1_first_encounter_sync_reaction(actor, encounter))
            return 0;
    }
    else if (encounter->hit_timer != 0u)
    {
        --encounter->hit_timer;
        if (!avsp_round1_first_encounter_sync_reaction(actor, encounter))
            return 0;
        if (encounter->hit_timer == 0u)
        {
            actor->state = 0x0200u;
            actor->substate = 0x1a00u;
            actor->source_action = 0x1a00u;
            actor->facing = 0u;
            if (!avsp_round1_class1f_bind_record(actor, 0x0012d5e4UL))
                return 0;
        }
    }
    else if (damage == 0)
    {
        if (actor->source_action == 0x1600u)
        {
            actor->state = 0x0200u;
            actor->substate = 0x1600u;
            actor->facing = 1u;
            avsp_round1_class1f_fraction(&encounter->x_numerator, &actor->x,
                avsp_round1_class1f_current.approach_x_delta);
            avsp_round1_class1f_fraction(&encounter->lane_numerator, &actor->z,
                avsp_round1_class1f_current.approach_z_delta);
            actor->y = actor->z;
            encounter->presentation_index = (unsigned short)(
                encounter->approach_elapsed & 7u);
            if (!avsp_round1_class1f_bind_record(actor,
                    avsp_round1_class1f_approach_records[
                        encounter->presentation_index]))
                return 0;
            ++encounter->approach_elapsed;
            if (encounter->approach_elapsed >=
                    avsp_round1_class1f_current.approach_ticks)
            {
                encounter->approach_elapsed = 0u;
                encounter->x_numerator = 0L;
                encounter->lane_numerator = 0L;
                encounter->rng_seed =
                    avsp_round1_class1f_rng_step(encounter->rng_seed);
                ++encounter->rng_cursor;
                encounter->attack_timer =
                    (encounter->rng_seed & 0xffu) < 0x40u ? 30u :
                    avsp_round1_class1f_current.attack_ticks;
                encounter->attack_elapsed = 0u;
                actor->source_action = 0x1800u;
                actor->substate = 0x1800u;
                if (!avsp_round1_class1f_bind_record(actor,
                        avsp_round1_class1f_attack_records[0]))
                    return 0;
            }
        }
        else if (actor->source_action == 0x1800u)
        {
            ++encounter->attack_elapsed;
            encounter->presentation_index = (unsigned short)(
                encounter->attack_elapsed & 3u);
            if (!avsp_round1_class1f_bind_record(actor,
                    avsp_round1_class1f_attack_records[
                        encounter->presentation_index]))
                return 0;
            if ((encounter->attack_elapsed ==
                    avsp_round1_class1f_current.contact_tick_a ||
                 encounter->attack_elapsed ==
                    avsp_round1_class1f_current.contact_tick_b) &&
                avsp_round1_class1f_abs((short)(
                    runtime->player_action.x - actor->x)) <= 68 &&
                runtime->player_action.lane == actor->z &&
                runtime->player_action.state != AVSP_PW_STATE_KO)
            {
                encounter->alien_contact = 1u;
                encounter->pending_player_damage = (unsigned char)
                    avsp_round1_class1f_current.contact_damage;
                ++encounter->alien_contacts;
            }
            if (encounter->attack_elapsed >= encounter->attack_timer)
            {
                encounter->attack_elapsed = 0u;
                encounter->attack_timer = 0u;
                if (runtime->player_action.x < actor->x)
                {
                    actor->source_action = 0x1a00u;
                    actor->substate = 0x1a00u;
                    actor->facing = 0u;
                    if (!avsp_round1_class1f_bind_record(
                            actor, 0x0012d5e4UL))
                        return 0;
                }
                else if (runtime->player_action.lane > actor->z)
                {
                    actor->source_action = 0x0600u;
                    actor->substate = 0x0600u;
                    actor->facing = 0u;
                    if (!avsp_round1_class1f_bind_record(
                            actor, 0x0012d5e4UL))
                        return 0;
                }
                else
                {
                    actor->source_action = 0x1600u;
                    actor->substate = 0x1600u;
                    actor->facing = 1u;
                    if (!avsp_round1_class1f_bind_record(actor,
                            avsp_round1_class1f_approach_records[0]))
                        return 0;
                }
            }
        }
    }
    if (encounter->alien_damage != 0u)
    {
        encounter->health_before = health_before;
        encounter->health_after = actor->health;
    }
    ++encounter->scheduler_updates;
    if (encounter->encounter_state == AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE &&
        encounter->target_ko_observed &&
        encounter->ko_timer == 0u &&
        !encounter->reaction.active)
    {
        short final_health = actor->health;
        encounter->encounter_state = AVSP_ROUND1_FIRST_ENCOUNTER_CLEARED;
        encounter->route_unlocked = 1u;
        encounter->unlock_player_x = runtime->player_action.x;
        ++encounter->clear_events;
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++encounter->lifecycle_releases;
        avsp_round1_first_encounter_cache_presentation(encounter, 0);
        encounter->presentation.removed = 1u;
        encounter->presentation.health = final_health;
        return 2;
    }
    if (!avsp_round1_class1f_state_context_supported(
            actor->state, actor->substate))
        return 0;
    avsp_round1_first_encounter_cache_presentation(encounter, actor);
    return 1;
}
#endif

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

static AvspRound1ActorCore *avsp_round1_find_pool_source_actor(
    AvspRound1Runtime *runtime, unsigned int pool_index,
    unsigned short source_slot)
{
    AvspRound1Pool *pool;
    unsigned int actor_index;
    if (runtime == 0 || pool_index >= AVSP_ROUND1_POOL_COUNT)
        return 0;
    pool = &runtime->pools[pool_index];
    if (source_slot < pool->source_base ||
        ((unsigned int)(source_slot - pool->source_base) % pool->stride) != 0u)
        return 0;
    actor_index = (unsigned int)(source_slot - pool->source_base) /
        pool->stride;
    if (actor_index >= pool->capacity ||
        !pool->records[actor_index].active)
        return 0;
    return &pool->records[actor_index];
}

static void avsp_round1_apply_coffee_shop_obstacle(
    AvspRound1Runtime *runtime)
{
    const AvspRound1ObstacleSpec *obstacle =
        &avsp_round1_coffee_shop_obstacle;
    AvspRound1ActorCore *actor = avsp_round1_find_pool_source_actor(
        runtime, 2u, (unsigned short)obstacle->source_slot);
    long dx;
    long dz;
    unsigned short x_penetration;
    unsigned short z_penetration;
    short signed_penetration;
    if (actor == 0 || actor->actor_class != obstacle->actor_class ||
        actor->type != obstacle->type ||
        actor->state != avsp_round1_coffee_shop_obstacle_lifecycle.active_state)
        return;
    dx = (long)actor->x + obstacle->attack_box.x_center -
        runtime->player_action.x;
    dz = (long)actor->z + obstacle->attack_box.z_center -
        runtime->player_action.lane;
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

static void avsp_round1_reset_player_walk_animation(
    AvspRound1Runtime *runtime)
{
    runtime->player_walk_animation_index = 0u;
    runtime->player_walk_animation_active = 0u;
    runtime->player_walk_animation_timer = 0u;
}

static void avsp_round1_bind_player_walk_record(
    AvspRound1Runtime *runtime, unsigned char index)
{
    const AvspRound1AnimationStateSpec *record;
    if (index >= AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)
    {
        ++runtime->failure_count;
        return;
    }
    record = &avsp_round1_player_walk_records[index];
    runtime->player_walk_animation_index = index;
    runtime->player_walk_animation_active = 1u;
    runtime->player_walk_animation_timer = record->timer;
    avsp_round1_bind_animation_state(&runtime->player, record);
    runtime->player.hurt_selector =
        avsp_round1_player_locomotion.current_hurt_selector;
    runtime->player.attack_selector =
        avsp_round1_player_locomotion.current_attack_selector;
}

static void avsp_round1_advance_player_walk_animation(
    AvspRound1Runtime *runtime)
{
    unsigned char next;
    if (!runtime->player_walk_animation_active)
    {
        avsp_round1_bind_player_walk_record(runtime, 0u);
        return;
    }
    if (runtime->player_walk_animation_timer > 1u)
    {
        --runtime->player_walk_animation_timer;
        runtime->player.animation_timer =
            runtime->player_walk_animation_timer;
        return;
    }
    next = (unsigned char)(runtime->player_walk_animation_index + 1u);
    if (next >= AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)
        next = 0u;
    avsp_round1_bind_player_walk_record(runtime, next);
}

static long avsp_round1_player_fractional_position(
    short position, long numerator)
{
    const long denominator = 20L;
    const long remainder = numerator % denominator;
    return (long)position * 65536L +
        remainder * 65536L / denominator;
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
        avsp_round1_reset_player_walk_animation(runtime);
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
        avsp_round1_advance_player_walk_animation(runtime);
        return;
    }
    if (runtime->player_cleanup_pending)
    {
        runtime->player_cleanup_pending = 0u;
        runtime->player_locomotion_action = direction != 255u ?
            avsp_round1_player_locomotion.cleanup_action :
            avsp_round1_player_locomotion.walking_action;
        runtime->player_was_directional = (unsigned char)(direction != 255u);
        if (direction != 255u)
            avsp_round1_bind_player_walk_record(runtime, 0u);
        else
            avsp_round1_reset_player_walk_animation(runtime);
        return;
    }
    if (direction != 255u)
    {
        if (!runtime->player_was_directional)
        {
            runtime->player_locomotion_action =
                avsp_round1_player_locomotion.cleanup_action;
            avsp_round1_bind_player_walk_record(runtime, 0u);
        }
        else
        {
            runtime->player_locomotion_action =
                avsp_round1_player_locomotion.walking_action;
            avsp_round1_advance_player_walk_animation(runtime);
        }
        runtime->player_was_directional = 1u;
    }
    else if (runtime->player_was_directional)
    {
        runtime->player_was_directional = 0u;
        runtime->player_stop_ticks = avsp_round1_player_locomotion.stop_ticks;
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.stop_action;
        avsp_round1_advance_player_walk_animation(runtime);
        ++runtime->player_stop_entries;
    }
    else
    {
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.walking_action;
        avsp_round1_reset_player_walk_animation(runtime);
    }
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

static int avsp_round1_class1f_player_collision_contract_valid(void)
{
    const AvspRound1Class1fPlayerCollisionSpec *spec =
        &avsp_round1_class1f_player_collision;
    const AvspRound1CollisionBoxSpec *attack = &spec->attack_box;
    const AvspRound1CollisionBoxSpec *hurt = &spec->hurt_box;
    return spec->attacker_table_set == 0x130ac8UL &&
        spec->attack_record == 0x130b5cUL &&
        spec->defender_table_set == 0x11ae02UL &&
        spec->hurt_record == 0x11ae8eUL &&
        spec->defender_animation_record == 0x0015f278UL &&
        spec->health_writer == 0x01d5eeUL &&
        spec->source_frame == 2750u && spec->attack_selector == 1u &&
        spec->hurt_selector == 17u && spec->damage == 10u &&
        spec->hitstop == 10u &&
        attack->x_center == -37 && attack->y_center == 53 &&
        attack->x_half == 38u && attack->y_half == 8u &&
        attack->z_center == 0 && attack->z_half == 8u &&
        attack->knockback_mode == 0 && attack->hit_value == 10u &&
        attack->damage_selector == 0u &&
        hurt->x_center == 1 && hurt->y_center == 45 &&
        hurt->x_half == 20u && hurt->y_half == 46u &&
        hurt->z_center == 0 && hurt->z_half == 6u &&
        hurt->knockback_mode == 0 && hurt->hit_value == 0u &&
        hurt->damage_selector == 0u;
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
        avsp_round1_player_weapon.empty_timer_initial != 16u ||
        avsp_round1_player_weapon.resource_capacity != 64u ||
        avsp_round1_player_weapon.resource_debit != 40u ||
        avsp_round1_player_weapon.recharge_after_success != 12u ||
        avsp_round1_player_weapon.normal_recharge_reload != 3u ||
        avsp_round1_player_weapon.depleted_recharge_reload != 6u ||
        avsp_round1_player_weapon.
            empty_dispatch_uses_depleted_latch != 1u ||
        avsp_round1_player_weapon.
            empty_entry_preserves_current_presentation != 1u ||
        avsp_round1_player_weapon.parent_class != 0 ||
        avsp_round1_player_weapon.child_class != 4 ||
        avsp_round1_player_weapon.projectile_source_base != 0x8680u ||
        avsp_round1_player_weapon.projectile_stride != 0x0080u ||
        avsp_round1_player_weapon.player_owner != 0x8380u ||
        avsp_round1_player_weapon.parent_attack_table != 0x0002fc3cUL ||
        avsp_round1_player_weapon.child_attack_table != 0x00030cb6UL ||
        avsp_round1_player_weapon_return_frame.action != 2u ||
        avsp_round1_player_weapon_return_frame.substate != 2u ||
        avsp_round1_player_weapon_return_frame.animation_record !=
            0x0015f1f4UL ||
        avsp_round1_player_weapon_return_frame.assembly != 0x001626a4UL ||
        avsp_round1_weapon_parent_route_angles[0] != 17u ||
        avsp_round1_weapon_parent_route_angles[18] != 35u ||
        avsp_round1_weapon_parent_route_angles[30] != 47u ||
        avsp_round1_weapon_parent_presentations[7].animation_record !=
            0x0002fbb8UL ||
        avsp_round1_weapon_parent_presentations[7].branch != -32768 ||
        avsp_round1_weapon_target_distance_thresholds[15] != 352u ||
        avsp_round1_player_weapon_frames[1][1].animation_record !=
            0x0015e594UL ||
        avsp_round1_player_weapon_frames[1][1].assembly !=
            0x0016179aUL ||
        avsp_round1_weapon_parent_base_motion[28].x != -489 ||
        avsp_round1_weapon_parent_base_motion[28].y != -169 ||
        avsp_round1_weapon_projectile.initial_state != 0u ||
        avsp_round1_weapon_projectile.active_state != 2u ||
        avsp_round1_weapon_projectile.emitter_state != 4u ||
        avsp_round1_weapon_projectile.release_state != 6u ||
        avsp_round1_weapon_projectile.object_or != 0x8000u ||
        avsp_round1_weapon_projectile.parent_dispatch != 0x02f870UL ||
        avsp_round1_weapon_projectile.child_dispatch != 0x0306feUL ||
        avsp_round1_weapon_projectile.parent_attack_relative != 12 ||
        avsp_round1_weapon_projectile.child_attack_relative != 12 ||
        avsp_round1_weapon_projectile.attack_record_stride != 16u ||
        avsp_round1_weapon_projectile.child_count != 5u ||
        avsp_round1_weapon_projectile.child_cadence_initial != 1u ||
        avsp_round1_weapon_projectile.child_cadence_reload != 6u ||
        avsp_round1_parent_weapon_effect.dispatch_entry != 0x08f080UL ||
        avsp_round1_parent_weapon_effect.record_type != 24u ||
        avsp_round1_parent_weapon_effect.actor_class != 0x49 ||
        avsp_round1_parent_weapon_effect.variant != 0u ||
        avsp_round1_parent_weapon_effect.timer != 8u ||
        avsp_round1_parent_weapon_effect.phase_mask != 1u ||
        avsp_round1_parent_weapon_effect.phase_expected != 1u ||
        avsp_round1_weapon_parent_attack_boxes[1].damage_selector != 25u ||
        avsp_round1_weapon_parent_impact_variants[1] != 10u ||
        avsp_round1_weapon_child_attack_boxes[1].damage_selector != 14u ||
        avsp_round1_weapon_child_impact_variants[1] != 1u ||
        avsp_round1_weapon_projectile.parent_damage != 127u ||
        avsp_round1_weapon_projectile.child_damage != 31u ||
        avsp_round1_air_weapon_projectile.actor_class != 3 ||
        avsp_round1_air_weapon_projectile.initial_state != 0u ||
        avsp_round1_air_weapon_projectile.active_state != 2u ||
        avsp_round1_air_weapon_projectile.emitter_state != 4u ||
        avsp_round1_air_weapon_projectile.release_state != 6u ||
        avsp_round1_air_weapon_projectile.player_collision_selector != 9u ||
        avsp_round1_air_weapon_projectile.child_cadence_reload != 4u ||
        avsp_round1_air_weapon_projectile.direction_timer_reload != 2u ||
        avsp_round1_air_weapon_projectile.effect_record_type != 24u ||
        avsp_round1_air_weapon_projectile.effect_class != 0x49u ||
        avsp_round1_air_weapon_projectile.effect_variant != 1u ||
        avsp_round1_air_weapon_player_sequence.selector != 18u ||
        avsp_round1_air_weapon_player_sequence.record_count != 5u ||
        avsp_round1_air_weapon_selector_offsets[6].x != -14 ||
        avsp_round1_air_weapon_motion_low[15][63].x != -23 ||
        avsp_round1_air_weapon_motion_high[12][63].y != 3492 ||
        avsp_round1_weapon_child_sequences[0].record_count != 17u ||
        avsp_round1_weapon_child_sequences[1].record_count != 10u ||
        avsp_round1_weapon_child_sequences[2].record_count != 16u ||
        avsp_round1_player_weapon.empty_effect_variant != 0u ||
        avsp_round1_player_weapon.empty_effect_allocation_tick != 1u ||
        avsp_round1_player_weapon.empty_effect_preserve_position_residue != 1u ||
        avsp_round1_empty_effect_variant_offsets[0].x != 0 ||
        avsp_round1_empty_effect_variant_offsets[0].y != 84 ||
        avsp_round1_empty_effect_variant1_records[0].timer != 1u ||
        avsp_round1_empty_effect_variant1_records[9].timer != 4095u ||
        avsp_round1_empty_effect_variant1_records[9].branch != -32767 ||
        avsp_round1_player_special.entry_action != 0x0800u ||
        avsp_round1_player_special.startup_action != 0x0802u ||
        avsp_round1_player_special.active_action != 0x0804u ||
        avsp_round1_player_special.presentation_selector != 47u ||
        avsp_round1_player_special.contact_attack_selector != 11u ||
        avsp_round1_player_special.health_cost != 6u ||
        avsp_round1_player_special.class4b_record_type != 24u ||
        avsp_round1_player_special.class4b_class != 0x4b ||
        avsp_round1_player_special.class3d_record_type != 24u ||
        avsp_round1_player_special.class3d_class != 0x3d ||
        avsp_round1_player_special_records[4].attack_selector != 11u ||
        avsp_round1_player_special_records[16].branch != -32768 ||
        avsp_round1_class4b_records[15].branch != 15 ||
        avsp_round1_class4b_records[31].branch != -32753 ||
        avsp_round1_class3d_records[8].branch != -32768 ||
        avsp_round1_class3d_offsets[0].x != -61 ||
        avsp_round1_class3d_offsets[8].x != 61)
        return 0;
    for (index = 0u;
         index < AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT; ++index)
    {
        unsigned int selector_index;
        for (selector_index = 0u;
             selector_index < AVSP_ROUND1_PLAYER_WEAPON_SELECTOR_COUNT;
             ++selector_index)
        {
            const AvspRound1PlayerWeaponFrameSpec *frame =
                &avsp_round1_player_weapon_frames[selector_index][index];
            if ((index == 0u && frame->action != 0x0c00u) ||
                (index > 0u && index < 4u && frame->action != 0x0c02u) ||
                (index >= 4u && index < 19u &&
                 frame->action != 0x0c04u) ||
                (index == 19u && frame->action != 0u))
                return 0;
        }
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
    runtime->player.substate = frame->action;
    runtime->player.animation_record = frame->animation_record;
    runtime->player.assembly = frame->assembly;
    runtime->player.hurt_selector = 0u;
    runtime->player.attack_selector = 0u;
    runtime->player_locomotion_action = frame->action;
    ++runtime->player_weapon_presentation_bindings;
}

static long avsp_round1_replace_fixed_high_word(long value, short high)
{
    return (long)high * 65536L +
        (long)((unsigned long)value & 0x0000ffffUL);
}

static void avsp_round1_clear_weapon_projectile_slot(
    AvspRound1WeaponProjectileAllocation *projectile)
{
    unsigned long animation_record = projectile->animation_record;
    unsigned long assembly = projectile->assembly;
    unsigned short animation_timer = projectile->animation_timer;
    short animation_branch = projectile->animation_branch;
    unsigned short x_fraction = (unsigned short)projectile->x_fp;
    unsigned short y_fraction = (unsigned short)projectile->y_fp;
    memset(projectile, 0, sizeof(*projectile));
    projectile->animation_record = animation_record;
    projectile->assembly = assembly;
    projectile->animation_timer = animation_timer;
    projectile->animation_branch = animation_branch;
    projectile->x_fp = (long)x_fraction;
    projectile->y_fp = (long)y_fraction;
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
    avsp_round1_clear_weapon_projectile_slot(projectile);
    projectile->collision_identity =
        avsp_round1_next_collision_identity(runtime);
    projectile->collision_registration_pending = 1u;
    projectile->active = 1u;
    projectile->actor_class = avsp_round1_player_weapon.parent_class;
    projectile->variant = 0u;
    projectile->facing = runtime->player.facing;
    projectile->source_slot = (unsigned short)(
        avsp_round1_player_weapon.projectile_source_base +
        index * avsp_round1_player_weapon.projectile_stride);
    projectile->owner = avsp_round1_player_weapon.player_owner;
    projectile->x = runtime->player.x;
    projectile->y = runtime->player.y;
    projectile->z = runtime->player.z;
    projectile->attack_table =
        avsp_round1_player_weapon.parent_attack_table;
    projectile->state = 0u;
    projectile->damage_class_index = 0u;
    projectile->angle = runtime->player_weapon_target_angle;
    projectile->parent_presentation_selector = 0u;
    projectile->child_count = avsp_round1_weapon_projectile.child_count;
    projectile->child_cadence =
        avsp_round1_weapon_projectile.child_cadence_initial;
    projectile->x_fp = avsp_round1_replace_fixed_high_word(
        projectile->x_fp, runtime->player.x);
    projectile->y_fp = avsp_round1_replace_fixed_high_word(
        projectile->y_fp, runtime->player.y);
    projectile->z_fp = (long)runtime->player.z * 65536L;
    ++runtime->player_weapon_allocations;
    return 1;
}

static void avsp_round1_player_weapon_target(
    const AvspRound1Runtime *runtime, unsigned char *presentation_selector,
    unsigned char *angle)
{
    const AvspRound1Pool *pool = &runtime->pools[0];
    unsigned int index;
    unsigned int threshold_index;
    unsigned short nearest = 0xffffu;
    unsigned char found = 0u;
    unsigned char distance_selector = 15u;
    for (index = 0u; index < pool->capacity; ++index)
    {
        const AvspRound1ActorCore *actor = &pool->records[index];
        short lane_delta;
        short x_delta;
        unsigned short distance;
        if (!actor->active || ((actor->state >> 8) & 0xffu) >= 4u)
            continue;
        lane_delta = (short)(actor->z - runtime->player.z);
        if ((unsigned short)(lane_delta + 16) >= 32u)
            continue;
        x_delta = (short)(actor->x - runtime->player.x);
        if (x_delta < 0)
        {
            if (runtime->player.facing != 0u)
                continue;
            distance = (unsigned short)-x_delta;
        }
        else
        {
            if (runtime->player.facing == 0u)
                continue;
            distance = (unsigned short)x_delta;
        }
        if (nearest < distance)
            continue;
        nearest = distance;
        found = 1u;
    }
    if (found)
    {
        for (threshold_index = AVSP_ROUND1_WEAPON_TARGET_DISTANCE_COUNT;
             threshold_index > 0u; --threshold_index)
            if (nearest >= avsp_round1_weapon_target_distance_thresholds[
                    threshold_index - 1u])
            {
                distance_selector = (unsigned char)(threshold_index - 1u);
                break;
            }
    }
    *presentation_selector =
        avsp_round1_weapon_target_presentation_selectors[distance_selector];
    *angle = (unsigned char)(32u - distance_selector);
    if (runtime->player.facing == 0u)
        *angle = (unsigned char)((0u - *angle) & 0x3fu);
}

static unsigned short avsp_round1_air_weapon_target_low(
    const AvspRound1Runtime *runtime)
{
    const AvspRound1Pool *pool = &runtime->pools[0];
    unsigned int index;
    unsigned short best_distance = 0x00ffu;
    unsigned short best_slot = 0u;
    for (index = 0u; index < pool->capacity; ++index)
    {
        const AvspRound1ActorCore *actor = &pool->records[index];
        short lane_delta;
        short x_delta;
        unsigned short distance;
        if (!actor->active || ((actor->state >> 8) & 0xffu) >= 4u)
            continue;
        lane_delta = (short)(actor->z - runtime->player_action.lane);
        if ((unsigned short)(lane_delta + 16) >= 32u)
            continue;
        x_delta = (short)(actor->x - runtime->player_action.x);
        if (x_delta < 0)
        {
            if (runtime->player.facing != 0u)
                continue;
            distance = (unsigned short)-x_delta;
        }
        else
        {
            if (runtime->player.facing == 0u)
                continue;
            distance = (unsigned short)x_delta;
        }
        if (distance > best_distance)
            continue;
        best_distance = distance;
        best_slot = (unsigned short)actor->source_slot;
    }
    return best_slot;
}

static unsigned char avsp_round1_air_weapon_direction(
    unsigned short input_mask, unsigned char facing)
{
    unsigned char input = 0u;
    unsigned char direction = 31u;
    if ((input_mask & AVSP_PW_INPUT_RIGHT) != 0u)
        input |= 0x01u;
    if ((input_mask & AVSP_PW_INPUT_LEFT) != 0u)
        input |= 0x02u;
    if ((input_mask & AVSP_PW_INPUT_DOWN) != 0u)
        input |= 0x04u;
    if ((input_mask & AVSP_PW_INPUT_UP) != 0u)
        input |= 0x08u;
    if (input != 0u)
    {
        direction = 3u;
        if ((input & 0x08u) == 0u)
        {
            direction = 31u;
            if ((input & 0x04u) == 0u)
                direction = 16u;
        }
    }
    if (facing == 0u)
        direction = (unsigned char)((0u - direction) & 0x3fu);
    return direction;
}

static int avsp_round1_allocate_player_air_weapon_projectile(
    AvspRound1Runtime *runtime, unsigned short input_mask)
{
    unsigned int index;
    AvspRound1WeaponProjectileAllocation *projectile;
    if (runtime->player_weapon_projectile_free_count == 0u)
    {
        ++runtime->player_air_weapon_allocation_failures;
        return 0;
    }
    --runtime->player_weapon_projectile_free_count;
    index = runtime->player_weapon_projectile_free_stack[
        runtime->player_weapon_projectile_free_count];
    if (index >= AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY)
        return 0;
    projectile = &runtime->player_weapon_projectiles[index];
    avsp_round1_clear_weapon_projectile_slot(projectile);
    projectile->collision_identity =
        avsp_round1_next_collision_identity(runtime);
    projectile->collision_registration_pending = 1u;
    projectile->active = 1u;
    projectile->actor_class = avsp_round1_air_weapon_projectile.actor_class;
    projectile->variant = 0u;
    projectile->facing = runtime->player.facing;
    projectile->source_slot = (unsigned short)(
        avsp_round1_player_weapon.projectile_source_base +
        index * avsp_round1_player_weapon.projectile_stride);
    projectile->owner = avsp_round1_player_weapon.player_owner;
    projectile->owner_field_26 = avsp_round1_air_weapon_target_low(runtime);
    projectile->owner_offset_selector = (unsigned char)(
        (runtime->player_jump_animation_timer >> 8) & 0x7fu);
    projectile->parent_presentation_selector =
        runtime->player_jump_presentation_selector;
    projectile->x = runtime->player_action.x;
    projectile->y = (short)(runtime->player_action.lane +
                            runtime->player_action.height);
    projectile->z = runtime->player_action.lane;
    projectile->attack_table = avsp_round1_air_weapon_projectile.attack_table;
    projectile->state = avsp_round1_air_weapon_projectile.initial_state;
    projectile->substate = 0u;
    projectile->health = 0;
    projectile->active_collision = 1u;
    projectile->angle = avsp_round1_air_weapon_direction(input_mask,
                                                          projectile->facing);
    projectile->child_count = avsp_round1_air_weapon_projectile.child_count;
    projectile->child_cadence =
        avsp_round1_air_weapon_projectile.child_cadence_initial;
    projectile->x_fp = avsp_round1_replace_fixed_high_word(
        projectile->x_fp, projectile->x);
    projectile->y_fp = avsp_round1_replace_fixed_high_word(
        projectile->y_fp, projectile->y);
    projectile->z_fp = (long)projectile->z * 65536L;
    ++runtime->player_weapon_allocations;
    ++runtime->player_air_weapon_allocations;
    return 1;
}

static short avsp_round1_fixed_high_word(long value)
{
    if (value >= 0L)
        return (short)(value / 65536L);
    return (short)-(((-value) + 65535L) / 65536L);
}

static unsigned char avsp_round1_next_collision_identity(
    AvspRound1Runtime *runtime)
{
    do
    {
        runtime->collision_identity_counter = (unsigned char)(
            runtime->collision_identity_counter + 1u);
    }
    while (runtime->collision_identity_counter == 0u);
    return runtime->collision_identity_counter;
}

static unsigned char avsp_round1_collision_visibility(
    const AvspRound1Runtime *runtime, short x, short y)
{
    unsigned short x_relative = (unsigned short)(
        (unsigned short)x - (unsigned short)runtime->camera_x_position +
        0x0040u);
    unsigned short y_relative = (unsigned short)(
        (unsigned short)y - (unsigned short)runtime->camera_z_position +
        0x0020u);
    return (unsigned char)(x_relative <= 0x0200u &&
                           y_relative <= 0x0140u);
}

static void avsp_round1_refresh_collision_registration(
    AvspRound1Runtime *runtime)
{
    unsigned int index;
    AvspRound1Pool *defenders = &runtime->pools[0];
    for (index = 0u; index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY;
         ++index)
    {
        AvspRound1WeaponProjectileAllocation *projectile =
            &runtime->player_weapon_projectiles[index];
        projectile->collision_registered = (unsigned char)(
            projectile->active == 1u &&
            projectile->collision_registration_pending == 0u &&
            avsp_round1_collision_visibility(runtime, projectile->x,
                                               projectile->y));
    }
    for (index = 0u; index < defenders->capacity; ++index)
    {
        AvspRound1ActorCore *actor = &defenders->records[index];
        if (actor->actor_class != 0x1f)
            continue;
        actor->source_field01 = (unsigned char)(
            actor->active == 1u &&
            avsp_round1_collision_visibility(runtime, actor->x, actor->y));
    }
}

static int avsp_round1_player_hit_contract_valid(void)
{
    unsigned int index;
    if (avsp_round1_player_hit.outer_dispatch_entry != 0x01A96EUL ||
        avsp_round1_player_hit.entry_body != 0x01A982UL ||
        avsp_round1_player_hit.active_body != 0x01AAD0UL ||
        avsp_round1_player_hit.phase0_body != 0x01AB2CUL ||
        avsp_round1_player_hit.phase2_body != 0x01AB52UL ||
        avsp_round1_player_hit.phase4_body != 0x01ABB8UL ||
        avsp_round1_player_hit.control_outer_state != 0x0200u ||
        avsp_round1_player_hit.hit_outer_state != 0x0202u ||
        avsp_round1_player_hit.entry_substate != 0x0000u ||
        avsp_round1_player_hit.shake_substate != 0x0200u ||
        avsp_round1_player_hit.motion_substate != 0x0202u ||
        avsp_round1_player_hit.return_substate != 0x0204u ||
        avsp_round1_player_hit.shake_count != 10u ||
        avsp_round1_player_hit.motion_index != 2u ||
        avsp_round1_player_hit.invulnerability != 1u ||
        avsp_round1_player_hit.return_facing != 0u ||
        avsp_round1_player_hit.audio_command != 0x003Bu ||
        avsp_round1_player_hit.x_velocity != 0x0001C000L ||
        avsp_round1_player_hit.x_acceleration != -0x00002000L ||
        avsp_round1_player_hit.carried_record.animation_record !=
            0x0015F278UL ||
        avsp_round1_player_hit.carried_record.assembly != 0x00160AF2UL ||
        avsp_round1_player_hit.carried_record.timer != 1u ||
        avsp_round1_player_hit.carried_record.hurt_selector != 0u ||
        avsp_round1_player_hit.hit_record.animation_record != 0x0015EEE8UL ||
        avsp_round1_player_hit.hit_record.assembly != 0x00160EDEUL ||
        avsp_round1_player_hit.hit_record.timer != 8u ||
        avsp_round1_player_hit.hit_record.branch != (short)-32768 ||
        avsp_round1_player_hit.hit_record.hurt_selector != 0u ||
        avsp_round1_player_hit.hit_record.attack_selector != 0u ||
        avsp_round1_player_hit.return_record.animation_record !=
            0x0015F1F4UL ||
        avsp_round1_player_hit.return_record.assembly != 0x001626A4UL ||
        avsp_round1_player_hit.return_record.timer != 0x0FFFu ||
        avsp_round1_player_hit.return_record.branch != (short)-32768)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_PLAYER_HIT_SHAKE_COUNT; ++index)
        if (avsp_round1_player_hit.shake_table[index] !=
                (short)((index & 1u) != 0u ? -2 : 2))
            return 0;
    return 1;
}

static int avsp_round1_player_hit_runtime_valid(
    const AvspRound1Runtime *runtime)
{
    if (!runtime->player_hit_active)
        return runtime->player_hit_phase == 0u &&
            runtime->player_hit_invulnerability <=
                avsp_round1_player_hit.invulnerability &&
            (!runtime->player_hit_invulnerability ||
             (runtime->player.state ==
                  avsp_round1_player_hit.control_outer_state &&
              runtime->player_action.state == AVSP_PW_STATE_CONTROL &&
              runtime->player_cleanup_pending));
    if (runtime->player_hit_phase < AVSP_ROUND1_PLAYER_HIT_ENTRY ||
        runtime->player_hit_phase > AVSP_ROUND1_PLAYER_HIT_SETTLE)
        return 0;
    if (runtime->player_hit_phase == AVSP_ROUND1_PLAYER_HIT_SETTLE)
        return runtime->player.state ==
                avsp_round1_player_hit.control_outer_state &&
            runtime->player_action.state == AVSP_PW_STATE_CONTROL &&
            runtime->player_hit_invulnerability ==
                avsp_round1_player_hit.invulnerability;
    return runtime->player.state == avsp_round1_player_hit.hit_outer_state &&
        runtime->player_action.state == AVSP_PW_STATE_HIT &&
        runtime->player_hit_invulnerability == 0u;
}

static void avsp_round1_bind_player_hit_record(
    AvspRound1Runtime *runtime, const AvspRound1AnimationStateSpec *record)
{
    avsp_round1_bind_animation_state(&runtime->player, record);
    runtime->player_hit_animation_timer = record->timer;
    runtime->player_hit_animation_branch = record->branch;
    runtime->player_action.animation_record = record->animation_record;
    runtime->player_action.assembly = record->assembly;
}

static int avsp_round1_begin_player_hit(AvspRound1Runtime *runtime,
                                        const AvspRound1ActorCore *attacker)
{
    if (!avsp_round1_player_hit_contract_valid() || runtime == 0 ||
        attacker == 0 || runtime->player_action.health < 0)
        return 0;
    runtime->player_hit_active = 1u;
    runtime->player_hit_phase = AVSP_ROUND1_PLAYER_HIT_ENTRY;
    runtime->player_hit_shake_remaining = 0u;
    runtime->player_hit_shake_index = 0u;
    runtime->player_hit_reaction_side = (unsigned char)(
        attacker->x < runtime->player_action.x);
    runtime->player_hit_invulnerability = 0u;
    runtime->player_hit_audio_latched = 0u;
    runtime->player_hit_x_fp = (long)runtime->player_action.x * 65536L;
    runtime->player_hit_x_velocity = 0L;
    runtime->player_hit_x_acceleration = 0L;
    runtime->player.source_x_fp = runtime->player_hit_x_fp;
    runtime->player.source_y_fp =
        (long)runtime->player_action.lane * 65536L;
    runtime->player_action.state = AVSP_PW_STATE_HIT;
    runtime->player_action.phase = AVSP_PW_PHASE_RECOVERY;
    runtime->player_action.source_action = 0u;
    runtime->player_action.source_substate = 0u;
    runtime->player_action.selector = 0u;
    runtime->player_action.attack_active = 0u;
    runtime->player_action.hit_timer = 0u;
    runtime->player_action.combo_next = 1u;
    runtime->player_action.combo_idle_frames = 0u;
    runtime->player_action.completed_close_step = 0u;
    runtime->player_action.combo_followup_counter = 0u;
    runtime->player_action.action_local_equipment_flag = 0u;
    runtime->player_action.height = 0;
    runtime->player.state = avsp_round1_player_hit.hit_outer_state;
    runtime->player.substate = avsp_round1_player_hit.entry_substate;
    runtime->player.source_action = 0u;
    runtime->player.hurt_selector = 0u;
    runtime->player.attack_selector = 0u;
    avsp_round1_bind_player_hit_record(
        runtime, &avsp_round1_player_hit.carried_record);
    runtime->player_stop_ticks = 0u;
    runtime->player_was_directional = 0u;
    runtime->player_cleanup_pending = 0u;
    if (runtime->player_jump_active)
        avsp_round1_interrupt_player_jump(runtime);
    if (runtime->player_weapon_active)
    {
        runtime->player_weapon_active = 0u;
        runtime->player_weapon_cleanup_pending = 0u;
        runtime->player_weapon_recovery_pending = 0u;
        ++runtime->player_weapon_interruptions;
    }
    runtime->player_special_attack_active = 0u;
    runtime->player_special_phase = 0u;
    ++runtime->player_hit_entries;
    return 1;
}

static int avsp_round1_step_class1f_player_collision(
    AvspRound1Runtime *runtime)
{
    unsigned int index;
    AvspRound1Pool *attackers = &runtime->pools[0];
    if (runtime->first_encounter.pending_player_damage != 0u ||
        runtime->player_hit_active || runtime->player_hit_invulnerability ||
        runtime->player.health <= 0 ||
        runtime->player_action.state == AVSP_PW_STATE_KO)
        return 1;
    for (index = 0u; index < attackers->capacity; ++index)
    {
        AvspRound1ActorCore *actor = &attackers->records[index];
        const AvspRound1Class1fActionRecordSpec *record;
        AvspAttackBox attack;
        AvspBox hurt;
        AvspActor attacker;
        AvspActor defender;
        unsigned char hurt_selector;
        unsigned char hit_value = 0u;
        if (actor->active != 1u || actor->actor_class != 0x1f ||
            actor->state != 0x0200u || actor->source_field01 != 1u ||
            actor->source_hitstop != 0u || actor->health < 0 ||
            avsp_round1_class1f_reaction_active(actor))
            continue;
        record = avsp_round1_find_class1f_action_record(
            actor->animation_record);
        if (record == 0)
            continue;
        if (record->attack_selector == 0u)
        {
            actor->source_player_collision_latched = 0u;
            continue;
        }
        if (actor->source_player_collision_latched != 0u)
            continue;
        hurt_selector = runtime->player_locomotion_action ==
                avsp_round1_player_locomotion.walking_action ||
                runtime->player_locomotion_action ==
                avsp_round1_player_locomotion.stop_action ||
                runtime->player.animation_record ==
                avsp_round1_class1f_player_collision.
                    defender_animation_record ?
            avsp_round1_class1f_player_collision.hurt_selector :
            runtime->player.hurt_selector;
        if (hurt_selector == 0u)
            continue;
        if (!avsp_collision_attack_box(
                avsp_round1_class1f_player_collision.attacker_table_set,
                record->attack_selector, &attack) ||
            !avsp_collision_hurt_box(
                avsp_round1_class1f_player_collision.defender_table_set,
                hurt_selector, &hurt))
            return 0;
        memset(&attacker, 0, sizeof(attacker));
        memset(&defender, 0, sizeof(defender));
        attacker.world_x = (unsigned short)actor->x;
        attacker.world_y = (unsigned short)actor->y;
        attacker.world_z = (unsigned short)actor->z;
        attacker.facing = actor->facing;
        defender.world_x = (unsigned short)runtime->player.x;
        defender.world_y = (unsigned short)runtime->player.y;
        defender.world_z = (unsigned short)runtime->player.z;
        defender.facing = runtime->player.facing;
        if (!avsp_collision_overlap_boxes(&attacker, &attack, &defender,
                                          &hurt, &hit_value))
            continue;
        if (record->attack_selector ==
                avsp_round1_class1f_player_collision.attack_selector &&
            hurt_selector ==
                avsp_round1_class1f_player_collision.hurt_selector &&
            (hit_value != avsp_round1_class1f_player_collision.damage ||
             hit_value != avsp_round1_class1f_player_collision.hitstop))
            return 0;
        actor->source_hitstop = hit_value;
        actor->source_player_collision_latched = 1u;
        runtime->player_action.health = (short)(
            runtime->player_action.health - (short)hit_value);
        runtime->player.health = runtime->player_action.health;
        runtime->first_encounter.pending_player_damage = hit_value;
        runtime->first_encounter.pending_player_damage_health_applied = 1u;
        runtime->first_encounter.alien_contact = 1u;
        ++runtime->first_encounter.alien_contacts;
        ++runtime->class1f_player_collision_writes;
        ++runtime->class1f_player_damage_writes;
        if (runtime->player_action.health >= 0 &&
            !avsp_round1_begin_player_hit(runtime, actor))
            return 0;
        return 1;
    }
    return 1;
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
    if (selector == avsp_round1_air_weapon_player_sequence.selector)
        return &avsp_round1_air_weapon_player_sequence;
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
    if (runtime->player_jump_phase == 0x0402u ||
        runtime->player_jump_phase == 0x0406u)
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
    unsigned char hurt_selector = actor->hurt_selector;
    unsigned char attack_selector = actor->attack_selector;
    if (sequence == 0 || sequence->record_count == 0u)
        return 0;
    actor->animation_index = 0u;
    avsp_round1_bind_animation_state(actor, &sequence->records[0]);
    actor->hurt_selector = hurt_selector;
    actor->attack_selector = attack_selector;
    return 1;
}

static int avsp_round1_step_class1f_animation(AvspRound1ActorCore *actor,
                                              unsigned char selector)
{
    const AvspRound1AnimationSequenceSpec *sequence =
        avsp_round1_find_initial_class1f_sequence(selector);
    unsigned char next;
    unsigned char hurt_selector = actor->hurt_selector;
    unsigned char attack_selector = actor->attack_selector;
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
    actor->hurt_selector = hurt_selector;
    actor->attack_selector = attack_selector;
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
        if (!avsp_round1_seed_class1f_action_fields(runtime, actor,
                runtime->rng_seed, (unsigned char)spec->transition_timer_initial,
                0))
            return 0;
        actor->state = spec->state;
        actor->substate = spec->substate;
        actor->source_action = spec->substate;
        actor->source_flags = spec->source_flags;
        actor->coordinate_mode = spec->coordinate_mode;
        actor->palette = spec->palette;
        actor->object_or = spec->object_or;
        actor->transition_timer = spec->transition_timer_initial;
        actor->hurt_selector = spec->hurt_selector;
        actor->attack_selector = spec->attack_selector;
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
        if (actor->source_action_timer == 0u)
            return 0;
        --actor->source_action_timer;
        actor->transition_timer = actor->source_action_timer;
        if (actor->source_action_timer == 0u)
        {
            actor->substate = 0u;
            ++runtime->class1f_transition_completions;
            return 1;
        }
        return avsp_round1_step_class1f_animation(actor, selector);
    }
    transition = avsp_round1_find_class1f_transition(runtime,
                                                     actor->source_slot);
    if (transition == 0)
        return 0;
    if (phase == 0x1400u)
    {
        if (runtime->entry.source_global_8209 != 2u)
            return avsp_round1_step_class1f_animation(actor, 1u);
        if (actor->source_action_timer == 0u)
            return 0;
        --actor->source_action_timer;
        actor->transition_timer = actor->source_action_timer;
        if (actor->source_action_timer != 0u)
            return avsp_round1_step_class1f_animation(actor, 1u);
        transition->active = 1u;
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
        actor->source_x_fp = transition->x_fp;
        actor->source_y_fp = transition->y_fp;
        if ((unsigned short)actor->z < (unsigned short)actor->y)
            return avsp_round1_step_class1f_animation(actor, 76u);
        actor->y = actor->z;
        transition->y_fp = (long)actor->z * 65536L;
        actor->source_y_fp = transition->y_fp;
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
    int sequence_index;
    if (actor->state == 0u)
    {
        actor->state = 0x0200u;
        actor->source_action = 0u;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_class09_sequences[0][0]);
        ++runtime->class09_initializations;
        return 1;
    }
    sequence_index = avsp_round1_find_class09_sequence(
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
    unsigned int presentation_count;
    const AvspRound1AnimationStateSpec *presentation_records;
    if (actor->variant != 1u && actor->variant != 4u &&
        actor->variant != 10u)
        return 0;
    if (actor->state == 0u)
    {
        unsigned char random;
        unsigned char table_offset;
        unsigned char jitter_index;
        const AvspRound1VecS16 *jitter;
        if (actor->variant == 4u)
        {
            const AvspRound1Class4eRngSpec *rng_spec = 0;
            unsigned int rng_index;
            for (rng_index = 0u;
                 rng_index < AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT;
                 ++rng_index)
                if ((unsigned short)avsp_round1_class4e_rng[
                        rng_index].source_slot ==
                        (unsigned short)actor->source_slot)
                {
                    rng_spec = &avsp_round1_class4e_rng[rng_index];
                    break;
                }
            if (rng_spec == 0 || runtime->rng_seed != rng_spec->seed_before)
                return 0;
            random = avsp_round1_source_rng(runtime);
            if (runtime->rng_seed != rng_spec->seed_after)
                return 0;
            table_offset = rng_spec->table_index;
            (void)random;
        }
        else
        {
            random = avsp_round1_source_rng(runtime);
            table_offset = (unsigned char)(random & 0x1cu);
        }
        jitter_index = (unsigned char)(table_offset >> 2);
        jitter = &avsp_round1_class4e_jitter[jitter_index];
        actor->x = (short)(actor->x + jitter->x);
        actor->y = (short)(actor->y + jitter->y);
        actor->state = 0x0200u;
        actor->coordinate_mode = 2u;
        actor->object_or = 0x8000u;
        actor->animation_index = 0u;
        presentation_records = actor->variant == 1u ?
            avsp_round1_class4e_variant1_records :
            actor->variant == 10u ?
                avsp_round1_class4e_variant10_records :
                avsp_round1_class4e_records;
        avsp_round1_bind_animation_state(actor, &presentation_records[0]);
        ++runtime->class4e_initializations;
        ++runtime->class4e_rng_calls;
        if (actor->variant == 1u)
            ++runtime->class4e_variant1_initializations;
        else if (actor->variant == 10u)
            ++runtime->class4e_variant10_initializations;
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
            presentation_count = actor->variant == 1u ?
                AVSP_ROUND1_CLASS4E_VARIANT1_PRESENTATION_COUNT :
                actor->variant == 10u ?
                    AVSP_ROUND1_CLASS4E_VARIANT10_PRESENTATION_COUNT :
                    AVSP_ROUND1_CLASS4E_PRESENTATION_COUNT;
            presentation_records = actor->variant == 1u ?
                avsp_round1_class4e_variant1_records :
                actor->variant == 10u ?
                    avsp_round1_class4e_variant10_records :
                    avsp_round1_class4e_records;
            if (actor->animation_index + 1u >= presentation_count)
                return 0;
            ++actor->animation_index;
            avsp_round1_bind_animation_state(actor,
                &presentation_records[actor->animation_index]);
        }
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        unsigned char variant = actor->variant;
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class4e_releases;
        if (variant == 1u)
            ++runtime->class4e_variant1_releases;
        else if (variant == 10u)
            ++runtime->class4e_variant10_releases;
        return 1;
    }
    return 0;
}

static unsigned int avsp_round1_class43_record_index(
    unsigned long animation_record)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS43_PRESENTATION_COUNT; ++index)
        if (avsp_round1_class43_records[index].animation_record ==
            animation_record)
            return index;
    return AVSP_ROUND1_CLASS43_PRESENTATION_COUNT;
}

static int avsp_round1_bind_class43_channel(AvspRound1ActorCore *actor,
                                            unsigned char selector,
                                            int alternate)
{
    unsigned int index;
    const AvspRound1AnimationStateSpec *record;
    if (selector >= AVSP_ROUND1_CLASS43_SEQUENCE_COUNT)
        return 0;
    index = avsp_round1_class43_sequence_offsets[selector];
    if (index >= AVSP_ROUND1_CLASS43_PRESENTATION_COUNT)
        return 0;
    record = &avsp_round1_class43_records[index];
    if (alternate)
    {
        actor->source_a4 = selector;
        actor->source_alternate_animation_record = record->animation_record;
        actor->source_alternate_assembly = record->assembly;
        actor->source_alternate_animation_timer = record->timer;
        actor->source_alternate_animation_branch = record->branch;
    }
    else
    {
        actor->source_a3 = selector;
        actor->source_primary_animation_record = record->animation_record;
        actor->source_primary_assembly = record->assembly;
        actor->source_primary_animation_timer = record->timer;
        actor->source_primary_animation_branch = record->branch;
    }
    return 1;
}

static int avsp_round1_advance_class43_channel(
    AvspRound1ActorCore *actor, int alternate)
{
    unsigned short *timer = alternate ?
        &actor->source_alternate_animation_timer :
        &actor->source_primary_animation_timer;
    short *branch = alternate ?
        &actor->source_alternate_animation_branch :
        &actor->source_primary_animation_branch;
    unsigned long current = alternate ?
        actor->source_alternate_animation_record :
        actor->source_primary_animation_record;
    unsigned char selector = alternate ? actor->source_a4 : actor->source_a3;
    unsigned int index;
    const AvspRound1AnimationStateSpec *record;
    if (*timer == 0u)
        return 0;
    --*timer;
    if (*timer != 0u)
        return 1;
    if (*branch < 0)
        return avsp_round1_bind_class43_channel(actor, selector, alternate);
    index = avsp_round1_class43_record_index(current);
    if (index + 1u >= AVSP_ROUND1_CLASS43_PRESENTATION_COUNT)
        return 0;
    record = &avsp_round1_class43_records[index + 1u];
    if (alternate)
    {
        actor->source_alternate_animation_record = record->animation_record;
        actor->source_alternate_assembly = record->assembly;
        actor->source_alternate_animation_timer = record->timer;
        actor->source_alternate_animation_branch = record->branch;
    }
    else
    {
        actor->source_primary_animation_record = record->animation_record;
        actor->source_primary_assembly = record->assembly;
        actor->source_primary_animation_timer = record->timer;
        actor->source_primary_animation_branch = record->branch;
    }
    return 1;
}

static int avsp_round1_step_class43(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor,
                                    unsigned int slot_index)
{
    unsigned short phase = actor->state & 0xff00u;
    unsigned char landed = (unsigned char)(actor->state & 0x00ffu);
    if (phase == 0u)
    {
        const AvspRound1Class45MotionSpec *motion;
        unsigned char random;
        unsigned char selector;
        unsigned int motion_index;
        actor->state = 0x0200u;
        actor->object_or = 0x8000u;
        random = avsp_round1_source_rng(runtime);
        selector = avsp_round1_class43_animation_selectors[
            random & (actor->variant == 0u ? 0x1fu : 0x07u)];
        if (!avsp_round1_bind_class43_channel(actor, selector, 1))
            return 0;
        random = avsp_round1_source_rng(runtime);
        selector = avsp_round1_class43_animation_selectors[
            random & (actor->variant == 0u ? 0x1fu : 0x07u)];
        if (!avsp_round1_bind_class43_channel(actor, selector, 0))
            return 0;
        random = avsp_round1_source_rng(runtime);
        actor->source_primary_x_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_primary_y_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_alternate_x_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_alternate_y_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        motion_index = (unsigned int)((random & 0x70u) >> 4);
        motion = &avsp_round1_class43_motion[motion_index];
        actor->source_motion_fields[0] = motion->primary_x_velocity;
        actor->source_motion_fields[1] = motion->alternate_x_velocity;
        actor->source_motion_fields[2] = motion->primary_y_velocity;
        actor->source_motion_fields[3] = motion->alternate_y_velocity;
        actor->source_motion_fields[4] = motion->primary_y_acceleration;
        actor->source_motion_fields[5] = motion->alternate_y_acceleration;
        if (actor->source_facing_selector == 0u)
        {
            actor->source_motion_fields[0] =
                (short)-actor->source_motion_fields[0];
            actor->source_motion_fields[1] =
                (short)-actor->source_motion_fields[1];
        }
        runtime->class43_rng_calls +=
            avsp_round1_class43.rng_calls_per_actor;
        ++runtime->class43_initializations;
        if (((unsigned long)runtime->frame +
             (pool->capacity - 1u - slot_index)) % 2u != 0u)
        {
            actor->source_x_fp = actor->source_alternate_x_fp;
            actor->source_y_fp = actor->source_alternate_y_fp;
            actor->animation_record =
                actor->source_alternate_animation_record;
            actor->assembly = actor->source_alternate_assembly;
            actor->animation_timer =
                actor->source_alternate_animation_timer;
            actor->animation_branch =
                actor->source_alternate_animation_branch;
        }
        else
        {
            actor->source_x_fp = actor->source_primary_x_fp;
            actor->source_y_fp = actor->source_primary_y_fp;
            actor->animation_record = actor->source_primary_animation_record;
            actor->assembly = actor->source_primary_assembly;
            actor->animation_timer = actor->source_primary_animation_timer;
            actor->animation_branch = actor->source_primary_animation_branch;
        }
        actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        return 1;
    }
    if (phase == 0x0200u)
    {
        if ((landed & 1u) == 0u)
        {
            actor->source_primary_x_fp +=
                (long)actor->source_motion_fields[0] * 256L;
            actor->source_primary_y_fp +=
                (long)actor->source_motion_fields[2] * 256L;
            actor->source_motion_fields[2] = (short)(
                actor->source_motion_fields[2] +
                actor->source_motion_fields[4]);
        }
        if ((landed & 2u) == 0u)
        {
            actor->source_alternate_x_fp +=
                (long)actor->source_motion_fields[1] * 256L;
            actor->source_alternate_y_fp +=
                (long)actor->source_motion_fields[3] * 256L;
            actor->source_motion_fields[3] = (short)(
                actor->source_motion_fields[3] +
                actor->source_motion_fields[5]);
        }
        if (!avsp_round1_advance_class43_channel(actor, 0) ||
            !avsp_round1_advance_class43_channel(actor, 1))
            return 0;
        if ((unsigned short)avsp_round1_fixed_high_word(
                actor->source_primary_y_fp) < (unsigned short)actor->z)
            landed |= 1u;
        if ((unsigned short)avsp_round1_fixed_high_word(
                actor->source_alternate_y_fp) < (unsigned short)actor->z)
            landed |= 2u;
        actor->state = (unsigned short)(0x0200u | landed);
        if (landed == 3u)
        {
            actor->state = 0x0403u;
            ++runtime->class43_state_transitions;
        }
        if (((unsigned long)runtime->frame +
             (pool->capacity - 1u - slot_index)) % 2u != 0u)
        {
            actor->source_x_fp = actor->source_alternate_x_fp;
            actor->source_y_fp = actor->source_alternate_y_fp;
            actor->animation_record =
                actor->source_alternate_animation_record;
            actor->assembly = actor->source_alternate_assembly;
            actor->animation_timer =
                actor->source_alternate_animation_timer;
            actor->animation_branch =
                actor->source_alternate_animation_branch;
        }
        else
        {
            actor->source_x_fp = actor->source_primary_x_fp;
            actor->source_y_fp = actor->source_primary_y_fp;
            actor->animation_record = actor->source_primary_animation_record;
            actor->assembly = actor->source_primary_assembly;
            actor->animation_timer = actor->source_primary_animation_timer;
            actor->animation_branch = actor->source_primary_animation_branch;
        }
        actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        return 1;
    }
    if (phase == 0x0400u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class43_releases;
        return 1;
    }
    return 0;
}

static unsigned int avsp_round1_class45_record_index(unsigned char selector)
{
    if (selector <= 1u)
        return selector;
    if (selector >= 3u && selector <= 5u)
        return (unsigned int)selector - 1u;
    return AVSP_ROUND1_CLASS45_PRESENTATION_COUNT;
}

static int avsp_round1_bind_class45_channel(AvspRound1ActorCore *actor,
                                            unsigned char selector,
                                            int alternate)
{
    unsigned int index = avsp_round1_class45_record_index(selector);
    const AvspRound1AnimationStateSpec *record;
    if (index >= AVSP_ROUND1_CLASS45_PRESENTATION_COUNT)
        return 0;
    record = &avsp_round1_class45_records[index];
    if (alternate)
    {
        actor->source_alternate_animation_record = record->animation_record;
        actor->source_alternate_assembly = record->assembly;
        actor->source_alternate_animation_timer = record->timer;
        actor->source_alternate_animation_branch = record->branch;
    }
    else
    {
        actor->source_primary_animation_record = record->animation_record;
        actor->source_primary_assembly = record->assembly;
        actor->animation_timer = record->timer;
        actor->animation_branch = record->branch;
    }
    return 1;
}

static void avsp_round1_step_class45_animation(AvspRound1ActorCore *actor)
{
    if (actor->animation_timer != 0u)
    {
        --actor->animation_timer;
        if (actor->animation_timer == 0u && actor->animation_branch < 0)
            actor->animation_timer =
                avsp_round1_class45_records[0].timer;
    }
    if (actor->source_alternate_animation_timer != 0u)
    {
        --actor->source_alternate_animation_timer;
        if (actor->source_alternate_animation_timer == 0u &&
            actor->source_alternate_animation_branch < 0)
            actor->source_alternate_animation_timer =
                avsp_round1_class45_records[0].timer;
    }
}

static int avsp_round1_step_class45(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor,
                                    unsigned int slot_index)
{
    if (actor->state == 0u)
    {
        const AvspRound1Class45MotionSpec *motion;
        unsigned char random;
        unsigned char selector;
        unsigned int motion_index;
        actor->state = 0x0200u;
        actor->object_or = 0x8000u;
        random = avsp_round1_source_rng(runtime);
        selector = avsp_round1_class45_animation_selectors[random & 0x1fu];
        if (!avsp_round1_bind_class45_channel(actor, selector, 1))
            return 0;
        random = avsp_round1_source_rng(runtime);
        selector = avsp_round1_class45_animation_selectors[random & 0x1fu];
        if (!avsp_round1_bind_class45_channel(actor, selector, 0))
            return 0;
        random = avsp_round1_source_rng(runtime);
        actor->facing = (unsigned char)(random & 3u);
        actor->source_primary_x_fp +=
            (long)((short)((random & 0x3fu) - 0x20u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_primary_y_fp +=
            (long)((short)((random & 0x7fu) - 0x40u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_alternate_x_fp +=
            (long)((short)((random & 0x3fu) - 0x20u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_alternate_y_fp +=
            (long)((short)((random & 0x7fu) - 0x40u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_flags = (unsigned char)(random & 1u);
        motion_index = (unsigned int)((random & 0x70u) >> 4);
        motion = &avsp_round1_class45_motion[motion_index];
        actor->source_motion_fields[0] = motion->primary_x_velocity;
        actor->source_motion_fields[1] = motion->alternate_x_velocity;
        actor->source_motion_fields[2] = motion->primary_y_velocity;
        actor->source_motion_fields[3] = motion->alternate_y_velocity;
        actor->source_motion_fields[4] = motion->primary_y_acceleration;
        actor->source_motion_fields[5] = motion->alternate_y_acceleration;
        runtime->class45_rng_calls += 7u;
        ++runtime->class45_initializations;
    }
    if (actor->state == 0x0200u)
    {
        long primary_x_delta =
            (long)actor->source_motion_fields[0] * 256L;
        long alternate_x_delta =
            (long)actor->source_motion_fields[1] * 256L;
        if (actor->source_flags == 0u)
        {
            primary_x_delta = -primary_x_delta;
            alternate_x_delta = -alternate_x_delta;
        }
        actor->source_primary_x_fp += primary_x_delta;
        actor->source_alternate_x_fp += alternate_x_delta;
        actor->source_primary_y_fp +=
            (long)actor->source_motion_fields[2] * 256L;
        actor->source_alternate_y_fp +=
            (long)actor->source_motion_fields[3] * 256L;
        actor->source_motion_fields[2] = (short)(
            actor->source_motion_fields[2] +
            actor->source_motion_fields[4]);
        actor->source_motion_fields[3] = (short)(
            actor->source_motion_fields[3] +
            actor->source_motion_fields[5]);
        ++actor->effect_timer;
        avsp_round1_step_class45_animation(actor);
        if (((unsigned int)actor->effect_timer + slot_index) % 2u != 0u)
        {
            actor->source_x_fp = actor->source_alternate_x_fp;
            actor->source_y_fp = actor->source_alternate_y_fp;
            actor->animation_record =
                actor->source_alternate_animation_record;
            actor->assembly = actor->source_alternate_assembly;
        }
        else
        {
            actor->source_x_fp = actor->source_primary_x_fp;
            actor->source_y_fp = actor->source_primary_y_fp;
            actor->animation_record = actor->source_primary_animation_record;
            actor->assembly = actor->source_primary_assembly;
        }
        actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        if ((unsigned short)avsp_round1_fixed_high_word(
                actor->source_primary_y_fp) <= (unsigned short)actor->z &&
            (unsigned short)avsp_round1_fixed_high_word(
                actor->source_alternate_y_fp) <= (unsigned short)actor->z)
        {
            actor->state = 0x0400u;
            ++runtime->class45_state_transitions;
        }
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class45_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_bind_class47_channel(AvspRound1ActorCore *actor,
                                            unsigned char selector,
                                            int alternate)
{
    const AvspRound1AnimationStateSpec *record;
    if (selector >= AVSP_ROUND1_CLASS47_PRESENTATION_COUNT)
        return 0;
    record = &avsp_round1_class47_records[selector];
    if (alternate)
    {
        actor->source_alternate_animation_record = record->animation_record;
        actor->source_alternate_assembly = record->assembly;
        actor->source_alternate_animation_timer = record->timer;
        actor->source_alternate_animation_branch = record->branch;
    }
    else
    {
        actor->source_primary_animation_record = record->animation_record;
        actor->source_primary_assembly = record->assembly;
        actor->animation_timer = record->timer;
        actor->animation_branch = record->branch;
    }
    return 1;
}

static void avsp_round1_step_class47_animation(AvspRound1ActorCore *actor)
{
    if (actor->animation_timer != 0u)
        --actor->animation_timer;
    if (actor->source_alternate_animation_timer != 0u)
        --actor->source_alternate_animation_timer;
}

static int avsp_round1_step_class47(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor,
                                    unsigned int slot_index)
{
    if (actor->state == 0u)
    {
        const AvspRound1Class45MotionSpec *motion;
        unsigned char random;
        unsigned char selector;
        unsigned int motion_index;
        actor->state = 0x0200u;
        actor->object_or = 0x8000u;
        random = avsp_round1_source_rng(runtime);
        selector = avsp_round1_class47_animation_selectors[
            random & (actor->variant == 0u ? 0x0fu : 0x1fu)];
        if (!avsp_round1_bind_class47_channel(actor, selector, 1))
            return 0;
        random = avsp_round1_source_rng(runtime);
        selector = avsp_round1_class47_animation_selectors[
            random & (actor->variant == 0u ? 0x0fu : 0x1fu)];
        if (!avsp_round1_bind_class47_channel(actor, selector, 0))
            return 0;
        random = avsp_round1_source_rng(runtime);
        actor->source_primary_x_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_primary_y_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_alternate_x_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        actor->source_alternate_y_fp +=
            (long)((short)((random & 0x1fu) - 0x10u)) * 65536L;
        random = avsp_round1_source_rng(runtime);
        motion_index = (unsigned int)((random & 0x70u) >> 4);
        motion = &avsp_round1_class47_motion[motion_index];
        actor->source_motion_fields[0] = motion->primary_x_velocity;
        actor->source_motion_fields[1] = motion->alternate_x_velocity;
        actor->source_motion_fields[2] = motion->primary_y_velocity;
        actor->source_motion_fields[3] = motion->alternate_y_velocity;
        actor->source_motion_fields[4] = motion->primary_y_acceleration;
        actor->source_motion_fields[5] = motion->alternate_y_acceleration;
        runtime->class47_rng_calls +=
            avsp_round1_class47.rng_calls_per_actor;
        ++runtime->class47_initializations;
    }
    if (actor->state == 0x0200u)
    {
        long primary_x_delta =
            (long)actor->source_motion_fields[0] * 256L;
        long alternate_x_delta =
            (long)actor->source_motion_fields[1] * 256L;
        if (actor->source_flags == 0u)
        {
            primary_x_delta = -primary_x_delta;
            alternate_x_delta = -alternate_x_delta;
        }
        actor->source_primary_x_fp += primary_x_delta;
        actor->source_alternate_x_fp += alternate_x_delta;
        actor->source_primary_y_fp +=
            (long)actor->source_motion_fields[2] * 256L;
        actor->source_alternate_y_fp +=
            (long)actor->source_motion_fields[3] * 256L;
        actor->source_motion_fields[2] = (short)(
            actor->source_motion_fields[2] +
            actor->source_motion_fields[4]);
        actor->source_motion_fields[3] = (short)(
            actor->source_motion_fields[3] +
            actor->source_motion_fields[5]);
        avsp_round1_step_class47_animation(actor);
        if (((unsigned long)runtime->frame +
             (pool->capacity - 1u - slot_index)) % 2u != 0u)
        {
            actor->source_x_fp = actor->source_alternate_x_fp;
            actor->source_y_fp = actor->source_alternate_y_fp;
            actor->animation_record =
                actor->source_alternate_animation_record;
            actor->assembly = actor->source_alternate_assembly;
        }
        else
        {
            actor->source_x_fp = actor->source_primary_x_fp;
            actor->source_y_fp = actor->source_primary_y_fp;
            actor->animation_record = actor->source_primary_animation_record;
            actor->assembly = actor->source_primary_assembly;
        }
        actor->x = avsp_round1_fixed_high_word(actor->source_x_fp);
        actor->y = avsp_round1_fixed_high_word(actor->source_y_fp);
        if ((unsigned short)avsp_round1_fixed_high_word(
                actor->source_primary_y_fp) <= (unsigned short)actor->z &&
            (unsigned short)avsp_round1_fixed_high_word(
                actor->source_alternate_y_fp) <= (unsigned short)actor->z)
        {
            actor->state = 0x0400u;
            ++runtime->class47_state_transitions;
        }
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class47_releases;
        return 1;
    }
    return 0;
}

static void avsp_round1_bind_class4b_record(AvspRound1ActorCore *actor,
                                            unsigned char index)
{
    const AvspRound1AnimationStateSpec *record =
        &avsp_round1_class4b_records[index];
    actor->animation_index = index;
    avsp_round1_bind_animation_state(actor, record);
}

static int avsp_round1_step_class4b(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor)
{
    if (actor->state == 0u)
    {
        actor->state = 0x0200u;
        actor->object_or = 0x8000u;
        actor->palette = 0u;
        actor->coordinate_mode = 0u;
        actor->z = (short)(actor->z - 1);
        actor->y = (short)(actor->y + 62);
        actor->x = (short)(actor->x + (actor->facing ? 8 : -8));
        avsp_round1_bind_class4b_record(actor, 0u);
        ++runtime->class4b_initializations;
    }
    if (actor->state == 0x0200u)
    {
        if (runtime->player_special_owner_contact != 0u ||
            runtime->player_special_animation_branch != 0)
        {
            actor->state = 0x0400u;
            return 1;
        }
        if (actor->animation_timer == 0u)
            return 0;
        --actor->animation_timer;
        if (actor->animation_timer == 0u)
        {
            if (actor->animation_branch < 0)
            {
                actor->animation_timer =
                    avsp_round1_class4b_records[
                        actor->animation_index].timer;
                return 1;
            }
            if (actor->animation_index + 1u >=
                    AVSP_ROUND1_CLASS4B_PRESENTATION_COUNT)
                return 0;
            avsp_round1_bind_class4b_record(actor,
                (unsigned char)(actor->animation_index + 1u));
        }
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        unsigned short released_slot = (unsigned short)actor->source_slot;
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        if (runtime->player_special_class4b_source_slot ==
                released_slot)
            runtime->player_special_class4b_source_slot = 0u;
        ++runtime->class4b_releases;
        return 1;
    }
    return 0;
}

static void avsp_round1_bind_class3d_record(AvspRound1ActorCore *actor,
                                            unsigned char index)
{
    const AvspRound1AnimationStateSpec *record =
        &avsp_round1_class3d_records[index];
    actor->animation_index = index;
    avsp_round1_bind_animation_state(actor, record);
}

static int avsp_round1_step_class3d(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor)
{
    if (actor->state == 0u)
    {
        actor->state = 0x0200u;
        actor->palette = 0u;
        actor->coordinate_mode = 0u;
        actor->object_or = 0x8000u;
        actor->source_motion_fields[0] = actor->x;
        actor->source_motion_fields[1] = actor->z;
        avsp_round1_bind_class3d_record(actor, 0u);
        ++runtime->class3d_initializations;
        return 1;
    }
    if (actor->state == 0x0200u)
    {
        const AvspRound1VecS16 *offset;
        short x_offset;
        if (actor->animation_branch < 0)
            actor->state = 0x0400u;
        offset = &avsp_round1_class3d_offsets[actor->variant & 0x0fu];
        x_offset = offset->x;
        if (actor->source_direction != 0u)
            x_offset = (short)-x_offset;
        actor->x = (short)(actor->source_motion_fields[0] + x_offset);
        actor->z = (short)(actor->source_motion_fields[1] + offset->y);
        actor->y = actor->z;
        actor->variant = (unsigned char)((actor->variant + 8u) & 0x0fu);
        if (actor->animation_timer == 0u)
            return 0;
        --actor->animation_timer;
        if (actor->animation_timer == 0u && actor->animation_branch >= 0)
        {
            if (actor->animation_index + 1u >=
                    AVSP_ROUND1_CLASS3D_PRESENTATION_COUNT)
                return 0;
            avsp_round1_bind_class3d_record(actor,
                (unsigned char)(actor->animation_index + 1u));
        }
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class3d_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_spawn_class43_population(
    AvspRound1Runtime *runtime, const AvspRound1ActorCore *owner)
{
    unsigned int group;
    for (group = 0u; group < avsp_round1_class43.group_count; ++group)
    {
        unsigned int index;
        for (index = 0u; index < avsp_round1_class43.actors_per_group;
             ++index)
        {
            AvspRound1ActorCore *actor;
            ++runtime->class43_spawn_requests;
            actor = avsp_round1_allocate_pool_actor(runtime, 3u);
            if (actor == 0)
            {
                ++runtime->class43_allocation_failures;
                break;
            }
            actor->active = 2u;
            actor->actor_class = avsp_round1_class43.actor_class;
            actor->variant = avsp_round1_class43.variant;
            actor->state = 0u;
            actor->substate = 0u;
            actor->facing = 0u;
            actor->source_facing_selector = owner->source_facing_selector;
            actor->x = owner->x;
            actor->y = (short)(owner->y + avsp_round1_class43.y_offset);
            actor->z = (short)(owner->z + avsp_round1_class43.z_offset);
            actor->source_primary_x_fp = (long)actor->x * 65536L;
            actor->source_primary_y_fp = (long)actor->y * 65536L;
            actor->source_alternate_x_fp = actor->source_primary_x_fp;
            actor->source_alternate_y_fp = actor->source_primary_y_fp;
            actor->source_x_fp = actor->source_primary_x_fp;
            actor->source_y_fp = actor->source_primary_y_fp;
            actor->dispatch_entry = avsp_round1_class43.dispatch;
            ++runtime->class43_allocations;
        }
    }
    return runtime->class43_allocation_failures == 0u;
}

static void avsp_round1_spawn_class47_group(AvspRound1Runtime *runtime,
                                            const AvspRound1ActorCore *owner)
{
    unsigned int index;
    for (index = 0u; index < avsp_round1_class47.child_count; ++index)
    {
        AvspRound1ActorCore *actor;
        ++runtime->class47_spawn_requests;
        actor = avsp_round1_allocate_pool_actor(runtime, 3u);
        if (actor == 0)
        {
            ++runtime->class47_allocation_failures;
            return;
        }
        actor->active = 2u;
        actor->actor_class = avsp_round1_class47.actor_class;
        actor->variant = avsp_round1_class47.variant;
        actor->state = 0u;
        actor->substate = 0u;
        actor->facing = 0u;
        actor->source_flags = owner->source_facing_selector;
        actor->x = owner->x;
        actor->y = (short)(owner->y + avsp_round1_class47.y_offset);
        actor->z = (short)(owner->z + avsp_round1_class47.z_offset);
        actor->source_primary_x_fp = (long)actor->x * 65536L;
        actor->source_primary_y_fp = (long)actor->y * 65536L;
        actor->source_alternate_x_fp = actor->source_primary_x_fp;
        actor->source_alternate_y_fp = actor->source_primary_y_fp;
        actor->source_x_fp = actor->source_primary_x_fp;
        actor->source_y_fp = actor->source_primary_y_fp;
        actor->dispatch_entry = avsp_round1_class47.dispatch;
        ++runtime->class47_allocations;
    }
}

static int avsp_round1_spawn_class45_group(
    AvspRound1Runtime *runtime, const AvspRound1ActorCore *owner,
    const AvspRound1Class45SpawnGroupSpec *group)
{
    unsigned int attempt = 0u;
    while (group->attempts == 0xffffu || attempt < group->attempts)
    {
        AvspRound1ActorCore *actor;
        unsigned int allocation_index;
        ++runtime->class45_spawn_attempts;
        actor = avsp_round1_allocate_pool_actor(runtime, 3u);
        if (actor == 0)
            return group->attempts == 0xffffu;
        allocation_index = (unsigned int)runtime->class45_allocations;
        if (allocation_index >= AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT ||
            actor->source_slot != avsp_round1_class45_source_slots[
                AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT - 1u -
                allocation_index])
            return 0;
        actor->actor_class = 0x45;
        actor->state = 0u;
        actor->substate = 0u;
        actor->x = (short)(owner->x + group->x_offset);
        actor->y = (short)(owner->y + group->y_offset);
        actor->z = (short)(owner->z + group->z_offset);
        actor->source_primary_x_fp = (long)actor->x * 65536L;
        actor->source_primary_y_fp = (long)actor->y * 65536L;
        actor->source_alternate_x_fp = actor->source_primary_x_fp;
        actor->source_alternate_y_fp = actor->source_primary_y_fp;
        actor->source_x_fp = actor->source_primary_x_fp;
        actor->source_y_fp = actor->source_primary_y_fp;
        actor->dispatch_entry = 0x0008dc1cUL;
        ++runtime->class45_allocations;
        ++attempt;
    }
    return 1;
}

static int avsp_round1_spawn_class45_population(
    AvspRound1Runtime *runtime, const AvspRound1ActorCore *owner)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT; ++index)
        if (!avsp_round1_spawn_class45_group(
                runtime, owner, &avsp_round1_class45_spawn_groups[index]))
            return 0;
    return runtime->class45_allocations ==
        AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT;
}

static int avsp_round1_step_class44_guard(AvspRound1Runtime *runtime,
                                          AvspRound1ActorCore *actor)
{
    if ((unsigned short)actor->source_slot !=
            (unsigned short)avsp_round1_class44_guard.source_slot ||
        actor->dispatch_entry != avsp_round1_class44_guard.dispatch)
        return 0;
    ++runtime->class44_guard_updates;
    if (actor->state == 0u)
    {
        actor->state = 0x0200u;
        actor->coordinate_mode = avsp_round1_class44_guard.coordinate_mode;
        actor->palette = avsp_round1_class44_guard.palette;
        actor->facing = avsp_round1_class44_guard.facing;
        actor->object_or = avsp_round1_class44_guard.object_or;
        avsp_round1_bind_animation_state(actor,
                                         &avsp_round1_class44_records[0]);
        return 1;
    }
    if (actor->state == 0x0200u)
    {
        if (runtime->class1f_effect_guard != 0u)
            actor->state = 0x0400u;
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        runtime->class1f_effect_guard = 0u;
        actor->state = 0x0402u;
        actor->effect_timer = 3u;
        ++runtime->class44_guard_clears;
        return 1;
    }
    if (actor->state == 0x0402u)
    {
        if (actor->effect_timer == 0u)
            return 0;
        --actor->effect_timer;
        if (actor->effect_timer == 0u)
        {
            actor->state = 0x0404u;
            actor->animation_index = 1u;
            avsp_round1_bind_animation_state(actor,
                                             &avsp_round1_class44_records[1]);
            if (!avsp_round1_spawn_class45_population(runtime, actor))
                return 0;
            if ((unsigned short)actor->source_slot ==
                    avsp_round1_recurring_spawn.intro_gate_owner_slot &&
                actor->actor_class ==
                    avsp_round1_recurring_spawn.intro_gate_owner_class &&
                actor->type ==
                    avsp_round1_recurring_spawn.intro_gate_owner_type &&
                actor->state ==
                    avsp_round1_recurring_spawn.intro_gate_owner_state)
                runtime->first_encounter.source_intro_gate = 0u;
        }
        return 1;
    }
    if (actor->state == 0x0404u)
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
        actor->state = 0u;
        actor->substate = spec->substate;
        actor->facing = spec->facing;
        actor->source_action = 0u;
    }
    for (slot_index = 0u; slot_index < pool20->capacity; ++slot_index)
    {
        unsigned short slot = (unsigned short)(pool20->source_base +
                                               slot_index * pool20->stride);
        if (slot == (unsigned short)avsp_round1_class09_initial_actors[0].source_slot ||
            slot == (unsigned short)avsp_round1_class09_initial_actors[1].source_slot)
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
        actor->source_slot = avsp_round1_class44_guard.source_slot;
        actor->x = avsp_round1_class44_guard.x;
        actor->y = avsp_round1_class44_guard.y;
        actor->z = avsp_round1_class44_guard.z;
        actor->state = 0u;
        actor->substate = avsp_round1_class44_guard.substate;
        actor->dispatch_entry = avsp_round1_class44_guard.dispatch;
    }
    free_index = 0u;
    for (slot_index = 0u; slot_index < pool24->capacity; ++slot_index)
    {
        unsigned short slot = (unsigned short)(pool24->source_base +
                                               slot_index * pool24->stride);
        if (slot == (unsigned short)avsp_round1_class44_guard.source_slot ||
            slot == 0xc600u)
            continue;
        pool24->free_stack[free_index++] = slot;
    }
    pool24->free_count = (unsigned char)free_index;
    return 1;
}

static unsigned short avsp_round1_coffee_scene_camera_x(
    const AvspRound1Runtime *runtime)
{
    if (runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE)
        return runtime->first_encounter.source_camera_bound;
    return (unsigned short)runtime->camera_x_position;
}

static int avsp_round1_spawn_coffee_scene_records(
    AvspRound1Runtime *runtime)
{
    unsigned short camera_x = avsp_round1_coffee_scene_camera_x(runtime);
    while (runtime->coffee_scene_record_cursor <
           AVSP_ROUND1_COFFEE_SCENE_RECORD_COUNT)
    {
        const AvspRound1CoffeeSceneRecordSpec *spec =
            &avsp_round1_coffee_scene_records[
                runtime->coffee_scene_record_cursor];
        AvspRound1ActorCore *actor;
        if (spec->camera_threshold > camera_x)
            break;
        ++runtime->coffee_scene_spawn_attempts;
        actor = avsp_round1_allocate_pool_source_slot(
            runtime, 2u, (unsigned short)spec->source_slot);
        if (actor == 0)
            return 1;
        actor->actor_class = spec->actor_class;
        actor->variant = spec->variant;
        actor->x = spec->x;
        actor->y = spec->y;
        actor->z = spec->y;
        actor->facing = spec->facing;
        actor->state = 0u;
        actor->substate = 0u;
        actor->transition_timer = spec->timer;
        actor->dispatch_entry = spec->actor_class == 0x01 ?
            avsp_round1_class01.dispatch : avsp_round1_class02.dispatch;
        ++runtime->coffee_scene_record_cursor;
        ++runtime->coffee_scene_spawns;
    }
    return 1;
}

static int avsp_round1_spawn_class01_enemy(AvspRound1Runtime *runtime,
                                            AvspRound1ActorCore *owner)
{
    AvspRound1ActorCore *actor;
    ++runtime->class01_spawn_requests;
    actor = avsp_round1_allocate_pool_actor(runtime, 0u);
    if (actor == 0)
    {
        ++runtime->class01_spawn_allocation_failures;
        return 0;
    }
    actor->actor_class = avsp_round1_class01.spawned_class;
    actor->variant = avsp_round1_class01.spawned_variant;
    actor->state = 0u;
    actor->substate = 0u;
    actor->source_action = 0u;
    actor->transition_timer = 0u;
    actor->source_dynamic_spawn = 1u;
    actor->x = owner->x;
    actor->y = owner->y;
    actor->z = owner->z;
    ++runtime->first_encounter.source_living_count;
    ++runtime->class01_spawn_allocations;
    return 1;
}

static int avsp_round1_step_class01_animation(AvspRound1ActorCore *actor)
{
    if (actor->animation_index >= AVSP_ROUND1_CLASS01_PRESENTATION_COUNT ||
        actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    if (actor->animation_branch < 0)
        return 1;
    if (actor->animation_index + 1u >=
        AVSP_ROUND1_CLASS01_PRESENTATION_COUNT)
        return 0;
    ++actor->animation_index;
    avsp_round1_bind_animation_state(
        actor, &avsp_round1_class01_records[actor->animation_index]);
    return 1;
}

static int avsp_round1_step_class01(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor)
{
    unsigned short camera_x = avsp_round1_coffee_scene_camera_x(runtime);
    if (actor->state == 0u)
    {
        actor->active = 2u;
        actor->state = 0x0200u;
        actor->substate = 0u;
        actor->object_or = 0x8000u;
        actor->z = actor->y;
        actor->source_motion_fields[0] = -32;
        actor->source_motion_fields[2] = 96;
        actor->source_motion_fields[4] = 0;
        actor->transition_timer = actor->variant == 0u ?
            avsp_round1_class01.timer_variant0 :
            avsp_round1_class01.timer_variant1;
        actor->source_a6 = avsp_round1_class01.initial_remaining_spawns;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
                                         &avsp_round1_class01_records[0]);
        ++runtime->class01_initializations;
        return 1;
    }
    if (actor->state == 0x0200u)
    {
        if (runtime->coffee_scene_active_flag == 0u)
        {
            actor->state = 0x0400u;
            ++runtime->class01_state_transitions;
        }
        else if ((unsigned short)(camera_x +
                     avsp_round1_class01.camera_activation_distance) >=
                 (unsigned short)actor->x)
        {
            actor->state = 0x0202u;
            ++runtime->class01_state_transitions;
        }
        return 1;
    }
    if (actor->state == 0x0202u)
    {
        if (actor->transition_timer == 0u)
        {
            actor->state = 0x0204u;
            ++runtime->class01_state_transitions;
        }
        else
            --actor->transition_timer;
        return 1;
    }
    if (actor->state == 0x0204u)
    {
        if (actor->animation_branch >= 0)
            return avsp_round1_step_class01_animation(actor);
        actor->state = 0x0206u;
        ++runtime->class01_state_transitions;
        if (!avsp_round1_spawn_class01_enemy(runtime, actor))
            return 0;
        if (!avsp_round1_spawn_class43_population(runtime, actor))
            return 0;
        runtime->class01_effect_requests += 8u;
        runtime->class01_audio_command = actor->variant == 0u ?
            avsp_round1_class01.initial_audio_command :
            avsp_round1_class01.variant_audio_command;
        ++runtime->class01_audio_events;
        return 1;
    }
    if (actor->state == 0x0206u)
    {
        if ((unsigned short)actor->x < camera_x)
        {
            actor->state = 0x0400u;
            ++runtime->class01_state_transitions;
            return 1;
        }
        if (actor->source_a6 == 0u)
            return 1;
        if (actor->transition_timer != 0u)
        {
            --actor->transition_timer;
            return 1;
        }
        if (runtime->first_encounter.source_living_count >=
            avsp_round1_class01.maximum_living)
            return 1;
        if (!avsp_round1_spawn_class01_enemy(runtime, actor))
            return 0;
        --actor->source_a6;
        actor->transition_timer = avsp_round1_class01.respawn_timer;
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        if ((unsigned short)(actor->x +
                avsp_round1_class01.camera_release_distance) < camera_x)
        {
            actor->state = 0x0600u;
            ++runtime->class01_state_transitions;
        }
        return 1;
    }
    if (actor->state == 0x0600u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class01_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_class02_damage_overlap(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *actor)
{
    const AvspRound1CollisionBoxSpec *attack = &avsp_round1_class02.attack_box;
    const AvspRound1CollisionBoxSpec *hurt = &avsp_round1_class02.hurt_box;
    long dx = (long)runtime->player_action.x + attack->x_center -
        actor->x - hurt->x_center;
    long dy = (long)runtime->player_action.lane +
        runtime->player_action.height + attack->y_center -
        actor->y - hurt->y_center;
    long dz = (long)runtime->player_action.lane + attack->z_center -
        actor->z - hurt->z_center;
    return avsp_round1_abs_long(dx) <
            (long)attack->x_half + hurt->x_half &&
        avsp_round1_abs_long(dy) <
            (long)attack->y_half + hurt->y_half &&
        avsp_round1_abs_long(dz) <
            (long)attack->z_half + hurt->z_half;
}

static int avsp_round1_class02_in_camera(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *actor)
{
    unsigned short camera_x = avsp_round1_coffee_scene_camera_x(runtime);
    return (unsigned short)(actor->x - (short)camera_x +
        (short)avsp_round1_class02.camera_bounds_bias) <=
        avsp_round1_class02.camera_bounds_span;
}

static int avsp_round1_step_class02(AvspRound1Runtime *runtime,
                                    AvspRound1Pool *pool,
                                    AvspRound1ActorCore *actor)
{
    if (actor->state == 0u)
    {
        actor->state = 0x0200u;
        actor->substate = 0u;
        actor->object_or = 0x8000u;
        actor->z = actor->y;
        actor->source_motion_fields[0] = 0;
        actor->source_motion_fields[2] = 80;
        actor->source_motion_fields[4] = 0;
        actor->source_a4 = avsp_round1_class02.initial_effect_count;
        actor->source_flags = (unsigned char)
            avsp_round1_class02_in_camera(runtime, actor);
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor,
                                         &avsp_round1_class02_records[0]);
        ++runtime->class02_initializations;
        return 1;
    }
    if (actor->state == 0x0200u)
    {
        unsigned char in_camera;
        if (actor->transition_timer != 0u)
        {
            --actor->transition_timer;
            return 1;
        }
        in_camera = (unsigned char)avsp_round1_class02_in_camera(
            runtime, actor);
        actor->source_flags = in_camera;
        if (in_camera && runtime->player_special_attack_contact_ready &&
            actor->source_player_guard == 0u)
        {
            ++runtime->class02_collision_tests;
            if (avsp_round1_class02_damage_overlap(runtime, actor))
            {
                short next_health = (short)(actor->health -
                                            avsp_round1_class02.damage);
                actor->health = next_health < 0 ?
                    avsp_round1_class02.ko_clamp : next_health;
                actor->source_facing_selector =
                    (unsigned short)runtime->player_action.x <
                        (unsigned short)actor->x ?
                    avsp_round1_class02.reaction_direction_less :
                    avsp_round1_class02.reaction_direction_greater_equal;
                actor->state = 0x0400u;
                actor->source_player_guard = 1u;
                ++runtime->class02_damage_writes;
                ++runtime->class02_state_transitions;
            }
        }
        if (!runtime->player_special_attack_active)
            actor->source_player_guard = 0u;
        return 1;
    }
    if (actor->state == 0x0400u)
    {
        actor->state = 0x0200u;
        ++runtime->class02_state_transitions;
        if (actor->source_a4 == 0u)
            return 0;
        --actor->source_a4;
        actor->source_motion_fields[4] = 0;
        actor->animation_index = 1u;
        avsp_round1_bind_animation_state(actor,
                                         &avsp_round1_class02_records[1]);
        runtime->class02_effect_requests += 4u;
        avsp_round1_spawn_class47_group(runtime, actor);
        runtime->class02_audio_command = avsp_round1_class02.audio_command;
        ++runtime->class02_audio_events;
        return 1;
    }
    if (actor->state == 0x0600u)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->class02_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_spawn_coffee_shop_obstacle(
    AvspRound1Runtime *runtime)
{
    const AvspRound1ObstacleLifecycleSpec *spec =
        &avsp_round1_coffee_shop_obstacle_lifecycle;
    AvspRound1ActorCore *actor;
    if (runtime->coffee_shop_obstacle_spawned ||
        runtime->coffee_shop_obstacle_released ||
        (unsigned short)runtime->camera_x_previous < spec->camera_threshold)
        return 1;
    ++runtime->coffee_shop_obstacle_spawn_attempts;
    actor = avsp_round1_allocate_pool_source_slot(
        runtime, 2u, (unsigned short)spec->source_slot);
    if (actor == 0)
        return 1;
    actor->actor_class = avsp_round1_coffee_shop_obstacle.actor_class;
    actor->dispatch_entry = spec->dispatch_entry;
    actor->x = spec->x;
    actor->y = spec->y;
    actor->z = spec->z;
    actor->facing = avsp_round1_coffee_shop_obstacle.facing;
    actor->health = spec->initial_health;
    actor->state = 0u;
    actor->substate = 0u;
    runtime->coffee_shop_obstacle_spawned = 1u;
    ++runtime->coffee_shop_obstacle_spawns;
    return 1;
}

static int avsp_round1_step_obstacle_child_animation(
    AvspRound1ActorCore *actor)
{
    const AvspRound1ObstacleChildSequenceSpec *sequence;
    unsigned char next;
    if (actor->variant >= AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS)
        return 0;
    sequence = &avsp_round1_coffee_shop_obstacle_child_sequences[
        actor->variant];
    if (sequence->record_count == 0u ||
        actor->animation_index >= sequence->record_count ||
        actor->animation_timer == 0u)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    next = (unsigned char)(actor->animation_index + 1u);
    if (actor->animation_branch < 0)
        next = 0u;
    if (next >= sequence->record_count)
        return 0;
    actor->animation_index = next;
    avsp_round1_bind_animation_state(actor, &sequence->records[next]);
    return 1;
}

static int avsp_round1_step_coffee_shop_obstacle_child(
    AvspRound1Runtime *runtime, AvspRound1Pool *pool,
    AvspRound1ActorCore *actor)
{
    AvspRound1ActorCore *parent = avsp_round1_find_pool_source_actor(
        runtime, 2u, actor->source_target_low);
    ++runtime->coffee_shop_obstacle_child_updates;
    if (parent == 0 || parent->actor_class !=
            avsp_round1_coffee_shop_obstacle.actor_class)
        return 0;
    if (actor->state == 0u)
    {
        const AvspRound1ObstacleChildSequenceSpec *sequence;
        if (actor->variant >= AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS)
            return 0;
        sequence = &avsp_round1_coffee_shop_obstacle_child_sequences[
            actor->variant];
        if (sequence->record_count == 0u)
            return 0;
        actor->state = 0x0200u;
        actor->object_or = avsp_round1_coffee_shop_obstacle_lifecycle.
            object_priority;
        actor->x = parent->x;
        actor->y = parent->y;
        actor->z = parent->z;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(actor, &sequence->records[0]);
        return 1;
    }
    if (actor->state == 0x0200u)
    {
        if (parent->state >=
                avsp_round1_coffee_shop_obstacle_lifecycle.break_state)
        {
            actor->state = 0x0400u;
            actor->animation_index = 4u;
            avsp_round1_bind_animation_state(
                actor, &avsp_round1_coffee_shop_obstacle_child_release);
            return 1;
        }
        return avsp_round1_step_obstacle_child_animation(actor);
    }
    if (actor->state == 0x0400u || actor->state == 0x0600u)
    {
        unsigned int index;
        if (actor->animation_branch >= 0)
            return 0;
        for (index = 0u; index < AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS;
             ++index)
            if (parent->source_children[index] ==
                    (unsigned short)actor->source_slot)
                parent->source_children[index] = 0u;
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        ++runtime->coffee_shop_obstacle_child_releases;
        return 1;
    }
    return 0;
}

static int avsp_round1_coffee_shop_obstacle_damage_overlap(
    const AvspRound1Runtime *runtime, const AvspRound1ActorCore *actor)
{
    const AvspRound1ObstacleLifecycleSpec *spec =
        &avsp_round1_coffee_shop_obstacle_lifecycle;
    long dx = (long)runtime->player_action.x +
        spec->player_attack_box.x_center - actor->x -
        spec->obstacle_hurt_box.x_center;
    long dy = (long)runtime->player_action.lane +
        runtime->player_action.height + spec->player_attack_box.y_center -
        actor->y - spec->obstacle_hurt_box.y_center;
    long dz = (long)runtime->player_action.lane +
        spec->player_attack_box.z_center - actor->z -
        spec->obstacle_hurt_box.z_center;
    return avsp_round1_abs_long(dx) <
            (long)spec->player_attack_box.x_half +
                spec->obstacle_hurt_box.x_half &&
        avsp_round1_abs_long(dy) <
            (long)spec->player_attack_box.y_half +
                spec->obstacle_hurt_box.y_half &&
        avsp_round1_abs_long(dz) <
            (long)spec->player_attack_box.z_half +
                spec->obstacle_hurt_box.z_half;
}

static int avsp_round1_step_coffee_shop_obstacle_parent_animation(
    AvspRound1ActorCore *actor)
{
    if (actor->animation_timer == 0u || actor->animation_index >=
            AVSP_ROUND1_OBSTACLE_PARENT_RECORD_COUNT)
        return 0;
    --actor->animation_timer;
    if (actor->animation_timer != 0u)
        return 1;
    if (actor->animation_branch < 0 || actor->animation_index + 1u >=
            AVSP_ROUND1_OBSTACLE_PARENT_RECORD_COUNT)
        return 0;
    ++actor->animation_index;
    avsp_round1_bind_animation_state(
        actor, &avsp_round1_coffee_shop_obstacle_records[
            actor->animation_index]);
    return 1;
}

static int avsp_round1_step_coffee_shop_obstacle(
    AvspRound1Runtime *runtime, AvspRound1Pool *pool,
    AvspRound1ActorCore *actor)
{
    const AvspRound1ObstacleLifecycleSpec *spec =
        &avsp_round1_coffee_shop_obstacle_lifecycle;
    unsigned int index;
    if (actor->state == 0u)
    {
        AvspRound1Pool *child_pool = &runtime->pools[5];
        if (child_pool->free_count < spec->child_count)
            return 1;
        actor->state = spec->active_state;
        actor->object_or = spec->object_priority;
        actor->source_field01 = spec->field64;
        actor->z = actor->y;
        actor->animation_index = 0u;
        avsp_round1_bind_animation_state(
            actor, &avsp_round1_coffee_shop_obstacle_records[0]);
        for (index = 0u; index < spec->child_count; ++index)
        {
            AvspRound1ActorCore *child =
                avsp_round1_allocate_pool_actor(runtime, 5u);
            if (child == 0)
                return 0;
            child->actor_class = spec->child_class;
            child->state = 0u;
            child->substate = 0u;
            child->variant = spec->child_variant_order[index];
            child->source_target_low = (unsigned short)actor->source_slot;
            actor->source_children[index] =
                (unsigned short)child->source_slot;
            ++runtime->coffee_shop_obstacle_child_allocations;
        }
        return 1;
    }
    if (actor->state == spec->active_state)
    {
        if (runtime->player_special_attack_contact_ready &&
            avsp_round1_coffee_shop_obstacle_damage_overlap(runtime, actor))
        {
            short health = (short)(actor->health - (short)spec->damage);
            actor->health = health < 0 ? -1 : health;
            actor->state = spec->break_state;
            actor->substate = 0u;
            runtime->player_special_attack_contact_ready = 0u;
            ++runtime->player_special_attack_contacts;
            ++runtime->coffee_shop_obstacle_damage_events;
            ++runtime->coffee_shop_obstacle_state_transitions;
        }
        return 1;
    }
    if (actor->state == spec->break_state)
    {
        actor->state = spec->break_timer_state;
        actor->effect_timer = spec->break_timer;
        actor->animation_index = 1u;
        avsp_round1_bind_animation_state(
            actor, &avsp_round1_coffee_shop_obstacle_records[1]);
        ++runtime->coffee_shop_obstacle_state_transitions;
        return 1;
    }
    if (actor->state == spec->break_timer_state)
    {
        if (actor->effect_timer != 0u)
        {
            --actor->effect_timer;
            return 1;
        }
        if (actor->animation_branch >= 0)
            return avsp_round1_step_coffee_shop_obstacle_parent_animation(
                actor);
        actor->state = spec->physics_state;
        actor->source_action_initialized = 0u;
        ++runtime->coffee_shop_obstacle_state_transitions;
        return 1;
    }
    if (actor->state == spec->physics_state)
    {
        if (!actor->source_action_initialized)
        {
            actor->source_x_fp = (long)actor->x * 65536L;
            actor->source_y_fp = (long)(actor->y + 48) * 65536L;
            actor->source_z_fp = (long)actor->x * 65536L;
            actor->source_aux_fp = (long)actor->y * 65536L;
            actor->source_motion_flags = 0u;
            actor->substate = 0u;
            for (index = 0u; index < 8u; ++index)
                actor->source_motion_fields[index] =
                    spec->physics_fields[index];
            if (actor->facing == 0u)
            {
                actor->source_motion_fields[0] = (short)
                    -actor->source_motion_fields[0];
                actor->source_motion_fields[2] = (short)
                    -actor->source_motion_fields[2];
                actor->source_motion_fields[4] = (short)
                    -actor->source_motion_fields[4];
                actor->source_motion_fields[6] = (short)
                    -actor->source_motion_fields[6];
            }
            actor->source_action_initialized = 1u;
            actor->animation_index = 3u;
            avsp_round1_bind_animation_state(
                actor, &avsp_round1_coffee_shop_obstacle_records[3]);
            return 1;
        }
        if ((actor->source_motion_flags & 1u) == 0u)
        {
            actor->source_x_fp +=
                (long)actor->source_motion_fields[0] * 256L;
            actor->source_y_fp +=
                (long)actor->source_motion_fields[1] * 256L;
            actor->source_motion_fields[1] = (short)(
                actor->source_motion_fields[1] +
                actor->source_motion_fields[3]);
            if ((unsigned short)avsp_round1_fixed_high_word(
                    actor->source_y_fp) < (unsigned short)actor->z)
                actor->source_motion_flags = (unsigned char)(
                    actor->source_motion_flags | 1u);
        }
        if ((actor->source_motion_flags & 2u) == 0u)
        {
            actor->source_z_fp +=
                (long)actor->source_motion_fields[4] * 256L;
            actor->source_aux_fp +=
                (long)actor->source_motion_fields[5] * 256L;
            actor->source_motion_fields[5] = (short)(
                actor->source_motion_fields[5] +
                actor->source_motion_fields[7]);
            if ((unsigned short)avsp_round1_fixed_high_word(
                    actor->source_aux_fp) < (unsigned short)actor->z)
                actor->source_motion_flags = (unsigned char)(
                    actor->source_motion_flags | 2u);
        }
        actor->substate = (unsigned short)(
            (unsigned short)actor->source_motion_flags << 8);
        actor->animation_index = (unsigned char)(
            (runtime->frame & 1u) == 0u ? 3u : 4u);
        avsp_round1_bind_animation_state(actor,
            &avsp_round1_coffee_shop_obstacle_records[
                actor->animation_index]);
        if (actor->source_motion_flags == 3u)
        {
            actor->state = spec->release_state;
            ++runtime->coffee_shop_obstacle_state_transitions;
        }
        return 1;
    }
    if (actor->state == spec->release_state)
    {
        if (!avsp_round1_release_pool_actor(pool, actor))
            return 0;
        runtime->coffee_shop_obstacle_released = 1u;
        ++runtime->coffee_shop_obstacle_releases;
        return 1;
    }
    return 0;
}

static void avsp_round1_bind_projectile_animation(
    AvspRound1WeaponProjectileAllocation *projectile)
{
    const AvspRound1AnimationStateSpec *record;
    if (projectile->actor_class == avsp_round1_air_weapon_projectile.actor_class)
    {
        if (projectile->presentation_index >=
            AVSP_ROUND1_AIR_WEAPON_PRESENTATION_COUNT)
            return;
        record = &avsp_round1_air_weapon_presentations[
            projectile->presentation_index];
    }
    else if (projectile->actor_class ==
             avsp_round1_weapon_projectile.parent_class)
    {
        if (projectile->presentation_index >=
            AVSP_ROUND1_WEAPON_PARENT_PRESENTATION_COUNT)
            return;
        record = &avsp_round1_weapon_parent_presentations[
            projectile->presentation_index];
    }
    else
    {
        const AvspRound1WeaponChildSequenceSpec *sequence;
        if (projectile->variant >= AVSP_ROUND1_WEAPON_CHILD_VARIANT_COUNT)
            return;
        sequence = &avsp_round1_weapon_child_sequences[projectile->variant];
        if (projectile->presentation_index >= sequence->record_count)
            return;
        record = &sequence->records[projectile->presentation_index];
    }
    projectile->animation_timer = record->timer;
    projectile->animation_branch = record->branch;
    projectile->animation_record = record->animation_record;
    projectile->assembly = record->assembly;
    projectile->attack_selector = record->attack_selector;
}

unsigned long avsp_round1_weapon_current_attack_record(
    const AvspRound1WeaponProjectileAllocation *projectile)
{
    short attack_relative;
    if (projectile == 0 || projectile->attack_selector == 0u)
        return 0UL;
    attack_relative = projectile->actor_class ==
            avsp_round1_weapon_projectile.child_class ?
        avsp_round1_weapon_projectile.child_attack_relative :
        avsp_round1_weapon_projectile.parent_attack_relative;
    return projectile->attack_table + (unsigned long)attack_relative +
        (unsigned long)projectile->attack_selector *
            avsp_round1_weapon_projectile.attack_record_stride;
}

static int avsp_round1_weapon_angle_index(unsigned char angle,
                                          unsigned int *angle_index)
{
    unsigned int index;
    for (index = 0u; index < AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT;
         ++index)
        if (avsp_round1_weapon_parent_route_angles[index] == angle)
        {
            *angle_index = index;
            return 1;
        }
    return 0;
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
    avsp_round1_clear_weapon_projectile_slot(projectile);
    ++runtime->player_weapon_projectile_releases;
    return 1;
}

static int avsp_round1_allocate_weapon_child(
    AvspRound1Runtime *runtime,
    const AvspRound1WeaponProjectileAllocation *parent,
    const AvspRound1WeaponChildSpawnSpec *row)
{
    unsigned int index;
    AvspRound1WeaponProjectileAllocation *child;
    short x_offset;
    if (runtime->player_weapon_projectile_free_count == 0u)
    {
        ++runtime->player_weapon_allocation_failures;
        return 0;
    }
    --runtime->player_weapon_projectile_free_count;
    index = runtime->player_weapon_projectile_free_stack[
        runtime->player_weapon_projectile_free_count];
    if (index >= AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY)
        return 0;
    child = &runtime->player_weapon_projectiles[index];
    avsp_round1_clear_weapon_projectile_slot(child);
    child->collision_identity = avsp_round1_next_collision_identity(runtime);
    child->collision_registration_pending = 1u;
    x_offset = parent->facing == 0u ? (short)-row->x : row->x;
    child->active = 1u;
    child->actor_class = avsp_round1_player_weapon.child_class;
    child->variant = row->variant;
    child->facing = parent->facing;
    child->source_slot = (unsigned short)(
        avsp_round1_player_weapon.projectile_source_base +
        index * avsp_round1_player_weapon.projectile_stride);
    child->owner = parent->source_slot;
    child->x = (short)(parent->x + x_offset);
    child->y = (short)(parent->z + row->y);
    child->z = (short)(parent->z + row->z);
    child->x_fp = avsp_round1_replace_fixed_high_word(child->x_fp, child->x);
    child->y_fp = avsp_round1_replace_fixed_high_word(child->y_fp, child->y);
    child->z_fp = (long)child->z * 65536L;
    child->attack_table = avsp_round1_player_weapon.child_attack_table;
    child->state = avsp_round1_weapon_projectile.initial_state;
    child->damage_class_index = 0u;
    ++runtime->player_weapon_allocations;
    return 1;
}

static int avsp_round1_allocate_weapon_effect(
    AvspRound1Runtime *runtime,
    const AvspRound1WeaponProjectileAllocation *projectile,
    unsigned char variant)
{
    AvspRound1ActorCore *effect;
    if (variant == avsp_round1_parent_weapon_effect.variant)
        ++runtime->player_weapon_parent_effect_requests;
    else
        ++runtime->player_air_weapon_effect_requests;
    effect = avsp_round1_allocate_pool_actor(runtime, 3u);
    if (effect == 0)
    {
        if (variant == avsp_round1_parent_weapon_effect.variant)
            ++runtime->player_weapon_parent_effect_allocation_failures;
        else
            ++runtime->player_air_weapon_effect_allocation_failures;
        return 1;
    }
    effect->actor_class = avsp_round1_parent_weapon_effect.actor_class;
    effect->variant = variant;
    effect->state = 0u;
    effect->x = projectile->x;
    effect->y = projectile->y;
    effect->z = projectile->z;
    effect->facing = projectile->facing;
    effect->animation_record = projectile->animation_record;
    effect->assembly = projectile->assembly;
    effect->effect_timer = avsp_round1_parent_weapon_effect.timer;
    effect->dispatch_entry = avsp_round1_parent_weapon_effect.dispatch_entry;
    if (variant == avsp_round1_parent_weapon_effect.variant)
        ++runtime->player_weapon_parent_effect_allocations;
    else
        ++runtime->player_air_weapon_effect_allocations;
    return 1;
}

static int avsp_round1_step_air_weapon_effect(
    AvspRound1Runtime *runtime, AvspRound1Pool *pool,
    AvspRound1ActorCore *effect)
{
    if (effect->state == 0u)
    {
        effect->state = 2u;
        effect->object_or = 0x8000u;
        effect->source_flags = 0u;
        effect->hurt_selector = 0u;
        effect->attack_selector = 0u;
    }
    if (effect->state == 2u)
    {
        if (effect->effect_timer == 0u)
            return 0;
        --effect->effect_timer;
        if (effect->effect_timer == 0u)
        {
            unsigned char variant = effect->variant;
            if (!avsp_round1_release_pool_actor(pool, effect))
                return 0;
            if (variant == avsp_round1_parent_weapon_effect.variant)
                ++runtime->player_weapon_parent_effect_releases;
            else
                ++runtime->player_air_weapon_effect_releases;
            return 1;
        }
        if (effect->variant != 0u)
            effect->x = (short)(effect->x +
                runtime->player_air_weapon_effect_x_delta);
        return 1;
    }
    if (effect->state == 4u)
    {
        if (!avsp_round1_release_pool_actor(pool, effect))
            return 0;
        ++runtime->player_air_weapon_effect_releases;
        return 1;
    }
    return 0;
}

static void avsp_round1_air_weapon_add_motion(
    AvspRound1WeaponProjectileAllocation *projectile,
    const AvspRound1VecS16 *motion)
{
    projectile->x_fp += (long)motion->x * 256L;
    projectile->y_fp += (long)motion->y * 256L;
    projectile->x = avsp_round1_fixed_high_word(projectile->x_fp);
    projectile->y = avsp_round1_fixed_high_word(projectile->y_fp);
}

static void avsp_round1_step_air_weapon_animation(
    AvspRound1WeaponProjectileAllocation *projectile)
{
    if (projectile->animation_timer > 0u)
        --projectile->animation_timer;
    if (projectile->animation_timer != 0u)
        return;
    if (projectile->animation_branch < 0)
    {
        projectile->animation_timer =
            avsp_round1_air_weapon_presentations[
                projectile->presentation_index].timer;
        return;
    }
    if (projectile->presentation_index + 1u <
        AVSP_ROUND1_AIR_WEAPON_PRESENTATION_COUNT)
    {
        ++projectile->presentation_index;
        avsp_round1_bind_projectile_animation(projectile);
    }
}

static int avsp_round1_step_air_weapon_projectile(
    AvspRound1Runtime *runtime, unsigned int index)
{
    AvspRound1WeaponProjectileAllocation *projectile =
        &runtime->player_weapon_projectiles[index];
    const AvspRound1VecS16 *base_motion;
    if (projectile->state == avsp_round1_air_weapon_projectile.initial_state)
    {
        const AvspRound1VecS16 *offset;
        if (projectile->owner_offset_selector >=
            AVSP_ROUND1_AIR_WEAPON_SELECTOR_COUNT || projectile->angle >=
            AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT)
            return 0;
        offset = &avsp_round1_air_weapon_selector_offsets[
            projectile->owner_offset_selector];
        projectile->x = (short)(projectile->x +
            (projectile->facing == 0u ? -offset->x : offset->x));
        projectile->y = (short)(projectile->y + offset->y);
        --projectile->z;
        projectile->x_fp = avsp_round1_replace_fixed_high_word(
            projectile->x_fp, projectile->x);
        projectile->y_fp = avsp_round1_replace_fixed_high_word(
            projectile->y_fp, projectile->y);
        projectile->z_fp = (long)projectile->z * 65536L;
        projectile->object_or = avsp_round1_air_weapon_projectile.object_or;
        projectile->active_collision = 1u;
        projectile->presentation_index = 0u;
        projectile->presentation_count =
            AVSP_ROUND1_AIR_WEAPON_PRESENTATION_COUNT;
        projectile->progress = 0u;
        projectile->substate = 0u;
        projectile->state = avsp_round1_air_weapon_projectile.active_state;
        avsp_round1_bind_projectile_animation(projectile);
        ++runtime->player_weapon_projectile_initializations;
        return 1;
    }
    if (projectile->state == avsp_round1_air_weapon_projectile.active_state)
    {
        if (projectile->angle >= AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT)
            return 0;
        if (projectile->substate == 0u)
        {
            unsigned char shifted = (unsigned char)(projectile->angle - 16u);
            if (projectile->angle == 16u || projectile->angle == 48u ||
                shifted >= 32u ||
                (unsigned short)(projectile->y - projectile->z) >= 0x009cu)
            {
                projectile->substate = 2u;
                projectile->progress = 0u;
                projectile->direction_timer = 1u;
            }
        }
        else if (projectile->substate == 2u)
        {
            if (projectile->direction_timer == 0u)
                return 0;
            --projectile->direction_timer;
            if (projectile->direction_timer == 0u)
            {
                projectile->direction_timer =
                    avsp_round1_air_weapon_projectile.direction_timer_reload;
                if ((projectile->angle & 0x0fu) == 0u)
                    projectile->substate = 4u;
                else if ((projectile->angle & 0x10u) == 0u)
                    ++projectile->angle;
                else
                    --projectile->angle;
                ++runtime->player_air_weapon_direction_steps;
            }
        }
        else if (projectile->substate != 4u)
            return 0;
        if (projectile->substate == 4u)
        {
            unsigned short x_distance;
            unsigned short y_distance;
            unsigned int low = projectile->progress & 0x0fu;
            unsigned int high = projectile->progress >> 4;
            if (projectile->health < 0 ||
                (unsigned short)projectile->y < (unsigned short)projectile->z)
            {
                projectile->state =
                    avsp_round1_air_weapon_projectile.emitter_state;
                projectile->substate = 0u;
                projectile->child_cadence =
                    avsp_round1_air_weapon_projectile.child_cadence_initial;
                return 1;
            }
            x_distance = (unsigned short)(projectile->x -
                runtime->camera_x_position + 0x50);
            y_distance = (unsigned short)(projectile->y -
                runtime->camera_z_position + 0x80);
            if (x_distance > 0x0220u || y_distance > 0x0240u)
            {
                projectile->state =
                    avsp_round1_air_weapon_projectile.release_state;
                return 1;
            }
            base_motion = &avsp_round1_air_weapon_motion_high[4][
                projectile->angle];
            avsp_round1_air_weapon_add_motion(projectile, base_motion);
            avsp_round1_step_air_weapon_animation(projectile);
            if (high != 0u)
                avsp_round1_air_weapon_add_motion(projectile,
                    &avsp_round1_air_weapon_motion_high[high][
                        projectile->angle]);
            if (low != 0u)
                avsp_round1_air_weapon_add_motion(projectile,
                    &avsp_round1_air_weapon_motion_low[low][
                        projectile->angle]);
            if (projectile->progress <
                avsp_round1_air_weapon_projectile.progress_max)
            {
                unsigned int next = projectile->progress +
                    avsp_round1_air_weapon_projectile.progress_step;
                projectile->progress = (unsigned char)(next >
                    avsp_round1_air_weapon_projectile.progress_max ?
                    avsp_round1_air_weapon_projectile.progress_max : next);
            }
        }
        else
        {
            base_motion = &avsp_round1_air_weapon_motion_high[4][
                projectile->angle];
            avsp_round1_air_weapon_add_motion(projectile, base_motion);
        }
        ++runtime->player_air_weapon_motion_updates;
        if ((runtime->scheduler_frames & 1u) == 0u &&
            !avsp_round1_allocate_weapon_effect(runtime, projectile,
                avsp_round1_air_weapon_projectile.effect_variant))
            return 0;
        return 1;
    }
    if (projectile->state == avsp_round1_air_weapon_projectile.emitter_state)
    {
        const AvspRound1WeaponChildSpawnSpec *rows = projectile->health < 0 ?
            avsp_round1_air_weapon_child_spawn_collision :
            avsp_round1_air_weapon_child_spawn_normal;
        if (projectile->substate == 0u)
        {
            projectile->substate = 2u;
            projectile->child_count =
                avsp_round1_air_weapon_projectile.child_count;
            projectile->child_cadence =
                avsp_round1_air_weapon_projectile.child_cadence_initial;
        }
        if (projectile->child_cadence > 0u)
            --projectile->child_cadence;
        if (projectile->child_cadence == 0u)
        {
            if (projectile->child_count == 0u)
                projectile->state =
                    avsp_round1_air_weapon_projectile.release_state;
            else
            {
                unsigned int row_index = projectile->child_count - 1u;
                --projectile->child_count;
                if (!avsp_round1_allocate_weapon_child(runtime, projectile,
                        &rows[row_index]))
                    ++runtime->failure_count;
                projectile->child_cadence =
                    avsp_round1_air_weapon_projectile.child_cadence_reload;
            }
        }
        return 1;
    }
    if (projectile->state == avsp_round1_air_weapon_projectile.release_state)
        return avsp_round1_release_player_weapon_projectile(runtime, index);
    return 0;
}

static int avsp_round1_step_weapon_projectile(
    AvspRound1Runtime *runtime, unsigned int index)
{
    AvspRound1WeaponProjectileAllocation *projectile =
        &runtime->player_weapon_projectiles[index];
    const AvspRound1VecS16 *low_motion;
    const AvspRound1VecS16 *high_motion;
    unsigned int angle_index;
    unsigned int low_index;
    unsigned int high_index;
    unsigned short x_distance;
    unsigned short y_distance;
    if (projectile->actor_class ==
        avsp_round1_air_weapon_projectile.actor_class)
        return avsp_round1_step_air_weapon_projectile(runtime, index);
    if (projectile->state == avsp_round1_weapon_projectile.initial_state)
    {
        const AvspRound1VecS16 *offset;
        if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)
        {
            const AvspRound1WeaponChildSequenceSpec *sequence;
            if (projectile->variant >= AVSP_ROUND1_WEAPON_CHILD_VARIANT_COUNT)
                return 0;
            sequence = &avsp_round1_weapon_child_sequences[projectile->variant];
            projectile->collision_result = 0;
            projectile->active_collision = 1u;
            projectile->object_or = avsp_round1_weapon_projectile.object_or;
            projectile->presentation_index = 0u;
            projectile->presentation_count = sequence->record_count;
            projectile->state = avsp_round1_weapon_projectile.active_state;
            avsp_round1_bind_projectile_animation(projectile);
            ++runtime->player_weapon_projectile_initializations;
            return 1;
        }
        if (projectile->parent_presentation_selector >=
            AVSP_ROUND1_WEAPON_PARENT_SELECTOR_COUNT)
            return 0;
        offset = &avsp_round1_weapon_parent_selector_offsets[
            projectile->parent_presentation_selector];
        projectile->x = (short)(projectile->x +
            (projectile->facing != 0u ? -offset->x : offset->x));
        projectile->y = (short)(projectile->y + offset->y);
        projectile->z = (short)(projectile->z - 1);
        projectile->x_fp = avsp_round1_replace_fixed_high_word(
            projectile->x_fp, projectile->x);
        projectile->y_fp = avsp_round1_replace_fixed_high_word(
            projectile->y_fp, projectile->y);
        projectile->z_fp = (long)projectile->z * 65536L;
        projectile->collision_result = 0;
        projectile->active_collision = 1u;
        projectile->coordinate_mode = 0u;
        projectile->palette = 0u;
        projectile->object_or = avsp_round1_weapon_projectile.object_or;
        projectile->presentation_index = 0u;
        projectile->presentation_count =
            AVSP_ROUND1_WEAPON_PARENT_PRESENTATION_COUNT;
        projectile->progress = 0u;
        avsp_round1_bind_projectile_animation(projectile);
        projectile->state = avsp_round1_weapon_projectile.active_state;
        ++runtime->player_weapon_projectile_initializations;
        return 1;
    }
    if (projectile->state == avsp_round1_weapon_projectile.active_state)
    {
        if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)
        {
            if (projectile->animation_branch < 0)
                projectile->state = avsp_round1_weapon_projectile.emitter_state;
            if (projectile->animation_timer > 0u)
                --projectile->animation_timer;
            if (projectile->state == avsp_round1_weapon_projectile.active_state &&
                projectile->animation_timer == 0u)
            {
                if (projectile->presentation_index + 1u >=
                    projectile->presentation_count)
                    return 0;
                ++projectile->presentation_index;
                avsp_round1_bind_projectile_animation(projectile);
            }
            return 1;
        }
        if (projectile->collision_result < 0)
        {
            projectile->state = avsp_round1_weapon_projectile.emitter_state;
            projectile->child_cadence =
                avsp_round1_weapon_projectile.child_cadence_initial;
            return 1;
        }
        x_distance = (unsigned short)(projectile->x -
            runtime->camera_x_position +
            avsp_round1_weapon_projectile.x_bound_bias);
        if (x_distance > avsp_round1_weapon_projectile.x_bound_span)
        {
            projectile->state = avsp_round1_weapon_projectile.emitter_state;
            projectile->child_cadence =
                avsp_round1_weapon_projectile.child_cadence_initial;
            return 1;
        }
        y_distance = (unsigned short)(projectile->y -
            runtime->camera_z_position +
            avsp_round1_weapon_projectile.y_bound_bias);
        if (y_distance > avsp_round1_weapon_projectile.y_bound_span)
        {
            projectile->state = avsp_round1_weapon_projectile.emitter_state;
            projectile->child_cadence =
                avsp_round1_weapon_projectile.child_cadence_initial;
            return 1;
        }
        if ((unsigned short)projectile->y < (unsigned short)projectile->z)
        {
            projectile->state = avsp_round1_weapon_projectile.emitter_state;
            projectile->child_cadence =
                avsp_round1_weapon_projectile.child_cadence_initial;
            return 1;
        }
        if (!avsp_round1_weapon_angle_index(projectile->angle, &angle_index))
            return 0;
        low_index = projectile->progress & 0x0fu;
        high_index = projectile->progress >> 4;
        if (high_index >= AVSP_ROUND1_WEAPON_PARENT_HIGH_MOTION_COUNT)
            high_index = AVSP_ROUND1_WEAPON_PARENT_HIGH_MOTION_COUNT - 1u;
        low_motion = &avsp_round1_weapon_parent_motion_low[angle_index][low_index];
        high_motion = &avsp_round1_weapon_parent_motion_high[angle_index][high_index];
        projectile->x_fp += (long)
            avsp_round1_weapon_parent_base_motion[angle_index].x * 256L;
        projectile->y_fp += (long)
            avsp_round1_weapon_parent_base_motion[angle_index].y * 256L;
        projectile->x_fp += (long)(low_motion->x + high_motion->x) * 256L;
        projectile->y_fp += (long)(low_motion->y + high_motion->y) * 256L;
        projectile->x = avsp_round1_fixed_high_word(projectile->x_fp);
        projectile->y = avsp_round1_fixed_high_word(projectile->y_fp);
        ++runtime->player_weapon_projectile_motion_updates;
        if (projectile->animation_timer > 0u)
            --projectile->animation_timer;
        if (projectile->progress < 0xc0u)
            projectile->progress = (unsigned char)(projectile->progress + 8u);
        if (projectile->animation_timer == 0u)
        {
            if (projectile->presentation_index + 1u >=
                projectile->presentation_count)
            {
                if (projectile->animation_branch >= 0 ||
                    projectile->presentation_count < 2u)
                    return 0;
                projectile->presentation_index = (unsigned char)(
                    projectile->presentation_count - 2u);
                avsp_round1_bind_projectile_animation(projectile);
            }
            else
            {
                ++projectile->presentation_index;
                avsp_round1_bind_projectile_animation(projectile);
            }
        }
        if ((runtime->scheduler_frames &
                avsp_round1_parent_weapon_effect.phase_mask) ==
                avsp_round1_parent_weapon_effect.phase_expected &&
            !avsp_round1_allocate_weapon_effect(runtime, projectile,
                avsp_round1_parent_weapon_effect.variant))
            return 0;
        return 1;
    }
    if (projectile->state == avsp_round1_weapon_projectile.emitter_state)
    {
        const AvspRound1WeaponChildSpawnSpec *rows =
            projectile->collision_result < 0 ?
                avsp_round1_weapon_child_spawn_collision :
                avsp_round1_weapon_child_spawn_normal;
        if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)
            return avsp_round1_release_player_weapon_projectile(runtime,
                                                                 index);
        else
        {
            if (projectile->substate == 0u)
                projectile->substate = 2u;
            if (projectile->child_cadence > 0u)
                --projectile->child_cadence;
            if (projectile->child_cadence == 0u)
            {
                if (projectile->child_count == 0u)
                    projectile->state = avsp_round1_weapon_projectile.release_state;
                else
                {
                    unsigned int row_index = projectile->child_count - 1u;
                    --projectile->child_count;
                    if (!avsp_round1_allocate_weapon_child(runtime, projectile,
                            &rows[row_index]))
                        ++runtime->failure_count;
                    projectile->child_cadence =
                        avsp_round1_weapon_projectile.child_cadence_reload;
                }
            }
        }
        return 1;
    }
    if (projectile->state == avsp_round1_weapon_projectile.release_state)
        return avsp_round1_release_player_weapon_projectile(runtime, index);
    return 0;
}

static short avsp_round1_source_midpoint(short first, short second)
{
    short delta = (short)(second - first);
    short half = (short)(delta / 2);
    if (delta < 0 && ((unsigned short)delta & 1u) != 0u)
        --half;
    return (short)(first + half);
}

static int avsp_round1_spawn_class4e_impact(
    AvspRound1Runtime *runtime,
    const AvspRound1WeaponProjectileAllocation *projectile,
    const AvspRound1ActorCore *target,
    const AvspRound1CollisionBoxSpec *attack_box,
    const AvspBox *hurt_box,
    unsigned char variant)
{
    AvspRound1ActorCore *impact;
    short depth_delta;
    short attack_x;
    short target_x;
    short attack_y;
    short target_y;
    if (!((projectile->actor_class ==
                avsp_round1_player_weapon.child_class && variant == 1u) ||
          (projectile->actor_class ==
                avsp_round1_player_weapon.parent_class && variant == 10u)))
        return 1;
    if (variant == 1u)
        ++runtime->class4e_variant1_allocation_requests;
    else
        ++runtime->class4e_variant10_allocation_requests;
    if (runtime->class4e_impact_suppressed)
        return 1;
    impact = avsp_round1_allocate_pool_actor_preserve_presentation(runtime, 3u);
    if (impact == 0)
    {
        if (variant == 1u)
            ++runtime->class4e_variant1_allocation_failures;
        else
            ++runtime->class4e_variant10_allocation_failures;
        return 1;
    }
    depth_delta = (short)(
        (short)(target->z + (short)hurt_box->z_center) -
        (short)(projectile->z + (short)attack_box->z_center));
    attack_x = (short)(projectile->x +
        (projectile->facing ? -(short)attack_box->x_center :
                              (short)attack_box->x_center));
    target_x = (short)(target->x +
        (target->facing ? -(short)hurt_box->x_center :
                          (short)hurt_box->x_center));
    attack_y = (short)(projectile->y + (short)attack_box->y_center +
                       depth_delta);
    target_y = (short)(target->y + (short)hurt_box->y_center);
    impact->actor_class = 0x4e;
    impact->variant = variant;
    impact->state = 0u;
    impact->substate = 0u;
    impact->facing = target->source_facing_selector;
    impact->x = avsp_round1_source_midpoint(attack_x, target_x);
    impact->y = avsp_round1_source_midpoint(attack_y, target_y);
    impact->z = (short)(target->z - 1);
    impact->dispatch_entry = 0x000927f6UL;
    if (variant == 1u)
        ++runtime->class4e_variant1_allocations;
    else
        ++runtime->class4e_variant10_allocations;
    return 1;
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
    unsigned int attack_index;
    unsigned char damage;
    unsigned char impact_variant;
    unsigned long current_attack_record;
    const AvspRound1CollisionBoxSpec *box;
    if (projectile->state != avsp_round1_weapon_projectile.active_state ||
        !projectile->active_collision || !projectile->collision_registered ||
        projectile->attack_selector == 0u ||
        projectile->attack_selector >=
            AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT)
        return 1;
    current_attack_record = avsp_round1_weapon_current_attack_record(projectile);
    if (current_attack_record == 0UL)
        return 1;
    attack_index = (unsigned int)((current_attack_record -
        projectile->attack_table -
        (unsigned long)(projectile->actor_class ==
            avsp_round1_weapon_projectile.child_class ?
            avsp_round1_weapon_projectile.child_attack_relative :
            avsp_round1_weapon_projectile.parent_attack_relative)) /
        avsp_round1_weapon_projectile.attack_record_stride);
    box = (projectile->actor_class ==
            avsp_round1_weapon_projectile.parent_class ||
           projectile->actor_class ==
            avsp_round1_air_weapon_projectile.actor_class) ?
        &avsp_round1_weapon_parent_attack_boxes[attack_index] :
        &avsp_round1_weapon_child_attack_boxes[attack_index];
    impact_variant = (projectile->actor_class ==
            avsp_round1_weapon_projectile.parent_class) ?
        avsp_round1_weapon_parent_impact_variants[attack_index] :
        projectile->actor_class ==
            avsp_round1_weapon_projectile.child_class ?
        avsp_round1_weapon_child_impact_variants[attack_index] : 0u;
    damage = (projectile->actor_class ==
            avsp_round1_weapon_projectile.parent_class ||
              projectile->actor_class ==
            avsp_round1_air_weapon_projectile.actor_class) ?
        avsp_round1_weapon_projectile.parent_damage :
        avsp_round1_weapon_projectile.child_damage;
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
        const AvspRound1PresentationSpec *target_presentation;
        const AvspRound1Class1fActionRecordSpec *target_action_record;
        unsigned char current_hurt_selector;
        short health;
        signed char latch_index = projectile->collision_latch_index;
        if (target->active != 1u || target->actor_class != 0x1f ||
            target->source_field01 != 1u ||
            target->source_collision_guard6d >= 4u ||
            target->source_collision_suppress70 != 0u ||
            target->health < 0)
            continue;
        target_presentation = avsp_round1_find_class1f_presentation(
            target->animation_record);
        target_action_record = avsp_round1_find_class1f_action_record(
            target->animation_record);
        if (target->animation_record == 0u)
            continue;
        if (target_presentation == 0 && target_action_record == 0)
        {
            runtime->scheduler_failure_source_slot = target->source_slot;
            runtime->scheduler_failure_state = target->state;
            runtime->scheduler_failure_substate = target->substate;
            runtime->scheduler_failure_animation_record =
                target->animation_record;
            return 0;
        }
        current_hurt_selector = target_action_record != 0 ?
            target_action_record->hurt_selector :
            target_presentation->hurt_selector;
        if (current_hurt_selector == 0u)
            continue;
        if (latch_index >= 0)
        {
            if ((unsigned char)latch_index >=
                    sizeof(target->source_collision_latches))
                return 0;
            if (target->source_collision_latches[
                    (unsigned char)latch_index] ==
                    projectile->collision_identity)
                continue;
        }
        if (!avsp_collision_hurt_box(0x00130ac8UL,
                                     current_hurt_selector, &hurt))
            return 0;
        memset(&defender, 0, sizeof(defender));
        defender.world_x = (unsigned short)target->x;
        defender.world_y = (unsigned short)target->y;
        defender.world_z = (unsigned short)target->z;
        defender.facing = target->facing;
        if (!avsp_collision_overlap_boxes(&attacker, &attack, &defender,
                                          &hurt, 0))
            continue;
        if (latch_index >= 0)
            target->source_collision_latches[(unsigned char)latch_index] =
                projectile->collision_identity;
        projectile->collision_result = -1;
        projectile->health = -1;
        ++runtime->player_weapon_projectile_collision_writes;
        health = target->health;
        target->source_prior_health = health;
        health = (short)(health - (short)damage);
        target->health = health < 0 ? -1 : health;
        ++runtime->player_weapon_projectile_damage_writes;
        ++runtime->first_encounter.player_contacts;
        ++runtime->first_encounter.alien_damage_events;
        target->source_facing_selector = projectile->facing;
        avsp_round1_class1f_queue_projectile_reaction(
            runtime, target, target->health < 0,
            target->source_prior_health);
        if (!avsp_round1_spawn_class4e_impact(
                runtime, projectile, target, box, &hurt, impact_variant))
            return 0;
        return 1;
    }
    return 1;
}

static int avsp_round1_step_record4_pool(AvspRound1Runtime *runtime,
                                          unsigned long *hash)
{
    unsigned int slot_index;
    for (slot_index = 0u;
         slot_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++slot_index)
    {
        AvspRound1WeaponProjectileAllocation *projectile =
            &runtime->player_weapon_projectiles[slot_index];
        AvspRound1SchedulerVisit *visit;
        if (!projectile->active)
            continue;
        if ((projectile->actor_class !=
                avsp_round1_player_weapon.parent_class &&
             projectile->actor_class !=
                avsp_round1_air_weapon_projectile.actor_class &&
             projectile->actor_class !=
                avsp_round1_player_weapon.child_class) ||
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
        *hash = avsp_round1_scheduler_hash_byte(*hash, 4u);
        *hash = avsp_round1_scheduler_hash_byte(*hash,
            (unsigned char)projectile->actor_class);
        *hash = avsp_round1_scheduler_hash_byte(*hash,
            (unsigned char)slot_index);
        ++runtime->player_weapon_projectile_scheduler_updates;
        ++runtime->scheduler_dispatches;
        if (!avsp_round1_step_weapon_projectile(runtime, slot_index))
        {
            runtime->scheduler_failure_code = 2u;
            ++runtime->failure_count;
            return 0;
        }
    }
    return 1;
}

static int avsp_round1_step_record4_collision(AvspRound1Runtime *runtime)
{
    unsigned int slot_index;
    for (slot_index = 0u;
         slot_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++slot_index)
    {
        AvspRound1WeaponProjectileAllocation *projectile =
            &runtime->player_weapon_projectiles[slot_index];
        if (projectile->active &&
            !avsp_round1_projectile_collision_pass(runtime, projectile))
        {
            runtime->scheduler_failure_code = 3u;
            ++runtime->failure_count;
            return 0;
        }
    }
    return 1;
}

static int avsp_round1_begin_empty_effect(AvspRound1Runtime *runtime)
{
    AvspRound1ActorCore *actor =
        avsp_round1_allocate_pool_actor_preserve_position_residue(runtime, 3u);
    if (actor == 0)
    {
        ++runtime->player_weapon_empty_auxiliary_allocation_failures;
        return 0;
    }
    actor->actor_class = 0x10;
    actor->variant = avsp_round1_player_weapon.empty_effect_variant;
    actor->state = 0u;
    actor->substate = 0u;
    actor->x = runtime->player.x;
    actor->y = runtime->player.y;
    actor->source_x_fp = (long)actor->x * 65536L +
        (unsigned short)actor->source_x_fp;
    actor->source_y_fp = (long)actor->y * 65536L +
        (unsigned short)actor->source_y_fp;
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
    if (actor->variant != avsp_round1_player_weapon.empty_effect_variant)
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
        actor->source_x_fp = (long)actor->x * 65536L +
            (unsigned short)actor->source_x_fp;
        actor->source_y_fp = (long)actor->y * 65536L +
            (unsigned short)actor->source_y_fp;
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
        {
            actor->y = (short)(actor->y + 4);
            actor->source_y_fp += 4L * 65536L;
        }
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

int avsp_round1_is_weapon_impact_actor(const AvspRound1ActorCore *actor)
{
    return actor != 0 && actor->active && actor->type == 24u &&
        actor->actor_class == 0x4e &&
        (actor->variant == 1u || actor->variant == 10u);
}

int avsp_round1_is_weapon_parent_projectile(
    const AvspRound1WeaponProjectileAllocation *projectile)
{
    return projectile != 0 && projectile->active &&
        (projectile->actor_class == avsp_round1_player_weapon.parent_class ||
         projectile->actor_class ==
            avsp_round1_air_weapon_projectile.actor_class);
}

int avsp_round1_is_weapon_child_projectile(
    const AvspRound1WeaponProjectileAllocation *projectile)
{
    return projectile != 0 && projectile->active &&
        projectile->actor_class == avsp_round1_player_weapon.child_class;
}

static void avsp_round1_bind_player_special_record(
    AvspRound1Runtime *runtime, unsigned char index)
{
    const AvspRound1AnimationStateSpec *record =
        &avsp_round1_player_special_records[index];
    runtime->player_special_animation_index = index;
    runtime->player_special_animation_timer =
        avsp_round1_player_special_visible_durations[index];
    runtime->player_special_animation_branch = record->branch;
    runtime->player.source_action = runtime->player_special_phase;
    runtime->player.substate = runtime->player_special_phase;
    runtime->player.animation_record = record->animation_record;
    runtime->player.assembly = record->assembly;
    runtime->player.hurt_selector = record->hurt_selector;
    runtime->player.attack_selector = record->attack_selector;
    runtime->player_locomotion_action = runtime->player_special_phase;
}

static int avsp_round1_allocate_player_special_class3d(
    AvspRound1Runtime *runtime, AvspRound1ActorCore *owner,
    unsigned char event)
{
    AvspRound1ActorCore *effect;
    ++runtime->class3d_allocation_requests;
    effect = avsp_round1_allocate_pool_actor_preserve_y(runtime, 3u);
    if (effect == 0)
    {
        ++runtime->class3d_allocation_failures;
        return 1;
    }
    effect->actor_class = avsp_round1_player_special.class3d_class;
    effect->variant = event;
    effect->x = owner->x;
    effect->z = owner->z;
    effect->source_direction = runtime->player.facing;
    ++runtime->class3d_allocations;
    return 1;
}

static int avsp_round1_allocate_player_special_class4b(
    AvspRound1Runtime *runtime)
{
    AvspRound1ActorCore *effect;
    ++runtime->class4b_allocation_requests;
    effect = avsp_round1_allocate_pool_actor(runtime, 3u);
    if (effect == 0)
    {
        ++runtime->class4b_allocation_failures;
        return 1;
    }
    effect->actor_class = avsp_round1_player_special.class4b_class;
    effect->variant = 0u;
    effect->x = runtime->player.x;
    effect->y = runtime->player.y;
    effect->z = runtime->player.z;
    effect->facing = runtime->player.facing;
    effect->source_target_low = 0x8380u;
    runtime->player_special_class4b_source_slot =
        (unsigned short)effect->source_slot;
    runtime->player_special_class4b_event_latch = 0xffu;
    ++runtime->class4b_allocations;
    return avsp_round1_allocate_player_special_class3d(runtime, effect, 0u);
}

static int avsp_round1_player_special_guard(
    const AvspRound1Runtime *runtime, unsigned char current,
    unsigned char previous)
{
    unsigned char new_buttons = (unsigned char)(current &
        (unsigned char)~previous & 0x70u);
    unsigned char count = 0u;
    unsigned char bits = new_buttons;
    while (bits != 0u)
    {
        count = (unsigned char)(count + (bits & 1u));
        bits >>= 1;
    }
    if (runtime->player_special_attack_active ||
        runtime->player.health == 0 ||
        runtime->player_special_owner_contact != 0u)
        return 0;
    if (count >= 2u)
        return 1;
    if ((current & AVSP_ROUND1_INPUT_BUTTON1) != 0u &&
        (previous & AVSP_ROUND1_INPUT_BUTTON1) != 0u &&
        (new_buttons & (AVSP_PW_INPUT_ATTACK |
                        AVSP_ROUND1_INPUT_BUTTON3)) != 0u)
        return 1;
    return (current & AVSP_ROUND1_INPUT_BUTTON3) != 0u &&
        (previous & AVSP_ROUND1_INPUT_BUTTON3) != 0u &&
        (new_buttons & AVSP_ROUND1_INPUT_BUTTON1) != 0u;
}

static void avsp_round1_begin_player_special(AvspRound1Runtime *runtime)
{
    runtime->player_special_attack_active = 1u;
    runtime->player_special_attack_elapsed = 0u;
    runtime->player_special_phase = avsp_round1_player_special.entry_action;
    runtime->player_special_animation_timer = 0u;
    runtime->player_special_animation_branch = 0;
    runtime->player_special_animation_index = 0u;
    runtime->player_special_class4b_source_slot = 0u;
    runtime->player_special_class4b_event_latch = 0xffu;
    runtime->player_special_owner_contact = 0u;
    runtime->player_weapon_active = 0u;
    runtime->player_weapon_cleanup_pending = 0u;
    runtime->player_weapon_return_pending = 0u;
    runtime->player_weapon_recovery_pending = 0u;
    runtime->player_jump_active = 0u;
    runtime->player_jump_cleanup_pending = 0u;
    runtime->player_stop_ticks = 0u;
    runtime->player_was_directional = 0u;
    ++runtime->player_special_attack_entries;
}

static int avsp_round1_step_player_special(AvspRound1Runtime *runtime)
{
    AvspRound1ActorCore *class4b;
    const AvspRound1AnimationStateSpec *record;
    if (!runtime->player_special_attack_active)
        return 0;
    if (runtime->player_special_phase ==
            avsp_round1_player_special.entry_action)
    {
        if (runtime->player_special_attack_elapsed == 0u)
        {
            runtime->player.source_action =
                avsp_round1_player_special.entry_action;
            runtime->player.substate = 0u;
            runtime->player_locomotion_action =
                avsp_round1_player_special.entry_action;
            runtime->player_special_attack_elapsed = 1u;
            return 1;
        }
        runtime->player_special_phase =
            avsp_round1_player_special.startup_action;
        runtime->player_special_attack_elapsed = 0u;
        avsp_round1_bind_player_special_record(runtime, 0u);
        return 1;
    }
    if (runtime->player_special_animation_branch < 0)
    {
        short health = runtime->player_action.health;
        if (health < (short)avsp_round1_player_special.health_cost)
            health = 0;
        else
            health = (short)(health -
                avsp_round1_player_special.health_cost);
        runtime->player_action.health = health;
        runtime->player.health = health;
        runtime->player_special_attack_active = 0u;
        runtime->player_special_phase =
            avsp_round1_player_special.return_action;
        runtime->player_locomotion_action =
            avsp_round1_player_special.return_action;
        ++runtime->player_special_health_debits;
        ++runtime->player_special_completions;
        return 0;
    }
    class4b = avsp_round1_find_pool_source_actor(runtime, 3u,
        runtime->player_special_class4b_source_slot);
    if (runtime->player_special_phase ==
            avsp_round1_player_special.active_action && class4b != 0 &&
        (unsigned char)class4b->animation_branch !=
            runtime->player_special_class4b_event_latch)
    {
        runtime->player_special_class4b_event_latch =
            (unsigned char)class4b->animation_branch;
        if (!avsp_round1_allocate_player_special_class3d(runtime, class4b,
                runtime->player_special_class4b_event_latch))
            return 0;
    }
    if (runtime->player_special_animation_timer == 0u)
        return 0;
    --runtime->player_special_animation_timer;
    ++runtime->player_special_attack_elapsed;
    if (runtime->player_special_animation_timer != 0u)
        return 1;
    if (runtime->player_special_animation_index + 1u >=
            AVSP_ROUND1_PLAYER_SPECIAL_PRESENTATION_COUNT)
        return 0;
    avsp_round1_bind_player_special_record(runtime,
        (unsigned char)(runtime->player_special_animation_index + 1u));
    record = &avsp_round1_player_special_records[
        runtime->player_special_animation_index];
    if (record->attack_selector ==
            avsp_round1_player_special.contact_attack_selector &&
        runtime->player_special_phase !=
            avsp_round1_player_special.active_action)
    {
        runtime->player_special_phase =
            avsp_round1_player_special.active_action;
        runtime->player.source_action = runtime->player_special_phase;
        runtime->player.substate = runtime->player_special_phase;
        runtime->player_locomotion_action = runtime->player_special_phase;
        runtime->player_special_attack_contact_ready = 1u;
        runtime->player_special_audio_events += 2u;
        runtime->player_special_audio_command =
            avsp_round1_player_special.audio_command_1;
        if (!avsp_round1_allocate_player_special_class4b(runtime))
            return 0;
    }
    return 1;
}

int avsp_round1_player_native_presentation_active(
    const AvspRound1Runtime *runtime)
{
    return runtime != 0 && (runtime->player_special_attack_active ||
        runtime->player_jump_active ||
        runtime->player_weapon_active ||
        runtime->player.source_action ==
            avsp_round1_player_weapon.return_action);
}

static void avsp_round1_tick_player_resource(AvspRound1Runtime *runtime)
{
    if (runtime->player_resource >=
        avsp_round1_player_weapon.resource_capacity)
    {
        runtime->player_resource_depleted = 0u;
        return;
    }
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
            runtime->player_resource =
                avsp_round1_player_weapon.resource_capacity;
    }
}

static void avsp_round1_begin_player_weapon(AvspRound1Runtime *runtime)
{
    runtime->player_weapon_active = 1u;
    runtime->player_weapon_empty =
        avsp_round1_player_weapon.empty_dispatch_uses_depleted_latch ?
            runtime->player_resource_depleted :
            (unsigned char)(runtime->player_resource <
                avsp_round1_player_weapon.resource_debit);
    runtime->player_weapon_tick = 0u;
    runtime->player_weapon_empty_timer =
        avsp_round1_player_weapon.empty_timer_initial;
    runtime->player_weapon_cleanup_pending = 0u;
    avsp_round1_player_weapon_target(runtime,
        &runtime->player_weapon_presentation_selector,
        &runtime->player_weapon_target_angle);
    runtime->player_stop_ticks = 0u;
    runtime->player_was_directional = 0u;
    runtime->player_cleanup_pending = 0u;
    ++runtime->player_weapon_entries;
    if (runtime->player_weapon_empty)
    {
        runtime->player_resource_depleted = 1u;
    }
}

static int avsp_round1_begin_player_air_weapon(AvspRound1Runtime *runtime,
                                                unsigned short input_mask)
{
    int allocated;
    if (runtime->player_resource < avsp_round1_player_weapon.resource_debit)
        return 1;
    runtime->player_jump_phase = 0x0406u;
    runtime->player.source_action = 0x0406u;
    runtime->player_jump_collision_selector =
        avsp_round1_air_weapon_projectile.player_collision_selector;
    if (!avsp_round1_bind_player_jump_sequence(runtime, 18u))
        return 0;
    allocated = avsp_round1_allocate_player_air_weapon_projectile(
        runtime, input_mask);
    if (allocated)
    {
        runtime->player_resource = (unsigned char)(
            runtime->player_resource -
            avsp_round1_player_weapon.resource_debit);
        runtime->player_resource_recharge =
            avsp_round1_player_weapon.recharge_after_success;
        ++runtime->player_weapon_resource_debits;
    }
    ++runtime->player_air_weapon_entries;
    return 1;
}

static int avsp_round1_step_player_weapon(AvspRound1Runtime *runtime,
                                          unsigned char weapon_pressed,
                                          unsigned char weapon_edge)
{
    const AvspRound1PlayerWeaponFrameSpec *frame;
    if (!runtime->player_weapon_active)
        return 0;
    if (runtime->player_weapon_empty &&
        runtime->player_weapon_tick ==
            avsp_round1_player_weapon.empty_effect_allocation_tick)
    {
        ++runtime->player_weapon_empty_auxiliary_requests;
        avsp_round1_begin_empty_effect(runtime);
    }
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
        if (runtime->player_weapon_tick == 0u &&
            avsp_round1_player_weapon.
                empty_entry_preserves_current_presentation)
        {
            runtime->player.source_action =
                avsp_round1_player_weapon.empty_entry_action;
            runtime->player.substate =
                avsp_round1_player_weapon.empty_entry_action;
            runtime->player_locomotion_action =
                avsp_round1_player_weapon.empty_entry_action;
        }
        else
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
        if (runtime->player_weapon_tick == 1u)
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
        if (runtime->player_weapon_tick == 2u)
        {
            ++runtime->player_weapon_attempts_total;
            avsp_round1_allocate_player_weapon_projectile(runtime);
        }
        if (runtime->player_weapon_presentation_selector < 4u ||
            runtime->player_weapon_presentation_selector > 7u)
        {
            ++runtime->failure_count;
            return 0;
        }
        frame = &avsp_round1_player_weapon_frames[
            runtime->player_weapon_presentation_selector - 4u][
            runtime->player_weapon_tick];
        avsp_round1_bind_player_weapon_frame(runtime, frame);
        if (runtime->player_weapon_tick == 19u)
        {
            runtime->player_weapon_active = 0u;
            runtime->player_weapon_cleanup_pending = 1u;
            ++runtime->player_weapon_completions;
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
           runtime->entry.started &&
           runtime->entry.dependencies_seeded)) ||
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
    if (!avsp_round1_spawn_coffee_scene_records(runtime))
    {
        runtime->scheduler_failure_code = 23u;
        ++runtime->failure_count;
        return 0;
    }
    if (!avsp_round1_spawn_coffee_shop_obstacle(runtime))
    {
        runtime->scheduler_failure_code = 19u;
        ++runtime->failure_count;
        return 0;
    }
    if (!avsp_round1_step_recurring_controller(runtime))
    {
        runtime->scheduler_failure_code = 15u;
        ++runtime->failure_count;
        return 0;
    }
    runtime->class1f_phase_guard_counter =
        runtime->first_encounter.source_phase_counter;
    if (!avsp_round1_step_record4_pool(runtime, &hash))
        return 0;
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
            if (actor->type == 24u && actor->actor_class == 0x49)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_air_weapon_effect(runtime,
                        &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 16u;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 16u && actor->actor_class == 0x06)
            {
                int type16_result;
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                type16_result = avsp_round1_step_type16_projectile(
                    runtime, &runtime->pools[pool_index], actor);
                if (type16_result == 0)
                {
                    runtime->scheduler_failure_code = 29u;
                    runtime->scheduler_failure_source_slot =
                        actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    runtime->scheduler_failure_substate = actor->substate;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 20u && actor->actor_class == 0x0a)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_coffee_shop_obstacle(
                        runtime, &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 20u;
                    runtime->scheduler_failure_source_slot = actor->source_slot;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 20u && actor->actor_class == 0x01)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class01(
                        runtime, &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 24u;
                    runtime->scheduler_failure_source_slot = actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 20u && actor->actor_class == 0x02)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class02(
                        runtime, &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 25u;
                    runtime->scheduler_failure_source_slot = actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 36u && actor->actor_class == 0x05)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_coffee_shop_obstacle_child(
                        runtime, &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 21u;
                    runtime->scheduler_failure_source_slot = actor->source_slot;
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
            if (actor->type == 24u && actor->actor_class == 0x43)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class43(runtime,
                        &runtime->pools[pool_index], actor, slot_index))
                {
                    runtime->scheduler_failure_code = 34u;
                    runtime->scheduler_failure_source_slot =
                        actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 24u && actor->actor_class == 0x45)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class45(runtime,
                        &runtime->pools[pool_index], actor, slot_index))
                {
                    runtime->scheduler_failure_code = 22u;
                    runtime->scheduler_failure_source_slot =
                        actor->source_slot;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 24u && actor->actor_class == 0x47)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class47(runtime,
                        &runtime->pools[pool_index], actor, slot_index))
                {
                    runtime->scheduler_failure_code = 26u;
                    runtime->scheduler_failure_source_slot =
                        actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 24u && actor->actor_class == 0x4b)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class4b(runtime,
                        &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 27u;
                    runtime->scheduler_failure_source_slot =
                        actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    ++runtime->failure_count;
                    return 0;
                }
                continue;
            }
            if (actor->type == 24u && actor->actor_class == 0x3d)
            {
                ++actor->scheduler_updates;
                ++runtime->scheduler_dispatches;
                if (!avsp_round1_step_class3d(runtime,
                        &runtime->pools[pool_index], actor))
                {
                    runtime->scheduler_failure_code = 28u;
                    runtime->scheduler_failure_source_slot =
                        actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
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
            if (actor->type == 12u && actor->actor_class == 0x1f)
            {
                int class1f_result = 1;
                AvspRound1Class1fTransitionRuntime *initial_air_transition =
                    avsp_round1_find_class1f_transition(runtime,
                                                        actor->source_slot);
                int initial_transition =
                    ((actor->handler_updates == 0u &&
                      actor->state == 0x0200u &&
                      (actor->substate == 0x1000u ||
                       actor->substate == 0x1200u ||
                       actor->substate == 0x1400u)) ||
                     (actor->state == 0x0200u &&
                      (actor->substate == 0x1000u ||
                       actor->substate == 0x1200u) &&
                      actor->transition_timer != 0u) ||
                     (actor->state == 0x0200u &&
                      initial_air_transition != 0 &&
                      (actor->substate == 0x1400u ||
                       actor->substate == 0x1402u ||
                       actor->substate == 0x1404u ||
                       actor->substate == 0x1406u ||
                       actor->substate == 0x1408u)));
                if (actor->source_projectile_reaction_pending != 0u)
                {
                    unsigned char pending =
                        actor->source_projectile_reaction_pending;
                    actor->source_projectile_reaction_pending = 0u;
                    if (!avsp_round1_class1f_consume_projectile_reaction(
                            runtime, actor, pending))
                    {
                        runtime->scheduler_failure_code = 17u;
                        runtime->scheduler_failure_source_slot =
                            actor->source_slot;
                        runtime->scheduler_failure_state = actor->state;
                        runtime->scheduler_failure_substate = actor->substate;
                        runtime->scheduler_failure_animation_record =
                            actor->animation_record;
                        ++runtime->failure_count;
                        return 0;
                    }
                }
                else if (avsp_round1_class1f_reaction_active(actor))
                {
                    if (!avsp_round1_class1f_step_reaction(runtime, actor))
                    {
                        runtime->scheduler_failure_code = 17u;
                        runtime->scheduler_failure_source_slot =
                            actor->source_slot;
                        runtime->scheduler_failure_state = actor->state;
                        runtime->scheduler_failure_substate = actor->substate;
                        runtime->scheduler_failure_animation_record =
                            actor->animation_record;
                        ++runtime->failure_count;
                        return 0;
                    }
                }
                else if (initial_transition)
                {
                    if (!avsp_round1_step_initial_class1f(runtime, actor))
                    {
                        runtime->scheduler_failure_code = 9u;
                        runtime->scheduler_failure_source_slot =
                            actor->source_slot;
                        runtime->scheduler_failure_state = actor->state;
                        runtime->scheduler_failure_substate = actor->substate;
                        runtime->scheduler_failure_animation_record =
                            actor->animation_record;
                        ++runtime->failure_count;
                        return 0;
                    }
                }
                else if (actor->source_hitstop != 0u)
                {
                    --actor->source_hitstop;
                    ++runtime->class1f_hitstop_updates;
                }
                else
                {
                    class1f_result = avsp_round1_step_class1f_source_action(
                        runtime, &runtime->pools[pool_index], actor);
                    if (class1f_result == 0)
                    {
                        runtime->scheduler_failure_code = 15u;
                        runtime->scheduler_failure_source_slot =
                            actor->source_slot;
                        runtime->scheduler_failure_state = actor->state;
                        runtime->scheduler_failure_substate = actor->substate;
                        runtime->scheduler_failure_animation_record =
                            actor->animation_record;
                        ++runtime->failure_count;
                        return 0;
                    }
                    if (class1f_result == 2 || class1f_result == 3)
                    {
                        ++runtime->actor_handler_dispatches;
                        ++runtime->scheduler_dispatches;
                        continue;
                    }
                }
                {
                    const AvspRound1Class1fActionRecordSpec *action_record =
                        avsp_round1_find_class1f_action_record(
                            actor->animation_record);
                    presentation = avsp_round1_find_class1f_presentation(
                        actor->animation_record);
                    actor->hurt_selector = actor->source_a5;
                    actor->attack_selector = actor->source_a6;
                    if (presentation != 0)
                    {
                        if (action_record == 0)
                            actor->assembly = presentation->assembly;
                    }
                    if (action_record == 0 && presentation == 0)
                    {
                        runtime->scheduler_failure_code = 10u;
                        runtime->scheduler_failure_source_slot =
                            actor->source_slot;
                        runtime->scheduler_failure_state = actor->state;
                        runtime->scheduler_failure_substate = actor->substate;
                        runtime->scheduler_failure_animation_record =
                            actor->animation_record;
                        ++runtime->failure_count;
                        return 0;
                    }
                }
                if (actor->active &&
                    !avsp_round1_class1f_reaction_active(actor) &&
                    !avsp_round1_class1f_melee_collision(runtime, actor))
                {
                    runtime->scheduler_failure_code = 18u;
                    runtime->scheduler_failure_source_slot = actor->source_slot;
                    runtime->scheduler_failure_state = actor->state;
                    runtime->scheduler_failure_substate = actor->substate;
                    runtime->scheduler_failure_animation_record =
                        actor->animation_record;
                    ++runtime->failure_count;
                    return 0;
                }
                if (runtime->first_encounter.dynamic_spawned &&
                    actor->source_slot ==
                        runtime->first_encounter.actor_source_slot)
                {
                    runtime->first_encounter.initialized = 1u;
                    runtime->first_encounter.encounter_state =
                        AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE;
                    runtime->first_encounter.rng_seed = runtime->rng_seed;
                    avsp_round1_first_encounter_cache_presentation(
                        &runtime->first_encounter, actor);
                }
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
    avsp_round1_refresh_collision_registration(runtime);
    if (!avsp_round1_step_class1f_player_collision(runtime))
    {
        runtime->scheduler_failure_code = 29u;
        ++runtime->failure_count;
        return 0;
    }
    if (!avsp_round1_step_record4_collision(runtime))
        return 0;
    for (slot_index = 0u;
         slot_index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++slot_index)
        if (runtime->player_weapon_projectiles[slot_index].active &&
            runtime->player_weapon_projectiles[slot_index].state !=
                avsp_round1_weapon_projectile.initial_state)
            runtime->player_weapon_projectiles[slot_index]
                .collision_registration_pending = 0u;
    runtime->scheduler_order_hash = hash;
    ++runtime->scheduler_frames;
    return 1;
}

void avsp_round1_first_encounter_view(
    const AvspRound1Runtime *runtime,
    AvspRound1FirstEncounterView *view)
{
    const AvspRound1FirstEncounterRuntime *encounter;
    if (runtime == 0 || view == 0)
        return;
    memset(view, 0, sizeof(*view));
    encounter = &runtime->first_encounter;
    view->initialized = encounter->initialized;
    view->encounter_state = encounter->encounter_state;
    view->route_unlocked = encounter->route_unlocked;
    view->continued_after_unlock = encounter->continued_after_unlock;
    view->player_contact = encounter->player_contact;
    view->alien_contact = encounter->alien_contact;
    view->player_damage = encounter->player_damage;
    view->alien_damage = encounter->alien_damage;
    view->semantic_hit = encounter->semantic_hit;
    view->semantic_ko = encounter->semantic_ko;
    view->health_before = encounter->health_before;
    view->health_after = encounter->health_after;
    view->alien = encounter->presentation;
    view->reaction = encounter->reaction.actor;
}

int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime)
{
    return runtime != 0 && runtime->head_canary == AVSP_ROUND1_CANARY_HEAD &&
        runtime->tail_canary == AVSP_ROUND1_CANARY_TAIL;
}

static int avsp_round1_apply_coffee_stage_setup(AvspRound1Runtime *runtime)
{
    const AvspRound1CoffeeStageSetupSpec *spec =
        &avsp_round1_coffee_stage_setup;
    short stage;
    short population_adjustment = 0;
    unsigned char random;
    if (runtime->coffee_stage_setup_complete)
        return 1;
    if (runtime->route_state != spec->route_state ||
        runtime->player_variant != spec->player_variant ||
        runtime->source_stage_record_type != spec->stage_record_type ||
        runtime->rng_seed != spec->rng_before)
        return 0;
    stage = spec->stage_row_value;
    if (spec->population_selector >= spec->population_mid_threshold)
        population_adjustment = spec->population_mid_adjustment;
    if (spec->population_selector >= spec->population_high_threshold)
        population_adjustment = spec->population_high_adjustment;
    stage = (short)(stage + population_adjustment);
    stage = (short)(stage + spec->variant_adjustment);
    random = avsp_round1_source_rng(runtime);
    if ((((unsigned short)random & 0x003eu) !=
            spec->random_masked_index) || runtime->rng_seed != spec->rng_after)
        return 0;
    stage = (short)(stage + spec->random_adjustment);
    stage = (short)(stage + spec->post_adjustment);
    if (stage < spec->lower_bound)
        stage = spec->lower_bound;
    else if (stage > spec->upper_bound)
        stage = spec->upper_bound;
    if (stage != spec->stage_parameter_after)
        return 0;
    runtime->source_stage_parameter = (unsigned short)stage;
    runtime->coffee_stage_setup_complete = 1u;
    ++runtime->coffee_stage_setup_calls;
    return 1;
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
    runtime->collision_identity_counter = 0x25u;
    runtime->player_variant = 1u;
    runtime->source_stage_record_type = 0x1cu;
    runtime->player.active = 1u;
    runtime->player.actor_class = 0;
    runtime->player.type = 0u;
    runtime->player.state = 0u;
    runtime->player.substate = 0u;
    runtime->player.health = 0;
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
    runtime->entry_controller.active = 1u;
    runtime->entry_controller.actor_class = 1;
    runtime->entry_controller.type = 32u;
    runtime->entry_controller.state =
        avsp_round1_recurring_spawn.initial_state;
    runtime->entry_controller.substate = 0u;
    runtime->entry_controller.source_slot = 0x00ffd180UL;
    runtime->entry_controller.x = 9;
    runtime->first_encounter.source_spawn_timer =
        avsp_round1_recurring_spawn.spawn_timer_initial;
    runtime->first_encounter.source_intro_timer =
        avsp_round1_recurring_spawn.intro_timer_initial;
    runtime->first_encounter.source_field46 =
        avsp_round1_recurring_spawn.field46_initial;
    runtime->first_encounter.source_field48 =
        avsp_round1_recurring_spawn.field48_initial;
    runtime->first_encounter.source_camera_bound =
        avsp_round1_recurring_spawn.source_camera_bound_initial;
    runtime->first_encounter.source_spawn_limit =
        avsp_round1_recurring_spawn.limit_table[1];
    runtime->first_encounter.source_spawn_index =
        avsp_round1_recurring_spawn.spawn_index_initial;
    runtime->first_encounter.source_phase_counter =
        avsp_round1_recurring_spawn.phase_initial;
    runtime->first_encounter.source_intro_gate = 0xffu;
    runtime->first_encounter.source_controller_initialized = 1u;
    runtime->coffee_scene_active_flag = 1u;
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
    runtime->player.animation_timer = 0x0fffu;
    runtime->player.animation_branch = (short)0x8000u;
    runtime->player.health = AVSP_ROUND1_PLAYER_HEALTH;
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
    if (runtime->route_state != AVSP_ROUND1_ROUTE_ENTRY_STATE)
        return 0;
    if (!runtime->entry.dependencies_seeded)
    {
        if (!avsp_round1_seed_first_segment_dependencies(runtime) ||
            !avsp_round1_apply_coffee_stage_setup(runtime))
        {
            ++runtime->failure_count;
            return 0;
        }
        runtime->entry.dependencies_seeded = 1u;
        step = &avsp_round1_entry_steps[runtime->entry.step_index];
        if (step->kind != AVSP_ROUND1_ENTRY_SET_POSITION ||
            runtime->entry.script_cursor != step->cursor)
        {
            ++runtime->failure_count;
            return 0;
        }
        runtime->entry.script_cursor = step->next_cursor;
        ++runtime->entry.step_index;
        runtime->player.x = (short)step->arg0;
        runtime->player.y = (short)step->arg1;
        runtime->player.z = (short)step->arg1;
        runtime->entry.animation_c0 = 2u;
        return avsp_round1_entry_valid(runtime);
    }
    if (!avsp_round1_spawn_first_entry(runtime))
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
            if (runtime->entry.step_index >= AVSP_ROUND1_ENTRY_STEP_COUNT ||
                avsp_round1_entry_steps[runtime->entry.step_index].kind !=
                    AVSP_ROUND1_ENTRY_DWELL)
                return avsp_round1_entry_valid(runtime);
        }
        else
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

static void avsp_round1_player_hit_input_history(
    AvspRound1Runtime *runtime, unsigned short input_mask)
{
    unsigned int index;
    unsigned short direction = (unsigned short)(input_mask &
        (AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT |
         AVSP_PW_INPUT_UP | AVSP_PW_INPUT_DOWN));
    runtime->player_action.current_mask = input_mask;
    runtime->player_action.input_edges = (unsigned short)(input_mask &
        (unsigned short)~runtime->player_action.previous_mask);
    if ((runtime->player_action.input_edges & AVSP_PW_INPUT_ATTACK) != 0u)
        ++runtime->player_action.rejected_attack_edges;
    for (index = AVSP_PW_DIRECTION_LATENCY - 1u; index > 0u; --index)
        runtime->player_action.direction_history[index] =
            runtime->player_action.direction_history[index - 1u];
    runtime->player_action.direction_history[0] = direction;
    runtime->player_action.previous_mask = input_mask;
}

static void avsp_round1_step_player_hit_animation(
    AvspRound1Runtime *runtime)
{
    if (runtime->player.animation_timer == 0u)
    {
        ++runtime->failure_count;
        return;
    }
    --runtime->player.animation_timer;
    if (runtime->player.animation_timer == 0u)
    {
        if (runtime->player.animation_branch != (short)-32768)
        {
            ++runtime->failure_count;
            return;
        }
        runtime->player.animation_timer =
            avsp_round1_player_hit.hit_record.timer;
    }
    runtime->player_hit_animation_timer = runtime->player.animation_timer;
}

static int avsp_round1_step_player_hit(AvspRound1Runtime *runtime,
                                       unsigned short input_mask)
{
    short proposed_x;
    short resolved_x;
    unsigned char weapon_pressed;
    unsigned char jump_pressed;
    unsigned char special_buttons;
    avsp_round1_player_hit_input_history(runtime, input_mask);
    weapon_pressed = (unsigned char)(
        (input_mask & AVSP_ROUND1_INPUT_BUTTON1) != 0u);
    jump_pressed = (unsigned char)(
        (input_mask & AVSP_ROUND1_INPUT_BUTTON3) != 0u);
    special_buttons = (unsigned char)(input_mask &
        (AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_ATTACK |
         AVSP_ROUND1_INPUT_BUTTON3));

    if (runtime->player_hit_phase == AVSP_ROUND1_PLAYER_HIT_ENTRY)
    {
        runtime->player_hit_phase = AVSP_ROUND1_PLAYER_HIT_SHAKE;
        runtime->player_hit_shake_remaining =
            avsp_round1_player_hit.shake_count;
        runtime->player.substate = avsp_round1_player_hit.shake_substate;
        runtime->player.source_action =
            avsp_round1_player_hit.shake_substate;
        runtime->player_action.source_action =
            avsp_round1_player_hit.shake_substate;
        avsp_round1_bind_player_hit_record(
            runtime, &avsp_round1_player_hit.hit_record);
        runtime->player_hit_audio_latched = 1u;
        runtime->player_hit_audio_command =
            avsp_round1_player_hit.audio_command;
        ++runtime->player_hit_audio_events;
        ++runtime->player_hit_phase_transitions;
    }
    else if (runtime->player_hit_phase == AVSP_ROUND1_PLAYER_HIT_SHAKE)
    {
        unsigned int index = runtime->player_hit_shake_remaining;
        short delta;
        if (index == 0u || index >= AVSP_ROUND1_PLAYER_HIT_SHAKE_COUNT)
        {
            ++runtime->failure_count;
            return 0;
        }
        delta = avsp_round1_player_hit.shake_table[index];
        if (runtime->player_hit_reaction_side)
            delta = (short)-delta;
        runtime->player_hit_x_fp += (long)delta * 65536L;
        runtime->player_hit_shake_index = (unsigned char)index;
        --runtime->player_hit_shake_remaining;
        ++runtime->player_hit_shake_updates;
        if (runtime->player_hit_shake_remaining == 0u)
        {
            runtime->player_hit_phase = AVSP_ROUND1_PLAYER_HIT_MOTION;
            runtime->player.substate =
                avsp_round1_player_hit.motion_substate;
            runtime->player.source_action =
                avsp_round1_player_hit.motion_substate;
            runtime->player_action.source_action =
                avsp_round1_player_hit.motion_substate;
            runtime->player_hit_x_velocity =
                avsp_round1_player_hit.x_velocity;
            runtime->player_hit_x_acceleration =
                avsp_round1_player_hit.x_acceleration;
            avsp_round1_step_player_hit_animation(runtime);
            ++runtime->player_hit_phase_transitions;
        }
    }
    else if (runtime->player_hit_phase == AVSP_ROUND1_PLAYER_HIT_MOTION)
    {
        long velocity = runtime->player_hit_x_velocity;
        if (velocity == 0L)
        {
            runtime->player_hit_phase = AVSP_ROUND1_PLAYER_HIT_RETURN;
            runtime->player.substate =
                avsp_round1_player_hit.return_substate;
            runtime->player.source_action =
                avsp_round1_player_hit.return_substate;
            runtime->player_action.source_action =
                avsp_round1_player_hit.return_substate;
            runtime->player_action.facing = (short)(
                runtime->player_hit_reaction_side ^ 1u);
            runtime->player.facing =
                (unsigned char)runtime->player_action.facing;
            avsp_round1_bind_player_hit_record(
                runtime, &avsp_round1_player_hit.return_record);
            ++runtime->player_hit_phase_transitions;
        }
        else
        {
            if (!runtime->player_hit_reaction_side)
                velocity = -velocity;
            runtime->player_hit_x_fp += velocity;
            runtime->player_hit_x_velocity +=
                runtime->player_hit_x_acceleration;
            ++runtime->player_hit_motion_updates;
            if (runtime->player_hit_x_velocity < 0L)
            {
                runtime->player_hit_phase = AVSP_ROUND1_PLAYER_HIT_RETURN;
                runtime->player.substate =
                    avsp_round1_player_hit.return_substate;
                runtime->player.source_action =
                    avsp_round1_player_hit.return_substate;
                runtime->player_action.source_action =
                    avsp_round1_player_hit.return_substate;
                runtime->player_action.facing = (short)(
                    runtime->player_hit_reaction_side ^ 1u);
                runtime->player.facing =
                    (unsigned char)runtime->player_action.facing;
                avsp_round1_bind_player_hit_record(
                    runtime, &avsp_round1_player_hit.return_record);
                ++runtime->player_hit_phase_transitions;
            }
            else
                avsp_round1_step_player_hit_animation(runtime);
        }
    }
    else if (runtime->player_hit_phase == AVSP_ROUND1_PLAYER_HIT_RETURN)
    {
        runtime->player_hit_active = 0u;
        runtime->player_hit_phase = 0u;
        runtime->player_hit_invulnerability =
            avsp_round1_player_hit.invulnerability;
        runtime->player.state = avsp_round1_player_hit.control_outer_state;
        runtime->player.substate = 0u;
        runtime->player.source_action = 0u;
        runtime->player_action.state = AVSP_PW_STATE_CONTROL;
        runtime->player_action.phase = AVSP_PW_PHASE_NONE;
        runtime->player_action.source_action = 0u;
        runtime->player_action.source_substate = 0u;
        runtime->player_action.x_numerator = 0L;
        runtime->player_locomotion_action =
            avsp_round1_player_locomotion.cleanup_action;
        runtime->player_cleanup_pending = 1u;
        ++runtime->player_hit_completions;
        ++runtime->player_hit_phase_transitions;
    }
    else
    {
        ++runtime->failure_count;
        return 0;
    }

    proposed_x = avsp_round1_fixed_high_word(runtime->player_hit_x_fp);
    runtime->player_action.x = proposed_x;
    avsp_round1_tick_player_resource(runtime);
    avsp_round1_apply_player_global_bounds(runtime);
    avsp_round1_apply_coffee_shop_obstacle(runtime);
    if (!avsp_round1_apply_first_segment_terrain(runtime) ||
        !avsp_round1_step_coffee_shop_camera(runtime))
    {
        ++runtime->failure_count;
        return 0;
    }
    resolved_x = runtime->player_action.x;
    if (resolved_x != proposed_x)
        runtime->player_hit_x_fp = (long)resolved_x * 65536L;
    else
        runtime->player_hit_x_fp = (long)resolved_x * 65536L +
            (unsigned short)runtime->player_hit_x_fp;
    runtime->player.x = resolved_x;
    runtime->player.y = runtime->player_action.lane;
    runtime->player.z = runtime->player_action.lane;
    runtime->player.source_x_fp = runtime->player_hit_x_fp;
    runtime->player.source_y_fp =
        (long)runtime->player_action.lane * 65536L;
    runtime->player.health = runtime->player_action.health;
    runtime->player.facing = (unsigned char)runtime->player_action.facing;
    runtime->player_weapon_previous_pressed = weapon_pressed;
    runtime->player_weapon_input_pipeline = weapon_pressed;
    runtime->player_jump_previous_pressed = jump_pressed;
    runtime->player_special_attack_previous_pressed = (unsigned char)(
        (special_buttons & (AVSP_ROUND1_INPUT_BUTTON1 |
                            AVSP_PW_INPUT_ATTACK)) ==
        (AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_ATTACK));
    runtime->player_special_previous_buttons = special_buttons;
    runtime->player_special_input_pipeline = special_buttons;
    ++runtime->player_controller_updates;
    return runtime->failure_count == 0u &&
        avsp_round1_entry_valid(runtime);
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
    unsigned char special_buttons;
    unsigned char special_physical_candidate;
    unsigned char special_pressed;
    unsigned char special_edge;
    unsigned char special_owned;
    if (runtime == 0 || runtime->route_state != 4 ||
        runtime->entry.control_enabled != 1u ||
        !avsp_round1_canaries_ok(runtime) || runtime->failure_count != 0u ||
        runtime->fallback_count != 0u)
        return 0;
    runtime->first_encounter.player_damage = 0u;
    runtime->player_special_attack_contact_ready = 0u;
    if (!runtime->player_hit_active && runtime->player_hit_invulnerability)
    {
        runtime->player_hit_invulnerability = 0u;
        runtime->player.source_x_fp = 0L;
        runtime->player.source_y_fp = 0L;
    }
    if (runtime->first_encounter.pending_player_damage != 0u)
    {
        if (received_damage != 0)
        {
            ++runtime->failure_count;
            return 0;
        }
        received_damage =
            (short)runtime->first_encounter.pending_player_damage;
        if (runtime->player_hit_active &&
            runtime->first_encounter.pending_player_damage_health_applied)
        {
            received_damage = 0;
            runtime->first_encounter.pending_player_damage_health_applied = 0u;
        }
        else if (runtime->first_encounter.pending_player_damage_health_applied)
        {
            runtime->player_action.health = (short)(
                runtime->player_action.health + received_damage);
            runtime->first_encounter.pending_player_damage_health_applied = 0u;
        }
        runtime->first_encounter.player_damage =
            runtime->first_encounter.pending_player_damage;
        runtime->first_encounter.pending_player_damage = 0u;
        ++runtime->first_encounter.player_damage_events;
    }
    if (runtime->first_encounter.route_unlocked &&
        !runtime->first_encounter.continued_after_unlock &&
        runtime->player_action.x >
            runtime->first_encounter.unlock_player_x + 8)
        runtime->first_encounter.continued_after_unlock = 1u;
    if (runtime->player_hit_active)
        return avsp_round1_step_player_hit(runtime, input_mask);
    jump_pressed = (unsigned char)(
        (input_mask & AVSP_ROUND1_INPUT_BUTTON3) != 0u);
    jump_edge = (unsigned char)(jump_pressed &&
        !runtime->player_jump_previous_pressed);
    special_buttons = runtime->player_special_input_pipeline;
    special_physical_candidate = (unsigned char)
        avsp_round1_player_special_guard(runtime,
            (unsigned char)(input_mask &
                (AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_ATTACK |
                 AVSP_ROUND1_INPUT_BUTTON3)),
            special_buttons);
    special_pressed = (unsigned char)(
        (special_buttons & (AVSP_ROUND1_INPUT_BUTTON1 |
                            AVSP_PW_INPUT_ATTACK)) ==
        (AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_ATTACK));
    special_edge = (unsigned char)avsp_round1_player_special_guard(
        runtime, special_buttons, runtime->player_special_previous_buttons);
    if (received_damage > 0)
    {
        runtime->player_special_attack_active = 0u;
        runtime->player_special_phase = 0u;
    }
    else if (special_edge &&
             runtime->player_action.state == AVSP_PW_STATE_CONTROL)
    {
        avsp_round1_begin_player_special(runtime);
    }
    special_owned = runtime->player_special_attack_active;
    if (runtime->player_jump_cleanup_pending)
        runtime->player_jump_cleanup_pending = 0u;
    if (runtime->player_jump_active && received_damage > 0)
        avsp_round1_interrupt_player_jump(runtime);
    if (!special_owned && !runtime->player_jump_active &&
        !runtime->player_weapon_active &&
        !runtime->player_weapon_cleanup_pending &&
        !runtime->player_weapon_return_pending && received_damage <= 0 &&
        jump_edge && runtime->player_action.state == AVSP_PW_STATE_CONTROL)
    {
        if (!avsp_round1_begin_player_jump(runtime))
        {
            ++runtime->failure_count;
            return 0;
        }
    }
    jump_owned = runtime->player_jump_active;
    weapon_pressed = runtime->player_weapon_input_pipeline;
    weapon_edge = (unsigned char)(weapon_pressed &&
        !runtime->player_weapon_previous_pressed);
    if (jump_owned && runtime->player_jump_phase == 0x0402u &&
        weapon_edge && (input_mask & AVSP_PW_INPUT_ATTACK) == 0u &&
        !avsp_round1_begin_player_air_weapon(runtime, input_mask))
    {
        ++runtime->failure_count;
        return 0;
    }
    recovery_start = (unsigned char)(
        runtime->player_weapon_cleanup_pending &&
        runtime->player_weapon_recovery_pending);
    weapon_return_owned = 0u;
    if (runtime->player_weapon_return_pending)
        runtime->player_weapon_return_pending = 0u;
    if (runtime->player_weapon_cleanup_pending && !recovery_start)
    {
        runtime->player_weapon_cleanup_pending = 0u;
        weapon_return_owned = 1u;
        runtime->player_locomotion_action =
            avsp_round1_player_weapon.return_action;
    }
    if (!special_owned && !jump_owned && !runtime->player_weapon_active &&
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
        jump_owned || special_owned);
    input.mask = (unsigned short)(input_mask &
        (unsigned short)~(AVSP_ROUND1_INPUT_BUTTON1 |
                          AVSP_ROUND1_INPUT_BUTTON3));
    if (special_physical_candidate)
        input.mask = (unsigned short)(input.mask &
            (unsigned short)~AVSP_PW_INPUT_ATTACK);
    if (weapon_motion_hold)
        input.mask = (unsigned short)(input.mask &
            (unsigned short)~AVSP_PW_INPUT_ATTACK);
    input.received_damage = received_damage;
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
    applied_direction = runtime->player_action.direction_history[
        AVSP_PW_DIRECTION_LATENCY - 1];
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
        if ((runtime->player_weapon_active || weapon_return_owned) &&
            received_damage <= 0)
            runtime->player_action.state = prior_state;
    }
    if (special_owned)
        special_owned = (unsigned char)avsp_round1_step_player_special(runtime);
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
    if (!special_owned && !jump_owned && !weapon_owned)
        avsp_round1_update_player_locomotion(runtime, applied_direction,
                                            was_stopping, &view);
    if (runtime->failure_count != 0u)
        return 0;
    runtime->player.state = AVSP_ROUND1_PLAYER_CONTROL_STATE;
    runtime->player.facing = (unsigned char)view.facing;
    runtime->player.x = view.x;
    runtime->player.y = (short)(view.lane + view.height);
    runtime->player.z = view.lane;
    runtime->player.source_x_fp = avsp_round1_player_fractional_position(
        view.x, runtime->player_action.x_numerator);
    runtime->player.source_y_fp = avsp_round1_player_fractional_position(
        view.lane, runtime->player_action.lane_numerator);
    runtime->player.health = view.health;
    if (special_owned)
    {
        runtime->player.source_action = runtime->player_special_phase;
        runtime->player.substate = runtime->player_special_phase;
    }
    else if (jump_owned)
    {
        runtime->player.source_action = runtime->player_jump_phase;
        if (!runtime->player_jump_active &&
            runtime->player_jump_cleanup_pending)
            runtime->player.source_action = 0u;
    }
    else if (!weapon_owned)
    {
        runtime->player.substate = runtime->player_was_directional ||
                runtime->player_stop_ticks != 0u ?
            runtime->player_locomotion_action :
            (unsigned short)(runtime->player_locomotion_action & 0x00ffu);
        runtime->player.source_action = runtime->player_locomotion_action;
        if (!runtime->player_walk_animation_active)
        {
            runtime->player.animation_record = view.animation_record;
            runtime->player.assembly = view.assembly;
            runtime->player.animation_timer = 4095u;
            runtime->player.animation_branch = -32768;
        }
    }
    runtime->player_weapon_previous_pressed = weapon_pressed;
    runtime->player_weapon_input_pipeline = (unsigned char)(
        (input_mask & AVSP_ROUND1_INPUT_BUTTON1) != 0u);
    runtime->player_jump_previous_pressed = jump_pressed;
    runtime->player_special_attack_previous_pressed = special_pressed;
    runtime->player_special_previous_buttons = special_buttons;
    runtime->player_special_input_pipeline = (unsigned char)(input_mask &
        (AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_ATTACK |
         AVSP_ROUND1_INPUT_BUTTON3));
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
        runtime->player_weapon_resource_debits >
            runtime->player_weapon_entries + runtime->player_air_weapon_entries ||
        runtime->player_weapon_empty_auxiliary_requests !=
            runtime->player_weapon_empty_auxiliary_allocations +
            runtime->player_weapon_empty_auxiliary_allocation_failures ||
        runtime->player_weapon_empty_auxiliary_releases >
            runtime->player_weapon_empty_auxiliary_allocations ||
        runtime->player_air_weapon_effect_requests !=
            runtime->player_air_weapon_effect_allocations +
            runtime->player_air_weapon_effect_allocation_failures ||
        runtime->player_air_weapon_effect_releases >
            runtime->player_air_weapon_effect_allocations ||
        runtime->player_weapon_parent_effect_requests !=
            runtime->player_weapon_parent_effect_allocations +
            runtime->player_weapon_parent_effect_allocation_failures ||
        runtime->player_weapon_parent_effect_releases >
            runtime->player_weapon_parent_effect_allocations ||
        runtime->player_weapon_completions > runtime->player_weapon_entries)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY; ++index)
    {
        const AvspRound1WeaponProjectileAllocation *projectile =
            &runtime->player_weapon_projectiles[index];
        unsigned short owner_relative;
        int owner_valid;
        if (!projectile->active)
            continue;
        owner_valid = projectile->owner ==
            avsp_round1_player_weapon.player_owner;
        if (projectile->actor_class ==
                avsp_round1_player_weapon.child_class)
        {
            owner_relative = (unsigned short)(projectile->owner -
                avsp_round1_player_weapon.projectile_source_base);
            owner_valid = projectile->owner >=
                    avsp_round1_player_weapon.projectile_source_base &&
                (unsigned int)owner_relative /
                    avsp_round1_player_weapon.projectile_stride <
                    AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY &&
                (unsigned int)owner_relative %
                    avsp_round1_player_weapon.projectile_stride == 0u;
        }
        if (projectile->active != 1u ||
            (projectile->actor_class !=
                avsp_round1_player_weapon.parent_class &&
             projectile->actor_class !=
                avsp_round1_air_weapon_projectile.actor_class &&
             projectile->actor_class !=
                avsp_round1_player_weapon.child_class) ||
            projectile->source_slot != (unsigned short)(
                avsp_round1_player_weapon.projectile_source_base +
                index * avsp_round1_player_weapon.projectile_stride) ||
            !owner_valid ||
            projectile->attack_table !=
                ((projectile->actor_class ==
                    avsp_round1_player_weapon.parent_class ||
                  projectile->actor_class ==
                    avsp_round1_air_weapon_projectile.actor_class) ?
                    avsp_round1_player_weapon.parent_attack_table :
                    avsp_round1_player_weapon.child_attack_table))
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
            if (runtime->player_weapon_tick == 1u &&
                avsp_round1_player_weapon.
                    empty_entry_preserves_current_presentation)
            {
                if (runtime->player.source_action !=
                        avsp_round1_player_weapon.empty_entry_action ||
                    runtime->player.substate !=
                        avsp_round1_player_weapon.empty_entry_action ||
                    runtime->player.hurt_selector != 0u ||
                    runtime->player.attack_selector != 0u)
                    return 0;
                frame = 0;
            }
            else
                frame = &avsp_round1_player_empty_frames[
                    runtime->player_weapon_tick - 1u];
        }
        else
        {
            if (runtime->player_weapon_tick >
                AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT)
                return 0;
            if (runtime->player_weapon_presentation_selector < 4u ||
                runtime->player_weapon_presentation_selector > 7u)
                return 0;
            frame = &avsp_round1_player_weapon_frames[
                runtime->player_weapon_presentation_selector - 4u][
                runtime->player_weapon_tick - 1u];
        }
        if (frame != 0 &&
            (runtime->player.source_action != frame->action ||
            runtime->player.substate != frame->action ||
            runtime->player.animation_record != frame->animation_record ||
            runtime->player.assembly != frame->assembly ||
            runtime->player.hurt_selector != 0u ||
            runtime->player.attack_selector != 0u))
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
            runtime->player.substate != frame->action ||
            runtime->player.animation_record != frame->animation_record ||
            runtime->player.assembly != frame->assembly ||
            runtime->player.hurt_selector != 0u ||
            runtime->player.attack_selector != 0u ||
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
        runtime->player_jump_phase != 0x0406u &&
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
    if (runtime->player_jump_phase == 0x0406u)
        return runtime->player_jump_airborne_latch == 1u &&
            runtime->player_jump_collision_selector == 9u &&
            runtime->player_jump_presentation_selector == 18u &&
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
        {0xA3C0u, 0xAE00u, 0xB600u, 0xC600u, 0xCE00u, 0xE240u};

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
        !avsp_round1_class1f_player_collision_contract_valid() ||
        !avsp_round1_player_hit_contract_valid() ||
        !avsp_round1_player_hit_runtime_valid(runtime) ||
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
    if (!avsp_round1_pool_active_free_valid(&runtime->pools[0]))
        return 0;
    if (!runtime->entry.started)
        return runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&
            runtime->player.state == 0u && runtime->player.substate == 0u &&
            runtime->player.health == 0 &&
            runtime->pools[0].free_count == 20u;
    if (runtime->entry_controller.active != 1u ||
        runtime->entry_controller.actor_class != 1 ||
        runtime->entry_controller.type != 32u ||
        runtime->entry_controller.source_slot != 0x00ffd180UL ||
        runtime->first_encounter.source_controller_initialized != 1u ||
        (!runtime->entry.spawned &&
         runtime->entry_controller.state !=
            avsp_round1_recurring_spawn.initial_state) ||
        (runtime->entry.spawned &&
         runtime->entry_controller.state !=
            avsp_round1_recurring_spawn.wait_state &&
         runtime->entry_controller.state !=
            avsp_round1_recurring_spawn.current_state) ||
        runtime->entry.gate81af != 1u ||
        runtime->entry.step_index > AVSP_ROUND1_ENTRY_STEP_COUNT ||
        runtime->entry.timer_decrements > 164u)
        return 0;
    if (!runtime->entry.dependencies_seeded)
        return runtime->pools[0].free_count == 20u &&
            runtime->entry.spawn_count == 0u &&
            runtime->player.state == AVSP_ROUND1_PLAYER_ENTRY_STATE &&
            runtime->pools[2].free_count == 16u &&
            runtime->pools[3].free_count == 32u &&
            runtime->class09_initializations == 0u;
    if (!runtime->entry.spawned)
        return runtime->pools[0].free_count == 20u &&
            runtime->entry.spawn_count == 0u &&
            runtime->player.state == AVSP_ROUND1_PLAYER_ENTRY_STATE &&
            runtime->pools[2].free_count == 14u &&
            runtime->pools[3].free_count == 30u &&
            (runtime->class09_initializations == 0u ||
             runtime->class09_initializations == 2u);
    if (runtime->entry.spawn_count != AVSP_ROUND1_FIRST_SPAWN_COUNT)
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
        if (actor->active == 0u)
            continue;
        if (actor->type != spec->record_type ||
            actor->source_slot != spec->source_slot)
            return 0;
        if (actor->source_dynamic_spawn == 0u &&
            actor->handler_updates == 0u &&
            actor->source_action_initialized == 0u &&
            (actor->actor_class != (signed char)spec->actor_class ||
            (actor->x != spec->x || actor->y != spec->y ||
             actor->z != spec->z || actor->variant != spec->variant ||
             actor->source_action != spec->source_action ||
             actor->state != spec->state || actor->substate != spec->substate ||
             actor->facing != spec->facing ||
             actor->animation_record != spec->animation_record ||
             actor->health != spec->health)))
            return 0;
    }
    if (runtime->route_state == 4)
    {
        int locomotion_valid = 1;
        if (runtime->player_special_attack_active ||
            runtime->player_jump_active ||
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
                    avsp_round1_player_locomotion.walking_action ||
                    (runtime->player_was_directional &&
                     runtime->player_locomotion_action ==
                        avsp_round1_player_locomotion.cleanup_action);
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
            (runtime->player.state == AVSP_ROUND1_PLAYER_CONTROL_STATE ||
             (runtime->player_hit_active &&
              runtime->player.state ==
                  avsp_round1_player_hit.hit_outer_state)) &&
            runtime->player_action.health == runtime->player.health &&
            runtime->player_action.x == runtime->player.x &&
            runtime->player_action.lane == runtime->player.z &&
            (runtime->player_special_attack_active ||
             runtime->player_jump_active ||
             runtime->player_jump_cleanup_pending ||
             runtime->player_weapon_active ||
             runtime->player_weapon_cleanup_pending ||
             runtime->player_weapon_return_pending ||
             runtime->player_hit_active ||
             runtime->player_hit_invulnerability ||
             runtime->player.source_action ==
                runtime->player_locomotion_action) && locomotion_valid;
    }
    if (runtime->entry.control_enabled ||
        runtime->player.state != AVSP_ROUND1_PLAYER_ENTRY_STATE)
        return 0;
    return 1;
}
