#include <string.h>
#include "probe3.h"

#define PROBE3_SLOT_BYTES 32UL
#define PROBE3_END_BIT 0x8000U
#define PROBE3_MAX_SLOTS (AVSP_PROBE3_VDP1_TABLE_BYTES / PROBE3_SLOT_BYTES)
#define PROBE3_SGL_SENTINEL_CONTROL 0x0501U
#define PROBE3_SGL_SENTINEL_SOURCE_WORD 0xFFE0U
#define PROBE3_SGL_SENTINEL_SIZE_WORD 0x0101U

volatile AvspProbe3Telemetry avsp_probe3_telemetry;
static unsigned char probe3_census_seen[PROBE3_MAX_SLOTS];

static unsigned long max_u32(unsigned long a, unsigned long b)
{ return a > b ? a : b; }

static unsigned long summary_checksum(void)
{
    const volatile unsigned long *words =
        (const volatile unsigned long *)&avsp_probe3_telemetry.magic;
    unsigned long count = (unsigned long)((const volatile unsigned long *)
        &avsp_probe3_telemetry.summary_checksum - words);
    unsigned long hash = 2166136261UL, index;
    for (index = 0; index < count; ++index)
        hash = (hash ^ words[index]) * 16777619UL;
    return hash;
}

void avsp_probe3_init(void)
{
    unsigned long mode;
    memset((void *)&avsp_probe3_telemetry, 0, sizeof(avsp_probe3_telemetry));
    avsp_probe3_telemetry.canary_begin = AVSP_PROBE3_CANARY;
    avsp_probe3_telemetry.canary_end = AVSP_PROBE3_CANARY;
    avsp_probe3_telemetry.magic = AVSP_PROBE3_MAGIC;
    avsp_probe3_telemetry.schema = AVSP_PROBE3_SCHEMA;
    avsp_probe3_telemetry.status = PROBE3_STATUS_RUNNING;
    avsp_probe3_telemetry.phase = PROBE3_PHASE_PRECHECK_MEASURE;
    avsp_probe3_telemetry.mode = PROBE3_REPRESENTATIVE;
    avsp_probe3_telemetry.detector_enabled = 1UL;
    avsp_probe3_telemetry.overload_expected = 1UL;
    avsp_probe3_telemetry.canary_state = 1UL;
    avsp_probe3_telemetry.timer_divisor = AVSP_PROBE3_FRC_DIVISOR;
    avsp_probe3_telemetry.soak_target_fields = AVSP_PROBE3_SOAK_FIELDS;
    avsp_probe3_telemetry.soak_block_fields = AVSP_PROBE3_SOAK_BLOCK_FIELDS;
    avsp_probe3_telemetry.soak_min_draw_margin_ticks = 0xFFFFFFFFUL;
    avsp_probe3_telemetry.soak_min_draw_margin_percent_x100 = 0xFFFFFFFFUL;
    for (mode = 0; mode < PROBE3_MODE_COUNT; ++mode) {
        avsp_probe3_telemetry.result[mode].min_draw_margin_ticks = 0xFFFFFFFFUL;
        avsp_probe3_telemetry.result[mode].min_draw_margin_percent_x100 =
            0xFFFFFFFFUL;
    }
}

const AvspProbe3Schedule *avsp_probe3_schedule(void)
{
    if (avsp_probe3_telemetry.mode == PROBE3_REPRESENTATIVE)
        return &avsp_probe3_schedules[0];
    return &avsp_probe3_schedules[1];
}

unsigned long avsp_probe3_deadline_tripped(
    const AvspProbe3DeadlineObservation *observation)
{
    unsigned long deadline_ticks;
    if (observation == 0 || observation->detector_enabled == 0UL)
        return 0UL;
    if (observation->draw_end_observed && observation->draw_end_reliable &&
        observation->field_period_ticks != 0UL) {
        deadline_ticks = observation->deadline_fields *
            observation->field_period_ticks;
        return observation->draw_elapsed_ticks > deadline_ticks ? 1UL : 0UL;
    }
    if (observation->field_delta > observation->deadline_fields)
        return 1UL;
    if (!observation->draw_end_observed &&
        observation->field_delta >= observation->deadline_fields)
        return 1UL;
    return 0UL;
}

static int is_sgl_scaled_sprite_sentinel(
    const volatile unsigned short *command)
{
    return command[0] == PROBE3_SGL_SENTINEL_CONTROL &&
        command[4] == PROBE3_SGL_SENTINEL_SOURCE_WORD &&
        command[5] == PROBE3_SGL_SENTINEL_SIZE_WORD;
}

