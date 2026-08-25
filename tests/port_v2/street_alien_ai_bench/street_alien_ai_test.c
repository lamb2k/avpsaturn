#include <stdio.h>
#include "street_alien_ai_bench.h"

static int check(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static AvspAlienInput input_at(const short x, const short lane,
                               const int damage)
{
    AvspAlienInput input;
    input.target.active = 1u;
    input.target.id = 1u;
    input.target.x = x;
    input.target.lane = lane;
    input.incoming_damage = (short)damage;
    return input;
}

static int test_loop(void)
{
    AvspAlienRuntime runtime;
    AvspAlienInput input;
    int frame;
    int contact_frames[2];
    int contacts;
    avsp_alien_ai_init(&runtime, 0x7301u);
    input = input_at(1003, 320, 0);
    contacts = 0;
    for (frame = 0; frame <= 157; ++frame)
    {
        avsp_alien_ai_step(&runtime, &input);
        if (runtime.contact && contacts < 2) contact_frames[contacts++] = frame;
        if (frame == 37 && !check(runtime.state == AVSP_ALIEN_STATE_ATTACK &&
                                  runtime.x == 1071 && runtime.lane == 320 &&
                                  runtime.rng_seed == 0x595au &&
                                  runtime.attack_timer == 120u,
                                  "source approach/RNG attack start drift")) return 0;
    }
    return check(contacts == 2 && contact_frames[0] == 85 &&
                 contact_frames[1] == 156 && runtime.state == AVSP_ALIEN_STATE_APPROACH &&
                 runtime.inner_state == 8u && runtime.damage_events == 2UL,
                 "contact/recovery loop drift");
}

static int test_counterfactuals(void)
{
    AvspAlienRuntime runtime;
    AvspAlienInput input;
    int frame;
    avsp_alien_ai_init(&runtime, 0x0001u);
    input = input_at(1200, 320, 0);
    for (frame = 0; frame < 38; ++frame) avsp_alien_ai_step(&runtime, &input);
    if (!check(runtime.attack_timer == 30u && runtime.rng_seed == 0x0001u,
               "forced RNG timer counterfactual drift")) return 0;
    input.target.x = 2000;
    for (frame = 0; frame < 30; ++frame) avsp_alien_ai_step(&runtime, &input);
    if (!check(runtime.contacts == 0UL && runtime.state == AVSP_ALIEN_STATE_APPROACH,
               "current-position contact counterfactual drift")) return 0;
    input.incoming_damage = 24;
    avsp_alien_ai_step(&runtime, &input);
    input.incoming_damage = 0;
    for (frame = 0; frame < 38; ++frame) avsp_alien_ai_step(&runtime, &input);
    if (!check(runtime.health == 63 && runtime.state == AVSP_ALIEN_STATE_APPROACH,
               "HIT recovery drift")) return 0;
    input.incoming_damage = 64;
    avsp_alien_ai_step(&runtime, &input);
    input.incoming_damage = 0;
    for (frame = 0; frame < 140; ++frame) avsp_alien_ai_step(&runtime, &input);
    return check(runtime.state == AVSP_ALIEN_STATE_INACTIVE && runtime.removed,
                 "KO removal drift");
}

int main(void)
{
    if (!check(avsp_alien_ai_contract_valid(), "source RNG contract rejected")) return 1;
    if (!test_loop() || !test_counterfactuals()) return 1;
    puts("SALVAGE-11 street alien AI core: PASS");
    return 0;
}
