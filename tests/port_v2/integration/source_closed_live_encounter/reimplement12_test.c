#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/integration/live_encounter/live_encounter.h"

static int check(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static void player_step(AvspPwRuntime *runtime, const unsigned short mask)
{
    AvspPwInput input;
    input.mask = mask;
    input.received_damage = 0;
    avsp_pw_step(runtime, &input);
}

static int test_navigation_projection_and_facing(void)
{
    AvspPwRuntime player;
    short x;
    short z;
    short before;
    int frame;
    x = 1200;
    z = 400;
    avsp_pw_resolve_navigation(&x, &z);
    if (!check(x == 1091 && z == 327,
               "Coffee Shop upper-wall envelope drift")) return 0;
    x = 1184;
    z = 224;
    avsp_pw_resolve_navigation(&x, &z);
    if (!check(x == 1184 && z == 224,
               "Coffee Shop lower-route witness drift")) return 0;
    if (!check(avsp_live_encounter_project_screen_y(327, 0) == 170 &&
               avsp_live_encounter_project_screen_y(319, 0) == 178 &&
               avsp_live_encounter_project_screen_y(224, 0) == 273,
               "source-world to screen projection drift")) return 0;
    avsp_pw_init(&player);
    before = avsp_live_encounter_project_screen_y(player.lane, 0);
    for (frame = 0; frame < 20; ++frame)
        player_step(&player, AVSP_PW_INPUT_UP);
    player_step(&player, 0u);
    player_step(&player, 0u);
    if (!check(player.lane == 327 &&
               avsp_live_encounter_project_screen_y(player.lane, 0) < before,
               "Up did not increase world-z and move upward on screen")) return 0;
    for (frame = 0; frame < 20; ++frame)
        player_step(&player, AVSP_PW_INPUT_RIGHT);
    for (frame = 0; frame < 6; ++frame) player_step(&player, 0u);
    if (!check(player.facing == 1,
               "neutral release did not retain right-facing latch")) return 0;
    player.x = 1091;
    player.lane = 320;
    for (frame = 0; frame < 80; ++frame)
        player_step(&player, AVSP_PW_INPUT_RIGHT);
    return check(player.x == 1091 && player.lane == 320,
                 "player traversed the measured upper wall");
}

static int test_combo_and_equipment(void)
{
    AvspPwRuntime player;
    int frame;
    avsp_pw_init(&player);
    player_step(&player, AVSP_PW_INPUT_ATTACK);
    for (frame = 0; frame < 6; ++frame)
        player_step(&player, AVSP_PW_INPUT_ATTACK);
    if (!check(player.accepted_attack_edges == 1UL && player.selector == 1u &&
               player.action_local_equipment_flag == 0u,
               "held input or equipment flag changed close-action authority"))
        return 0;
    player_step(&player, 0u);
    while (player.phase != AVSP_PW_PHASE_RECOVERY)
        player_step(&player, 0u);
    player_step(&player, AVSP_PW_INPUT_ATTACK);
    if (!check(player.selector == 2u && player.action_elapsed == 0u &&
               player.accepted_attack_edges == 2UL,
               "live recovery edge did not dispatch close step 2")) return 0;
    player_step(&player, 0u);
    while (!avsp_pw_can_control(&player)) player_step(&player, 0u);
    for (frame = 0; frame < 31; ++frame) player_step(&player, 0u);
    player_step(&player, AVSP_PW_INPUT_ATTACK);
    if (!check(player.selector == 1u,
               "expired follow-up did not restart close step 1")) return 0;
    return check(player.assembly ==
                     avsp_pw_assembly_for_record(player.animation_record) &&
                 player.assembly != 0UL,
                 "player record and assembly lost single-state ownership");
}

static AvspAlienInput alien_input(const short x, const short z)
{
    AvspAlienInput input;
    memset(&input, 0, sizeof(input));
    input.target.active = 1u;
    input.target.id = 1u;
    input.target.x = x;
    input.target.lane = z;
    return input;
}

static int run_to_attack(AvspAlienRuntime *alien, AvspAlienInput *input)
{
    int frame;
    avsp_alien_ai_step(alien, input);
    if (!check(alien->source_action == 0x1600u && alien->facing == 1,
               "authored approach facing changed with target position")) return 0;
    for (frame = 1; frame < 38; ++frame)
        avsp_alien_ai_step(alien, input);
    return check(alien->state == AVSP_ALIEN_STATE_ATTACK &&
                 alien->x == 1071 && alien->lane == 320 &&
                 alien->facing == 1 && alien->source_action == 0x1800u &&
                 alien->animation_record == 0x0012E8ECUL &&
                 alien->assembly == 0x0012F5DEUL,
                 "authored approach/RNG attack identity drift");
}

static int test_alien_state_presentation_and_contact(void)
{
    AvspAlienRuntime alien;
    AvspAlienInput input;
    int frame;
    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(800, 320);
    if (!run_to_attack(&alien, &input)) return 0;
    if (!check(alien.facing == 1,
               "opening route was replaced by generic face-target")) return 0;
    input.target.x = 1003;
    for (frame = 0; frame < 48; ++frame) avsp_alien_ai_step(&alien, &input);
    if (!check(alien.contact && alien.contact_damage == 8u,
               "measured distance-68 contact witness was lost")) return 0;
    for (; frame < 120; ++frame) avsp_alien_ai_step(&alien, &input);
    if (!check(alien.state == AVSP_ALIEN_STATE_APPROACH &&
               alien.source_action == 0x1A00u && alien.facing == 0 &&
               alien.animation_record == 0x0012D5E4UL &&
               alien.assembly == 0x0012FAE8UL,
               "delayed crossing state did not own facing and assembly")) return 0;

    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1002, 320);
    if (!run_to_attack(&alien, &input)) return 0;
    for (frame = 0; frame < 48; ++frame) avsp_alien_ai_step(&alien, &input);
    if (!check(!alien.contact, "legacy wider alien contact distance returned"))
        return 0;
    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1003, 321);
    if (!run_to_attack(&alien, &input)) return 0;
    for (frame = 0; frame < 48; ++frame) avsp_alien_ai_step(&alien, &input);
    return check(!alien.contact,
                 "alien contact ignored the measured same-floor guard");
}

