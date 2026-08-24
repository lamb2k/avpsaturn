#!/usr/bin/env python3
"""Schema, disposition, and transition checks for the port_v2 migration ledger."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/port_v2_migration_map.yaml"

DECISIONS = {
    "UNTESTED", "SALVAGE_AS_IS", "SALVAGE_WITH_ADAPTER", "REPAIR",
    "REPLACE", "PROMOTED", "DEFERRED",
}
TECHNICAL = {"PASS", "FAIL", "UNRUN"}
FIDELITY = {"MEASURED", "ADAPTED", "UNKNOWN"}
USER = {
    "NOT_REVIEWED", "AWAITING_USER_FEEDBACK", "APPROVED",
    "CHANGES_REQUESTED",
}
REQUIRED_SUBSYSTEMS = {
    "old-build-baseline", "build-iso-pipeline", "loading-memory-ownership",
    "controller-input", "player-assets", "player-rendering",
    "player-animation", "enemy-assets", "enemy-rendering",
    "enemy-animation", "collision-combat", "palette-cram",
    "vdp2-stage-layers", "camera-framing", "hud", "pcm",
    "cdda-residency", "diagnostics-emulator-readback",
    "playable-skeleton-prototype", "player-action-controller",
    "street-alien-ai", "round1-encounter-controller",
}
REQUIRED_FIELDS = {
    "id", "existing_source_paths", "existing_dependencies",
    "authored_controller_coupling", "proposed_isolated_bench",
    "technical_status", "fidelity_status", "user_status",
    "salvage_decision", "production_interface", "promoted_commit", "blockers",
    "exact_next_experiment", "user_feedback",
}
QUESTION = (
    "What should remain unchanged, what looks or feels wrong, and which issue "
    "should be fixed first?"
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_relative_artifact(value: str, field: str) -> None:
    require(bool(value) and not Path(value).is_absolute(),
            f"{field} is not a relative artifact path")
    require(".." not in Path(value).parts, f"{field} escapes the repository")


def validate_artifact_metadata(entry: dict, identity: str | None = None) -> None:
    identity = identity or entry.get("id") or entry.get("task_id") or "ledger entry"
    for field, value in entry.items():
        if value is None:
            continue
        if isinstance(value, dict):
            validate_artifact_metadata(value, identity)
            continue
        if field.endswith("_sha256"):
            require(isinstance(value, str) and SHA256.fullmatch(value) is not None,
                    f"{identity} {field} is not a SHA-256")
        if field in {"evidence_commit", "evaluated_commit", "promoted_commit"}:
            require(isinstance(value, str) and COMMIT.fullmatch(value) is not None,
                    f"{identity} {field} is not a commit id")
        if field in {"diagnostic_interface", "production_interface", "artifact_path"}:
            require_relative_artifact(value, f"{identity} {field}")


def validate_disposition(entry: dict) -> None:
    require(entry["technical_status"] in TECHNICAL,
            f"{entry['id']} invalid technical status")
    require(entry["fidelity_status"] in FIDELITY,
            f"{entry['id']} invalid fidelity status")
    require(entry["user_status"] in USER,
            f"{entry['id']} invalid user status")
    require(entry["salvage_decision"] in DECISIONS,
            f"{entry['id']} invalid salvage decision")

    technical = entry["technical_status"]
    fidelity = entry["fidelity_status"]
    user_status = entry["user_status"]
    decision = entry["salvage_decision"]
    if technical == "UNRUN" or decision == "UNTESTED":
        require(technical == "UNRUN" and fidelity == "UNKNOWN" and
                user_status == "NOT_REVIEWED" and decision == "UNTESTED",
                f"{entry['id']} has an internally inconsistent untested state")
    if technical == "FAIL":
        require(decision in {"REPAIR", "REPLACE", "DEFERRED"},
                f"{entry['id']} failed without a repair, replace, or defer decision")
    if decision == "PROMOTED":
        require(technical == "PASS", f"{entry['id']} promoted without a pass")
        require(isinstance(entry["production_interface"], str) and
                entry["production_interface"],
                f"{entry['id']} promoted without a production interface")
        require(isinstance(entry["promoted_commit"], str) and
                COMMIT.fullmatch(entry["promoted_commit"]) is not None,
                f"{entry['id']} promoted without a pinned commit")
    else:
        require(entry["production_interface"] is None and
                entry["promoted_commit"] is None,
                f"{entry['id']} claims production metadata before promotion")

    blockers = entry["blockers"]
    require(isinstance(blockers, list), f"{entry['id']} blockers are not a list")
    for blocker in blockers:
        require(isinstance(blocker, str) and blocker.startswith("Unblock:"),
                f"{entry['id']} blocker lacks an unblock condition")

    feedback = entry["user_feedback"]
    require(set(feedback) == {
        "exact_response", "approved_components", "requested_changes", "priority",
    }, f"{entry['id']} user feedback schema drifted")
    if user_status in {"NOT_REVIEWED", "AWAITING_USER_FEEDBACK"}:
        require(feedback["exact_response"] is None,
                f"{entry['id']} invents user feedback")
    if user_status == "APPROVED":
        require(bool(feedback["exact_response"]) or bool(feedback["approved_components"]),
                f"{entry['id']} approval lacks feedback or evidence")
    if user_status == "CHANGES_REQUESTED":
        require(bool(feedback["requested_changes"]) and
                bool(entry["exact_next_experiment"]),
                f"{entry['id']} requested changes lack a correction path")

    require(bool(entry["authored_controller_coupling"]),
            f"{entry['id']} lacks coupling classification")
    require(bool(entry["proposed_isolated_bench"]),
            f"{entry['id']} lacks proposed bench")
    require(bool(entry["exact_next_experiment"]),
            f"{entry['id']} lacks next experiment")
    validate_artifact_metadata(entry)


def validate_card_results(ledger: dict) -> None:
    required = {
        "task_id", "evaluated_commit", "technical_status", "fidelity_status",
        "user_status", "salvage_decision", "production_interface",
        "diagnostic_interface", "blockers", "exact_next_experiment", "evidence",
        "user_observation_state",
    }
    results = ledger.get("card_results", [])
    ids = [result.get("task_id") for result in results]
    require(len(ids) == len(set(ids)), "duplicate card-result task ids")
    for result in results:
        missing = required - set(result)
        require(not missing, f"{result.get('task_id')} missing {sorted(missing)}")
        require(result["technical_status"] in TECHNICAL,
                f"{result['task_id']} invalid technical status")
        require(result["fidelity_status"] in FIDELITY,
                f"{result['task_id']} invalid fidelity status")
        require(result["user_status"] in USER,
                f"{result['task_id']} invalid user status")
        require(result["salvage_decision"] in DECISIONS,
                f"{result['task_id']} invalid salvage decision")
        require_relative_artifact(result["diagnostic_interface"],
                                  f"{result['task_id']} diagnostic interface")
        if result["production_interface"] is not None:
            require(result["salvage_decision"] == "PROMOTED",
                    f"{result['task_id']} claims a production interface without promotion")
            require_relative_artifact(
                result["production_interface"],
                f"{result['task_id']} production interface",
            )
        for blocker in result["blockers"]:
            require(isinstance(blocker, str) and blocker.startswith("Unblock:"),
                    f"{result['task_id']} blocker lacks an unblock condition")
        require(bool(result["exact_next_experiment"]),
                f"{result['task_id']} lacks next experiment")
        observations = result["user_observation_state"]
        require(observations["formal_review_question_asked"] is False,
                f"{result['task_id']} invents a formal user review")
        require(observations["approved_components"] == [] and
                observations["requested_changes"] == [] and
                observations["priority"] is None,
                f"{result['task_id']} invents an approval or requested change")
        validate_artifact_metadata(result)


def validate_ledger(ledger: dict) -> None:
    # JSON is a strict YAML 1.2 subset and avoids a runtime parser dependency.
    require(ledger["schema"] == 1, "unsupported migration schema")
    require(ledger["workflow"] == "interactive-salvage-promotion-integration",
            "migration workflow drifted")
    require(set(ledger["decision_values"]) == DECISIONS, "decision enum drifted")
    require(set(ledger["technical_status_values"]) == TECHNICAL,
            "technical enum drifted")
    require(set(ledger["fidelity_status_values"]) == FIDELITY,
            "fidelity enum drifted")
    require(set(ledger["user_status_values"]) == USER, "user enum drifted")

    contract = ledger["human_review_contract"]
    require(contract["package_root"] == "build/feedback/<task-id>/",
            "feedback package root drifted")
    require(contract["required_question"] == QUESTION, "feedback question drifted")
    require(contract["approval_from_silence"] is False,
            "silence can become approval")
    require(contract["exact_response_required"] is True,
            "exact user response is not required")

    prototypes = ledger["prototype_inventory"]
    require(len(prototypes) == 1, "prototype inventory drifted")
    prototype = prototypes[0]
    require(prototype["classification"] in {
        "REUSABLE_STATE", "THIN_ADAPTER", "DUPLICATE_INFRASTRUCTURE",
        "LAB_ONLY_DIAGNOSTIC", "UNNECESSARY_WORK",
    }, "invalid prototype classification")
    require(prototype["classification"] == "REUSABLE_STATE" and
            prototype["dirty"] is True and prototype["preserve"] is True,
            "dirty prototype is not preserved reusable state")

    subsystems = ledger["subsystems"]
    ids = [entry["id"] for entry in subsystems]
    require(len(ids) == len(set(ids)), "duplicate subsystem ids")
    require(set(ids) == REQUIRED_SUBSYSTEMS,
            "major subsystem inventory is incomplete")
    for entry in subsystems:
        missing = REQUIRED_FIELDS - set(entry)
        require(not missing, f"{entry.get('id')} missing {sorted(missing)}")
        require(isinstance(entry["existing_source_paths"], list) and
                entry["existing_source_paths"], f"{entry['id']} lacks source paths")
        require(isinstance(entry["existing_dependencies"], list),
                f"{entry['id']} dependencies are not a list")
        validate_disposition(entry)
    for identifier in (
        "player-action-controller", "street-alien-ai",
        "round1-encounter-controller",
    ):
        entry = subsystem(ledger, identifier)
        require(entry["technical_status"] == "UNRUN" and
                entry["fidelity_status"] == "UNKNOWN" and
                entry["salvage_decision"] == "UNTESTED",
                f"{identifier} advanced before live-gameplay execution")
    validate_card_results(ledger)


def subsystem(ledger: dict, identifier: str) -> dict:
    return next(entry for entry in ledger["subsystems"] if entry["id"] == identifier)


def expect_invalid(ledger: dict, message: str) -> None:
    try:
        validate_ledger(ledger)
    except AssertionError:
        return
    raise AssertionError(message)


def initial_fixture(ledger: dict) -> dict:
    fixture = copy.deepcopy(ledger)
    for entry in fixture["subsystems"]:
        entry.update({
            "technical_status": "UNRUN", "fidelity_status": "UNKNOWN",
            "user_status": "NOT_REVIEWED", "salvage_decision": "UNTESTED",
            "production_interface": None, "promoted_commit": None, "blockers": [],
        })
        entry.pop("evidence_commit", None)
        entry["user_feedback"] = {
            "exact_response": None, "approved_components": [],
            "requested_changes": [], "priority": None,
        }
    return fixture


def validate_transition_fixtures(ledger: dict) -> None:
    initial = initial_fixture(ledger)
    validate_ledger(initial)

    progressed = copy.deepcopy(initial)
    entry = subsystem(progressed, "loading-memory-ownership")
    entry.update({"technical_status": "PASS", "fidelity_status": "MEASURED",
                  "salvage_decision": "SALVAGE_AS_IS"})
    validate_ledger(progressed)

    awaiting = copy.deepcopy(progressed)
    subsystem(awaiting, "loading-memory-ownership")["user_status"] = \
        "AWAITING_USER_FEEDBACK"
    validate_ledger(awaiting)

    blocked = copy.deepcopy(progressed)
    subsystem(blocked, "loading-memory-ownership")["blockers"] = [
        "Unblock: capture the missing allocation readback from the pinned emulator."
    ]
    validate_ledger(blocked)

    promoted = copy.deepcopy(progressed)
    entry = subsystem(promoted, "loading-memory-ownership")
    entry.update({"user_status": "APPROVED", "salvage_decision": "PROMOTED",
                  "production_interface": "port_v2/loading_memory",
                  "promoted_commit": "a" * 40})
    entry["user_feedback"] = {
        "exact_response": "Keep the proven player loading behavior unchanged.",
        "approved_components": ["player loading"], "requested_changes": [], "priority": None,
    }
    validate_ledger(promoted)

    invalid_untested = copy.deepcopy(progressed)
    subsystem(invalid_untested, "loading-memory-ownership")["salvage_decision"] = \
        "UNTESTED"
    expect_invalid(invalid_untested, "tested subsystem accepted an UNTESTED decision")

    invalid_promotion = copy.deepcopy(promoted)
    subsystem(invalid_promotion, "loading-memory-ownership")["promoted_commit"] = None
    expect_invalid(invalid_promotion, "promotion accepted missing commit metadata")

    invalid_approval = copy.deepcopy(promoted)
    entry = subsystem(invalid_approval, "loading-memory-ownership")
    entry["user_feedback"] = {"exact_response": None, "approved_components": [],
                              "requested_changes": [], "priority": None}
    expect_invalid(invalid_approval, "approval accepted without feedback evidence")

    invalid_changes = copy.deepcopy(progressed)
    entry = subsystem(invalid_changes, "loading-memory-ownership")
    entry["user_status"] = "CHANGES_REQUESTED"
    expect_invalid(invalid_changes, "changes requested accepted without requested changes")

    invalid_blocker = copy.deepcopy(blocked)
    subsystem(invalid_blocker, "loading-memory-ownership")["blockers"] = ["Need readback"]
    expect_invalid(invalid_blocker, "blocker accepted without unblock condition")

    invalid_hash = copy.deepcopy(progressed)
    subsystem(invalid_hash, "loading-memory-ownership")["evidence_sha256"] = "not-a-hash"
    expect_invalid(invalid_hash, "invalid evidence hash was accepted")


def main() -> None:
    ledger = json.loads(PATH.read_text(encoding="utf-8"))
    validate_ledger(ledger)
    validate_transition_fixtures(ledger)
    print("migration-map schema and transitions: PASS")


if __name__ == "__main__":
    main()
