#include "capability_model.h"
#include "generated/avsp_stage1_route.h"

#define CAP_LANE_MIN 148
#define CAP_LANE_MAX 198
#define CAP_ATTACK_ACTIVE_FRAME 16
#define CAP_ATTACK_TOTAL_FRAMES 40
#define CAP_SHOOT_ACTIVE_FRAME 16
#define CAP_SHOOT_TOTAL_FRAMES 40
#define CAP_SPECIAL_ACTIVE_FRAME 12
#define CAP_SPECIAL_TOTAL_FRAMES 34
#define CAP_JUMP_TOTAL_FRAMES 30
#define CAP_DASH_TOTAL_FRAMES 30
#define CAP_ROOM_ONE_RIGHT 336
#define CAP_ROOM_ONE_EXIT 480
#define CAP_KO_VISIBLE_FRAMES 45
#define CAP_CLEAR_HOLD_FRAMES 60

typedef struct
{
    int x;
    int lane;
    int variant;
} CapStage1Spawn;

/* Capture-derived opening-room composition. Wave one reflects the crowded
   2760-3240 interval; wave two adds the palette mix seen by frame 3480. */
static const CapStage1Spawn cap_stage1_spawns[CAP_STAGE1_TOTAL_ENEMIES] =
{
    {36, 174, 1},
    {92, 190, 2},
    {154, 158, 1},
    {224, 196, 0},
    {348, 180, 1},
    {18, 164, 3},
    {286, 154, 0},
    {366, 198, 2}
};

static int cap_abs(const int value)
{
    return value < 0 ? -value : value;
}

static int cap_clamp(const int value, const int minimum, const int maximum)
{
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return value;
}

int cap_background_scroll_x(int camera_x, int stage_area)
{
    const int maximum_camera = CAP_WORLD_WIDTH - CAP_VIEW_WIDTH;
    const int maximum_scroll = CAP_BACKGROUND_WIDTH - CAP_VIEW_WIDTH;
    const int scrollable_after_crop = maximum_scroll - CAP_CENTER_CROP_X;

    /* Each captured CPS2 room begins with a 384-pixel active picture inside a
       512-pixel Saturn bitmap. Start 16 pixels into that picture so 352-wide
       output crops both arcade edges evenly. The street then consumes the
       remaining bitmap width as the native camera advances. */
    if (stage_area != 0) return CAP_CENTER_CROP_X;
    camera_x = cap_clamp(camera_x, 0, maximum_camera);
    return CAP_CENTER_CROP_X +
        (camera_x * scrollable_after_crop) / maximum_camera;
}

int cap_background_fit_scroll_x(int camera_x, int stage_area)
{
    const int maximum_camera = CAP_WORLD_WIDTH - CAP_VIEW_WIDTH;
    const int maximum_scroll = CAP_FITTED_BACKGROUND_WIDTH - CAP_VIEW_WIDTH;

    if (stage_area != 0) return 0;
    camera_x = cap_clamp(camera_x, 0, maximum_camera);
    return (camera_x * maximum_scroll) / maximum_camera;
}

int cap_actor_screen_x(int world_x, int camera_x, int full_width_fit)
{
    int centered = world_x - camera_x - CAP_CPS2_VIEW_WIDTH / 2;

    /* Actor coordinates are authored in the CPS2's 384-pixel picture.  Exact
       mode exposes the centered 352-pixel subset, while full-fit applies the
       same 352/384 transform as the actor cel widths and VDP2 background. */
    if (!full_width_fit) return centered;
    if (centered < 0)
        return -((-centered * CAP_VIEW_WIDTH) / CAP_CPS2_VIEW_WIDTH);
    return (centered * CAP_VIEW_WIDTH) / CAP_CPS2_VIEW_WIDTH;
}

int cap_stage1_route_event_count(void)
{
    return AVSP_STAGE1_ROUTE_EVENT_COUNT;
}

int cap_stage1_source_start_frame(void)
{
    return avsp_stage1_route_events[0].source_frame;
}

