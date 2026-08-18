#!/usr/bin/env python3
"""Validate the tracked MSHvSF training-plan artifact package."""

from __future__ import annotations

import json
from pathlib import Path


CLASSIFICATIONS = {
    "MATCH",
    "EQUIVALENT",
    "PLATFORM ADAPTATION",
    "OPTIMIZATION",
    "REDUCTION",
    "ALTERATION",
    "ADDITION",
    "BUG",
    "UNRESOLVED",
}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


JSON_ARTIFACTS = (
    "data/mshvsf_reference_audit.json",
    "data/mshvsf_cps2_vertical_slice.json",
    "data/mshvsf_saturn_disc_manifest.json",
    "data/mshvsf_saturn_first_pass.json",
    "data/mshvsf_saturn_asset_topology.json",
    "data/mshvsf_saturn_program_inventory.json",
    "data/mshvsf_cps2_semantic_model.json",
    "data/mshvsf_saturn_semantic_model.json",
    "data/mshvsf_reconstructed_vertical_slice.json",
    "data/mshvsf_correspondence.json",
    "data/mshvsf_difference_ledger.json",
    "data/mshvsf_hardware_budget.json",
    "data/mshvsf_fidelity_scorecard.json",
    "data/mshvsf_porting_patterns.json",
    "templates/capcom_saturn_porting/candidate_assessment.template.json",
    "templates/capcom_saturn_porting/system_mapping.template.json",
    "templates/capcom_saturn_porting/hardware_budget.template.json",
    "templates/capcom_saturn_porting/difference_ledger.template.json",
)

DOC_ARTIFACTS = (
    "docs/MSHVSF_REFERENCE_LANE.md",
    "docs/MSHVSF_SATURN_ARCHITECTURE.md",
    "docs/MSHVSF_TRAINING_PLAN_STATUS.md",
    "docs/MSHVSF_TO_AVP_TRANSFER_MATRIX.md",
    "docs/CAPCOM_SATURN_PORTING_PLAYBOOK.md",
    "docs/CAPCOM_SATURN_TRAINING_EXERCISES.md",
    "docs/CAPCOM_SATURN_PORT_CANDIDATE_CHECKLIST.md",
    "docs/CAPCOM_SATURN_PORT_ACCEPTANCE_CHECKLIST.md",
    "docs/CAPCOM_SATURN_FIDELITY_STANDARD.md",
)


