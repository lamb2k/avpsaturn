#ifndef AVSP_PORT_V2_AUDIO_CDDA_H
#define AVSP_PORT_V2_AUDIO_CDDA_H

#define AVSP_PORT_V2_CDDA_INTERFACE_VERSION 1
#define AVSP_PORT_V2_CDDA_TRACK_STAGE1 2
#define AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1 2520

enum AvspPortV2CddaCommand
{
    AVSP_PORT_V2_CDDA_NONE = 0,
    AVSP_PORT_V2_CDDA_START,
    AVSP_PORT_V2_CDDA_STOP
};

typedef struct
{
    int track;
    int source_frame;
    int repeat;
    int payload_bytes;
    const char *payload_sha256;
} AvspPortV2CddaConfig;

typedef struct
{
    int command;
    int track;
    int source_frame;
} AvspPortV2CddaInput;

typedef struct
{
    int active;
    int track;
    int source_frame;
    int event_count;
    int ownership_transitions;
} AvspPortV2CddaRuntime;

typedef struct
{
    int track;
    int source_frame;
    int repeat;
    int start_request;
    int stop_request;
    int active;
    int event_count;
    int ownership_transitions;
} AvspPortV2CddaFrame;

typedef int (*AvspPortV2CddaStart)(const AvspPortV2CddaFrame *frame);
typedef int (*AvspPortV2CddaStop)(const AvspPortV2CddaFrame *frame);

typedef struct
{
    AvspPortV2CddaStart start;
    AvspPortV2CddaStop stop;
} AvspPortV2CddaAudioOps;

extern const AvspPortV2CddaConfig avsp_port_v2_cdda_stage1_config;

int avsp_port_v2_cdda_validate_config(const AvspPortV2CddaConfig *config);
void avsp_port_v2_cdda_init(AvspPortV2CddaRuntime *runtime);
int avsp_port_v2_cdda_step(AvspPortV2CddaRuntime *runtime,
                           const AvspPortV2CddaInput *input,
                           AvspPortV2CddaFrame *frame);
int avsp_port_v2_cdda_submit(const AvspPortV2CddaFrame *frame,
                             const AvspPortV2CddaAudioOps *operations);

#endif
