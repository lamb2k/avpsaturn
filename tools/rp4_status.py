#!/usr/bin/env python3
"""RP4 acceptance-status computation (pure, host-testable).

The RP4 contract requires EIGHT executed negative controls and one
measured actor/foreground overlap. This module owns the aggregation so
the acceptance instrument cannot drift back into ambiguity:

- a blocked or missing required control can never yield overall success;
- overlap = None is FALSIFIED, regardless of how many generic controls
  detect (generic object-over-plane ordering is a separate, independent
  MEASURED claim and never substitutes for actor_foreground_priority);
- corrupt or stale evidence hashes are rejected before status is
  computed;
- PASS requires exactly: 8 executed, 8 passed, 0 blocked, a measured
  overlap, and zero plane mismatches.

verify_street_composite.py builds its report through build_status();
tests/test_rp4_status.py holds the failing-first unit controls.
"""
from __future__ import annotations

REQUIRED_CONTROLS = (
    "wrong_transform",
    "scroll_shift",
    "row_entry",
    "palette_cycle",
    "patch_dropped",
    "register_order",
    "overlap_object_shift",
    "overlap_priority_swap",
)


class EvidenceError(ValueError):
    """Corrupt or stale evidence: hashes disagree with the inputs."""


def check_evidence(recorded: dict, actual: dict) -> None:
    """Reject a report whose recorded input hashes are corrupt/stale.

    `recorded` is the hash map stored in the evidence report; `actual`
    is recomputed from the inputs on disk. Every recorded key must match
    its recomputation exactly; unknown or missing keys are rejected too.
    """
    if set(recorded) != set(actual):
        raise EvidenceError(
            f"evidence hash keys diverge: recorded {sorted(recorded)} vs "
            f"actual {sorted(actual)}")
    for key in sorted(recorded):
        if recorded[key] != actual[key]:
            raise EvidenceError(
                f"stale evidence: {key} recorded {recorded[key]} but "
                f"inputs hash to {actual[key]}")


def build_status(controls: dict, overlap: dict | None,
                 plane_mismatches: int) -> dict:
    """The single authoritative RP4 status block.

    controls: name -> {"detected": True | False | None, ...} where None
    means the control was BLOCKED (could not execute).
    """
    missing = [name for name in REQUIRED_CONTROLS if name not in controls]
    executed = [name for name in REQUIRED_CONTROLS
                if controls.get(name, {}).get("detected") is not None]
    passed = [name for name in executed
              if controls[name]["detected"] is True]
    blocked = [name for name in REQUIRED_CONTROLS
               if name in controls and
               controls[name].get("detected") is None]

    overlap_measured = overlap is not None
    all_ran_and_detected = (not missing and len(executed) == 8 and
                            len(passed) == 8 and not blocked)

    if len(executed) != len(passed) or plane_mismatches > 0:
        contract = "FAIL"
    elif not overlap_measured or blocked or missing:
        contract = "FALSIFIED"
    elif all_ran_and_detected:
        contract = "PASS"
    else:
        contract = "FAIL"

    return {
        "required_controls_total": len(REQUIRED_CONTROLS),
        "required_controls_executed": len(executed),
        "required_controls_passed": len(passed),
        "required_controls_blocked": len(blocked) + len(missing),
        "controls_all_detected": all_ran_and_detected,
        "rp4_contract_status": contract,
        "actor_foreground_overlap_status":
            "MEASURED" if overlap_measured else "FALSIFIED",
        "generic_object_plane_order_status": "MEASURED",
        "composite_residue_status": "GAP",
        "live_register_readback_note":
            "live Saturn priority-register readback is MEASURED "
            "separately and is not a substitute for the deliberate "
            "overlap",
    }


def exit_code(status: dict) -> int:
    """0 = PASS, 3 = FALSIFIED fixture, 1 = failed control/evidence."""
    verdict = status["rp4_contract_status"]
    if verdict == "PASS":
        return 0
    if verdict == "FALSIFIED":
        return 3
    return 1
