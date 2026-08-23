#include <stdio.h>
#include <string.h>

#include "../../../src/port_v2/camera/camera.h"
#include "../../../src/port_v2/stage/stage.h"

static int layer_submissions;
static int priority_submissions;
static AvspPortV2StageLayerEvent submitted_layers[2];
static int submitted_actor_priority;
static int submitted_foreground_priority;

static int require_true(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static int submit_layer(const AvspPortV2StageLayerEvent *event)
{
    if (event == 0 || layer_submissions >= 2) return 0;
    submitted_layers[layer_submissions] = *event;
    ++layer_submissions;
    return 1;
}

static int submit_priorities(const int actor, const int foreground)
{
    ++priority_submissions;
    submitted_actor_priority = actor;
    submitted_foreground_priority = foreground;
    return 1;
}

static void replay(AvspPortV2CameraRuntime *runtime)
{
    AvspPortV2CameraInput input;
    int frame;
    avsp_port_v2_camera_init(runtime);
    for (frame = 0; frame <= 46; ++frame)
    {
        input.scroll_x[0] = frame < 46 ? 0 : 10;
        input.scroll_x[1] = frame < 46 ? 7 : 15;
        input.scroll_y[0] = 16;
        input.scroll_y[1] = 16;
        avsp_port_v2_camera_step(runtime, &input);
    }
}

static int runtime_equal(const AvspPortV2CameraRuntime *first,
                         const AvspPortV2CameraRuntime *second)
{
    int layer;
    if (first->scroll_steps != second->scroll_steps ||
        first->has_previous != second->has_previous) return 0;
    for (layer = 0; layer < AVSP_PORT_V2_CAMERA_LAYER_COUNT; ++layer)
        if (first->scroll_x[layer] != second->scroll_x[layer] ||
            first->scroll_y[layer] != second->scroll_y[layer] ||
            first->previous_scroll_x[layer] !=
                second->previous_scroll_x[layer] ||
            first->previous_scroll_y[layer] !=
                second->previous_scroll_y[layer]) return 0;
    return 1;
}

static int test_replay_and_render_port(void)
{
    AvspPortV2CameraRuntime first;
    AvspPortV2CameraRuntime second;
    AvspPortV2CameraView view;
    AvspPortV2StageFrame frame;
    AvspPortV2StageRenderOps operations;
    replay(&first);
    replay(&second);
    if (!require_true(runtime_equal(&first, &second),
                      "deterministic camera replay drifted")) return 0;
    avsp_port_v2_camera_view(&first, &view);
    if (!require_true(view.scroll_x[0] == 10 && view.scroll_x[1] == 15 &&
                      view.scroll_y[0] == 16 && view.scroll_y[1] == 16 &&
                      view.scroll_steps == 1 &&
                      view.source_width == 384 && view.output_width == 352 &&
                      view.output_height == 224,
                      "approved camera threshold drifted")) return 0;
    if (!require_true(avsp_port_v2_stage_build_frame(&view, &frame),
                      "stage semantic frame was rejected")) return 0;
    operations.submit_layer = submit_layer;
    operations.submit_sprite_priorities = submit_priorities;
    layer_submissions = 0;
    priority_submissions = 0;
    if (!require_true(avsp_port_v2_stage_submit(&frame, &operations),
                      "stage render port submission failed")) return 0;
    return require_true(layer_submissions == 2 && priority_submissions == 1 &&
                        submitted_layers[0].priority == 3 &&
                        submitted_layers[0].palette_bank == 2 &&
                        submitted_layers[1].priority == 2 &&
                        submitted_layers[1].palette_bank == 3 &&
                        submitted_actor_priority == 4 &&
                        submitted_foreground_priority == 6 &&
                        frame.row_scroll_status ==
                            AVSP_PORT_V2_STAGE_ROW_SCROLL_ADAPTED_UNCAPTURED,
                        "approved stage presentation event drifted");
}

static int test_negative_control(void)
{
    AvspPortV2CameraConfig camera = avsp_port_v2_camera_approved_config;
    AvspPortV2StageConfig stage = avsp_port_v2_stage_approved_config;
    AvspPortV2CameraRuntime runtime;
    AvspPortV2CameraView view;
    AvspPortV2StageFrame frame;
    AvspPortV2StageRenderOps operations;
    camera.output_width = 384;
    if (!require_true(!avsp_port_v2_camera_validate_config(&camera),
                      "384-wide camera mutation was accepted")) return 0;
    stage.layer_count = 1;
    if (!require_true(!avsp_port_v2_stage_validate_config(&stage),
                      "missing plane dependency was accepted")) return 0;
    stage = avsp_port_v2_stage_approved_config;
    stage.actor_priority = 2;
    if (!require_true(!avsp_port_v2_stage_validate_config(&stage),
                      "priority inversion was accepted")) return 0;
    avsp_port_v2_camera_init(&runtime);
    avsp_port_v2_camera_view(&runtime, &view);
    if (!avsp_port_v2_stage_build_frame(&view, &frame)) return 0;
    frame.layers[1].palette_bank = 2;
    operations.submit_layer = submit_layer;
    operations.submit_sprite_priorities = submit_priorities;
    if (!require_true(!avsp_port_v2_stage_submit(&frame, &operations),
                      "mutated plane dependency reached the render port"))
        return 0;
    return require_true(avsp_port_v2_camera_source_to_output(0) == 0 &&
                        avsp_port_v2_camera_source_to_output(383) == 351,
                        "endpoint-aligned 384-to-352 transform drifted");
}

int main(const int argc, char **argv)
{
    const int negative = argc == 2 &&
        strcmp(argv[1], "--negative-control") == 0;
    if (!require_true(avsp_port_v2_camera_validate_config(
            &avsp_port_v2_camera_approved_config),
            "approved camera config was rejected")) return 1;
    if (!require_true(avsp_port_v2_stage_validate_config(
            &avsp_port_v2_stage_approved_config),
            "approved stage config was rejected")) return 1;
    if (!test_replay_and_render_port()) return 1;
    if (negative && !test_negative_control()) return 1;
    puts(negative ? "Camera/stage port_v2 negative control: PASS" :
                    "Camera/stage port_v2 contract: PASS");
    return 0;
}
