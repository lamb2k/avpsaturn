#ifndef AVSP_COMBAT_INTEGRATION_DIAGNOSTIC_H
#define AVSP_COMBAT_INTEGRATION_DIAGNOSTIC_H

#include "../../../../src/port_v2/integration/combat/combat.h"

#define AVSP_COMBAT_DIAGNOSTIC_INTERFACE_VERSION 1

extern volatile int avsp_diag_combat_interface_version;
extern volatile int avsp_diag_combat_frame;
extern volatile int avsp_diag_combat_source_sample;
extern volatile int avsp_diag_combat_event_kind;
extern volatile int avsp_diag_combat_attack_selector;
extern volatile int avsp_diag_combat_contact_count;
extern volatile int avsp_diag_combat_damage_count;
extern volatile int avsp_diag_combat_enemy_health;
extern volatile int avsp_diag_combat_hit_count;
extern volatile int avsp_diag_combat_ko_count;
extern volatile int avsp_diag_combat_event_count;
extern volatile int avsp_diag_combat_event_samples[4];
extern volatile int avsp_diag_combat_event_kinds[4];
extern volatile int avsp_diag_combat_event_selectors[4];
extern volatile int avsp_diag_combat_event_hit_values[4];
extern volatile int avsp_diag_combat_event_health_before[4];
extern volatile int avsp_diag_combat_event_health_after[4];
extern volatile int avsp_diag_combat_transition_state;
extern volatile int avsp_diag_combat_transition_sub_state;
extern volatile int avsp_diag_combat_transition_action;
extern volatile unsigned long avsp_diag_combat_transition_anim_record;
extern volatile int avsp_diag_combat_transition_timer;
extern volatile int avsp_diag_combat_transition_hit_value;
extern volatile int avsp_diag_combat_player_attack_active;
extern volatile int avsp_diag_combat_player_action_frame;
extern volatile int avsp_diag_combat_enemy_visual_action;
extern volatile int avsp_diag_combat_enemy_action_frame;
extern volatile int avsp_diag_combat_negative_rejections;
extern volatile int avsp_diag_combat_failures;
extern volatile int avsp_diag_combat_complete;
extern volatile int avsp_diag_combat_canary_ok;
extern volatile int avsp_diag_combat_player_x;
extern volatile int avsp_diag_combat_player_lane;
extern volatile int avsp_diag_combat_player_height;
extern volatile int avsp_diag_combat_player_facing;
extern volatile int avsp_diag_combat_enemy_x;
extern volatile int avsp_diag_combat_enemy_lane;
extern volatile int avsp_diag_combat_enemy_height;
extern volatile int avsp_diag_combat_enemy_facing;
extern volatile int avsp_diag_combat_baseline_delta;
extern volatile int avsp_diag_combat_attack_toward_target;
extern volatile int avsp_diag_combat_alignment_ok;

int avsp_combat_diagnostic_init(AvspPortV2CombatRuntime *runtime);
void avsp_combat_diagnostic_step(AvspPortV2CombatRuntime *runtime);

#endif
