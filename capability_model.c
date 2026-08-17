#include "capability_model.h"

#define CAP_LANE_MIN 148
#define CAP_LANE_MAX 198
#define CAP_ATTACK_ACTIVE_FRAME 16
#define CAP_ATTACK_TOTAL_FRAMES 40
#define CAP_SPECIAL_ACTIVE_FRAME 12
#define CAP_ROOM_ONE_RIGHT 336
#define CAP_ROOM_ONE_EXIT 480
#define CAP_KO_VISIBLE_FRAMES 45
#define CAP_CLEAR_HOLD_FRAMES 60
#define CAP_BOSS_INTRO_FRAMES 90
#define CAP_STAGE_CLEAR_FRAMES 180

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
    const int fitted_source_width = CAP_CPS2_VIEW_WIDTH;
    const int maximum_scroll = CAP_BACKGROUND_WIDTH - fitted_source_width;

    if (stage_area != 0) return 0;
    camera_x = cap_clamp(camera_x, 0, maximum_camera);
    return (camera_x * maximum_scroll) / maximum_camera;
}

static void cap_deactivate_enemy(CapActor *enemy, const int index)
{
    enemy->x = -256 - index * 32;
    enemy->lane = 178;
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
    world->player_ko_timer = 0;
    world->encounter_started = 0;
    world->encounter_state = CAP_ENCOUNTER_APPROACH;
    world->encounter_timer = 0;
    world->enemies_defeated = 0;
    world->room_locked = 0;
    world->stage_transitioned = 0;
    world->stage_area = 0;
    world->boss_defeated = 0;
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

static void cap_resolve_player_hit(CapWorld *world, const int range, const int damage)
{
    CapActor *player = &world->player;
    int index;

    if (player->hit_latched) return;
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
    }
}

static CapClipRequest cap_update_player(CapWorld *world, const CapInput *input)
{
    CapActor *player = &world->player;
    int speed = input->dash_held ? 4 : 2;
    int moving = 0;

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
        }
        return CAP_CLIP_NONE;
    }

    if (player->action == CAP_ACT_ATTACK || player->action == CAP_ACT_SPECIAL)
    {
        ++player->action_frame;
        if (player->action == CAP_ACT_ATTACK && player->action_frame == CAP_ATTACK_ACTIVE_FRAME)
            cap_resolve_player_hit(world, 58, 1);
        if (player->action == CAP_ACT_SPECIAL && player->action_frame == CAP_SPECIAL_ACTIVE_FRAME)
            cap_resolve_player_hit(world, 82, 2);
        if ((player->action == CAP_ACT_ATTACK &&
             player->action_frame >= CAP_ATTACK_TOTAL_FRAMES) ||
            (player->action == CAP_ACT_SPECIAL && player->action_frame >= 34))
        {
            player->action = CAP_ACT_IDLE;
            player->action_frame = 0;
            player->hit_latched = 0;
        }
        return CAP_CLIP_NONE;
    }

    if (input->attack_pressed)
    {
        player->action = CAP_ACT_ATTACK;
        player->action_frame = 0;
        player->hit_latched = 0;
        return CAP_CLIP_ATTACK;
    }
    if (input->special_pressed)
    {
        player->action = CAP_ACT_SPECIAL;
        player->action_frame = 0;
        player->hit_latched = 0;
        return CAP_CLIP_SPECIAL;
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
    world->encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    world->encounter_timer = 0;
    world->room_locked = 1;
    cap_spawn_range(world, 0, 5);
}

static void cap_update_encounter(CapWorld *world)
{
    ++world->encounter_timer;
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
        world->encounter_state = CAP_ENCOUNTER_BOSS_INTRO;
        world->stage_transitioned = 1;
        world->stage_area = 1;
        world->room_locked = 1;
        world->player.x = 88;
        world->player.lane = 178;
        world->camera_x = 0;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS_INTRO &&
        world->encounter_timer >= CAP_BOSS_INTRO_FRAMES)
    {
        cap_spawn_boss(world);
        world->encounter_state = CAP_ENCOUNTER_BOSS;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_BOSS && world->boss_defeated)
    {
        world->encounter_state = CAP_ENCOUNTER_STAGE_CLEAR;
        world->encounter_timer = 0;
    }
    if (world->encounter_state == CAP_ENCOUNTER_STAGE_CLEAR &&
        world->encounter_timer >= CAP_STAGE_CLEAR_FRAMES)
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
    int index;
    int target_camera;

    if (!world->encounter_started &&
        (input->left || input->right || input->up || input->down ||
         input->attack_pressed || input->special_pressed || input->dash_held))
        cap_begin_encounter(world);
    request = cap_update_player(world, input);
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
