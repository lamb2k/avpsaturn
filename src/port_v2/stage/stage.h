#ifndef AVSP_PORT_V2_STAGE_H
#define AVSP_PORT_V2_STAGE_H

#include "../camera/camera.h"

#define AVSP_PORT_V2_STAGE_INTERFACE_VERSION 1
#define AVSP_PORT_V2_STAGE_LAYER_COUNT 2
#define AVSP_PORT_V2_STAGE_ROW_SCROLL_ADAPTED_UNCAPTURED 1

typedef struct
{
    int layer_count;
    int layer_priority[AVSP_PORT_V2_STAGE_LAYER_COUNT];
    int layer_palette_bank[AVSP_PORT_V2_STAGE_LAYER_COUNT];
    int actor_priority;
    int foreground_priority;
    int row_scroll_status;
} AvspPortV2StageConfig;

typedef struct
{
    int layer_id;
    int scroll_x;
    int scroll_y;
    int priority;
    int palette_bank;
} AvspPortV2StageLayerEvent;

typedef struct
{
    AvspPortV2StageLayerEvent layers[AVSP_PORT_V2_STAGE_LAYER_COUNT];
    int layer_count;
    int actor_priority;
    int foreground_priority;
    int row_scroll_status;
} AvspPortV2StageFrame;

typedef int (*AvspPortV2StageSubmitLayer)(
    const AvspPortV2StageLayerEvent *event);
typedef int (*AvspPortV2StageSubmitSpritePriorities)(
    int actor_priority, int foreground_priority);

typedef struct
{
    AvspPortV2StageSubmitLayer submit_layer;
    AvspPortV2StageSubmitSpritePriorities submit_sprite_priorities;
} AvspPortV2StageRenderOps;

extern const AvspPortV2StageConfig avsp_port_v2_stage_approved_config;

int avsp_port_v2_stage_validate_config(const AvspPortV2StageConfig *config);
int avsp_port_v2_stage_build_frame(const AvspPortV2CameraView *camera,
                                   AvspPortV2StageFrame *frame);
int avsp_port_v2_stage_submit(const AvspPortV2StageFrame *frame,
                              const AvspPortV2StageRenderOps *operations);

#endif
