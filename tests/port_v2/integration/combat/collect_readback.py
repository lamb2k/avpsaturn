#!/usr/bin/env python3
"""Pinned-Yaba semantic and visual readback for CombatIntegrationBench."""

import argparse
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = load_module(
    "enemy_bench_readback", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(mcp, address):
    return tools.signed32(mcp.u32(address))


def array(mcp, address, count, signed_values=False):
    values = [mcp.u32(address + index * 4) for index in range(count)]
    if signed_values:
        values = [tools.signed32(value) for value in values]
    return values


def scalar_state(mcp, syms):
    names = [
        "runtime_ready", "player_render_count", "player_canary_ok",
        "player_asset_failures", "player_disc_late_reads",
        "enemy_render_count", "enemy_canary_ok", "enemy_asset_failures",
        "enemy_disc_late_reads", "enemy_tile_bank_misses",
        "enemy_tile_rank_misses", "integration_approval_locks_ok",
        "integration_actor_count", "integration_render_order_ok",
        "integration_canaries_ok", "integration_asset_failures",
        "integration_disc_late_reads", "combat_interface_version",
        "combat_frame", "combat_source_sample", "combat_event_kind",
        "combat_attack_selector", "combat_contact_count",
        "combat_damage_count", "combat_enemy_health", "combat_hit_count",
        "combat_ko_count", "combat_event_count", "combat_transition_state",
        "combat_transition_sub_state", "combat_transition_action",
        "combat_transition_anim_record", "combat_transition_timer",
        "combat_transition_hit_value", "combat_player_attack_active",
        "combat_player_action_frame", "combat_enemy_visual_action",
        "combat_enemy_action_frame", "combat_negative_rejections",
        "combat_failures", "combat_complete", "combat_canary_ok"
        , "combat_missing_code_count", "combat_presented_frame"
    ]
    result = {}
    for name in names:
        symbol = "avsp_diag_" + name
        result[name] = signed(mcp, syms[symbol])
    return result


def wait_frame(mcp, syms, target, timeout):
    address = hex(syms["avsp_diag_combat_presented_frame"])
    deadline = time.time() + timeout
    mcp.call("pause")
    current = signed(mcp, syms["avsp_diag_combat_presented_frame"])
    if target - current > 10:
        mcp.call("resume")
        while time.time() < deadline:
            current = signed(mcp, syms["avsp_diag_combat_presented_frame"])
            if current >= target - 10:
                break
            time.sleep(0.002)
        mcp.call("pause")
        current = signed(mcp, syms["avsp_diag_combat_presented_frame"])
    if current > target:
        raise RuntimeError(
            f"combat passed frame {target} before exact stop: {current}")
    if current == target:
        return scalar_state(mcp, syms)
    mcp.call("breakpoint_add", cpu="master", type="memory", address=address,
             write=True, value=hex(target))
    try:
        while current < target and time.time() < deadline:
            mcp.call("resume")
            stopped = mcp.call(
                "wait_for_stop",
                timeout_ms=max(1, int((deadline - time.time()) * 1000)))
            if "stopped: true" not in stopped:
                raise TimeoutError(f"combat frame {target} was not reached")
            current = signed(mcp, syms["avsp_diag_combat_presented_frame"])
        state = scalar_state(mcp, syms)
        if (state["combat_frame"] != target or
                state["combat_presented_frame"] != target):
            raise RuntimeError(
                f"combat stopped at frame {state['combat_frame']}, expected {target}")
        return state
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=address)


def validate_hit(state):
    expected = {
        "runtime_ready": 1, "integration_approval_locks_ok": 1,
        "integration_actor_count": 2, "integration_render_order_ok": 1,
        "integration_canaries_ok": 1, "integration_asset_failures": 0,
        "integration_disc_late_reads": 0, "combat_interface_version": 1,
        "combat_source_sample": 5190, "combat_event_kind": 3,
        "combat_attack_selector": 1, "combat_contact_count": 1,
        "combat_damage_count": 1, "combat_enemy_health": 63,
        "combat_hit_count": 1, "combat_ko_count": 0,
        "combat_event_count": 1, "combat_transition_state": 1,
        "combat_frame": 185, "combat_presented_frame": 185,
        "combat_enemy_action_frame": 5,
        "combat_player_action_frame": 9,
        "combat_transition_hit_value": 4,
        "combat_negative_rejections": 2, "combat_failures": 0,
        "combat_canary_ok": 1, "combat_enemy_visual_action": 1,
        "player_canary_ok": 1, "player_asset_failures": 0,
        "player_disc_late_reads": 0, "enemy_canary_ok": 1,
        "enemy_asset_failures": 0, "enemy_disc_late_reads": 0,
        "enemy_tile_bank_misses": 0, "enemy_tile_rank_misses": 0
    }
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(f"combat HIT readback drifted: {name}={state[name]} expected {value}")
    if state["player_render_count"] <= 0 or state["enemy_render_count"] <= 0:
        raise RuntimeError("combat HIT frame did not render both approved actors")


