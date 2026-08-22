#include <string.h>

#include "diagnostic.h"

#define AVSP_COMBAT_CANARY_HEAD 0x434D4248UL
#define AVSP_COMBAT_CANARY_TAIL 0x434D4254UL
#define AVSP_COMBAT_FIRST_EVENT_FRAME 180
#define AVSP_COMBAT_EVENT_PERIOD 180
#define AVSP_COMBAT_PLAYER_ATTACK_LEAD 4
#define AVSP_COMBAT_PLAYER_ATTACK_FRAMES 24

typedef struct
{
    unsigned long head_canary;
    int frame;
    int event_index;
    int player_attack_frame;
    int enemy_action_frame;
    int last_event_kind;
    int negative_rejections;
    int failures;
    AvspPortV2CombatEvent last_event;
    unsigned long tail_canary;
} AvspCombatDiagnosticState;

static AvspCombatDiagnosticState diagnostic;

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
volatile int avsp_diag_combat_player_action_frame;
volatile int avsp_diag_combat_enemy_visual_action;
volatile int avsp_diag_combat_enemy_action_frame;
volatile int avsp_diag_combat_negative_rejections;
volatile int avsp_diag_combat_failures;
volatile int avsp_diag_combat_complete;
volatile int avsp_diag_combat_canary_ok;

static void contact_input(const AvspPortV2CombatSourceEvent *source,
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

static void publish(const AvspPortV2CombatRuntime *runtime)
{
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
    avsp_diag_combat_player_attack_active =
        diagnostic.player_attack_frame >= 0 &&
        diagnostic.player_attack_frame < AVSP_COMBAT_PLAYER_ATTACK_FRAMES;
    avsp_diag_combat_player_action_frame = diagnostic.player_attack_frame;
    avsp_diag_combat_enemy_visual_action =
        diagnostic.last_event_kind == AVSP_PORT_V2_COMBAT_EVENT_KO ? 2 :
        (runtime->transition.active &&
         diagnostic.last_event_kind == AVSP_PORT_V2_COMBAT_EVENT_HIT ? 1 : 0);
    avsp_diag_combat_enemy_action_frame = diagnostic.enemy_action_frame;
    avsp_diag_combat_negative_rejections = diagnostic.negative_rejections;
    avsp_diag_combat_failures = diagnostic.failures;
    avsp_diag_combat_complete = diagnostic.event_index == 4 &&
        !runtime->transition.active && diagnostic.frame >= 440;
    avsp_diag_combat_canary_ok =
        diagnostic.head_canary == AVSP_COMBAT_CANARY_HEAD &&
        diagnostic.tail_canary == AVSP_COMBAT_CANARY_TAIL;
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
    diagnostic.player_attack_frame = -1;
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
    if (!avsp_port_v2_combat_apply_contact(
            runtime, &input, &diagnostic.last_event))
        ++diagnostic.failures;
    else
    {
        int index = diagnostic.event_index;
        diagnostic.last_event_kind = diagnostic.last_event.kind;
        diagnostic.enemy_action_frame = 0;
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
    int scheduled;
    if (runtime == 0) return;
    scheduled = AVSP_COMBAT_FIRST_EVENT_FRAME +
        diagnostic.event_index * AVSP_COMBAT_EVENT_PERIOD;
    if (diagnostic.event_index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT &&
        diagnostic.frame == scheduled - AVSP_COMBAT_PLAYER_ATTACK_LEAD)
        diagnostic.player_attack_frame = 0;
    if (diagnostic.event_index < AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT &&
        diagnostic.frame == scheduled)
        apply_scheduled_event(runtime);
    else if (runtime->transition.active &&
             !avsp_port_v2_combat_step_transition(runtime))
        ++diagnostic.failures;
    if (diagnostic.player_attack_frame >= 0)
    {
        ++diagnostic.player_attack_frame;
        if (diagnostic.player_attack_frame >= AVSP_COMBAT_PLAYER_ATTACK_FRAMES)
            diagnostic.player_attack_frame = -1;
    }
    if (runtime->transition.active ||
        diagnostic.last_event_kind == AVSP_PORT_V2_COMBAT_EVENT_KO)
        ++diagnostic.enemy_action_frame;
    ++diagnostic.frame;
    publish(runtime);
}
