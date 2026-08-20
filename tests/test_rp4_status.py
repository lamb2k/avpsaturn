#!/usr/bin/env python3
"""Failing-first controls for the RP4 acceptance instrument.

Written BEFORE the verifier behaviour change (Chapter 1 of the overlap
correction book). Capture-free: exercises tools/rp4_status.py directly
and the tracked evidence in data/rp4_street_readback.json.

Required behaviours:

1. six executed + two blocked controls can never report overall success;
2. overlap = None produces rp4_contract_status = FALSIFIED;
3. generic object-over-scroll ordering (independently MEASURED) cannot
   satisfy actor_foreground_priority;
4. a missing or blocked required control prevents acceptance;
5. a synthetic positive fixture (measured overlap, all eight controls
   executed and detecting) reaches PASS with exit code 0;
6. corrupt or stale evidence hashes are rejected;
7. (wired in test.ps1) a FALSIFIED tracked RP4 result fails the suite.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rp4_status import (REQUIRED_CONTROLS, EvidenceError,  # noqa: E402
                        build_status, check_evidence, exit_code)

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"ok   {name}")
    else:
        print(f"FAIL {name} {detail}")
        failures.append(name)


def controls(detected_map):
    return {name: {"detected": detected_map.get(name, True)}
            for name in REQUIRED_CONTROLS}


def main() -> None:
    # 1 + 4: six executed, two blocked -> never success.
    six_two = controls({"overlap_object_shift": None,
                        "overlap_priority_swap": None})
    status = build_status(six_two, overlap=None, plane_mismatches=0)
    check("blocked controls cannot report success",
          status["controls_all_detected"] is False and
          status["rp4_contract_status"] != "PASS", str(status))
    check("blocked counts are explicit",
          status["required_controls_total"] == 8 and
          status["required_controls_executed"] == 6 and
          status["required_controls_passed"] == 6 and
          status["required_controls_blocked"] == 2, str(status))

    # 2: overlap null -> FALSIFIED (exit 3).
    check("null overlap is FALSIFIED",
          status["rp4_contract_status"] == "FALSIFIED" and
          exit_code(status) == 3, str(status))

    # 3: generic ordering measured but no actor overlap -> still FALSIFIED.
    check("generic order cannot satisfy actor_foreground_priority",
          status["generic_object_plane_order_status"] == "MEASURED" and
          status["actor_foreground_overlap_status"] == "FALSIFIED",
          str(status))

    # 4b: a MISSING control (not even reported) prevents acceptance.
    missing = controls({})
    del missing["row_entry"]
    status_missing = build_status(missing, overlap={"frame": 1},
                                  plane_mismatches=0)
    check("missing required control prevents acceptance",
          status_missing["rp4_contract_status"] != "PASS" and
          status_missing["required_controls_blocked"] >= 1,
          str(status_missing))

    # a failed executed control is FAIL (exit 1), not FALSIFIED.
    failed = controls({"scroll_shift": False})
    status_failed = build_status(failed, overlap={"frame": 1},
                                 plane_mismatches=0)
    check("failed control is FAIL with exit 1",
          status_failed["rp4_contract_status"] == "FAIL" and
          exit_code(status_failed) == 1, str(status_failed))

    # plane mismatches force FAIL even with all controls green.
    status_planes = build_status(controls({}), overlap={"frame": 1},
                                 plane_mismatches=3)
    check("plane mismatches force FAIL",
          status_planes["rp4_contract_status"] == "FAIL",
          str(status_planes))

    # 5: synthetic positive fixture -> PASS, exit 0.
    status_pass = build_status(controls({}), overlap={"frame": 1},
                               plane_mismatches=0)
    check("synthetic positive fixture passes",
          status_pass["rp4_contract_status"] == "PASS" and
          status_pass["controls_all_detected"] is True and
          status_pass["required_controls_passed"] == 8 and
          exit_code(status_pass) == 0, str(status_pass))

    # 6: corrupt / stale / mismatched evidence hashes are rejected.
    good = {"strips_bin": "aa" * 32, "census": "bb" * 32}
    try:
        check_evidence(good, dict(good))
        check("matching evidence accepted", True)
    except EvidenceError as error:
        check("matching evidence accepted", False, str(error))
    for label, actual in (
            ("stale hash rejected", {"strips_bin": "cc" * 32,
                                     "census": "bb" * 32}),
            ("missing hash key rejected", {"strips_bin": "aa" * 32}),
            ("extra hash key rejected", {**good, "rogue": "dd" * 32})):
        try:
            check_evidence(good, actual)
            check(label, False, "EvidenceError not raised")
        except EvidenceError:
            check(label, True)

    # 7 (schema side): the TRACKED evidence must carry the explicit
    # fields; while it is FALSIFIED the suite must treat it as red.
    readback = json.loads(
        (ROOT / "data" / "rp4_street_readback.json").read_text())
    composite = readback.get("composite", {})
    st = composite.get("status")
    check("tracked evidence carries the explicit status block",
          isinstance(st, dict) and
          st.get("required_controls_total") == 8 and
          st.get("rp4_contract_status") in ("PASS", "FALSIFIED", "FAIL"),
          f"composite keys: {sorted(composite)}")
    if isinstance(st, dict):
        recomputed = build_status(
            composite.get("controls", {}),
            composite.get("overlap"),
            plane_mismatches=sum(
                readback.get("plane_pixels_mismatched", {"x": 1}).values()))
        check("tracked status recomputes from tracked controls",
              recomputed["rp4_contract_status"] ==
              st.get("rp4_contract_status"),
              f"recomputed {recomputed['rp4_contract_status']} vs "
              f"tracked {st.get('rp4_contract_status')}")

    if failures:
        print(f"rp4 status tests: {len(failures)} FAILURES: {failures}")
        raise SystemExit(1)
    print("rp4 status tests: all behaviours hold")


if __name__ == "__main__":
    main()
