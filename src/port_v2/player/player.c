#include "player.h"

const AvspPortV2PlayerConfig avsp_port_v2_player_approved_config =
{
    48, 304, 138, 218,
    2, 1,
    2, 3,
    56, 74, 136, 184
};

int avsp_port_v2_player_validate_config(const AvspPortV2PlayerConfig *config)
{
    const AvspPortV2PlayerConfig *approved =
        &avsp_port_v2_player_approved_config;
    if (config == 0) return 0;
    return config->minimum_x == approved->minimum_x &&
           config->maximum_x == approved->maximum_x &&
           config->minimum_lane == approved->minimum_lane &&
           config->maximum_lane == approved->maximum_lane &&
           config->horizontal_step == approved->horizontal_step &&
           config->vertical_step == approved->vertical_step &&
           config->idle_layers == approved->idle_layers &&
           config->walk_layers == approved->walk_layers &&
           config->idle_left == approved->idle_left &&
           config->idle_top == approved->idle_top &&
           config->idle_right == approved->idle_right &&
           config->idle_bottom == approved->idle_bottom;
}

int avsp_port_v2_player_load(const int cartridge_available,
                             const AvspPortV2PlayerLoadOps *operations)
{
    if (!cartridge_available || operations == 0 ||
        operations->load_background == 0 ||
        operations->load_idle_cels == 0 ||
        operations->load_action_sequences == 0 ||
        operations->create_sprite_working_set == 0)
        return 0;
    return operations->load_background() &&
           operations->load_idle_cels() &&
           operations->load_action_sequences() &&
           operations->create_sprite_working_set();
}

void avsp_port_v2_player_init(AvspPortV2PlayerRuntime *runtime)
{
    if (runtime == 0) return;
    runtime->x = 192;
    runtime->lane = 178;
    runtime->facing = 1;
    runtime->action = AVSP_PORT_V2_PLAYER_ACTION_IDLE;
    runtime->locomotion_frame = 0;
    runtime->input_mask = 0;
    runtime->input_edges = 0;
    runtime->previous_input_mask = 0;
}

void avsp_port_v2_player_step(AvspPortV2PlayerRuntime *runtime,
                              const AvspPortV2PlayerInput *input)
{
    int moving;
    int mask;
    if (runtime == 0 || input == 0) return;
    moving = 0;
    mask = (input->left ? AVSP_PORT_V2_PLAYER_INPUT_LEFT : 0) |
           (input->right ? AVSP_PORT_V2_PLAYER_INPUT_RIGHT : 0) |
           (input->up ? AVSP_PORT_V2_PLAYER_INPUT_UP : 0) |
           (input->down ? AVSP_PORT_V2_PLAYER_INPUT_DOWN : 0);

    if (input->left && !input->right)
    {
        runtime->x -= avsp_port_v2_player_approved_config.horizontal_step;
        runtime->facing = -1;
        moving = 1;
    }
    else if (input->right && !input->left)
    {
        runtime->x += avsp_port_v2_player_approved_config.horizontal_step;
        runtime->facing = 1;
        moving = 1;
    }
    if (input->up && !input->down)
    {
        runtime->lane -= avsp_port_v2_player_approved_config.vertical_step;
        moving = 1;
    }
    else if (input->down && !input->up)
    {
        runtime->lane += avsp_port_v2_player_approved_config.vertical_step;
        moving = 1;
    }

    if (runtime->x < avsp_port_v2_player_approved_config.minimum_x)
        runtime->x = avsp_port_v2_player_approved_config.minimum_x;
    if (runtime->x > avsp_port_v2_player_approved_config.maximum_x)
        runtime->x = avsp_port_v2_player_approved_config.maximum_x;
    if (runtime->lane < avsp_port_v2_player_approved_config.minimum_lane)
        runtime->lane = avsp_port_v2_player_approved_config.minimum_lane;
    if (runtime->lane > avsp_port_v2_player_approved_config.maximum_lane)
        runtime->lane = avsp_port_v2_player_approved_config.maximum_lane;

    runtime->action = moving ? AVSP_PORT_V2_PLAYER_ACTION_WALK :
                               AVSP_PORT_V2_PLAYER_ACTION_IDLE;
    if (moving) ++runtime->locomotion_frame;
    runtime->input_mask = mask;
    if (mask == 0)
        runtime->input_edges = 0;
    else
        runtime->input_edges |= mask & ~runtime->previous_input_mask;
    runtime->previous_input_mask = mask;
}

void avsp_port_v2_player_view(const AvspPortV2PlayerRuntime *runtime,
                              AvspPortV2PlayerView *view)
{
    if (runtime == 0 || view == 0) return;
    view->world_x = runtime->x;
    view->lane = runtime->lane;
    view->facing = runtime->facing;
    view->action = runtime->action;
    view->locomotion_frame = runtime->locomotion_frame;
    view->render_layers = runtime->action == AVSP_PORT_V2_PLAYER_ACTION_WALK ?
        avsp_port_v2_player_approved_config.walk_layers :
        avsp_port_v2_player_approved_config.idle_layers;
}

int avsp_port_v2_player_bounds_valid(const int left, const int top,
                                     const int right, const int bottom)
{
    return left >= 0 && top >= 0 && right > left && bottom > top &&
           right <= 192 && bottom <= 192;
}
