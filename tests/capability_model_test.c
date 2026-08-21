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

static void release_selection_input(CapWorld *world)
{
    CapInput input;
    memset(&input, 0, sizeof(input));
    (void)cap_world_step(world, &input);
}

static void test_start_transition_boundary(void)
{
    CapWorld world;
    CapInput input;
    int step;

    /* The measured start transition is exactly 30 source frames (CPS2 source
       frames 1689-1718). Pin the literal value independently of the traversal
       below so a changed macro cannot silently move the boundary. */
    assert(CAP_START_TRANSITION_FRAMES == 30);

    cap_world_init(&world);
    assert(world.encounter_state == CAP_ENCOUNTER_MAIN_MENU);

    /* Start leaves MAIN_MENU for START_TRANSITION with the timer at zero. */
    memset(&input, 0, sizeof(input));
    input.start_pressed = 1;
    (void)cap_world_step(&world, &input);
    assert(world.encounter_state == CAP_ENCOUNTER_START_TRANSITION);
    assert(world.encounter_timer == 0);
    assert(world.encounter_started == 0);

    /* 29 no-input steps hold START_TRANSITION with the timer reaching 29. The
       count is a literal, never derived from CAP_START_TRANSITION_FRAMES. */
    for (step = 0; step < 29; ++step)
    {
        memset(&input, 0, sizeof(input));
        (void)cap_world_step(&world, &input);
    }
    assert(world.encounter_state == CAP_ENCOUNTER_START_TRANSITION);
    assert(world.encounter_timer == 29);

    /* The 30th step advances to CHARACTER_SELECT and resets the timer. */
    memset(&input, 0, sizeof(input));
    (void)cap_world_step(&world, &input);
    assert(world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT);
    assert(world.encounter_timer == 0);
    assert(world.encounter_started == 0);
}

static void test_character_selection_semantics(void)
{
    CapWorld world;
    CapInput input;

    cap_world_init(&world);
    assert(world.selected_character == CAP_CHARACTER_PREDATOR_WARRIOR);
    assert(world.selection_cursor == CAP_CHARACTER_PREDATOR_WARRIOR);
    memset(&input, 0, sizeof(input));
    input.start_pressed = 1;
    (void)cap_world_step(&world, &input);
    assert(world.encounter_state == CAP_ENCOUNTER_START_TRANSITION);
    /* Traverse the start transition before the character-select screen. */
    step_empty(&world, CAP_START_TRANSITION_FRAMES);
    assert(world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT);

    memset(&input, 0, sizeof(input));
    input.right = 1;
    (void)cap_world_step(&world, &input);
    assert(world.selection_cursor == CAP_CHARACTER_PREDATOR_WARRIOR);
    step_empty(&world, 2);
    assert(world.selection_cursor == CAP_CHARACTER_PREDATOR_WARRIOR);
    step_empty(&world, 1);
    assert(world.selection_cursor == CAP_CHARACTER_MAJOR_SCHAEFER);
    /* Holding at the right boundary does not wrap or retrigger. */
    step_empty(&world, 8);
    assert(world.selection_cursor == CAP_CHARACTER_MAJOR_SCHAEFER);
    release_selection_input(&world);

    memset(&input, 0, sizeof(input));
    input.down = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, CAP_SELECTION_MOVE_LATENCY_FRAMES);
    assert(world.selection_cursor == CAP_CHARACTER_PREDATOR_HUNTER);
    release_selection_input(&world);

    memset(&input, 0, sizeof(input));
    input.left = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, CAP_SELECTION_MOVE_LATENCY_FRAMES);
    assert(world.selection_cursor == CAP_CHARACTER_LINN_KUROSAWA);
    release_selection_input(&world);

    memset(&input, 0, sizeof(input));
    input.up = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, CAP_SELECTION_MOVE_LATENCY_FRAMES);
    assert(world.selection_cursor == CAP_CHARACTER_PREDATOR_WARRIOR);
    release_selection_input(&world);

    /* Left/up at the source boundary are accepted as no-op, never wrap. */
    memset(&input, 0, sizeof(input));
    input.left = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, CAP_SELECTION_MOVE_LATENCY_FRAMES);
    assert(world.selection_cursor == CAP_CHARACTER_PREDATOR_WARRIOR);
    release_selection_input(&world);

    /* All three gameplay buttons confirm. Use C on a non-default character
       and prove the source ID survives the current adapted Warrior fallback. */
    memset(&input, 0, sizeof(input));
    input.right = 1;
    (void)cap_world_step(&world, &input);
    step_empty(&world, CAP_SELECTION_MOVE_LATENCY_FRAMES);
    release_selection_input(&world);
    memset(&input, 0, sizeof(input));
    input.jump_pressed = 1;
    (void)cap_world_step(&world, &input);
    assert(world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM);
    assert(world.selected_character == CAP_CHARACTER_MAJOR_SCHAEFER);
    assert(world.adapted_character_fallbacks == 0);
    step_empty(&world, 240);
    assert(world.selected_character == CAP_CHARACTER_MAJOR_SCHAEFER);
    assert(world.adapted_character_fallbacks == 1);
    assert(world.player.variant == 0);
}

