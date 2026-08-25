#include <jo/jo.h>
#include <string.h>
#include "capability_model.h"
#include "avsp_tiles.h"
#include "avsp_collision.h"
#include "avsp_cram.h"
#include "avsp_frontend.h"
#include "avsp_disc_guard.h"
#include "src/port_v2/player/player.h"
#include "src/port_v2/enemy/enemy.h"
#include "src/port_v2/camera/camera.h"
#include "src/port_v2/stage/stage.h"
#include "src/port_v2/hud/hud.h"
#include "src/port_v2/audio/pcm/pcm.h"
#include "src/port_v2/integration/player_enemy/player_enemy.h"
#ifdef AVSP_COLLISION_SALVAGE_BENCH
#include "tests/port_v2/collision_bench/collision_bench.h"
#endif
#ifdef AVSP_CDDA_RESIDENCY_SALVAGE_BENCH
#include "tests/port_v2/cdda_residency_bench/cdda_residency_bench.h"
#endif
#ifdef AVSP_CDDA_RESIDENCY_PROMOTION_BENCH
#include "src/port_v2/audio/cdda/cdda.h"
#include "src/port_v2/residency/residency.h"
#endif
#ifdef AVSP_HIT_KO_PROMOTION_BENCH
#include "tests/port_v2/combat/hit_ko/diagnostic.h"
#endif
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
#include "src/port_v2/integration/combat/combat.h"
#include "src/port_v2/integration/combat/source_player_generated.h"
#include "tests/port_v2/integration/combat/diagnostic.h"
#endif
#ifdef AVSP_PLAYABLE_SLICE
/* Human-review pacing only. Source samples, damage, HIT, and KO semantics
 * remain owned by the deterministic Port V2 combat integration. */
#include "src/port_v2/integration/slice/slice.h"
#endif
#ifdef AVSP_LIVE_ENCOUNTER
#include "src/port_v2/integration/live_encounter/live_encounter.h"
#endif
#ifdef AVSP_PROBE3
#include "tests/hardware/probe3/probe3.h"
#endif
#ifdef AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH
#include "tests/port_v2/predator_warrior_action_bench/predator_warrior_action_bench.h"
#elif defined(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH)
#include "src/port_v2/gameplay/player_action/player_action.h"
#endif
#ifdef AVSP_STREET_ALIEN_AI_SALVAGE_BENCH
#include "tests/port_v2/street_alien_ai_bench/street_alien_ai_bench.h"
#elif defined(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH)
#include "src/port_v2/gameplay/street_alien_ai/street_alien_ai.h"
#endif

#include "generated/avsp_anim_records.h"
#include "generated/avsp_emit_windows.h"
#include "generated/avsp_boss_animation.h"
#include "generated/avsp_boss_clear_audio.h"
#include "generated/avsp_boss_intro_audio.h"
#include "generated/avsp_boss_rom.h"
#include "generated/avsp_breach_audio.h"
#include "generated/avsp_audio.h"
#include "generated/avsp_contact_audio.h"
#include "generated/avsp_door_dialogue_audio.h"
#include "generated/avsp_enemy_animation.h"
#include "generated/avsp_hud.h"
#include "generated/avsp_ko_contact_audio.h"
#include "generated/avsp_interior_transition_audio.h"
#include "generated/avsp_melee_audio.h"
#include "generated/avsp_palette.h"
#include "generated/avsp_player_action_animation.h"
#include "generated/avsp_round_title_a_audio.h"
#include "generated/avsp_round_title_b_audio.h"
#include "generated/avsp_sequence_palette.h"
#include "generated/avsp_stalker_animation.h"
#include "generated/avsp_withdraw_audio.h"

#define CEL_WIDTH 192
#define CEL_HEIGHT 192
#define CEL_BYTES ((CEL_WIDTH * CEL_HEIGHT) / 2)
#define BACKGROUND_WIDTH CAP_BACKGROUND_WIDTH
#define BACKGROUND_HEIGHT 256
#define SNAPSHOT_FIT_WIDTH CAP_VIEW_WIDTH
#define SNAPSHOT_HEIGHT 224
#define SNAPSHOT_FIT_BYTES (SNAPSHOT_FIT_WIDTH * SNAPSHOT_HEIGHT)
#define AVSP_CART_DRAM1_BASE ((unsigned char *)0x22600000)
#define AVSP_CART_DRAM1_BYTES 0x200000
/* Body E: the ROM tile archive owns a carved region at the head of
   cartridge bank 1, mirroring the reference port's cart-resident,
   byte-stable texture source; only the remainder joins the general
   allocator, so the archive can never displace main-pool assets.
   MEASURED budget ceiling: growing this to 0xC0000 for the full
   four-route archive (612,720 bytes) left EACT.RLE (131,552 bytes)
   with no single zone holding it - cart bank0 had ~13 KB free and
   bank1 ~103 KB, neither enough alone. The street-only archive
   (202,564 bytes) is what currently fits; widening to stalkers/boss
   needs more PCM moved to phase-boundary loads first (S3 enabler,
   tracked in the handoff), not a bigger carve alone. */
/* Widened from 0x40000 for the RP4 street archive (297,764 bytes with the
 * representative-interval object tiles). Scene loading boundaries are the
 * residency lever: the carve holds one scene-scope archive at a time and is
 * reloaded during transitions, when data-track reads are legal. */
#define AVSP_TILE_REGION_BYTES 0x50000

/* RP4 street test: the interval strip bundle is staged after the tile
 * carve, outside the allocator, only in that build profile. */
#ifdef AVSP_STREET_TEST
#define AVSP_STRIPS_REGION_BYTES 0x48000
#else
#define AVSP_STRIPS_REGION_BYTES 0
#endif

#ifdef AVSP_STREET_TEST
/* MEASURED (live write watchpoint at 0x25E40000 -> prnt_0): SGL's
 * slPrint/slLocate write the ASCII text map at VDP2_VRAM_B0 (0x25E40000),
 * which the street test owns as the NBG0 pattern-name area. Every
 * jo_printf in this profile is therefore redirected into a work-RAM
 * buffer that the debug rig reads back over MCP, and frame_callback's
 * jo_clear_screen is compiled out; nothing may write the ASCII layer. */
char avsp_diag_print_buffer[128];
#undef jo_printf
#define jo_printf(X, Y, ...) sprintf(avsp_diag_print_buffer, __VA_ARGS__)
#endif
#define AVSP_PCM_CHANNEL_WEAPON 0
#define AVSP_PCM_CHANNEL_MELEE 1
#define AVSP_PCM_CHANNEL_CONTACT 2
#define AVSP_PCM_CHANNEL_SEQUENCE 3
#define AVSP_PCM_CHANNEL_TRANSITION 4
#define AVSP_PCM_CHANNEL_OPENING 5
#define BITMAP_SCENE_NONE (-1000)
#define BITMAP_SCENE_CORRIDOR (-2)
#define BITMAP_SCENE_BOSS (-3)
#define BITMAP_SCENE_FRONTEND_BASE 100
#define BITMAP_SCENE_ROUTE_BASE 200
#define AVSP_VDP1_TEXTURE_BUDGET 458488
/* S2 Body E: resident VDP1 pool of 16x16 ROM tile textures, LRU-replaced
   in place, so the per-frame cost is command-table-only (the reference
   port's measured model: per-16x16-tile normal sprites in colour-bank
   mode). */
#define AVSP_TILE_SPRITE_POOL 96
#define AVSP_VDP1_TEXTURE_BYTES \
    (2 * CEL_BYTES + \
     AVSP_PLAYER_ACTION_LAYERS * AVSP_PLAYER_ACTION_DECODED_BYTES + \
     CAP_MAX_ENEMIES * AVSP_ENEMY_DECODED_BYTES + \
     AVSP_BOSS_DECODED_BYTES + \
     AVSP_HUD_TEXTURE_BYTES + \
     AVSP_TILE_SPRITE_POOL * AVSP_TILE_BYTES + \
     AVSP_FRONTEND_VDP1_MAX_BYTES)

#if JO_TV_WIDTH != CAP_VIEW_WIDTH || JO_TV_HEIGHT != 224
#error "The AvP fidelity build requires Saturn TV_352x224"
#endif
#if AVSP_FRONTEND_START_TRANSITION_FRAMES != CAP_START_TRANSITION_FRAMES
#error "Frontend model and generated source transition schedules differ"
#endif
#if AVSP_STALKER_DECODED_BYTES != AVSP_ENEMY_DECODED_BYTES || \
    AVSP_STALKER_CEL_WIDTH != AVSP_ENEMY_CEL_WIDTH || \
    AVSP_STALKER_CEL_HEIGHT != AVSP_ENEMY_CEL_HEIGHT
#error "Stalker clips must reuse the existing alien VDP1 slot pool"
#endif
#if AVSP_VDP1_TEXTURE_BYTES > AVSP_VDP1_TEXTURE_BUDGET
#error "The AvP actor working set exceeds Saturn VDP1 texture VRAM"
#endif

extern jo_color *nbg1_bitmap;

typedef enum
{
    CEL_PLAYER_IDLE_0 = 0,
    CEL_PLAYER_IDLE_1,
    CEL_COUNT
} CelId;

typedef struct
{
    const char *filename;
    unsigned short width;
    unsigned short height;
    int expected_bytes;
    jo_img_4bits image;
} CelAsset;

static CelAsset cel_assets[CEL_COUNT] =
{
    {"PXI0.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}},
    {"PXI1.BIN", CEL_WIDTH, CEL_HEIGHT, CEL_BYTES, {0, 0, JO_NULL}}
};

static CapWorld world;
static jo_palette background_palette;
static jo_palette boss_background_palette;
static jo_palette actor_palette;
static jo_palette hud_palette;
static jo_palette frontend_palettes[AVSP_FRONTEND_SCENES];
static jo_img_8bits background_image;
static jo_img_8bits boss_background_image;
static AvspFrontend frontend_runtime;
static unsigned char *sequence_rle[AVSP_SEQUENCE_SCENES];
static unsigned char *sequence_pixels;
static unsigned char *background_bitmap;
static unsigned char *player_action_archive;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
static unsigned char *source_combat_player_archive;
static jo_img_4bits source_combat_player_image;
#endif
static unsigned char *enemy_action_archive;
static unsigned char *stalker_action_archive;
static unsigned char *enemy_action_buffer;
static jo_img_4bits player_action_images[AVSP_PLAYER_ACTION_LAYERS];
static jo_img_4bits enemy_action_images[CAP_MAX_ENEMIES];
static jo_img_4bits boss_action_image;
static jo_img_8bits hud_top_image;
static jo_img_8bits hud_prompt_image;
static jo_img_8bits hud_heat_image;
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static jo_img_8bits hud_p2_top_image;
static jo_img_8bits hud_p2_heat_image;
#endif
static jo_sound weapon_sound;
static jo_sound melee_sound;
static jo_sound contact_sound;
static jo_sound ko_contact_sound;
static jo_sound *contact_channel_sound;
static jo_sound boss_intro_sound;
static jo_sound boss_clear_sound;
static jo_sound *sequence_channel_sound;
static jo_sound door_dialogue_sound;
static jo_sound interior_transition_sound;
static jo_sound *transition_channel_sound;
static jo_sound round_title_a_sound;
static jo_sound round_title_b_sound;
static jo_sound withdraw_sound;
static jo_sound breach_sound;
static jo_sound *opening_channel_sound;
static int player_idle_sprites[2];
static int player_action_sprites[AVSP_PLAYER_ACTION_LAYERS];
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
static int source_combat_player_sprite;
static int current_source_combat_player_pose;
#endif
static int enemy_action_sprites[CAP_MAX_ENEMIES];
static int boss_action_sprite;
static int hud_top_sprite;
static int hud_prompt_sprite;
static int hud_heat_sprite;
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static int hud_p2_top_sprite;
static int hud_p2_heat_sprite;
#endif
static int displayed_hud_health;
static int displayed_hud_energy;
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static int displayed_hud_p2_health;
static int displayed_hud_p2_energy;
#endif
static int current_player_action_pose;
static int current_enemy_action_poses[CAP_MAX_ENEMIES];
static CapActorKind current_enemy_action_kinds[CAP_MAX_ENEMIES];
static int current_boss_action_pose;
static int debug_hud_enabled;
static const char *failed_asset;
static int runtime_ready;
static int cart_available;
static int stage_music_started;
static int weapon_audio_played_shots;
static int weapon_audio_pending_shot;
static int weapon_audio_channel_observed;
static int melee_audio_pending;
static int melee_audio_play_count;
static int melee_audio_channel_observed;
static int contact_audio_play_count;
static int ko_contact_audio_play_count;
static int contact_audio_channel_observed;
static int boss_intro_audio_play_count;
static int boss_clear_audio_play_count;
static int sequence_audio_channel_observed;
static int door_dialogue_audio_play_count;
static int interior_transition_audio_play_count;
static int transition_audio_channel_observed;
static int round_title_a_audio_play_count;
static int round_title_b_audio_play_count;
static int withdraw_audio_play_count;
static int breach_audio_play_count;
static int opening_audio_channel_observed;
static int enemy_runtime_ready;
static int boss_runtime_ready;
static int current_bitmap_scene;

#ifdef AVSP_PLAYER_SALVAGE_BENCH
/* This is a presentation view only.  It deliberately does not own a
 * CapWorld, collision, camera, encounter timer, or combat action.  The
 * canaries make the view's bounded input update observable over MCP. */
#define PLAYER_BENCH_CANARY_HEAD 0x50564248UL
#define PLAYER_BENCH_CANARY_TAIL 0x50564254UL
typedef struct
{
    unsigned long head_canary;
    CapActor actor;
    unsigned long tail_canary;
} PlayerBenchView;
static PlayerBenchView player_bench;
static int player_bench_frame;
#ifndef AVSP_PLAYER_PROMOTION_BENCH
static int player_bench_previous_input;
#endif
#ifdef AVSP_PLAYER_PROMOTION_BENCH
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
static AvspPortV2CombatRuntime combat_port_v2;
static int combat_last_event_count;
#define player_enemy_port_v2 combat_port_v2.presentation
#else
static AvspPortV2PlayerEnemyRuntime player_enemy_port_v2;
#endif
#else
static AvspPortV2PlayerRuntime player_port_v2;
#endif
#endif
#endif

#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
#define HUD_PCM_BENCH_CANARY_HEAD 0x48504348UL
#define HUD_PCM_BENCH_CANARY_TAIL 0x48504354UL
#define HUD_PCM_BENCH_CYCLE_FRAMES 480
#define HUD_PCM_BENCH_FIRST_EVENT 147
#define HUD_PCM_BENCH_SECOND_EVENT 387
#define HUD_PCM_BENCH_START_DELAY 3
#define HUD_PCM_BENCH_PCM_FRAMES \
    ((((AVSP_MELEE_PCM_BYTES / 4) * 60) + \
      AVSP_MELEE_PCM_SAMPLE_RATE - 1) / AVSP_MELEE_PCM_SAMPLE_RATE)
typedef struct
{
    unsigned long head_canary;
    int frame;
    int pending;
    int pcm_active;
    int planned_end_frame;
    int underrun_reported_start;
    int negative_control_mask;
    int p2_health;
    int p2_energy;
    unsigned long tail_canary;
} HudPcmBenchState;
static HudPcmBenchState hud_pcm_bench;
#ifdef AVSP_PCM_PROMOTION_BENCH
static AvspPortV2PcmRuntime pcm_port_v2;
#endif
#endif

#ifdef AVSP_CDDA_RESIDENCY_SALVAGE_BENCH
typedef struct
{
    unsigned long head_canary;
#ifdef AVSP_CDDA_RESIDENCY_PROMOTION_BENCH
    unsigned char bytes[AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES];
#else
    unsigned char bytes[AVSP_CDDA_RESIDENCY_FIXTURE_BYTES];
#endif
    unsigned long tail_canary;
} CddaResidencyReadBuffer;

#ifdef AVSP_CDDA_RESIDENCY_PROMOTION_BENCH
static AvspPortV2CddaRuntime cdda_port_v2;
static AvspPortV2ResidencyRuntime residency_port_v2;
static int cdda_residency_frame;
#else
static AvspCddaResidencyRuntime cdda_residency_runtime;
#endif
static CddaResidencyReadBuffer cdda_residency_read_buffer;
#endif

#ifdef AVSP_PLAYABLE_SLICE
#define AVSP_SLICE_CDDA_STOP_FRAME 3000
static AvspPortV2SliceRuntime playable_slice_runtime;
static AvspPortV2SliceFrame playable_slice_frame;
volatile int avsp_diag_slice_interface_version;
volatile int avsp_diag_slice_frame;
volatile int avsp_diag_slice_ready;
volatile int avsp_diag_slice_actor_count;
volatile int avsp_diag_slice_render_commands;
volatile int avsp_diag_slice_combat_events;
volatile int avsp_diag_slice_enemy_health;
volatile int avsp_diag_slice_hit_count;
volatile int avsp_diag_slice_ko_count;
volatile int avsp_diag_slice_stage_submissions;
volatile int avsp_diag_slice_hud_render_count;
volatile int avsp_diag_slice_pcm_events;
volatile int avsp_diag_slice_pcm_active;
volatile int avsp_diag_slice_cdda_active;
volatile int avsp_diag_slice_cdda_transitions;
volatile int avsp_diag_slice_late_reads;
volatile int avsp_diag_slice_asset_failures;
volatile int avsp_diag_slice_fallback_used;
volatile int avsp_diag_slice_canaries_ok;
volatile int avsp_diag_slice_stability_frames;
volatile int avsp_diag_slice_physical_saturn;
volatile int avsp_diag_slice_init_stage;
volatile int avsp_diag_slice_frame_stage;
volatile int avsp_diag_slice_review_phase;
volatile int avsp_diag_slice_player_world_x;
volatile int avsp_diag_slice_enemy_world_x;
volatile int avsp_diag_slice_camera_world_x;
volatile int avsp_diag_slice_player_screen_x;
volatile int avsp_diag_slice_enemy_screen_x;
volatile int avsp_diag_slice_aperture_origin_x;
volatile int avsp_diag_slice_player_delta_world_x;
volatile int avsp_diag_slice_enemy_delta_world_x;
volatile int avsp_diag_slice_delta_camera_world_x;
volatile int avsp_diag_slice_player_delta_screen_x;
volatile int avsp_diag_slice_enemy_delta_screen_x;
volatile int avsp_diag_slice_layer0_scroll_x;
volatile int avsp_diag_slice_layer1_scroll_x;
volatile int avsp_diag_slice_player_action;
volatile int avsp_diag_slice_player_action_frame;
volatile int avsp_diag_slice_player_attack_active;
volatile int avsp_diag_slice_player_presentation_active;
volatile int avsp_diag_slice_source_sample;
volatile int avsp_diag_slice_source_event_index;
volatile int avsp_diag_slice_attack_sequence_step;
volatile int avsp_diag_slice_attack_selector;
volatile int avsp_diag_slice_player_source_action;
volatile int avsp_diag_slice_player_source_substate;
volatile int avsp_diag_slice_player_source_pose;
volatile int avsp_diag_slice_player_source_pivot_x;
volatile int avsp_diag_slice_player_source_pivot_y;
volatile int avsp_diag_slice_player_source_height;
volatile int avsp_diag_slice_enemy_action;
volatile int avsp_diag_slice_enemy_action_frame;
volatile int avsp_diag_slice_enemy_source_action;
volatile int avsp_diag_slice_enemy_source_substate;
volatile int avsp_diag_slice_collision_result;
volatile int avsp_diag_slice_attacker_id;
volatile int avsp_diag_slice_defender_id;
volatile int avsp_diag_slice_health_before;
volatile int avsp_diag_slice_health_after;
volatile int avsp_diag_slice_semantic_hit;
volatile int avsp_diag_slice_semantic_ko;
volatile int avsp_diag_slice_player_actor_id;
volatile int avsp_diag_slice_player_role;
volatile int avsp_diag_slice_player_class_id;
volatile int avsp_diag_slice_player_archetype_id;
volatile int avsp_diag_slice_player_asset_set_id;
volatile int avsp_diag_slice_player_animation_set_id;
volatile int avsp_diag_slice_player_palette_bank;
volatile int avsp_diag_slice_player_animation_record;
volatile int avsp_diag_slice_player_object_identity;
volatile int avsp_diag_slice_player_tile_identity;
volatile int avsp_diag_slice_enemy_actor_id;
volatile int avsp_diag_slice_enemy_role;
volatile int avsp_diag_slice_enemy_class_id;
volatile int avsp_diag_slice_enemy_archetype_id;
volatile int avsp_diag_slice_enemy_asset_set_id;
volatile int avsp_diag_slice_enemy_animation_set_id;
volatile int avsp_diag_slice_enemy_palette_bank;
volatile int avsp_diag_slice_enemy_animation_record;
volatile int avsp_diag_slice_enemy_object_count;
volatile int avsp_diag_slice_enemy_object_identity;
volatile int avsp_diag_slice_enemy_tile_identity;
#endif

#ifdef AVSP_LIVE_ENCOUNTER
#define AVSP_LIVE_DIAG_SAMPLES 512
typedef struct
{
    int frame;
    int input_mask;
    int player_x;
    int player_lane;
    int player_health;
    int player_state;
    int player_selector;
    int player_attack_active;
    int player_facing;
    int player_animation_record;
    int player_assembly;
    int player_screen_y;
    int alien_x;
    int alien_lane;
    int alien_health;
    int alien_state;
    int alien_inner;
    int alien_action;
    int alien_facing;
    int alien_animation_record;
    int alien_assembly;
    int alien_screen_y;
    int alien_rng;
    int player_contact;
    int alien_contact;
    int player_damage;
    int alien_damage;
    int attack_miss;
    int encounter_state;
    int route_unlocked;
    int continued_after_unlock;
    int camera_world_x;
    int failures;
} LiveEncounterDiagSample;
static AvspLiveEncounterRuntime live_encounter_runtime;
static AvspLiveEncounterFrame live_encounter_frame;
volatile LiveEncounterDiagSample avsp_diag_live_samples[
    AVSP_LIVE_DIAG_SAMPLES];
volatile int avsp_diag_live_sample_count;
volatile int avsp_diag_live_interface_version;
volatile int avsp_diag_live_contract_flags;
volatile int avsp_diag_live_frame_stage;
volatile int avsp_diag_live_internal_failures;
volatile int avsp_diag_live_pcm_retriggers;
volatile int avsp_diag_live_frame;
volatile int avsp_diag_live_input_mask;
volatile int avsp_diag_live_player_x;
volatile int avsp_diag_live_player_lane;
volatile int avsp_diag_live_player_health;
volatile int avsp_diag_live_player_state;
volatile int avsp_diag_live_player_selector;
volatile int avsp_diag_live_player_facing;
volatile int avsp_diag_live_player_animation_record;
volatile int avsp_diag_live_player_assembly;
volatile int avsp_diag_live_player_screen_y;
volatile int avsp_diag_live_alien_x;
volatile int avsp_diag_live_alien_lane;
volatile int avsp_diag_live_alien_health;
volatile int avsp_diag_live_alien_state;
volatile int avsp_diag_live_alien_inner;
volatile int avsp_diag_live_alien_action;
volatile int avsp_diag_live_alien_facing;
volatile int avsp_diag_live_alien_animation_record;
volatile int avsp_diag_live_alien_assembly;
volatile int avsp_diag_live_alien_screen_y;
volatile int avsp_diag_live_alien_rng;
volatile int avsp_diag_live_player_contact;
volatile int avsp_diag_live_alien_contact;
volatile int avsp_diag_live_player_damage;
volatile int avsp_diag_live_alien_damage;
volatile int avsp_diag_live_attack_miss;
volatile int avsp_diag_live_hit_events;
volatile int avsp_diag_live_ko_events;
volatile int avsp_diag_live_encounter_state;
volatile int avsp_diag_live_route_unlocked;
volatile int avsp_diag_live_continued_after_unlock;
volatile int avsp_diag_live_camera_world_x;
volatile int avsp_diag_live_player_screen_x;
volatile int avsp_diag_live_alien_screen_x;
volatile int avsp_diag_live_failures;
volatile int avsp_diag_live_fallback_count;
volatile int avsp_diag_live_canaries_ok;
volatile int avsp_diag_live_physical_saturn;
#ifdef AVSP_LIVE_ENCOUNTER_AUTOTEST
static int live_autotest_phase;
static int live_autotest_release;
#endif
#endif

#ifdef AVSP_ENEMY_SALVAGE_BENCH
#define ENEMY_BENCH_CANARY_HEAD 0x454E4D48UL
#define ENEMY_BENCH_CANARY_TAIL 0x454E4D54UL
#define ENEMY_BENCH_PHASE_FRAMES 120
typedef struct
{
    unsigned long head_canary;
    int frame;
    int negative_rejections;
    unsigned long tail_canary;
} EnemyBenchState;
static EnemyBenchState enemy_bench;
#ifdef AVSP_ENEMY_PROMOTION_BENCH
#ifndef AVSP_PLAYER_ENEMY_INTEGRATION
static AvspPortV2EnemyRuntime enemy_port_v2;
#endif
#endif
#endif

/* Stable headless readback surface. These are intentionally global and
 * volatile so stock emulator debugger memory reads can verify the focused
 * frontend profile without relying on a GUI screenshot. */
volatile int avsp_diag_runtime_ready;
volatile int avsp_diag_encounter_state;
volatile int avsp_diag_world_frame;
volatile int avsp_diag_selected_character;
volatile int avsp_diag_selection_cursor;
volatile int avsp_diag_encounter_timer;
volatile int avsp_diag_background_bitmap;
volatile int avsp_diag_frontend_late_reads;
volatile int avsp_diag_frontend_missing_assets;
volatile int avsp_diag_frontend_rle_errors;
volatile int avsp_diag_frontend_palette_errors;
volatile int avsp_diag_frontend_palette_boundary_writes;
volatile int avsp_diag_frontend_commands;
#ifdef AVSP_CAMERA_STAGE_SALVAGE_BENCH
volatile int avsp_diag_stage_interface_version;
volatile int avsp_diag_stage_layer_count;
volatile int avsp_diag_stage_source_width;
volatile int avsp_diag_stage_output_width;
volatile int avsp_diag_stage_priority_lock_ok;
volatile int avsp_diag_stage_palette_cycle_state;
volatile int avsp_diag_stage_scroll_steps;
volatile int avsp_diag_stage_asset_failures;
volatile int avsp_diag_stage_disc_late_reads;
#ifdef AVSP_CAMERA_STAGE_PROMOTION_BENCH
volatile int avsp_diag_stage_row_scroll_status;
volatile int avsp_diag_stage_render_submissions;
volatile int avsp_diag_stage_port_lock_ok;
#endif
#endif
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
volatile int avsp_diag_hud_pcm_interface_version;
volatile int avsp_diag_hud_pcm_frame;
volatile int avsp_diag_hud_pcm_phase;
volatile int avsp_diag_hud_state;
volatile int avsp_diag_hud_health;
volatile int avsp_diag_hud_energy;
volatile int avsp_diag_hud_health_fill;
volatile int avsp_diag_hud_energy_fill;
volatile int avsp_diag_hud_render_count;
volatile int avsp_diag_hud_p2_state;
volatile int avsp_diag_hud_p2_health;
volatile int avsp_diag_hud_p2_energy;
volatile int avsp_diag_hud_p2_health_fill;
volatile int avsp_diag_hud_p2_energy_fill;
volatile int avsp_diag_hud_p2_render_count;
volatile int avsp_diag_hud_p2_binding_ok;
volatile int avsp_diag_hud_asset_failures;
volatile int avsp_diag_pcm_audio_failures;
volatile int avsp_diag_pcm_event_count;
volatile int avsp_diag_pcm_event_frame;
volatile int avsp_diag_pcm_start_frame;
volatile int avsp_diag_pcm_end_frame;
volatile int avsp_diag_pcm_active;
volatile int avsp_diag_pcm_channel_observed;
volatile int avsp_diag_pcm_underruns;
volatile int avsp_diag_hud_pcm_negative_rejections;
volatile int avsp_diag_hud_pcm_canary_ok;
volatile int avsp_diag_hud_pcm_disc_late_reads;
volatile int avsp_diag_hud_palette_binding_ok;
volatile int avsp_diag_hud_palette_yellow;
volatile int avsp_diag_hud_palette_red;
volatile int avsp_diag_hud_palette_energy;
volatile int avsp_diag_hud_palette_empty;
#ifdef AVSP_HUD_PROMOTION_BENCH
volatile int avsp_diag_hud_production_interface_version;
volatile int avsp_diag_hud_port_lock_ok;
volatile int avsp_diag_hud_submit_count;
#endif
#ifdef AVSP_PCM_PROMOTION_BENCH
volatile int avsp_diag_pcm_production_interface_version;
volatile int avsp_diag_pcm_port_lock_ok;
volatile int avsp_diag_pcm_allocation_ok;
volatile int avsp_diag_pcm_submit_count;
volatile int avsp_diag_pcm_semantic_active;
#endif
#endif
#ifdef AVSP_CDDA_RESIDENCY_SALVAGE_BENCH
volatile int avsp_diag_cdda_interface_version;
volatile int avsp_diag_cdda_frame;
volatile int avsp_diag_cdda_action;
volatile int avsp_diag_cdda_ownership;
volatile int avsp_diag_cdda_track;
volatile int avsp_diag_cdda_source_frame;
volatile int avsp_diag_cdda_track_events;
volatile int avsp_diag_cdda_ownership_transitions;
volatile int avsp_diag_cdda_window_open;
volatile int avsp_diag_cdda_legal_windows;
volatile int avsp_diag_cdda_legal_reads;
volatile int avsp_diag_cdda_late_reads;
volatile int avsp_diag_cdda_refused_windows;
volatile int avsp_diag_cdda_negative_rejections;
volatile int avsp_diag_cdda_failures;
volatile int avsp_diag_cdda_asset_failures;
volatile int avsp_diag_cdda_canary_ok;
volatile int avsp_diag_cdda_work_ram_high_water;
volatile int avsp_diag_cdda_cart_high_water;
volatile int avsp_diag_cdda_vdp1_high_water;
volatile int avsp_diag_cdda_vdp2_high_water;
volatile int avsp_diag_cdda_cram_high_water;
volatile int avsp_diag_cdda_scsp_high_water;
#ifdef AVSP_CDDA_RESIDENCY_PROMOTION_BENCH
volatile int avsp_diag_cdda_production_interface_version;
volatile int avsp_diag_residency_production_interface_version;
volatile int avsp_diag_cdda_port_lock_ok;
volatile int avsp_diag_cdda_submit_count;
volatile int avsp_diag_residency_submit_count;
volatile int avsp_diag_cdda_fallback_used;
#endif
#endif
#ifdef AVSP_PLAYER_SALVAGE_BENCH
volatile int avsp_diag_player_frame;
volatile int avsp_diag_player_input_mask;
volatile int avsp_diag_player_input_edges;
volatile int avsp_diag_player_x;
volatile int avsp_diag_player_lane;
volatile int avsp_diag_player_facing;
volatile int avsp_diag_player_pose;
volatile int avsp_diag_player_pivot_y;
volatile int avsp_diag_player_cel_left;
volatile int avsp_diag_player_cel_top;
volatile int avsp_diag_player_cel_right;
volatile int avsp_diag_player_cel_bottom;
volatile int avsp_diag_player_render_count;
volatile int avsp_diag_player_canary_ok;
volatile int avsp_diag_player_asset_failures;
volatile int avsp_diag_player_disc_late_reads;
#ifdef AVSP_PLAYER_PROMOTION_BENCH
volatile int avsp_diag_player_interface_version;
volatile int avsp_diag_player_approval_lock_ok;
volatile int avsp_diag_player_loader_adapter_ok;
#endif
#endif
#ifdef AVSP_ENEMY_SALVAGE_BENCH
volatile int avsp_diag_enemy_interface_version;
volatile int avsp_diag_enemy_frame;
volatile int avsp_diag_enemy_phase;
volatile int avsp_diag_enemy_class_id;
volatile int avsp_diag_enemy_x;
volatile int avsp_diag_enemy_lane;
volatile int avsp_diag_enemy_facing;
volatile int avsp_diag_enemy_anim_record;
volatile int avsp_diag_enemy_assembly;
volatile int avsp_diag_enemy_object_count;
volatile int avsp_diag_enemy_render_count;
volatile int avsp_diag_enemy_command_code;
volatile int avsp_diag_enemy_palette_bank;
volatile int avsp_diag_enemy_asset_failures;
volatile int avsp_diag_enemy_negative_rejections;
volatile int avsp_diag_enemy_canary_ok;
volatile int avsp_diag_enemy_disc_late_reads;
volatile int avsp_diag_enemy_tile_bank_misses;
volatile int avsp_diag_enemy_tile_rank_misses;
#ifdef AVSP_ENEMY_PROMOTION_BENCH
volatile int avsp_diag_enemy_approval_lock_ok;
volatile int avsp_diag_enemy_loader_adapter_ok;
#endif
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
volatile int avsp_diag_integration_interface_version;
volatile int avsp_diag_integration_approval_locks_ok;
volatile int avsp_diag_integration_loader_order_ok;
volatile int avsp_diag_integration_actor_count;
volatile int avsp_diag_integration_render_order_ok;
volatile int avsp_diag_integration_render_command_count;
volatile int avsp_diag_integration_canaries_ok;
volatile int avsp_diag_integration_asset_failures;
volatile int avsp_diag_integration_disc_late_reads;
/* The MCP backend watches a 16-byte block for memory breakpoints. Keep the
 * integration frame marker in its own aligned block so adjacent diagnostic
 * writes cannot satisfy a value-filtered frame breakpoint. */
volatile int avsp_diag_integration_frame[4] __attribute__((aligned(16)));
typedef struct
{
    int source_frame;
    int player_x;
    int player_lane;
    int player_facing;
    int player_pose;
    int player_cel_left;
    int player_cel_top;
    int player_cel_right;
    int player_cel_bottom;
    int player_render_count;
    int player_canary_ok;
    int player_asset_failures;
    int player_disc_late_reads;
    int player_interface_version;
    int player_approval_lock_ok;
    int player_loader_adapter_ok;
    int enemy_phase;
    int enemy_class_id;
    int enemy_x;
    int enemy_lane;
    int enemy_facing;
    int enemy_anim_record;
    int enemy_assembly;
    int enemy_object_count;
    int enemy_render_count;
    int enemy_palette_bank;
    int enemy_canary_ok;
    int enemy_asset_failures;
    int enemy_disc_late_reads;
    int enemy_tile_bank_misses;
    int enemy_tile_rank_misses;
    int enemy_interface_version;
    int enemy_negative_rejections;
    int enemy_approval_lock_ok;
    int enemy_loader_adapter_ok;
    int integration_interface_version;
    int integration_approval_locks_ok;
    int integration_loader_order_ok;
    int integration_actor_count;
    int integration_render_order_ok;
    int integration_render_command_count;
    int integration_canaries_ok;
    int integration_asset_failures;
    int integration_disc_late_reads;
} AvspIntegrationDiagnosticSample;
volatile AvspIntegrationDiagnosticSample avsp_diag_integration_samples[3];
volatile int avsp_diag_integration_sample_count;
#endif
#endif
#ifdef AVSP_COLLISION_SALVAGE_BENCH
#define COLLISION_BENCH_CANARY_HEAD 0x434F4C48UL
#define COLLISION_BENCH_CANARY_TAIL 0x434F4C54UL
typedef struct
{
    unsigned long head_canary;
    int frame;
    int failures;
    int negative_rejections;
    unsigned long tail_canary;
} AvspCollisionDiagnosticState;
static AvspCollisionDiagnosticState collision_bench_state;
volatile int avsp_diag_collision_interface_version;
volatile int avsp_diag_collision_frame;
volatile int avsp_diag_collision_case;
volatile int avsp_diag_collision_overlap;
volatile int avsp_diag_collision_expected_overlap;
volatile int avsp_diag_collision_guarded;
volatile int avsp_diag_collision_expected_guarded;
volatile int avsp_diag_collision_hit_value;
volatile int avsp_diag_collision_table_set_ok;
volatile int avsp_diag_collision_negative_rejections;
volatile int avsp_diag_collision_damage_writes;
volatile int avsp_diag_collision_failures;
volatile int avsp_diag_collision_canary_ok;
volatile AvspCollisionBenchResult
    avsp_diag_collision_samples[AVSP_COLLISION_CASE_COUNT];
volatile int avsp_diag_collision_sample_count;
#endif
#if defined(AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH) || \
    defined(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH)
#define PW_ACTION_CANARY_HEAD 0x50574148UL
#define PW_ACTION_CANARY_TAIL 0x50574154UL
#define PW_ACTION_CAPTURE_FRAMES 384
typedef struct
{
    int frame;
    int input_mask;
    int x;
    int lane;
    int height;
    int health;
    int facing;
    int state;
    int phase;
    int selector;
    int action_elapsed;
    int source_action;
    int source_substate;
    int attack_active;
    int box_x_center;
    int box_x_half;
    int box_y_center;
    int box_y_half;
    int box_z_center;
    int box_z_half;
    int hit_value;
} AvspPwDiagnosticSample;
typedef struct
{
    unsigned long head_canary;
    AvspPwRuntime runtime;
    unsigned long tail_canary;
} AvspPwDiagnosticState;
static AvspPwDiagnosticState pw_action_state;
volatile AvspPwDiagnosticSample
    avsp_diag_pw_action_samples[PW_ACTION_CAPTURE_FRAMES];
volatile int avsp_diag_pw_action_sample_count;
volatile int avsp_diag_pw_action_interface_version;
volatile int avsp_diag_pw_action_frame;
volatile int avsp_diag_pw_action_failures;
volatile int avsp_diag_pw_action_canary_ok;
volatile int avsp_diag_pw_action_accepted_edges;
volatile int avsp_diag_pw_action_rejected_edges;
volatile int avsp_diag_pw_action_contact_reports;
volatile int avsp_diag_pw_action_negative_rejections;
#endif
#if defined(AVSP_STREET_ALIEN_AI_SALVAGE_BENCH) || \
    defined(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH)
#define ALIEN_AI_CANARY_HEAD 0x41494148UL
#define ALIEN_AI_CANARY_TAIL 0x41494154UL
#define ALIEN_AI_CAPTURE_FRAMES 576
typedef struct
{
    int frame;
    int target_active;
    int target_x;
    int target_lane;
    int state;
    int inner_state;
    int target_id;
    int x;
    int lane;
    int health;
    int facing;
    int approach_elapsed;
    int attack_elapsed;
    int attack_timer;
    int rng_seed;
    int rng_cursor;
    int contact;
    int contact_damage;
    int removed;
} AvspAlienAiDiagnosticSample;
typedef struct
{
    unsigned long head_canary;
    AvspAlienRuntime runtime;
    unsigned long tail_canary;
} AvspAlienAiDiagnosticState;
static AvspAlienAiDiagnosticState alien_ai_state;
volatile AvspAlienAiDiagnosticSample
    avsp_diag_alien_ai_samples[ALIEN_AI_CAPTURE_FRAMES];
volatile int avsp_diag_alien_ai_sample_count;
volatile int avsp_diag_alien_ai_interface_version;
volatile int avsp_diag_alien_ai_frame;
volatile int avsp_diag_alien_ai_failures;
volatile int avsp_diag_alien_ai_canary_ok;
volatile int avsp_diag_alien_ai_negative_rejections;
volatile int avsp_diag_alien_ai_contacts;
volatile int avsp_diag_alien_ai_damage_events;
volatile int avsp_diag_alien_ai_scheduler_updates;
volatile int avsp_diag_alien_ai_target_selections;
#endif
#ifdef AVSP_FRONTEND_SHOT_TEST
/* Visual-verification profile. The frontend surfaces this pass must compare
 * are short-lived - the ROM's cursor intro is three source frames - so a
 * wall-clock screenshot cannot land on them. Instead the route stops the
 * world at a listed (encounter state, encounter timer) point while rendering
 * continues, so the VDP1 command table and colour RAM can be read at an
 * exact frame. Holds are visited in listed order and never re-armed. */
#define AVSP_SHOT_HOLD_TICKS 300
typedef struct
{
    int state;
    int timer;
} AvspShotHold;
static const AvspShotHold avsp_shot_holds[] = {
    { CAP_ENCOUNTER_MAIN_MENU,        60 },  /* settled title             */
    { CAP_ENCOUNTER_START_TRANSITION,  1 },  /* mask plate, first frame   */
    { CAP_ENCOUNTER_START_TRANSITION, 10 },  /* mask bars, intermediate   */
    { CAP_ENCOUNTER_START_TRANSITION, 20 },  /* mask bars, intermediate   */
    { CAP_ENCOUNTER_START_TRANSITION, 25 },  /* mask bars, last drawn     */
    { CAP_ENCOUNTER_START_TRANSITION, 27 },  /* cursor intro cel 0        */
    { CAP_ENCOUNTER_START_TRANSITION, 28 },  /* cursor intro cel 1        */
    { CAP_ENCOUNTER_START_TRANSITION, 29 },  /* cursor intro cel 2        */
    { CAP_ENCOUNTER_CHARACTER_SELECT,  1 },  /* cursor cycle phase 1      */
    { CAP_ENCOUNTER_CHARACTER_SELECT,  2 },  /* cursor cycle phase 2      */
    { CAP_ENCOUNTER_CHARACTER_SELECT,  3 },  /* cursor cycle phase 3      */
    { CAP_ENCOUNTER_CHARACTER_SELECT, 30 },  /* settled cursor 0 Warrior  */
    { CAP_ENCOUNTER_CHARACTER_SELECT, 60 },  /* settled cursor 1 Schaefer */
    { CAP_ENCOUNTER_CHARACTER_SELECT,100 },  /* settled cursor 2 Hunter   */
    { CAP_ENCOUNTER_CHARACTER_SELECT,140 },  /* settled cursor 3 Linn     */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM, 1 },  /* marker blink visible      */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,10 },  /* marker blink visible      */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,20 },  /* marker blink blank        */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,40 },  /* markers retired           */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,90 },  /* shutter moving            */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,100 }, /* shutter moving            */
    { CAP_ENCOUNTER_CHARACTER_CONFIRM,110 }, /* shutter closed            */
    { CAP_ENCOUNTER_ROUND_TITLE,      20 },  /* title text over black     */
    { CAP_ENCOUNTER_ROUND_TITLE,      60 },  /* title text over street    */
    { CAP_ENCOUNTER_ROUND_TITLE,     100 }   /* street after text clear   */
};
#define AVSP_SHOT_HOLD_COUNT ((int)(sizeof(avsp_shot_holds) / sizeof(avsp_shot_holds[0])))
static int avsp_shot_hold_index;
static int avsp_shot_hold_ticks;
/* cap_update_encounter() does not advance encounter_timer in every state,
 * so the shot route counts frames spent in the current state itself. The
 * counter only advances on frames the world actually stepped, which is what
 * makes a hold frame-exact. */
static int avsp_shot_state = -1;
static int avsp_shot_state_frames;
volatile int avsp_diag_hold_index = -1;
volatile int avsp_diag_hold_active;
volatile int avsp_diag_hold_timer = -1;
static int avsp_shot_should_hold(void)
{
    if (avsp_shot_hold_index >= AVSP_SHOT_HOLD_COUNT) return 0;
    if ((int)world.encounter_state !=
            avsp_shot_holds[avsp_shot_hold_index].state ||
        avsp_shot_state_frames !=
            avsp_shot_holds[avsp_shot_hold_index].timer)
        return 0;
    avsp_diag_hold_index = avsp_shot_hold_index;
    avsp_diag_hold_timer = avsp_shot_state_frames;
    avsp_diag_hold_active = 1;
    if (++avsp_shot_hold_ticks < AVSP_SHOT_HOLD_TICKS) return 1;
    avsp_shot_hold_ticks = 0;
    avsp_diag_hold_active = 0;
    ++avsp_shot_hold_index;
    return 0;
}
#endif

#ifdef AVSP_VISUAL_TEST
static int visual_action_index;
static int visual_walk_frames;
static int visual_enemy_action_index;
static int visual_enemy_frame;
#endif

/* Cartridge-safe file read. jo_fs_read_file_in_dir's whole-file GFS_Load
 * path cannot fill a buffer the allocator places in cartridge DRAM (SBL's
 * default transfer is SCU DMA, and SCU DMA cannot write the A-bus), and
 * with the 4 MB cartridge carrying most of the working set almost every
 * large allocation lands there. Following the proven period pattern
 * (BrooklynBangout2D's asset staging), every read streams through a fixed
 * work-RAM staging buffer in 32-sector bursts and is copied out with the
 * CPU, which every destination accepts. jo_fs_read_next_bytes is NOT used:
 * it refills with a single-sector GFS_Fread regardless of the configured
 * buffer size, so enlarging jo's stream buffer serves garbage.
 * All disc reads in this file go through here. */
/* 31 sectors, not 32: the encounter profile's BSS crossed the
 * 0x060C0000 user work-RAM limit by 0x5a0 bytes after the RP3 carve
 * rework, and one sector off this burst buffer reclaims 2 KiB without
 * changing behavior (the read loop accepts any burst size). */
#define AVSP_FS_STAGING_SECTORS 31
#define AVSP_FS_SECTOR_BYTES 2048
#define AVSP_FS_STAGING_BYTES (AVSP_FS_STAGING_SECTORS * AVSP_FS_SECTOR_BYTES)
static unsigned char avsp_fs_staging[AVSP_FS_STAGING_BYTES];
/* Boot-bringup diagnostic: which stage of the cartridge-safe reader
 * failed last. Volatile so the release optimizer keeps these
 * debugger-read fields. */
/* RP5: every data-track read asks this guard first; CDDA ownership and
 * measured phase-boundary windows are the only inputs. Non-static so the
 * debug rig reads the counters by symbol. */
AvspDiscGuard avsp_disc_guard_state;
static const char *volatile avsp_fs_last_error;
static volatile int avsp_fs_last_read;
volatile const char *avsp_diag_fs_name;
volatile const char *avsp_diag_fs_dir;
volatile int avsp_diag_fs_expected;
volatile int avsp_diag_fs_offset;
volatile int avsp_diag_fs_reads;

/* Stream one file into dest (any bus). Returns bytes read, or -1. */
static int avsp_fs_read_into(const char *const filename,
                             const char *const sub_dir,
                             unsigned char *dest, const int max_bytes)
{
    Sint32 fid;
    GfsHn gfs;
    Sint32 sctsize;
    Sint32 nsct;
    Sint32 lastsize;
    int fsize;
    int offset = 0;

    if (!avsp_disc_guard_check(&avsp_disc_guard_state))
    {
        /* CDDA owns the drive and no measured window is open: reject the
           read loudly instead of seeking the data track mid-music. */
        avsp_fs_last_error = "FS CDDA LOCK";
        return -1;
    }
    avsp_diag_fs_name = filename;
    avsp_diag_fs_dir = sub_dir;
    avsp_diag_fs_expected = 0;
    avsp_diag_fs_offset = 0;
    jo_fs_cd(sub_dir);
    fid = GFS_NameToId((Sint8 *)filename);
    if (fid < 0)
    {
        jo_fs_cd(JO_PARENT_DIR);
        avsp_fs_last_error = "FS NAME";
        return -1;
    }
    gfs = GFS_Open(fid);
    if (gfs == JO_NULL)
    {
        jo_fs_cd(JO_PARENT_DIR);
        avsp_fs_last_error = "FS OPEN";
        return -1;
    }
    GFS_GetFileSize(gfs, &sctsize, &nsct, &lastsize);
    fsize = sctsize * (nsct - 1) + lastsize;
    avsp_diag_fs_expected = fsize;
    if (fsize <= 0 || fsize > max_bytes)
    {
        GFS_Close(gfs);
        jo_fs_cd(JO_PARENT_DIR);
        avsp_fs_last_error = "FS SIZE";
        avsp_fs_last_read = fsize;
        return -1;
    }
    while (offset < fsize)
    {
        int chunk;
        avsp_diag_fs_offset = offset;
        ++avsp_diag_fs_reads;
        Sint32 got = GFS_Fread(gfs, AVSP_FS_STAGING_SECTORS,
                               avsp_fs_staging, AVSP_FS_STAGING_BYTES);
        if (got <= 0)
        {
            GFS_Close(gfs);
            jo_fs_cd(JO_PARENT_DIR);
            avsp_fs_last_error = "FS READ";
            avsp_fs_last_read = offset;
            return -1;
        }
        chunk = (int)got;
        /* The final burst is sector-padded past the true file size. */
        if (offset + chunk > fsize) chunk = fsize - offset;
        memcpy(dest + offset, avsp_fs_staging, (unsigned int)chunk);
        offset += chunk;
    }
    GFS_Close(gfs);
    jo_fs_cd(JO_PARENT_DIR);
    return fsize;
}

static char *avsp_fs_read_file_in_dir(const char *const filename,
                                      const char *const sub_dir, int *len)
{
    jo_file probe;
    int opened;
    int read_bytes;
    char *dest;

    /* Size the allocation with a jo probe, then stream for real. */
    jo_fs_cd(sub_dir);
    opened = jo_fs_open(&probe, filename);
    if (opened) jo_fs_close(&probe);
    jo_fs_cd(JO_PARENT_DIR);
    if (!opened || probe.size <= 0)
    {
        avsp_fs_last_error = "FS PROBE";
        return JO_NULL;
    }
    dest = (char *)jo_malloc_with_behaviour((unsigned int)probe.size,
                                            JO_MALLOC_TRY_REUSE_BLOCK);
    if (dest == JO_NULL)
    {
        avsp_fs_last_error = "FS ALLOC";
        return JO_NULL;
    }
    read_bytes = avsp_fs_read_into(filename, sub_dir,
                                   (unsigned char *)dest, probe.size);
    if (read_bytes != probe.size)
    {
        jo_free(dest);
        return JO_NULL;
    }
    if (len != JO_NULL) *len = read_bytes;
    return dest;
}

static int load_cel_asset(CelAsset *asset)
{
    int length = 0;
    asset->image.width = asset->width;
    asset->image.height = asset->height;
    asset->image.data = (unsigned char *)avsp_fs_read_file_in_dir(asset->filename, "SPR4", &length);
    if (asset->image.data == JO_NULL || length != asset->expected_bytes)
    {
        failed_asset = asset->filename;
        return 0;
    }
    return 1;
}

static int load_all_cels(void)
{
    int index;
    for (index = 0; index < CEL_COUNT; ++index)
        if (!load_cel_asset(&cel_assets[index])) return 0;
    return 1;
}

static int load_pcm_audio(jo_sound *sound, const char *filename,
                          const char *directory, const int expected_bytes,
                          const int sample_rate)
{
    int length = 0;
    sound->data = avsp_fs_read_file_in_dir(filename, directory, &length);
    if (sound->data == JO_NULL || length != expected_bytes)
    {
        failed_asset = filename;
        return 0;
    }
    sound->data_length = length;
    sound->mode = JoSoundStereo16Bit;
    sound->current_playing_channel = 0;
    sound->sample_rate = sample_rate;
    sound->volume = JO_MAX_AUDIO_VOLUME;
    sound->pan = 0;
    return 1;
}

static int load_action_audio(void)
{
    return load_pcm_audio(&weapon_sound, AVSP_GUN_PCM_FILE,
                          AVSP_GUN_PCM_DIRECTORY, AVSP_GUN_PCM_BYTES,
                          AVSP_GUN_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&melee_sound, AVSP_MELEE_PCM_FILE,
                          AVSP_MELEE_PCM_DIRECTORY, AVSP_MELEE_PCM_BYTES,
                          AVSP_MELEE_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&contact_sound, AVSP_CONTACT_PCM_FILE,
                          AVSP_CONTACT_PCM_DIRECTORY,
                          AVSP_CONTACT_PCM_BYTES,
                          AVSP_CONTACT_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&ko_contact_sound, AVSP_KO_CONTACT_PCM_FILE,
                          AVSP_KO_CONTACT_PCM_DIRECTORY,
                          AVSP_KO_CONTACT_PCM_BYTES,
                          AVSP_KO_CONTACT_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&boss_intro_sound, AVSP_BOSS_INTRO_PCM_FILE,
                          AVSP_BOSS_INTRO_PCM_DIRECTORY,
                          AVSP_BOSS_INTRO_PCM_BYTES,
                          AVSP_BOSS_INTRO_PCM_SAMPLE_RATE) &&
           /* boss_clear_sound (637 KB, the largest PCM) is phase-loaded at
              the interior transition instead of boot: the 32 Mbit cartridge
              cannot hold the whole boot working set plus the Body E ROM
              tile archive at once, and by that phase the ~900 KB of
              released opening PCM leaves ample room. CDDA is not active
              there (stage music start is currently disabled; when it
              returns, the interior wipe remains a legal seek window). */
           load_pcm_audio(&door_dialogue_sound,
                          AVSP_DOOR_DIALOGUE_PCM_FILE,
                          AVSP_DOOR_DIALOGUE_PCM_DIRECTORY,
                          AVSP_DOOR_DIALOGUE_PCM_BYTES,
                          AVSP_DOOR_DIALOGUE_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&interior_transition_sound,
                          AVSP_INTERIOR_TRANSITION_PCM_FILE,
                          AVSP_INTERIOR_TRANSITION_PCM_DIRECTORY,
                          AVSP_INTERIOR_TRANSITION_PCM_BYTES,
                          AVSP_INTERIOR_TRANSITION_PCM_SAMPLE_RATE);
}

/* The four opening-overlay PCMs (title A/B, withdrawal, breach) are the
   phase-transient part of the boot working set: all four are released by the
   first wave. Jo's allocator never coalesces free neighbours and only a
   block adjacent to the zone's bump pointer rolls it back, so these MUST be
   the LAST large boot allocations - at the TOP of their zone - or their
   ~900 KB returns as unmergeable islands. The measured 2026-08-19 heap dump
   showed exactly that: with these loaded before the cel/archive sweep they
   sat at the BOTTOM of cartridge bank 1 under permanent assets, and the
   637,084-byte BOSSCLR.PCM phase load could never find more than 498,552
   contiguous bytes. Called last in the jo_main init chain; do not fold back
   into load_action_audio. */
static int load_opening_audio(void)
{
    return load_pcm_audio(&round_title_a_sound,
                          AVSP_ROUND_TITLE_A_PCM_FILE,
                          AVSP_ROUND_TITLE_A_PCM_DIRECTORY,
                          AVSP_ROUND_TITLE_A_PCM_BYTES,
                          AVSP_ROUND_TITLE_A_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&round_title_b_sound,
                          AVSP_ROUND_TITLE_B_PCM_FILE,
                          AVSP_ROUND_TITLE_B_PCM_DIRECTORY,
                          AVSP_ROUND_TITLE_B_PCM_BYTES,
                          AVSP_ROUND_TITLE_B_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&withdraw_sound, AVSP_WITHDRAW_PCM_FILE,
                          AVSP_WITHDRAW_PCM_DIRECTORY,
                          AVSP_WITHDRAW_PCM_BYTES,
                          AVSP_WITHDRAW_PCM_SAMPLE_RATE) &&
           load_pcm_audio(&breach_sound, AVSP_BREACH_PCM_FILE,
                          AVSP_BREACH_PCM_DIRECTORY,
                          AVSP_BREACH_PCM_BYTES,
                          AVSP_BREACH_PCM_SAMPLE_RATE);
}

static void release_pcm_data(jo_sound *sound)
{
    if (sound->data == JO_NULL) return;
    jo_free(sound->data);
    sound->data = JO_NULL;
    sound->data_length = 0;
}

/* Jo Engine queues SGL sound commands and flushes before, rather than after,
   slPCMOn. Explicitly commit both halves of a retrigger so a cue requested on
   the following frame cannot leave the prior start pending or see a stale
   channel state. This is required by the verified +2/+3 contact pair. */
static void play_pcm_committed(jo_sound *sound, jo_sound *previous_sound,
                               const unsigned char channel)
{
    if (previous_sound != JO_NULL && jo_audio_is_channel_playing(channel))
    {
        jo_audio_stop_sound(previous_sound);
        slSndFlush();
    }
    jo_audio_play_sound_on_channel(sound, channel);
    slSndFlush();
}

static int load_player_action_sequences(void)
{
    int layer;
    int length = 0;
    player_action_archive = (unsigned char *)avsp_fs_read_file_in_dir(
        AVSP_PLAYER_ACTION_ARCHIVE_FILE, "SPR4", &length);
    if (player_action_archive == JO_NULL ||
        length != AVSP_PLAYER_ACTION_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_PLAYER_ACTION_ARCHIVE_FILE;
        return 0;
    }
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        player_action_images[layer].width = CEL_WIDTH;
        player_action_images[layer].height = CEL_HEIGHT;
        player_action_images[layer].data =
            (unsigned char *)jo_malloc(AVSP_PLAYER_ACTION_DECODED_BYTES);
        if (player_action_images[layer].data == JO_NULL)
        {
            failed_asset = "PLAYER ACTION BUFFER";
            return 0;
        }
    }
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    length = 0;
    source_combat_player_archive =
        (unsigned char *)avsp_fs_read_file_in_dir(
            AVSP_SOURCE_COMBAT_PLAYER_ARCHIVE_FILE, "SPR4", &length);
    if (source_combat_player_archive == JO_NULL ||
        length != AVSP_SOURCE_COMBAT_PLAYER_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_SOURCE_COMBAT_PLAYER_ARCHIVE_FILE;
        return 0;
    }
    source_combat_player_image.width = CEL_WIDTH;
    source_combat_player_image.height = CEL_HEIGHT;
    source_combat_player_image.data = (unsigned char *)jo_malloc(
        AVSP_SOURCE_COMBAT_PLAYER_DECODED_BYTES);
    if (source_combat_player_image.data == JO_NULL)
    {
        failed_asset = "SOURCE COMBAT PLAYER BUFFER";
        return 0;
    }
#endif
    return 1;
}

#ifdef AVSP_COMBAT_INTEGRATION_BENCH
static int decode_source_combat_player_pose(const int pose)
{
    unsigned int source = 0;
    unsigned int target = 0;
    unsigned int source_offset;
    unsigned int source_length;
    const unsigned char *source_data;
    unsigned char *output;
    if (pose < 0 || pose >= AVSP_SOURCE_COMBAT_PLAYER_POSES) return 0;
    source_offset = avsp_source_combat_player_rle_offsets[pose];
    source_length = avsp_source_combat_player_rle_bytes[pose];
    if (source_offset + source_length >
        AVSP_SOURCE_COMBAT_PLAYER_ARCHIVE_BYTES) return 0;
    source_data = source_combat_player_archive + source_offset;
    output = source_combat_player_image.data;
    while (source + 1 < source_length)
    {
        unsigned int count = source_data[source++];
        unsigned char value = source_data[source++];
        if (count == 0 || target + count >
            AVSP_SOURCE_COMBAT_PLAYER_DECODED_BYTES) return 0;
        memset(output + target, value, count);
        target += count;
    }
    return source == source_length &&
        target == AVSP_SOURCE_COMBAT_PLAYER_DECODED_BYTES;
}
#endif

static int decode_player_action_pose(const int pose)
{
    int layer;
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        unsigned int source = 0;
        unsigned int target = 0;
        const unsigned int source_offset =
            avsp_player_action_rle_offsets[pose][layer];
        const unsigned int source_length =
            avsp_player_action_rle_bytes[pose][layer];
        const unsigned char *source_data;
        unsigned char *output = player_action_images[layer].data;
        if (source_offset + source_length > AVSP_PLAYER_ACTION_ARCHIVE_BYTES)
        {
            failed_asset = "PLAYER ACTION INDEX";
            return 0;
        }
        source_data = player_action_archive + source_offset;
        while (source + 1 < source_length)
        {
            unsigned int count = source_data[source++];
            unsigned char value = source_data[source++];
            if (count == 0 || target + count > AVSP_PLAYER_ACTION_DECODED_BYTES)
            {
                failed_asset = "PLAYER ACTION RLE";
                return 0;
            }
            memset(output + target, value, count);
            target += count;
        }
        if (source != source_length ||
            target != AVSP_PLAYER_ACTION_DECODED_BYTES)
        {
            failed_asset = "PLAYER ACTION SIZE";
            return 0;
        }
    }
    return 1;
}

static int load_enemy_action_archive(void)
{
    int length = 0;
    enemy_action_archive = (unsigned char *)avsp_fs_read_file_in_dir(
        AVSP_ENEMY_ARCHIVE_FILE, "SPR4", &length);
    if (enemy_action_archive == JO_NULL ||
        length != AVSP_ENEMY_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_ENEMY_ARCHIVE_FILE;
        return 0;
    }
    return 1;
}

static int allocate_enemy_action_buffer(void)
{
    int slot;
    const unsigned int total_bytes =
        CAP_MAX_ENEMIES * AVSP_ENEMY_DECODED_BYTES;

    if (enemy_action_buffer != JO_NULL) return 1;
    /* One contiguous pool can reuse the completed 396 KiB withdrawal PCM
       block. Jo's allocator does not split a reused free block, so eight
       individual allocations would strand most of that phase-overlay RAM. */
    enemy_action_buffer = (unsigned char *)jo_malloc_with_behaviour(
        total_bytes, JO_MALLOC_TRY_REUSE_BLOCK);
    if (enemy_action_buffer == JO_NULL)
    {
        failed_asset = "ENEMY ACTION BUFFER";
        return 0;
    }
    for (slot = 0; slot < CAP_MAX_ENEMIES; ++slot)
    {
        enemy_action_images[slot].width = AVSP_ENEMY_CEL_WIDTH;
        enemy_action_images[slot].height = AVSP_ENEMY_CEL_HEIGHT;
        enemy_action_images[slot].data = enemy_action_buffer +
            slot * AVSP_ENEMY_DECODED_BYTES;
    }
    return 1;
}

static int decode_enemy_action_pose(const int pose, const int slot)
{
    unsigned int source = 0;
    unsigned int target = 0;
    const unsigned int source_offset = avsp_enemy_rle_offsets[pose];
    const unsigned int source_length = avsp_enemy_rle_bytes[pose];
    const unsigned char *source_data;
    unsigned char *output = enemy_action_images[slot].data;
    if (source_offset + source_length > AVSP_ENEMY_ARCHIVE_BYTES)
    {
        failed_asset = "ENEMY ACTION INDEX";
        return 0;
    }
    source_data = enemy_action_archive + source_offset;
    while (source + 1 < source_length)
    {
        unsigned int count = source_data[source++];
        unsigned char value = source_data[source++];
        if (count == 0 || target + count > AVSP_ENEMY_DECODED_BYTES)
        {
            failed_asset = "ENEMY ACTION RLE";
            return 0;
        }
        memset(output + target, value, count);
        target += count;
    }
    if (source != source_length || target != AVSP_ENEMY_DECODED_BYTES)
    {
        failed_asset = "ENEMY ACTION SIZE";
        return 0;
    }
    return 1;
}

static int load_stalker_action_archive(void)
{
    int length = 0;
    stalker_action_archive = (unsigned char *)avsp_fs_read_file_in_dir(
        AVSP_STALKER_ARCHIVE_FILE, "SPR4", &length);
    if (stalker_action_archive == JO_NULL ||
        length != AVSP_STALKER_ARCHIVE_BYTES)
    {
        failed_asset = AVSP_STALKER_ARCHIVE_FILE;
        return 0;
    }
    return 1;
}

static int decode_stalker_action_pose(const int pose, const int slot)
{
    unsigned int source = 0;
    unsigned int target = 0;
    const unsigned int source_offset = avsp_stalker_rle_offsets[pose];
    const unsigned int source_length = avsp_stalker_rle_bytes[pose];
    const unsigned char *source_data;
    unsigned char *output = enemy_action_images[slot].data;
    if (source_offset + source_length > AVSP_STALKER_ARCHIVE_BYTES)
    {
        failed_asset = "STALKER ACTION INDEX";
        return 0;
    }
    source_data = stalker_action_archive + source_offset;
    while (source + 1 < source_length)
    {
        unsigned int count = source_data[source++];
        unsigned char value = source_data[source++];
        if (count == 0 || target + count > AVSP_STALKER_DECODED_BYTES)
        {
            failed_asset = "STALKER ACTION RLE";
            return 0;
        }
        memset(output + target, value, count);
        target += count;
    }
    if (source != source_length || target != AVSP_STALKER_DECODED_BYTES)
    {
        failed_asset = "STALKER ACTION SIZE";
        return 0;
    }
    return 1;
}

/* Compose the given Chrysalis pose into boss_action_image from the ROM tile
   tables in generated/avsp_boss_rom.h. The ROM stores raw CPS2 pens (0..14
   visible, 15 transparent) in two-pens-per-byte tiles; the composed cel keeps
   pen+1 so the buffer's zero value stays transparent, in the same 4bpp
   high-nibble-first layout the VDP1 sprite and the archive oracles use. Parts
   are painted in reverse order so earlier parts overdraw later ones, matching
   the host-test compose that verifies all 29 poses against the archived
   BACT/BHIT/BKO output pixel for pixel. */
static int compose_boss_rom_pose(const int pose)
{
    const AvspBossRomPose *rom_pose;
    const AvspBossRomPart *parts;
    const AvspBossRomPart *part;
    const unsigned short *part_tiles;
    const unsigned char *tile;
    unsigned char *output;
    int min_x, max_x, min_y, max_y;
    int origin_x, origin_y;
    int i, p, tile_x, tile_y;
    int source_x, source_y, index, dest_x, dest_y;
    int tx, ty, src_tx, src_ty, cx, cy, pen, bit, tile_byte;

    output = boss_action_image.data;
    if (pose < 0 || pose >= AVSP_BOSS_ROM_POSE_COUNT || output == JO_NULL)
    {
        failed_asset = "BOSS ROM POSE";
        return 0;
    }
    memset(output, 0, AVSP_BOSS_DECODED_BYTES);
    rom_pose = &avsp_boss_rom_poses[pose];
    parts = &avsp_boss_rom_parts[rom_pose->part_offset];
    if (rom_pose->part_count == 0)
        return 1;
    min_x = -parts[0].lx - parts[0].nx * 16;
    max_x = -parts[0].lx;
    min_y = parts[0].ly;
    max_y = parts[0].ly + parts[0].ny * 16;
    for (i = 1; i < (int)rom_pose->part_count; ++i)
    {
        part = &parts[i];
        if (-part->lx - part->nx * 16 < min_x)
            min_x = -part->lx - part->nx * 16;
        if (-part->lx > max_x)
            max_x = -part->lx;
        if (part->ly < min_y)
            min_y = part->ly;
        if (part->ly + part->ny * 16 > max_y)
            max_y = part->ly + part->ny * 16;
    }
    origin_x = AVSP_BOSS_ROM_CEL_WIDTH / 2 - (min_x + max_x) / 2 + rom_pose->dx;
    origin_y = AVSP_BOSS_ROM_CEL_HEIGHT / 2 - (min_y + max_y) / 2 + rom_pose->dy;
    for (p = (int)rom_pose->part_count - 1; p >= 0; --p)
    {
        part = &parts[p];
        part_tiles = &avsp_boss_rom_part_tiles[part->tile_offset];
        for (tile_y = 0; tile_y < part->ny; ++tile_y)
        {
            for (tile_x = 0; tile_x < part->nx; ++tile_x)
            {
                source_y = part->flip_y ? part->ny - 1 - tile_y : tile_y;
                source_x = part->flip_x ? part->nx - 1 - tile_x : tile_x;
                index = part_tiles[source_y * part->nx + source_x];
                tile = &avsp_boss_rom_tiles[index * AVSP_BOSS_ROM_TILE_BYTES];
                dest_x = origin_x - part->lx - part->nx * 16 + tile_x * 16;
                dest_y = origin_y + part->ly + tile_y * 16;
                for (ty = 0; ty < 16; ++ty)
                {
                    for (tx = 0; tx < 16; ++tx)
                    {
                        src_ty = part->flip_y ? 15 - ty : ty;
                        src_tx = part->flip_x ? 15 - tx : tx;
                        tile_byte = tile[(src_ty * 16 + src_tx) / 2];
                        pen = (src_tx & 1) ? (tile_byte & 0xF) :
                            (tile_byte >> 4);
                        if (pen == 15)
                            continue;
                        cx = dest_x + tx;
                        cy = dest_y + ty;
                        if (cx < 0 || cx >= AVSP_BOSS_ROM_CEL_WIDTH ||
                            cy < 0 || cy >= AVSP_BOSS_ROM_CEL_HEIGHT)
                            continue;
                        bit = cy * AVSP_BOSS_ROM_CEL_WIDTH + cx;
                        if (bit & 1)
                        {
                            output[bit / 2] = (unsigned char)
                                ((output[bit / 2] & 0x0F) | ((pen + 1) << 4));
                        }
                        else
                        {
                            output[bit / 2] = (unsigned char)
                                ((output[bit / 2] & 0xF0) | (pen + 1));
                        }
                    }
                }
            }
        }
    }
    return 1;
}

static void set_actor_palette(void)
{
    static jo_color colors[256];
    int bank;
    int index;

    for (index = 0; index < 256; ++index) colors[index] = JO_COLOR_Black;
    for (bank = 0; bank < AVSP_EXACT_PALETTE_BANKS; ++bank)
    {
        for (index = 0; index < 15; ++index)
            /* Jo's palette allocation starts at CRAM base + 1. Sprite pen 1
               therefore reads array entry 0, not array entry 1. */
            colors[bank * 16 + index] = JO_COLOR_RGB(
                avsp_exact_palettes[bank][index][0],
                avsp_exact_palettes[bank][index][1],
                avsp_exact_palettes[bank][index][2]);
    }

    jo_create_palette_from(&actor_palette, colors, AVSP_CRAM_MAX_COLOURS);
}

static void set_frontend_palettes(void)
{
    static jo_color colors[256];
    int scene;
    int index;

    for (scene = 0; scene < AVSP_FRONTEND_SCENES; ++scene)
    {
        for (index = 0; index < 256; ++index)
            colors[index] = JO_COLOR_Black;
        jo_create_palette_from(&frontend_palettes[scene], colors,
                               AVSP_CRAM_MAX_COLOURS);
    }
}

#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static int hud_palette_binding_valid(const jo_color *colors,
                                     const int source_offset)
{
    int index;
    for (index = 0; index < AVSP_CRAM_MAX_COLOURS; ++index)
    {
        if (colors[index] != JO_COLOR_RGB(
                avsp_hud_palette[index + source_offset][0],
                avsp_hud_palette[index + source_offset][1],
                avsp_hud_palette[index + source_offset][2]))
            return 0;
    }
    return 1;
}
#endif

static void set_hud_palette(void)
{
    static jo_color colors[256];
    int index;

    for (index = 0; index < 256; ++index) colors[index] = JO_COLOR_Black;
    for (index = 0; index < AVSP_CRAM_MAX_COLOURS; ++index)
        /* HUD texels are one-based: transparent is source index 0. Jo's
           palette allocation already reserves sprite pen 0, so source index
           1 must be copied into CRAM array entry 0. */
        colors[index] = JO_COLOR_RGB(
            avsp_hud_palette[index + 1][0], avsp_hud_palette[index + 1][1],
            avsp_hud_palette[index + 1][2]);
    jo_create_palette_from(&hud_palette, colors, AVSP_CRAM_MAX_COLOURS);
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
    avsp_diag_hud_palette_binding_ok =
        hud_palette_binding_valid(hud_palette.data, 1);
    avsp_diag_hud_palette_yellow =
        hud_palette.data[AVSP_HUD_YELLOW_INDEX - 1];
    avsp_diag_hud_palette_red =
        hud_palette.data[AVSP_HUD_RED_INDEX - 1];
    avsp_diag_hud_palette_energy =
        hud_palette.data[AVSP_HUD_ENERGY_INDEX - 1];
    avsp_diag_hud_palette_empty =
        hud_palette.data[AVSP_HUD_EMPTY_INDEX - 1];
#endif
}

static int load_hud_image(jo_img_8bits *image, const char *filename,
                          const int width, const int height)
{
    int length = 0;
    image->width = width;
    image->height = height;
    image->data = (unsigned char *)avsp_fs_read_file_in_dir(
        filename, "SPR8", &length);
    if (image->data == JO_NULL || length != width * height)
    {
        failed_asset = filename;
        return 0;
    }
    return 1;
}

static int load_hud_assets(void)
{
    return load_hud_image(&hud_top_image, "HUDTOP.BIN",
                          AVSP_HUD_TOP_WIDTH, AVSP_HUD_TOP_HEIGHT) &&
           load_hud_image(&hud_prompt_image, "HUDP2.BIN",
                          AVSP_HUD_PROMPT_WIDTH, AVSP_HUD_PROMPT_HEIGHT) &&
           load_hud_image(&hud_heat_image, "HUDHEAT.BIN",
                          AVSP_HUD_HEAT_WIDTH, AVSP_HUD_HEAT_HEIGHT);
}

#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static int load_player2_hud_assets(void)
{
    return load_hud_image(&hud_p2_top_image, "HUD2TOP.BIN",
                          AVSP_HUD_P2_TOP_WIDTH,
                          AVSP_HUD_P2_TOP_HEIGHT) &&
           load_hud_image(&hud_p2_heat_image, "HUD2HEAT.BIN",
                          AVSP_HUD_P2_HEAT_WIDTH,
                          AVSP_HUD_P2_HEAT_HEIGHT);
}
#endif

static int load_frontend_assets(void)
{
    avsp_frontend_init(&frontend_runtime, avsp_fs_read_file_in_dir,
                       background_bitmap, &frontend_palettes[0],
                       &frontend_palettes[1]);
    if (!avsp_frontend_load_title_surface(&frontend_runtime))
    {
        failed_asset = "ROM FRONTEND TITLE";
        return 0;
    }
    return 1;
}

static void release_frontend_scene(const int scene)
{
    if (scene == 0)
        avsp_frontend_release_title_objects(&frontend_runtime);
    else if (scene == 1)
        avsp_frontend_release_select_objects(&frontend_runtime);
}

static void copy_snapshot_to_background(const unsigned char *source)
{
    static unsigned char empty_row[BACKGROUND_WIDTH];
    int y;
    for (y = 0; y < BACKGROUND_HEIGHT; ++y)
    {
        unsigned char *target = background_bitmap + y * BACKGROUND_WIDTH;
        /* CPU copies avoid the transition-time DMA busy-wait deadlock seen
         * in interactive boots. This helper remains shared by the route
         * sequence surfaces; the ROM frontend RLE decoder writes NBG1
         * directly and does not call it. */
        memcpy(target, empty_row, BACKGROUND_WIDTH);
        if (y < SNAPSHOT_HEIGHT)
            memcpy(target, source + y * SNAPSHOT_FIT_WIDTH,
                   SNAPSHOT_FIT_WIDTH);
    }
}

static int activate_frontend_scene(const int scene)
{
    int bitmap_scene = BITMAP_SCENE_FRONTEND_BASE + scene;
    if (current_bitmap_scene == bitmap_scene) return 1;
    if (scene == 0 && !frontend_runtime.title_surface_ready)
    {
        failed_asset = "ROM FRONTEND TITLE";
        return 0;
    }
    if (scene == 1 && !frontend_runtime.select_surface_ready)
    {
        failed_asset = "ROM FRONTEND SELECT";
        return 0;
    }
    if (scene == 0)
        avsp_frontend_activate_title(&frontend_runtime);
    else
        avsp_frontend_activate_select(&frontend_runtime);
    current_bitmap_scene = bitmap_scene;
    return 1;
}

static int load_route_sequences(void)
{
    int scene;
    int length;
    sequence_pixels = (unsigned char *)jo_malloc(SNAPSHOT_FIT_BYTES);
    if (sequence_pixels == JO_NULL)
    {
        failed_asset = "SEQUENCE BUFFER";
        return 0;
    }
    for (scene = 0; scene < AVSP_SEQUENCE_SCENES; ++scene)
    {
        length = 0;
        sequence_rle[scene] = (unsigned char *)avsp_fs_read_file_in_dir(
            avsp_sequence_files[scene], "SPR8", &length);
        if (sequence_rle[scene] == JO_NULL ||
            length != (int)avsp_sequence_rle_bytes[scene])
        {
            failed_asset = avsp_sequence_files[scene];
            return 0;
        }
    }
    return 1;
}

static int sequence_scene_for_world(void)
{
    if (world.encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO)
    {
        if (world.encounter_timer < 120) return AVSP_SEQUENCE_BARRICADE_INTRO;
        if (world.encounter_timer < 240) return AVSP_SEQUENCE_WITHDRAW_DIALOGUE;
        return AVSP_SEQUENCE_BARRICADE_BREACH;
    }
    if (world.encounter_state == CAP_ENCOUNTER_DOOR_DIALOGUE)
        return AVSP_SEQUENCE_DOOR_DIALOGUE;
    if (world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION)
        return AVSP_SEQUENCE_INTERIOR_TRANSITION;
    if (world.encounter_state == CAP_ENCOUNTER_BOSS_DEFEAT)
        return world.encounter_timer < 60 ? -1 :
            AVSP_SEQUENCE_BOSS_DEATH_EXPLOSION;
    if (world.encounter_state == CAP_ENCOUNTER_STAGE_CLEAR)
        return AVSP_SEQUENCE_STAGE_CLEAR;
    if (world.encounter_state == CAP_ENCOUNTER_RESULTS)
        return world.encounter_timer < 300 ? AVSP_SEQUENCE_RESULTS_BEGIN :
                                             AVSP_SEQUENCE_RESULTS_COMPLETE;
    if (world.encounter_state == CAP_ENCOUNTER_RESULTS_EXIT)
        return AVSP_SEQUENCE_RESULTS_EXIT;
    if (world.encounter_state == CAP_ENCOUNTER_INTERMISSION)
        return AVSP_SEQUENCE_INTERMISSION;
    if (world.encounter_state == CAP_ENCOUNTER_COMPLETE)
        return AVSP_SEQUENCE_ROUND_2_BOUNDARY;
    return -1;
}

static int activate_route_sequence(const int scene)
{
    static jo_color colors[256];
    unsigned int source = 0;
    unsigned int target = 0;
    int index;

    if (scene < 0 || current_bitmap_scene == BITMAP_SCENE_ROUTE_BASE + scene)
        return 1;
    while (source + 1 < avsp_sequence_rle_bytes[scene])
    {
        unsigned int count = sequence_rle[scene][source++];
        unsigned char value = sequence_rle[scene][source++];
        if (count == 0 || target + count > SNAPSHOT_FIT_BYTES)
        {
            failed_asset = "SEQUENCE RLE";
            return 0;
        }
        memset(sequence_pixels + target, value, count);
        target += count;
    }
    if (source != avsp_sequence_rle_bytes[scene] ||
        target != SNAPSHOT_FIT_BYTES)
    {
        failed_asset = "SEQUENCE SIZE";
        return 0;
    }
    for (index = 0; index < 256; ++index)
        colors[index] = JO_COLOR_RGB(
            avsp_sequence_palettes[scene][index][0],
            avsp_sequence_palettes[scene][index][1],
            avsp_sequence_palettes[scene][index][2]);
    /* The route-sequence RLE pixels are already one-based (measured minimum 1
       across all thirteen holds), and avsp_sequence_palettes is indexed by
       source colour, so entry k is the colour of pixel k + 1 and transcribes
       straight into the Jo data range. 255 entries, not 256: the 256th would
       land on the next allocation's block boundary. */
    if (!avsp_cram_copy_source_indexed(
            (unsigned short *)frontend_palettes[0].data,
            (const unsigned short *)colors, AVSP_CRAM_MAX_COLOURS))
    {
        failed_asset = "SEQUENCE PALETTE COPY";
        return 0;
    }
    copy_snapshot_to_background(sequence_pixels);
    slBMPaletteNbg1((unsigned short)frontend_palettes[0].id);
    jo_move_background(0, 0);
    current_bitmap_scene = BITMAP_SCENE_ROUTE_BASE + scene;
    return 1;
}

static int load_background(void)
{
    background_image.data = JO_NULL;
    jo_create_palette(&background_palette);
    if (background_palette.data == JO_NULL)
    {
        failed_asset = "BG PALETTE";
        return 0;
    }
    jo_set_tga_default_palette(&background_palette);
    if (jo_tga_8bits_loader(&background_image, "BG", "CORRIDOR.TGA", 0) != JO_TGA_OK ||
        background_image.width != BACKGROUND_WIDTH ||
        background_image.height != BACKGROUND_HEIGHT)
    {
        failed_asset = "CORRIDOR.TGA";
        return 0;
    }
    if (nbg1_bitmap != JO_NULL)
    {
        jo_vdp2_free(nbg1_bitmap);
        nbg1_bitmap = JO_NULL;
    }
    background_bitmap = (unsigned char *)jo_vdp2_malloc(
        JO_VDP2_RAM_BITMAP_NBG1, BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
    if (background_bitmap == JO_NULL)
    {
        failed_asset = "NBG1 BITMAP";
        return 0;
    }
    slBitMapNbg1(COL_TYPE_256, BM_512x256, background_bitmap);
    /* The generated background is already horizontally fitted to Saturn's
       352-pixel field.  Keep VDP2 at 1:1 so emulator and hardware paths use
       the same deterministic coordinate mapping. */
    slZoomModeNbg1(ZOOM_1);
    slBMPaletteNbg1((unsigned short)background_palette.id);
    memcpy(background_bitmap, background_image.data, BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
    current_bitmap_scene = BITMAP_SCENE_CORRIDOR;
    jo_set_displayed_screens(JO_NBG0_SCREEN | JO_NBG1_SCREEN);
    return 1;
}

static int load_boss_background(void)
{
    boss_background_image.data = JO_NULL;
    jo_create_palette(&boss_background_palette);
    if (boss_background_palette.data == JO_NULL)
    {
        failed_asset = "BOSS BG PALETTE";
        return 0;
    }
    jo_set_tga_default_palette(&boss_background_palette);
    if (jo_tga_8bits_loader(&boss_background_image, "BG", "BOSSROOM.TGA", 0) != JO_TGA_OK ||
        boss_background_image.width != BACKGROUND_WIDTH ||
        boss_background_image.height != BACKGROUND_HEIGHT)
    {
        failed_asset = "BOSSROOM.TGA";
        return 0;
    }
    return 1;
}

static void activate_gameplay_background(const int stage_area)
{
    int requested = stage_area == 1 ? BITMAP_SCENE_BOSS : BITMAP_SCENE_CORRIDOR;
    if (current_bitmap_scene == requested) return;
    if (stage_area == 1)
    {
        memcpy(background_bitmap, boss_background_image.data,
                    BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
        slBMPaletteNbg1((unsigned short)boss_background_palette.id);
    }
    else
    {
        memcpy(background_bitmap, background_image.data,
                    BACKGROUND_WIDTH * BACKGROUND_HEIGHT);
        slBMPaletteNbg1((unsigned short)background_palette.id);
    }
    current_bitmap_scene = requested;
}

static int add_sprite_for_asset(const CelId cel)
{
    int sprite_id = jo_sprite_add_4bits_image(&cel_assets[cel].image);
    if (sprite_id < 0) failed_asset = cel_assets[cel].filename;
    return sprite_id;
}

static int create_sprite_working_set(void)
{
    int layer;
    player_idle_sprites[0] = add_sprite_for_asset(CEL_PLAYER_IDLE_0);
    player_idle_sprites[1] = add_sprite_for_asset(CEL_PLAYER_IDLE_1);
    if (!decode_player_action_pose(0)) return 0;
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        player_action_sprites[layer] = jo_sprite_add_4bits_image(
            &player_action_images[layer]);
        if (player_action_sprites[layer] < 0)
            failed_asset = "PLAYER ACTION VDP1";
    }
    current_player_action_pose = 0;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    if (!decode_source_combat_player_pose(0)) return 0;
    source_combat_player_sprite = jo_sprite_add_4bits_image(
        &source_combat_player_image);
    if (source_combat_player_sprite < 0)
    {
        failed_asset = "SOURCE COMBAT PLAYER VDP1";
        return 0;
    }
    current_source_combat_player_pose = 0;
#endif
    hud_top_sprite = jo_sprite_add_8bits_image(&hud_top_image);
    hud_prompt_sprite = jo_sprite_add_8bits_image(&hud_prompt_image);
    hud_heat_sprite = jo_sprite_add_8bits_image(&hud_heat_image);
    if (hud_top_sprite < 0 || hud_prompt_sprite < 0 || hud_heat_sprite < 0)
        failed_asset = "HUD VDP1";
    displayed_hud_health = -1;
    displayed_hud_energy = -1;
    return failed_asset == JO_NULL;
}

#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static int create_hud_sprite_working_set(void)
{
    hud_top_sprite = jo_sprite_add_8bits_image(&hud_top_image);
    hud_prompt_sprite = jo_sprite_add_8bits_image(&hud_prompt_image);
    hud_heat_sprite = jo_sprite_add_8bits_image(&hud_heat_image);
    hud_p2_top_sprite = jo_sprite_add_8bits_image(&hud_p2_top_image);
    hud_p2_heat_sprite = jo_sprite_add_8bits_image(&hud_p2_heat_image);
    if (hud_top_sprite < 0 || hud_prompt_sprite < 0 || hud_heat_sprite < 0 ||
        hud_p2_top_sprite < 0 || hud_p2_heat_sprite < 0)
    {
        failed_asset = "HUD VDP1";
        return 0;
    }
    displayed_hud_health = -1;
    displayed_hud_energy = -1;
    displayed_hud_p2_health = -1;
    displayed_hud_p2_energy = -1;
    return 1;
}
#endif

#ifdef AVSP_PLAYER_SALVAGE_BENCH
static int create_player_sprite_working_set(void)
{
    int layer;
    player_idle_sprites[0] = add_sprite_for_asset(CEL_PLAYER_IDLE_0);
    player_idle_sprites[1] = add_sprite_for_asset(CEL_PLAYER_IDLE_1);
    if (!decode_player_action_pose(0)) return 0;
    for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
    {
        player_action_sprites[layer] = jo_sprite_add_4bits_image(
            &player_action_images[layer]);
        if (player_action_sprites[layer] < 0)
        {
            failed_asset = "PLAYER ACTION VDP1";
            return 0;
        }
    }
    current_player_action_pose = 0;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    if (!decode_source_combat_player_pose(0)) return 0;
    source_combat_player_sprite = jo_sprite_add_4bits_image(
        &source_combat_player_image);
    if (source_combat_player_sprite < 0)
    {
        failed_asset = "SOURCE COMBAT PLAYER VDP1";
        return 0;
    }
    current_source_combat_player_pose = 0;
#endif
    return 1;
}
#endif

static int prepare_enemy_runtime(void)
{
    int slot;

    if (enemy_runtime_ready) return 1;
    if (!allocate_enemy_action_buffer()) return 0;
    for (slot = 0; slot < CAP_MAX_ENEMIES; ++slot)
    {
        if (!decode_enemy_action_pose(0, slot)) return 0;
        enemy_action_sprites[slot] = jo_sprite_add_4bits_image(
            &enemy_action_images[slot]);
        if (enemy_action_sprites[slot] < 0)
        {
            failed_asset = "ENEMY ACTION VDP1";
            return 0;
        }
        current_enemy_action_poses[slot] = 0;
        current_enemy_action_kinds[slot] = CAP_ACTOR_ALIEN;
    }
    enemy_runtime_ready = 1;
    return 1;
}

static int prepare_boss_runtime(void)
{
    if (boss_runtime_ready) return 1;
    /* The boss is composed entirely from the ROM tile tables (see
       compose_boss_rom_pose), so no archive is loaded for its animation.
       Only the single decoded-cel buffer is allocated here. */
    boss_action_image.width = AVSP_BOSS_CEL_WIDTH;
    boss_action_image.height = AVSP_BOSS_CEL_HEIGHT;
    boss_action_image.data = (unsigned char *)jo_malloc_with_behaviour(
        AVSP_BOSS_DECODED_BYTES, JO_MALLOC_TRY_REUSE_BLOCK);
    if (boss_action_image.data == JO_NULL)
    {
        failed_asset = "BOSS ACTION BUFFER";
        return 0;
    }
    if (!compose_boss_rom_pose(0)) return 0;
    boss_action_sprite = jo_sprite_add_4bits_image(&boss_action_image);
    if (boss_action_sprite < 0)
    {
        failed_asset = "BOSS ACTION VDP1";
        return 0;
    }
    current_boss_action_pose = 0;
    boss_runtime_ready = 1;
    return 1;
}

static int player_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_SHOOT) return AVSP_PLAYER_CLIP_GUN;
    if (action == CAP_ACT_ATTACK) return AVSP_PLAYER_CLIP_MELEE;
    if (action == CAP_ACT_JUMP) return AVSP_PLAYER_CLIP_JUMP;
    if (action == CAP_ACT_DASH) return AVSP_PLAYER_CLIP_DASH;
    if (action == CAP_ACT_SPECIAL) return AVSP_PLAYER_CLIP_SPECIAL;
    if (action == CAP_ACT_WALK) return AVSP_PLAYER_CLIP_WALK;
    if (action == CAP_ACT_HIT) return AVSP_PLAYER_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_PLAYER_CLIP_KO;
    return -1;
}

#ifdef AVSP_VISUAL_TEST
static CapAction visual_action_for_index(const int index)
{
    if (index == 0) return CAP_ACT_WALK;
    if (index == 1) return CAP_ACT_SHOOT;
    if (index == 2) return CAP_ACT_ATTACK;
    if (index == 3) return CAP_ACT_JUMP;
    if (index == 4) return CAP_ACT_DASH;
    if (index == 5) return CAP_ACT_SPECIAL;
    if (index == 6) return CAP_ACT_HIT;
    return CAP_ACT_KO;
}

static CapAction visual_enemy_action_for_index(const int index)
{
    if (index == 1) return CAP_ACT_ATTACK;
    if (index == 2) return CAP_ACT_HIT;
    if (index == 3) return CAP_ACT_KO;
    return CAP_ACT_WALK;
}
#endif

static int player_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_player_action_step_counts[clip]; ++step)
    {
        int duration = avsp_player_action_step_durations[clip][step];
        if (remaining < duration)
            return avsp_player_action_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_player_action_step_poses[clip]
        [avsp_player_action_step_counts[clip] - 1];
}

static int enemy_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_ATTACK) return AVSP_ENEMY_CLIP_ATTACK;
    if (action == CAP_ACT_HIT) return AVSP_ENEMY_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_ENEMY_CLIP_KO;
    return AVSP_ENEMY_CLIP_WALK;
}

static int enemy_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_enemy_step_counts[clip]; ++step)
    {
        int duration = avsp_enemy_step_durations[clip][step];
        if (remaining < duration)
            return avsp_enemy_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_enemy_step_poses[clip][avsp_enemy_step_counts[clip] - 1];
}

static int stalker_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_ATTACK) return AVSP_STALKER_CLIP_ATTACK;
    if (action == CAP_ACT_HIT) return AVSP_STALKER_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_STALKER_CLIP_KO;
    return AVSP_STALKER_CLIP_WALK;
}

static int stalker_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_stalker_step_counts[clip]; ++step)
    {
        int duration = avsp_stalker_step_durations[clip][step];
        if (remaining < duration)
            return avsp_stalker_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_stalker_step_poses[clip]
        [avsp_stalker_step_counts[clip] - 1];
}

static int boss_clip_for_action(const CapAction action)
{
    if (action == CAP_ACT_ATTACK) return AVSP_BOSS_CLIP_ATTACK;
    if (action == CAP_ACT_HIT) return AVSP_BOSS_CLIP_HIT;
    if (action == CAP_ACT_KO) return AVSP_BOSS_CLIP_KO;
    if (action == CAP_ACT_WALK) return AVSP_BOSS_CLIP_WALK;
    return AVSP_BOSS_CLIP_IDLE;
}

static int boss_pose_for_frame(const int clip, const int action_frame)
{
    int step;
    int remaining = action_frame;
    for (step = 0; step < avsp_boss_step_counts[clip]; ++step)
    {
        int duration = avsp_boss_step_durations[clip][step];
        if (remaining < duration)
            return avsp_boss_step_poses[clip][step];
        remaining -= duration;
    }
    return avsp_boss_step_poses[clip][avsp_boss_step_counts[clip] - 1];
}

static void draw_exact_layer_offset(const CapActor *actor, const int screen_x,
                                    const int screen_offset_x,
                                    const int screen_offset_y,
                                    const int sprite_id, const int palette_bank,
                                    const int depth)
{
    /* Captured player and enemy pivots sit at pixel 184 in each 192px cel. */
    int screen_y = actor->lane - 200 - actor->height + screen_offset_y;
    jo_sprite_set_palette_4bits(actor_palette.id, palette_bank);
    if (actor->facing < 0) jo_sprite_enable_horizontal_flip();
    jo_sprite_draw3D(sprite_id, screen_x + screen_offset_x, screen_y, depth);
    if (actor->facing < 0) jo_sprite_disable_horizontal_flip();
}

static void draw_exact_layer(const CapActor *actor, const int screen_x,
                             const int sprite_id, const int palette_bank,
                             const int depth)
{
    draw_exact_layer_offset(actor, screen_x, 0, 0,
                            sprite_id, palette_bank, depth);
}

static void draw_player(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    int layer;
    int clip;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
#ifdef AVSP_PLAYABLE_SLICE
    if (playable_slice_frame.scene.player_presentation_active)
    {
        int pose = playable_slice_frame.scene.player_source_pose;
        if (pose != current_source_combat_player_pose)
        {
            if (!decode_source_combat_player_pose(pose))
            {
                runtime_ready = 0;
                return;
            }
            jo_sprite_replace_4bits_image(
                &source_combat_player_image, source_combat_player_sprite);
            current_source_combat_player_pose = pose;
        }
        draw_exact_layer(actor, screen_x, source_combat_player_sprite, 0,
                         depth);
        return;
    }
#else
    if (avsp_diag_combat_player_presentation_active)
    {
        int pose = avsp_diag_combat_player_source_pose;
        if (pose != current_source_combat_player_pose)
        {
            if (!decode_source_combat_player_pose(pose))
            {
                runtime_ready = 0;
                return;
            }
            jo_sprite_replace_4bits_image(
                &source_combat_player_image, source_combat_player_sprite);
            current_source_combat_player_pose = pose;
        }
        draw_exact_layer(actor, screen_x, source_combat_player_sprite, 0,
                         depth);
        return;
    }
#endif
#endif
    clip = player_clip_for_action(actor->action);
    if (clip >= 0)
    {
        int frame = actor->action == CAP_ACT_WALK ?
            (actor->locomotion_frame > 0 ? actor->locomotion_frame - 1 : 0) :
            actor->action_frame;
        int screen_offset_x;
        int screen_offset_y;
        int pose;
        if (actor->action == CAP_ACT_WALK)
            frame %= avsp_player_action_total_frames[clip];
        else if (frame >= avsp_player_action_total_frames[clip])
            frame = avsp_player_action_total_frames[clip] - 1;
        pose = player_pose_for_frame(clip, frame);
        screen_offset_x = avsp_player_action_frame_x[clip][frame] *
            CAP_VIEW_WIDTH / CAP_CPS2_VIEW_WIDTH;
        if (actor->facing < 0) screen_offset_x = -screen_offset_x;
        screen_offset_y = avsp_player_action_frame_y[clip][frame];
        if (pose != current_player_action_pose)
        {
            if (!decode_player_action_pose(pose))
            {
                runtime_ready = 0;
                return;
            }
            for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
                jo_sprite_replace_4bits_image(
                    &player_action_images[layer], player_action_sprites[layer]);
            current_player_action_pose = pose;
        }
        for (layer = 0; layer < AVSP_PLAYER_ACTION_LAYERS; ++layer)
            draw_exact_layer_offset(
                actor, screen_x, screen_offset_x, screen_offset_y,
                player_action_sprites[layer], layer, depth - layer);
    }
    else
    {
        draw_exact_layer(actor, screen_x, player_idle_sprites[0], 0, depth);
        draw_exact_layer(actor, screen_x, player_idle_sprites[1], 1, depth - 1);
    }
}

static void draw_alien(const CapActor *actor, const int screen_x,
                       const int slot)
{
    int is_stalker = actor->kind == CAP_ACTOR_STALKER;
    int depth = 330 - actor->lane;
    int clip = is_stalker ? stalker_clip_for_action(actor->action) :
                            enemy_clip_for_action(actor->action);
    int frame = (actor->action == CAP_ACT_WALK ||
                 actor->action == CAP_ACT_IDLE) ?
        actor->locomotion_frame : actor->action_frame;
    int total_frames = is_stalker ? avsp_stalker_total_frames[clip] :
                                    avsp_enemy_total_frames[clip];
    int pose;
    if ((is_stalker && clip == AVSP_STALKER_CLIP_WALK) ||
        (!is_stalker && clip == AVSP_ENEMY_CLIP_WALK))
        frame %= total_frames;
    else if (frame >= total_frames)
        frame = total_frames - 1;
    pose = is_stalker ? stalker_pose_for_frame(clip, frame) :
                        enemy_pose_for_frame(clip, frame);
    if (pose != current_enemy_action_poses[slot] ||
        current_enemy_action_kinds[slot] != actor->kind)
    {
        int decoded = is_stalker ? decode_stalker_action_pose(pose, slot) :
                                   decode_enemy_action_pose(pose, slot);
        if (!decoded)
        {
            runtime_ready = 0;
            return;
        }
        jo_sprite_replace_4bits_image(
            &enemy_action_images[slot], enemy_action_sprites[slot]);
        current_enemy_action_poses[slot] = pose;
        current_enemy_action_kinds[slot] = actor->kind;
    }
    draw_exact_layer(actor, screen_x, enemy_action_sprites[slot],
                     is_stalker ? AVSP_STALKER_PALETTE_BANK :
                                  3 + actor->variant, depth);
}

static void draw_boss(const CapActor *actor, const int screen_x)
{
    int depth = 330 - actor->lane;
    int clip = boss_clip_for_action(actor->action);
    int frame = clip == AVSP_BOSS_CLIP_WALK ?
        actor->locomotion_frame : actor->action_frame;
    int pose;
    int screen_offset_x;
    int screen_offset_y;
    /* Boss graphics enter the working set only after the opening PCM overlay
       has ended. This avoids reserving a second large decoded actor cel during
       the cold-boot menu and first-wave allocation phase. */
    if (!prepare_boss_runtime())
    {
        runtime_ready = 0;
        return;
    }
    if (clip == AVSP_BOSS_CLIP_WALK)
        frame %= avsp_boss_total_frames[clip];
    else if (frame >= avsp_boss_total_frames[clip])
        frame = avsp_boss_total_frames[clip] - 1;
    screen_offset_x = avsp_boss_frame_x[clip][frame] *
        CAP_VIEW_WIDTH / CAP_CPS2_VIEW_WIDTH;
    screen_offset_y = avsp_boss_frame_y[clip][frame];
    pose = boss_pose_for_frame(clip, frame);
    if (pose != current_boss_action_pose)
    {
        if (!compose_boss_rom_pose(pose))
        {
            runtime_ready = 0;
            return;
        }
        jo_sprite_replace_4bits_image(
            &boss_action_image, boss_action_sprite);
        current_boss_action_pose = pose;
    }
    draw_exact_layer_offset(actor, screen_x, screen_offset_x, screen_offset_y,
                            boss_action_sprite, AVSP_BOSS_PALETTE_BANK, depth);
}

/* The captured character-confirm transition is a row shutter over the held
   selection image, not an animation: every visible row is byte-identical to
   the held frame and everything else is black. The selection pixels are
   already in the VDP2 bitmap, so the shutter is a progressive blackout of
   that bitmap and needs no stored frames and no source surface. Blacking is
   safe because the band only ever shrinks; only the rows newly hidden since
   the previous frame are written. See docs/AGENT_HANDOFF.md and
   data/frontend_geometry_cadence1.json. */
static void apply_confirm_shutter(void)
{
    static unsigned char empty_row[BACKGROUND_WIDTH];
    int top = 0;
    int bottom = 0;
    int previous_top = 0;
    int previous_bottom = 0;
    int row;

    /* The band is a function of frames since the confirm input. The
       rendered encounter timer leads that count by one (the confirm step
       both zeroes and increments it), and the complete-interval proof in
       tools/verify_confirm_shutter.py pins the first masked source frame
       to input + 86, so the timer is converted back before the lookup. */
    if (world.encounter_timer - 1 <= CAP_CONFIRM_SHUTTER_START_TIMER) return;
    (void)cap_confirm_shutter_band(world.encounter_timer - 1, &top, &bottom);
    (void)cap_confirm_shutter_band(world.encounter_timer - 2, &previous_top,
                                   &previous_bottom);
    if (previous_top > previous_bottom) return;
    if (top > bottom)
    {
        top = previous_bottom + 1;
        bottom = previous_bottom;
    }
    for (row = previous_top; row < top; ++row)
        memcpy(background_bitmap + row * BACKGROUND_WIDTH, empty_row,
                    BACKGROUND_WIDTH);
    for (row = bottom + 1; row <= previous_bottom; ++row)
        memcpy(background_bitmap + row * BACKGROUND_WIDTH, empty_row,
                    BACKGROUND_WIDTH);
}

/* S2 Body D, widened toward the full cast: EVERY active street alien
 * carries a real animation record (avsp_anim_frame_tick over the shipped
 * spans) and produces its semantic object list each frame through the
 * proven decoder (avsp_emit_pose_view over the generated ROM windows).
 * Coverage boundary, stated plainly: the ROM path runs for street aliens
 * in their WALK and ATTACK actions only, using the same two live-verified
 * script seeds Body D shipped; hit/KO/spawn actions and stalkers fall
 * back to the capture cels.
 *
 * tools/gen_avsp_action_seeds.py mined a real (actor_type, action ->
 * record) table from the captures (data/avsp_action_seeds.json), but it
 * is NOT wired here: its key is the game's OWN action word at actor
 * +0x06, a different space from this model's CapAction enum, and no
 * translation between the two exists yet - inventing one would be a
 * guess, not a measurement. That table becomes usable once S5 supplies
 * the real action-selection logic (which naturally produces the ROM
 * action word instead of the model's enum); until then it is decoded
 * evidence, not a wireable bridge. Of 42 mined keys only 16 were
 * unanimous across every observed re-point; the rest showed the game
 * choosing among per-instance variants this table doesn't yet resolve,
 * and were withheld rather than guessed.
 *
 * Pose seeding on action change is ADAPTED from the capability model's
 * action enum; the coordinate/anchor mapping between model space and
 * CPS2 world space is ADAPTED likewise; the per-slot palette follows the
 * corpus-observed street bank set 0x10..0x13 through the model's variant
 * field (ADAPTED). */
static AvspAnimScript rom_actor_script;
static AvspRomView rom_actor_view;
static AvspAnimFrame rom_actor_frames[CAP_MAX_ENEMIES];
static AvspActor rom_actor_collision_views[CAP_MAX_ENEMIES];
static unsigned char rom_actor_seeded[CAP_MAX_ENEMIES];
static int rom_actor_last_actions[CAP_MAX_ENEMIES];
static unsigned long rom_actor_last_records[CAP_MAX_ENEMIES];
static AvspObjectEntry rom_actor_entries_all[CAP_MAX_ENEMIES][16];
static int rom_actor_entry_counts[CAP_MAX_ENEMIES];
static unsigned short rom_actor_emit_world_x[CAP_MAX_ENEMIES];
static unsigned short rom_actor_emit_world_y[CAP_MAX_ENEMIES];
/* HUD/back-compat aggregates: total entries and the first live code. */
static int rom_actor_entry_count = 0;
static AvspObjectEntry rom_actor_entries[16];
/* Step 3 collision diagnostics, both per-frame and cumulative.
 *
 * NH counts the MEASURED cannot-be-hit verdict: the live record advertises a
 * hurt selector of 0, which the game rejects before any table read. That is a
 * real rule, so it is honored with no fallback to the point approximation.
 *
 * GAP counts the opposite case - a ROM-driven slot for which this frame
 * produced NO measured verdict at all (a pose outside the two street loops,
 * an unresolvable record, or a selector the decoded family cannot resolve).
 * A missing measurement is not evidence of invulnerability, so those frames
 * keep the pre-existing ADAPTED point approximation; the counter is what keeps
 * the gap visible instead of silent. */
static volatile int rom_collision_no_hurt;
static volatile int rom_collision_no_hurt_frame;
static volatile int rom_collision_gap;
static volatile int rom_collision_gap_frame;
static volatile int rom_class_lookup_miss;
static volatile int rom_class_lookup_miss_frame;

/* Resolve the record, emitted objects and collision view that BOTH gameplay
 * and rendering consume this frame. Animation advancement is deliberately in
 * rom_actor_advance() after draw_world(), so collision and pixels cannot see
 * adjacent records. */
static void rom_actor_prepare(void)
{
    int index;
    AvspEmitActor state;

    rom_actor_entry_count = 0;
    rom_collision_no_hurt_frame = 0;
    rom_collision_gap_frame = 0;
    rom_class_lookup_miss_frame = 0;
    /* The ROM collision view is valid only for ROM-driven street aliens in the
     * two street-wave states; zero it for every slot each frame so the point
     * approximation applies everywhere else (capture-cel actors, boss, etc.). */
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        memset(&rom_actor_collision_views[index], 0, sizeof(AvspActor));
        world.enemies[index].rom_street_alien = 0;
        world.enemies[index].rom_can_hit = 0;
        world.enemies[index].rom_box_x_lo = 0;
        world.enemies[index].rom_box_x_hi = 0;
    }
    /* Run only in the two street-wave combat states: outside them enemy
     * slots can be mid-initialization, and a reported freeze at the
     * character-confirm transition traced to ticking against one. */
    if (world.encounter_state != CAP_ENCOUNTER_WAVE_ONE &&
        world.encounter_state != CAP_ENCOUNTER_WAVE_TWO)
    {
        for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        {
            rom_actor_seeded[index] = 0;
            rom_actor_entry_counts[index] = 0;
        }
        return;
    }
    if (rom_actor_script.spans == 0)
    {
        rom_actor_script.rom = 0;
        rom_actor_script.base = 0;
        rom_actor_script.size = 0;
        rom_actor_script.spans = avsp_anim_spans;
        rom_actor_script.span_count = avsp_anim_span_count;
        rom_actor_view.spans = avsp_emit_windows;
        rom_actor_view.span_count = AVSP_EMIT_WINDOW_COUNT;
    }
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world.enemies[index];
        unsigned int seed;
        int n;

        rom_actor_entry_counts[index] = 0;
        if (!enemy->active || enemy->kind != CAP_ACTOR_ALIEN)
        {
            rom_actor_seeded[index] = 0;
            continue;
        }
        if (enemy->action != CAP_ACT_WALK &&
            enemy->action != CAP_ACT_ATTACK
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
            && enemy->action != CAP_ACT_HIT &&
            enemy->action != CAP_ACT_KO
#endif
            )
        {
            /* No ROM record is driven outside the two street loops (hit, KO,
             * idle, spawn), so this frame has NO measured hit geometry for the
             * slot. It keeps the ADAPTED point approximation: silence about a
             * pose is not a measurement that it cannot be hit, and inventing a
             * 36-frame hitstun invulnerability out of missing data would be a
             * fabricated rule. Per-state ROM coverage needs the state-dispatch
             * decode first (see the active task card in project_state.yaml). */
            rom_actor_seeded[index] = 0;
            ++rom_collision_gap;
            ++rom_collision_gap_frame;
            continue;
        }
        /* ADAPTED action bridge: the two live-verified street-alien loops. */
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
#ifdef AVSP_PLAYABLE_SLICE
        seed = (unsigned int)
            playable_slice_frame.scene.enemy_identity.animation_record;
#else
        if (enemy->action == CAP_ACT_HIT || enemy->action == CAP_ACT_KO)
            seed = avsp_diag_combat_enemy_render_anim_record;
        else
            seed = (enemy->action == CAP_ACT_ATTACK) ? 0x12D8A0u : 0x12EB4Cu;
#endif
#else
        seed = (enemy->action == CAP_ACT_ATTACK) ? 0x12D8A0u : 0x12EB4Cu;
#endif
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
#ifdef AVSP_PLAYABLE_SLICE
        if (!rom_actor_seeded[index] ||
            rom_actor_last_records[index] != seed)
#else
        if ((enemy->action == CAP_ACT_HIT || enemy->action == CAP_ACT_KO) &&
            (!rom_actor_seeded[index] ||
             rom_actor_last_records[index] != seed))
#endif
        {
            avsp_anim_frame_start(&rom_actor_frames[index],
                                  &rom_actor_script, seed);
            rom_actor_seeded[index] = 1;
            rom_actor_last_actions[index] = (int)enemy->action;
            rom_actor_last_records[index] = seed;
        }
        else
#endif
        if (!rom_actor_seeded[index] ||
            (int)enemy->action != rom_actor_last_actions[index])
        {
            avsp_anim_frame_start(&rom_actor_frames[index],
                                  &rom_actor_script, seed);
            rom_actor_seeded[index] = 1;
            rom_actor_last_actions[index] = (int)enemy->action;
            rom_actor_last_records[index] = seed;
        }
        if (!rom_actor_frames[index].pose.valid) continue;
        /* ADAPTED coordinate bridge: model-space camera as the anchor pair
         * so decoded X approximates screen position. */
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
#ifndef AVSP_PLAYABLE_SLICE
        if (enemy->action == CAP_ACT_HIT || enemy->action == CAP_ACT_KO)
        {
            AvspPortV2CombatSourceEvent combat_source;
            int combat_index = avsp_diag_combat_enemy_source_event_index;
            if (!avsp_port_v2_combat_source_event(
                    combat_index, &combat_source))
            {
                ++rom_collision_gap;
                ++rom_collision_gap_frame;
                continue;
            }
            state.world_x = (unsigned short)
                avsp_diag_combat_enemy_source_world_x;
            state.world_y = (unsigned short)
                avsp_diag_combat_enemy_source_world_y;
        }
        else
#endif
#endif
        {
            state.world_x = (unsigned short)enemy->x;
            state.world_y = (unsigned short)(200 + enemy->height);
        }
        rom_actor_emit_world_x[index] = state.world_x;
        rom_actor_emit_world_y[index] = state.world_y;
        state.facing = (unsigned char)(enemy->facing < 0 ? 1 : 0);
        state.palette = (unsigned char)(0x10 + (enemy->variant & 3));
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
#ifdef AVSP_PLAYABLE_SLICE
        state.palette = (unsigned char)
            playable_slice_frame.scene.enemy_identity.palette_bank;
#else
        if (enemy->action == CAP_ACT_HIT || enemy->action == CAP_ACT_KO)
            state.palette = (unsigned char)
                avsp_diag_combat_enemy_render_palette;
#endif
#endif
        state.mode = 1;
        state.or_value = 0x8000;
        state.anchor_x = (unsigned short)world.camera_x;
        state.anchor_y = 0x00FF;
        n = avsp_emit_pose_view(&rom_actor_view,
                                rom_actor_frames[index].pose.assembly,
                                &state, rom_actor_entries_all[index], 16);
        rom_actor_entry_counts[index] = (n > 0) ? n : 0;
        if (rom_actor_entry_counts[index] > 0 && rom_actor_entry_count == 0)
            rom_actor_entries[0] = rom_actor_entries_all[index][0];
        rom_actor_entry_count += rom_actor_entry_counts[index];
        /* S4: the DEFENDER's MEASURED hurt box. sel_hurt is the live
         * animation record's byte +8 (byte +9, sel_attack, is the attacker
         * side and is deferred - the player has no ROM record yet). The X
         * centre is resolved in the same ADAPTED model-space world_x/facing
         * the emitter above used, so it is comparable to the player's reach in
         * cap_resolve_player_hit. The canonical AvspActor below is also the
         * single source for record, selectors and collision table this frame. */
        {
            const unsigned char *rec = avsp_anim_resolve(&rom_actor_script,
                                                         rom_actor_frames[index].addr,
                                                         10);
            unsigned char sel_hurt = (rec != 0) ? rec[8] : 0u;
            unsigned char sel_attack = (rec != 0) ? rec[9] : 0u;
            AvspActor *view = &rom_actor_collision_views[index];
            AvspBox hurt;

            /* Class 0x1F is assigned only on this validated street-alien path.
             * The approximate model does not produce source sub_state or
             * action_word values, so those remain zero/unresolved rather than
             * fabricating class 0x00/0x06 transitions. */
            view->state = 1u;
            view->class_id = 0x1Fu;
            view->type = 0x0Cu;
            view->facing = state.facing;
            view->world_x = state.world_x;
            view->world_y = state.world_y;
            view->world_z = (unsigned short)enemy->lane;
            view->anim_record = (unsigned long)rom_actor_frames[index].addr;
            view->sel_hurt = sel_hurt;
            view->sel_attack = sel_attack;
            if (!avsp_table_set_for_class(view->class_id, &view->table_set))
            {
                ++rom_class_lookup_miss;
                ++rom_class_lookup_miss_frame;
                ++rom_collision_gap;
                ++rom_collision_gap_frame;
                continue;
            }
            /* rom_street_alien is set ONLY where this frame produced a measured
             * verdict, so cap_resolve_player_hit leaves every other frame on the
             * ADAPTED approximation rather than on an invented invulnerability. */
            if (rec != 0 && sel_hurt == 0u)
            {
                /* MEASURED cannot-be-hit: the game rejects selector 0 before
                 * any table read. Honor it with no fallback, and count it. */
                enemy->rom_street_alien = 1;
                enemy->rom_can_hit = 0;
                ++rom_collision_no_hurt;
                ++rom_collision_no_hurt_frame;
            }
            else if (rec != 0 &&
                     avsp_collision_hurt_box(view->table_set, sel_hurt, &hurt))
            {
                int center = (int)state.world_x +
                             (state.facing ? -(int)hurt.x_center
                                           : (int)hurt.x_center);
                enemy->rom_street_alien = 1;
                enemy->rom_can_hit = 1;
                enemy->rom_box_x_lo = center - (int)hurt.x_half;
                enemy->rom_box_x_hi = center + (int)hurt.x_half;
            }
            else
            {
                /* Unresolvable record, or a selector the decoded family cannot
                 * resolve: a DATA GAP, not a cannot-hit pose. It must not occur
                 * for the checked street class, so it stays on the ADAPTED
                 * approximation and is counted where it can be seen. */
                ++rom_collision_gap;
                ++rom_collision_gap_frame;
            }
        }
    }
}

/* Advance exactly once after the prepared record has been rendered. If the
 * approximate model changed action during cap_world_step(), discard the old
 * program instead; the next frame starts the newly selected ADAPTED seed. */
static void rom_actor_advance(void)
{
    int index;

    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        if (!rom_actor_seeded[index]) continue;
        if (!world.enemies[index].active ||
            world.enemies[index].kind != CAP_ACTOR_ALIEN ||
            (int)world.enemies[index].action != rom_actor_last_actions[index])
        {
            rom_actor_seeded[index] = 0;
            continue;
        }
        avsp_anim_frame_tick(&rom_actor_frames[index], &rom_actor_script);
    }
}

/* S2 Body E: the per-object VDP1 consumer. The ROM actor's semantic object
 * list renders as one 16x16 normal-sprite draw per referenced tile - the
 * measured architecture of the reference Capcom Saturn port (all foreground
 * commands 16x16, 16-colour bank mode, flip in the command, flat draw
 * order) - textured from the cart-resident TILES.BIN archive through a
 * fixed VDP1 pool with in-place LRU replacement. */
static unsigned char *tile_archive_data;
static AvspTileArchive tile_archive;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
static AvspTileArchive combat_tile_archive;
static int combat_tile_archive_ready;
#endif
static jo_palette tile_palette;
static int tile_archive_ready;
static int tile_pool_sprite[AVSP_TILE_SPRITE_POOL];
static long tile_pool_rank[AVSP_TILE_SPRITE_POOL];
static const AvspTileArchive *tile_pool_archive[AVSP_TILE_SPRITE_POOL];
static unsigned long tile_pool_stamp[AVSP_TILE_SPRITE_POOL];
static unsigned long tile_pool_clock;
static int tile_pool_used;
#ifdef AVSP_PROBE3
typedef void (*Probe3InterruptHandler)(void);
typedef void (*Probe3SetScuHandler)(unsigned long, void *);
typedef Probe3InterruptHandler (*Probe3GetScuHandler)(unsigned long);
typedef void (*Probe3ChangeScuMask)(unsigned long, unsigned long);
#define PROBE3_SCU_SPR_VECTOR 0x4DUL
#define PROBE3_SCU_SPR_MASK (1UL << 13)
#define PROBE3_SYS_SET_SCU_HANDLER(n, h) \
    ((*(Probe3SetScuHandler *)0x06000300UL)((n), (void *)(h)))
#define PROBE3_SYS_GET_SCU_HANDLER(n) \
    ((*(Probe3GetScuHandler *)0x06000304UL)(n))
#define PROBE3_SYS_CHANGE_SCU_MASK(and_mask, or_mask) \
    ((*(Probe3ChangeScuMask *)0x06000344UL)((and_mask), (or_mask)))
static volatile unsigned long probe3_copy_count;
static volatile unsigned long probe3_copy_ticks;
static volatile unsigned long probe3_texture_bytes;
static volatile unsigned long probe3_cart_read_bytes;
static volatile unsigned long probe3_cart_source_valid;
static volatile unsigned long probe3_vdp1_destination_valid;
static volatile unsigned long probe3_cart_to_vdp1_path_valid;
static volatile unsigned long probe3_cram_writes_pending;
static volatile unsigned long probe3_vblank_fields;
static volatile unsigned long probe3_vblank_raw;
static volatile unsigned long probe3_vblank_timestamp;
static volatile unsigned long probe3_field_period_ticks;
static volatile unsigned long probe3_draw_end_timestamp;
static volatile unsigned long probe3_draw_end_field_start;
static volatile unsigned long probe3_draw_end_field_period;
static volatile unsigned long probe3_draw_end_field_number;
static volatile unsigned long probe3_draw_end_edsr;
static volatile unsigned long probe3_draw_end_reliable;
static volatile unsigned long probe3_draw_end_armed;
static volatile unsigned long probe3_transfer_start_timestamp;
static volatile unsigned long probe3_transfer_end_timestamp;
static void (*probe3_previous_sprite_irq)(void);
static unsigned long probe3_submission_field_number;
static unsigned long probe3_prepare_start_timestamp;
static unsigned long probe3_prepare_end_timestamp;
static unsigned long probe3_submission_timestamp;
static unsigned long probe3_submitted_draws;
static unsigned long probe3_submitted_mode;
static unsigned long probe3_submitted_checksum;
static unsigned long probe3_submitted_cram_writes;
static unsigned long probe3_submitted_asset_failures;
static int probe3_pending_measurement;
static int probe3_submission_needs_arm;
static int probe3_need_census;
static volatile unsigned long probe3_irq_census_ready;
static AvspProbe3Census probe3_irq_census;
static unsigned long probe3_frame_number;
static unsigned long probe3_soak_start_field_number;
static int probe3_last_mode;
#endif
/* A missing tile or bank is an asset defect, never a silent skip: these
   counters surface on the debug HUD and stay readable by the headless
   debugger (volatile so the release optimizer keeps them). */
static volatile int tile_diag_no_bank;
static volatile int tile_diag_no_rank;
static volatile int tile_diag_no_sprite;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
volatile int avsp_diag_combat_missing_code_count;
volatile unsigned long avsp_diag_combat_missing_codes[16];
volatile int avsp_diag_combat_presented_frame;
volatile int avsp_diag_combat_tile_sprite_misses;
#endif

static int load_tile_archive(void)
{
    int read_bytes;
    int slot;
    int index;
    static jo_color colors[256];

    /* Staged CPU read straight into the carved cartridge region. */
    tile_archive_data = AVSP_CART_DRAM1_BASE;
    read_bytes = avsp_fs_read_into("TILES.BIN", "SPR4", tile_archive_data,
                                   AVSP_TILE_REGION_BYTES);
    if (read_bytes <= 0 ||
        !avsp_tiles_open(&tile_archive, tile_archive_data,
                         (unsigned long)read_bytes))
    {
        failed_asset = "TILES.BIN";
        return 0;
    }
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    {
        int overlay_bytes = avsp_fs_read_into(
            "COMBAT.BIN", "SPR4", tile_archive_data + read_bytes,
            AVSP_TILE_REGION_BYTES - read_bytes);
        if (overlay_bytes <= 0 ||
            !avsp_tiles_open(&combat_tile_archive,
                             tile_archive_data + read_bytes,
                             (unsigned long)overlay_bytes))
        {
            failed_asset = "COMBAT.BIN";
            return 0;
        }
        combat_tile_archive_ready = 1;
    }
#endif
    /* Pixel value p+1 reads palette array entry p after Jo's CRAM base+1
       shift, so slot colours transcribe directly. */
    for (index = 0; index < 256; ++index) colors[index] = JO_COLOR_Black;
    for (slot = 0; slot < (int)tile_archive.palette_slots; ++slot)
        for (index = 0; index < 15; ++index)
            colors[slot * 16 + index] = (jo_color)
                avsp_tiles_cram_color(&tile_archive, slot, index);
    jo_create_palette_from(&tile_palette, colors, AVSP_CRAM_MAX_COLOURS);
#ifdef AVSP_PROBE3
    probe3_cram_writes_pending = AVSP_CRAM_MAX_COLOURS;
#endif
    tile_pool_used = 0;
    tile_pool_clock = 0;
    tile_archive_ready = 1;
    return 1;
}

static int tile_sprite_for_archive_rank(const AvspTileArchive *archive,
                                        const long rank)
{
    int index;
    int victim = 0;
    jo_img_4bits img;

    for (index = 0; index < tile_pool_used; ++index)
    {
        if (tile_pool_archive[index] == archive &&
            tile_pool_rank[index] == rank)
        {
            tile_pool_stamp[index] = ++tile_pool_clock;
            return tile_pool_sprite[index];
        }
    }
    img.width = 16;
    img.height = 16;
    img.data = (unsigned char *)avsp_tiles_texture(archive, rank);
    if (img.data == JO_NULL) return -1;
#ifdef AVSP_PROBE3
    {
        unsigned long source = (unsigned long)img.data;
        unsigned long archive_start = (unsigned long)archive->data;
        unsigned long archive_end = archive_start + archive->size;
        unsigned int copy_start = (unsigned int)jo_time_get_frc();
        int sprite_id;
        unsigned long destination;
        if (probe3_copy_count == 0UL)
            probe3_transfer_start_timestamp = probe3_vblank_timestamp +
                (((unsigned long)copy_start - probe3_vblank_raw) & 0xFFFFUL);
        if (source < archive_start || source + AVSP_TILE_BYTES > archive_end ||
            archive_start < (unsigned long)AVSP_CART_DRAM1_BASE ||
            archive_end > (unsigned long)(AVSP_CART_DRAM1_BASE +
                                           AVSP_TILE_REGION_BYTES))
            probe3_cart_source_valid = 0;
        if (tile_pool_used < AVSP_TILE_SPRITE_POOL)
        {
            sprite_id = jo_sprite_add_4bits_image(&img);
            if (sprite_id < 0) return -1;
            tile_pool_sprite[tile_pool_used] = sprite_id;
            tile_pool_rank[tile_pool_used] = rank;
            tile_pool_archive[tile_pool_used] = archive;
            tile_pool_stamp[tile_pool_used] = ++tile_pool_clock;
            ++tile_pool_used;
        }
        else
        {
            for (index = 1; index < AVSP_TILE_SPRITE_POOL; ++index)
                if (tile_pool_stamp[index] < tile_pool_stamp[victim])
                    victim = index;
            if (jo_sprite_replace_4bits_image(&img,
                                               tile_pool_sprite[victim]) < 0)
                return -1;
            tile_pool_rank[victim] = rank;
            tile_pool_archive[victim] = archive;
            tile_pool_stamp[victim] = ++tile_pool_clock;
            sprite_id = tile_pool_sprite[victim];
        }
        destination = (unsigned long)JO_VDP1_VRAM +
            (unsigned long)__jo_sprite_def[sprite_id].adr * 8UL;
        if (destination < (unsigned long)JO_VDP1_VRAM +
                JO_VDP1_TEXTURE_DEF_BASE_ADDRESS ||
            destination + AVSP_TILE_BYTES >
                (unsigned long)JO_VDP1_USER_AREA_END_ADDR)
            probe3_vdp1_destination_valid = 0;
        if (!probe3_cart_source_valid || !probe3_vdp1_destination_valid)
            probe3_cart_to_vdp1_path_valid = 0;
        ++probe3_copy_count;
        probe3_texture_bytes += AVSP_TILE_BYTES;
        probe3_cart_read_bytes += AVSP_TILE_BYTES;
        probe3_copy_ticks +=
            ((unsigned int)jo_time_get_frc() - copy_start) & 0xFFFFU;
        probe3_transfer_end_timestamp = probe3_vblank_timestamp +
            (((unsigned long)(unsigned int)jo_time_get_frc() -
              probe3_vblank_raw) & 0xFFFFUL);
        return sprite_id;
    }
#else
    if (tile_pool_used < AVSP_TILE_SPRITE_POOL)
    {
        int sprite_id = jo_sprite_add_4bits_image(&img);
        if (sprite_id < 0) return -1;
        tile_pool_sprite[tile_pool_used] = sprite_id;
        tile_pool_rank[tile_pool_used] = rank;
        tile_pool_archive[tile_pool_used] = archive;
        tile_pool_stamp[tile_pool_used] = ++tile_pool_clock;
        return tile_pool_sprite[tile_pool_used++];
    }
    for (index = 1; index < AVSP_TILE_SPRITE_POOL; ++index)
        if (tile_pool_stamp[index] < tile_pool_stamp[victim]) victim = index;
    if (jo_sprite_replace_4bits_image(&img, tile_pool_sprite[victim]) < 0)
        return -1;
    tile_pool_rank[victim] = rank;
    tile_pool_archive[victim] = archive;
    tile_pool_stamp[victim] = ++tile_pool_clock;
    return tile_pool_sprite[victim];
#endif
}

static int wrap_signed_10bit(int delta)
{
    delta &= 0x3FF;
    if (delta >= 512) delta -= 1024;
    return delta;
}

static int fit_352(const int cps_x)
{
    if (cps_x < 0) return -((-cps_x * CAP_VIEW_WIDTH) / CAP_CPS2_VIEW_WIDTH);
    return (cps_x * CAP_VIEW_WIDTH) / CAP_CPS2_VIEW_WIDTH;
}

static int draw_rom_actor_tiles(const CapActor *actor, const int slot)
{
    /* ADAPTED placement bridge: the emitter ran with model-space anchors
       (rom_actor_prepare), so entries are positioned as offsets from the
       decoded origin and re-anchored at the actor's model screen position;
       exact CPS2 anchor alignment lands with S5's world-space translation.
       The cel pivot convention (pixel 184 of a 192px cel drawn centred at
       lane-200-height) puts the actor's CPS2 origin 88px below the cel
       centre. */
    const int emit_origin_cps_x =
        0x40 + rom_actor_emit_world_x[slot] - world.camera_x;
#ifndef AVSP_PLAYABLE_SLICE
    const int visual_origin_cps_x = 0x40 + actor->x - world.camera_x;
#endif
    const int origin_dec_y =
        (0x100 + 0xFF - rom_actor_emit_world_y[slot]) & 0x3FF;
    const int anchor_jo_y = actor->lane - 200 - actor->height + 88;
    const int depth = 330 - actor->lane;
    int index;
    int rendered = 0;
#if defined(AVSP_PLAYABLE_SLICE) || defined(AVSP_COMBAT_INTEGRATION_BENCH)
    unsigned long object_identity = 2166136261UL;
    unsigned long tile_identity = 2166136261UL;
#endif
#ifdef AVSP_PLAYABLE_SLICE
    avsp_diag_slice_enemy_object_count = rom_actor_entry_counts[slot];
#elif defined(AVSP_COMBAT_INTEGRATION_BENCH)
    avsp_diag_combat_enemy_render_object_count =
        rom_actor_entry_counts[slot];
#endif

    jo_sprite_set_palette_4bits(tile_palette.id, 0);
    for (index = rom_actor_entry_counts[slot] - 1; index >= 0; --index)
    {
        const AvspObjectEntry *entry = &rom_actor_entries_all[slot][index];
        AvspEntryTile tiles[64];
        int offset_x = wrap_signed_10bit((int)(entry->x & 0x3FF) -
                                         (emit_origin_cps_x & 0x3FF));
        int offset_y = wrap_signed_10bit((int)(entry->y & 0x3FF) -
                                         origin_dec_y);
        int bank_slot = avsp_tiles_bank_slot(&tile_archive,
                                             entry->attr & 0x1F);
        int count = avsp_entry_tiles(entry->y, entry->code, entry->attr,
                                     tiles, 64);
        int tile;
#if defined(AVSP_PLAYABLE_SLICE) || \
    defined(AVSP_COMBAT_INTEGRATION_BENCH)
        /* Identity is source-pose local.  Screen/world placement belongs to
         * the shared camera transform and must not change the source object
         * family contract. */
        object_identity = (object_identity ^
                           (unsigned short)offset_x) * 16777619UL;
        object_identity = (object_identity ^
                           (unsigned short)offset_y) * 16777619UL;
        object_identity = (object_identity ^ entry->code) * 16777619UL;
        object_identity = (object_identity ^ entry->attr) * 16777619UL;
#endif
        if (count <= 0 || bank_slot < 0)
        {
            ++tile_diag_no_bank;
            continue;
        }
        jo_sprite_set_palette_4bits(tile_palette.id, bank_slot);
        for (tile = 0; tile < count; ++tile)
        {
            const AvspTileArchive *source_archive = &tile_archive;
            long rank = avsp_tiles_find(&tile_archive, tiles[tile].code);
            int sprite_id;
            int jo_x;
            int jo_y;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
            if (rank < 0 && combat_tile_archive_ready)
            {
                source_archive = &combat_tile_archive;
                rank = avsp_tiles_find(source_archive, tiles[tile].code);
            }
#endif
            if (rank < 0)
            {
                ++tile_diag_no_rank;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
                if (avsp_diag_combat_missing_code_count < 16)
                    avsp_diag_combat_missing_codes[
                        avsp_diag_combat_missing_code_count++] =
                        tiles[tile].code;
#endif
                continue;
            }
            sprite_id = tile_sprite_for_archive_rank(source_archive, rank);
            if (sprite_id < 0)
            {
                ++tile_diag_no_sprite;
                continue;
            }
#ifdef AVSP_PLAYABLE_SLICE
            jo_x = playable_slice_frame.scene.enemy_screen_x +
                fit_352(offset_x + tiles[tile].dx + 8);
#else
            jo_x = fit_352(visual_origin_cps_x - 256 + offset_x +
                           tiles[tile].dx + 8);
#endif
#if defined(AVSP_PLAYABLE_SLICE) || defined(AVSP_COMBAT_INTEGRATION_BENCH)
            tile_identity =
                (tile_identity ^ tiles[tile].code) * 16777619UL;
#endif
            jo_y = anchor_jo_y + offset_y + tiles[tile].dy + 8;
            if (tiles[tile].flip_x) jo_sprite_enable_horizontal_flip();
            if (tiles[tile].flip_y) jo_sprite_enable_vertical_flip();
            jo_sprite_draw3D(sprite_id, jo_x, jo_y, depth);
            ++rendered;
            if (tiles[tile].flip_x) jo_sprite_disable_horizontal_flip();
            if (tiles[tile].flip_y) jo_sprite_disable_vertical_flip();
        }
    }
#ifdef AVSP_PLAYABLE_SLICE
    avsp_diag_slice_enemy_object_identity = (int)object_identity;
    avsp_diag_slice_enemy_tile_identity = (int)tile_identity;
#elif defined(AVSP_COMBAT_INTEGRATION_BENCH)
    avsp_diag_combat_enemy_render_object_identity = object_identity;
    avsp_diag_combat_enemy_render_tile_identity = tile_identity;
#endif
    return rendered;
}

#ifdef AVSP_PROBE3
static int probe3_decode_coordinate(const int value)
{
    int decoded = value & 0x3FF;
    if (decoded >= 512) decoded -= 1024;
    return decoded;
}

static void probe3_vblank_callback(void)
{
    unsigned long raw = (unsigned long)(unsigned int)jo_time_get_frc();
    unsigned long delta = (raw - probe3_vblank_raw) & 0xFFFFUL;
    if (probe3_vblank_fields != 0UL)
    {
        probe3_vblank_timestamp += delta;
        probe3_field_period_ticks = delta;
    }
    else probe3_vblank_timestamp = raw;
    probe3_vblank_raw = raw;
    ++probe3_vblank_fields;
}

static unsigned long probe3_timestamp_now(void)
{
    unsigned long raw = (unsigned long)(unsigned int)jo_time_get_frc();
    return probe3_vblank_timestamp + ((raw - probe3_vblank_raw) & 0xFFFFUL);
}

/* Probe-only wrapper around the SCU sprite-drawing-finished vector.  Capture
 * before chaining so the timestamp is the first software observation of the
 * actual hardware event; SGL's installed handler remains in the path. */
static void probe3_sprite_draw_end_irq(void)
{
    if (probe3_draw_end_armed && !probe3_draw_end_reliable)
    {
        probe3_draw_end_timestamp = probe3_timestamp_now();
        probe3_draw_end_field_start = probe3_vblank_timestamp;
        probe3_draw_end_field_period = probe3_field_period_ticks;
        probe3_draw_end_field_number = probe3_vblank_fields;
        probe3_draw_end_edsr = JO_VDP1_EDSR;
        probe3_draw_end_reliable = 1UL;
        probe3_draw_end_armed = 0UL;
    }
    if (probe3_previous_sprite_irq != JO_NULL)
        probe3_previous_sprite_irq();
}

static void probe3_invalidate_texture_cache(void)
{
    int index;
    for (index = 0; index < tile_pool_used; ++index)
    {
        tile_pool_rank[index] = -1;
        tile_pool_archive[index] = JO_NULL;
        tile_pool_stamp[index] = 0;
    }
    tile_pool_clock = 0;
}

static int probe3_draw_schedule(const AvspProbe3Schedule *schedule)
{
    int object_index;
    int drawn = 0;
    for (object_index = (int)schedule->object_count - 1;
         object_index >= 0; --object_index)
    {
        const AvspProbe3Object *object = &schedule->objects[object_index];
        AvspEntryTile tiles[256];
        int bank_slot = avsp_tiles_bank_slot(&tile_archive,
                                             object->attr & 0x1F);
        int tile_count = avsp_entry_tiles(object->y, object->code,
                                          object->attr, tiles, 256);
        int x = probe3_decode_coordinate((object->x + 0x40) & 0x3FF);
        int y = probe3_decode_coordinate((0x100 - object->y) & 0x3FF);
        int priority = (object->x >> 13) & 7;
        int tile_index;
        if (bank_slot < 0 || tile_count <= 0)
        {
            ++tile_diag_no_bank;
            continue;
        }
        jo_sprite_set_palette_4bits(tile_palette.id, bank_slot);
        for (tile_index = 0; tile_index < tile_count; ++tile_index)
        {
            long rank = avsp_tiles_find(&tile_archive,
                                        tiles[tile_index].code);
            int sprite_id;
            int jo_x;
            int jo_y;
            if (rank < 0)
            {
                ++tile_diag_no_rank;
                continue;
            }
            sprite_id = tile_sprite_for_archive_rank(&tile_archive, rank);
            if (sprite_id < 0)
            {
                ++tile_diag_no_sprite;
                continue;
            }
            jo_x = fit_352(x - CAP_CPS2_VIEW_WIDTH / 2 +
                           tiles[tile_index].dx + 8);
            jo_y = y - 112 + tiles[tile_index].dy + 8;
            if (tiles[tile_index].flip_x)
                jo_sprite_enable_horizontal_flip();
            if (tiles[tile_index].flip_y)
                jo_sprite_enable_vertical_flip();
            jo_sprite_draw3D(sprite_id, jo_x, jo_y, 360 - priority * 8);
            ++drawn;
            if (tiles[tile_index].flip_x)
                jo_sprite_disable_horizontal_flip();
            if (tiles[tile_index].flip_y)
                jo_sprite_disable_vertical_flip();
        }
    }
    return drawn;
}

static void probe3_frame_callback(void)
{
    const AvspProbe3Schedule *schedule;

    if (!runtime_ready || avsp_probe3_telemetry.status ==
        PROBE3_STATUS_FAILED)
    {
        jo_clear_screen();
        jo_printf(2, 3, "PROBE 3 FAILED %lu",
                  avsp_probe3_telemetry.failure_reason);
        jo_printf(2, 5, "PHYSICAL SATURN UNRUN");
        return;
    }

    if (probe3_pending_measurement && !probe3_draw_end_reliable)
    {
        /* slSynch can return before the Probe-only SCU draw-end wrapper has
         * observed the just-submitted list.  Do not consume stale timestamp
         * fields or submit a replacement list while this one is pending. */
        if (probe3_vblank_fields - probe3_submission_field_number > 4UL)
            avsp_probe3_fail(PROBE3_FAILURE_DRAW_END_TIMESTAMP);
        return;
    }

    if (probe3_pending_measurement)
    {
        AvspProbe3DeadlineObservation observation;
        AvspProbe3Census census;
        unsigned long draw_elapsed = 0UL;
        unsigned long margin = 0UL;
        unsigned long total_elapsed = 0UL;
        unsigned long total_budget = 0UL;
        unsigned long total_margin = 0UL;
        unsigned long period = probe3_draw_end_field_period;
        unsigned long field_delta = probe3_draw_end_field_number -
            probe3_submission_field_number;
        if (probe3_draw_end_timestamp >= probe3_draw_end_field_start)
            draw_elapsed = probe3_draw_end_timestamp -
                probe3_draw_end_field_start;
        if (period > draw_elapsed) margin = period - draw_elapsed;
        if (probe3_draw_end_timestamp >= probe3_prepare_start_timestamp)
            total_elapsed = probe3_draw_end_timestamp -
                probe3_prepare_start_timestamp;
        total_budget = period * 2UL;
        if (total_budget > total_elapsed)
            total_margin = total_budget - total_elapsed;

        avsp_probe3_telemetry.mode = probe3_submitted_mode;
        avsp_probe3_telemetry.frame_number = ++probe3_frame_number;
        avsp_probe3_telemetry.workload_checksum_word =
            probe3_submitted_checksum;
        avsp_probe3_telemetry.requested_workload_tile_draws =
            avsp_probe3_schedule()->reachable_commands;
        avsp_probe3_telemetry.submitted_workload_draw_calls =
            probe3_submitted_draws;
        avsp_probe3_telemetry.vdp1_draw_end_state = probe3_draw_end_edsr;
        avsp_probe3_telemetry.draw_end_deadline_fields =
            probe3_submitted_mode == PROBE3_OVERLOAD ? 0UL : 1UL;
        avsp_probe3_telemetry.field_delta = field_delta;
        avsp_probe3_telemetry.field_start_timestamp =
            probe3_draw_end_field_start;
        avsp_probe3_telemetry.field_period_ticks = period;
        avsp_probe3_telemetry.timer_calibration_field_ticks = period;
        avsp_probe3_telemetry.cpu_prepare_start_timestamp =
            probe3_prepare_start_timestamp;
        avsp_probe3_telemetry.cpu_prepare_end_timestamp =
            probe3_prepare_end_timestamp;
        avsp_probe3_telemetry.transfer_start_timestamp =
            probe3_transfer_start_timestamp;
        avsp_probe3_telemetry.transfer_end_timestamp =
            probe3_transfer_end_timestamp;
        avsp_probe3_telemetry.submission_timestamp =
            probe3_submission_timestamp;
        avsp_probe3_telemetry.draw_end_timestamp = probe3_draw_end_timestamp;
        avsp_probe3_telemetry.draw_end_timestamp_reliable =
            probe3_draw_end_reliable;
        avsp_probe3_telemetry.draw_end_margin_ticks = margin;
        avsp_probe3_telemetry.draw_end_margin_percent_x100 = period == 0UL ?
            0UL : (margin * 10000UL) / period;
        avsp_probe3_telemetry.total_frame_margin_ticks = total_margin;
        avsp_probe3_telemetry.total_frame_margin_percent_x100 =
            total_budget == 0UL ? 0UL :
            (total_margin * 10000UL) / total_budget;
        avsp_probe3_telemetry.timer_wrapped =
            ((probe3_draw_end_timestamp & 0xFFFFUL) <
             (probe3_prepare_start_timestamp & 0xFFFFUL)) ? 1UL : 0UL;
        avsp_probe3_telemetry.texture_bytes_copied = probe3_texture_bytes;
        avsp_probe3_telemetry.copy_count = probe3_copy_count;
        avsp_probe3_telemetry.copy_ticks = probe3_copy_ticks;
        avsp_probe3_telemetry.cart_texture_source_valid =
            probe3_cart_source_valid;
        avsp_probe3_telemetry.vdp1_texture_destination_valid =
            probe3_vdp1_destination_valid;
        avsp_probe3_telemetry.cart_to_vdp1_path_valid =
            probe3_cart_to_vdp1_path_valid;
        avsp_probe3_telemetry.cram_writes = probe3_submitted_cram_writes;
        avsp_probe3_telemetry.cartridge_read_bytes =
            probe3_cart_read_bytes;
        avsp_probe3_telemetry.asset_failures =
            probe3_submitted_asset_failures;
        if (field_delta == 0UL) {
            ++avsp_probe3_telemetry.repeated_fields;
            if (avsp_probe3_telemetry.phase == PROBE3_PHASE_SOAK)
                ++avsp_probe3_telemetry.soak_repeated_fields;
        } else if (field_delta > 1UL) {
            avsp_probe3_telemetry.skipped_fields += field_delta - 1UL;
            if (avsp_probe3_telemetry.phase == PROBE3_PHASE_SOAK)
                avsp_probe3_telemetry.soak_skipped_fields += field_delta - 1UL;
        }

        observation.detector_enabled =
            avsp_probe3_telemetry.detector_enabled;
        observation.draw_end_observed = probe3_draw_end_reliable;
        observation.draw_end_reliable = probe3_draw_end_reliable;
        observation.field_delta = field_delta;
        observation.deadline_fields =
            avsp_probe3_telemetry.draw_end_deadline_fields;
        observation.draw_elapsed_ticks = draw_elapsed;
        observation.field_period_ticks = period;
        observation.soak_elapsed_fields = 0UL;
        probe3_pending_measurement = 0;
        if (probe3_need_census)
        {
            if (!probe3_irq_census_ready)
            {
                avsp_probe3_fail(PROBE3_FAILURE_COMMAND_TABLE);
                return;
            }
            census = probe3_irq_census;
            avsp_probe3_record_precheck(&observation, &census);
            if (avsp_probe3_telemetry.phase == PROBE3_PHASE_SOAK)
                probe3_soak_start_field_number = probe3_vblank_fields;
        }
        else
        {
            /* A ten-minute soak is 36,000 elapsed NTSC VBlank fields, not
             * 36,000 completed workloads.  Draw-end field_delta can be zero
             * when submission and IRQ land within one field, so summing it
             * undercounts real elapsed time. */
            observation.soak_elapsed_fields = probe3_vblank_fields -
                probe3_soak_start_field_number;
            avsp_probe3_record_soak(&observation);
        }
        probe3_draw_end_reliable = 0UL;
        probe3_need_census = 0;
    }

    if (avsp_probe3_telemetry.complete)
    {
        jo_clear_screen();
        jo_printf(2, 3, "PROBE 3 READY FOR PHYSICAL");
        jo_printf(2, 5, "WORK REP %lu PEAK %lu OVL %lu",
                  avsp_probe3_telemetry.
                    representative_workload_tile_draw_high_water,
                  avsp_probe3_telemetry.peak_workload_tile_draw_high_water,
                  avsp_probe3_telemetry.overload_tripped);
        jo_printf(2, 7, "SOAK %lu/%lu MIN %lu.%02lu%%",
                  avsp_probe3_telemetry.soak_elapsed_fields,
                  avsp_probe3_telemetry.soak_target_fields,
                  avsp_probe3_telemetry.soak_min_draw_margin_percent_x100 / 100UL,
                  avsp_probe3_telemetry.soak_min_draw_margin_percent_x100 % 100UL);
        jo_printf(2, 9, "MISS %lu LATE %lu CANARY %lu",
                  avsp_probe3_telemetry.soak_missed_fields,
                  avsp_probe3_telemetry.soak_late_lists,
                  avsp_probe3_telemetry.canary_state);
        jo_printf(2, 11, "SUMMARY %08lX",
                  avsp_probe3_telemetry.summary_checksum);
        jo_printf(2, 13, "PHYSICAL SATURN UNRUN");
        return;
    }

    if (probe3_last_mode != (int)avsp_probe3_telemetry.mode)
    {
        probe3_invalidate_texture_cache();
        probe3_last_mode = (int)avsp_probe3_telemetry.mode;
    }
    schedule = avsp_probe3_schedule();
    probe3_copy_count = 0;
    probe3_copy_ticks = 0;
    probe3_texture_bytes = 0;
    probe3_cart_read_bytes = 0;
    probe3_cart_source_valid = 1UL;
    probe3_vdp1_destination_valid = 1UL;
    probe3_cart_to_vdp1_path_valid = 1UL;
    tile_diag_no_bank = 0;
    tile_diag_no_rank = 0;
    tile_diag_no_sprite = 0;
    probe3_submitted_cram_writes = probe3_cram_writes_pending;
    probe3_cram_writes_pending = 0;
    probe3_transfer_start_timestamp = probe3_timestamp_now();
    probe3_transfer_end_timestamp = probe3_transfer_start_timestamp;
    probe3_prepare_start_timestamp = probe3_timestamp_now();
    probe3_submitted_draws = (unsigned long)probe3_draw_schedule(schedule);
    probe3_prepare_end_timestamp = probe3_timestamp_now();
    probe3_submitted_asset_failures =
        (unsigned long)(tile_diag_no_bank + tile_diag_no_rank +
                        tile_diag_no_sprite);
    probe3_submitted_mode = avsp_probe3_telemetry.mode;
    probe3_submitted_checksum = schedule->checksum_word;
    probe3_pending_measurement = 1;
    probe3_submission_needs_arm = 1;
    probe3_need_census = avsp_probe3_telemetry.phase != PROBE3_PHASE_SOAK;
    probe3_irq_census_ready = 0UL;
    if (probe3_need_census)
        avsp_probe3_telemetry.phase = PROBE3_PHASE_PRECHECK_VALIDATE;
}

static void probe3_run_loop(void)
{
    for (;;)
    {
        probe3_frame_callback();
        slSynch();
        if (probe3_submission_needs_arm)
        {
            /* SGL retires the preceding list and submits the draw calls
             * queued by probe3_frame_callback inside slSynch.  Arm only
             * after that return so the next sprite-draw-end IRQ belongs to
             * this workload rather than to the preceding SGL list. */
            probe3_submission_timestamp = probe3_timestamp_now();
            probe3_submission_field_number = probe3_vblank_fields;
            if (probe3_need_census)
            {
                /* Census the finalized submission before VDP1 can rewrite
                 * its active END marker onto the first workload command at
                 * draw completion.  The IRQ remains the sole timing source;
                 * this snapshot is the authoritative submitted topology. */
                avsp_probe3_census(
                    (const volatile unsigned short *)JO_VDP1_VRAM,
                    AVSP_PROBE3_VDP1_TABLE_BYTES, probe3_submitted_draws,
                    &probe3_irq_census);
                probe3_irq_census.submitted_workload_draw_calls =
                    probe3_submitted_draws;
                probe3_irq_census_ready = 1UL;
            }
            probe3_draw_end_reliable = 0UL;
            probe3_draw_end_armed = 1UL;
            probe3_submission_needs_arm = 0;
        }
    }
}
#endif


#ifdef AVSP_STREET_TEST
/* ---- RP4 representative street interval (source frames 3474-3674) ----
 *
 * Plays the STRIPS.BIN bundle generated by tools/gen_avsp_street_planes.py:
 * scroll3 on NBG1 and scroll2 on NBG0 as VDP2 cell planes built offline
 * from ROM tiles at the shared endpoint-aligned 384-to-352 pre-scale,
 * per-frame independent scroll from the captured CPS-A registers, the
 * measured bank-1 palette cycle as CRAM rewrites, the measured map-cell
 * animation as pattern-name updates, and the recorded object schedule
 * through the same avsp_entry_tiles VDP1 path gameplay uses. */

#define STREET_NBG0_CEL ((unsigned char *)VDP2_VRAM_A0)
#define STREET_NBG1_CEL ((unsigned char *)VDP2_VRAM_A1)
#define STREET_NBG0_PNT ((unsigned short *)VDP2_VRAM_B0)
#define STREET_NBG1_PNT ((unsigned short *)(VDP2_VRAM_B0 + 0x4000))
#define STREET_PAGE_WORDS 0x1000 /* one 64x64 1-word pattern page */

extern void slPageNbg0(void *, void *, Uint16);
extern void slMapNbg0(void *, void *, void *, void *);
extern void slPlaneNbg0(Uint16);
extern void slScrPosNbg0(FIXED, FIXED);
extern void slColRAMOffsetNbg0(Uint16);
extern void slColRAMOffsetNbg1(Uint16);
/* SGL's SL_DEF.H (in scope through the Jo/SGL include chain) already
   defines the sprite-class screen selectors; keep guarded fallbacks so
   the values (-8, -5) stay pinned to the measured registers. */
#ifndef scnSPR1
#define scnSPR1 (-8)
#endif
#ifndef scnSPR2
#define scnSPR2 (-5)
#endif

typedef struct
{
    int cell_cols;
    int cell_rows;
    int world_x0;
    int row0;
    int char_count;
    unsigned long char_offset;
    unsigned long pnt_offset;
} StreetPlane;

static unsigned char *street_data;
static long street_bytes;
static int street_ready;
static int street_frames;
static StreetPlane street_plane[2];
static unsigned long street_scroll_offset;
static unsigned long street_patch_offset;
static unsigned long street_objects_offset;
static int street_cycle_period;
static int street_cycle_first_flip;
static int street_cycle_entries;
static unsigned long street_cycle_offset;
static jo_palette street_palette[2];
#define STREET_MAX_FRAMES 256
#define STREET_MAX_PATCH_CELLS 64
static unsigned long street_object_frame_offset[STREET_MAX_FRAMES];
static unsigned long street_patch_revert[STREET_MAX_PATCH_CELLS][2];
static int street_patch_revert_count;
volatile int avsp_diag_street_frame;
volatile int avsp_diag_street_scx[2];
volatile int avsp_diag_street_objects;
#if defined(AVSP_CAMERA_STAGE_SALVAGE_BENCH) && \
    !defined(AVSP_CAMERA_STAGE_PROMOTION_BENCH)
static int stage_previous_scx0;
static int stage_previous_scx1;
static int stage_has_previous_scroll;
#endif
#ifdef AVSP_CAMERA_STAGE_PROMOTION_BENCH
static AvspPortV2CameraRuntime stage_camera_runtime;
static AvspPortV2StageRenderOps stage_render_operations;

static int stage_submit_layer(
    const AvspPortV2StageLayerEvent *event)
{
    if (event == 0) return 0;
    if (event->layer_id == 0)
    {
        slColRAMOffsetNbg0((Uint16)event->palette_bank);
        slPriority(scnNBG0, event->priority);
        slScrPosNbg0(toFIXED(event->scroll_x), toFIXED(event->scroll_y));
    }
    else if (event->layer_id == 1)
    {
        slColRAMOffsetNbg1((Uint16)event->palette_bank);
        slPriority(scnNBG1, event->priority);
        slScrPosNbg1(toFIXED(event->scroll_x), toFIXED(event->scroll_y));
    }
    else return 0;
    ++avsp_diag_stage_render_submissions;
    return 1;
}

static int stage_submit_sprite_priorities(const int actor_priority,
                                          const int foreground_priority)
{
    slPriority(scnSPR1, actor_priority);
    slPriority(scnSPR2, foreground_priority);
    ++avsp_diag_stage_render_submissions;
    return 1;
}
#endif

static void street_load_planes(void);

/* CPS object priority -> Saturn sprite priority class. SPCTL is type 3
 * (measured 0x0023): frame-buffer bits 14-13 select the sprite priority
 * register. Jo leaves them zero (class 0, the HUD/default class); the
 * street objects OR class 1 (CPS priority 1, actors) or class 2 (CPS
 * priority 4, foreground) into the colour-bank word, exactly the
 * mechanism the official MSHvSF port was measured to use (0x6000/0x7000
 * prefixes over the 11-bit colour entry). */
#define STREET_SPR_CLASS_ACTOR 0x2000UL
#define STREET_SPR_CLASS_FOREGROUND 0x4000UL
extern jo_sprite_attributes __jo_sprite_attributes;

static void street_object_palette(const int bank_slot, const int priority)
{
    jo_sprite_set_palette_4bits(tile_palette.id, bank_slot);
    __jo_sprite_attributes.color_table_index |=
        priority >= 4 ? STREET_SPR_CLASS_FOREGROUND :
        STREET_SPR_CLASS_ACTOR;
}

static unsigned int street_u16(const unsigned long offset)
{
    return ((unsigned int)street_data[offset] << 8) |
           street_data[offset + 1];
}

static unsigned long street_u32(const unsigned long offset)
{
    return ((unsigned long)street_u16(offset) << 16) |
           street_u16(offset + 2);
}

/* Runtime inverse of the generator's out_of(): the smallest output column
 * whose endpoint-aligned source is at least world_x. */
static int street_out_of(const int world_x)
{
    return avsp_port_v2_camera_source_to_output(world_x);
}

static int street_setup(void)
{
    long read_bytes;
    int plane;
    int index;

    street_data = AVSP_CART_DRAM1_BASE + AVSP_TILE_REGION_BYTES;
    read_bytes = avsp_fs_read_into("STRIPS.BIN", "ST1", street_data,
                                   AVSP_STRIPS_REGION_BYTES);
    if (read_bytes <= 0 || street_u32(0) != 0x41565353UL ||
        street_u16(4) != 1)
    {
        failed_asset = "STRIPS.BIN";
        return 0;
    }
    street_bytes = read_bytes;
    street_frames = (int)street_u16(6);
    if (street_frames <= 0 || street_frames > STREET_MAX_FRAMES)
    {
        failed_asset = "STRIPS FRAMES";
        return 0;
    }
    /* Each plane header is 20 bytes: six u16 fields then two u32s. */
    for (plane = 0; plane < 2; ++plane)
    {
        const unsigned long at = 8 + (unsigned long)plane * 20;
        street_plane[plane].cell_cols = (int)street_u16(at);
        street_plane[plane].cell_rows = (int)street_u16(at + 2);
        street_plane[plane].world_x0 = (int)street_u16(at + 4);
        street_plane[plane].row0 = (int)street_u16(at + 6);
        street_plane[plane].char_count = (int)street_u16(at + 8);
        street_plane[plane].char_offset = street_u32(at + 12);
        street_plane[plane].pnt_offset = street_u32(at + 16);
        if (street_plane[plane].cell_cols <= 0 ||
            street_plane[plane].cell_cols > 128 ||
            street_plane[plane].cell_rows <= 0 ||
            street_plane[plane].cell_rows > 64 ||
            street_plane[plane].char_count <= 0 ||
            street_plane[plane].char_count > 2048 ||
            street_plane[plane].char_offset +
                (unsigned long)street_plane[plane].char_count * 64 >
                (unsigned long)street_bytes ||
            street_plane[plane].pnt_offset +
                (unsigned long)street_plane[plane].cell_cols *
                street_plane[plane].cell_rows * 2 >
                (unsigned long)street_bytes)
        {
            failed_asset = "STRIPS PLANE";
            return 0;
        }
    }

    /* Palettes: two 256-entry blocks; strip pixel i reads block[i], with
       Jo's data pointer starting one entry above the block base. The
       street test REUSES the two frontend scene palette blocks instead of
       allocating new ones: boot already claims every remaining CRAM
       block, and Jo reports out-of-VDP2-memory on a fresh allocation
       (observed live). The frontend surfaces never draw in this mode. */
    for (plane = 0; plane < 2; ++plane)
    {
        const unsigned long at = 48 + (unsigned long)plane * 512;
        street_palette[plane] = frontend_palettes[plane];
        for (index = 1; index < 256; ++index)
            street_palette[plane].data[index - 1] =
                (jo_color)street_u16(at + (unsigned long)index * 2);
    }
    street_cycle_period = (int)street_u16(48 + 1024);
    street_cycle_first_flip = (int)street_u16(48 + 1026);
    street_cycle_entries = (int)street_u16(48 + 1028);
    street_cycle_offset = 48 + 1030;
    street_scroll_offset = street_cycle_offset +
        (unsigned long)street_cycle_entries * 6;
    street_patch_offset = street_scroll_offset +
        (unsigned long)street_frames * 8;
    street_objects_offset = street_patch_offset + 2;
    {
        int patch;
        const int patch_count = (int)street_u16(street_patch_offset);
        unsigned long cursor = street_patch_offset + 2;
        for (patch = 0; patch < patch_count; ++patch)
        {
            const int updates = (int)street_u16(cursor + 4);
            cursor += 6 + (unsigned long)updates * 6;
        }
        street_objects_offset = cursor;
    }
    /* Index every frame's object list once so per-frame lookup is O(1),
       and bounds-check the whole schedule against the file size. */
    {
        unsigned long cursor = street_objects_offset;
        int frame;
        for (frame = 0; frame < street_frames; ++frame)
        {
            int count;
            if (cursor + 2 > (unsigned long)street_bytes)
            {
                failed_asset = "STRIPS OBJECTS";
                return 0;
            }
            street_object_frame_offset[frame] = cursor;
            count = (int)street_u16(cursor);
            cursor += 2 + (unsigned long)count * 8;
        }
        if (cursor > (unsigned long)street_bytes)
        {
            failed_asset = "STRIPS OBJECTS";
            return 0;
        }
    }

    /* Character data and base pattern grids. */
    street_load_planes();

    slColRAMOffsetNbg0((Uint16)street_palette[0].id);
    slColRAMOffsetNbg1((Uint16)street_palette[1].id);
    slCharNbg0(COL_TYPE_256, CHAR_SIZE_1x1);
    slCharNbg1(COL_TYPE_256, CHAR_SIZE_1x1);
    slPageNbg0((void *)STREET_NBG0_CEL, 0, PNB_1WORD | CN_12BIT);
    slPageNbg1((void *)STREET_NBG1_CEL, 0, PNB_1WORD | CN_12BIT);
    slPlaneNbg0(PL_SIZE_2x1);
    slPlaneNbg1(PL_SIZE_2x1);
    slMapNbg0((void *)STREET_NBG0_PNT, (void *)STREET_NBG0_PNT,
              (void *)STREET_NBG0_PNT, (void *)STREET_NBG0_PNT);
    slMapNbg1((void *)STREET_NBG1_PNT, (void *)STREET_NBG1_PNT,
              (void *)STREET_NBG1_PNT, (void *)STREET_NBG1_PNT);
    slPriority(scnNBG0, 3);
    slPriority(scnNBG1, 2);
    /* Sprite class registers: class 0 (Jo default, HUD/debug) stays at 6;
       class 1 carries CPS priority-1 actors above both planes; class 2
       carries CPS priority-4 foreground above the actors. */
    slPriority(scnSPR1, 4);
    slPriority(scnSPR2, 6);
    jo_set_displayed_screens(JO_NBG0_SCREEN | JO_NBG1_SCREEN |
                             JO_SPRITE_SCREEN);
#ifdef AVSP_CAMERA_STAGE_SALVAGE_BENCH
    avsp_diag_stage_interface_version = 1;
    avsp_diag_stage_layer_count = 2;
    avsp_diag_stage_source_width = 384;
    avsp_diag_stage_output_width = 352;
    avsp_diag_stage_priority_lock_ok = 1;
    avsp_diag_stage_scroll_steps = 0;
#ifndef AVSP_CAMERA_STAGE_PROMOTION_BENCH
    stage_has_previous_scroll = 0;
#endif
#endif
#ifdef AVSP_CAMERA_STAGE_PROMOTION_BENCH
    avsp_port_v2_camera_init(&stage_camera_runtime);
    stage_render_operations.submit_layer = stage_submit_layer;
    stage_render_operations.submit_sprite_priorities =
        stage_submit_sprite_priorities;
    avsp_diag_stage_row_scroll_status =
        AVSP_PORT_V2_STAGE_ROW_SCROLL_ADAPTED_UNCAPTURED;
    avsp_diag_stage_render_submissions = 0;
    avsp_diag_stage_port_lock_ok =
        avsp_port_v2_camera_validate_config(
            &avsp_port_v2_camera_approved_config) &&
        avsp_port_v2_stage_validate_config(
            &avsp_port_v2_stage_approved_config);
    if (!avsp_diag_stage_port_lock_ok)
    {
        failed_asset = "CAMERA STAGE PORT";
        return 0;
    }
#endif
    street_ready = 1;
    return 1;
}

static void street_load_planes(void)
{
    int plane;
    for (plane = 0; plane < 2; ++plane)
    {
        const StreetPlane *sp = &street_plane[plane];
        unsigned short *cel = plane == 0 ?
            (unsigned short *)STREET_NBG0_CEL :
            (unsigned short *)STREET_NBG1_CEL;
        unsigned short *pnt = plane == 0 ? STREET_NBG0_PNT :
            STREET_NBG1_PNT;
        const unsigned long char_words =
            (unsigned long)sp->char_count * 32;
        unsigned long word;
        int cx;
        int cy;
        for (word = 0; word < char_words; ++word)
            cel[word] = (unsigned short)street_u16(sp->char_offset +
                                                   word * 2);
        /* Pattern pages: plane is 2x1 pages; cell (cx,cy) lands in page
           cx/64 at slot cy*64 + cx%64. 256-colour chars advance the
           12-bit character number by 2 per 8x8 cell. */
        for (word = 0; word < STREET_PAGE_WORDS * 2; ++word)
            pnt[word] = 0;
        for (cy = 0; cy < sp->cell_rows; ++cy)
            for (cx = 0; cx < sp->cell_cols; ++cx)
            {
                const unsigned int char_index = street_u16(
                    sp->pnt_offset +
                    ((unsigned long)cy * sp->cell_cols + cx) * 2);
                pnt[(cx / 64) * STREET_PAGE_WORDS +
                    (unsigned long)cy * 64 + (cx % 64)] =
                    (unsigned short)(char_index * 2);
            }
    }
}

static void street_apply_patches(const int rel)
{
    const int patch_count = (int)street_u16(street_patch_offset);
    unsigned long cursor = street_patch_offset + 2;
    int patch;
    for (patch = 0; patch < patch_count; ++patch)
    {
        const int frame_rel = (int)street_u16(cursor);
        const int plane = (int)street_u16(cursor + 2);
        const int updates = (int)street_u16(cursor + 4);
        if (frame_rel == rel)
        {
            unsigned short *pnt = plane == 0 ? STREET_NBG0_PNT :
                STREET_NBG1_PNT;
            int update;
            for (update = 0; update < updates; ++update)
            {
                const unsigned long at = cursor + 6 +
                    (unsigned long)update * 6;
                const int cx = (int)street_u16(at);
                const int cy = (int)street_u16(at + 2);
                const unsigned int char_index = street_u16(at + 4);
                unsigned short *slot = &pnt[(cx / 64) * STREET_PAGE_WORDS +
                    (unsigned long)cy * 64 + (cx % 64)];
                if (street_patch_revert_count < STREET_MAX_PATCH_CELLS)
                {
                    street_patch_revert[street_patch_revert_count][0] =
                        (unsigned long)slot;
                    street_patch_revert[street_patch_revert_count][1] =
                        *slot;
                    ++street_patch_revert_count;
                }
                *slot = (unsigned short)(char_index * 2);
            }
        }
        cursor += 6 + (unsigned long)updates * 6;
    }
}

static void street_apply_cycle(const int rel)
{
    /* First-flip semantics: measured state A until the first flip
       frame, then alternate every cycle period. */
    const int step = (street_cycle_period > 0 &&
                      rel >= street_cycle_first_flip) ?
        (((rel - street_cycle_first_flip) / street_cycle_period) + 1) & 1 : 0;
    int entry;
    for (entry = 0; entry < street_cycle_entries; ++entry)
    {
        const unsigned long at = street_cycle_offset +
            (unsigned long)entry * 6;
        const int index = (int)street_u16(at);
        const unsigned short colour = (unsigned short)
            street_u16(at + 2 + (unsigned long)step * 2);
        street_palette[0].data[index - 1] = colour;
    }
#ifdef AVSP_CAMERA_STAGE_SALVAGE_BENCH
    avsp_diag_stage_palette_cycle_state = step;
#endif
}

#ifdef AVSP_LIVE_ENCOUNTER
/* The live camera is expressed in CPS2 scroll2 world X.  NBG0/NBG1 are
 * cropped strips with independent origins, and scroll3 follows its own
 * captured register trajectory.  Feeding camera_world_x (or half of it)
 * directly to SGL treats world coordinates as PNT offsets and exposes
 * wrapped/empty map regions.  Interpolate only inside the captured
 * scroll2-to-scroll3 schedule and clamp at its measured endpoints. */
static int street_scroll3_for_scroll2(const int scroll2_x)
{
    unsigned long at;
    int previous_scroll2;
    int previous_scroll3;
    int frame;

    at = street_scroll_offset;
    previous_scroll2 = (int)street_u16(at);
    previous_scroll3 = (int)street_u16(at + 4);
    if (scroll2_x <= previous_scroll2) return previous_scroll3;

    for (frame = 1; frame < street_frames; ++frame)
    {
        const int current_scroll2 = (int)street_u16(
            street_scroll_offset + (unsigned long)frame * 8);
        const int current_scroll3 = (int)street_u16(
            street_scroll_offset + (unsigned long)frame * 8 + 4);
        if (current_scroll2 > previous_scroll2)
        {
            if (scroll2_x <= current_scroll2)
            {
                const int span = current_scroll2 - previous_scroll2;
                const int offset = scroll2_x - previous_scroll2;
                const int delta = current_scroll3 - previous_scroll3;
                return previous_scroll3 +
                    (offset * delta + span / 2) / span;
            }
            previous_scroll2 = current_scroll2;
            previous_scroll3 = current_scroll3;
        }
    }
    return previous_scroll3;
}
#endif

static void street_test_frame(void)
{
    static int frame_counter = 0;
#ifdef AVSP_PLAYABLE_SLICE
    const int rel = frame_counter < street_frames ?
        frame_counter : street_frames - 1;
#else
    const int rel = frame_counter % street_frames;
#endif
    unsigned long at;
#ifndef AVSP_PLAYABLE_SLICE
    unsigned long objects;
    int entry_count;
    int entry;
#endif
    int drawn = 0;

    if (!street_ready)
    {
        if (!street_setup())
        {
            jo_printf(1, 12, "STREET TEST FAILED: %s",
                      failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
            return;
        }
        frame_counter = 0;
    }
    if (rel == 0 && street_patch_revert_count > 0)
    {
        /* Loop wrap: undo the measured map patches by restoring the
           original pattern words recorded when they were applied. */
        int revert;
        for (revert = 0; revert < street_patch_revert_count; ++revert)
            *(unsigned short *)street_patch_revert[revert][0] =
                (unsigned short)street_patch_revert[revert][1];
        street_patch_revert_count = 0;
    }

    at = street_scroll_offset + (unsigned long)rel * 8;
    {
        const int s2x = (int)street_u16(at);
        const int s2y = (int)street_u16(at + 2);
        const int s3x = (int)street_u16(at + 4);
        const int s3y = (int)street_u16(at + 6);
        int scx0 = street_out_of(s2x + 64) -
            street_out_of(street_plane[0].world_x0);
        const int scy0 = s2y + 16 - street_plane[0].row0 * 16;
        int scx1 = street_out_of(s3x + 64) -
            street_out_of(street_plane[1].world_x0);
        const int scy1 = s3y + 16 - street_plane[1].row0 * 32;
#ifdef AVSP_LIVE_ENCOUNTER
        /* The live encounter owns the camera after load.  The approved stage
         * port still owns both VDP2 submissions and their priority/palette
         * locks. Translate source scroll2 world X through each strip origin;
         * derive scroll3 from the captured register relationship. */
        const int live_scroll2_x = live_encounter_runtime.camera_world_x;
        const int live_scroll3_x =
            street_scroll3_for_scroll2(live_scroll2_x);
        scx0 = street_out_of(live_scroll2_x + 64) -
            street_out_of(street_plane[0].world_x0);
        scx1 = street_out_of(live_scroll3_x + 64) -
            street_out_of(street_plane[1].world_x0);
#endif
#ifdef AVSP_CAMERA_STAGE_PROMOTION_BENCH
        AvspPortV2CameraInput camera_input;
        AvspPortV2CameraView camera_view;
        AvspPortV2StageFrame stage_frame;
        camera_input.scroll_x[0] = scx0;
        camera_input.scroll_y[0] = scy0;
        camera_input.scroll_x[1] = scx1;
        camera_input.scroll_y[1] = scy1;
        avsp_port_v2_camera_step(&stage_camera_runtime, &camera_input);
        avsp_port_v2_camera_view(&stage_camera_runtime, &camera_view);
        if (!avsp_port_v2_stage_build_frame(&camera_view, &stage_frame) ||
            !avsp_port_v2_stage_submit(&stage_frame,
                                       &stage_render_operations))
        {
            avsp_diag_stage_port_lock_ok = 0;
            failed_asset = "CAMERA STAGE SUBMIT";
            return;
        }
        avsp_diag_stage_scroll_steps = camera_view.scroll_steps;
        avsp_diag_stage_row_scroll_status = stage_frame.row_scroll_status;
#else
        slScrPosNbg0(toFIXED(scx0), toFIXED(scy0));
        slScrPosNbg1(toFIXED(scx1), toFIXED(scy1));
#endif
        avsp_diag_street_scx[0] = scx0;
        avsp_diag_street_scx[1] = scx1;
#if defined(AVSP_CAMERA_STAGE_SALVAGE_BENCH) && \
    !defined(AVSP_CAMERA_STAGE_PROMOTION_BENCH)
        if (stage_has_previous_scroll &&
            (scx0 != stage_previous_scx0 || scx1 != stage_previous_scx1))
            ++avsp_diag_stage_scroll_steps;
        stage_previous_scx0 = scx0;
        stage_previous_scx1 = scx1;
        stage_has_previous_scroll = 1;
#endif
    }
    street_apply_cycle(rel);
    street_apply_patches(rel);

    /* The stage/card benchmark replays its captured foreground object stream
       to prove the VDP1/VDP2 composition.  The production playable slice must
       not replay those authored actors: its promoted player/enemy pipeline is
       the sole gameplay-actor owner. */
#ifndef AVSP_PLAYABLE_SLICE
    objects = street_object_frame_offset[rel];
    entry_count = (int)street_u16(objects);
    objects += 2;
    for (entry = 0; entry < entry_count; ++entry)
    {
        const unsigned int x = street_u16(objects);
        const unsigned int y = street_u16(objects + 2);
        const unsigned int code = street_u16(objects + 4);
        const unsigned int attr = street_u16(objects + 6);
        const int priority = (int)((x >> 13) & 7);
        AvspEntryTile entry_tiles[64];
        const int bank_slot = avsp_tiles_bank_slot(&tile_archive,
                                                   (int)(attr & 0x1F));
        const int count = avsp_entry_tiles((unsigned short)y,
                                           (unsigned short)code,
                                           (unsigned short)attr,
                                           entry_tiles, 64);
        int tile;
        objects += 8;
        if (count <= 0 || bank_slot < 0) continue;
        street_object_palette(bank_slot, priority);
        for (tile = 0; tile < count; ++tile)
        {
            const long rank = avsp_tiles_find(&tile_archive,
                                              entry_tiles[tile].code);
            int sprite_id;
            if (rank < 0) continue;
            sprite_id = tile_sprite_for_archive_rank(&tile_archive, rank);
            if (sprite_id < 0) continue;
            if (entry_tiles[tile].flip_x) jo_sprite_enable_horizontal_flip();
            if (entry_tiles[tile].flip_y) jo_sprite_enable_vertical_flip();
            /* Objects share the plane's endpoint-aligned 384->352 rule
               (street_out_of), then shift into Jo's centered space; the
               centered fit_352 sat 1 px left of the plane mapping for
               6,761 of the 12,118 scheduled objects (measured). */
            jo_sprite_draw3D(sprite_id,
                             street_out_of((int)(x & 0x3FF) - 64 +
                                           entry_tiles[tile].dx + 8) - 176,
                             (int)(y & 0x3FF) - 16 +
                                 entry_tiles[tile].dy + 8 - 112,
                             priority >= 4 ? 120 : 240);
            if (entry_tiles[tile].flip_x)
                jo_sprite_disable_horizontal_flip();
            if (entry_tiles[tile].flip_y)
                jo_sprite_disable_vertical_flip();
            ++drawn;
        }
    }
#endif
    avsp_diag_street_objects = drawn;
    avsp_diag_street_frame = rel;
#ifdef AVSP_CAMERA_STAGE_SALVAGE_BENCH
    avsp_diag_stage_asset_failures = failed_asset == JO_NULL ? 0 : 1;
    avsp_diag_stage_disc_late_reads = avsp_disc_guard_state.late_read_attempts;
#endif
    ++frame_counter;
}
#endif

static void draw_world(void)
{
    int index;
    int player_x = cap_actor_screen_x(world.player.x, world.camera_x, 1);
    int background_scroll = cap_background_fit_scroll_x(
        world.camera_x, world.stage_area);

    /* Per-frame evidence: states that draw no frontend objects must report
     * zero rather than the previous state's count. */
    frontend_runtime.vdp1_commands_last_frame = 0;

    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ||
        world.encounter_state == CAP_ENCOUNTER_START_TRANSITION ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM)
    {
        int scene = world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ? 0 : 1;
        int cursor_visible = 1;
        if (!activate_frontend_scene(scene)) runtime_ready = 0;
        if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
            avsp_frontend_draw_title(&frontend_runtime);
        else if (world.encounter_state == CAP_ENCOUNTER_START_TRANSITION)
            avsp_frontend_draw_start_transition(
                &frontend_runtime, world.encounter_timer);
        else
        {
            /* The measured blink: the markers first vanish three frames
             * after the confirm input, alternate every four frames, and
             * retire permanently after their fourth visible window - the
             * complete captured confirm interval shows no marker from
             * frames-since-input 27 onward. cap_confirm_character() zeroes
             * encounter_timer on the confirm step and
             * cap_update_encounter() increments it in that same step, so
             * frames since input is encounter_timer - 1. */
            if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM &&
                world.encounter_timer - 1 >= 3)
                cursor_visible = world.encounter_timer - 1 < 27 &&
                    (((world.encounter_timer - 1 - 3) / 4) & 1) != 0;
            avsp_frontend_draw_cursor(
                &frontend_runtime, world.selection_cursor,
                world.encounter_timer, cursor_visible);
            /* The Round 1 title text appears over the shutter-blacked
             * screen 171 frames after the confirm input and fades in
             * through the source's own sixteen measured palette rows. */
            if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM &&
                world.encounter_timer - 1 >= AVSP_FRONTEND_R1TEXT_CONFIRM_FRAME)
            {
                avsp_frontend_set_r1text_fade(
                    &frontend_runtime, world.encounter_timer - 1 -
                        AVSP_FRONTEND_R1TEXT_CONFIRM_FRAME);
                avsp_frontend_draw_round1_text(&frontend_runtime);
            }
        }
        if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM)
            apply_confirm_shutter();
        return;
    }
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE)
    {
        /* Measured Round 1 title: the text stays over the shutter-blacked
         * bitmap until the street scene pops in at frame 35, and clears
         * instantly at frame 90. The scene itself is the native street
         * renderer below, not a captured picture. */
        if (world.encounter_timer < AVSP_FRONTEND_R1TEXT_CLEAR_FRAME)
            avsp_frontend_draw_round1_text(&frontend_runtime);
        if (world.encounter_timer < AVSP_FRONTEND_R1SCENE_POP_FRAME)
            return;
    }
    if (sequence_scene_for_world() >= 0)
        return;
    activate_gameplay_background(world.stage_area);
    /* The source capture is already exactly 224 lines high.  A non-zero Y
       scroll silently discards arcade scanlines and is therefore a crop. */
    jo_move_background(background_scroll, 0);
    jo_sprite_change_sprite_scale_xy(
        (float)CAP_VIEW_WIDTH / (float)CAP_CPS2_VIEW_WIDTH, 1.0f);
    draw_player(&world.player, player_x);
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
    {
        CapActor *enemy = &world.enemies[index];
        int screen_x = cap_actor_screen_x(enemy->x, world.camera_x, 1);
        if (!enemy->active) continue;
        if (screen_x < -256 || screen_x > 256) continue;
        if (enemy->kind == CAP_ACTOR_BOSS)
            draw_boss(enemy, screen_x);
        else if (rom_actor_entry_counts[index] > 0 && tile_archive_ready)
            /* Body E: any ROM-driven actor renders from its own decoded
               object list; its capture cel stays unused as the
               regression/comparison path. */
            draw_rom_actor_tiles(enemy, index);
        else
            draw_alien(enemy, screen_x, index);
    }
    jo_sprite_restore_sprite_scale();
}

static void update_hud_textures(void)
{
    int x;
    int y;
    if (displayed_hud_health != world.player.health &&
        !(displayed_hud_health >= 0 &&
          (world.player.action == CAP_ACT_HIT ||
           world.player.action == CAP_ACT_KO) &&
          world.player.action_frame < 2))
    {
        int source_fill = (world.player.health * 5) / 4;
        int fill = (source_fill * CAP_VIEW_WIDTH + CAP_CPS2_VIEW_WIDTH - 1) /
                   CAP_CPS2_VIEW_WIDTH;
        if (fill > AVSP_HUD_HEALTH_WIDTH) fill = AVSP_HUD_HEALTH_WIDTH;
        for (y = 0; y < AVSP_HUD_HEALTH_HEIGHT; ++y)
            for (x = 0; x < AVSP_HUD_HEALTH_WIDTH; ++x)
                hud_top_image.data[
                    (AVSP_HUD_HEALTH_Y + y) * AVSP_HUD_TOP_WIDTH +
                    AVSP_HUD_HEALTH_X + x] =
                        x < fill ? AVSP_HUD_YELLOW_INDEX : AVSP_HUD_RED_INDEX;
        jo_sprite_replace((const jo_img *)&hud_top_image, hud_top_sprite);
        displayed_hud_health = world.player.health;
    }
    if (displayed_hud_energy != world.weapon_energy &&
        !(displayed_hud_energy >= 0 &&
          world.player.action == CAP_ACT_SHOOT &&
          world.player.action_frame < 3))
    {
        int fill = (world.weapon_energy * AVSP_HUD_HEAT_BAR_WIDTH +
                    CAP_WEAPON_MAX_ENERGY - 1) / CAP_WEAPON_MAX_ENERGY;
        for (y = 0; y < AVSP_HUD_HEAT_BAR_HEIGHT; ++y)
            for (x = 0; x < AVSP_HUD_HEAT_BAR_WIDTH; ++x)
                hud_heat_image.data[
                    (AVSP_HUD_HEAT_BAR_Y + y) * AVSP_HUD_HEAT_WIDTH +
                    AVSP_HUD_HEAT_BAR_X + x] =
                        x < fill ? AVSP_HUD_ENERGY_INDEX : AVSP_HUD_EMPTY_INDEX;
        jo_sprite_replace((const jo_img *)&hud_heat_image, hud_heat_sprite);
        displayed_hud_energy = world.weapon_energy;
    }
}

#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static void update_player2_hud_textures(void)
{
    int x;
    int y;
    if (displayed_hud_p2_health != hud_pcm_bench.p2_health)
    {
        int source_fill = (hud_pcm_bench.p2_health * 5) / 4;
        int fill = (source_fill * CAP_VIEW_WIDTH + CAP_CPS2_VIEW_WIDTH - 1) /
                   CAP_CPS2_VIEW_WIDTH;
        if (fill > AVSP_HUD_P2_HEALTH_WIDTH)
            fill = AVSP_HUD_P2_HEALTH_WIDTH;
        for (y = 0; y < AVSP_HUD_P2_HEALTH_HEIGHT; ++y)
            for (x = 0; x < AVSP_HUD_P2_HEALTH_WIDTH; ++x)
                hud_p2_top_image.data[
                    (AVSP_HUD_P2_HEALTH_Y + y) * AVSP_HUD_P2_TOP_WIDTH +
                    AVSP_HUD_P2_HEALTH_X + x] =
                        x < fill ? AVSP_HUD_YELLOW_INDEX : AVSP_HUD_RED_INDEX;
        jo_sprite_replace((const jo_img *)&hud_p2_top_image,
                          hud_p2_top_sprite);
        displayed_hud_p2_health = hud_pcm_bench.p2_health;
    }
    if (displayed_hud_p2_energy != hud_pcm_bench.p2_energy)
    {
        int fill = (hud_pcm_bench.p2_energy * AVSP_HUD_P2_HEAT_BAR_WIDTH +
                    CAP_WEAPON_MAX_ENERGY - 1) / CAP_WEAPON_MAX_ENERGY;
        for (y = 0; y < AVSP_HUD_P2_HEAT_BAR_HEIGHT; ++y)
            for (x = 0; x < AVSP_HUD_P2_HEAT_BAR_WIDTH; ++x)
                hud_p2_heat_image.data[
                    (AVSP_HUD_P2_HEAT_BAR_Y + y) *
                        AVSP_HUD_P2_HEAT_WIDTH +
                    AVSP_HUD_P2_HEAT_BAR_X + x] =
                        x < fill ? AVSP_HUD_ENERGY_INDEX :
                                   AVSP_HUD_EMPTY_INDEX;
        jo_sprite_replace((const jo_img *)&hud_p2_heat_image,
                          hud_p2_heat_sprite);
        displayed_hud_p2_energy = hud_pcm_bench.p2_energy;
    }
}
#endif

static void draw_arcade_hud(void)
{
    /* Every frontend state, including the Start transition. The transition
     * is drawn by the frontend over the title surface and the ROM shows no
     * gameplay HUD across it; reading the live VDP1 list at held transition
     * frames caught the arcade HUD emitting two to three sprites there. */
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU ||
        world.encounter_state == CAP_ENCOUNTER_START_TRANSITION ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT ||
        world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM ||
        sequence_scene_for_world() >= 0)
        return;
    /* The source writes the gameplay HUD tilemap 32 frames into the Round 1
       title, three frames before the street scene pops in. */
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world.encounter_timer < AVSP_FRONTEND_R1HUD_FRAME)
        return;
    update_hud_textures();
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
    update_player2_hud_textures();
#endif
    jo_sprite_set_palette(hud_palette.id);
    jo_sprite_draw3D(hud_top_sprite,
                     -JO_TV_WIDTH_2 + AVSP_HUD_TOP_WIDTH / 2,
                     -JO_TV_HEIGHT_2 + AVSP_HUD_TOP_HEIGHT / 2, 100);
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
    jo_sprite_draw3D(hud_p2_top_sprite,
                     -JO_TV_WIDTH_2 + AVSP_HUD_P2_TOP_X +
                         AVSP_HUD_P2_TOP_WIDTH / 2,
                     -JO_TV_HEIGHT_2 + AVSP_HUD_P2_TOP_HEIGHT / 2, 100);
    jo_sprite_draw3D(hud_p2_heat_sprite,
                     -JO_TV_WIDTH_2 + AVSP_HUD_P2_HEAT_X +
                         AVSP_HUD_P2_HEAT_WIDTH / 2,
                     -JO_TV_HEIGHT_2 + AVSP_HUD_P2_HEAT_Y +
                         AVSP_HUD_P2_HEAT_HEIGHT / 2, 100);
#else
    if ((world.frame & 63) < 32)
        jo_sprite_draw3D(hud_prompt_sprite,
                         -JO_TV_WIDTH_2 + AVSP_HUD_PROMPT_X +
                             AVSP_HUD_PROMPT_WIDTH / 2,
                         -JO_TV_HEIGHT_2 + AVSP_HUD_PROMPT_HEIGHT / 2, 100);
#endif
    jo_sprite_draw3D(hud_heat_sprite,
                     -JO_TV_WIDTH_2 + AVSP_HUD_HEAT_WIDTH / 2,
                     -JO_TV_HEIGHT_2 + AVSP_HUD_HEAT_Y +
                         AVSP_HUD_HEAT_HEIGHT / 2, 100);
}

#ifdef AVSP_HUD_PROMOTION_BENCH
/* Temporary legacy render adapter. The production HUD emits only semantic
 * state; this bounded adapter applies it to the already-approved Jo textures
 * and draw order until the Saturn presentation adapter displaces main.c. */
static int hud_port_submit_frame(const AvspPortV2HudFrame *frame)
{
    if (frame == JO_NULL || frame->player_count != AVSP_PORT_V2_HUD_PLAYER_COUNT)
        return 0;
    if (!frame->players[AVSP_PORT_V2_HUD_P1].visible ||
        !frame->players[AVSP_PORT_V2_HUD_P2].visible)
        return frame->render_count == 0;
    world.player.health = frame->players[AVSP_PORT_V2_HUD_P1].health;
    world.weapon_energy = frame->players[AVSP_PORT_V2_HUD_P1].energy;
    hud_pcm_bench.p2_health = frame->players[AVSP_PORT_V2_HUD_P2].health;
    hud_pcm_bench.p2_energy = frame->players[AVSP_PORT_V2_HUD_P2].energy;
    draw_arcade_hud();
    ++avsp_diag_hud_submit_count;
    return 1;
}
#endif

#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
static int hud_pcm_sound_valid(const jo_sound *sound)
{
    return sound != JO_NULL && sound->data != JO_NULL &&
           sound->data_length == AVSP_MELEE_PCM_BYTES &&
           sound->sample_rate == AVSP_MELEE_PCM_SAMPLE_RATE &&
           sound->mode == JoSoundStereo16Bit;
}

static int hud_pcm_hud_valid(const jo_img_8bits *image, const int sprite)
{
    return image != JO_NULL && image->data != JO_NULL && sprite >= 0;
}

static int hud_pcm_player2_binding_valid(const jo_img_8bits *top,
                                         const jo_img_8bits *heat)
{
    return hud_pcm_hud_valid(top, hud_p2_top_sprite) &&
           hud_pcm_hud_valid(heat, hud_p2_heat_sprite) &&
           top->width == AVSP_HUD_P2_TOP_WIDTH &&
           top->height == AVSP_HUD_P2_TOP_HEIGHT &&
           heat->width == AVSP_HUD_P2_HEAT_WIDTH &&
           heat->height == AVSP_HUD_P2_HEAT_HEIGHT &&
           top->data != hud_prompt_image.data;
}

#ifndef AVSP_HUD_PROMOTION_BENCH
static int hud_pcm_health_fill(const int health)
{
    int source_fill = (health * 5) / 4;
    int fill = (source_fill * CAP_VIEW_WIDTH + CAP_CPS2_VIEW_WIDTH - 1) /
               CAP_CPS2_VIEW_WIDTH;
    if (fill > AVSP_HUD_HEALTH_WIDTH) fill = AVSP_HUD_HEALTH_WIDTH;
    return fill;
}

static int hud_pcm_energy_fill(const int energy)
{
    return (energy * AVSP_HUD_HEAT_BAR_WIDTH + CAP_WEAPON_MAX_ENERGY - 1) /
           CAP_WEAPON_MAX_ENERGY;
}
#endif

#ifdef AVSP_PCM_PROMOTION_BENCH
/* Temporary SCSP adapter for the already-approved cue. The semantic port owns
 * cue identity and source-frame timing; this adapter only starts/stops the Jo
 * sound object and remains deletable once the Saturn audio adapter lands. */
static int pcm_port_start(const AvspPortV2PcmFrame *frame)
{
    if (frame == JO_NULL ||
        frame->cue_id != AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE ||
        !hud_pcm_sound_valid(&melee_sound))
        return 0;
    play_pcm_committed(&melee_sound, &melee_sound, AVSP_PCM_CHANNEL_MELEE);
    hud_pcm_bench.pcm_active = 1;
    hud_pcm_bench.planned_end_frame =
        hud_pcm_bench.frame +
        avsp_port_v2_pcm_predator_melee_config.duration_frames;
    hud_pcm_bench.underrun_reported_start = -1;
    avsp_diag_pcm_start_frame = frame->start_frame;
    ++avsp_diag_pcm_submit_count;
    return 1;
}

static int pcm_port_stop(const AvspPortV2PcmFrame *frame)
{
    if (frame == JO_NULL ||
        frame->cue_id != AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE)
        return 0;
    if (jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_MELEE))
    {
        jo_audio_stop_sound(&melee_sound);
        slSndFlush();
    }
    hud_pcm_bench.pcm_active = 0;
    avsp_diag_pcm_end_frame = frame->end_frame;
    ++avsp_diag_pcm_submit_count;
    return 1;
}
#endif

static void hud_pcm_bench_negative_control(const int control)
{
    static jo_color rejected_zero_based[AVSP_CRAM_MAX_COLOURS];
    int index;
    if ((hud_pcm_bench.negative_control_mask & (1 << control)) != 0) return;
    hud_pcm_bench.negative_control_mask |= 1 << control;
    if (control == 0)
    {
        jo_img_8bits missing_hud = hud_top_image;
        missing_hud.data = JO_NULL;
        if (!hud_pcm_hud_valid(&missing_hud, hud_top_sprite))
            ++avsp_diag_hud_pcm_negative_rejections;
        else
            ++avsp_diag_hud_asset_failures;
    }
    else if (control == 1)
    {
        jo_sound invalid_sound = melee_sound;
        invalid_sound.sample_rate = 0;
        if (!hud_pcm_sound_valid(&invalid_sound))
            ++avsp_diag_hud_pcm_negative_rejections;
        else
            ++avsp_diag_pcm_audio_failures;
    }
    else if (control == 2)
    {
        jo_sound missing_sound = melee_sound;
        missing_sound.data = JO_NULL;
        if (!hud_pcm_sound_valid(&missing_sound))
            ++avsp_diag_hud_pcm_negative_rejections;
        else
            ++avsp_diag_pcm_audio_failures;
    }
    else if (control == 3)
    {
        for (index = 0; index < AVSP_CRAM_MAX_COLOURS; ++index)
            rejected_zero_based[index] = JO_COLOR_RGB(
                avsp_hud_palette[index][0], avsp_hud_palette[index][1],
                avsp_hud_palette[index][2]);
        if (!hud_palette_binding_valid(rejected_zero_based, 1))
            ++avsp_diag_hud_pcm_negative_rejections;
        else
            ++avsp_diag_hud_asset_failures;
    }
    else
    {
        if (!hud_pcm_player2_binding_valid(&hud_prompt_image,
                                           &hud_p2_heat_image))
            ++avsp_diag_hud_pcm_negative_rejections;
        else
            ++avsp_diag_hud_asset_failures;
    }
}

static void hud_pcm_bench_init(void)
{
    memset(&hud_pcm_bench, 0, sizeof(hud_pcm_bench));
    hud_pcm_bench.head_canary = HUD_PCM_BENCH_CANARY_HEAD;
    hud_pcm_bench.tail_canary = HUD_PCM_BENCH_CANARY_TAIL;
    hud_pcm_bench.underrun_reported_start = -1;
    avsp_diag_hud_pcm_interface_version = 3;
    avsp_diag_pcm_event_frame = -1;
    avsp_diag_pcm_start_frame = -1;
    avsp_diag_pcm_end_frame = -1;
#ifdef AVSP_HUD_PROMOTION_BENCH
    avsp_diag_hud_production_interface_version =
        AVSP_PORT_V2_HUD_INTERFACE_VERSION;
    avsp_diag_hud_submit_count = 0;
#endif
#ifdef AVSP_PCM_PROMOTION_BENCH
    avsp_port_v2_pcm_init(&pcm_port_v2);
    avsp_diag_pcm_production_interface_version =
        AVSP_PORT_V2_PCM_INTERFACE_VERSION;
    avsp_diag_pcm_submit_count = 0;
#endif
    world.encounter_started = 1;
    world.encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    world.frame = 0;
    world.player.health = 0;
    world.weapon_energy = 0;
    hud_pcm_bench.p2_health = 0;
    hud_pcm_bench.p2_energy = 0;
}

static void hud_pcm_bench_frame_callback(void)
{
    int relative;
    int phase;
    int channel_playing;
#ifdef AVSP_HUD_PROMOTION_BENCH
    AvspPortV2HudInput hud_input;
    AvspPortV2HudFrame hud_frame;
    AvspPortV2HudRenderOps hud_operations;
#endif
#ifdef AVSP_PCM_PROMOTION_BENCH
    AvspPortV2PcmInput pcm_input;
    AvspPortV2PcmFrame pcm_frame;
    AvspPortV2PcmAudioOps pcm_operations;
#endif
    jo_clear_screen();
    avsp_diag_runtime_ready = runtime_ready;
    if (!runtime_ready)
    {
        avsp_diag_hud_asset_failures = 1;
        jo_printf(1, 12, "HUD PCM BENCH FAILED: %s",
                  failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
    relative = hud_pcm_bench.frame % HUD_PCM_BENCH_CYCLE_FRAMES;
    phase = relative / 120;
    world.frame = relative;
    if (relative == 0)
    {
        /* Every cycle is an independent readback experiment. This makes MCP
         * attachment latency irrelevant without concealing persistent asset
         * or audio failures. */
        avsp_diag_pcm_event_count = 0;
        avsp_diag_pcm_event_frame = -1;
        avsp_diag_pcm_start_frame = -1;
        avsp_diag_pcm_end_frame = -1;
        avsp_diag_pcm_channel_observed = 0;
        avsp_diag_pcm_underruns = 0;
        avsp_diag_hud_pcm_negative_rejections = 0;
        hud_pcm_bench.negative_control_mask = 0;
        hud_pcm_bench.underrun_reported_start = -1;
#ifdef AVSP_HUD_PROMOTION_BENCH
        avsp_diag_hud_submit_count = 0;
#endif
#ifdef AVSP_PCM_PROMOTION_BENCH
        avsp_port_v2_pcm_init(&pcm_port_v2);
        avsp_diag_pcm_submit_count = 0;
#endif
    }
    if (phase == 0)
    {
        world.player.health = 0;
        world.weapon_energy = 0;
        hud_pcm_bench.p2_health = 0;
        hud_pcm_bench.p2_energy = 0;
    }
    else if (phase == 1)
    {
        world.player.health = 50;
        world.weapon_energy = 32;
        hud_pcm_bench.p2_health = 50;
        hud_pcm_bench.p2_energy = 32;
    }
    else if (phase == 2)
    {
        world.player.health = 101;
        world.weapon_energy = CAP_WEAPON_MAX_ENERGY;
        hud_pcm_bench.p2_health = 101;
        hud_pcm_bench.p2_energy = CAP_WEAPON_MAX_ENERGY;
    }
    else
    {
        world.player.health = 50;
        world.weapon_energy = 32;
        hud_pcm_bench.p2_health = 50;
        hud_pcm_bench.p2_energy = 32;
    }

#ifdef AVSP_PCM_PROMOTION_BENCH
    pcm_input.frame = relative;
    pcm_input.cue_event = relative == HUD_PCM_BENCH_FIRST_EVENT ||
                          relative == HUD_PCM_BENCH_SECOND_EVENT;
    pcm_input.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
    if (!avsp_port_v2_pcm_step(&pcm_port_v2, &pcm_input, &pcm_frame))
    {
        ++avsp_diag_pcm_audio_failures;
        memset(&pcm_frame, 0, sizeof(pcm_frame));
    }
    pcm_operations.start = pcm_port_start;
    pcm_operations.stop = pcm_port_stop;
    if (!avsp_port_v2_pcm_submit(&pcm_frame, &pcm_operations))
        ++avsp_diag_pcm_audio_failures;
    avsp_diag_pcm_event_count = pcm_frame.event_count;
    avsp_diag_pcm_event_frame = pcm_frame.event_frame;
    avsp_diag_pcm_semantic_active = pcm_frame.active;
    avsp_diag_pcm_port_lock_ok =
        avsp_port_v2_pcm_validate_config(
            &avsp_port_v2_pcm_predator_melee_config) &&
        (relative < HUD_PCM_BENCH_FIRST_EVENT ||
         pcm_frame.event_count > 0);
    avsp_diag_pcm_allocation_ok =
        hud_pcm_sound_valid(&melee_sound) &&
        avsp_port_v2_pcm_predator_melee_config.scsp_channel ==
            AVSP_PCM_CHANNEL_MELEE;
    channel_playing = jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_MELEE);
    if (hud_pcm_bench.pcm_active && channel_playing)
        avsp_diag_pcm_channel_observed = 1;
    if (hud_pcm_bench.pcm_active &&
        hud_pcm_bench.frame >
            hud_pcm_bench.planned_end_frame - HUD_PCM_BENCH_PCM_FRAMES + 1 &&
        hud_pcm_bench.frame < hud_pcm_bench.planned_end_frame &&
        !channel_playing &&
        hud_pcm_bench.underrun_reported_start !=
            hud_pcm_bench.planned_end_frame)
    {
        ++avsp_diag_pcm_underruns;
        hud_pcm_bench.underrun_reported_start =
            hud_pcm_bench.planned_end_frame;
    }
#else
    if (relative == HUD_PCM_BENCH_FIRST_EVENT ||
        relative == HUD_PCM_BENCH_SECOND_EVENT)
    {
        hud_pcm_bench.pending = 1;
        ++avsp_diag_pcm_event_count;
        avsp_diag_pcm_event_frame = relative;
    }
    if (hud_pcm_bench.pending &&
        (relative == HUD_PCM_BENCH_FIRST_EVENT + HUD_PCM_BENCH_START_DELAY ||
         relative == HUD_PCM_BENCH_SECOND_EVENT + HUD_PCM_BENCH_START_DELAY))
    {
        if (hud_pcm_sound_valid(&melee_sound))
        {
            play_pcm_committed(&melee_sound, &melee_sound,
                               AVSP_PCM_CHANNEL_MELEE);
            hud_pcm_bench.pcm_active = 1;
            hud_pcm_bench.pending = 0;
            hud_pcm_bench.planned_end_frame =
                hud_pcm_bench.frame + HUD_PCM_BENCH_PCM_FRAMES;
            hud_pcm_bench.underrun_reported_start = -1;
            avsp_diag_pcm_start_frame = relative;
        }
        else
        {
            ++avsp_diag_pcm_audio_failures;
            hud_pcm_bench.pending = 0;
        }
    }
    channel_playing = jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_MELEE);
    if (hud_pcm_bench.pcm_active && channel_playing)
        avsp_diag_pcm_channel_observed = 1;
    if (hud_pcm_bench.pcm_active &&
        hud_pcm_bench.frame >
            hud_pcm_bench.planned_end_frame - HUD_PCM_BENCH_PCM_FRAMES + 1 &&
        hud_pcm_bench.frame < hud_pcm_bench.planned_end_frame &&
        !channel_playing &&
        hud_pcm_bench.underrun_reported_start !=
            hud_pcm_bench.planned_end_frame)
    {
        ++avsp_diag_pcm_underruns;
        hud_pcm_bench.underrun_reported_start =
            hud_pcm_bench.planned_end_frame;
    }
    if (hud_pcm_bench.pcm_active &&
        hud_pcm_bench.frame >= hud_pcm_bench.planned_end_frame)
    {
        if (channel_playing)
        {
            jo_audio_stop_sound(&melee_sound);
            slSndFlush();
        }
        hud_pcm_bench.pcm_active = 0;
        avsp_diag_pcm_end_frame = relative;
    }
#endif

    if (relative == 450) hud_pcm_bench_negative_control(0);
    if (relative == 451) hud_pcm_bench_negative_control(1);
    if (relative == 452) hud_pcm_bench_negative_control(2);
    if (relative == 453) hud_pcm_bench_negative_control(3);
    if (relative == 454) hud_pcm_bench_negative_control(4);

    avsp_diag_hud_pcm_phase = phase;
    avsp_diag_hud_state = phase < 3 ? phase : -1;
    avsp_diag_hud_p2_state = phase < 3 ? phase : -1;
#ifdef AVSP_HUD_PROMOTION_BENCH
    memset(&hud_input, 0, sizeof(hud_input));
    hud_input.players[AVSP_PORT_V2_HUD_P1].visible = phase < 3;
    hud_input.players[AVSP_PORT_V2_HUD_P1].character_id =
        AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR;
    hud_input.players[AVSP_PORT_V2_HUD_P1].health = world.player.health;
    hud_input.players[AVSP_PORT_V2_HUD_P1].energy = world.weapon_energy;
    hud_input.players[AVSP_PORT_V2_HUD_P2].visible = phase < 3;
    hud_input.players[AVSP_PORT_V2_HUD_P2].character_id =
        AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER;
    hud_input.players[AVSP_PORT_V2_HUD_P2].health = hud_pcm_bench.p2_health;
    hud_input.players[AVSP_PORT_V2_HUD_P2].energy = hud_pcm_bench.p2_energy;
    if (!avsp_port_v2_hud_build_frame(&hud_input, &hud_frame))
    {
        ++avsp_diag_hud_asset_failures;
        memset(&hud_frame, 0, sizeof(hud_frame));
    }
    avsp_diag_hud_health = hud_frame.players[AVSP_PORT_V2_HUD_P1].health;
    avsp_diag_hud_energy = hud_frame.players[AVSP_PORT_V2_HUD_P1].energy;
    avsp_diag_hud_health_fill =
        hud_frame.players[AVSP_PORT_V2_HUD_P1].health_fill;
    avsp_diag_hud_energy_fill =
        hud_frame.players[AVSP_PORT_V2_HUD_P1].energy_fill;
    avsp_diag_hud_p2_health = hud_frame.players[AVSP_PORT_V2_HUD_P2].health;
    avsp_diag_hud_p2_energy = hud_frame.players[AVSP_PORT_V2_HUD_P2].energy;
    avsp_diag_hud_p2_health_fill =
        hud_frame.players[AVSP_PORT_V2_HUD_P2].health_fill;
    avsp_diag_hud_p2_energy_fill =
        hud_frame.players[AVSP_PORT_V2_HUD_P2].energy_fill;
#else
    avsp_diag_hud_health = world.player.health;
    avsp_diag_hud_energy = world.weapon_energy;
    avsp_diag_hud_health_fill = hud_pcm_health_fill(world.player.health);
    avsp_diag_hud_energy_fill = hud_pcm_energy_fill(world.weapon_energy);
    avsp_diag_hud_p2_health = hud_pcm_bench.p2_health;
    avsp_diag_hud_p2_energy = hud_pcm_bench.p2_energy;
    avsp_diag_hud_p2_health_fill =
        hud_pcm_health_fill(hud_pcm_bench.p2_health);
    avsp_diag_hud_p2_energy_fill =
        hud_pcm_energy_fill(hud_pcm_bench.p2_energy);
#endif
    avsp_diag_hud_p2_binding_ok =
        hud_pcm_player2_binding_valid(&hud_p2_top_image,
                                      &hud_p2_heat_image);
#ifdef AVSP_HUD_PROMOTION_BENCH
    avsp_diag_hud_render_count = hud_frame.render_count;
    avsp_diag_hud_p2_render_count =
        hud_frame.players[AVSP_PORT_V2_HUD_P2].render_count;
    avsp_diag_hud_port_lock_ok =
        avsp_port_v2_hud_validate_config(&avsp_port_v2_hud_approved_config) &&
        hud_frame.players[AVSP_PORT_V2_HUD_P1].character_id ==
            AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR &&
        hud_frame.players[AVSP_PORT_V2_HUD_P2].character_id ==
            AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER &&
        (phase >= 3 || (hud_frame.render_count == 4 &&
         hud_frame.players[AVSP_PORT_V2_HUD_P2].render_count == 2));
    hud_operations.submit_frame = hud_port_submit_frame;
    if (!avsp_port_v2_hud_submit(&hud_frame, &hud_operations))
        ++avsp_diag_hud_asset_failures;
#else
    avsp_diag_hud_render_count = 0;
    avsp_diag_hud_p2_render_count = 0;
    if (phase < 3)
    {
        draw_arcade_hud();
        avsp_diag_hud_render_count = 4;
        avsp_diag_hud_p2_render_count = 2;
    }
#endif
    avsp_diag_pcm_active = hud_pcm_bench.pcm_active;
    avsp_diag_hud_pcm_canary_ok =
        hud_pcm_bench.head_canary == HUD_PCM_BENCH_CANARY_HEAD &&
        hud_pcm_bench.tail_canary == HUD_PCM_BENCH_CANARY_TAIL;
    avsp_diag_hud_pcm_disc_late_reads =
        avsp_disc_guard_state.late_read_attempts;
    jo_printf(0, 24, "HUDPCM P%d H%d E%d R%d",
              phase, world.player.health, world.weapon_energy,
              avsp_diag_hud_render_count);
    jo_printf(0, 25, "PCM E%d S%d X%d A%d U%d N%d",
              avsp_diag_pcm_event_count, avsp_diag_pcm_start_frame,
              avsp_diag_pcm_end_frame, avsp_diag_pcm_active,
              avsp_diag_pcm_underruns,
              avsp_diag_hud_pcm_negative_rejections);
    /* Publish the frame marker last so debugger-triggered readback observes a
     * complete, internally consistent snapshot for this frame. */
    avsp_diag_hud_pcm_frame = relative;
    ++hud_pcm_bench.frame;
}
#endif

#ifdef AVSP_ENEMY_SALVAGE_BENCH
/* One class-0x1F actor under fixed semantic state.  This bench deliberately
 * advances the extracted animation record and emits its source-derived tile
 * objects, but owns no AI, collision, damage, camera movement, HUD, PCM, or
 * CDDA state. */
static void enemy_bench_init(void)
{
    CapActor *enemy;

    memset(&enemy_bench, 0, sizeof(enemy_bench));
    enemy_bench.head_canary = ENEMY_BENCH_CANARY_HEAD;
    enemy_bench.tail_canary = ENEMY_BENCH_CANARY_TAIL;
    if (avsp_tiles_bank_slot(&tile_archive, 0x1Fu) < 0)
        ++enemy_bench.negative_rejections;
    if (avsp_tiles_find(&tile_archive, 0xFFFFu) < 0)
        ++enemy_bench.negative_rejections;
#ifdef AVSP_ENEMY_PROMOTION_BENCH
#ifndef AVSP_PLAYER_ENEMY_INTEGRATION
    avsp_port_v2_enemy_init(&enemy_port_v2);
#endif
#endif

    cap_world_init(&world);
    world.encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    world.camera_x = 0;
    enemy = &world.enemies[0];
    enemy->x = 192;
    enemy->lane = 200;
    enemy->height = 0;
    enemy->facing = -1;
    enemy->health = 87;
    enemy->action = CAP_ACT_WALK;
    enemy->action_frame = 0;
    enemy->locomotion_frame = 0;
    enemy->active = 1;
    enemy->variant = 1; /* source palette bank 0x11 */
    enemy->kind = CAP_ACTOR_ALIEN;
}

static void enemy_bench_frame_callback(void)
{
    CapActor *enemy = &world.enemies[0];
    int relative = enemy_bench.frame % (ENEMY_BENCH_PHASE_FRAMES * 2);
    int rendered = 0;
#ifdef AVSP_ENEMY_PROMOTION_BENCH
#ifndef AVSP_PLAYER_ENEMY_INTEGRATION
    AvspPortV2EnemyInput promoted_input;
#endif
    AvspPortV2EnemyView promoted_view;
#endif

    if (!runtime_ready)
    {
        avsp_diag_runtime_ready = 0;
        avsp_diag_enemy_asset_failures = 1;
        return;
    }
#ifdef AVSP_ENEMY_PROMOTION_BENCH
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
    avsp_port_v2_enemy_view(&player_enemy_port_v2.enemy, &promoted_view);
#else
    promoted_input.translated = relative >= ENEMY_BENCH_PHASE_FRAMES;
    avsp_port_v2_enemy_step(&enemy_port_v2, &promoted_input);
    avsp_port_v2_enemy_view(&enemy_port_v2, &promoted_view);
#endif
    enemy->x = promoted_view.world_x;
    enemy->lane = promoted_view.lane;
    enemy->facing = promoted_view.facing;
    enemy->locomotion_frame = promoted_view.locomotion_frame;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    enemy->health = combat_port_v2.enemy_health;
    enemy->x = avsp_diag_combat_enemy_x;
    enemy->lane = avsp_diag_combat_enemy_lane;
    enemy->height = avsp_diag_combat_enemy_height;
    enemy->facing = avsp_diag_combat_enemy_facing;
    if (avsp_diag_combat_enemy_visual_action == 1)
        enemy->action = CAP_ACT_HIT;
    else if (avsp_diag_combat_enemy_visual_action == 2)
        enemy->action = CAP_ACT_KO;
    else if (avsp_diag_combat_enemy_visual_action == 3)
        enemy->action = CAP_ACT_HIT;
    else
        enemy->action = CAP_ACT_WALK;
    enemy->action_frame = avsp_diag_combat_enemy_action_frame;
#endif
#else
    enemy->x = relative < ENEMY_BENCH_PHASE_FRAMES ? 192 : 240;
    enemy->locomotion_frame = relative;
#endif
    world.frame = relative;
    world.encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    rom_actor_prepare();
    activate_gameplay_background(0);
    jo_move_background(0, 0);
    if (rom_actor_entry_counts[0] > 0 && tile_archive_ready)
        rendered = draw_rom_actor_tiles(enemy, 0);
    rom_actor_advance();

    avsp_diag_runtime_ready = 1;
    avsp_diag_enemy_interface_version = AVSP_PORT_V2_ENEMY_INTERFACE_VERSION;
    avsp_diag_enemy_phase = relative < ENEMY_BENCH_PHASE_FRAMES ? 0 : 1;
    avsp_diag_enemy_class_id = rom_actor_collision_views[0].class_id;
    avsp_diag_enemy_x = enemy->x;
    avsp_diag_enemy_lane = enemy->lane;
    avsp_diag_enemy_facing = enemy->facing;
    avsp_diag_enemy_anim_record = (int)rom_actor_frames[0].addr;
    avsp_diag_enemy_assembly = (int)rom_actor_frames[0].pose.assembly;
    avsp_diag_enemy_object_count = rom_actor_entry_counts[0];
    avsp_diag_enemy_render_count = rendered;
    avsp_diag_enemy_command_code = rom_actor_entry_counts[0] > 0 ?
        (int)rom_actor_entries_all[0][0].code : -1;
    avsp_diag_enemy_palette_bank = 0x11;
    avsp_diag_enemy_asset_failures = failed_asset == JO_NULL ? 0 : 1;
    avsp_diag_enemy_negative_rejections = enemy_bench.negative_rejections;
    avsp_diag_enemy_canary_ok =
        enemy_bench.head_canary == ENEMY_BENCH_CANARY_HEAD &&
        enemy_bench.tail_canary == ENEMY_BENCH_CANARY_TAIL;
    avsp_diag_enemy_disc_late_reads = avsp_disc_guard_state.late_read_attempts;
    avsp_diag_enemy_tile_bank_misses = tile_diag_no_bank;
    avsp_diag_enemy_tile_rank_misses = tile_diag_no_rank;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    avsp_diag_combat_tile_sprite_misses = tile_diag_no_sprite;
#endif
#ifdef AVSP_ENEMY_PROMOTION_BENCH
    avsp_diag_enemy_approval_lock_ok = avsp_port_v2_enemy_validate_config(
        &avsp_port_v2_enemy_approved_config);
#endif
    /* Publish last so debugger breakpoints observe one coherent frame. */
    avsp_diag_enemy_frame = relative;
    ++enemy_bench.frame;
}
#endif

static CapInput read_input(void)
{
    CapInput input;
    input.left = jo_is_pad1_key_pressed(JO_KEY_LEFT);
    input.right = jo_is_pad1_key_pressed(JO_KEY_RIGHT);
    input.up = jo_is_pad1_key_pressed(JO_KEY_UP);
    input.down = jo_is_pad1_key_pressed(JO_KEY_DOWN);
    input.shoot_pressed = jo_is_pad1_key_down(JO_KEY_A);
    input.attack_pressed = jo_is_pad1_key_down(JO_KEY_B);
    input.jump_pressed = jo_is_pad1_key_down(JO_KEY_C);
    input.start_pressed = jo_is_pad1_key_down(JO_KEY_START);
    return input;
}

#ifdef AVSP_PLAYER_SALVAGE_BENCH
/* The prototype's pure player-only limits are retained as a deliberately
 * fixed-camera presentation window, translated around the 384px source
 * centre.  This is an adapter for exercising the existing presentation path,
 * not a replacement gameplay input or movement system. */
#define PLAYER_BENCH_MIN_X 48
#define PLAYER_BENCH_MAX_X 304
#define PLAYER_BENCH_MIN_LANE 138
#define PLAYER_BENCH_MAX_LANE 218

#ifndef AVSP_PLAYER_PROMOTION_BENCH
static int player_bench_input_mask(const CapInput *input)
{
    return (input->left ? 1 : 0) |
           (input->right ? 2 : 0) |
           (input->up ? 4 : 0) |
           (input->down ? 8 : 0) |
           (input->shoot_pressed ? 16 : 0) |
           (input->attack_pressed ? 32 : 0) |
           (input->jump_pressed ? 64 : 0) |
           (input->start_pressed ? 128 : 0);
}
#endif

static void player_bench_init(void)
{
    memset(&player_bench, 0, sizeof(player_bench));
    player_bench.head_canary = PLAYER_BENCH_CANARY_HEAD;
    player_bench.tail_canary = PLAYER_BENCH_CANARY_TAIL;
#ifdef AVSP_PLAYER_PROMOTION_BENCH
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    avsp_combat_diagnostic_init(&combat_port_v2);
    combat_last_event_count = 0;
#else
    avsp_port_v2_player_enemy_init(&player_enemy_port_v2);
#endif
    player_bench.actor.x = player_enemy_port_v2.player.x;
    player_bench.actor.lane = player_enemy_port_v2.player.lane;
    player_bench.actor.facing = player_enemy_port_v2.player.facing;
#else
    avsp_port_v2_player_init(&player_port_v2);
    player_bench.actor.x = player_port_v2.x;
    player_bench.actor.lane = player_port_v2.lane;
    player_bench.actor.facing = player_port_v2.facing;
#endif
#else
    player_bench.actor.x = 192;
    player_bench.actor.lane = 178;
    player_bench.actor.facing = 1;
#endif
    player_bench.actor.action = CAP_ACT_IDLE;
    player_bench.actor.active = 1;
    player_bench.actor.kind = CAP_ACTOR_PLAYER;
    player_bench_frame = 0;
#ifndef AVSP_PLAYER_PROMOTION_BENCH
    player_bench_previous_input = 0;
#endif
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
    enemy_bench_init();
#endif
}

static void player_bench_step(const CapInput *input)
{
    CapActor *actor = &player_bench.actor;
#ifdef AVSP_PLAYER_PROMOTION_BENCH
    AvspPortV2PlayerInput promoted_input;
    AvspPortV2PlayerView promoted_view;
    promoted_input.left = input->left;
    promoted_input.right = input->right;
    promoted_input.up = input->up;
    promoted_input.down = input->down;
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
    {
        AvspPortV2PlayerEnemyInput integration_input;
        integration_input.player = promoted_input;
        integration_input.enemy_translated =
            enemy_bench.frame % (ENEMY_BENCH_PHASE_FRAMES * 2) >=
            ENEMY_BENCH_PHASE_FRAMES;
        avsp_port_v2_player_enemy_step(&player_enemy_port_v2,
                                       &integration_input);
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
        avsp_combat_diagnostic_step(&combat_port_v2);
        if (avsp_diag_combat_event_count != combat_last_event_count)
        {
            tile_diag_no_bank = 0;
            tile_diag_no_rank = 0;
            tile_diag_no_sprite = 0;
            avsp_diag_combat_missing_code_count = 0;
            combat_last_event_count = avsp_diag_combat_event_count;
        }
#endif
        avsp_port_v2_player_view(&player_enemy_port_v2.player,
                                 &promoted_view);
    }
#else
    avsp_port_v2_player_step(&player_port_v2, &promoted_input);
    avsp_port_v2_player_view(&player_port_v2, &promoted_view);
#endif
    actor->x = promoted_view.world_x;
    actor->lane = promoted_view.lane;
    actor->facing = promoted_view.facing;
    actor->action = promoted_view.action == AVSP_PORT_V2_PLAYER_ACTION_WALK ?
        CAP_ACT_WALK : CAP_ACT_IDLE;
    actor->action_frame = 0;
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
    actor->x = avsp_diag_combat_player_x;
    actor->lane = avsp_diag_combat_player_lane;
    actor->height = avsp_diag_combat_player_height;
    actor->facing = avsp_diag_combat_player_facing;
#ifdef AVSP_PLAYABLE_SLICE
    if (avsp_diag_combat_player_attack_active)
#else
    if (avsp_diag_combat_player_presentation_active)
#endif
    {
        actor->action = CAP_ACT_ATTACK;
        actor->action_frame = avsp_diag_combat_player_action_frame;
    }
#endif
    actor->locomotion_frame = promoted_view.locomotion_frame;
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
    avsp_diag_player_input_mask = player_enemy_port_v2.player.input_mask;
    avsp_diag_player_input_edges = player_enemy_port_v2.player.input_edges;
#else
    avsp_diag_player_input_mask = player_port_v2.input_mask;
    avsp_diag_player_input_edges = player_port_v2.input_edges;
#endif
#else
    int moving = 0;
    int mask = player_bench_input_mask(input);

    if (input->left && !input->right)
    {
        actor->x -= 2;
        actor->facing = -1;
        moving = 1;
    }
    else if (input->right && !input->left)
    {
        actor->x += 2;
        actor->facing = 1;
        moving = 1;
    }
    if (input->up && !input->down)
    {
        --actor->lane;
        moving = 1;
    }
    else if (input->down && !input->up)
    {
        ++actor->lane;
        moving = 1;
    }
    if (actor->x < PLAYER_BENCH_MIN_X) actor->x = PLAYER_BENCH_MIN_X;
    if (actor->x > PLAYER_BENCH_MAX_X) actor->x = PLAYER_BENCH_MAX_X;
    if (actor->lane < PLAYER_BENCH_MIN_LANE) actor->lane = PLAYER_BENCH_MIN_LANE;
    if (actor->lane > PLAYER_BENCH_MAX_LANE) actor->lane = PLAYER_BENCH_MAX_LANE;
    actor->action = moving ? CAP_ACT_WALK : CAP_ACT_IDLE;
    actor->action_frame = 0;
    if (moving) ++actor->locomotion_frame;

    avsp_diag_player_input_mask = mask;
    /* Hold a newly seen edge through the active press so MCP sampling cannot
     * lose a one-frame event between debugger requests.  Releasing returns
     * the diagnostic to zero before the next input case. */
    if (mask == 0)
        avsp_diag_player_input_edges = 0;
    else
        avsp_diag_player_input_edges |= mask & ~player_bench_previous_input;
    player_bench_previous_input = mask;
#endif
}

static void player_bench_frame_callback(void)
{
    CapInput input;
    CapActor *actor = &player_bench.actor;
    int pose = -1;

    if (!runtime_ready)
    {
        avsp_diag_runtime_ready = 0;
        avsp_diag_player_asset_failures = 1;
        jo_printf(1, 12, "PLAYER BENCH FAILED: %s",
                  failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
    input = read_input();
    player_bench_step(&input);
    jo_move_background(0, 0);
    jo_sprite_change_sprite_scale_xy(
        (float)CAP_VIEW_WIDTH / (float)CAP_CPS2_VIEW_WIDTH, 1.0f);
    draw_player(actor, cap_actor_screen_x(actor->x, 0, 1));
    jo_sprite_restore_sprite_scale();
    if (actor->action == CAP_ACT_WALK)
    {
        int frame = actor->locomotion_frame %
            avsp_player_action_total_frames[AVSP_PLAYER_CLIP_WALK];
        pose = player_pose_for_frame(AVSP_PLAYER_CLIP_WALK, frame);
    }
    ++player_bench_frame;
    avsp_diag_runtime_ready = 1;
    avsp_diag_player_frame = player_bench_frame;
    avsp_diag_player_x = actor->x;
    avsp_diag_player_lane = actor->lane;
    avsp_diag_player_facing = actor->facing;
    avsp_diag_player_pose = pose;
    avsp_diag_player_pivot_y = actor->lane - 200 - actor->height;
    if (pose < 0)
    {
        /* Measured isolated idle frame 2525 selected-command extent. */
        avsp_diag_player_cel_left = 56;
        avsp_diag_player_cel_top = 74;
        avsp_diag_player_cel_right = 136;
        avsp_diag_player_cel_bottom = 184;
    }
    else
    {
        avsp_diag_player_cel_left = avsp_player_action_canvas_bounds[pose][0];
        avsp_diag_player_cel_top = avsp_player_action_canvas_bounds[pose][1];
        avsp_diag_player_cel_right = avsp_player_action_canvas_bounds[pose][2];
        avsp_diag_player_cel_bottom = avsp_player_action_canvas_bounds[pose][3];
    }
    avsp_diag_player_render_count = actor->action == CAP_ACT_WALK ?
        AVSP_PLAYER_ACTION_LAYERS : 2;
    avsp_diag_player_canary_ok =
        player_bench.head_canary == PLAYER_BENCH_CANARY_HEAD &&
        player_bench.tail_canary == PLAYER_BENCH_CANARY_TAIL;
    avsp_diag_player_asset_failures = failed_asset == JO_NULL ? 0 : 1;
    avsp_diag_player_disc_late_reads = avsp_disc_guard_state.late_read_attempts;
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
    {
        AvspPortV2PlayerEnemyView integration_view;
    enemy_bench_frame_callback();
        avsp_port_v2_player_enemy_view(&player_enemy_port_v2,
                                       &integration_view);
    avsp_diag_integration_interface_version = AVSP_PORT_V2_PLAYER_ENEMY_INTERFACE_VERSION;
    avsp_diag_integration_approval_locks_ok = avsp_port_v2_player_enemy_approvals_valid();
        avsp_diag_integration_actor_count = integration_view.actor_count;
        avsp_diag_integration_render_order_ok =
            avsp_port_v2_player_enemy_render_order_valid(
                integration_view.render_order, integration_view.actor_count);
        avsp_diag_integration_render_command_count =
            avsp_diag_player_render_count + avsp_diag_enemy_render_count;
        avsp_diag_integration_canaries_ok =
            avsp_diag_player_canary_ok && avsp_diag_enemy_canary_ok;
        avsp_diag_integration_asset_failures =
            avsp_diag_player_asset_failures + avsp_diag_enemy_asset_failures;
        avsp_diag_integration_disc_late_reads =
            avsp_diag_player_disc_late_reads +
            avsp_diag_enemy_disc_late_reads;
        {
            int sample_index = -1;
            volatile AvspIntegrationDiagnosticSample *sample;
            if (avsp_diag_integration_sample_count == 0 &&
                avsp_diag_enemy_frame == 20)
                sample_index = 0;
            else if (avsp_diag_integration_sample_count == 1 &&
                     avsp_diag_enemy_frame == 140)
                sample_index = 1;
            else if (avsp_diag_integration_sample_count == 2 &&
                     avsp_diag_enemy_frame == 20)
                sample_index = 2;
            if (sample_index >= 0)
            {
                sample = &avsp_diag_integration_samples[sample_index];
                sample->source_frame = avsp_diag_enemy_frame;
                sample->player_x = avsp_diag_player_x;
                sample->player_lane = avsp_diag_player_lane;
                sample->player_facing = avsp_diag_player_facing;
                sample->player_pose = avsp_diag_player_pose;
                sample->player_cel_left = avsp_diag_player_cel_left;
                sample->player_cel_top = avsp_diag_player_cel_top;
                sample->player_cel_right = avsp_diag_player_cel_right;
                sample->player_cel_bottom = avsp_diag_player_cel_bottom;
                sample->player_render_count = avsp_diag_player_render_count;
                sample->player_canary_ok = avsp_diag_player_canary_ok;
                sample->player_asset_failures =
                    avsp_diag_player_asset_failures;
                sample->player_disc_late_reads =
                    avsp_diag_player_disc_late_reads;
                sample->player_interface_version =
                    avsp_diag_player_interface_version;
                sample->player_approval_lock_ok =
                    avsp_diag_player_approval_lock_ok;
                sample->player_loader_adapter_ok =
                    avsp_diag_player_loader_adapter_ok;
                sample->enemy_phase = avsp_diag_enemy_phase;
                sample->enemy_class_id = avsp_diag_enemy_class_id;
                sample->enemy_x = avsp_diag_enemy_x;
                sample->enemy_lane = avsp_diag_enemy_lane;
                sample->enemy_facing = avsp_diag_enemy_facing;
                sample->enemy_anim_record = avsp_diag_enemy_anim_record;
                sample->enemy_assembly = avsp_diag_enemy_assembly;
                sample->enemy_object_count = avsp_diag_enemy_object_count;
                sample->enemy_render_count = avsp_diag_enemy_render_count;
                sample->enemy_palette_bank = avsp_diag_enemy_palette_bank;
                sample->enemy_canary_ok = avsp_diag_enemy_canary_ok;
                sample->enemy_asset_failures =
                    avsp_diag_enemy_asset_failures;
                sample->enemy_disc_late_reads =
                    avsp_diag_enemy_disc_late_reads;
                sample->enemy_tile_bank_misses =
                    avsp_diag_enemy_tile_bank_misses;
                sample->enemy_tile_rank_misses =
                    avsp_diag_enemy_tile_rank_misses;
                sample->enemy_interface_version =
                    avsp_diag_enemy_interface_version;
                sample->enemy_negative_rejections =
                    avsp_diag_enemy_negative_rejections;
                sample->enemy_approval_lock_ok =
                    avsp_diag_enemy_approval_lock_ok;
                sample->enemy_loader_adapter_ok =
                    avsp_diag_enemy_loader_adapter_ok;
                sample->integration_interface_version =
                    avsp_diag_integration_interface_version;
                sample->integration_approval_locks_ok =
                    avsp_diag_integration_approval_locks_ok;
                sample->integration_loader_order_ok =
                    avsp_diag_integration_loader_order_ok;
                sample->integration_actor_count =
                    avsp_diag_integration_actor_count;
                sample->integration_render_order_ok =
                    avsp_diag_integration_render_order_ok;
                sample->integration_render_command_count =
                    avsp_diag_integration_render_command_count;
                sample->integration_canaries_ok =
                    avsp_diag_integration_canaries_ok;
                sample->integration_asset_failures =
                    avsp_diag_integration_asset_failures;
                sample->integration_disc_late_reads =
                    avsp_diag_integration_disc_late_reads;
                /* Publish the count only after the complete sample. */
                avsp_diag_integration_sample_count = sample_index + 1;
            }
        }
#ifdef AVSP_COMBAT_INTEGRATION_BENCH
        /* MCP reads the diagnostic symbols directly.  Text rows 20-23 used
         * to obscure the actor pixels and updated on a separate UI cadence,
         * making a clean paired visual trace impossible. */
        avsp_diag_combat_presented_frame = avsp_diag_combat_frame;
#endif
        /* Publish last so MCP observes one complete integration snapshot. */
        avsp_diag_integration_frame[0] = avsp_diag_enemy_frame;
    }
#endif
#ifdef AVSP_PLAYER_PROMOTION_BENCH
    avsp_diag_player_interface_version = AVSP_PORT_V2_PLAYER_INTERFACE_VERSION;
    avsp_diag_player_approval_lock_ok =
        avsp_port_v2_player_validate_config(
            &avsp_port_v2_player_approved_config) &&
        avsp_port_v2_player_bounds_valid(
            avsp_diag_player_cel_left, avsp_diag_player_cel_top,
            avsp_diag_player_cel_right, avsp_diag_player_cel_bottom);
#endif
}
#endif

#ifdef AVSP_ENCOUNTER_TEST
static int active_enemy_count(void)
{
    int count = 0;
    int index;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        if (world.enemies[index].active) ++count;
    return count;
}

static CapInput encounter_test_input(void)
{
    CapInput input;
    int index;
    memset(&input, 0, sizeof(input));
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
    {
        if (world.frame >= 120) input.start_pressed = 1;
        return input;
    }
    if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        if (world.frame >= 240) input.attack_pressed = 1;
        return input;
    }
    /* Prove both contact composites without sacrificing deterministic route
       completion: accept one normal hit, arm the next contact as lethal, then
       restore the diagnostic's usual invulnerability after the KO cue fires. */
    if (contact_audio_play_count > 0 && ko_contact_audio_play_count == 0)
        world.player.health = CAP_ENEMY_CONTACT_DAMAGE;
    else
        world.player.health = CAP_PLAYER_MAX_HEALTH;
    if (world.encounter_state == CAP_ENCOUNTER_WAVE_ONE ||
        world.encounter_state == CAP_ENCOUNTER_WAVE_TWO ||
        world.encounter_state == CAP_ENCOUNTER_BOSS)
    {
        if (world.encounter_state == CAP_ENCOUNTER_BOSS &&
            world.encounter_timer < 600)
            return input;
        /* Exercise the natural 40-frame Chrysalis hit clip before the
           diagnostic starts its deterministic one-hit clear. One B edge at
           timer 600 lands at the captured melee contact offset; keeping four
           health leaves the boss alive at one health for the full reaction. */
        if (world.encounter_state == CAP_ENCOUNTER_BOSS &&
            world.encounter_timer < 680)
        {
            CapActor *boss = &world.enemies[0];
            boss->x = world.player.x + 34;
            boss->lane = world.player.lane;
            if (boss->action != CAP_ACT_HIT) boss->health = 4;
            if (world.encounter_timer == 600)
                input.attack_pressed = 1;
            return input;
        }
        /* Keep the five-enemy opening wave visible long enough to inspect
           after a real BIOS/CD boot before the automated clear begins. */
        if (world.frame >= 600)
        {
            for (index = 0; index < CAP_MAX_ENEMIES; ++index)
            {
                CapActor *enemy = &world.enemies[index];
                if (!enemy->active || enemy->action == CAP_ACT_KO) continue;
                if (ko_contact_audio_play_count > 0 &&
                    enemy->action == CAP_ACT_ATTACK)
                {
                    /* The diagnostic has already proven normal and KO
                       contact. Cancel later windups so the forced respawn is
                       not permanently hit-locked by six adjacent actors. */
                    enemy->action = CAP_ACT_IDLE;
                    enemy->action_frame = 0;
                    enemy->hit_latched = 0;
                }
                enemy->x = world.player.x + 34 + (index & 1) * 8;
                enemy->lane = world.player.lane;
                enemy->health = 1;
            }
            if (world.player.action == CAP_ACT_IDLE ||
                world.player.action == CAP_ACT_WALK)
            {
                if (world.shots_fired == 0)
                    input.shoot_pressed = 1;
                else
                    input.attack_pressed = 1;
            }
        }
    }
    else if (world.encounter_state == CAP_ENCOUNTER_CLEAR)
        input.right = 1;
    return input;
}
#endif

#ifdef AVSP_FRONTEND_TEST
static CapInput frontend_test_input(void)
{
    CapInput input;
    memset(&input, 0, sizeof(input));
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
    {
        if (world.frame == 120) input.start_pressed = 1;
    }
    else if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        /* Warrior -> Schaefer -> Hunter, with releases between source edges. */
        if (world.frame == 180) input.right = 1;
        if (world.frame == 200) input.down = 1;
        if (world.frame == 240) input.jump_pressed = 1;
    }
    return input;
}
#endif

#ifdef AVSP_FRONTEND_SHOT_TEST
/* Same source semantics as the focused frontend route, but keyed to the
 * encounter timer and extended to settle on every one of the four cursor
 * positions. The source has no cancel action, so the walk is right, down,
 * left, which visits Warrior, Schaefer, Hunter and Linn in turn. */
static CapInput frontend_shot_input(void)
{
    CapInput input;
    memset(&input, 0, sizeof(input));
    if (world.encounter_state == CAP_ENCOUNTER_MAIN_MENU)
    {
        if (avsp_shot_state_frames == 120) input.start_pressed = 1;
    }
    else if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT)
    {
        if (avsp_shot_state_frames == 40) input.right = 1;
        if (avsp_shot_state_frames == 80) input.down = 1;
        if (avsp_shot_state_frames == 120) input.left = 1;
        if (avsp_shot_state_frames == 160) input.jump_pressed = 1;
    }
    return input;
}
#endif

static void draw_hud(void)
{
    if (!debug_hud_enabled) return;
    jo_printf(0, 0, "AVP CPS2 -> SATURN NATIVE SLICE");
    jo_printf(0, 1, "ROUND 1 CITY OF DESPAIR  HP %02d", world.player.health);
    jo_printf(0, 2, "SCORE %05d  KO %d/%d  CART %s",
              world.score, world.enemies_defeated, CAP_STAGE1_TOTAL_ENEMIES,
              cart_available ? "4MB" : "FAIL");
    jo_printf(0, 3, "VDP1 %02d%% EXACT CPS2 PALETTE LAYERS",
              jo_sprite_usage_percent());
    jo_printf(0, 4, "VIEW FULL FIT  X HUD");
    jo_printf(0, 5, "ROOM %d  LOCK %d  EXIT %d",
              world.encounter_state, world.room_locked, world.stage_transitioned);
    if (world.encounter_state == CAP_ENCOUNTER_BOSS && world.enemies[0].active)
        jo_printf(0, 6, "CHRYSALIS HP %02d/%02d", world.enemies[0].health,
                   CAP_BOSS_MAX_HEALTH);
    if (world.stage_area == 1)
        jo_printf(0, 7, "STALKER %d/%d  WAVE %d/2",
                  world.boss_adds_defeated, world.boss_adds_spawned,
                  world.boss_reinforcement_wave);
    jo_printf(0, 27, "D-PAD MOVE  A GUN  B ATTACK  C JUMP/DASH");
}

static void draw_route_overlay(void)
{
    if (world.encounter_state == CAP_ENCOUNTER_CLEAR)
        jo_printf(35, 12, "GO >>>");
}

#ifdef AVSP_COLLISION_SALVAGE_BENCH
static int collision_bench_init(void)
{
    AvspCollisionBenchResult result;
    int case_id;

    memset(&collision_bench_state, 0, sizeof(collision_bench_state));
    collision_bench_state.head_canary = COLLISION_BENCH_CANARY_HEAD;
    collision_bench_state.tail_canary = COLLISION_BENCH_CANARY_TAIL;
    avsp_diag_collision_sample_count = 0;
    for (case_id = 0; case_id < AVSP_COLLISION_CASE_COUNT; ++case_id) {
        if (!avsp_collision_bench_evaluate(case_id, &result) ||
            !avsp_collision_bench_result_ok(&result)) {
            ++collision_bench_state.failures;
        }
        else if (!result.expected_overlap || result.expected_guarded) {
            ++collision_bench_state.negative_rejections;
        }
        avsp_diag_collision_samples[case_id] = result;
        avsp_diag_collision_sample_count = case_id + 1;
    }
    return collision_bench_state.failures == 0 &&
           collision_bench_state.negative_rejections == 8;
}

static void collision_bench_frame_callback(void)
{
    AvspCollisionBenchResult result;
    int case_id;

    case_id = (collision_bench_state.frame / 60) %
              AVSP_COLLISION_CASE_COUNT;
    if (!avsp_collision_bench_evaluate(case_id, &result) ||
        !avsp_collision_bench_result_ok(&result)) {
        ++collision_bench_state.failures;
    }
    ++collision_bench_state.frame;
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_collision_interface_version = 1;
    avsp_diag_collision_frame = collision_bench_state.frame;
    avsp_diag_collision_case = result.case_id;
    avsp_diag_collision_overlap = result.overlap;
    avsp_diag_collision_expected_overlap = result.expected_overlap;
    avsp_diag_collision_guarded = result.guarded;
    avsp_diag_collision_expected_guarded = result.expected_guarded;
    avsp_diag_collision_hit_value = result.hit_value;
    avsp_diag_collision_table_set_ok = result.table_set_ok;
    avsp_diag_collision_negative_rejections =
        collision_bench_state.negative_rejections;
    avsp_diag_collision_damage_writes = result.damage_write_count;
    avsp_diag_collision_failures = collision_bench_state.failures;
    avsp_diag_collision_canary_ok =
        collision_bench_state.head_canary == COLLISION_BENCH_CANARY_HEAD &&
        collision_bench_state.tail_canary == COLLISION_BENCH_CANARY_TAIL;
    jo_printf(2, 3, "SALVAGE-03 COLLISION");
    jo_printf(2, 5, "SOURCE 01D25E-01D312");
    jo_printf(2, 7, "CASE %02d OVERLAP %d/%d", result.case_id,
              result.overlap, result.expected_overlap);
    jo_printf(2, 8, "GUARD %d/%d HIT %d", result.guarded,
              result.expected_guarded, result.hit_value);
    jo_printf(2, 10, "TABLE 130AC8 %s",
              result.table_set_ok ? "PASS" : "FAIL");
    jo_printf(2, 12, "NEGATIVE CONTROLS %d/8",
              collision_bench_state.negative_rejections);
    jo_printf(2, 14, "DAMAGE HIT KO WRITES %d",
              result.damage_write_count);
    jo_printf(2, 16, "CANARY %s FAILURES %d",
              avsp_diag_collision_canary_ok ? "PASS" : "FAIL",
              collision_bench_state.failures);
    jo_printf(2, 18, "PHYSICAL SATURN UNRUN");
}
#endif

#if defined(AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH) || \
    defined(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH)
static int pw_action_bench_init(void)
{
    AvspPwAttackDef mutation[AVSP_PW_ACTION_COUNT];
    memset(&pw_action_state, 0, sizeof(pw_action_state));
    pw_action_state.head_canary = PW_ACTION_CANARY_HEAD;
    pw_action_state.tail_canary = PW_ACTION_CANARY_TAIL;
    avsp_pw_init(&pw_action_state.runtime);
    avsp_diag_pw_action_sample_count = 0;
    avsp_diag_pw_action_failures = 0;
    avsp_diag_pw_action_negative_rejections = 0;
    if (!avsp_pw_action_defs_valid(avsp_pw_action_defs,
                                   AVSP_PW_ACTION_COUNT))
        ++avsp_diag_pw_action_failures;
    if (!avsp_pw_action_defs_valid(avsp_pw_action_defs,
                                   AVSP_PW_ACTION_COUNT - 1u))
        ++avsp_diag_pw_action_negative_rejections;
    memcpy(mutation, avsp_pw_action_defs, sizeof(mutation));
    mutation[3].box.z_half = 11;
    if (!avsp_pw_action_defs_valid(mutation, AVSP_PW_ACTION_COUNT))
        ++avsp_diag_pw_action_negative_rejections;
    return avsp_diag_pw_action_failures == 0 &&
           avsp_diag_pw_action_negative_rejections == 2;
}

static AvspPwInput pw_action_bench_input(const int frame)
{
    AvspPwInput input;
    input.mask = 0u;
    input.received_damage = 0;
    if (frame >= 0 && frame < 20) input.mask |= AVSP_PW_INPUT_RIGHT;
    if (frame >= 30 && frame < 50) input.mask |= AVSP_PW_INPUT_UP;
    if (frame == 80 || frame == 125 || frame == 170 || frame == 215)
        input.mask |= AVSP_PW_INPUT_ATTACK;
    if (frame == 270) input.received_damage = 8;
    if (frame == 310) input.received_damage = 100;
    return input;
}

static void pw_action_bench_frame_callback(void)
{
    AvspPwDiagnosticSample sample;
    AvspPwInput input;
    AvspPwView view;
    int frame;
    frame = avsp_diag_pw_action_frame;
    if (frame < PW_ACTION_CAPTURE_FRAMES)
    {
        input = pw_action_bench_input(frame);
        avsp_pw_step(&pw_action_state.runtime, &input);
        if (pw_action_state.runtime.attack_active)
            avsp_pw_report_contact(&pw_action_state.runtime);
        avsp_pw_view(&pw_action_state.runtime, &view);
        sample.frame = frame;
        sample.input_mask = input.mask;
        sample.x = view.x;
        sample.lane = view.lane;
        sample.height = view.height;
        sample.health = view.health;
        sample.facing = view.facing;
        sample.state = view.state;
        sample.phase = view.phase;
        sample.selector = view.selector;
        sample.action_elapsed = view.action_elapsed;
        sample.source_action = view.source_action;
        sample.source_substate = view.source_substate;
        sample.attack_active = view.attack_active;
        sample.box_x_center = view.attack_box.x_center;
        sample.box_x_half = view.attack_box.x_half;
        sample.box_y_center = view.attack_box.y_center;
        sample.box_y_half = view.attack_box.y_half;
        sample.box_z_center = view.attack_box.z_center;
        sample.box_z_half = view.attack_box.z_half;
        sample.hit_value = view.attack_box.hit_value;
        avsp_diag_pw_action_samples[frame] = sample;
        avsp_diag_pw_action_sample_count = frame + 1;
        ++avsp_diag_pw_action_frame;
    }
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_pw_action_interface_version =
        AVSP_PW_ACTION_BENCH_INTERFACE_VERSION;
    avsp_diag_pw_action_canary_ok =
        pw_action_state.head_canary == PW_ACTION_CANARY_HEAD &&
        pw_action_state.tail_canary == PW_ACTION_CANARY_TAIL;
    avsp_diag_pw_action_accepted_edges =
        (int)pw_action_state.runtime.accepted_attack_edges;
    avsp_diag_pw_action_rejected_edges =
        (int)pw_action_state.runtime.rejected_attack_edges;
    avsp_diag_pw_action_contact_reports =
        (int)pw_action_state.runtime.contact_reports;
    jo_printf(2, 3, "SALVAGE-10 P WARRIOR ACTION");
    jo_printf(2, 5, "FRAME %03d SAMPLE %03d", avsp_diag_pw_action_frame,
              avsp_diag_pw_action_sample_count);
    jo_printf(2, 7, "POS %d,%d H %d HP %d", pw_action_state.runtime.x,
              pw_action_state.runtime.lane, pw_action_state.runtime.height,
              pw_action_state.runtime.health);
    jo_printf(2, 9, "STATE %d PHASE %d SEL %d T %d",
              pw_action_state.runtime.state, pw_action_state.runtime.phase,
              pw_action_state.runtime.selector,
              pw_action_state.runtime.action_elapsed);
    jo_printf(2, 11, "EDGES %d REJECT %d CONTACT %d",
              avsp_diag_pw_action_accepted_edges,
              avsp_diag_pw_action_rejected_edges,
              avsp_diag_pw_action_contact_reports);
    jo_printf(2, 13, "NEG %d/2 CANARY %s FAIL %d",
              avsp_diag_pw_action_negative_rejections,
              avsp_diag_pw_action_canary_ok ? "PASS" : "FAIL",
              avsp_diag_pw_action_failures);
    jo_printf(2, 15, "PHYSICAL SATURN UNRUN");
}
#endif

#if defined(AVSP_STREET_ALIEN_AI_SALVAGE_BENCH) || \
    defined(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH)
static int alien_ai_bench_init(void)
{
    memset(&alien_ai_state, 0, sizeof(alien_ai_state));
    alien_ai_state.head_canary = ALIEN_AI_CANARY_HEAD;
    alien_ai_state.tail_canary = ALIEN_AI_CANARY_TAIL;
    avsp_alien_ai_init(&alien_ai_state.runtime, 0x7301u);
    avsp_diag_alien_ai_frame = 0;
    avsp_diag_alien_ai_sample_count = 0;
    avsp_diag_alien_ai_failures = 0;
    avsp_diag_alien_ai_negative_rejections = 0;
    if (!avsp_alien_ai_contract_valid()) ++avsp_diag_alien_ai_failures;
    if (avsp_alien_ai_rng_step(0x7301u) != 0x595bu)
        ++avsp_diag_alien_ai_negative_rejections;
    if (avsp_alien_ai_timer_for_seed(0x595au) != 30u)
        ++avsp_diag_alien_ai_negative_rejections;
    return avsp_diag_alien_ai_failures == 0 &&
           avsp_diag_alien_ai_negative_rejections == 2;
}

static AvspAlienInput alien_ai_bench_input(const int frame)
{
    AvspAlienInput input;
    input.target.active = 1u;
    input.target.id = 1u;
    input.target.x = 1200;
    input.target.lane = 320;
    input.incoming_damage = 0;
    if (frame == 300) input.incoming_damage = 24;
    if (frame == 400) input.incoming_damage = 64;
    return input;
}

static void alien_ai_bench_frame_callback(void)
{
    AvspAlienAiDiagnosticSample sample;
    AvspAlienInput input;
    AvspAlienView view;
    int frame;
    frame = avsp_diag_alien_ai_frame;
    if (frame < ALIEN_AI_CAPTURE_FRAMES)
    {
        input = alien_ai_bench_input(frame);
        avsp_alien_ai_step(&alien_ai_state.runtime, &input);
        avsp_alien_ai_view(&alien_ai_state.runtime, &view);
        sample.frame = frame;
        sample.target_active = input.target.active;
        sample.target_x = input.target.x;
        sample.target_lane = input.target.lane;
        sample.state = view.state;
        sample.inner_state = view.inner_state;
        sample.target_id = view.target_id;
        sample.x = view.x;
        sample.lane = view.lane;
        sample.health = view.health;
        sample.facing = view.facing;
        sample.approach_elapsed = view.approach_elapsed;
        sample.attack_elapsed = view.attack_elapsed;
        sample.attack_timer = view.attack_timer;
        sample.rng_seed = view.rng_seed;
        sample.rng_cursor = view.rng_cursor;
        sample.contact = view.contact;
        sample.contact_damage = view.contact_damage;
        sample.removed = view.removed;
        avsp_diag_alien_ai_samples[frame] = sample;
        avsp_diag_alien_ai_sample_count = frame + 1;
        ++avsp_diag_alien_ai_frame;
    }
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_alien_ai_interface_version = AVSP_ALIEN_AI_INTERFACE_VERSION;
    avsp_diag_alien_ai_canary_ok =
        alien_ai_state.head_canary == ALIEN_AI_CANARY_HEAD &&
        alien_ai_state.tail_canary == ALIEN_AI_CANARY_TAIL;
    avsp_diag_alien_ai_contacts = (int)alien_ai_state.runtime.contacts;
    avsp_diag_alien_ai_damage_events =
        (int)alien_ai_state.runtime.damage_events;
    avsp_diag_alien_ai_scheduler_updates =
        (int)alien_ai_state.runtime.scheduler_updates;
    avsp_diag_alien_ai_target_selections =
        (int)alien_ai_state.runtime.target_selections;
    jo_printf(2, 3, "SALVAGE-11 STREET ALIEN AI");
    jo_printf(2, 5, "FRAME %03d SAMPLE %03d", avsp_diag_alien_ai_frame,
              avsp_diag_alien_ai_sample_count);
    jo_printf(2, 7, "STATE %d INNER %d TARGET %d",
              alien_ai_state.runtime.state, alien_ai_state.runtime.inner_state,
              alien_ai_state.runtime.target_id);
    jo_printf(2, 9, "POS %d,%d HP %d FACE %d", alien_ai_state.runtime.x,
              alien_ai_state.runtime.lane, alien_ai_state.runtime.health,
              alien_ai_state.runtime.facing);
    jo_printf(2, 11, "RNG %04x CUR %d ATK %d/%d",
              alien_ai_state.runtime.rng_seed,
              alien_ai_state.runtime.rng_cursor,
              alien_ai_state.runtime.attack_elapsed,
              alien_ai_state.runtime.attack_timer);
    jo_printf(2, 13, "CONTACT %d DAMAGE %d UPDATE %d",
              avsp_diag_alien_ai_contacts, avsp_diag_alien_ai_damage_events,
              avsp_diag_alien_ai_scheduler_updates);
    jo_printf(2, 15, "NEG %d/2 CANARY %s FAIL %d",
              avsp_diag_alien_ai_negative_rejections,
              avsp_diag_alien_ai_canary_ok ? "PASS" : "FAIL",
              avsp_diag_alien_ai_failures);
    jo_printf(2, 17, "PHYSICAL SATURN UNRUN");
}
#endif

#ifdef AVSP_CDDA_RESIDENCY_SALVAGE_BENCH
#ifdef AVSP_CDDA_RESIDENCY_PROMOTION_BENCH
static int cdda_residency_read_buffer_ok(void)
{
    static const unsigned char expected[
        AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES] =
        "AVSP-CDDA-RESIDENCY-V1|TRACK=02|WINDOW=PHASE-BOUNDARY|OK!!!!!!!\n";
    return cdda_residency_read_buffer.head_canary ==
               AVSP_PORT_V2_RESIDENCY_CANARY_HEAD &&
           cdda_residency_read_buffer.tail_canary ==
               AVSP_PORT_V2_RESIDENCY_CANARY_TAIL &&
           memcmp(cdda_residency_read_buffer.bytes, expected,
                  AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES) == 0;
}

static int cdda_port_start(const AvspPortV2CddaFrame *frame)
{
    jo_audio_play_cd_track(frame->track, frame->track,
                           frame->repeat != 0);
    avsp_disc_guard_cdda_started(&avsp_disc_guard_state);
    ++avsp_diag_cdda_submit_count;
    return 1;
}

static int cdda_port_stop(const AvspPortV2CddaFrame *frame)
{
    JO_UNUSED_ARG(frame);
    jo_audio_stop_cd();
    avsp_disc_guard_cdda_stopped(&avsp_disc_guard_state);
    ++avsp_diag_cdda_submit_count;
    return 1;
}

static int residency_port_read(const int region_id,
                               unsigned char *destination,
                               const int capacity)
{
    long read_bytes;

    if (region_id != AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC ||
        destination == 0 ||
        capacity < AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES)
        return -1;
    read_bytes = avsp_fs_read_into(
        "RESCHK.BIN", "DIAG", destination,
        AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES);
    if (read_bytes == AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES)
        ++avsp_diag_residency_submit_count;
    return (int)read_bytes;
}

static int cdda_residency_promotion_init(void)
{
    avsp_port_v2_cdda_init(&cdda_port_v2);
    avsp_port_v2_residency_init(&residency_port_v2);
    cdda_residency_frame = 0;
    memset(&cdda_residency_read_buffer, 0,
           sizeof(cdda_residency_read_buffer));
    cdda_residency_read_buffer.head_canary =
        AVSP_PORT_V2_RESIDENCY_CANARY_HEAD;
    cdda_residency_read_buffer.tail_canary =
        AVSP_PORT_V2_RESIDENCY_CANARY_TAIL;
    avsp_disc_guard_init(&avsp_disc_guard_state);
    avsp_diag_cdda_interface_version =
        AVSP_PORT_V2_CDDA_INTERFACE_VERSION;
    avsp_diag_cdda_production_interface_version =
        AVSP_PORT_V2_CDDA_INTERFACE_VERSION;
    avsp_diag_residency_production_interface_version =
        AVSP_PORT_V2_RESIDENCY_INTERFACE_VERSION;
    avsp_diag_cdda_track = avsp_port_v2_cdda_stage1_config.track;
    avsp_diag_cdda_source_frame =
        avsp_port_v2_cdda_stage1_config.source_frame;
    avsp_diag_cdda_work_ram_high_water =
        avsp_port_v2_stage1_residency_manifest.phase_high_water_bytes[
            AVSP_PORT_V2_DOMAIN_WORK_RAM];
    avsp_diag_cdda_cart_high_water =
        avsp_port_v2_stage1_residency_manifest.phase_high_water_bytes[
            AVSP_PORT_V2_DOMAIN_CARTRIDGE];
    avsp_diag_cdda_vdp1_high_water =
        avsp_port_v2_stage1_residency_manifest.phase_high_water_bytes[
            AVSP_PORT_V2_DOMAIN_VDP1];
    avsp_diag_cdda_vdp2_high_water =
        avsp_port_v2_stage1_residency_manifest.phase_high_water_bytes[
            AVSP_PORT_V2_DOMAIN_VDP2];
    avsp_diag_cdda_cram_high_water =
        avsp_port_v2_stage1_residency_manifest.phase_high_water_bytes[
            AVSP_PORT_V2_DOMAIN_CRAM];
    avsp_diag_cdda_scsp_high_water =
        avsp_port_v2_stage1_residency_manifest.phase_high_water_bytes[
            AVSP_PORT_V2_DOMAIN_SCSP];
    avsp_diag_cdda_fallback_used = 0;
    avsp_diag_cdda_port_lock_ok =
        avsp_port_v2_cdda_validate_config(
            &avsp_port_v2_cdda_stage1_config) &&
        avsp_port_v2_residency_validate_manifest(
            &avsp_port_v2_stage1_residency_manifest) &&
        sizeof(cdda_residency_read_buffer) ==
            AVSP_PORT_V2_RESIDENCY_WORK_RAM_BYTES;
    return avsp_diag_cdda_port_lock_ok;
}

static int cdda_residency_action(const int relative)
{
    if (relative == 30) return AVSP_CDDA_ACTION_START_TRACK;
    if (relative == 60) return AVSP_CDDA_ACTION_ILLEGAL_READ;
    if (relative == 90) return AVSP_CDDA_ACTION_ILLEGAL_WINDOW;
    if (relative == 120) return AVSP_CDDA_ACTION_STOP_TRACK;
    if (relative == 150) return AVSP_CDDA_ACTION_WINDOW_BEGIN;
    if (relative == 151) return AVSP_CDDA_ACTION_LEGAL_READ;
    if (relative == 152) return AVSP_CDDA_ACTION_WINDOW_END;
    return AVSP_CDDA_ACTION_NONE;
}

static void cdda_residency_bench_frame_callback(void)
{
    AvspPortV2CddaInput input;
    AvspPortV2CddaFrame cdda_frame;
    AvspPortV2CddaAudioOps audio_operations;
    AvspPortV2ResidencyAssetOps asset_operations;
    const int relative =
        cdda_residency_frame % AVSP_CDDA_RESIDENCY_CYCLE_FRAMES;
    const int action = cdda_residency_action(relative);
    int succeeded = 1;

    jo_clear_screen();
    avsp_diag_runtime_ready = runtime_ready;
    if (!runtime_ready)
    {
        jo_printf(2, 10, "CDDA RESIDENCY PROMOTION FAILED");
        return;
    }
    if (relative == 0 && cdda_residency_frame != 0)
    {
        int prior_failures = residency_port_v2.failures;
        if (cdda_port_v2.active || residency_port_v2.window_open)
            ++prior_failures;
        if (!avsp_port_v2_residency_canaries_ok(&residency_port_v2))
            ++prior_failures;
        avsp_port_v2_cdda_init(&cdda_port_v2);
        avsp_port_v2_residency_init(&residency_port_v2);
        residency_port_v2.failures = prior_failures;
        avsp_disc_guard_init(&avsp_disc_guard_state);
        avsp_diag_cdda_submit_count = 0;
        avsp_diag_residency_submit_count = 0;
    }
    input.command = AVSP_PORT_V2_CDDA_NONE;
    input.track = AVSP_PORT_V2_CDDA_TRACK_STAGE1;
    input.source_frame = AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1;
    if (action == AVSP_CDDA_ACTION_START_TRACK)
        input.command = AVSP_PORT_V2_CDDA_START;
    else if (action == AVSP_CDDA_ACTION_STOP_TRACK)
        input.command = AVSP_PORT_V2_CDDA_STOP;
    if (!avsp_port_v2_cdda_step(&cdda_port_v2, &input, &cdda_frame))
    {
        ++residency_port_v2.failures;
        memset(&cdda_frame, 0, sizeof(cdda_frame));
    }
    audio_operations.start = cdda_port_start;
    audio_operations.stop = cdda_port_stop;
    asset_operations.read = residency_port_read;
    if (action == AVSP_CDDA_ACTION_START_TRACK)
    {
        succeeded = avsp_port_v2_residency_cdda_started(
            &residency_port_v2) &&
            avsp_port_v2_cdda_submit(&cdda_frame, &audio_operations);
    }
    else if (action == AVSP_CDDA_ACTION_ILLEGAL_READ)
    {
        succeeded = avsp_port_v2_residency_submit_read(
            &residency_port_v2,
            AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
            cdda_residency_read_buffer.bytes,
            AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES,
            &asset_operations);
        succeeded = !succeeded;
    }
    else if (action == AVSP_CDDA_ACTION_ILLEGAL_WINDOW)
    {
        succeeded = !avsp_port_v2_residency_window_begin(
            &residency_port_v2);
    }
    else if (action == AVSP_CDDA_ACTION_STOP_TRACK)
    {
        succeeded = avsp_port_v2_cdda_submit(
            &cdda_frame, &audio_operations) &&
            avsp_port_v2_residency_cdda_stopped(&residency_port_v2);
    }
    else if (action == AVSP_CDDA_ACTION_WINDOW_BEGIN)
    {
        succeeded = avsp_port_v2_residency_window_begin(
                        &residency_port_v2) &&
                    avsp_disc_guard_window_begin(
                        &avsp_disc_guard_state,
                        "promoted phase-boundary residency check");
    }
    else if (action == AVSP_CDDA_ACTION_LEGAL_READ)
    {
        succeeded = avsp_port_v2_residency_submit_read(
                        &residency_port_v2,
                        AVSP_PORT_V2_RESIDENCY_REGION_DIAGNOSTIC,
                        cdda_residency_read_buffer.bytes,
                        AVSP_PORT_V2_RESIDENCY_FIXTURE_BYTES,
                        &asset_operations) &&
                    cdda_residency_read_buffer_ok();
        if (!succeeded) ++avsp_diag_cdda_asset_failures;
    }
    else if (action == AVSP_CDDA_ACTION_WINDOW_END)
    {
        succeeded = avsp_port_v2_residency_window_end(
            &residency_port_v2);
        avsp_disc_guard_window_end(&avsp_disc_guard_state);
    }
    if (!succeeded) ++residency_port_v2.failures;
    avsp_diag_cdda_action = action;
    avsp_diag_cdda_ownership =
        residency_port_v2.disc_owner == AVSP_PORT_V2_DISC_CDDA;
    avsp_diag_cdda_track_events = cdda_port_v2.event_count;
    avsp_diag_cdda_ownership_transitions =
        residency_port_v2.ownership_transitions;
    avsp_diag_cdda_window_open = residency_port_v2.window_open;
    avsp_diag_cdda_legal_windows = residency_port_v2.legal_window_count;
    avsp_diag_cdda_legal_reads = residency_port_v2.legal_read_count;
    avsp_diag_cdda_late_reads = residency_port_v2.late_read_attempts;
    avsp_diag_cdda_refused_windows = residency_port_v2.refused_windows;
    avsp_diag_cdda_negative_rejections =
        residency_port_v2.negative_rejections;
    avsp_diag_cdda_failures = residency_port_v2.failures;
    avsp_diag_cdda_canary_ok =
        avsp_port_v2_residency_canaries_ok(&residency_port_v2) &&
        (residency_port_v2.legal_read_count == 0 ||
         cdda_residency_read_buffer_ok());
    jo_printf(2, 2, "CDDA / RESIDENCY PROMOTED");
    jo_printf(2, 5, "F %03d TRACK %d OWNER %d", relative,
              avsp_diag_cdda_track, avsp_diag_cdda_ownership);
    jo_printf(2, 7, "TRANS %d EVENT %d WINDOW %d READ %d",
              avsp_diag_cdda_ownership_transitions,
              avsp_diag_cdda_track_events,
              avsp_diag_cdda_legal_windows,
              avsp_diag_cdda_legal_reads);
    jo_printf(2, 9, "LATE %d REFUSED %d NEG %d",
              avsp_diag_cdda_late_reads,
              avsp_diag_cdda_refused_windows,
              avsp_diag_cdda_negative_rejections);
    jo_printf(2, 11, "PORT %s SUBMIT %d/%d FAIL %d",
              avsp_diag_cdda_port_lock_ok ? "PASS" : "FAIL",
              avsp_diag_cdda_submit_count,
              avsp_diag_residency_submit_count,
              avsp_diag_cdda_failures + avsp_diag_cdda_asset_failures);
    jo_printf(2, 15, "PHYSICAL SATURN UNRUN");
    avsp_diag_cdda_frame = relative;
    ++cdda_residency_frame;
}
#else
static int cdda_residency_read_buffer_ok(void)
{
    static const unsigned char expected[AVSP_CDDA_RESIDENCY_FIXTURE_BYTES] =
        "AVSP-CDDA-RESIDENCY-V1|TRACK=02|WINDOW=PHASE-BOUNDARY|OK!!!!!!!\n";
    return cdda_residency_read_buffer.head_canary ==
               AVSP_CDDA_RESIDENCY_CANARY_HEAD &&
           cdda_residency_read_buffer.tail_canary ==
               AVSP_CDDA_RESIDENCY_CANARY_TAIL &&
           memcmp(cdda_residency_read_buffer.bytes, expected,
                  AVSP_CDDA_RESIDENCY_FIXTURE_BYTES) == 0;
}

static int cdda_residency_bench_init(void)
{
    avsp_cdda_residency_init(&cdda_residency_runtime);
    memset(&cdda_residency_read_buffer, 0,
           sizeof(cdda_residency_read_buffer));
    cdda_residency_read_buffer.head_canary =
        AVSP_CDDA_RESIDENCY_CANARY_HEAD;
    cdda_residency_read_buffer.tail_canary =
        AVSP_CDDA_RESIDENCY_CANARY_TAIL;
    avsp_disc_guard_init(&avsp_disc_guard_state);
    avsp_diag_cdda_interface_version =
        AVSP_CDDA_RESIDENCY_INTERFACE_VERSION;
    avsp_diag_cdda_track = AVSP_CDDA_RESIDENCY_TRACK;
    avsp_diag_cdda_source_frame = AVSP_CDDA_RESIDENCY_SOURCE_FRAME;
    avsp_diag_cdda_work_ram_high_water =
        avsp_cdda_residency_manifest.phase_high_water_bytes[
            AVSP_CDDA_DOMAIN_WORK_RAM];
    avsp_diag_cdda_cart_high_water =
        avsp_cdda_residency_manifest.phase_high_water_bytes[
            AVSP_CDDA_DOMAIN_CARTRIDGE];
    avsp_diag_cdda_vdp1_high_water =
        avsp_cdda_residency_manifest.phase_high_water_bytes[
            AVSP_CDDA_DOMAIN_VDP1];
    avsp_diag_cdda_vdp2_high_water =
        avsp_cdda_residency_manifest.phase_high_water_bytes[
            AVSP_CDDA_DOMAIN_VDP2];
    avsp_diag_cdda_cram_high_water =
        avsp_cdda_residency_manifest.phase_high_water_bytes[
            AVSP_CDDA_DOMAIN_CRAM];
    avsp_diag_cdda_scsp_high_water =
        avsp_cdda_residency_manifest.phase_high_water_bytes[
            AVSP_CDDA_DOMAIN_SCSP];
    return avsp_cdda_residency_validate_manifest(
               &avsp_cdda_residency_manifest) &&
           sizeof(cdda_residency_read_buffer) ==
               AVSP_CDDA_RESIDENCY_WORK_RAM_BYTES;
}

static void cdda_residency_bench_frame_callback(void)
{
    AvspCddaResidencyFrame frame;
    int succeeded = 1;
    int read_bytes;

    jo_clear_screen();
    avsp_diag_runtime_ready = runtime_ready;
    if (!runtime_ready)
    {
        jo_printf(2, 10, "CDDA RESIDENCY BENCH FAILED");
        return;
    }
    if (cdda_residency_runtime.frame != 0 &&
        cdda_residency_runtime.frame %
            AVSP_CDDA_RESIDENCY_CYCLE_FRAMES == 0)
        avsp_disc_guard_init(&avsp_disc_guard_state);
    if (!avsp_cdda_residency_step(&cdda_residency_runtime, &frame))
    {
        ++cdda_residency_runtime.failures;
        return;
    }
    if (frame.action == AVSP_CDDA_ACTION_START_TRACK)
    {
        jo_audio_play_cd_track(2, 2, true);
        avsp_disc_guard_cdda_started(&avsp_disc_guard_state);
    }
    else if (frame.action == AVSP_CDDA_ACTION_ILLEGAL_READ)
    {
        read_bytes = avsp_fs_read_into(
            "RESCHK.BIN", "DIAG", cdda_residency_read_buffer.bytes,
            AVSP_CDDA_RESIDENCY_FIXTURE_BYTES);
        succeeded = read_bytes >= 0;
    }
    else if (frame.action == AVSP_CDDA_ACTION_ILLEGAL_WINDOW)
        succeeded = avsp_disc_guard_window_begin(
            &avsp_disc_guard_state, "illegal while CDDA active");
    else if (frame.action == AVSP_CDDA_ACTION_STOP_TRACK)
    {
        jo_audio_stop_cd();
        avsp_disc_guard_cdda_stopped(&avsp_disc_guard_state);
    }
    else if (frame.action == AVSP_CDDA_ACTION_WINDOW_BEGIN)
        succeeded = avsp_disc_guard_window_begin(
            &avsp_disc_guard_state, "phase-boundary residency check");
    else if (frame.action == AVSP_CDDA_ACTION_LEGAL_READ)
    {
        read_bytes = avsp_fs_read_into(
            "RESCHK.BIN", "DIAG", cdda_residency_read_buffer.bytes,
            AVSP_CDDA_RESIDENCY_FIXTURE_BYTES);
        succeeded = read_bytes == AVSP_CDDA_RESIDENCY_FIXTURE_BYTES &&
                    cdda_residency_read_buffer_ok();
        if (!succeeded)
            ++avsp_diag_cdda_asset_failures;
    }
    else if (frame.action == AVSP_CDDA_ACTION_WINDOW_END)
        avsp_disc_guard_window_end(&avsp_disc_guard_state);
    if (!avsp_cdda_residency_observe(
            &cdda_residency_runtime, &frame, succeeded))
        avsp_diag_cdda_failures = cdda_residency_runtime.failures;

    avsp_diag_cdda_frame = frame.relative_frame;
    avsp_diag_cdda_action = frame.action;
    avsp_diag_cdda_ownership = cdda_residency_runtime.cdda_active;
    avsp_diag_cdda_track_events =
        cdda_residency_runtime.track_event_count;
    avsp_diag_cdda_ownership_transitions =
        cdda_residency_runtime.ownership_transitions;
    avsp_diag_cdda_window_open = cdda_residency_runtime.window_open;
    avsp_diag_cdda_legal_windows =
        cdda_residency_runtime.legal_window_count;
    avsp_diag_cdda_legal_reads = cdda_residency_runtime.legal_read_count;
    avsp_diag_cdda_late_reads = avsp_disc_guard_state.late_read_attempts;
    avsp_diag_cdda_refused_windows = avsp_disc_guard_state.refused_windows;
    avsp_diag_cdda_negative_rejections =
        cdda_residency_runtime.negative_rejections;
    avsp_diag_cdda_failures = cdda_residency_runtime.failures;
    avsp_diag_cdda_canary_ok =
        avsp_cdda_residency_canaries_ok(&cdda_residency_runtime) &&
        (cdda_residency_runtime.legal_read_count == 0 ||
         cdda_residency_read_buffer_ok());
    jo_printf(2, 2, "CDDA / RESIDENCY SALVAGE");
    jo_printf(2, 5, "F %03d TRACK %d OWNER %d",
              frame.relative_frame, avsp_diag_cdda_track,
              avsp_diag_cdda_ownership);
    jo_printf(2, 7, "TRANS %d EVENT %d WINDOW %d READ %d",
              avsp_diag_cdda_ownership_transitions,
              avsp_diag_cdda_track_events,
              avsp_diag_cdda_legal_windows,
              avsp_diag_cdda_legal_reads);
    jo_printf(2, 9, "LATE %d REFUSED %d NEG %d",
              avsp_diag_cdda_late_reads,
              avsp_diag_cdda_refused_windows,
              avsp_diag_cdda_negative_rejections);
    jo_printf(2, 11, "WRAM %d CANARY %s FAIL %d",
              avsp_diag_cdda_work_ram_high_water,
              avsp_diag_cdda_canary_ok ? "PASS" : "FAIL",
              avsp_diag_cdda_failures + avsp_diag_cdda_asset_failures);
    jo_printf(2, 15, "PHYSICAL SATURN UNRUN");
}
#endif
#endif

#ifdef AVSP_PLAYABLE_SLICE
static int playable_slice_load_residency(const int region_id,
                                         unsigned char *destination,
                                         const int capacity)
{
    int result;
    avsp_diag_slice_init_stage = 1;
    result = residency_port_read(region_id, destination, capacity);
    avsp_diag_slice_init_stage = result == capacity ? 2 : -1;
    return result;
}

static int playable_slice_load_tiles(void)
{
    avsp_diag_slice_init_stage = 3;
    if (!load_tile_archive())
    {
        avsp_diag_slice_init_stage = -3;
        return 0;
    }
    avsp_diag_slice_init_stage = 4;
    return 1;
}

static int playable_slice_load_stage(void)
{
    avsp_diag_slice_init_stage = 5;
    if (!load_background() || !street_setup())
    {
        avsp_diag_slice_init_stage = -5;
        return 0;
    }
    avsp_diag_slice_init_stage = 6;
    return 1;
}

static int playable_slice_load_player_idle(void)
{
    avsp_diag_slice_init_stage = 7;
    if (!load_all_cels())
    {
        avsp_diag_slice_init_stage = -7;
        return 0;
    }
    avsp_diag_slice_init_stage = 8;
    return 1;
}

static int playable_slice_load_player_actions(void)
{
    avsp_diag_slice_init_stage = 9;
    if (!load_player_action_sequences())
    {
        avsp_diag_slice_init_stage = -9;
        return 0;
    }
    avsp_diag_slice_init_stage = 10;
    return 1;
}

static int playable_slice_create_player_sprites(void)
{
    avsp_diag_slice_init_stage = 11;
    if (!create_player_sprite_working_set())
    {
        avsp_diag_slice_init_stage = -11;
        return 0;
    }
    avsp_diag_slice_init_stage = 12;
    return 1;
}

static int playable_slice_load_hud(void)
{
    avsp_diag_slice_init_stage = 13;
    if (!load_hud_assets() || !load_player2_hud_assets() ||
        !create_hud_sprite_working_set())
    {
        avsp_diag_slice_init_stage = -13;
        return 0;
    }
    avsp_diag_slice_init_stage = 14;
    return 1;
}

static int playable_slice_load_pcm(void)
{
    avsp_diag_slice_init_stage = 15;
    if (!load_pcm_audio(&melee_sound, AVSP_MELEE_PCM_FILE,
                        AVSP_MELEE_PCM_DIRECTORY, AVSP_MELEE_PCM_BYTES,
                        AVSP_MELEE_PCM_SAMPLE_RATE) ||
        !hud_pcm_sound_valid(&melee_sound))
    {
        avsp_diag_slice_init_stage = -15;
        return 0;
    }
    avsp_diag_slice_init_stage = 16;
    return 1;
}

static int playable_slice_init(void)
{
    AvspPortV2SliceLoadOps operations;
    memset(&operations, 0, sizeof(operations));
    avsp_diag_slice_init_stage = 0;
    avsp_diag_slice_frame_stage = 0;
    operations.residency_assets.read = playable_slice_load_residency;
    operations.actor_assets.load_tile_archive = playable_slice_load_tiles;
    operations.actor_assets.load_background = playable_slice_load_stage;
    operations.actor_assets.load_player_idle = playable_slice_load_player_idle;
    operations.actor_assets.load_player_actions =
        playable_slice_load_player_actions;
    operations.actor_assets.create_player_sprites =
        playable_slice_create_player_sprites;
    operations.load_hud = playable_slice_load_hud;
    operations.load_pcm = playable_slice_load_pcm;
    avsp_port_v2_slice_init(&playable_slice_runtime);
    if (!avsp_port_v2_slice_load(
            &playable_slice_runtime, cart_available, &operations))
        return 0;
    avsp_diag_slice_init_stage = 17;
    avsp_diag_slice_interface_version = AVSP_PORT_V2_SLICE_INTERFACE_VERSION;
    avsp_diag_slice_frame = 0;
    avsp_diag_slice_ready = 1;
    avsp_diag_slice_physical_saturn = 0;
    avsp_diag_slice_review_phase = 1;
    avsp_diag_hud_port_lock_ok = avsp_port_v2_hud_validate_config(
        &avsp_port_v2_hud_approved_config);
    avsp_diag_pcm_port_lock_ok = avsp_port_v2_pcm_validate_config(
        &avsp_port_v2_pcm_predator_melee_config);
    avsp_diag_cdda_port_lock_ok = avsp_port_v2_cdda_validate_config(
        &avsp_port_v2_cdda_stage1_config);
    return 1;
}

static int playable_slice_scripted_attack(const int frame)
{
    /* ADAPTED input choreography; each edge is the measured source input
     * sample translated around the first contact at slice frame 600. */
    return frame == 595 || frame == 640 || frame == 685 || frame == 730;
}

static void playable_slice_scripted_movement(AvspPortV2SliceInput *input)
{
    const int frame = input->frame;
    input->player.down = frame >= 30 && frame < 60;
    input->player.right = frame >= 300 && frame < 335;
    input->enemy_move = frame >= 300 && frame < 490;
    input->player_attack = playable_slice_scripted_attack(frame);
    input->player_height = 0;
}

static void playable_slice_publish_combat(void)
{
    avsp_diag_combat_transition_state =
        playable_slice_runtime.combat.transition.actor.state;
    avsp_diag_combat_transition_sub_state =
        playable_slice_runtime.combat.transition.actor.sub_state;
    avsp_diag_combat_transition_action =
        playable_slice_runtime.combat.transition.actor.action;
    avsp_diag_combat_transition_anim_record =
        playable_slice_runtime.combat.transition.actor.anim_record;
    avsp_diag_combat_transition_timer =
        playable_slice_runtime.combat.transition.actor.anim_timer;
    avsp_diag_combat_transition_hit_value =
        playable_slice_runtime.combat.transition.actor.hit_value;
    avsp_diag_combat_contact_count =
        playable_slice_runtime.combat.contact_count;
    avsp_diag_combat_damage_count =
        playable_slice_runtime.combat.damage_count;
    avsp_diag_combat_hit_count = playable_slice_runtime.combat.hit_count;
    avsp_diag_combat_ko_count = playable_slice_runtime.combat.ko_count;
    avsp_diag_combat_enemy_health =
        playable_slice_runtime.combat.enemy_health;
}

static void playable_slice_draw_actors(void)
{
    CapActor player;
    CapActor *enemy = &world.enemies[0];
    int rendered = 0;
    unsigned long expected_enemy_object;
    unsigned long expected_enemy_tile;
    memset(&player, 0, sizeof(player));
    player.active = 1;
    player.kind = CAP_ACTOR_PLAYER;
    player.x = playable_slice_frame.actors.player.world_x;
    player.lane = playable_slice_frame.actors.player.lane;
#ifdef AVSP_LIVE_ENCOUNTER
    player.height = live_encounter_frame.player.height;
#else
    player.height = playable_slice_runtime.player_height;
#endif
    player.facing = playable_slice_frame.actors.player.facing;
    player.locomotion_frame =
        playable_slice_frame.actors.player.locomotion_frame;
    if (playable_slice_frame.scene.player_action ==
        AVSP_PORT_V2_SLICE_ACTION_ATTACK)
        player.action = CAP_ACT_ATTACK;
    else if (playable_slice_frame.scene.player_action ==
             AVSP_PORT_V2_SLICE_ACTION_HIT)
        player.action = CAP_ACT_HIT;
    else if (playable_slice_frame.scene.player_action ==
             AVSP_PORT_V2_SLICE_ACTION_KO)
        player.action = CAP_ACT_KO;
    else if (playable_slice_frame.scene.player_action ==
             AVSP_PORT_V2_SLICE_ACTION_WALK)
        player.action = CAP_ACT_WALK;
    else
        player.action = CAP_ACT_IDLE;
    player.action_frame = playable_slice_frame.scene.player_action_frame;
    memset(enemy, 0, sizeof(*enemy));
    enemy->active = 1;
#ifdef AVSP_LIVE_ENCOUNTER
    enemy->active = !live_encounter_frame.alien.removed;
#endif
    enemy->kind = CAP_ACTOR_ALIEN;
    enemy->variant = 1;
#ifdef AVSP_LIVE_ENCOUNTER
    enemy->health = live_encounter_frame.alien.health;
#else
    enemy->health = playable_slice_runtime.combat.enemy_health;
#endif
    enemy->x = playable_slice_frame.actors.enemy.world_x;
    enemy->lane = playable_slice_frame.actors.enemy.lane;
    enemy->facing = playable_slice_frame.actors.enemy.facing;
    enemy->locomotion_frame =
        playable_slice_frame.actors.enemy.locomotion_frame;
    if (playable_slice_frame.scene.enemy_action ==
        AVSP_PORT_V2_SLICE_ACTION_HIT)
        enemy->action = CAP_ACT_HIT;
    else if (playable_slice_frame.scene.enemy_action ==
             AVSP_PORT_V2_SLICE_ACTION_KO)
        enemy->action = CAP_ACT_KO;
    else if (playable_slice_frame.scene.enemy_action ==
             AVSP_PORT_V2_SLICE_ACTION_ATTACK)
        enemy->action = CAP_ACT_ATTACK;
    else
        enemy->action = CAP_ACT_WALK;
    enemy->action_frame = playable_slice_frame.scene.enemy_action_frame;
    world.encounter_started = 1;
    world.encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    world.camera_x = playable_slice_frame.scene.camera_world_x;
    rom_actor_prepare();
    jo_sprite_change_sprite_scale_xy(
        (float)CAP_VIEW_WIDTH / (float)CAP_CPS2_VIEW_WIDTH, 1.0f);
    draw_player(&player, playable_slice_frame.scene.player_screen_x);
    if (!playable_slice_frame.scene.player_presentation_active)
    {
        playable_slice_frame.scene.player_identity.emitted_object_identity =
            2166136261UL ^ (unsigned long)(unsigned int)
                playable_slice_frame.scene.player_action ^
            ((unsigned long)(unsigned int)current_player_action_pose << 8);
        playable_slice_frame.scene.player_identity.emitted_tile_identity =
            2166136261UL ^
            (unsigned long)(unsigned int)player_action_sprites[0] ^
            ((unsigned long)(unsigned int)player_action_sprites[1] << 8);
    }
    expected_enemy_object =
        playable_slice_frame.scene.enemy_identity.emitted_object_identity;
    expected_enemy_tile =
        playable_slice_frame.scene.enemy_identity.emitted_tile_identity;
    if (enemy->active && rom_actor_entry_counts[0] > 0 && tile_archive_ready)
        rendered = draw_rom_actor_tiles(enemy, 0);
    jo_sprite_restore_sprite_scale();
    rom_actor_advance();
    avsp_diag_player_x = player.x;
    avsp_diag_player_lane = player.lane;
    avsp_diag_player_facing = player.facing;
    avsp_diag_enemy_x = enemy->x;
    avsp_diag_enemy_lane = enemy->lane;
    avsp_diag_enemy_facing = enemy->facing;
    avsp_diag_enemy_render_count = rendered;
    playable_slice_frame.scene.enemy_identity.emitted_object_identity =
        (unsigned long)(unsigned int)avsp_diag_slice_enemy_object_identity;
    playable_slice_frame.scene.enemy_identity.emitted_tile_identity =
        (unsigned long)(unsigned int)avsp_diag_slice_enemy_tile_identity;
    if (expected_enemy_object != 0UL &&
        (playable_slice_frame.scene.enemy_identity.emitted_object_identity !=
             expected_enemy_object ||
         playable_slice_frame.scene.enemy_identity.emitted_tile_identity !=
             expected_enemy_tile))
    {
#ifdef AVSP_LIVE_ENCOUNTER
        ++live_encounter_runtime.failures;
#else
        ++playable_slice_runtime.asset_failures;
#endif
    }
    if (!avsp_port_v2_slice_identity_valid(
            &playable_slice_frame.scene.enemy_identity))
    {
#ifdef AVSP_LIVE_ENCOUNTER
        ++live_encounter_runtime.failures;
#else
        ++playable_slice_runtime.asset_failures;
#endif
    }
}

#ifdef AVSP_LIVE_ENCOUNTER
static unsigned short live_encounter_real_input(void)
{
    unsigned short mask = 0u;
    if (jo_is_pad1_key_pressed(JO_KEY_LEFT)) mask |= AVSP_PW_INPUT_LEFT;
    if (jo_is_pad1_key_pressed(JO_KEY_RIGHT)) mask |= AVSP_PW_INPUT_RIGHT;
    if (jo_is_pad1_key_pressed(JO_KEY_UP)) mask |= AVSP_PW_INPUT_UP;
    if (jo_is_pad1_key_pressed(JO_KEY_DOWN)) mask |= AVSP_PW_INPUT_DOWN;
    if (jo_is_pad1_key_down(JO_KEY_B)) mask |= AVSP_PW_INPUT_ATTACK;
    return mask;
}

#ifdef AVSP_LIVE_ENCOUNTER_AUTOTEST
static int live_encounter_near_target(void)
{
    int dx = live_encounter_runtime.alien.x - live_encounter_runtime.player.x;
    int dz = live_encounter_runtime.alien.lane -
        live_encounter_runtime.player.lane;
    if (dx < 0) dx = -dx;
    if (dz < 0) dz = -dz;
    return dx <= 52 && dz <= 6;
}

static unsigned short live_encounter_autotest_input(void)
{
    unsigned short mask = 0u;
    if (live_autotest_release)
    {
        live_autotest_release = 0;
        return 0u;
    }
    if (live_encounter_runtime.route_unlocked)
        return AVSP_PW_INPUT_RIGHT;
    if (live_autotest_phase == 0)
    {
        if (live_encounter_runtime.encounter_state ==
            AVSP_LIVE_ENCOUNTER_WAIT_ENTRY)
            return AVSP_PW_INPUT_RIGHT;
        live_autotest_phase = 1;
    }
    if (live_autotest_phase == 1)
    {
        if (live_encounter_runtime.alien_contacts == 0UL) return 0u;
        live_autotest_phase = 2;
    }
    if (live_autotest_phase == 2)
    {
        if (live_encounter_runtime.player.x > 914)
            return AVSP_PW_INPUT_LEFT;
        if (avsp_pw_can_control(&live_encounter_runtime.player))
        {
            live_autotest_phase = 3;
            live_autotest_release = 1;
            return AVSP_PW_INPUT_ATTACK;
        }
        return 0u;
    }
    if (live_encounter_runtime.player.state != AVSP_PW_STATE_CONTROL)
        return 0u;
    if (live_encounter_runtime.player.x <
        live_encounter_runtime.alien.x - 42)
        mask |= AVSP_PW_INPUT_RIGHT;
    else if (live_encounter_runtime.player.x >
             live_encounter_runtime.alien.x + 42)
        mask |= AVSP_PW_INPUT_LEFT;
    if (live_encounter_runtime.player.lane <
        live_encounter_runtime.alien.lane - 4)
        mask |= AVSP_PW_INPUT_UP;
    else if (live_encounter_runtime.player.lane >
             live_encounter_runtime.alien.lane + 4)
        mask |= AVSP_PW_INPUT_DOWN;
    if (live_encounter_near_target())
    {
        live_autotest_release = 1;
        return AVSP_PW_INPUT_ATTACK;
    }
    return mask;
}
#endif

static void live_encounter_identity(void)
{
    AvspPortV2SliceActorIdentity *player =
        &playable_slice_frame.scene.player_identity;
    AvspPortV2SliceActorIdentity *alien =
        &playable_slice_frame.scene.enemy_identity;
    player->actor_id = AVSP_PORT_V2_SLICE_ACTOR_PLAYER;
    player->role = AVSP_PORT_V2_SLICE_ROLE_PLAYER;
    player->class_id = AVSP_PORT_V2_SLICE_CLASS_NOT_APPLICABLE;
    player->archetype_id = AVSP_PORT_V2_SLICE_ARCHETYPE_PREDATOR_WARRIOR;
    player->asset_set_id = AVSP_PORT_V2_SLICE_ASSET_PLAYER_APPROVED;
    player->animation_set_id = AVSP_PORT_V2_SLICE_ANIM_PLAYER_APPROVED;
    player->palette_bank = 0;
    alien->actor_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
    alien->role = AVSP_PORT_V2_SLICE_ROLE_ENEMY;
    alien->class_id = AVSP_PORT_V2_ENEMY_CLASS_ID;
    alien->archetype_id = AVSP_PORT_V2_SLICE_ARCHETYPE_STREET_ALIEN;
    alien->asset_set_id = AVSP_PORT_V2_SLICE_ASSET_STREET_ALIEN_ROM;
    alien->animation_set_id = AVSP_PORT_V2_SLICE_ANIM_STREET_ALIEN_ROM;
    alien->palette_bank = AVSP_PORT_V2_ENEMY_PALETTE_BANK;
}

static void live_encounter_build_slice_frame(void)
{
    AvspPortV2SliceSceneTrace *scene;
    AvspPortV2PlayerCombatPresentation presentation;
    AvspPortV2CameraInput camera_input;
    AvspPortV2HudInput hud_input;
    int source_frame;
    memset(&playable_slice_frame, 0, sizeof(playable_slice_frame));
    scene = &playable_slice_frame.scene;
    scene->source_event_index = -1;
    playable_slice_frame.interface_version =
        AVSP_PORT_V2_SLICE_INTERFACE_VERSION;
    playable_slice_frame.ready = 1;
    playable_slice_frame.frame = (int)live_encounter_frame.frame;
    playable_slice_frame.actors.actor_count =
        live_encounter_frame.alien.removed ? 1 : 2;
    playable_slice_frame.actors.render_order[0] =
        AVSP_PORT_V2_PLAYER_ENEMY_RENDER_PLAYER;
    playable_slice_frame.actors.render_order[1] =
        AVSP_PORT_V2_PLAYER_ENEMY_RENDER_ENEMY;
    playable_slice_frame.actors.render_command_count =
        live_encounter_frame.alien.removed ? 2 : 34;
    playable_slice_frame.actors.player.world_x =
        live_encounter_frame.player.x;
    /* The source projection is top-origin CPS2 screen space; Jo's sprite
       submission is centre-origin, and the captured 192px cel pivot is 88px
       below its centre.  Convert both offsets exactly once before the legacy
       lane-to-screen bridge also derives its positive VDP1 depth. */
    playable_slice_frame.actors.player.lane =
        live_encounter_frame.player_screen_y + 200 - JO_TV_HEIGHT / 2 - 88 +
        live_encounter_frame.player.height;
    playable_slice_frame.actors.player.facing =
        avsp_pw_render_facing(live_encounter_frame.player.facing);
    playable_slice_frame.actors.player.locomotion_frame =
        (int)(live_encounter_frame.frame % 39UL);
    playable_slice_frame.actors.enemy.class_id = AVSP_PORT_V2_ENEMY_CLASS_ID;
    playable_slice_frame.actors.enemy.palette_bank =
        AVSP_PORT_V2_ENEMY_PALETTE_BANK;
    playable_slice_frame.actors.enemy.world_x = live_encounter_frame.alien.x;
    playable_slice_frame.actors.enemy.lane =
        live_encounter_frame.alien_screen_y + 200 - JO_TV_HEIGHT / 2 - 88;
    playable_slice_frame.actors.enemy.facing =
        live_encounter_frame.alien.facing ? -1 : 1;
    playable_slice_frame.actors.enemy.locomotion_frame =
        (int)(live_encounter_frame.frame % AVSP_PORT_V2_ENEMY_WALK_FRAMES);
    scene->player_world_x = live_encounter_frame.player.x;
    scene->enemy_world_x = live_encounter_frame.alien.x;
    scene->camera_world_x = live_encounter_frame.camera_world_x;
    scene->aperture_origin_x = AVSP_LIVE_ENCOUNTER_APERTURE_ORIGIN_X;
    scene->player_screen_x = live_encounter_frame.player_screen_x;
    scene->enemy_screen_x = live_encounter_frame.alien_screen_x;
    scene->layer_scroll_x[0] = live_encounter_frame.camera_world_x;
    scene->layer_scroll_x[1] = live_encounter_frame.camera_world_x / 2;
    scene->player_action_frame = live_encounter_frame.player.action_elapsed;
    scene->player_attack_active = live_encounter_frame.player.attack_active;
    if (live_encounter_frame.player.state == AVSP_PW_STATE_ATTACK)
        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_ATTACK;
    else if (live_encounter_frame.player.state == AVSP_PW_STATE_HIT)
    {
        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_HIT;
        scene->player_action_frame =
            16 - (int)live_encounter_runtime.player.hit_timer;
    }
    else if (live_encounter_frame.player.state == AVSP_PW_STATE_KO)
    {
        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_KO;
        scene->player_action_frame = 0;
    }
    else if ((live_encounter_frame.input_mask &
              (AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT |
               AVSP_PW_INPUT_UP | AVSP_PW_INPUT_DOWN)) != 0u)
        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_WALK;
    else
        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_IDLE;
    live_encounter_identity();
    scene->player_identity.animation_record =
        live_encounter_frame.player.animation_record;
    if (avsp_pw_source_presentation_ready(
            live_encounter_frame.player.selector,
            live_encounter_frame.player.action_elapsed))
    {
        source_frame = (int)live_encounter_frame.player.action_elapsed -
            (int)avsp_pw_action_defs[
                live_encounter_frame.player.selector - 1u].presentation_first;
        if (source_frame >= 0 && avsp_port_v2_combat_source_player_frame(
                (int)live_encounter_frame.player.selector - 1,
                source_frame, &presentation))
        {
            scene->player_presentation_active = 1;
            scene->source_event_index =
                (int)live_encounter_frame.player.selector - 1;
            scene->attack_sequence_step = presentation.sequence_step;
            scene->attack_selector = presentation.attack_selector;
            scene->player_source_action = presentation.source_action;
            scene->player_source_substate = presentation.source_substate;
            scene->player_source_pose = presentation.pose_index;
            scene->player_source_pivot_x = presentation.pivot_x;
            scene->player_source_pivot_y = presentation.pivot_y;
            scene->player_source_height = presentation.height;
            scene->player_identity.animation_record =
                presentation.source_animation_record;
            scene->player_identity.emitted_object_identity =
                presentation.source_object_identity;
            scene->player_identity.emitted_tile_identity =
                presentation.source_tile_identity;
        }
    }
    if (live_encounter_frame.player.state == AVSP_PW_STATE_ATTACK &&
        !scene->player_presentation_active)
    {
        /* The measured source remains in its control pose for the first two
           attack ticks. Do not flash the unrelated legacy attack clip before
           the selector-owned source presentation becomes active. */
        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_IDLE;
        scene->player_action_frame = 0;
    }
    if (live_encounter_frame.alien.state == AVSP_ALIEN_STATE_KO)
    {
        scene->enemy_action = AVSP_PORT_V2_SLICE_ACTION_KO;
        scene->enemy_identity.animation_record =
            live_encounter_frame.alien_presentation.anim_record != 0UL ?
            live_encounter_frame.alien_presentation.anim_record :
            AVSP_PORT_V2_KO_ANIM_RECORD_5;
    }
    else if (live_encounter_frame.alien.state == AVSP_ALIEN_STATE_HIT)
    {
        scene->enemy_action = AVSP_PORT_V2_SLICE_ACTION_HIT;
        scene->enemy_identity.animation_record =
            live_encounter_frame.alien_presentation.anim_record != 0UL ?
            live_encounter_frame.alien_presentation.anim_record :
            AVSP_PORT_V2_HIT_RECOVERY_ANIM_RECORD;
    }
    else if (live_encounter_frame.alien.state == AVSP_ALIEN_STATE_ATTACK)
    {
        scene->enemy_action = AVSP_PORT_V2_SLICE_ACTION_ATTACK;
        scene->enemy_identity.animation_record =
            live_encounter_frame.alien.animation_record;
    }
    else
    {
        scene->enemy_action = AVSP_PORT_V2_SLICE_ACTION_WALK;
        scene->enemy_identity.animation_record =
            live_encounter_frame.alien.animation_record;
    }
    scene->enemy_action_frame =
        (live_encounter_frame.alien.state == AVSP_ALIEN_STATE_HIT ||
         live_encounter_frame.alien.state == AVSP_ALIEN_STATE_KO) ?
        live_encounter_runtime.reaction_elapsed :
        live_encounter_frame.alien.presentation_index;
    scene->enemy_source_action = live_encounter_frame.alien.source_action;
    scene->enemy_source_substate = live_encounter_frame.alien.inner_state;
    scene->collision_result = live_encounter_frame.player_contact;
    scene->health_before = live_encounter_frame.health_before;
    scene->health_after = live_encounter_frame.health_after;
    scene->semantic_hit = live_encounter_frame.semantic_hit;
    scene->semantic_ko = live_encounter_frame.semantic_ko;
    if (scene->collision_result)
    {
        scene->attacker_id = AVSP_PORT_V2_SLICE_ACTOR_PLAYER;
        scene->defender_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
    }
    else if (scene->enemy_action == AVSP_PORT_V2_SLICE_ACTION_HIT ||
             scene->enemy_action == AVSP_PORT_V2_SLICE_ACTION_KO)
        scene->defender_id = AVSP_PORT_V2_SLICE_ACTOR_STREET_ALIEN;
    memset(&camera_input, 0, sizeof(camera_input));
    camera_input.scroll_x[0] = live_encounter_frame.camera_world_x;
    camera_input.scroll_x[1] = live_encounter_frame.camera_world_x / 2;
    avsp_port_v2_camera_step(&playable_slice_runtime.camera, &camera_input);
    avsp_port_v2_camera_view(&playable_slice_runtime.camera,
                             &playable_slice_frame.camera);
    avsp_port_v2_stage_build_frame(&playable_slice_frame.camera,
                                   &playable_slice_frame.stage);
    memset(&hud_input, 0, sizeof(hud_input));
    hud_input.players[AVSP_PORT_V2_HUD_P1].visible = 1;
    hud_input.players[AVSP_PORT_V2_HUD_P1].character_id =
        AVSP_PORT_V2_CHARACTER_PREDATOR_WARRIOR;
    hud_input.players[AVSP_PORT_V2_HUD_P1].health =
        live_encounter_frame.player.health;
    hud_input.players[AVSP_PORT_V2_HUD_P1].energy = 64;
    /* Preserve the already-approved two-player HUD shell. P2 remains a
     * presentation-only zero-health slot; no second gameplay actor or input
     * authority is introduced by this integration card. */
    hud_input.players[AVSP_PORT_V2_HUD_P2].visible = 1;
    hud_input.players[AVSP_PORT_V2_HUD_P2].character_id =
        AVSP_PORT_V2_CHARACTER_MAJOR_SCHAEFER;
    hud_input.players[AVSP_PORT_V2_HUD_P2].health = 0;
    hud_input.players[AVSP_PORT_V2_HUD_P2].energy = 0;
    avsp_port_v2_hud_build_frame(&hud_input, &playable_slice_frame.hud);
    playable_slice_frame.combat_event_count =
        (int)live_encounter_runtime.player_contacts;
    playable_slice_frame.asset_failures =
        (int)live_encounter_runtime.failures;
    playable_slice_frame.fallback_used =
        (int)live_encounter_runtime.fallback_count;
    playable_slice_frame.canaries_ok =
        avsp_live_encounter_canaries_ok(&live_encounter_runtime) &&
        avsp_port_v2_slice_canaries_ok(&playable_slice_runtime);
}

static int live_encounter_audio_step(void)
{
    AvspPortV2PcmInput pcm_input;
    AvspPortV2PcmFrame stop_frame;
    AvspPortV2CddaInput cdda_input;
    memset(&pcm_input, 0, sizeof(pcm_input));
    pcm_input.frame = (int)live_encounter_frame.frame;
    pcm_input.cue_event = live_encounter_frame.player_contact;
    pcm_input.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
    /* The approved PCM core models one SCSP channel and rejects overlapping
     * ownership. Source-paced combo contacts can arrive inside its 50-frame
     * cue, so the integration boundary deterministically cuts the old cue and
     * rearms that same channel. This is explicit arbitration, not a dropped
     * sound or alternate fallback path. */
    if (pcm_input.cue_event &&
        (playable_slice_runtime.pcm.pending ||
         playable_slice_runtime.pcm.active))
    {
        if (playable_slice_runtime.pcm.active)
        {
            memset(&stop_frame, 0, sizeof(stop_frame));
            stop_frame.cue_id = AVSP_PORT_V2_PCM_CUE_PREDATOR_MELEE;
            if (!pcm_port_stop(&stop_frame)) return 0;
        }
        avsp_port_v2_pcm_init(&playable_slice_runtime.pcm);
        ++avsp_diag_live_pcm_retriggers;
    }
    if (!avsp_port_v2_pcm_step(&playable_slice_runtime.pcm, &pcm_input,
                               &playable_slice_frame.pcm)) return 0;
    memset(&cdda_input, 0, sizeof(cdda_input));
    cdda_input.command = live_encounter_frame.frame == 0UL ?
        AVSP_PORT_V2_CDDA_START : AVSP_PORT_V2_CDDA_NONE;
    cdda_input.track = AVSP_PORT_V2_CDDA_TRACK_STAGE1;
    cdda_input.source_frame = AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1;
    if (!avsp_port_v2_cdda_step(&playable_slice_runtime.cdda, &cdda_input,
                                &playable_slice_frame.cdda)) return 0;
    if (playable_slice_frame.cdda.start_request &&
        !avsp_port_v2_residency_cdda_started(
            &playable_slice_runtime.residency)) return 0;
    return 1;
}

static void live_encounter_publish(void)
{
    if (live_encounter_frame.frame < AVSP_LIVE_DIAG_SAMPLES)
    {
        volatile LiveEncounterDiagSample *sample =
            &avsp_diag_live_samples[live_encounter_frame.frame];
        sample->frame = (int)live_encounter_frame.frame;
        sample->input_mask = live_encounter_frame.input_mask;
        sample->player_x = live_encounter_frame.player.x;
        sample->player_lane = live_encounter_frame.player.lane;
        sample->player_health = live_encounter_frame.player.health;
        sample->player_state = live_encounter_frame.player.state;
        sample->player_selector = live_encounter_frame.player.selector;
        sample->player_attack_active =
            live_encounter_frame.player.attack_active;
        sample->player_facing = live_encounter_frame.player.facing;
        sample->player_animation_record =
            (int)live_encounter_frame.player.animation_record;
        sample->player_assembly =
            (int)live_encounter_frame.player.assembly;
        sample->player_screen_y = live_encounter_frame.player_screen_y;
        sample->alien_x = live_encounter_frame.alien.x;
        sample->alien_lane = live_encounter_frame.alien.lane;
        sample->alien_health = live_encounter_frame.alien.health;
        sample->alien_state = live_encounter_frame.alien.state;
        sample->alien_inner = live_encounter_frame.alien.inner_state;
        sample->alien_action = live_encounter_frame.alien.source_action;
        sample->alien_facing = live_encounter_frame.alien.facing;
        sample->alien_animation_record =
            (int)live_encounter_frame.alien.animation_record;
        sample->alien_assembly =
            (int)live_encounter_frame.alien.assembly;
        sample->alien_screen_y = live_encounter_frame.alien_screen_y;
        sample->alien_rng = live_encounter_frame.alien.rng_seed;
        sample->player_contact = live_encounter_frame.player_contact;
        sample->alien_contact = live_encounter_frame.alien_contact;
        sample->player_damage = live_encounter_frame.player_damage;
        sample->alien_damage = live_encounter_frame.alien_damage;
        sample->attack_miss = live_encounter_frame.attack_miss;
        sample->encounter_state = live_encounter_frame.encounter_state;
        sample->route_unlocked = live_encounter_frame.route_unlocked;
        sample->continued_after_unlock =
            live_encounter_frame.continued_after_unlock;
        sample->camera_world_x = live_encounter_frame.camera_world_x;
        sample->failures = (int)live_encounter_runtime.failures;
        avsp_diag_live_sample_count = (int)live_encounter_frame.frame + 1;
    }
    avsp_diag_live_interface_version = AVSP_LIVE_ENCOUNTER_INTERFACE_VERSION;
    avsp_diag_live_input_mask = live_encounter_frame.input_mask;
    avsp_diag_live_player_x = live_encounter_frame.player.x;
    avsp_diag_live_player_lane = live_encounter_frame.player.lane;
    avsp_diag_live_player_health = live_encounter_frame.player.health;
    avsp_diag_live_player_state = live_encounter_frame.player.state;
    avsp_diag_live_player_selector = live_encounter_frame.player.selector;
    avsp_diag_live_player_facing = live_encounter_frame.player.facing;
    avsp_diag_live_player_animation_record =
        (int)live_encounter_frame.player.animation_record;
    avsp_diag_live_player_assembly =
        (int)live_encounter_frame.player.assembly;
    avsp_diag_live_player_screen_y = live_encounter_frame.player_screen_y;
    avsp_diag_live_alien_x = live_encounter_frame.alien.x;
    avsp_diag_live_alien_lane = live_encounter_frame.alien.lane;
    avsp_diag_live_alien_health = live_encounter_frame.alien.health;
    avsp_diag_live_alien_state = live_encounter_frame.alien.state;
    avsp_diag_live_alien_inner = live_encounter_frame.alien.inner_state;
    avsp_diag_live_alien_action = live_encounter_frame.alien.source_action;
    avsp_diag_live_alien_facing = live_encounter_frame.alien.facing;
    avsp_diag_live_alien_animation_record =
        (int)live_encounter_frame.alien.animation_record;
    avsp_diag_live_alien_assembly =
        (int)live_encounter_frame.alien.assembly;
    avsp_diag_live_alien_screen_y = live_encounter_frame.alien_screen_y;
    avsp_diag_live_alien_rng = live_encounter_frame.alien.rng_seed;
    avsp_diag_live_player_contact = live_encounter_frame.player_contact;
    avsp_diag_live_alien_contact = live_encounter_frame.alien_contact;
    avsp_diag_live_player_damage = live_encounter_frame.player_damage;
    avsp_diag_live_alien_damage = live_encounter_frame.alien_damage;
    avsp_diag_live_attack_miss = live_encounter_frame.attack_miss;
    avsp_diag_live_hit_events = (int)live_encounter_runtime.hit_events;
    avsp_diag_live_ko_events = (int)live_encounter_runtime.ko_events;
    avsp_diag_live_encounter_state = live_encounter_frame.encounter_state;
    avsp_diag_live_route_unlocked = live_encounter_frame.route_unlocked;
    avsp_diag_live_continued_after_unlock =
        live_encounter_frame.continued_after_unlock;
    avsp_diag_live_camera_world_x = live_encounter_frame.camera_world_x;
    avsp_diag_live_player_screen_x = live_encounter_frame.player_screen_x;
    avsp_diag_live_alien_screen_x = live_encounter_frame.alien_screen_x;
    avsp_diag_live_failures = (int)live_encounter_runtime.failures;
    avsp_diag_live_fallback_count =
        (int)live_encounter_runtime.fallback_count;
    avsp_diag_live_canaries_ok = playable_slice_frame.canaries_ok;
    avsp_diag_slice_frame = (int)live_encounter_frame.frame;
    avsp_diag_slice_enemy_health = live_encounter_frame.alien.health;
    avsp_diag_slice_hit_count = (int)live_encounter_runtime.hit_events;
    avsp_diag_slice_ko_count = (int)live_encounter_runtime.ko_events;
    avsp_diag_slice_combat_events =
        (int)live_encounter_runtime.player_contacts;
    avsp_diag_slice_asset_failures = (int)live_encounter_runtime.failures;
    avsp_diag_slice_fallback_used =
        (int)live_encounter_runtime.fallback_count;
    avsp_diag_slice_canaries_ok = playable_slice_frame.canaries_ok;
    avsp_diag_live_frame = (int)live_encounter_frame.frame;
}

static void live_encounter_frame_callback(void)
{
    AvspLiveEncounterInput input;
    AvspPortV2PcmAudioOps pcm_operations;
    AvspPortV2CddaAudioOps cdda_operations;
    AvspPortV2HudRenderOps hud_operations;
    if (!runtime_ready)
    {
        if (avsp_diag_live_frame_stage == 0)
            avsp_diag_live_frame_stage = -1;
        return;
    }
    avsp_diag_live_frame_stage = 1;
    street_test_frame();
    input.frame = live_encounter_runtime.frame;
#ifdef AVSP_LIVE_ENCOUNTER_AUTOTEST
    input.player_mask = live_encounter_autotest_input();
#else
    input.player_mask = live_encounter_real_input();
#endif
    if (!avsp_live_encounter_step(&live_encounter_runtime, &input,
                                  &live_encounter_frame))
    {
        avsp_diag_live_frame_stage = -2;
        avsp_diag_live_internal_failures =
            (int)live_encounter_runtime.failures;
        runtime_ready = 0;
        return;
    }
    avsp_diag_live_frame_stage = 2;
    live_encounter_build_slice_frame();
    avsp_diag_live_frame_stage = 3;
    if (!live_encounter_audio_step())
    {
        ++live_encounter_runtime.failures;
        avsp_diag_live_frame_stage = -3;
        avsp_diag_live_internal_failures =
            (int)live_encounter_runtime.failures;
        runtime_ready = 0;
        return;
    }
    avsp_diag_live_frame_stage = 4;
    pcm_operations.start = pcm_port_start;
    pcm_operations.stop = pcm_port_stop;
    cdda_operations.start = cdda_port_start;
    cdda_operations.stop = cdda_port_stop;
    if (!avsp_port_v2_pcm_submit(&playable_slice_frame.pcm,
                                 &pcm_operations) ||
        !avsp_port_v2_cdda_submit(&playable_slice_frame.cdda,
                                  &cdda_operations))
    {
        ++live_encounter_runtime.failures;
        avsp_diag_live_frame_stage = -4;
        avsp_diag_live_internal_failures =
            (int)live_encounter_runtime.failures;
        runtime_ready = 0;
        return;
    }
    avsp_diag_live_frame_stage = 5;
    playable_slice_draw_actors();
    avsp_diag_live_frame_stage = 6;
    hud_operations.submit_frame = hud_port_submit_frame;
    if (!avsp_port_v2_hud_submit(&playable_slice_frame.hud,
                                 &hud_operations))
    {
        ++live_encounter_runtime.failures;
        avsp_diag_live_frame_stage = -5;
        avsp_diag_live_internal_failures =
            (int)live_encounter_runtime.failures;
        runtime_ready = 0;
        return;
    }
    avsp_diag_live_frame_stage = 7;
    live_encounter_publish();
    avsp_diag_runtime_ready = runtime_ready;
}
#endif

static void playable_slice_frame_callback(void)
{
    AvspPortV2SliceInput input;
    AvspPortV2PcmAudioOps pcm_operations;
    AvspPortV2CddaAudioOps cdda_operations;
    if (!runtime_ready)
    {
        avsp_diag_runtime_ready = 0;
        return;
    }
    avsp_diag_slice_frame_stage = 1;
    street_test_frame();
    avsp_diag_slice_frame_stage = 2;
    memset(&input, 0, sizeof(input));
    input.frame = playable_slice_runtime.frame;
    playable_slice_scripted_movement(&input);
    input.camera.scroll_x[0] = avsp_diag_street_scx[0];
    input.camera.scroll_x[1] = avsp_diag_street_scx[1];
    input.player_health = 101;
    input.player_energy = 64;
    input.player2_visible = 1;
    input.player2_health = 50;
    input.player2_energy = 32;
    input.pcm_cue_event = input.frame == 600;
    if (input.frame == 0) input.cdda_command = AVSP_PORT_V2_CDDA_START;
    if (input.frame == AVSP_SLICE_CDDA_STOP_FRAME)
        input.cdda_command = AVSP_PORT_V2_CDDA_STOP;
    if (!avsp_port_v2_slice_step(
            &playable_slice_runtime, &input, &playable_slice_frame))
    {
        ++playable_slice_runtime.asset_failures;
        runtime_ready = 0;
        return;
    }
    avsp_diag_slice_frame_stage = 3;
    pcm_operations.start = pcm_port_start;
    pcm_operations.stop = pcm_port_stop;
    cdda_operations.start = cdda_port_start;
    cdda_operations.stop = cdda_port_stop;
    hud_pcm_bench.frame = input.frame;
    if (!avsp_port_v2_pcm_submit(&playable_slice_frame.pcm,
                                 &pcm_operations) ||
        !avsp_port_v2_cdda_submit(&playable_slice_frame.cdda,
                                  &cdda_operations))
    {
        ++playable_slice_runtime.asset_failures;
        runtime_ready = 0;
        return;
    }
    avsp_diag_slice_frame_stage = 4;
    playable_slice_publish_combat();
    playable_slice_draw_actors();
    avsp_diag_slice_frame_stage = 5;
    {
        AvspPortV2HudRenderOps hud_operations;
        hud_operations.submit_frame = hud_port_submit_frame;
        if (!avsp_port_v2_hud_submit(&playable_slice_frame.hud,
                                     &hud_operations))
        {
            ++playable_slice_runtime.asset_failures;
            runtime_ready = 0;
            return;
        }
    }
    avsp_diag_slice_frame_stage = 6;
    if (playable_slice_frame.scene.semantic_ko)
        avsp_diag_slice_review_phase = 4;
    else if (playable_slice_frame.scene.semantic_hit)
        avsp_diag_slice_review_phase = 3;
    else if (playable_slice_frame.scene.player_action ==
             AVSP_PORT_V2_SLICE_ACTION_ATTACK)
        avsp_diag_slice_review_phase = 2;
    else
        avsp_diag_slice_review_phase = 1;
    avsp_diag_runtime_ready = 1;
    avsp_diag_slice_ready = playable_slice_frame.ready;
    avsp_diag_slice_actor_count = playable_slice_frame.actors.actor_count;
    avsp_diag_slice_render_commands =
        playable_slice_frame.actors.render_command_count;
    avsp_diag_slice_combat_events =
        playable_slice_frame.combat_event_count;
    avsp_diag_slice_enemy_health =
        playable_slice_runtime.combat.enemy_health;
    avsp_diag_slice_hit_count = playable_slice_runtime.combat.hit_count;
    avsp_diag_slice_ko_count = playable_slice_runtime.combat.ko_count;
    avsp_diag_slice_stage_submissions = avsp_diag_stage_render_submissions;
    avsp_diag_slice_hud_render_count = playable_slice_frame.hud.render_count;
    avsp_diag_slice_pcm_events = playable_slice_frame.pcm.event_count;
    avsp_diag_slice_pcm_active = playable_slice_frame.pcm.active;
    avsp_diag_slice_cdda_active = playable_slice_frame.cdda.active;
    avsp_diag_slice_cdda_transitions =
        playable_slice_frame.cdda.ownership_transitions;
    avsp_diag_slice_late_reads =
        playable_slice_runtime.residency.late_read_attempts;
    avsp_diag_slice_asset_failures = playable_slice_runtime.asset_failures;
    avsp_diag_slice_fallback_used = playable_slice_runtime.fallback_used;
    avsp_diag_slice_canaries_ok =
        avsp_port_v2_slice_canaries_ok(&playable_slice_runtime);
    avsp_diag_slice_player_world_x =
        playable_slice_frame.scene.player_world_x;
    avsp_diag_slice_enemy_world_x =
        playable_slice_frame.scene.enemy_world_x;
    avsp_diag_slice_camera_world_x =
        playable_slice_frame.scene.camera_world_x;
    avsp_diag_slice_player_screen_x =
        playable_slice_frame.scene.player_screen_x;
    avsp_diag_slice_enemy_screen_x =
        playable_slice_frame.scene.enemy_screen_x;
    avsp_diag_slice_aperture_origin_x =
        playable_slice_frame.scene.aperture_origin_x;
    avsp_diag_slice_player_delta_world_x =
        playable_slice_frame.scene.player_delta_world_x;
    avsp_diag_slice_enemy_delta_world_x =
        playable_slice_frame.scene.enemy_delta_world_x;
    avsp_diag_slice_delta_camera_world_x =
        playable_slice_frame.scene.delta_camera_world_x;
    avsp_diag_slice_player_delta_screen_x =
        playable_slice_frame.scene.player_delta_screen_x;
    avsp_diag_slice_enemy_delta_screen_x =
        playable_slice_frame.scene.enemy_delta_screen_x;
    avsp_diag_slice_layer0_scroll_x =
        playable_slice_frame.scene.layer_scroll_x[0];
    avsp_diag_slice_layer1_scroll_x =
        playable_slice_frame.scene.layer_scroll_x[1];
    avsp_diag_slice_player_action =
        playable_slice_frame.scene.player_action;
    avsp_diag_slice_player_action_frame =
        playable_slice_frame.scene.player_action_frame;
    avsp_diag_slice_player_attack_active =
        playable_slice_frame.scene.player_attack_active;
    avsp_diag_slice_player_presentation_active =
        playable_slice_frame.scene.player_presentation_active;
    avsp_diag_slice_source_sample = playable_slice_frame.scene.source_sample;
    avsp_diag_slice_source_event_index =
        playable_slice_frame.scene.source_event_index;
    avsp_diag_slice_attack_sequence_step =
        playable_slice_frame.scene.attack_sequence_step;
    avsp_diag_slice_attack_selector =
        playable_slice_frame.scene.attack_selector;
    avsp_diag_slice_player_source_action =
        playable_slice_frame.scene.player_source_action;
    avsp_diag_slice_player_source_substate =
        playable_slice_frame.scene.player_source_substate;
    avsp_diag_slice_player_source_pose =
        playable_slice_frame.scene.player_source_pose;
    avsp_diag_slice_player_source_pivot_x =
        playable_slice_frame.scene.player_source_pivot_x;
    avsp_diag_slice_player_source_pivot_y =
        playable_slice_frame.scene.player_source_pivot_y;
    avsp_diag_slice_player_source_height =
        playable_slice_frame.scene.player_source_height;
    avsp_diag_slice_enemy_action = playable_slice_frame.scene.enemy_action;
    avsp_diag_slice_enemy_action_frame =
        playable_slice_frame.scene.enemy_action_frame;
    avsp_diag_slice_enemy_source_action =
        playable_slice_frame.scene.enemy_source_action;
    avsp_diag_slice_enemy_source_substate =
        playable_slice_frame.scene.enemy_source_substate;
    avsp_diag_slice_collision_result =
        playable_slice_frame.scene.collision_result;
    avsp_diag_slice_attacker_id = playable_slice_frame.scene.attacker_id;
    avsp_diag_slice_defender_id = playable_slice_frame.scene.defender_id;
    avsp_diag_slice_health_before = playable_slice_frame.scene.health_before;
    avsp_diag_slice_health_after = playable_slice_frame.scene.health_after;
    avsp_diag_slice_semantic_hit = playable_slice_frame.scene.semantic_hit;
    avsp_diag_slice_semantic_ko = playable_slice_frame.scene.semantic_ko;
    avsp_diag_slice_player_actor_id =
        playable_slice_frame.scene.player_identity.actor_id;
    avsp_diag_slice_player_role =
        playable_slice_frame.scene.player_identity.role;
    avsp_diag_slice_player_class_id =
        playable_slice_frame.scene.player_identity.class_id;
    avsp_diag_slice_player_archetype_id =
        playable_slice_frame.scene.player_identity.archetype_id;
    avsp_diag_slice_player_asset_set_id =
        playable_slice_frame.scene.player_identity.asset_set_id;
    avsp_diag_slice_player_animation_set_id =
        playable_slice_frame.scene.player_identity.animation_set_id;
    avsp_diag_slice_player_palette_bank =
        playable_slice_frame.scene.player_identity.palette_bank;
    avsp_diag_slice_player_animation_record =
        (int)playable_slice_frame.scene.player_identity.animation_record;
    avsp_diag_slice_player_object_identity =
        (int)playable_slice_frame.scene.player_identity.emitted_object_identity;
    avsp_diag_slice_player_tile_identity =
        (int)playable_slice_frame.scene.player_identity.emitted_tile_identity;
    avsp_diag_slice_enemy_actor_id =
        playable_slice_frame.scene.enemy_identity.actor_id;
    avsp_diag_slice_enemy_role =
        playable_slice_frame.scene.enemy_identity.role;
    avsp_diag_slice_enemy_class_id =
        playable_slice_frame.scene.enemy_identity.class_id;
    avsp_diag_slice_enemy_archetype_id =
        playable_slice_frame.scene.enemy_identity.archetype_id;
    avsp_diag_slice_enemy_asset_set_id =
        playable_slice_frame.scene.enemy_identity.asset_set_id;
    avsp_diag_slice_enemy_animation_set_id =
        playable_slice_frame.scene.enemy_identity.animation_set_id;
    avsp_diag_slice_enemy_palette_bank =
        playable_slice_frame.scene.enemy_identity.palette_bank;
    avsp_diag_slice_enemy_animation_record =
        (int)playable_slice_frame.scene.enemy_identity.animation_record;
    ++avsp_diag_slice_stability_frames;
    /* Publish last so debugger readback sees a complete semantic frame. */
    avsp_diag_slice_frame = playable_slice_frame.frame;
    avsp_diag_slice_frame_stage = 7;
}
#endif

static void frame_callback(void)
{
    CapInput input;
    CapClipRequest clip_request;
#ifdef AVSP_PROBE3
    probe3_frame_callback();
    return;
#endif
#ifndef AVSP_STREET_TEST
    /* MEASURED (write watchpoint, prnt_0 via jo_clear_screen_line): the
     * SGL ASCII text map lives at VDP2_VRAM_B0 (0x25E40000), which the
     * street test owns as the NBG0 pattern-name area. Clearing the text
     * screen every frame would space-fill the street map, so the street
     * profile never touches the SGL ASCII layer. */
    jo_clear_screen();
#endif
#ifdef AVSP_PLAYABLE_SLICE
#ifdef AVSP_LIVE_ENCOUNTER
    live_encounter_frame_callback();
#else
    playable_slice_frame_callback();
#endif
    return;
#endif
#ifdef AVSP_HIT_KO_PROMOTION_BENCH
    avsp_hit_ko_diagnostic_step();
    avsp_diag_runtime_ready = runtime_ready;
    jo_printf(2, 3, "V2-B1 EXACT HIT KO");
    jo_printf(2, 5, "PHASE %d SAMPLE %d", avsp_diag_hit_ko_phase,
              avsp_diag_hit_ko_sample);
    jo_printf(2, 7, "STATE %04X SUB %04X", avsp_diag_hit_ko_state,
              avsp_diag_hit_ko_sub_state);
    jo_printf(2, 9, "ACTION %04X ANIM %08lX", avsp_diag_hit_ko_action,
              avsp_diag_hit_ko_anim_record);
    jo_printf(2, 11, "TIMER %04X HP %d HIT %d", avsp_diag_hit_ko_anim_timer,
              avsp_diag_hit_ko_health, avsp_diag_hit_ko_hit_value);
    jo_printf(2, 13, "SAMPLES %d/%d", avsp_diag_hit_ko_hit_sample_count,
              avsp_diag_hit_ko_ko_sample_count);
    jo_printf(2, 15, "NEG %d FAIL %d CANARY %d",
              avsp_diag_hit_ko_negative_rejections,
              avsp_diag_hit_ko_failures, avsp_diag_hit_ko_canary_ok);
    jo_printf(2, 17, "PHYSICAL SATURN UNRUN");
    return;
#endif
#ifdef AVSP_COLLISION_SALVAGE_BENCH
    collision_bench_frame_callback();
    return;
#endif
#if defined(AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH) || \
    defined(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH)
    pw_action_bench_frame_callback();
    return;
#endif
#if defined(AVSP_STREET_ALIEN_AI_SALVAGE_BENCH) || \
    defined(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH)
    alien_ai_bench_frame_callback();
    return;
#endif
#ifdef AVSP_CDDA_RESIDENCY_SALVAGE_BENCH
    cdda_residency_bench_frame_callback();
    return;
#endif
#ifdef AVSP_PLAYER_SALVAGE_BENCH
    player_bench_frame_callback();
    return;
#endif
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
    hud_pcm_bench_frame_callback();
    return;
#endif
#ifdef AVSP_ENEMY_SALVAGE_BENCH
    enemy_bench_frame_callback();
    return;
#endif
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_encounter_state = (int)world.encounter_state;
    avsp_diag_world_frame = world.frame;
    if (!runtime_ready)
    {
        jo_printf(1, 12, "CAPABILITY TEST FAILED: %s", failed_asset == JO_NULL ? "UNKNOWN" : failed_asset);
        return;
    }
#ifdef AVSP_STREET_TEST
    street_test_frame();
    return;
#endif
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_IDLE)
    {
        world.player.action = visual_action_for_index(visual_action_index);
        world.player.action_frame = 0;
        if (world.player.action == CAP_ACT_WALK)
            visual_walk_frames = AVSP_PLAYER_ACTION_MAX_FRAMES * 8;
        visual_action_index = (visual_action_index + 1) % AVSP_PLAYER_ACTION_CLIPS;
    }
#endif
    input = read_input();
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_WALK && visual_walk_frames > 0)
    {
        input.right = 1;
        --visual_walk_frames;
    }
#endif
#ifdef AVSP_ENCOUNTER_TEST
    input = encounter_test_input();
#endif
#ifdef AVSP_FRONTEND_TEST
    input = frontend_test_input();
#endif
#ifdef AVSP_FRONTEND_SHOT_TEST
    input = frontend_shot_input();
#endif
#ifdef AVSP_BOSS_HIT_TEST
    /* Repeat the 40-frame reaction every two seconds so visual inspection is
       not timing-sensitive after the emulator's long CD preload. */
    if ((world.frame % 120) == 1)
    {
        world.enemies[0].action = CAP_ACT_HIT;
        world.enemies[0].action_frame = 0;
        world.enemies[0].hit_latched = 0;
    }
#endif
#ifdef AVSP_BOSS_KO_TEST
    /* Replay the complete lethal reaction and grounded-corpse hold on a
       timing-insensitive ten-second loop. After the complete 428-frame source
       motion, keep the last captured corpse frame visible for inspection;
       production builds retain the measured 60-frame hold. */
    if ((world.frame % 600) == 1)
    {
        CapActor *boss = &world.enemies[0];
        boss->x = 240;
        boss->lane = world.player.lane;
        boss->height = 0;
        boss->health = 0;
        boss->action = CAP_ACT_KO;
        boss->action_frame = 0;
        boss->hit_latched = 0;
        boss->active = 1;
        boss->kind = CAP_ACTOR_BOSS;
    }
    else if ((world.frame % 600) >=
                 avsp_boss_total_frames[AVSP_BOSS_CLIP_KO] &&
             (world.frame % 600) < 599)
    {
        CapActor *boss = &world.enemies[0];
        boss->action = CAP_ACT_KO;
        boss->action_frame =
            avsp_boss_total_frames[AVSP_BOSS_CLIP_KO] - 2;
        boss->active = 1;
    }
#endif
    /* Prepare one canonical ROM record before gameplay. cap_world_step() and
     * draw_world() therefore consume the same collision/render frame. */
#ifdef AVSP_FRONTEND_SHOT_TEST
    if (avsp_shot_should_hold())
    {
        /* Held: render the same frame again without advancing the world. */
        memset(&clip_request, 0, sizeof(clip_request));
    }
    else
#endif
    {
        rom_actor_prepare();
        clip_request = cap_world_step(&world, &input);
#ifdef AVSP_FRONTEND_SHOT_TEST
        if ((int)world.encounter_state != avsp_shot_state)
        {
            avsp_shot_state = (int)world.encounter_state;
            avsp_shot_state_frames = 0;
        }
        else
            ++avsp_shot_state_frames;
#endif
    }
    /* Start permanently leaves the title scene. Reuse its 78,848-byte RAM
       block for the 64,118-byte Stalker archive before character confirmation
       starts CDDA. This keeps the cold-boot working set unchanged and avoids
       any data-disc seek while Stage 1 music is playing. */
    if (world.encounter_state == CAP_ENCOUNTER_START_TRANSITION &&
        !frontend_runtime.select_surface_ready)
    {
        if (!avsp_frontend_enter_select(&frontend_runtime))
        {
            failed_asset = "ROM FRONTEND SELECT";
            runtime_ready = 0;
            return;
        }
        current_bitmap_scene = BITMAP_SCENE_NONE;
    }
    if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_SELECT &&
        stalker_action_archive == JO_NULL)
    {
        if (!load_stalker_action_archive())
        {
            runtime_ready = 0;
            return;
        }
    }
    /* Body E note: the ROM tile archive is loaded during jo_main init (see
       the comment there) - by character select both cartridge banks are
       already nearly full. */
    /* Phase-boundary load: the Stage Clear composite arrives during the
       interior wipe, long before its BOSS_DEFEAT timer-150 play. The
       loading line is the standing pattern for stage-boundary CD reads:
       printed before the blocking read so it shows during the stall,
       cleared on the next frame. */
    if (world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION &&
        boss_clear_sound.data == JO_NULL)
    {
        int loaded;
        /* The breach cue's natural WAVE_ONE release is gated on the channel
           going idle, but slPCMStat can stay asserted forever after a finite
           buffer elapses on Yaba Sanshiro (the withdraw path documents the
           same quirk), leaving its 298 KB block held. The breach source is
           long finished by the interior wipe, so close and reclaim it
           unconditionally here - it is the top-of-zone block whose free
           rolls the bump pointer back for the load below. */
        if (breach_sound.data != JO_NULL)
        {
            if (jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
            {
                jo_audio_stop_sound(&breach_sound);
                slSndFlush();
            }
            release_pcm_data(&breach_sound);
        }
        /* Reclaim any trailing run of freed blocks into bump space; jo_free
           alone rolls back only a block directly adjacent to the pointer. */
        jo_reduce_memory_fragmentation();
        /* The interior wipe is the declared legal seek window: stage CDDA
           is paused for the wipe (the start call itself is still disabled,
           so today this encodes the contract skeleton - ADAPTED until the
           CD track start returns), the one bounded load runs inside an
           explicit measured window, and music ownership is restored after.
           Reads outside declared windows after the music point are
           rejected and counted by the guard. */
        avsp_disc_guard_cdda_stopped(&avsp_disc_guard_state);
        if (!avsp_disc_guard_window_begin(&avsp_disc_guard_state,
                                          "interior wipe: CDDA paused"))
        {
            failed_asset = "DISC WINDOW";
            runtime_ready = 0;
            return;
        }
        jo_printf(15, 13, "NOW LOADING");
        loaded = load_pcm_audio(&boss_clear_sound, AVSP_BOSS_CLEAR_PCM_FILE,
                                AVSP_BOSS_CLEAR_PCM_DIRECTORY,
                                AVSP_BOSS_CLEAR_PCM_BYTES,
                                AVSP_BOSS_CLEAR_PCM_SAMPLE_RATE);
        jo_printf(15, 13, "           ");
        avsp_disc_guard_window_end(&avsp_disc_guard_state);
        avsp_disc_guard_cdda_started(&avsp_disc_guard_state);
        if (!loaded)
        {
            runtime_ready = 0;
            return;
        }
    }
    /* Character confirmation keeps the already-copied selection pixels in
       VDP2, so its 78,848-byte source block can return to the allocator for
       the stage. The Chrysalis boss is composed from ROM tables and needs no
       archive, so nothing is loaded here (release_frontend_scene is
       idempotent). */
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world.encounter_timer >= AVSP_FRONTEND_R1TEXT_CLEAR_FRAME)
        release_frontend_scene(1);
    if (clip_request == CAP_CLIP_SHOOT)
        weapon_audio_pending_shot = world.shots_fired;
    if (clip_request == CAP_CLIP_ATTACK)
        melee_audio_pending = 1;
    /* The CPS2 input is injected at source frame 2525 and QSound voice 12
       becomes audible at frame 2530. Bind the processed SCSP cue to that same
       five-frame action offset, not to the controller edge. */
    if (world.player.action == CAP_ACT_SHOOT &&
        world.player.action_frame == 5 &&
        weapon_audio_played_shots < weapon_audio_pending_shot)
    {
        play_pcm_committed(&weapon_sound, &weapon_sound,
                           AVSP_PCM_CHANNEL_WEAPON);
        weapon_audio_played_shots = weapon_audio_pending_shot;
    }
    if (weapon_audio_played_shots > 0 &&
        jo_audio_is_channel_playing(weapon_sound.current_playing_channel))
        weapon_audio_channel_observed = 1;
    /* The melee composite first differs from idle three frames after input.
       Retrigger its own prior channel so fast attacks follow the CPS2 voice
       reuse behavior instead of exhausting all six Jo PCM slots. */
    if (world.player.action == CAP_ACT_ATTACK &&
        world.player.action_frame == 3 && melee_audio_pending)
    {
        play_pcm_committed(&melee_sound, &melee_sound,
                           AVSP_PCM_CHANNEL_MELEE);
        melee_audio_pending = 0;
        ++melee_audio_play_count;
    }
    if (melee_audio_play_count > 0 &&
        jo_audio_is_channel_playing(melee_sound.current_playing_channel))
        melee_audio_channel_observed = 1;
    /* Each contact composite is a paired QSound capture of impact at +2 and
       the shared player vocal at +3. One SCSP start preserves that internal
       offset without issuing fragile back-to-back stereo upload commands. */
    if ((world.player.action == CAP_ACT_HIT ||
         world.player.action == CAP_ACT_KO) &&
        world.player.action_frame == 2)
    {
        jo_sound *next_contact = world.player.action == CAP_ACT_KO ?
                                 &ko_contact_sound : &contact_sound;
        play_pcm_committed(next_contact, contact_channel_sound,
                           AVSP_PCM_CHANNEL_CONTACT);
        contact_channel_sound = next_contact;
        if (world.player.action == CAP_ACT_KO)
            ++ko_contact_audio_play_count;
        else
            ++contact_audio_play_count;
    }
    if ((contact_audio_play_count > 0 || ko_contact_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_CONTACT))
        contact_audio_channel_observed = 1;
    /* The boss-room voice starts eight CPS2 frames after the captured room
       entry. The defeat/Stage Clear composite begins 150 frames after the
       Chrysalis defeat and deliberately continues across the native
       BOSS_DEFEAT -> STAGE_CLEAR -> RESULTS boundaries. Both use one SCSP
       channel because the source events cannot overlap. */
    if (world.encounter_state == CAP_ENCOUNTER_BOSS_INTRO &&
        world.encounter_timer == 8 && boss_intro_audio_play_count == 0)
    {
        play_pcm_committed(&boss_intro_sound, sequence_channel_sound,
                           AVSP_PCM_CHANNEL_SEQUENCE);
        sequence_channel_sound = &boss_intro_sound;
        ++boss_intro_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_BOSS_DEFEAT &&
        world.encounter_timer == 150 && boss_clear_audio_play_count == 0 &&
        boss_clear_sound.data != JO_NULL)
    {
        play_pcm_committed(&boss_clear_sound, sequence_channel_sound,
                           AVSP_PCM_CHANNEL_SEQUENCE);
        sequence_channel_sound = &boss_clear_sound;
        ++boss_clear_audio_play_count;
    }
    if ((boss_intro_audio_play_count > 0 || boss_clear_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_SEQUENCE))
        sequence_audio_channel_observed = 1;
    /* The doorway voice and following transition effect are source-sequential,
       so one bounded SCSP channel reproduces both without consuming the final
       available slot. Their native state timers are aligned to source frames
       5384 (+44 from the doorway anchor) and 5438 (+38 from the interior
       transition anchor). */
    if (world.encounter_state == CAP_ENCOUNTER_DOOR_DIALOGUE &&
        world.encounter_timer == 44 && door_dialogue_audio_play_count == 0)
    {
        play_pcm_committed(&door_dialogue_sound, transition_channel_sound,
                           AVSP_PCM_CHANNEL_TRANSITION);
        transition_channel_sound = &door_dialogue_sound;
        ++door_dialogue_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_INTERIOR_TRANSITION &&
        world.encounter_timer == 38 &&
        interior_transition_audio_play_count == 0)
    {
        play_pcm_committed(&interior_transition_sound,
                           transition_channel_sound,
                           AVSP_PCM_CHANNEL_TRANSITION);
        transition_channel_sound = &interior_transition_sound;
        ++interior_transition_audio_play_count;
    }
    if ((door_dialogue_audio_play_count > 0 ||
         interior_transition_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_TRANSITION))
        transition_audio_channel_observed = 1;
    /* Character confirmation occurs at source frame 1800. The first Round 1
       cue starts 231 frames later, nine frames before the sampled title card;
       the second starts at title timer 36. The withdraw and breach composites
       then start at barricade timers 95 and 259. Their source windows never
       overlap, so all four reuse the final bounded Jo/SGL PCM channel. */
    if (world.encounter_state == CAP_ENCOUNTER_CHARACTER_CONFIRM &&
        world.encounter_timer == 231 &&
        round_title_a_audio_play_count == 0)
    {
        play_pcm_committed(&round_title_a_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &round_title_a_sound;
        ++round_title_a_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_ROUND_TITLE &&
        world.encounter_timer == 36 && round_title_b_audio_play_count == 0)
    {
        /* The first title cue has completed. Its main-RAM copy is no longer
           needed after SGL reports the shared opening channel idle. */
        if (!jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
            release_pcm_data(&round_title_a_sound);
        play_pcm_committed(&round_title_b_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &round_title_b_sound;
        ++round_title_b_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO &&
        world.encounter_timer == 95 && withdraw_audio_play_count == 0)
    {
        if (!jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        {
            release_pcm_data(&round_title_a_sound);
            release_pcm_data(&round_title_b_sound);
        }
        play_pcm_committed(&withdraw_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &withdraw_sound;
        ++withdraw_audio_play_count;
    }
    if (world.encounter_state == CAP_ENCOUNTER_BARRICADE_INTRO &&
        world.encounter_timer == 259 && breach_audio_play_count == 0)
    {
        /* The source withdrawal composite ends at barricade timer 228. Free
           that 396 KiB block and reuse it as the complete eight-slot alien
           decode pool before the breach reveals the first playable wave. */
        /* slPCMStat can remain asserted after the finite source buffer has
           elapsed on Yaba Sanshiro. The capture has already been silent for
           31 source frames here, so explicitly close and flush the slot before
           returning its main-RAM buffer to the phase overlay. */
        if (jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        {
            jo_audio_stop_sound(&withdraw_sound);
            slSndFlush();
        }
        release_pcm_data(&round_title_a_sound);
        release_pcm_data(&round_title_b_sound);
        release_pcm_data(&withdraw_sound);
        if (!prepare_enemy_runtime())
        {
            runtime_ready = 0;
            return;
        }
        play_pcm_committed(&breach_sound, opening_channel_sound,
                           AVSP_PCM_CHANNEL_OPENING);
        opening_channel_sound = &breach_sound;
        ++breach_audio_play_count;
    }
    if ((round_title_a_audio_play_count > 0 ||
         round_title_b_audio_play_count > 0 ||
         withdraw_audio_play_count > 0 || breach_audio_play_count > 0) &&
        jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        opening_audio_channel_observed = 1;
    if (world.encounter_state == CAP_ENCOUNTER_WAVE_ONE &&
        breach_sound.data != JO_NULL &&
        !jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING))
        release_pcm_data(&breach_sound);
#ifdef AVSP_VISUAL_TEST
    if (world.player.action == CAP_ACT_WALK)
        world.player.x = JO_TV_WIDTH_2;
#endif
    if (!activate_route_sequence(sequence_scene_for_world()))
    {
        runtime_ready = 0;
        return;
    }
    if (world.encounter_started && !stage_music_started)
    {
        /* Track 2 is an ignored, locally captured QSound reference mix. The
           Saturn plays it through its CD audio path; no QSound emulator ships
           in the executable. Isolated SCSP PCM event cues are the next audio
           fidelity step. */
        /* Boot-bringup probe: the second boot wall is ST 3 / T 2 - exactly
         * when this CD-DA start command fires - matching a CDC command
         * ACK spin. Disabled to test; stage music returns once the CD
         * track start is made non-blocking or the cue layout is fixed. */
        /* jo_audio_play_cd_track(2, 2, true); */
        stage_music_started = 1;
        avsp_frontend_lock_disc_reads(&frontend_runtime);
        /* The data-read guard mirrors the frontend lock: from here the
           drive belongs to CDDA (the start call is temporarily disabled,
           but the residency contract is enforced as if it were live). */
        avsp_disc_guard_cdda_started(&avsp_disc_guard_state);
    }
#ifdef AVSP_VISUAL_TEST
    {
        int clip = visual_enemy_action_index;
        int total = avsp_enemy_total_frames[clip];
        CapActor *enemy = &world.enemies[0];
        enemy->x = world.player.x + 112;
        enemy->lane = world.player.lane;
        enemy->action = visual_enemy_action_for_index(visual_enemy_action_index);
        enemy->active = 1;
        enemy->kind = CAP_ACTOR_ALIEN;
        enemy->facing = -1;
        if (enemy->action == CAP_ACT_WALK)
            enemy->locomotion_frame = visual_enemy_frame;
        else
            enemy->action_frame = visual_enemy_frame;
        ++visual_enemy_frame;
        if (visual_enemy_frame >= total)
        {
            visual_enemy_frame = 0;
            visual_enemy_action_index =
                (visual_enemy_action_index + 1) % AVSP_ENEMY_ACTION_CLIPS;
        }
    }
#endif
    if (jo_is_pad1_key_down(JO_KEY_X)) debug_hud_enabled = !debug_hud_enabled;
    /* Boot-bringup breadcrumb: encounter state + timer heartbeat. The
     * staged boot into WAVE_ONE is now verified, so this no longer runs
     * unconditionally - it drew over the frontend surfaces the visual
     * comparison pass captures. Kept behind the debug HUD toggle because
     * it still distinguishes "stuck inside a draw/load call" from "state
     * machine never transitions". */
    if (debug_hud_enabled)
    {
        jo_printf(0, 0, "ST %d T %d F %d   ",
                  (int)world.encounter_state, (int)world.encounter_timer,
                  (int)world.frame);
    }
    /* Rows 24/25: draw_hud() runs after this and rewrites rows 0-7, so a
     * diagnostic printed on row 2 was overwritten in the same frame - it could
     * never be read back. These two rows are clear of every overlay. */
    if (debug_hud_enabled && rom_actor_entry_count > 0)
    {
        jo_printf(0, 24, "ROM n=%d code=%04x MISS %d/%d/%d POOL %d    ",
                  rom_actor_entry_count, rom_actor_entries[0].code,
                  tile_diag_no_bank, tile_diag_no_rank, tile_diag_no_sprite,
                  tile_pool_used);
        jo_printf(0, 25, "COLL N%d/%d G%d/%d C%d/%d H%d/%d    ",
                  rom_collision_no_hurt_frame, rom_collision_no_hurt,
                  rom_collision_gap_frame, rom_collision_gap,
                  rom_class_lookup_miss_frame, rom_class_lookup_miss,
                  cap_rom_box_hits, cap_approx_hits);
    }
    draw_world();
    rom_actor_advance();
    draw_arcade_hud();
    draw_route_overlay();
    draw_hud();
#ifdef AVSP_ENCOUNTER_TEST
    /* Draw test evidence last so captured VDP1 actors cannot obscure it. */
    jo_printf(0, 4, "PCM OPEN %d%d%d%d CH %d SEEN %d",
              round_title_a_audio_play_count,
              round_title_b_audio_play_count,
              withdraw_audio_play_count, breach_audio_play_count,
              jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_OPENING),
              opening_audio_channel_observed);
    jo_printf(0, 5, "PCM D/T %d/%d CH %d SEEN %d",
              door_dialogue_audio_play_count,
              interior_transition_audio_play_count,
              jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_TRANSITION),
              transition_audio_channel_observed);
    jo_printf(0, 6, "PCM SEQ %d/%d CH %d SEEN %d",
              boss_intro_audio_play_count, boss_clear_audio_play_count,
              jo_audio_is_channel_playing(AVSP_PCM_CHANNEL_SEQUENCE),
              sequence_audio_channel_observed);
    jo_printf(0, 7, "PCM CONTACT %d/%d SEEN %d",
              contact_audio_play_count, ko_contact_audio_play_count,
              contact_audio_channel_observed);
    jo_printf(0, 8, "PCM SHOT %d PLAYED %d CH %d SEEN %d",
              world.shots_fired, weapon_audio_played_shots,
              jo_audio_is_channel_playing(
                  weapon_sound.current_playing_channel),
              weapon_audio_channel_observed);
    jo_printf(0, 9, "PCM MELEE %d CH %d SEEN %d",
              melee_audio_play_count,
              jo_audio_is_channel_playing(melee_sound.current_playing_channel),
              melee_audio_channel_observed);
    jo_printf(0, 10, "ENCOUNTER %d KO %d/%d ACTIVE %d EXIT %d LVL %d",
              world.encounter_state, world.enemies_defeated,
              CAP_STAGE1_TOTAL_ENEMIES, active_enemy_count(),
              world.stage_transitioned, world.level_completed);
    jo_printf(0, 11, "FRONT SEL %d CUR %d ADAPT %d LATE %d MISS %d",
              world.selected_character, world.selection_cursor,
              world.adapted_character_fallbacks,
              frontend_runtime.late_disc_reads,
              frontend_runtime.missing_assets);
    jo_printf(0, 12, "FRONT RLE %d PAL %d CMD %d",
              frontend_runtime.rle_errors, frontend_runtime.palette_errors,
              frontend_runtime.vdp1_commands_last_frame);
#endif
#ifdef AVSP_VISUAL_TEST
    jo_printf(0, 5, "VISUAL A%d P%02d/%02d E%d:%03d/%02d",
              world.player.action, world.player.action_frame,
              current_player_action_pose,
              visual_enemy_action_index, visual_enemy_frame,
              current_enemy_action_poses[0]);
#endif
#ifdef AVSP_BOSS_HIT_TEST
    jo_printf(0, 20, "BOSS HIT A%d F%02d P%02d HP %02d",
              world.enemies[0].action, world.enemies[0].action_frame,
              current_boss_action_pose, world.enemies[0].health);
#endif
#ifdef AVSP_BOSS_KO_TEST
    jo_printf(0, 20, "BOSS KO A%d F%03d P%02d LIVE %d",
              world.enemies[0].action, world.enemies[0].action_frame,
              current_boss_action_pose, world.enemies[0].active);
#endif
    avsp_diag_runtime_ready = runtime_ready;
    avsp_diag_encounter_state = (int)world.encounter_state;
    avsp_diag_world_frame = world.frame;
    avsp_diag_selected_character = (int)world.selected_character;
    avsp_diag_selection_cursor = world.selection_cursor;
    avsp_diag_encounter_timer = (int)world.encounter_timer;
    avsp_diag_background_bitmap = (int)background_bitmap;
    avsp_diag_frontend_late_reads = frontend_runtime.late_disc_reads;
    avsp_diag_frontend_missing_assets = frontend_runtime.missing_assets;
    avsp_diag_frontend_rle_errors = frontend_runtime.rle_errors;
    avsp_diag_frontend_palette_boundary_writes =
        frontend_runtime.palette_boundary_writes;
    avsp_diag_frontend_palette_errors = frontend_runtime.palette_errors;
    avsp_diag_frontend_commands = frontend_runtime.vdp1_commands_last_frame;
}

void jo_main(void)
{
    int index;
#if defined(AVSP_PLAYER_PROMOTION_BENCH) && \
    !defined(AVSP_PLAYER_ENEMY_INTEGRATION)
    AvspPortV2PlayerLoadOps player_load_operations;
#endif
    failed_asset = JO_NULL;
    avsp_disc_guard_init(&avsp_disc_guard_state);
    background_bitmap = JO_NULL;
    background_image.data = JO_NULL;
    boss_background_image.data = JO_NULL;
    hud_top_image.data = JO_NULL;
    hud_prompt_image.data = JO_NULL;
    hud_heat_image.data = JO_NULL;
#ifdef AVSP_HUD_PCM_SALVAGE_BENCH
    hud_p2_top_image.data = JO_NULL;
    hud_p2_heat_image.data = JO_NULL;
#endif
    debug_hud_enabled = 0;
    stage_music_started = 0;
    weapon_audio_played_shots = 0;
    weapon_audio_pending_shot = 0;
    weapon_audio_channel_observed = 0;
    melee_audio_pending = 0;
    melee_audio_play_count = 0;
    melee_audio_channel_observed = 0;
    contact_audio_play_count = 0;
    ko_contact_audio_play_count = 0;
    contact_audio_channel_observed = 0;
    contact_channel_sound = JO_NULL;
    boss_intro_audio_play_count = 0;
    boss_clear_audio_play_count = 0;
    sequence_audio_channel_observed = 0;
    sequence_channel_sound = JO_NULL;
    door_dialogue_audio_play_count = 0;
    interior_transition_audio_play_count = 0;
    transition_audio_channel_observed = 0;
    transition_channel_sound = JO_NULL;
    round_title_a_audio_play_count = 0;
    round_title_b_audio_play_count = 0;
    withdraw_audio_play_count = 0;
    breach_audio_play_count = 0;
    opening_audio_channel_observed = 0;
    opening_channel_sound = JO_NULL;
    enemy_action_buffer = JO_NULL;
    enemy_runtime_ready = 0;
    boss_action_image.data = JO_NULL;
    boss_runtime_ready = 0;
    current_bitmap_scene = BITMAP_SCENE_NONE;
#ifdef AVSP_VISUAL_TEST
    visual_action_index = 0;
    visual_walk_frames = 0;
    visual_enemy_action_index = 0;
    visual_enemy_frame = 0;
    debug_hud_enabled = 1;
#endif
#ifdef AVSP_FRONTEND_TEST
    debug_hud_enabled = 1;
#endif
#ifdef AVSP_FRONTEND_SHOT_TEST
    /* The visual pass compares frontend surfaces; keep the debug text off. */
    debug_hud_enabled = 0;
#endif
    sequence_pixels = JO_NULL;
    for (index = 0; index < AVSP_SEQUENCE_SCENES; ++index)
        sequence_rle[index] = JO_NULL;

    jo_core_init(JO_COLOR_Black);
    cart_available = jo_get_extended_ram_cartridge_type() == CART_32MBits;
    if (cart_available)
    {
        /* Jo Engine registers only DRAM0 for a 32 Mbit cartridge. The Sega
           expansion-RAM map provides a second 2 MiB data bank at
           0x22600000-0x227fffff. Register it before loading assets so the
           runtime can use the cartridge's complete 4 MiB capacity. The
           first AVSP_TILE_REGION_BYTES are carved out for the ROM tile
           archive and stay outside the allocator. */
        jo_add_memory_zone(AVSP_CART_DRAM1_BASE + AVSP_TILE_REGION_BYTES +
                               AVSP_STRIPS_REGION_BYTES,
                           AVSP_CART_DRAM1_BYTES - AVSP_TILE_REGION_BYTES -
                               AVSP_STRIPS_REGION_BYTES);
    }
#ifndef AVSP_PROBE3
    set_actor_palette();
#endif
#if defined(AVSP_PROBE3)
    avsp_probe3_init();
    probe3_last_mode = -1;
    probe3_frame_number = 0;
    probe3_vblank_fields = 0;
    probe3_vblank_raw = (unsigned long)(unsigned int)jo_time_get_frc();
    probe3_vblank_timestamp = probe3_vblank_raw;
    probe3_field_period_ticks = 0UL;
    probe3_pending_measurement = 0;
    probe3_submission_needs_arm = 0;
    probe3_need_census = 0;
    probe3_irq_census_ready = 0UL;
    probe3_draw_end_reliable = 0UL;
    probe3_draw_end_armed = 0UL;
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
        avsp_probe3_telemetry.status = PROBE3_STATUS_FAILED;
        avsp_probe3_telemetry.failure_reason = PROBE3_FAILURE_ASSET;
    }
    else
    {
        runtime_ready = load_tile_archive();
        if (!runtime_ready)
        {
            avsp_probe3_telemetry.status = PROBE3_STATUS_FAILED;
            avsp_probe3_telemetry.failure_reason = PROBE3_FAILURE_ASSET;
        }
    }
    JO_UNUSED_ARG(index);
#elif defined(AVSP_PLAYABLE_SLICE)
    set_frontend_palettes();
    set_hud_palette();
    cap_world_init(&world);
    hud_pcm_bench_init();
    runtime_ready = playable_slice_init();
#ifdef AVSP_LIVE_ENCOUNTER
    avsp_live_encounter_init(&live_encounter_runtime);
    avsp_diag_live_frame_stage = 0;
    avsp_diag_live_internal_failures = 0;
    avsp_diag_live_pcm_retriggers = 0;
    avsp_diag_live_contract_flags =
        (int)avsp_live_encounter_contract_flags();
#ifdef AVSP_LIVE_ENCOUNTER_AUTOTEST
    live_autotest_phase = 0;
    live_autotest_release = 0;
#endif
    avsp_diag_live_physical_saturn = 0;
    runtime_ready = runtime_ready && avsp_diag_live_contract_flags == 127;
#endif
    if (!runtime_ready) failed_asset = "PLAYABLE SLICE FAILED";
    JO_UNUSED_ARG(index);
#elif defined(AVSP_HIT_KO_PROMOTION_BENCH)
    runtime_ready = avsp_hit_ko_diagnostic_init();
    if (!runtime_ready) failed_asset = "HIT KO BENCH FAILED";
    JO_UNUSED_ARG(index);
#elif defined(AVSP_COLLISION_SALVAGE_BENCH)
    runtime_ready = collision_bench_init();
    if (!runtime_ready) failed_asset = "COLLISION BENCH FAILED";
    JO_UNUSED_ARG(index);
#elif defined(AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH) || \
      defined(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH)
    runtime_ready = pw_action_bench_init();
    if (!runtime_ready) failed_asset = "P WARRIOR ACTION BENCH FAILED";
    JO_UNUSED_ARG(index);
#elif defined(AVSP_STREET_ALIEN_AI_SALVAGE_BENCH) || \
      defined(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH)
    runtime_ready = alien_ai_bench_init();
    if (!runtime_ready) failed_asset = "STREET ALIEN AI BENCH FAILED";
    JO_UNUSED_ARG(index);
#elif defined(AVSP_PLAYER_SALVAGE_BENCH)
#ifdef AVSP_PLAYER_ENEMY_INTEGRATION
    {
        AvspPortV2PlayerEnemyLoadOps operations;
        operations.load_tile_archive = load_tile_archive;
        operations.load_background = load_background;
        operations.load_player_idle = load_all_cels;
        operations.load_player_actions = load_player_action_sequences;
        operations.create_player_sprites = create_player_sprite_working_set;
        runtime_ready = avsp_port_v2_player_enemy_load(cart_available, &operations);
        avsp_diag_integration_loader_order_ok = runtime_ready;
        avsp_diag_player_loader_adapter_ok = runtime_ready;
        avsp_diag_enemy_loader_adapter_ok = runtime_ready;
        if (!cart_available) failed_asset = "4MB RAM CART REQUIRED";
    }
#else
#ifdef AVSP_PLAYER_PROMOTION_BENCH
    player_load_operations.load_background = load_background;
    player_load_operations.load_idle_cels = load_all_cels;
    player_load_operations.load_action_sequences =
        load_player_action_sequences;
    player_load_operations.create_sprite_working_set =
        create_player_sprite_working_set;
    runtime_ready = avsp_port_v2_player_load(
        cart_available, &player_load_operations);
    avsp_diag_player_loader_adapter_ok = runtime_ready;
    if (!cart_available) failed_asset = "4MB RAM CART REQUIRED";
#else
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        /* Player-only resident set: fixed background, two idle layers, action
         * archive/decode buffers, actor palette, and VDP1 sprites.  No stage
         * route, enemy archive, collision model, HUD, PCM, or CDDA loads. */
        runtime_ready = load_background() && load_all_cels() &&
                        load_player_action_sequences() &&
                        create_player_sprite_working_set();
    }
#endif
#endif
    if (runtime_ready) player_bench_init();
    JO_UNUSED_ARG(index);
#elif defined(AVSP_CDDA_RESIDENCY_SALVAGE_BENCH)
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        /* CDDA-only residency body: the track streams from disc and the only
         * phase-owned allocation is the canary-wrapped legal-read buffer. */
        #ifdef AVSP_CDDA_RESIDENCY_PROMOTION_BENCH
        runtime_ready = cdda_residency_promotion_init();
        #else
        runtime_ready = cdda_residency_bench_init();
        #endif
        if (!runtime_ready) failed_asset = "CDDA RESIDENCY BENCH";
    }
    JO_UNUSED_ARG(index);
#elif defined(AVSP_HUD_PCM_SALVAGE_BENCH)
    set_hud_palette();
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        /* Isolated HUD/PCM resident set. No player/enemy archive, camera,
         * stage expansion, CDDA, combat, or loading-phase redesign. */
        runtime_ready = load_hud_assets() && load_player2_hud_assets() &&
            load_pcm_audio(&melee_sound, AVSP_MELEE_PCM_FILE,
                           AVSP_MELEE_PCM_DIRECTORY,
                           AVSP_MELEE_PCM_BYTES,
                           AVSP_MELEE_PCM_SAMPLE_RATE) &&
            create_hud_sprite_working_set() &&
            hud_pcm_sound_valid(&melee_sound);
    }
    cap_world_init(&world);
    if (runtime_ready) hud_pcm_bench_init();
    JO_UNUSED_ARG(index);
#elif defined(AVSP_ENEMY_SALVAGE_BENCH)
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        /* Isolated class-0x1F ROM tile path. No capture-cel fallback,
         * AI, collision, camera movement, HUD, PCM, CDDA, or stage route. */
#ifdef AVSP_ENEMY_PROMOTION_BENCH
        AvspPortV2EnemyLoadOps operations;
        operations.load_tile_archive = load_tile_archive;
        operations.load_background = load_background;
        runtime_ready = avsp_port_v2_enemy_load(cart_available, &operations);
        avsp_diag_enemy_loader_adapter_ok = runtime_ready;
#else
        runtime_ready = load_tile_archive() && load_background();
#endif
    }
    if (runtime_ready) enemy_bench_init();
    JO_UNUSED_ARG(index);
#else
    set_frontend_palettes();
    set_hud_palette();
    if (!cart_available)
    {
        failed_asset = "4MB RAM CART REQUIRED";
        runtime_ready = 0;
    }
    else
    {
        /* The ROM tile archive loads FIRST: it needs one ~200 KB
           contiguous cartridge block, and the boot asset sweep below
           fills both cartridge banks nearly to capacity (the measured
           post-boot free space is under 130 KB per bank). No CDDA is
           active at init, so the early read is seek-safe. */
        runtime_ready = load_tile_archive() &&
                        load_route_sequences() &&
                        load_background() && load_boss_background() &&
                        load_frontend_assets() &&
                        load_hud_assets() &&
                        load_action_audio() &&
                        load_all_cels() && load_player_action_sequences() &&
                        load_enemy_action_archive() &&
                        create_sprite_working_set() &&
                        avsp_frontend_load_title_objects(&frontend_runtime) &&
                        /* LAST on purpose: the opening overlay's ~900 KB must
                           sit at the top of its zone so its release rolls the
                           bump pointer back for the BOSSCLR.PCM phase load
                           (see load_opening_audio). */
                        load_opening_audio();
    }
#ifdef AVSP_VISUAL_TEST
    if (runtime_ready)
    {
        /* The visual loop starts directly in combat and never consumes the
           frontend opening cues, so release their overlay immediately. */
        release_pcm_data(&round_title_a_sound);
        release_pcm_data(&round_title_b_sound);
        release_pcm_data(&withdraw_sound);
        release_pcm_data(&breach_sound);
        runtime_ready = prepare_enemy_runtime();
    }
#endif
#if defined(AVSP_BOSS_HIT_TEST) || defined(AVSP_BOSS_KO_TEST)
    if (runtime_ready)
    {
        /* Focused boss diagnostics bypass the frontend, so the main loop's
           CHARACTER_SELECT/CONFIRM scene releases are skipped; free those
           lifetime assets here to leave room for the stage working set. The
           boss itself is composed from ROM tables and needs no archive. */
        release_frontend_scene(0);
        release_frontend_scene(1);
        release_pcm_data(&round_title_a_sound);
        release_pcm_data(&round_title_b_sound);
        release_pcm_data(&withdraw_sound);
        release_pcm_data(&breach_sound);
        /* The four frees above are not last-in-first-out, so only the final
           one rolled the bump pointer back; compact the rest of the trailing
           free run before the large allocation below. */
        jo_reduce_memory_fragmentation();
        /* These profiles skip the interior transition where the Stage
           Clear composite is phase-loaded; load it here instead so a
           forced BOSS_DEFEAT still plays it. */
        if (runtime_ready)
            runtime_ready = load_pcm_audio(
                &boss_clear_sound, AVSP_BOSS_CLEAR_PCM_FILE,
                AVSP_BOSS_CLEAR_PCM_DIRECTORY, AVSP_BOSS_CLEAR_PCM_BYTES,
                AVSP_BOSS_CLEAR_PCM_SAMPLE_RATE);
    }
#endif
    cap_world_init(&world);
#if defined(AVSP_BOSS_HIT_TEST) || defined(AVSP_BOSS_KO_TEST)
    world.encounter_started = 1;
    world.encounter_state = CAP_ENCOUNTER_BOSS;
    world.room_locked = 1;
    world.stage_area = 1;
#ifdef AVSP_BOSS_KO_TEST
    world.boss_reinforcement_wave = 2;
#endif
    world.frame = 1;
    world.player.x = 170;
    world.player.lane = 182;
    for (index = 0; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].active = 0;
    world.enemies[0].x = 240;
    world.enemies[0].lane = world.player.lane;
    world.enemies[0].height = 0;
    world.enemies[0].facing = -1;
    world.enemies[0].health =
#ifdef AVSP_BOSS_KO_TEST
        0;
    world.enemies[0].action = CAP_ACT_KO;
#else
        21;
    world.enemies[0].action = CAP_ACT_HIT;
#endif
    world.enemies[0].action_frame = 0;
    world.enemies[0].active = 1;
    world.enemies[0].kind = CAP_ACTOR_BOSS;
    debug_hud_enabled = 1;
#elif defined(AVSP_VISUAL_TEST)
    world.encounter_started = 1;
    world.encounter_state = CAP_ENCOUNTER_WAVE_ONE;
    world.room_locked = 1;
    world.frame = 1;
    world.player.x = JO_TV_WIDTH_2;
    world.enemies[0].x = world.player.x + 112;
    world.enemies[0].lane = world.player.lane;
    for (index = 1; index < CAP_MAX_ENEMIES; ++index)
        world.enemies[index].x = 900;
#else
    JO_UNUSED_ARG(index);
#endif
#endif
    jo_core_set_screens_order(JO_NBG0_SCREEN, JO_SPRITE_SCREEN, JO_NBG1_SCREEN);
#ifdef AVSP_PROBE3
    jo_core_add_vblank_callback(probe3_vblank_callback);
    probe3_previous_sprite_irq =
        PROBE3_SYS_GET_SCU_HANDLER(PROBE3_SCU_SPR_VECTOR);
    PROBE3_SYS_SET_SCU_HANDLER(PROBE3_SCU_SPR_VECTOR,
                               probe3_sprite_draw_end_irq);
    PROBE3_SYS_CHANGE_SCU_MASK(~PROBE3_SCU_SPR_MASK, 0UL);
#endif
#ifdef AVSP_PROBE3
    probe3_run_loop();
#else
    jo_core_add_callback(frame_callback);
    jo_core_run();
#endif
}
