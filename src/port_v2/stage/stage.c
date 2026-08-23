#include "stage.h"

const AvspPortV2StageConfig avsp_port_v2_stage_approved_config =
{
    2,
    {3, 2},
    {2, 3},
    4,
    6,
    AVSP_PORT_V2_STAGE_ROW_SCROLL_ADAPTED_UNCAPTURED
};

int avsp_port_v2_stage_validate_config(const AvspPortV2StageConfig *config)
{
    const AvspPortV2StageConfig *approved = &avsp_port_v2_stage_approved_config;
    int layer;
    if (config == 0 || config->layer_count != approved->layer_count ||
        config->actor_priority != approved->actor_priority ||
        config->foreground_priority != approved->foreground_priority ||
        config->row_scroll_status != approved->row_scroll_status)
        return 0;
    for (layer = 0; layer < AVSP_PORT_V2_STAGE_LAYER_COUNT; ++layer)
        if (config->layer_priority[layer] != approved->layer_priority[layer] ||
            config->layer_palette_bank[layer] !=
                approved->layer_palette_bank[layer])
            return 0;
    return approved->layer_priority[1] < approved->layer_priority[0] &&
           approved->layer_priority[0] < approved->actor_priority &&
           approved->actor_priority < approved->foreground_priority;
}

int avsp_port_v2_stage_build_frame(const AvspPortV2CameraView *camera,
                                   AvspPortV2StageFrame *frame)
{
    int layer;
    if (camera == 0 || frame == 0 ||
        camera->source_width != 384 || camera->output_width != 352 ||
        camera->output_height != 224 ||
        !avsp_port_v2_stage_validate_config(
            &avsp_port_v2_stage_approved_config))
        return 0;
    frame->layer_count = AVSP_PORT_V2_STAGE_LAYER_COUNT;
    for (layer = 0; layer < AVSP_PORT_V2_STAGE_LAYER_COUNT; ++layer)
    {
        frame->layers[layer].layer_id = layer;
        frame->layers[layer].scroll_x = camera->scroll_x[layer];
        frame->layers[layer].scroll_y = camera->scroll_y[layer];
        frame->layers[layer].priority =
            avsp_port_v2_stage_approved_config.layer_priority[layer];
        frame->layers[layer].palette_bank =
            avsp_port_v2_stage_approved_config.layer_palette_bank[layer];
    }
    frame->actor_priority = avsp_port_v2_stage_approved_config.actor_priority;
    frame->foreground_priority =
        avsp_port_v2_stage_approved_config.foreground_priority;
    frame->row_scroll_status =
        avsp_port_v2_stage_approved_config.row_scroll_status;
    return 1;
}

int avsp_port_v2_stage_submit(const AvspPortV2StageFrame *frame,
                              const AvspPortV2StageRenderOps *operations)
{
    int layer;
    if (frame == 0 || operations == 0 || operations->submit_layer == 0 ||
        operations->submit_sprite_priorities == 0 ||
        frame->layer_count != AVSP_PORT_V2_STAGE_LAYER_COUNT ||
        frame->row_scroll_status !=
            AVSP_PORT_V2_STAGE_ROW_SCROLL_ADAPTED_UNCAPTURED)
        return 0;
    for (layer = 0; layer < AVSP_PORT_V2_STAGE_LAYER_COUNT; ++layer)
    {
        const AvspPortV2StageLayerEvent *event = &frame->layers[layer];
        if (event->layer_id != layer ||
            event->priority !=
                avsp_port_v2_stage_approved_config.layer_priority[layer] ||
            event->palette_bank !=
                avsp_port_v2_stage_approved_config.layer_palette_bank[layer] ||
            !operations->submit_layer(event))
            return 0;
    }
    return operations->submit_sprite_priorities(
        frame->actor_priority, frame->foreground_priority);
}
