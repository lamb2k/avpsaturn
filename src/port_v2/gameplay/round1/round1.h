#ifndef AVSP_PORT_V2_ROUND1_H
#define AVSP_PORT_V2_ROUND1_H

#include "../player_action/player_action.h"
#include "../street_alien_ai/street_alien_ai.h"
#include "../../combat/hit_ko/hit_ko.h"

#define AVSP_ROUND1_SPEC02_SHA256 \
"b70488087c0d4f512fa9a08fa0336a6bec35e8d0a733f2886d014a42b10bad5c"
#define AVSP_ROUND1_CANARY_HEAD 0x52314548UL
#define AVSP_ROUND1_CANARY_TAIL 0x52314554UL
#define AVSP_ROUND1_ROUTE_ENTRY_STATE 2
#define AVSP_ROUND1_INITIAL_RNG 0x8DEFu
#define AVSP_ROUND1_PLAYER_HEALTH 101
#define AVSP_ROUND1_POOL_COUNT 6
#define AVSP_ROUND1_MAX_POOL_CAPACITY 64
#define AVSP_ROUND1_FIRST_SPAWN_COUNT 10
#define AVSP_ROUND1_ENTRY_PROGRAM_BYTES 26
#define AVSP_ROUND1_ENTRY_STEP_COUNT 8
#define AVSP_ROUND1_SCHEDULER_POOL_COUNT 6
#define AVSP_ROUND1_SCHEDULER_GLOBAL_COUNT 2u
#define AVSP_ROUND1_SCHEDULER_GLOBAL_CAMERA_X_PREVIOUS 1u
#define AVSP_ROUND1_SCHEDULER_GLOBAL_CAMERA_Z_PREVIOUS 2u
#define AVSP_ROUND1_REQUIRED_DISPATCH_COUNT 16
#define AVSP_ROUND1_SCHEDULER_TRACE_CAPACITY 192
#define AVSP_ROUND1_PLAYER_ENTRY_STATE 2048u
#define AVSP_ROUND1_PLAYER_CONTROL_STATE 512u
#define AVSP_ROUND1_PLAYER_MELEE_COUNT 4u
#define AVSP_ROUND1_PLAYER_CONTEXTUAL_MELEE_SEQUENCE_COUNT 2u
#define AVSP_ROUND1_PLAYER_CONTEXTUAL_MELEE_MAX_RECORDS 6u
#define AVSP_ROUND1_PLAYER_CONTEXTUAL_MELEE_AUDIO_COUNT 2u
#define AVSP_ROUND1_PLAYER_HIT_SHAKE_COUNT 32u
#define AVSP_ROUND1_PLAYER_HIT_REACTION_COUNT 3u
#define AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT 12u
#define AVSP_ROUND1_PLAYER_JUMP_VECTOR_COUNT 6u
#define AVSP_ROUND1_PLAYER_JUMP_DOWN_VECTOR_COUNT 2u
#define AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_COUNT 9u
#define AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_MAX_RECORDS 8u
#define AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT 20u
#define AVSP_ROUND1_PLAYER_WEAPON_SELECTOR_COUNT 4u
#define AVSP_ROUND1_PLAYER_WEAPON_SEQUENCE_COUNT 5u
#define AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT 18u
#define AVSP_ROUND1_PLAYER_SPECIAL_PRESENTATION_COUNT 17u
#define AVSP_ROUND1_CLASS4B_PRESENTATION_COUNT 32u
#define AVSP_ROUND1_CLASS3D_PRESENTATION_COUNT 9u
#define AVSP_ROUND1_CLASS3D_OFFSET_COUNT 16u
#define AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY 24u
#define AVSP_ROUND1_WEAPON_PARENT_PRESENTATION_COUNT 8u
#define AVSP_ROUND1_WEAPON_PARENT_SELECTOR_COUNT 6u
#define AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT 31u
#define AVSP_ROUND1_WEAPON_TARGET_DISTANCE_COUNT 16u
#define AVSP_ROUND1_WEAPON_PARENT_LOW_MOTION_COUNT 16u
#define AVSP_ROUND1_WEAPON_PARENT_HIGH_MOTION_COUNT 13u
#define AVSP_ROUND1_AIR_WEAPON_SELECTOR_COUNT 7u
#define AVSP_ROUND1_AIR_WEAPON_PRESENTATION_COUNT 8u
#define AVSP_ROUND1_AIR_WEAPON_PLAYER_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT 64u
#define AVSP_ROUND1_AIR_WEAPON_LOW_TABLE_COUNT 16u
#define AVSP_ROUND1_AIR_WEAPON_HIGH_TABLE_COUNT 13u
#define AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT 5u
#define AVSP_ROUND1_WEAPON_CHILD_VARIANT_COUNT 3u
#define AVSP_ROUND1_WEAPON_CHILD_PRESENTATION_MAX 17u
#define AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT 3u
#define AVSP_ROUND1_EMPTY_EFFECT_VARIANT_COUNT 4u
#define AVSP_ROUND1_EMPTY_EFFECT_PRESENTATION_COUNT 10u
#define AVSP_ROUND1_CLASS1F_INITIAL_ACTOR_COUNT 10u
#define AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT 3u
#define AVSP_ROUND1_CLASS1F_INITIAL_SEQUENCE_COUNT 6u
#define AVSP_ROUND1_CLASS1F_INITIAL_SEQUENCE_MAX_RECORDS 5u
#define AVSP_ROUND1_CLASS1F_APPROACH_RECORD_COUNT 8u
#define AVSP_ROUND1_CLASS1F_ATTACK_RECORD_COUNT 4u
#define AVSP_ROUND1_RECURRING_LIMIT_COUNT 4u
#define AVSP_ROUND1_RECURRING_LANE_OFFSET_COUNT 6u
#define AVSP_ROUND1_RECURRING_SELECTOR_COUNT 10u
#define AVSP_ROUND1_RECURRING_LANE_BUCKET_COUNT 64u
#define AVSP_ROUND1_RECURRING_VARIANT_COUNT 96u
#define AVSP_ROUND1_COFFEE_EXIT_STEP_COUNT 9u
#define AVSP_ROUND1_COFFEE_EXIT_MOTION_COUNT 32u
#define AVSP_ROUND1_COFFEE_EXIT_CALLBACK_GROUP_COUNT 25u
#define AVSP_ROUND1_COFFEE_EXIT_LOAD_COUNT 2u
#define AVSP_ROUND1_EXIT_STEP_BOOTSTRAP 0u
#define AVSP_ROUND1_EXIT_STEP_MOVE_TO 1u
#define AVSP_ROUND1_EXIT_STEP_SET_MODE 2u
#define AVSP_ROUND1_EXIT_STEP_DWELL 3u
#define AVSP_ROUND1_EXIT_STEP_TERMINATE 4u
#define AVSP_ROUND1_EXIT_STEP_BALLISTIC 5u
#define AVSP_ROUND1_CLASS1F_ACTION_TARGET_COUNT 16u
#define AVSP_ROUND1_CLASS1F_ACTION_VARIANT_COUNT 10u
#define AVSP_ROUND1_CLASS1F_ACTION_SELECTOR_COUNT 22u
#define AVSP_ROUND1_CLASS1F_ACTION_RECORD_COUNT 132u
#define AVSP_ROUND1_CLASS1F_ACTION4_RANDOM_GROUP_COUNT 32u
#define AVSP_ROUND1_CLASS1F_ACTION4_GROUP_COUNT 4u
#define AVSP_ROUND1_CLASS1F_ACTION4_SELECTOR_COUNT 9u
#define AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT 32u
#define AVSP_ROUND1_CLASS1F_ACTION4_TIMER_ROW_COUNT 5u
#define AVSP_ROUND1_CLASS1F_MOVEMENT_TABLE_COUNT 2u
#define AVSP_ROUND1_CLASS1F_MOVEMENT_DIRECTION_COUNT 32u
#define AVSP_ROUND1_CLASS1F_INNER8_RECORD_COUNT 152u
#define AVSP_ROUND1_CLASS1F_INNER8_MOVEMENT_TABLE_COUNT 10u
#define AVSP_ROUND1_CLASS1F_ATTACK_TIMER_COUNT 16u
#define AVSP_ROUND1_CLASS1F_SOURCE_HIT_PHASE_COUNT 6u
#define AVSP_ROUND1_CLASS1F_SOURCE_HIT_RNG_TIMER_COUNT 16u
#define AVSP_ROUND1_CLASS1F_SOURCE_HIT_REACTION_RECORD_COUNT 6u
#define AVSP_ROUND1_CLASS1F_SOURCE_HIT_TERMINAL_RECORD_COUNT 11u
#define AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT 2u
#define AVSP_ROUND1_CLASS09_SEQUENCE_COUNT 5u
#define AVSP_ROUND1_CLASS09_SEQUENCE_RECORDS 2u
#define AVSP_ROUND1_CLASS4E_JITTER_COUNT 8u
#define AVSP_ROUND1_CLASS4E_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_CLASS4E_VARIANT0_PRESENTATION_COUNT 3u
#define AVSP_ROUND1_CLASS4E_VARIANT1_PRESENTATION_COUNT 3u
#define AVSP_ROUND1_CLASS4E_VARIANT5_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_CLASS4E_VARIANT10_PRESENTATION_COUNT 6u
#define AVSP_ROUND1_CLASS4E_VARIANT20_PRESENTATION_COUNT 8u
#define AVSP_ROUND1_CLASS44_PRESENTATION_COUNT 2u
#define AVSP_ROUND1_CLASS43_SELECTOR_COUNT 32u
#define AVSP_ROUND1_CLASS43_SEQUENCE_COUNT 16u
#define AVSP_ROUND1_CLASS43_PRESENTATION_COUNT 70u
#define AVSP_ROUND1_CLASS43_MOTION_COUNT 8u
#define AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT 28u
#define AVSP_ROUND1_CLASS45_SELECTOR_COUNT 32u
#define AVSP_ROUND1_CLASS45_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_CLASS45_MOTION_COUNT 8u
#define AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT 3u
#define AVSP_ROUND1_CLASS47_SCENE_ACTOR_COUNT 4u
#define AVSP_ROUND1_CLASS47_SELECTOR_COUNT 32u
#define AVSP_ROUND1_CLASS47_PRESENTATION_COUNT 9u
#define AVSP_ROUND1_CLASS47_MOTION_COUNT 8u
#define AVSP_ROUND1_TYPE16_MOTION_COUNT 3u
#define AVSP_ROUND1_TYPE16_PARENT_PRESENTATION_COUNT 11u
#define AVSP_ROUND1_TYPE16_PRESENTATION_COUNT 11u
#define AVSP_ROUND1_COFFEE_SCENE_RECORD_COUNT 6u
#define AVSP_ROUND1_CLASS01_PRESENTATION_COUNT 3u
#define AVSP_ROUND1_CLASS02_PRESENTATION_COUNT 2u
#define AVSP_ROUND1_CLASS05_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_CLASS08_PARENT_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_HEALTH_PICKUP_PRESENTATION_COUNT 1u
#define AVSP_ROUND1_PLAYER_PICKUP_PRESENTATION_COUNT 2u
#define AVSP_ROUND1_TERRAIN_RECORD_COUNT 9u
#define AVSP_ROUND1_TERRAIN_GRID_X_MIN 640
#define AVSP_ROUND1_TERRAIN_GRID_X_MAX 1360
#define AVSP_ROUND1_TERRAIN_GRID_Z_MIN 272
#define AVSP_ROUND1_TERRAIN_GRID_Z_MAX 400
#define AVSP_ROUND1_TERRAIN_GRID_TILE_SIZE 16u
#define AVSP_ROUND1_TERRAIN_GRID_WIDTH 46u
#define AVSP_ROUND1_TERRAIN_GRID_HEIGHT 9u
#define AVSP_ROUND1_TERRAIN_GRID_CELL_COUNT 414u
#define AVSP_ROUND1_TERRAIN_PACKED_BYTES 104u
#define AVSP_ROUND1_TERRAIN_SELECTOR_MAP_COUNT 4096u
#define AVSP_ROUND1_TERRAIN_SELECTOR_RUN_COUNT 383u
#define AVSP_ROUND1_TERRAIN_STREAM_TRANSACTION_COUNT 41u
#define AVSP_ROUND1_TERRAIN_STREAM_WRITE_COUNT 1476u
#define AVSP_ROUND1_CAMERA_SPEED_COUNT 20u
#define AVSP_ROUND1_INPUT_BUTTON1 0x0010u
#define AVSP_ROUND1_INPUT_BUTTON3 0x0040u
#define AVSP_ROUND1_FIRST_ENCOUNTER_SLOT 0xA000u
#define AVSP_ROUND1_FIRST_ENCOUNTER_ENTRY_X 1003
#define AVSP_ROUND1_FIRST_ENCOUNTER_WAIT_ENTRY 0u
#define AVSP_ROUND1_FIRST_ENCOUNTER_ACTIVE 1u
#define AVSP_ROUND1_FIRST_ENCOUNTER_CLEARED 2u

