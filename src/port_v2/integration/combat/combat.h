#ifndef AVSP_PORT_V2_COMBAT_H
#define AVSP_PORT_V2_COMBAT_H

#include "../player_enemy/player_enemy.h"
#include "../../combat/hit_ko/hit_ko.h"

#define AVSP_PORT_V2_COMBAT_INTERFACE_VERSION 1
#define AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT 4

#define AVSP_PORT_V2_COMBAT_PLAYER_TABLE_SET 0x0011AE02UL
#define AVSP_PORT_V2_COMBAT_ENEMY_TABLE_SET 0x00130AC8UL
#define AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR 1
#define AVSP_PORT_V2_COMBAT_SOURCE_VIEW_WIDTH 384
#define AVSP_PORT_V2_COMBAT_TARGET_VIEW_WIDTH 352
#define AVSP_PORT_V2_COMBAT_ENEMY_ANCHOR_X 160
#define AVSP_PORT_V2_COMBAT_ENEMY_ANCHOR_LANE 200
#define AVSP_PORT_V2_COMBAT_BASELINE_DELTA_LIMIT 8

typedef enum
{
    AVSP_PORT_V2_COMBAT_EVENT_NONE = 0,
    AVSP_PORT_V2_COMBAT_EVENT_CONTACT_MISS = 1,
    AVSP_PORT_V2_COMBAT_EVENT_DAMAGE = 2,
    AVSP_PORT_V2_COMBAT_EVENT_HIT = 3,
    AVSP_PORT_V2_COMBAT_EVENT_KO = 4
} AvspPortV2CombatEventKind;

typedef struct
{
    unsigned short source_sample;
    unsigned short attack_selector;
    unsigned short hit_value;
    short health_before;
    short health_after;
    int player_x;
    int player_y;
    int player_z;
    int enemy_x;
    int enemy_y;
    int enemy_z;
    unsigned short player_facing;
    unsigned short enemy_facing;
    unsigned short transition_kind;
} AvspPortV2CombatSourceEvent;

typedef struct
{
    unsigned short source_sample;
    int player_x;
    int player_lane;
    int player_height;
    int player_facing;
    int player_attack_direction;
    int enemy_x;
    int enemy_lane;
    int enemy_height;
    int enemy_facing;
    int baseline_delta;
} AvspPortV2CombatPresentation;

typedef struct
{
    unsigned short source_sample;
    unsigned short attack_selector;
    unsigned short enemy_hurt_selector;
    unsigned short player_facing;
    unsigned short enemy_facing;
    int player_x;
    int player_y;
    int player_z;
    int enemy_x;
    int enemy_y;
    int enemy_z;
} AvspPortV2CombatContactInput;

typedef struct
{
    unsigned short kind;
    unsigned short source_sample;
    unsigned short attack_selector;
    unsigned short contact;
    unsigned short guarded;
    unsigned short hit_value;
    short health_before;
    short health_after;
} AvspPortV2CombatEvent;

typedef struct
{
    AvspPortV2PlayerEnemyRuntime presentation;
    AvspPortV2HitKoRuntime transition;
    short enemy_health;
    unsigned short contact_count;
    unsigned short damage_count;
    unsigned short hit_count;
    unsigned short ko_count;
    unsigned short rejected_count;
} AvspPortV2CombatRuntime;

void avsp_port_v2_combat_init(AvspPortV2CombatRuntime *runtime);
int avsp_port_v2_combat_source_event(
    int index, AvspPortV2CombatSourceEvent *event);
int avsp_port_v2_combat_presentation(
    const AvspPortV2CombatSourceEvent *source,
    AvspPortV2CombatPresentation *presentation);
int avsp_port_v2_combat_alignment_valid(
    const AvspPortV2CombatPresentation *presentation);
int avsp_port_v2_combat_apply_contact(
    AvspPortV2CombatRuntime *runtime,
    const AvspPortV2CombatContactInput *input,
    AvspPortV2CombatEvent *event);
int avsp_port_v2_combat_step_transition(AvspPortV2CombatRuntime *runtime);
int avsp_port_v2_combat_approval_locks_valid(void);

#endif
