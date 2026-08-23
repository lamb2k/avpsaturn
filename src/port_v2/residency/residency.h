#ifndef AVSP_PORT_V2_RESIDENCY_H
#define AVSP_PORT_V2_RESIDENCY_H

#define AVSP_PORT_V2_RESIDENCY_INTERFACE_VERSION 1
#define AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC 1
#define AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES 64
#define AVSP_PORT_V2_RESIDENCY_WORK_RAM_BYTES 72
#define AVSP_PORT_V2_RESIDENCY_CANARY_HEAD 0x52534844UL
#define AVSP_PORT_V2_RESIDENCY_CANARY_TAIL 0x5253544CUL

enum AvspPortV2ResidencyDomain
{
    AVSP_PORT_V2_DOMAIN_WORK_RAM = 0,
    AVSP_PORT_V2_DOMAIN_CARTRIDGE,
    AVSP_PORT_V2_DOMAIN_VDP1,
    AVSP_PORT_V2_DOMAIN_VDP2,
    AVSP_PORT_V2_DOMAIN_CRAM,
    AVSP_PORT_V2_DOMAIN_SCSP,
    AVSP_PORT_V2_DOMAIN_COUNT
};

enum AvspPortV2DiscOwner
{
    AVSP_PORT_V2_DISC_DATA = 0,
    AVSP_PORT_V2_DISC_CDDA = 1
};

typedef struct
{
    int region_id;
    int bytes;
    const char *payload_sha256;
} AvspPortV2ResidencyRegion;

typedef struct
{
    int track;
    int source_frame;
    int capacity_bytes[AVSP_PORT_V2_DOMAIN_COUNT];
    int phase_high_water_bytes[AVSP_PORT_V2_DOMAIN_COUNT];
    int canary_required[AVSP_PORT_V2_DOMAIN_COUNT];
    const AvspPortV2ResidencyRegion *regions;
    int region_count;
} AvspPortV2ResidencyManifest;

typedef struct
{
    unsigned long head_canary;
    int disc_owner;
    int window_open;
    int ownership_transitions;
    int legal_window_count;
    int legal_read_count;
    int late_read_attempts;
    int refused_windows;
    int negative_rejections;
    int failures;
    unsigned long tail_canary;
} AvspPortV2ResidencyRuntime;

typedef int (*AvspPortV2ResidencyRead)(int region_id,
                                       unsigned char *destination,
                                       int capacity);

typedef struct
{
    AvspPortV2ResidencyRead read;
} AvspPortV2ResidencyAssetOps;

extern const AvspPortV2ResidencyManifest
    avsp_port_v2_stage1_residency_manifest;

int avsp_port_v2_residency_validate_manifest(
    const AvspPortV2ResidencyManifest *manifest);
void avsp_port_v2_residency_init(AvspPortV2ResidencyRuntime *runtime);
int avsp_port_v2_residency_cdda_started(
    AvspPortV2ResidencyRuntime *runtime);
int avsp_port_v2_residency_cdda_stopped(
    AvspPortV2ResidencyRuntime *runtime);
int avsp_port_v2_residency_window_begin(
    AvspPortV2ResidencyRuntime *runtime);
int avsp_port_v2_residency_window_end(
    AvspPortV2ResidencyRuntime *runtime);
int avsp_port_v2_residency_submit_read(
    AvspPortV2ResidencyRuntime *runtime,
    int region_id,
    unsigned char *destination,
    int capacity,
    const AvspPortV2ResidencyAssetOps *operations);
int avsp_port_v2_residency_canaries_ok(
    const AvspPortV2ResidencyRuntime *runtime);

#endif
