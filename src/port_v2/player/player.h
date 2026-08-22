#ifndef AVSP_PORT_V2_PLAYER_H
#define AVSP_PORT_V2_PLAYER_H

#define AVSP_PORT_V2_PLAYER_INTERFACE_VERSION 1

#define AVSP_PORT_V2_PLAYER_INPUT_LEFT 1
#define AVSP_PORT_V2_PLAYER_INPUT_RIGHT 2
#define AVSP_PORT_V2_PLAYER_INPUT_UP 4
#define AVSP_PORT_V2_PLAYER_INPUT_DOWN 8

#define AVSP_PORT_V2_PLAYER_ACTION_IDLE 0
#define AVSP_PORT_V2_PLAYER_ACTION_WALK 1

typedef struct
{
    int minimum_x;
    int maximum_x;
    int minimum_lane;
    int maximum_lane;
    int horizontal_step;
    int vertical_step;
    int idle_layers;
    int walk_layers;
    int idle_left;
    int idle_top;
    int idle_right;
    int idle_bottom;
} AvspPortV2PlayerConfig;

typedef struct
{
    int left;
    int right;
    int up;
    int down;
} AvspPortV2PlayerInput;

typedef struct
{
    int x;
    int lane;
    int facing;
    int action;
    int locomotion_frame;
    int input_mask;
    int input_edges;
    int previous_input_mask;
} AvspPortV2PlayerRuntime;

typedef struct
{
    int world_x;
    int lane;
    int facing;
    int action;
    int locomotion_frame;
    int render_layers;
} AvspPortV2PlayerView;

typedef int (*AvspPortV2PlayerLoadStep)(void);

typedef struct
{
    AvspPortV2PlayerLoadStep load_background;
    AvspPortV2PlayerLoadStep load_idle_cels;
    AvspPortV2PlayerLoadStep load_action_sequences;
    AvspPortV2PlayerLoadStep create_sprite_working_set;
} AvspPortV2PlayerLoadOps;

extern const AvspPortV2PlayerConfig avsp_port_v2_player_approved_config;

int avsp_port_v2_player_validate_config(const AvspPortV2PlayerConfig *config);
int avsp_port_v2_player_load(int cartridge_available,
                             const AvspPortV2PlayerLoadOps *operations);
void avsp_port_v2_player_init(AvspPortV2PlayerRuntime *runtime);
void avsp_port_v2_player_step(AvspPortV2PlayerRuntime *runtime,
                              const AvspPortV2PlayerInput *input);
void avsp_port_v2_player_view(const AvspPortV2PlayerRuntime *runtime,
                              AvspPortV2PlayerView *view);
int avsp_port_v2_player_bounds_valid(int left, int top, int right, int bottom);

#endif
