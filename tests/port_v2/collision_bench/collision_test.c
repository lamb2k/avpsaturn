#include <stdio.h>
#include <string.h>

#include "tests/port_v2/collision_bench/collision_bench.h"

int main(int argc, char **argv)
{
    AvspCollisionBenchResult result;
    int case_id;
    int negative_control;

    negative_control = argc == 2 && strcmp(argv[1], "--negative-control") == 0;
    for (case_id = 0; case_id < AVSP_COLLISION_CASE_COUNT; ++case_id) {
        if (!avsp_collision_bench_evaluate(case_id, &result) ||
            !avsp_collision_bench_result_ok(&result)) {
            printf("case %d failed\n", case_id);
            return 1;
        }
        printf("%02d overlap=%d guard=%d hit=%d ax=%d dx=%d ay=%d dy=%d az=%d dz=%d\n",
               case_id, result.overlap, result.guarded, result.hit_value,
               result.attacker_x, result.defender_x,
               result.attacker_y, result.defender_y,
               result.attacker_z, result.defender_z);
    }
    if (negative_control) {
        if (!avsp_collision_bench_evaluate(AVSP_COLLISION_CASE_X_OUTSIDE,
                                           &result)) {
            return 1;
        }
        result.expected_overlap = 1;
        if (avsp_collision_bench_result_ok(&result)) {
            printf("mutated outside case escaped the harness\n");
            return 1;
        }
        printf("negative control rejected\n");
    }
    return 0;
}
