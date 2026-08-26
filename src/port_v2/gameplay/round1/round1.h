#ifndef AVSP_PORT_V2_ROUND1_H
#define AVSP_PORT_V2_ROUND1_H

#include "../player_action/player_action.h"

#define AVSP_ROUND1_SPEC02_SHA256 \
    "5700f7c21d7820f0272f788b8177227de9a8047025817771efeed12cb421fe47"
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
#define AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT 50u
#define AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT 18u
#define AVSP_ROUND1_WEAPON_PROJECTILE_CAPACITY 24u
#define AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT 16u
#define AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT 12u
#define AVSP_ROUND1_WEAPON_PROJECTILE_MOTION_COUNT 64u
#define AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT 3u
#define AVSP_ROUND1_WEAPON_IMPACT_VARIANT_COUNT 5u
#define AVSP_ROUND1_WEAPON_IMPACT_PRESENTATION_COUNT 5u
#define AVSP_ROUND1_WEAPON_IMPACT_AUDIO_COMMAND_COUNT 2u
#define AVSP_ROUND1_WEAPON_DAMAGE_OFFENSE_COUNT 2u
#define AVSP_ROUND1_WEAPON_DAMAGE_DEFENSE_COUNT 1u
#define AVSP_ROUND1_WEAPON_DAMAGE_MATRIX_COUNT 2u
#define AVSP_ROUND1_EMPTY_EFFECT_VARIANT_COUNT 4u
#define AVSP_ROUND1_EMPTY_EFFECT_PRESENTATION_COUNT 10u
#define AVSP_ROUND1_INPUT_BUTTON1 0x0010u

#define AVSP_ROUND1_ENTRY_SET_POSITION 1u
#define AVSP_ROUND1_ENTRY_SET_SUBHANDLER 2u
#define AVSP_ROUND1_ENTRY_SOURCE_18 3u
#define AVSP_ROUND1_ENTRY_DWELL 4u
#define AVSP_ROUND1_ENTRY_SOURCE_16 5u
#define AVSP_ROUND1_ENTRY_TERMINATE 6u

typedef struct
{
    short x;
    short y;
} AvspRound1VecS16;

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
    unsigned char impact_state;
    unsigned char release_state;
    unsigned char target_pointer_high;
    short x_bound_bias;
    unsigned short x_bound_span;
    short y_bound_bias;
    unsigned short y_bound_span;
    signed char impact_class;
    unsigned char impact_variant;
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned short object_or;
} AvspRound1WeaponProjectileSpec;

typedef struct
{
    unsigned char record_type;
    signed char actor_class;
    unsigned char variant;
    unsigned char initial_state;
    unsigned char active_state;
    unsigned char release_state;
    unsigned long dispatch;
    unsigned char coordinate_mode;
    unsigned char palette;
    unsigned short object_or;
    unsigned short audio_commands[AVSP_ROUND1_WEAPON_IMPACT_AUDIO_COMMAND_COUNT];
} AvspRound1WeaponImpactSpec;

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
    unsigned char animation_index;
    unsigned short animation_timer;
    short animation_branch;
    unsigned long dispatch_entry;
    unsigned long scheduler_updates;
    unsigned long handler_updates;
    unsigned long state_handler_updates;
} AvspRound1ActorCore;

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
    signed char attempt_initial;
    unsigned char cadence_initial;
    unsigned char cadence_reload;
    unsigned char empty_timer_initial;
    unsigned char resource_capacity;
    unsigned char resource_debit;
    unsigned char recharge_after_success;
    unsigned char normal_recharge_reload;
    unsigned char depleted_recharge_reload;
    signed char projectile_class;
    unsigned short projectile_source_base;
    unsigned short projectile_stride;
    unsigned short player_owner;
    unsigned long projectile_attack_table;
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
    unsigned char angle;
    unsigned char damage_class_index;
    unsigned char attack_selector;
    unsigned short object_or;
    unsigned long animation_record;
    unsigned long assembly;
    unsigned char active_collision;
    unsigned char parent_presentation_selector;
    unsigned char presentation_index;
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
    unsigned char navigation_bounds_active;
    short navigation_bound_x;
    short navigation_bound_z;
    unsigned long navigation_applications;
    unsigned long navigation_clamps;
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
    unsigned long player_weapon_impact_requests;
    unsigned long player_weapon_impact_allocations;
    unsigned long player_weapon_impact_allocation_failures;
    unsigned long player_weapon_impact_releases;
    unsigned long player_weapon_impact_presentation_bindings;
    unsigned long player_weapon_impact_audio_events;
    unsigned short player_weapon_impact_audio_command;
    unsigned char player_weapon_impact_audio_selector;
    unsigned long player_resource_recharges;
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
int avsp_round1_is_weapon_impact_actor(const AvspRound1ActorCore *actor);
int avsp_round1_entry_valid(const AvspRound1Runtime *runtime);
int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime);

#endif
