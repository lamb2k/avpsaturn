#!/usr/bin/env python3
"""Pinned-Yaba semantic readback for HitKoPromotionBench."""

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


def signed(mcp, syms, name):
    return tools.signed32(mcp.u32(syms[name]))


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
    bounds = tools.window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if (mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and
                mcp.u32(syms["avsp_diag_hit_ko_complete"]) == 1):
            break
        time.sleep(0.02)
    else:
        raise TimeoutError("HIT/KO diagnostic did not complete")
    mcp.call("pause")
    state = {name: signed(mcp, syms, symbol) for name, symbol in {
        "runtime_ready": "avsp_diag_runtime_ready",
        "interface_version": "avsp_diag_hit_ko_interface_version",
        "frame": "avsp_diag_hit_ko_frame",
        "phase": "avsp_diag_hit_ko_phase",
        "sample": "avsp_diag_hit_ko_sample",
        "state": "avsp_diag_hit_ko_state",
        "sub_state": "avsp_diag_hit_ko_sub_state",
        "action": "avsp_diag_hit_ko_action",
        "anim_record": "avsp_diag_hit_ko_anim_record",
        "anim_timer": "avsp_diag_hit_ko_anim_timer",
        "health": "avsp_diag_hit_ko_health",
        "hit_value": "avsp_diag_hit_ko_hit_value",
        "hit_samples": "avsp_diag_hit_ko_hit_sample_count",
        "ko_samples": "avsp_diag_hit_ko_ko_sample_count",
        "negative_rejections": "avsp_diag_hit_ko_negative_rejections",
        "failures": "avsp_diag_hit_ko_failures",
        "complete": "avsp_diag_hit_ko_complete",
        "canary_ok": "avsp_diag_hit_ko_canary_ok"
    }.items()}
    expected = {
        "runtime_ready": 1, "interface_version": 1, "phase": 3,
        "sample": 5469, "state": 2, "sub_state": 0x0600,
        "action": 0, "anim_record": 0x0012E268, "anim_timer": 6,
        "health": -1, "hit_value": 0, "hit_samples": 37,
        "ko_samples": 140, "negative_rejections": 1,
        "failures": 0, "complete": 1, "canary_ok": 1
    }
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(f"HIT/KO readback drifted: {name}={state[name]} expected {value}")
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    screenshot = run_root / "emulator.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "state": state,
        "screenshot": {"path": screenshot.relative_to(ROOT).as_posix(),
                       "sha256": sha(screenshot), "bytes": screenshot.stat().st_size},
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR", "process_id": process["pid"],
                     "executable_sha256": sha(executable),
                     "settings_sha256": sha(settings),
                     "command_line": process["command_line"]},
        "disabled_systems": json.loads((HERE / "approved_contract.json").read_text())["disabled_systems"],
        "physical_saturn": "UNRUN", "result": "PASS"
    }
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