int cap_stage1_source_end_frame(void)
{
    return avsp_stage1_route_events[AVSP_STAGE1_ROUTE_EVENT_COUNT - 1].source_frame;
}

static void cap_deactivate_enemy(CapActor *enemy, const int index)
{
    enemy->x = -256 - index * 32;
    enemy->lane = 178;
    enemy->height = 0;
    enemy->motion_x = 0;
    enemy->facing = -1;
    enemy->health = 0;
    enemy->action = CAP_ACT_KO;
    enemy->action_frame = 0;
    enemy->locomotion_frame = index * 7;
    enemy->hit_latched = 0;
    enemy->active = 0;
    enemy->variant = 0;
    enemy->kind = CAP_ACTOR_ALIEN;
}

static void cap_spawn_enemy(CapActor *enemy, const int index)
{
    const CapStage1Spawn *spawn = &cap_stage1_spawns[index];
    enemy->x = spawn->x;
    enemy->lane = spawn->lane;
    enemy->height = 0;
    enemy->motion_x = 0;
    enemy->facing = -1;
    enemy->health = 3;
    enemy->action = CAP_ACT_WALK;
    enemy->action_frame = 0;
    enemy->locomotion_frame = index * 7;
    enemy->hit_latched = 0;
    enemy->active = 1;
    enemy->variant = spawn->variant;
    enemy->kind = CAP_ACTOR_ALIEN;
}

static void cap_spawn_boss(CapWorld *world)
{
    CapActor *boss = &world->enemies[0];
    boss->x = 276;
    boss->lane = 182;
    boss->height = 0;
    boss->motion_x = 0;
    boss->facing = -1;
    boss->health = CAP_BOSS_MAX_HEALTH;
    boss->action = CAP_ACT_WALK;
    boss->action_frame = 0;
    boss->locomotion_frame = 0;
    boss->hit_latched = 0;
    boss->active = 1;
    boss->variant = 0;
    boss->kind = CAP_ACTOR_BOSS;
}

static void cap_spawn_boss_add(CapWorld *world)
{
    int index;
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *add = &world->enemies[index];
        if (add->active) continue;
        add->x = 244 + (world->boss_adds_spawned & 1) * 74;
        add->lane = 158 + (world->boss_adds_spawned % 3) * 18;
        add->height = 0;
        add->motion_x = 0;
        add->facing = -1;
        add->health = 3;
        add->action = CAP_ACT_WALK;
        add->action_frame = 0;
        add->locomotion_frame = world->boss_adds_spawned * 7;
        add->hit_latched = 0;
        add->active = 1;
        add->variant = 0;
        add->kind = CAP_ACTOR_STALKER;
        ++world->boss_adds_spawned;
        return;
    }
}

static void cap_spawn_boss_adds(CapWorld *world, const int count)
{
    int spawned;
    for (spawned = 0; spawned < count; ++spawned)
        cap_spawn_boss_add(world);
}

static void cap_spawn_range(CapWorld *world, const int first, const int count)
{
    int index;
    for (index = first; index < first + count; ++index)
        cap_spawn_enemy(&world->enemies[index], index);
}

void cap_world_init(CapWorld *world)
{
    int index;

    world->player.x = 300;
    world->player.lane = 178;
    world->player.height = 0;
    world->player.motion_x = 0;
    world->player.facing = 1;
    world->player.health = CAP_PLAYER_MAX_HEALTH;
    world->player.action = CAP_ACT_IDLE;
    world->player.action_frame = 0;
    world->player.locomotion_frame = 0;
    world->player.hit_latched = 0;
    world->player.active = 1;
    world->player.variant = 0;
    world->player.kind = CAP_ACTOR_PLAYER;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        cap_deactivate_enemy(&world->enemies[index], index);
    world->camera_x = 0;
    world->frame = 0;
    world->score = 0;
    world->weapon_energy = CAP_WEAPON_MAX_ENERGY;
    world->shots_fired = 0;
    world->special_health_spent = 0;
    world->player_ko_timer = 0;
    world->encounter_started = 0;
    world->encounter_state = CAP_ENCOUNTER_MAIN_MENU;
    world->encounter_timer = 0;
    world->enemies_defeated = 0;
    world->room_locked = 0;
    world->stage_transitioned = 0;
    world->stage_area = 0;
    world->boss_defeated = 0;
    world->boss_adds_spawned = 0;
    world->boss_adds_defeated = 0;
    world->boss_reinforcement_wave = 0;
    world->level_completed = 0;
}

