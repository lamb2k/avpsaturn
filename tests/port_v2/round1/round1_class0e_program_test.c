/* Appended to the native translation unit only by the existing host harness.
 * These initialized-state counterfactuals are not production choreography. */
#ifdef AVSP_CLASS0E_INTERNAL_TEST
int avsp_round1_class0e_test_bridge(void)
{
    AvspRound1Runtime runtime;
    AvspRound1ActorCore *parent;
    AvspRound1ActorCore *child;
    AvspRound1Pool *pool;
    unsigned long seed;
    unsigned short free_count;
    avsp_round1_init(&runtime);
    pool = &runtime.pools[5];
    parent = &runtime.pools[0].records[0];
    parent->active = 2u;
    parent->type = 12u;
    parent->actor_class = 0x1f;
    parent->source_slot = 0x00ff9580UL;
    parent->state = 0x0402u;
    parent->substate = 0u;
    parent->source_hit_kind = 2;
    parent->coordinate_mode = 1u;
    parent->palette = 17u;
    parent->facing = 1u;
    parent->x = 1000;
    parent->y = 300;
    parent->z = 280;
    parent->animation_branch = -32768;
    seed = runtime.rng_seed;
    runtime.source_aux_ffe29c = 0x00abc123UL;
    pool->records[63].source_x_fp = 0x1234L;
    pool->records[63].source_y_fp = 0x5678L;
    pool->records[63].source_z_fp = 0x9abcL;
    if (!avsp_round1_spawn_type36_class0e(&runtime, parent) ||
        runtime.type36_class0e_allocations != 1UL || parent->source_field2b != 6u)
        return 201;
    child = &pool->records[63];
    if (child->active != 1u || child->actor_class != 0x0e ||
        child->source_target_low != 0x9580u || child->palette != 17u ||
        !avsp_round1_step_type36_class0e(&runtime, pool, child))
        return 202;
    if (runtime.source_aux_ffe29c != 0x01abc123UL ||
        parent->source_type36_class04_child != 0xe240u)
        return 203;
    if (child->x != 1000 || child->y != 300 || child->z != 280 ||
        child->facing != 1u || (unsigned short)child->source_x_fp != 0x1234u ||
        (unsigned short)child->source_y_fp != 0x5678u ||
        (unsigned short)child->source_z_fp != 0x9abcu ||
        child->animation_record != 0x0009dca8UL || child->animation_timer != 4095u)
        return 204;
    parent->animation_branch = (short)(-32768 + 34);
    if (!avsp_round1_step_type36_class0e(&runtime, pool, child) ||
        child->x != 1004 || child->y != 355 || child->facing != 1u ||
        child->animation_record != 0x0009d6b2UL)
        return 205;
    parent->facing = 0u;
    if (!avsp_round1_step_type36_class0e(&runtime, pool, child) ||
        child->x != 996 || child->y != 355 || child->facing != 0u)
        return 206;
    parent->animation_branch = (short)(-32768 + 24);
    parent->state = 0x0600u;
    if (!avsp_round1_step_type36_class0e(&runtime, pool, child) ||
        child->state != 0x0600u || child->active != 1u ||
        child->x != 1025 || child->y != 317 ||
        child->animation_record != 0x0009dd20UL || child->animation_timer != 8u)
        return 207;
    parent->active = 0u;
    child->source_field01 = 7u;
    if (!avsp_round1_step_type36_class0e(&runtime, pool, child) ||
        child->active != 0u || pool->free_count != 64u ||
        child->source_field01 != 0u ||
        parent->source_type36_class04_child != 0u ||
        child->animation_record != 0x0009dd20UL || runtime.rng_seed != seed)
        return 208;
    avsp_round1_clear_coffee_scene_pools(&runtime);
    if (runtime.source_aux_ffe29c != 0UL)
        return 209;
    parent = &runtime.pools[0].records[0];
    parent->active = 2u; parent->type = 12u; parent->actor_class = 0x1f;
    parent->source_slot = 0x00ff9580UL; parent->state = 0x0402u;
    parent->source_hit_kind = 21;
    free_count = pool->free_count;
    if (!avsp_round1_spawn_type36_class0e(&runtime, parent) ||
        pool->free_count != free_count || parent->source_field2b != 6u)
        return 210;
    parent->source_hit_kind = 2;
    pool->free_count = 0u;
    if (!avsp_round1_spawn_type36_class0e(&runtime, parent) ||
        runtime.type36_class0e_allocation_failures != 1UL)
        return 211;
    return 0;
}
#else
extern int avsp_round1_class0e_test_bridge(void);
int main(void)
{
    return avsp_round1_class0e_test_bridge();
}
#endif
