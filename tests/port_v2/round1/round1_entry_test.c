#include "round1.h"

#include <stdio.h>

int main(void)
{
    AvspRound1Runtime runtime;
    unsigned int calls = 0u;
    unsigned short selector;
    const AvspRound1ActorCore *first;
    const AvspRound1ActorCore *last;
    avsp_round1_init(&runtime);
    if (!avsp_round1_entry_valid(&runtime))
        return 1;
    if (!avsp_round1_begin_first_entry(&runtime) ||
        runtime.player.state != AVSP_ROUND1_PLAYER_ENTRY_STATE ||
        runtime.entry.script_cursor != 0x00128FAAUL ||
        runtime.entry.gate8236 != 1u || runtime.entry.gate81af != 1u)
        return 2;
    while (!runtime.entry.control_enabled && calls < 1000u)
    {
        if (!avsp_round1_step_first_entry(&runtime))
        {
            fprintf(stderr,
                    "entry step failed calls=%u route=%u terminal=%u action=%u player_action=%u cleanup=%u player=%d/%d controller=%d/%d health=%d/%d nav=%u/%d/%d failures=%lu\n",
                    calls, runtime.route_state, runtime.entry.terminal_seen,
                    runtime.player_locomotion_action,
                    runtime.player.source_action,
                    runtime.player_cleanup_pending,
                    runtime.player.x, runtime.player.z,
                    runtime.player_action.x, runtime.player_action.lane,
                    runtime.player.health, runtime.player_action.health,
                    runtime.navigation_bounds_active,
                    runtime.navigation_bound_x, runtime.navigation_bound_z,
                    runtime.failure_count);
            return 3;
        }
        ++calls;
        if (runtime.route_state == 4 && !runtime.entry.terminal_seen)
            return 4;
    }
    if (calls != 171u || runtime.route_state != 4 ||
        runtime.player.state != AVSP_ROUND1_PLAYER_CONTROL_STATE ||
        runtime.entry.spawn_count != AVSP_ROUND1_FIRST_SPAWN_COUNT ||
        runtime.entry.timer_decrements != 164u ||
        runtime.entry.step_index != AVSP_ROUND1_ENTRY_STEP_COUNT ||
        runtime.entry.gate8236 != 0u || runtime.entry.gate81af != 1u ||
        runtime.entry.source_global_8209 != 2u ||
        runtime.entry.script_cursor != 0x00128FC4UL ||
        runtime.navigation_bounds_active != 1u ||
        runtime.navigation_bound_x != 720 || runtime.navigation_bound_z != 256 ||
        runtime.pools[0].free_count != 10u ||
        !avsp_round1_entry_valid(&runtime))
        return 5;
    if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        !avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        !avsp_round1_step_player(&runtime, AVSP_PW_INPUT_RIGHT, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x <= 944 || runtime.player.z != 320 ||
        runtime.player.facing != 1u || runtime.player_controller_updates != 5u ||
        runtime.player.substate != 512u ||
        !avsp_round1_entry_valid(&runtime))
        return 6;
    if (!avsp_round1_step_scheduler(&runtime) ||
        runtime.scheduler_trace_count != 10u ||
        runtime.scheduler_frames != 1u ||
        runtime.scheduler_dispatches != 10u ||
        runtime.actor_handler_dispatches != 10u ||
        runtime.presentation_bindings != 10u ||
        runtime.state_context_bindings != 10u ||
        runtime.pools[0].records[10].assembly != 0x0012F5DEUL ||
        runtime.pools[0].records[10].hurt_selector != 2u ||
        runtime.pools[0].records[10].attack_selector != 0u ||
        runtime.pools[0].records[16].assembly != 0x0012F994UL ||
        runtime.pools[0].records[16].hurt_selector != 1u ||
        runtime.pools[0].records[10].dispatch_entry != 0x00060532UL)
        return 7;
    for (calls = 0u; calls < 10u; ++calls)
    {
        if (runtime.scheduler_trace[calls].record_type != 12u ||
            runtime.scheduler_trace[calls].actor_class != 0x1f ||
            runtime.scheduler_trace[calls].pool_slot != calls + 10u ||
            runtime.scheduler_trace[calls].source_slot !=
                0x00ff9d00UL + calls * 192u)
            return 8;
    }
    runtime.pools[1].records[0].active = 1u;
    runtime.pools[1].records[0].actor_class = 0x06;
    runtime.pools[1].records[0].type = 16u;
    runtime.pools[1].records[0].source_slot = 0x00ffa480UL;
    runtime.pools[1].free_count = 19u;
    runtime.pools[2].records[0].active = 1u;
    runtime.pools[2].records[0].actor_class = 0x07;
    runtime.pools[2].records[0].type = 20u;
    runtime.pools[2].records[0].source_slot = 0x00ffae80UL;
    runtime.pools[2].free_count = 15u;
    runtime.pools[3].records[0].active = 1u;
    runtime.pools[3].records[0].actor_class = 0x10;
    runtime.pools[3].records[0].type = 24u;
    runtime.pools[3].records[0].variant = 1u;
    runtime.pools[3].records[0].source_facing_selector = 1u;
    runtime.pools[3].records[0].source_slot = 0x00ffb680UL;
    runtime.pools[3].free_count = 31u;
    if (!avsp_round1_step_scheduler(&runtime) ||
        runtime.scheduler_trace_count != 13u ||
        runtime.scheduler_frames != 2u ||
        runtime.scheduler_dispatches != 23u ||
        runtime.actor_handler_dispatches != 20u ||
        runtime.presentation_bindings != 20u ||
        runtime.state_context_bindings != 20u ||
        runtime.scheduler_trace[10].record_type != 16u ||
        runtime.scheduler_trace[11].record_type != 20u ||
        runtime.scheduler_trace[12].record_type != 24u ||
        runtime.pools[0].records[10].scheduler_updates != 2u ||
        runtime.pools[0].records[10].handler_updates != 2u ||
        runtime.pools[0].records[10].state_handler_updates != 2u)
        return 9;
    first = &runtime.pools[0].records[19];
    last = &runtime.pools[0].records[10];
    if (first->source_slot != 0x00FFA3C0UL || first->x != 656 ||
        first->z != 312 || first->variant != 8u ||
        first->source_action != 16u || first->substate != 5120u ||
        first->animation_record != 0x0012E8ECUL || first->health != 87 ||
        last->source_slot != 0x00FF9D00UL || last->x != 632 ||
        last->z != 296 || last->variant != 6u ||
        last->substate != 4096u || last->animation_record != 0x0012E8ECUL)
        return 10;
    runtime.player_action.x = 2000;
    runtime.player_action.lane = 1000;
    if (!avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x != 1072 || runtime.player.z != 327)
    {
        fprintf(stderr,
                "high clamp x=%d z=%d action_x=%d lane=%d applications=%lu clamps=%lu\n",
                runtime.player.x, runtime.player.z,
                runtime.player_action.x, runtime.player_action.lane,
                runtime.navigation_applications, runtime.navigation_clamps);
        return 11;
    }
    runtime.player_action.x = -1000;
    runtime.player_action.lane = -1000;
    if (!avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.x != 752 || runtime.player.z != 272 ||
        runtime.navigation_applications != 7u ||
        runtime.navigation_clamps != 3u)
    {
        fprintf(stderr,
                "low clamp x=%d z=%d action_x=%d lane=%d applications=%lu clamps=%lu\n",
                runtime.player.x, runtime.player.z,
                runtime.player_action.x, runtime.player_action.lane,
                runtime.navigation_applications, runtime.navigation_clamps);
        return 12;
    }
    for (calls = 0u; calls < 9u; ++calls)
        if (!avsp_round1_step_player(&runtime, 0u, 0))
            return 13;
    if (runtime.player_stop_ticks != 0u ||
        runtime.player.source_action != 512u ||
        runtime.player_cleanup_pending != 1u ||
        runtime.player_stop_entries != 1u ||
        runtime.player_stop_completions != 1u)
        return 14;
    if (!avsp_round1_step_player(&runtime, 0u, 0) ||
        runtime.player.source_action != 514u ||
        runtime.player_cleanup_pending != 0u ||
        runtime.player.facing != 1u ||
        runtime.navigation_applications != 17u ||
        runtime.navigation_clamps != 3u ||
        runtime.player_stop_motion_suppressions != 10u)
        return 15;
    for (selector = 1u; selector <= AVSP_ROUND1_PLAYER_MELEE_COUNT;
         ++selector)
    {
        unsigned long entries = runtime.player_melee_entries;
        if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_ATTACK, 0) ||
            runtime.player_action.state != AVSP_PW_STATE_ATTACK ||
            runtime.player_action.selector != selector ||
            runtime.player_melee_entries != entries + 1u ||
            runtime.player_melee_selector_mask !=
                ((1UL << selector) - 1UL))
            return 16;
        if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_ATTACK, 0) ||
            runtime.player_melee_entries != entries + 1u ||
            runtime.player_action.action_elapsed != 1u)
            return 17;
        if (!avsp_round1_step_player(&runtime, 0u, 0) ||
            runtime.player.source_action != 1536u)
            return 18;
        while (!avsp_pw_can_control(&runtime.player_action))
            if (!avsp_round1_step_player(&runtime, 0u, 0))
                return 19;
        if (runtime.player_melee_completions != selector)
            return 20;
        while (runtime.player_action.combo_idle_frames < 20u)
            if (!avsp_round1_step_player(&runtime, 0u, 0))
                return 21;
    }
    if (runtime.player_melee_entries != 4u ||
        runtime.player_melee_completions != 4u ||
        runtime.player_melee_selector_mask != 0x0fUL ||
        runtime.player_melee_presentation_mask != 0x0fUL ||
        runtime.player_melee_interruptions != 0u)
        return 22;
    if (!avsp_round1_step_player(&runtime, AVSP_PW_INPUT_ATTACK, 0) ||
        !avsp_round1_step_player(&runtime, 0u, 8) ||
        runtime.player_action.state != AVSP_PW_STATE_HIT ||
        runtime.player_melee_entries != 5u ||
        runtime.player_melee_completions != 4u ||
        runtime.player_melee_interruptions != 1u)
        return 23;
    for (calls = 0u; calls < 16u; ++calls)
        if (!avsp_round1_step_player(&runtime, 0u, 0))
            return 24;
    if (!avsp_pw_can_control(&runtime.player_action) ||
        !avsp_round1_entry_valid(&runtime))
        return 25;
    {
        AvspRound1Runtime weapon_runtime = runtime;
        short weapon_x = weapon_runtime.player.x;
        short weapon_z = weapon_runtime.player.z;
        unsigned long debit_count;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1 | AVSP_PW_INPUT_RIGHT, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 1u ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player.substate != 0u ||
            weapon_runtime.player.animation_record != 0x001642f4UL ||
            weapon_runtime.player.assembly != 0x00165694UL ||
            weapon_runtime.player_weapon_entries != 1u ||
            weapon_runtime.player_weapon_attempts_total != 1u ||
            weapon_runtime.player_weapon_allocations != 1u ||
            weapon_runtime.player_weapon_resource_debits != 1u ||
            weapon_runtime.player_resource != 61u ||
            weapon_runtime.player_resource_recharge != 11u ||
            weapon_runtime.player.x != weapon_x ||
            weapon_runtime.player.z != weapon_z)
            return 26;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x0c02u ||
            weapon_runtime.player.animation_record != 0x00165400UL)
            return 27;
        while (weapon_runtime.player_weapon_tick < 48u)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 28;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player_weapon_recovery_pending != 1u ||
            weapon_runtime.player_weapon_tick != 49u ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player_weapon_active != 0u ||
            weapon_runtime.player_weapon_cleanup_pending != 1u ||
            weapon_runtime.player.source_action != 0u ||
            weapon_runtime.player_weapon_completions != 1u ||
            weapon_runtime.player_weapon_allocations != 12u ||
            weapon_runtime.player_resource != 28u ||
            !avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player_weapon_active != 1u ||
            weapon_runtime.player_weapon_tick != 1u ||
            weapon_runtime.player.source_action != 0x0c00u ||
            weapon_runtime.player_weapon_entries != 2u)
            return 29;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 30;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 31;
        if (weapon_runtime.player_weapon_completions != 2u ||
            weapon_runtime.player_weapon_allocations != 24u ||
            weapon_runtime.player_weapon_projectile_free_count != 0u ||
            weapon_runtime.player_weapon_projectiles[7].variant != 1u ||
            weapon_runtime.player_weapon_projectiles[19].variant != 1u ||
            weapon_runtime.player_weapon_projectiles[23].source_slot !=
                0x9200u ||
            weapon_runtime.player_weapon_projectiles[23].owner != 0x8380u ||
            weapon_runtime.player_weapon_projectiles[23].attack_table !=
                0x03136aUL ||
            weapon_runtime.player_weapon_projectiles[0].state != 0u ||
            weapon_runtime.player_weapon_projectiles[0].
                parent_presentation_selector != 6u ||
            weapon_runtime.player_weapon_projectiles[0].angle !=
                (weapon_runtime.player_weapon_projectiles[0].facing ?
                    24u : 40u) ||
            weapon_runtime.player_weapon_projectiles[0].x_fp !=
                (long)weapon_runtime.player_weapon_projectiles[0].x * 65536L)
            return 32;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 33;
        weapon_runtime.player_resource = 64u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 0u;
        debit_count = weapon_runtime.player_weapon_resource_debits;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 34;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 35;
        if (weapon_runtime.player_weapon_attempts_total != 36u ||
            weapon_runtime.player_weapon_allocation_failures != 12u ||
            weapon_runtime.player_weapon_allocations != 24u ||
            weapon_runtime.player_weapon_resource_debits != debit_count ||
            weapon_runtime.player_resource != 64u)
            return 36;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
            return 37;
        weapon_runtime.player_resource = 0u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            weapon_runtime.player.source_action != 0x1a00u ||
            weapon_runtime.player_weapon_empty != 1u ||
            weapon_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            weapon_runtime.player_weapon_allocations != 24u)
            return 38;
        if (!avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 0x1a02u ||
            weapon_runtime.player.animation_record != 0x001645d4UL ||
            weapon_runtime.player.assembly != 0x00166bf8UL)
            return 39;
        while (weapon_runtime.player_weapon_active)
            if (!avsp_round1_step_player(&weapon_runtime, 0u, 0))
                return 40;
        if (weapon_runtime.player_weapon_completions != 4u ||
            weapon_runtime.player.source_action != 0u ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 0) ||
            weapon_runtime.player.source_action != 2u)
            return 41;
        weapon_runtime.player_resource = 64u;
        weapon_runtime.player_resource_recharge = 12u;
        weapon_runtime.player_resource_depleted = 0u;
        if (!avsp_round1_step_player(&weapon_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            !avsp_round1_step_player(&weapon_runtime, 0u, 8) ||
            weapon_runtime.player_weapon_active != 0u ||
            weapon_runtime.player_weapon_interruptions != 1u ||
            weapon_runtime.player_action.state != AVSP_PW_STATE_HIT ||
            weapon_runtime.player.source_action != 514u ||
            !avsp_round1_entry_valid(&weapon_runtime))
            return 42;
    }
    {
        AvspRound1Runtime effect_runtime;
        AvspRound1ActorCore *effect;
        int index;
        unsigned int effect_entry_calls = 0u;
        avsp_round1_init(&effect_runtime);
        if (!avsp_round1_begin_first_entry(&effect_runtime))
            return 43;
        while (!effect_runtime.entry.control_enabled &&
               effect_entry_calls < 1000u)
        {
            if (!avsp_round1_step_first_entry(&effect_runtime))
                return 43;
            ++effect_entry_calls;
        }
        if (effect_runtime.route_state != 4)
            return 43;
        effect_runtime.player_resource = 0u;
        effect_runtime.player_resource_depleted = 1u;
        if (!avsp_round1_step_player(&effect_runtime,
                AVSP_ROUND1_INPUT_BUTTON1, 0) ||
            effect_runtime.player_weapon_empty_auxiliary_requests != 1u ||
            effect_runtime.player_weapon_empty_auxiliary_allocations != 1u ||
            effect_runtime.pools[3].free_count != 31u)
            return 43;
        effect = &effect_runtime.pools[3].records[31];
        if (!avsp_round1_step_scheduler(&effect_runtime) ||
            effect->state != 2u || effect->variant != 1u ||
            effect->x != effect_runtime.player.x ||
            effect->y != effect_runtime.player.y + 78 ||
            effect->animation_record != 0x0007a09cUL ||
            effect->animation_timer != 1u || effect->animation_branch != 0)
            return 44;
        for (index = 0; index < 8; ++index)
            if (!avsp_round1_step_scheduler(&effect_runtime))
                return 45;
        if (effect->y != effect_runtime.player.y + 110 ||
            effect->animation_index != 8u ||
            effect->animation_record != 0x0007a11cUL ||
            effect->animation_timer != 8u || effect->animation_branch != 1)
            return 46;
        for (index = 0; index < 8; ++index)
            if (!avsp_round1_step_scheduler(&effect_runtime))
                return 47;
        if (effect->animation_index != 9u ||
            effect->animation_record != 0x0007a12cUL ||
            effect->animation_branch != -32767 ||
            !avsp_round1_step_scheduler(&effect_runtime) ||
            effect->state != 4u ||
            !avsp_round1_step_scheduler(&effect_runtime) ||
            effect_runtime.pools[3].free_count != 32u ||
            effect_runtime.player_weapon_empty_auxiliary_releases != 1u)
            return 48;
    }
    runtime.entry.gate8236 = 1u;
    if (avsp_round1_entry_valid(&runtime))
        return 49;
    puts("REIMPLEMENT-13 native entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Button1-resource/class10-effect: PASS");
    return 0;
}