static void cap_damage_enemy(CapWorld *world, CapActor *enemy, const int damage)
{
    enemy->health -= damage;
    enemy->action_frame = 0;
    enemy->hit_latched = 0;
    if (enemy->health <= 0)
    {
        enemy->health = 0;
        enemy->action = CAP_ACT_KO;
        if (enemy->kind == CAP_ACTOR_BOSS)
        {
            world->score += 1000;
            world->boss_defeated = 1;
        }
        else if (enemy->kind == CAP_ACTOR_STALKER)
        {
            world->score += 100;
            ++world->boss_adds_defeated;
        }
        else
        {
            world->score += 100;
            ++world->enemies_defeated;
        }
    }
    else
    {
        enemy->action = CAP_ACT_HIT;
        world->score += 20;
    }
}

static int cap_resolve_player_hit(CapWorld *world, const int range, const int damage)
{
    CapActor *player = &world->player;
    int index;
    int hits = 0;

    if (player->hit_latched) return 0;
    player->hit_latched = 1;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world->enemies[index];
        int delta_x;
        if (!enemy->active || enemy->action == CAP_ACT_KO) continue;
        delta_x = enemy->x - player->x;
        if (cap_abs(enemy->lane - player->lane) > 19) continue;
        if (delta_x * player->facing < 0 || cap_abs(delta_x) > range) continue;
        cap_damage_enemy(world, enemy, damage);
        ++hits;
    }
    return hits;
}

