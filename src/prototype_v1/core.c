#include "core.h"

void prototype_v1_init(PrototypeWorld *world)
{
    world->frame = 0;
    world->player_x = -64;
    world->player_lane = 28;
    world->player_facing = 1;
}

void prototype_v1_step(PrototypeWorld *world, const PrototypeInput *input)
{
    ++world->frame;
    if (input->left && !input->right)
    {
        world->player_x -= 2;
        world->player_facing = -1;
    }
    else if (input->right && !input->left)
    {
        world->player_x += 2;
        world->player_facing = 1;
    }
    if (input->up && !input->down) world->player_lane -= 1;
    else if (input->down && !input->up) world->player_lane += 1;

    if (world->player_x < PROTO_PLAYER_MIN_X)
        world->player_x = PROTO_PLAYER_MIN_X;
    if (world->player_x > PROTO_PLAYER_MAX_X)
        world->player_x = PROTO_PLAYER_MAX_X;
    if (world->player_lane < PROTO_LANE_MIN)
        world->player_lane = PROTO_LANE_MIN;
    if (world->player_lane > PROTO_LANE_MAX)
        world->player_lane = PROTO_LANE_MAX;
}
