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

static int active_enemy_count(const CapWorld *world)
{
    int count = 0;
    int index;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        if (world->enemies[index].active) ++count;
    return count;
}

static int test_abs(const int value)
{
    return value < 0 ? -value : value;
}

static void start_encounter(CapWorld *world)
{
    CapInput input;
    int frame;
    memset(&input, 0, sizeof(input));
    input.start_pressed = 1;
    (void)cap_world_step(world, &input);
    assert(world->encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT);
    assert(world->encounter_started == 0);
    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    (void)cap_world_step(world, &input);
    assert(world->encounter_state == CAP_ENCOUNTER_ROUND_TITLE);
    assert(world->room_locked == 1);
    assert(active_enemy_count(world) == 0);
    for (frame = 0; frame < 600 &&
         world->encounter_state != CAP_ENCOUNTER_WAVE_ONE; ++frame)
        step_empty(world, 1);
    assert(world->encounter_state == CAP_ENCOUNTER_WAVE_ONE);
    assert(world->room_locked == 1);
    assert(active_enemy_count(world) == 5);
    assert(frame == 479);
}

static void test_attack_requests_and_damage(void)
{
    CapWorld world;
    CapInput input;
    CapClipRequest request;

    cap_world_init(&world);
    start_encounter(&world);
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
    start_encounter(&world);
    world.frame = 1;
    world.enemies[0].x = world.player.x + 120;
    world.enemies[0].lane = world.player.lane;
    memset(&input, 0, sizeof(input));
    input.shoot_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_SHOOT);
    assert(world.player.action == CAP_ACT_SHOOT);
    assert(world.weapon_energy == CAP_WEAPON_MAX_ENERGY - CAP_WEAPON_SHOT_COST);
    assert(world.shots_fired == 1);
    step_empty(&world, 16);
    assert(world.enemies[0].health == 2);
}

static void test_jump_dash_and_two_button_special(void)
{
    CapWorld world;
    CapInput input;
    CapClipRequest request;
    int index;

    cap_world_init(&world);
    start_encounter(&world);
    memset(&input, 0, sizeof(input));
    input.jump_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_JUMP);
    assert(world.player.action == CAP_ACT_JUMP);
    step_empty(&world, 21);
    assert(world.player.height > 0);
    step_empty(&world, 21);
    assert(world.player.action == CAP_ACT_IDLE);
    assert(world.player.height == 0);

    world.player.x = 100;
    memset(&input, 0, sizeof(input));
    input.right = 1;
    input.jump_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_DASH);
    assert(world.player.action == CAP_ACT_DASH);
    assert(world.player.motion_x == 6);
    step_empty(&world, 24);
    assert(world.player.x == 244);
    assert(world.player.height == 0);

    for (index = 2; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    world.enemies[0].x = world.player.x + 40;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].health = 3;
    world.enemies[1].active = 1;
    world.enemies[1].x = world.player.x + 30;
    world.enemies[1].lane = world.player.lane;
    world.enemies[1].health = 3;
    memset(&input, 0, sizeof(input));
    input.shoot_pressed = 1;
    input.attack_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_SPECIAL);
    assert(world.player.action == CAP_ACT_SPECIAL);
    step_empty(&world, 12);
    assert(world.enemies[0].health == 1);
    assert(world.enemies[1].health == 1);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH - 1);
    assert(world.special_health_spent == 1);
}

static void test_encounter_waits_for_player_input(void)
{
    CapWorld world;
    int enemy_x;

    cap_world_init(&world);
    enemy_x = world.enemies[0].x;
    step_empty(&world, 1200);
    assert(world.encounter_started == 0);
    assert(world.encounter_state == CAP_ENCOUNTER_MAIN_MENU);
    assert(active_enemy_count(&world) == 0);
    assert(world.enemies[0].x == enemy_x);

    start_encounter(&world);
    assert(world.encounter_started == 1);
    assert(world.encounter_state == CAP_ENCOUNTER_WAVE_ONE);
}

