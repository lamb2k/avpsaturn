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
        "representative_high_water": telemetry["representative_high_water"],
        "peak_high_water": telemetry["peak_high_water"],
        "overload_expected": telemetry["overload_expected"],
        "overload_tripped": telemetry["overload_tripped"],
        "complete": telemetry["complete"],
        "results": {
            mode: {
                "reachable": result["reachable_high_water"],
                "drawn": result["drawn_high_water"],
                "detector_tripped": result["detector_tripped"],
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
    require(state["representative_high_water"] == 567,
            "representative command high-water mismatch")
    require(state["peak_high_water"] == 909,
            "peak command high-water mismatch")
    require(state["overload_tripped"] == 1,
            "overload negative control did not trip")
    require(all(report["physical_saturn"] == "UNRUN" for report in reports),
            "emulator evidence was promoted to physical evidence")
    print("HW-01 Probe 3 paired pinned-emulator semantics: PASS")
    print(f"iso_sha256={reports[0]['image']['sha256']}")
    print("physical_saturn=UNRUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
