#ifndef AVSP_PORT_V2_PLAYER_ACTION_H
#define AVSP_PORT_V2_PLAYER_ACTION_H

#define AVSP_PW_ACTION_BENCH_INTERFACE_VERSION 2
#define AVSP_PW_ACTION_COUNT 4
#define AVSP_PW_DIRECTION_LATENCY 2

#define AVSP_PW_INPUT_LEFT 0x0004u
#define AVSP_PW_INPUT_RIGHT 0x0008u
#define AVSP_PW_INPUT_ATTACK 0x0020u
#define AVSP_PW_INPUT_UP 0x0080u
#define AVSP_PW_INPUT_DOWN 0x0100u

#define AVSP_PW_STATE_CONTROL 0
#define AVSP_PW_STATE_ATTACK 1
#define AVSP_PW_STATE_HIT 2
#define AVSP_PW_STATE_KO 3

#define AVSP_PW_PHASE_NONE 0
#define AVSP_PW_PHASE_STARTUP 1
#define AVSP_PW_PHASE_ACTIVE 2
#define AVSP_PW_PHASE_RECOVERY 3

typedef struct
{
    short x_center;
    short x_half;
    short y_center;
    short y_half;
    short z_center;
    short z_half;
    short hit_value;
} AvspPwAttackBox;

typedef struct
{
    unsigned short selector;
    unsigned short presentation_first;
    unsigned short active_first;
    unsigned short active_last;
    unsigned short return_frame;
    unsigned short source_action;
    AvspPwAttackBox box;
} AvspPwAttackDef;

typedef struct
{
    unsigned short mask;
    short received_damage;
} AvspPwInput;

typedef struct
{
    long x_numerator;
    long lane_numerator;
    short x;
    short lane;
    short height;
    short health;
    short facing;
    unsigned short state;
    unsigned short phase;
    unsigned short selector;
    unsigned short action_elapsed;
    unsigned short source_action;
    unsigned short source_substate;
    unsigned short attack_active;
    unsigned short hit_timer;
    unsigned short combo_next;
    unsigned short combo_idle_frames;
    unsigned short completed_close_step;
    unsigned short combo_followup_counter;
    unsigned short action_local_equipment_flag;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned short current_mask;
    unsigned short previous_mask;
    unsigned short input_edges;
    unsigned short direction_history[AVSP_PW_DIRECTION_LATENCY];
    unsigned long accepted_attack_edges;
    unsigned long rejected_attack_edges;
    unsigned long contact_reports;
} AvspPwRuntime;

typedef struct
{
    short x;
    short lane;
    short height;
    short health;
    short facing;
    unsigned short state;
    unsigned short phase;
    unsigned short selector;
    unsigned short action_elapsed;
    unsigned short source_action;
    unsigned short source_substate;
    unsigned short attack_active;
    unsigned short completed_close_step;
    unsigned short combo_followup_counter;
    unsigned short action_local_equipment_flag;
    unsigned long animation_record;
    unsigned long assembly;
    AvspPwAttackBox attack_box;
} AvspPwView;

extern const AvspPwAttackDef avsp_pw_action_defs[AVSP_PW_ACTION_COUNT];

int avsp_pw_action_defs_valid(const AvspPwAttackDef *defs, unsigned int count);
int avsp_pw_render_facing(unsigned short source_facing);
int avsp_pw_source_presentation_ready(unsigned short selector,
                                      unsigned short action_elapsed);
unsigned long avsp_pw_assembly_for_record(unsigned long animation_record);
void avsp_pw_resolve_navigation(short *world_x, short *world_z);
void avsp_pw_init(AvspPwRuntime *runtime);
void avsp_pw_step(AvspPwRuntime *runtime, const AvspPwInput *input);
void avsp_pw_step_round1(AvspPwRuntime *runtime, const AvspPwInput *input);
void avsp_pw_view(const AvspPwRuntime *runtime, AvspPwView *view);
void avsp_pw_report_contact(AvspPwRuntime *runtime);
int avsp_pw_can_control(const AvspPwRuntime *runtime);

#endif
