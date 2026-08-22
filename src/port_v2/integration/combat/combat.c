#include <string.h>

#include "combat.h"
#include "../../../../avsp_actor.h"
#include "../../../../avsp_collision.h"

static const AvspPortV2CombatSourceEvent source_events[
    AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT] =
{
    {5190u, 1u, 8u, 87, 63, 1360, 319, 319, 1304, 311, 311,
     AVSP_PORT_V2_HIT_KO_HIT},
    {5236u, 2u, 8u, 63, 39, 1360, 319, 319, 1286, 311, 311,
     AVSP_PORT_V2_HIT_KO_NONE},
    {5283u, 3u, 10u, 39, 8, 1360, 319, 319, 1248, 311, 311,
     AVSP_PORT_V2_HIT_KO_NONE},
    {5329u, 4u, 12u, 8, -1, 1360, 332, 319, 1231, 311, 311,
     AVSP_PORT_V2_HIT_KO_KO}
};

void avsp_port_v2_combat_init(AvspPortV2CombatRuntime *runtime)
{
    if (runtime == 0) return;
    memset(runtime, 0, sizeof(*runtime));
    avsp_port_v2_player_enemy_init(&runtime->presentation);
    runtime->enemy_health = 87;
}

int avsp_port_v2_combat_source_event(
    const int index, AvspPortV2CombatSourceEvent *event)
{
    if (event == 0 || index < 0 ||
        index >= AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT) return 0;
    *event = source_events[index];
    return 1;
}

static const AvspPortV2CombatSourceEvent *find_source_event(
    const unsigned short sample)
{
    int index;
    for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT; ++index)
    {
        if (source_events[index].source_sample == sample)
            return &source_events[index];
    }
    return 0;
}

static void configure_actor_pair(
    const AvspPortV2CombatContactInput *input,
    AvspActor *attacker, AvspActor *defender)
{
    memset(attacker, 0, sizeof(*attacker));
    memset(defender, 0, sizeof(*defender));
    attacker->state = 1u;
    attacker->table_set = AVSP_PORT_V2_COMBAT_PLAYER_TABLE_SET;
    attacker->sel_attack = (unsigned char)input->attack_selector;
    attacker->facing = (unsigned char)input->player_facing;
    attacker->world_x = (unsigned short)input->player_x;
    attacker->world_y = (unsigned short)input->player_y;
    attacker->world_z = (unsigned short)input->player_z;
    attacker->attacker_id = 155u;
    attacker->latch_index = 0u;
    defender->state = 1u;
    defender->table_set = AVSP_PORT_V2_COMBAT_ENEMY_TABLE_SET;
    defender->sel_hurt = (unsigned char)input->enemy_hurt_selector;
    defender->facing = (unsigned char)input->enemy_facing;
    defender->world_x = (unsigned short)input->enemy_x;
    defender->world_y = (unsigned short)input->enemy_y;
    defender->world_z = (unsigned short)input->enemy_z;
}

static int begin_transition(
    AvspPortV2CombatRuntime *runtime,
    const AvspPortV2CombatSourceEvent *source)
{
    if (source->transition_kind == AVSP_PORT_V2_HIT_KO_NONE) return 1;
    if (runtime->transition.active) return 0;
    if (source->transition_kind == AVSP_PORT_V2_HIT_KO_HIT)
        return avsp_port_v2_hit_ko_begin(
            &runtime->transition, AVSP_PORT_V2_HIT_KO_HIT,
            &avsp_port_v2_hit_source_before);
    return avsp_port_v2_hit_ko_begin(
        &runtime->transition, AVSP_PORT_V2_HIT_KO_KO,
        &avsp_port_v2_ko_source_before);
}

int avsp_port_v2_combat_apply_contact(
    AvspPortV2CombatRuntime *runtime,
    const AvspPortV2CombatContactInput *input,
    AvspPortV2CombatEvent *event)
{
    const AvspPortV2CombatSourceEvent *source;
    AvspActor attacker;
    AvspActor defender;
    unsigned char hit_value;
    int contact;
    int guarded;
    if (runtime == 0 || input == 0 || event == 0) return 0;
    memset(event, 0, sizeof(*event));
    source = find_source_event(input->source_sample);
    if (source == 0 || input->attack_selector != source->attack_selector ||
        input->enemy_hurt_selector != AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR ||
        runtime->enemy_health != source->health_before)
    {
        ++runtime->rejected_count;
        return 0;
    }
    configure_actor_pair(input, &attacker, &defender);
    hit_value = 0u;
    contact = avsp_collision_overlap(&attacker, &defender, &hit_value);
    guarded = avsp_collision_guarded(&attacker, &defender);
    event->source_sample = input->source_sample;
    event->attack_selector = input->attack_selector;
    event->contact = (unsigned short)contact;
    event->guarded = (unsigned short)guarded;
    event->health_before = runtime->enemy_health;
    event->health_after = runtime->enemy_health;
    if (!contact || guarded)
    {
        event->kind = AVSP_PORT_V2_COMBAT_EVENT_CONTACT_MISS;
        return 1;
    }
    if ((unsigned short)hit_value != source->hit_value ||
        !begin_transition(runtime, source))
    {
        ++runtime->rejected_count;
        return 0;
    }
    runtime->enemy_health = source->health_after;
    ++runtime->contact_count;
    ++runtime->damage_count;
    event->hit_value = (unsigned short)hit_value;
    event->health_after = runtime->enemy_health;
    if (source->transition_kind == AVSP_PORT_V2_HIT_KO_HIT)
    {
        event->kind = AVSP_PORT_V2_COMBAT_EVENT_HIT;
        ++runtime->hit_count;
    }
    else if (source->transition_kind == AVSP_PORT_V2_HIT_KO_KO)
    {
        event->kind = AVSP_PORT_V2_COMBAT_EVENT_KO;
        ++runtime->ko_count;
    }
    else
        event->kind = AVSP_PORT_V2_COMBAT_EVENT_DAMAGE;
    return 1;
}

int avsp_port_v2_combat_step_transition(AvspPortV2CombatRuntime *runtime)
{
    if (runtime == 0 || !runtime->transition.active) return 0;
    return avsp_port_v2_hit_ko_step(&runtime->transition);
}

int avsp_port_v2_combat_approval_locks_valid(void)
{
    unsigned long enemy_table_set;
    AvspAttackBox attack;
    return avsp_port_v2_player_enemy_approvals_valid() &&
           avsp_table_set_for_class(AVSP_PORT_V2_ENEMY_CLASS_ID,
                                    &enemy_table_set) &&
           enemy_table_set == AVSP_PORT_V2_COMBAT_ENEMY_TABLE_SET &&
           avsp_collision_attack_box(AVSP_PORT_V2_COMBAT_PLAYER_TABLE_SET,
                                     1u, &attack) &&
           attack.hit_value == 8u;
}
