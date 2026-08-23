#include <stdio.h>
#include <string.h>

#include "cdda_residency_bench.h"

static int simulate(const char *negative)
{
    AvspCddaResidencyRuntime runtime;
    AvspCddaResidencyFrame frame;
    AvspCddaResidencyManifest manifest;
    int index;
    int success;

    manifest = avsp_cdda_residency_manifest;
    if (negative != 0 && strcmp(negative, "missing-allocation") == 0)
        manifest.phase_high_water_bytes[AVSP_CDDA_DOMAIN_WORK_RAM] = -1;
    if (negative != 0 && strcmp(negative, "wrong-source-event") == 0)
        manifest.source_frame = AVSP_CDDA_RESIDENCY_SOURCE_FRAME + 1;
    if (!avsp_cdda_residency_validate_manifest(&manifest))
        return negative != 0;
    avsp_cdda_residency_init(&runtime);
    for (index = 0; index < AVSP_CDDA_RESIDENCY_CYCLE_FRAMES * 2; ++index)
    {
        if (!avsp_cdda_residency_step(&runtime, &frame))
            return 0;
        success = 1;
        if (frame.action == AVSP_CDDA_ACTION_ILLEGAL_READ ||
            frame.action == AVSP_CDDA_ACTION_ILLEGAL_WINDOW)
            success = 0;
        if (negative != 0 &&
            strcmp(negative, "permit-illegal-read") == 0 &&
            frame.action == AVSP_CDDA_ACTION_ILLEGAL_READ)
            success = 1;
        if (!avsp_cdda_residency_observe(&runtime, &frame, success) &&
            negative == 0)
            return 0;
    }
    if (negative != 0)
        return runtime.failures > 0;
    return runtime.failures == 0 && runtime.cdda_active == 0 &&
           runtime.window_open == 0 &&
           runtime.ownership_transitions == 2 &&
           runtime.track_event_count == 1 &&
           runtime.legal_window_count == 1 &&
           runtime.legal_read_count == 1 &&
           runtime.negative_rejections == 2 &&
           avsp_cdda_residency_canaries_ok(&runtime);
}

int main(int argc, char **argv)
{
    const char *negative = 0;

    if (argc == 3 && strcmp(argv[1], "--negative-control") == 0)
        negative = argv[2];
    if (!simulate(negative))
    {
        printf("cdda_residency_test: FAIL\n");
        return 1;
    }
    printf("cdda_residency_test: %s\n",
           negative == 0 ? "PASS" : "negative control PASS");
    return 0;
}
