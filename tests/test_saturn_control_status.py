#!/usr/bin/env python3
"""Failing-first controls for the RP4 v1 Saturn-control evidence.

Written BEFORE the StreetTest diagnostic path and the variant builds.
Capture-free: exercises tools/saturn_control_status.py directly.

Required behaviours:

1. exactly three named controls exist, and an unknown name is rejected;
2. a record missing ANY required evidence field cannot be scored;
3. a blocked control can never be promoted to passed;
4. corrupting the expected winner fails the control;
5. comparing a build against itself is rejected outright;
6. altering one VDP1 command fails the control that requires the
   command table to be identical;
7. a witness that did not change, or a negative control that did,
   fails the control;
8. the aggregate is MEASURED only when all three controls pass.

Every mutation below differs from the passing fixture in exactly one
input, so a failure names the behaviour that broke.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from saturn_control_status import (  # noqa: E402
    REQUIRED_FIELDS, REQUIRED_SATURN_CONTROLS, ControlEvidenceError,
    as_v1_controls, build_saturn_status, score_control, validate_control)

failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}" if detail else name)


def good(name: str) -> dict:
    record = {
        "baseline_build_sha256": "a" * 64,
        "variant_build_sha256": "b" * 64,
        "fixture_sha256": "c" * 64,
        "witness_sha256": "d" * 64,
        "source_frame": 3474,
        "streettest_rel": 0,
        "expected_winner": "earlier object-RAM entry",
        "observed_winner": "earlier object-RAM entry",
        "witness_pixels_changed": 12,
        "negative_control_pixels_changed": 0,
        "status": "passed",
        "baseline_command_table_sha256": "e" * 64,
        "variant_command_table_sha256": "f" * 64,
    }
    if name == "sprite_priority_register_effect":
        # This control isolates the priority input, so the emitted
        # commands must be identical between the two builds.
        record["variant_command_table_sha256"] = "e" * 64
    return record


def all_good() -> dict:
    return {name: good(name) for name in REQUIRED_SATURN_CONTROLS}


def main() -> None:
    check("exactly three Saturn controls are required",
          len(REQUIRED_SATURN_CONTROLS) == 3, str(REQUIRED_SATURN_CONTROLS))
    for expected in ("command_order", "cmdcolr_priority_selector",
                     "sprite_priority_register_effect"):
        check(f"control {expected} is named",
              expected in REQUIRED_SATURN_CONTROLS)

    status = build_saturn_status(all_good())
    check("all three passing controls reach MEASURED",
          status["saturn_output_order_status"] == "MEASURED",
          status["saturn_output_order_status"])
    check("register readback is always reported UNREADABLE",
          status["saturn_vdp2_register_readback"] == "UNREADABLE")
    check("MSHvSF architecture stays ADAPTED",
          status["mshvsf_priority_architecture"] == "ADAPTED")
    check("jump-record coverage stays GAP",
          status["animation_jump_record_coverage"] == "GAP")

    try:
        validate_control("not_a_control", good("command_order"))
        check("unknown control is rejected", False, "no error raised")
    except ControlEvidenceError:
        pass

    for field in REQUIRED_FIELDS:
        record = good("command_order")
        del record[field]
        try:
            score_control("command_order", record)
            check(f"missing {field} is rejected", False, "no error raised")
        except ControlEvidenceError:
            pass

    # Mutation: a blocked control must never be promoted to passed.
    blocked = all_good()
    blocked["command_order"]["status"] = "blocked"
    scored = build_saturn_status(blocked)
    check("a blocked control cannot pass",
          scored["per_control"]["command_order"]["detected"] is None,
          str(scored["per_control"]["command_order"]))
    check("a blocked control blocks the aggregate",
          scored["saturn_output_order_status"] == "BLOCKED",
          scored["saturn_output_order_status"])
    check("blocked controls are counted",
          scored["controls_blocked"] == 1)

    # Mutation: corrupt the expected winner.
    corrupted = all_good()
    corrupted["command_order"]["expected_winner"] = "later object-RAM entry"
    scored = build_saturn_status(corrupted)
    check("a wrong observed winner fails the control",
          scored["per_control"]["command_order"]["detected"] is False,
          str(scored["per_control"]["command_order"]))
    check("a failed control fails the aggregate",
          scored["saturn_output_order_status"] == "FAIL",
          scored["saturn_output_order_status"])

    # Mutation: swap the baseline and variant build hashes so the
    # control compares a build against itself.
    same_build = all_good()
    same_build["command_order"]["variant_build_sha256"] = \
        same_build["command_order"]["baseline_build_sha256"]
    try:
        build_saturn_status(same_build)
        check("comparing a build against itself is rejected", False,
              "no error raised")
    except ControlEvidenceError:
        pass

    # Mutation: alter one VDP1 command in the control that requires the
    # command table to stay identical.
    altered = all_good()
    altered["sprite_priority_register_effect"][
        "variant_command_table_sha256"] = "9" * 64
    scored = build_saturn_status(altered)
    check("a changed command table fails the priority-effect control",
          scored["per_control"]["sprite_priority_register_effect"]
          ["detected"] is False)

    # ...and the mirror: a command-order control whose table did NOT
    # change proves nothing about ordering.
    unchanged = all_good()
    unchanged["command_order"]["variant_command_table_sha256"] = \
        unchanged["command_order"]["baseline_command_table_sha256"]
    scored = build_saturn_status(unchanged)
    check("an unchanged command table fails the ordering control",
          scored["per_control"]["command_order"]["detected"] is False)

    # Mutation: alter one witness pixel (none changed).
    still = all_good()
    still["command_order"]["witness_pixels_changed"] = 0
    scored = build_saturn_status(still)
    check("an unchanged witness fails the control",
          scored["per_control"]["command_order"]["detected"] is False)

    # Mutation: a negative-control pixel moved, so more than the
    # declared variable changed.
    leaked = all_good()
    leaked["command_order"]["negative_control_pixels_changed"] = 1
    scored = build_saturn_status(leaked)
    check("a moved negative control fails the control",
          scored["per_control"]["command_order"]["detected"] is False)

    # A control that is simply absent is blocked, never passed.
    absent = all_good()
    del absent["cmdcolr_priority_selector"]
    scored = build_saturn_status(absent)
    check("an absent control is blocked",
          scored["per_control"]["cmdcolr_priority_selector"]["detected"]
          is None)
    check("an absent control cannot reach MEASURED",
          scored["saturn_output_order_status"] != "MEASURED")

    # The v1 bridge must carry the same verdicts under the v1 names.
    bridged = as_v1_controls(all_good())
    check("the v1 bridge names all three controls",
          set(bridged) == {"reverse_saturn_command_order",
                           "change_cmdcolr_priority_bits",
                           "perturb_pris_prin"}, str(sorted(bridged)))
    check("the v1 bridge carries the verdicts",
          all(c["detected"] is True for c in bridged.values()))
    bridged_blocked = as_v1_controls(blocked)
    check("the v1 bridge carries a blocked verdict as None",
          bridged_blocked["reverse_saturn_command_order"]["detected"]
          is None)

    if failures:
        print(f"saturn control tests: {len(failures)} FAILURES: "
              f"{failures[:6]}")
        raise SystemExit(1)
    print("saturn control tests: all behaviours hold")


if __name__ == "__main__":
    main()
