#ifndef AVSP_PORT_V2_ROUND1_H
#define AVSP_PORT_V2_ROUND1_H

#define AVSP_ROUND1_SPEC02_SHA256 \
    "3cfa5410fee3942a9bd6bb515f10aefdd293ee4cd628fb503d9685bce4c7c3f8"
#define AVSP_ROUND1_CANARY_HEAD 0x52314548UL
#define AVSP_ROUND1_CANARY_TAIL 0x52314554UL
#define AVSP_ROUND1_ROUTE_ENTRY_STATE 2
#define AVSP_ROUND1_INITIAL_RNG 0x8DEFu
#define AVSP_ROUND1_PLAYER_HEALTH 101
#define AVSP_ROUND1_POOL_COUNT 4
#define AVSP_ROUND1_MAX_POOL_CAPACITY 32

typedef struct
{
    unsigned char active;
    signed char actor_class;
    unsigned short state;
    unsigned short substate;
    unsigned char type;
    unsigned char facing;
    short x;
    short y;
    short z;
    short health;
} AvspRound1ActorCore;

typedef struct
{
    unsigned char record_type;
    unsigned char capacity;
    unsigned short stride;
    unsigned short source_base;
    unsigned char free_count;
    unsigned short free_stack[AVSP_ROUND1_MAX_POOL_CAPACITY];
} AvspRound1Pool;

typedef struct
{
    unsigned long head_canary;
    short route_state;
    unsigned short rng_seed;
    AvspRound1ActorCore player;
    AvspRound1Pool pools[AVSP_ROUND1_POOL_COUNT];
    unsigned long frame;
    unsigned long fallback_count;
    unsigned long tail_canary;
} AvspRound1Runtime;

void avsp_round1_init(AvspRound1Runtime *runtime);
int avsp_round1_entry_valid(const AvspRound1Runtime *runtime);
int avsp_round1_canaries_ok(const AvspRound1Runtime *runtime);

#endif
