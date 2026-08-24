#ifndef AVSP_PROBE3_H
#define AVSP_PROBE3_H

#include "generated/probe3_schedule.h"

#define AVSP_PROBE3_MAGIC 0x50524233UL
#define AVSP_PROBE3_SCHEMA 1UL
#define AVSP_PROBE3_CANARY 0xA53C19E7UL
#define AVSP_PROBE3_NORMAL_MODE_FRAMES 120UL

typedef enum
{
    PROBE3_REPRESENTATIVE = 0,
    PROBE3_PEAK_909 = 1,
    PROBE3_OVERLOAD = 2,
    PROBE3_MODE_COUNT = 3
} AvspProbe3Mode;

typedef enum
{
    PROBE3_STATUS_UNINITIALIZED = 0,
    PROBE3_STATUS_RUNNING = 1,
    PROBE3_STATUS_COMPLETE = 2,
    PROBE3_STATUS_FAILED = 3
} AvspProbe3Status;

typedef enum
{
    PROBE3_FAILURE_NONE = 0,
    PROBE3_FAILURE_ASSET = 1,
    PROBE3_FAILURE_COMMAND_COUNT = 2,
    PROBE3_FAILURE_CANARY = 3,
    PROBE3_FAILURE_OVERLOAD_DID_NOT_TRIP = 4,
    PROBE3_FAILURE_ILLEGAL_COPY_DIRECTION = 5
} AvspProbe3Failure;

typedef struct
{
    unsigned long reachable_high_water;
    unsigned long drawn_high_water;
    unsigned long cpu_prepare_ticks_high_water;
    unsigned long texture_bytes_high_water;
    unsigned long copy_count_high_water;
    unsigned long copy_ticks_high_water;
    unsigned long cart_read_bytes_high_water;
    unsigned long missed_fields;
    unsigned long late_lists;
    unsigned long detector_tripped;
} AvspProbe3ModeResult;

/* Fixed-size, linker-visible work-RAM block.  The map address is copied into
 * the Probe 3 manifest and the MCP readback reads this exact symbol. */
typedef struct
{
    unsigned long canary_begin;
    unsigned long magic;
    unsigned long schema;
    unsigned long status;
    unsigned long mode;
    unsigned long mode_frame;
    unsigned long frame_number;
    unsigned long workload_checksum_word;
    unsigned long reachable_commands;
    unsigned long drawn_commands;
    unsigned long vdp1_draw_end_state;
    unsigned long draw_end_deadline_fields;
    unsigned long cpu_prepare_ticks;
    unsigned long texture_bytes_copied;
    unsigned long copy_count;
    unsigned long copy_ticks;
    unsigned long legal_copy_direction;
    unsigned long cram_writes;
    unsigned long cartridge_read_bytes;
    unsigned long missed_fields;
    unsigned long late_command_lists;
    unsigned long skipped_fields;
    unsigned long repeated_fields;
    unsigned long canary_state;
    unsigned long asset_failures;
    unsigned long failure_reason;
    unsigned long overload_expected;
    unsigned long overload_tripped;
    unsigned long representative_high_water;
    unsigned long peak_high_water;
    unsigned long summary_checksum;
    unsigned long complete;
    AvspProbe3ModeResult result[PROBE3_MODE_COUNT];
    unsigned long canary_end;
} AvspProbe3Telemetry;

extern volatile AvspProbe3Telemetry avsp_probe3_telemetry;

void avsp_probe3_init(void);
const AvspProbe3Schedule *avsp_probe3_schedule(void);
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
    unsigned long asset_failures);

#endif
