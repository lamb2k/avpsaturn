#!/usr/bin/env python3
"""Validate slice rendering against the independent MAME source contract."""

from __future__ import annotations


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_trace(trace: dict, source_contract: dict) -> dict:
    """Check provenance and the causal contact binding without candidate pins."""
    require(trace.get("fidelity") == "SOURCE_BOUND_WITH_ADAPTED_INPUT",
            "slice fidelity label drifted")
    require(trace.get("source_contract", {}).get("origin") ==
            "MAME_SOURCE_ONLY",
            "slice trace is not bound to independent MAME evidence")
    require(source_contract.get("classification") ==
            "MEASURED MAME source contract" and
            source_contract.get("source", {}).get("byte_identical_reruns") is
            True,
            "independent source contract provenance drifted")
    contacts = [sample for sample in trace["samples"]
                if sample["slice_collision_result"]]
    require([sample["slice_source_sample"] for sample in contacts] ==
            [event["contact_frame"] for event in source_contract["events"]],
            "contact samples are detached from the source events")
    require([sample["slice_attack_selector"] for sample in contacts] ==
            [event["attack_selector"] for event in source_contract["events"]],
            "rendered attack selectors are detached from source collision")
    require([sample["slice_player_animation_record"] for sample in contacts] ==
            [int(event["player"]["animation_record"], 16)
             for event in source_contract["events"]],
            "rendered player records are detached from source collision")
    require(all(sample["slice_asset_failures"] == 0 and
                sample["slice_player_object_identity"] != 0 and
                sample["slice_player_tile_identity"] != 0 and
                sample["slice_enemy_object_identity"] != 0 and
                sample["slice_enemy_tile_identity"] != 0
                for sample in trace["samples"]),
            "a source-emitted identity or palette comparison failed")
    source_window = [sample for sample in trace["samples"]
                     if 583 <= sample["slice_frame"] <= 879]
    require(source_window and all(
                sample["slice_enemy_palette_bank"] == 19
                for sample in source_window),
            "source-window alien palette drifted")
    return {
        "result": "PASS",
        "source": "data/avsp_source_combat_presentation_contract.json",
        "origin": "MAME_SOURCE_ONLY",
        "contacts": [sample["slice_frame"] for sample in contacts],
    }