static void test_first_room_waves_and_transition(void)
{
    CapWorld world;
    CapInput input;
    int index;

    cap_world_init(&world);
    start_encounter(&world);
    world.frame = 1;
    for (index = 0; index < 3; ++index)
    {
        world.enemies[index].x = world.player.x + 40;
        world.enemies[index].lane = world.player.lane;
        world.enemies[index].health = 1;
    }
    for (index = 3; index < 5; ++index)
        world.enemies[index].x = 24;

    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, 16);
    assert(world.enemies_defeated == 3);
    assert(world.encounter_state == CAP_ENCOUNTER_WAVE_TWO);
    assert(active_enemy_count(&world) == 8);

    step_empty(&world, 24);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        if (!world.enemies[index].active ||
            world.enemies[index].action == CAP_ACT_KO) continue;
        world.enemies[index].x = world.player.x + 40;
        world.enemies[index].lane = world.player.lane;
        world.enemies[index].health = 1;
    }
    /* Avoid an enemy attack residue during this 16-frame hit-window proof. */
    world.frame = 24;
    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, 16);
    assert(world.enemies_defeated == CAP_STAGE1_TOTAL_ENEMIES);
    assert(world.encounter_state == CAP_ENCOUNTER_CLEAR);
    assert(world.room_locked == 1);

    step_empty(&world, 60);
    assert(world.room_locked == 0);
    memset(&input, 0, sizeof(input));
    input.right = 1;
    for (index = 0; index < 120 && !world.stage_transitioned; ++index)
        (void)cap_world_step(&world, &input);
    assert(world.stage_transitioned == 1);
    assert(world.stage_area == 0);
    assert(world.encounter_state == CAP_ENCOUNTER_DOOR_DIALOGUE);

    step_empty(&world, 60);
    assert(world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION);
    step_empty(&world, 60);
    assert(world.encounter_state == CAP_ENCOUNTER_BOSS_INTRO);
    assert(world.stage_area == 1);
    assert(active_enemy_count(&world) == 1);
    assert(world.enemies[0].kind == CAP_ACTOR_BOSS);
    step_empty(&world, 60);
    assert(world.encounter_state == CAP_ENCOUNTER_BOSS);
    assert(active_enemy_count(&world) == 2);
    assert(world.enemies[0].kind == CAP_ACTOR_BOSS);
    assert(world.enemies[0].health == CAP_BOSS_MAX_HEALTH);
    assert(world.enemies[1].kind == CAP_ACTOR_STALKER);
    assert(world.boss_adds_spawned == 1);

    world.enemies[0].health = 16;
    step_empty(&world, 1);
    assert(world.boss_reinforcement_wave == 1);
    assert(world.boss_adds_spawned == 3);
    assert(active_enemy_count(&world) == 4);
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    world.enemies[0].health = 8;
    step_empty(&world, 1);
    assert(world.boss_reinforcement_wave == 2);
    assert(world.boss_adds_spawned == CAP_BOSS_TOTAL_ADDS);
    assert(active_enemy_count(&world) == 3);

    world.enemies[0].x = world.player.x + 40;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].health = 1;
    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, 16);
    assert(world.boss_defeated == 1);
    assert(world.encounter_state == CAP_ENCOUNTER_BOSS_DEFEAT);
    step_empty(&world, 240);
    assert(world.encounter_state == CAP_ENCOUNTER_STAGE_CLEAR);
    step_empty(&world, 120);
    assert(world.encounter_state == CAP_ENCOUNTER_RESULTS);
    step_empty(&world, 360);
    assert(world.encounter_state == CAP_ENCOUNTER_RESULTS_EXIT);
    step_empty(&world, 60);
    assert(world.encounter_state == CAP_ENCOUNTER_INTERMISSION);
    step_empty(&world, 60);
    assert(world.level_completed == 1);
    assert(world.encounter_state == CAP_ENCOUNTER_COMPLETE);
}

