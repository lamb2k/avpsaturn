#ifndef AVSP_CDDA_RESIDENCY_BENCH_H
#define AVSP_CDDA_RESIDENCY_BENCH_H

#define AVSP_CDDA_RESIDENCY_INTERFACE_VERSION 1
#define AVSP_CDDA_RESIDENCY_CYCLE_FRAMES 300
#define AVSP_CDDA_RESIDENCY_TRACK 2
#define AVSP_CDDA_RESIDENCY_SOURCE_FRAME 2520
#define AVSP_CDDA_RESIDENCY_FIXTURE_BYTES 64
#define AVSP_CDDA_RESIDENCY_WORK_RAM_BYTES \
    (AVSP_CDDA_RESIDENCY_FIXTURE_BYTES + 8)
#define AVSP_CDDA_RESIDENCY_CANARY_HEAD 0x43445248UL
#define AVSP_CDDA_RESIDENCY_CANARY_TAIL 0x43445254UL

enum AvspCddaResidencyDomain
{
    AVSP_CDDA_DOMAIN_WORK_RAM = 0,
    AVSP_CDDA_DOMAIN_CARTRIDGE,
    AVSP_CDDA_DOMAIN_VDP1,
    AVSP_CDDA_DOMAIN_VDP2,
    AVSP_CDDA_DOMAIN_CRAM,
    AVSP_CDDA_DOMAIN_SCSP,
    AVSP_CDDA_DOMAIN_COUNT
};

enum AvspCddaResidencyAction
{
    AVSP_CDDA_ACTION_NONE = 0,
    AVSP_CDDA_ACTION_START_TRACK,
    AVSP_CDDA_ACTION_ILLEGAL_READ,
    AVSP_CDDA_ACTION_ILLEGAL_WINDOW,
    AVSP_CDDA_ACTION_STOP_TRACK,
    AVSP_CDDA_ACTION_WINDOW_BEGIN,
    AVSP_CDDA_ACTION_LEGAL_READ,
    AVSP_CDDA_ACTION_WINDOW_END
};

typedef struct
{
    int track;
    int source_frame;
    int capacity_bytes[AVSP_CDDA_DOMAIN_COUNT];
    int phase_high_water_bytes[AVSP_CDDA_DOMAIN_COUNT];
    int canary_required[AVSP_CDDA_DOMAIN_COUNT];
} AvspCddaResidencyManifest;

typedef struct
{
    unsigned long head_canary;
    int frame;
    int cdda_active;
    int window_open;
    int ownership_transitions;
    int track_event_count;
    int legal_window_count;
    int legal_read_count;
    int negative_rejections;
    int failures;
    unsigned long tail_canary;
} AvspCddaResidencyRuntime;

typedef struct
{
    int relative_frame;
    int action;
} AvspCddaResidencyFrame;

extern const AvspCddaResidencyManifest avsp_cdda_residency_manifest;

int avsp_cdda_residency_validate_manifest(
    const AvspCddaResidencyManifest *manifest);
void avsp_cdda_residency_init(AvspCddaResidencyRuntime *runtime);
int avsp_cdda_residency_step(AvspCddaResidencyRuntime *runtime,
                             AvspCddaResidencyFrame *frame);
int avsp_cdda_residency_observe(AvspCddaResidencyRuntime *runtime,
                                const AvspCddaResidencyFrame *frame,
                                int operation_succeeded);
int avsp_cdda_residency_canaries_ok(
    const AvspCddaResidencyRuntime *runtime);

#endif
