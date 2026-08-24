#include <string.h>

#include "diagnostic.h"

#define AVSP_COMBAT_CANARY_HEAD 0x434D4248UL
#define AVSP_COMBAT_CANARY_TAIL 0x434D4254UL
#define AVSP_COMBAT_SOURCE_BASE_FRAME 5185
#define AVSP_COMBAT_DIAGNOSTIC_LEAD_IN 180

typedef struct
{
    unsigned long head_canary;
    int frame;
    int event_index;
    int last_event_kind;
    int negative_rejections;
    int failures;
    AvspPortV2CombatEvent last_event;
    unsigned long tail_canary;
} AvspCombatDiagnosticState;

static AvspCombatDiagnosticState diagnostic;

static int source_frame(void)
{
    return AVSP_COMBAT_SOURCE_BASE_FRAME + diagnostic.frame -
        AVSP_COMBAT_DIAGNOSTIC_LEAD_IN;
}

static int target_delta(const int source_delta)
{
    if (source_delta < 0)
        return -((-source_delta * AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH) /
                 AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH);
    return (source_delta * AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH) /
        AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH;
}

volatile int avsp_diag_combat_interface_version;
volatile int avsp_diag_combat_frame;
volatile int avsp_diag_combat_source_sample;
volatile int avsp_diag_combat_event_kind;
volatile int avsp_diag_combat_attack_selector;
volatile int avsp_diag_combat_contact_count;
volatile int avsp_diag_combat_damage_count;
volatile int avsp_diag_combat_enemy_health;
volatile int avsp_diag_combat_hit_count;
volatile int avsp_diag_combat_ko_count;
volatile int avsp_diag_combat_event_count;
volatile int avsp_diag_combat_event_samples[4];
volatile int avsp_diag_combat_event_kinds[4];
volatile int avsp_diag_combat_event_selectors[4];
volatile int avsp_diag_combat_event_hit_values[4];
volatile int avsp_diag_combat_event_health_before[4];
volatile int avsp_diag_combat_event_health_after[4];
volatile int avsp_diag_combat_transition_state;
volatile int avsp_diag_combat_transition_sub_state;
volatile int avsp_diag_combat_transition_action;
volatile unsigned long avsp_diag_combat_transition_anim_record;
volatile int avsp_diag_combat_transition_timer;
volatile int avsp_diag_combat_transition_hit_value;
volatile int avsp_diag_combat_player_attack_active;
volatile int avsp_diag_combat_player_presentation_active;
volatile int avsp_diag_combat_player_source_pose;
volatile unsigned long avsp_diag_combat_player_source_anim_record;
volatile int avsp_diag_combat_player_source_action;
volatile int avsp_diag_combat_player_source_substate;
volatile unsigned long avsp_diag_combat_player_source_object_identity;
volatile unsigned long avsp_diag_combat_player_source_tile_identity;
volatile int avsp_diag_combat_player_source_pivot_x;
volatile int avsp_diag_combat_player_source_pivot_y;
volatile int avsp_diag_combat_player_action_frame;
volatile int avsp_diag_combat_enemy_visual_action;
volatile int avsp_diag_combat_enemy_action_frame;
volatile unsigned long avsp_diag_combat_enemy_render_anim_record;
volatile int avsp_diag_combat_enemy_render_palette;
volatile unsigned long avsp_diag_combat_enemy_source_object_identity;
volatile unsigned long avsp_diag_combat_enemy_source_tile_identity;
volatile unsigned long avsp_diag_combat_enemy_render_object_identity;
volatile unsigned long avsp_diag_combat_enemy_render_tile_identity;
volatile int avsp_diag_combat_enemy_render_object_count;
volatile int avsp_diag_combat_enemy_source_event_index;
volatile int avsp_diag_combat_enemy_source_world_x;
volatile int avsp_diag_combat_enemy_source_world_y;
volatile int avsp_diag_combat_enemy_source_world_z;
volatile int avsp_diag_combat_negative_rejections;
volatile int avsp_diag_combat_failures;
volatile int avsp_diag_combat_complete;
volatile int avsp_diag_combat_canary_ok;
volatile int avsp_diag_combat_player_x;
volatile int avsp_diag_combat_player_lane;
volatile int avsp_diag_combat_player_height;
volatile int avsp_diag_combat_player_facing;
volatile int avsp_diag_combat_enemy_x;
volatile int avsp_diag_combat_enemy_lane;
volatile int avsp_diag_combat_enemy_height;
volatile int avsp_diag_combat_enemy_facing;
volatile int avsp_diag_combat_baseline_delta;
volatile int avsp_diag_combat_attack_toward_target;
volatile int avsp_diag_combat_alignment_ok;

