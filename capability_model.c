#include "capability_model.h"

#define CAP_LANE_MIN 148
#define CAP_LANE_MAX 198
#define CAP_ATTACK_ACTIVE_FRAME 8
#define CAP_SPECIAL_ACTIVE_FRAME 12

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

static void cap_reset_enemy(CapActor *enemy, const int index)
{
    static const int stage_one_x[CAP_MAX_ENEMIES] = {80, 140, 200, 500};
    enemy->x = stage_one_x[index];
    enemy->lane = 154 + (index % 3) * 18;
    enemy->facing = -1;
    enemy->health = 3;
    enemy->action = CAP_ACT_IDLE;
    enemy->action_frame = 0;
    enemy->locomotion_frame = index * 7;
    enemy->hit_latched = 0;
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
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        cap_reset_enemy(&world->enemies[index], index);
    world->camera_x = 0;
    world->frame = 0;
    world->score = 0;
    world->player_ko_timer = 0;
    world->encounter_started = 0;
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
        world->score += 100;
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
        if (enemy->action == CAP_ACT_KO) continue;
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
        if ((player->action == CAP_ACT_ATTACK && player->action_frame >= 24) ||
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
    player->x = cap_clamp(player->x, 24, CAP_WORLD_WIDTH - 24);
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

    if (!world->encounter_started)
    {
        enemy->action = CAP_ACT_IDLE;
        return;
    }

    if (enemy->action == CAP_ACT_KO)
    {
        ++enemy->action_frame;
        if (enemy->action_frame >= 210)
        {
            cap_reset_enemy(enemy, index);
            enemy->x = cap_clamp(world->camera_x + 360 + index * 34, 400, CAP_WORLD_WIDTH - 24);
        }
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

CapClipRequest cap_world_step(CapWorld *world, const CapInput *input)
{
    CapClipRequest request;
    int index;
    int target_camera;

    if (input->left || input->right || input->up || input->down ||
        input->attack_pressed || input->special_pressed || input->dash_held)
        world->encounter_started = 1;
    request = cap_update_player(world, input);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        cap_update_enemy(world, &world->enemies[index], index);
    target_camera = cap_clamp(world->player.x - 288, 0, CAP_WORLD_WIDTH - 320);
    if (world->camera_x < target_camera) world->camera_x += 2;
    if (world->camera_x > target_camera) world->camera_x -= 2;
    ++world->frame;
    return request;
}
