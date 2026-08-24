#include <stdio.h>
#include <string.h>

#include "predator_warrior_action_bench.h"

static int require_true(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static void step(AvspPwRuntime *runtime, const unsigned short mask,
                 const int damage)
{
    AvspPwInput input;
    input.mask = mask;
    input.received_damage = (short)damage;
    avsp_pw_step(runtime, &input);
}

static void direction_pulse(AvspPwRuntime *runtime, const unsigned short mask)
{
    int frame;
    for (frame = 0; frame < 20; ++frame) step(runtime, mask, 0);
    step(runtime, 0u, 0);
    step(runtime, 0u, 0);
}

static int test_movement(void)
{
    AvspPwRuntime runtime;
    avsp_pw_init(&runtime);
    direction_pulse(&runtime, AVSP_PW_INPUT_RIGHT);
    if (!require_true(runtime.x == 1023 && runtime.facing == 1,
                      "right source differential drift")) return 0;
    direction_pulse(&runtime, AVSP_PW_INPUT_LEFT);
    if (!require_true(runtime.x == 978 && runtime.facing == 0,
                      "left source differential drift")) return 0;
    direction_pulse(&runtime, AVSP_PW_INPUT_UP);
    if (!require_true(runtime.lane == 327,
                      "up-lane source differential drift")) return 0;
    direction_pulse(&runtime, AVSP_PW_INPUT_DOWN);
    return require_true(runtime.lane == 315,
                        "down-lane source differential drift");
}

static int test_attack(const unsigned short expected_selector)
{
    AvspPwRuntime runtime;
    AvspPwView view;
    const AvspPwAttackDef *definition;
    unsigned short selector;
    unsigned short elapsed;
    int active_count;
    avsp_pw_init(&runtime);
    for (selector = 1u; selector < expected_selector; ++selector)
    {
        step(&runtime, AVSP_PW_INPUT_ATTACK, 0);
        step(&runtime, 0u, 0);
        while (!avsp_pw_can_control(&runtime)) step(&runtime, 0u, 0);
        while (runtime.combo_idle_frames < 20u) step(&runtime, 0u, 0);
    }
    definition = &avsp_pw_action_defs[expected_selector - 1u];
    step(&runtime, AVSP_PW_INPUT_ATTACK, 0);
    if (!require_true(runtime.selector == expected_selector &&
                      runtime.action_elapsed == 0u &&
                      runtime.source_action == 2u,
                      "attack edge did not select source step")) return 0;
    step(&runtime, 0u, 0);
    active_count = 0;
    for (elapsed = 1u; elapsed < definition->return_frame; ++elapsed)
    {
        avsp_pw_view(&runtime, &view);
        if (!require_true(view.action_elapsed == elapsed,
                          "attack elapsed frame drift")) return 0;
        if (elapsed == definition->presentation_first &&
            !require_true(view.source_action == 1536u,
                          "presentation start drift")) return 0;
        if (elapsed >= definition->active_first &&
            elapsed <= definition->active_last)
        {
            ++active_count;
            if (!require_true(view.attack_active &&
                              view.attack_box.hit_value == definition->box.hit_value,
                              "active box drift")) return 0;
        }
        step(&runtime, 0u, 0);
    }
    if (!require_true(active_count ==
            (int)(definition->active_last - definition->active_first + 1u),
            "active duration drift")) return 0;
    return require_true(avsp_pw_can_control(&runtime) &&
                        runtime.accepted_attack_edges == expected_selector,
                        "return-to-control or attack-edge ownership drift");
}

static unsigned long replay_checksum(const int report_contacts)
{
    AvspPwRuntime runtime;
    AvspPwView view;
    unsigned long checksum;
    int frame;
    avsp_pw_init(&runtime);
    checksum = 2166136261UL;
    for (frame = 0; frame < 240; ++frame)
    {
        unsigned short mask = 0u;
        if (frame < 20) mask |= AVSP_PW_INPUT_RIGHT;
        if (frame == 30 || frame == 75 || frame == 120 || frame == 165)
            mask |= AVSP_PW_INPUT_ATTACK;
        step(&runtime, mask, 0);
        if (report_contacts && runtime.attack_active) avsp_pw_report_contact(&runtime);
        avsp_pw_view(&runtime, &view);
        checksum = (checksum ^ (unsigned long)(view.x & 0xffff)) * 16777619UL;
        checksum = (checksum ^ (unsigned long)view.selector) * 16777619UL;
        checksum = (checksum ^ (unsigned long)view.action_elapsed) * 16777619UL;
    }
    checksum ^= runtime.accepted_attack_edges << 8;
    return checksum;
}

static int test_contact_independence(void)
{
    unsigned long no_contacts = replay_checksum(0);
    unsigned long contacts = replay_checksum(1);
    return require_true(no_contacts == contacts,
        "contact reports became player attack-selection authority");
}

static int test_hit_ko(void)
{
    AvspPwRuntime runtime;
    int frame;
    avsp_pw_init(&runtime);
    step(&runtime, AVSP_PW_INPUT_ATTACK, 0);
    step(&runtime, 0u, 8);
    if (!require_true(runtime.state == AVSP_PW_STATE_HIT &&
                      runtime.health == 93 && runtime.selector == 0u,
                      "HIT did not interrupt attack")) return 0;
    for (frame = 0; frame < 16; ++frame) step(&runtime, 0u, 0);
    if (!require_true(avsp_pw_can_control(&runtime),
                      "nonlethal HIT did not return control")) return 0;
    step(&runtime, 0u, 100);
    return require_true(runtime.state == AVSP_PW_STATE_KO &&
                        runtime.health <= 0 && !avsp_pw_can_control(&runtime),
                        "lethal damage did not hold KO");
}

static int test_mutation(void)
{
    AvspPwAttackDef mutation[AVSP_PW_ACTION_COUNT];
    memcpy(mutation, avsp_pw_action_defs, sizeof(mutation));
    mutation[2].active_first = 6u;
    if (!require_true(!avsp_pw_action_defs_valid(mutation,
            AVSP_PW_ACTION_COUNT), "timing mutation was accepted")) return 0;
    memcpy(mutation, avsp_pw_action_defs, sizeof(mutation));
    mutation[3].box.x_half = 54;
    return require_true(!avsp_pw_action_defs_valid(mutation,
            AVSP_PW_ACTION_COUNT), "box mutation was accepted");
}

int main(void)
{
    unsigned short selector;
    if (!require_true(avsp_pw_action_defs_valid(avsp_pw_action_defs,
            AVSP_PW_ACTION_COUNT), "approved action definitions rejected")) return 1;
    if (!test_movement()) return 1;
    for (selector = 1u; selector <= 4u; ++selector)
        if (!test_attack(selector)) return 1;
    if (!test_contact_independence() || !test_hit_ko() || !test_mutation()) return 1;
    puts("SALVAGE-10 Predator Warrior action core: PASS");
    return 0;
}