static void contact_input(const AvspPortV2CombatSourceEvent *source,
                          AvspPortV2CombatContactInput *input)
{
    memset(input, 0, sizeof(*input));
    input->source_sample = source->source_sample;
    input->attack_selector = source->attack_selector;
    input->enemy_hurt_selector = AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR;
    input->player_facing = source->player_facing;
    input->enemy_facing = source->enemy_facing;
    input->player_x = source->player_x;
    input->player_y = source->player_y;
    input->player_z = source->player_z;
    input->enemy_x = source->enemy_x;
    input->enemy_y = source->enemy_y;
    input->enemy_z = source->enemy_z;
}

static void publish(const AvspPortV2CombatRuntime *runtime)
{
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatPresentation presentation;
    AvspPortV2PlayerCombatPresentation player_presentation;
    AvspPortV2CombatEnemyPresentation enemy_presentation;
    int current_source_frame = source_frame();
    int player_event = -1;
    int reaction_event = -1;
    int enemy_event = -1;
    int index;
    int source_index = diagnostic.event_index > 0 ?
        diagnostic.event_index - 1 : 0;
    avsp_diag_combat_interface_version =
        AVSP_COMBAT_DIAGNOSTIC_INTERFACE_VERSION;
    avsp_diag_combat_source_sample = diagnostic.last_event.source_sample;
    avsp_diag_combat_event_kind = diagnostic.last_event.kind;
    avsp_diag_combat_attack_selector = diagnostic.last_event.attack_selector;
    avsp_diag_combat_contact_count = runtime->contact_count;
    avsp_diag_combat_damage_count = runtime->damage_count;
    avsp_diag_combat_enemy_health = runtime->enemy_health;
    avsp_diag_combat_hit_count = runtime->hit_count;
    avsp_diag_combat_ko_count = runtime->ko_count;
    avsp_diag_combat_transition_state = runtime->transition.actor.state;
    avsp_diag_combat_transition_sub_state = runtime->transition.actor.sub_state;
    avsp_diag_combat_transition_action = runtime->transition.actor.action;
    avsp_diag_combat_transition_anim_record =
        runtime->transition.actor.anim_record;
    avsp_diag_combat_transition_timer = runtime->transition.actor.anim_timer;
    avsp_diag_combat_transition_hit_value = runtime->transition.actor.hit_value;
    for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT; ++index)
    {
        AvspPortV2CombatSourceEvent candidate;
        if (!avsp_port_v2_combat_source_event(index, &candidate)) continue;
        if (current_source_frame >= candidate.player_presentation_start &&
            current_source_frame <= candidate.player_presentation_end)
            player_event = index;
        if (current_source_frame >= candidate.enemy_reaction_start + 1 &&
            current_source_frame <= candidate.enemy_reaction_end + 1)
            reaction_event = index;
    }
    avsp_diag_combat_player_presentation_active = 0;
    avsp_diag_combat_player_attack_active = 0;
    avsp_diag_combat_player_action_frame = -1;
    avsp_diag_combat_player_source_pose = -1;
    avsp_diag_combat_player_source_anim_record = 0;
    avsp_diag_combat_player_source_action = 0;
    avsp_diag_combat_player_source_substate = 0;
    avsp_diag_combat_player_source_object_identity = 0;
    avsp_diag_combat_player_source_tile_identity = 0;
    avsp_diag_combat_player_source_pivot_x = 0;
    avsp_diag_combat_player_source_pivot_y = 0;
    if (player_event >= 0 &&
        avsp_port_v2_combat_source_event(player_event, &source) &&
        avsp_port_v2_combat_source_player_frame(
            player_event,
            current_source_frame - source.player_presentation_start,
            &player_presentation))
    {
        avsp_diag_combat_player_presentation_active = 1;
        avsp_diag_combat_player_attack_active =
            player_presentation.attack_active;
        avsp_diag_combat_player_action_frame =
            player_presentation.action_frame;
        avsp_diag_combat_player_source_pose = player_presentation.pose_index;
        avsp_diag_combat_player_source_anim_record =
            player_presentation.source_animation_record;
        avsp_diag_combat_player_source_action =
            player_presentation.source_action;
        avsp_diag_combat_player_source_substate =
            player_presentation.source_substate;
        avsp_diag_combat_player_source_object_identity =
            player_presentation.source_object_identity;
        avsp_diag_combat_player_source_tile_identity =
            player_presentation.source_tile_identity;
        avsp_diag_combat_player_source_pivot_x = player_presentation.pivot_x;
        avsp_diag_combat_player_source_pivot_y = player_presentation.pivot_y;
        avsp_diag_combat_attack_selector =
            player_presentation.attack_selector;
    }
    avsp_diag_combat_enemy_visual_action = 0;
    avsp_diag_combat_enemy_action_frame = 0;
    avsp_diag_combat_enemy_render_anim_record = 0;
    avsp_diag_combat_enemy_render_palette = 19;
    avsp_diag_combat_enemy_source_object_identity = 0;
    avsp_diag_combat_enemy_source_tile_identity = 0;
    avsp_diag_combat_enemy_source_event_index = -1;
    avsp_diag_combat_enemy_source_world_x = 0;
    avsp_diag_combat_enemy_source_world_y = 0;
    avsp_diag_combat_enemy_source_world_z = 0;
    for (index = 0; index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT; ++index)
    {
        AvspPortV2CombatSourceEvent candidate;
        if (avsp_port_v2_combat_source_event(index, &candidate) &&
            current_source_frame > candidate.source_sample)
            enemy_event = index;
    }
    if (enemy_event < 0) enemy_event = 0;
    if (avsp_port_v2_combat_source_enemy_sample(
            current_source_frame - 1, &enemy_presentation))
    {
        avsp_diag_combat_enemy_visual_action =
            reaction_event == 3 ? 2 : (reaction_event >= 0 ? 1 : 3);
        avsp_diag_combat_enemy_action_frame = enemy_presentation.action_frame;
        avsp_diag_combat_enemy_render_anim_record =
            enemy_presentation.source_animation_record;
        avsp_diag_combat_enemy_render_palette = enemy_presentation.palette;
        avsp_diag_combat_enemy_source_object_identity =
            enemy_presentation.source_object_identity;
        avsp_diag_combat_enemy_source_tile_identity =
            enemy_presentation.source_tile_identity;
        avsp_diag_combat_enemy_source_event_index = enemy_event;
        avsp_diag_combat_enemy_source_world_x = enemy_presentation.world_x;
        avsp_diag_combat_enemy_source_world_y = enemy_presentation.world_y;
        avsp_diag_combat_enemy_source_world_z = enemy_presentation.world_z;
    }
    avsp_diag_combat_negative_rejections = diagnostic.negative_rejections;
    avsp_diag_combat_failures = diagnostic.failures;
    avsp_diag_combat_complete = diagnostic.event_index == 4 &&
        !runtime->transition.active && current_source_frame > 5469;
    avsp_diag_combat_canary_ok =
        diagnostic.head_canary == AVSP_COMBAT_CANARY_HEAD &&
        diagnostic.tail_canary == AVSP_COMBAT_CANARY_TAIL;
    if (player_event >= 0) source_index = player_event;
    if (enemy_event >= 0) source_index = enemy_event;
    if (avsp_port_v2_combat_source_event(source_index, &source) &&
        avsp_port_v2_combat_presentation(&source, &presentation))
    {
        int target_direction;
        presentation.player_height =
            avsp_diag_combat_player_presentation_active ?
            player_presentation.height : 0;
        if (enemy_event >= 0 && avsp_diag_combat_enemy_source_world_x != 0)
        {
            presentation.enemy_x = AVSP_PORT_V2_COMBAT_PLAYER_ANCHOR_X -
                target_delta(1360 -
                             avsp_diag_combat_enemy_source_world_x);
            presentation.enemy_lane =
                AVSP_PORT_V2_COMBAT_PLAYER_ANCHOR_LANE -
                (319 - avsp_diag_combat_enemy_source_world_z);
            presentation.enemy_height =
                avsp_diag_combat_enemy_source_world_y -
                avsp_diag_combat_enemy_source_world_z;
            presentation.enemy_facing = enemy_presentation.facing ? -1 : 1;
            presentation.baseline_delta =
                (presentation.player_lane - presentation.player_height) -
                (presentation.enemy_lane - presentation.enemy_height);
        }
        target_direction = presentation.enemy_x < presentation.player_x ?
            -1 : 1;
        avsp_diag_combat_player_x = presentation.player_x;
        avsp_diag_combat_player_lane = presentation.player_lane;
        avsp_diag_combat_player_height =
            presentation.player_height;
        avsp_diag_combat_player_facing = presentation.player_facing;
        avsp_diag_combat_enemy_x = presentation.enemy_x;
        avsp_diag_combat_enemy_lane = presentation.enemy_lane;
        avsp_diag_combat_enemy_height = presentation.enemy_height;
        avsp_diag_combat_enemy_facing = presentation.enemy_facing;
        avsp_diag_combat_baseline_delta = presentation.baseline_delta;
        avsp_diag_combat_attack_toward_target =
            presentation.player_attack_direction == target_direction;
        avsp_diag_combat_alignment_ok =
            avsp_port_v2_combat_alignment_valid(&presentation);
    }
    else
    {
        avsp_diag_combat_alignment_ok = 0;
        ++diagnostic.failures;
    }
    avsp_diag_combat_frame = diagnostic.frame;
}

