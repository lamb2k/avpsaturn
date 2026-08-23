#ifndef AVSP_PORT_V2_INTEGRATION_SLICE_H
#define AVSP_PORT_V2_INTEGRATION_SLICE_H

#include "../combat/combat.h"
#include "../../camera/camera.h"
#include "../../stage/stage.h"
#include "../../hud/hud.h"
#include "../../audio/pcm/pcm.h"
#include "../../audio/cdda/cdda.h"
#include "../../residency/residency.h"

#define AVSP_PORT_V2_SLICE_INTERFACE_VERSION 1
#define AVSP_PORT_V2_SLICE_CANARY_HEAD 0x534C4844UL
#define AVSP_PORT_V2_SLICE_CANARY_TAIL 0x534C544CUL

typedef int (*AvspPortV2SliceLoadStep)(void);

typedef struct
{
    AvspPortV2ResidencyAssetOps residency_assets;
    AvspPortV2PlayerEnemyLoadOps actor_assets;
    AvspPortV2SliceLoadStep load_hud;
    AvspPortV2SliceLoadStep load_pcm;
} AvspPortV2SliceLoadOps;

typedef struct
{
    int frame;
    AvspPortV2PlayerInput player;
    int enemy_translated;
    AvspPortV2CameraInput camera;
    int contact_event;
    int contact_index;
    int player_health;
    int player_energy;
    int player2_visible;
    int player2_health;
    int player2_energy;
    int pcm_cue_event;
    int cdda_command;
} AvspPortV2SliceInput;

typedef struct
{
    int interface_version;
    int ready;
    int frame;
    AvspPortV2PlayerEnemyView actors;
    AvspPortV2CameraView camera;
    AvspPortV2StageFrame stage;
    AvspPortV2HudFrame hud;
    AvspPortV2PcmFrame pcm;
    AvspPortV2CddaFrame cdda;
    AvspPortV2CombatEvent combat;
    int combat_event_count;
    int asset_failures;
    int fallback_used;
    int canaries_ok;
} AvspPortV2SliceFrame;

typedef struct
{
    unsigned long head_canary;
    AvspPortV2CombatRuntime combat;
    AvspPortV2CameraRuntime camera;
    AvspPortV2PcmRuntime pcm;
    AvspPortV2CddaRuntime cdda;
    AvspPortV2ResidencyRuntime residency;
    unsigned char residency_buffer[AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES];
    AvspPortV2CombatEvent last_combat;
    int ready;
    int frame;
    int combat_event_count;
    int asset_failures;
    int fallback_used;
    unsigned long tail_canary;
} AvspPortV2SliceRuntime;

int avsp_port_v2_slice_approval_locks_valid(void);
void avsp_port_v2_slice_init(AvspPortV2SliceRuntime *runtime);
int avsp_port_v2_slice_load(AvspPortV2SliceRuntime *runtime,
                            int cartridge_available,
                            const AvspPortV2SliceLoadOps *operations);
int avsp_port_v2_slice_step(AvspPortV2SliceRuntime *runtime,
                            const AvspPortV2SliceInput *input,
                            AvspPortV2SliceFrame *frame);
int avsp_port_v2_slice_submit_read(AvspPortV2SliceRuntime *runtime,
                                   int region_id,
                                   unsigned char *destination,
                                   int capacity,
                                   const AvspPortV2ResidencyAssetOps *operations);
int avsp_port_v2_slice_canaries_ok(const AvspPortV2SliceRuntime *runtime);

#endif
