#!/usr/bin/env python3
"""Validate deterministic SPEC-02 generation and real field-family controls."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "spec02", ROOT / "tools/build_spec02_round1_contract.py")
assert SPEC and SPEC.loader
spec02 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(spec02)
contract = json.loads(spec02.OUT.read_text(encoding="ascii"))
fixtures = json.loads(spec02.FIXTURES.read_text(encoding="ascii"))
spec02.validate(contract, fixtures)
weapon = fixtures["authority_data"]["player"][
    "weapon_projectile_resource"]["implementation_contract"]
assert weapon["source_input"]["button1_mask"] == "0x0010"
assert weapon["sufficient_action"]["cleanup_tick"] == 19
assert weapon["sufficient_action"]["resource_debit_u8"] == 40
assert weapon["empty_fallback"]["cleanup_tick"] == 17
parent = weapon["record4_parent_class0"]
child = weapon["record4_child_class4"]
assert parent["spec_executable"] is True and parent["class_u8"] == 0
assert child["spec_executable"] is True and child["class_u8"] == 4
assert parent["collision_table"]["table"] == "0x0002fc3c"
assert child["collision_table"]["table"] == "0x00030cb6"
assert parent["child_emitter_state"]["spawn_ticks_from_parent_state4"] == [
    1, 7, 13, 19, 25]
parent_state = parent["child_emitter_state"]["state_projection"]
assert parent_state["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert parent_state["spec_executable"] is True
assert [row["source_state_u16"] for row in
        parent_state["coffee_shop_first_parent"]] == [
            "0x0400", "0x0402", "0x0602"]
assert parent_state["first_child_visible_frame_u16"] == 2288
assert parent_state["mutation_control"]["first_rejected_frame_u16"] == 2288
assert [len(child["initialization"]["variant_presentation_sequences"][str(i)])
        for i in range(3)] == [17, 10, 16]
damage = weapon["current_state_collision_damage"]
assert damage["parent_contact"]["damage_u8"] == 127
assert damage["child_contact"]["damage_u8"] == 31
registration = damage["registration_and_pair_eligibility"]
assert registration["spec_executable"] is True
registration_boundary = registration["new_allocation_registration_boundary"]
assert registration_boundary["classification"] == \
    "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert registration_boundary["spec_executable"] is True
assert registration_boundary["coffee_shop_slot_0xff8880"] == {
    "identity_assignment_frame_u16": 2305,
    "collision_identity_u8": 42,
    "allocation_visible_frame_u16": 2306,
    "attacker_list_absent_frame_u16": 2305,
    "attacker_list_present_frame_u16": 2306,
    "source_contact_frame_u16": 2306,
    "source_target_slot": "0xffa180",
    "source_attack_record": "0x030cd2"}
assert [row["slots"] for row in registration_boundary["attacker_lists"]] == [
    ["0xff8700", "0xff8800"],
    ["0xff8700", "0xff8800", "0xff8880"]]
assert registration_boundary["mutation_control"][
    "first_rejected_visible_frame_u16"] == 2306
reaction_handoff = registration["collision_to_reaction_handoff"]
assert reaction_handoff["classification"] == \
    "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert reaction_handoff["spec_executable"] is True
assert reaction_handoff["coffee_shop_slot_0xffa180"] == {
    "collision_scheduler_source_frame_u16": 2306,
    "collision_visible_frame_u16": 2307,
    "health_before_s16": 87,
    "health_after_s16": 56,
    "state_u16": "0x0202",
    "substate_u16": "0x0000",
    "animation_record": "0x0012eb5c",
    "hurt_selector_u8": 1,
    "attack_selector_u8": 1,
    "next_record12_visible_frame_u16": 2308,
    "next_state_u16": "0x0202",
    "next_substate_u16": "0x0002",
    "next_animation_record": "0x0012e04c",
    "next_hurt_selector_u8": 1,
    "next_attack_selector_u8": 1}
assert reaction_handoff["mutation_control"][
    "first_rejected_visible_frame_u16"] == 2307
assert registration["visibility"]["x_guard"] == \
    "u16(actor_x - camera_x + 0x0040) <= 0x0200"
assert registration["visibility"]["y_guard"] == \
    "u16(actor_y - camera_z + 0x0020) <= 0x0140"
assert registration["identity_writer"][
    "coffee_shop_counter_before_parent_u8"] == 0x25
assert [row["identity_u8"] for row in
        registration["identity_writer"]["assignments"]] == \
    [0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b]
assert registration["coffee_shop_projection"]["first_registered_frame"] == 2296
assert registration["coffee_shop_projection"]["first_contact_frame"] == 2306
assert registration["mutation_control"]["target_first_contact_frame_after"] == 2311
assert weapon["empty_effect_variant1_contract"]["spec_executable"] is True
weapon_actor = weapon["player_actor_projection"]
assert weapon_actor["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert weapon_actor["spec_executable"] is True
assert [(row["first_frame_u16"], row["last_frame_u16"],
         row["substate_u16"])
        for row in weapon_actor["visible_runs"]] == [
            (2252, 2252, "0x0c00"), (2253, 2255, "0x0c02"),
            (2256, 2272, "0x0c04"), (2273, 2273, "0x0000"),
            (2274, 2274, "0x0002")]
assert all(row["hurt_selector_u8"] == 0 and
           row["attack_selector_u8"] == 0
           for row in weapon_actor["visible_runs"])
assert weapon_actor["mutation_control"]["first_rejected_frame_u16"] == 2252
assert weapon["empty_effect_variant1_contract"]["initialization"][
    "presentation_actor_fields"] == {
        "coordinate_mode_u8": 0, "palette_u8": 0, "facing_u8": 0,
        "object_or_u16": "0x8000",
        "source_fields": {
            "coordinate_mode": "zero-initialized actor +0x0d u8",
            "palette": "zero-initialized actor +0x0e u8",
            "facing": "clr.b actor +0x0f at 0x07a020",
            "object_or": "move.w #0x8000 to actor +0x2e at 0x07a014"}}
class1f = next(item for item in fixtures["authority_data"]["enemies"]["archetypes"]
               if item["class"] == "0x1f")
class1f_records = {row["animation_record"]: row for row in
                   class1f["presentation_and_collision"]["records"]}
assert (class1f_records["0x0012dd50"]["assembly"],
        class1f_records["0x0012dd50"]["hurt_selector"],
        class1f_records["0x0012dd50"]["attack_selector"]) == \
       ("0x00130248", 1, 0)
assert (class1f_records["0x0012e214"]["assembly"],
        class1f_records["0x0012e214"]["hurt_selector"],
        class1f_records["0x0012e214"]["attack_selector"]) == \
       ("0x0013020c", 14, 0)
assert (class1f_records["0x0012eb5c"]["hurt_selector"],
        class1f_records["0x0012ec74"]["hurt_selector"]) == (1, 2)
initial = class1f["initial_transition_contract"]
assert initial["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert [row["entry_delay_u8"] for row in initial["actors"][-3:]] == [9, 3, 16]
assert [row["coordinate_mode_u8"] for row in initial["actors"]] == [1] * 10
assert [row["palette_u8"] for row in initial["actors"]] == [16, 17, 17, 18, 17, 16, 18, 17, 19, 19]
assert [row["object_or_u16"] for row in initial["actors"]] == ["0x8000"] * 10
assert [row["hurt_selector_u8"] for row in initial["actors"]] == [1] * 10
assert [row["attack_selector_u8"] for row in initial["actors"]] == [1] * 10
assert [row["selector_u8"] for row in initial["animation_sequences"]] == [0, 1, 52, 60, 62, 76]
current = class1f["current_state_implementation_contract"]
assert current["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert current["authority_boundary"]["retained_gameplay_authority_forbidden"] is True
assert current["spawn"]["first_dynamic"]["slot"] == "0xff9c40"
assert current["spawn"]["bounded_current_state_dynamic"]["slot"] == "0xffa000"
assert current["spawn"]["bounded_current_state_dynamic"]["writer_pc"] == "0x028a3e"
assert current["actions"]["approach_0x1600"]["x_delta_s16"] == 111
assert current["actions"]["attack_0x1800"]["contact_offsets_u16"] == [48, 119]
assert current["damage_hit_ko_removal"]["damage_by_player_selector_s16"] == [8, 8, 10, 12]
hit_entry = current["damage_hit_ko_removal"]["source_hit_entry_program"]
assert hit_entry["capture_identity"]["byte_identical"] is True
assert hit_entry["entry_guard"]["recovery_timer_actor_2c_u8"] == 8
assert hit_entry["reaction_table"]["reaction_selector_actor_4d_u8"] == 0x36
assert hit_entry["reaction_table"]["hit_mode_actor_46_u8"] == 2
assert hit_entry["visible_result"]["animation_record"] == "0x0012e04c"
assert hit_entry["visible_result"]["assembly"] == "0x001308a6"
assert hit_entry["recovery"]["captured_values_before_decrement"] == [8, 7, 6, 5, 4, 3, 2, 1, 0]
assert hit_entry["recovery"]["transition_scheduler_boundary"] == {"recovery_transition_returns_before_action_dispatch": True, "transition_visible_source_frame": 2317, "transition_visible_substate_u16": 0x0200, "transition_visible_animation_record": "0x0012e04c", "transition_visible_x_fp_u32": 0x02ac4c00, "transition_visible_y_fp_u32": 0x0136d600, "launch_visible_source_frame": 2318, "launch_visible_substate_u16": 0x0202, "launch_visible_animation_record": "0x0012e05c", "launch_visible_x_fp_u32": 0x02aa8c00, "launch_visible_y_fp_u32": 0x01425600}
assert hit_entry["action_dispatch"]["required_action_phases_u16"] == [0x0200, 0x0202, 0x0204, 0x0206, 0x0208, 0x020a]
assert hit_entry["source_hit_program"]["phase_0x0200_launch"]["observed_written_motion"]["x_velocity_s32_16_16"] == -0x1c000
assert hit_entry["source_hit_program"]["phase_0x0202_first_flight"]["landing_visible_frame"] == 2364
assert hit_entry["source_hit_program"]["phase_0x0204_landing_hold"]["captured_values_before_decrement"] == [3, 2, 1]
assert hit_entry["source_hit_program"]["phase_0x0206_bounce"]["observed_motion_after_facing"]["y_acceleration_s32_16_16"] == -0xc000
assert hit_entry["source_hit_program"]["phase_0x0208_rng_hold"]["timer_initial_u8"] == 10
assert hit_entry["source_hit_program"]["phase_0x020a_terminal_animation"]["records"][-1]["animation_record"] == "0x0012ded8"
assert hit_entry["source_hit_program"]["animation_sequences"]["reaction_0x36"]["records"][0]["animation_record"] == "0x0012e04c"
assert hit_entry["source_hit_program"]["selector_context_rule"]["generic_action_selector_0x36_record"] == "0x0012e410"
assert hit_entry["source_hit_program"]["selector_context_rule"]["generic_action_selector_binding_forbidden"] is True
assert hit_entry["source_hit_program"]["normal_return"]["class1f_resume_at_2414"] == "0x0200:1600"
assert hit_entry["source_hit_program"]["normal_return"]["preserved_resume_fields"] == {"source_frame": 2413, "dispatch_pc": "0x0607e8", "actor_85_style_u8": 0, "actor_a3_u8": 0, "actor_a4_u8": 1, "actor_a5_u8": 1, "actor_a6_u8": 1, "actor_b0_u8": 2, "facing_u8": 1, "actor_x_s16": 582, "actor_z_s16": 310, "player_x_s16": 944, "player_z_s16": 320}
assert hit_entry["rng"]["seed_before_u16"] == 0xedd9
assert hit_entry["rng"]["seed_after_u16"] == 0xc9a2
assert hit_entry["rng"]["result_low_nibble_u8"] == 2
assert hit_entry["rng"]["timer_table_row_u8"] == [10] * 4 + [40] * 4 + [60] * 3 + [90] * 3 + [120] * 2
assert hit_entry["rng"]["selected_timer_u8"] == 10
assert hit_entry["mutation_control"]["mutant_animation_record"] == "0x0012dc50"
ko_entry = current["damage_hit_ko_removal"]["source_projectile_ko_program"]
assert ko_entry["capture_identity"]["byte_identical"] is True
assert ko_entry["collision_visible_result"]["outer_state_u16"] == 0x0400
assert ko_entry["scheduler_handoff"]["outer_state_u16"] == 0x0402
assert ko_entry["scheduler_handoff"]["recovery_values_before_decrement_u8"] == [8, 7, 6, 5, 4, 3, 2, 1, 0]
assert ko_entry["scheduler_handoff"]["reaction_selector_actor_4d_u8"] == 0x36
assert ko_entry["state_program"]["launch"]["y_velocity_s32_16_16"] == 0x98000
assert ko_entry["state_program"]["first_landing"]["timer_actor_2a_u8"] == 3
assert ko_entry["state_program"]["bounce"]["y_acceleration_s32_16_16"] == -0xc000
assert ko_entry["state_program"]["removal_hold"]["timer_actor_2a_u8"] == 60
assert ko_entry["state_program"]["release"]["release_writer"] == "0x0176ba"
assert ko_entry["state_program"]["rng_calls"] == []
actions = class1f["first_segment_action_execution_contract"]
assert actions["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert actions["capture_identity"]["byte_identical"] is True
assert len(actions["initializer"]["variants"]) == 10
assert [row["action_u8"] for row in actions["current_dispatch"]["action_targets"]] == list(range(0, 32, 2))
assert actions["current_dispatch"]["action_targets"][11] == {"action_u8": 22, "target": "0x060c2e"}
assert [row["selector_u8"] for row in actions["animation_selector_table"]["selectors"]] == [0, 1, 34, 35, 36, 43, 52, 53, 54, 55, 56, 60, 62, 68, 69, 70, 71, 72, 73, 74, 76, 77]
assert [row["table_index_u8"] for row in actions["movement_tables"]] == [1, 8]
assert actions["movement_tables"][1]["vectors"][8] == {"direction_u8": 8, "x_delta_s16": 2048, "y_delta_s16": 0}
assert actions["action_programs"]["source_bounds"]["x_max_u16"] == 0x05f0
assert actions["action_programs"]["source_bounds"]["activation_field_u8"] == "actor+0x01"
assert actions["action_programs"]["source_bounds"]["camera_operand_u16"] == "0xff8278"
assert actions["action_programs"]["animation_movement_helper_0x0165c4"]["movement_cadence"] == "only on timer expiry after binding the next animation record"
assert actions["action_programs"]["direction_helper_0x061032"]["upper_directions_by_a5_u8"] == [0x16, 0x0a]
assert actions["action_programs"]["action_0x0e"]["z_velocity_table_s32_16_16"] == [-0x00010000, -0x00014000, -0x00018000, -0x00020000]
assert actions["action_programs"]["action_0x04"]["selector_groups_u16"] == [[55], [56], [43, 43, 43, 55], [43, 43, 56]]
assert actions["attack_timer_table_u8"] == [30] * 4 + [60] * 4 + [120] * 4 + [160] * 4
assert actions["suppression_control"]["writer_pc"] == "0x0607e8"
assert actions["suppression_control"]["suppressed_writes"] == 179
assert actions["suppression_control"]["fixed_frame_substitute"] is False
inner8 = actions["inner_state_0x08_program"]
assert inner8["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert inner8["capture_identity"]["byte_identical"] is True
assert inner8["entry_transition"]["writer_pc"] == "0x0610c8"
assert inner8["entry_transition"]["timer_u16"] == 600
assert list(inner8["route_reachable_action_handlers"]) == [
    "0x00", "0x04", "0x06", "0x08", "0x0a", "0x0e", "0x10"]
assert len(inner8["animation_records"]) == 54
assert [row["table_index_u8"] for row in inner8["movement"]["tables"]] == [
    4, 11, 12, 15, 18, 19, 23, 25]
assert len(inner8["rng_calls"]) == 13
assert inner8["action_0x0e_motion"]["phase_2_terminal"][
    "x_velocity_by_facing_s32_16_16"] == [65536, -65536]
assert inner8["type16_emission"]["observed_source_spawn_frames"] == [
    3253, 3258, 3263]
assert inner8["mutation_control"]["suppressed_writer"] == "0x0610c8"
assert inner8["mutation_control"]["mutant_type16_spawn_frames"] == []
assert inner8["observed_path_program"]["action_0x00"][
    "captured_rng_call_counts"]["frame_3004_style_match"] == 4
assert inner8["observed_path_program"]["action_0x04"][
    "captured_terminals"]["frame_3134"].endswith("action 0x10")
assert inner8["observed_path_program"]["action_0x10"][
    "overlap_transition"]["writer"] == "0x04130e"
assert inner8["observed_path_program"]["action_0x0e"][
    "captured_selection"]["motion_selector_96_u16"] == 24
progression = fixtures["authority_data"]["route"]["first_segment_recurring_spawn"]
activation = fixtures["authority_data"]["route"]["first_entry_body"][
    "route4_player_activation_order"]
assert activation["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert activation["spec_executable"] is True
assert activation["route_writer"]["write_frame_u16"] == 2237
assert activation["route_writer"]["visible_sample_frame_u16"] == 2238
assert activation["visible_player_sample"] == {
    "source_frame_u16": 2238, "state_u16": "0x0200",
    "substate_u16": "0x0000"}
assert activation["mutation_control"]["rejected_visible_sample"][
    "substate_u16"] == "0x0200"
assert activation["mutation_control"]["fixed_frame_substitute"] is False
projection = fixtures["authority_data"]["player"][
    "locomotion_neutral_facing"]["actor_state_projection"]
assert projection["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert projection["spec_executable"] is True
assert projection["control_state_u16"] == "0x0200"
assert [(row["source_action_u16"], row["substate_u16"])
        for row in projection["action_projection"]] == [
            ("0x0200", "0x0000"), ("0x0202", "0x0002"),
            ("0x0204", "0x0004")]
assert projection["visible_samples"][-1] == {
    "source_frame_u16": 2239, "state_u16": "0x0200",
    "substate_u16": "0x0002"}
assert projection["mutation_control"]["rejected_substate_u16"] == "0x0200"
assert progression["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert progression["controller_program"]["initializer"]["limit_table_u16"] == [0, 35, 55, 70]
assert progression["controller_program"]["initializer"]["observed_after"]["state_u16"] == 0x0200
assert progression["controller_program"]["intro_gate_transition"]["write_values"] == {
    "camera_x_call_threshold_s16": 720,
    "conditional_local_0x2c_u8": 0,
    "conditional_phase_0x2e_u8": 1,
    "source_camera_target_u16": 208}
assert progression["controller_program"]["initial_spawn_transition"]["observed_after"] == {
    "frame": 2074, "living_enemy_count_u16": 10, "state_u16": 0x0202}
assert progression["progress_increment_boundary"]["writer_pc"] == "0x061070"
assert progression["progress_increment_boundary"]["transition_guard"] == {
    "class_u8": "0x1f", "health_s16": -1, "record_type_u8": 12,
    "state_u16": 0x0402, "substate_u16": 0}
assert progression["progress_increment_boundary"]["increment_u16"] == 1
assert len(progression["progress_increment_boundary"]["observed_transactions"]) == 20
assert progression["controller_program"]["intro_gate_transition"]["gate_owner"] == {
    "class_u8": "0x44", "effect": "u8(0xff1a11) = 0",
    "record": "0xffc580", "record_type_u8": 24,
    "source_contract": "accepted auxiliary first-segment class-0x44 command-guard owner",
    "state_u16": 0x0404, "writer_instruction": "0x08da32",
    "writer_successor_pc": "0x08da38"}
assert progression["intro_gate_suppression_control"]["mutant_at_frame_4100"] == {
    "aux_spawn_transactions": 0, "intro_gate_u8": 0xff,
    "main_spawn_transactions": 0, "state_u16": 0x0202,
    "timer42_u16": 60}
assert progression["primary_writer"]["tables"]["lane_offsets_s16"] == [24, 40, 56, 72, 88, 104]
assert len(progression["primary_writer"]["tables"]["lane_bucket_u8"]) == 64
assert progression["primary_writer"]["tables"]["lane_bucket_u8"][48:] == [3] * 16
assert progression["primary_writer"]["rng"]["calls"] == 1
dependencies = fixtures["authority_data"]["auxiliary"]["first_segment_dependencies"]
assert dependencies["class_0x09_type20_rng_owner"]["first_segment_calls_before_class4e"] == 44
assert dependencies["class_0x4e_type24_variant4_effect"]["allocation_pop_order"] == [
    "0x00ffc500", "0x00ffc480"]
class4e1 = dependencies["class_0x4e_type24_variant4_effect"][
    "variant1_collision_effect"]
assert class4e1["scene_lifetime_count_u16"] == 23
assert class4e1["first_collision"]["attacker_attack_record"] == "0x00030cd2"
assert class4e1["allocation"]["scheduler_guard"].startswith(
    "record-type-24 release/dispatch")
assert class4e1["allocation"]["fixed_slot_reuse_presentation"] == {
    "prior_visible_frame_u16": 2306,
    "prior_class_u8": "0x45",
    "allocation_visible_frame_u16": 2307,
    "allocated_class_u8": "0x4e",
    "rule": "0x0177da pops the released fixed slot without clearing fields not written by 0x01d622; retain the prior presentation until class-0x4e state 0 runs on its next scheduler visit",
    "retained_fields": ["animation_record", "animation_timer", "animation_branch"],
    "animation_record": "0x0008df2c", "assembly": "0x0008df96",
    "animation_timer_u16": 4045, "animation_branch_s16": -32768,
    "state0_scheduler_frame_u16": 2307,
    "state0_visible_frame_u16": 2308,
    "state0_animation_record": "0x00092914",
    "state0_assembly": "0x00092c04"}
assert class4e1["state0"]["first_seed_after"] == "0x4d11"
type36 = fixtures["authority_data"]["auxiliary"][
    "coffee_shop_type36_presentation"]
scene_components = fixtures["authority_data"]["auxiliary"][
    "coffee_shop_scene_component_identities"]
assert type36["pool"] == {"record_type_u8": 36, "base": "0xffd280",
                          "capacity": 64, "stride_u16": 64,
                          "scheduler": "0x01bd48"}
assert [(row["class"], row["lifetime_count"])
        for row in type36["classes"]] == [
            ("0x03", 50), ("0x04", 15), ("0x05", 4), ("0x0e", 16)]
assert scene_components["identified_pairs"] == 9
assert scene_components["unidentified_pairs"] == 0
navigation = fixtures["authority_data"]["navigation"]
assert len(navigation["terrain_resolver"]["records"]) == 6
assert navigation["terrain_resolver"]["implementation_contract"]["handlers"]["6"][
    "selected_entry"] == "0x0b1e9c"
assert navigation["obstacle_response"]["implementation_contract"]["player_geometry"][
    "box"] is None
assert navigation["obstacle_response"]["implementation_contract"]["obstacle_box"][
    "x_half_u8"] == 32
obstacle_lifecycle = navigation["obstacle_response"]["lifecycle_contract"]
assert obstacle_lifecycle["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert obstacle_lifecycle["source_scene_record"]["camera_threshold_u16"] == 688
assert obstacle_lifecycle["initializer"]["child_allocation"]["variant_order_u8"] == [3, 2, 1, 0]
assert obstacle_lifecycle["state_program"]["state_0200"]["source_frame"] == 2804
assert obstacle_lifecycle["lifetimes"]["parent"]["first_frame"] == 2246
assert obstacle_lifecycle["transition_suppression"]["suppressed_writes"] == 18
assert navigation["camera"]["implementation_contract"]["coffee_shop_guard"][
    "fixed_frame_authority"] is False
assert navigation["camera"]["implementation_contract"]["x_target_arithmetic"][
    "speed_table_u16"][-4:] == [11, 11, 11, 11]
button3 = fixtures["authority_data"]["player"][
    "directional_airborne_interruption"]["directional_actions"][
        "implementation_contract"]
assert button3["spec_executable"] is True
assert [entry["x_velocity_s32_16_16"]["raw_s32"]
        for entry in button3["vector_table"]] == [
            0, 0, -0x000f0000, -0x00090000, 0x00090000, 0x00088000]
assert [entry["entry_index"] for entry in button3["input_facing_mapping"][:10]] == [
    0, 1, 2, 4, 4, 2, 3, 5, 5, 3]
assert button3["initialization"]["down"]["collision_selector_u8"] == 7
assert button3["motion_and_landing"]["phase_0x040a"][
    "negative_velocity_transition"]["phase_timer_s16"] == 10
assert any(row["attack_selector_u8"] == 35
           for row in button3["presentation_records"])
assert button3["presentation_actor_fields"]["object_or_u16"] == "0x8000"
assert button3["rng_calls"] == []
scene = fixtures["scene_manifests"]["coffee_shop"]
class1f_inventory = next(row for row in scene["class_type_inventory"]
                         if row["type"] == 12 and row["class"] == "0x1f")
class1f_system = next(row for row in scene["systems"]
                      if row["id"] == "coffee-shop-class1f-current-authority")
assert class1f_inventory["classification"] == "NATIVE_IMPLEMENTED"
assert class1f_inventory["lifetime_count"] == 47
assert class1f_system["classification"] == "NATIVE_IMPLEMENTED"
assert all(row["classification"] == "NATIVE_IMPLEMENTED"
           for row in scene["actor_lifetimes"]
           if row["type"] == 12 and row["class"] == "0x1f")
assert any(row["classification"] == "NATIVE_IMPLEMENTED"
           for row in scene["health_writes"])
assert any(row["classification"] == "BLOCKED_MISSING_SPEC"
           for row in scene["health_writes"])
rebuilt_contract, rebuilt_fixtures = spec02.build_artifacts()
assert spec02.canonical(rebuilt_contract) == spec02.OUT.read_bytes()
assert spec02.canonical(rebuilt_fixtures) == spec02.FIXTURES.read_bytes()

def reject(c, f, label):
    try:
        spec02.validate(c, f)
    except (ValueError, KeyError):
        return
    raise AssertionError(f"SPEC-02 mutation escaped: {label}")

mutations = []
m = copy.deepcopy(contract); m["required_unknown_count"] = 1; mutations.append((m, fixtures, "required unknown"))
m = copy.deepcopy(contract); m["field_contracts"][0]["transition_guard"] = "UNKNOWN fallback"; mutations.append((m, fixtures, "unknown guard"))
m = copy.deepcopy(contract); m["field_contracts"][1]["reads"] = []; mutations.append((m, fixtures, "empty reads"))
m = copy.deepcopy(contract); m["field_contracts"][2]["source"]["evidence_hash"] = "0" * 64; mutations.append((m, fixtures, "wrong evidence hash"))
m = copy.deepcopy(contract); m["field_contracts"][3]["source"]["json_pointer"] = "/missing"; mutations.append((m, fixtures, "missing source pointer"))
m = copy.deepcopy(contract); m["field_contracts"][4]["mutation_control"]["json_pointer"] = "/missing"; mutations.append((m, fixtures, "missing real mutation"))
m = copy.deepcopy(contract); m["coverage_gate"]["orphan_authoritative_writers"] = 1; mutations.append((m, fixtures, "weakened gate"))
f = copy.deepcopy(fixtures); f["authority_data"]["rng"]["algorithm"]["recurrence"] = "guess"; mutations.append((contract, f, "fixture mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["record4_parent_class0"]["child_emitter_state"]["cadence_reload_u8"] = 5; mutations.append((contract, f, "weapon cadence mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["empty_effect_variant1_contract"]["variant"] = 0; mutations.append((contract, f, "empty effect variant mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["empty_effect_variant1_contract"]["initialization"]["presentation_actor_fields"]["object_or_u16"] = "0x0000"; mutations.append((contract, f, "empty effect priority mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["current_state_collision_damage"]["child_contact"]["damage_u8"] = 30; mutations.append((contract, f, "projectile damage lookup mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["current_state_collision_damage"]["registration_and_pair_eligibility"]["visibility"]["x_guard"] = "u16(actor_x - camera_x + 0x0020) <= 0x0200"; mutations.append((contract, f, "projectile collision registration bias mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["current_state_collision_damage"]["registration_and_pair_eligibility"]["identity_writer"]["coffee_shop_counter_before_parent_u8"] = 0x24; mutations.append((contract, f, "projectile collision identity seed mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["current_state_collision_damage"]["registration_and_pair_eligibility"]["mutation_control"]["target_first_contact_frame_after"] = 2306; mutations.append((contract, f, "projectile collision registration control mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["record4_parent_class0"]["initialization"]["object_or_u16"] = "0x0000"; mutations.append((contract, f, "projectile presentation object priority mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["record4_child_class4"]["class_u8"] = 5; mutations.append((contract, f, "projectile child class mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["initial_transition_contract"]["phase_0x1400"]["substates"][1]["writes"]["x_velocity_s32_16_16"] = 0x20000; mutations.append((contract, f, "class1f transition motion mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["initial_transition_contract"]["actors"][0]["coordinate_mode_u8"] = 0; mutations.append((contract, f, "class1f presentation mode mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["initial_transition_contract"]["actors"][0]["palette_u8"] = 15; mutations.append((contract, f, "class1f presentation palette mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["initial_transition_contract"]["actors"][0]["object_or_u16"] = "0x0000"; mutations.append((contract, f, "class1f presentation priority mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["spawn"]["bounded_current_state_dynamic"]["writer_pc"] = "0x06b3fe"; mutations.append((contract, f, "class1f current spawn writer mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["actions"]["approach_0x1600"]["x_delta_s16"] = 110; mutations.append((contract, f, "class1f current movement mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["actions"]["attack_0x1800"]["contact_offsets_u16"][0] = 47; mutations.append((contract, f, "class1f current contact mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["ko_ticks_u16"] = 140; mutations.append((contract, f, "class1f current KO mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["accepted_port_v2_reaction_mapping"]["hit_entry_outer_state_u16"] = 0x0400; mutations.append((contract, f, "class1f reaction mapping mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["reaction_table"]["reaction_selector_actor_4d_u8"] = 0; mutations.append((contract, f, "class1f source HIT selector mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["visible_result"]["animation_record"] = "0x0012dc50"; mutations.append((contract, f, "class1f source HIT record mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["recovery"]["captured_values_before_decrement"][0] = 7; mutations.append((contract, f, "class1f source HIT recovery mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["recovery"]["transition_scheduler_boundary"]["recovery_transition_returns_before_action_dispatch"] = False; mutations.append((contract, f, "class1f source HIT recovery boundary mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["phase_0x0200_launch"]["observed_written_motion"]["x_velocity_s32_16_16"] = -0x1b000; mutations.append((contract, f, "class1f source HIT launch mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["phase_0x0202_first_flight"]["landing_visible_frame"] = 2363; mutations.append((contract, f, "class1f source HIT landing mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["phase_0x0206_bounce"]["observed_motion_after_facing"]["y_acceleration_s32_16_16"] = -0xb000; mutations.append((contract, f, "class1f source HIT bounce mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["rng"]["selected_timer_u8"] = 9; mutations.append((contract, f, "class1f source HIT RNG timer mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["animation_sequences"]["reaction_0x36"]["records"][0]["animation_record"] = "0x0012e410"; mutations.append((contract, f, "class1f source HIT selector-context mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["selector_context_rule"]["generic_action_selector_binding_forbidden"] = False; mutations.append((contract, f, "class1f source HIT generic-selector mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["normal_return"]["class1f_resume_at_2414"] = "0x0200:0000"; mutations.append((contract, f, "class1f source HIT return mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_hit_entry_program"]["source_hit_program"]["normal_return"]["preserved_resume_fields"]["actor_85_style_u8"] = 1; mutations.append((contract, f, "class1f source HIT return predicate mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_projectile_ko_program"]["collision_visible_result"]["outer_state_u16"] = 0x0402; mutations.append((contract, f, "class1f projectile KO collision chronology mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_projectile_ko_program"]["state_program"]["launch"]["y_velocity_s32_16_16"] = 0x97000; mutations.append((contract, f, "class1f projectile KO launch mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["current_state_implementation_contract"]["damage_hit_ko_removal"]["source_projectile_ko_program"]["state_program"]["removal_hold"]["timer_actor_2a_u8"] = 59; mutations.append((contract, f, "class1f projectile KO hold mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["initializer"]["variants"][6]["writes"]["action_u8"] = 18; mutations.append((contract, f, "class1f action variant mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["current_dispatch"]["action_targets"][11]["target"] = "0x060c30"; mutations.append((contract, f, "class1f action target mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["animation_selector_table"]["selectors"][2]["selector_u8"] = 33; mutations.append((contract, f, "class1f action selector mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["movement_tables"][1]["vectors"][8]["x_delta_s16"] = 2047; mutations.append((contract, f, "class1f action movement mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["source_bounds"]["x_max_u16"] = 0x05ef; mutations.append((contract, f, "class1f action source-bound mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["source_bounds"]["activation_field_u8"] = "actor+0x02"; mutations.append((contract, f, "class1f action source-bound activation mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["animation_movement_helper_0x0165c4"]["movement_cadence"] = "every scheduler frame"; mutations.append((contract, f, "class1f action movement cadence mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["direction_helper_0x061032"]["upper_directions_by_a5_u8"][0] = 0x15; mutations.append((contract, f, "class1f action direction mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["action_0x0e"]["z_velocity_table_s32_16_16"][0] = -0x0000f000; mutations.append((contract, f, "class1f action jump mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["action_0x04"]["selector_groups_u16"][2][0] = 44; mutations.append((contract, f, "class1f action attack-selector mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["action_programs"]["action_0x04"]["timer_rows_u8"][1][1] = 7; mutations.append((contract, f, "class1f action4 timer-row mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["attack_timer_table_u8"][4] = 59; mutations.append((contract, f, "class1f action timer mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["suppression_control"]["suppressed_writes"] = 178; mutations.append((contract, f, "class1f action suppression mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["entry_transition"]["writer_pc"] = "0x0610ca"; mutations.append((contract, f, "class1f inner8 writer mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["entry_transition"]["timer_u16"] = 599; mutations.append((contract, f, "class1f inner8 timer mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["movement"]["tables"][0]["vectors"][8]["x_delta_s16"] -= 1; mutations.append((contract, f, "class1f inner8 movement mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["action_0x0e_motion"]["phase_2_terminal"]["x_velocity_by_facing_s32_16_16"].reverse(); mutations.append((contract, f, "class1f inner8 motion-facing mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["type16_emission"]["fixed_frame_spawn_forbidden"] = False; mutations.append((contract, f, "class1f inner8 fixed-frame emission mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["mutation_control"]["mutant_type16_spawn_frames"] = [3253]; mutations.append((contract, f, "class1f inner8 suppression mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["animation_records"][0]["next_animation_record"] = "0x0012d424"; mutations.append((contract, f, "class1f inner8 next-record mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["observed_path_program"]["action_0x00"]["captured_rng_call_counts"]["frame_3004_style_match"] = 3; mutations.append((contract, f, "class1f inner8 chooser RNG mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["observed_path_program"]["action_0x04"]["captured_terminals"]["frame_3134"] = "fixed frame"; mutations.append((contract, f, "class1f inner8 action4 transition mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["observed_path_program"]["action_0x10"]["overlap_transition"]["writer"] = "0x041310"; mutations.append((contract, f, "class1f inner8 action10 writer mutation"))
f = copy.deepcopy(fixtures); next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["first_segment_action_execution_contract"]["inner_state_0x08_program"]["observed_path_program"]["action_0x0e"]["captured_selection"]["motion_selector_96_u16"] = 22; mutations.append((contract, f, "class1f inner8 motion-selector mutation"))
f = copy.deepcopy(fixtures); next(row for row in next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["presentation_and_collision"]["records"] if row["animation_record"] == "0x0012dd50")["assembly"] = "0x0013020c"; mutations.append((contract, f, "class1f HIT presentation mutation"))
f = copy.deepcopy(fixtures); next(row for row in next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["presentation_and_collision"]["records"] if row["animation_record"] == "0x0012e214")["hurt_selector"] = 1; mutations.append((contract, f, "class1f KO selector mutation"))
f = copy.deepcopy(fixtures); next(row for row in next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["presentation_and_collision"]["records"] if row["animation_record"] == "0x0012ec74")["hurt_selector"] = 1; mutations.append((contract, f, "class1f first Button1 target selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["route"]["first_segment_recurring_spawn"]["controller_program"]["initializer"]["limit_table_u16"][1] = 34; mutations.append((contract, f, "encounter controller limit-table mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["route"]["first_segment_recurring_spawn"]["controller_program"]["intro_gate_transition"]["gate_owner"]["writer_successor_pc"] = "0x08da22"; mutations.append((contract, f, "encounter intro-gate writer mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["route"]["first_segment_recurring_spawn"]["intro_gate_suppression_control"]["mutant_at_frame_4100"]["main_spawn_transactions"] = 1; mutations.append((contract, f, "encounter intro-gate suppression mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["route"]["first_segment_recurring_spawn"]["primary_writer"]["rng"]["calls"] = 0; mutations.append((contract, f, "encounter recurring RNG mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["route"]["first_segment_recurring_spawn"]["progress_increment_boundary"]["increment_u16"] = 2; mutations.append((contract, f, "encounter KO progress mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["route"]["first_segment_recurring_spawn"]["source_update_cadence"]["exceptions"][0]["updates_u8"] = 1; mutations.append((contract, f, "Coffee Shop scheduler cadence mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x09_type20_rng_owner"]["selector_table_u16"][0] = 1; mutations.append((contract, f, "class09 RNG selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x4e_type24_variant4_effect"]["allocation_pop_order"].reverse(); mutations.append((contract, f, "class4e allocation-order mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x4e_type24_variant4_effect"]["variant1_collision_effect"]["allocation"]["scheduler_guard"] = "projectile first"; mutations.append((contract, f, "class4e variant1 scheduler mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x4e_type24_variant4_effect"]["variant1_collision_effect"]["allocation"]["fixed_slot_reuse_presentation"]["animation_record"] = "0x00092914"; mutations.append((contract, f, "class4e retained-presentation mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["weapon_projectile_resource"]["implementation_contract"]["record4_parent_class0"]["collision_table"]["attack_entries"][1]["impact_variant_u8"] = 1; mutations.append((contract, f, "class4e variant10 attack-field mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x4e_type24_variant4_effect"]["variant10_collision_effect"]["state0"]["first_seed_after"] = "0xe34d"; mutations.append((contract, f, "class4e variant10 RNG mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["coffee_shop_type36_presentation"]["pool"]["capacity"] = 32; mutations.append((contract, f, "Coffee Shop type36 pool mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["coffee_shop_scene_component_identities"]["unidentified_pairs"] = 1; mutations.append((contract, f, "Coffee Shop component identity mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["terrain_resolver"]["records"][4]["decoded_six_fields"]["z_parameter_s8"] = -8; mutations.append((contract, f, "terrain record sign mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["obstacle_response"]["implementation_contract"]["obstacle_box"]["x_half_u8"] = 16; mutations.append((contract, f, "obstacle box mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["obstacle_response"]["lifecycle_contract"]["source_scene_record"]["camera_threshold_u16"] = 689; mutations.append((contract, f, "obstacle spawn threshold mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["obstacle_response"]["lifecycle_contract"]["initializer"]["child_allocation"]["variant_order_u8"] = [0,1,2,3]; mutations.append((contract, f, "obstacle child order mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["obstacle_response"]["lifecycle_contract"]["transition_suppression"]["suppressed_writes"] = 0; mutations.append((contract, f, "obstacle transition control mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["camera"]["implementation_contract"]["coffee_shop_guard"]["phase2_unlock_guard"] = "frame >= 4992"; mutations.append((contract, f, "camera unlock guard mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["vector_table"][2]["x_velocity_s32_16_16"]["raw_s32"] = -0x000e0000; mutations.append((contract, f, "Button3 vector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["input_facing_mapping"][3]["entry_index"] = 2; mutations.append((contract, f, "Button3 facing map mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["initialization"]["non_down"]["opposite_facing_horizontal"]["collision_level_u8"] = 2; mutations.append((contract, f, "Button3 collision selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["motion_and_landing"]["phase_0x040a"]["negative_velocity_transition"]["phase_timer_s16"] = 9; mutations.append((contract, f, "Button3 timer mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["rng_calls"] = ["guess"]; mutations.append((contract, f, "Button3 RNG mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["presentation_actor_fields"]["object_or_u16"] = "0x0000"; mutations.append((contract, f, "Button3 presentation actor mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["airborne_actions"]["button1"]["record4_class03"]["class_u8"] = 0; mutations.append((contract, f, "airborne Button1 class-3 identity mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["airborne_actions"]["button1"]["record4_class03"]["player_phase_0x0406"]["presentation_selector_u8"] = 17; mutations.append((contract, f, "airborne Button1 player presentation selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["airborne_actions"]["button1"]["record4_class03"]["effect_allocation"]["audio_command"] = "0x0008"; mutations.append((contract, f, "class-3 effect mislabeled as audio"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["airborne_actions"]["button1"]["record4_class03"]["active_state"]["low_nibble_motion_tables_s16"]["1"] = f["authority_data"]["player"]["directional_airborne_interruption"]["airborne_actions"]["button1"]["record4_class03"]["active_state"]["low_nibble_motion_tables_s16"]["1"][:16]; mutations.append((contract, f, "class-3 direction table truncation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["airborne_actions"]["button1"]["record4_class03"]["effect_allocation"]["record_type_u8"] = 36; mutations.append((contract, f, "class-3 effect wrong fixed pool"))
f = copy.deepcopy(fixtures); f["scene_manifests"]["coffee_shop"]["actor_lifetimes"].pop(); mutations.append((contract, f, "Coffee Shop actor omission"))
f = copy.deepcopy(fixtures); f["scene_manifests"]["coffee_shop"]["audio_events"].pop(); mutations.append((contract, f, "Coffee Shop audio omission"))
f = copy.deepcopy(fixtures); f["scene_manifests"]["coffee_shop"]["health_writes"].pop(); mutations.append((contract, f, "Coffee Shop health-write omission"))
f = copy.deepcopy(fixtures); f["scene_manifests"]["coffee_shop"]["actor_lifetimes"][0]["classification"] = "UNKNOWN"; mutations.append((contract, f, "Coffee Shop unknown classification"))
f = copy.deepcopy(fixtures); next(row for row in f["scene_manifests"]["coffee_shop"]["class_type_inventory"] if row["type"] == 12 and row["class"] == "0x1f")["classification"] = "BLOCKED_MISSING_SPEC"; mutations.append((contract, f, "Coffee Shop class1f implementation regression"))
f = copy.deepcopy(fixtures); f["scene_manifests"]["coffee_shop"]["acceptance_gate"]["ready"] = True; mutations.append((contract, f, "Coffee Shop premature acceptance"))
m = copy.deepcopy(contract); m["protected_boundaries"]["physical_saturn"] = "PASS"; mutations.append((m, fixtures, "hardware overclaim"))
m = copy.deepcopy(contract); m["next_card"] = "SALVAGE-08-FRONTEND"; mutations.append((m, fixtures, "frontend bypass"))
for args in mutations:
    reject(*args)
print(f"SPEC-02 Round 1 executable contract: PASS ({len(mutations)} mutations rejected)")
