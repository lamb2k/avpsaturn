#include <stdio.h>
#include <string.h>

#include "../../../src/port_v2/audio/cdda/cdda.h"
#include "../../../src/port_v2/residency/residency.h"

static int starts;
static int stops;
static int reads;

static int expect(const int condition, const char *message)
{
    if (!condition)
    {
        fprintf(stderr, "%s\n", message);
        return 0;
    }
    return 1;
}

static int capture_start(const AvspPortV2CddaFrame *frame)
{
    if (frame->track != 2 || frame->source_frame != 2520) return 0;
    ++starts;
    return 1;
}

static int capture_stop(const AvspPortV2CddaFrame *frame)
{
    if (frame->track != 2 || frame->source_frame != 2520) return 0;
    ++stops;
    return 1;
}

static int capture_read(const int region_id, unsigned char *destination,
                        const int capacity)
{
    static const unsigned char payload[64] =
        "AVSP-CDDA-RESIDENCY-V1|TRACK=02|WINDOW=PHASE-BOUNDARY|OK!!!!!!!\n";
    if (region_id != AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC ||
        capacity < 64) return -1;
    memcpy(destination, payload, 64);
    ++reads;
    return 64;
}

static int run_sequence(AvspPortV2CddaFrame *final_cdda,
                        AvspPortV2ResidencyRuntime *final_residency)
{
    AvspPortV2CddaRuntime cdda;
    AvspPortV2ResidencyRuntime residency;
    AvspPortV2CddaInput input;
    AvspPortV2CddaFrame frame;
    AvspPortV2CddaAudioOps audio;
    AvspPortV2ResidencyAssetOps assets;
    unsigned char buffer[64];
    int tick;

    avsp_port_v2_cdda_init(&cdda);
    avsp_port_v2_residency_init(&residency);
    audio.start = capture_start;
    audio.stop = capture_stop;
    assets.read = capture_read;
    memset(buffer, 0, sizeof(buffer));
    for (tick = 0; tick <= 240; ++tick)
    {
        input.command = AVSP_PORT_V2_CDDA_NONE;
        input.track = 2;
        input.source_frame = 2520;
        if (tick == 30) input.command = AVSP_PORT_V2_CDDA_START;
        if (tick == 120) input.command = AVSP_PORT_V2_CDDA_STOP;
        if (!avsp_port_v2_cdda_step(&cdda, &input, &frame)) return 0;
        if (tick == 30)
        {
            if (!avsp_port_v2_residency_cdda_started(&residency) ||
                !avsp_port_v2_cdda_submit(&frame, &audio)) return 0;
        }
        if (tick == 60 && avsp_port_v2_residency_submit_read(
                &residency, AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
                buffer, sizeof(buffer), &assets)) return 0;
        if (tick == 90 &&
            avsp_port_v2_residency_window_begin(&residency)) return 0;
        if (tick == 120)
        {
            if (!avsp_port_v2_cdda_submit(&frame, &audio) ||
                !avsp_port_v2_residency_cdda_stopped(&residency)) return 0;
        }
        if (tick == 150 &&
            !avsp_port_v2_residency_window_begin(&residency)) return 0;
        if (tick == 151 && !avsp_port_v2_residency_submit_read(
                &residency, AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
                buffer, sizeof(buffer), &assets)) return 0;
        if (tick == 152 &&
            !avsp_port_v2_residency_window_end(&residency)) return 0;
    }
    *final_cdda = frame;
    *final_residency = residency;
    return expect(cdda.event_count == 1 && cdda.ownership_transitions == 2 &&
                  !cdda.active && starts == 1 && stops == 1 && reads == 1,
                  "CDDA semantic sequence drifted") &&
           expect(residency.ownership_transitions == 2 &&
                  residency.late_read_attempts == 1 &&
                  residency.refused_windows == 1 &&
                  residency.negative_rejections == 2 &&
                  residency.legal_window_count == 1 &&
                  residency.legal_read_count == 1 &&
                  residency.failures == 0 && !residency.window_open &&
                  avsp_port_v2_residency_canaries_ok(&residency),
                  "residency semantic sequence drifted");
}

int main(const int argc, char **argv)
{
    AvspPortV2CddaConfig bad_cdda;
    AvspPortV2ResidencyManifest bad_manifest;
    AvspPortV2ResidencyRuntime residency;
    AvspPortV2ResidencyAssetOps assets;
    unsigned char buffer[AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES];
    AvspPortV2CddaFrame first_cdda;
    AvspPortV2CddaFrame second_cdda;
    AvspPortV2ResidencyRuntime first_residency;
    AvspPortV2ResidencyRuntime second_residency;
    int negative = 0;

    if (argc == 2 && strcmp(argv[1], "--wrong-track") == 0) negative = 1;
    if (argc == 2 && strcmp(argv[1], "--missing-region") == 0) negative = 2;
    if (argc == 2 && strcmp(argv[1], "--illegal-read") == 0) negative = 3;
    if (argc > 2 || (argc == 2 && negative == 0)) return 2;
    if (negative == 1)
    {
        bad_cdda = avsp_port_v2_cdda_stage1_config;
        bad_cdda.track = 3;
        return expect(!avsp_port_v2_cdda_validate_config(&bad_cdda),
                      "altered track was accepted") ? 0 : 1;
    }
    if (negative == 2)
    {
        bad_manifest = avsp_port_v2_stage1_residency_manifest;
        bad_manifest.region_count = 0;
        return expect(!avsp_port_v2_residency_validate_manifest(&bad_manifest),
                      "missing region was accepted") ? 0 : 1;
    }
    if (negative == 3)
    {
        avsp_port_v2_residency_init(&residency);
        assets.read = capture_read;
        reads = 0;
        if (!avsp_port_v2_residency_cdda_started(&residency)) return 1;
        return expect(!avsp_port_v2_residency_submit_read(
                          &residency,
                          AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
                          buffer, sizeof(buffer), &assets) &&
                      residency.late_read_attempts == 1 &&
                      residency.negative_rejections == 1 && reads == 0,
                      "read while CDDA owned the drive was accepted") ? 0 : 1;
    }
    if (!expect(avsp_port_v2_cdda_validate_config(
                    &avsp_port_v2_cdda_stage1_config),
                "approved CDDA config rejected") ||
        !expect(avsp_port_v2_residency_validate_manifest(
                    &avsp_port_v2_stage1_residency_manifest),
                "approved residency manifest rejected")) return 1;
    starts = stops = reads = 0;
    if (!run_sequence(&first_cdda, &first_residency)) return 1;
    starts = stops = reads = 0;
    if (!run_sequence(&second_cdda, &second_residency)) return 1;
    if (!expect(memcmp(&first_cdda, &second_cdda,
                       sizeof(first_cdda)) == 0 &&
                memcmp(&first_residency, &second_residency,
                       sizeof(first_residency)) == 0,
                "CDDA/residency deterministic repeat drifted")) return 1;
    puts("CDDA/residency promotion host contract: PASS");
    return 0;
}
