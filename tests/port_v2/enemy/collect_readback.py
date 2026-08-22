#!/usr/bin/env python3
"""Pinned-Yaba readback for the promoted enemy interface."""

import argparse, hashlib, importlib.util, json, os, sys, time
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
legacy_path = ROOT / "tests/port_v2/enemy_bench/collect_readback.py"
spec = importlib.util.spec_from_file_location("enemy_bench_readback", legacy_path)
legacy = importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "approved_contract.json").read_text())
    build = json.loads((ROOT / inventory["build_root"] / f"run-{args.run}/build.json").read_text())
    syms = legacy.symbols(inventory["required_readback_symbols"])
    mcp = legacy.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try: mcp.initialize(); break
        except Exception:
            if time.time() >= deadline: raise
            time.sleep(0.25)
    mcp.call("set_debug_option", cpu_core="interpreter")
    bounds = legacy.window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if (mcp.u32(syms["avsp_diag_runtime_ready"]) == 1 and
            mcp.u32(syms["avsp_diag_enemy_interface_version"]) == contract["interface_version"]): break
        time.sleep(0.05)
    else: raise TimeoutError("enemy promotion bench did not become ready")
    samples = {}
    for label in ("stationary", "translated", "repeat_stationary"):
        samples[label] = legacy.wait_frame(mcp, syms, contract["samples"][label]["frame"], args.timeout)
        samples[label]["approval_lock_ok"] = legacy.signed32(mcp.u32(syms["avsp_diag_enemy_approval_lock_ok"]))
        samples[label]["loader_adapter_ok"] = legacy.signed32(mcp.u32(syms["avsp_diag_enemy_loader_adapter_ok"]))
        if label == "translated":
            screenshot = ROOT / inventory["build_root"] / f"run-{args.run}/emulator.png"
            ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    mcp.call("resume")
    actor = contract["source_actor"]
    for label, state in samples.items():
        expected = contract["samples"][label]
        if not (state["runtime_ready"] == 1 and state["interface_version"] == 1 and
                (state["class_id"],state["palette_bank"],state["lane"],state["facing"]) ==
                (actor["class_id"],actor["palette_bank"],actor["lane"],actor["facing"]) and
                (state["phase"],state["x"]) == (expected["phase"],expected["x"]) and
                state["anim_record"] > 0 and state["assembly"] > 0 and
                state["render_count"] >= state["object_count"] > 0 and state["command_code"] >= 0 and
                state["asset_failures"] == 0 and state["negative_rejections"] == 2 and
                state["canary_ok"] == 1 and state["disc_late_reads"] == 0 and
                state["tile_bank_misses"] == 0 and state["tile_rank_misses"] == 0 and
                state["approval_lock_ok"] == 1 and state["loader_adapter_ok"] == 1):
            raise RuntimeError(f"promoted enemy invariant failed at {label}: {state}")
    process = legacy.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {"schema":1, "task_id":inventory["task_id"], "card_profile":inventory["card_profile"],
              "source_commit":build["source_commit"], "iso_sha256":build["artifacts"]["game_iso"]["sha256"],
              "samples":samples, "bounded_stability_frames":samples["repeat_stationary"]["emulator_frame"]-samples["stationary"]["emulator_frame"],
              "final_scanout":{"width":352,"height":224,"screenshot":{"path":screenshot.relative_to(ROOT).as_posix(),"sha256":sha(screenshot),"bytes":screenshot.stat().st_size}},
              "emulator":{"identity":"Yaba Sanshiro 1.20.37-2986eb","evidence_tier":"ONE_EMULATOR",
                          "process_id":process["pid"],"executable_sha256":sha(executable),"settings_sha256":sha(settings),"command_line":process["command_line"]},
              "disabled_systems":contract["disabled_systems"],"physical_saturn":"UNRUN","result":"PASS"}
    output = ROOT / inventory["build_root"] / f"run-{args.run}/readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"recorded {output.relative_to(ROOT)}")

if __name__ == "__main__": main()
