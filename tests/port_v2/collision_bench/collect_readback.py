#!/usr/bin/env python3
"""Pinned-Yaba readback for the isolated source-collision diagnostic."""

import argparse
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


enemy_tools = load_module(
    "enemy_bench_readback", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


FIELDS = (
    "case_id", "expected_overlap", "overlap", "expected_guarded", "guarded",
    "hit_value", "attacker_x", "attacker_y", "attacker_z", "defender_x",
    "defender_y", "defender_z", "attack_selector", "hurt_selector",
    "table_set_ok", "damage_write_count"
)


def read_signed(mcp, syms, name):
    return enemy_tools.signed32(mcp.u32(syms[name]))


def sample(mcp, base, index):
    address = base + index * len(FIELDS) * 4
    return {name: enemy_tools.signed32(mcp.u32(address + offset * 4))
            for offset, name in enumerate(FIELDS)}


def validate(samples, state, contract):
    expected_overlap = (1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1)
    expected_guarded = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1)
    if len(samples) != contract["expected_case_count"]:
        raise RuntimeError("collision sample count drifted")
    for index, value in enumerate(samples):
        overlap = expected_overlap[index]
        guard = expected_guarded[index]
        hit = contract["expected_hit_value"] if overlap else 0
        if not (value["case_id"] == index and
                value["expected_overlap"] == value["overlap"] == overlap and
                value["expected_guarded"] == value["guarded"] == guard and
                value["hit_value"] == hit and value["table_set_ok"] == 1 and
                value["damage_write_count"] == 0):
            raise RuntimeError(f"collision case {index} drifted: {value}")
    if not (state["runtime_ready"] == 1 and state["interface_version"] == 1 and
            state["negative_rejections"] == contract["expected_negative_rejections"] and
            state["damage_writes"] == state["failures"] == 0 and
            state["canary_ok"] == 1):
        raise RuntimeError(f"collision runtime invariant failed: {state}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "contract.json").read_text())
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
    bounds = enemy_tools.window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if (mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and
                mcp.u32(syms["avsp_diag_collision_sample_count"]) ==
                contract["expected_case_count"] and
                mcp.u32(syms["avsp_diag_collision_frame"]) >= 900):
            break
        time.sleep(0.02)
    else:
        raise TimeoutError("collision diagnostic did not complete a stable cycle")
    mcp.call("pause")
    state = {
        "runtime_ready": read_signed(mcp, syms, "avsp_diag_runtime_ready"),
        "interface_version": read_signed(mcp, syms, "avsp_diag_collision_interface_version"),
        "frame": read_signed(mcp, syms, "avsp_diag_collision_frame"),
        "case": read_signed(mcp, syms, "avsp_diag_collision_case"),
        "overlap": read_signed(mcp, syms, "avsp_diag_collision_overlap"),
        "expected_overlap": read_signed(mcp, syms, "avsp_diag_collision_expected_overlap"),
        "guarded": read_signed(mcp, syms, "avsp_diag_collision_guarded"),
        "expected_guarded": read_signed(mcp, syms, "avsp_diag_collision_expected_guarded"),
        "hit_value": read_signed(mcp, syms, "avsp_diag_collision_hit_value"),
        "table_set_ok": read_signed(mcp, syms, "avsp_diag_collision_table_set_ok"),
        "negative_rejections": read_signed(mcp, syms, "avsp_diag_collision_negative_rejections"),
        "damage_writes": read_signed(mcp, syms, "avsp_diag_collision_damage_writes"),
        "failures": read_signed(mcp, syms, "avsp_diag_collision_failures"),
        "canary_ok": read_signed(mcp, syms, "avsp_diag_collision_canary_ok")
    }
    samples = [sample(mcp, syms["avsp_diag_collision_samples"], index)
               for index in range(contract["expected_case_count"])]
    validate(samples, state, contract)
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    screenshot = run_root / "emulator.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    process = enemy_tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "state": state, "samples": samples,
        "screenshot": {"path": screenshot.relative_to(ROOT).as_posix(),
                       "sha256": sha(screenshot), "bytes": screenshot.stat().st_size},
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR", "process_id": process["pid"],
                     "executable_sha256": sha(executable),
                     "settings_sha256": sha(settings),
                     "command_line": process["command_line"]},
        "disabled_systems": contract["disabled_systems"],
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
