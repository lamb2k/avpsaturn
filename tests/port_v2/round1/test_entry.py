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
EXPECTED = "12c61b100077e5494170def25b8522fe4084b33ebf44b2edd7e53ea9ec887ea5"
assert hashlib.sha256(SPEC.read_bytes()).hexdigest() == EXPECTED
assert json.loads(SPEC.read_text())["status"] == "ACCEPTED"
source = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text()
header = (ROOT / "src/port_v2/gameplay/round1/round1.h").read_text()
generated = (ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h").read_text()
player_source = (ROOT / "src/port_v2/gameplay/player_action/player_action.c").read_text()
test_source = (ROOT / "tests/port_v2/round1/round1_entry_test.c").read_text()
assert EXPECTED in header
subprocess.run(["python", str(ROOT / "tools/gen_spec02_round1_entry.py"), "--check"], check=True)

def wsl(path):
    return subprocess.run(["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root", "--",
                           "wslpath", "-a",
                           str(path).replace("\\", "/")],
                          check=True, capture_output=True, text=True).stdout.strip()

def run(body, header_body, passes, label="baseline", player_body=player_source,
        expected_returncode=None, generated_body=None, test_body=None):
    with tempfile.TemporaryDirectory(prefix="round1-entry-") as name:
        temp = Path(name)
        linux_output = f"/tmp/{temp.name}-test"
        if generated_body is None:
            generated_body = generated
        if test_body is None:
            test_body = test_source
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
        (temp / "spec02_round1_entry_data.h").write_text(generated_body)
        (temp / "player_action.c").write_text(player_body)
        (temp / "round1_entry_test.c").write_text(test_body)
        command = (f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{wsl(temp)}' -I . -I src/port_v2/gameplay/player_action "
                   f"-I src/port_v2/gameplay/street_alien_ai -I src/port_v2/combat/hit_ko "
                   f"-I src/port_v2/integration/combat "
                   f"'{wsl(temp / 'round1.c')}' "
                   f"avsp_actor.c avsp_collision.c "
                   f"'{wsl(temp / 'player_action.c')}' "
                   f"src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
                   f"src/port_v2/combat/hit_ko/hit_ko.c "
                   f"src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
                   f"src/port_v2/integration/player_enemy/player_enemy.c "
                   f"src/port_v2/integration/combat/combat.c "
                   f"'{wsl(temp / 'round1_entry_test.c')}' -o '{linux_output}' && "
                   f"ulimit -s unlimited && '{linux_output}'")
        result = subprocess.run(["wsl.exe", "-d", "Ubuntu-24.04", "-u", "root",
                                 "--", "bash", "-lc", command],
                                capture_output=True)
        if expected_returncode is not None:
            assert result.returncode == expected_returncode, (
                f"label={label}\nexpected_returncode={expected_returncode}\n"
                f"returncode={result.returncode}\n" +
                result.stdout.decode(errors="replace") +
                result.stderr.decode(errors="replace"))
            return
        assert (result.returncode == 0) == passes, (
            f"label={label}\nreturncode={result.returncode}\n" +
            result.stdout.decode(errors="replace") +
            result.stderr.decode(errors="replace"))

jump_stop_marker = "    {\n        AvspRound1Runtime contextual = runtime;"
assert jump_stop_marker in test_source
jump_test_body = test_source.replace(
    jump_stop_marker, "    return 0;\n" + jump_stop_marker, 1)

run(source, header, True,
    expected_returncode=(123 if "--weapon-timing-only" in sys.argv else
                         123 if "--contextual-melee-only" in sys.argv else
                         123 if "--locomotion-only" in sys.argv else
                         123 if "--generated-walk-only" in sys.argv else
                         123 if "--controller-edge-only" in sys.argv else
                         123 if "--player-hit-only" in sys.argv else
                         123 if "--action0c-only" in sys.argv else
                         123 if "--inner8-only" in sys.argv else
                         123 if "--type16-terminal-only" in sys.argv else
                         123 if "--special-input-only" in sys.argv else
                         None),
    test_body=(jump_test_body if "--jump-only" in sys.argv else None))
if "--baseline-only" in sys.argv:
    print("REIMPLEMENT-13 focused baseline: PASS")
    raise SystemExit(0)
queue_before = """    for (index = AVSP_PW_DIRECTION_LATENCY - 1; index > 0; --index)
        runtime->direction_history[index] = runtime->direction_history[index - 1];
    runtime->direction_history[0] = direction_mask;
    delayed_direction = runtime->direction_history[AVSP_PW_DIRECTION_LATENCY - 1];"""
queue_after = """    delayed_direction = runtime->direction_history[AVSP_PW_DIRECTION_LATENCY - 1];
    for (index = AVSP_PW_DIRECTION_LATENCY - 1; index > 0; --index)
        runtime->direction_history[index] = runtime->direction_history[index - 1];
    runtime->direction_history[0] = direction_mask;"""
assert queue_before in player_source
subset_flags = {"--inner8-only", "--ko-only", "--registration-only",
                "--locomotion-only", "--generated-walk-only",
                "--controller-edge-only", "--player-hit-only",
                "--weapon-timing-only", "--contextual-melee-only",
                "--action0c-only", "--jump-only",
                "--type16-terminal-only", "--special-input-only"}
if "--queue-only" in sys.argv or not subset_flags.intersection(sys.argv):
    run(source, header, False, "consume-before-direction-queue-shift",
        player_source.replace(queue_before, queue_after, 1))
if "--queue-only" in sys.argv:
    print("REIMPLEMENT-13 direction-queue-order mutation lane: PASS (1 real mutation)")
    raise SystemExit(0)
inner8_mutations = {
    "    if (record == 0)\n"
    "        record = avsp_round1_find_class1f_inner8_record(address);\n"
    "    return record;",
    "(actor->state == 0x0200u &&\n                      (actor->substate == 0x1000u ||",
    "actor->state = 0x0208u;\n    actor->substate = 0x0600u;",
    "if ((*random_out & 3u) != 0u)",
    "*rng_consumed = 1u;",
    "actor->source_motion_fields[0] = 8;\n        actor->source_action_timer =",
    "actor->source_x_fp += actor->source_x_velocity;",
    "            *value = runtime->camera_x_previous;",
    "            --actor->source_action_timer;\n"
    "            if (actor->source_action_timer != 0u)",
    "record = avsp_round1_class1f_inner8_program.\n"
    "        action10_phase_records_by_style_relation[index];",
    "            if (actor->source_style85 != 0u)\n"
    "            {\n"
    "                actor->substate = 0x0802u;",
    "        if (phase == 2u)\n"
    "        {\n"
    "            if (actor->animation_branch < 0)\n"
    "            {\n"
    "                actor->source_style85 = 0u;\n"
    "                actor->substate = 0x0e00u;",
    "            actor->source_airborne = 0u;\n"
    "            actor->source_motion_fields[0] = 6;\n"
    "            actor->source_projectile_enable = 1u;",
    "target->facing = (unsigned char)(target->source_facing_selector ^\n"
    "                avsp_round1_class1f_collision_reaction_facing_xor);",
    "actor->transition_timer = (unsigned short)(actor->transition_timer - 1u);",
}
type16_terminal_mutations = {
    "        if (projectile->animation_branch < 0)\n"
    "        {\n"
    "            if (projectile->transition_timer != 0u)"
}
special_input_mutations = {
    "        !special_physical_candidate && jump_edge &&\n"
    "        runtime->player_action.state == AVSP_PW_STATE_CONTROL)"
}
ko_mutations = {
    "actor->state = ko ? avsp_round1_class1f_source_ko.collision_state :",
    "actor->source_hit_recovery_active = 2u;",
    "actor->source_y_velocity = spec->launch_y_velocity;",
    "actor->source_hit_action_timer =\n                avsp_round1_class1f_source_ko.removal_hold_timer;",
    "runtime->first_encounter.source_progress = (unsigned short)(\n        runtime->first_encounter.source_progress +\n        avsp_round1_recurring_spawn.progress_increment);",
}
registration_mutations = {
    "if (runtime->player_weapon_projectiles[slot_index].active &&\n            runtime->player_weapon_projectiles[slot_index].state !=\n                avsp_round1_weapon_projectile.initial_state)",
}
locomotion_mutations = {
    "if (next >= AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)",
    "const long denominator = 20L;",
    "runtime->player_weapon_cleanup_pending = 0u;\n        weapon_return_owned = 1u;",
    "weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||\n"
    "        (jump_owned && !jump_began) || special_owned || contextual_owned);",
    "if (weapon_motion_hold)\n        input.mask = (unsigned short)(input.mask &\n            (unsigned short)~AVSP_PW_INPUT_ATTACK);",
    "if (!was_stopping && !weapon_motion_hold &&\n"
    "        avsp_round1_source_direction(applied_direction) == 2u)",
}
controller_edge_mutations = {
    "camera_x = avsp_round1_recurring_spawn.camera_edge_uses_current_position ?\n        (unsigned short)runtime->camera_x_position :\n        (unsigned short)runtime->camera_x_previous;",
    "encounter->source_blocked_by_living_count = 1u;\n    }\n    else",
}
player_hit_mutations = {
    "runtime->player_hit_x_fp = runtime->player.source_x_fp;",
    "if (resolved_x != bounded_x)",
    "runtime->player_hit_x_fp = avsp_round1_replace_fixed_high_word(\n"
    "            runtime->player_hit_x_fp, resolved_x);",
    "if (!runtime->player_hit_active && runtime->player_hit_invulnerability)\n"
    "        runtime->player_hit_invulnerability = 0u;",
    "avsp_round1_replace_fixed_high_word(\n"
    "                control_source_x_fp, view.x);",
    "runtime->player_hit_shake_remaining =\n            reaction->shake_count;",
    "runtime, &reaction->presentation);",
    "runtime->player_hit_x_velocity =\n                reaction->x_velocity;",
    "runtime->player_hit_x_acceleration =\n                reaction->x_acceleration;",
    "runtime->player_hit_special_pending = 1u;",
    "runtime->player_action.health - reaction->damage",
    "(unsigned char)reaction->damage;",
    "runtime->player.hurt_selector !=\n"
    "                avsp_round1_type16.player_hurt_selector ||",
}
weapon_timing_mutations = {
    "else if (weapon_owned || contextual_owned)\n    {\n"
    "        runtime->player.source_x_fp = view.x != bounded_player_x ?",
    "runtime->player_weapon_tick = 1u;",
    "runtime->player_weapon_dispatch_delay =\n"
    "        avsp_round1_player_weapon.action_dispatch_delay_updates;",
    "runtime->player.source_action = entry_action;",
    "avsp_round1_player_stage_progress.action_entry_tick +\n"
    "                    avsp_round1_player_weapon.\n"
    "                        action_dispatch_delay_updates",
    "avsp_round1_player_weapon.resource_debit_tick +\n"
    "                    avsp_round1_player_weapon.\n"
    "                        action_dispatch_delay_updates",
    "avsp_round1_player_weapon.parent_allocation_tick +\n"
    "                    avsp_round1_player_weapon.\n"
    "                        action_dispatch_delay_updates",
    "if (runtime->player_weapon_dispatch_delay != 0u)\n"
    "    {\n"
    "        --runtime->player_weapon_dispatch_delay;\n"
    "        return 1;\n"
    "    }",
}
contextual_melee_mutations = {
    "runtime->player.source_target_low =\n"
    "            avsp_round1_player_contextual_melee.target_low;",
    "unsigned char index = runtime->player_action.facing != 0 ? 0u : 1u;",
    "runtime->player_contextual_melee_dispatch_delay = 2u;",
    "avsp_round1_player_contextual_melee.active_action;",
    "if (runtime->player_contextual_melee_animation_branch < 0)",
    "avsp_round1_player_contextual_melee.audio_commands[\n"
    "                    runtime->player_contextual_melee_entries];",
    "(jump_owned && !jump_began) || special_owned || contextual_owned);",
    "if (runtime->player_contextual_melee_active && weapon_edge &&",
}
action0c_mutations = {
    "    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT)\n"
    "        return 0u;",
}
jump_mutations = {
    "runtime->player_jump_dispatch_delay =\n"
    "        avsp_round1_player_jump_timing.dispatch_delay_counter;",
    "if (avsp_round1_player_jump_timing.preserve_landing_fraction)",
    "runtime->player.animation_timer = avsp_round1_player_jump_timing.neutral_timer;",
    "runtime->player.animation_branch = avsp_round1_player_jump_timing.neutral_branch;",
    "runtime->player_jump_y_fp += runtime->player_jump_y_velocity;",
    "if (facing != 0u)\n        {\n"
    "            runtime->player_jump_x_velocity =\n"
    "                -runtime->player_jump_x_velocity;",
}
for before, after in (
    ("runtime->player.source_target_low =\n"
     "            avsp_round1_player_contextual_melee.target_low;",
     "runtime->player.source_target_low = 0u;"),
    ("unsigned char index = runtime->player_action.facing != 0 ? 0u : 1u;",
     "unsigned char index = runtime->player_action.facing != 0 ? 1u : 0u;"),
    ("runtime->player_contextual_melee_dispatch_delay = 2u;",
     "runtime->player_contextual_melee_dispatch_delay = 0u;"),
    ("avsp_round1_player_contextual_melee.active_action;",
     "avsp_round1_player_contextual_melee.common_action;"),
    ("if (runtime->player_contextual_melee_animation_branch < 0)",
     "if (runtime->player_contextual_melee_animation_branch == -32768)"),
    ("avsp_round1_player_contextual_melee.audio_commands[\n"
     "                    runtime->player_contextual_melee_entries];",
     "avsp_round1_player_contextual_melee.audio_commands[0];"),
    ("(jump_owned && !jump_began) || special_owned || contextual_owned);",
     "(jump_owned && !jump_began) || special_owned);"),
    ("if (runtime->player_contextual_melee_active && weapon_edge &&",
     "if (0 && runtime->player_contextual_melee_active && weapon_edge &&"),
    ("    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT)\n"
     "        return 0u;",
     "    if (stage >= AVSP_ROUND1_CLASS1F_ACTION4_STAGE_COUNT ||\n"
     "        stage != avsp_round1_class1f_inner8_program.\n"
     "            action0c_observed_stage_parameter)\n"
     "        return 0u;"),
    ("    bank = avsp_round1_class1f_inner8_program.action4_timer_bank_by_stage[\n"
     "        runtime->source_stage_parameter];",
     "    bank = avsp_round1_class1f_inner8_program.action4_timer_bank_by_stage[\n"
     "        avsp_round1_class1f_inner8_program.action4_stage_parameter];"),
    ("    if (actor->source_navigation_contact_bits != 0u)\n"
     "        actor->source_direction = (unsigned char)(\n"
     "            (actor->source_direction +\n"
     "             avsp_round1_class1f_inner8_program.\n"
     "                action4_contact_direction_delta) &\n"
     "            avsp_round1_class1f_inner8_program.action4_direction_mask);",
     "    if (actor->source_navigation_contact_bits == 0u)\n"
     "        actor->source_direction = (unsigned char)(\n"
     "            (actor->source_direction +\n"
     "             avsp_round1_class1f_inner8_program.\n"
     "                action4_contact_direction_delta) &\n"
     "            avsp_round1_class1f_inner8_program.action4_direction_mask);"),
    ("            *value = runtime->camera_x_previous;",
     "            *value = runtime->camera_x_position;"),
    ("            --actor->source_action_timer;\n"
     "            if (actor->source_action_timer != 0u)",
     "            if (actor->source_action_timer == 0u)\n"
     "                return 0;\n"
     "            --actor->source_action_timer;\n"
     "            if (actor->source_action_timer != 0u)"),
    ("    return (unsigned short)runtime->camera_x_previous;",
     "    return (unsigned short)runtime->camera_x_position;"),
    ("            if (!avsp_round1_step_coffee_shop_camera(runtime))\n"
     "            {\n"
     "                ++runtime->failure_count;\n"
     "                return 0;\n"
     "            }",
     "            /* first route-4 camera update suppressed */"),
    ("    effect->animation_timer = retained_animation_timer;\n"
     "    effect->animation_branch = retained_animation_branch;",
     "    effect->animation_timer = 0u;\n"
     "    effect->animation_branch = 0;"),
    ("        if (actor->animation_timer == 0u)\n"
     "            return 0;\n"
     "        --actor->animation_timer;\n"
     "        if (actor->animation_branch < 0)\n"
     "        {\n"
     "            actor->state = 0x0400u;\n"
     "            return 1;\n"
     "        }",
     "        if (actor->animation_branch < 0)\n"
     "        {\n"
     "            actor->state = 0x0400u;\n"
     "            return 1;\n"
     "        }\n"
     "        if (actor->animation_timer == 0u)\n"
     "            return 0;\n"
     "        --actor->animation_timer;"),
    ("if (!avsp_round1_allocate_class4e_impact_to_player(\n"
     "                runtime, actor, &attack, &hurt,\n"
     "                avsp_round1_class1f_player_collision.impact_variant))",
     "if (0)"),
    ("runtime->player.source_facing_selector =\n"
     "            (unsigned char)(actor->x < runtime->player.x);",
     "runtime->player.source_facing_selector = 0u;"),
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
    ("actor->assembly = action_record->assembly;\n        actor->hurt_selector = action_record->hurt_selector;\n        actor->attack_selector = action_record->attack_selector;",
     "actor->assembly = action_record->assembly;\n        actor->hurt_selector = action_record->hurt_selector;\n        actor->attack_selector = actor->source_a6;"),
    ("actor->dispatch_entry = AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY;", "actor->dispatch_entry = 0UL;"),
    ("avsp_round1_apply_player_global_bounds(runtime);", "/* bounds suppressed */"),
    ("avsp_round1_update_player_locomotion(runtime, applied_direction,\n                                            was_stopping, &view);", "/* locomotion transition suppressed */"),
    ("if (next >= AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)",
     "if (next > AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT)"),
    ("const long denominator = 20L;", "const long denominator = 19L;"),
    ("runtime->player_weapon_cleanup_pending = 0u;\n        weapon_return_owned = 1u;",
     "runtime->player_weapon_cleanup_pending = 0u;\n        runtime->player_weapon_return_pending = 1u;\n        weapon_return_owned = 1u;"),
    ("weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||\n"
     "        (jump_owned && !jump_began) || special_owned || contextual_owned);",
     "weapon_motion_hold = (unsigned char)(runtime->player_weapon_active ||\n"
     "        weapon_return_owned || (jump_owned && !jump_began) ||\n"
     "        special_owned || contextual_owned);"),
    ("if (weapon_motion_hold)\n        input.mask = (unsigned short)(input.mask &\n            (unsigned short)~AVSP_PW_INPUT_ATTACK);",
     "if (weapon_motion_hold)\n        input.mask = (unsigned short)(input.mask & (unsigned short)~(\n            AVSP_PW_INPUT_LEFT | AVSP_PW_INPUT_RIGHT |\n            AVSP_PW_INPUT_UP | AVSP_PW_INPUT_DOWN |\n            AVSP_PW_INPUT_ATTACK));"),
    ("avsp_round1_observe_player_melee(runtime, prior_state, prior_selector,\n                                    prior_attack_edges);", "/* melee observation suppressed */"),
    ("++runtime->player_melee_entries;", "runtime->player_melee_entries += 2u;"),
    ("runtime->player_melee_selector_mask |= 1UL << (selector - 1u);", "runtime->player_melee_selector_mask = 0UL;"),
    ("++runtime->player_melee_completions;", "runtime->player_melee_completions += 2u;"),
    ("runtime->player_melee_presentation_mask |= 1UL << index;", "runtime->player_melee_presentation_mask = 0UL;"),
    ("projectile->angle = runtime->player_weapon_target_angle;",
     "projectile->angle = 0u;"),
    ("*presentation_selector =\n        avsp_round1_weapon_target_presentation_selectors[distance_selector];",
     "*presentation_selector = 4u;"),
    ("projectile->actor_class = avsp_round1_player_weapon.parent_class;",
     "projectile->actor_class = avsp_round1_player_weapon.child_class;"),
    ("runtime->player_action.state = prior_state;", "runtime->player_action.state = AVSP_PW_STATE_ATTACK;"),
    ("runtime->player_resource_recharge =\n            avsp_round1_player_weapon.recharge_after_success;", "runtime->player_resource_recharge = 11u;"),
    ("++runtime->player_weapon_resource_debits;", "runtime->player_weapon_resource_debits += 2u;"),
    ("++runtime->player_weapon_allocation_failures;", "runtime->player_weapon_allocation_failures += 2u;"),
    ("avsp_round1_tick_player_resource(runtime);", "/* resource tick suppressed */"),
    ("avsp_round1_begin_empty_effect(runtime);", "/* empty effect suppressed */"),
    ("actor->variant = avsp_round1_player_weapon.empty_effect_variant;",
     "actor->variant = (unsigned char)(avsp_round1_player_weapon.empty_effect_variant + 1u);"),
    ("runtime->player_weapon_tick ==\n            avsp_round1_player_weapon.empty_effect_allocation_tick",
     "runtime->player_weapon_tick == 0u"),
    ("runtime->player_weapon_tick ==\n"
     "                avsp_round1_player_weapon.parent_allocation_tick",
     "runtime->player_weapon_tick == (unsigned char)(\n"
     "                avsp_round1_player_weapon.parent_allocation_tick + 1u)"),
    ("avsp_round1_allocate_pool_actor_preserve_position_residue(runtime, 3u);",
     "avsp_round1_allocate_pool_actor(runtime, 3u);"),
    ("actor->y = (short)(actor->y + 4);", "actor->y = (short)(actor->y + 3);"),
    ("if (actor->animation_branch < 0)", "if (actor->animation_branch < -32767)"),
    ("++runtime->player_weapon_empty_auxiliary_releases;", "runtime->player_weapon_empty_auxiliary_releases += 2u;"),
    ("projectile->collision_result = -1;", "projectile->collision_result = 0;"),
    ("avsp_round1_weapon_parent_impact_variants[attack_index] :",
     "0u :"),
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
    ("actor->hurt_selector = action_record->hurt_selector;",
     "actor->hurt_selector = actor->source_a5;"),
    ("actor->assembly = presentation->assembly;\n    actor->hurt_selector = presentation->hurt_selector;\n    actor->attack_selector = presentation->attack_selector;",
     "actor->assembly = presentation->assembly;\n    actor->hurt_selector = actor->source_a5;\n    actor->attack_selector = actor->source_a6;"),
    ("actor->source_style85 =\n        avsp_round1_class1f_source_hit.normal_return_style85;",
     "actor->source_style85 = 1u;"),
    ("slot == 0xc600u", "slot == 0xc580u"),
    ("AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT - 1u -\n                allocation_index",
     "allocation_index"),
    ("runtime->class45_rng_calls += 7u;",
     "runtime->class45_rng_calls += 6u;"),
    ("if (!avsp_round1_spawn_class43_population(runtime, actor))",
     "if (1)"),
    ("runtime->class43_rng_calls +=\n            avsp_round1_class43.rng_calls_per_actor;",
     "runtime->class43_rng_calls += 6u;"),
    ("random & (actor->variant == 0u ? 0x1fu : 0x07u)",
     "random & 0x07u"),
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
    ("runtime->player_jump_dispatch_delay =\n"
     "        avsp_round1_player_jump_timing.dispatch_delay_counter;",
     "runtime->player_jump_dispatch_delay = (unsigned char)(\n"
     "        avsp_round1_player_jump_timing.dispatch_delay_counter + 1u);"),
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
    ("if (avsp_round1_player_jump_timing.preserve_landing_fraction)",
     "if (0)"),
    ("runtime->player.animation_timer = avsp_round1_player_jump_timing.neutral_timer;",
     "runtime->player.animation_timer = (unsigned short)(\n"
     "        avsp_round1_player_jump_timing.neutral_timer - 1u);"),
    ("runtime->player.animation_branch = avsp_round1_player_jump_timing.neutral_branch;",
     "runtime->player.animation_branch = 0;"),
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
    ("effect->effect_timer = avsp_round1_parent_weapon_effect.timer;",
     "effect->effect_timer = 7u;"),
    ("(runtime->scheduler_frames & 1u) == 0u",
     "(runtime->scheduler_frames & 2u) == 0u"),
    ("encounter->source_phase_counter + 1u",
     "encounter->source_phase_counter + 2u"),
    ("return entry->updates;", "return 1u;"),
    ("if (encounter->source_intro_gate != 0u)",
     "if (encounter->source_intro_gate == 0u)"),
    ("runtime->camera_z_lower = (short)\n"
     "            avsp_round1_recurring_spawn.source_camera_target_current;",
     "runtime->camera_z_lower = (short)\n"
     "            avsp_round1_recurring_spawn.source_camera_bound_initial;"),
    ("if (preserve_collision_selectors)\n        {\n"
     "            avsp_round1_class1f_bind_source_hit_record(",
     "if (!preserve_collision_selectors)\n        {\n"
     "            avsp_round1_class1f_bind_source_hit_record("),
    ("encounter->source_intro_timer - 1u",
     "encounter->source_intro_timer - 2u"),
    ("(unsigned short)actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot",
     "actor->source_slot ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_slot"),
    ("actor->state ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state",
     "actor->substate ==\n                    avsp_round1_recurring_spawn.intro_gate_owner_state"),
    ("encounter->source_living_count >=\n            avsp_round1_recurring_spawn.maximum_living",
     "encounter->source_living_count >\n            avsp_round1_recurring_spawn.maximum_living"),
    ("camera_x = avsp_round1_recurring_spawn.camera_edge_uses_current_position ?\n        (unsigned short)runtime->camera_x_position :\n        (unsigned short)runtime->camera_x_previous;",
     "camera_x = avsp_round1_recurring_spawn.camera_edge_uses_current_position ?\n        (unsigned short)runtime->camera_x_previous :\n        (unsigned short)runtime->camera_x_position;"),
    ("encounter->source_blocked_by_living_count = 1u;\n    }\n    else",
     "encounter->source_blocked_by_living_count = 1u;\n        return 1;\n    }\n    else"),
    ("if (avsp_round1_recurring_spawn.preserve_reused_presentation != 0u)",
     "if (0)"),
    ("avsp_round1_class1f_action_program.fall_initial_selector",
     "35u"),
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
    ("projectile->animation_record = animation_record;\n    projectile->assembly = assembly;",
     "projectile->animation_record = 0UL;\n    projectile->assembly = assembly;"),
    ("projectile->x_fp = (long)x_fraction;",
     "projectile->x_fp = 0L;"),
    ("unsigned short nearest = 0xffffu;",
     "unsigned short nearest = 0x00ffu;"),
    ("runtime->camera_x_position +\n            avsp_round1_weapon_projectile.x_bound_bias",
     "runtime->navigation_bound_x +\n            avsp_round1_weapon_projectile.x_bound_bias"),
    ("projectile->state = avsp_round1_weapon_projectile.emitter_state;\n            projectile->child_cadence =\n                avsp_round1_weapon_projectile.child_cadence_initial;\n            return 1;",
     "return avsp_round1_release_player_weapon_projectile(runtime, index);"),
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
    ("runtime->player.hurt_selector !=\n                avsp_round1_type16.player_hurt_selector ||",
     "runtime->player.hurt_selector ==\n                avsp_round1_type16.player_hurt_selector ||"),
    ("(unsigned char)avsp_round1_type16.damage;",
     "(unsigned char)(avsp_round1_type16.damage - 1);"),
    ("++runtime->type16_releases;",
     "runtime->type16_releases += 2u;"),
    ("actor->type == 16u && actor->actor_class == 0x06",
     "actor->type == 16u && actor->actor_class == 0x05"),
    ("if (projectile->health < 0)\n        {\n            projectile->state = 0x0600u;",
     "if (projectile->health < 0)\n        {\n            projectile->state = 0x0400u;"),
    ("runtime->player_action.health - reaction->damage",
     "runtime->player_action.health - (short)hit_value"),
    ("(unsigned char)reaction->damage;",
     "hit_value;"),
    ("        if (projectile->animation_branch < 0)\n"
     "        {\n"
     "            if (projectile->transition_timer != 0u)",
     "        if (projectile->animation_timer == 0u)\n"
     "        {\n"
     "            if (projectile->transition_timer != 0u)"),
    ("        !special_physical_candidate && jump_edge &&\n"
     "        runtime->player_action.state == AVSP_PW_STATE_CONTROL)",
     "        jump_edge &&\n"
     "        runtime->player_action.state == AVSP_PW_STATE_CONTROL)"),
    ("(actor->state == 0x0200u &&\n                      (actor->substate == 0x1000u ||",
     "(actor->state == 0x0208u &&\n                      (actor->substate == 0x1000u ||"),
    ("actor->state = 0x0208u;\n    actor->substate = 0x0600u;",
     "actor->state = 0x0200u;\n    actor->substate = 0x0600u;"),
    ("if ((*random_out & 3u) != 0u)",
     "if ((*random_out & 3u) != 3u)"),
    ("*rng_consumed = 1u;",
     "*rng_consumed = 0u;"),
    ("actor->source_motion_fields[0] = 8;\n        actor->source_action_timer =",
     "actor->source_motion_fields[0] = 6;\n        actor->source_action_timer ="),
    ("actor->source_x_fp += actor->source_x_velocity;",
     "actor->source_x_fp += 0;"),
    ("record = avsp_round1_class1f_inner8_program.\n"
     "        action10_phase_records_by_style_relation[index];",
     "record = avsp_round1_class1f_inner8_program.\n"
     "        movement_records_by_style_relation[index];"),
    ("            if (actor->source_style85 != 0u)\n"
     "            {\n"
     "                actor->substate = 0x0802u;",
     "            if (actor->source_style85 == 0u)\n"
     "            {\n"
     "                actor->substate = 0x0802u;"),
    ("        if (phase == 2u)\n"
     "        {\n"
     "            if (actor->animation_branch < 0)\n"
     "            {\n"
     "                actor->source_style85 = 0u;\n"
     "                actor->substate = 0x0e00u;",
     "        if (phase == 2u)\n"
     "        {\n"
     "            if (actor->animation_branch < 0)\n"
     "            {\n"
     "                actor->source_style85 = 0u;\n"
     "                actor->substate = 0x0400u;"),
    ("            actor->source_airborne = 0u;\n"
     "            actor->source_motion_fields[0] = 6;\n"
     "            actor->source_projectile_enable = 1u;",
     "            actor->source_y_fp = (long)(\n"
     "                ((unsigned long)(unsigned short)actor->z << 16) |\n"
     "                ((unsigned long)actor->source_y_fp & 0x0000ffffUL));\n"
     "            actor->y = actor->z;\n"
     "            actor->source_airborne = 0u;\n"
     "            actor->source_motion_fields[0] = 6;\n"
     "            actor->source_projectile_enable = 1u;"),
    ("target->facing = (unsigned char)(target->source_facing_selector ^\n"
     "                avsp_round1_class1f_collision_reaction_facing_xor);",
     "target->facing = (unsigned char)target->source_facing_selector;"),
    ("actor->transition_timer = (unsigned short)(actor->transition_timer - 1u);",
     "if (actor->transition_timer != 0u)\n"
     "        --actor->transition_timer;"),
    ("actor->animation_record = animation_record;",
     "actor->animation_record = 0UL;"),
    ("actor->state = ko ? avsp_round1_class1f_source_ko.collision_state :",
     "actor->state = ko ? avsp_round1_class1f_source_ko.dispatch_state :"),
    ("actor->source_hit_recovery_active = 2u;",
     "actor->source_hit_recovery_active = 1u;"),
    ("actor->source_y_velocity = spec->launch_y_velocity;",
     "actor->source_y_velocity = 0L;"),
    ("actor->source_hit_action_timer =\n                avsp_round1_class1f_source_ko.removal_hold_timer;",
     "actor->source_hit_action_timer =\n                avsp_round1_class1f_source_ko.landing_hold_timer;"),
    ("runtime->first_encounter.source_progress = (unsigned short)(\n        runtime->first_encounter.source_progress +\n        avsp_round1_recurring_spawn.progress_increment);",
     "runtime->first_encounter.source_progress = (unsigned short)(\n        runtime->first_encounter.source_progress + 0u);"),
    ("effect->attack_selector = 0u;\n    }\n    if (effect->state == 2u)",
     "effect->attack_selector = 0u;\n        return 1;\n    }\n    if (effect->state == 2u)"),
    ("runtime->player.animation_branch = record->branch;",
     "runtime->player.animation_branch = 0;"),
    ("runtime->player.animation_timer =\n        runtime->player_special_animation_timer;",
     "runtime->player.animation_timer = 0u;"),
    ("if (!was_in_camera)\n                avsp_round1_bind_animation_state(",
     "if (0)\n                avsp_round1_bind_animation_state("),
    ("actor->source_hitstop = hit_value;\n        actor->source_player_guard = 1u;",
     "actor->source_hitstop = hit_value;\n        actor->source_player_guard = 0u;"),
    ("else if (runtime->player.animation_timer != 0u)\n                --runtime->player.animation_timer;",
     "else if (runtime->player.animation_timer != 0u)\n                runtime->player.animation_timer = runtime->player.animation_timer;"),
    ("if (!avsp_round1_step_coffee_shop_obstacle_parent_animation(actor))\n            return 0;",
     "if (0)\n            return 0;"),
    ("(unsigned short)runtime->camera_x_previous < spec->camera_threshold",
     "(unsigned short)runtime->camera_x_position < spec->camera_threshold"),
    ("runtime->player.animation_timer = frame->timer;\n    runtime->player.animation_branch = frame->branch;",
     "runtime->player.animation_timer = 4095u;\n    runtime->player.animation_branch = -32768;"),
    ("runtime->player_hit_shake_remaining =\n            reaction->shake_count;",
     "runtime->player_hit_shake_remaining =\n            avsp_round1_player_hit.shake_count;"),
    ("runtime, &reaction->presentation);",
     "runtime, &avsp_round1_player_hit.hit_record);"),
    ("runtime->player_hit_x_velocity =\n                reaction->x_velocity;",
     "runtime->player_hit_x_velocity =\n                avsp_round1_player_hit.x_velocity;"),
    ("runtime->player_hit_x_acceleration =\n                reaction->x_acceleration;",
     "runtime->player_hit_x_acceleration = 0L;"),
    ("runtime->player_hit_special_pending = 1u;",
     "runtime->player_hit_special_pending = 0u;"),
    ("runtime->player_hit_x_fp = runtime->player.source_x_fp;",
     "runtime->player_hit_x_fp =\n"
     "        (long)runtime->player_action.x * 65536L;"),
    ("if (resolved_x != bounded_x)",
     "if (resolved_x != proposed_x)"),
    ("runtime->player_hit_x_fp = avsp_round1_replace_fixed_high_word(\n"
     "            runtime->player_hit_x_fp, resolved_x);",
     "runtime->player_hit_x_fp = (long)resolved_x * 65536L;"),
    ("if (!runtime->player_hit_active && runtime->player_hit_invulnerability)\n"
     "        runtime->player_hit_invulnerability = 0u;",
     "if (!runtime->player_hit_active && runtime->player_hit_invulnerability)\n"
     "    {\n"
     "        runtime->player_hit_invulnerability = 0u;\n"
     "        runtime->player.source_x_fp = 0L;\n"
     "        runtime->player.source_y_fp = 0L;\n"
     "    }"),
    ("avsp_round1_replace_fixed_high_word(\n"
     "                control_source_x_fp, view.x);",
     "avsp_round1_player_fractional_position(\n"
     "                view.x, runtime->player_action.x_numerator);"),
    ("if (!was_stopping && !weapon_motion_hold &&\n"
     "        avsp_round1_source_direction(applied_direction) == 2u)",
     "if (0 && !was_stopping && !weapon_motion_hold &&\n"
     "        avsp_round1_source_direction(applied_direction) == 2u)"),
    ("12u, 0x1f, record->attack_selector);",
     "12u, 0x1f, 1u);"),
    ("special_buttons = runtime->player_special_input_pipeline;",
     "special_buttons = (unsigned char)(input_mask & 0x70u);"),
    ("if (avsp_round1_player_special_guard(\n                runtime, special_buttons,",
     "if (0 && avsp_round1_player_special_guard(\n                runtime, special_buttons,"),
    ("sufficient_entry_preserves_current_presentation)",
     "sufficient_entry_preserves_current_presentation == 0u)"),
    ("runtime->player_weapon_tick = 1u;",
     "runtime->player_weapon_tick = 0u;"),
    ("else if (weapon_owned || contextual_owned)\n    {\n"
     "        runtime->player.source_x_fp = view.x != bounded_player_x ?",
     "else if ((weapon_owned && 0) || contextual_owned)\n    {\n"
     "        runtime->player.source_x_fp = view.x != bounded_player_x ?"),
    ("runtime->player_weapon_dispatch_delay =\n"
     "        avsp_round1_player_weapon.action_dispatch_delay_updates;",
     "runtime->player_weapon_dispatch_delay = 0u;"),
    ("runtime->player.source_action = entry_action;",
     "runtime->player.source_action = 0u;"),
    ("avsp_round1_player_stage_progress.action_entry_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates",
     "avsp_round1_player_stage_progress.action_entry_tick"),
    ("avsp_round1_player_weapon.resource_debit_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates",
     "avsp_round1_player_weapon.resource_debit_tick"),
    ("avsp_round1_player_weapon.parent_allocation_tick +\n"
     "                    avsp_round1_player_weapon.\n"
     "                        action_dispatch_delay_updates",
     "avsp_round1_player_weapon.parent_allocation_tick"),
    ("if (runtime->player_weapon_dispatch_delay != 0u)\n"
     "    {\n"
     "        --runtime->player_weapon_dispatch_delay;\n"
     "        return 1;\n"
     "    }",
     "if (runtime->player_weapon_dispatch_delay != 0u)\n"
     "    {\n"
     "        if (runtime->player_weapon_empty &&\n"
     "            runtime->player_weapon_tick ==\n"
     "                avsp_round1_player_weapon.empty_effect_allocation_tick)\n"
     "        {\n"
     "            ++runtime->player_weapon_empty_auxiliary_requests;\n"
     "            avsp_round1_begin_empty_effect(runtime);\n"
     "        }\n"
     "        --runtime->player_weapon_dispatch_delay;\n"
     "        return 1;\n"
     "    }"),
    ("else if (!avsp_round1_step_player_weapon_animation(runtime, frame))\n            return 0;",
     "else if (0)\n            return 0;"),
    ("if (runtime->player_weapon_projectiles[slot_index].active &&\n            runtime->player_weapon_projectiles[slot_index].state !=\n                avsp_round1_weapon_projectile.initial_state)",
     "if (runtime->player_weapon_projectiles[slot_index].active)"),
):
    if "--inner8-only" in sys.argv and before not in inner8_mutations:
        continue
    if "--ko-only" in sys.argv and before not in ko_mutations:
        continue
    if "--registration-only" in sys.argv and before not in registration_mutations:
        continue
    if "--locomotion-only" in sys.argv and before not in locomotion_mutations:
        continue
    if "--controller-edge-only" in sys.argv and before not in controller_edge_mutations:
        continue
    if "--player-hit-only" in sys.argv and before not in player_hit_mutations:
        continue
    if "--weapon-timing-only" in sys.argv and before not in weapon_timing_mutations:
        continue
    if "--contextual-melee-only" in sys.argv and before not in contextual_melee_mutations:
        continue
    if "--action0c-only" in sys.argv and before not in action0c_mutations:
        continue
    if "--jump-only" in sys.argv and before not in jump_mutations:
        continue
    if ("--type16-terminal-only" in sys.argv and
            before not in type16_terminal_mutations):
        continue
    if ("--special-input-only" in sys.argv and
            before not in special_input_mutations):
        continue
    if "--generated-walk-only" in sys.argv:
        continue
    assert before in source, before
    run(source.replace(before, after), header, False, before,
        test_body=(jump_test_body if "--jump-only" in sys.argv else None),
        expected_returncode=(94 if "--action0c-only" in sys.argv
                             else None))
if "--inner8-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f inner-state mutation lane: PASS (15 real mutations)")
    raise SystemExit(0)
