/* SALVAGE-03 source-collision diagnostic contract. C90. */
#ifndef AVSP_COLLISION_BENCH_H
#define AVSP_COLLISION_BENCH_H

#define AVSP_COLLISION_BENCH_TABLE_SET 0x00130AC8uL

typedef enum
{
    AVSP_COLLISION_CASE_INSIDE = 0,
    AVSP_COLLISION_CASE_X_EDGE,
    AVSP_COLLISION_CASE_X_OUTSIDE,
    AVSP_COLLISION_CASE_TRANSLATED,
    AVSP_COLLISION_CASE_Z_EDGE,
    AVSP_COLLISION_CASE_Z_OUTSIDE,
    AVSP_COLLISION_CASE_Y_EDGE,
    AVSP_COLLISION_CASE_Y_OUTSIDE,
    AVSP_COLLISION_CASE_EMPTY_ATTACK,
    AVSP_COLLISION_CASE_EMPTY_HURT,
    AVSP_COLLISION_CASE_SUPPRESSED,
    AVSP_COLLISION_CASE_INACTIVE,
    AVSP_COLLISION_CASE_LATCHED,
    AVSP_COLLISION_CASE_COUNT
} AvspCollisionBenchCase;

typedef struct
{
    int case_id;
    int expected_overlap;
    int overlap;
    int expected_guarded;
    int guarded;
    int hit_value;
    int attacker_x;
    int attacker_y;
    int attacker_z;
    int defender_x;
    int defender_y;
    int defender_z;
    int attack_selector;
    int hurt_selector;
    int table_set_ok;
    int damage_write_count;
} AvspCollisionBenchResult;

int avsp_collision_bench_evaluate(int case_id, AvspCollisionBenchResult *out);
int avsp_collision_bench_result_ok(const AvspCollisionBenchResult *result);

#endif