static void start_encounter(CapWorld *world)
{
    CapInput input;
    int frame;
    memset(&input, 0, sizeof(input));
    input.start_pressed = 1;
    (void)cap_world_step(world, &input);
    assert(world->encounter_state == CAP_ENCOUNTER_START_TRANSITION);
    assert(world->encounter_started == 0);
    /* Traverse the 30-frame start transition before character select. */
    step_empty(world, CAP_START_TRANSITION_FRAMES);
    assert(world->encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT);
    assert(world->encounter_started == 0);
    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    (void)cap_world_step(world, &input);
    assert(world->encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM);
    assert(world->encounter_started == 1);
    assert(world->room_locked == 1);
    assert(active_enemy_count(world) == 0);
    for (frame = 0; frame < 900 &&
         world->encounter_state != CAP_ENCOUNTER_WAVE_ONE; ++frame)
        step_empty(world, 1);
    assert(world->encounter_state == CAP_ENCOUNTER_WAVE_ONE);
    assert(world->room_locked == 1);
    assert(active_enemy_count(world) == 5);
    assert(frame == 719);
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
    assert(world.weapon_recharge_timer == CAP_WEAPON_RECHARGE_DELAY_FRAMES);
    assert(world.shots_fired == 1);
    step_empty(&world, 14);
    assert(world.weapon_energy == CAP_WEAPON_MAX_ENERGY - CAP_WEAPON_SHOT_COST);
    assert(world.weapon_recharge_timer == 0);
    step_empty(&world, 1);
    assert(world.weapon_energy ==
           CAP_WEAPON_MAX_ENERGY - CAP_WEAPON_SHOT_COST + 1);
    assert(world.weapon_recharge_timer ==
           CAP_WEAPON_RECHARGE_CADENCE_FRAMES - 1);
    step_empty(&world, 1);
    assert(world.enemies[0].health == 2);
    step_empty(&world, 2);
    assert(world.weapon_energy ==
           CAP_WEAPON_MAX_ENERGY - CAP_WEAPON_SHOT_COST + 2);
}

static void test_jump_dash_and_captured_special_chord(void)
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

    cap_world_init(&world);
    start_encounter(&world);
    memset(&input, 0, sizeof(input));
    input.attack_pressed = 1;
    input.jump_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_ATTACK);
    assert(world.player.action == CAP_ACT_ATTACK);

    cap_world_init(&world);
    start_encounter(&world);
    memset(&input, 0, sizeof(input));
    input.shoot_pressed = 1;
    input.jump_pressed = 1;
    request = cap_world_step(&world, &input);
    assert(request == CAP_CLIP_SHOOT);
    assert(world.player.action == CAP_ACT_SHOOT);

    cap_world_init(&world);
    start_encounter(&world);
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
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH);
    world.enemies[0].active = 0;
    world.enemies[1].active = 0;
    step_empty(&world, 69);
    assert(world.player.health ==
           CAP_PLAYER_MAX_HEALTH - CAP_SPECIAL_HEALTH_COST);
    assert(world.special_health_spent == CAP_SPECIAL_HEALTH_COST);
}

