#ifndef AVSP_PORT_V2_STREET_ALIEN_AI_H
#define AVSP_PORT_V2_STREET_ALIEN_AI_H

#define AVSP_ALIEN_AI_INTERFACE_VERSION 1
#define AVSP_ALIEN_CLASS_ID 0x1fu
#define AVSP_ALIEN_STATE_INACTIVE 0u
#define AVSP_ALIEN_STATE_APPROACH 2u
#define AVSP_ALIEN_STATE_ATTACK 3u
#define AVSP_ALIEN_STATE_HIT 4u
#define AVSP_ALIEN_STATE_KO 5u

typedef struct
{
    unsigned short active;
    unsigned short id;
    short x;
    short lane;
} AvspAlienTarget;

typedef struct
{
    AvspAlienTarget target;
    short incoming_damage;
} AvspAlienInput;

typedef struct
{
    unsigned short class_id;
    unsigned short state;
    unsigned short inner_state;
    unsigned short target_id;
    short x;
    short lane;
    short health;
    short facing;
    unsigned short approach_elapsed;
    unsigned short attack_elapsed;
    unsigned short attack_timer;
    unsigned short hit_timer;
    unsigned short ko_timer;
    unsigned short rng_seed;
    unsigned short rng_cursor;
    unsigned short contact;
    unsigned short contact_damage;
    unsigned short removed;
    long x_numerator;
    long lane_numerator;
    unsigned long scheduler_updates;
    unsigned long target_selections;
    unsigned long contacts;
    unsigned long damage_events;
} AvspAlienRuntime;

typedef struct
{
    unsigned short class_id;
    unsigned short state;
    unsigned short inner_state;
    unsigned short target_id;
    short x;
    short lane;
    short health;
    short facing;
    unsigned short approach_elapsed;
    unsigned short attack_elapsed;
    unsigned short attack_timer;
    unsigned short rng_seed;
    unsigned short rng_cursor;
    unsigned short contact;
    unsigned short contact_damage;
    unsigned short removed;
} AvspAlienView;

void avsp_alien_ai_init(AvspAlienRuntime *runtime, unsigned short seed);
void avsp_alien_ai_step(AvspAlienRuntime *runtime, const AvspAlienInput *input);
void avsp_alien_ai_view(const AvspAlienRuntime *runtime, AvspAlienView *view);
unsigned short avsp_alien_ai_rng_step(unsigned short seed);
unsigned short avsp_alien_ai_timer_for_seed(unsigned short seed_after);
int avsp_alien_ai_contract_valid(void);

#endif
