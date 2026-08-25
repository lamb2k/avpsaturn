#include "street_alien_ai.h"

#define AVSP_ALIEN_START_X 960
#define AVSP_ALIEN_START_LANE 343
#define AVSP_ALIEN_START_HEALTH 87
#define AVSP_ALIEN_APPROACH_FRAMES 38u
#define AVSP_ALIEN_APPROACH_X 111
#define AVSP_ALIEN_APPROACH_LANE 23
#define AVSP_ALIEN_HIT_FRAMES 39u
#define AVSP_ALIEN_KO_FRAMES 141u
#define AVSP_ALIEN_CONTACT_DAMAGE 8u
#define AVSP_ALIEN_MAX_CONTACT_X 68

static const unsigned long avsp_alien_approach_records[8] =
{
    0x0012EC04UL, 0x0012EC14UL, 0x0012EC24UL, 0x0012EC34UL,
    0x0012EC44UL, 0x0012EC54UL, 0x0012EC64UL, 0x0012EC74UL
};

static const unsigned long avsp_alien_attack_records[4] =
{
    0x0012E8ECUL, 0x0012E8FCUL, 0x0012E90CUL, 0x0012E91CUL
};

static short avsp_alien_abs(const short value)
{
    return value < 0 ? (short)-value : value;
}

static void avsp_alien_fraction(long *numerator, short *position,
                                const int amount)
{
    long before;
    long after;
    before = *numerator / (long)AVSP_ALIEN_APPROACH_FRAMES;
    *numerator += amount;
    after = *numerator / (long)AVSP_ALIEN_APPROACH_FRAMES;
    *position = (short)(*position + (short)(after - before));
}

unsigned short avsp_alien_ai_rng_step(const unsigned short seed)
{
    unsigned short high;
    unsigned short low;
    high = (unsigned short)(((unsigned long)3u * seed & 0xffffu) >> 8);
    low = (unsigned short)(((seed & 0xffu) + high) & 0xffu);
    return (unsigned short)((high << 8) | low);
}

unsigned short avsp_alien_ai_timer_for_seed(const unsigned short seed_after)
{
    return (seed_after & 0xffu) < 0x40u ? 30u : 120u;
}

unsigned long avsp_alien_ai_assembly_for_record(const unsigned long record)
{
    switch (record)
    {
        case 0x0012DDB0UL: return 0x00130346UL;
        case 0x0012EC04UL: return 0x0012F7CCUL;
        case 0x0012EC14UL: return 0x0012F7E4UL;
        case 0x0012EC24UL: return 0x0012F7FCUL;
        case 0x0012EC34UL: return 0x0012F814UL;
        case 0x0012EC44UL: return 0x0012F82CUL;
        case 0x0012EC54UL: return 0x0012F85EUL;
        case 0x0012EC64UL: return 0x0012F890UL;
        case 0x0012EC74UL: return 0x0012F8B8UL;
        case 0x0012E8ECUL: return 0x0012F5DEUL;
        case 0x0012E8FCUL: return 0x0012FA0CUL;
        case 0x0012E90CUL: return 0x0012FA2AUL;
        case 0x0012E91CUL: return 0x0012FA0CUL;
        case 0x0012D5E4UL: return 0x0012FAE8UL;
        case 0x0012DD50UL: return 0x00130248UL;
        case 0x0012DD28UL: return 0x0013020CUL;
        case 0x0012DD3CUL: return 0x0013023AUL;
        case 0x0012E214UL: return 0x0013020CUL;
        default: return 0UL;
    }
}

static void avsp_alien_set_presentation(AvspAlienRuntime *runtime,
                                        const unsigned long record,
                                        const unsigned short index)
{
    runtime->presentation_index = index;
    runtime->animation_record = record;
    runtime->assembly = avsp_alien_ai_assembly_for_record(record);
}

int avsp_alien_ai_contract_valid(void)
{
    return avsp_alien_ai_rng_step(0x7301u) == 0x595au &&
           avsp_alien_ai_timer_for_seed(0x595au) == 120u &&
           avsp_alien_ai_rng_step(0x0001u) == 0x0001u &&
           avsp_alien_ai_timer_for_seed(0x0001u) == 30u &&
           avsp_alien_ai_assembly_for_record(0x0012E8ECUL) ==
               0x0012F5DEUL &&
           avsp_alien_ai_assembly_for_record(0x0012D5E4UL) ==
               0x0012FAE8UL;
}

