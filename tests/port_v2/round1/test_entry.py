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
EXPECTED = "b1613ab1bbd777abbcbeae7c5521463171c5cc1ad4b12367248a436acbb563af"
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
for before, after in (
    ("runtime->route_state = AVSP_ROUND1_ROUTE_ENTRY_STATE;", "runtime->route_state = 4;"),
    ("{20u, 20u, 16u, 32u}", "{20u, 20u, 16u, 31u}"),
    ("{192u, 128u, 128u, 128u}", "{128u, 128u, 128u, 128u}"),
    ("runtime->rng_seed = AVSP_ROUND1_INITIAL_RNG;", "runtime->rng_seed = 1u;"),
    ("runtime->entry.gate8236 & runtime->entry.gate81af", "runtime->entry.gate8236 | runtime->entry.gate81af"),
    ("--runtime->entry.animation_c8;", "runtime->entry.animation_c8 = 0u;"),
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
    ("projectile->angle = runtime->player.facing ? 17u : 47u;",
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
    ("projectile->y_fp += (long)(low_motion->y + high_motion->y) * 256L;",
     "projectile->y_fp += (long)(low_motion->y + high_motion->y) * 0L;"),
    ("projectile->child_cadence =\n                        avsp_round1_weapon_projectile.child_cadence_reload;",
     "projectile->child_cadence = 5u;"),
    ("projectile->assembly = record->assembly;", "projectile->assembly = 0UL;"),
    ("(unsigned long)old_seed * 3UL &", "(unsigned long)old_seed * 2UL &"),
    ("!(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&\n           runtime->entry.spawned)", "!(runtime->route_state == AVSP_ROUND1_ROUTE_ENTRY_STATE &&\n           0u)"),
    ("transition->x_velocity = actor->facing == 0u ? -0x00030000L :\n            0x00030000L;", "transition->x_velocity = actor->facing == 0u ? -0x00020000L :\n            0x00020000L;"),
    ("transition->y_acceleration = -0x00005000L;", "transition->y_acceleration = 0x00005000L;"),
    ("actor->effect_timer = 42u;", "actor->effect_timer = 41u;"),
    ("runtime->class1f_effect_guard = 0u;", "runtime->class1f_effect_guard = 1u;"),
    ("actor->effect_timer = 3u;", "actor->effect_timer = 2u;"),
    ("table_offset = 28u;", "table_offset = 24u;"),
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
    ("if (encounter->source_intro_gate != 0u)",
     "if (encounter->source_intro_gate == 0u)"),
    ("encounter->source_intro_timer - 1u",
     "encounter->source_intro_timer - 2u"),
    ("(unsigned short)actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot",
     "actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot"),
    ("actor->substate ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state",
     "actor->state ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state"),
    ("encounter->source_living_count >=\n            avsp_round1_recurring_spawn.maximum_living",
     "encounter->source_living_count >\n            avsp_round1_recurring_spawn.maximum_living"),
    ("actor->source_slot = 0x00ff0000UL | (unsigned long)slot;",
     "actor->source_slot = slot;"),
    ("actor->source_slot ==\n                        runtime->first_encounter.actor_source_slot)",
     "actor->source_slot ==\n                        runtime->first_encounter.actor_source_slot + 1u)"),
):
    assert before in source, before
    run(source.replace(before, after), header, False, before)
for before, after in (
    ("{ 0xffa3c0u, 12u, 656, 312, 312,", "{ 0xffa3c0u, 12u, 657, 312, 312,"),
    ("{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 60u,", "{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 59u,"),
    ("    12u, 16u, 20u, 24u", "    16u, 12u, 20u, 24u"),
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
    ("    17u, 35u, 47u", "    17u, 34u, 47u"),
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
    ("0x00ffc580UL, 792, 296, 296, 0x0200u, 0x0000u, 0x08d9a4UL", "0x00ffc580UL, 792, 296, 296, 0x0202u, 0x0000u, 0x08d9a4UL"),
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
print("REIMPLEMENT-13 entry/player/scheduler/class1f/Coffee-Shop-navigation/neutral-stop/melee/Button1/Button3/first-encounter differential: PASS (121 real mutations)")