static void test_capture_exact_enemy_action_timing(void)
{
    CapWorld world;
    CapActor *enemy;
    int index;

    cap_world_init(&world);
    start_encounter(&world);
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    enemy = &world.enemies[0];
    enemy->x = world.player.x + 20;
    enemy->lane = world.player.lane;

    enemy->x = world.player.x + 145;
    world.frame = 1;
    step_empty(&world, 1);
    assert(enemy->x == world.player.x + 142);
    enemy->x = world.player.x + 20;

    enemy->action = CAP_ACT_HIT;
    enemy->action_frame = 0;
    step_empty(&world, 35);
    assert(enemy->action == CAP_ACT_HIT);
    assert(enemy->action_frame == 35);
    step_empty(&world, 1);
    assert(enemy->action == CAP_ACT_IDLE);

    enemy->action = CAP_ACT_ATTACK;
    enemy->action_frame = 0;
    world.player.health = CAP_PLAYER_MAX_HEALTH;
    step_empty(&world, 47);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH);
    step_empty(&world, 1);
    assert(world.player.health ==
           CAP_PLAYER_MAX_HEALTH - CAP_ENEMY_CONTACT_DAMAGE);
    step_empty(&world, 70);
    assert(world.player.health ==
           CAP_PLAYER_MAX_HEALTH - CAP_ENEMY_CONTACT_DAMAGE);
    assert(enemy->action == CAP_ACT_ATTACK);
    assert(enemy->action_frame == 118);
    step_empty(&world, 1);
    assert(world.player.health ==
           CAP_PLAYER_MAX_HEALTH - 2 * CAP_ENEMY_CONTACT_DAMAGE);
    assert(enemy->action_frame == 119);
    step_empty(&world, 1);
    assert(enemy->action == CAP_ACT_IDLE);

    enemy->active = 1;
    enemy->action = CAP_ACT_KO;
    enemy->action_frame = 0;
    step_empty(&world, 139);
    assert(enemy->active == 1);
    assert(enemy->action_frame == 139);
    step_empty(&world, 1);
    assert(enemy->active == 0);
}

static void test_capture_exact_boss_attack_timing(void)
{
    CapWorld world;
    CapActor *boss;
    int index;

    cap_world_init(&world);
    start_encounter(&world);
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    boss = &world.enemies[0];
    boss->kind = CAP_ACTOR_BOSS;
    boss->active = 1;
    boss->x = world.player.x + 100;
    boss->lane = world.player.lane;
    boss->action = CAP_ACT_ATTACK;
    boss->action_frame = 0;
    boss->hit_latched = 0;
    world.player.health = CAP_PLAYER_MAX_HEALTH;

    step_empty(&world, 20);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH);
    step_empty(&world, 1);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH - 10);
    step_empty(&world, 34);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH - 20);
    step_empty(&world, 42);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH - 36);
    step_empty(&world, 91);
    assert(boss->action == CAP_ACT_ATTACK);
    assert(boss->action_frame == 188);
    step_empty(&world, 1);
    assert(boss->action == CAP_ACT_IDLE);

    boss->action = CAP_ACT_HIT;
    boss->action_frame = 0;
    step_empty(&world, 39);
    assert(boss->action == CAP_ACT_HIT);
    assert(boss->action_frame == 39);
    step_empty(&world, 1);
    assert(boss->action == CAP_ACT_IDLE);

    boss->action = CAP_ACT_KO;
    boss->action_frame = 0;
    boss->active = 1;
    step_empty(&world, 427);
    assert(boss->active == 1);
    assert(boss->action == CAP_ACT_KO);
    assert(boss->action_frame == 427);
    step_empty(&world, 1);
    assert(boss->active == 1); /* Hold the settled corpse for 60 frames. */
    step_empty(&world, 59);
    assert(boss->active == 1);
    step_empty(&world, 1);
    assert(boss->active == 0);
}

