#ifndef AVSP_PORT_V2_LIVE_ENCOUNTER_H
#define AVSP_PORT_V2_LIVE_ENCOUNTER_H

#include "../../gameplay/player_action/player_action.h"
#include "../../gameplay/street_alien_ai/street_alien_ai.h"
#include "../../combat/hit_ko/hit_ko.h"

#define AVSP_LIVE_ENCOUNTER_INTERFACE_VERSION 2
#define AVSP_LIVE_ENCOUNTER_SPEC01_SHA256 \
    "a8a8d5ff06d70a8df4cc7687928e0eb5200927ac8901adb3eb76745c4b42bd0f"
#define AVSP_LIVE_ENCOUNTER_CANARY_HEAD 0x4C564844UL
#define AVSP_LIVE_ENCOUNTER_CANARY_TAIL 0x4C56544CUL
#define AVSP_LIVE_ENCOUNTER_APERTURE_ORIGIN_X (-176)
#define AVSP_LIVE_ENCOUNTER_ENTRY_X 1003
#define AVSP_LIVE_ENCOUNTER_PLAYER_X 978
#define AVSP_LIVE_ENCOUNTER_PLAYER_LANE 320
#define AVSP_LIVE_ENCOUNTER_ALIEN_X 960
#define AVSP_LIVE_ENCOUNTER_ALIEN_LANE 343
#define AVSP_LIVE_ENCOUNTER_CAMERA_LOCK_X 768
#define AVSP_LIVE_ENCOUNTER_WORLD_Z_ANCHOR 319
#define AVSP_LIVE_ENCOUNTER_SCREEN_Y_ANCHOR 178

#define AVSP_LIVE_ENCOUNTER_WAIT_ENTRY 0u
#define AVSP_LIVE_ENCOUNTER_ACTIVE 1u
#define AVSP_LIVE_ENCOUNTER_CLEARED 2u

typedef struct
{
    unsigned long frame;
    unsigned short player_mask;
} AvspLiveEncounterInput;

typedef struct
{
    unsigned long head_canary;
    AvspPwRuntime player;
    AvspAlienRuntime alien;
    AvspPortV2HitKoRuntime alien_transition;
    unsigned long frame;
    unsigned short encounter_state;
    unsigned short target_ko_observed;
    unsigned short route_unlocked;
    unsigned short continued_after_unlock;
    unsigned short attack_latched;
    unsigned short pending_player_damage;
    unsigned short last_attack_selector;
    unsigned short reaction_elapsed;
    short camera_world_x;
    short unlock_player_x;
    unsigned long player_attack_edges;
    unsigned long player_misses;
    unsigned long player_contacts;
    unsigned long alien_contacts;
    unsigned long player_damage_events;
    unsigned long alien_damage_events;
    unsigned long hit_events;
    unsigned long ko_events;
    unsigned long clear_events;
    unsigned long fallback_count;
    unsigned long failures;
    unsigned long tail_canary;
} AvspLiveEncounterRuntime;

typedef struct
{
    unsigned long frame;
    unsigned short input_mask;
    AvspPwView player;
    AvspAlienView alien;
    AvspPortV2HitKoActorState alien_presentation;
    unsigned short encounter_state;
    unsigned short player_contact;
    unsigned short alien_contact;
    unsigned short player_damage;
    unsigned short alien_damage;
    unsigned short attack_miss;
    unsigned short semantic_hit;
    unsigned short semantic_ko;
    unsigned short route_unlocked;
    unsigned short continued_after_unlock;
    unsigned short canaries_ok;
    short health_before;
    short health_after;
    short camera_world_x;
    short player_screen_x;
    short alien_screen_x;
    short player_screen_y;
    short alien_screen_y;
} AvspLiveEncounterFrame;

int avsp_live_encounter_contract_valid(void);
unsigned int avsp_live_encounter_contract_flags(void);
int avsp_live_encounter_clear_allowed(unsigned short target_ko,
                                      unsigned short target_inactive,
                                      unsigned short timer_elapsed,
                                      unsigned short presentation_flag);
int avsp_live_encounter_canaries_ok(const AvspLiveEncounterRuntime *runtime);
short avsp_live_encounter_project_screen_y(short world_z, short height);
void avsp_live_encounter_init(AvspLiveEncounterRuntime *runtime);
int avsp_live_encounter_step(AvspLiveEncounterRuntime *runtime,
                             const AvspLiveEncounterInput *input,
                             AvspLiveEncounterFrame *frame);

#endif
