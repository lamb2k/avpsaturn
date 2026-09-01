#!/usr/bin/env python3
"""Validate the first post-Coffee-Shop paired census segment and mutations."""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = json.loads((ROOT / "data/oracle10_round1_census_extension_5567_6200.json")
                    .read_text(encoding="ascii"))
CONTINUE = json.loads((ROOT / "data/oracle10_round1_census_extension_6201_6692.json")
                      .read_text(encoding="ascii"))
WAREHOUSE = json.loads((ROOT / "data/oracle10_round1_census_extension_6693_7438.json")
                       .read_text(encoding="ascii"))
INTERWAVE = json.loads((ROOT / "data/oracle10_round1_census_extension_7439_7503.json")
                       .read_text(encoding="ascii"))
WAREHOUSE2 = json.loads((ROOT / "data/oracle10_round1_census_extension_7504_9004.json")
                        .read_text(encoding="ascii"))
INTERWAVE2 = json.loads((ROOT / "data/oracle10_round1_census_extension_9005_9039.json")
                        .read_text(encoding="ascii"))
GENERATOR = (ROOT / "tools/analyze_oracle10_round1_census_extension.py") \
    .read_text(encoding="utf-8")


def validate(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    coverage = report["coverage"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [5567, 6200]
    assert ceremony["independent_raw_captures"] == [
        "full_route", "full_route_rerun"]
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 634
    assert semantics["canonical_semantic_sha256"] == \
        "4a4a0ab9d4485ca37e15e9bb6e1644748cec11455fb8298f1338d96f2629ee30"
    assert semantics["player_active_frames"] == 632
    assert semantics["required_character_u8"] == 0
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"]) for row in
            census["class_type_inventory"]] == [
                ("0x00", 0), ("0x00", 12), ("0x06", 12),
                ("0x07", 20), ("0x49", 24)]
    assert len(census["actor_lifetimes"]) == 16
    assert len(census["spawn_edges"]) == 13
    assert len(census["despawn_edges"]) == 12
    assert len(census["hit_ko_transitions"]) == 57
    assert census["audio"]["handler_transaction_count"] == 39
    assert len(census["audio"]["source_owned_trigger_groups_first_seen"]) == 12
    assert len(census["audio"]["player_origin_edges"]) == 5
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert [row["sample_transition_frame"] for row in report
            ["route_authority_extension"]["route_state_edges"]] == [
                5720, 6199, 6200]
    assert [row["id"] for row in census["load_release_boundaries"]] == [
        "route-load-release-6200"]
    assert census["load_release_boundaries"][0]["failure_control"] \
        ["package_difference"] is True
    assert report["table_demand_delta"]["unbound_table_identities"] == []
    assert report["table_demand_delta"] \
        ["spec_executable_review_deferred_to_p3"] is True
    assert all(value == 0 for value in coverage.values())
    assert report["physical_saturn"] == "UNRUN"


def reject(label: str, path: tuple[str, ...], value: object) -> None:
    mutant = copy.deepcopy(REPORT)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate(mutant)
    except AssertionError:
        return
    raise AssertionError(f"Round 1 census mutation accepted: {label}")


validate(REPORT)
for token in (
        "PLAYER = 0xFF8380", "player_offset + 0xD2", "region_workram.bin",
        "paired route ledger drift", "unowned post-Coffee-Shop class/type"):
    assert token in GENERATOR, f"census generator control missing: {token}"

reject("semantic identity", ("paired_capture_ceremony", "segment_semantics",
                             "canonical_semantic_sha256"), "0" * 64)
reject("character swap", ("paired_capture_ceremony", "segment_semantics",
                          "character_mismatch_frames"), [5800])
reject("identity gate", ("paired_capture_ceremony", "segment_semantics",
                        "per_frame_character_identity_gate"), False)
reject("unowned class", ("coverage", "unidentified_source_class_type_pairs"),
       1)
reject("route edge", ("route_authority_extension", "route_state_edges"), [])
reject("audio owner", ("scene_census_delta", "audio",
                       "orphan_trigger_groups"), 1)
reject("load control", ("scene_census_delta", "load_release_boundaries"), [])
reject("physical claim", ("physical_saturn",), "PASS")


def validate_continue(report: dict[str, object]) -> None:
    validate_common = report["paired_capture_ceremony"]
    semantics = validate_common["segment_semantics"]
    census = report["scene_census_delta"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [6201, 6692]
    assert report["segment"]["scene_ids"] == ["continue-countdown"]
    assert validate_common["raw_capture_files_byte_identical"] is True
    assert validate_common["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 492
    assert semantics["canonical_semantic_sha256"] == \
        "d93a3dcd53bf4951d0631bcf0927a6560b399da1bb913414e3de94f212252c2e"
    assert semantics["player_active_frames"] == 0
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"]) for row in
            census["class_type_inventory"]] == [
                ("0x00", 12), ("0x06", 12), ("0x07", 20)]
    assert len(census["actor_lifetimes"]) == 4
    assert census["spawn_edges"] == [] and census["despawn_edges"] == []
    assert census["hit_ko_transitions"] == []
    assert census["audio"]["handler_transaction_count"] == 1
    assert census["audio"]["command_counts"] == {"0x000f": 1}
    assert census["load_release_boundaries"] == []
    edges = report["route_authority_extension"]["route_state_edges"]
    assert [(row["sample_transition_frame"], row["writer_pc"], row["value"])
            for row in edges] == [(6692, "0x0090f2", 4)]
    controls = report["targeted_counterfactuals"]
    assert controls["failure_continue"]["start_with_available_credit_enters_continue"] is True
    assert controls["failure_continue"]["direction_only_confirms"] is False
    assert controls["input_counterfactuals"]["coin_only_no_respawn"] is True
    assert controls["input_counterfactuals"]["no_continue_no_respawn"] is True
    assert controls["route_wide_perturbation_difference"]["frame"] == 6692
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_continue(CONTINUE)
for label, path, value in (
        ("continue semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("invented active player",
         ("paired_capture_ceremony", "segment_semantics",
          "player_active_frames"), 1),
        ("missing credited route edge",
         ("route_authority_extension", "route_state_edges"), []),
        ("direction confirms", ("targeted_counterfactuals",
                                "failure_continue",
                                "direction_only_confirms"), True),
        ("orphan continue audio", ("coverage", "unowned_audio_events"), 1),
        ("continue physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(CONTINUE)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_continue(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Round 1 continue census mutation accepted: {label}")


def validate_warehouse(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [6693, 7438]
    assert report["segment"]["scene_ids"] == ["round1-warehouse-stalker"]
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 746
    assert semantics["canonical_semantic_sha256"] == \
        "00fdcda6ef8e9c8e02190fc6e5892951898570bffc07ae718ddd98ced61595e4"
    assert semantics["player_active_frames"] == 716
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x00", 12, 2), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 6),
                ("0x3d", 24, 20), ("0x49", 24, 12),
                ("0x4b", 24, 1), ("0x4e", 24, 4)]
    assert len(census["actor_lifetimes"]) == 48
    assert len(census["spawn_edges"]) == 44
    assert len(census["despawn_edges"]) == 44
    assert len(census["hit_ko_transitions"]) == 55
    assert census["audio"]["handler_transaction_count"] == 64
    assert len(census["audio"]["source_owned_trigger_groups_first_seen"]) == 10
    assert len(census["audio"]["player_origin_edges"]) == 3
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 5
    controls = report["targeted_counterfactuals"]
    assert controls["respawn_return"]["active_frame"] == 6723
    assert controls["respawn_return"]["return_to_control_frame"] == 6786
    assert len(controls["auxiliary_class_controls"]) == 6
    assert controls["auxiliary_zero_gap_coverage"]["orphan_dispatched_pairs"] == 0
    assert report["table_demand_delta"]["unbound_table_identities"] == []
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_warehouse(WAREHOUSE)
for label, path, value in (
        ("warehouse semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("warehouse player identity",
         ("paired_capture_ceremony", "segment_semantics",
          "identity_mismatch_frames"), [7000]),
        ("warehouse missing actor",
         ("scene_census_delta", "actor_lifetimes"), []),
        ("warehouse missing respawn",
         ("targeted_counterfactuals", "respawn_return", "active_frame"), 0),
        ("warehouse missing auxiliary controls",
         ("targeted_counterfactuals", "auxiliary_class_controls"), []),
        ("warehouse orphan actor", ("coverage", "unowned_actor_lifetimes"), 1),
        ("warehouse physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(WAREHOUSE)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_warehouse(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Warehouse census mutation accepted: {label}")


def validate_interwave(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [7439, 7503]
    assert len(report["segment"]["scene_ids"]) == 19
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 65
    assert semantics["canonical_semantic_sha256"] == \
        "f6c5cfa838a709a8538a0b763d953bdf71bc2c4d1ed8760c125163d399fad691"
    assert semantics["player_active_frames"] == 65
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 1)]
    assert len(census["actor_lifetimes"]) == 4
    assert len(census["spawn_edges"]) == 1
    assert len(census["despawn_edges"]) == 1
    assert len(census["hit_ko_transitions"]) == 1
    assert census["audio"]["handler_transaction_count"] == 3
    assert census["audio"]["command_counts"] == {
        "0x003e": 1, "0x010a": 1, "0x0200": 1}
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 19
    assert all(row["classification"] ==
               "SOURCE_CLOSED_PRESENTATION_DEPENDENCY" and
               row["owns_progression"] is False
               for row in controls["presentation_boundaries"])
    assert len(controls["enemy_class_controls"]) == 1
    assert len(controls["auxiliary_class_controls"]) == 2
    assert controls["navigation_route_wide"]["status"] == "PASS"
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_interwave(INTERWAVE)
for label, path, value in (
        ("interwave semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("interwave missing presentation boundaries",
         ("targeted_counterfactuals", "presentation_boundaries"), []),
        ("interwave presentation owns progression",
         ("targeted_counterfactuals", "presentation_boundaries", "0",
          "owns_progression"), True),
        ("interwave missing actor", ("scene_census_delta", "actor_lifetimes"), []),
        ("interwave orphan audio", ("coverage", "unowned_audio_events"), 1),
        ("interwave physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(INTERWAVE)
    target = mutant
    try:
        for key in path[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        target[path[-1]] = value
        validate_interwave(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Interwave census mutation accepted: {label}")


def validate_warehouse2(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [7504, 9004]
    assert report["segment"]["scene_ids"] == ["round1-warehouse-stalker-2"]
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 1501
    assert semantics["canonical_semantic_sha256"] == \
        "976ae53a62b2edc0ab7cb61572e4c01f2c8853b8177ab614bd840c849ced0221"
    assert semantics["player_active_frames"] == 1501
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x00", 12, 3), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 2),
                ("0x49", 24, 19), ("0x4e", 24, 1)]
    assert len(census["actor_lifetimes"]) == 28
    assert len(census["spawn_edges"]) == 25
    assert len(census["despawn_edges"]) == 23
    assert len(census["hit_ko_transitions"]) == 60
    assert census["audio"]["handler_transaction_count"] == 135
    assert len(census["audio"]["command_counts"]) == 27
    assert len(census["audio"]["source_owned_trigger_groups_first_seen"]) == 10
    assert len(census["audio"]["player_origin_edges"]) == 3
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 1
    assert controls["presentation_boundaries"][0]["owns_progression"] is False
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 4
    assert controls["navigation_route_wide"]["status"] == "PASS"
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_warehouse2(WAREHOUSE2)
for label, path, value in (
        ("warehouse2 semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("warehouse2 player identity",
         ("paired_capture_ceremony", "segment_semantics",
          "identity_mismatch_frames"), [8000]),
        ("warehouse2 missing spawn edges", ("scene_census_delta", "spawn_edges"), []),
        ("warehouse2 missing enemy controls",
         ("targeted_counterfactuals", "enemy_class_controls"), []),
        ("warehouse2 orphan lifecycle",
         ("coverage", "unmapped_spawn_despawn_edges"), 1),
        ("warehouse2 physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(WAREHOUSE2)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_warehouse2(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Warehouse 2 census mutation accepted: {label}")


def validate_interwave2(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [9005, 9039]
    assert len(report["segment"]["scene_ids"]) == 11
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 35
    assert semantics["canonical_semantic_sha256"] == \
        "8d59f0a7c1c334c3f9171203d001e3a8d4c1ce53cdca51386b1e4cb54b1dedc5"
    assert semantics["player_active_frames"] == 35
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x00", 12, 2),
                ("0x06", 12, 1), ("0x07", 20, 1)]
    assert len(census["actor_lifetimes"]) == 5
    assert census["spawn_edges"] == [] and census["despawn_edges"] == []
    assert census["hit_ko_transitions"] == []
    assert census["audio"]["handler_transaction_count"] == 1
    assert census["audio"]["command_counts"] == {"0x024e": 1}
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 11
    assert all(row["owns_progression"] is False
               for row in controls["presentation_boundaries"])
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 1
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_interwave2(INTERWAVE2)
for label, path, value in (
        ("interwave2 semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("interwave2 presentation owners",
         ("targeted_counterfactuals", "presentation_boundaries"), []),
        ("interwave2 missing actors", ("scene_census_delta", "actor_lifetimes"), []),
        ("interwave2 orphan audio", ("coverage", "unowned_audio_events"), 1),
        ("interwave2 physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(INTERWAVE2)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_interwave2(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Interwave 2 census mutation accepted: {label}")

print("ORACLE-10 Round 1 census extension 5567..9039: PASS "
      "(38 mutations rejected)")
