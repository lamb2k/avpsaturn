#ifndef AVSP_PORT_V2_INTEGRATION_SLICE_H
#define AVSP_PORT_V2_INTEGRATION_SLICE_H

#include "../combat/combat.h"
#include "../../camera/camera.h"
#include "../../stage/stage.h"
#include "../../hud/hud.h"
#include "../../audio/pcm/pcm.h"
#include "../../audio/cdda/cdda.h"
#include "../../residency/residency.h"

#define AVSP_PORT_V2_SLICE_INTERFACE_VERSION 3
#define AVSP_PORT_V2_SLICE_CANARY_HEAD 0x534C4844UL
#define AVSP_PORT_V2_SLICE_CANARY_TAIL 0x534C544CUL

#define AVSP_PORT_V2_SLICE_ACTOR_PLAYER 1
#define AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN 31
#define AVSP_PORT_V2_SLICE_ROLE_PLAYER 1
#define AVSP_PORT_V2_SLICE_ROLE_ENEMY 2
#define AVSP_PORT_V2_SLICE_CLASS_NOT_APPLICABLE (-1)
#define AVSP_PORT_V2_SLICE_ARCHETYPE_PREDATOR_WARRIOR 1
#define AVSP_PORT_V2_SLICE_ARCHETYPE_STREET_ALIEN 31
#define AVSP_PORT_V2_SLICE_ARCHETYPE_STALKER 100
#define AVSP_PORT_V2_SLICE_ASSET_PLAYER_APPROVED 1
#define AVSP_PORT_V2_SLICE_ASSET_STREET_ALIEN_ROM 2
#define AVSP_PORT_V2_SLICE_ASSET_STALKER_CAPTURE 3
#define AVSP_PORT_V2_SLICE_ANIM_PLAYER_APPROVED 1
#define AVSP_PORT_V2_SLICE_ANIM_STREET_ALIEN_ROM 2
#define AVSP_PORT_V2_SLICE_ANIM_STALKER_CAPTURE 3
#define AVSP_PORT_V2_SLICE_PLAYER_WORLD_X_INITIAL 304
#define AVSP_PORT_V2_SLICE_PLAYER_LANE_INITIAL 178
#define AVSP_PORT_V2_SLICE_ENEMY_WORLD_X_INITIAL 128
#define AVSP_PORT_V2_SLICE_ENEMY_LANE 200
#define AVSP_PORT_V2_SLICE_APERTURE_ORIGIN_X (-176)
#define AVSP_PORT_V2_SLICE_SOURCE_FIRST 5173
#define AVSP_PORT_V2_SLICE_SOURCE_LAST 5469
#define AVSP_PORT_V2_SLICE_SOURCE_FIRST_CONTACT 5190
#define AVSP_PORT_V2_SLICE_FIRST_CONTACT_FRAME 600
#define AVSP_PORT_V2_SLICE_SOURCE_PLAYER_ANCHOR_X 440
#define AVSP_PORT_V2_SLICE_SOURCE_PLAYER_ANCHOR_LANE 208
#define AVSP_PORT_V2_SLICE_ENEMY_WALK_RECORD 0x0012EB4CUL

typedef enum
{
    AVSP_PORT_V2_SLICE_ACTION_IDLE = 0,
    AVSP_PORT_V2_SLICE_ACTION_WALK = 1,
    AVSP_PORT_V2_SLICE_ACTION_ATTACK = 2,
    AVSP_PORT_V2_SLICE_ACTION_HIT = 3,
    AVSP_PORT_V2_SLICE_ACTION_KO = 4
} AvspPortV2SliceAction;

typedef struct
{
    int actor_id;
    int role;
    int class_id;
    int archetype_id;
    int asset_set_id;
    int animation_set_id;
    int palette_bank;
    unsigned long animation_record;
    unsigned long emitted_object_identity;
    unsigned long emitted_tile_identity;
} AvspPortV2SliceActorIdentity;

typedef struct
{
    int player_world_x;
    int enemy_world_x;
    int camera_world_x;
    int aperture_origin_x;
    int player_screen_x;
    int enemy_screen_x;
    int player_delta_world_x;
    int enemy_delta_world_x;
    int delta_camera_world_x;
    int player_delta_screen_x;
    int enemy_delta_screen_x;
    int layer_scroll_x[AVSP_PORT_V2_CAMERA_LAYER_COUNT];
    int player_action;
    int player_action_frame;
    int player_attack_active;
    int player_presentation_active;
    int source_sample;
    int source_event_index;
    int attack_sequence_step;
    int attack_selector;
    int player_source_action;
    int player_source_substate;
    int player_source_pose;
    int player_source_pivot_x;
    int player_source_pivot_y;
    int player_source_height;
    int enemy_action;
    int enemy_action_frame;
    int enemy_source_action;
    int enemy_source_substate;
    int collision_result;
    int attacker_id;
    int defender_id;
    int health_before;
    int health_after;
    int semantic_hit;
    int semantic_ko;
    AvspPortV2SliceActorIdentity player_identity;
    AvspPortV2SliceActorIdentity enemy_identity;
} AvspPortV2SliceSceneTrace;

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
    int player_attack;
    int player_height;
    int enemy_move;
    AvspPortV2CameraInput camera;
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
    AvspPortV2SliceSceneTrace scene;
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
    int player_world_x;
    int player_lane;
    int player_height;
    int enemy_world_x;
    int enemy_lane;
    int camera_world_x;
    int previous_player_world_x;
    int previous_enemy_world_x;
    int previous_camera_world_x;
    int player_attack_active;
    int player_attack_frame;
    int player_attack_previous;
    int player_attack_contact_attempted;
    int source_sample;
    int source_event_index;
    int armed_source_event;
    int player_presentation_active;
    AvspPortV2PlayerCombatPresentation player_source;
    AvspPortV2CombatEnemyPresentation enemy_source;
    int contact_this_frame;
    int enemy_action;
    int enemy_action_frame;
    int semantic_hit;
    int semantic_ko;
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
int avsp_port_v2_slice_identity_valid(
    const AvspPortV2SliceActorIdentity *identity);
int avsp_port_v2_slice_scene_valid(const AvspPortV2SliceSceneTrace *scene);

#endif
