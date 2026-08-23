#include "hud.h"

const AvspPortV2HudConfig avsp_port_v2_hud_approved_config = {
    101,
    64,
    116,
    59,
    384,
    352,
    1,
    33791,
    32799,
    48119,
    50737,
    {2, 2}
};

static int avsp_port_v2_hud_clamp(const int value, const int maximum)
{
    if (value < 0) return 0;
    if (value > maximum) return maximum;
    return value;
}

static int avsp_port_v2_hud_health_fill(const int health)
{
    int source_fill;
    int fill;
    int clamped;
    const AvspPortV2HudConfig *config = &avsp_port_v2_hud_approved_config;

    clamped = avsp_port_v2_hud_clamp(health, config->max_health);
    source_fill = (clamped * 5) / 4;
    fill = (source_fill * config->output_width + config->source_width - 1) /
           config->source_width;
    if (fill > config->health_width) fill = config->health_width;
    return fill;
}

static int avsp_port_v2_hud_energy_fill(const int energy)
{
    int clamped;
    const AvspPortV2HudConfig *config = &avsp_port_v2_hud_approved_config;

    clamped = avsp_port_v2_hud_clamp(energy, config->max_energy);
    return (clamped * config->energy_width + config->max_energy - 1) /
           config->max_energy;
}

int avsp_port_v2_hud_validate_config(const AvspPortV2HudConfig *config)
{
    if (config == 0) return 0;
    return config->max_health == 101 &&
           config->max_energy == 64 &&
           config->health_width == 116 &&
           config->energy_width == 59 &&
           config->source_width == 384 &&
           config->output_width == 352 &&
           config->palette_source_offset == 1 &&
           config->palette_yellow == 33791 &&
           config->palette_red == 32799 &&
           config->palette_energy == 48119 &&
           config->palette_empty == 50737 &&
           config->player_render_count[AVSP_PORT_V2_HUD_P1] == 2 &&
           config->player_render_count[AVSP_PORT_V2_HUD_P2] == 2;
}

int avsp_port_v2_hud_build_frame(const AvspPortV2HudInput *input,
                                 AvspPortV2HudFrame *frame)
{
    int index;
    const AvspPortV2HudConfig *config = &avsp_port_v2_hud_approved_config;

    if (input == 0 || frame == 0 ||
        !avsp_port_v2_hud_validate_config(config))
        return 0;
    frame->player_count = AVSP_PORT_V2_HUD_PLAYER_COUNT;
    frame->render_count = 0;
    for (index = 0; index < AVSP_PORT_V2_HUD_PLAYER_COUNT; ++index)
    {
        const AvspPortV2HudPlayerState *state = &input->players[index];
        AvspPortV2HudPlayerView *view = &frame->players[index];
        view->player_id = index;
        view->character_id = state->character_id;
        view->visible = state->visible ? 1 : 0;
        view->health = avsp_port_v2_hud_clamp(state->health,
                                              config->max_health);
        view->energy = avsp_port_v2_hud_clamp(state->energy,
                                              config->max_energy);
        view->health_fill = avsp_port_v2_hud_health_fill(view->health);
        view->energy_fill = avsp_port_v2_hud_energy_fill(view->energy);
        view->render_count = view->visible ?
            config->player_render_count[index] : 0;
        frame->render_count += view->render_count;
    }
    return 1;
}

int avsp_port_v2_hud_submit(const AvspPortV2HudFrame *frame,
                            const AvspPortV2HudRenderOps *operations)
{
    if (frame == 0 || operations == 0 || operations->submit_frame == 0)
        return 0;
    return operations->submit_frame(frame);
}
