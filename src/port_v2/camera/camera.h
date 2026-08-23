#ifndef AVSP_PORT_V2_CAMERA_H
#define AVSP_PORT_V2_CAMERA_H

#define AVSP_PORT_V2_CAMERA_INTERFACE_VERSION 1
#define AVSP_PORT_V2_CAMERA_LAYER_COUNT 2

typedef struct
{
    int source_width;
    int output_width;
    int output_height;
} AvspPortV2CameraConfig;

typedef struct
{
    int scroll_x[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int scroll_y[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
} AvspPortV2CameraInput;

typedef struct
{
    int scroll_x[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int scroll_y[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int previous_scroll_x[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int previous_scroll_y[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int scroll_steps;
    int has_previous;
} AvspPortV2CameraRuntime;

typedef struct
{
    int scroll_x[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int scroll_y[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int scroll_steps;
    int source_width;
    int output_width;
    int output_height;
} AvspPortV2CameraView;

extern const AvspPortV2CameraConfig avsp_port_v2_camera_approved_config;

int avsp_port_v2_camera_validate_config(const AvspPortV2CameraConfig *config);
int avsp_port_v2_camera_source_to_output(int source_x);
void avsp_port_v2_camera_init(AvspPortV2CameraRuntime *runtime);
void avsp_port_v2_camera_step(AvspPortV2CameraRuntime *runtime,
                              const AvspPortV2CameraInput *input);
void avsp_port_v2_camera_view(const AvspPortV2CameraRuntime *runtime,
                              AvspPortV2CameraView *view);

#endif
