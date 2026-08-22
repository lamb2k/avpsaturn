#!/usr/bin/env python3
"""Pinned-Yaba readback for simultaneous promoted player and enemy output."""

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


enemy_tools = load_module(
    "enemy_bench_readback",
    ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
player_tools = load_module(
    "player_promotion_readback",
    ROOT / "tests/port_v2/player/collect_readback.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_signed(mcp, syms, name):
    return enemy_tools.signed32(mcp.u32(syms[name]))


def snapshot(mcp, syms):
    player_fields = {
        "frame": "avsp_diag_player_frame",
        "input_mask": "avsp_diag_player_input_mask",
        "input_edges": "avsp_diag_player_input_edges",
        "x": "avsp_diag_player_x", "lane": "avsp_diag_player_lane",
        "facing": "avsp_diag_player_facing", "pose": "avsp_diag_player_pose",
        "cel_left": "avsp_diag_player_cel_left",
        "cel_top": "avsp_diag_player_cel_top",
        "cel_right": "avsp_diag_player_cel_right",
        "cel_bottom": "avsp_diag_player_cel_bottom",
        "render_count": "avsp_diag_player_render_count",
        "canary_ok": "avsp_diag_player_canary_ok",
        "asset_failures": "avsp_diag_player_asset_failures",
        "disc_late_reads": "avsp_diag_player_disc_late_reads",
        "interface_version": "avsp_diag_player_interface_version",
        "approval_lock_ok": "avsp_diag_player_approval_lock_ok",
        "loader_adapter_ok": "avsp_diag_player_loader_adapter_ok"
    }
    integration_fields = {
        "frame": "avsp_diag_integration_frame",
        "interface_version": "avsp_diag_integration_interface_version",
        "approval_locks_ok": "avsp_diag_integration_approval_locks_ok",
        "loader_order_ok": "avsp_diag_integration_loader_order_ok",
        "actor_count": "avsp_diag_integration_actor_count",
        "render_order_ok": "avsp_diag_integration_render_order_ok",
        "render_command_count": "avsp_diag_integration_render_command_count",
        "canaries_ok": "avsp_diag_integration_canaries_ok",
        "asset_failures": "avsp_diag_integration_asset_failures",
        "disc_late_reads": "avsp_diag_integration_disc_late_reads"
    }
    enemy = enemy_tools.snapshot(mcp, syms)
    enemy["approval_lock_ok"] = read_signed(
        mcp, syms, "avsp_diag_enemy_approval_lock_ok")
    enemy["loader_adapter_ok"] = read_signed(
        mcp, syms, "avsp_diag_enemy_loader_adapter_ok")
    return {
        "runtime_ready": read_signed(mcp, syms, "avsp_diag_runtime_ready"),
        "player": {name: read_signed(mcp, syms, symbol)
                   for name, symbol in player_fields.items()},
        "enemy": enemy,
        "integration": {name: read_signed(mcp, syms, symbol)
                        for name, symbol in integration_fields.items()}
    }


def wait_frame(mcp, syms, target, timeout):
    # Co-residency changes the BSS neighborhood, and this emulator's memory
    # breakpoint backend can stop on a write to another word in the watched
    # block. Poll the published source-frame counter, pause immediately, and
    # accept only a pause that confirms the exact value is still current.
    deadline = time.time() + timeout
    mcp.call("resume")
    while time.time() < deadline:
        if enemy_tools.signed32(
                mcp.u32(syms["avsp_diag_enemy_frame"])) == target:
            mcp.call("pause")
            if enemy_tools.signed32(
                    mcp.u32(syms["avsp_diag_enemy_frame"])) == target:
                state = snapshot(mcp, syms)
                if state["enemy"]["relative_frame"] == target:
                    return state
            mcp.call("resume")
    raise TimeoutError(f"enemy frame {target} was not confirmed")


def validate(state, contract):
    player = state["player"]
    enemy = state["enemy"]
    integration = state["integration"]
    expected = contract["enemy"]
    if not (state["runtime_ready"] == 1 and
            player["interface_version"] == player["approval_lock_ok"] ==
            player["loader_adapter_ok"] == player["canary_ok"] == 1 and
            player["asset_failures"] == player["disc_late_reads"] == 0 and
            player["render_count"] in (2, 3) and
            0 <= player["cel_left"] < player["cel_right"] <= 192 and
            0 <= player["cel_top"] < player["cel_bottom"] <= 192 and
            enemy["interface_version"] == 1 and
            enemy["class_id"] == expected["class_id"] and
            enemy["palette_bank"] == expected["palette_bank"] and
            enemy["lane"] == expected["lane"] and
            enemy["facing"] == expected["facing"] and
            enemy["render_count"] == 32 and enemy["object_count"] == 5 and
            enemy["negative_rejections"] == 2 and
            enemy["canary_ok"] == 1 and enemy["asset_failures"] == 0 and
            enemy["disc_late_reads"] == 0 and enemy["tile_bank_misses"] == 0 and
            enemy["tile_rank_misses"] == 0 and
            enemy["approval_lock_ok"] == enemy["loader_adapter_ok"] == 1 and
            integration["interface_version"] == 1 and
            integration["approval_locks_ok"] == 1 and
            integration["loader_order_ok"] == 1 and
            integration["actor_count"] == contract["actor_count"] and
            integration["render_order_ok"] == 1 and
            integration["render_command_count"] ==
            player["render_count"] + enemy["render_count"] and
            integration["canaries_ok"] == 1 and
            integration["asset_failures"] == 0 and
            integration["disc_late_reads"] == 0):
        raise RuntimeError(f"integration invariant failed: {state}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "approved_contract.json").read_text())
    build = json.loads((ROOT / inventory["build_root"] /
                        f"run-{args.run}/build.json").read_text())
    syms = enemy_tools.symbols(inventory["required_readback_symbols"])
    mcp = enemy_tools.Mcp("http://127.0.0.1:9640/mcp")
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
    hwnd, bounds = player_tools.wait_window(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if (mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and
                mcp.u32(syms["avsp_diag_integration_interface_version"]) == 1):
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("player/enemy integration did not become ready")
    samples = {}
    screenshot = None
    vdp1_commands = None
    for label in ("stationary", "translated", "repeat_stationary"):
        expected = contract["enemy"]["samples"][label]
        samples[label] = wait_frame(mcp, syms, expected["frame"], args.timeout)
        enemy = samples[label]["enemy"]
        if (enemy["phase"], enemy["x"]) != (expected["phase"], expected["x"]):
            raise RuntimeError(f"enemy schedule drifted at {label}: {enemy}")
        validate(samples[label], contract)
        if label == "translated":
            run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
            screenshot = run_root / "emulator.png"
            ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
            vdp1_commands = player_tools.capture_vdp1(mcp)
    mcp.call("resume")
    right_before, right_live, right_after = player_tools.pulse(
        mcp, syms, hwnd, "RIGHT", 2, args.timeout)
    if not (right_after["x"] > right_before["x"] and
            right_after["facing"] == 1 and right_live["render_count"] == 3):
        raise RuntimeError("integrated player input/render response drifted")
    final = snapshot(mcp, syms)
    validate(final, contract)
    if final["integration"]["render_command_count"] != contract["idle_render_commands"]:
        raise RuntimeError("combined idle render count drifted after input release")
    process = enemy_tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "samples": samples,
        "player_input": {"right": {"before": right_before,
                                     "during": right_live,
                                     "after": right_after}},
        "final": final,
        "vdp1_command_count": len(vdp1_commands),
        "screenshot": {"path": screenshot.relative_to(ROOT).as_posix(),
                       "sha256": sha(screenshot), "bytes": screenshot.stat().st_size},
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR",
                     "process_id": process["pid"],
                     "executable_sha256": sha(executable),
                     "settings_sha256": sha(settings),
                     "command_line": process["command_line"]},
        "disabled_systems": contract["disabled_systems"],
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = ROOT / inventory["build_root"] / f"run-{args.run}/readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
