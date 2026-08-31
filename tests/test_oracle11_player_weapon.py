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
    assert contract["source_input"]["native_input_pipeline_updates_u8"] == 1
    assert contract["source_input"]["action_dispatch_delay_updates_u8"] == 1
    assert contract["source_input"]["coffee_shop_control"] == {
        "physical_edge_frame": 2250,
        "action_entry_visible_frame": 2252,
        "parent_first_visible_frame": 2254,
    }
    action = contract["sufficient_action"]
    assert action["cleanup_tick"] == 19 and action["return_tick"] == 20
    assert action["resource_capacity_u8"] == 64
    assert action["resource_debit_u8"] == 40
    assert action["recharge_countdown_after_entry_u8"] == 12
    assert action["player_position_and_facing_latched"] is True
    assert action["resource_debit_tick"] == 1
    assert action["parent_allocation_tick"] == 1
    assert action["rng_calls"] == []
    stage_progress = action["source_stage_progress"]
    assert stage_progress["classification"] == \
        "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert stage_progress["spec_executable"] is True
    assert stage_progress["caller"] == {
        "player_state_program": "0x024060",
        "delta_load_pc": "0x024094",
        "helper_call_pc": "0x024096",
        "delta_u16": 3,
        "action_entry_tick_u8": 0,
        "scheduler_position": "sufficient Button1 action-entry player update before resource debit, projectile allocation, and actor scheduler",
        "source_window": {
            "start": "0x024060", "end_exclusive": "0x024100",
            "bytes": 160,
            "sha256": "629285f7329ff301a5f80b01ce3e1b9ac268a1df8bf56865bfd1b941ab1915d4",
        },
    }
    helper = stage_progress["helper"]
    assert helper["entry"] == "0x0179e2" and helper["return"] == "0x017b74"
    assert helper["guard"] == {
        "field": "a5+0x01b0:u8",
        "predicate": "u8(a5+0x01b0) == 0",
        "checked_before_add_and_before_route_bounds": True,
    }
    assert helper["fields"] == {
        "progress": "a5+0x0226:u16",
        "stage_parameter": "a5+0x01ea:s16",
        "upper_bound": "a5+0x021a:s16",
        "lower_bound": "a5+0x021c:s16",
    }
    assert helper["field_layout"] == {
        "guard": {"a5_offset_u16": 0x01b0,
                  "absolute": "0x00ff81b0", "width_u8": 1,
                  "signed": False},
        "stage_parameter": {"a5_offset_u16": 0x01ea,
                            "absolute": "0x00ff81ea", "width_u8": 2,
                            "signed": True},
        "upper_bound": {"a5_offset_u16": 0x021a,
                        "absolute": "0x00ff821a", "width_u8": 2,
                        "signed": True},
        "lower_bound": {"a5_offset_u16": 0x021c,
                        "absolute": "0x00ff821c", "width_u8": 2,
                        "signed": True},
        "progress": {"a5_offset_u16": 0x0226,
                     "absolute": "0x00ff8226", "width_u8": 2,
                     "signed": False},
    }
    assert (helper["progress_threshold_u16"],
            helper["progress_mask_u16"],
            helper["stage_domain_limit_u16"],
            helper["stage_domain_mask_u16"],
            helper["coffee_shop_lower_bound_s16"],
            helper["coffee_shop_upper_bound_s16"]) == (8, 7, 32, 31, 8, 16)
    assert helper["rng_calls"] == []
    assert [(row["source_frame_u16"], row["progress_before_u16"],
             row["progress_after_add_u16"], row["progress_after_mask_u16"],
             row["stage_before_s16"], row["stage_after_s16"])
            for row in stage_progress["coffee_shop_calls"][:3]] == [
                (2252, 0, 3, 3, 8, 8),
                (2342, 3, 6, 6, 8, 8),
                (2432, 6, 9, 1, 8, 9),
            ]
    assert len(stage_progress["coffee_shop_calls"]) == 15
    assert stage_progress["capture_identity"]["independent_captures"] == 2
    assert stage_progress["capture_identity"][
        "byte_identical_selected_rows"] is True
    assert stage_progress["fixed_frame_substitute"] is False
    timeline = action["presentation_timeline"]
    assert len(timeline) == 20
    assert [timeline[index]["animation_record"] for index in range(8)] == [
        "0x0015f1f4", "0x0015e540", "0x0015e540", "0x0015e540",
        "0x0015e550", "0x0015e560", "0x0015e560", "0x0015e570",
    ]
    assert timeline[-2]["animation_record"] == "0x0015e580"
    assert timeline[-1]["animation_record"] == "0x0015f1f4"
    assert timeline[5]["assembly"] == "0x00161a0a"
    selector_contract = action["presentation_selector_contract"]
    assert selector_contract["selector_range_u8"] == [4, 7]
    assert selector_contract["selection_tick"] == 0
    assert selector_contract[
        "projectile_angle_and_player_presentation_share_scan"] is True
    assert selector_contract["coffee_shop_source_witness"] == {
        "frame": 2343,
        "selector_u8": 5,
        "animation_record": "0x0015e594",
    }
    selector_timelines = selector_contract["selector_timelines"]
    assert sorted(map(int, selector_timelines)) == [4, 5, 6, 7]
    assert all(len(rows) == 20 for rows in selector_timelines.values())
    assert selector_timelines["4"] == timeline
    assert selector_timelines["5"][1]["animation_record"] == "0x0015e594"
    assert selector_timelines["5"][1]["assembly"] == "0x0016179a"
    assert selector_timelines["6"][1]["animation_record"] == "0x0015e5e8"
    assert selector_timelines["7"][1]["animation_record"] == "0x0015e63c"

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
    assert len(init["presentation_records"]) == 8
    assert init["presentation_records"][-1]["animation_record"] == "0x0002fbb8"
    assert init["presentation_records"][-1]["branch_s16"] < 0
    assert "negate x only when facing is nonzero" in init["position_rule"]
    assert "preserve their reused fractional low words" in \
        init["position_rule"]
    assert "fractional low words survive fixed-slot reuse" in \
        parent["allocation_writes"]["position"]
    active = parent["active_state"]
    assert active["angle_u8_route_values"] == {
        "cold_run_1": [17], "facing_reversed": [47],
        "target_inside": [35], "target_outside": [35],
    }
    assert len(active["low_nibble_motion_pointer_u32"]) == 16
    assert len(active["high_nibble_motion_pointer_u32"]) == 13
    assert active["low_nibble_motion_pointer_u32"][1] == "0x001fa7c0"
    assert active["high_nibble_motion_pointer_u32"][2] == "0x001fb7c0"
    assert sorted(map(int, active["route_motion_vectors_s16"]["low"])) == \
        list(range(17, 48))
    assert len(active["route_motion_vectors_s16"]["low"]["17"]) == 16
    assert len(active["route_motion_vectors_s16"]["high"]["47"]) == 13
    assert active["coffee_shop_route_angles_u8"] == [17, 21, 42, 45, 46]
    assert active["base_motion_vectors_s16"]["45"] == [-489, -169]
    assert active["presentation_terminal_rule"] == (
        "record 0x0002fbb8 branch -32768 returns to 0x0002fba8; it does "
        "not enter emitter state 4")
    target = active["target_selection"]
    assert target["entry"] == "0x0241f0"
    assert target["distance_thresholds_u16"] == [
        0, 13, 16, 22, 30, 38, 48, 58, 70, 88, 103, 123, 153,
        192, 251, 352]
    assert target["presentation_selectors_u8"] == \
        [7, 7, 7, 7, 6, 6, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4]
    assert "unsigned word comparison begins at 65535" in \
        target["nearest_rule"]
    emitter = parent["child_emitter_state"]
    assert emitter["initial_child_count_u8"] == 5
    assert emitter["cadence_reload_u8"] == 6
    assert emitter["spawn_ticks_from_parent_state4"] == [1, 7, 13, 19, 25]
    assert emitter["child_spawn_source_frames"] == [4445, 4451, 4457, 4463, 4469]
    assert [row["variant_u8"] for row in emitter["normal_rows"]] == [0, 0, 0, 0, 1]
    assert [row["variant_u8"] for row in emitter["collision_rows"]] == [2, 2, 2, 2, 1]
    assert emitter["position_rule"] == (
        "child x uses parent x plus facing-adjusted row x; child y and z "
        "both use parent z plus their signed row field")
    effect = parent["effect_allocation"]
    assert effect["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert effect["guard"] == "global phase byte +0x19 bit0 is clear"
    assert effect["native_phase_projection"]["mask_u8"] == 1
    assert effect["native_phase_projection"]["expected_u8"] == 1
    assert effect["timer_u8"] == 8
    assert effect["state0"]["falls_through_to_state2"] is True
    assert effect["scene_actor_rows_u16"] == 793
    assert effect["scene_lifetime_count_u16"] == 113
    reuse = effect["fixed_slot_reuse_presentation"]
    assert reuse["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert reuse["unwritten_retained_fields"] == [
        "animation_timer actor+0x0a:u16",
        "animation_branch actor+0x24:s16"]
    assert reuse["prior_owner"]["animation_timer_u16"] == 4094
    assert reuse["prior_owner"]["animation_branch_s16"] == -32768
    assert [row["source_slot"] for row in reuse["first_reuses"]] == [
        "0x00ffc500", "0x00ffc480"]
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
    registration = damage["registration_and_pair_eligibility"]
    assert registration["classification"] == \
        "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert registration["spec_executable"] is True
    assert registration["visibility"] == {
        "fail_write": "actor+0x01:u8 = 0 at 0x0167e6",
        "pass_write": "actor+0x01:u8 = 1 at 0x0167d0",
        "update_order": [
            "actor state/action/movement/animation",
            "visibility guard and actor+0x01 write",
            "record-type collision-list registration",
            "record4-v-record12 collision scheduler",
        ],
        "x_guard": "u16(actor_x - camera_x + 0x0040) <= 0x0200",
        "y_guard": "u16(actor_y - camera_z + 0x0020) <= 0x0140",
    }
    assert registration["registration"]["record4"]["writer"] == \
        "0x01681e..0x016828"
    assert registration["registration"]["record12"]["writer"] == \
        "0x016864..0x01686e"
    assert registration["identity_writer"][
        "coffee_shop_counter_before_parent_u8"] == 0x25
    assert [row["identity_u8"] for row in
            registration["identity_writer"]["assignments"]] == \
        [0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b]
    assert registration["types_and_signedness"]["defender_latches"] == \
        "defender+0x68:u8[8]"
    assert registration["pair_guards"] == [
        "defender+0x6d:u8 < 4 in scheduler",
        "defender+0x00:u8 == 1",
        "defender+0x70:u8 == 0",
        "if attacker+0x65:s8 >= 0 then defender+0x68[index] != attacker+0x67",
        "attacker animation record byte +9 attack selector != 0",
        "defender animation record byte +8 hurt selector != 0",
        "current attack and hurt boxes overlap",
    ]
    assert registration["coffee_shop_projection"] == {
        "absent_through_frame": 2295,
        "contact_attacker": "0xff8880",
        "contact_identity_u8": 0x2a,
        "first_contact_frame": 2306,
        "first_registered_frame": 2296,
        "health_s16": [87, 56],
        "target_slot": "0xffa180",
    }
    assert registration["mutation_control"] == {
        "actor_and_route_projection_unchanged_through_frame": 2305,
        "frames": [2296, 2310],
        "kind": "redirect only target 0xffa180 record12 list writes to 0xffa240",
        "list_count_unchanged_u8": 7,
        "suppressed_writes": 15,
        "target_first_contact_frame_after": 2311,
        "target_first_contact_frame_before": 2306,
        "writer": "0x01686c",
    }
    resource_tick = contract["resource_tick"]
    assert resource_tick["classification"] == \
        "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert resource_tick["dispatch_guard"]["routine"] == "0x01a6f4"
    assert resource_tick["dispatch_guard"]["empty_action_u16"] == "0x1a00"
    assert resource_tick["dispatch_guard"]["rule"] == \
        "player+0x8b:u8 nonzero owns the empty-resource Button1 dispatch; " \
        "the instantaneous player+0x8c resource value does not override " \
        "that latch"
    assert resource_tick["normal_tick"]["reload_u8"] == 3
    assert resource_tick["normal_tick"]["increment_writer_pc"] == \
        "0x0adf2e"
    assert resource_tick["depleted_tick"]["reload_u8"] == 6
    assert resource_tick["depleted_tick"]["clear_latch_writer_pc"] == \
        "0x0adfe6"
    assert resource_tick["coffee_shop_projection"]["before_empty_dispatch"] == {
        "depleted_u8": 1, "frame_u16": 2521, "recharge_u8": 1,
        "resource_u8": 13, "state_u16": "0x0200",
        "substate_u16": "0x0002",
    }
    assert resource_tick["mutation_control"][
        "high_resource_depleted_witness"] == {
            "depleted_u8": 1, "frame_u16": 2522, "recharge_u8": 5,
            "resource_u8": 43, "state_u16": "0x0200",
            "substate_u16": "0x1a00",
        }
    assert resource_tick["mutation_control"]["suppressed_writes"] == 18
    empty = contract["empty_fallback"]
    assert empty["cleanup_tick"] == 17 and empty["return_tick"] == 18
    assert empty["damaging_record4_count"] == 0
    assert {row["animation_record"] for row in empty["presentation_timeline"][1:17]} == {
        "0x0015fcfc"}
    empty_effect = contract["empty_effect_variant1_contract"]
    assert empty_effect["class"] == "0x10"
    assert empty_effect["variant"] == 0
    assert empty_effect["allocation"]["allocation_update_after_entry_u8"] == 1
    assert empty_effect["allocation"]["variant_writer"] == \
        "0x019f6c copies player+0xd2:u8"
    assert empty_effect["allocation"]["unwritten_fields_retained"] == [
        "x_fraction:u16", "y_fraction:u16", "z:s16"]
    assert empty_effect["capture_projection"][
        "coffee_shop_first_visible_position_s16"] == [944, 404, 319]
    assert contract["implementation_blocker"] is None
    sufficient_entry = contract["sufficient_action"]["entry_projection"]
    assert sufficient_entry["entry_preserves_current_presentation"] is True
    assert sufficient_entry["coffee_shop_witness"] == {
        "prior_frame_u16": 2251, "entry_frame_u16": 2252,
        "prior_animation_record": "0x0015f1f4",
        "entry_animation_record": "0x0015f1f4",
        "prior_timer_u16": 4082, "entry_timer_u16": 4082,
        "prior_branch_s16": -32768, "entry_branch_s16": -32768,
        "active_frame_u16": 2253,
        "active_animation_record": "0x0015e540",
        "active_timer_u16": 2, "active_branch_s16": 0,
    }
    animation_execution = contract["sufficient_action"]["animation_execution"]
    assert animation_execution["entry_rebind_updates_u8"] == [1, 2]
    assert animation_execution["writers"] == {
        "record_bind": "0x01652a then 0x016588",
        "timer_bind": "0x01652e then 0x01658c",
        "branch_bind": "0x016534 then 0x016592",
        "timer_decrement": "0x016574",
    }
    assert animation_execution["coffee_shop_writer_frames"] == {
        "first_bind_u16": 2252, "second_bind_u16": 2253,
        "first_decrement_u16": 2254,
        "next_record_bind_frames_u16": [2255, 2256, 2258, 2259],
    }
    assert animation_execution["capture_identity"] == {
        "independent_captures": 2, "byte_identical": True,
        "sha256": "bc3c9cc7df2830bbf61cd8a4a8bbebd57e7860b0a2d3aacad9e6c75a07575438",
    }
    special = data["special_implementation_contract"]
    assert special["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
    assert special["spec_executable"] is True
    assert special["source_input"]["guard_routine"] == "0x01a7e6"
    assert special["source_input"]["action_writer"] == "0x01a89a"
    assert special["source_input"]["physical_combo_frame"] == 2790
    assert special["source_input"]["visible_action_entry_frame"] == 2792
    assert special["state_dispatch"]["entry"] == "0x023132"
    assert special["state_dispatch"]["handlers"] == {
        "0x00": "0x02314e", "0x02": "0x0231a4",
        "0x04": "0x023202"}
    assert special["state_dispatch"]["route_state_sequence_u16"] == \
        [0x0800, 0x0802, 0x0804]
    assert special["initialization"]["presentation_selector_u8"] == 47
    assert len(special["initialization"]["presentation_records"]) == 17
    assert [row["visible_duration_u16"] for row in
            special["initialization"]["visible_presentation_runs"]] == \
        [4, 4, 3, 1, 5, 4, 4, 4, 4, 4, 6, 4, 4, 4, 4, 16, 1]
    assert special["initialization"]["presentation_records"][4][
        "attack_selector_u8"] == 11
    assert special["active_state"]["class4b_allocation_writer"] == \
        "0x0231c2..0x0231f2"
    assert special["active_state"]["class4b_class_u8"] == "0x4b"
    assert special["active_state"]["class3d_allocation_writer"] == \
        "0x023220..0x023246"
    assert special["active_state"]["class3d_class_u8"] == "0x3d"
    assert special["active_state"]["source_contact_frame"] == 2804
    assert special["active_state"]["source_audio_commands"] == \
        ["0x0091", "0x0096"]
    assert special["completion"]["health_cost_s16"] == 6
    assert special["completion"]["cleanup_frame"] == 2869
    assert special["completion"]["return_locomotion_frame"] == 2870
    assert special["capture_identity"]["independent_captures"] == 2
    assert special["capture_identity"]["byte_identical"] is True
    assert special["fixed_frame_substitute_forbidden"] is True
    assert data["special_causal_trace"]["player_routine"] == "0x023132"
    assert "0x024f04" in data["special_causal_trace"]["correction"]
    assert data["special_causal_trace"]["actors"] == \
        ["type24 class0x4b", "type24 class0x3d"]
    assert data["mutation_controls"]["wrong_character_rejected"] is True
    assert data["mutation_controls"]["count"] == 15
    assert len(data["counterfactuals"]) == 15
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
    (("implementation_contract", "sufficient_action", "presentation_selector_contract", "selector_timelines", "5", 1, "animation_record"), "0x0015e540", "Coffee Shop target selector collapsed"),
    (("implementation_contract", "record4_parent_class0", "class_u8"), 5, "Major projectile class"),
    (("implementation_contract", "record4_parent_class0", "dispatch"), "0x030d34", "Major dispatcher"),
    (("implementation_contract", "record4_parent_class0", "state_sequence_u8"), [0, 2, 4, 6, 8], "invented parent state"),
    (("implementation_contract", "record4_parent_class0", "active_state", "angle_u8_route_values", "cold_run_1"), [16], "wrong target angle"),
    (("implementation_contract", "record4_parent_class0", "active_state", "target_selection", "distance_thresholds_u16", 13), 191, "wrong target threshold"),
    (("implementation_contract", "record4_parent_class0", "active_state", "target_selection", "nearest_rule"), "scan from 255", "truncated nearest-target range"),
    (("implementation_contract", "record4_parent_class0", "active_state", "presentation_terminal_rule"), "enter state 4", "terminal presentation loop removed"),
    (("implementation_contract", "record4_parent_class0", "allocation_writes", "position"), "copy complete fixed point position", "fixed-slot fractional residue cleared"),
    (("implementation_contract", "record4_parent_class0", "active_state", "base_motion_vectors_s16", "45", 0), -488, "wrong shared base motion"),
    (("implementation_contract", "record4_parent_class0", "initialization", "presentation_records", 7, "animation_record"), "0x0002fba8", "missing terminal presentation"),
    (("implementation_contract", "source_input", "native_input_pipeline_updates_u8"), 0, "missing source input pipeline"),
    (("implementation_contract", "source_input", "action_dispatch_delay_updates_u8"), 0, "premature source action dispatch"),
    (("implementation_contract", "sufficient_action", "parent_allocation_tick"), 2, "deferred parent allocation"),
    (("implementation_contract", "sufficient_action", "source_stage_progress", "caller", "delta_u16"), 2, "wrong stage-progress delta"),
    (("implementation_contract", "sufficient_action", "source_stage_progress", "helper", "progress_threshold_u16"), 7, "wrong stage-progress threshold"),
    (("implementation_contract", "sufficient_action", "source_stage_progress", "coffee_shop_calls", 2, "source_frame_u16"), 2433, "late stage-progress invocation"),
    (("implementation_contract", "sufficient_action", "source_stage_progress", "fixed_frame_substitute"), True, "fixed-frame stage transition"),
    (("implementation_contract", "resource_tick", "dispatch_guard", "rule"), "resource below debit owns empty dispatch", "instantaneous resource guess"),
    (("implementation_contract", "resource_tick", "normal_tick", "reload_u8"), 2, "wrong normal resource cadence"),
    (("implementation_contract", "resource_tick", "depleted_tick", "clear_latch_writer_pc"), "0x0adfe0", "premature depleted clear"),
    (("implementation_contract", "record4_parent_class0", "child_emitter_state", "cadence_reload_u8"), 5, "wrong child cadence"),
    (("implementation_contract", "record4_parent_class0", "child_emitter_state", "normal_rows", 4, "variant_u8"), 0, "wrong terminal child variant"),
    (("implementation_contract", "record4_parent_class0", "child_emitter_state", "position_rule"), "child y uses parent y", "wrong child coordinate base"),
    (("implementation_contract", "record4_parent_class0", "effect_allocation", "native_phase_projection", "expected_u8"), 0, "wrong parent effect phase"),
    (("implementation_contract", "record4_parent_class0", "effect_allocation", "state0", "falls_through_to_state2"), False, "parent effect state0 early return"),
    (("implementation_contract", "record4_parent_class0", "effect_allocation", "fixed_slot_reuse_presentation", "prior_owner", "animation_timer_u16"), 4095, "parent effect animation residue cleared"),
    (("implementation_contract", "record4_parent_class0", "collision_table", "table"), "0x0003136a", "Major collision table"),
    (("implementation_contract", "record4_child_class4", "class_u8"), 5, "wrong child class"),
    (("implementation_contract", "record4_child_class4", "initialization", "variant_offsets_u16", 1), 285, "wrong child presentation offset"),
    (("implementation_contract", "record4_child_class4", "collision_table", "attack_entries", 1, "damage_selector_u8"), 6, "Major damage selector"),
    (("implementation_contract", "current_state_collision_damage", "parent_contact", "damage_u8"), 24, "Major damage"),
    (("implementation_contract", "current_state_collision_damage", "registration_and_pair_eligibility", "visibility", "x_guard"), "u16(actor_x - camera_x + 0x0020) <= 0x0200", "wrong collision visibility bias"),
    (("implementation_contract", "current_state_collision_damage", "registration_and_pair_eligibility", "registration", "record12", "writer"), "0x016864..0x01686a", "wrong defender registration writer"),
    (("implementation_contract", "current_state_collision_damage", "registration_and_pair_eligibility", "identity_writer", "coffee_shop_counter_before_parent_u8"), 0x24, "wrong collision identity seed"),
    (("implementation_contract", "current_state_collision_damage", "registration_and_pair_eligibility", "pair_guards", 2), "no per-attacker latch", "missing projectile latch guard"),
    (("implementation_contract", "current_state_collision_damage", "registration_and_pair_eligibility", "mutation_control", "target_first_contact_frame_after"), 2306, "nondiscriminating registration mutation"),
    (("implementation_contract", "empty_fallback", "presentation_timeline", 1, "animation_record"), "0x001645d4", "Major empty pose"),
    (("special_implementation_contract", "source_input", "guard_routine"), "0x024f04", "wrong special guard owner"),
    (("special_implementation_contract", "state_dispatch", "entry"), "0x024f04", "wrong special dispatcher"),
    (("special_implementation_contract", "state_dispatch", "route_state_sequence_u16"), [0x0800, 0x0802], "missing special active state"),
    (("special_implementation_contract", "initialization", "presentation_selector_u8"), 42, "wrong special selector"),
    (("special_implementation_contract", "initialization", "presentation_records", 4, "attack_selector_u8"), 0, "missing special attack selector"),
    (("special_implementation_contract", "initialization", "visible_presentation_runs", 4, "visible_duration_u16"), 3, "wrong special visible cadence"),
    (("special_implementation_contract", "active_state", "class4b_class_u8"), "0x20", "wrong special presentation child"),
    (("special_implementation_contract", "active_state", "class3d_class_u8"), "0x47", "wrong special emitted effect"),
    (("special_implementation_contract", "completion", "health_cost_s16"), 5, "wrong special health cost"),
    (("special_implementation_contract", "fixed_frame_substitute_forbidden"), False, "special fixed-frame substitute"),
    (("mutation_controls", "wrong_character_rejected"), False, "identity rejection disabled"),
]:
    mutant = copy.deepcopy(data)
    cursor = mutant
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    reject(mutant, label)
print("ORACLE-11 corrected Predator Button1 tests: PASS (57 mutations rejected)")
