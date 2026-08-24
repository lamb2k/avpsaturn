#ifndef AVSP_PROBE3_H
#define AVSP_PROBE3_H

#include "generated/probe3_schedule.h"

#define AVSP_PROBE3_MAGIC 0x50524233UL
#define AVSP_PROBE3_SCHEMA 3UL
#define AVSP_PROBE3_CANARY 0xA53C19E7UL
#define AVSP_PROBE3_NORMAL_MODE_FRAMES 120UL
#define AVSP_PROBE3_SOAK_FIELDS 36000UL
#define AVSP_PROBE3_SOAK_BLOCK_FIELDS 60UL
#define AVSP_PROBE3_FRC_DIVISOR 32UL
#define AVSP_PROBE3_VDP1_TABLE_BYTES 0x10000UL

typedef enum { PROBE3_REPRESENTATIVE = 0, PROBE3_PEAK_909 = 1,
    PROBE3_OVERLOAD = 2, PROBE3_MODE_COUNT = 3 } AvspProbe3Mode;
typedef enum { PROBE3_PHASE_PRECHECK_MEASURE = 0,
    PROBE3_PHASE_PRECHECK_VALIDATE = 1, PROBE3_PHASE_SOAK = 2,
    PROBE3_PHASE_SUMMARY = 3 } AvspProbe3Phase;
typedef enum { PROBE3_STATUS_UNINITIALIZED = 0, PROBE3_STATUS_RUNNING = 1,
    PROBE3_STATUS_COMPLETE = 2, PROBE3_STATUS_FAILED = 3 } AvspProbe3Status;
typedef enum { PROBE3_FAILURE_NONE = 0, PROBE3_FAILURE_ASSET = 1,
    PROBE3_FAILURE_COMMAND_COUNT = 2, PROBE3_FAILURE_CANARY = 3,
    PROBE3_FAILURE_OVERLOAD_DID_NOT_TRIP = 4,
    PROBE3_FAILURE_COPY_PATH = 5, PROBE3_FAILURE_COMMAND_TABLE = 6,
    PROBE3_FAILURE_DRAW_END_TIMESTAMP = 7,
    PROBE3_FAILURE_PRODUCTION_DEADLINE = 8,
    PROBE3_FAILURE_OVERLOAD_FALSE_POSITIVE = 9 } AvspProbe3Failure;

typedef struct {
    unsigned long detector_enabled, draw_end_observed, draw_end_reliable;
    unsigned long field_delta, deadline_fields, draw_elapsed_ticks;
    unsigned long field_period_ticks, soak_elapsed_fields;
} AvspProbe3DeadlineObservation;

typedef struct {
    unsigned long requested_workload_tile_draws;
    unsigned long submitted_workload_draw_calls;
    unsigned long stored_nonzero_slots;
    unsigned long reachable_table_entries;
    unsigned long workload_tile_draw_commands;
    unsigned long auxiliary_draw_commands;
    unsigned long sgl_scaled_sprite_sentinel_draw_commands;
    unsigned long total_reachable_draw_commands;
    unsigned long reachable_state_commands;
    unsigned long reachable_skipped_commands;
    unsigned long terminator_present, invalid_link;
    unsigned long loop_detected, traversal_failure, premature_end;
    unsigned long table_truncated;
} AvspProbe3Census;

typedef struct {
    unsigned long workload_tile_draw_high_water;
    unsigned long submitted_workload_draw_high_water;
    unsigned long cpu_prepare_ticks_high_water, texture_bytes_high_water;
    unsigned long copy_count_high_water, copy_ticks_high_water;
    unsigned long cart_read_bytes_high_water, missed_fields, late_lists;
    unsigned long detector_tripped, min_draw_margin_ticks;
    unsigned long min_draw_margin_percent_x100;
    AvspProbe3Census census;
} AvspProbe3ModeResult;

/* Fixed linker-visible work-RAM block. The manifest records its exact size. */
typedef struct {
    unsigned long canary_begin, magic, schema, status, phase, mode;
    unsigned long mode_frame, frame_number, workload_checksum_word;
    unsigned long requested_workload_tile_draws;
    unsigned long submitted_workload_draw_calls;
    unsigned long vdp1_draw_end_state, draw_end_deadline_fields;
    unsigned long detector_enabled, detector_predicate_tripped, field_delta;
    unsigned long field_start_timestamp, field_period_ticks;
    unsigned long cpu_prepare_start_timestamp, cpu_prepare_end_timestamp;
    unsigned long transfer_start_timestamp, transfer_end_timestamp;
    unsigned long submission_timestamp, draw_end_timestamp;
    unsigned long draw_end_timestamp_reliable, draw_end_margin_ticks;
    unsigned long draw_end_margin_percent_x100, total_frame_margin_ticks;
    unsigned long total_frame_margin_percent_x100, timer_wrapped;
    unsigned long timer_divisor, timer_calibration_field_ticks;
    unsigned long texture_bytes_copied, copy_count, copy_ticks;
    unsigned long cart_texture_source_valid;
    unsigned long vdp1_texture_destination_valid;
    unsigned long cart_to_vdp1_path_valid, cram_writes;
    unsigned long cartridge_read_bytes, missed_fields, late_command_lists;
    unsigned long skipped_fields, repeated_fields, canary_state;
    unsigned long asset_failures, copy_path_failures, failure_reason;
    unsigned long overload_expected, overload_tripped;
    unsigned long representative_workload_tile_draw_high_water;
    unsigned long peak_workload_tile_draw_high_water;
    unsigned long soak_target_fields, soak_elapsed_fields;
    unsigned long soak_workload_fields, soak_block_fields;
    unsigned long soak_requested_workload_high_water;
    unsigned long soak_submitted_workload_high_water;
    unsigned long soak_cpu_ticks_high_water, soak_transfer_ticks_high_water;
    unsigned long soak_min_draw_margin_ticks;
    unsigned long soak_min_draw_margin_percent_x100;
    unsigned long soak_missed_fields, soak_late_lists;
    unsigned long soak_skipped_fields, soak_repeated_fields;
    unsigned long soak_canary_failures, soak_asset_failures;
    unsigned long soak_copy_path_failures, summary_checksum, complete;
    AvspProbe3ModeResult result[PROBE3_MODE_COUNT];
    unsigned long canary_end;
} AvspProbe3Telemetry;

extern volatile AvspProbe3Telemetry avsp_probe3_telemetry;
void avsp_probe3_init(void);
const AvspProbe3Schedule *avsp_probe3_schedule(void);
unsigned long avsp_probe3_deadline_tripped(
    const AvspProbe3DeadlineObservation *observation);
void avsp_probe3_census(const volatile unsigned short *vdp1_vram,
                        unsigned long table_bytes,
                        unsigned long expected_draws,
                        AvspProbe3Census *census);
void avsp_probe3_record_precheck(const AvspProbe3DeadlineObservation *observation,
                                const AvspProbe3Census *census);
void avsp_probe3_record_soak(const AvspProbe3DeadlineObservation *observation);
void avsp_probe3_fail(AvspProbe3Failure reason);
void avsp_probe3_finish(void);
#endif
