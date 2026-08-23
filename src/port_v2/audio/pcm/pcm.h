#ifndef AVSP_PORT_V2_AUDIO_PCM_H
#define AVSP_PORT_V2_AUDIO_PCM_H

#define AVSP_PORT_V2_PCM_INTERFACE_VERSION 1
#define AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE 1

typedef struct
{
    int cue_id;
    int payload_bytes;
    int sample_rate;
    int channels;
    int sample_bits;
    int scsp_channel;
    int start_delay_frames;
    int duration_frames;
    const char *payload_sha256;
} AvspPortV2PcmConfig;

typedef struct
{
    int frame;
    int cue_event;
    int cue_id;
} AvspPortV2PcmInput;

typedef struct
{
    int pending;
    int active;
    int event_count;
    int event_frame;
    int start_frame;
    int end_frame;
} AvspPortV2PcmRuntime;

typedef struct
{
    int cue_id;
    int start_request;
    int stop_request;
    int active;
    int event_count;
    int event_frame;
    int start_frame;
    int end_frame;
} AvspPortV2PcmFrame;

typedef int (*AvspPortV2PcmStart)(const AvspPortV2PcmFrame *frame);
typedef int (*AvspPortV2PcmStop)(const AvspPortV2PcmFrame *frame);

typedef struct
{
    AvspPortV2PcmStart start;
    AvspPortV2PcmStop stop;
} AvspPortV2PcmAudioOps;

extern const AvspPortV2PcmConfig avsp_port_v2_pcm_predator_melee_config;

int avsp_port_v2_pcm_validate_config(const AvspPortV2PcmConfig *config);
void avsp_port_v2_pcm_init(AvspPortV2PcmRuntime *runtime);
int avsp_port_v2_pcm_step(AvspPortV2PcmRuntime *runtime,
                          const AvspPortV2PcmInput *input,
                          AvspPortV2PcmFrame *frame);
int avsp_port_v2_pcm_submit(const AvspPortV2PcmFrame *frame,
                            const AvspPortV2PcmAudioOps *operations);

#endif
