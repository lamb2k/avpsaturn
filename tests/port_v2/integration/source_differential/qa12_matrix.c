#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/integration/live_encounter/live_encounter.h"

static int failures;

static void result(const char *name, const int passed)
{
    printf("CASE,%s,%s\n", name, passed ? "PASS" : "FAIL");
    if (!passed) ++failures;
}

static void player_step(AvspPwRuntime *runtime, const unsigned short mask,
                        const short damage)
{
    AvspPwInput input;
    input.mask = mask;
    input.received_damage = damage;
    avsp_pw_step(runtime, &input);
}

static void navigation_matrix(void)
{
    short x;
    short z;
    AvspPwRuntime player;
    int index;
    x = 863; z = 319; avsp_pw_resolve_navigation(&x, &z);
    result("navigation-left-bound", x == 864 && z == 319);
    x = 1185; z = 319; avsp_pw_resolve_navigation(&x, &z);
    result("navigation-lower-right-bound", x == 1184 && z == 319);
    x = 1184; z = 320; avsp_pw_resolve_navigation(&x, &z);
    result("navigation-upper-wall", x == 1091 && z == 320);
    x = 1184; z = 224; avsp_pw_resolve_navigation(&x, &z);
    result("navigation-lower-bypass", x == 1184 && z == 224);
    x = 1200; z = 400; avsp_pw_resolve_navigation(&x, &z);
    result("navigation-upper-corner", x == 1091 && z == 327);
    x = 900; z = 223; avsp_pw_resolve_navigation(&x, &z);
    result("navigation-lane-min", x == 900 && z == 224);

    avsp_pw_init(&player);
    for (index = 0; index < 30; ++index)
        player_step(&player, AVSP_PW_INPUT_UP, 0);
    result("movement-up-world-positive-screen-negative",
           player.lane == 327 &&
           avsp_live_encounter_project_screen_y(player.lane, 0) < 177);
    for (index = 0; index < 30; ++index)
        player_step(&player, AVSP_PW_INPUT_DOWN, 0);
    result("movement-down-reversal", player.lane < 327 &&
           avsp_live_encounter_project_screen_y(player.lane, 0) > 170);

    avsp_pw_init(&player);
    for (index = 0; index < 3; ++index)
        player_step(&player, AVSP_PW_INPUT_RIGHT, 0);
    for (index = 0; index < 5; ++index) player_step(&player, 0u, 0);
    result("facing-right-neutral-latch", player.facing == 1);
    for (index = 0; index < 3; ++index)
        player_step(&player, AVSP_PW_INPUT_LEFT, 0);
    for (index = 0; index < 5; ++index) player_step(&player, 0u, 0);
    result("facing-left-neutral-latch", player.facing == 0);

    player.x = 1091;
    player.x_numerator = 0L;
    player.lane = 320;
    player.lane_numerator = 0L;
    for (index = 0; index < 80; ++index)
        player_step(&player, AVSP_PW_INPUT_RIGHT, 0);
    result("upper-wall-no-traversal", player.x == 1091);
    for (index = 0; index < 8; ++index)
        player_step(&player, AVSP_PW_INPUT_DOWN, 0);
    for (index = 0; index < 80; ++index)
        player_step(&player, AVSP_PW_INPUT_RIGHT, 0);
    result("lower-route-bypasses-wall", player.lane < 320 && player.x == 1184);
}

static void player_matrix(void)
{
    AvspPwRuntime player;
    unsigned short expected;
    int guard;
    int identities = 1;
    avsp_pw_init(&player);
    player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
    for (guard = 0; guard < 6; ++guard)
        player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
    result("held-attack-no-repeat", player.accepted_attack_edges == 1UL &&
           player.selector == 1u && player.action_local_equipment_flag == 0u);

    avsp_pw_init(&player);
    for (expected = 1u; expected <= 4u; ++expected)
    {
        player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
        if (player.selector != expected) identities = 0;
        player_step(&player, 0u, 0);
        guard = 0;
        while (player.phase != AVSP_PW_PHASE_RECOVERY && guard++ < 80)
        {
            if (player.assembly == 0UL || player.assembly !=
                avsp_pw_assembly_for_record(player.animation_record) ||
                player.action_local_equipment_flag != 0u) identities = 0;
            player_step(&player, 0u, 0);
        }
    }
    result("combo-selectors-1-through-4", player.accepted_attack_edges == 4UL);
    result("player-state-record-assembly-continuity", identities);
    result("equipment-flag-not-visible-authority",
           player.action_local_equipment_flag == 0u);

    avsp_pw_init(&player);
    player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
    player_step(&player, 0u, 0);
    player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
    result("startup-repeat-rejected", player.accepted_attack_edges == 1UL &&
           player.rejected_attack_edges == 1UL && player.selector == 1u);

    while (!avsp_pw_can_control(&player)) player_step(&player, 0u, 0);
    for (guard = 0; guard < 31; ++guard) player_step(&player, 0u, 0);
    player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
    result("expired-combo-restarts-one", player.selector == 1u);

    avsp_pw_init(&player);
    player_step(&player, AVSP_PW_INPUT_ATTACK, 0);
    player_step(&player, 0u, 8);
    result("player-hit-cancels-action", player.state == AVSP_PW_STATE_HIT &&
           player.selector == 0u && player.action_local_equipment_flag == 0u);
    for (guard = 0; guard < 16; ++guard) player_step(&player, 0u, 0);
    result("player-hit-recovers-control", player.state == AVSP_PW_STATE_CONTROL);
}

