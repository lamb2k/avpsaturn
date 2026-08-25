#include <string.h>

#include "live_encounter.h"
#include "../../../../avsp_actor.h"
#include "../../../../avsp_collision.h"
#include "../combat/combat.h"

static short avsp_live_damage_for_selector(const unsigned short selector)
{
    AvspPortV2CombatSourceEvent source;
    if (selector < 1u || selector > AVSP_PORT_V2_COMBAT_SOURCE_EVENT_COUNT ||
        !avsp_port_v2_combat_source_event((int)selector - 1, &source))
        return 0;
    return (short)(source.health_before - source.health_after);
}

unsigned int avsp_live_encounter_contract_flags(void)
{
    unsigned int flags = 0u;
    short x;
    short z;
    if (avsp_pw_action_defs_valid(avsp_pw_action_defs,
                                  AVSP_PW_ACTION_COUNT))
        flags |= 1u;
    if (avsp_alien_ai_contract_valid()) flags |= 2u;
    if (avsp_port_v2_combat_approval_locks_valid()) flags |= 4u;
    if (avsp_live_damage_for_selector(1u) == 24 &&
        avsp_live_damage_for_selector(2u) == 24 &&
        avsp_live_damage_for_selector(3u) == 31 &&
        avsp_live_damage_for_selector(4u) == 9)
        flags |= 8u;
    x = 1200;
    z = 400;
    avsp_pw_resolve_navigation(&x, &z);
    if (x == 1091 && z == 327) flags |= 16u;
    if (avsp_live_encounter_project_screen_y(327, 0) == 170 &&
        avsp_live_encounter_project_screen_y(224, 0) == 273)
        flags |= 32u;
    if (strlen(AVSP_LIVE_ENCOUNTER_SPEC01_SHA256) == 64u &&
        avsp_alien_ai_assembly_for_record(0x0012E8ECUL) == 0x0012F5DEUL)
        flags |= 64u;
    return flags;
}

int avsp_live_encounter_contract_valid(void)
{
    return avsp_live_encounter_contract_flags() == 127u;
}

short avsp_live_encounter_project_screen_y(const short world_z,
                                           const short height)
{
    return (short)(AVSP_LIVE_ENCOUNTER_SCREEN_Y_ANCHOR -
        (world_z - AVSP_LIVE_ENCOUNTER_WORLD_Z_ANCHOR) - height);
}

int avsp_live_encounter_clear_allowed(const unsigned short target_ko,
                                      const unsigned short target_inactive,
                                      const unsigned short timer_elapsed,
                                      const unsigned short presentation_flag)
{
    (void)timer_elapsed;
    (void)presentation_flag;
    return target_ko != 0u && target_inactive != 0u;
}

int avsp_live_encounter_canaries_ok(const AvspLiveEncounterRuntime *runtime)
{
    return runtime != 0 &&
        runtime->head_canary == AVSP_LIVE_ENCOUNTER_CANARY_HEAD &&
        runtime->tail_canary == AVSP_LIVE_ENCOUNTER_CANARY_TAIL;
}

void avsp_live_encounter_init(AvspLiveEncounterRuntime *runtime)
{
    if (runtime == 0) return;
    memset(runtime, 0, sizeof(*runtime));
    runtime->head_canary = AVSP_LIVE_ENCOUNTER_CANARY_HEAD;
    runtime->tail_canary = AVSP_LIVE_ENCOUNTER_CANARY_TAIL;
    avsp_pw_init(&runtime->player);
    avsp_alien_ai_init(&runtime->alien, 0x7301u);
    runtime->player.x = AVSP_LIVE_ENCOUNTER_PLAYER_X;
    runtime->player.lane = AVSP_LIVE_ENCOUNTER_PLAYER_LANE;
    runtime->alien.x = AVSP_LIVE_ENCOUNTER_ALIEN_X;
    runtime->alien.lane = AVSP_LIVE_ENCOUNTER_ALIEN_LANE;
    runtime->camera_world_x = AVSP_LIVE_ENCOUNTER_CAMERA_LOCK_X;
}

