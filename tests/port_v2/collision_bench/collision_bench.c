/*
 * Bounded SALVAGE-03 adapter around the measured source collision routines.
 * It owns no damage, HIT, KO, AI, animation, or presentation state.
 */

#include <string.h>

#include "collision_bench.h"
#include "../../../avsp_collision.h"

#define BENCH_CLASS_ID 0x1Fu
#define BENCH_ATTACKER_ID 0x5Au
#define BENCH_LATCH_INDEX 2u

int avsp_collision_bench_evaluate(int case_id, AvspCollisionBenchResult *out)
{
    AvspActor attacker;
    AvspActor defender;
    unsigned long table_set;
    unsigned char hit_value;

    if (out == 0 || case_id < 0 || case_id >= AVSP_COLLISION_CASE_COUNT) {
        return 0;
    }
    memset(&attacker, 0, sizeof(attacker));
    memset(&defender, 0, sizeof(defender));
    memset(out, 0, sizeof(*out));
    table_set = 0uL;
    if (!avsp_table_set_for_class(BENCH_CLASS_ID, &table_set) ||
        table_set != AVSP_COLLISION_BENCH_TABLE_SET) {
        return 0;
    }

    attacker.table_set = table_set;
    attacker.sel_attack = 1u;
    attacker.world_x = 192;
    attacker.world_y = 0;
    attacker.world_z = 200;
    attacker.attacker_id = BENCH_ATTACKER_ID;
    attacker.latch_index = BENCH_LATCH_INDEX;

    defender.table_set = table_set;
    defender.sel_hurt = 1u;
    defender.world_x = 233;
    defender.world_y = 0;
    defender.world_z = 200;
    defender.state = 1u;

    out->case_id = case_id;
    out->expected_overlap = 1;
    out->expected_guarded = 0;
    switch (case_id) {
    case AVSP_COLLISION_CASE_X_EDGE:
        defender.world_x = 234;
        break;
    case AVSP_COLLISION_CASE_X_OUTSIDE:
        defender.world_x = 235;
        out->expected_overlap = 0;
        break;
    case AVSP_COLLISION_CASE_TRANSLATED:
        attacker.world_x += 48;
        defender.world_x += 48;
        break;
    case AVSP_COLLISION_CASE_Z_EDGE:
        defender.world_z = 216;
        break;
    case AVSP_COLLISION_CASE_Z_OUTSIDE:
        defender.world_z = 217;
        out->expected_overlap = 0;
        break;
    case AVSP_COLLISION_CASE_Y_EDGE:
        defender.world_y = 58;
        break;
    case AVSP_COLLISION_CASE_Y_OUTSIDE:
        defender.world_y = 59;
        out->expected_overlap = 0;
        break;
    case AVSP_COLLISION_CASE_EMPTY_ATTACK:
        attacker.sel_attack = 0u;
        out->expected_overlap = 0;
        break;
    case AVSP_COLLISION_CASE_EMPTY_HURT:
        defender.sel_hurt = 0u;
        out->expected_overlap = 0;
        break;
    case AVSP_COLLISION_CASE_SUPPRESSED:
        defender.suppress = 1u;
        out->expected_guarded = 1;
        break;
    case AVSP_COLLISION_CASE_INACTIVE:
        defender.state = 2u;
        out->expected_guarded = 1;
        break;
    case AVSP_COLLISION_CASE_LATCHED:
        defender.latch[BENCH_LATCH_INDEX] = BENCH_ATTACKER_ID;
        out->expected_guarded = 1;
        break;
    default:
        break;
    }

    hit_value = 0u;
    out->overlap = avsp_collision_overlap(&attacker, &defender, &hit_value);
    out->guarded = avsp_collision_guarded(&attacker, &defender);
    out->hit_value = (int)hit_value;
    out->attacker_x = attacker.world_x;
    out->attacker_y = attacker.world_y;
    out->attacker_z = attacker.world_z;
    out->defender_x = defender.world_x;
    out->defender_y = defender.world_y;
    out->defender_z = defender.world_z;
    out->attack_selector = (int)attacker.sel_attack;
    out->hurt_selector = (int)defender.sel_hurt;
    out->table_set_ok = 1;
    /* This diagnostic never calls the source hit-apply routine. */
    out->damage_write_count = 0;
    return 1;
}

int avsp_collision_bench_result_ok(const AvspCollisionBenchResult *result)
{
    if (result == 0 || result->table_set_ok != 1 ||
        result->damage_write_count != 0) {
        return 0;
    }
    if (result->overlap != result->expected_overlap ||
        result->guarded != result->expected_guarded) {
        return 0;
    }
    if (result->overlap && result->hit_value != 10) {
        return 0;
    }
    if (!result->overlap && result->hit_value != 0) {
        return 0;
    }
    return 1;
}
