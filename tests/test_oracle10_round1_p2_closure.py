#!/usr/bin/env python3
"""Validate the cumulative P2 closure report and its rejection controls."""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = json.loads((ROOT / "data/oracle10_round1_p2_closure.json")
                    .read_text(encoding="ascii"))
GENERATOR = (ROOT / "tools/analyze_oracle10_round1_p2_closure.py") \
    .read_text(encoding="utf-8")


def validate(report: dict[str, object]) -> None:
    coverage = report["source_coverage"]
    identity = report["paired_full_route_identity"]
    ownership = report["ownership_closure"]
    programs = report["p3_reusable_program_controller_families"]
    demand = report["table_demand_delta"]
    mutable = report["mutable_carve"]
    assert report["status"] == "P2_CLOSED"
    assert coverage["accepted_pre_p2_range"] == [1972, 5566]
    assert coverage["p2_extension_range"] == [5567, 15193]
    assert coverage["complete_round1_route_span"] == [1972, 15193]
    assert coverage["complete_round1_route_frames"] == 13222
    assert coverage["p2_frames"] == 9627
    assert coverage["segment_count"] == 20
    assert coverage["continuous"] is True
    assert coverage["non_overlapping"] is True
    assert coverage["stable_round2_handoff_frame"] == 15193
    assert coverage["round2_gameplay_census_extended"] is False
    assert coverage["round1_to_round2_seam_classification"] == \
        "ADAPTED_PRESENTATION_FOR_USER_10"
    assert len(report["segment_evidence"]) == 20
    assert report["segment_evidence"][0]["source_frame_range"] == [5567, 6200]
    assert report["segment_evidence"][-1]["source_frame_range"] == [15193, 15193]
    assert identity["independently_launched"] is True
    assert identity["raw_capture_files_byte_identical"] is True
    assert identity["all_segment_semantics_byte_identical"] is True
    assert identity["segment_semantic_stream_sha256"] == \
        "0da340aab00fdb0f2654c2a2ee92033398ced92be8207131fc99a426ad46b038"
    assert ownership["contradictory_segment_ownership"] == []
    assert ownership["zero_unidentified_or_unowned_gameplay_authority"] is True
    assert all(value == 0 for value in ownership["coverage_gaps"].values())
    assert [(row["class"], row["type"], row["source_owner"],
             row["first_p2_source_frame"])
            for row in ownership["new_class_type_pairs_vs_frame_5566"]] == [
                ("0x00", 12, "round1-enemy-archetypes", 5567),
                ("0x01", 12, "round1-enemy-archetypes", 9976),
                ("0x4b", 24,
                 "pickups-equipment-weapons-projectiles-hazards-destructibles",
                 6693),
            ]
    assert len(programs["actor_programs"]) == 9
    assert len(programs["route_transition_programs"]) == 7
    assert len(programs["audio_owner_families"]) == 6
    assert len(programs["load_release_boundaries"]) == 2
    assert report["route_controls"]["paired_route_state_edges"] == 10
    assert report["route_controls"]["accepted_route_perturbation"]["status"] == "PASS"
    assert report["route_controls"]["accepted_failure_continue"] \
        ["stable_round2_handoff_frame"] == 15193
    assert all(value == "PASS" or key == "production_runtime_writes"
               for key, value in report["route_controls"]
               ["accepted_counterfactual_gate"].items())
    assert report["route_controls"]["accepted_counterfactual_gate"] \
        ["production_runtime_writes"] == 0
    assert demand == {
        "accepted_archive_bytes": 47056,
        "accepted_archive_sha256":
            "ccf8795a147daf337c1f72364c81f05fc2cfd255d8d21b40a56c74c97f8d15bd",
        "accepted_archive_table_count": 157,
        "new_table_bytes": 0,
        "new_table_count": 0,
        "unbound_table_identities": [],
    }
    assert mutable["capacity_bytes"] == 102400
    assert mutable["required_bytes_before_p2"] == 99380
    assert mutable["required_bytes_after_p2"] == 99380
    assert mutable["p2_headroom_consumed_bytes"] == 0
    assert mutable["remaining_headroom_bytes"] == 3020
    assert all(not values for values in report["remaining_blockers"].values())
    assert report["memory_plan_holds_without_revision"] is True
    assert report["next_phase"] == "P3_SPEC02_BATCHED_WHOLE_ROUTINE_BODIES"
    assert report["physical_saturn"] == "UNRUN"


validate(REPORT)
for token in ("P2_FIRST = 5567", "STABLE_ROUND2_SEAM = 15193",
              "contradictory pair ownership", "accepted archive identity drift",
              "memory-plan archive identity drift"):
    assert token in GENERATOR, f"P2 closure generator control missing: {token}"

for label, path, value in (
        ("coverage gap", ("source_coverage", "continuous"), False),
        ("overlap", ("source_coverage", "non_overlapping"), False),
        ("semantic identity", ("paired_full_route_identity",
                               "all_segment_semantics_byte_identical"), False),
        ("ownership", ("ownership_closure",
                       "zero_unidentified_or_unowned_gameplay_authority"), False),
        ("actor program", ("p3_reusable_program_controller_families",
                           "actor_programs"), []),
        ("route program", ("p3_reusable_program_controller_families",
                           "route_transition_programs"), []),
        ("archive", ("table_demand_delta", "accepted_archive_table_count"), 156),
        ("unbound table", ("table_demand_delta", "unbound_table_identities"),
                          ["0xdeadbe"]),
        ("capacity", ("mutable_carve", "remaining_headroom_bytes"), -1),
        ("memory plan", ("memory_plan_holds_without_revision",), False),
        ("round2 gameplay", ("source_coverage",
                             "round2_gameplay_census_extended"), True),
        ("physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(REPORT)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"P2 closure mutation accepted: {label}")

print("ORACLE-10 Round 1 P2 cumulative closure: PASS (12 mutations rejected)")
