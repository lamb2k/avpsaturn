#!/usr/bin/env python3
"""Controls for the RP4 v1 source-order acceptance status.

Capture-free: exercises tools/rp4_status.build_v1_status directly.

Required behaviours:

1. the v0 verdict is preserved as a constant, never recomputed, so the
   falsified source premise cannot be quietly rewritten into a pass;
2. every one of the eight v1 controls must be executed AND detect;
3. a blocked or missing control yields FALSIFIED, never PASS;
4. a control that executed and did NOT detect yields FAIL, which is a
   harder verdict than FALSIFIED and must not be softened;
5. witnesses below the required count, or any ordering counterexample,
   block acceptance even when all eight controls pass;
6. composite mismatches yield FAIL;
7. exit codes map PASS/FALSIFIED/FAIL to 0/3/1.

Each assertion is mutation-checked in test.ps1 terms by construction:
every case differs from the passing fixture in exactly one input.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rp4_status import (REQUIRED_V1_CONTROLS,            # noqa: E402
                        REQUIRED_V1_SATURN_CONTROLS,
                        REQUIRED_V1_SOURCE_CONTROLS,
                        V0_STATUS, build_v1_status, v1_exit_code)

GOOD_WITNESSES = {"object_order": 11, "object_layer": 4,
                  "counterexamples": 0}
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}" if detail else name)


def all_detected() -> dict:
    return {name: {"detected": True} for name in REQUIRED_V1_CONTROLS}


def main() -> None:
    passing = build_v1_status(all_detected(), GOOD_WITNESSES, 0)
    check("all eight controls detecting reaches PASS",
          passing["rp4_v1_status"] == "PASS", passing["rp4_v1_status"])
    check("PASS exits 0", v1_exit_code(passing) == 0)
    check("v0 verdict is preserved verbatim",
          passing["rp4_v0_status"] == V0_STATUS ==
          "FALSIFIED_BY_SOURCE_PREMISE", passing["rp4_v0_status"])
    check("source and Saturn control counts are reported separately",
          passing["rp4_v1_source_controls_passed"] ==
          len(REQUIRED_V1_SOURCE_CONTROLS) and
          passing["rp4_v1_saturn_controls_passed"] ==
          len(REQUIRED_V1_SATURN_CONTROLS))
    check("eight controls are required",
          passing["rp4_v1_controls_total"] == 8 ==
          len(REQUIRED_V1_CONTROLS))

    for name in REQUIRED_V1_CONTROLS:
        blocked = all_detected()
        blocked[name] = {"detected": None}
        status = build_v1_status(blocked, GOOD_WITNESSES, 0)
        check(f"blocked control {name} cannot pass",
              status["rp4_v1_status"] == "FALSIFIED",
              status["rp4_v1_status"])
        check(f"blocked control {name} exits 3",
              v1_exit_code(status) == 3)

        missing = all_detected()
        del missing[name]
        status = build_v1_status(missing, GOOD_WITNESSES, 0)
        check(f"missing control {name} cannot pass",
              status["rp4_v1_status"] != "PASS",
              status["rp4_v1_status"])

        undetected = all_detected()
        undetected[name] = {"detected": False}
        status = build_v1_status(undetected, GOOD_WITNESSES, 0)
        check(f"undetected control {name} is a hard FAIL",
              status["rp4_v1_status"] == "FAIL",
              status["rp4_v1_status"])
        check(f"undetected control {name} exits 1",
              v1_exit_code(status) == 1)

    thin = build_v1_status(all_detected(),
                           {**GOOD_WITNESSES, "object_order": 2}, 0)
    check("too few ordering witnesses cannot pass",
          thin["rp4_v1_status"] == "FALSIFIED", thin["rp4_v1_status"])
    thin_layer = build_v1_status(all_detected(),
                                 {**GOOD_WITNESSES, "object_layer": 1}, 0)
    check("too few layer witnesses cannot pass",
          thin_layer["rp4_v1_status"] == "FALSIFIED",
          thin_layer["rp4_v1_status"])
    check("witness status reports FALSIFIED when thin",
          thin["rp4_v1_witness_status"] == "FALSIFIED")

    counter = build_v1_status(all_detected(),
                              {**GOOD_WITNESSES, "counterexamples": 1}, 0)
    check("an ordering counterexample is a hard FAIL",
          counter["rp4_v1_status"] == "FAIL", counter["rp4_v1_status"])

    mismatched = build_v1_status(all_detected(), GOOD_WITNESSES, 7)
    check("composite mismatches are a hard FAIL",
          mismatched["rp4_v1_status"] == "FAIL",
          mismatched["rp4_v1_status"])
    check("mismatch count is reported",
          mismatched["rp4_v1_composite_mismatches"] == 7)

    empty = build_v1_status({}, GOOD_WITNESSES, 0)
    check("no controls at all cannot pass",
          empty["rp4_v1_status"] == "FALSIFIED", empty["rp4_v1_status"])
    check("no controls counts all eight as blocked",
          empty["rp4_v1_controls_blocked"] == 8)

    if failures:
        print(f"rp4 v1 status tests: {len(failures)} FAILURES: "
              f"{failures[:6]}")
        raise SystemExit(1)
    print("rp4 v1 status tests: all behaviours hold")


if __name__ == "__main__":
    main()
