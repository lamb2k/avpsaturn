#ifndef CAPABILITY_MODEL_H
#define CAPABILITY_MODEL_H

#define CAP_MAX_ENEMIES 8
#define CAP_WORLD_WIDTH 960
#define CAP_VIEW_WIDTH 352
#define CAP_CPS2_VIEW_WIDTH 384
#define CAP_BACKGROUND_WIDTH 512
#define CAP_FITTED_BACKGROUND_WIDTH 469
#define CAP_CENTER_CROP_X ((CAP_CPS2_VIEW_WIDTH - CAP_VIEW_WIDTH) / 2)
#define CAP_PLAYER_MAX_HEALTH 12
#define CAP_STAGE1_TOTAL_ENEMIES 8
#define CAP_BOSS_MAX_HEALTH 24
#define CAP_BOSS_TOTAL_ADDS 5

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

typedef enum
{
    CAP_ACTOR_PLAYER = 0,
    CAP_ACTOR_ALIEN,
    CAP_ACTOR_STALKER,
    CAP_ACTOR_BOSS
} CapActorKind;

typedef enum
{
    CAP_ENCOUNTER_MAIN_MENU = 0,
    CAP_ENCOUNTER_CHARACTER_SELECT,
    CAP_ENCOUNTER_ROUND_TITLE,
    CAP_ENCOUNTER_BARRICADE_INTRO,
    CAP_ENCOUNTER_WAVE_ONE,
    CAP_ENCOUNTER_WAVE_TWO,
    CAP_ENCOUNTER_CLEAR,
    CAP_ENCOUNTER_DOOR_DIALOGUE,
    CAP_ENCOUNTER_INTERIOR_TRANSITION,
    CAP_ENCOUNTER_BOSS_INTRO,
    CAP_ENCOUNTER_BOSS,
    CAP_ENCOUNTER_BOSS_DEFEAT,
    CAP_ENCOUNTER_STAGE_CLEAR,
    CAP_ENCOUNTER_RESULTS,
    CAP_ENCOUNTER_INTERMISSION,
    CAP_ENCOUNTER_COMPLETE
} CapEncounterState;

typedef struct
{
    int left;
    int right;
    int up;
    int down;
    int attack_pressed;
    int special_pressed;
    int dash_held;
    int start_pressed;
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
    int active;
    int variant;
    CapActorKind kind;
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
    CapEncounterState encounter_state;
    int encounter_timer;
    int enemies_defeated;
    int room_locked;
    int stage_transitioned;
    int stage_area;
    int boss_defeated;
    int boss_adds_spawned;
    int boss_adds_defeated;
    int boss_reinforcement_wave;
    int level_completed;
} CapWorld;

void cap_world_init(CapWorld *world);
CapClipRequest cap_world_step(CapWorld *world, const CapInput *input);
int cap_background_scroll_x(int camera_x, int stage_area);
int cap_background_fit_scroll_x(int camera_x, int stage_area);
int cap_actor_screen_x(int world_x, int camera_x, int full_width_fit);
int cap_stage1_route_event_count(void);
int cap_stage1_source_start_frame(void);
int cap_stage1_source_end_frame(void);

#endif
