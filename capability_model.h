#ifndef CAPABILITY_MODEL_H
#define CAPABILITY_MODEL_H

#define CAP_MAX_ENEMIES 4
#define CAP_WORLD_WIDTH 960
#define CAP_VIEW_WIDTH 352
#define CAP_PLAYER_MAX_HEALTH 12

typedef enum
{
    CAP_ACT_IDLE = 0,
    CAP_ACT_WALK,
    CAP_ACT_ATTACK,
    CAP_ACT_SPECIAL,
    CAP_ACT_HIT,
    CAP_ACT_KO
} CapAction;

typedef enum
{
    CAP_CLIP_NONE = 0,
    CAP_CLIP_ATTACK,
    CAP_CLIP_SPECIAL
} CapClipRequest;

typedef struct
{
    int left;
    int right;
    int up;
    int down;
    int attack_pressed;
    int special_pressed;
    int dash_held;
} CapInput;

typedef struct
{
    int x;
    int lane;
    int facing;
    int health;
    CapAction action;
    int action_frame;
    int locomotion_frame;
    int hit_latched;
} CapActor;

typedef struct
{
    CapActor player;
    CapActor enemies[CAP_MAX_ENEMIES];
    int camera_x;
    int frame;
    int score;
    int player_ko_timer;
    int encounter_started;
} CapWorld;

void cap_world_init(CapWorld *world);
CapClipRequest cap_world_step(CapWorld *world, const CapInput *input);

#endif
