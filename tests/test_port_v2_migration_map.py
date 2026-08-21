#!/usr/bin/env python3
"""Schema and neutral-initialization checks for the port_v2 migration ledger."""

from __future__ import annotations

import json
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
    "playable-skeleton-prototype",
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # JSON is a strict YAML 1.2 subset and avoids a runtime parser dependency.
    ledger = json.loads(PATH.read_text(encoding="utf-8"))
    require(ledger["schema"] == 1, "unsupported migration schema")
    require(ledger["workflow"] ==
            "interactive-salvage-promotion-integration",
            "migration workflow drifted")
    require(set(ledger["decision_values"]) == DECISIONS,
            "decision enum drifted")
    require(set(ledger["technical_status_values"]) == TECHNICAL,
            "technical enum drifted")
    require(set(ledger["fidelity_status_values"]) == FIDELITY,
            "fidelity enum drifted")
    require(set(ledger["user_status_values"]) == USER,
            "user enum drifted")

    contract = ledger["human_review_contract"]
    require(contract["package_root"] == "build/feedback/<task-id>/",
            "feedback package root drifted")
    require(contract["required_question"] == QUESTION,
            "feedback question drifted")
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
        require(entry["technical_status"] in TECHNICAL,
                f"{entry['id']} invalid technical status")
        require(entry["fidelity_status"] in FIDELITY,
                f"{entry['id']} invalid fidelity status")
        require(entry["user_status"] in USER,
                f"{entry['id']} invalid user status")
        require(entry["salvage_decision"] in DECISIONS,
                f"{entry['id']} invalid salvage decision")
        require(entry["technical_status"] == "UNRUN" and
                entry["fidelity_status"] == "UNKNOWN" and
                entry["user_status"] == "NOT_REVIEWED" and
                entry["salvage_decision"] == "UNTESTED",
                f"{entry['id']} assumes a result before its bench")
        require(isinstance(entry["existing_source_paths"], list) and
                entry["existing_source_paths"],
                f"{entry['id']} lacks source paths")
        require(isinstance(entry["existing_dependencies"], list),
                f"{entry['id']} dependencies are not a list")
        require(isinstance(entry["blockers"], list),
                f"{entry['id']} blockers are not a list")
        require(bool(entry["authored_controller_coupling"]),
                f"{entry['id']} lacks coupling classification")
        require(bool(entry["proposed_isolated_bench"]),
                f"{entry['id']} lacks proposed bench")
        require(bool(entry["exact_next_experiment"]),
                f"{entry['id']} lacks next experiment")
        require(entry["production_interface"] is None and
                entry["promoted_commit"] is None,
                f"{entry['id']} claims promotion before a bench")
        feedback = entry["user_feedback"]
        require(set(feedback) == {
            "exact_response", "approved_components", "requested_changes",
            "priority",
        }, f"{entry['id']} user feedback schema drifted")
        require(feedback["exact_response"] is None,
                f"{entry['id']} invents user feedback")

    print("migration-map schema: PASS")


if __name__ == "__main__":
    main()
