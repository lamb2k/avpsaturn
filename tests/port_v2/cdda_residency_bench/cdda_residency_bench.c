#include "cdda_residency_bench.h"

const AvspCddaResidencyManifest avsp_cdda_residency_manifest =
{
    AVSP_CDDA_RESIDENCY_TRACK,
    AVSP_CDDA_RESIDENCY_SOURCE_FRAME,
    {770048, 4194304, 524288, 524288, 4096, 524288},
    {AVSP_CDDA_RESIDENCY_WORK_RAM_BYTES, 0, 0, 0, 0, 0},
    {1, 0, 0, 0, 0, 0}
};

int avsp_cdda_residency_validate_manifest(
    const AvspCddaResidencyManifest *manifest)
{
    int domain;

    if (manifest == 0 || manifest->track != AVSP_CDDA_RESIDENCY_TRACK ||
        manifest->source_frame != AVSP_CDDA_RESIDENCY_SOURCE_FRAME)
        return 0;
    for (domain = 0; domain < AVSP_CDDA_DOMAIN_COUNT; ++domain)
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
    return manifest->phase_high_water_bytes[AVSP_CDDA_DOMAIN_WORK_RAM] ==
               AVSP_CDDA_RESIDENCY_WORK_RAM_BYTES;
}

void avsp_cdda_residency_init(AvspCddaResidencyRuntime *runtime)
{
    runtime->head_canary = AVSP_CDDA_RESIDENCY_CANARY_HEAD;
    runtime->frame = 0;
    runtime->cdda_active = 0;
    runtime->window_open = 0;
    runtime->ownership_transitions = 0;
    runtime->track_event_count = 0;
    runtime->legal_window_count = 0;
    runtime->legal_read_count = 0;
    runtime->negative_rejections = 0;
    runtime->failures = 0;
    runtime->tail_canary = AVSP_CDDA_RESIDENCY_CANARY_TAIL;
}

int avsp_cdda_residency_step(AvspCddaResidencyRuntime *runtime,
                             AvspCddaResidencyFrame *frame)
{
    int relative;

    if (runtime == 0 || frame == 0 ||
        !avsp_cdda_residency_canaries_ok(runtime))
        return 0;
    relative = runtime->frame % AVSP_CDDA_RESIDENCY_CYCLE_FRAMES;
    if (relative == 0 && runtime->frame != 0)
    {
        if (runtime->cdda_active || runtime->window_open)
            ++runtime->failures;
        runtime->ownership_transitions = 0;
        runtime->track_event_count = 0;
        runtime->legal_window_count = 0;
        runtime->legal_read_count = 0;
        runtime->negative_rejections = 0;
    }
    frame->relative_frame = relative;
    frame->action = AVSP_CDDA_ACTION_NONE;
    if (relative == 30)
        frame->action = AVSP_CDDA_ACTION_START_TRACK;
    else if (relative == 60)
        frame->action = AVSP_CDDA_ACTION_ILLEGAL_READ;
    else if (relative == 90)
        frame->action = AVSP_CDDA_ACTION_ILLEGAL_WINDOW;
    else if (relative == 120)
        frame->action = AVSP_CDDA_ACTION_STOP_TRACK;
    else if (relative == 150)
        frame->action = AVSP_CDDA_ACTION_WINDOW_BEGIN;
    else if (relative == 151)
        frame->action = AVSP_CDDA_ACTION_LEGAL_READ;
    else if (relative == 152)
        frame->action = AVSP_CDDA_ACTION_WINDOW_END;
    ++runtime->frame;
    return 1;
}

int avsp_cdda_residency_observe(AvspCddaResidencyRuntime *runtime,
                                const AvspCddaResidencyFrame *frame,
                                const int operation_succeeded)
{
    int expected = 1;

    if (runtime == 0 || frame == 0)
        return 0;
    if (frame->action == AVSP_CDDA_ACTION_START_TRACK)
    {
        if (runtime->cdda_active || runtime->window_open)
            expected = 0;
        else if (operation_succeeded)
        {
            runtime->cdda_active = 1;
            ++runtime->ownership_transitions;
            ++runtime->track_event_count;
        }
    }
    else if (frame->action == AVSP_CDDA_ACTION_ILLEGAL_READ ||
             frame->action == AVSP_CDDA_ACTION_ILLEGAL_WINDOW)
    {
        if (!runtime->cdda_active || runtime->window_open ||
            operation_succeeded)
            expected = 0;
        else
            ++runtime->negative_rejections;
    }
    else if (frame->action == AVSP_CDDA_ACTION_STOP_TRACK)
    {
        if (!runtime->cdda_active || !operation_succeeded)
            expected = 0;
        else
        {
            runtime->cdda_active = 0;
            ++runtime->ownership_transitions;
        }
    }
    else if (frame->action == AVSP_CDDA_ACTION_WINDOW_BEGIN)
    {
        if (runtime->cdda_active || runtime->window_open ||
            !operation_succeeded)
            expected = 0;
        else
        {
            runtime->window_open = 1;
            ++runtime->legal_window_count;
        }
    }
    else if (frame->action == AVSP_CDDA_ACTION_LEGAL_READ)
    {
        if (runtime->cdda_active || !runtime->window_open ||
            !operation_succeeded)
            expected = 0;
        else
            ++runtime->legal_read_count;
    }
    else if (frame->action == AVSP_CDDA_ACTION_WINDOW_END)
    {
        if (!runtime->window_open || !operation_succeeded)
            expected = 0;
        else
            runtime->window_open = 0;
    }
    if (!expected)
        ++runtime->failures;
    return expected;
}

int avsp_cdda_residency_canaries_ok(
    const AvspCddaResidencyRuntime *runtime)
{
    return runtime != 0 &&
           runtime->head_canary == AVSP_CDDA_RESIDENCY_CANARY_HEAD &&
           runtime->tail_canary == AVSP_CDDA_RESIDENCY_CANARY_TAIL;
}
