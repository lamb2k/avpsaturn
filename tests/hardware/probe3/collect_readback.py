#!/usr/bin/env python3
"""Collect the fixed Probe 3 work-RAM block from pinned Yaba Sanshiro."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
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
    "canary_begin", "magic", "schema", "status", "phase", "mode",
    "mode_frame", "frame_number", "workload_checksum_word",
    "requested_workload_tile_draws", "submitted_workload_draw_calls",
    "vdp1_draw_end_state",
    "draw_end_deadline_fields", "detector_enabled",
    "detector_predicate_tripped", "field_delta", "field_start_timestamp",
    "field_period_ticks", "cpu_prepare_start_timestamp",
    "cpu_prepare_end_timestamp", "transfer_start_timestamp",
    "transfer_end_timestamp", "submission_timestamp", "draw_end_timestamp",
    "draw_end_timestamp_reliable", "draw_end_margin_ticks",
    "draw_end_margin_percent_x100", "total_frame_margin_ticks",
    "total_frame_margin_percent_x100", "timer_wrapped", "timer_divisor",
    "timer_calibration_field_ticks", "texture_bytes_copied", "copy_count",
    "copy_ticks", "cart_texture_source_valid",
    "vdp1_texture_destination_valid", "cart_to_vdp1_path_valid",
    "cram_writes", "cartridge_read_bytes", "missed_fields",
    "late_command_lists", "skipped_fields", "repeated_fields",
    "canary_state", "asset_failures", "copy_path_failures",
    "failure_reason", "overload_expected", "overload_tripped",
    "representative_workload_tile_draw_high_water",
    "peak_workload_tile_draw_high_water", "soak_target_fields",
    "soak_elapsed_fields", "soak_workload_fields", "soak_block_fields",
    "soak_requested_workload_high_water",
    "soak_submitted_workload_high_water",
    "soak_cpu_ticks_high_water", "soak_transfer_ticks_high_water",
    "soak_min_draw_margin_ticks", "soak_min_draw_margin_percent_x100",
    "soak_missed_fields", "soak_late_lists", "soak_skipped_fields",
    "soak_repeated_fields", "soak_canary_failures", "soak_asset_failures",
    "soak_copy_path_failures", "summary_checksum", "complete",
)
RESULT_FIELDS = (
    "workload_tile_draw_high_water", "submitted_workload_draw_high_water",
    "cpu_prepare_ticks_high_water", "texture_bytes_high_water",
    "copy_count_high_water", "copy_ticks_high_water",
    "cart_read_bytes_high_water", "missed_fields", "late_lists",
    "detector_tripped", "min_draw_margin_ticks",
    "min_draw_margin_percent_x100",
    "census_requested_workload_tile_draws",
    "census_submitted_workload_draw_calls",
    "census_stored_nonzero_slots", "census_reachable_table_entries",
    "census_workload_tile_draw_commands",
    "census_auxiliary_draw_commands",
    "census_sgl_scaled_sprite_sentinel_draw_commands",
    "census_total_reachable_draw_commands",
    "census_reachable_state_commands",
    "census_reachable_skipped_commands",
    "census_terminator_present", "census_invalid_link",
    "census_loop_detected", "census_traversal_failure",
    "census_premature_end", "census_table_truncated",
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
    parser.add_argument("--timeout", type=float, default=900.0)
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
        if mcp.u32(symbol + FIELDS.index("complete") * 4) == 1:
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("Probe 3 did not reach its bounded summary")

    mcp.call("pause")
    telemetry = read_block(mcp, symbol)
    if telemetry["status"] != 2 or telemetry["complete"] != 1:
        print(json.dumps(telemetry, indent=2, sort_keys=True))
        model_spec = importlib.util.spec_from_file_location(
            "probe3_vdp1_model", ROOT / "tools/avsp_vdp1_model.py")
        model = importlib.util.module_from_spec(model_spec)
        assert model_spec.loader is not None
        sys.modules[model_spec.name] = model
        model_spec.loader.exec_module(model)
        vram = mcp.read(0x25C00000, 0x10000)
        traversal = model.traverse(vram)
        print(json.dumps({
            "vdp1_command_histogram": traversal.command_type_histogram(),
            "vdp1_jump_histogram": traversal.jump_mode_histogram(),
            "vdp1_last_commands": [command.to_json()
                                    for command in traversal.visited[-8:]],
        }, indent=2, sort_keys=True))
    rep = telemetry["results"]["PROBE3_REPRESENTATIVE"]
    peak = telemetry["results"]["PROBE3_PEAK_909"]
    overload = telemetry["results"]["PROBE3_OVERLOAD"]
    require(telemetry["magic"] == 0x50524233, "Probe 3 magic mismatch")
    require(telemetry["schema"] == 3, "Probe 3 schema mismatch")
    require(telemetry["status"] == 2 and telemetry["complete"] == 1,
            "Probe 3 did not complete")
    require(telemetry["failure_reason"] == 0 and telemetry["asset_failures"] == 0,
            "Probe 3 reported a diagnostic failure")
    require(telemetry["canary_begin"] == 0xA53C19E7 and
            telemetry["canary_end"] == 0xA53C19E7 and
            telemetry["canary_state"] == 1, "Probe 3 canary failed")
    for result, expected, name in ((rep, 567, "representative"),
                                   (peak, 909, "peak-909"),
                                   (overload, 909, "overload")):
        require(result["workload_tile_draw_high_water"] == expected and
                result["submitted_workload_draw_high_water"] == expected and
                result["census_requested_workload_tile_draws"] == expected and
                result["census_submitted_workload_draw_calls"] == expected and
                result["census_workload_tile_draw_commands"] == expected and
                result["census_auxiliary_draw_commands"] == 1 and
                result["census_sgl_scaled_sprite_sentinel_draw_commands"] == 1 and
                result["census_total_reachable_draw_commands"] == expected + 1 and
                result["census_reachable_state_commands"] == 3 and
                result["census_reachable_skipped_commands"] == 0 and
                result["census_terminator_present"] == 1 and
                result["census_reachable_table_entries"] == expected + 5 and
                result["census_stored_nonzero_slots"] >= expected + 5 and
                result["census_invalid_link"] == 0 and
                result["census_loop_detected"] == 0 and
                result["census_traversal_failure"] == 0 and
                result["census_premature_end"] == 0 and
                result["census_table_truncated"] == 0,
                f"{name} actual command-table census failed")
    require(overload["workload_tile_draw_high_water"] == 909 and
            overload["detector_tripped"] == 1 and
            telemetry["overload_tripped"] == 1,
            "overload negative control did not trip")
    require(rep["detector_tripped"] == 0 and peak["detector_tripped"] == 0,
            "production modes tripped because overload was enabled")
    require(telemetry["draw_end_timestamp_reliable"] == 1 and
            telemetry["field_period_ticks"] > 0 and
            telemetry["timer_divisor"] == 32,
            "quantitative draw-end timestamp telemetry is incomplete")
    require(telemetry["soak_target_fields"] == 36000 and
            telemetry["soak_elapsed_fields"] >= 36000 and
            telemetry["soak_requested_workload_high_water"] == 909 and
            telemetry["soak_submitted_workload_high_water"] == 909,
            "full alternating soak contract did not complete")
    require(telemetry["soak_missed_fields"] == 0 and
            telemetry["soak_late_lists"] == 0 and
            telemetry["soak_canary_failures"] == 0 and
            telemetry["soak_asset_failures"] == 0 and
            telemetry["soak_copy_path_failures"] == 0,
            "soak reported a hard failure")
    require(telemetry["cart_texture_source_valid"] == 1 and
            telemetry["vdp1_texture_destination_valid"] == 1 and
            telemetry["cart_to_vdp1_path_valid"] == 1,
            "cart-to-VDP1 copy path was not proven")

    run_root = ROOT / f"build/hardware/probe3/emulator/run-{args.run}"
    run_root.mkdir(parents=True, exist_ok=True)
    screenshot = run_root / "post-run-summary.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": "avsp-probe3-emulator-readback-v3",
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