if "--ko-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f projectile KO mutation lane: PASS (5 real mutations)")
    raise SystemExit(0)
if "--registration-only" in sys.argv:
    print("REIMPLEMENT-13 deferred record-4 registration mutation lane: PASS (1 real mutation)")
    raise SystemExit(0)
if "--contextual-melee-only" in sys.argv:
    print("REIMPLEMENT-13 contextual Button2 mutation lane: PASS (8 real mutations)")
    raise SystemExit(0)
if "--locomotion-only" in sys.argv:
    print("REIMPLEMENT-13 locomotion/weapon-return mutation lane: PASS (6 real mutations)")
    raise SystemExit(0)
if ("--controller-edge-only" in sys.argv or
        not subset_flags.intersection(sys.argv)):
    pre_before = """            if (phase_updates != 0u && scene_runtime.entry.spawned &&
                !avsp_round1_step_scheduler_pre_player_source_differential(
                    &scene_runtime, source_updates != 0u))
                return 112;
"""
    post_before = """            if (phase_updates != 0u && scene_runtime.entry.spawned)
            {
                if (!avsp_round1_step_scheduler_post_player_source_differential(
"""
    assert pre_before in test_source
    assert post_before in test_source
    post_after = """            if (phase_updates != 0u && scene_runtime.entry.spawned)
            {
                if (!avsp_round1_step_scheduler_pre_player_source_differential(
                        &scene_runtime, source_updates != 0u))
                    return 112;
                if (!avsp_round1_step_scheduler_post_player_source_differential(
"""
    post_player_controller = test_source.replace(pre_before, "", 1).replace(
        post_before, post_after, 1)
    run(source, header, False, "post-player-recurring-controller",
        expected_returncode=117, test_body=post_player_controller)
    if "--controller-edge-only" in sys.argv:
        print("REIMPLEMENT-13 controller camera-edge mutation lane: PASS (3 real mutations)")
        raise SystemExit(0)