#define AVSP_ROUND1_ENTRY_SET_POSITION 1u
#define AVSP_ROUND1_ENTRY_SET_SUBHANDLER 2u
#define AVSP_ROUND1_ENTRY_SOURCE_18 3u
#define AVSP_ROUND1_ENTRY_DWELL 4u
#define AVSP_ROUND1_ENTRY_SOURCE_16 5u
#define AVSP_ROUND1_ENTRY_TERMINATE 6u

#define AVSP_ROUND1_ANIMATION_TERMINAL_LOOP_FIRST 1u
#define AVSP_ROUND1_ANIMATION_TERMINAL_SELF_LOOP 2u
#define AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD 3u

typedef struct
{
    short x;
    short y;
} AvspRound1VecS16;

typedef struct
{
    short route_state;
    unsigned short player_variant;
    unsigned char stage_record_type;
    short stage_row_value;
    unsigned short population_selector;
    unsigned short population_mid_threshold;
    unsigned short population_high_threshold;
    short population_mid_adjustment;
    short population_high_adjustment;
    signed char variant_adjustment;
    unsigned char random_masked_index;
    short random_adjustment;
    signed char post_adjustment;
    short lower_bound;
    short upper_bound;
    unsigned short rng_before;
    unsigned short rng_after;
    short stage_parameter_after;
} AvspRound1CoffeeStageSetupSpec;

typedef struct
{
    short x;
    short y;
    short z;
    unsigned char variant;
} AvspRound1WeaponChildSpawnSpec;

typedef struct
{
    unsigned short timer;
    short branch;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char hurt_selector;
    unsigned char attack_selector;
} AvspRound1AnimationStateSpec;

typedef struct
{
    unsigned short entry_action;
    unsigned short startup_action;
    unsigned short active_action;
    unsigned short cleanup_action;
    unsigned short return_action;
    unsigned char presentation_selector;
    unsigned char contact_attack_selector;
    unsigned char health_cost;
    unsigned char class4b_record_type;
    signed char class4b_class;
    unsigned char class3d_record_type;
    signed char class3d_class;
    unsigned short audio_command_0;
    unsigned short audio_command_1;
} AvspRound1PlayerSpecialSpec;

typedef struct
{
    unsigned char record_count;
    AvspRound1AnimationStateSpec records[
        AVSP_ROUND1_WEAPON_CHILD_PRESENTATION_MAX];
} AvspRound1WeaponChildSequenceSpec;

typedef struct
{
    unsigned char selector;
    unsigned char record_count;
    unsigned char terminal_policy;
    AvspRound1AnimationStateSpec records[
        AVSP_ROUND1_CLASS1F_INITIAL_SEQUENCE_MAX_RECORDS];
} AvspRound1AnimationSequenceSpec;

typedef struct
{
    signed char x_center;
    signed char y_center;
    unsigned char x_half;
    unsigned char y_half;
    signed char z_center;
    unsigned char z_half;
    signed char knockback_mode;
    unsigned char hit_value;
    unsigned char damage_selector;
} AvspRound1CollisionBoxSpec;

typedef struct
{
    unsigned long scene_record;
    unsigned long source_slot;
    unsigned short source_frame;
    unsigned short camera_threshold;
    short x;
    short y;
    unsigned short allocator;
    signed char actor_class;
    unsigned char variant;
    signed char guard_0a;
    unsigned char guard_0b;
    unsigned char facing;
    unsigned char field_0d;
    unsigned short timer;
} AvspRound1CoffeeSceneRecordSpec;

typedef struct
{
    unsigned long dispatch;
    unsigned long animation_table;
    unsigned short timer_variant0;
    unsigned short timer_variant1;
    unsigned short respawn_timer;
    unsigned short camera_activation_distance;
    unsigned short camera_release_distance;
    unsigned char initial_remaining_spawns;
    unsigned char maximum_living;
    signed char spawned_class;
    unsigned char spawned_variant;
    unsigned short initial_audio_command;
    unsigned short variant_audio_command;
} AvspRound1Class01Spec;

typedef struct
{
    unsigned long dispatch;
    unsigned long animation_table;
    unsigned long attack_record;
    unsigned long hurt_record;
    unsigned short camera_bounds_bias;
    unsigned short camera_bounds_span;
    unsigned char initial_effect_count;
    unsigned char child_record_type;
    signed char child_class;
    unsigned char child_variant;
    short child_x_add;
    short child_y_add;
    short child_z_add;
    short damage;
    short ko_clamp;
    unsigned short audio_command;
    unsigned char reaction_direction_less;
    unsigned char reaction_direction_greater_equal;
    AvspRound1CollisionBoxSpec attack_box;
    AvspRound1CollisionBoxSpec hurt_box;
} AvspRound1Class02Spec;

typedef struct
{
    unsigned char class_index;
    unsigned short route_index;
    unsigned char value;
} AvspRound1DamageClassValueSpec;

typedef struct
{
    unsigned char defense;
    unsigned char damage_index;
    unsigned char damage;
} AvspRound1DamageMatrixValueSpec;

typedef struct
{
    unsigned char initial_state;
    unsigned char active_state;
    unsigned char emitter_state;
    unsigned char release_state;
    short x_bound_bias;
    unsigned short x_bound_span;
    short y_bound_bias;
    unsigned short y_bound_span;
    signed char parent_class;
    signed char child_class;
    unsigned char child_count;
    unsigned char child_cadence_initial;
    unsigned char child_cadence_reload;
    unsigned short object_or;
    unsigned long parent_dispatch;
    unsigned long child_dispatch;
    unsigned long parent_attack_table;
    unsigned long child_attack_table;
    short parent_attack_relative;
    short child_attack_relative;
    unsigned short attack_record_stride;
    unsigned char parent_damage;
    unsigned char child_damage;
} AvspRound1WeaponProjectileSpec;

typedef struct
{
    signed char actor_class;
    unsigned char variant;
    unsigned char group_count;
    unsigned char actors_per_group;
    unsigned char rng_calls_per_actor;
    short y_offset;
    short z_offset;
    unsigned long dispatch;
} AvspRound1Class43Spec;

typedef struct
{
    signed char actor_class;
    unsigned char initial_state;
    unsigned char active_state;
    unsigned char emitter_state;
    unsigned char release_state;
    unsigned char player_collision_selector;
    unsigned char child_count;
    unsigned char child_cadence_initial;
    unsigned char child_cadence_reload;
    unsigned char direction_timer_reload;
    unsigned char progress_step;
    unsigned char progress_max;
    unsigned short object_or;
    unsigned long dispatch;
    unsigned long attack_table;
    unsigned char effect_record_type;
    unsigned char effect_class;
    unsigned char effect_variant;
} AvspRound1AirWeaponProjectileSpec;

