#include <string.h>
#include "probe3.h"

volatile AvspProbe3Telemetry avsp_probe3_telemetry;

static unsigned long max_u32(unsigned long left, unsigned long right)
{
    return left > right ? left : right;
}

static unsigned long summary_checksum(void)
{
    const volatile unsigned long *words =
        (const volatile unsigned long *)&avsp_probe3_telemetry.magic;
    unsigned long count =
        (unsigned long)((const volatile unsigned long *)
            &avsp_probe3_telemetry.summary_checksum - words);
    unsigned long hash = 2166136261UL;
    unsigned long index;
    for (index = 0; index < count; ++index)
        hash = (hash ^ words[index]) * 16777619UL;
    return hash;
}

void avsp_probe3_init(void)
{
    memset((void *)&avsp_probe3_telemetry, 0,
           sizeof(avsp_probe3_telemetry));
    avsp_probe3_telemetry.canary_begin = AVSP_PROBE3_CANARY;
    avsp_probe3_telemetry.canary_end = AVSP_PROBE3_CANARY;
    avsp_probe3_telemetry.magic = AVSP_PROBE3_MAGIC;
    avsp_probe3_telemetry.schema = AVSP_PROBE3_SCHEMA;
    avsp_probe3_telemetry.status = PROBE3_STATUS_RUNNING;
    avsp_probe3_telemetry.mode = PROBE3_REPRESENTATIVE;
    avsp_probe3_telemetry.overload_expected = 1;
    avsp_probe3_telemetry.canary_state = 1;
}

const AvspProbe3Schedule *avsp_probe3_schedule(void)
{
    if (avsp_probe3_telemetry.mode == PROBE3_REPRESENTATIVE)
        return &avsp_probe3_schedules[0];
    return &avsp_probe3_schedules[1];
}

static void fail(const AvspProbe3Failure reason)
{
    avsp_probe3_telemetry.failure_reason = (unsigned long)reason;
    avsp_probe3_telemetry.status = PROBE3_STATUS_FAILED;
    avsp_probe3_telemetry.complete = 1;
    avsp_probe3_telemetry.summary_checksum = summary_checksum();
}