static AvspAlienInput alien_input(const short x, const short z,
                                  const short damage)
{
    AvspAlienInput input;
    memset(&input, 0, sizeof(input));
    input.target.active = 1u;
    input.target.id = 1u;
    input.target.x = x;
    input.target.lane = z;
    input.incoming_damage = damage;
    return input;
}

static void alien_to_attack(AvspAlienRuntime *alien, AvspAlienInput *input)
{
    int index;
    for (index = 0; index < 38; ++index) avsp_alien_ai_step(alien, input);
}

static void alien_matrix(void)
{
    AvspAlienRuntime alien;
    AvspAlienInput input;
    int index;
    int attack_identity = 1;
    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(800, 320, 0);
    alien_to_attack(&alien, &input);
    result("alien-authored-approach", alien.x == 1071 && alien.lane == 320 &&
           alien.state == AVSP_ALIEN_STATE_ATTACK && alien.facing == 1 &&
           alien.source_action == 0x1800u);
    input.target.x = 1003;
    for (index = 0; index < 48; ++index)
    {
        avsp_alien_ai_step(&alien, &input);
        if (alien.assembly != avsp_alien_ai_assembly_for_record(
                alien.animation_record)) attack_identity = 0;
    }
    result("alien-contact-offset-48-distance-68", alien.contact &&
           alien.contact_damage == 8u);
    for (; index < 119; ++index) avsp_alien_ai_step(&alien, &input);
    result("alien-contact-offset-119", alien.contact &&
           alien.contact_damage == 8u);
    result("alien-attack-record-assembly-continuity", attack_identity);
    avsp_alien_ai_step(&alien, &input);
    result("alien-crossing-state-owns-facing", alien.state ==
           AVSP_ALIEN_STATE_APPROACH && alien.source_action == 0x1A00u &&
           alien.facing == 0 && alien.animation_record == 0x0012D5E4UL &&
           alien.assembly == 0x0012FAE8UL);

    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1002, 320, 0);
    alien_to_attack(&alien, &input);
    for (index = 0; index < 48; ++index) avsp_alien_ai_step(&alien, &input);
    result("alien-distance-69-misses", !alien.contact);
    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1003, 321, 0);
    alien_to_attack(&alien, &input);
    for (index = 0; index < 48; ++index) avsp_alien_ai_step(&alien, &input);
    result("alien-different-floor-misses", !alien.contact);

    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1100, 321, 0);
    alien_to_attack(&alien, &input);
    for (index = 0; index < 120; ++index) avsp_alien_ai_step(&alien, &input);
    result("alien-above-lane-state", alien.source_action == 0x0600u &&
           alien.facing == 0 && alien.assembly == 0x0012FAE8UL);
    result("alien-rng-timer", avsp_alien_ai_rng_step(0x7301u) == 0x595au &&
           avsp_alien_ai_timer_for_seed(0x595au) == 120u &&
           avsp_alien_ai_timer_for_seed(0x0001u) == 30u);

    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1000, 320, 24);
    avsp_alien_ai_step(&alien, &input);
    input.incoming_damage = 0;
    result("alien-hit-state", alien.state == AVSP_ALIEN_STATE_HIT &&
           alien.health == 63 && alien.animation_record == 0x0012DD50UL &&
           alien.assembly == 0x00130248UL);
    for (index = 0; index < 38; ++index) avsp_alien_ai_step(&alien, &input);
    result("alien-hit-recovery", alien.state == AVSP_ALIEN_STATE_APPROACH &&
           alien.source_action == 0x1A00u && alien.facing == 0);

    avsp_alien_ai_init(&alien, 0x7301u);
    input = alien_input(1000, 320, 100);
    avsp_alien_ai_step(&alien, &input);
    input.incoming_damage = 0;
    result("alien-ko-state", alien.state == AVSP_ALIEN_STATE_KO &&
           alien.health < 0 && alien.assembly == 0x0013020CUL);
    for (index = 0; index < 140; ++index) avsp_alien_ai_step(&alien, &input);
    result("alien-ko-removal", alien.state == AVSP_ALIEN_STATE_INACTIVE &&
           alien.removed == 1u);
}

