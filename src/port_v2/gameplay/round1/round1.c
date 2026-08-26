#include "round1.h"

#include <string.h>

static const unsigned char avsp_round1_pool_types[AVSP_ROUND1_POOL_COUNT] =
    {12u, 16u, 20u, 24u};
static const unsigned char avsp_round1_pool_capacities[AVSP_ROUND1_POOL_COUNT] =
    {20u, 20u, 16u, 32u};
static const unsigned short avsp_round1_pool_strides[AVSP_ROUND1_POOL_COUNT] =
    {192u, 128u, 128u, 128u};
static const unsigned short avsp_round1_pool_bases[AVSP_ROUND1_POOL_COUNT] =
    {0x9580u, 0xA480u, 0xAE80u, 0xB680u};

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

int avsp_round1_entry_valid(const AvspRound1Runtime *runtime)
{
    unsigned int index;
    static const unsigned short last_slots[AVSP_ROUND1_POOL_COUNT] =
        {0xA3C0u, 0xAE00u, 0xB600u, 0xC600u};

    if (!avsp_round1_canaries_ok(runtime) ||
        runtime->route_state != AVSP_ROUND1_ROUTE_ENTRY_STATE ||
        runtime->rng_seed != AVSP_ROUND1_INITIAL_RNG ||
        runtime->player.active != 1u || runtime->player.actor_class != 0 ||
        runtime->player.type != 0u || runtime->player.state != 0u ||
        runtime->player.substate != 0u ||
        runtime->player.health != AVSP_ROUND1_PLAYER_HEALTH ||
        runtime->fallback_count != 0u)
        return 0;
    for (index = 0u; index < AVSP_ROUND1_POOL_COUNT; ++index)
    {
        const AvspRound1Pool *pool = &runtime->pools[index];
        if (pool->record_type != avsp_round1_pool_types[index] ||
            pool->capacity != avsp_round1_pool_capacities[index] ||
            pool->stride != avsp_round1_pool_strides[index] ||
            pool->source_base != avsp_round1_pool_bases[index] ||
            pool->free_count != pool->capacity ||
            pool->free_stack[pool->capacity - 1u] != last_slots[index])
            return 0;
    }
    return 1;
}
