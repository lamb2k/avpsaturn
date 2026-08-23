#ifndef AVSP_PORT_V2_HUD_H
#define AVSP_PORT_V2_HUD_H

#define AVSP_PORT_V2_HUD_INTERFACE_VERSION 1
#define AVSP_PORT_V2_HUD_PLAYER_COUNT 2
#define AVSP_PORT_V2_HUD_P1 0
#define AVSP_PORT_V2_HUD_P2 1
#define AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR 0
#define AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER 1

typedef struct
{
    int max_health;
    int max_energy;
    int health_width;
    int energy_width;
    int source_width;
    int output_width;
    int palette_source_offset;
    int palette_yellow;
    int palette_red;
    int palette_energy;
    int palette_empty;
    int player_render_count[AVSP_PORT_V2_HUD_PLAYER_COUNT];
} AvspPortV2HudConfig;

typedef struct
{
    int visible;
    int character_id;
    int health;
    int energy;
} AvspPortV2HudPlayerState;

typedef struct
{
    AvspPortV2HudPlayerState players[AVSP_PORT_V2_HUD_PLAYER_COUNT];
} AvspPortV2HudInput;

typedef struct
{
    int player_id;
    int character_id;
    int visible;
    int health;
    int energy;
    int health_fill;
    int energy_fill;
    int render_count;
} AvspPortV2HudPlayerView;

typedef struct
{
    AvspPortV2HudPlayerView players[AVSP_PORT_V2_HUD_PLAYER_COUNT];
    int player_count;
    int render_count;
} AvspPortV2HudFrame;

typedef int (*AvspPortV2HudSubmitFrame)(const AvspPortV2HudFrame *frame);

typedef struct
{
    AvspPortV2HudSubmitFrame submit_frame;
} AvspPortV2HudRenderOps;

extern const AvspPortV2HudConfig avsp_port_v2_hud_approved_config;

int avsp_port_v2_hud_validate_config(const AvspPortV2HudConfig *config);
int avsp_port_v2_hud_build_frame(const AvspPortV2HudInput *input,
                                 AvspPortV2HudFrame *frame);
int avsp_port_v2_hud_submit(const AvspPortV2HudFrame *frame,
                            const AvspPortV2HudRenderOps *operations);

#endif