typedef struct
{
    unsigned char active;
    signed char actor_class;
    unsigned short state;
    unsigned short substate;
    unsigned char type;
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned char facing;
    unsigned char variant;
    unsigned short source_action;
    unsigned long source_slot;
    short x;
    short y;
    short z;
    short health;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char hurt_selector;
    unsigned char attack_selector;
    unsigned short object_or;
    unsigned char source_facing_selector;
    unsigned char source_flags;
    unsigned char source_selector83;
    unsigned char effect_timer;
    unsigned char animation_index;
    unsigned short transition_timer;
    unsigned short animation_timer;
    short animation_branch;
    long source_x_fp;
    long source_y_fp;
    long source_z_fp;
    long source_aux_fp;
    long source_x_velocity;
    long source_x_acceleration;
    long source_z_velocity;
    long source_y_velocity;
    long source_y_acceleration;
    long source_primary_x_fp;
    long source_primary_y_fp;
    long source_alternate_x_fp;
    long source_alternate_y_fp;
    unsigned short source_target_low;
    unsigned short source_bound_b2;
    unsigned char source_direction;
    unsigned char source_action_timer;
    unsigned char source_hitstop;
    unsigned char source_player_collision_latched;
    unsigned char source_a3;
    unsigned char source_a4;
    unsigned char source_a5;
    unsigned char source_a6;
    unsigned char source_special_latch_ad;
    unsigned char source_transition_latch_ae;
    unsigned char source_style85;
    unsigned char source_airborne;
    unsigned char source_b0;
    unsigned char source_action_group;
    unsigned char source_action_group_cursor;
    unsigned char source_player_guard;
    signed char source_inner8_band;
    signed char source_inner8_group;
    unsigned char source_inner8_cursor;
    unsigned char source_inner8_membership;
    unsigned char source_inner8_prior_group;
    unsigned char source_inner8_prior_membership;
    short source_inner8_x_offset;
    short source_inner8_z_offset;
    unsigned char source_action_initialized;
    unsigned char source_dynamic_spawn;
    unsigned char source_projectile_enable;
    unsigned char source_motion_flags;
    short source_motion_fields[8];
    unsigned short source_children[4];
    unsigned char source_field01;
    unsigned char source_collision_guard6d;
    unsigned char source_collision_latches[8];
    unsigned char source_collision_suppress70;
    unsigned char source_collision_current_active;
    signed char source_collision_current_class;
    unsigned short source_collision_current_state;
    short source_collision_current_x;
    short source_collision_current_y;
    short source_collision_current_z;
    short source_collision_current_health;
    unsigned char source_collision_current_facing;
    unsigned char source_collision_current_attack_selector;
    unsigned char source_projectile_reaction_pending;
    unsigned char source_a2;
    unsigned char source_movement_table;
    unsigned char source_navigation_contact_bits;
    unsigned long source_next_animation_record;
    unsigned long source_primary_animation_record;
    unsigned long source_primary_assembly;
    unsigned long source_alternate_animation_record;
    unsigned long source_alternate_assembly;
    unsigned short source_alternate_animation_timer;
    short source_alternate_animation_branch;
    unsigned long dispatch_entry;
    unsigned long scheduler_updates;
    unsigned long handler_updates;
    unsigned long state_handler_updates;
} AvspRound1ActorCore;

/* These class-0x1f HIT fields are phase-exclusive with the inner-state
 * motion scratch and action timer. Keep the aliases explicit so lifting the
 * source fields does not add eight bytes to every record in every fixed pool. */
#define source_hit_mode source_motion_fields[0]
#define source_hit_kind source_motion_fields[1]
#define source_reaction_selector source_motion_fields[2]
#define source_prior_health source_motion_fields[3]
#define source_hit_recovery_active source_motion_fields[4]
#define source_hit_action_timer transition_timer

/* Source class-0x1f inner-state action 0x0c owns four word fields at
 * actor+0x80/+0x82/+0x96/+0x98. They are phase-exclusive with HIT/KO and
 * the action-0x0e motion scratch, so retain the fixed-pool footprint. */
#define source_action0c_plan source_motion_fields[4]
#define source_action0c_cursor source_motion_fields[5]
#define source_action0c_selector source_motion_fields[6]
#define source_action0c_selector_phase source_motion_fields[7]
#define source_action0c_field95 source_motion_flags

/* Class-0x43 uses two presentation channels but has no child actors and only
 * six motion words. Keep its primary-channel timer/branch in phase-exclusive
 * fixed-pool scratch instead of adding four bytes to every actor record. */
#define source_primary_animation_timer source_children[0]
#define source_primary_animation_branch source_motion_fields[6]

typedef struct
{
    unsigned long source_slot;
    unsigned short state;
    unsigned short substate;
    short x;
    short y;
    short z;
    unsigned char facing;
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned short object_or;
    unsigned short transition_timer_initial;
    unsigned char source_flags;
    unsigned char animation_selector;
    unsigned char hurt_selector;
    unsigned char attack_selector;
} AvspRound1Class1fInitialSpec;

typedef struct
{
    unsigned long controller_source_slot;
    unsigned long bounded_dynamic_source_slot;
    unsigned char controller_type;
    signed char controller_class;
    short start_x;
    short start_y;
    short start_z;
    short start_health;
    short approach_x_delta;
    short approach_z_delta;
    unsigned short approach_ticks;
    unsigned short attack_ticks;
    unsigned short contact_tick_a;
    unsigned short contact_tick_b;
    unsigned short contact_damage;
    unsigned short hit_ticks;
    unsigned short ko_ticks;
    unsigned short player_damage[AVSP_ROUND1_PLAYER_MELEE_COUNT];
} AvspRound1Class1fCurrentSpec;

typedef struct
{
    unsigned short state;
    unsigned short entry_action_phase;
    unsigned short next_action_phase;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char reaction_selector;
    unsigned char hit_mode;
    unsigned char hit_kind;
    unsigned char recovery_timer;
    unsigned char action_timer;
    unsigned char recovery_transition_returns;
    unsigned char hurt_selector;
    unsigned char attack_selector;
    unsigned short phases[AVSP_ROUND1_CLASS1F_SOURCE_HIT_PHASE_COUNT];
    long launch_x_velocity_before_facing;
    long launch_x_acceleration_before_facing;
    long launch_y_velocity;
    long launch_y_acceleration;
    long bounce_x_velocity_before_facing;
    long bounce_x_acceleration_before_facing;
    long bounce_y_velocity;
    long bounce_y_acceleration;
    unsigned char landing_hold_timer;
    unsigned char landing_selector;
    unsigned char bounce_selector;
    unsigned char rng_hold_selector;
    unsigned char terminal_selector;
    unsigned short rng_seed_before;
    unsigned short rng_seed_after;
    unsigned char rng_result_low_nibble;
    unsigned char rng_hit_count;
    unsigned char rng_timer_row[AVSP_ROUND1_CLASS1F_SOURCE_HIT_RNG_TIMER_COUNT];
    unsigned char rng_selected_timer;
    unsigned short global_pause_guard_zero;
    unsigned char reaction_record_count;
    AvspRound1AnimationStateSpec reaction_records[
        AVSP_ROUND1_CLASS1F_SOURCE_HIT_REACTION_RECORD_COUNT];
    AvspRound1AnimationStateSpec landing_hold_record;
    AvspRound1AnimationStateSpec bounce_record;
    AvspRound1AnimationStateSpec rng_hold_record;
    unsigned char terminal_record_count;
    AvspRound1AnimationStateSpec terminal_records[
        AVSP_ROUND1_CLASS1F_SOURCE_HIT_TERMINAL_RECORD_COUNT];
    unsigned short normal_return_state;
    unsigned short normal_return_substate;
    unsigned short class1f_resume_substate;
    unsigned char normal_return_style85;
    unsigned char resume_style85;
    unsigned char resume_a3;
    unsigned char resume_a4;
    unsigned char resume_a5;
    unsigned char resume_a6;
    unsigned char resume_b0;
    unsigned char resume_facing;
    short resume_actor_x;
    short resume_actor_z;
    short resume_player_x;
    short resume_player_z;
} AvspRound1Class1fSourceHitSpec;

typedef struct
{
    unsigned short collision_state;
    unsigned short dispatch_state;
    unsigned short hold_state;
    unsigned short release_state;
    unsigned short action_phases[4];
    unsigned char dispatch_active;
    unsigned char reaction_selector;
    unsigned char hit_mode;
    unsigned char hit_kind;
    unsigned char recovery_timer;
    unsigned char landing_hold_timer;
    unsigned char removal_hold_timer;
    unsigned char reaction_record_count;
    long launch_x_velocity_before_facing;
    long launch_x_acceleration_before_facing;
    long launch_y_velocity;
    long launch_y_acceleration;
    long bounce_x_velocity_before_facing;
    long bounce_x_acceleration_before_facing;
    long bounce_y_velocity;
    long bounce_y_acceleration;
    AvspRound1AnimationStateSpec reaction_records[
        AVSP_ROUND1_CLASS1F_SOURCE_HIT_REACTION_RECORD_COUNT];
    AvspRound1AnimationStateSpec landing_hold_record;
    AvspRound1AnimationStateSpec bounce_record;
} AvspRound1Class1fSourceKoSpec;

typedef struct
{
    unsigned char variant;
    unsigned char a4;
    unsigned char a5;
    unsigned char a6;
    unsigned char action;
    unsigned char airborne;
    unsigned char style85;
    unsigned char animation_selector;
    unsigned char timer_aa;
    unsigned char rule_flags;
    unsigned short bound_b2_base;
} AvspRound1Class1fActionVariantSpec;

typedef struct
{
    unsigned char action;
    unsigned long target;
} AvspRound1Class1fActionTargetSpec;

typedef struct
{
    unsigned char selector;
    unsigned short first_record;
    unsigned char record_count;
} AvspRound1Class1fActionSelectorSpec;

typedef struct
{
    unsigned long animation_record;
    unsigned long next_animation_record;
    unsigned long assembly;
    unsigned short timer;
    short branch;
    unsigned char hurt_selector;
    unsigned char attack_selector;
    unsigned char movement_table;
} AvspRound1Class1fActionRecordSpec;

typedef struct
{
    short x_delta;
    short y_delta;
} AvspRound1Class1fMovementVectorSpec;

typedef struct
{
    unsigned char table_index;
    AvspRound1Class1fMovementVectorSpec vectors[
        AVSP_ROUND1_CLASS1F_MOVEMENT_DIRECTION_COUNT];
} AvspRound1Class1fMovementTableSpec;

