#!/usr/bin/env python3
"""Mutation controls for the Round 1 navigation closure checkpoint."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_round1_navigation.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_navigation", ROOT / "tools" /
    "analyze_oracle11_round1_navigation.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted navigation mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "navigation family reopened")

mutant = copy.deepcopy(report)
mutant["capture_identity"]["byte_identical"] = False
reject(mutant, "non-deterministic baselines admitted")

mutant = copy.deepcopy(report)
mutant["capture_identity"]["perturbation_discriminated_navigation"] = False
reject(mutant, "non-discriminating perturbation admitted")

mutant = copy.deepcopy(report)
mutant["global_bounds"]["source_routine"] = "guessed rectangle"
reject(mutant, "rectangular fallback substituted for source bounds")

mutant = copy.deepcopy(report)
del mutant["global_bounds"]["writer_pcs"]["0x01b030"]
reject(mutant, "right clamp writer orphaned")

mutant = copy.deepcopy(report)
mutant["terrain_resolver"]["records"].pop()
reject(mutant, "route terrain record dropped")

mutant = copy.deepcopy(report)
mutant["terrain_resolver"]["records"][0]["source_program_match"] = False
reject(mutant, "captured terrain record detached from source data")

mutant = copy.deepcopy(report)
response = next(item for item in mutant["terrain_resolver"]["records"]
                if item["address"] == "0x0b20d6")
response["perturbed_calls"]["0x0b1c68"] = 0
reject(mutant, "discriminating terrain response removed")

mutant = copy.deepcopy(report)
mutant["navigation_bodies"]["instances"].pop()
reject(mutant, "navigation class/type body orphaned")

mutant = copy.deepcopy(report)
mutant["navigation_bodies"]["instances"][0]["complete_actor_authority"] = \
    "SOURCE_CLOSED"
reject(mutant, "destruction/presentation authority silently absorbed")

mutant = copy.deepcopy(report)
mutant["navigation_bodies"]["instances"][0]["source_block_sha256"] = "0" * 64
reject(mutant, "type-20 source routine detached")

mutant = copy.deepcopy(report)
mutant["camera"]["primary_writer"] = "fixed frame"
reject(mutant, "fixed-frame camera substitute admitted")

mutant = copy.deepcopy(report)
mutant["camera"]["camera_lock_and_unlock_runs"].pop()
reject(mutant, "camera edge orphaned")

mutant = copy.deepcopy(report)
mutant["closure"]["guessed_camera_guards"] = 1
reject(mutant, "guessed camera guard hidden")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["spec02_active"] = True
reject(mutant, "SPEC-02 activated")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["implementation_contract"]["obstacle_box"]["x_half_u8"] = 16
reject(mutant, "wrong Coffee Shop obstacle box admitted")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["implementation_contract"]["minimum_penetration"]["axis_guard"] = \
    "always resolve x"
reject(mutant, "minimum-penetration axis branch replaced")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["source_scene_record"]["camera_threshold_u16"] = 689
reject(mutant, "Coffee Shop obstacle spawn threshold changed")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["spawn"]["camera_sample_order"]["native_rule"] = "scheduler guard uses camera_x_position"
reject(mutant, "Coffee Shop obstacle scheduler camera sample changed")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["initializer"]["child_allocation"]["variant_order_u8"] = [0, 1, 2, 3]
reject(mutant, "Coffee Shop obstacle child allocation order changed")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["state_program"]["state_0404"]["completion_guard"] = "fixed frame"
reject(mutant, "Coffee Shop obstacle completion guard replaced")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["transition_suppression"]["suppressed_writes"] = 0
reject(mutant, "Coffee Shop obstacle suppression control removed")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["child_presentation"]["dispatch_table"]["offsets_u16"][1] = 50
reject(mutant, "Coffee Shop obstacle child dispatch changed")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["child_presentation"]["state_program"]["state_0200"]["guard"] = "fixed frame"
reject(mutant, "Coffee Shop obstacle child parent-state guard replaced")

mutant = copy.deepcopy(report)
mutant["obstacle_response"]["lifecycle_contract"]["state_program"]["state_0200"]["player_trigger"]["edge_to_damage_ticks_u8"] = 13
reject(mutant, "Coffee Shop obstacle special contact timing changed")

mutant = copy.deepcopy(report)
record = next(item for item in mutant["terrain_resolver"]["records"]
              if item["address"] == "0x0b218e")
record["decoded_six_fields"]["z_parameter_s8"] = -8
reject(mutant, "terrain record sign changed")

mutant = copy.deepcopy(report)
mutant["terrain_resolver"]["implementation_contract"]["six_fields"][4]["type"] = "u8"
reject(mutant, "kind-dependent terrain field signedness removed")

mutant = copy.deepcopy(report)
mutant["terrain_resolver"]["implementation_contract"]["selection"]["bounded_packed_grid"]["packed_bytes_hex"] = "00" * 104
reject(mutant, "bounded source-derived terrain grid changed")

mutant = copy.deepcopy(report)
mutant["camera"]["implementation_contract"]["x_target_arithmetic"]["narrow_right_delta"] = \
    "max_x-x_target-0x00c0"
reject(mutant, "wrong camera target arithmetic admitted")

mutant = copy.deepcopy(report)
mutant["camera"]["implementation_contract"]["coffee_shop_guard"]["phase2_unlock_guard"] = \
    "frame >= 4992"
reject(mutant, "fixed-frame Coffee Shop unlock admitted")

mutant = copy.deepcopy(report)
mutant["camera"]["implementation_contract"]["world_to_plane_order"]["raw_pattern_name_offset_forbidden"] = False
reject(mutant, "raw camera coordinate submitted as plane offset")

mutant = copy.deepcopy(report)
mutant["camera"]["implementation_contract"]["initialization"][
    "first_control_chronology"][1]["camera_x_s16"] = 640
reject(mutant, "camera first-control handoff update")

print("ORACLE-11 Round 1 navigation tests: PASS (32 mutations rejected)")