static void test_capture_exact_stalker_timing(void)
{
    CapWorld world;
    CapActor *stalker;
    int index;

    cap_world_init(&world);
    start_encounter(&world);
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    stalker = &world.enemies[0];
    stalker->kind = CAP_ACTOR_STALKER;
    stalker->active = 1;
    stalker->lane = world.player.lane;

    stalker->x = world.player.x + 145;
    stalker->action = CAP_ACT_IDLE;
    world.frame = 1;
    step_empty(&world, 2);
    assert(stalker->x == world.player.x + 142);

    stalker->x = world.player.x + 20;
    stalker->action = CAP_ACT_IDLE;
    stalker->action_frame = 0;
    stalker->hit_latched = 0;
    world.frame = 0;
    world.player.health = CAP_PLAYER_MAX_HEALTH;
    step_empty(&world, 1);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH - 12);
    assert(stalker->action == CAP_ACT_ATTACK);
    assert(stalker->action_frame == 0);
    step_empty(&world, 16);
    assert(stalker->action == CAP_ACT_ATTACK);
    assert(stalker->action_frame == 16);
    step_empty(&world, 1);
    assert(stalker->action == CAP_ACT_IDLE);

    stalker->active = 1;
    stalker->action = CAP_ACT_KO;
    stalker->action_frame = 0;
    step_empty(&world, 156);
    assert(stalker->active == 1);
    assert(stalker->action_frame == 156);
    step_empty(&world, 1);
    assert(stalker->active == 0);
}

static void test_walk_locomotion_counter(void)
{
    CapWorld world;
    CapInput input;
    int index;
    int start_x;

    cap_world_init(&world);
    start_encounter(&world);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    world.player.x = 100;
    start_x = world.player.x;
    memset(&input, 0, sizeof(input));
    input.right = 1;
    for (index = 0; index < 48; ++index)
        cap_world_step(&world, &input);
    assert(world.player.action == CAP_ACT_WALK);
    assert(world.player.locomotion_frame == 48);
    assert(world.player.x == start_x + 96);
    step_empty(&world, 1);
    assert(world.player.action == CAP_ACT_IDLE);
    cap_world_step(&world, &input);
    assert(world.player.action == CAP_ACT_WALK);
    assert(world.player.locomotion_frame == 49);
}

static void test_player_hit_and_ko_timing(void)
{
    CapWorld world;
    int index;

    cap_world_init(&world);
    start_encounter(&world);
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    world.enemies[0].x = world.player.x;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].action = CAP_ACT_ATTACK;
    world.enemies[0].action_frame = 47;
    world.enemies[0].hit_latched = 0;
    step_empty(&world, 1);
    assert(world.player.action == CAP_ACT_HIT);
    assert(world.player.action_frame == 0);
    step_empty(&world, 24);
    assert(world.player.action == CAP_ACT_HIT);
    assert(world.player.action_frame == 24);
    step_empty(&world, 1);
    assert(world.player.action == CAP_ACT_IDLE);

    world.player.health = 1;
    world.enemies[0].active = 1;
    world.enemies[0].x = world.player.x;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].action = CAP_ACT_ATTACK;
    world.enemies[0].action_frame = 47;
    world.enemies[0].hit_latched = 0;
    step_empty(&world, 1);
    assert(world.player.action == CAP_ACT_KO);
    assert(world.player.action_frame == 0);
    world.enemies[0].active = 0;
    step_empty(&world, 95);
    assert(world.player.action == CAP_ACT_KO);
    assert(world.player.action_frame == 95);
    step_empty(&world, 1);
    assert(world.player.action == CAP_ACT_IDLE);
    assert(world.player.health == CAP_PLAYER_MAX_HEALTH);
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
    assert(world.encounter_state == CAP_ENCOUNTER_BOSS);
    assert(world.enemies[0].action == CAP_ACT_KO);
    step_empty(&world, 426);
    assert(world.encounter_state == CAP_ENCOUNTER_BOSS);
    assert(world.enemies[0].action_frame == 427);
    step_empty(&world, 1);
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
        assert(world.weapon_recharge_timer >= 0 &&
               world.weapon_recharge_timer <= CAP_WEAPON_RECHARGE_DELAY_FRAMES);
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

