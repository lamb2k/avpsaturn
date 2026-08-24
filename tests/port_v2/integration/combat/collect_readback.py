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
        "combat_player_presentation_active", "combat_player_source_pose",
        "combat_player_source_anim_record", "combat_player_source_action",
        "combat_player_source_substate",
        "combat_player_source_object_identity",
        "combat_player_source_tile_identity",
        "combat_player_source_pivot_x", "combat_player_source_pivot_y",
        "combat_player_action_frame", "combat_enemy_visual_action",
        "combat_enemy_action_frame", "combat_negative_rejections",
        "combat_enemy_render_anim_record", "combat_enemy_render_palette",
        "combat_enemy_source_object_identity",
        "combat_enemy_source_tile_identity",
        "combat_enemy_render_object_identity",
        "combat_enemy_render_tile_identity",
        "combat_enemy_render_object_count",
        "combat_enemy_source_event_index", "combat_enemy_source_world_x",
        "combat_enemy_source_world_y", "combat_enemy_source_world_z",
        "combat_failures", "combat_complete", "combat_canary_ok"
        , "combat_missing_code_count", "combat_tile_sprite_misses",
        "combat_presented_frame",
        "combat_player_x", "combat_player_lane", "combat_player_height",
        "combat_player_facing", "combat_enemy_x", "combat_enemy_lane",
        "combat_enemy_height", "combat_enemy_facing",
        "combat_baseline_delta", "combat_attack_toward_target",
        "combat_alignment_ok"
    ]
    result = {}
    for name in names:
        symbol = "avsp_diag_" + name
        result[name] = (mcp.u32(syms[symbol]) if name.endswith("identity")
                        else signed(mcp, syms[symbol]))
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


def validate_common(state, frame):
    expected = {
        "runtime_ready": 1, "integration_approval_locks_ok": 1,
        "integration_actor_count": 2, "integration_render_order_ok": 1,
        "integration_canaries_ok": 1, "integration_asset_failures": 0,
        "integration_disc_late_reads": 0, "combat_interface_version": 2,
        "combat_frame": frame, "combat_presented_frame": frame,
        "combat_negative_rejections": 2, "combat_failures": 0,
        "combat_canary_ok": 1, "player_canary_ok": 1,
        "player_asset_failures": 0, "player_disc_late_reads": 0,
        "enemy_canary_ok": 1, "enemy_asset_failures": 0,
        "enemy_disc_late_reads": 0, "enemy_tile_bank_misses": 0,
        "enemy_tile_rank_misses": 0, "combat_attack_toward_target": 1,
        "combat_alignment_ok": 1, "combat_tile_sprite_misses": 0,
    }
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(
                f"combat frame {frame} drifted: {name}={state[name]} expected {value}")
    if state["player_render_count"] <= 0 or state["enemy_render_count"] <= 0:
        raise RuntimeError(
            f"combat frame {frame} did not render both actors: "
            f"player={state['player_render_count']} "
            f"enemy={state['enemy_render_count']} "
            f"objects={state['combat_enemy_render_object_count']} "
            f"sprite_misses={state['combat_tile_sprite_misses']}")


