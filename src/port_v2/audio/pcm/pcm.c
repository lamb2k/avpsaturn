#include <string.h>

#include "pcm.h"

const AvspPortV2PcmConfig avsp_port_v2_pcm_predator_melee_config = {
    AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE,
    144752,
    44100,
    2,
    16,
    1,
    3,
    50,
    "e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125"
};

int avsp_port_v2_pcm_validate_config(const AvspPortV2PcmConfig *config)
{
    if (config == 0 || config->payload_sha256 == 0) return 0;
    return config->cue_id == AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE &&
           config->payload_bytes == 144752 &&
           config->sample_rate == 44100 &&
           config->channels == 2 &&
           config->sample_bits == 16 &&
           config->scsp_channel == 1 &&
           config->start_delay_frames == 3 &&
           config->duration_frames == 50 &&
           strcmp(config->payload_sha256,
                  "e2f2870251cf28c5cf52d0d074c3b426cc6db5afb4cde2eebf4838ffa296f125") == 0;
}

void avsp_port_v2_pcm_init(AvspPortV2PcmRuntime *runtime)
{
    if (runtime == 0) return;
    memset(runtime, 0, sizeof(*runtime));
    runtime->event_frame = -1;
    runtime->start_frame = -1;
    runtime->end_frame = -1;
}

int avsp_port_v2_pcm_step(AvspPortV2PcmRuntime *runtime,
                          const AvspPortV2PcmInput *input,
                          AvspPortV2PcmFrame *frame)
{
    const AvspPortV2PcmConfig *config =
        &avsp_port_v2_pcm_predator_melee_config;

    if (runtime == 0 || input == 0 || frame == 0 ||
        !avsp_port_v2_pcm_validate_config(config))
        return 0;
    if (input->cue_event)
    {
        if (input->cue_id != config->cue_id || runtime->pending ||
            runtime->active)
            return 0;
        runtime->pending = 1;
        runtime->event_frame = input->frame;
        ++runtime->event_count;
    }
    memset(frame, 0, sizeof(*frame));
    frame->cue_id = config->cue_id;
    if (runtime->pending &&
        input->frame == runtime->event_frame + config->start_delay_frames)
    {
        runtime->pending = 0;
        runtime->active = 1;
        runtime->start_frame = input->frame;
        runtime->end_frame = input->frame + config->duration_frames;
        frame->start_request = 1;
    }
    if (runtime->active && input->frame == runtime->end_frame)
    {
        runtime->active = 0;
        frame->stop_request = 1;
    }
    frame->active = runtime->active;
    frame->event_count = runtime->event_count;
    frame->event_frame = runtime->event_frame;
    frame->start_frame = runtime->start_frame;
    frame->end_frame = runtime->end_frame;
    return 1;
}

int avsp_port_v2_pcm_submit(const AvspPortV2PcmFrame *frame,
                            const AvspPortV2PcmAudioOps *operations)
{
    if (frame == 0 || operations == 0 || operations->start == 0 ||
        operations->stop == 0)
        return 0;
    if (frame->start_request && !operations->start(frame)) return 0;
    if (frame->stop_request && !operations->stop(frame)) return 0;
    return 1;
}
