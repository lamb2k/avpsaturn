#ifndef AVSP_PORT_V2_ROUND1_H
#define AVSP_PORT_V2_ROUND1_H

#include "../player_action/player_action.h"
#include "../street_alien_ai/street_alien_ai.h"
#include "../../combat/hit_ko/hit_ko.h"

#define AVSP_ROUND1_SPEC02_SHA256 \
    "b1613ab1bbd777abbcbeae7c5521463171c5cc1ad4b12367248a436acbb563af"
#define AVSP_ROUND1_CANARY_HEAD 0x52314548UL
#define AVSP_ROUND1_CANARY_TAIL 0x52314554UL
#define AVSP_ROUND1_ROUTE_ENTRY_STATE 2
#define AVSP_ROUND1_INITIAL_RNG 0x8DEFu
#define AVSP_ROUND1_PLAYER_HEALTH 101
#define AVSP_ROUND1_POOL_COUNT 4
#define AVSP_ROUND1_MAX_POOL_CAPACITY 32
#define AVSP_ROUND1_FIRST_SPAWN_COUNT 10
#define AVSP_ROUND1_ENTRY_PROGRAM_BYTES 26
#define AVSP_ROUND1_ENTRY_STEP_COUNT 8
#define AVSP_ROUND1_SCHEDULER_POOL_COUNT 4
#define AVSP_ROUND1_REQUIRED_DISPATCH_COUNT 16
#define AVSP_ROUND1_SCHEDULER_TRACE_CAPACITY 78
#define AVSP_ROUND1_PLAYER_ENTRY_STATE 2048u
#define AVSP_ROUND1_PLAYER_CONTROL_STATE 512u
#define AVSP_ROUND1_PLAYER_MELEE_COUNT 4u
#define AVSP_ROUND1_PLAYER_JUMP_VECTOR_COUNT 6u
#define AVSP_ROUND1_PLAYER_JUMP_DOWN_VECTOR_COUNT 2u
#define AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_COUNT 9u
#define AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_MAX_RECORDS 8u
#define AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT 20u
#define AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT 18u
#define AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY 24u
#define AVSP_ROUND1_WEAPON_PARENT_PRESENTATION_COUNT 7u
#define AVSP_ROUND1_WEAPON_PARENT_SELECTOR_COUNT 6u
#define AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT 3u
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
#define AVSP_ROUND1_CLASS1F_ATTACK_TIMER_COUNT 16u
#define AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT 2u
#define AVSP_ROUND1_CLASS09_SEQUENCE_COUNT 5u
#define AVSP_ROUND1_CLASS09_SEQUENCE_RECORDS 2u
#define AVSP_ROUND1_CLASS4E_JITTER_COUNT 8u
#define AVSP_ROUND1_CLASS4E_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_CLASS44_PRESENTATION_COUNT 2u
#define AVSP_ROUND1_TERRAIN_RECORD_COUNT 7u
#define AVSP_ROUND1_TERRAIN_GRID_X_MIN 640
#define AVSP_ROUND1_TERRAIN_GRID_X_MAX 1360
#define AVSP_ROUND1_TERRAIN_GRID_Z_MIN 272
#define AVSP_ROUND1_TERRAIN_GRID_Z_MAX 400
#define AVSP_ROUND1_TERRAIN_GRID_TILE_SIZE 16u
#define AVSP_ROUND1_TERRAIN_GRID_WIDTH 46u
#define AVSP_ROUND1_TERRAIN_GRID_HEIGHT 9u
#define AVSP_ROUND1_TERRAIN_GRID_CELL_COUNT 414u
#define AVSP_ROUND1_TERRAIN_PACKED_BYTES 104u
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
    unsigned char parent_damage;
    unsigned char child_damage;
} AvspRound1WeaponProjectileSpec;

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
    long source_x_velocity;
    long source_y_velocity;
    long source_y_acceleration;
    unsigned short source_target_low;
    unsigned short source_bound_b2;
    unsigned char source_direction;
    unsigned char source_action_timer;
    unsigned char source_a3;
    unsigned char source_a4;
    unsigned char source_a5;
    unsigned char source_a6;
    unsigned char source_style85;
    unsigned char source_airborne;
    unsigned char source_b0;
    unsigned char source_action_group;
    unsigned char source_action_group_cursor;
    unsigned char source_player_guard;
    unsigned char source_action_initialized;
    unsigned char source_movement_table;
    unsigned long source_next_animation_record;
    unsigned long dispatch_entry;
    unsigned long scheduler_updates;
    unsigned long handler_updates;
    unsigned long state_handler_updates;
} AvspRound1ActorCore;

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
    unsigned short x_max;
    unsigned short camera_relative_bias;
    unsigned short camera_relative_span;
    unsigned short release_state;
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
    long jump_x_velocity[4];
    long jump_y_velocity;
    long jump_y_acceleration;
    short jump_initial_y_add;
    long fall_y_delta;
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
    unsigned short initial_state;
    unsigned short wait_state;
    unsigned short current_state;
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
} AvspRound1RecurringSpawnSpec;

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
    unsigned char direction_resolver[16];
} AvspRound1PlayerLocomotionSpec;

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
    unsigned short action;
    unsigned short substate;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char hurt_selector;
    unsigned char attack_selector;
} AvspRound1PlayerWeaponFrameSpec;

