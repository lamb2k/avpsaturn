#include <stdio.h>
#include <string.h>

#include "../../../../src/port_v2/integration/combat/combat.h"

static int require_true(const int condition, const char *message)
{
    if (condition) return 1;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static void source_input(const AvspPortV2CombatSourceEvent *source,
                         AvspPortV2CombatContactInput *input)
{
    memset(input, 0, sizeof(*input));
    input->source_sample = source->source_sample;
    input->attack_selector = source->attack_selector;
    input->enemy_hurt_selector = AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR;
    input->player_facing = 0u;
    input->enemy_facing = 1u;
    input->player_x = source->player_x;
    input->player_y = source->player_y;
    input->player_z = source->player_z;
    input->enemy_x = source->enemy_x;
    input->enemy_y = source->enemy_y;
    input->enemy_z = source->enemy_z;
}

static int step_until_inactive(AvspPortV2CombatRuntime *runtime)
{
    int steps = 0;
    while (runtime->transition.active && steps < 200)
    {
        if (!avsp_port_v2_combat_step_transition(runtime)) return -1;
        ++steps;
    }
    return steps;
}

static int replay(AvspPortV2CombatRuntime *runtime, int emit)
{
    int index;
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput input;
    AvspPortV2CombatEvent event;
    avsp_port_v2_combat_init(runtime);
    for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT; ++index)
    {
        if (!avsp_port_v2_combat_source_event(index, &source)) return 0;
        source_input(&source, &input);
        if (!avsp_port_v2_combat_apply_contact(runtime, &input, &event))
            return 0;
        if (emit)
            printf("%u,%u,%u,%u,%u,%d,%d\n",
                   event.source_sample, event.attack_selector,
                   event.kind, event.contact, event.hit_value,
                   event.health_before, event.health_after);
        if (runtime->transition.active)
        {
            int steps = step_until_inactive(runtime);
            int expected = event.kind == AVSP_PORT_V2_COMBAT_EVENT_HIT ?
                36 : 139;
            if (steps != expected) return 0;
            if (emit)
                printf("T,%u,%d,%u,%u,%u,%lu,%u,%d,%u\n",
                       event.source_sample, steps,
                       runtime->transition.actor.state,
                       runtime->transition.actor.sub_state,
                       runtime->transition.actor.action,
                       runtime->transition.actor.anim_record,
                       runtime->transition.actor.anim_timer,
                       runtime->transition.actor.health,
                       runtime->transition.actor.hit_value);
        }
    }
    return 1;
}

static int test_presentation_lock(void)
{
    AvspPortV2CombatRuntime runtime;
    AvspPortV2PlayerEnemyInput input;
    AvspPortV2PlayerEnemyView view;
    int frame;
    memset(&input, 0, sizeof(input));
    avsp_port_v2_combat_init(&runtime);
    for (frame = 0; frame < 260; ++frame)
    {
        input.player.right = frame >= 4 && frame < 12;
        input.player.down = frame >= 16 && frame < 22;
        input.player.left = frame >= 24 && frame < 29;
        input.enemy_translated = (frame % 240) >= 120;
        avsp_port_v2_player_enemy_step(&runtime.presentation, &input);
    }
    avsp_port_v2_player_enemy_view(&runtime.presentation, &view);
    return view.actor_count == 2 && view.player.world_x == 198 &&
           view.player.lane == 184 && view.player.render_layers == 2 &&
           view.enemy.class_id == 31 && view.enemy.palette_bank == 17 &&
           view.enemy.world_x == 192 && view.enemy.locomotion_frame == 19 &&
           view.render_command_count == 34 &&
           avsp_port_v2_player_enemy_render_order_valid(
               view.render_order, view.actor_count);
}

static int test_no_contact(void)
{
    AvspPortV2CombatRuntime runtime;
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput input;
    AvspPortV2CombatEvent event;
    avsp_port_v2_combat_init(&runtime);
    if (!avsp_port_v2_combat_source_event(0, &source)) return 0;
    source_input(&source, &input);
    input.enemy_x += 256;
    return avsp_port_v2_combat_apply_contact(&runtime, &input, &event) &&
           event.kind == AVSP_PORT_V2_COMBAT_EVENT_CONTACT_MISS &&
           event.contact == 0u && runtime.enemy_health == 87 &&
           runtime.damage_count == 0u;
}

static int test_wrong_selector(void)
{
    AvspPortV2CombatRuntime runtime;
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput input;
    AvspPortV2CombatEvent event;
    avsp_port_v2_combat_init(&runtime);
    if (!avsp_port_v2_combat_source_event(0, &source)) return 0;
    source_input(&source, &input);
    input.attack_selector = 2u;
    return !avsp_port_v2_combat_apply_contact(&runtime, &input, &event) &&
           runtime.rejected_count == 1u;
}

int main(const int argc, char **argv)
{
    AvspPortV2CombatRuntime first;
    AvspPortV2CombatRuntime second;
    const int negative = argc == 2 &&
        strcmp(argv[1], "--negative-control") == 0;
    if (!require_true(avsp_port_v2_combat_approval_locks_valid(),
                      "approved combat dependencies drifted")) return 1;
    if (!require_true(replay(&first, 1), "combat replay failed")) return 1;
    if (!require_true(replay(&second, 0), "combat repeat failed")) return 1;
    if (!require_true(memcmp(&first, &second, sizeof(first)) == 0,
                      "combat deterministic repeat drifted")) return 1;
    if (!require_true(first.enemy_health == -1 &&
                      first.contact_count == 4u &&
                      first.damage_count == 4u &&
                      first.hit_count == 1u && first.ko_count == 1u &&
                      first.rejected_count == 0u,
                      "combat final state drifted")) return 1;
    if (!require_true(test_presentation_lock(),
                      "approved actor presentation regressed")) return 1;
    if (negative &&
        (!require_true(test_no_contact(),
                       "no-contact control applied damage") ||
         !require_true(test_wrong_selector(),
                       "wrong-selector control was accepted"))) return 1;
    puts(negative ? "Combat integration negative controls: PASS" :
                    "Combat integration contract: PASS");
    return 0;
}
