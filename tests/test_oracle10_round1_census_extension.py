#!/usr/bin/env python3
"""Validate the first post-Coffee-Shop paired census segment and mutations."""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = json.loads((ROOT / "data/oracle10_round1_census_extension_5567_6200.json")
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

print("ORACLE-10 Round 1 census extension 5567..6200: PASS "
      "(8 mutations rejected)")
