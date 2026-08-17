#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../capability_model.h"

static void step_empty(CapWorld *world, const int count)
{
    CapInput input;
    int frame;
    memset(&input, 0, sizeof(input));
    for (frame = 0; frame < count; ++frame)
        (void)cap_world_step(world, &input);
}

static void test_attack_requests_and_damage(void)
{
    CapWorld world;
    CapInput input;
    CapClipRequest request;

    cap_world_init(&world);
    world.frame = 1; /* Keep enemy AI from opening on its frame-zero attack. */
    world.enemies[0].x = world.player.x + 40;
    world.enemies[0].lane = world.player.lane;
    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_ATTACK);
    assert(world.player.action == CAP_ACT_ATTACK);
    /* Dense CPS2 samples place the hit window at attack pose four/frame 16. */
    step_empty(&world, 16);
    assert(world.enemies[0].health == 2);

    cap_world_init(&world);
    world.enemies[0].x = world.player.x + 60;
    world.enemies[0].lane = world.player.lane;
    memset(&input, 0, sizeof(input));
    input.special_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_SPECIAL);
    step_empty(&world, 12);
    assert(world.enemies[0].health == 1);
}

static void test_encounter_waits_for_player_input(void)
{
    CapWorld world;
    CapInput input;
    int enemy_x;

    cap_world_init(&world);
    enemy_x = world.enemies[0].x;
    step_empty(&world, 1200);
    assert(world.encounter_started == 0);
    assert(world.enemies[0].x == enemy_x);

    memset(&input, 0, sizeof(input));
    input.right = 1;
    (void)cap_world_step(&world, &input);
    assert(world.encounter_started == 1);
    assert(world.enemies[0].x == enemy_x + 1);
}

static void test_long_deterministic_run(void)
{
    CapWorld world;
    CapInput input;
    int frame;
    int index;

    cap_world_init(&world);
    for (frame = 0; frame < 12000; ++frame)
    {
        memset(&input, 0, sizeof(input));
        input.right = (frame % 600) < 430;
        input.left = !input.right;
        input.up = (frame % 240) < 60;
        input.down = (frame % 240) >= 120 && (frame % 240) < 180;
        input.dash_held = (frame % 90) < 30;
        input.attack_pressed = (frame % 73) == 0;
        input.special_pressed = (frame % 211) == 0 && !input.attack_pressed;
        (void)cap_world_step(&world, &input);

        assert(world.player.x >= 24 && world.player.x <= CAP_WORLD_WIDTH - 24);
        assert(world.player.lane >= 148 && world.player.lane <= 198);
        assert(world.player.health >= 0 && world.player.health <= CAP_PLAYER_MAX_HEALTH);
        assert(world.camera_x >= 0 &&
               world.camera_x <= CAP_WORLD_WIDTH - CAP_VIEW_WIDTH);
        assert(world.player.action >= CAP_ACT_IDLE && world.player.action <= CAP_ACT_KO);
        for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        {
            assert(world.enemies[index].lane >= 148 && world.enemies[index].lane <= 198);
            assert(world.enemies[index].health >= 0 && world.enemies[index].health <= 3);
            assert(world.enemies[index].action >= CAP_ACT_IDLE);
            assert(world.enemies[index].action <= CAP_ACT_KO);
        }
    }
    assert(world.frame == 12000);
}

int main(void)
{
    test_attack_requests_and_damage();
    test_encounter_waits_for_player_input();
    test_long_deterministic_run();
    puts("Capability model tests passed (12,000 deterministic frames).");
    return 0;
}
