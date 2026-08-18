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
    "data/mshvsf_saturn_runtime_memory.json",
    "data/mshvsf_cps2_semantic_model.json",
    "data/mshvsf_saturn_semantic_model.json",
    "data/mshvsf_reconstructed_vertical_slice.json",
    "data/mshvsf_correspondence.json",
    "data/mshvsf_difference_ledger.json",
    "data/mshvsf_hardware_budget.json",
    "data/mshvsf_fidelity_scorecard.json",
    "data/mshvsf_porting_patterns.json",
    "data/mshvsf_saturn_vdp1_control_flow.json",
    "data/mshvsf_saturn_vdp2_scsp.json",
    "data/reference_engine_normal_hit_report.json",
    "templates/capcom_saturn_porting/candidate_assessment.template.json",
    "templates/capcom_saturn_porting/system_mapping.template.json",
    "templates/capcom_saturn_porting/hardware_budget.template.json",
    "templates/capcom_saturn_porting/difference_ledger.template.json",
)

DOC_ARTIFACTS = (
    "docs/MSHVSF_AGENT_HANDOFF.md",
    "docs/MSHVSF_REFERENCE_LANE.md",
    "docs/MSHVSF_SATURN_ARCHITECTURE.md",
    "docs/MSHVSF_TRAINING_PLAN_STATUS.md",
    "docs/MSHVSF_TO_AVP_TRANSFER_MATRIX.md",
    "docs/CAPCOM_SATURN_PORTING_PLAYBOOK.md",
    "docs/CAPCOM_SATURN_TRAINING_EXERCISES.md",
    "docs/CAPCOM_SATURN_PORT_CANDIDATE_CHECKLIST.md",
    "docs/CAPCOM_SATURN_PORT_ACCEPTANCE_CHECKLIST.md",
    "docs/CAPCOM_SATURN_FIDELITY_STANDARD.md",
    "docs/CPS2_SATURN_REFERENCE_ENGINE.md",
    "docs/CPS2_SATURN_REFERENCE_ENGINE_AVP_ADAPTERS.md",
)