def validate_event(state, event, event_index, frame, reaction=False):
    validate_common(state, frame)
    expected_kind = (3, 2, 2, 4)[event_index]
    expected = {
        "combat_source_sample": event["contact_frame"],
        "combat_event_kind": expected_kind,
        "combat_attack_selector": event["attack_selector"],
        "combat_contact_count": event_index + 1,
        "combat_damage_count": event_index + 1,
        "combat_enemy_health": event["health_after"],
        "combat_hit_count": 1,
        "combat_ko_count": 1 if event_index == 3 else 0,
        "combat_event_count": event_index + 1,
        "combat_player_presentation_active": 1,
        "combat_player_attack_active": 1,
        "combat_player_source_anim_record": int(
            event["player"]["animation_record"], 16),
        "combat_player_source_object_identity":
            event["player"]["runtime_object_identity_fnv32"],
        "combat_player_source_tile_identity":
            event["player"]["runtime_tile_identity_fnv32"],
        "combat_player_source_pivot_x": event["player"]["pivot"][0],
        "combat_player_x": 264, "combat_player_lane": 208,
        "combat_player_height": event["player"]["height"],
        "combat_player_facing": 1,
        "combat_enemy_render_palette": event["enemy_reaction" if reaction
                                               else "enemy_contact"]["palette"],
        "combat_enemy_render_anim_record": int(
            event["enemy_reaction" if reaction else "enemy_contact"]
            ["animation_record"], 16),
        "combat_enemy_source_object_identity":
            event["enemy_reaction" if reaction else "enemy_contact"]
            ["runtime_object_identity_fnv32"],
        "combat_enemy_source_tile_identity":
            event["enemy_reaction" if reaction else "enemy_contact"]
            ["runtime_tile_identity_fnv32"],
    }
    if reaction:
        expected["combat_enemy_visual_action"] = 2 if event_index == 3 else 1
    else:
        expected["combat_enemy_visual_action"] = 3
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(
                f"event {event_index + 1} frame {frame} drifted: "
                f"{name}={state[name]} expected {value}")
    if (state["combat_enemy_render_object_identity"] !=
            state["combat_enemy_source_object_identity"] or
            state["combat_enemy_render_tile_identity"] !=
            state["combat_enemy_source_tile_identity"] or
            state["combat_enemy_render_object_count"] <= 0):
        raise RuntimeError(
            f"event {event_index + 1} rendered alien identity detached from source: "
            f"object={state['combat_enemy_render_object_identity']}/"
            f"{state['combat_enemy_source_object_identity']} "
            f"tile={state['combat_enemy_render_tile_identity']}/"
            f"{state['combat_enemy_source_tile_identity']} "
            f"count={state['combat_enemy_render_object_count']}")


def validate_final(state, frame):
    validate_common(state, frame)
    expected = {
        "combat_source_sample": 5329, "combat_event_kind": 4,
        "combat_attack_selector": 4, "combat_contact_count": 4,
        "combat_damage_count": 4, "combat_enemy_health": -1,
        "combat_hit_count": 1, "combat_ko_count": 1,
        "combat_event_count": 4, "combat_complete": 1,
        "combat_player_presentation_active": 0,
        "combat_player_attack_active": 0, "combat_player_height": 0,
    }
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(
                f"combat final frame {frame} drifted: "
                f"{name}={state[name]} expected {value}")


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
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    source_contract = json.loads((
        ROOT / "data/avsp_source_combat_presentation_contract.json").read_text())
    event_frames = (186, 232, 279, 325)
    states = []
    screenshots = {}
    for event_index, (event, event_frame) in enumerate(
            zip(source_contract["events"], event_frames)):
        attack_frame = event_frame - 1
        attack_state = wait_frame(mcp, syms, attack_frame, args.timeout)
        validate_common(attack_state, attack_frame)
        attack_path = run_root / f"event-{event_index + 1}-attack.png"
        ImageGrab.grab(bbox=bounds, all_screens=True).save(attack_path)
        contact_state = wait_frame(mcp, syms, event_frame, args.timeout)
        validate_event(contact_state, event, event_index, event_frame)
        contact_path = run_root / f"event-{event_index + 1}-contact.png"
        ImageGrab.grab(bbox=bounds, all_screens=True).save(contact_path)
        reaction_frame = event_frame + 1
        reaction_state = wait_frame(mcp, syms, reaction_frame, args.timeout)
        validate_event(reaction_state, event, event_index, reaction_frame,
                       reaction=True)
        reaction_path = run_root / f"event-{event_index + 1}-reaction.png"
        ImageGrab.grab(bbox=bounds, all_screens=True).save(reaction_path)
        states.append({"attack": attack_state, "contact": contact_state,
                       "reaction": reaction_state})
        for label, path in (("attack", attack_path),
                            ("contact", contact_path),
                            ("reaction", reaction_path)):
            screenshots[f"event_{event_index + 1}_{label}"] = {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha(path), "bytes": path.stat().st_size}
    final_frame = 465
    final_state = wait_frame(mcp, syms, final_frame, args.timeout)
    if final_state["enemy_tile_rank_misses"]:
        count = min(final_state["combat_missing_code_count"], 16)
        codes = array(mcp, syms["avsp_diag_combat_missing_codes"], count)
        raise RuntimeError(
            f"combat KO missing tile codes: count={final_state['combat_missing_code_count']} "
            f"codes={[hex(value) for value in codes]}")
    validate_final(final_state, final_frame)
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
    ko_shot = run_root / "final-ko.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(ko_shot)
    screenshots["final_ko"] = {
        "path": ko_shot.relative_to(ROOT).as_posix(),
        "sha256": sha(ko_shot), "bytes": ko_shot.stat().st_size}
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "event_states": states, "final_state": final_state,
        "events": events,
        "screenshots": screenshots,
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
