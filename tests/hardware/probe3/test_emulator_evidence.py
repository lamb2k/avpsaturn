#!/usr/bin/env python3
"""Validate paired Probe 3 pinned-emulator semantic evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "build" / "hardware" / "probe3" / "emulator"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def semantic(report: dict) -> dict:
    telemetry = report["telemetry"]
    return {
        "magic": telemetry["magic"],
        "schema": telemetry["schema"],
        "status": telemetry["status"],
        "failure_reason": telemetry["failure_reason"],
        "canary_state": telemetry["canary_state"],
        "asset_failures": telemetry["asset_failures"],
        "representative_workload_tile_draw_high_water":
            telemetry["representative_workload_tile_draw_high_water"],
        "peak_workload_tile_draw_high_water":
            telemetry["peak_workload_tile_draw_high_water"],
        "overload_expected": telemetry["overload_expected"],
        "overload_tripped": telemetry["overload_tripped"],
        "draw_end_timestamp_reliable": telemetry["draw_end_timestamp_reliable"],
        "timer_divisor": telemetry["timer_divisor"],
        "soak_target_fields": telemetry["soak_target_fields"],
        "soak_elapsed_fields": telemetry["soak_elapsed_fields"],
        "soak_workload_fields": telemetry["soak_workload_fields"],
        "soak_requested_workload_high_water":
            telemetry["soak_requested_workload_high_water"],
        "soak_submitted_workload_high_water":
            telemetry["soak_submitted_workload_high_water"],
        "soak_missed_fields": telemetry["soak_missed_fields"],
        "soak_late_lists": telemetry["soak_late_lists"],
        "copy_path": [telemetry["cart_texture_source_valid"],
                      telemetry["vdp1_texture_destination_valid"],
                      telemetry["cart_to_vdp1_path_valid"]],
        "complete": telemetry["complete"],
        "results": {
            mode: {
                "workload_tile_draw_high_water":
                    result["workload_tile_draw_high_water"],
                "submitted_workload_draw_high_water":
                    result["submitted_workload_draw_high_water"],
                "detector_tripped": result["detector_tripped"],
                "census_stored_nonzero_slots":
                    result["census_stored_nonzero_slots"],
                "census_stored_nonzero_slots":
                    result["census_stored_nonzero_slots"],
                "census_reachable_table_entries":
                    result["census_reachable_table_entries"],
                "census_workload_tile_draw_commands":
                    result["census_workload_tile_draw_commands"],
                "census_auxiliary_draw_commands":
                    result["census_auxiliary_draw_commands"],
                "census_sgl_scaled_sprite_sentinel_draw_commands":
                    result["census_sgl_scaled_sprite_sentinel_draw_commands"],
                "census_total_reachable_draw_commands":
                    result["census_total_reachable_draw_commands"],
                "census_reachable_state_commands":
                    result["census_reachable_state_commands"],
                "census_reachable_skipped_commands":
                    result["census_reachable_skipped_commands"],
                "census_terminator_present":
                    result["census_terminator_present"],
            }
            for mode, result in telemetry["results"].items()
        },
    }


def main() -> int:
    reports = [json.loads((BUILD / f"run-{run}" / "readback.json").read_text())
               for run in (1, 2)]
    require(all(report["semantic_result"] == "PASS" for report in reports),
            "one Probe 3 emulator run did not pass")
    require(reports[0]["image"]["sha256"] == reports[1]["image"]["sha256"],
            "paired emulator images differ")
    require(semantic(reports[0]) == semantic(reports[1]),
            "paired Probe 3 semantic telemetry differs")
    state = semantic(reports[0])
    require(state["representative_workload_tile_draw_high_water"] == 567,
            "representative workload tile-draw high-water mismatch")
    require(state["peak_workload_tile_draw_high_water"] == 909,
            "peak workload tile-draw high-water mismatch")
    require(state["overload_tripped"] == 1,
            "overload negative control did not trip")
    for mode, workload, total_entries in (
            ("PROBE3_REPRESENTATIVE", 567, 572),
            ("PROBE3_PEAK_909", 909, 914),
            ("PROBE3_OVERLOAD", 909, 914)):
        result = state["results"][mode]
        require(result["census_workload_tile_draw_commands"] == workload and
                result["census_auxiliary_draw_commands"] == 1 and
                result["census_sgl_scaled_sprite_sentinel_draw_commands"] == 1 and
                result["census_total_reachable_draw_commands"] == workload + 1 and
                result["census_reachable_state_commands"] == 3 and
                result["census_reachable_table_entries"] == total_entries and
                result["census_stored_nonzero_slots"] >= total_entries,
                f"{mode} measured VDP1 command composition mismatch")
    require(state["soak_elapsed_fields"] >= 36000 and
            state["soak_submitted_workload_high_water"] == 909 and
            state["soak_missed_fields"] == 0 and
            state["soak_late_lists"] == 0,
            "full alternating soak did not pass")
    require(all(report["physical_saturn"] == "UNRUN" for report in reports),
            "emulator evidence was promoted to physical evidence")
    print("HW-01 Probe 3 paired pinned-emulator semantics: PASS")
    print(f"iso_sha256={reports[0]['image']['sha256']}")
    print("physical_saturn=UNRUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
