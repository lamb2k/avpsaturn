#!/usr/bin/env python3
"""Pinned-Yaba readback for the SALVAGE-10 action-controller diagnostic."""

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
    "frame", "input_mask", "x", "lane", "height", "health", "facing",
    "state", "phase", "selector", "action_elapsed", "source_action",
    "source_substate", "attack_active", "box_x_center", "box_x_half",
    "box_y_center", "box_y_half", "box_z_center", "box_z_half", "hit_value"
)


def read_signed(mcp, syms, name):
    return enemy_tools.signed32(mcp.u32(syms[name]))


def sample(mcp, base, index):
    address = base + index * len(FIELDS) * 4
    return {name: enemy_tools.signed32(mcp.u32(address + offset * 4))
            for offset, name in enumerate(FIELDS)}


def require_sample(samples, frame, **expected):
    value = samples[frame]
    if value["frame"] != frame:
        raise RuntimeError(f"sample index drift at {frame}: {value}")
    drift = {key: (value[key], wanted) for key, wanted in expected.items()
             if value[key] != wanted}
    if drift:
        raise RuntimeError(f"sample {frame} drifted: {drift}")


def validate(samples, state, contract):
    if len(samples) != contract["expected_sample_count"]:
        raise RuntimeError("SALVAGE-10 sample count drifted")
    required = (
        state["runtime_ready"] == 1 and
        state["interface_version"] == contract["interface_version"] and
        state["failures"] == 0 and state["canary_ok"] == 1 and
        state["negative_rejections"] == contract["expected_negative_rejections"] and
        state["accepted_edges"] == contract["expected_accepted_edges"] and
        state["rejected_edges"] == contract["expected_rejected_edges"] and
        state["contact_reports"] == contract["expected_contact_reports"])
    if not required:
        raise RuntimeError(f"SALVAGE-10 runtime invariant failed: {state}")
    require_sample(samples, 0, x=978, lane=320, state=0)
    require_sample(samples, 1, x=978, lane=320, state=0)
    require_sample(samples, 21, x=1023, lane=320, state=0, facing=1)
    require_sample(samples, 51, x=1023, lane=327, state=0)
    for start, first, last, returned, selector, hit in zip(
            (80, 125, 170, 215), contract["active_first"],
            contract["active_last"], contract["return_frames"],
            contract["attack_selectors"], contract["hit_values"]):
        require_sample(samples, start, state=1, phase=1, selector=selector,
                       action_elapsed=0, attack_active=0)
        require_sample(samples, start + first, state=1, phase=2,
                       selector=selector, action_elapsed=first,
                       attack_active=1, hit_value=hit)
        require_sample(samples, start + last, state=1, phase=2,
                       selector=selector, action_elapsed=last,
                       attack_active=1, hit_value=hit)
        require_sample(samples, start + returned, state=0, phase=0,
                       selector=0, attack_active=0)
    require_sample(samples, 270, health=93, state=2, selector=0,
                   attack_active=0, source_action=514)
    require_sample(samples, 285, health=93, state=0, phase=0)
    require_sample(samples, 310, health=-7, state=3, selector=0,
                   attack_active=0, source_action=1024)
    require_sample(samples, 383, health=-7, state=3)


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
                mcp.u32(syms["avsp_diag_pw_action_sample_count"]) ==
                contract["expected_sample_count"]):
            break
        time.sleep(0.02)
    else:
        raise TimeoutError("SALVAGE-10 diagnostic did not complete")
    mcp.call("pause")
    state = {
        "runtime_ready": read_signed(mcp, syms, "avsp_diag_runtime_ready"),
        "interface_version": read_signed(mcp, syms, "avsp_diag_pw_action_interface_version"),
        "frame": read_signed(mcp, syms, "avsp_diag_pw_action_frame"),
        "failures": read_signed(mcp, syms, "avsp_diag_pw_action_failures"),
        "canary_ok": read_signed(mcp, syms, "avsp_diag_pw_action_canary_ok"),
        "accepted_edges": read_signed(mcp, syms, "avsp_diag_pw_action_accepted_edges"),
        "rejected_edges": read_signed(mcp, syms, "avsp_diag_pw_action_rejected_edges"),
        "contact_reports": read_signed(mcp, syms, "avsp_diag_pw_action_contact_reports"),
        "negative_rejections": read_signed(mcp, syms, "avsp_diag_pw_action_negative_rejections")
    }
    samples = [sample(mcp, syms["avsp_diag_pw_action_samples"], index)
               for index in range(contract["expected_sample_count"])]
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
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