static void test_controller_only_route_completion(void)
{
    CapWorld world;
    CapInput input;
    int frame;

    cap_world_init(&world);
    for (frame = 0; frame < 90000 && !world.level_completed; ++frame)
    {
        CapActor *target = 0;
        int target_distance = 0;
        int index;

        memset(&input, 0, sizeof(input));
        if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
            input.start_pressed = 1;
        else if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
            input.attack_pressed = 1;
        else if (world.encounter_state == CAP_ENCOUNTER_CLEAR)
        {
            input.right = 1;
            if (world.player.action == CAP_ACT_IDLE ||
                world.player.action == CAP_ACT_WALK)
                input.jump_pressed = 1;
        }
        else if (world.player.action != CAP_ACT_KO &&
                 world.encounter_state != CAP_ENCOUNTER_BOSS_INTRO &&
                 world.encounter_state != CAP_ENCOUNTER_STAGE_CLEAR)
        {
            for (index = 0; index < CAP_MAX_ENEMIES; ++index)
            {
                CapActor *enemy = &world.enemies[index];
                int distance;
                if (!enemy->active || enemy->action == CAP_ACT_KO) continue;
                distance = test_abs(enemy->x - world.player.x) +
                    test_abs(enemy->lane - world.player.lane) * 2;
                if (target == 0 || distance < target_distance)
                {
                    target = enemy;
                    target_distance = distance;
                }
            }
            if (target != 0 &&
                (world.player.action == CAP_ACT_IDLE ||
                 world.player.action == CAP_ACT_WALK))
            {
                int delta_x = target->x - world.player.x;
                int delta_lane = target->lane - world.player.lane;
                if (test_abs(delta_lane) > 10)
                {
                    input.up = delta_lane < 0;
                    input.down = delta_lane > 0;
                }
                else if (test_abs(delta_x) > 54)
                {
                    input.left = delta_x < 0;
                    input.right = delta_x > 0;
                    input.jump_pressed = 1;
                }
                else
                {
                    if ((delta_x < 0 && world.player.facing > 0) ||
                        (delta_x > 0 && world.player.facing < 0))
                    {
                        input.left = delta_x < 0;
                        input.right = delta_x > 0;
                    }
                    else
                    {
                        input.shoot_pressed = 1;
                        input.attack_pressed = 1;
                    }
                }
            }
        }
        (void)cap_world_step(&world, &input);
    }

    assert(world.level_completed == 1);
    assert(world.encounter_state == CAP_ENCOUNTER_COMPLETE);
    assert(world.enemies_defeated == CAP_STAGE1_TOTAL_ENEMIES);
    assert(world.boss_defeated == 1);
    assert(world.boss_adds_spawned == CAP_BOSS_TOTAL_ADDS);
    assert(frame < 90000);
    printf("Controller-only route reached Round 2 boundary in %d frames.\n", frame);
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
        input.attack_pressed = (frame % 73) == 0;
        input.shoot_pressed = (frame % 211) == 0 && !input.attack_pressed;
        input.jump_pressed = (frame % 307) == 0 && !input.attack_pressed &&
                             !input.shoot_pressed;
        input.start_pressed = frame == 0;
        if (frame == 1) input.attack_pressed = 1;
        (void)cap_world_step(&world, &input);

        assert(world.player.x >= 24 && world.player.x <= CAP_WORLD_WIDTH - 24);
        assert(world.player.lane >= 148 && world.player.lane <= 198);
        assert(world.player.health >= 0 && world.player.health <= CAP_PLAYER_MAX_HEALTH);
        assert(world.player.height >= 0 && world.player.height <= 111);
        assert(world.player.motion_x >= -6 && world.player.motion_x <= 6);
        assert(world.weapon_energy >= 0 &&
               world.weapon_energy <= CAP_WEAPON_MAX_ENERGY);
        assert(world.shots_fired >= 0);
        assert(world.special_health_spent >= 0);
        assert(world.camera_x >= 0 &&
               world.camera_x <= CAP_WORLD_WIDTH - CAP_VIEW_WIDTH);
        assert(world.player.action >= CAP_ACT_IDLE && world.player.action <= CAP_ACT_KO);
        assert(world.encounter_state >= CAP_ENCOUNTER_MAIN_MENU);
        assert(world.encounter_state <= CAP_ENCOUNTER_COMPLETE);
        assert(world.stage_area == 0 || world.stage_area == 1);
        assert(world.boss_defeated == 0 || world.boss_defeated == 1);
        assert(world.level_completed == 0 || world.level_completed == 1);
        assert(world.boss_adds_spawned >= 0 &&
               world.boss_adds_spawned <= CAP_BOSS_TOTAL_ADDS);
        assert(world.boss_adds_defeated >= 0 &&
               world.boss_adds_defeated <= CAP_BOSS_TOTAL_ADDS);
        assert(world.boss_reinforcement_wave >= 0 &&
               world.boss_reinforcement_wave <= 2);
        assert(world.enemies_defeated >= 0 &&
               world.enemies_defeated <= CAP_STAGE1_TOTAL_ENEMIES);
        for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        {
            assert(world.enemies[index].lane >= 148 && world.enemies[index].lane <= 198);
            assert(world.enemies[index].health >= 0 &&
                   world.enemies[index].health <=
                       (world.enemies[index].kind == CAP_ACTOR_BOSS ?
                        CAP_BOSS_MAX_HEALTH : 3));
            assert(world.enemies[index].action >= CAP_ACT_IDLE);
            assert(world.enemies[index].action <= CAP_ACT_KO);
            assert(world.enemies[index].active == 0 || world.enemies[index].active == 1);
            assert(world.enemies[index].variant >= 0 && world.enemies[index].variant <= 3);
            assert(world.enemies[index].kind >= CAP_ACTOR_ALIEN);
            assert(world.enemies[index].kind <= CAP_ACTOR_BOSS);
        }
    }
    assert(world.frame == 12000);
}

