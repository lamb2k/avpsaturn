#ifndef AVSP_PROTOTYPE_V1_CORE_H
#define AVSP_PROTOTYPE_V1_CORE_H

enum
{
    PROTO_PLAYER_MIN_X = -144,
    PROTO_PLAYER_MAX_X = 112,
    PROTO_LANE_MIN = -12,
    PROTO_LANE_MAX = 52
};

typedef struct
{
    int left;
    int right;
    int up;
    int down;
} PrototypeInput;

typedef struct
{
    unsigned long frame;
    int player_x;
    int player_lane;
    int player_facing;
} PrototypeWorld;

void prototype_v1_init(PrototypeWorld *world);
void prototype_v1_step(PrototypeWorld *world, const PrototypeInput *input);

#endif
