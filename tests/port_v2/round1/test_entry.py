#!/usr/bin/env python3
"""Strict host compile and real stable-entry mutations for REIMPLEMENT-13."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "data/spec02_round1_executable_contract.json"
EXPECTED = "3abfcff9da0e862327d1c5afbf1698259eb42c89552f147ec9edef9ca160688d"
assert hashlib.sha256(SPEC.read_bytes()).hexdigest() == EXPECTED
assert json.loads(SPEC.read_text())["status"] == "ACCEPTED"
source = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text()
header = (ROOT / "src/port_v2/gameplay/round1/round1.h").read_text()
generated = (ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h").read_text()
assert EXPECTED in header
subprocess.run(["python", str(ROOT / "tools/gen_spec02_round1_entry.py"), "--check"], check=True)

def wsl(path):
    return subprocess.run(["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
                           "wslpath", "-a",
                           str(path).replace("\\", "/")],
                          check=True, capture_output=True, text=True).stdout.strip()

def run(body, header_body, passes, label="baseline"):
    with tempfile.TemporaryDirectory(prefix="round1-entry-") as name:
        temp = Path(name)
        linux_output = f"/tmp/{temp.name}-test"
        temp_body = body.replace(
            '#include "../../integration/combat/combat.h"', '#include "combat.h"')
        temp_body = temp_body.replace(
            '#include "../../../../avsp_actor.h"', '#include "avsp_actor.h"')
        temp_body = temp_body.replace(
            '#include "../../../../avsp_collision.h"', '#include "avsp_collision.h"')
        (temp / "round1.c").write_text(temp_body)
        temp_header = header_body.replace(
            '#include "../player_action/player_action.h"', '#include "player_action.h"')
        temp_header = temp_header.replace(
            '#include "../street_alien_ai/street_alien_ai.h"', '#include "street_alien_ai.h"')
        temp_header = temp_header.replace(
            '#include "../../combat/hit_ko/hit_ko.h"', '#include "hit_ko.h"')
        (temp / "round1.h").write_text(temp_header)
        (temp / "spec02_round1_entry_data.h").write_text(generated)
        command = (f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{wsl(temp)}' -I . -I src/port_v2/gameplay/player_action "
                   f"-I src/port_v2/gameplay/street_alien_ai -I src/port_v2/combat/hit_ko "
                   f"-I src/port_v2/integration/combat "
                   f"'{wsl(temp / 'round1.c')}' "
                   f"avsp_actor.c avsp_collision.c "
                   f"src/port_v2/gameplay/player_action/player_action.c "
                   f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
                   f"src/port_v2/combat/hit_ko/hit_ko.c "
                   f"src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
                   f"src/port_v2/integration/player_enemy/player_enemy.c "
                   f"src/port_v2/integration/combat/combat.c "
                   f"tests/port_v2/round1/round1_entry_test.c -o '{linux_output}' && "
                   f"ulimit -s unlimited && '{linux_output}'")
        result = subprocess.run(["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root",
                                 "--", "bash", "-lc", command],
                                capture_output=True)
        assert (result.returncode == 0) == passes, (
            f"label={label}\nreturncode={result.returncode}\n" +
            result.stdout.decode(errors="replace") +
            result.stderr.decode(errors="replace"))

run(source, header, True)
if "--baseline-only" in sys.argv:
    print("REIMPLEMENT-13 focused baseline: PASS")
    raise SystemExit(0)
inner8_mutations = {
    "(actor->state == 0x0200u &&\n                      (actor->substate == 0x1000u ||",
    "actor->state = 0x0208u;\n    actor->substate = 0x0600u;",
    "if ((random & 3u) != 0u)",
    "actor->source_motion_fields[0] = 8;\n        actor->source_action_timer =",
    "actor->source_x_fp += actor->source_x_velocity;",
}
for before, after in (
    ("runtime->route_state = AVSP_ROUND1_ROUTE_ENTRY_STATE;", "runtime->route_state = 4;"),
    ("{20u, 20u, 16u, 32u, 16u, 64u}",
     "{20u, 20u, 16u, 32u, 16u, 63u}"),
    ("{192u, 128u, 128u, 128u, 128u, 64u}",
     "{128u, 128u, 128u, 128u, 128u, 64u}"),
    ("{0x9580u, 0xA480u, 0xAE80u, 0xB680u, 0xC680u, 0xD280u}",
     "{0x9580u, 0xA480u, 0xAE80u, 0xB680u, 0xC680u, 0xD240u}"),
    ("runtime->rng_seed = AVSP_ROUND1_INITIAL_RNG;", "runtime->rng_seed = 1u;"),
    ("runtime->entry.gate8236 & runtime->entry.gate81af", "runtime->entry.gate8236 | runtime->entry.gate81af"),
    ("--runtime->entry.animation_c8;", "runtime->entry.animation_c8 = 0u;"),
    ("avsp_round1_entry_steps[runtime->entry.step_index].kind !=\n                    AVSP_ROUND1_ENTRY_DWELL",
     "avsp_round1_entry_steps[runtime->entry.step_index].kind ==\n                    AVSP_ROUND1_ENTRY_DWELL"),
    ("++runtime->entry.timer_decrements;", "runtime->entry.timer_decrements += 2u;"),
    ("pool->free_stack[pool->free_count - 1u]", "pool->free_stack[0]"),
    ("avsp_pw_step_round1(&runtime->player_action, &input);", "input.mask = 0u; avsp_pw_step_round1(&runtime->player_action, &input);"),
    ("if (actor->active == 0u)\n                continue;", "if (actor->active != 0u)\n                continue;"),
    ("pool_index = order_index;", "pool_index = (order_index + 1u) % AVSP_ROUND1_POOL_COUNT;"),
    ("!avsp_round1_dispatch_supported(actor->type,\n                                                actor->actor_class)", "0"),
    ("actor->source_next_animation_record = record->next_animation_record;\n    actor->assembly = record->assembly;",
     "actor->source_next_animation_record = record->next_animation_record;\n    actor->assembly = 0UL;"),
    ("actor->dispatch_entry = AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY;", "actor->dispatch_entry = 0UL;"),
    ("avsp_round1_apply_player_global_bounds(runtime);", "/* bounds suppressed */"),
    ("avsp_round1_update_player_locomotion(runtime, applied_direction,\n                                            was_stopping, &view);", "/* locomotion transition suppressed */"),
    ("avsp_round1_observe_player_melee(runtime, prior_state, prior_selector,\n                                    prior_attack_edges);", "/* melee observation suppressed */"),
    ("++runtime->player_melee_entries;", "runtime->player_melee_entries += 2u;"),
    ("runtime->player_melee_selector_mask |= 1UL << (selector - 1u);", "runtime->player_melee_selector_mask = 0UL;"),
    ("++runtime->player_melee_completions;", "runtime->player_melee_completions += 2u;"),
    ("runtime->player_melee_presentation_mask |= 1UL << index;", "runtime->player_melee_presentation_mask = 0UL;"),
    ("projectile->angle = avsp_round1_player_weapon_target_angle(runtime);",
     "projectile->angle = 35u;"),
    ("projectile->actor_class = avsp_round1_player_weapon.parent_class;",
     "projectile->actor_class = avsp_round1_player_weapon.child_class;"),
    ("runtime->player_action.state = prior_state;", "runtime->player_action.state = AVSP_PW_STATE_ATTACK;"),
    ("runtime->player_resource_recharge =\n            avsp_round1_player_weapon.recharge_after_success;", "runtime->player_resource_recharge = 11u;"),
    ("++runtime->player_weapon_resource_debits;", "runtime->player_weapon_resource_debits += 2u;"),
    ("++runtime->player_weapon_allocation_failures;", "runtime->player_weapon_allocation_failures += 2u;"),
    ("avsp_round1_tick_player_resource(runtime);", "/* resource tick suppressed */"),
    ("avsp_round1_begin_empty_effect(runtime);", "/* empty effect suppressed */"),
    ("actor->variant = 1u;", "actor->variant = 0u;"),
    ("actor->y = (short)(actor->y + 4);", "actor->y = (short)(actor->y + 3);"),
    ("if (actor->animation_branch < 0)", "if (actor->animation_branch < -32767)"),
    ("++runtime->player_weapon_empty_auxiliary_releases;", "runtime->player_weapon_empty_auxiliary_releases += 2u;"),
    ("projectile->collision_result = -1;", "projectile->collision_result = 0;"),
    ("actor->state = reaction->actor.sub_state;",
     "actor->state = 0x0400u;"),
    ("actor->substate = 0u;\n            ++runtime->class1f_transition_completions;", "actor->state = 0u;\n            actor->substate = 0u;\n            ++runtime->class1f_transition_completions;"),
    ("projectile->child_cadence =\n                        avsp_round1_weapon_projectile.child_cadence_reload;",
     "projectile->child_cadence = 5u;"),
    ("projectile->assembly = record->assembly;", "projectile->assembly = 0UL;"),
    ("(unsigned long)old_seed * 3UL &", "(unsigned long)old_seed * 2UL &"),
    ("!(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&\n           runtime->entry.started &&\n           runtime->entry.dependencies_seeded)", "!(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&\n           0u)"),
    ("transition->x_velocity = actor->facing == 0u ? -0x00030000L :\n            0x00030000L;", "transition->x_velocity = actor->facing == 0u ? -0x00020000L :\n            0x00020000L;"),
    ("transition->y_acceleration = -0x00005000L;", "transition->y_acceleration = 0x00005000L;"),
    ("actor->effect_timer = 42u;", "actor->effect_timer = 41u;"),
    ("runtime->class1f_effect_guard = 0u;", "runtime->class1f_effect_guard = 1u;"),
    ("actor->hurt_selector = actor->source_a5;",
     "actor->hurt_selector = 0u;"),
    ("actor->attack_selector = actor->source_a6;",
     "actor->attack_selector = 0u;"),
    ("slot == 0xc600u", "slot == 0xc580u"),
    ("AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT - 1u -\n                allocation_index",
     "allocation_index"),
    ("runtime->class45_rng_calls += 7u;",
     "runtime->class45_rng_calls += 6u;"),
    ("avsp_round1_spawn_class47_group(runtime, actor);",
     "/* class-0x47 spawn suppressed */"),
    ("runtime->class47_rng_calls +=\n            avsp_round1_class47.rng_calls_per_actor;",
     "runtime->class47_rng_calls += 6u;"),
    ("(pool->capacity - 1u - slot_index)) % 2u != 0u",
     "slot_index) % 2u != 0u"),
    ("actor->source_flags = owner->source_facing_selector;",
     "actor->source_flags = 0u;"),
    ("avsp_round1_class02.reaction_direction_less :",
     "avsp_round1_class02.reaction_direction_greater_equal :"),
    ("(long)actor->source_motion_fields[1] * 256L;",
     "(long)actor->source_motion_fields[1] * 0L;"),
    ("index < AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT; ++index",
     "index + 1u < AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT; ++index"),
    ("actor->effect_timer = 3u;", "actor->effect_timer = 2u;"),
    ("table_offset = rng_spec->table_index;",
     "table_offset = (unsigned char)(rng_spec->table_index + 4u);"),
    ("if (actor->source_field01 == 0u)",
     "if (actor->source_field01 != 0u)"),
    ("avsp_round1_apply_coffee_shop_obstacle(runtime);",
     "/* Coffee Shop obstacle suppressed */"),
    ("if (z_penetration < x_penetration)",
     "if (z_penetration <= x_penetration)"),
    ("else if (code == 1u)\n        *selector = 24u;",
     "else if (code == 1u)\n        *selector = 8u;"),
    ("!avsp_round1_apply_first_segment_terrain(runtime)", "0"),
    ("!avsp_round1_step_coffee_shop_camera(runtime)", "0"),
    ("--runtime->camera_guard_countdown;",
     "runtime->camera_guard_countdown = runtime->camera_guard_countdown;"),
    ("unsigned short index = (unsigned short)(byte_offset >> 1);",
     "unsigned short index = (unsigned short)(byte_offset >> 2);"),
    ("if (up)\n            index += 1u;",
     "if (up)\n            index += 2u;"),
    ("if ((unsigned char)(right ^ facing) != 0u)\n                index += 2u;",
     "if ((unsigned char)(right ^ facing) != 0u)\n                index += 1u;"),
    ("if (facing != 0u)\n        {\n            runtime->player_jump_x_velocity =\n                -runtime->player_jump_x_velocity;",
     "if (facing == 0u)\n        {\n            runtime->player_jump_x_velocity =\n                -runtime->player_jump_x_velocity;"),
    ("runtime->player_jump_collision_selector = up ? 1u : 2u;",
     "runtime->player_jump_collision_selector = up ? 2u : 1u;"),
    ("runtime->player_jump_collision_selector = up ? 4u : 8u;",
     "runtime->player_jump_collision_selector = up ? 8u : 4u;"),
    ("runtime->player_jump_phase = 0x040au;",
     "runtime->player_jump_phase = 0x0402u;"),
    ("runtime->player_jump_y_fp += runtime->player_jump_y_velocity;",
     "runtime->player_jump_y_fp -= runtime->player_jump_y_velocity;"),
    ("runtime->player_jump_y_velocity += runtime->player_jump_y_acceleration;",
     "runtime->player_jump_y_velocity -= runtime->player_jump_y_acceleration;"),
    ("avsp_round1_fixed_high_word(runtime->player_jump_y_fp) <=\n            runtime->player_action.lane",
     "avsp_round1_fixed_high_word(runtime->player_jump_y_fp) <\n            runtime->player_action.lane"),
    ("runtime->player_jump_phase_timer = 10u;",
     "runtime->player_jump_phase_timer = 9u;"),
    ("--runtime->player_jump_phase_timer;",
     "runtime->player_jump_phase_timer -= 2u;"),
    ("++runtime->player_jump_entries;\n    return avsp_round1_bind_player_jump_sequence(runtime, 3u);",
     "++runtime->player_jump_entries;\n    avsp_round1_source_rng(runtime);\n    return avsp_round1_bind_player_jump_sequence(runtime, 3u);"),
    ("if (runtime->player_jump_active && received_damage > 0)\n        avsp_round1_interrupt_player_jump(runtime);",
     "if (runtime->player_jump_active && received_damage < 0)\n        avsp_round1_interrupt_player_jump(runtime);"),
    ("input |= 0x08u;",
     "input |= 0x04u;"),
    ("projectile->actor_class = avsp_round1_air_weapon_projectile.actor_class;",
     "projectile->actor_class = avsp_round1_player_weapon.child_class;"),
    ("effect->effect_timer = 8u;",
     "effect->effect_timer = 7u;"),
    ("(runtime->scheduler_frames & 1u) == 0u",
     "(runtime->scheduler_frames & 2u) == 0u"),
    ("encounter->source_phase_counter + 1u",
     "encounter->source_phase_counter + 2u"),
    ("return entry->updates;", "return 1u;"),
    ("if (encounter->source_intro_gate != 0u)",
     "if (encounter->source_intro_gate == 0u)"),
    ("encounter->source_intro_timer - 1u",
     "encounter->source_intro_timer - 2u"),
    ("(unsigned short)actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot",
     "actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot"),
    ("actor->state ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state",
     "actor->substate ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state"),
    ("encounter->source_living_count >=\n            avsp_round1_recurring_spawn.maximum_living",
     "encounter->source_living_count >\n            avsp_round1_recurring_spawn.maximum_living"),
    ("actor->source_slot = 0x00ff0000UL | (unsigned long)slot;",
     "actor->source_slot = slot;"),
    ("actor->source_slot ==\n                        runtime->first_encounter.actor_source_slot)",
     "actor->source_slot ==\n                        runtime->first_encounter.actor_source_slot + 1u)"),
    ("runtime->player.health = 0;",
     "runtime->player.health = AVSP_ROUND1_PLAYER_HEALTH;"),
    ("actor->state = 0x0402u;",
     "actor->substate = 0x0402u;"),
    ("child->y = (short)(parent->z + row->y);",
     "child->y = (short)(parent->y + row->y);"),
    ("runtime->collision_identity_counter = 0x25u;",
     "runtime->collision_identity_counter = 0x24u;"),
    ("(unsigned short)x - (unsigned short)runtime->camera_x_position +\n        0x0040u);",
     "(unsigned short)x - (unsigned short)runtime->camera_x_position +\n        0x0020u);"),
    ("!projectile->active_collision || !projectile->collision_registered ||",
     "!projectile->active_collision ||"),
    ("target->source_field01 != 1u ||",
     "target->source_field01 == 2u ||"),
    ("if (target->source_collision_latches[\n                    (unsigned char)latch_index] ==\n                    projectile->collision_identity)\n                continue;",
     "if (0)\n                continue;"),
    ("if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)\n            return avsp_round1_release_player_weapon_projectile(runtime,\n                                                                 index);",
     "if (projectile->actor_class == avsp_round1_weapon_projectile.child_class)\n            projectile->state = avsp_round1_weapon_projectile.release_state;"),
    ("weapon_pressed = runtime->player_weapon_input_pipeline;",
     "weapon_pressed = (unsigned char)((input_mask & AVSP_ROUND1_INPUT_BUTTON1) != 0u);"),
    ("actor->state != 0x0208u || actor->substate != 0x0e02u",
     "actor->state != 0x0200u || actor->substate != 0x0e02u"),
    ("if (parent->facing != 0u)\n        x_offset = (short)-x_offset;",
     "if (parent->facing == 0u)\n        x_offset = (short)-x_offset;"),
    ("projectile->source_x_velocity = motion->x_velocity;",
     "projectile->source_x_velocity = motion->y_velocity;"),
    ("projectile->attack_selector ==\n                avsp_round1_type16.attack_selector",
     "projectile->attack_selector !=\n                avsp_round1_type16.attack_selector"),
    ("(unsigned char)avsp_round1_type16.damage;",
     "(unsigned char)(avsp_round1_type16.damage - 1);"),
    ("++runtime->type16_releases;",
     "runtime->type16_releases += 2u;"),
    ("actor->type == 16u && actor->actor_class == 0x06",
     "actor->type == 16u && actor->actor_class == 0x05"),
    ("if (projectile->health < 0)\n        {\n            projectile->state = 0x0600u;",
     "if (projectile->health < 0)\n        {\n            projectile->state = 0x0400u;"),
    ("(actor->state == 0x0200u &&\n                      (actor->substate == 0x1000u ||",
     "(actor->state == 0x0208u &&\n                      (actor->substate == 0x1000u ||"),
    ("actor->state = 0x0208u;\n    actor->substate = 0x0600u;",
     "actor->state = 0x0200u;\n    actor->substate = 0x0600u;"),
    ("if ((random & 3u) != 0u)",
     "if ((random & 3u) != 3u)"),
    ("actor->source_motion_fields[0] = 8;\n        actor->source_action_timer =",
     "actor->source_motion_fields[0] = 6;\n        actor->source_action_timer ="),
    ("actor->source_x_fp += actor->source_x_velocity;",
     "actor->source_x_fp += 0;"),
    ("actor->animation_record = animation_record;",
     "actor->animation_record = 0UL;"),
):
    if "--inner8-only" in sys.argv and before not in inner8_mutations:
        continue
    assert before in source, before
    run(source.replace(before, after), header, False, before)
if "--inner8-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f inner-state mutation lane: PASS (5 real mutations)")
    raise SystemExit(0)
for before, after in (
    ("{ 0xffa3c0u, 12u, 656, 312, 312,", "{ 0xffa3c0u, 12u, 657, 312, 312,"),
    ("{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 60u,", "{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 59u,"),
    ("    12u, 16u, 20u, 24u, 28u, 36u",
     "    16u, 12u, 20u, 24u, 28u, 36u"),
    ("{ 6u, 1u, 1u, 1u, 16u, 0u, 1u, 1u, 216u, 0x1Du, 0x0000u },",
     "{ 6u, 1u, 1u, 1u, 16u, 0u, 1u, 1u, 215u, 0x1Du, 0x0000u },"),
    ("{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u,", "{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 0u, 16u, 0x8000, 216u,"),
    ("{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u,", "{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 15u, 0x8000, 216u,"),
    ("{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x8000, 216u,", "{ 0x00ff9d00UL, 0x0200u, 0x1000u, 632, 296, 296, 1u, 1u, 16u, 0x0000, 216u,"),
    ("{ 0x0200u, 0x1400u },", "{ 0x0200u, 0x1401u },"),
    ("    640, 256, 640, 832, 256, 256, 0x40u, 0x20u,",
     "    640, 256, 640, 831, 256, 256, 0x40u, 0x20u,"),
    ("    { 0, 0, 32u, 127u, 0, 6u, 0, 0u, 0u }",
     "    { 0, 0, 31u, 127u, 0, 6u, 0, 0u, 0u }"),
    ("{ 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x10u, 0xFFu, 0x80u },",
     "{ 0x02u, 0x02u, 0x80u, 0x80u, 0x10u, 0x10u, 0x00u, 0x80u },"),
    ("    1u, 1200u,", "    1u, 1199u,"),
    ("7u, 7u, 8u, 8u, 9u, 9u", "7u, 7u, 7u, 8u, 9u, 9u"),
    ("    10u,\n    {255u, 2u, 6u, 255u,", "    9u,\n    {255u, 2u, 6u, 255u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1538u,\n    5120u,\n    30u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1536u,\n    5120u,\n    29u,"),
    ("{ 0x1600f8UL, 0x162a04UL, 8u, 1u },", "{ 0x1600f8UL, 0x162a82UL, 8u, 1u },"),
    ("{ 0x1601c0UL, 0x1614a4UL, 8u, 3u },", "{ 0x1601c0UL, 0x1614a4UL, 8u, 2u },"),
    ("    40u,\n    12u,\n    2u,", "    39u,\n    12u,\n    2u,"),
    ("{ 3074u, 2u, 0x0015e540UL, 0x00161772UL, 1u, 0u },",
     "{ 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u },"),
    ("{ 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u },",
     "{ 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },"),
    ("    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 47u",
     "    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 46u"),
    ("    { 5, 86 },", "    { 6, 86 },"),
    ("    { 0, 78 },", "    { 0, 77 },"),
    ("{ 4095u, -32767, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },", "{ 4095u, -32768, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },"),
    ("{ 0, -8, 4u, 12u, 0, 8u, 0, 8u, 25u },",
     "{ 0, -8, 4u, 12u, 0, 8u, 0, 8u, 24u },"),
    ("{ 0, 10, 16u, 10u, 0, 8u, 1, 8u, 14u },",
     "{ 0, 10, 16u, 10u, 0, 8u, 1, 8u, 13u },"),
    ("    0, 4,\n    5u,\n    1u,\n    6u, 0x8000u,",
     "    0, 5,\n    5u,\n    1u,\n    6u, 0x8000u,"),
    ("    127u,\n    31u", "    126u,\n    31u"),
    ("{ 0x00ffa300UL, 0x0200u, 0x1400u, 704, 296, 296, 1u, 1u, 19u, 0x8000, 3u,", "{ 0x00ffa300UL, 0x0200u, 0x1400u, 704, 296, 296, 1u, 1u, 19u, 0x8000, 4u,"),
    ("{ 60u, 3u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 8u, 1,", "{ 60u, 3u, AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD, { { 7u, 1,"),
    ("    0x004Du, 0x0118u, 0x0000u", "    0x004Du, 0x0119u, 0x0000u"),
    ("    { -8, 8 },", "    { -7, 8 },"),
    ("0x08d9a4UL, 0u, 0u, 0u, 0x8000u", "0x08d9a4UL, 0u, 0u, 0u, 0x0000u"),
    ("{ 0L, 0L, 557056L, -32768L },",
     "{ 0L, 0L, 524288L, -32768L },"),
    ("{ -983040L, 26624L, 262144L, -14336L },",
     "{ -917504L, 26624L, 262144L, -14336L },"),
    ("{ 786432L, -40960L, 0L, 0L }",
     "{ 786432L, -32768L, 0L, 0L }"),
    ("{ 4u, 5u, { { 8u, 0, 0x15f2f0UL, 0x160cdaUL, 2u, 0u }",
     "{ 4u, 5u, { { 7u, 0, 0x15f2f0UL, 0x160cdaUL, 2u, 0u }"),
    ("{ 6u, 8u, { { 2u, 0, 0x15f3b8UL, 0x160beeUL, 2u, 0u }",
     "{ 6u, 8u, { { 2u, 0, 0x15f3c8UL, 0x160beeUL, 2u, 0u }"),
    ("{ 41u, 2u, { { 4u, 0, 0x15fc3cUL, 0x162ee2UL, 9u, 22u }",
     "{ 41u, 2u, { { 4u, 0, 0x15fc3cUL, 0x162ee2UL, 9u, 21u }"),
    ("{ 60u, 1u, { { 4095u, -32768, 0x15fc60UL, 0x162ee2UL, 9u, 35u }",
     "{ 60u, 1u, { { 4095u, -32768, 0x15fc60UL, 0x162ee2UL, 9u, 34u }"),
    ("{ 0x0015c108UL, 0x00ffb600UL, 2072u, 512u, 752, 336,",
     "{ 0x0015c108UL, 0x00ffb600UL, 2072u, 641u, 752, 336,"),
    ("0x06B2FAUL, 0x06B520UL, 240u, 60u, 360u, 192u, 40u,",
     "0x06B2FAUL, 0x06B520UL, 239u, 60u, 360u, 192u, 40u,"),
    ("8, 64, -8, 25, -1, 0x0077u,",
     "8, 64, -8, 24, -1, 0x0077u,"),
    ("0x47, 0u, 4u, 7u, 80, -1, 0x08eb86UL",
     "0x47, 0u, 3u, 7u, 80, -1, 0x08eb86UL"),
    ("0x47, 0u, 4u, 7u, 80, -1, 0x08eb86UL",
     "0x47, 0u, 4u, 7u, 79, -1, 0x08eb86UL"),
    ("0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u",
     "0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 3u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u"),
    ("{ 512, 1792, -96, 384, 1280, -96 },",
     "{ 0, 1792, -96, 384, 1280, -96 },"),
    ("0x0077u, 1u, 0u,",
     "0x0077u, 0u, 0u,"),
    ("{ -65536L, -81920L, -98304L, -131072L },",
     "{ -32768L, -40960L, -49152L, -65536L },"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,",
     "    -58, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,",
     "    -59, 64, 0x0058u, 0x0232u, 16, 16u, 0x06, 1u, 20u,"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,",
     "    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x05, 1u, 20u,"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,",
     "    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 2u, 20u,"),
    ("    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },",
     "    { 100, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },"),
    ("    { 1, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }",
     "    { 101, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }"),
    ("    { 524288L, -8192L, 262144L, -16384L, 0L },",
     "    { 524287L, -8192L, 262144L, -16384L, 0L },"),
    ("    { 1u, 1, 0x0012e580UL, 0x00130946UL, 8u, 0u },",
     "    { 1u, 0, 0x0012e580UL, 0x00130946UL, 8u, 0u },"),
):
    assert before in generated
    changed = generated.replace(before, after, 1)
    with tempfile.TemporaryDirectory(prefix="round1-generated-mutation-") as name:
        temp = Path(name)
        linux_output = f"/tmp/{temp.name}-test"
        temp_body = source.replace(
            '#include "../../integration/combat/combat.h"', '#include "combat.h"')
        temp_body = temp_body.replace(
            '#include "../../../../avsp_actor.h"', '#include "avsp_actor.h"')
        temp_body = temp_body.replace(
            '#include "../../../../avsp_collision.h"', '#include "avsp_collision.h"')
        (temp / "round1.c").write_text(temp_body)
        temp_header = header.replace(
            '#include "../player_action/player_action.h"', '#include "player_action.h"')
        temp_header = temp_header.replace(
            '#include "../street_alien_ai/street_alien_ai.h"', '#include "street_alien_ai.h"')
        temp_header = temp_header.replace(
            '#include "../../combat/hit_ko/hit_ko.h"', '#include "hit_ko.h"')
        (temp / "round1.h").write_text(temp_header)
        (temp / "spec02_round1_entry_data.h").write_text(changed)
        command = (f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{wsl(temp)}' -I . -I src/port_v2/gameplay/player_action "
                   f"-I src/port_v2/gameplay/street_alien_ai -I src/port_v2/combat/hit_ko "
                   f"-I src/port_v2/integration/combat "
                   f"'{wsl(temp / 'round1.c')}' "
                   f"avsp_actor.c avsp_collision.c "
                   f"src/port_v2/gameplay/player_action/player_action.c "
                   f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
                   f"src/port_v2/combat/hit_ko/hit_ko.c "
                   f"src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
                   f"src/port_v2/integration/player_enemy/player_enemy.c "
                   f"src/port_v2/integration/combat/combat.c "
                   f"tests/port_v2/round1/round1_entry_test.c -o '{linux_output}' && "
                   f"ulimit -s unlimited && '{linux_output}'")
        result = subprocess.run(["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root",
                                 "--", "bash", "-lc", command],
                                capture_output=True)
        assert result.returncode != 0, f"generated mutation escaped: {before}"
print("REIMPLEMENT-13 entry/player/scheduler/class1f/Coffee-Shop-navigation/neutral-stop/melee/Button1/Button3/type16-projectile/first-encounter differential: PASS (162 real mutations)")