typedef struct
{
    unsigned short captured_source_slot_low;
    unsigned short inner_timer;
    unsigned short timeout_outer_state;
    unsigned short timeout_action_substate;
    unsigned char timeout_special_latch;
    unsigned short action0_style_bits;
    unsigned short action4_choice_bits;
    unsigned char action4_contact_direction_delta;
    unsigned char action4_direction_mask;
    unsigned char action4_stage_parameter;
    unsigned char action4_timer_bank_by_stage[32];
    signed char action4_timer_banks[8][16];
    unsigned char field88_table[16];
    unsigned char wander_quadrant_delta[16];
    short wander_target_offsets[4];
    unsigned char wander_direction_delta_same_style[32];
    unsigned char wander_direction_delta_other_style[32];
    unsigned char direction_axis_equal[4];
    unsigned char direction_octant_base[32];
    unsigned short wander_band_thresholds[4];
    short wander_z_offset;
    unsigned char wander_group_count;
    unsigned char wander_cursor_limit;
    unsigned char action10_offset_selector[16];
    short action10_x_offsets[3];
    short action10_z_offset;
    unsigned char action10_timer;
    unsigned char action10_lifetime;
    unsigned long turn_records_by_style[2];
    unsigned long movement_records_by_style_relation[4];
    unsigned long action10_phase_records_by_style_relation[4];
    unsigned long style_one_record;
    unsigned long style_zero_record;
    unsigned long idle_record;
    unsigned long mismatch_zero_record;
    unsigned long mismatch_zero_follow_record;
    unsigned long motion_record;
    unsigned long airborne_record;
    unsigned long parent_record;
    unsigned short target_x_span;
    unsigned short target_z_span;
    unsigned short attack_x_span;
    unsigned short attack_z_span;
    unsigned char terminal_delay;
    unsigned char motion_selector;
    long x_velocity_by_facing[2];
    long x_acceleration;
    long y_velocity;
    long y_acceleration;
    unsigned short action0c_plan_by_rng_index[32];
    signed short action0c_selector_sequences[8][5];
    unsigned char action0c_selector_by_field96[8];
    unsigned long action0c_record_by_field96[8];
    unsigned char action0c_timer_stage_offsets[32];
    unsigned char action0c_timer_rows[
        AVSP_ROUND1_CLASS1F_ACTION4_TIMER_ROW_COUNT]
        [AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT];
    unsigned char action0c_observed_stage_parameter;
    unsigned short action0c_audio_slots[3];
    unsigned short action0c_audio_commands[3];
} AvspRound1Class1fInner8ProgramSpec;

typedef struct
{
    unsigned short x_max;
    unsigned short camera_relative_bias;
    unsigned short camera_relative_span;
    unsigned short release_state;
    unsigned char phase_guard_mask;
    unsigned short upper_lane;
    unsigned short lower_lane;
    unsigned char upper_directions[2];
    unsigned char lower_directions[2];
    unsigned short near_x_bias;
    unsigned short near_x_span;
    unsigned short near_z_bias;
    unsigned short near_z_span;
    unsigned char turn_selectors[2];
    unsigned char idle_selectors[2];
    unsigned char movement_selector_bases[2];
    long jump_z_velocity[4];
    long jump_y_velocity;
    long jump_y_acceleration;
    short jump_initial_y_add;
    long fall_y_delta;
    unsigned char fall_initial_selector;
    unsigned char fall_middle_selector;
    unsigned char jump_initial_selector;
    unsigned char jump_landing_selector;
    unsigned char jump_terminal_style;
    unsigned short action4_random_groups[
        AVSP_ROUND1_CLASS1F_ACTION4_RANDOM_GROUP_COUNT];
    unsigned short action4_group_first[
        AVSP_ROUND1_CLASS1F_ACTION4_GROUP_COUNT];
    unsigned char action4_group_count[
        AVSP_ROUND1_CLASS1F_ACTION4_GROUP_COUNT];
    unsigned short action4_selectors[
        AVSP_ROUND1_CLASS1F_ACTION4_SELECTOR_COUNT];
    unsigned char action4_stage_offsets[
        AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT];
    unsigned char action4_timer_rows[
        AVSP_ROUND1_CLASS1F_ACTION4_TIMER_ROW_COUNT]
        [AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT];
} AvspRound1Class1fActionProgramSpec;

typedef struct
{
    unsigned long attacker_table_set;
    unsigned long attack_record;
    unsigned long defender_table_set;
    unsigned long hurt_record;
    unsigned long defender_animation_record;
    unsigned long health_writer;
    unsigned short source_frame;
    unsigned char attack_selector;
    unsigned char hurt_selector;
    unsigned char damage;
    unsigned char hitstop;
    AvspRound1CollisionBoxSpec attack_box;
    AvspRound1CollisionBoxSpec hurt_box;
    unsigned long impact_source_slot;
    unsigned short impact_visible_frame;
    unsigned short impact_rng_seed_before;
    unsigned short impact_rng_seed_after;
    short impact_spawn_x;
    short impact_spawn_y;
    short impact_spawn_z;
    unsigned char impact_record_type;
    signed char impact_class;
    unsigned char impact_variant;
} AvspRound1Class1fPlayerCollisionSpec;

typedef struct
{
    unsigned long attacker_table_set;
    unsigned long attack_record;
    unsigned long defender_table_set;
    unsigned long hurt_record;
    unsigned long health_writer;
    unsigned long clamp_writer;
    unsigned long reaction_writer;
    unsigned long target_source_slot;
    unsigned short source_frame;
    unsigned short target_state;
    unsigned short target_substate;
    short health_before;
    short health_after_damage;
    short health_after_clamp;
    unsigned char attack_selector;
    unsigned char hurt_selector;
    unsigned char damage;
    unsigned char impact_variant;
    AvspRound1CollisionBoxSpec attack_box;
    AvspRound1CollisionBoxSpec hurt_box;
    unsigned long impact_source_slot;
    unsigned short impact_visible_frame;
    short impact_spawn_x;
    short impact_spawn_y;
    short impact_spawn_z;
    unsigned char impact_facing;
} AvspRound1PlayerSpecialTargetCollisionSpec;

typedef struct
{
    unsigned short initial_state;
    unsigned short wait_state;
    unsigned short current_state;
    unsigned short camera_edge_substate;
    unsigned short camera_edge_field46_threshold;
    unsigned short camera_edge_x;
    unsigned char camera_edge_uses_current_position;
    unsigned short spawn_timer_initial;
    unsigned short intro_timer_initial;
    unsigned short field46_initial;
    unsigned short field48_initial;
    unsigned short source_camera_bound_initial;
    unsigned short source_camera_target_current;
    short source_camera_call_threshold;
    unsigned short spawn_index_initial;
    unsigned short limit_table[AVSP_ROUND1_RECURRING_LIMIT_COUNT];
    unsigned char phase_initial;
    unsigned char maximum_living;
    unsigned char primary_phase_mask;
    unsigned char auxiliary_phase_add;
    unsigned char auxiliary_phase_mask;
    short primary_x_offset;
    short auxiliary_camera_x_limit;
    short auxiliary_x;
    short auxiliary_y;
    short auxiliary_z;
    unsigned char auxiliary_variant;
    unsigned char auxiliary_selector;
    unsigned char conditional_phase;
    unsigned char conditional_local;
    unsigned short intro_gate_owner_slot;
    signed char intro_gate_owner_class;
    unsigned char intro_gate_owner_type;
    unsigned short intro_gate_owner_state;
    unsigned short progress_ko_state;
    unsigned short progress_ko_substate;
    short progress_ko_health;
    unsigned short progress_increment;
    unsigned char preserve_reused_position_fraction;
    unsigned char preserve_reused_presentation;
} AvspRound1RecurringSpawnSpec;

typedef struct
{
    unsigned short phase_wait;
    unsigned short phase_camera;
    unsigned short phase_complete;
    unsigned short withdrawal_state;
    unsigned short progress_threshold;
    unsigned short field46_phase_threshold;
    unsigned short camera_phase_edge;
    unsigned short withdrawal_timer;
    unsigned short withdrawal_camera_edge;
    short route_withdrawal;
    short route_teardown;
    short route_next_entry;
    unsigned short teardown_countdown;
    unsigned short first_stall_frames;
    unsigned short second_stall_frames;
    unsigned short third_stall_frames;
    unsigned short teardown_visible_frame;
    unsigned short next_scene_substate2_visible_frame;
    unsigned short player_outer_state;
    unsigned long player_program_address;
    unsigned long terminal_cursor;
} AvspRound1CoffeeExitSpec;

typedef struct
{
    unsigned long cursor;
    unsigned long next_cursor;
    unsigned long animation_record;
    short x;
    short z;
    unsigned short ticks;
    unsigned char kind;
    unsigned char mode;
    unsigned char subhandler;
} AvspRound1CoffeeExitStepSpec;

typedef struct
{
    short x;
    short z;
} AvspRound1CoffeeExitMotionSpec;

typedef struct
{
    unsigned char program_tick;
    unsigned char display_ticks;
    unsigned char updates;
} AvspRound1CoffeeExitCallbackGroupSpec;

typedef struct
{
    long x_velocity;
    long x_acceleration;
    long y_velocity;
    long y_acceleration;
    unsigned char selector;
    unsigned char terminal_substate;
} AvspRound1CoffeeExitBallisticSpec;

typedef struct
{
    unsigned short first_source_frame;
    unsigned short last_source_frame;
    unsigned short input_mask;
} AvspRound1SceneInputRun;

typedef struct
{
    unsigned short source_frame;
    unsigned char updates;
} AvspRound1SceneUpdateCadence;

typedef struct
{
    unsigned long source_slot;
    short x;
    short y;
    short z;
    unsigned short state;
    unsigned short substate;
    unsigned char facing;
    unsigned long animation_record;
} AvspRound1Class09InitialSpec;

typedef struct
{
    unsigned long source_slot;
    short x;
    short y;
    short z;
} AvspRound1Class4eSpawnSpec;

typedef struct
{
    unsigned long source_slot;
    unsigned short seed_before;
    unsigned short seed_after;
    unsigned char table_index;
} AvspRound1Class4eRngSpec;