if "--player-hit-only" in sys.argv:
    print("REIMPLEMENT-13 Coffee Shop player-HIT program mutation lane: PASS (11 real mutations)")
    raise SystemExit(0)
if ("--weapon-timing-only" in sys.argv or
        not subset_flags.intersection(sys.argv)):
    generated_resource_before = """    16u,
    1u,
    1u,
    1u,
    64u,
"""
    generated_resource_after = """    16u,
    1u,
    1u,
    0u,
    64u,
"""
    assert generated.count(generated_resource_before) == 1
    run(source, header, False, "generated-resource-debit-tick",
        generated_body=generated.replace(
            generated_resource_before, generated_resource_after, 1))
    if "--weapon-timing-only" in sys.argv:
        print("REIMPLEMENT-13 Button1 timing mutation lane: PASS (9 real mutations)")
        raise SystemExit(0)
if "--action0c-only" in sys.argv:
    print("REIMPLEMENT-13 class-0x1f action-0x0c timer-row mutation lane: PASS (1 real mutation)")
    raise SystemExit(0)
if "--jump-only" in sys.argv:
    generated_jump_timing = (
        "    1u, 1u, 2u, 5u, 10u, 1u, 4095u, -32768")
    assert generated.count(generated_jump_timing) == 1
    for label, changed_timing in (
        ("dispatch-delay", "    1u, 1u, 1u, 5u, 10u, 1u, 4095u, -32768"),
        ("same-facing-selector", "    1u, 1u, 2u, 6u, 10u, 1u, 4095u, -32768"),
        ("landing-fraction", "    1u, 1u, 2u, 5u, 10u, 0u, 4095u, -32768"),
        ("neutral-timer", "    1u, 1u, 2u, 5u, 10u, 1u, 4094u, -32768"),
        ("neutral-branch", "    1u, 1u, 2u, 5u, 10u, 1u, 4095u, 0"),
    ):
        run(source, header, False, "generated-jump-" + label,
            generated_body=generated.replace(
                generated_jump_timing, changed_timing, 1),
            test_body=jump_test_body)
    print("REIMPLEMENT-13 Button3 source-timing mutation lane: PASS (11 real mutations)")
    raise SystemExit(0)
