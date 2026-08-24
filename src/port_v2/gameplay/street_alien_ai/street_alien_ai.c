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

int avsp_alien_ai_contract_valid(void)
{
    return avsp_alien_ai_rng_step(0x7301u) == 0x595au &&
           avsp_alien_ai_timer_for_seed(0x595au) == 120u &&
           avsp_alien_ai_rng_step(0x0001u) == 0x0001u &&
           avsp_alien_ai_timer_for_seed(0x0001u) == 30u;
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
}

static void avsp_alien_approach(AvspAlienRuntime *runtime,
                                const AvspAlienTarget *target)
{
    int lane_amount;
    if (runtime->x < target->x)
    {
        avsp_alien_fraction(&runtime->x_numerator, &runtime->x,
                            AVSP_ALIEN_APPROACH_X);
        runtime->facing = 1;
    }
    else if (runtime->x > target->x)
    {
        avsp_alien_fraction(&runtime->x_numerator, &runtime->x,
                            -AVSP_ALIEN_APPROACH_X);
        runtime->facing = 0;
    }
    lane_amount = 0;
    if (runtime->lane < target->lane) lane_amount = AVSP_ALIEN_APPROACH_LANE;
    else if (runtime->lane > target->lane) lane_amount = -AVSP_ALIEN_APPROACH_LANE;
    if (lane_amount != 0)
        avsp_alien_fraction(&runtime->lane_numerator, &runtime->lane,
                            lane_amount);
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
    if ((runtime->attack_elapsed == 48u || runtime->attack_elapsed == 119u) &&
        avsp_alien_abs((short)(target->x - runtime->x)) <= 160 &&
        avsp_alien_abs((short)(target->lane - runtime->lane)) <= 32)
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
        }
        else
        {
            runtime->state = AVSP_ALIEN_STATE_HIT;
            runtime->hit_timer = AVSP_ALIEN_HIT_FRAMES;
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
        }
        return;
    }
    if (!avsp_alien_select_target(runtime, &input->target)) return;
    if (runtime->state == AVSP_ALIEN_STATE_APPROACH)
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
}