typedef struct
{
    unsigned long stage_record;
    unsigned long parent_source_slot;
    unsigned long pickup_source_slot;
    unsigned long parent_dispatch;
    unsigned long pickup_dispatch;
    unsigned long parent_attack_record;
    unsigned long parent_hurt_record;
    unsigned long player_hurt_record;
    unsigned long pickup_hurt_record;
    unsigned short stage_gate;
    unsigned short allocator_selector;
    unsigned short class_variant_word;
    short spawn_x;
    short spawn_y;
    short parent_initial_health;
    short parent_collision_damage;
    short parent_health_clamp;
    unsigned short parent_drop_state;
    unsigned short parent_drop_timer;
    unsigned short parent_audio_command;
    unsigned short pickup_subtype;
    unsigned short pickup_state;
    unsigned short pickup_motion_substate;
    unsigned short pickup_first_landing_substate;
    unsigned short pickup_second_landing_substate;
    unsigned short pickup_collected_state;
    short pickup_x;
    short pickup_y;
    short pickup_z;
    long pickup_x_velocity;
    long pickup_y_velocity;
    long pickup_y_acceleration;
    long pickup_first_landing_velocity;
    long pickup_first_landing_acceleration;
    unsigned short player_pickup_action;
    short health_amount;
    short health_cap;
    unsigned short player_audio_command;
    unsigned short rng_seed_before;
    unsigned short rng_seed_after;
    unsigned char parent_record_type;
    signed char parent_class;
    unsigned char pickup_record_type;
    signed char pickup_class;
    unsigned char parent_hurt_selector;
    unsigned char pickup_hurt_selector;
    unsigned char player_hurt_selector;
    unsigned char impact_variant;
    unsigned char damage_selector;
    unsigned char hit_value;
    unsigned char drop_rng_calls;
    unsigned char drop_mask;
    unsigned char drop_selector_source;
    unsigned char pickup_field5c;
    unsigned char pickup_field64;
    unsigned char drop_selector_row[32];
    AvspRound1CollisionBoxSpec parent_attack_box;
    AvspRound1CollisionBoxSpec parent_hurt_box;
    AvspRound1CollisionBoxSpec player_hurt_box;
    AvspRound1CollisionBoxSpec pickup_hurt_box;
} AvspRound1Class08HealthPickupSpec;

typedef struct
{
    unsigned short state;
    unsigned short alternate_landing_substate;
    unsigned short release_state;
    unsigned short release_substate;
    short ground;
    long primary_x_fp;
    long primary_y_fp;
    long primary_x_velocity;
    long primary_y_velocity;
    long primary_y_acceleration;
    long alternate_x_fp;
    long alternate_y_fp;
    long alternate_x_velocity;
    long alternate_y_velocity;
    long alternate_y_acceleration;
    long alternate_freeze_x_fp;
    long alternate_freeze_y_fp;
} AvspRound1Class08DebrisSpec;

typedef struct
{
    unsigned long dispatch;
    unsigned long table_set;
    unsigned long player_attack_record;
    unsigned long hurt_record;
    unsigned short active_state;
    unsigned short reaction_state;
    unsigned short reaction_wait_state;
    unsigned short debris_state;
    unsigned short alternate_landing_substate;
    unsigned short release_state;
    unsigned short release_substate;
    unsigned short reaction_timer;
    unsigned short audio_command;
    short damage;
    short health_clamp;
    signed char actor_class;
    unsigned char hurt_selector;
    unsigned char impact_variant;
    unsigned char field64;
    AvspRound1CollisionBoxSpec player_attack_box;
    AvspRound1CollisionBoxSpec hurt_box;
} AvspRound1Class05Spec;

typedef struct
{
    short primary_y_offset;
    long primary_x_velocity;
    long primary_y_velocity;
    long primary_x_acceleration;
    long primary_y_acceleration;
    long alternate_x_velocity;
    long alternate_y_velocity;
    long alternate_x_acceleration;
    long alternate_y_acceleration;
} AvspRound1Class05MotionSpec;

typedef struct
{
    unsigned long source_slot;
    short x;
    short y;
    short z;
    unsigned short state;
    unsigned short substate;
    unsigned long dispatch;
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned char facing;
    unsigned short object_or;
} AvspRound1Class44GuardSpec;

typedef struct
{
    short primary_x_velocity;
    short primary_y_velocity;
    short primary_y_acceleration;
    short alternate_x_velocity;
    short alternate_y_velocity;
    short alternate_y_acceleration;
} AvspRound1Class45MotionSpec;

typedef struct
{
    unsigned short attempts;
    short x_offset;
    short y_offset;
    short z_offset;
} AvspRound1Class45SpawnGroupSpec;

typedef struct
{
    long x_velocity;
    long x_acceleration;
    long y_velocity;
    long y_acceleration;
    long z_velocity;
} AvspRound1Type16MotionSpec;

typedef struct
{
    unsigned long dispatch;
    unsigned long spawn_routine;
    unsigned long allocator;
    unsigned long release_routine;
    unsigned long collision_table;
    unsigned long attack_record;
    unsigned long player_table;
    unsigned long player_hurt_record;
    short spawn_x_offset;
    short spawn_y_offset;
    unsigned short camera_bias;
    unsigned short camera_limit;
    short damage;
    unsigned char record_type;
    signed char actor_class;
    unsigned char attack_selector;
    unsigned char player_hurt_selector;
    unsigned char hit_value;
    AvspRound1CollisionBoxSpec attack_box;
    AvspRound1CollisionBoxSpec player_hurt_box;
} AvspRound1Type16Spec;

typedef struct
{
    signed char actor_class;
    unsigned char variant;
    unsigned char child_count;
    unsigned char rng_calls_per_actor;
    short y_offset;
    short z_offset;
    unsigned long dispatch;
} AvspRound1Class47Spec;

typedef struct
{
    unsigned long source_slot;
    long x_fp;
    long y_fp;
    long x_velocity;
    long y_velocity;
    long y_acceleration;
    unsigned char active;
} AvspRound1Class1fTransitionRuntime;

typedef struct
{
    unsigned char record_type;
    signed char actor_class;
} AvspRound1DispatchSpec;

typedef struct
{
    unsigned short a5_offset;
    unsigned long absolute_address;
    unsigned char width_bytes;
    unsigned char native_binding;
} AvspRound1SchedulerGlobalSpec;

typedef struct
{
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char hurt_selector;
    unsigned char attack_selector;
} AvspRound1PresentationSpec;

typedef struct
{
    unsigned short state;
    unsigned short substate;
} AvspRound1StateContextSpec;

typedef struct
{
    short bound_x;
    short bound_z;
    short x_min;
    short x_max;
    short z_min;
    short z_max;
} AvspRound1NavigationBoundsSpec;

typedef struct
{
    unsigned char kind;
    unsigned char branch_selector;
    unsigned char orientation;
    unsigned char shift;
    unsigned char x_parameter;
    unsigned char z_parameter;
    unsigned char retry_selector;
    unsigned char reserved;
} AvspRound1TerrainRecordSpec;

typedef struct
{
    unsigned short selector_index;
    unsigned char selector;
    unsigned char attribute;
} AvspRound1TerrainStreamWriteSpec;

typedef struct
{
    unsigned char run_length_minus_one;
    unsigned char selector;
} AvspRound1TerrainSelectorRunSpec;

typedef struct
{
    short camera_x_observed;
    short camera_z_observed;
    unsigned char camera_x_tile;
    unsigned char camera_z_tile;
    unsigned char direction;
    unsigned char phase_after;
    unsigned short first_write;
    unsigned short write_count;
} AvspRound1TerrainStreamTransactionSpec;

typedef struct
{
    unsigned long source_slot;
    signed char actor_class;
    unsigned char type;
    unsigned short state;
    unsigned short substate;
    short x;
    short y;
    short z;
    unsigned char facing;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char hurt_selector;
    unsigned char attack_selector;
    AvspRound1CollisionBoxSpec attack_box;
} AvspRound1ObstacleSpec;

#define AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS 4u
#define AVSP_ROUND1_OBSTACLE_CHILD_RECORD_MAX 8u
#define AVSP_ROUND1_OBSTACLE_PARENT_RECORD_COUNT 5u

typedef struct
{
    unsigned char record_count;
    AvspRound1AnimationStateSpec records[
        AVSP_ROUND1_OBSTACLE_CHILD_RECORD_MAX];
} AvspRound1ObstacleChildSequenceSpec;

typedef struct
{
    unsigned long scene_record;
    unsigned long source_slot;
    unsigned long dispatch_entry;
    unsigned long player_attack_record;
    unsigned short camera_threshold;
    short x;
    short y;
    short z;
    short initial_health;
    unsigned short active_state;
    unsigned short break_state;
    unsigned short break_timer_state;
    unsigned short physics_state;
    unsigned short release_state;
    unsigned short object_priority;
    unsigned char field64;
    unsigned char child_record_type;
    signed char child_class;
    unsigned char child_count;
    unsigned char child_variant_order[
        AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS];
    unsigned char break_timer;
    unsigned char damage;
    unsigned char special_edge_to_damage_ticks;
    unsigned char player_attack_hit_value;
    signed char player_attack_knockback;
    unsigned char break_rng_calls;
    unsigned short break_audio_command;
    AvspRound1CollisionBoxSpec player_attack_box;
    AvspRound1CollisionBoxSpec obstacle_hurt_box;
    short physics_fields[8];
} AvspRound1ObstacleLifecycleSpec;

typedef struct
{
    short initial_x;
    short initial_z;
    short initial_x_lower;
    short initial_x_upper;
    short initial_z_upper;
    short initial_z_lower;
    unsigned short x_spread;
    unsigned short z_spread;
    short x_wide_offset;
    short x_right_offset;
    short x_left_offset;
    short z_wide_offset;
    short z_upper_offset;
    short z_lower_offset;
    unsigned char guard_threshold_byte;
    unsigned short guard_countdown;
    unsigned short x_speed[AVSP_ROUND1_CAMERA_SPEED_COUNT];
} AvspRound1CameraSpec;

typedef struct
{
    unsigned short walking_action;
    unsigned short stop_action;
    unsigned short cleanup_action;
    unsigned short stop_ticks;
    long right_delta_s16_16;
    unsigned char current_hurt_selector;
    unsigned char current_attack_selector;
    unsigned char direction_resolver[16];
} AvspRound1PlayerLocomotionSpec;

typedef struct
{
    unsigned long outer_dispatch_entry;
    unsigned long entry_body;
    unsigned long active_body;
    unsigned long phase0_body;
    unsigned long phase2_body;
    unsigned long phase4_body;
    unsigned short control_outer_state;
    unsigned short hit_outer_state;
    unsigned short entry_substate;
    unsigned short shake_substate;
    unsigned short motion_substate;
    unsigned short return_substate;
    unsigned char shake_count;
    unsigned char motion_index;
    unsigned char invulnerability;
    unsigned char return_facing;
    unsigned short audio_command;
    unsigned char queue_special_input_during_hit;
    long x_velocity;
    long x_acceleration;
    AvspRound1AnimationStateSpec carried_record;
    AvspRound1AnimationStateSpec hit_record;
    AvspRound1AnimationStateSpec return_record;
    short shake_table[AVSP_ROUND1_PLAYER_HIT_SHAKE_COUNT];
} AvspRound1PlayerHitSpec;

