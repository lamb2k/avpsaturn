#!/usr/bin/env python3
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


tools = load_module("enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
FIELDS = ("frame", "target_active", "target_x", "target_lane", "state",
          "inner_state", "target_id", "x", "lane", "health", "facing",
          "approach_elapsed", "attack_elapsed", "attack_timer", "rng_seed",
          "rng_cursor", "contact", "contact_damage", "removed")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(mcp, address):
    return tools.signed32(mcp.u32(address))


def read_sample(mcp, base, index):
    address = base + index * len(FIELDS) * 4
    return {name:signed(mcp, address + offset * 4)
            for offset, name in enumerate(FIELDS)}


def require_sample(samples, frame, **expected):
    value = samples[frame]
    drift = {key:(value[key], wanted) for key, wanted in expected.items()
             if value[key] != wanted}
    if value["frame"] != frame or drift:
        raise RuntimeError(f"alien AI sample {frame} drifted: {drift or value}")


def validate(samples, state):
    if not (state["runtime_ready"] == state["interface_version"] == 1 and
            state["failures"] == 0 and state["canary_ok"] == 1 and
            state["negative_rejections"] == 2 and state["contacts"] == 3 and
            state["damage_events"] == 3 and state["scheduler_updates"] == 541 and
            state["target_selections"] == 1):
        raise RuntimeError(f"alien AI runtime invariant failed: {state}")
    require_sample(samples, 0, state=2, target_id=1, health=87, x=962, lane=343)
    require_sample(samples, 37, state=3, x=1071, lane=320, attack_timer=120,
                   rng_seed=0x595a, rng_cursor=1)
    require_sample(samples, 85, state=3, attack_elapsed=48, contact=1, contact_damage=8)
    require_sample(samples, 156, state=3, attack_elapsed=119, contact=1, contact_damage=8)
    require_sample(samples, 157, state=2, inner_state=8, attack_timer=0)
    require_sample(samples, 195, state=3, attack_timer=120, rng_seed=0x0c66, rng_cursor=2)
    require_sample(samples, 243, contact=1, contact_damage=8)
    require_sample(samples, 300, state=4, health=63, contact=0)
    require_sample(samples, 338, state=2, health=63)
    require_sample(samples, 400, state=5, health=-1, contact=0)
    require_sample(samples, 540, state=0, health=-1, removed=1)
    require_sample(samples, 575, state=0, removed=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    build = json.loads((ROOT / inventory["build_root"] / f"run-{args.run}/build.json").read_text())
    syms = tools.symbols(inventory["required_readback_symbols"])
    mcp = tools.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize(); break
        except Exception:
            if time.time() >= deadline: raise
            time.sleep(0.25)
    mcp.call("set_debug_option", cpu_core="interpreter")
    bounds = tools.window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and mcp.u32(syms["avsp_diag_alien_ai_sample_count"]) == 576:
            break
        time.sleep(0.02)
    else:
        raise TimeoutError("SALVAGE-11 diagnostic did not complete")
    mcp.call("pause")
    mapping = {"runtime_ready":"avsp_diag_runtime_ready",
               "interface_version":"avsp_diag_alien_ai_interface_version",
               "frame":"avsp_diag_alien_ai_frame", "failures":"avsp_diag_alien_ai_failures",
               "canary_ok":"avsp_diag_alien_ai_canary_ok",
               "negative_rejections":"avsp_diag_alien_ai_negative_rejections",
               "contacts":"avsp_diag_alien_ai_contacts", "damage_events":"avsp_diag_alien_ai_damage_events",
               "scheduler_updates":"avsp_diag_alien_ai_scheduler_updates",
               "target_selections":"avsp_diag_alien_ai_target_selections"}
    state = {key:signed(mcp, syms[value]) for key, value in mapping.items()}
    samples = [read_sample(mcp, syms["avsp_diag_alien_ai_samples"], i) for i in range(576)]
    validate(samples, state)
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    screenshot = run_root / "emulator.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {"schema":1, "task_id":inventory["task_id"], "card_profile":inventory["card_profile"],
              "source_commit":build["source_commit"], "iso_sha256":build["artifacts"]["game_iso"]["sha256"],
              "state":state, "samples":samples,
              "screenshot":{"path":screenshot.relative_to(ROOT).as_posix(), "sha256":sha(screenshot), "bytes":screenshot.stat().st_size},
              "emulator":{"identity":"Yaba Sanshiro 1.20.37-2986eb", "evidence_tier":"ONE_EMULATOR",
                          "process_id":process["pid"], "executable_sha256":sha(executable),
                          "settings_sha256":sha(settings), "command_line":process["command_line"]},
              "physical_saturn":"UNRUN", "result":"PASS"}
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