static int near_target(const AvspLiveEncounterRuntime *runtime)
{
    int dx = runtime->alien.x - runtime->player.x;
    int dz = runtime->alien.lane - runtime->player.lane;
    if (dx < 0) dx = -dx;
    if (dz < 0) dz = -dz;
    return dx <= 52 && dz <= 6;
}

static unsigned short policy(AvspLiveEncounterRuntime *runtime,
                             int *phase, int *release)
{
    unsigned short mask = 0u;
    if (*release)
    {
        *release = 0;
        return 0u;
    }
    if (runtime->route_unlocked) return AVSP_PW_INPUT_RIGHT;
    if (*phase == 0)
    {
        if (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_WAIT_ENTRY)
            return AVSP_PW_INPUT_RIGHT;
        *phase = 1;
    }
    if (*phase == 1)
    {
        if (runtime->alien_contacts == 0UL) return 0u;
        *phase = 2;
    }
    if (*phase == 2)
    {
        if (runtime->player.x > 914) return AVSP_PW_INPUT_LEFT;
        if (avsp_pw_can_control(&runtime->player))
        {
            *phase = 3;
            *release = 1;
            return AVSP_PW_INPUT_ATTACK;
        }
        return 0u;
    }
    if (runtime->player.state != AVSP_PW_STATE_CONTROL) return 0u;
    if (runtime->player.x < runtime->alien.x - 42)
        mask |= AVSP_PW_INPUT_RIGHT;
    else if (runtime->player.x > runtime->alien.x + 42)
        mask |= AVSP_PW_INPUT_LEFT;
    if (runtime->player.lane < runtime->alien.lane - 4)
        mask |= AVSP_PW_INPUT_UP;
    else if (runtime->player.lane > runtime->alien.lane + 4)
        mask |= AVSP_PW_INPUT_DOWN;
    if (near_target(runtime))
    {
        *release = 1;
        return AVSP_PW_INPUT_ATTACK;
    }
    return mask;
}

static void emit_replay(void)
{
    AvspLiveEncounterRuntime runtime;
    AvspLiveEncounterFrame frame;
    AvspLiveEncounterInput input;
    int phase = 0;
    int release = 0;
    int index;
    avsp_live_encounter_init(&runtime);
    for (index = 0; index <= 470; ++index)
    {
        input.frame = runtime.frame;
        input.player_mask = policy(&runtime, &phase, &release);
        if (!avsp_live_encounter_step(&runtime, &input, &frame))
        {
            ++failures;
            return;
        }
        printf("FRAME,%lu,%u,%d,%d,%d,%u,%u,%u,%d,%lu,%lu,%d,"
               "%d,%d,%d,%u,%u,%u,%d,%lu,%lu,%d,%u,%u,%u,%u,%u,"
               "%u,%u,%u,%u,%d,%lu\n",
               frame.frame, frame.input_mask, frame.player.x,
               frame.player.lane, frame.player.health, frame.player.state,
               frame.player.selector, frame.player.attack_active,
               frame.player.facing, frame.player.animation_record,
               frame.player.assembly, frame.player_screen_y, frame.alien.x,
               frame.alien.lane, frame.alien.health, frame.alien.state,
               frame.alien.inner_state, frame.alien.source_action,
               frame.alien.facing, frame.alien.animation_record,
               frame.alien.assembly, frame.alien_screen_y,
               frame.alien.rng_seed, frame.player_contact,
               frame.alien_contact, frame.player_damage, frame.alien_damage,
               frame.attack_miss, frame.encounter_state,
               frame.route_unlocked, frame.continued_after_unlock,
               frame.camera_world_x, runtime.failures);
    }
}

int main(void)
{
    navigation_matrix();
    player_matrix();
    alien_matrix();
    result("clear-authority", !avsp_live_encounter_clear_allowed(
               0u, 0u, 1u, 1u) && !avsp_live_encounter_clear_allowed(
               1u, 0u, 1u, 1u) && avsp_live_encounter_clear_allowed(
               1u, 1u, 0u, 0u));
    emit_replay();
    return failures == 0 ? 0 : 1;
}