void avsp_alien_ai_init(AvspAlienRuntime *runtime,
                        const unsigned short seed)
{
    if (runtime == 0) return;
    runtime->class_id = AVSP_ALIEN_CLASS_ID;
    runtime->state = AVSP_ALIEN_STATE_APPROACH;
    runtime->inner_state = 0u;
    runtime->target_id = 0u;
    runtime->x = AVSP_ALIEN_START_X;
    runtime->lane = AVSP_ALIEN_START_LANE;
    runtime->health = AVSP_ALIEN_START_HEALTH;
    runtime->facing = 1;
    runtime->approach_elapsed = 0u;
    runtime->attack_elapsed = 0u;
    runtime->attack_timer = 0u;
    runtime->hit_timer = 0u;
    runtime->ko_timer = 0u;
    runtime->rng_seed = seed;
    runtime->rng_cursor = 0u;
    runtime->contact = 0u;
    runtime->contact_damage = 0u;
    runtime->removed = 0u;
    runtime->source_action = 0x1600u;
    avsp_alien_set_presentation(runtime, avsp_alien_approach_records[0], 0u);
    runtime->x_numerator = 0;
    runtime->lane_numerator = 0;
    runtime->scheduler_updates = 0UL;
    runtime->target_selections = 0UL;
    runtime->contacts = 0UL;
    runtime->damage_events = 0UL;
}

static int avsp_alien_select_target(AvspAlienRuntime *runtime,
                                    const AvspAlienTarget *target)
{
    if (!target->active) return 0;
    if (runtime->target_id != target->id)
    {
        runtime->target_id = target->id;
        ++runtime->target_selections;
    }
    return 1;
}

static void avsp_alien_begin_attack(AvspAlienRuntime *runtime)
{
    runtime->rng_seed = avsp_alien_ai_rng_step(runtime->rng_seed);
    ++runtime->rng_cursor;
    runtime->attack_timer = avsp_alien_ai_timer_for_seed(runtime->rng_seed);
    runtime->attack_elapsed = 0u;
    runtime->state = AVSP_ALIEN_STATE_ATTACK;
    runtime->inner_state = 0u;
    runtime->source_action = 0x1800u;
    runtime->facing = 1;
    avsp_alien_set_presentation(runtime, avsp_alien_attack_records[0], 0u);
}

static void avsp_alien_approach(AvspAlienRuntime *runtime,
                                const AvspAlienTarget *target)
{
    (void)target;
    runtime->source_action = 0x1600u;
    runtime->facing = 1;
    avsp_alien_fraction(&runtime->x_numerator, &runtime->x,
                        AVSP_ALIEN_APPROACH_X);
    avsp_alien_fraction(&runtime->lane_numerator, &runtime->lane,
                        -AVSP_ALIEN_APPROACH_LANE);
    avsp_alien_set_presentation(runtime,
        avsp_alien_approach_records[runtime->approach_elapsed & 7u],
        (unsigned short)(runtime->approach_elapsed & 7u));
    ++runtime->approach_elapsed;
    if (runtime->approach_elapsed >= AVSP_ALIEN_APPROACH_FRAMES)
    {
        runtime->approach_elapsed = 0u;
        runtime->x_numerator = 0;
        runtime->lane_numerator = 0;
        avsp_alien_begin_attack(runtime);
    }
}

static void avsp_alien_attack(AvspAlienRuntime *runtime,
                              const AvspAlienTarget *target)
{
    ++runtime->attack_elapsed;
    avsp_alien_set_presentation(runtime,
        avsp_alien_attack_records[runtime->attack_elapsed & 3u],
        (unsigned short)(runtime->attack_elapsed & 3u));
    if ((runtime->attack_elapsed == 48u || runtime->attack_elapsed == 119u) &&
        avsp_alien_abs((short)(target->x - runtime->x)) <=
            AVSP_ALIEN_MAX_CONTACT_X &&
        target->lane == runtime->lane)
    {
        runtime->contact = 1u;
        runtime->contact_damage = AVSP_ALIEN_CONTACT_DAMAGE;
        ++runtime->contacts;
        ++runtime->damage_events;
    }
    if (runtime->attack_elapsed >= runtime->attack_timer)
    {
        runtime->state = AVSP_ALIEN_STATE_APPROACH;
        runtime->inner_state = 8u;
        runtime->attack_elapsed = 0u;
        runtime->attack_timer = 0u;
        if (target->x < runtime->x)
        {
            runtime->source_action = 0x1A00u;
            runtime->facing = 0;
            avsp_alien_set_presentation(runtime, 0x0012D5E4UL, 0u);
        }
        else if (target->lane > runtime->lane)
        {
            runtime->source_action = 0x0600u;
            runtime->facing = 0;
            avsp_alien_set_presentation(runtime, 0x0012D5E4UL, 0u);
        }
        else
        {
            runtime->source_action = 0x1600u;
            runtime->facing = 1;
            avsp_alien_set_presentation(runtime,
                avsp_alien_approach_records[0], 0u);
        }
    }
}

