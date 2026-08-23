#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/audio/pcm/pcm.h"

static int starts;
static int stops;

static int capture_start(const AvspPortV2PcmFrame *frame)
{
    if (frame->cue_id != AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE) return 0;
    ++starts;
    return 1;
}

static int capture_stop(const AvspPortV2PcmFrame *frame)
{
    if (frame->cue_id != AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE) return 0;
    ++stops;
    return 1;
}

static int expect(const int condition, const char *message)
{
    if (!condition)
    {
        fprintf(stderr, "%s\n", message);
        return 0;
    }
    return 1;
}

static int run_sequence(AvspPortV2PcmFrame *final)
{
    AvspPortV2PcmRuntime runtime;
    AvspPortV2PcmInput input;
    AvspPortV2PcmFrame frame;
    AvspPortV2PcmAudioOps operations;
    int tick;

    avsp_port_v2_pcm_init(&runtime);
    operations.start = capture_start;
    operations.stop = capture_stop;
    for (tick = 0; tick <= 200; ++tick)
    {
        input.frame = tick;
        input.cue_event = tick == 147;
        input.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
        if (!avsp_port_v2_pcm_step(&runtime, &input, &frame) ||
            !avsp_port_v2_pcm_submit(&frame, &operations))
            return 0;
        if (tick == 147 && !expect(frame.event_count == 1 &&
                                   frame.event_frame == 147 &&
                                   frame.start_request == 0,
                                   "semantic event timing drifted")) return 0;
        if (tick == 150 && !expect(frame.start_request == 1 &&
                                   frame.start_frame == 150 &&
                                   frame.end_frame == 200 && frame.active == 1,
                                   "semantic start timing drifted")) return 0;
        if (tick == 200 && !expect(frame.stop_request == 1 &&
                                   frame.active == 0,
                                   "semantic stop timing drifted")) return 0;
    }
    *final = frame;
    return 1;
}

int main(const int argc, char **argv)
{
    AvspPortV2PcmConfig rejected;
    AvspPortV2PcmRuntime runtime;
    AvspPortV2PcmInput input;
    AvspPortV2PcmFrame first;
    AvspPortV2PcmFrame second;
    int negative = 0;

    if (argc == 2 && strcmp(argv[1], "--wrong-cue") == 0) negative = 1;
    if (argc == 2 && strcmp(argv[1], "--wrong-timing") == 0) negative = 2;
    if (argc > 2 || (argc == 2 && negative == 0)) return 2;
    rejected = avsp_port_v2_pcm_predator_melee_config;
    if (negative == 1)
    {
        avsp_port_v2_pcm_init(&runtime);
        input.frame = 147;
        input.cue_event = 1;
        input.cue_id = 99;
        return expect(!avsp_port_v2_pcm_step(&runtime, &input, &first),
                      "wrong cue was accepted") ? 0 : 1;
    }
    if (negative == 2)
    {
        rejected.start_delay_frames = 2;
        return expect(!avsp_port_v2_pcm_validate_config(&rejected),
                      "wrong cue timing was accepted") ? 0 : 1;
    }
    if (!expect(avsp_port_v2_pcm_validate_config(
                    &avsp_port_v2_pcm_predator_melee_config),
                "approved PCM config rejected")) return 1;
    starts = 0;
    stops = 0;
    if (!expect(run_sequence(&first) && starts == 1 && stops == 1,
                "first PCM sequence failed")) return 1;
    starts = 0;
    stops = 0;
    if (!expect(run_sequence(&second) && starts == 1 && stops == 1 &&
                memcmp(&first, &second, sizeof(first)) == 0,
                "deterministic PCM repeat drifted")) return 1;
    puts("PCM promotion host contract: PASS");
    return 0;
}