typedef struct
{
    unsigned short sufficient_entry_action;
    unsigned short sufficient_active_action;
    unsigned short empty_entry_action;
    unsigned short empty_active_action;
    unsigned short cleanup_action;
    unsigned short return_action;
    unsigned char empty_timer_initial;
    unsigned char resource_capacity;
    unsigned char resource_debit;
    unsigned char recharge_after_success;
    unsigned char normal_recharge_reload;
    unsigned char depleted_recharge_reload;
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
    unsigned short source_stage_parameter;
    unsigned long class1f_action4_rng_calls;
    unsigned long class1f_action4_timer_rng_calls;
    AvspRound1FirstEncounterRuntime first_encounter;
    unsigned long class09_initializations;
    unsigned long class09_rng_calls;
    unsigned long class4e_initializations;
    unsigned long class4e_rng_calls;
    unsigned long class4e_releases;
    unsigned long class44_guard_updates;
    unsigned long class44_guard_clears;
    unsigned char navigation_bounds_active;
    short navigation_bound_x;
    short navigation_bound_z;
    unsigned long navigation_applications;
    unsigned long navigation_clamps;
    unsigned long navigation_obstacle_tests;
    unsigned long navigation_obstacle_responses;
    unsigned long navigation_terrain_tests;
    unsigned long navigation_terrain_responses;
    unsigned long navigation_terrain_retries;
    unsigned char navigation_contact_bits;
    short camera_x_previous;
    short camera_x_position;
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
    unsigned short player_locomotion_action;
    unsigned short player_stop_ticks;
    unsigned char player_was_directional;
    unsigned char player_cleanup_pending;
    unsigned long player_stop_entries;
    unsigned long player_stop_completions;
    unsigned long player_stop_motion_suppressions;
    unsigned long player_melee_entries;
    unsigned long player_melee_completions;
    unsigned long player_melee_selector_mask;
    unsigned long player_melee_presentation_mask;
    unsigned long player_melee_interruptions;
    unsigned char player_jump_active;
    unsigned char player_jump_cleanup_pending;
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
    unsigned char player_weapon_cadence;
    signed char player_weapon_attempts;
    unsigned char player_weapon_empty_timer;
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
    unsigned long player_weapon_impact_requests;
    unsigned long player_weapon_impact_allocations;
    unsigned long player_weapon_impact_allocation_failures;
    unsigned long player_weapon_impact_releases;
    unsigned long player_weapon_impact_presentation_bindings;
    unsigned long player_weapon_impact_audio_events;
    unsigned short player_weapon_impact_audio_command;
    unsigned char player_weapon_impact_audio_selector;
    unsigned long player_resource_recharges;
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
int avsp_round1_begin_first_entry(AvspRound1Runtime *runtime);
int avsp_round1_step_first_entry(AvspRound1Runtime *runtime);
int avsp_round1_step_player(AvspRound1Runtime *runtime,
                            unsigned short input_mask,
                            short received_damage);
int avsp_round1_step_scheduler(AvspRound1Runtime *runtime);
void avsp_round1_first_encounter_view(
    const AvspRound1Runtime *runtime,
    AvspRound1FirstEncounterView *view);
int avsp_round1_is_weapon_impact_actor(const AvspRound1ActorCore *actor);
int avsp_round1_is_weapon_parent_projectile(
    const AvspRound1WeaponProjectileAllocation *projectile);
int avsp_round1_is_weapon_child_projectile(
    const AvspRound1WeaponProjectileAllocation *projectile);
int avsp_round1_player_native_presentation_active(
    const AvspRound1Runtime *runtime);
int avsp_round1_entry_valid(const AvspRound1Runtime *runtime);
int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime);

#endif