static CapClipRequest cap_update_player(CapWorld *world, const CapInput *input)
{
    CapActor *player = &world->player;
    int speed = 2;
    int moving = 0;
    int pressed_buttons = input->shoot_pressed + input->attack_pressed +
                          input->jump_pressed;

    if (player->action != CAP_ACT_SHOOT &&
        world->weapon_energy < CAP_WEAPON_MAX_ENERGY &&
        (world->frame & 1) == 0)
        ++world->weapon_energy;

    if (player->action == CAP_ACT_KO)
    {
        ++world->player_ko_timer;
        if (world->player_ko_timer >= 120)
        {
            player->x = world->camera_x + 96;
            player->lane = 178;
            player->health = CAP_PLAYER_MAX_HEALTH;
            player->action = CAP_ACT_IDLE;
            player->action_frame = 0;
            player->height = 0;
            player->motion_x = 0;
            world->player_ko_timer = 0;
        }
        return CAP_CLIP_NONE;
    }

    if (player->action == CAP_ACT_HIT)
    {
        ++player->action_frame;
        if (player->action_frame >= 16)
        {
            player->action = CAP_ACT_IDLE;
            player->action_frame = 0;
            player->height = 0;
            player->motion_x = 0;
        }
        return CAP_CLIP_NONE;
    }

    if (player->action == CAP_ACT_JUMP || player->action == CAP_ACT_DASH)
    {
        int total = player->action == CAP_ACT_DASH ?
                    CAP_DASH_TOTAL_FRAMES : CAP_JUMP_TOTAL_FRAMES;
        ++player->action_frame;
        player->x += player->motion_x;
        player->x = cap_clamp(player->x, 24,
                              world->room_locked ? CAP_ROOM_ONE_RIGHT :
                                                   CAP_WORLD_WIDTH - 24);
        player->height = (player->action_frame *
                          (total - player->action_frame)) / 4;
        if (player->action_frame >= total)
        {
            player->action = CAP_ACT_IDLE;
            player->action_frame = 0;
            player->height = 0;
            player->motion_x = 0;
        }
        return CAP_CLIP_NONE;
    }

    if (player->action == CAP_ACT_ATTACK || player->action == CAP_ACT_SHOOT ||
        player->action == CAP_ACT_SPECIAL)
    {
        ++player->action_frame;
        if (player->action == CAP_ACT_ATTACK && player->action_frame == CAP_ATTACK_ACTIVE_FRAME)
            (void)cap_resolve_player_hit(world, 58, 1);
        if (player->action == CAP_ACT_SHOOT && player->action_frame == CAP_SHOOT_ACTIVE_FRAME)
            (void)cap_resolve_player_hit(world, 220, 1);
        if (player->action == CAP_ACT_SPECIAL && player->action_frame == CAP_SPECIAL_ACTIVE_FRAME)
            (void)cap_resolve_player_hit(world, 82, 2);
        if ((player->action == CAP_ACT_ATTACK &&
             player->action_frame >= CAP_ATTACK_TOTAL_FRAMES) ||
            (player->action == CAP_ACT_SHOOT &&
             player->action_frame >= CAP_SHOOT_TOTAL_FRAMES) ||
            (player->action == CAP_ACT_SPECIAL &&
             player->action_frame >= CAP_SPECIAL_TOTAL_FRAMES))
        {
            player->action = CAP_ACT_IDLE;
            player->action_frame = 0;
            player->hit_latched = 0;
        }
        return CAP_CLIP_NONE;
    }

    if (pressed_buttons >= 2)
    {
        int health_spent = player->health > 1 ? 1 : 0;
        player->health -= health_spent;
        world->special_health_spent += health_spent;
        player->action = CAP_ACT_SPECIAL;
        player->action_frame = 0;
        player->hit_latched = 0;
        return CAP_CLIP_SPECIAL;
    }
    if (input->shoot_pressed && world->weapon_energy >= CAP_WEAPON_SHOT_COST)
    {
        world->weapon_energy -= CAP_WEAPON_SHOT_COST;
        ++world->shots_fired;
        player->action = CAP_ACT_SHOOT;
        player->action_frame = 0;
        player->hit_latched = 0;
        return CAP_CLIP_SHOOT;
    }
    if (input->attack_pressed)
    {
        player->action = CAP_ACT_ATTACK;
        player->action_frame = 0;
        player->hit_latched = 0;
        return CAP_CLIP_ATTACK;
    }
    if (input->jump_pressed)
    {
        if (input->left || input->right)
        {
            player->action = CAP_ACT_DASH;
            player->facing = input->left ? -1 : 1;
            player->motion_x = player->facing * 6;
        }
        else
        {
            player->action = CAP_ACT_JUMP;
            player->motion_x = 0;
        }
        player->action_frame = 0;
        player->height = 0;
        player->hit_latched = 0;
        return player->action == CAP_ACT_DASH ? CAP_CLIP_DASH : CAP_CLIP_JUMP;
    }

    if (input->left)
    {
        player->x -= speed;
        player->facing = -1;
        moving = 1;
    }
    if (input->right)
    {
        player->x += speed;
        player->facing = 1;
        moving = 1;
    }
    if (input->up)
    {
        player->lane -= speed;
        moving = 1;
    }
    if (input->down)
    {
        player->lane += speed;
        moving = 1;
    }
    player->x = cap_clamp(player->x, 24,
                          world->room_locked ? CAP_ROOM_ONE_RIGHT : CAP_WORLD_WIDTH - 24);
    player->lane = cap_clamp(player->lane, CAP_LANE_MIN, CAP_LANE_MAX);
    if (moving)
    {
        player->action = CAP_ACT_WALK;
        ++player->locomotion_frame;
    }
    else
    {
        player->action = CAP_ACT_IDLE;
    }
    return CAP_CLIP_NONE;
}