static int test_live_same_tick_contract(void)
{
    AvspLiveEncounterRuntime runtime;
    AvspLiveEncounterFrame output;
    AvspLiveEncounterInput input;
    avsp_live_encounter_init(&runtime);
    input.frame = 0UL;
    input.player_mask = 0u;
    if (!avsp_live_encounter_step(&runtime, &input, &output)) return 0;
    if (!check(output.player_screen_y == 177 && output.alien_screen_y == 154,
               "initial screen projection is not source-world derived")) return 0;
    if (!check(output.player.animation_record != 0UL &&
               output.player.assembly ==
                   avsp_pw_assembly_for_record(output.player.animation_record) &&
               output.alien.animation_record != 0UL &&
               output.alien.assembly == avsp_alien_ai_assembly_for_record(
                   output.alien.animation_record),
               "same-tick state/record/assembly diagnostics drift")) return 0;
    avsp_live_encounter_init(&runtime);
    runtime.route_unlocked = 1u;
    runtime.unlock_player_x = 990;
    runtime.player.x_numerator = 1000L * 8L;
    runtime.player.x = 1000;
    input.frame = 0UL;
    input.player_mask = 0u;
    if (!avsp_live_encounter_step(&runtime, &input, &output)) return 0;
    if (!check(output.camera_world_x == 790 &&
               output.continued_after_unlock == 1u,
               "source-world camera delta lost its approved lock origin"))
        return 0;
    return check(!avsp_live_encounter_clear_allowed(0u, 0u, 1u, 1u) &&
                 !avsp_live_encounter_clear_allowed(1u, 0u, 1u, 1u) &&
                 avsp_live_encounter_clear_allowed(1u, 1u, 0u, 0u),
                 "timer or presentation regained encounter-clear authority");
}

int main(void)
{
    if (!check(avsp_live_encounter_contract_flags() == 127u &&
               avsp_live_encounter_contract_valid(),
               "REIMPLEMENT-12 SPEC-01 identity rejected")) return 1;
    if (!test_navigation_projection_and_facing() ||
        !test_combo_and_equipment() ||
        !test_alien_state_presentation_and_contact() ||
        !test_live_same_tick_contract()) return 1;
    puts("REIMPLEMENT-12 source-closed live encounter: PASS");
    return 0;
}