if "--type16-terminal-only" in sys.argv:
    print("REIMPLEMENT-13 type16 terminal action-timer lane: PASS "
          "(1 real mutation)")
    raise SystemExit(0)
if "--special-input-only" in sys.argv:
    print("REIMPLEMENT-13 simultaneous special-input arbitration lane: PASS "
          "(1 real mutation)")
    raise SystemExit(0)
generated_walk_mutations = {
    "    { 4u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },",
    "    { 4u, -32768, 0x0015F2B8UL, 0x00160B9EUL, 17u, 0u },",
    "    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
    "    147456L,",
}
for before, after in (
    ("    { 4u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },",
     "    { 3u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },"),
    ("    { 4u, 0, 0x0015F208UL, 0x00160A02UL, 17u, 0u },",
     "    { 4u, 0, 0x0015F208UL, 0x00160A2AUL, 17u, 0u },"),
    ("    { 4u, -32768, 0x0015F2B8UL, 0x00160B9EUL, 17u, 0u },",
     "    { 4u, 0, 0x0015F2B8UL, 0x00160B9EUL, 17u, 0u },"),
    ("    0x0400u, 0x0402u, 0x0404u, 0x0600u,",
     "    0x0402u, 0x0402u, 0x0404u, 0x0600u,"),
    ("    114688L, 0L, 622592L, -20480L,",
     "    114688L, 0L, 618496L, -20480L,"),
    ("    2u, 0x36u, 0u, 0x15u, 8u, 3u, 60u, 6u,",
     "    2u, 0x36u, 0u, 0x15u, 8u, 3u, 59u, 6u,"),
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
    ("    147456L,", "    147455L,"),
    ("    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
     "    514u,\n    516u,\n    512u,\n    9u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,"),
    ("    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
     "    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    16u,\n    0u,\n    {255u, 2u, 6u, 255u,"),
    ("    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    0u,\n    {255u, 2u, 6u, 255u,",
     "    514u,\n    516u,\n    512u,\n    10u,\n    147456L,\n    17u,\n    1u,\n    {255u, 2u, 6u, 255u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1538u,\n    5120u,\n    30u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1536u,\n    5120u,\n    29u,"),
    ("{ 0x1600f8UL, 0x162a04UL, 8u, 1u },", "{ 0x1600f8UL, 0x162a82UL, 8u, 1u },"),
    ("{ 0x1601c0UL, 0x1614a4UL, 8u, 3u },", "{ 0x1601c0UL, 0x1614a4UL, 8u, 2u },"),
    ("    40u,\n    12u,\n    3u,\n    6u,\n    1u,",
     "    39u,\n    12u,\n    3u,\n    6u,\n    1u,"),
    ("    40u,\n    12u,\n    3u,\n    6u,\n    1u,\n    1u,\n    1u,\n    0u,\n    1u,\n    1u,\n    0,\n    4,",
     "    40u,\n    12u,\n    3u,\n    6u,\n    1u,\n    0u,\n    1u,\n    0u,\n    1u,\n    1u,\n    0,\n    4,"),
    ("{ 3074u, 2u, 0x0015e594UL, 0x0016179aUL, 1u, 0u, 2u, 0 },",
     "{ 3074u, 2u, 0x00165410UL, 0x00166c22UL, 1u, 0u, 2u, 0 },"),
    ("{ 6658u, 2u, 0x0015fcfcUL, 0x00161772UL, 1u, 0u, 4095u, -32768 },",
     "{ 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u, 4095u, -32768 },"),
    ("    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 47u",
     "    17u, 18u, 19u, 20u, 21u, 22u, 23u, 24u, 25u, 26u, 27u, 28u, 29u, 30u, 31u, 32u, 33u, 34u, 35u, 36u, 37u, 38u, 39u, 40u, 41u, 42u, 43u, 44u, 45u, 46u, 46u"),
    ("    { 5, 86 },", "    { 6, 86 },"),
    ("    { 0, 84 },", "    { 0, 83 },"),
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
    ("0x43, 0u, 2u, 4u, 7u, 80, -1, 0x08ce44UL",
     "0x43, 0u, 1u, 4u, 7u, 80, -1, 0x08ce44UL"),
    ("0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u",
     "0u, 1u, 2u, 3u, 4u, 5u, 6u, 0u, 1u, 2u, 3u, 3u, 5u, 6u, 0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 7u, 8u, 7u, 8u, 0u, 1u, 2u, 3u, 4u"),
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
    ("    2750u, 1u, 17u, 10u, 10u,\n"
     "    { -37, 53, 38u, 8u, 0, 8u, 0, 10u, 0u },\n"
     "    { 1, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }",
     "    2750u, 1u, 17u, 10u, 10u,\n"
     "    { -37, 53, 38u, 8u, 0, 8u, 0, 10u, 0u },\n"
     "    { 101, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }"),
    ("    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,\n"
     "    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },\n"
     "    { 1, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }",
     "    -59, 64, 0x0058u, 0x0232u, 17, 16u, 0x06, 1u, 20u,\n"
     "    { 0, 0, 8u, 8u, 0, 8u, 0, 20u, 10u },\n"
     "    { 101, 45, 20u, 46u, 0, 6u, 0, 0u, 0u }"),
    ("    { 524288L, -8192L, 262144L, -16384L, 0L },",
     "    { 524287L, -8192L, 262144L, -16384L, 0L },"),
    ("    { 1u, 1, 0x0012e580UL, 0x00130946UL, 8u, 0u },",
     "    { 1u, 0, 0x0012e580UL, 0x00130946UL, 8u, 0u },"),
    ("    0u, 10u, 138u",
     "    0u, 1u, 138u"),
    ("    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 1u",
     "    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 0u"),
    ("    0x08F080UL, 24u, 0x49, 0u, 8u, 1u, 1u",
     "    0x08F080UL, 24u, 0x49, 0u, 7u, 1u, 1u"),
    ("    10u, 2u, 1u, 0u, 0x003Bu,",
     "    10u, 2u, 1u, 0u, 0x003Au,"),
    ("    10u, 2u, 1u, 0u, 0x003Bu,",
     "    10u, 2u, 0u, 0u, 0x003Bu,"),
    ("    114688L, -8192L,",
     "    114687L, -8192L,"),
    ("    { 1u, 0, 0x0015f278UL, 0x00160af2UL, 17u, 0u },",
     "    { 1u, 0, 0x0015f278UL, 0x00160af2UL, 16u, 0u },"),
    ("    { 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2 }",
     "    { 3, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2, 2, -2 }"),
    ("    0x00ffc300UL, 2751u, 0xeea3u, 0xcb6eu, 1095, 369, 319, 24u, 0x4e, 0u",
     "    0x00ffc380UL, 2751u, 0xeea3u, 0xcb6eu, 1095, 369, 319, 24u, 0x4e, 0u"),
    ("    0x00ffc300UL, 2751u, 0xeea3u, 0xcb6eu, 1095, 369, 319, 24u, 0x4e, 0u",
     "    0x00ffc300UL, 2751u, 0xeea3u, 0xcb6eu, 1096, 369, 319, 24u, 0x4e, 0u"),
    ("    { 4u, 0, 0x000928e0UL, 0x00092be8UL, 0u, 0u },",
     "    { 4u, 0, 0x000928f0UL, 0x00092be8UL, 0u, 0u },"),
    ("    { 4095u, -32768, 0x00092900UL, 0x00092bf6UL, 0u, 0u },",
     "    { 4095u, -32768, 0x00092910UL, 0x00092bf6UL, 0u, 0u },"),
):
    if "--generated-walk-only" in sys.argv and before not in generated_walk_mutations:
        continue
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
if "--generated-walk-only" in sys.argv:
    print("REIMPLEMENT-13 generated walk fixture mutation lane: PASS (6 real mutations)")
    raise SystemExit(0)
print("REIMPLEMENT-13 entry/player/scheduler/class1f/Coffee-Shop-navigation/neutral-stop/melee/Button1/Button3/type16-projectile/player-HIT/first-encounter differential: PASS (224 real mutations)")
