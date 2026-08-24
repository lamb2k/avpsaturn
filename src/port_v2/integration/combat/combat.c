#include <string.h>

#include "combat.h"
#include "source_player_generated.h"
#include "../../../../avsp_actor.h"
#include "../../../../avsp_collision.h"

static const AvspPortV2CombatSourceEvent source_events[
    AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT] =
{
    {5190u, 5185u, 5187u, 5205u, 5189u, 5199u, 5191u, 5227u,
     1u, 8u, 87, 63, 1360, 319, 319, 1304, 311, 311, 0u, 1u,
     AVSP_PORT_V2_HIT_KO_HIT, 1538u, 512u, 0x001600F8UL,
     0x0012EB4CUL, 0x0012DD50UL,
     1317755716UL, 3976238547UL, 2331368752UL, 1791278282UL, 19u},
    {5236u, 5230u, 5232u, 5250u, 5235u, 5244u, 5237u, 5277u,
     2u, 8u, 63, 39, 1360, 319, 319, 1286, 311, 311, 0u, 1u,
     AVSP_PORT_V2_HIT_KO_NONE, 1538u, 512u, 0x0016014CUL,
     0x0012EB1CUL, 0x0012DD28UL,
     3410836603UL, 2394891641UL, 2546903006UL, 230372650UL, 19u},
    {5283u, 5275u, 5277u, 5300u, 5282u, 5294u, 5284u, 5322u,
     3u, 10u, 39, 8, 1360, 319, 319, 1248, 311, 311, 0u, 1u,
     AVSP_PORT_V2_HIT_KO_NONE, 1538u, 512u, 0x001601C0UL,
     0x0012EB0CUL, 0x0012DD3CUL,
     2761335286UL, 130878419UL, 2176011357UL, 3820751445UL, 19u},
    {5329u, 5320u, 5322u, 5352u, 5328u, 5343u, 5330u, 5469u,
     4u, 12u, 8, -1, 1360, 332, 319, 1231, 311, 311, 0u, 1u,
     AVSP_PORT_V2_HIT_KO_KO, 1542u, 512u, 0x00160234UL,
     0x0012EB1CUL, 0x0012E214UL,
     3410836603UL, 2394891641UL, 2546903006UL, 230372650UL, 19u}
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

int avsp_port_v2_combat_source_player_frame(
    const int event_index, const int action_frame,
    AvspPortV2PlayerCombatPresentation *presentation)
{
    const AvspPortV2CombatSourceEvent *source;
    int source_sample;
    if (presentation == 0 || event_index < 0 ||
        event_index >= AVSP_SOURCE_COMBAT_PLAYER_CLIPS || action_frame < 0 ||
        action_frame >= avsp_source_combat_player_frame_counts[event_index])
        return 0;
    source = &source_events[event_index];
    source_sample = source->player_presentation_start + action_frame;
    memset(presentation, 0, sizeof(*presentation));
    presentation->sequence_step = (unsigned short)(event_index + 1);
    presentation->attack_selector = source->attack_selector;
    presentation->source_action =
        avsp_source_combat_player_actions[event_index][action_frame];
    presentation->source_substate =
        avsp_source_combat_player_substates[event_index][action_frame];
    presentation->source_animation_record =
        avsp_source_combat_player_records[event_index][action_frame];
    presentation->source_object_identity =
        avsp_source_combat_player_object_identity[event_index][action_frame];
    presentation->source_tile_identity =
        avsp_source_combat_player_tile_identity[event_index][action_frame];
    presentation->pose_index =
        avsp_source_combat_player_poses[event_index][action_frame];
    presentation->action_frame = (unsigned short)action_frame;
    presentation->pivot_x =
        avsp_source_combat_player_pivot_x[event_index][action_frame];
    presentation->pivot_y =
        avsp_source_combat_player_pivot_y[event_index][action_frame];
    presentation->height =
        avsp_source_combat_player_heights[event_index][action_frame];
    presentation->attack_active = (unsigned short)
        (source_sample >= source->attack_active_start &&
         source_sample <= source->attack_active_end);
    return avsp_port_v2_combat_source_player_frame_valid(
        event_index, action_frame, presentation);
}

int avsp_port_v2_combat_source_player_frame_valid(
    const int event_index, const int action_frame,
    const AvspPortV2PlayerCombatPresentation *presentation)
{
    const AvspPortV2CombatSourceEvent *source;
    int source_sample;
    if (!avsp_port_v2_player_combat_presentation_valid(presentation) ||
        event_index < 0 || event_index >= AVSP_SOURCE_COMBAT_PLAYER_CLIPS ||
        action_frame < 0 ||
        action_frame >= avsp_source_combat_player_frame_counts[event_index])
        return 0;
    source = &source_events[event_index];
    source_sample = source->player_presentation_start + action_frame;
    return presentation->sequence_step == (unsigned short)(event_index + 1) &&
           presentation->attack_selector == source->attack_selector &&
           presentation->source_action ==
               avsp_source_combat_player_actions[event_index][action_frame] &&
           presentation->source_substate ==
               avsp_source_combat_player_substates[event_index][action_frame] &&
           presentation->source_animation_record ==
               avsp_source_combat_player_records[event_index][action_frame] &&
           presentation->source_object_identity ==
               avsp_source_combat_player_object_identity[
                   event_index][action_frame] &&
           presentation->source_tile_identity ==
               avsp_source_combat_player_tile_identity[
                   event_index][action_frame] &&
           presentation->pose_index ==
               avsp_source_combat_player_poses[event_index][action_frame] &&
           presentation->pivot_x ==
               avsp_source_combat_player_pivot_x[event_index][action_frame] &&
           presentation->pivot_y ==
               avsp_source_combat_player_pivot_y[event_index][action_frame] &&
           presentation->height ==
               avsp_source_combat_player_heights[event_index][action_frame] &&
           presentation->attack_active == (unsigned short)
               (source_sample >= source->attack_active_start &&
                source_sample <= source->attack_active_end);
}

int avsp_port_v2_combat_source_enemy_frame(
    const int event_index, const int action_frame,
    AvspPortV2CombatEnemyPresentation *presentation)
{
    const AvspPortV2CombatSourceEvent *source;
    if (presentation == 0 || event_index < 0 ||
        event_index >= AVSP_SOURCE_COMBAT_PLAYER_CLIPS || action_frame < 0 ||
        action_frame >= avsp_source_combat_enemy_frame_counts[event_index])
        return 0;
    source = &source_events[event_index];
    memset(presentation, 0, sizeof(*presentation));
    presentation->source_sample = (unsigned short)
        (source->enemy_reaction_start + action_frame);
    presentation->source_action =
        avsp_source_combat_enemy_actions[event_index][action_frame];
    presentation->source_substate =
        avsp_source_combat_enemy_substates[event_index][action_frame];
    presentation->palette =
        avsp_source_combat_enemy_palettes[event_index][action_frame];
    presentation->action_frame = (unsigned short)action_frame;
    presentation->facing =
        avsp_source_combat_enemy_facing[event_index][action_frame];
    presentation->source_animation_record =
        avsp_source_combat_enemy_records[event_index][action_frame];
    presentation->source_object_identity =
        avsp_source_combat_enemy_object_identity[event_index][action_frame];
    presentation->source_tile_identity =
        avsp_source_combat_enemy_tile_identity[event_index][action_frame];
    presentation->world_x =
        avsp_source_combat_enemy_world_x[event_index][action_frame];
    presentation->world_y =
        avsp_source_combat_enemy_world_y[event_index][action_frame];
    presentation->world_z =
        avsp_source_combat_enemy_world_z[event_index][action_frame];
    return avsp_port_v2_combat_source_enemy_frame_valid(
        event_index, action_frame, presentation);
}

int avsp_port_v2_combat_source_enemy_frame_valid(
    const int event_index, const int action_frame,
    const AvspPortV2CombatEnemyPresentation *presentation)
{
    const AvspPortV2CombatSourceEvent *source;
    if (presentation == 0 || event_index < 0 ||
        event_index >= AVSP_SOURCE_COMBAT_PLAYER_CLIPS || action_frame < 0 ||
        action_frame >= avsp_source_combat_enemy_frame_counts[event_index])
        return 0;
    source = &source_events[event_index];
    return presentation->source_sample == (unsigned short)
               (source->enemy_reaction_start + action_frame) &&
           presentation->source_action ==
               avsp_source_combat_enemy_actions[event_index][action_frame] &&
           presentation->source_substate ==
               avsp_source_combat_enemy_substates[event_index][action_frame] &&
           presentation->palette ==
               avsp_source_combat_enemy_palettes[event_index][action_frame] &&
           presentation->facing ==
               avsp_source_combat_enemy_facing[event_index][action_frame] &&
           presentation->source_animation_record ==
               avsp_source_combat_enemy_records[event_index][action_frame] &&
           presentation->source_object_identity ==
               avsp_source_combat_enemy_object_identity[
                   event_index][action_frame] &&
           presentation->source_tile_identity ==
               avsp_source_combat_enemy_tile_identity[
                   event_index][action_frame] &&
           presentation->world_x ==
               avsp_source_combat_enemy_world_x[event_index][action_frame] &&
           presentation->world_y ==
               avsp_source_combat_enemy_world_y[event_index][action_frame] &&
           presentation->world_z ==
               avsp_source_combat_enemy_world_z[event_index][action_frame];
}

int avsp_port_v2_combat_source_enemy_sample(
    const int source_sample, AvspPortV2CombatEnemyPresentation *presentation)
{
    int index;
    if (presentation == 0 ||
        source_sample < AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FIRST ||
        source_sample > AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_LAST)
        return 0;
    index = source_sample - AVSP_SOURCE_COMBAT_ENEMY_TIMELINE_FIRST;
    memset(presentation, 0, sizeof(*presentation));
    presentation->source_sample = (unsigned short)source_sample;
    presentation->source_action =
        avsp_source_combat_enemy_timeline_actions[index];
    presentation->source_substate =
        avsp_source_combat_enemy_timeline_substates[index];
    presentation->palette =
        avsp_source_combat_enemy_timeline_palettes[index];
    presentation->action_frame = (unsigned short)index;
    presentation->facing =
        avsp_source_combat_enemy_timeline_facing[index];
    presentation->source_animation_record =
        avsp_source_combat_enemy_timeline_records[index];
    presentation->source_object_identity =
        avsp_source_combat_enemy_timeline_object_identity[index];
    presentation->source_tile_identity =
        avsp_source_combat_enemy_timeline_tile_identity[index];
    presentation->world_x =
        avsp_source_combat_enemy_timeline_world_x[index];
    presentation->world_y =
        avsp_source_combat_enemy_timeline_world_y[index];
    presentation->world_z =
        avsp_source_combat_enemy_timeline_world_z[index];
    return presentation->source_animation_record != 0UL &&
           presentation->source_object_identity != 0UL &&
           presentation->source_tile_identity != 0UL;
}

static int scale_horizontal_delta(const int delta)
{
    if (delta < 0)
        return -((-delta * AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH) /
                 AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH);
    return (delta * AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH) /
        AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH;
}

int avsp_port_v2_combat_presentation(
    const AvspPortV2CombatSourceEvent *source,
    AvspPortV2CombatPresentation *presentation)
{
    int player_height;
    int enemy_height;
    if (source == 0 || presentation == 0) return 0;
    player_height = source->player_y - source->player_z;
    enemy_height = source->enemy_y - source->enemy_z;
    if (player_height < 0 || enemy_height < 0) return 0;
    memset(presentation, 0, sizeof(*presentation));
    presentation->source_sample = source->source_sample;
    presentation->player_x = AVSP_PORT_V2_COMBAT_PLAYER_ANCHOR_X;
    presentation->enemy_x = presentation->player_x -
        scale_horizontal_delta(source->player_x - source->enemy_x);
    presentation->player_lane = AVSP_PORT_V2_COMBAT_PLAYER_ANCHOR_LANE;
    presentation->enemy_lane = presentation->player_lane -
        (source->player_z - source->enemy_z);
    presentation->player_height = player_height;
    presentation->enemy_height = enemy_height;
    /* The captured player base art faces left at source facing byte zero;
     * CapActor's signed renderer convention uses +1 for that unflipped art. */
    presentation->player_facing = source->player_facing ? -1 : 1;
    presentation->enemy_facing = source->enemy_facing ? -1 : 1;
    presentation->player_attack_direction = source->player_facing ? 1 : -1;
    presentation->baseline_delta =
        (presentation->player_lane - presentation->player_height) -
        (presentation->enemy_lane - presentation->enemy_height);
    return 1;
}

int avsp_port_v2_combat_alignment_valid(
    const AvspPortV2CombatPresentation *presentation)
{
    int target_direction;
    int baseline_delta;
    if (presentation == 0 ||
        presentation->player_x == presentation->enemy_x) return 0;
    target_direction = presentation->enemy_x < presentation->player_x ? -1 : 1;
    baseline_delta = presentation->baseline_delta < 0 ?
        -presentation->baseline_delta : presentation->baseline_delta;
    return presentation->player_attack_direction == target_direction &&
        baseline_delta <= AVSP_PORT_V2_COMBAT_BASELINE_DELTA_LIMIT;
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