static int run_negative_controls(void)
{
    AvspPortV2CombatRuntime runtime;
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput input;
    AvspPortV2CombatEvent event;
    avsp_port_v2_combat_init(&runtime);
    if (!avsp_port_v2_combat_source_event(0, &source)) return 0;
    contact_input(&source, &input);
    input.enemy_x += 256;
    if (avsp_port_v2_combat_apply_contact(&runtime, &input, &event) &&
        event.kind == AVSP_PORT_V2_COMBAT_EVENT_CONTACT_MISS &&
        runtime.enemy_health == 87)
        ++diagnostic.negative_rejections;
    else
        ++diagnostic.failures;
    avsp_port_v2_combat_init(&runtime);
    contact_input(&source, &input);
    input.attack_selector = 2u;
    if (!avsp_port_v2_combat_apply_contact(&runtime, &input, &event))
        ++diagnostic.negative_rejections;
    else
        ++diagnostic.failures;
    return diagnostic.failures == 0 && diagnostic.negative_rejections == 2;
}

int avsp_combat_diagnostic_init(AvspPortV2CombatRuntime *runtime)
{
    if (runtime == 0) return 0;
    memset(&diagnostic, 0, sizeof(diagnostic));
    diagnostic.head_canary = AVSP_COMBAT_CANARY_HEAD;
    diagnostic.tail_canary = AVSP_COMBAT_CANARY_TAIL;
    avsp_port_v2_combat_init(runtime);
    if (!avsp_port_v2_combat_approval_locks_valid())
        ++diagnostic.failures;
    run_negative_controls();
    publish(runtime);
    return diagnostic.failures == 0;
}

