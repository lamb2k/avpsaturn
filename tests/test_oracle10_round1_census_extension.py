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
WAREHOUSE_GAMEPLAY2 = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_9040_9940.json")
    .read_text(encoding="ascii"))
CHRYSALIS_INTERWAVE = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_9941_9975.json")
    .read_text(encoding="ascii"))
CHRYSALIS = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_9976_11476.json")
    .read_text(encoding="ascii"))
STALKER3_INTERWAVE = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_11477_11541.json")
    .read_text(encoding="ascii"))
STALKER3 = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_11542_12442.json")
    .read_text(encoding="ascii"))
WAREHOUSE3_ENTRY = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_12443_12477.json")
    .read_text(encoding="ascii"))
WAREHOUSE3 = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_12478_12799.json")
    .read_text(encoding="ascii"))
CONTINUE2 = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_12800_13292.json")
    .read_text(encoding="ascii"))
CHRYSALIS2 = json.loads(
    (ROOT / "data/oracle10_round1_census_extension_13293_15039.json")
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


def validate_warehouse_gameplay2(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [9040, 9940]
    assert report["segment"]["scene_ids"] == ["round1-warehouse-gameplay-2"]
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 901
    assert semantics["canonical_semantic_sha256"] == \
        "c6a06d1bf0278d29374081b9e90c09fc343198d5873aa563c344b83d8919b4a3"
    assert semantics["player_active_frames"] == 901
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x00", 12, 2),
                ("0x06", 12, 1), ("0x07", 20, 1),
                ("0x3d", 24, 8)]
    assert len(census["actor_lifetimes"]) == 13
    assert len(census["spawn_edges"]) == 8
    assert len(census["despawn_edges"]) == 10
    assert len(census["hit_ko_transitions"]) == 29
    assert census["audio"]["handler_transaction_count"] == 73
    assert len(census["audio"]["command_counts"]) == 23
    assert len(census["audio"]["source_owned_trigger_groups_first_seen"]) == 2
    assert len(census["audio"]["player_origin_edges"]) == 3
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 3
    assert len(controls["presentation_boundaries"]) == 1
    assert controls["presentation_boundaries"][0]["owns_progression"] is False
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 2
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_warehouse_gameplay2(WAREHOUSE_GAMEPLAY2)
for label, path, value in (
        ("warehouse gameplay2 semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("warehouse gameplay2 identity",
         ("paired_capture_ceremony", "segment_semantics",
          "character_mismatch_frames"), [9500]),
        ("warehouse gameplay2 missing lifecycle",
         ("scene_census_delta", "spawn_edges"), []),
        ("warehouse gameplay2 missing controls",
         ("targeted_counterfactuals", "enemy_class_controls"), []),
        ("warehouse gameplay2 orphan camera",
         ("coverage", "unowned_route_camera_events"), 1),
        ("warehouse gameplay2 physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(WAREHOUSE_GAMEPLAY2)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_warehouse_gameplay2(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Warehouse gameplay 2 census mutation accepted: {label}")


def validate_chrysalis_interwave(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [9941, 9975]
    assert len(report["segment"]["scene_ids"]) == 11
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 35
    assert semantics["canonical_semantic_sha256"] == \
        "e7c513451b2a1eea9733a78cbfe9ac41bdc4c8e11068d33d39e207e1a1b56ccf"
    assert semantics["player_active_frames"] == 35
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x06", 12, 1), ("0x07", 20, 1)]
    assert len(census["actor_lifetimes"]) == 3
    assert census["spawn_edges"] == [] and census["despawn_edges"] == []
    assert census["hit_ko_transitions"] == []
    assert census["audio"]["handler_transaction_count"] == 3
    assert census["audio"]["command_counts"] == {
        "0x003e": 1, "0x0113": 1, "0x0203": 1}
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 11
    assert all(row["owns_progression"] is False
               for row in controls["presentation_boundaries"])
    assert len(controls["enemy_class_controls"]) == 1
    assert len(controls["auxiliary_class_controls"]) == 1
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_chrysalis_interwave(CHRYSALIS_INTERWAVE)
for label, path, value in (
        ("chrysalis interwave semantic",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("chrysalis interwave presentation",
         ("targeted_counterfactuals", "presentation_boundaries"), []),
        ("chrysalis interwave actors", ("scene_census_delta", "actor_lifetimes"), []),
        ("chrysalis interwave orphan audio", ("coverage", "unowned_audio_events"), 1),
        ("chrysalis interwave physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(CHRYSALIS_INTERWAVE)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_chrysalis_interwave(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Chrysalis interwave mutation accepted: {label}")


def validate_chrysalis(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [9976, 11476]
    assert report["segment"]["scene_ids"] == ["round1-chrysalis-battle"]
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 1501
    assert semantics["canonical_semantic_sha256"] == \
        "4bb1aea23c6f0a54ba47b8fd1c0f8ba61e4cbaa81293dc1c0b579e5cd851d51e"
    assert semantics["player_active_frames"] == 1501
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x01", 12, 2), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 5),
                ("0x3d", 24, 22), ("0x49", 24, 29),
                ("0x4e", 24, 1)]
    assert len(census["actor_lifetimes"]) == 62
    assert len(census["spawn_edges"]) == 59
    assert len(census["despawn_edges"]) == 57
    assert len(census["hit_ko_transitions"]) == 34
    assert census["audio"]["handler_transaction_count"] == 130
    assert len(census["audio"]["command_counts"]) == 23
    assert len(census["audio"]["source_owned_trigger_groups_first_seen"]) == 2
    assert len(census["audio"]["player_origin_edges"]) == 3
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 1
    assert controls["presentation_boundaries"][0]["owns_progression"] is False
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 5
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_chrysalis(CHRYSALIS)
for label, path, value in (
        ("chrysalis semantic identity",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("chrysalis player identity",
         ("paired_capture_ceremony", "segment_semantics",
          "identity_mismatch_frames"), [11000]),
        ("chrysalis missing lifecycle", ("scene_census_delta", "spawn_edges"), []),
        ("chrysalis missing class controls",
         ("targeted_counterfactuals", "enemy_class_controls"), []),
        ("chrysalis orphan actor", ("coverage", "unowned_actor_lifetimes"), 1),
        ("chrysalis physical claim", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(CHRYSALIS)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_chrysalis(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Chrysalis census mutation accepted: {label}")


def validate_stalker3_interwave(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [11477, 11541]
    assert len(report["segment"]["scene_ids"]) == 19
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 65
    assert semantics["canonical_semantic_sha256"] == \
        "423e70ebb77bdd6f1f95aa67aae69b51b6bbfb7001a8fc8f945c37f2e9ecd921"
    assert semantics["player_active_frames"] == 65
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x01", 12, 2), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 2)]
    assert len(census["actor_lifetimes"]) == 7
    assert len(census["spawn_edges"]) == 2
    assert len(census["despawn_edges"]) == 1
    assert len(census["hit_ko_transitions"]) == 2
    assert census["audio"]["handler_transaction_count"] == 4
    assert census["audio"]["command_counts"] == {
        "0x003e": 1, "0x0109": 1, "0x024e": 2}
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 19
    assert all(row["owns_progression"] is False
               for row in controls["presentation_boundaries"])
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 2
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_stalker3_interwave(STALKER3_INTERWAVE)
for label, path, value in (
        ("stalker3 interwave semantic",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("stalker3 interwave presentation",
         ("targeted_counterfactuals", "presentation_boundaries"), []),
        ("stalker3 interwave lifecycle", ("scene_census_delta", "spawn_edges"), []),
        ("stalker3 interwave orphan", ("coverage", "unowned_actor_lifetimes"), 1),
        ("stalker3 interwave physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(STALKER3_INTERWAVE)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_stalker3_interwave(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Stalker 3 interwave mutation accepted: {label}")


def validate_stalker3(report: dict[str, object]) -> None:
    ceremony = report["paired_capture_ceremony"]
    semantics = ceremony["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [11542, 12442]
    assert report["segment"]["scene_ids"] == ["round1-warehouse-stalker-3"]
    assert ceremony["raw_capture_files_byte_identical"] is True
    assert ceremony["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 901
    assert semantics["canonical_semantic_sha256"] == \
        "c56ec8e416d2c39050e24c6040e3d7532e5e0b4d5b54a13c34f63f8eb21e4152"
    assert semantics["player_active_frames"] == 901
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert semantics["per_frame_character_identity_gate"] is True
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x01", 12, 2), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 11), ("0x49", 24, 12)]
    assert len(census["actor_lifetimes"]) == 28
    assert len(census["spawn_edges"]) == 22
    assert len(census["despawn_edges"]) == 23
    assert len(census["hit_ko_transitions"]) == 27
    assert census["audio"]["handler_transaction_count"] == 71
    assert len(census["audio"]["command_counts"]) == 23
    assert len(census["audio"]["source_owned_trigger_groups_first_seen"]) == 2
    assert len(census["audio"]["player_origin_edges"]) == 5
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 1
    assert controls["presentation_boundaries"][0]["owns_progression"] is False
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 3
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_stalker3(STALKER3)
for label, path, value in (
        ("stalker3 semantic", ("paired_capture_ceremony", "segment_semantics",
                               "canonical_semantic_sha256"), "0" * 64),
        ("stalker3 identity", ("paired_capture_ceremony", "segment_semantics",
                               "identity_mismatch_frames"), [12000]),
        ("stalker3 lifecycle", ("scene_census_delta", "spawn_edges"), []),
        ("stalker3 orphan", ("coverage", "unmapped_spawn_despawn_edges"), 1),
        ("stalker3 physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(STALKER3)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_stalker3(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Stalker 3 census mutation accepted: {label}")


def validate_warehouse3_entry(report: dict[str, object]) -> None:
    semantics = report["paired_capture_ceremony"]["segment_semantics"]
    census = report["scene_census_delta"]
    controls = report["targeted_counterfactuals"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [12443, 12477]
    assert len(report["segment"]["scene_ids"]) == 11
    assert report["paired_capture_ceremony"]["raw_capture_files_byte_identical"] is True
    assert report["paired_capture_ceremony"]["paired_route_ledgers_byte_identical"] is True
    assert semantics["frame_count"] == 35
    assert semantics["canonical_semantic_sha256"] == \
        "fec4caf85e842696db67bce8daf82fed479d39c4ac18a9aae53edb14cc1f9ce6"
    assert semantics["player_active_frames"] == 35
    assert semantics["character_mismatch_frames"] == []
    assert semantics["identity_mismatch_frames"] == []
    assert [(row["class"], row["type"], row["instance_count"])
            for row in census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x01", 12, 1), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 2)]
    assert len(census["actor_lifetimes"]) == 6
    assert len(census["spawn_edges"]) == 1
    assert len(census["despawn_edges"]) == 1
    assert census["hit_ko_transitions"] == []
    assert census["audio"]["handler_transaction_count"] == 0
    assert census["load_release_boundaries"] == []
    assert report["route_authority_extension"]["route_state_edges"] == []
    assert len(report["route_authority_extension"]["camera_lock_runs"]) == 1
    assert len(controls["presentation_boundaries"]) == 11
    assert all(row["owns_progression"] is False
               for row in controls["presentation_boundaries"])
    assert len(controls["enemy_class_controls"]) == 2
    assert len(controls["auxiliary_class_controls"]) == 2
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_warehouse3_entry(WAREHOUSE3_ENTRY)
for label, path, value in (
        ("warehouse3 entry semantic",
         ("paired_capture_ceremony", "segment_semantics",
          "canonical_semantic_sha256"), "0" * 64),
        ("warehouse3 entry identity",
         ("paired_capture_ceremony", "segment_semantics",
          "identity_mismatch_frames"), [12460]),
        ("warehouse3 entry presentation",
         ("targeted_counterfactuals", "presentation_boundaries"), []),
        ("warehouse3 entry orphan", ("coverage", "unowned_actor_lifetimes"), 1),
        ("warehouse3 entry physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(WAREHOUSE3_ENTRY)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_warehouse3_entry(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Warehouse gameplay 3 entry mutation accepted: {label}")


def validate_warehouse3(report: dict[str, object]) -> None:
    semantics = report["paired_capture_ceremony"]["segment_semantics"]
    census = report["scene_census_delta"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [12478, 12799]
    assert semantics["frame_count"] == 322
    assert semantics["canonical_semantic_sha256"] == \
        "655519331dc74eff591584b216bd586acb32799d7a1240304b2a05bb86c416bf"
    assert semantics["player_active_frames"] == 320
    assert semantics["identity_mismatch_frames"] == []
    assert len(census["actor_lifetimes"]) == 10
    assert len(census["spawn_edges"]) == 5
    assert len(census["despawn_edges"]) == 7
    assert len(census["hit_ko_transitions"]) == 3
    assert census["audio"]["handler_transaction_count"] == 14
    assert [(row["sample_transition_frame"], row["value"], row["writer_pc"])
            for row in report["route_authority_extension"]["route_state_edges"]] == [
                (12798, 0, "0x008546"), (12799, 2, "0x008bb2")]
    assert [row["id"] for row in census["load_release_boundaries"]] == [
        "route-load-release-12799"]
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_warehouse3(WAREHOUSE3)
for label, path, value in (
        ("warehouse3 semantic", ("paired_capture_ceremony", "segment_semantics",
                                 "canonical_semantic_sha256"), "0" * 64),
        ("warehouse3 route", ("route_authority_extension", "route_state_edges"), []),
        ("warehouse3 load", ("scene_census_delta", "load_release_boundaries"), []),
        ("warehouse3 orphan", ("coverage", "unowned_load_release_events"), 1),
        ("warehouse3 physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(WAREHOUSE3)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_warehouse3(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Warehouse gameplay 3 mutation accepted: {label}")

def validate_continue2(report: dict[str, object]) -> None:
    semantics = report["paired_capture_ceremony"]["segment_semantics"]
    census = report["scene_census_delta"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [12800, 13292]
    assert report["segment"]["scene_ids"] == ["continue-countdown-2"]
    assert semantics["frame_count"] == 493
    assert semantics["canonical_semantic_sha256"] == \
        "ff82b9cdf5081ff8def9d4168ce80809e9013009cff9fa47d2c65441d36947fa"
    assert semantics["player_active_frames"] == 0
    assert semantics["identity_mismatch_frames"] == []
    assert [(row["class"], row["type"]) for row in
            census["class_type_inventory"]] == [
                ("0x01", 12), ("0x06", 12), ("0x07", 20)]
    assert len(census["actor_lifetimes"]) == 3
    assert census["spawn_edges"] == [] and census["despawn_edges"] == []
    assert census["hit_ko_transitions"] == []
    assert census["audio"]["command_counts"] == {"0x000f": 1, "0x0202": 1}
    assert census["audio"]["handler_transaction_count"] == 2
    assert census["load_release_boundaries"] == []
    edges = report["route_authority_extension"]["route_state_edges"]
    assert [(row["sample_transition_frame"], row["write_frame"],
             row["writer_pc"], row["value"]) for row in edges] == [
                 (13292, 13291, "0x0090f2", 4)]
    assert report["targeted_counterfactuals"]["presentation_boundaries"] == [{
        "classification": "SOURCE_CLOSED_PRESENTATION_DEPENDENCY",
        "owns_progression": False,
        "signature": "S0236cab182f2-1",
    }]
    assert all(value == 0 for value in report["coverage"].values())
    assert report["physical_saturn"] == "UNRUN"


validate_continue2(CONTINUE2)
for label, path, value in (
        ("continue2 semantic", ("paired_capture_ceremony", "segment_semantics",
                                "canonical_semantic_sha256"), "0" * 64),
        ("continue2 active player", ("paired_capture_ceremony", "segment_semantics",
                                     "player_active_frames"), 1),
        ("continue2 route", ("route_authority_extension", "route_state_edges"), []),
        ("continue2 audio", ("scene_census_delta", "audio",
                             "handler_transaction_count"), 1),
        ("continue2 presentation progression", ("targeted_counterfactuals",
                                                 "presentation_boundaries"), []),
        ("continue2 orphan", ("coverage", "unowned_route_camera_events"), 1),
        ("continue2 physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(CONTINUE2)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_continue2(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Round 1 continue-2 mutation accepted: {label}")

def validate_chrysalis2(report: dict[str, object]) -> None:
    semantics = report["paired_capture_ceremony"]["segment_semantics"]
    census = report["scene_census_delta"]
    assert report["status"] == "CENSUS_SEGMENT_COMPLETE"
    assert report["segment"]["source_frame_range"] == [13293, 15039]
    assert report["segment"]["scene_ids"] == ["round1-chrysalis-battle-2"]
    assert semantics["frame_count"] == 1747
    assert semantics["canonical_semantic_sha256"] == \
        "2ea02ee902a115824dccdd918b71076b15cb548213635b5c497da875750990f7"
    assert semantics["player_active_frames"] == 1747
    assert semantics["identity_mismatch_frames"] == []
    assert [(row["class"], row["type"], row["instance_count"]) for row in
            census["class_type_inventory"]] == [
                ("0x00", 0, 1), ("0x01", 12, 1), ("0x06", 12, 1),
                ("0x07", 20, 1), ("0x10", 24, 4), ("0x3d", 24, 39),
                ("0x49", 24, 14), ("0x4b", 24, 1), ("0x4e", 24, 1)]
    assert len(census["actor_lifetimes"]) == 63
    assert len(census["spawn_edges"]) == 60
    assert len(census["despawn_edges"]) == 60
    assert len(census["hit_ko_transitions"]) == 18
    assert census["audio"]["handler_transaction_count"] == 96
    assert len(census["audio"]["command_counts"]) == 30
    assert census["audio"]["orphan_handler_transactions"] == 0
    assert census["audio"]["orphan_trigger_groups"] == 0
    assert census["load_release_boundaries"] == []
    edges = report["route_authority_extension"]["route_state_edges"]
    assert [(row["sample_transition_frame"], row["write_frame"],
             row["writer_pc"], row["value"]) for row in edges] == [
                 (15019, 15018, "0x008418", 6),
                 (15021, 15020, "0x00c886", 0)]
    assert all(value == 0 for value in report["coverage"].values())
    assert report["table_demand_delta"]["unbound_table_identities"] == []
    assert report["physical_saturn"] == "UNRUN"


validate_chrysalis2(CHRYSALIS2)
for label, path, value in (
        ("chrysalis2 semantic", ("paired_capture_ceremony", "segment_semantics",
                                 "canonical_semantic_sha256"), "0" * 64),
        ("chrysalis2 identity", ("paired_capture_ceremony", "segment_semantics",
                                 "identity_mismatch_frames"), [14000]),
        ("chrysalis2 lifecycle", ("scene_census_delta", "spawn_edges"), []),
        ("chrysalis2 route", ("route_authority_extension", "route_state_edges"), []),
        ("chrysalis2 audio", ("scene_census_delta", "audio",
                              "orphan_trigger_groups"), 1),
        ("chrysalis2 table", ("table_demand_delta", "unbound_table_identities"),
                              ["0xdeadbe"]),
        ("chrysalis2 physical", ("physical_saturn",), "PASS")):
    mutant = copy.deepcopy(CHRYSALIS2)
    target = mutant
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    try:
        validate_chrysalis2(mutant)
    except AssertionError:
        continue
    raise AssertionError(f"Round 1 Chrysalis-2 mutation accepted: {label}")

print("ORACLE-10 Round 1 census extension 5567..15039: PASS "
      "(89 mutations rejected)")
