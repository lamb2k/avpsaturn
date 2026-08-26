#ifndef AVSP_PORT_V2_ROUND1_H
#define AVSP_PORT_V2_ROUND1_H

#include "../player_action/player_action.h"

#define AVSP_ROUND1_SPEC02_SHA256 \
    "3cfa5410fee3942a9bd6bb515f10aefdd293ee4cd628fb503d9685bce4c7c3f8"
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

#define AVSP_ROUND1_ENTRY_SET_POSITION 1u
#define AVSP_ROUND1_ENTRY_SET_SUBHANDLER 2u
#define AVSP_ROUND1_ENTRY_SOURCE_18 3u
#define AVSP_ROUND1_ENTRY_DWELL 4u
#define AVSP_ROUND1_ENTRY_SOURCE_16 5u
#define AVSP_ROUND1_ENTRY_TERMINATE 6u

typedef struct
{
    unsigned char active;
    signed char actor_class;
    unsigned short state;
    unsigned short substate;
    unsigned char type;
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
    unsigned long scheduler_updates;
    unsigned long handler_updates;
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
int avsp_round1_entry_valid(const AvspRound1Runtime *runtime);
int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime);

#endif