typedef struct
{
    unsigned long attack_record;
    long x_velocity;
    long x_acceleration;
    AvspRound1AnimationStateSpec presentation;
    short damage;
    unsigned char source_record_type;
    signed char source_class;
    unsigned char source_attack_selector;
    unsigned char hit_kind;
    unsigned char presentation_selector;
    unsigned char active_body_selector;
    unsigned char shake_count;
    unsigned char motion_index;
} AvspRound1PlayerHitReactionSpec;

typedef struct
{
    unsigned short common_action;
    unsigned short target_context_action;
    unsigned short followup_ticks;
    unsigned short selector_count;
    unsigned char selectors[AVSP_ROUND1_PLAYER_MELEE_COUNT];
    unsigned char step_values[AVSP_ROUND1_PLAYER_MELEE_COUNT];
} AvspRound1PlayerMeleeSpec;

typedef struct
{
    unsigned char facing;
    unsigned char selector;
    unsigned char record_count;
    AvspRound1AnimationStateSpec records[
        AVSP_ROUND1_PLAYER_CONTEXTUAL_MELEE_MAX_RECORDS];
} AvspRound1PlayerContextualMeleeSequenceSpec;

typedef struct
{
    unsigned long target_link_clear_writer;
    unsigned long target_link_allocator;
    unsigned long target_to_player_writer;
    unsigned long player_to_target_writer;
    unsigned long entry_body;
    unsigned long active_body;
    unsigned long common_reset;
    unsigned long target_source_slot;
    unsigned short target_low;
    unsigned short target_state;
    unsigned short target_substate;
    unsigned short common_action;
    unsigned short entry_action;
    unsigned short active_action;
    unsigned short followup_ticks;
    unsigned short audio_commands[
        AVSP_ROUND1_PLAYER_CONTEXTUAL_MELEE_AUDIO_COUNT];
    unsigned char target_record_type;
    signed char target_class;
} AvspRound1PlayerContextualMeleeSpec;

typedef struct
{
    long x_velocity;
    long x_acceleration;
    long y_velocity;
    long y_acceleration;
} AvspRound1PlayerJumpVectorSpec;

typedef struct
{
    unsigned char selector;
    unsigned char record_count;
    AvspRound1AnimationStateSpec records[
        AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_MAX_RECORDS];
} AvspRound1PlayerJumpSequenceSpec;

typedef struct
{
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned short object_or;
} AvspRound1PlayerPresentationActorSpec;

typedef struct
{
    unsigned char physical_to_pipeline_updates;
    unsigned char pipeline_to_dispatch_updates;
    unsigned char dispatch_delay_counter;
    unsigned char same_facing_level_selector;
    unsigned char landing_selector;
    unsigned char preserve_landing_fraction;
    unsigned short neutral_timer;
    short neutral_branch;
} AvspRound1PlayerJumpTimingSpec;

typedef struct
{
    unsigned short action;
    unsigned short substate;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char hurt_selector;
    unsigned char attack_selector;
    unsigned short timer;
    short branch;
} AvspRound1PlayerWeaponFrameSpec;

typedef struct
{
    unsigned long helper_entry;
    unsigned long caller_delta_pc;
    unsigned long caller_call_pc;
    unsigned short guard_a5_offset;
    unsigned short stage_a5_offset;
    unsigned short upper_bound_a5_offset;
    unsigned short lower_bound_a5_offset;
    unsigned short progress_a5_offset;
    unsigned short delta;
    unsigned short threshold;
    unsigned short progress_mask;
    unsigned short stage_domain_limit;
    unsigned short stage_domain_mask;
    short lower_bound;
    short upper_bound;
    unsigned char action_entry_tick;
} AvspRound1PlayerStageProgressSpec;

typedef struct
{
    unsigned short sufficient_entry_action;
    unsigned short sufficient_active_action;
    unsigned short empty_entry_action;
    unsigned short empty_active_action;
    unsigned short cleanup_action;
    unsigned short return_action;
    unsigned char empty_timer_initial;
    unsigned char action_dispatch_delay_updates;
    unsigned char parent_allocation_tick;
    unsigned char resource_debit_tick;
    unsigned char resource_capacity;
    unsigned char resource_debit;
    unsigned char recharge_after_success;
    unsigned char normal_recharge_reload;
    unsigned char depleted_recharge_reload;
    unsigned char empty_dispatch_uses_depleted_latch;
    unsigned char sufficient_entry_preserves_current_presentation;
    unsigned char empty_entry_preserves_current_presentation;
    unsigned char empty_effect_variant;
    unsigned char empty_effect_allocation_tick;
    unsigned char empty_effect_preserve_position_residue;
    signed char parent_class;
    signed char child_class;
    unsigned short projectile_source_base;
    unsigned short projectile_stride;
    unsigned short player_owner;
    unsigned long parent_attack_table;
    unsigned long child_attack_table;
} AvspRound1PlayerWeaponSpec;

typedef struct
{
    unsigned long dispatch_entry;
    unsigned char record_type;
    signed char actor_class;
    unsigned char variant;
    unsigned char timer;
    unsigned char phase_mask;
    unsigned char phase_expected;
} AvspRound1PlayerWeaponEffectSpec;

typedef struct
{
    unsigned char active;
    signed char actor_class;
    unsigned char variant;
    unsigned char facing;
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned short source_slot;
    unsigned short owner;
    short x;
    short y;
    short z;
    unsigned long attack_table;
    unsigned char state;
    unsigned char substate;
    unsigned char angle;
    unsigned char damage_class_index;
    unsigned char attack_selector;
    unsigned short object_or;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char active_collision;
    unsigned char collision_registered;
    unsigned char collision_registration_pending;
    signed char collision_latch_index;
    unsigned char collision_identity;
    unsigned char owner_offset_selector;
    unsigned char parent_presentation_selector;
    unsigned char presentation_index;
    unsigned char presentation_count;
    unsigned char child_count;
    unsigned char child_cadence;
    unsigned char progress;
    unsigned char direction_timer;
    short health;
    unsigned short owner_field_26;
    unsigned short animation_timer;
    short animation_branch;
    short collision_result;
    long x_fp;
    long y_fp;
    long z_fp;
} AvspRound1WeaponProjectileAllocation;

typedef struct
{
    unsigned char record_type;
    signed char actor_class;
    unsigned short pool_slot;
    unsigned long source_slot;
} AvspRound1SchedulerVisit;

typedef struct
{
    unsigned long source_slot;
    unsigned char record_type;
    short x;
    short y;
    short z;
    unsigned char actor_class;
    unsigned char variant;
    unsigned short source_action;
    unsigned short state;
    unsigned short substate;
    unsigned char facing;
    unsigned long animation_record;
    short health;
} AvspRound1EntrySpawnSpec;

typedef struct
{
    unsigned char kind;
    unsigned char opcode;
    unsigned short arg0;
    unsigned short arg1;
    unsigned short arg2;
    unsigned long cursor;
    unsigned long next_cursor;
} AvspRound1EntryStepSpec;

typedef struct
{
    unsigned char record_type;
    unsigned char capacity;
    unsigned short stride;
    unsigned short source_base;
    unsigned char free_count;
    unsigned short free_stack[AVSP_ROUND1_MAX_POOL_CAPACITY];
    AvspRound1ActorCore records[AVSP_ROUND1_MAX_POOL_CAPACITY];
} AvspRound1Pool;

typedef struct
{
    unsigned char started;
    unsigned char dependencies_seeded;
    unsigned char spawned;
    unsigned char terminal_seen;
    unsigned char control_enabled;
    unsigned char step_index;
    unsigned char gate8236;
    unsigned char gate81af;
    unsigned char source_global_8209;
    unsigned char animation_c0;
    unsigned char animation_c1;
    unsigned char animation_c2;
    unsigned short animation_c8;
    unsigned short timer_decrements;
    unsigned short spawn_count;
    unsigned short source18_argument;
    unsigned long script_cursor;
    unsigned long exit_script_cursor;
    unsigned short exit_script_ticks;
    unsigned short exit_route_countdown;
    unsigned short exit_stall_remaining;
    unsigned char exit_started;
    unsigned char exit_script_step;
    unsigned char exit_script_mode;
    unsigned char exit_script_subhandler;
    unsigned char exit_route_phase;
    unsigned char exit_route_substate;
    unsigned char exit_load_index;
    unsigned char exit_complete;
    unsigned char exit_display_tick;
    unsigned long exit_script_updates;
    unsigned long exit_route_updates;
    unsigned long exit_pool_teardowns;
    unsigned long exit_load_events;
} AvspRound1EntryRuntime;

typedef struct
{
    AvspPortV2HitKoRuntime reaction;
    /* Read-only presentation cache; the fixed-pool actor remains authoritative. */
    AvspAlienView presentation;
    unsigned long actor_source_slot;
    unsigned short target_id;
    unsigned short approach_elapsed;
    unsigned short attack_elapsed;
    unsigned short attack_timer;
    unsigned short hit_timer;
    unsigned short ko_timer;
    unsigned short rng_seed;
    unsigned short rng_cursor;
    unsigned short presentation_index;
    unsigned short controller_timer;
    unsigned short source_spawn_timer;
    unsigned short source_intro_timer;
    unsigned short source_field46;
    unsigned short source_field48;
    unsigned short source_camera_bound;
    unsigned short source_camera_target;
    unsigned short source_spawn_limit;
    unsigned short source_spawn_index;
    unsigned short source_living_count;
    unsigned short source_progress;
    unsigned short source_progress_snapshot;
    unsigned short source_controller_updates;
    unsigned char controller_state;
    unsigned char controller_remaining;
    unsigned char source_phase_counter;
    unsigned char source_intro_gate;
    unsigned char source_phase;
    unsigned char source_local;
    unsigned char source_controller_initialized;
    unsigned char source_initial_spawn_complete;
    unsigned char source_current_enabled;
    unsigned char source_blocked_by_living_count;
    long x_numerator;
    long lane_numerator;
    unsigned char initialized;
    unsigned char dynamic_spawned;
    unsigned char encounter_state;
    unsigned char target_ko_observed;
    unsigned char route_unlocked;
    unsigned char continued_after_unlock;
    unsigned char attack_latched;
    unsigned char pending_player_damage;
    unsigned char pending_player_damage_health_applied;
    unsigned char player_contact;
    unsigned char alien_contact;
    unsigned char player_damage;
    unsigned char alien_damage;
    unsigned char semantic_hit;
    unsigned char semantic_ko;
    short health_before;
    short health_after;
    short unlock_player_x;
    unsigned long scheduler_updates;
    unsigned long player_contacts;
    unsigned long alien_contacts;
    unsigned long player_damage_events;
    unsigned long alien_damage_events;
    unsigned long hit_events;
    unsigned long ko_events;
    unsigned long lifecycle_releases;
    unsigned long clear_events;
} AvspRound1FirstEncounterRuntime;

