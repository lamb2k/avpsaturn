#!/usr/bin/env python3
"""RP4 v1 Saturn-side control evidence: schema and status (pure).

The three Saturn controls prove the port reproduces the source's output
order. They are executed as VISUAL/OUTPUT DIFFERENTIALS against the
StreetTest build, never as VDP2 register readback: this instrument
cannot read VDP2 registers at all, so nothing here may be described as
register-exact.

  command_order                 baseline reversed emission versus a
                                forward-emission variant build
  cmdcolr_priority_selector     only the CMDCOLR priority-select bits
                                differ between the two builds
  sprite_priority_register_effect
                                only the slPriority class input differs;
                                the VDP1 command table must stay
                                byte-identical

Every control must carry its full evidence record. A control missing any
required field is INVALID and can never be counted as passed, and a
blocked control can never be promoted to passed.
"""
from __future__ import annotations

REQUIRED_SATURN_CONTROLS = (
    "command_order",
    "cmdcolr_priority_selector",
    "sprite_priority_register_effect",
)

REQUIRED_FIELDS = (
    "baseline_build_sha256",
    "variant_build_sha256",
    "fixture_sha256",
    "witness_sha256",
    "source_frame",
    "streettest_rel",
    "expected_winner",
    "observed_winner",
    "witness_pixels_changed",
    "negative_control_pixels_changed",
    "status",
)

VALID_STATUS = ("executed", "passed", "failed", "blocked")

# Controls whose proof requires the VDP1 command table to be identical
# between the two builds, and controls whose proof requires it to differ.
COMMAND_TABLE_MUST_MATCH = ("sprite_priority_register_effect",)
COMMAND_TABLE_MUST_DIFFER = ("command_order", "cmdcolr_priority_selector")


#: The one alternative evidence kind this instrument can actually produce.
#: The VDP1 framebuffer is unreadable here, so a witness PIXEL cannot be
#: observed; the final command SEQUENCE can.
FINAL_COMMAND_SEQUENCE = "final_vdp1_command_sequence"

#: Only the draw-order control is decidable from the command sequence alone.
#: The other two ask what the composite finally shows when a priority input
#: changes while the command table stays byte-identical - a question the
#: command table cannot answer about itself. They stay pixel-only, so this
#: evidence kind can never promote them.
SEQUENCE_DECIDABLE_CONTROLS = ("command_order",)

#: Every relationship a command-sequence pass must establish.
REQUIRED_SEQUENCE_FACTS = (
    "same_command_count",
    "same_identity_multiset",
    "sorted_pair_inert",
)


class ControlEvidenceError(ValueError):
    """A control record that cannot be scored as written."""


def command_sequence_faults(name: str, record: dict) -> list:
    """Why a final-command-sequence pass is not yet earned.

    This exists so `command_order` can pass on evidence this instrument
    can really obtain. It deliberately does not relax anything: a control
    that needs a pixel still needs a pixel.
    """
    if name not in SEQUENCE_DECIDABLE_CONTROLS:
        return [f"{name} cannot be decided from the final command sequence: "
                f"it needs an observed witness pixel, which this instrument "
                f"cannot read"]
    sequence = record.get("command_sequence")
    if not isinstance(sequence, dict):
        return ["command_sequence evidence is missing"]
    faults = [f"command_sequence.{fact} is not established"
              for fact in REQUIRED_SEQUENCE_FACTS if not sequence.get(fact)]
    unique = sequence.get("unique_witnesses", 0)
    agreeing = sequence.get("witnesses_in_required_direction", 0)
    if unique <= 0:
        faults.append("no source witness joined uniquely to final commands")
    elif agreeing != unique:
        faults.append(
            f"only {agreeing} of {unique} uniquely joined witnesses place the "
            f"earlier CPS2 entry later in final VDP1 order")
    return faults