EVIDENCE_LABELS = ("MEASURED", "DECODED", "INFERRED", "ADAPTED", "UNRESOLVED")


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

    memory = load("data/mshvsf_saturn_runtime_memory.json")
    if memory.get("evidence_class") != "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP":
        raise RuntimeError("Saturn memory evidence lost its AvP promotion boundary")
    expected_anchors = {
        "idle": 3540,
        "normal_active": 3828,
        "impact": 3840,
        "recovery": 3900,
    }
    actual_anchors = {
        item["label"]: item["captured_frame"] for item in memory["anchors"]
    }
    if actual_anchors != expected_anchors:
        raise RuntimeError(f"Unexpected Saturn memory anchors: {actual_anchors}")
    if len(memory.get("transitions", [])) != 3:
        raise RuntimeError("Saturn memory report must contain three anchor transitions")

    vdp1 = load("data/mshvsf_saturn_vdp1_control_flow.json")
    if vdp1.get("evidence_class") != "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP":
        raise RuntimeError("VDP1 control-flow report lost its AvP promotion boundary")
    vdp1_anchors = {item["label"]: item["captured_frame"] for item in vdp1["anchors"]}
    if vdp1_anchors != expected_anchors:
        raise RuntimeError(f"Unexpected VDP1 control-flow anchors: {vdp1_anchors}")
    for anchor in vdp1["anchors"]:
        for key in ("reachable_slot_count", "sequential_slot_count", "stored_nonzero_slots"):
            if key not in anchor:
                raise RuntimeError(f"VDP1 anchor {anchor['label']} is missing {key}")
        if anchor["stored_nonzero_slots"] <= anchor["reachable_slot_count"]:
            raise RuntimeError(
                f"VDP1 anchor {anchor['label']} no longer distinguishes reachable "
                "commands from sequentially stored commands"
            )
        if anchor["control_flow_anomalies"]:
            raise RuntimeError(
                f"VDP1 anchor {anchor['label']} reports control-flow anomalies: "
                f"{anchor['control_flow_anomalies']}"
            )
    for finding in vdp1["findings"]:
        require_fields(
            finding,
            {"id", "claim", "holds", "consequence", "falsification", "evidence"},
            f"vdp1_finding[{finding.get('id')}]",
        )
        if finding["evidence"] not in EVIDENCE_LABELS:
            raise RuntimeError(f"Invalid VDP1 finding label: {finding['evidence']}")

    video_audio = load("data/mshvsf_saturn_vdp2_scsp.json")
    if video_audio.get("evidence_class") != "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP":
        raise RuntimeError("VDP2/SCSP report lost its AvP promotion boundary")
    va_anchors = {item["label"]: item["captured_frame"] for item in video_audio["anchors"]}
    if va_anchors != expected_anchors:
        raise RuntimeError(f"Unexpected VDP2/SCSP anchors: {va_anchors}")
    for anchor in video_audio["anchors"]:
        if anchor["vdp2"]["vdp2_registers_readable"]:
            raise RuntimeError(
                f"VDP2 registers became readable at {anchor['label']}; the recorded "
                "instrument limit is stale and layer claims must be re-derived"
            )
        if not anchor["vdp2"]["all_referenced_banks_populated"]:
            raise RuntimeError(
                f"A VDP1 colour bank at {anchor['label']} does not resolve into "
                "populated colour RAM"
            )
    for transition in video_audio["transitions"]:
        if not transition["scsp_slot_registers_identical"]:
            raise RuntimeError(
                f"SCSP slot registers changed between {transition['from']} and "
                f"{transition['to']}; the static-slot finding no longer holds"
            )
        if transition["sound_ram_changed_bytes"] <= 0:
            raise RuntimeError(
                f"Sound RAM did not change between {transition['from']} and "
                f"{transition['to']}; the streaming inference loses its support"
            )
    for finding in video_audio["findings"]:
        require_fields(
            finding,
            {"id", "claim", "holds", "consequence", "falsification", "evidence"},
            f"vdp2_scsp_finding[{finding.get('id')}]",
        )
        if finding["evidence"] not in EVIDENCE_LABELS:
            raise RuntimeError(f"Invalid VDP2/SCSP finding label: {finding['evidence']}")

    engine = load("data/reference_engine_normal_hit_report.json")
    for claim_name, claim in engine["claims"].items():
        if claim["evidence"] not in EVIDENCE_LABELS:
            raise RuntimeError(f"Unlabelled reference-engine claim: {claim_name}")
        if claim["evidence"] == "INFERRED" and not claim.get("falsification"):
            raise RuntimeError(f"Inferred claim without falsification: {claim_name}")
        if claim["evidence"] == "UNRESOLVED" and not claim.get("probe"):
            raise RuntimeError(f"Unresolved claim without probe: {claim_name}")
    counts = engine["evidence_label_counts"]
    missing_labels = [label for label in EVIDENCE_LABELS if not counts.get(label)]
    if missing_labels:
        raise RuntimeError(f"Reference-engine report lacks labels: {missing_labels}")
    if not engine["prohibited_inferences"]:
        raise RuntimeError("Reference-engine report must state its prohibited inferences")
    if not engine["required_avp_probe"].strip():
        raise RuntimeError("Reference-engine report must name the required AvP probe")
    for sentence in ("will_decide", "must_verify"):
        if not engine["decision_statement"].get(sentence, "").strip():
            raise RuntimeError(f"Reference-engine report must complete {sentence}")
    for item in engine["inputs"]:
        if len(item["sha256"]) != 64:
            raise RuntimeError(f"Reference-engine input lacks a hash: {item['path']}")

    print(
        f"Validated {len(JSON_ARTIFACTS)} JSON artifacts, "
        f"{len(DOC_ARTIFACTS)} documents, "
        f"{len(correspondence['records'])} correspondence records, and "
        f"{len(patterns['patterns'])} patterns."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
