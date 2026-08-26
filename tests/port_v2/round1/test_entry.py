#!/usr/bin/env python3
"""Strict host compile and real stable-entry mutations for REIMPLEMENT-13."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "data/spec02_round1_executable_contract.json"
EXPECTED = "cd3a2f050aa4ef3af80ed99d3ba10e9d7ba88d3075053c2fd589fe065645d926"
assert hashlib.sha256(SPEC.read_bytes()).hexdigest() == EXPECTED
assert json.loads(SPEC.read_text())["status"] == "ACCEPTED"
source = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text()
header = (ROOT / "src/port_v2/gameplay/round1/round1.h").read_text()
generated = (ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h").read_text()
subprocess.run(["python", str(ROOT / "tools/gen_spec02_round1_entry.py"), "--check"], check=True)

def wsl(path):
    return subprocess.run(["wsl.exe", "wslpath", "-a", str(path).replace("\\", "/")],
                          check=True, capture_output=True, text=True).stdout.strip()

def run(body, header_body, passes):
    with tempfile.TemporaryDirectory(prefix="round1-entry-") as name:
        temp = Path(name); (temp / "round1.c").write_text(body)
        (temp / "round1.h").write_text(header_body.replace(
            '#include "../player_action/player_action.h"', '#include "player_action.h"'))
        (temp / "spec02_round1_entry_data.h").write_text(generated)
        command = (f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{wsl(temp)}' -I src/port_v2/gameplay/player_action "
                   f"'{wsl(temp / 'round1.c')}' "
                   f"src/port_v2/gameplay/player_action/player_action.c "
                   f"tests/port_v2/round1/round1_entry_test.c -o '{wsl(temp / 'test')}' && "
                   f"'{wsl(temp / 'test')}'")
        result = subprocess.run(["wsl.exe", "bash", "-lc", command], capture_output=True)
        assert (result.returncode == 0) == passes

run(source, header, True)
for before, after in (
    ("runtime->route_state = AVSP_ROUND1_ROUTE_ENTRY_STATE;", "runtime->route_state = 4;"),
    ("{20u, 20u, 16u, 32u}", "{20u, 20u, 16u, 31u}"),
    ("{192u, 128u, 128u, 128u}", "{128u, 128u, 128u, 128u}"),
    ("runtime->rng_seed = AVSP_ROUND1_INITIAL_RNG;", "runtime->rng_seed = 1u;"),
    ("runtime->entry.gate8236 & runtime->entry.gate81af", "runtime->entry.gate8236 | runtime->entry.gate81af"),
    ("--runtime->entry.animation_c8;", "runtime->entry.animation_c8 = 0u;"),
    ("++runtime->entry.timer_decrements;", "runtime->entry.timer_decrements += 2u;"),
    ("pool->free_stack[pool->free_count - 1u]", "pool->free_stack[0]"),
    ("avsp_pw_step(&runtime->player_action, &input);", "input.mask = 0u; avsp_pw_step(&runtime->player_action, &input);"),
    ("if (actor->active == 0u)\n                continue;", "if (actor->active != 0u)\n                continue;"),
    ("pool_index = order_index;", "pool_index = (order_index + 1u) % AVSP_ROUND1_POOL_COUNT;"),
    ("!avsp_round1_dispatch_supported(actor->type,\n                                                actor->actor_class)", "0"),
    ("actor->assembly = presentation->assembly;", "actor->assembly = 0UL;"),
    ("actor->dispatch_entry = AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY;", "actor->dispatch_entry = 0UL;"),
    ("avsp_round1_apply_player_global_bounds(runtime);", "/* bounds suppressed */"),
    ("avsp_round1_update_player_locomotion(runtime, applied_direction,\n                                            was_stopping, &view);", "/* locomotion transition suppressed */"),
    ("avsp_round1_observe_player_melee(runtime, prior_state, prior_selector,\n                                    prior_attack_edges);", "/* melee observation suppressed */"),
    ("++runtime->player_melee_entries;", "runtime->player_melee_entries += 2u;"),
    ("runtime->player_melee_selector_mask |= 1UL << (selector - 1u);", "runtime->player_melee_selector_mask = 0UL;"),
    ("++runtime->player_melee_completions;", "runtime->player_melee_completions += 2u;"),
    ("runtime->player_melee_presentation_mask |= 1UL << index;", "runtime->player_melee_presentation_mask = 0UL;"),
    ("runtime->player_weapon_cadence =\n                    avsp_round1_player_weapon.cadence_reload;", "runtime->player_weapon_cadence = 3u;"),
    ("runtime->player_weapon_attempts =\n        avsp_round1_player_weapon.attempt_initial;", "runtime->player_weapon_attempts = 11;"),
    ("runtime->player_weapon_recovery_pending = 1u;", "runtime->player_weapon_recovery_pending = 0u;"),
    ("runtime->player_resource_recharge =\n                            avsp_round1_player_weapon.recharge_after_success;", "runtime->player_resource_recharge = 11u;"),
    ("++runtime->player_weapon_resource_debits;", "runtime->player_weapon_resource_debits += 2u;"),
    ("++runtime->player_weapon_allocation_failures;", "runtime->player_weapon_allocation_failures += 2u;"),
    ("avsp_round1_tick_player_resource(runtime);", "/* resource tick suppressed */"),
    ("avsp_round1_begin_empty_effect(runtime);", "/* empty effect suppressed */"),
    ("actor->variant = 1u;", "actor->variant = 0u;"),
    ("actor->y = (short)(actor->y + 4);", "actor->y = (short)(actor->y + 3);"),
    ("if (actor->animation_branch < 0)", "if (actor->animation_branch < -32767)"),
    ("++runtime->player_weapon_empty_auxiliary_releases;", "runtime->player_weapon_empty_auxiliary_releases += 2u;"),
):
    assert before in source
    run(source.replace(before, after), header, False)
for before, after in (
    ("{ 0xffa3c0u, 12u, 656, 312, 312,", "{ 0xffa3c0u, 12u, 657, 312, 312,"),
    ("{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 60u,", "{ AVSP_ROUND1_ENTRY_DWELL, 0x00u, 0u, 59u,"),
    ("    12u, 16u, 20u, 24u", "    16u, 12u, 20u, 24u"),
    ("{ 0x0012e8ecUL, 0x0012f5deUL,", "{ 0x0012e8ecUL, 0x0012f994UL,"),
    ("{ 0x0200u, 0x1400u },", "{ 0x0200u, 0x1401u },"),
    ("    720, 256, 752, 1072,", "    720, 256, 752, 1200,"),
    ("    10u,\n    {255u, 2u, 6u, 255u,", "    9u,\n    {255u, 2u, 6u, 255u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1538u,\n    5120u,\n    30u,"),
    ("    1536u,\n    5120u,\n    30u,", "    1536u,\n    5120u,\n    29u,"),
    ("{ 0x1600f8UL, 0x162a04UL, 8u, 1u },", "{ 0x1600f8UL, 0x162a82UL, 8u, 1u },"),
    ("{ 0x1601c0UL, 0x1614a4UL, 8u, 3u },", "{ 0x1601c0UL, 0x1614a4UL, 8u, 2u },"),
    ("    12,\n    1u,\n    4u,", "    11,\n    1u,\n    4u,"),
    ("    3u,\n    12u,\n    2u,", "    2u,\n    12u,\n    2u,"),
    ("{ 3074u, 2u, 0x00165400UL, 0x00166bf8UL, 1u, 0u },", "{ 3074u, 2u, 0x00165410UL, 0x00166bf8UL, 1u, 0u },"),
    ("{ 6658u, 2u, 0x001645d4UL, 0x00166bf8UL, 1u, 0u },", "{ 6658u, 2u, 0x001645d4UL, 0x00166c22UL, 1u, 0u },"),
    ("    40u, 42u, 44u, 46u, 48u, 50u, 49u, 47u, 45u, 43u, 41u, 40u", "    39u, 42u, 44u, 46u, 48u, 50u, 49u, 47u, 45u, 43u, 41u, 40u"),
    ("    { 0, 78 },", "    { 0, 77 },"),
    ("{ 4095u, -32767, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },", "{ 4095u, -32768, 0x0007a12cUL, 0x0007a3a0UL, 0u, 0u },"),
):
    assert before in generated
    changed = generated.replace(before, after, 1)
    with tempfile.TemporaryDirectory(prefix="round1-generated-mutation-") as name:
        temp = Path(name)
        (temp / "round1.c").write_text(source)
        (temp / "round1.h").write_text(header.replace(
            '#include "../player_action/player_action.h"', '#include "player_action.h"'))
        (temp / "spec02_round1_entry_data.h").write_text(changed)
        command = (f"cd '{wsl(ROOT)}' && gcc -std=c90 -pedantic -Wall -Wextra -Werror "
                   f"-I '{wsl(temp)}' -I src/port_v2/gameplay/player_action "
                   f"'{wsl(temp / 'round1.c')}' "
                   f"src/port_v2/gameplay/player_action/player_action.c "
                   f"tests/port_v2/round1/round1_entry_test.c -o '{wsl(temp / 'test')}' && "
                   f"'{wsl(temp / 'test')}'")
        result = subprocess.run(["wsl.exe", "bash", "-lc", command], capture_output=True)
        assert result.returncode != 0, f"generated mutation escaped: {before}"
print("REIMPLEMENT-13 entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Button1 differential: PASS (51 real mutations)")