typedef struct
{
    AvspAlienView alien;
    AvspPortV2HitKoActorState reaction;
    unsigned char initialized;
    unsigned char encounter_state;
    unsigned char route_unlocked;
    unsigned char continued_after_unlock;
    unsigned char player_contact;
    unsigned char alien_contact;
    unsigned char player_damage;
    unsigned char alien_damage;
    unsigned char semantic_hit;
    unsigned char semantic_ko;
    short health_before;
    short health_after;
} AvspRound1FirstEncounterView;

typedef struct
{
    unsigned long head_canary;
    short route_state;
    unsigned short rng_seed;
    unsigned char collision_identity_counter;
    AvspRound1ActorCore player;
    AvspPwRuntime player_action;
    AvspRound1ActorCore entry_controller;
    AvspRound1EntryRuntime entry;
    AvspRound1Pool pools[AVSP_ROUND1_POOL_COUNT];
    unsigned long frame;
    unsigned long player_controller_updates;
    AvspRound1SchedulerVisit scheduler_trace[
        AVSP_ROUND1_SCHEDULER_TRACE_CAPACITY];
    unsigned short scheduler_trace_count;
    unsigned long scheduler_frames;
    unsigned long scheduler_dispatches;
    unsigned long scheduler_order_hash;
    unsigned long actor_handler_dispatches;
    unsigned long presentation_bindings;
    unsigned long state_context_bindings;
    AvspRound1Class1fTransitionRuntime class1f_transition[
        AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT];
    unsigned char class1f_effect_guard;
    unsigned char class1f_phase_guard_counter;
    unsigned short class1f_audio_command;
    unsigned long class1f_initializations;
    unsigned long class1f_initial_rng_calls;
    unsigned long class1f_transition_updates;
    unsigned long class1f_transition_completions;
    unsigned long class1f_effect_requests;
    unsigned long class1f_effect_allocations;
    unsigned long class1f_effect_allocation_failures;
    unsigned long class1f_audio_events;
    unsigned long class1f_action_initializations;
    unsigned long class1f_action_dispatches;
    unsigned long class1f_action_animation_steps;
    unsigned long class1f_action_movement_steps;
    unsigned long class1f_action_releases;
    unsigned long class1f_action0c_entries;
    unsigned long class1f_action0c_plan_bindings;
    unsigned long class1f_action0c_timer_rng_calls;
    unsigned long class1f_player_collision_writes;
    unsigned long class1f_player_damage_writes;
    unsigned long class1f_hitstop_updates;
    unsigned short source_stage_parameter;
    unsigned short source_stage_progress_accumulator;
    unsigned char source_stage_progress_guard;
    unsigned long player_stage_progress_calls;
    unsigned long player_stage_progress_carries;
    unsigned short source_global_hit_pause;
    unsigned short player_variant;
    unsigned char source_stage_record_type;
    unsigned char coffee_stage_setup_complete;
    unsigned long coffee_stage_setup_calls;
    unsigned long class1f_action4_rng_calls;
    unsigned long class1f_action4_timer_rng_calls;
    unsigned long class1f_action0e_rng_calls;
    unsigned char class1f_inner8_group_population[4];
    AvspRound1FirstEncounterRuntime first_encounter;
    unsigned long class09_initializations;
    unsigned long class09_rng_calls;
    unsigned long class4e_initializations;
    unsigned long class4e_rng_calls;
    unsigned long class4e_releases;
    unsigned char class4e_impact_suppressed;
    unsigned long class4e_variant1_allocation_requests;
    unsigned long class4e_variant1_allocations;
    unsigned long class4e_variant1_allocation_failures;
    unsigned long class4e_variant1_initializations;
    unsigned long class4e_variant1_releases;
    unsigned long class4e_variant10_allocation_requests;
    unsigned long class4e_variant10_allocations;
    unsigned long class4e_variant10_allocation_failures;
    unsigned long class4e_variant10_initializations;
    unsigned long class4e_variant10_releases;
    unsigned long class44_guard_updates;
    unsigned long class44_guard_clears;
    unsigned long class43_spawn_requests;
    unsigned long class43_allocations;
    unsigned long class43_allocation_failures;
    unsigned long class43_initializations;
    unsigned long class43_rng_calls;
    unsigned long class43_state_transitions;
    unsigned long class43_releases;
    unsigned long class45_spawn_attempts;
    unsigned long class45_allocations;
    unsigned long class45_initializations;
    unsigned long class45_rng_calls;
    unsigned long class45_state_transitions;
    unsigned long class45_releases;
    unsigned char coffee_scene_record_cursor;
    unsigned char coffee_scene_active_flag;
    unsigned long coffee_scene_spawn_attempts;
    unsigned long coffee_scene_spawns;
    unsigned long class01_initializations;
    unsigned long class01_spawn_requests;
    unsigned long class01_spawn_allocations;
    unsigned long class01_spawn_allocation_failures;
    unsigned long class01_effect_requests;
    unsigned long class01_audio_events;
    unsigned short class01_audio_command;
    unsigned long class01_state_transitions;
    unsigned long class01_releases;
    unsigned long class02_initializations;
    unsigned long class02_collision_tests;
    unsigned long class02_damage_writes;
    unsigned long class02_effect_requests;
    unsigned long class02_audio_events;
    unsigned short class02_audio_command;
    unsigned long coffee_shop_obstacle_rng_calls;
    unsigned long coffee_shop_obstacle_audio_events;
    unsigned short coffee_shop_obstacle_audio_command;
    unsigned long class02_state_transitions;
    unsigned long class02_releases;
    unsigned char class08_parent_spawned;
    unsigned char class08_parent_released;
    unsigned char health_pickup_spawned;
    unsigned char health_pickup_collected;
    unsigned char player_pickup_pending;
    unsigned char player_pickup_active;
    unsigned char player_pickup_animation_index;
    unsigned short player_pickup_animation_timer;
    short player_pickup_animation_branch;
    unsigned long class08_parent_spawn_attempts;
    unsigned long class08_parent_spawns;
    unsigned long class08_parent_initializations;
    unsigned long class08_parent_collision_writes;
    unsigned long class08_parent_damage_writes;
    unsigned long class08_parent_rng_calls;
    unsigned long class08_parent_audio_events;
    unsigned short class08_parent_audio_command;
    unsigned long class08_parent_state_transitions;
    unsigned long class08_parent_releases;
    unsigned long health_pickup_allocations;
    unsigned long health_pickup_initializations;
    unsigned long health_pickup_state_transitions;
    unsigned long health_pickup_collections;
    unsigned long health_pickup_releases;
    unsigned long player_pickup_audio_events;
    unsigned short player_pickup_audio_command;
    unsigned long class47_spawn_requests;
    unsigned long class47_allocations;
    unsigned long class47_allocation_failures;
    unsigned long class47_initializations;
    unsigned long class47_rng_calls;
    unsigned long class47_state_transitions;
    unsigned long class47_releases;
    unsigned char navigation_bounds_active;
    short navigation_bound_x;
    short navigation_bound_z;
    unsigned long navigation_applications;
    unsigned long navigation_clamps;
    unsigned long navigation_obstacle_tests;
    unsigned long navigation_obstacle_responses;
    unsigned char coffee_shop_obstacle_spawned;
    unsigned char coffee_shop_obstacle_released;
    unsigned long coffee_shop_obstacle_spawn_attempts;
    unsigned long coffee_shop_obstacle_spawns;
    unsigned long coffee_shop_obstacle_child_allocations;
    unsigned long coffee_shop_obstacle_damage_events;
    unsigned long coffee_shop_obstacle_state_transitions;
    unsigned long coffee_shop_obstacle_releases;
    unsigned long coffee_shop_obstacle_child_updates;
    unsigned long coffee_shop_obstacle_child_releases;
    unsigned char player_special_attack_active;
    unsigned char player_special_attack_previous_pressed;
    unsigned char player_special_attack_contact_ready;
    unsigned char player_special_attack_elapsed;
    unsigned char player_special_cleanup_pending;
    unsigned char player_special_input_pipeline;
    unsigned char player_special_previous_buttons;
    unsigned char player_special_animation_index;
    unsigned char player_special_class4b_event_latch;
    unsigned char player_special_owner_contact;
    unsigned short player_special_phase;
    unsigned short player_special_animation_timer;
    short player_special_animation_branch;
    unsigned short player_special_class4b_source_slot;
    unsigned long player_special_attack_entries;
    unsigned long player_special_attack_contacts;
    unsigned long player_special_class1f_collision_tests;
    unsigned long player_special_class1f_damage_writes;
    unsigned long player_special_record20_damage_writes;
    unsigned long player_special_completions;
    unsigned long player_special_health_debits;
    unsigned long player_special_audio_events;
    unsigned short player_special_audio_command;
    unsigned long class4b_allocation_requests;
    unsigned long class4b_allocations;
    unsigned long class4b_allocation_failures;
    unsigned long class4b_initializations;
    unsigned long class4b_releases;
    unsigned long class3d_allocation_requests;
    unsigned long class3d_allocations;
    unsigned long class3d_allocation_failures;
    unsigned long class3d_initializations;
    unsigned long class3d_releases;
    unsigned long navigation_terrain_tests;
    unsigned long navigation_terrain_responses;
    unsigned long navigation_terrain_retries;
    unsigned long class1f_terrain_tests;
    unsigned long class1f_terrain_responses;
    unsigned long class1f_terrain_retries;
    unsigned char terrain_selector_map[
        AVSP_ROUND1_TERRAIN_SELECTOR_MAP_COUNT];
    unsigned char terrain_stream_phase_x;
    unsigned char terrain_stream_initialized;
    unsigned short terrain_stream_last_transaction;
    unsigned long terrain_stream_transactions;
    unsigned long terrain_stream_writes;
    unsigned long terrain_stream_failures;
    unsigned char navigation_contact_bits;
    short camera_x_previous;
    short camera_x_position;
    short camera_z_previous;
    short camera_z_position;
    short camera_x_target;
    short camera_z_target;
    short camera_x_target_previous;
    short camera_z_target_previous;
    short camera_z_upper;
    short camera_z_lower;
    short camera_x_lower;
    short camera_x_upper;
    short camera_scroll2_x;
    unsigned char camera_coffee_phase;
    unsigned short camera_guard_counter;
    unsigned short camera_guard_snapshot;
    unsigned short camera_guard_countdown;
    unsigned long camera_updates;
    unsigned long camera_locks;
    unsigned long camera_unlocks;
    unsigned char player_hit_active;
    unsigned char player_hit_phase;
    unsigned char player_hit_shake_remaining;
    unsigned char player_hit_shake_index;
    unsigned char player_hit_reaction_side;
    unsigned char player_hit_invulnerability;
    unsigned char player_hit_audio_latched;
    unsigned char player_hit_reaction_index;
    unsigned char player_hit_kind;
    unsigned char player_hit_presentation_selector;
    unsigned char player_hit_active_body_selector;
    unsigned char player_hit_special_pending;
    unsigned short player_hit_animation_timer;
    short player_hit_animation_branch;
    long player_hit_x_fp;
    long player_hit_x_velocity;
    long player_hit_x_acceleration;
    unsigned long player_hit_entries;
    unsigned long player_hit_shake_updates;
    unsigned long player_hit_motion_updates;
    unsigned long player_hit_phase_transitions;
    unsigned long player_hit_completions;
    unsigned long player_hit_audio_events;
    unsigned short player_hit_audio_command;
    unsigned short player_locomotion_action;
    unsigned short player_stop_ticks;
    unsigned char player_was_directional;
    unsigned char player_cleanup_pending;
    unsigned char player_walk_animation_index;
    unsigned char player_walk_animation_active;
    unsigned short player_walk_animation_timer;
    unsigned long player_stop_entries;
    unsigned long player_stop_completions;
    unsigned long player_stop_motion_suppressions;
    unsigned long player_melee_entries;
    unsigned long player_melee_completions;
    unsigned long player_melee_selector_mask;
    unsigned long player_melee_presentation_mask;
    unsigned long player_melee_interruptions;
    unsigned char player_contextual_melee_active;
    unsigned char player_contextual_melee_dispatch_delay;
    unsigned char player_contextual_melee_sequence;
    unsigned char player_contextual_melee_animation_index;
    unsigned char player_contextual_melee_step81;
    unsigned char player_contextual_melee_toggle87;
    unsigned short player_contextual_melee_animation_timer;
    short player_contextual_melee_animation_branch;
    unsigned long player_contextual_melee_entries;
    unsigned long player_contextual_melee_completions;
    unsigned long player_contextual_melee_interruptions;
    unsigned long player_contextual_melee_presentation_mask;
    unsigned long player_contextual_melee_audio_events;
    unsigned short player_contextual_melee_audio_command;
    unsigned char player_jump_active;
    unsigned char player_jump_cleanup_pending;
    unsigned char player_jump_dispatch_delay;
    unsigned char player_jump_previous_pressed;
    unsigned char player_jump_direction_class;
    unsigned char player_jump_collision_selector;
    unsigned char player_jump_presentation_selector;
    unsigned char player_jump_animation_index;
    unsigned char player_jump_airborne_latch;
    unsigned short player_jump_phase;
    unsigned short player_jump_phase_timer;
    unsigned short player_jump_animation_timer;
    short player_jump_animation_branch;
    long player_jump_x_fp;
    long player_jump_y_fp;
    long player_jump_x_velocity;
    long player_jump_y_velocity;
    long player_jump_x_acceleration;
    long player_jump_y_acceleration;
    unsigned long player_jump_entries;
    unsigned long player_jump_completions;
    unsigned long player_jump_landings;
    unsigned long player_jump_interruptions;
    unsigned long player_jump_motion_updates;
    unsigned long player_jump_presentation_bindings;
    unsigned char player_weapon_active;
    unsigned char player_weapon_empty;
    unsigned char player_weapon_tick;
    unsigned char player_weapon_dispatch_delay;
    unsigned char player_weapon_presentation_selector;
    unsigned char player_weapon_target_angle;
    unsigned char player_weapon_empty_timer;
    unsigned char player_weapon_input_pipeline;
    unsigned char player_weapon_previous_pressed;
    unsigned char player_weapon_cleanup_pending;
    unsigned char player_weapon_return_pending;
    unsigned char player_weapon_recovery_pending;
    unsigned char player_resource;
    unsigned char player_resource_recharge;
    unsigned char player_resource_depleted;
    unsigned char player_weapon_projectile_free_count;
    unsigned char player_weapon_projectile_free_stack[
        AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY];
    AvspRound1WeaponProjectileAllocation player_weapon_projectiles[
        AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY];
    unsigned long player_weapon_entries;
    unsigned long player_weapon_completions;
    unsigned long player_weapon_attempts_total;
    unsigned long player_weapon_allocations;
    unsigned long player_weapon_allocation_failures;
    unsigned long player_weapon_resource_debits;
    unsigned long player_weapon_held_suppressions;
    unsigned long player_weapon_motion_suppressions;
    unsigned long player_weapon_interruptions;
    unsigned long player_weapon_presentation_bindings;
    unsigned long player_weapon_empty_auxiliary_requests;
    unsigned long player_weapon_empty_auxiliary_allocations;
    unsigned long player_weapon_empty_auxiliary_allocation_failures;
    unsigned long player_weapon_empty_auxiliary_releases;
    unsigned long player_weapon_empty_auxiliary_presentation_bindings;
    unsigned long player_weapon_projectile_initializations;
    unsigned long player_weapon_projectile_scheduler_updates;
    unsigned long type16_spawn_requests;
    unsigned long type16_allocations;
    unsigned long type16_movement_steps;
    unsigned long type16_collision_writes;
    unsigned long type16_damage_writes;
    unsigned long type16_releases;
    unsigned long player_weapon_projectile_motion_updates;
    unsigned long player_weapon_projectile_collision_writes;
    unsigned long player_weapon_projectile_damage_writes;
    unsigned long player_weapon_projectile_releases;
    short player_air_weapon_effect_x_delta;
    unsigned long player_air_weapon_entries;
    unsigned long player_air_weapon_allocations;
    unsigned long player_air_weapon_allocation_failures;
    unsigned long player_air_weapon_direction_steps;
    unsigned long player_air_weapon_motion_updates;
    unsigned long player_air_weapon_effect_requests;
    unsigned long player_air_weapon_effect_allocations;
    unsigned long player_air_weapon_effect_allocation_failures;
    unsigned long player_air_weapon_effect_releases;
    unsigned long player_weapon_parent_effect_requests;
    unsigned long player_weapon_parent_effect_allocations;
    unsigned long player_weapon_parent_effect_allocation_failures;
    unsigned long player_weapon_parent_effect_releases;
    unsigned long player_weapon_impact_requests;
    unsigned long player_weapon_impact_allocations;
    unsigned long player_weapon_impact_allocation_failures;
    unsigned long player_weapon_impact_releases;
    unsigned long player_weapon_impact_presentation_bindings;
    unsigned long player_weapon_impact_audio_events;
    unsigned short player_weapon_impact_audio_command;
    unsigned char player_weapon_impact_audio_selector;
    unsigned long player_resource_recharges;
    unsigned long class05_initializations;
    unsigned long class05_collision_tests;
    unsigned long class05_collision_writes;
    unsigned long class05_damage_writes;
    unsigned long class05_rng_calls;
    unsigned long class05_audio_events;
    unsigned short class05_audio_command;
    unsigned long class05_state_transitions;
    unsigned long class05_releases;
    unsigned short scheduler_failure_code;
    unsigned short scheduler_failure_source_slot;
    unsigned short scheduler_failure_state;
    unsigned short scheduler_failure_substate;
    unsigned long scheduler_failure_animation_record;
    unsigned long failure_count;
    unsigned long fallback_count;
    unsigned long tail_canary;
} AvspRound1Runtime;