static void test_capture_backed_route_boundary(void)
{
    assert(cap_stage1_route_event_count() == 26);
    assert(cap_stage1_source_start_frame() == 1440);
    assert(cap_stage1_source_end_frame() == 14760);
}

static void test_centered_background_mapping(void)
{
    assert(CAP_CENTER_CROP_X == 16);
    assert(cap_background_scroll_x(0, 0) == 16);
    assert(cap_background_scroll_x(CAP_WORLD_WIDTH - CAP_VIEW_WIDTH, 0) == 160);
    assert(cap_background_scroll_x(-100, 0) == 16);
    assert(cap_background_scroll_x(5000, 0) == 160);
    assert(cap_background_scroll_x(0, 1) == 16);
    assert(cap_background_scroll_x(5000, 1) == 16);
    assert(cap_background_fit_scroll_x(0, 0) == 0);
    assert(CAP_FITTED_BACKGROUND_WIDTH == 469);
    assert(cap_background_fit_scroll_x(CAP_WORLD_WIDTH - CAP_VIEW_WIDTH, 0) == 117);
    assert(cap_background_fit_scroll_x(-100, 0) == 0);
    assert(cap_background_fit_scroll_x(5000, 0) == 117);
    assert(cap_background_fit_scroll_x(5000, 1) == 0);
}

static void test_actor_display_mapping(void)
{
    /* Full-fit maps the complete 384-pixel CPS2 field to Saturn 352x224. */
    assert(cap_actor_screen_x(0, 0, 1) == -176);
    assert(cap_actor_screen_x(192, 0, 1) == 0);
    assert(cap_actor_screen_x(384, 0, 1) == 176);
    assert(cap_actor_screen_x(300, 0, 1) == 99);

    /* Exact mode centers the source and therefore crops 16 pixels per side. */
    assert(cap_actor_screen_x(0, 0, 0) == -192);
    assert(cap_actor_screen_x(16, 0, 0) == -176);
    assert(cap_actor_screen_x(192, 0, 0) == 0);
    assert(cap_actor_screen_x(368, 0, 0) == 176);
    assert(cap_actor_screen_x(300, 0, 0) == 108);

    assert(cap_actor_screen_x(300, 108, 1) == 0);
    assert(cap_actor_screen_x(300, 108, 0) == 0);
}

int main(void)
{
    test_attack_requests_and_damage();
    test_jump_dash_and_two_button_special();
    test_encounter_waits_for_player_input();
    test_first_room_waves_and_transition();
    test_controller_only_route_completion();
    test_long_deterministic_run();
    test_capture_backed_route_boundary();
    test_centered_background_mapping();
    test_actor_display_mapping();
    puts("Capability model tests passed (12,000 deterministic frames).");
    return 0;
}