static void test_capture_exact_confirm_shutter(void)
{
    /* Every row of this table is the visible band measured from the cadence-1
       capture in data/frontend_geometry_cadence1.json, converted to confirm
       timer by subtracting source frame 1800. A band of -1 means the shutter
       has closed and the screen is black. The model must reproduce the
       capture, so this table is evidence and must not be relaxed to match a
       changed implementation. */
    static const int expected[][3] = {
        {  70,  40, 223 }, {  71,  40, 223 }, {  72,  40, 223 },
        {  73,  40, 223 }, {  74,  40, 223 }, {  75,  40, 223 },
        {  76,  40, 223 }, {  77,  40, 223 }, {  78,  40, 223 },
        {  79,  40, 223 }, {  80,  40, 223 }, {  81,  40, 223 },
        {  82,  40, 223 }, {  83,  40, 223 }, {  84,  40, 223 },
        {  85,  40, 223 }, {  86,  44, 219 }, {  87,  48, 215 },
        {  88,  52, 211 }, {  89,  56, 207 }, {  90,  60, 203 },
        {  91,  64, 199 }, {  92,  68, 195 }, {  93,  72, 191 },
        {  94,  76, 187 }, {  95,  80, 183 }, {  96,  84, 179 },
        {  97,  88, 175 }, {  98,  92, 171 }, {  99,  96, 167 },
        { 100, 100, 163 }, { 101, 104, 159 }, { 102, 108, 155 },
        { 103, 112, 151 }, { 104, 116, 147 }, { 105, 120, 143 },
        { 106, 124, 139 }, { 107, 128, 135 }, { 108,  -1,  -1 },
        { 109,  -1,  -1 }, { 110,  -1,  -1 }, { 111,  -1,  -1 },
        { 112,  -1,  -1 },
    };
    const int count = (int)(sizeof(expected) / sizeof(expected[0]));
    int index;
    int top;
    int bottom;

    for (index = 0; index < count; ++index)
    {
        const int timer = expected[index][0];
        const int visible = cap_confirm_shutter_band(timer, &top, &bottom);
        if (expected[index][1] < 0)
        {
            assert(visible == 0);
            continue;
        }
        assert(visible == 1);
        assert(top == expected[index][1]);
        assert(bottom == expected[index][2]);
    }

    /* The band is held from confirm entry until the measured start frame. */
    assert(cap_confirm_shutter_band(0, &top, &bottom) == 1);
    assert(top == CAP_CONFIRM_CONTENT_TOP_ROW);
    assert(bottom == CAP_CONFIRM_CONTENT_BOTTOM_ROW);

    /* Once closed it stays closed for the rest of the 240-frame hold. */
    assert(cap_confirm_shutter_band(239, &top, &bottom) == 0);

    /* The centre never moves while the band is open. */
    for (index = CAP_CONFIRM_SHUTTER_START_TIMER; index < 108; ++index)
    {
        assert(cap_confirm_shutter_band(index, &top, &bottom) == 1);
        assert(top + bottom == CAP_CONFIRM_CONTENT_TOP_ROW +
                               CAP_CONFIRM_CONTENT_BOTTOM_ROW);
    }
}

int main(void)
{
    test_start_transition_boundary();
    test_character_selection_semantics();
    test_attack_requests_and_damage();
    test_jump_dash_and_captured_special_chord();
    test_capture_exact_enemy_action_timing();
    test_capture_exact_boss_attack_timing();
    test_capture_exact_stalker_timing();
    test_walk_locomotion_counter();
    test_player_hit_and_ko_timing();
    test_encounter_waits_for_player_input();
    test_first_room_waves_and_transition();
    test_controller_only_route_completion();
    test_long_deterministic_run();
    test_capture_backed_route_boundary();
    test_centered_background_mapping();
    test_actor_display_mapping();
    test_capture_exact_confirm_shutter();
    puts("Capability model tests passed (12,000 deterministic frames).");
    return 0;
}
