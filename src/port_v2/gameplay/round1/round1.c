#include "round1.h"
#include "spec02_round1_entry_data.h"

#include <string.h>

static const unsigned char avsp_round1_pool_types[AVSP_ROUND1_POOL_COUNT] =
    {12u, 16u, 20u, 24u};
static const unsigned char avsp_round1_pool_capacities[AVSP_ROUND1_POOL_COUNT] =
    {20u, 20u, 16u, 32u};
static const unsigned short avsp_round1_pool_strides[AVSP_ROUND1_POOL_COUNT] =
    {192u, 128u, 128u, 128u};
static const unsigned short avsp_round1_pool_bases[AVSP_ROUND1_POOL_COUNT] =
    {0x9580u, 0xA480u, 0xAE80u, 0xB680u};

static int avsp_round1_pool_metadata_valid(const AvspRound1Pool *pool,
                                           unsigned int index)
{
    return pool->record_type == avsp_round1_pool_types[index] &&
        pool->capacity == avsp_round1_pool_capacities[index] &&
        pool->stride == avsp_round1_pool_strides[index] &&
        pool->source_base == avsp_round1_pool_bases[index] &&
        pool->free_count <= pool->capacity;
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
    if (runtime == 0 || runtime->route_state != 4 ||
        runtime->entry.control_enabled != 1u ||
        !avsp_round1_canaries_ok(runtime) || runtime->failure_count != 0u ||
        runtime->fallback_count != 0u)
        return 0;
    input.mask = input_mask;
    input.received_damage = received_damage;
    avsp_pw_step(&runtime->player_action, &input);
    avsp_pw_view(&runtime->player_action, &view);
    runtime->player.state = AVSP_ROUND1_PLAYER_CONTROL_STATE;
    runtime->player.substate = view.source_substate;
    runtime->player.source_action = view.source_action;
    runtime->player.facing = (unsigned char)view.facing;
    runtime->player.x = view.x;
    runtime->player.y = view.lane;
    runtime->player.z = view.lane;
    runtime->player.health = view.health;
    runtime->player.animation_record = view.animation_record;
    ++runtime->player_controller_updates;
    return avsp_round1_entry_valid(runtime);
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
        runtime->rng_seed != AVSP_ROUND1_INITIAL_RNG ||
        runtime->player.active != 1u || runtime->player.actor_class != 0 ||
        runtime->player.type != 0u ||
        runtime->player.health > AVSP_ROUND1_PLAYER_HEALTH ||
        runtime->fallback_count != 0u || runtime->failure_count != 0u)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_POOL_COUNT; ++index)
    {
        const AvspRound1Pool *pool = &runtime->pools[index];
        if (!avsp_round1_pool_metadata_valid(pool, index) ||
            pool->free_stack[pool->capacity - 1u] != last_slots[index])
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
            runtime->player.state == AVSP_ROUND1_PLAYER_ENTRY_STATE;
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
            actor->type != spec->record_type || actor->source_slot != spec->source_slot ||
            actor->x != spec->x || actor->y != spec->y || actor->z != spec->z ||
            actor->variant != spec->variant || actor->source_action != spec->source_action ||
            actor->state != spec->state || actor->substate != spec->substate ||
            actor->facing != spec->facing ||
            actor->animation_record != spec->animation_record ||
            actor->health != spec->health)
            return 0;
    }
    if (runtime->route_state == 4)
        return runtime->entry.terminal_seen == 1u &&
            runtime->entry.control_enabled == 1u &&
            runtime->entry.gate8236 == 0u &&
            runtime->entry.timer_decrements == 164u &&
            runtime->entry.step_index == AVSP_ROUND1_ENTRY_STEP_COUNT &&
            runtime->player.state == AVSP_ROUND1_PLAYER_CONTROL_STATE &&
            runtime->player_action.health == runtime->player.health &&
            runtime->player_action.x == runtime->player.x &&
            runtime->player_action.lane == runtime->player.z;
    if (runtime->entry.control_enabled ||
        runtime->player.state != AVSP_ROUND1_PLAYER_ENTRY_STATE)
        return 0;
    return 1;
}