static int avsp_live_player_overlap(const AvspLiveEncounterRuntime *runtime,
                                    unsigned char *hit_value)
{
    AvspActor player;
    AvspActor alien;
    memset(&player, 0, sizeof(player));
    memset(&alien, 0, sizeof(alien));
    player.state = 1u;
    player.table_set = AVSP_PORT_V2_COMBAT_PLAYER_TABLE_SET;
    player.sel_attack = (unsigned char)runtime->player.selector;
    player.facing = (unsigned char)runtime->player.facing;
    player.world_x = (unsigned short)runtime->player.x;
    player.world_y = (unsigned short)(runtime->player.lane +
                                       runtime->player.height);
    player.world_z = (unsigned short)runtime->player.lane;
    player.attacker_id = 155u;
    player.latch_index = 0u;
    alien.state = 1u;
    alien.table_set = AVSP_PORT_V2_COMBAT_ENEMY_TABLE_SET;
    alien.sel_hurt = AVSP_PORT_V2_COMBAT_ENEMY_HURT_SELECTOR;
    alien.facing = (unsigned char)runtime->alien.facing;
    alien.world_x = (unsigned short)runtime->alien.x;
    alien.world_y = (unsigned short)runtime->alien.lane;
    alien.world_z = (unsigned short)runtime->alien.lane;
    return avsp_collision_overlap(&player, &alien, hit_value) &&
           !avsp_collision_guarded(&player, &alien);
}

static void avsp_live_begin_transition(AvspLiveEncounterRuntime *runtime,
                                       const int ko)
{
    memset(&runtime->alien_transition, 0,
           sizeof(runtime->alien_transition));
    if (ko)
        avsp_port_v2_hit_ko_begin(&runtime->alien_transition,
            AVSP_PORT_V2_HIT_KO_KO, &avsp_port_v2_ko_source_before);
    else
        avsp_port_v2_hit_ko_begin(&runtime->alien_transition,
            AVSP_PORT_V2_HIT_KO_HIT, &avsp_port_v2_hit_source_before);
}

static void avsp_live_camera_step(AvspLiveEncounterRuntime *runtime)
{
    int target;
    if (!runtime->route_unlocked)
    {
        runtime->camera_world_x = AVSP_LIVE_ENCOUNTER_CAMERA_LOCK_X;
        return;
    }
    target = runtime->player.x - AVSP_LIVE_ENCOUNTER_PLAYER_X;
    if (target < AVSP_LIVE_ENCOUNTER_CAMERA_LOCK_X)
        target = AVSP_LIVE_ENCOUNTER_CAMERA_LOCK_X;
    runtime->camera_world_x = (short)target;
    if (!runtime->continued_after_unlock &&
        runtime->player.x > runtime->unlock_player_x + 8)
        runtime->continued_after_unlock = 1u;
}