void avsp_probe3_census(const volatile unsigned short *vram,
                        unsigned long table_bytes,
                        unsigned long expected_workload_tile_draws,
                        AvspProbe3Census *census)
{
    unsigned long max_slots = table_bytes / PROBE3_SLOT_BYTES;
    unsigned long slot = 0UL, return_slot = 0UL, have_return = 0UL, step;
    memset(census, 0, sizeof(*census));
    memset(probe3_census_seen, 0, sizeof(probe3_census_seen));
    census->requested_workload_tile_draws = expected_workload_tile_draws;
    if (max_slots > PROBE3_MAX_SLOTS) max_slots = PROBE3_MAX_SLOTS;
    for (step = 0; step < max_slots; ++step) {
        unsigned long word, nonzero = 0UL;
        for (word = 0; word < 16UL; ++word)
            nonzero |= (unsigned long)vram[step * 16UL + word];
        if (nonzero == 0UL) break;
        ++census->stored_nonzero_slots;
    }
    for (step = 0; step < max_slots; ++step) {
        unsigned short control, link;
        unsigned long mode, type, next;
        if (slot >= max_slots) {
            census->invalid_link = 1UL;
            census->traversal_failure = 1UL;
            return;
        }
        if (probe3_census_seen[slot]) {
            census->loop_detected = 1UL;
            census->traversal_failure = 1UL;
            return;
        }
        probe3_census_seen[slot] = 1U;
        control = vram[slot * 16UL];
        link = vram[slot * 16UL + 1UL];
        ++census->reachable_table_entries;
        if (control & PROBE3_END_BIT) {
            census->terminator_present = 1UL;
            if (census->workload_tile_draw_commands !=
                expected_workload_tile_draws)
                census->premature_end = 1UL;
            return;
        }
        mode = ((unsigned long)control >> 12) & 7UL;
        type = (unsigned long)control & 15UL;
        if (mode >= 4UL) ++census->reachable_skipped_commands;
        if (type <= 7UL && mode < 4UL) {
            ++census->total_reachable_draw_commands;
            if (is_sgl_scaled_sprite_sentinel(&vram[slot * 16UL])) {
                ++census->auxiliary_draw_commands;
                ++census->sgl_scaled_sprite_sentinel_draw_commands;
            } else ++census->workload_tile_draw_commands;
        }
        else if (type >= 8UL && type <= 10UL)
            ++census->reachable_state_commands;
        else if (type > 10UL) {
            census->traversal_failure = 1UL;
            return;
        }
        if (mode == 2UL || mode == 6UL) {
            if (have_return) census->traversal_failure = 1UL;
            return_slot = slot + 1UL;
            have_return = 1UL;
        }
        if (mode == 3UL || mode == 7UL) {
            if (!have_return) {
                census->traversal_failure = 1UL;
                return;
            }
            next = return_slot;
            have_return = 0UL;
        } else if (mode == 1UL || mode == 2UL || mode == 5UL || mode == 6UL) {
            unsigned long byte_address = (unsigned long)link * 8UL;
            if ((byte_address & (PROBE3_SLOT_BYTES - 1UL)) != 0UL ||
                byte_address >= table_bytes) {
                census->invalid_link = 1UL;
                census->traversal_failure = 1UL;
                return;
            }
            next = byte_address / PROBE3_SLOT_BYTES;
        } else next = slot + 1UL;
        slot = next;
    }
    census->table_truncated = 1UL;
    census->traversal_failure = 1UL;
}

void avsp_probe3_fail(AvspProbe3Failure reason)
{
    if (avsp_probe3_telemetry.status == PROBE3_STATUS_FAILED) return;
    avsp_probe3_telemetry.failure_reason = (unsigned long)reason;
    avsp_probe3_telemetry.status = PROBE3_STATUS_FAILED;
    avsp_probe3_telemetry.complete = 1UL;
    avsp_probe3_telemetry.summary_checksum = summary_checksum();
}