void avsp_probe3_record_frame(
    unsigned long frame_number,
    unsigned long vdp1_draw_end_state,
    unsigned long field_delta,
    unsigned long drawn_commands,
    unsigned long cpu_prepare_ticks,
    unsigned long texture_bytes_copied,
    unsigned long copy_count,
    unsigned long copy_ticks,
    unsigned long legal_copy_direction,
    unsigned long cram_writes,
    unsigned long cartridge_read_bytes,
    unsigned long asset_failures)
{
    const AvspProbe3Schedule *schedule = avsp_probe3_schedule();
    AvspProbe3Mode mode = (AvspProbe3Mode)avsp_probe3_telemetry.mode;
    volatile AvspProbe3ModeResult *result =
        &avsp_probe3_telemetry.result[mode];
    unsigned long draw_end = vdp1_draw_end_state & 0x2UL;
    unsigned long expected_frames = mode == PROBE3_OVERLOAD ? 1UL :
        AVSP_PROBE3_NORMAL_MODE_FRAMES;

    avsp_probe3_telemetry.frame_number = frame_number;
    avsp_probe3_telemetry.workload_checksum_word = schedule->checksum_word;
    avsp_probe3_telemetry.reachable_commands = schedule->reachable_commands;
    avsp_probe3_telemetry.drawn_commands = drawn_commands;
    avsp_probe3_telemetry.vdp1_draw_end_state = vdp1_draw_end_state;
    avsp_probe3_telemetry.draw_end_deadline_fields =
        mode == PROBE3_OVERLOAD ? 0UL : 1UL;
    avsp_probe3_telemetry.cpu_prepare_ticks = cpu_prepare_ticks;
    avsp_probe3_telemetry.texture_bytes_copied = texture_bytes_copied;
    avsp_probe3_telemetry.copy_count = copy_count;
    avsp_probe3_telemetry.copy_ticks = copy_ticks;
    avsp_probe3_telemetry.legal_copy_direction = legal_copy_direction;
    avsp_probe3_telemetry.cram_writes = cram_writes;
    avsp_probe3_telemetry.cartridge_read_bytes = cartridge_read_bytes;
    avsp_probe3_telemetry.asset_failures = asset_failures;

    if (field_delta == 0UL)
        ++avsp_probe3_telemetry.repeated_fields;
    else if (field_delta > 1UL)
        avsp_probe3_telemetry.skipped_fields += field_delta - 1UL;

    /* EDSR CEF sampled at the following field boundary is the production
     * VDP1 deadline detector.  The overload control intentionally tightens
     * its declared deadline to zero fields, so it must trip even when CEF is
     * already set.  It does not assert a production timing budget. */
    if (mode == PROBE3_OVERLOAD)
    {
        avsp_probe3_telemetry.overload_tripped = 1;
        result->detector_tripped = 1;
    }
    else if (!draw_end && avsp_probe3_telemetry.mode_frame > 0UL)
    {
        ++avsp_probe3_telemetry.missed_fields;
        ++avsp_probe3_telemetry.late_command_lists;
        ++result->missed_fields;
        ++result->late_lists;
    }

    result->reachable_high_water = max_u32(
        result->reachable_high_water, schedule->reachable_commands);
    result->drawn_high_water = max_u32(
        result->drawn_high_water, drawn_commands);
    result->cpu_prepare_ticks_high_water = max_u32(
        result->cpu_prepare_ticks_high_water, cpu_prepare_ticks);
    result->texture_bytes_high_water = max_u32(
        result->texture_bytes_high_water, texture_bytes_copied);
    result->copy_count_high_water = max_u32(
        result->copy_count_high_water, copy_count);
    result->copy_ticks_high_water = max_u32(
        result->copy_ticks_high_water, copy_ticks);
    result->cart_read_bytes_high_water = max_u32(
        result->cart_read_bytes_high_water, cartridge_read_bytes);
    if (mode == PROBE3_REPRESENTATIVE)
        avsp_probe3_telemetry.representative_high_water =
            result->drawn_high_water;
    if (mode == PROBE3_PEAK_909)
        avsp_probe3_telemetry.peak_high_water = result->drawn_high_water;

    if (avsp_probe3_telemetry.canary_begin != AVSP_PROBE3_CANARY ||
        avsp_probe3_telemetry.canary_end != AVSP_PROBE3_CANARY)
    {
        avsp_probe3_telemetry.canary_state = 0;
        fail(PROBE3_FAILURE_CANARY);
        return;
    }
    if (asset_failures != 0UL)
    {
        fail(PROBE3_FAILURE_ASSET);
        return;
    }
    if (!legal_copy_direction)
    {
        fail(PROBE3_FAILURE_ILLEGAL_COPY_DIRECTION);
        return;
    }
    if (drawn_commands != schedule->reachable_commands)
    {
        fail(PROBE3_FAILURE_COMMAND_COUNT);
        return;
    }

    ++avsp_probe3_telemetry.mode_frame;
    if (avsp_probe3_telemetry.mode_frame < expected_frames)
        return;

    if (mode == PROBE3_OVERLOAD)
    {
        if (!avsp_probe3_telemetry.overload_tripped)
        {
            fail(PROBE3_FAILURE_OVERLOAD_DID_NOT_TRIP);
            return;
        }
        avsp_probe3_telemetry.status = PROBE3_STATUS_COMPLETE;
        avsp_probe3_telemetry.complete = 1;
        avsp_probe3_telemetry.summary_checksum = summary_checksum();
        return;
    }
    ++avsp_probe3_telemetry.mode;
    avsp_probe3_telemetry.mode_frame = 0;
}
