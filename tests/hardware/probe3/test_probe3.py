#!/usr/bin/env python3
"""Focused host controls for the Probe 3 schedule and profile isolation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "probe3_schedule_generator", HERE / "generate_schedule.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def compile_and_run_contract() -> None:
    translated = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(ROOT)], check=True,
        capture_output=True, text=True).stdout.strip()
    command = (
        f"cd '{translated}' && mkdir -p build/hardware/probe3/host && "
        "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 -I. "
        "tests/hardware/probe3/probe3.c "
        "tests/hardware/probe3/test_probe3_contract.c "
        "-o build/hardware/probe3/host/probe3_contract && "
        "./build/hardware/probe3/host/probe3_contract")
    subprocess.run(["wsl.exe", "sh", "-lc", command], check=True)


def validate_identity(report: dict, expected_peak_count: int = 909,
                      expected_peak_id: str = "PROBE3_PEAK_909") -> None:
    rep, peak = report["schedules"]
    require(rep["id"] == "PROBE3_REPRESENTATIVE",
            "representative workload identity drifted")
    require(peak["id"] == expected_peak_id,
            "peak workload identity drifted")
    require(peak["requested_tile_count"] == expected_peak_count,
            "peak requested count drifted")
    require(peak["actual_reachable_command_count"] == expected_peak_count,
            "peak reachable count drifted")
    require(peak["actual_expected_drawn_command_count"] == expected_peak_count,
            "peak drawn count drifted")


def expect_reject(report: dict, count: int, workload_id: str) -> None:
    try:
        validate_identity(report, count, workload_id)
    except AssertionError:
        return
    raise AssertionError("mutated schedule identity was accepted")


def main() -> int:
    compile_and_run_contract()
    generator = load_generator()
    report = json.loads((HERE / "probe3-schedule.json").read_text())
    validate_identity(report)
    rep, peak = report["schedules"]
    require(rep["source_frame"] == 5637 and
            rep["actual_reachable_command_count"] == 567,
            "representative provenance/count drifted")
    require(peak["source_frame"] == 5776 and
            peak["actual_reachable_command_count"] == 909,
            "peak-909 provenance/count drifted")
    require(rep["object_count"] == 57 and peak["object_count"] == 78,
            "object command counts drifted")
    require(rep["workload_checksum_sha256"] ==
            "194cb70efb503a3277e9f1256b71f01bcf4393566aeed6f3a538018c0e385e68",
            "representative checksum drifted")
    require(peak["workload_checksum_sha256"] ==
            "92e468908f59a9c1ca3b6c5c7ccfbf5a98e38ccf464adb05393233db03f7966c",
            "peak checksum drifted")
    require(report["overload"] == {
        "base_schedule": "PROBE3_PEAK_909",
        "expected_detector_state": "DEADLINE_TRIPPED",
        "id": "PROBE3_OVERLOAD",
        "method": "declared diagnostic deadline tightened to zero fields",
        "production_budget_claim": False,
        "reachable_commands": 909,
    }, "overload negative control drifted")

    # Re-expand every tracked command through the same contract and require
    # exact agreement with the tracked counts and checksums.
    for schedule in (rep, peak):
        tiles = []
        for entry in schedule["object_entries"]:
            tiles += generator.expand_entry(
                entry["y"], entry["code"], entry["attr"])
        require(len(tiles) == schedule["actual_reachable_command_count"],
                f"{schedule['id']} expansion count mismatch")
        require(generator.workload_checksum(
            schedule["object_entries"], tiles) ==
            schedule["workload_checksum_sha256"],
            f"{schedule['id']} checksum mismatch")

    mutated_count = json.loads(json.dumps(report))
    mutated_count["schedules"][1]["actual_reachable_command_count"] = 908
    expect_reject(mutated_count, 909, "PROBE3_PEAK_909")
    mutated_id = json.loads(json.dumps(report))
    mutated_id["schedules"][1]["id"] = "PROBE3_PEAK_APPROX"
    expect_reject(mutated_id, 909, "PROBE3_PEAK_909")

    build = (ROOT / "build.ps1").read_text(encoding="utf-8")
    make = (ROOT / "makefile").read_text(encoding="utf-8")
    main_c = (ROOT / "main.c").read_text(encoding="utf-8")
    require("[switch]$Probe3" in build and "AVSP_PROBE3=1" in build,
            "Probe 3 profile wiring missing")
    require("ifneq ($(AVSP_PROBE3),)" in make,
            "Probe 3 compile isolation missing")
    require("#ifdef AVSP_PROBE3" in main_c,
            "Probe 3 runtime isolation missing")
    require("PROBE3_SCU_SPR_VECTOR" in main_c and
            "probe3_sprite_draw_end_irq" in main_c,
            "reliable Probe-only VDP1 draw-end interrupt seam missing")
    require("probe3_run_loop" in main_c and "slSynch();" in main_c,
            "explicit Probe-only command-list submission seam missing")
    require("AVSP_PROBE3_SOAK_FIELDS 36000UL" in
            (HERE / "probe3.h").read_text(encoding="utf-8"),
            "release Probe image lacks full ten-minute NTSC soak")
    probe_header = (HERE / "probe3.h").read_text(encoding="utf-8")
    require("AVSP_PROBE3_SCHEMA 3UL" in probe_header and
            "workload_tile_draw_commands" in probe_header and
            "auxiliary_draw_commands" in probe_header and
            "sgl_scaled_sprite_sentinel_draw_commands" in probe_header and
            "total_reachable_draw_commands" in probe_header and
            "reachable_state_commands" in probe_header and
            "reachable_table_entries" in probe_header and
            "stored_nonzero_slots" in probe_header,
            "Probe 3 command-composition telemetry contract is incomplete")
    require("src/port_v2" not in str(HERE.relative_to(ROOT)).replace("\\", "/"),
            "Probe 3 diagnostic escaped its owned path")

    print("HW-01 Probe 3 focused host controls: PASS")
    print(f"schedule_sha256={sha256(HERE / 'probe3-schedule.json')}")
    print(f"header_sha256={sha256(HERE / 'generated/probe3_schedule.h')}")
    print("negative_controls=detector-disable,deadline-mutation,manual-assertion,"
          "production-false-positive,early-end,invalid-link,sentinel-signature,"
          "command-composition,elapsed-field-clock,count-mutation,"
          "workload-identity-mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
