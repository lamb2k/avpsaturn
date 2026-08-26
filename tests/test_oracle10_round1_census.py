#!/usr/bin/env python3
"""ORACLE-10 tracked census, route identity, and mutation controls."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT / "data" / "oracle10_round1_route.json"
COVERAGE_PATH = ROOT / "data" / "round1_system_coverage.yaml"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CLASSIFICATIONS = {
    "SOURCE_CLOSED", "PARTIAL", "OBSERVED", "ADAPTED", "UNKNOWN",
    "NOT_REQUIRED_FOR_ROUND1",
}
REQUIRED_AUTHORITIES = {
    "predator-warrior-player-authority",
    "round1-navigation-terrain-camera",
    "actor-scheduler-allocation-lifecycle",
    "round1-enemy-archetypes",
    "pickups-equipment-weapons-projectiles-hazards-destructibles",
    "encounters-waves-scripted-triggers",
    "round1-boss",
    "stage-clear-failure-continue-round2-handoff",
    "gameplay-audio-load-release",
    "rng-consumption",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate(route: dict, coverage: dict) -> None:
    require(route["schema"] == "oracle10-round1-route-v1",
            "route schema drifted")
    require(route["status"] == "ACCEPTED", "ORACLE-10 is not accepted")
    controls = route["control_captures"]
    require(controls["independently_launched"] is True and
            controls["byte_identical"] is True,
            "control captures are not independent and byte-identical")
    for capture in (controls["capture_a"], controls["capture_b"]):
        require(capture["screenshot_count"] == 18000,
                "control capture is not cadence-1 through frame 18000")
        require(SHA256.fullmatch(capture["screenshot_hash_stream_sha256"]),
                "control screenshot identity is invalid")
        for metadata in capture["files"].values():
            require(metadata["bytes"] > 0 and SHA256.fullmatch(metadata["sha256"]),
                    "control raw identity metadata is invalid")

    perturb = route["route_wide_perturbation"]
    require(perturb["status"] == "PASS" and
            perturb["first_input_difference"] and
            perturb["stable_round2_handoff_frame"] == 16425,
            "completing route-wide perturbation drifted")
    require(route["failure_continue_path"]["status"] == "OBSERVED" and
            route["failure_continue_path"]["completion_after_continue"] is True and
            len(route["failure_continue_path"]["continue_scene_ranges"]) >= 1,
            "bounded failure/continue evidence is missing")

    gate = route["completion_gate"]
    require(set(gate.values()) == {"PASS", 0},
            "ORACLE-10 completion gate is not fully passed/read-only")
    counterfactuals = route["targeted_counterfactuals"]
    require(len(counterfactuals) == 13,
            "counterfactual matrix count drifted")
    for name, result in counterfactuals.items():
        require(result["status"] == "PASS" and result["detected"] is True and
                result["semantic_difference"] is not None,
                f"{name} is not a detected semantic counterfactual")
        for artifact in ("samples_sha256", "actor_events_sha256"):
            require(SHA256.fullmatch(result[artifact]),
                    f"{name} {artifact} is invalid")
    require(counterfactuals["no_continue"]["completed_round1"] is False,
            "no-continue negative control unexpectedly completed")
    require(counterfactuals["remove_class_06"]["completed_round1"] is False,
            "boss removal produced an unsourced clear")

    authority_ids = {
        row["authority_family"]
        for row in route["counterfactual_authority_coverage"]
    }
    require(authority_ids == REQUIRED_AUTHORITIES,
            "authority counterfactual coverage is incomplete")
    require(all(row["status"] == "PASS" and row["variants"]
                for row in route["counterfactual_authority_coverage"]),
            "authority counterfactual family lacks a passing variant")

    required_body_fields = {
        "source_frame_range", "actor_slots_and_classes",
        "responsible_source_routine_or_table", "fields_read", "fields_written",
        "state_transitions", "rng_consumption", "update_scheduler_order",
        "animation_and_assembly_identities", "collision_selectors",
        "presentation_dependency", "source_closure_status",
        "exact_next_experiment",
    }
    require(len(route["segments"]) == 94,
            "complete route scene/body census drifted")
    for segment in route["segments"]:
        require(required_body_fields <= set(segment),
                f"route segment {segment['id']} is incomplete")
        require(segment["source_closure_status"] in CLASSIFICATIONS,
                f"route segment {segment['id']} classification drifted")
    require(len(route["actor_archetypes"]) == 20,
            "actor class/type census drifted")
    for actor in route["actor_archetypes"]:
        require(required_body_fields <= set(actor),
                f"actor body {actor['id']} is incomplete")
        require(actor["source_closure_status"] in CLASSIFICATIONS,
                f"actor body {actor['id']} classification drifted")
    known = {(row["class"], row["type"]): row
             for row in route["actor_archetypes"]}
    require(known[("0x1f", 12)]["semantic_identity"] == "street-alien" and
            known[("0x1f", 12)]["source_closure_status"] == "SOURCE_CLOSED",
            "accepted class-0x1F binding drifted")
    require(known[("0x00", 12)]["semantic_identity"] == "stalker" and
            known[("0x06", 12)]["semantic_identity"] == "chrysalis-boss",
            "required Round 1 enemy identities drifted")
    require(len(route["source_route_events"]) >= 20 and
            route["source_route_events"][-1]["id"] == "round_2_boundary",
            "source route event census does not reach Round 2")
    require(len(route["player_action_families"]) == 6,
            "player action-family census is incomplete")
    require(route["baseline_writer_bindings"]["route"]["unique_pcs"] and
            route["baseline_writer_bindings"]["qsound"]["unique_pcs"],
            "route/audio writer bindings are absent")

    require(coverage["schema"] == "round1-system-coverage-v1" and
            coverage["status"] == "ACCEPTED" and
            coverage["oracle10_exit"] == "PASS",
            "coverage ledger is not accepted")
    require(set(coverage["classification_vocabulary"]) == CLASSIFICATIONS,
            "coverage classification vocabulary drifted")
    spec02_eligible = coverage.get("spec02_closure_gate", {}).get(
        "spec02_eligible", False)
    spec02_path = ROOT / "data/spec02_round1_executable_contract.json"
    spec02_accepted = (spec02_path.exists() and
                       json.loads(spec02_path.read_text())["status"] == "ACCEPTED")
    expected_next = ("REIMPLEMENT-13-SOURCE-CLOSED-ROUND1" if spec02_accepted
                     else "SPEC-02-ROUND1-EXECUTABLE-CONTRACT" if spec02_eligible
                     else "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE")
    require(coverage["pending_oracle10_controls"] == [] and
            coverage["next_card"] == expected_next,
            "accepted census did not route through the current zero-gap gate")
    require(coverage["production_runtime_writes"] == 0 and
            coverage["frontend_active"] is False and
            coverage["user09_status"] == "CHANGES_REQUESTED" and
            coverage["physical_saturn"] == "UNRUN",
            "ORACLE-10 crossed a protected boundary")


def main() -> None:
    route = json.loads(ROUTE_PATH.read_text())
    coverage = json.loads(COVERAGE_PATH.read_text())
    validate(route, coverage)

    mutations = []
    mutated = copy.deepcopy(route)
    mutated["control_captures"]["byte_identical"] = False
    mutations.append((mutated, copy.deepcopy(coverage)))
    mutated = copy.deepcopy(route)
    mutated["route_wide_perturbation"]["stable_round2_handoff_frame"] = None
    mutations.append((mutated, copy.deepcopy(coverage)))
    mutated = copy.deepcopy(route)
    mutated["targeted_counterfactuals"]["remove_class_06"]["completed_round1"] = True
    mutations.append((mutated, copy.deepcopy(coverage)))
    mutated = copy.deepcopy(route)
    del mutated["actor_archetypes"][0]["fields_written"]
    mutations.append((mutated, copy.deepcopy(coverage)))
    mutated = copy.deepcopy(route)
    mutated["counterfactual_authority_coverage"][0]["status"] = "FAIL"
    mutations.append((mutated, copy.deepcopy(coverage)))
    mutated_coverage = copy.deepcopy(coverage)
    mutated_coverage["production_runtime_writes"] = 1
    mutations.append((copy.deepcopy(route), mutated_coverage))
    mutated_coverage = copy.deepcopy(coverage)
    mutated_coverage["next_card"] = "SPEC-02-ROUND1-EXECUTABLE-CONTRACT"
    mutations.append((copy.deepcopy(route), mutated_coverage))

    for index, (mutated_route, mutated_coverage) in enumerate(mutations):
        try:
            validate(mutated_route, mutated_coverage)
        except AssertionError:
            continue
        raise AssertionError(f"mutation {index} escaped ORACLE-10 validation")

    print("ORACLE-10 Round 1 system census and controls: PASS")


if __name__ == "__main__":
    main()