void avsp_round1_init(AvspRound1Runtime *runtime);
int avsp_round1_bind_content_archive(const void *data,
                                     unsigned long bytes);
int avsp_round1_begin_first_entry(AvspRound1Runtime *runtime);
int avsp_round1_step_first_entry(AvspRound1Runtime *runtime);
int avsp_round1_step_coffee_exit_display(AvspRound1Runtime *runtime);
int avsp_round1_step_player(AvspRound1Runtime *runtime,
                            unsigned short input_mask,
                            short received_damage);
int avsp_round1_step_scheduler(AvspRound1Runtime *runtime);
int avsp_round1_step_scheduler_pre_player_source_differential(
    AvspRound1Runtime *runtime, int include_default);
int avsp_round1_step_scheduler_post_player_source_differential(
    AvspRound1Runtime *runtime, int include_default, int include_class02);
int avsp_round1_step_scheduler_source_differential(
    AvspRound1Runtime *runtime, int include_default, int include_class02);
void avsp_round1_first_encounter_view(
    const AvspRound1Runtime *runtime,
    AvspRound1FirstEncounterView *view);
int avsp_round1_is_weapon_impact_actor(const AvspRound1ActorCore *actor);
int avsp_round1_is_weapon_parent_projectile(
    const AvspRound1WeaponProjectileAllocation *projectile);
int avsp_round1_is_weapon_child_projectile(
    const AvspRound1WeaponProjectileAllocation *projectile);
unsigned long avsp_round1_weapon_current_attack_record(
    const AvspRound1WeaponProjectileAllocation *projectile);
int avsp_round1_player_native_presentation_active(
    const AvspRound1Runtime *runtime);
unsigned short avsp_round1_coffee_shop_source_input(
    unsigned short source_frame);
unsigned int avsp_round1_coffee_shop_source_updates(
    unsigned short source_frame);
unsigned int avsp_round1_coffee_shop_class02_source_updates(
    unsigned short source_frame);
int avsp_round1_entry_valid(const AvspRound1Runtime *runtime);
int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime);

#endif