void avsp_alien_ai_step(AvspAlienRuntime *runtime,
                        const AvspAlienInput *input)
{
    if (runtime == 0 || input == 0 || runtime->state == AVSP_ALIEN_STATE_INACTIVE)
        return;
    ++runtime->scheduler_updates;
    runtime->contact = 0u;
    runtime->contact_damage = 0u;
    if (input->incoming_damage > 0 && runtime->state != AVSP_ALIEN_STATE_KO)
    {
        runtime->health = (short)(runtime->health - input->incoming_damage);
        runtime->attack_elapsed = 0u;
        runtime->attack_timer = 0u;
        runtime->approach_elapsed = 0u;
        runtime->x_numerator = 0;
        runtime->lane_numerator = 0;
        if (runtime->health <= 0)
        {
            runtime->state = AVSP_ALIEN_STATE_KO;
            runtime->ko_timer = AVSP_ALIEN_KO_FRAMES;
            avsp_alien_set_presentation(runtime, 0x0012E214UL, 0u);
        }
        else
        {
            runtime->state = AVSP_ALIEN_STATE_HIT;
            runtime->hit_timer = AVSP_ALIEN_HIT_FRAMES;
            avsp_alien_set_presentation(runtime, 0x0012DD50UL, 0u);
        }
    }
    if (runtime->state == AVSP_ALIEN_STATE_KO)
    {
        if (runtime->ko_timer > 0u) --runtime->ko_timer;
        if (runtime->ko_timer == 0u)
        {
            runtime->state = AVSP_ALIEN_STATE_INACTIVE;
            runtime->removed = 1u;
        }
        return;
    }
    if (runtime->state == AVSP_ALIEN_STATE_HIT)
    {
        if (runtime->hit_timer > 0u) --runtime->hit_timer;
        if (runtime->hit_timer == 0u)
        {
            runtime->state = AVSP_ALIEN_STATE_APPROACH;
            runtime->inner_state = 8u;
            runtime->source_action = 0x1A00u;
            runtime->facing = 0;
            avsp_alien_set_presentation(runtime, 0x0012D5E4UL, 0u);
        }
        return;
    }
    if (!avsp_alien_select_target(runtime, &input->target)) return;
    if (runtime->state == AVSP_ALIEN_STATE_APPROACH &&
        runtime->source_action == 0x1600u)
        avsp_alien_approach(runtime, &input->target);
    else if (runtime->state == AVSP_ALIEN_STATE_ATTACK)
        avsp_alien_attack(runtime, &input->target);
}

void avsp_alien_ai_view(const AvspAlienRuntime *runtime, AvspAlienView *view)
{
    if (runtime == 0 || view == 0) return;
    view->class_id = runtime->class_id;
    view->state = runtime->state;
    view->inner_state = runtime->inner_state;
    view->target_id = runtime->target_id;
    view->x = runtime->x;
    view->lane = runtime->lane;
    view->health = runtime->health;
    view->facing = runtime->facing;
    view->approach_elapsed = runtime->approach_elapsed;
    view->attack_elapsed = runtime->attack_elapsed;
    view->attack_timer = runtime->attack_timer;
    view->rng_seed = runtime->rng_seed;
    view->rng_cursor = runtime->rng_cursor;
    view->contact = runtime->contact;
    view->contact_damage = runtime->contact_damage;
    view->removed = runtime->removed;
    view->source_action = runtime->source_action;
    view->presentation_index = runtime->presentation_index;
    view->animation_record = runtime->animation_record;
    view->assembly = runtime->assembly;
}