static void cap_enemy_attack_player(CapWorld *world, CapActor *enemy)
{
    CapActor *player = &world->player;
    if (enemy->hit_latched || player->action == CAP_ACT_KO) return;
    enemy->hit_latched = 1;
    if (cap_abs(enemy->x - player->x) > 44 || cap_abs(enemy->lane - player->lane) > 18)
        return;
    --player->health;
    player->action_frame = 0;
    if (player->health <= 0)
    {
        player->health = 0;
        player->action = CAP_ACT_KO;
        world->player_ko_timer = 0;
    }
    else
    {
        player->action = CAP_ACT_HIT;
    }
}

static void cap_update_enemy(CapWorld *world, CapActor *enemy, const int index)
{
    CapActor *player = &world->player;
    int delta_x;
    int delta_lane;

    if (!enemy->active) return;

    if (enemy->action == CAP_ACT_KO)
    {
        ++enemy->action_frame;
        if (enemy->action_frame >= CAP_KO_VISIBLE_FRAMES)
            cap_deactivate_enemy(enemy, index);
        return;
    }
    if (enemy->action == CAP_ACT_HIT)
    {
        ++enemy->action_frame;
        if (enemy->action_frame >= 14)
        {
            enemy->action = CAP_ACT_IDLE;
            enemy->action_frame = 0;
        }
        return;
    }
    if (enemy->action == CAP_ACT_ATTACK)
    {
        ++enemy->action_frame;
        if (enemy->action_frame == 12)
            cap_enemy_attack_player(world, enemy);
        if (enemy->action_frame >= 30)
        {
            enemy->action = CAP_ACT_IDLE;
            enemy->action_frame = 0;
            enemy->hit_latched = 0;
        }
        return;
    }
    if (player->action == CAP_ACT_KO) return;

    delta_x = player->x - enemy->x;
    delta_lane = player->lane - enemy->lane;
    enemy->facing = delta_x < 0 ? -1 : 1;
    if (cap_abs(delta_x) <= 40 && cap_abs(delta_lane) <= 16 &&
        ((world->frame + index * 19) % 78) == 0)
    {
        enemy->action = CAP_ACT_ATTACK;
        enemy->action_frame = 0;
        enemy->hit_latched = 0;
        return;
    }
    if (cap_abs(delta_x) > 34)
        enemy->x += delta_x < 0 ? -1 : 1;
    if (cap_abs(delta_lane) > 8)
        enemy->lane += delta_lane < 0 ? -1 : 1;
    enemy->action = CAP_ACT_WALK;
    ++enemy->locomotion_frame;
}

static void cap_begin_encounter(CapWorld *world)
{
    world->encounter_started = 1;
    world->encounter_state = CAP_ENCOUNTER_ROUND_TITLE;
    world->encounter_timer = 0;
    world->room_locked = 1;
}

