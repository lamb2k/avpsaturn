#include <string.h>

#include "cdda.h"

const AvspPortV2CddaConfig avsp_port_v2_cdda_stage1_config =
{
    AVSP_PORT_V2_CDDA_TRACK_STAGE1,
    AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1,
    1,
    29637952,
    "42e755b02ba0e59e514a07dabe2f8273390e641c2ab410e4af8b7f1b656f2a43"
};

int avsp_port_v2_cdda_validate_config(const AvspPortV2CddaConfig *config)
{
    if (config == 0 || config->payload_sha256 == 0) return 0;
    return config->track == AVSP_PORT_V2_CDDA_TRACK_STAGE1 &&
           config->source_frame == AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1 &&
           config->repeat == 1 &&
           config->payload_bytes == 29637952 &&
           strcmp(config->payload_sha256,
                  "42e755b02ba0e59e514a07dabe2f8273390e641c2ab410e4af8b7f1b656f2a43") == 0;
}

void avsp_port_v2_cdda_init(AvspPortV2CddaRuntime *runtime)
{
    if (runtime == 0) return;
    memset(runtime, 0, sizeof(*runtime));
}

int avsp_port_v2_cdda_step(AvspPortV2CddaRuntime *runtime,
                           const AvspPortV2CddaInput *input,
                           AvspPortV2CddaFrame *frame)
{
    const AvspPortV2CddaConfig *config = &avsp_port_v2_cdda_stage1_config;

    if (runtime == 0 || input == 0 || frame == 0 ||
        !avsp_port_v2_cdda_validate_config(config))
        return 0;
    memset(frame, 0, sizeof(*frame));
    frame->track = config->track;
    frame->source_frame = config->source_frame;
    frame->repeat = config->repeat;
    if (input->command == AVSP_PORT_V2_CDDA_START)
    {
        if (runtime->active || input->track != config->track ||
            input->source_frame != config->source_frame)
            return 0;
        runtime->active = 1;
        runtime->track = input->track;
        runtime->source_frame = input->source_frame;
        ++runtime->event_count;
        ++runtime->ownership_transitions;
        frame->start_request = 1;
    }
    else if (input->command == AVSP_PORT_V2_CDDA_STOP)
    {
        if (!runtime->active || input->track != runtime->track ||
            input->source_frame != runtime->source_frame)
            return 0;
        runtime->active = 0;
        ++runtime->ownership_transitions;
        frame->stop_request = 1;
    }
    else if (input->command != AVSP_PORT_V2_CDDA_NONE)
        return 0;
    frame->active = runtime->active;
    frame->event_count = runtime->event_count;
    frame->ownership_transitions = runtime->ownership_transitions;
    return 1;
}

int avsp_port_v2_cdda_submit(const AvspPortV2CddaFrame *frame,
                             const AvspPortV2CddaAudioOps *operations)
{
    if (frame == 0 || operations == 0 || operations->start == 0 ||
        operations->stop == 0)
        return 0;
    if (frame->start_request && !operations->start(frame)) return 0;
    if (frame->stop_request && !operations->stop(frame)) return 0;
    return 1;
}
