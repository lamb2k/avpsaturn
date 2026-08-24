#!/usr/bin/env python3
"""Collect the fixed Probe 3 work-RAM block from pinned Yaba Sanshiro."""

from __future__ import annotations

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
COMMON = ROOT / "tests" / "port_v2" / "enemy_bench" / "collect_readback.py"
spec = importlib.util.spec_from_file_location("probe3_common", COMMON)
tools = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tools)

FIELDS = (
    "canary_begin", "magic", "schema", "status", "mode", "mode_frame",
    "frame_number", "workload_checksum_word", "reachable_commands",
    "drawn_commands", "vdp1_draw_end_state", "draw_end_deadline_fields",
    "cpu_prepare_ticks", "texture_bytes_copied", "copy_count", "copy_ticks",
    "legal_copy_direction", "cram_writes", "cartridge_read_bytes",
    "missed_fields", "late_command_lists", "skipped_fields",
    "repeated_fields", "canary_state", "asset_failures", "failure_reason",
    "overload_expected", "overload_tripped", "representative_high_water",
    "peak_high_water", "summary_checksum", "complete",
)
RESULT_FIELDS = (
    "reachable_high_water", "drawn_high_water",
    "cpu_prepare_ticks_high_water", "texture_bytes_high_water",
    "copy_count_high_water", "copy_ticks_high_water",
    "cart_read_bytes_high_water", "missed_fields", "late_lists",
    "detector_tripped",
)
MODE_NAMES = ("PROBE3_REPRESENTATIVE", "PROBE3_PEAK_909", "PROBE3_OVERLOAD")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_block(mcp, address: int) -> dict[str, object]:
    telemetry = {name: mcp.u32(address + index * 4)
                 for index, name in enumerate(FIELDS)}
    results = {}
    start = len(FIELDS)
    for mode_index, mode_name in enumerate(MODE_NAMES):
        offset = start + mode_index * len(RESULT_FIELDS)
        results[mode_name] = {
            name: mcp.u32(address + (offset + index) * 4)
            for index, name in enumerate(RESULT_FIELDS)
        }
    telemetry["results"] = results
    telemetry["canary_end"] = mcp.u32(
        address + (start + len(MODE_NAMES) * len(RESULT_FIELDS)) * 4)
    return telemetry


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    manifest = json.loads((ROOT / "build/hardware/probe3/probe3-manifest.json").read_text())
    symbol = tools.symbols(["avsp_probe3_telemetry"])["avsp_probe3_telemetry"]
    recorded_address = int(manifest["telemetry"]["work_ram_address"], 16)
    require(symbol == recorded_address, "telemetry symbol/manifest address drifted")
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
        if mcp.u32(symbol + 31 * 4) == 1:
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("Probe 3 did not reach its bounded summary")

    mcp.call("pause")
    telemetry = read_block(mcp, symbol)
    rep = telemetry["results"]["PROBE3_REPRESENTATIVE"]
    peak = telemetry["results"]["PROBE3_PEAK_909"]
    overload = telemetry["results"]["PROBE3_OVERLOAD"]
    require(telemetry["magic"] == 0x50524233, "Probe 3 magic mismatch")
    require(telemetry["schema"] == 1, "Probe 3 schema mismatch")
    require(telemetry["status"] == 2 and telemetry["complete"] == 1,
            "Probe 3 did not complete")
    require(telemetry["failure_reason"] == 0 and telemetry["asset_failures"] == 0,
            "Probe 3 reported a diagnostic failure")
    require(telemetry["canary_begin"] == 0xA53C19E7 and
            telemetry["canary_end"] == 0xA53C19E7 and
            telemetry["canary_state"] == 1, "Probe 3 canary failed")
    require(rep["reachable_high_water"] == 567 and
            rep["drawn_high_water"] == 567,
            "representative schedule did not draw exactly")
    require(peak["reachable_high_water"] == 909 and
            peak["drawn_high_water"] == 909,
            "peak-909 schedule did not draw exactly")
    require(overload["reachable_high_water"] == 909 and
            overload["drawn_high_water"] == 909 and
            overload["detector_tripped"] == 1 and
            telemetry["overload_tripped"] == 1,
            "overload negative control did not trip")

    run_root = ROOT / f"build/hardware/probe3/emulator/run-{args.run}"
    run_root.mkdir(parents=True, exist_ok=True)
    screenshot = run_root / "post-run-summary.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": "avsp-probe3-emulator-readback-v1",
        "task": "HW-01-PROBE-3-VDP1-BUDGET-PRETEST",
        "run": args.run,
        "image": manifest["artifacts"]["iso"],
        "telemetry_address": f"0x{symbol:08x}",
        "telemetry": telemetry,
        "post_run_summary": {
            "summary_checksum": f"0x{telemetry['summary_checksum']:08x}",
            "screenshot": {
                "file": screenshot.relative_to(ROOT).as_posix(),
                "bytes": screenshot.stat().st_size,
                "sha256": sha256(screenshot),
            },
        },
        "emulator": {
            "identity": "Yaba Sanshiro 1.20.37-2986eb",
            "evidence_tier": "ONE_EMULATOR",
            "process": process,
            "executable_sha256": sha256(executable),
            "settings_sha256": sha256(settings),
        },
        "semantic_result": "PASS",
        "timing_scope": "EMULATOR_ONLY_NOT_HARDWARE_MARGIN",
        "physical_saturn": "UNRUN",
    }
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print(f"Probe 3 emulator run {args.run}: PASS")
    print(f"summary_checksum=0x{telemetry['summary_checksum']:08x}")
    print(f"readback={output}")
    mcp.call("resume")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
