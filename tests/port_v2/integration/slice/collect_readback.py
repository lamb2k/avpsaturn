#!/usr/bin/env python3
"""Pinned-Yaba semantic and scanout readback for INTEGRATE-03."""

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


def state(mcp, syms):
    result = {}
    for symbol in syms:
        name = symbol.removeprefix("avsp_diag_")
        result[name] = signed(mcp, syms[symbol])
    return result


def wait_frame(mcp, syms, target, timeout):
    symbol = "avsp_diag_slice_frame"
    address = hex(syms[symbol])
    deadline = time.time() + timeout
    mcp.call("pause")
    current = signed(mcp, syms[symbol])
    if target - current > 10:
        mcp.call("resume")
        last_progress = time.time()
        last_current = current
        while time.time() < deadline:
            current = signed(mcp, syms[symbol])
            if current >= target - 10:
                break
            if current != last_current:
                last_current = current
                last_progress = time.time()
            elif time.time() - last_progress >= 0.25:
                # Yaba can report one residual stop after an unfiltered write
                # watchpoint is removed. Resume it here; a real runtime stall
                # still times out because the published frame will not move.
                mcp.call("resume")
                last_progress = time.time()
            time.sleep(0.002)
        mcp.call("pause")
        current = signed(mcp, syms[symbol])
    if current > target:
        raise RuntimeError(f"slice passed frame {target}: {current}")
    if current != target:
        # Stop on each diagnostic publish and inspect the value.  A value-
        # filtered watchpoint is unreliable while Yaba is completing the long
        # initial disc load; the unfiltered write watchpoint remains exact and
        # bounds this loop to at most ten published frames.
        mcp.call("breakpoint_add", cpu="master", type="memory",
                 address=address, write=True)
        try:
            while current < target and time.time() < deadline:
                mcp.call("resume")
                stopped = mcp.call(
                    "wait_for_stop",
                    timeout_ms=max(1, int((deadline - time.time()) * 1000)))
                if "stopped: true" not in stopped:
                    raise TimeoutError(f"slice frame {target} was not reached")
                current = signed(mcp, syms[symbol])
        finally:
            mcp.call("breakpoint_remove", cpu="master", type="memory",
                     address=address)
    result = state(mcp, syms)
    if result["slice_frame"] != target:
        raise RuntimeError(f"slice stopped at {result['slice_frame']}, expected {target}")
    return result


def require_fields(actual, expected, label):
    for name, value in expected.items():
        if actual[name] != value:
            raise RuntimeError(
                f"{label} drifted: {name}={actual[name]} expected {value}")


def validate_hit(actual):
    require_fields(actual, {
        "runtime_ready": 1, "slice_interface_version": 1,
        "slice_frame": 605, "slice_ready": 1, "slice_actor_count": 2,
        "slice_combat_events": 1, "slice_enemy_health": 63,
        "slice_hit_count": 1, "slice_ko_count": 0,
        "slice_hud_render_count": 4, "slice_pcm_events": 1,
        "slice_pcm_active": 1, "slice_cdda_active": 1,
        "slice_cdda_transitions": 1, "slice_late_reads": 0,
        "slice_asset_failures": 0, "slice_fallback_used": 0,
        "slice_canaries_ok": 1, "slice_stability_frames": 606,
        "slice_physical_saturn": 0, "stage_port_lock_ok": 1,
        "hud_port_lock_ok": 1, "slice_review_phase": 3
    }, "playable-slice HIT")
    if actual["enemy_render_count"] <= 0 or \
            actual["slice_stage_submissions"] < 3 or \
            actual["pcm_submit_count"] < 1 or actual["cdda_submit_count"] != 1:
        raise RuntimeError("HIT frame lacks a promoted presentation/audio submit")


def validate_ko(actual):
    require_fields(actual, {
        "runtime_ready": 1, "slice_interface_version": 1,
        "slice_frame": 2480, "slice_ready": 1, "slice_actor_count": 2,
        "slice_combat_events": 4, "slice_enemy_health": -1,
        "slice_hit_count": 1, "slice_ko_count": 1,
        "slice_hud_render_count": 4, "slice_pcm_events": 1,
        "slice_pcm_active": 0, "slice_cdda_active": 1,
        "slice_cdda_transitions": 1, "slice_late_reads": 0,
        "slice_asset_failures": 0, "slice_fallback_used": 0,
        "slice_canaries_ok": 1, "slice_stability_frames": 2481,
        "slice_physical_saturn": 0, "slice_review_phase": 4
    }, "playable-slice KO")
    if actual["enemy_render_count"] <= 0 or \
            actual["combat_transition_anim_record"] != 0x0012E268:
        raise RuntimeError("KO frame lacks the promoted enemy transition")


def validate_final(actual):
    require_fields(actual, {
        "runtime_ready": 1, "slice_frame": 3000, "slice_ready": 1,
        "slice_combat_events": 4, "slice_enemy_health": -1,
        "slice_cdda_active": 0, "slice_cdda_transitions": 2,
        "slice_late_reads": 0, "slice_asset_failures": 0,
        "slice_fallback_used": 0, "slice_canaries_ok": 1,
        "slice_stability_frames": 3001, "slice_physical_saturn": 0,
        "slice_review_phase": 4
    }, "playable-slice final")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    build = json.loads((ROOT / inventory["build_root"] /
                        f"run-{args.run}/build.json").read_text())
    required = inventory["required_readback_symbols"]
    all_symbols = tools.symbols(required)
    syms = {name: all_symbols[name] for name in required}
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
    hit = wait_frame(mcp, syms, 605, args.timeout)
    validate_hit(hit)
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    hit_path = run_root / "hit.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(hit_path)
    ko = wait_frame(mcp, syms, 2480, args.timeout)
    validate_ko(ko)
    ko_path = run_root / "ko.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(ko_path)
    final = wait_frame(mcp, syms, 3000, args.timeout)
    validate_final(final)
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "hit_state": hit, "ko_state": ko, "final_state": final,
        "screenshots": {
            "hit": {"path": hit_path.relative_to(ROOT).as_posix(),
                    "sha256": sha(hit_path), "bytes": hit_path.stat().st_size},
            "ko": {"path": ko_path.relative_to(ROOT).as_posix(),
                   "sha256": sha(ko_path), "bytes": ko_path.stat().st_size}},
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR", "process_id": process["pid"],
                     "executable_sha256": sha(executable),
                     "settings_sha256": sha(settings),
                     "command_line": process["command_line"]},
        "physical_saturn": "UNRUN", "result": "PASS"}
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