static void cap_update_encounter(CapWorld *world)
{
    ++world->encounter_timer;
    if (world->encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world->encounter_timer >= AVSP_STAGE1_ROUND_TITLE_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_BARRICADE_INTRO;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO &&
        world->encounter_timer >= AVSP_STAGE1_BARRICADE_INTRO_FRAMES)
    {
        cap_spawn_range(world, 0, 5);
        world->encounter_state = CAP_ENCOUNTER_WAVE_ONE;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_WAVE_ONE &&
        world->enemies_defeated >= 3)
    {
        cap_spawn_range(world, 5, 3);
        world->encounter_state = CAP_ENCOUNTER_WAVE_TWO;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_WAVE_TWO &&
        world->enemies_defeated >= CAP_STAGE1_TOTAL_ENEMIES)
    {
        world->encounter_state = CAP_ENCOUNTER_CLEAR;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_CLEAR &&
        world->encounter_timer >= CAP_CLEAR_HOLD_FRAMES)
        world->room_locked = 0;
    if (world->encounter_state == CAP_ENCOUNTER_CLEAR &&
        !world->room_locked && world->player.x >= CAP_ROOM_ONE_EXIT)
    {
        int index;
        for (index = 0; index < CAP_MAX_ENEMIES; ++index)
            cap_deactivate_enemy(&world->enemies[index], index);
        world->encounter_state = CAP_ENCOUNTER_DOOR_DIALOGUE;
        world->stage_transitioned = 1;
        world->room_locked = 1;
        world->player.x = 88;
        world->player.lane = 178;
        world->camera_x = 0;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_DOOR_DIALOGUE &&
        world->encounter_timer >= AVSP_STAGE1_DOOR_DIALOGUE_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_INTERIOR_TRANSITION;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION &&
        world->encounter_timer >= AVSP_STAGE1_INTERIOR_TRANSITION_FRAMES)
    {
        world->stage_area = 1;
        cap_spawn_boss(world);
        world->encounter_state = CAP_ENCOUNTER_BOSS_INTRO;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS_INTRO &&
        world->encounter_timer >= AVSP_STAGE1_BOSS_INTRO_FRAMES)
    {
        cap_spawn_boss_adds(world, 1);
        world->encounter_state = CAP_ENCOUNTER_BOSS;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS && !world->boss_defeated &&
        world->enemies[0].health <= 16 && world->boss_reinforcement_wave < 1)
    {
        cap_spawn_boss_adds(world, 2);
        world->boss_reinforcement_wave = 1;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS && !world->boss_defeated &&
        world->enemies[0].health <= 8 && world->boss_reinforcement_wave < 2)
    {
        cap_spawn_boss_adds(world, 2);
        world->boss_reinforcement_wave = 2;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS && world->boss_defeated)
    {
        world->encounter_state = CAP_ENCOUNTER_BOSS_DEFEAT;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS_DEFEAT &&
        world->encounter_timer >= AVSP_STAGE1_BOSS_DEFEAT_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_STAGE_CLEAR;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_STAGE_CLEAR &&
        world->encounter_timer >= AVSP_STAGE1_STAGE_CLEAR_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_RESULTS;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_RESULTS &&
        world->encounter_timer >= AVSP_STAGE1_RESULTS_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_RESULTS_EXIT;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_RESULTS_EXIT &&
        world->encounter_timer >= AVSP_STAGE1_RESULTS_EXIT_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_INTERMISSION;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_INTERMISSION &&
        world->encounter_timer >= AVSP_STAGE1_INTERMISSION_FRAMES)
    {
        world->encounter_state = CAP_ENCOUNTER_COMPLETE;
        world->level_completed = 1;
        world->room_locked = 0;
        world->encounter_timer = 0;
    }
}

CapClipRequest cap_world_step(CapWorld *world, const CapInput *input)
{
    CapClipRequest request;
    CapInput gated_input;
    const CapInput *player_input = input;
    int index;
    int target_camera;

    if (world->encounter_state == CAP_ENCOUNTER_MAIN_MENU && input->start_pressed)
    {
        world->encounter_state = CAP_ENCOUNTER_CHARACTER_SELECT;
        world->encounter_timer = 0;
    }
    else if (world->encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT &&
             input->attack_pressed)
        cap_begin_encounter(world);
    if (world->encounter_state != CAP_ENCOUNTER_WAVE_ONE &&
        world->encounter_state != CAP_ENCOUNTER_WAVE_TWO &&
        world->encounter_state != CAP_ENCOUNTER_CLEAR &&
        world->encounter_state != CAP_ENCOUNTER_BOSS)
    {
        gated_input.left = 0;
        gated_input.right = 0;
        gated_input.up = 0;
        gated_input.down = 0;
        gated_input.shoot_pressed = 0;
        gated_input.attack_pressed = 0;
        gated_input.jump_pressed = 0;
        gated_input.start_pressed = 0;
        player_input = &gated_input;
    }
    request = cap_update_player(world, player_input);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        cap_update_enemy(world, &world->enemies[index], index);
    if (world->encounter_started)
        cap_update_encounter(world);
    target_camera = (world->room_locked || world->stage_area == 1) ? 0 :
        cap_clamp(world->player.x - (CAP_VIEW_WIDTH - 32),
                  0, CAP_WORLD_WIDTH - CAP_VIEW_WIDTH);
    if (world->camera_x < target_camera) world->camera_x += 2;
    if (world->camera_x > target_camera) world->camera_x -= 2;
    ++world->frame;
    return request;
}