static int common_frame_valid(const AvspProbe3DeadlineObservation *observation)
{
    if (avsp_probe3_telemetry.canary_begin != AVSP_PROBE3_CANARY ||
        avsp_probe3_telemetry.canary_end != AVSP_PROBE3_CANARY) {
        avsp_probe3_telemetry.canary_state = 0UL;
        avsp_probe3_fail(PROBE3_FAILURE_CANARY);
        return 0;
    }
    if (avsp_probe3_telemetry.asset_failures != 0UL) {
        avsp_probe3_fail(PROBE3_FAILURE_ASSET);
        return 0;
    }
    if (!avsp_probe3_telemetry.cart_texture_source_valid ||
        !avsp_probe3_telemetry.vdp1_texture_destination_valid ||
        !avsp_probe3_telemetry.cart_to_vdp1_path_valid) {
        ++avsp_probe3_telemetry.copy_path_failures;
        avsp_probe3_fail(PROBE3_FAILURE_COPY_PATH);
        return 0;
    }
    if (!observation->draw_end_observed || !observation->draw_end_reliable ||
        observation->field_period_ticks == 0UL) {
        avsp_probe3_fail(PROBE3_FAILURE_DRAW_END_TIMESTAMP);
        return 0;
    }
    return 1;
}

static void update_result(volatile AvspProbe3ModeResult *result)
{
    result->workload_tile_draw_high_water = max_u32(
        result->workload_tile_draw_high_water,
        avsp_probe3_telemetry.requested_workload_tile_draws);
    result->submitted_workload_draw_high_water = max_u32(
        result->submitted_workload_draw_high_water,
        avsp_probe3_telemetry.submitted_workload_draw_calls);
    result->cpu_prepare_ticks_high_water = max_u32(
        result->cpu_prepare_ticks_high_water,
        avsp_probe3_telemetry.cpu_prepare_end_timestamp -
        avsp_probe3_telemetry.cpu_prepare_start_timestamp);
    result->texture_bytes_high_water = max_u32(result->texture_bytes_high_water,
        avsp_probe3_telemetry.texture_bytes_copied);
    result->copy_count_high_water = max_u32(result->copy_count_high_water,
        avsp_probe3_telemetry.copy_count);
    result->copy_ticks_high_water = max_u32(result->copy_ticks_high_water,
        avsp_probe3_telemetry.copy_ticks);
    result->cart_read_bytes_high_water = max_u32(
        result->cart_read_bytes_high_water,
        avsp_probe3_telemetry.cartridge_read_bytes);
    if (avsp_probe3_telemetry.draw_end_margin_ticks <
        result->min_draw_margin_ticks)
        result->min_draw_margin_ticks =
            avsp_probe3_telemetry.draw_end_margin_ticks;
    if (avsp_probe3_telemetry.draw_end_margin_percent_x100 <
        result->min_draw_margin_percent_x100)
        result->min_draw_margin_percent_x100 =
            avsp_probe3_telemetry.draw_end_margin_percent_x100;
}

void avsp_probe3_record_precheck(const AvspProbe3DeadlineObservation *observation,
                                const AvspProbe3Census *census)
{
    AvspProbe3Mode mode = (AvspProbe3Mode)avsp_probe3_telemetry.mode;
    volatile AvspProbe3ModeResult *result = &avsp_probe3_telemetry.result[mode];
    unsigned long tripped;
    if (!common_frame_valid(observation)) return;
    result->census = *census;
    if (census->submitted_workload_draw_calls !=
            census->requested_workload_tile_draws ||
        census->workload_tile_draw_commands !=
            census->requested_workload_tile_draws ||
        census->auxiliary_draw_commands != 1UL ||
        census->sgl_scaled_sprite_sentinel_draw_commands != 1UL ||
        census->total_reachable_draw_commands !=
            census->workload_tile_draw_commands +
            census->auxiliary_draw_commands ||
        census->reachable_state_commands != 3UL ||
        census->reachable_skipped_commands != 0UL ||
        census->reachable_table_entries !=
            census->total_reachable_draw_commands +
            census->reachable_state_commands + 1UL ||
        !census->terminator_present || census->invalid_link ||
        census->loop_detected || census->traversal_failure ||
        census->premature_end || census->table_truncated) {
        avsp_probe3_fail(PROBE3_FAILURE_COMMAND_TABLE);
        return;
    }
    tripped = avsp_probe3_deadline_tripped(observation);
    avsp_probe3_telemetry.detector_predicate_tripped = tripped;
    result->detector_tripped = tripped;
    update_result(result);
    if (mode == PROBE3_OVERLOAD) {
        avsp_probe3_telemetry.overload_tripped = tripped;
        if (!tripped) {
            avsp_probe3_fail(PROBE3_FAILURE_OVERLOAD_DID_NOT_TRIP);
            return;
        }
        avsp_probe3_telemetry.phase = PROBE3_PHASE_SOAK;
        avsp_probe3_telemetry.mode = PROBE3_REPRESENTATIVE;
        avsp_probe3_telemetry.mode_frame = 0UL;
        return;
    }
    if (tripped) {
        avsp_probe3_fail(PROBE3_FAILURE_OVERLOAD_FALSE_POSITIVE);
        return;
    }
    if (mode == PROBE3_REPRESENTATIVE) {
        avsp_probe3_telemetry.representative_workload_tile_draw_high_water =
            result->workload_tile_draw_high_water;
        avsp_probe3_telemetry.mode = PROBE3_PEAK_909;
    } else {
        avsp_probe3_telemetry.peak_workload_tile_draw_high_water =
            result->workload_tile_draw_high_water;
        avsp_probe3_telemetry.mode = PROBE3_OVERLOAD;
    }
    avsp_probe3_telemetry.mode_frame = 0UL;
    avsp_probe3_telemetry.phase = PROBE3_PHASE_PRECHECK_MEASURE;
}