def validate_final(state):
    expected = {
        "runtime_ready": 1, "integration_approval_locks_ok": 1,
        "integration_actor_count": 2, "integration_render_order_ok": 1,
        "integration_canaries_ok": 1, "integration_asset_failures": 0,
        "integration_disc_late_reads": 0, "combat_interface_version": 1,
        "combat_source_sample": 5329, "combat_event_kind": 4,
        "combat_attack_selector": 4, "combat_contact_count": 4,
        "combat_damage_count": 4, "combat_enemy_health": -1,
        "combat_hit_count": 1, "combat_ko_count": 1,
        "combat_event_count": 4, "combat_transition_state": 2,
        "combat_transition_sub_state": 0x0600,
        "combat_transition_action": 0,
        "combat_transition_anim_record": 0x0012E268,
        "combat_transition_timer": 6, "combat_transition_hit_value": 0,
        "combat_enemy_visual_action": 2, "combat_negative_rejections": 2,
        "combat_failures": 0, "combat_complete": 1,
        "combat_frame": 860, "combat_presented_frame": 860,
        "combat_enemy_action_frame": 140,
        "combat_canary_ok": 1, "player_canary_ok": 1,
        "player_asset_failures": 0, "player_disc_late_reads": 0,
        "enemy_canary_ok": 1, "enemy_asset_failures": 0,
        "enemy_disc_late_reads": 0, "enemy_tile_bank_misses": 0,
        "enemy_tile_rank_misses": 0
    }
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(f"combat final readback drifted: {name}={state[name]} expected {value}")
    if state["player_render_count"] <= 0 or state["enemy_render_count"] <= 0:
        raise RuntimeError("combat KO frame did not render both approved actors")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    build = json.loads((ROOT / inventory["build_root"] /
                        f"run-{args.run}/build.json").read_text())
    syms = tools.symbols(inventory["required_readback_symbols"])
    mcp = tools.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.25)
    mcp.call("set_debug_option", cpu_core="interpreter")
    mcp.call("pause")
    bounds = tools.window_bounds(args.emulator_pid, args.timeout)
    hit_state = wait_frame(mcp, syms, 185, args.timeout)
    if hit_state["enemy_tile_rank_misses"]:
        count = min(hit_state["combat_missing_code_count"], 16)
        codes = array(mcp, syms["avsp_diag_combat_missing_codes"], count)
        raise RuntimeError(
            f"combat HIT missing tile codes: count={hit_state['combat_missing_code_count']} "
            f"codes={[hex(value) for value in codes]}")
    validate_hit(hit_state)
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    hit_shot = run_root / "hit.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(hit_shot)
    final_state = wait_frame(mcp, syms, 860, args.timeout)
    if final_state["enemy_tile_rank_misses"]:
        count = min(final_state["combat_missing_code_count"], 16)
        codes = array(mcp, syms["avsp_diag_combat_missing_codes"], count)
        raise RuntimeError(
            f"combat KO missing tile codes: count={final_state['combat_missing_code_count']} "
            f"codes={[hex(value) for value in codes]}")
    validate_final(final_state)
    events = {
        "samples": array(mcp, syms["avsp_diag_combat_event_samples"], 4),
        "kinds": array(mcp, syms["avsp_diag_combat_event_kinds"], 4),
        "selectors": array(mcp, syms["avsp_diag_combat_event_selectors"], 4),
        "hit_values": array(mcp, syms["avsp_diag_combat_event_hit_values"], 4),
        "health_before": array(mcp, syms["avsp_diag_combat_event_health_before"], 4, True),
        "health_after": array(mcp, syms["avsp_diag_combat_event_health_after"], 4, True)
    }
    expected_events = {
        "samples": [5190, 5236, 5283, 5329],
        "kinds": [3, 2, 2, 4], "selectors": [1, 2, 3, 4],
        "hit_values": [8, 8, 10, 12],
        "health_before": [87, 63, 39, 8],
        "health_after": [63, 39, 8, -1]
    }
    if events != expected_events:
        raise RuntimeError(f"combat event ledger drifted: {events}")
    ko_shot = run_root / "ko.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(ko_shot)
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "hit_state": hit_state, "final_state": final_state,
        "events": events,
        "screenshots": {
            "hit": {"path": hit_shot.relative_to(ROOT).as_posix(),
                    "sha256": sha(hit_shot), "bytes": hit_shot.stat().st_size},
            "ko": {"path": ko_shot.relative_to(ROOT).as_posix(),
                   "sha256": sha(ko_shot), "bytes": ko_shot.stat().st_size}
        },
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR", "process_id": process["pid"],
                     "executable_sha256": sha(executable),
                     "settings_sha256": sha(settings),
                     "command_line": process["command_line"]},
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
