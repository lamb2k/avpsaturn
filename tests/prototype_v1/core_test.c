#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../../src/prototype_v1/core.h"

static PrototypeInput no_input(void)
{
    PrototypeInput input;
    memset(&input, 0, sizeof(input));
    return input;
}

static void step_n(PrototypeWorld *world, PrototypeInput input, int count)
{
    int i;
    for (i = 0; i < count; ++i) prototype_v1_step(world, &input);
}

static void test_direct_boot_state(void)
{
    PrototypeWorld world;
    prototype_v1_init(&world);
    assert(world.frame == 0);
    assert(world.player_x == -64);
    assert(world.player_lane == 28);
    assert(world.player_facing == 1);
}

static void test_movement_and_bounds(void)
{
    PrototypeWorld world;
    PrototypeInput input = no_input();
    prototype_v1_init(&world);
    input.left = 1;
    input.up = 1;
    step_n(&world, input, 200);
    assert(world.player_x == PROTO_PLAYER_MIN_X);
    assert(world.player_lane == PROTO_LANE_MIN);
    assert(world.player_facing == -1);
    input = no_input();
    input.right = 1;
    input.down = 1;
    step_n(&world, input, 300);
    assert(world.player_x == PROTO_PLAYER_MAX_X);
    assert(world.player_lane == PROTO_LANE_MAX);
    assert(world.player_facing == 1);
}

static void test_three_minute_idle_model(void)
{
    PrototypeWorld world;
    PrototypeInput input = no_input();
    prototype_v1_init(&world);
    step_n(&world, input, 60 * 180);
    assert(world.frame == 10800);
    assert(world.player_x == -64);
    assert(world.player_lane == 28);
}

int main(void)
{
    test_direct_boot_state();
    test_movement_and_bounds();
    test_three_minute_idle_model();
    puts("prototype_v1 P0 core: PASS");
    return 0;
}