void avsp_probe3_record_soak(const AvspProbe3DeadlineObservation *observation)
{
    unsigned long tripped;
    if (!common_frame_valid(observation)) return;
    tripped = avsp_probe3_deadline_tripped(observation);
    avsp_probe3_telemetry.detector_predicate_tripped = tripped;
    if (tripped) {
        ++avsp_probe3_telemetry.soak_missed_fields;
        ++avsp_probe3_telemetry.soak_late_lists;
        avsp_probe3_fail(PROBE3_FAILURE_PRODUCTION_DEADLINE);
        return;
    }
    if (observation->soak_elapsed_fields >
        avsp_probe3_telemetry.soak_elapsed_fields)
        avsp_probe3_telemetry.soak_elapsed_fields =
            observation->soak_elapsed_fields;
    ++avsp_probe3_telemetry.soak_workload_fields;
    avsp_probe3_telemetry.soak_requested_workload_high_water = max_u32(
        avsp_probe3_telemetry.soak_requested_workload_high_water,
        avsp_probe3_telemetry.requested_workload_tile_draws);
    avsp_probe3_telemetry.soak_submitted_workload_high_water = max_u32(
        avsp_probe3_telemetry.soak_submitted_workload_high_water,
        avsp_probe3_telemetry.submitted_workload_draw_calls);
    avsp_probe3_telemetry.soak_cpu_ticks_high_water = max_u32(
        avsp_probe3_telemetry.soak_cpu_ticks_high_water,
        avsp_probe3_telemetry.cpu_prepare_end_timestamp -
        avsp_probe3_telemetry.cpu_prepare_start_timestamp);
    avsp_probe3_telemetry.soak_transfer_ticks_high_water = max_u32(
        avsp_probe3_telemetry.soak_transfer_ticks_high_water,
        avsp_probe3_telemetry.transfer_end_timestamp -
        avsp_probe3_telemetry.transfer_start_timestamp);
    if (avsp_probe3_telemetry.draw_end_margin_ticks <
        avsp_probe3_telemetry.soak_min_draw_margin_ticks)
        avsp_probe3_telemetry.soak_min_draw_margin_ticks =
            avsp_probe3_telemetry.draw_end_margin_ticks;
    if (avsp_probe3_telemetry.draw_end_margin_percent_x100 <
        avsp_probe3_telemetry.soak_min_draw_margin_percent_x100)
        avsp_probe3_telemetry.soak_min_draw_margin_percent_x100 =
            avsp_probe3_telemetry.draw_end_margin_percent_x100;
    avsp_probe3_telemetry.mode =
        ((avsp_probe3_telemetry.soak_elapsed_fields /
          AVSP_PROBE3_SOAK_BLOCK_FIELDS) & 1UL) ?
        PROBE3_PEAK_909 : PROBE3_REPRESENTATIVE;
    if (avsp_probe3_telemetry.soak_elapsed_fields >= AVSP_PROBE3_SOAK_FIELDS)
        avsp_probe3_finish();
}

void avsp_probe3_finish(void)
{
    avsp_probe3_telemetry.phase = PROBE3_PHASE_SUMMARY;
    avsp_probe3_telemetry.status = PROBE3_STATUS_COMPLETE;
    avsp_probe3_telemetry.complete = 1UL;
    avsp_probe3_telemetry.summary_checksum = summary_checksum();
}
