#include "camera.h"

const AvspPortV2CameraConfig avsp_port_v2_camera_approved_config =
{
    384, 352, 224
};

int avsp_port_v2_camera_validate_config(const AvspPortV2CameraConfig *config)
{
    const AvspPortV2CameraConfig *approved =
        &avsp_port_v2_camera_approved_config;
    if (config == 0) return 0;
    return config->source_width == approved->source_width &&
           config->output_width == approved->output_width &&
           config->output_height == approved->output_height;
}

int avsp_port_v2_camera_source_to_output(const int source_x)
{
    return (source_x * 351 - 175 + 382) / 383;
}

void avsp_port_v2_camera_init(AvspPortV2CameraRuntime *runtime)
{
    int layer;
    if (runtime == 0) return;
    for (layer = 0; layer < AVSP_PORT_V2_CAMERA_LAYER_COUNT; ++layer)
    {
        runtime->scroll_x[layer] = 0;
        runtime->scroll_y[layer] = 0;
        runtime->previous_scroll_x[layer] = 0;
        runtime->previous_scroll_y[layer] = 0;
    }
    runtime->scroll_steps = 0;
    runtime->has_previous = 0;
}

void avsp_port_v2_camera_step(AvspPortV2CameraRuntime *runtime,
                              const AvspPortV2CameraInput *input)
{
    int changed;
    int layer;
    if (runtime == 0 || input == 0) return;
    changed = 0;
    for (layer = 0; layer < AVSP_PORT_V2_CAMERA_LAYER_COUNT; ++layer)
    {
        if (runtime->has_previous &&
            (input->scroll_x[layer] != runtime->scroll_x[layer] ||
             input->scroll_y[layer] != runtime->scroll_y[layer]))
            changed = 1;
        runtime->previous_scroll_x[layer] = runtime->scroll_x[layer];
        runtime->previous_scroll_y[layer] = runtime->scroll_y[layer];
        runtime->scroll_x[layer] = input->scroll_x[layer];
        runtime->scroll_y[layer] = input->scroll_y[layer];
    }
    if (changed) ++runtime->scroll_steps;
    runtime->has_previous = 1;
}

void avsp_port_v2_camera_view(const AvspPortV2CameraRuntime *runtime,
                              AvspPortV2CameraView *view)
{
    int layer;
    if (runtime == 0 || view == 0) return;
    for (layer = 0; layer < AVSP_PORT_V2_CAMERA_LAYER_COUNT; ++layer)
    {
        view->scroll_x[layer] = runtime->scroll_x[layer];
        view->scroll_y[layer] = runtime->scroll_y[layer];
    }
    view->scroll_steps = runtime->scroll_steps;
    view->source_width = avsp_port_v2_camera_approved_config.source_width;
    view->output_width = avsp_port_v2_camera_approved_config.output_width;
    view->output_height = avsp_port_v2_camera_approved_config.output_height;
}