int avsp_live_encounter_step(AvspLiveEncounterRuntime *runtime,
                             const AvspLiveEncounterInput *input,
                             AvspLiveEncounterFrame *frame)
{
    AvspPwInput player_input;
    AvspAlienInput alien_input;
    AvspPwView player_view;
    AvspPortV2PlayerCombatPresentation player_presentation;
    unsigned char hit_value;
    short damage;
    short health_before;
    int overlap;
    if (runtime == 0 || input == 0 || frame == 0 ||
        input->frame != runtime->frame ||
        !avsp_live_encounter_canaries_ok(runtime) ||
        !avsp_live_encounter_contract_valid())
    {
        if (runtime != 0) ++runtime->failures;
        return 0;
    }
    memset(frame, 0, sizeof(*frame));
    player_input.mask = input->player_mask;
    player_input.received_damage = (short)runtime->pending_player_damage;
    if (runtime->pending_player_damage != 0u)
    {
        frame->player_damage = runtime->pending_player_damage;
        ++runtime->player_damage_events;
    }
    runtime->pending_player_damage = 0u;
    avsp_pw_step(&runtime->player, &player_input);
    if ((runtime->player.input_edges & AVSP_PW_INPUT_ATTACK) != 0u)
        ++runtime->player_attack_edges;
    if (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_WAIT_ENTRY &&
        runtime->player.x >= AVSP_LIVE_ENCOUNTER_ENTRY_X)
        runtime->encounter_state = AVSP_LIVE_ENCOUNTER_ACTIVE;

    memset(&alien_input, 0, sizeof(alien_input));
    alien_input.target.active = (unsigned short)
        (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_ACTIVE &&
         runtime->player.state != AVSP_PW_STATE_KO);
    alien_input.target.id = 1u;
    alien_input.target.x = runtime->player.x;
    alien_input.target.lane = runtime->player.lane;
    avsp_pw_view(&runtime->player, &player_view);
    if (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_ACTIVE &&
        player_view.attack_active && !runtime->attack_latched &&
        runtime->alien.state != AVSP_ALIEN_STATE_KO &&
        runtime->alien.state != AVSP_ALIEN_STATE_INACTIVE)
    {
        hit_value = 0u;
        overlap = avsp_live_player_overlap(runtime, &hit_value);
        runtime->attack_latched = 1u;
        if (overlap && runtime->player.selector >= 1u &&
            runtime->player.selector <= AVSP_PW_ACTION_COUNT &&
            hit_value == (unsigned char)avsp_pw_action_defs[
                runtime->player.selector - 1u].box.hit_value)
        {
            damage = avsp_live_damage_for_selector(runtime->player.selector);
            alien_input.incoming_damage = damage;
            frame->player_contact = 1u;
            frame->alien_damage = (unsigned short)damage;
            frame->health_before = runtime->alien.health;
            frame->health_after = (short)(runtime->alien.health - damage);
            runtime->last_attack_selector = runtime->player.selector;
            runtime->reaction_elapsed = 0u;
            ++runtime->player_contacts;
            ++runtime->alien_damage_events;
            avsp_pw_report_contact(&runtime->player);
        }
        else
        {
            frame->attack_miss = 1u;
            ++runtime->player_misses;
        }
    }
    if (!player_view.attack_active) runtime->attack_latched = 0u;

    health_before = runtime->alien.health;
    if (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_ACTIVE)
        avsp_alien_ai_step(&runtime->alien, &alien_input);
    if (alien_input.incoming_damage > 0)
    {
        if (runtime->alien.state == AVSP_ALIEN_STATE_KO)
        {
            runtime->target_ko_observed = 1u;
            frame->semantic_ko = 1u;
            ++runtime->ko_events;
            avsp_live_begin_transition(runtime, 1);
        }
        else
        {
            frame->semantic_hit = 1u;
            ++runtime->hit_events;
            avsp_live_begin_transition(runtime, 0);
        }
    }
    else if (runtime->alien_transition.active)
    {
        avsp_port_v2_hit_ko_step(&runtime->alien_transition);
        ++runtime->reaction_elapsed;
    }
    if (runtime->alien.contact && runtime->alien.contact_damage > 0u &&
        runtime->player.state != AVSP_PW_STATE_KO)
    {
        frame->alien_contact = 1u;
        runtime->pending_player_damage = runtime->alien.contact_damage;
        ++runtime->alien_contacts;
    }
    if (frame->alien_damage != 0u)
    {
        frame->health_before = health_before;
        frame->health_after = runtime->alien.health;
    }
    if (runtime->encounter_state == AVSP_LIVE_ENCOUNTER_ACTIVE &&
        avsp_live_encounter_clear_allowed(runtime->target_ko_observed,
            runtime->alien.state == AVSP_ALIEN_STATE_INACTIVE,
            (unsigned short)(runtime->frame > 0UL), 0u))
    {
        runtime->encounter_state = AVSP_LIVE_ENCOUNTER_CLEARED;
        runtime->route_unlocked = 1u;
        runtime->unlock_player_x = runtime->player.x;
        ++runtime->clear_events;
    }
    avsp_live_camera_step(runtime);

    frame->frame = runtime->frame;
    frame->input_mask = input->player_mask;
    avsp_pw_view(&runtime->player, &frame->player);
    avsp_alien_ai_view(&runtime->alien, &frame->alien);
    frame->alien_presentation = runtime->alien_transition.actor;
    if (avsp_pw_source_presentation_ready(frame->player.selector,
            frame->player.action_elapsed) &&
        avsp_port_v2_combat_source_player_frame(
            (int)frame->player.selector - 1,
            (int)frame->player.action_elapsed -
                (int)avsp_pw_action_defs[
                    frame->player.selector - 1u].presentation_first,
            &player_presentation))
    {
        frame->player.animation_record =
            player_presentation.source_animation_record;
        frame->player.assembly = avsp_pw_assembly_for_record(
            frame->player.animation_record);
    }
    if ((frame->alien.state == AVSP_ALIEN_STATE_HIT ||
         frame->alien.state == AVSP_ALIEN_STATE_KO) &&
        frame->alien_presentation.anim_record != 0UL)
    {
        frame->alien.animation_record =
            frame->alien_presentation.anim_record;
        frame->alien.assembly = avsp_alien_ai_assembly_for_record(
            frame->alien.animation_record);
    }
    frame->encounter_state = runtime->encounter_state;
    frame->route_unlocked = runtime->route_unlocked;
    frame->continued_after_unlock = runtime->continued_after_unlock;
    frame->canaries_ok = (unsigned short)
        avsp_live_encounter_canaries_ok(runtime);
    frame->camera_world_x = runtime->camera_world_x;
    frame->player_screen_x = (short)(frame->player.x -
        frame->camera_world_x + AVSP_LIVE_ENCOUNTER_APERTURE_ORIGIN_X);
    frame->alien_screen_x = (short)(frame->alien.x -
        frame->camera_world_x + AVSP_LIVE_ENCOUNTER_APERTURE_ORIGIN_X);
    frame->player_screen_y = avsp_live_encounter_project_screen_y(
        frame->player.lane, frame->player.height);
    frame->alien_screen_y = avsp_live_encounter_project_screen_y(
        frame->alien.lane, 0);
    ++runtime->frame;
    return 1;
}