static void apply_scheduled_event(AvspPortV2CombatRuntime *runtime)
{
    AvspPortV2CombatSourceEvent source;
    AvspPortV2CombatContactInput input;
    if (!avsp_port_v2_combat_source_event(diagnostic.event_index, &source))
    {
        ++diagnostic.failures;
        return;
    }
    contact_input(&source, &input);
    if (!avsp_diag_combat_player_presentation_active ||
        !avsp_diag_combat_player_attack_active ||
        avsp_diag_combat_attack_selector != source.attack_selector)
    {
        ++diagnostic.failures;
        return;
    }
    if (!avsp_port_v2_combat_apply_contact(
            runtime, &input, &diagnostic.last_event))
        ++diagnostic.failures;
    else
    {
        int index = diagnostic.event_index;
        diagnostic.last_event_kind = diagnostic.last_event.kind;
        ++diagnostic.event_index;
        avsp_diag_combat_event_samples[index] =
            diagnostic.last_event.source_sample;
        avsp_diag_combat_event_kinds[index] = diagnostic.last_event.kind;
        avsp_diag_combat_event_selectors[index] =
            diagnostic.last_event.attack_selector;
        avsp_diag_combat_event_hit_values[index] =
            diagnostic.last_event.hit_value;
        avsp_diag_combat_event_health_before[index] =
            diagnostic.last_event.health_before;
        avsp_diag_combat_event_health_after[index] =
            diagnostic.last_event.health_after;
        avsp_diag_combat_event_count = diagnostic.event_index;
    }
}

void avsp_combat_diagnostic_step(AvspPortV2CombatRuntime *runtime)
{
    AvspPortV2CombatSourceEvent source;
    int current_source_frame;
    if (runtime == 0) return;
    publish(runtime);
    current_source_frame = source_frame();
    if (diagnostic.event_index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT &&
        avsp_port_v2_combat_source_event(diagnostic.event_index, &source) &&
        current_source_frame == source.source_sample)
        apply_scheduled_event(runtime);
    else if (runtime->transition.active &&
             !avsp_port_v2_combat_step_transition(runtime))
        ++diagnostic.failures;
    ++diagnostic.frame;
    publish(runtime);
}
