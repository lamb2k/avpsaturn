#!/usr/bin/env python3
"""Committed controls for the corrected Predator Warrior Button1 contract."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/oracle11_predator_weapon_projectile_resource.json"


def validate(data):
    assert data["schema"] == 2 and data["status"] == "SOURCE_CLOSED"
    assert data["determinism"] == {
        "byte_identical": True,
        "identical_files": [
            "samples.tsv", "writes.tsv", "actors.tsv", "qsound.tsv",
            "damage.tsv", "impact_audio.tsv", "objects.tsv",
            "character_samples.tsv",
        ],
        "independent_cold_runs": 2,
    }
    identity = data["character_identity"]
    assert identity["required_character_u8"] == 0
    assert identity["required_character"] == "predator_warrior"
    assert identity["rejected_character_u8"] == 1
    assert identity["rejected_character"] == "major_schaefer"
    assert identity["captured_field"] == "player +0xd2 u8"
    assert identity["per_frame_asserted"] is True
    assert identity["normalized_object_stream_asserted"] is True
    assert identity["required_probe"]["character"] == "0"
    assert identity["required_probe"]["animation"] == "0015e560"
    assert identity["required_probe"]["assembly"] == "00161a0a"
    assert identity["rejected_probe"]["character"] == "1"
    assert identity["required_object_stream"]["sha256"] != \
        identity["rejected_object_stream"]["sha256"]
    assert identity["required_object_stream"]["row_count"] > 400

    separation = data["authority_separation"]
    assert separation["projectile_lifecycle"] == {
        "children": "five record type 4 class 4 actors at six-frame cadence",
        "forbidden_rejected_path": "record type 4 class 5 and type-24 class 0x3a belong to Major Schaefer's rejected capture",
        "parent": "record type 4 class 0",
    }
    assert separation["resource"].startswith("one 40-unit debit")
    resource = data["resource_causal_trace"]
    assert resource["sufficient"] == {
        "child_count": 5, "debit": 40, "dispatch_frame": 4422,
        "parent_allocation_count": 1, "resource_after_entry": 24,
        "resource_start": 64,
    }
    assert resource["allocation_unavailable"]["parent_allocation_count"] == 0
    assert resource["allocation_unavailable"]["resource_after_entry"] == 24

    contract = data["implementation_contract"]
    assert contract["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert contract["source_input"]["button1_mask"] == "0x0010"
    action = contract["sufficient_action"]
    assert action["cleanup_tick"] == 19 and action["return_tick"] == 20
    assert action["resource_capacity_u8"] == 64
    assert action["resource_debit_u8"] == 40
    assert action["recharge_countdown_after_entry_u8"] == 12
    assert action["player_position_and_facing_latched"] is True
    assert action["rng_calls"] == []
    timeline = action["presentation_timeline"]
    assert len(timeline) == 20
    assert [timeline[index]["animation_record"] for index in range(8)] == [
        "0x0015f1f4", "0x0015e540", "0x0015e540", "0x0015e540",
        "0x0015e550", "0x0015e560", "0x0015e560", "0x0015e570",
    ]
    assert timeline[-2]["animation_record"] == "0x0015e580"
    assert timeline[-1]["animation_record"] == "0x0015f1f4"
    assert timeline[5]["assembly"] == "0x00161a0a"

    parent = contract["record4_parent_class0"]
    assert parent["spec_executable"] is True
    assert parent["record_type_u8"] == 4 and parent["class_u8"] == 0
    assert parent["dispatch"] == "0x02f870"
    assert parent["state_sequence_u8"] == [0, 2, 4, 6]
    assert parent["allocation_writes"]["angle_u8"] == "copy player +0x8a"
    init = parent["initialization"]
    assert init["motion_table_u32"] == "0x001fb7c0"
    assert init["collision_table_u32"] == "0x0002fc3c"
    assert init["object_or_u16"] == "0x8000"
    assert len(init["presentation_records"]) == 7
    active = parent["active_state"]
    assert active["angle_u8_route_values"] == {
        "cold_run_1": [17], "facing_reversed": [47],
        "target_inside": [35], "target_outside": [35],
    }
    assert len(active["low_nibble_motion_pointer_u32"]) == 16
    assert len(active["high_nibble_motion_pointer_u32"]) == 13
    assert active["low_nibble_motion_pointer_u32"][1] == "0x001fa7c0"
    assert active["high_nibble_motion_pointer_u32"][2] == "0x001fb7c0"
    assert len(active["route_motion_vectors_s16"]["low"]["17"]) == 16
    assert len(active["route_motion_vectors_s16"]["high"]["47"]) == 13
    emitter = parent["child_emitter_state"]
    assert emitter["initial_child_count_u8"] == 5
    assert emitter["cadence_reload_u8"] == 6
    assert emitter["spawn_ticks_from_parent_state4"] == [1, 7, 13, 19, 25]
    assert emitter["child_spawn_source_frames"] == [4445, 4451, 4457, 4463, 4469]
    assert [row["variant_u8"] for row in emitter["normal_rows"]] == [0, 0, 0, 0, 1]
    assert [row["variant_u8"] for row in emitter["collision_rows"]] == [2, 2, 2, 2, 1]
    parent_box = parent["collision_table"]
    assert parent_box["table"] == "0x0002fc3c"
    assert parent_box["attack_entries"][1]["damage_selector_u8"] == 25
    assert parent_box["attack_entries"][1]["hit_value_u8"] == 8

    child = contract["record4_child_class4"]
    assert child["spec_executable"] is True
    assert child["record_type_u8"] == 4 and child["class_u8"] == 4
    assert child["dispatch"] == "0x0306fe"
    assert child["state_sequence_u8"] == [0, 2, 4]
    assert child["initialization"]["variant_offsets_u16"] == [8, 284, 448]
    assert [len(child["initialization"]["variant_presentation_sequences"][str(index)])
            for index in range(3)] == [17, 10, 16]
    assert child["collision_table"]["table"] == "0x00030cb6"
    assert child["collision_table"]["attack_entries"][1]["damage_selector_u8"] == 14
    assert child["capture_projection"]["spawn_cadence_frames"] == 6

    damage = contract["current_state_collision_damage"]
    assert damage["parent_contact"] == {
        "attack_record": "0x0002fc58", "attack_selector_u8": 25,
        "attacker": "0xff8680", "damage_u8": 127, "frame": 4424,
    }
    assert damage["child_contact"] == {
        "attack_record": "0x00030cd2", "attack_selector_u8": 14,
        "attacker": "0xff8700", "damage_u8": 31, "frame": 4427,
    }
    empty = contract["empty_fallback"]
    assert empty["cleanup_tick"] == 17 and empty["return_tick"] == 18
    assert empty["damaging_record4_count"] == 0
    assert {row["animation_record"] for row in empty["presentation_timeline"][1:17]} == {
        "0x0015fcfc"}
    assert contract["empty_effect_variant1_contract"]["class"] == "0x10"
    assert contract["implementation_blocker"] is None
    assert data["mutation_controls"]["wrong_character_rejected"] is True
    assert data["mutation_controls"]["count"] == 13
    assert len(data["counterfactuals"]) == 13
    assert data["physical_saturn"] == "UNRUN"
    assert data["saturn_emulator"] == "UNRUN"


def reject(mutant, label):
    try:
        validate(mutant)
    except AssertionError:
        return
    raise AssertionError("accepted mutation: " + label)


data = json.loads(ART.read_text(encoding="ascii"))
validate(data)
for path, value, label in [
    (("character_identity", "required_character_u8"), 1, "wrong character"),
    (("character_identity", "per_frame_asserted"), False, "identity not sampled"),
    (("character_identity", "required_probe", "animation"), "00165410", "Major animation admitted"),
    (("character_identity", "required_object_stream", "sha256"),
     data["character_identity"]["rejected_object_stream"]["sha256"], "Major object stream admitted"),
    (("resource_causal_trace", "sufficient", "debit"), 3, "Major resource debit"),
    (("implementation_contract", "sufficient_action", "cleanup_tick"), 49, "Major action duration"),
    (("implementation_contract", "sufficient_action", "resource_debit_u8"), 3, "Major resource rule"),
    (("implementation_contract", "sufficient_action", "presentation_timeline", 5, "animation_record"), "0x00165410", "Major presentation"),
    (("implementation_contract", "record4_parent_class0", "class_u8"), 5, "Major projectile class"),
    (("implementation_contract", "record4_parent_class0", "dispatch"), "0x030d34", "Major dispatcher"),
    (("implementation_contract", "record4_parent_class0", "state_sequence_u8"), [0, 2, 4, 6, 8], "invented parent state"),
    (("implementation_contract", "record4_parent_class0", "active_state", "angle_u8_route_values", "cold_run_1"), [16], "wrong target angle"),
    (("implementation_contract", "record4_parent_class0", "child_emitter_state", "cadence_reload_u8"), 5, "wrong child cadence"),
    (("implementation_contract", "record4_parent_class0", "child_emitter_state", "normal_rows", 4, "variant_u8"), 0, "wrong terminal child variant"),
    (("implementation_contract", "record4_parent_class0", "collision_table", "table"), "0x0003136a", "Major collision table"),
    (("implementation_contract", "record4_child_class4", "class_u8"), 5, "wrong child class"),
    (("implementation_contract", "record4_child_class4", "initialization", "variant_offsets_u16", 1), 285, "wrong child presentation offset"),
    (("implementation_contract", "record4_child_class4", "collision_table", "attack_entries", 1, "damage_selector_u8"), 6, "Major damage selector"),
    (("implementation_contract", "current_state_collision_damage", "parent_contact", "damage_u8"), 24, "Major damage"),
    (("implementation_contract", "empty_fallback", "presentation_timeline", 1, "animation_record"), "0x001645d4", "Major empty pose"),
    (("mutation_controls", "wrong_character_rejected"), False, "identity rejection disabled"),
]:
    mutant = copy.deepcopy(data)
    cursor = mutant
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    reject(mutant, label)
print("ORACLE-11 corrected Predator Button1 tests: PASS (21 mutations rejected)")