def load(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require_fields(item: dict[str, object], fields: set[str], label: str) -> None:
    missing = fields - set(item)
    if missing:
        raise RuntimeError(f"{label} missing fields: {sorted(missing)}")


def main() -> int:
    for path in JSON_ARTIFACTS + DOC_ARTIFACTS:
        artifact = Path(path)
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty artifact: {path}")

    correspondence = load("data/mshvsf_correspondence.json")
    required_correspondence = {
        "id",
        "semantic_concept",
        "claim",
        "cps2_address_data_function",
        "saturn_address_data_function",
        "cps2_evidence",
        "saturn_evidence",
        "relationship",
        "test",
        "falsification",
        "confidence",
        "uncertainty",
        "avp_lesson",
    }
    for index, record in enumerate(correspondence["records"]):
        require_fields(record, required_correspondence, f"correspondence[{index}]")
        if record["relationship"] not in CLASSIFICATIONS:
            raise RuntimeError(f"Invalid correspondence classification: {record['relationship']}")
        if record["confidence"] not in CONFIDENCE:
            raise RuntimeError(f"Invalid correspondence confidence: {record['confidence']}")

    ledger = load("data/mshvsf_difference_ledger.json")
    for index, entry in enumerate(ledger["entries"]):
        require_fields(
            entry,
            {
                "id",
                "system",
                "original_behavior",
                "saturn_behavior",
                "observable",
                "classification",
                "reason",
                "evidence",
                "confidence",
                "mechanical_impact",
                "presentation_impact",
                "validation_status",
                "falsification",
            },
            f"difference_ledger[{index}]",
        )
        if entry["classification"] not in CLASSIFICATIONS:
            raise RuntimeError(f"Invalid ledger classification: {entry['classification']}")
        if entry["confidence"] not in CONFIDENCE:
            raise RuntimeError(f"Invalid ledger confidence: {entry['confidence']}")

    scorecard = load("data/mshvsf_fidelity_scorecard.json")
    dimensions = {item["dimension"] for item in scorecard["dimensions"]}
    expected_dimensions = {
        "gameplay",
        "animation",
        "graphics",
        "content",
        "audio",
        "performance",
    }
    if dimensions != expected_dimensions:
        raise RuntimeError(f"Unexpected fidelity dimensions: {sorted(dimensions)}")
    if scorecard["release_gate"] != "OPEN":
        raise RuntimeError("Pilot release gate must remain OPEN while required evidence is missing")
    expected_summary = {key: 0 for key in CLASSIFICATIONS}
    for record in correspondence["records"]:
        expected_summary[record["relationship"]] += 1
    actual_summary = dict(scorecard["classification_summary"])
    actual_summary.pop("source", None)
    actual_summary = {key: int(actual_summary.get(key, 0)) for key in CLASSIFICATIONS}
    if actual_summary != expected_summary:
        raise RuntimeError(
            "Fidelity classification summary does not match correspondence records"
        )

    resources = {item["resource"] for item in load("data/mshvsf_hardware_budget.json")["resources"]}
    required_resources = {
        "master_sh2",
        "slave_sh2",
        "work_ram_low",
        "work_ram_high",
        "expansion_ram_32mbit",
        "vdp1_vram",
        "vdp1_framebuffers",
        "vdp2_vram",
        "vdp2_color_ram",
        "scsp_sound_ram",
        "cd_data_track",
        "cdda",
        "dma",
    }
    if resources != required_resources:
        raise RuntimeError(f"Unexpected hardware resource set: {sorted(resources)}")

    patterns = load("data/mshvsf_porting_patterns.json")
    required_pattern = {
        "id",
        "pattern_class",
        "problem",
        "official_capcom_solution",
        "hardware_rationale",
        "implementation_pattern",
        "constraints",
        "applicable_game_types",
        "evidence",
        "confidence",
        "status",
    }
    ids: set[str] = set()
    for index, pattern in enumerate(patterns["patterns"]):
        require_fields(pattern, required_pattern, f"patterns[{index}]")
        if pattern["id"] in ids:
            raise RuntimeError(f"Duplicate pattern id: {pattern['id']}")
        ids.add(pattern["id"])
        if pattern["confidence"] not in CONFIDENCE:
            raise RuntimeError(f"Invalid pattern confidence: {pattern['confidence']}")
        if pattern["pattern_class"] == "CANDIDATE_CAPCOM_PATTERN" and pattern["status"] == "REUSABLE_METHOD":
            raise RuntimeError(f"Unconfirmed Capcom candidate promoted: {pattern['id']}")

    reconstruction = load("data/mshvsf_reconstructed_vertical_slice.json")
    if reconstruction["status"] != "FIRST_PASS_COMPLETE_PROJECTILE_DEFERRED":
        raise RuntimeError("Reconstruction boundary no longer matches evidence")
    if not any(item["semantic_concept"] == "Hadouken projectile lifecycle" and item["saturn"] is None for item in reconstruction["events"]):
        raise RuntimeError("Deferred Saturn projectile gap is not explicit")

    manifest = load("data/mshvsf_saturn_disc_manifest.json")
    runtime = manifest["verified_runtime_observation"]
    if runtime.get("paired_report") != "data/mshvsf_saturn_first_pass.json":
        raise RuntimeError("Disc manifest contains stale deterministic-input status")

    print(
        f"Validated {len(JSON_ARTIFACTS)} JSON artifacts, "
        f"{len(DOC_ARTIFACTS)} documents, "
        f"{len(correspondence['records'])} correspondence records, and "
        f"{len(patterns['patterns'])} patterns."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
