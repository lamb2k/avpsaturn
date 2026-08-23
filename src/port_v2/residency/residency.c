#include <string.h>

#include "residency.h"

static const AvspPortV2ResidencyRegion stage1_regions[] =
{
    {
        AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
        AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES,
        "84a73962f97c2479b1c514c5e6747a95a5c3be1a58530ed62dc09cb3fbb57d2d"
    }
};

const AvspPortV2ResidencyManifest avsp_port_v2_stage1_residency_manifest =
{
    2,
    2520,
    {770048, 4194304, 524288, 524288, 4096, 524288},
    {AVSP_PORT_V2_RESIDENCY_WORK_RAM_BYTES, 0, 0, 0, 0, 0},
    {1, 0, 0, 0, 0, 0},
    stage1_regions,
    1
};

int avsp_port_v2_residency_validate_manifest(
    const AvspPortV2ResidencyManifest *manifest)
{
    int domain;

    if (manifest == 0 || manifest->track != 2 ||
        manifest->source_frame != 2520 || manifest->regions == 0 ||
        manifest->region_count != 1 ||
        manifest->regions[0].region_id !=
            AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC ||
        manifest->regions[0].bytes != AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES ||
        manifest->regions[0].payload_sha256 == 0 ||
        strcmp(manifest->regions[0].payload_sha256,
               "84a73962f97c2479b1c514c5e6747a95a5c3be1a58530ed62dc09cb3fbb57d2d") != 0)
        return 0;
    for (domain = 0; domain < AVSP_PORT_V2_DOMAIN_COUNT; ++domain)
    {
        if (manifest->capacity_bytes[domain] <= 0 ||
            manifest->phase_high_water_bytes[domain] < 0 ||
            manifest->phase_high_water_bytes[domain] >
                manifest->capacity_bytes[domain])
            return 0;
        if ((manifest->phase_high_water_bytes[domain] > 0) !=
            (manifest->canary_required[domain] != 0))
            return 0;
    }
    return manifest->phase_high_water_bytes[AVSP_PORT_V2_DOMAIN_WORK_RAM] ==
               AVSP_PORT_V2_RESIDENCY_WORK_RAM_BYTES;
}

void avsp_port_v2_residency_init(AvspPortV2ResidencyRuntime *runtime)
{
    if (runtime == 0) return;
    memset(runtime, 0, sizeof(*runtime));
    runtime->head_canary = AVSP_PORT_V2_RESIDENCY_CANARY_HEAD;
    runtime->tail_canary = AVSP_PORT_V2_RESIDENCY_CANARY_TAIL;
    runtime->disc_owner = AVSP_PORT_V2_DISC_DATA;
}

int avsp_port_v2_residency_cdda_started(
    AvspPortV2ResidencyRuntime *runtime)
{
    if (runtime == 0 || runtime->disc_owner != AVSP_PORT_V2_DISC_DATA ||
        runtime->window_open) return 0;
    runtime->disc_owner = AVSP_PORT_V2_DISC_CDDA;
    ++runtime->ownership_transitions;
    return 1;
}

int avsp_port_v2_residency_cdda_stopped(
    AvspPortV2ResidencyRuntime *runtime)
{
    if (runtime == 0 || runtime->disc_owner != AVSP_PORT_V2_DISC_CDDA)
        return 0;
    runtime->disc_owner = AVSP_PORT_V2_DISC_DATA;
    ++runtime->ownership_transitions;
    return 1;
}

int avsp_port_v2_residency_window_begin(
    AvspPortV2ResidencyRuntime *runtime)
{
    if (runtime == 0) return 0;
    if (runtime->disc_owner == AVSP_PORT_V2_DISC_CDDA)
    {
        ++runtime->refused_windows;
        ++runtime->negative_rejections;
        return 0;
    }
    if (runtime->window_open) return 0;
    runtime->window_open = 1;
    ++runtime->legal_window_count;
    return 1;
}

int avsp_port_v2_residency_window_end(
    AvspPortV2ResidencyRuntime *runtime)
{
    if (runtime == 0 || !runtime->window_open ||
        runtime->disc_owner != AVSP_PORT_V2_DISC_DATA)
        return 0;
    runtime->window_open = 0;
    return 1;
}

int avsp_port_v2_residency_submit_read(
    AvspPortV2ResidencyRuntime *runtime,
    const int region_id,
    unsigned char *destination,
    const int capacity,
    const AvspPortV2ResidencyAssetOps *operations)
{
    const AvspPortV2ResidencyRegion *region;
    int read_bytes;

    if (runtime == 0) return 0;
    if (runtime->disc_owner == AVSP_PORT_V2_DISC_CDDA)
    {
        ++runtime->late_read_attempts;
        ++runtime->negative_rejections;
        return 0;
    }
    if (!runtime->window_open || destination == 0 || operations == 0 ||
        operations->read == 0)
        return 0;
    region = &avsp_port_v2_stage1_residency_manifest.regions[0];
    if (region_id != region->region_id || capacity < region->bytes)
        return 0;
    read_bytes = operations->read(region_id, destination, capacity);
    if (read_bytes != region->bytes)
    {
        ++runtime->failures;
        return 0;
    }
    ++runtime->legal_read_count;
    return 1;
}

int avsp_port_v2_residency_canaries_ok(
    const AvspPortV2ResidencyRuntime *runtime)
{
    return runtime != 0 &&
           runtime->head_canary == AVSP_PORT_V2_RESIDENCY_CANARY_HEAD &&
           runtime->tail_canary == AVSP_PORT_V2_RESIDENCY_CANARY_TAIL;
}