def validate_control(name: str, record: dict) -> None:
    """Reject a control record that cannot support a verdict."""
    if name not in REQUIRED_SATURN_CONTROLS:
        raise ControlEvidenceError(f"unknown Saturn control: {name}")
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        raise ControlEvidenceError(
            f"{name} is missing required evidence: {sorted(missing)}")
    if record["status"] not in VALID_STATUS:
        raise ControlEvidenceError(
            f"{name} has invalid status {record['status']!r}")
    if record["baseline_build_sha256"] == record["variant_build_sha256"]:
        raise ControlEvidenceError(
            f"{name} compares a build against itself: the baseline and "
            f"variant hashes are identical")
    if name in COMMAND_TABLE_MUST_MATCH or name in COMMAND_TABLE_MUST_DIFFER:
        for key in ("baseline_command_table_sha256",
                    "variant_command_table_sha256"):
            if key not in record:
                raise ControlEvidenceError(
                    f"{name} requires {key}")


def score_control(name: str, record: dict) -> dict:
    """Decide one control. Returns {'detected': True|False|None}."""
    validate_control(name, record)
    if record["status"] == "blocked":
        return {"detected": None, "reason": record.get("blocked_reason",
                                                       "blocked")}
    if record["status"] == "failed":
        return {"detected": False, "reason": "recorded as failed"}

    reasons = []
    if record["observed_winner"] != record["expected_winner"]:
        reasons.append(
            f"observed winner {record['observed_winner']!r} is not the "
            f"predicted {record['expected_winner']!r}")
    if record.get("evidence_kind") == FINAL_COMMAND_SEQUENCE:
        reasons.extend(command_sequence_faults(name, record))
    elif record["witness_pixels_changed"] <= 0:
        reasons.append("the witness did not change")
    if record["negative_control_pixels_changed"] != 0:
        reasons.append(
            f"{record['negative_control_pixels_changed']} negative-control "
            f"pixels changed, so more than the declared variable moved")

    same = (record.get("baseline_command_table_sha256") ==
            record.get("variant_command_table_sha256"))
    if name in COMMAND_TABLE_MUST_MATCH and not same:
        reasons.append("the VDP1 command table changed, so this control "
                       "did not isolate the priority input")
    if name in COMMAND_TABLE_MUST_DIFFER and same:
        reasons.append("the VDP1 command table is unchanged, so the "
                       "variant did not alter the emitted commands")

    if reasons:
        return {"detected": False, "reason": "; ".join(reasons)}
    return {"detected": True, "reason": "predicted and observed agree"}


def build_saturn_status(controls: dict) -> dict:
    """Aggregate the three Saturn controls."""
    scored = {}
    for name in REQUIRED_SATURN_CONTROLS:
        if name not in controls:
            scored[name] = {"detected": None, "reason": "not recorded"}
            continue
        scored[name] = score_control(name, controls[name])

    executed = [n for n, s in scored.items() if s["detected"] is not None]
    passed = [n for n, s in scored.items() if s["detected"] is True]
    failed = [n for n, s in scored.items() if s["detected"] is False]

    if failed:
        status = "FAIL"
    elif len(passed) == len(REQUIRED_SATURN_CONTROLS):
        status = "MEASURED"
    else:
        status = "BLOCKED"

    return {
        "saturn_output_order_status": status,
        "saturn_vdp2_register_readback": "UNREADABLE",
        "mshvsf_priority_architecture": "ADAPTED",
        "animation_jump_record_coverage": "GAP",
        "controls_total": len(REQUIRED_SATURN_CONTROLS),
        "controls_executed": len(executed),
        "controls_passed": len(passed),
        "controls_blocked": len(REQUIRED_SATURN_CONTROLS) - len(executed),
        "per_control": scored,
    }


def as_v1_controls(controls: dict) -> dict:
    """The three Saturn controls in the v1 status module's shape."""
    scored = build_saturn_status(controls)["per_control"]
    mapping = {
        "command_order": "reverse_saturn_command_order",
        "cmdcolr_priority_selector": "change_cmdcolr_priority_bits",
        "sprite_priority_register_effect": "perturb_pris_prin",
    }
    return {mapping[name]: {"detected": result["detected"],
                            "note": result["reason"]}
            for name, result in scored.items()}
