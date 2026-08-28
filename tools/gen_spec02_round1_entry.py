#!/usr/bin/env python3
"""Generate the bounded native Round 1 entry tables from SPEC-02 fixtures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/spec02_round1_generated_fixtures.json"
CONTRACT = ROOT / "data/spec02_round1_executable_contract.json"
OUT = ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h"

KINDS = (
    "AVSP_ROUND1_ENTRY_SET_POSITION",
    "AVSP_ROUND1_ENTRY_SET_SUBHANDLER",
    "AVSP_ROUND1_ENTRY_SOURCE_18",
    "AVSP_ROUND1_ENTRY_DWELL",
    "AVSP_ROUND1_ENTRY_DWELL",
    "AVSP_ROUND1_ENTRY_SOURCE_16",
    "AVSP_ROUND1_ENTRY_DWELL",
    "AVSP_ROUND1_ENTRY_TERMINATE",
)
LENGTHS = (6, 2, 2, 4, 4, 2, 4, 2)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> str:
    fixtures = json.loads(FIXTURES.read_text(encoding="ascii"))
    body = fixtures["authority_data"]["route"]["first_entry_body"]
    spawns = body["spawn_table"]["rows"]
    player = body["player_entry_script"]
    commands = player["source_program"]["commands"]
    program = bytes.fromhex(player["source_program"]["hex"])
    scheduler = fixtures["authority_data"]["scheduler"]
    scheduler_order = scheduler["frame_scheduler"]["required_round1_order"]
    dispatches = []
    for pool in scheduler["pools"]:
        for dispatch in pool["required_round1_dispatch"]:
            dispatches.append((pool["record_type"], int(dispatch["class"], 16)))
    class1f = next(archetype for archetype in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if archetype["type"] == 12 and archetype["class"] == "0x1f")
    presentation = class1f["presentation_and_collision"]
    presentation_rows = presentation["records"]
    dispatch_entry = int(class1f["dispatch_entry"], 16)
    class1f_initial = class1f["initial_transition_contract"]
    class1f_current = class1f["current_state_implementation_contract"]
    class1f_current_spawn = class1f_current["spawn"]
    class1f_current_actions = class1f_current["actions"]
    class1f_current_damage = class1f_current["damage_hit_ko_removal"]
    class1f_current_reaction = class1f_current_damage[
        "accepted_port_v2_reaction_mapping"]
    class1f_actions = class1f["first_segment_action_execution_contract"]
    action_variants = class1f_actions["initializer"]["variants"]
    action_targets = class1f_actions["current_dispatch"]["action_targets"]
    action_selectors = class1f_actions["animation_selector_table"]["selectors"]
    action_records = [record for sequence in action_selectors
                      for record in sequence["records"]]
    action_movement_tables = class1f_actions["movement_tables"]
    action_attack_timers = class1f_actions["attack_timer_table_u8"]
    action_programs = class1f_actions["action_programs"]
    action_bounds = action_programs["source_bounds"]
    action_direction = action_programs["direction_helper_0x061032"]
    action_zero = action_programs["action_0x00"]
    action_fall = action_programs["action_0x0c"]
    action_jump = action_programs["action_0x0e"]
    action_attack = action_programs["action_0x04"]
    recurring = fixtures["authority_data"]["route"][
        "first_segment_recurring_spawn"]
    recurring_controller = recurring["controller_program"]
    recurring_initializer = recurring_controller["initializer"]
    recurring_gate = recurring_controller["intro_gate_transition"]
    recurring_primary = recurring["primary_writer"]
    recurring_auxiliary = recurring["auxiliary_writer"]
    recurring_tables = recurring_primary["tables"]
    class1f_initial_actors = class1f_initial["actors"]
    class1f_initialization = class1f_initial["initialization"]
    class1f_sequences = class1f_initial["animation_sequences"]
    class1f_phase1400 = class1f_initial["phase_0x1400"]
    class1f_audio_edges = class1f_phase1400["substates"][2]["audio_edges"]
    auxiliary_dependencies = fixtures["authority_data"]["auxiliary"][
        "first_segment_dependencies"]
    class09 = auxiliary_dependencies["class_0x09_type20_rng_owner"]
    class4e = auxiliary_dependencies["class_0x4e_type24_variant4_effect"]
    class44 = auxiliary_dependencies["class_0x44_type24_command_guard_owner"]
    state_contexts = sorted(set(
        tuple(int(part, 16) for part in context.split(":"))
        for context in (class1f["state_phase_contexts"] +
                        class1f_actions["current_dispatch"]
                            ["required_state_contexts"])))
    navigation = fixtures["authority_data"]["navigation"]
    global_bounds = navigation["global_bounds"]
    terrain = navigation["terrain_resolver"]["implementation_contract"]
    terrain_records = terrain["implementation_records"]
    terrain_map = terrain["selection"]["captured_first_segment_map"]
    terrain_selectors = bytes.fromhex(terrain_map["selector_bytes_hex"])
    terrain_grid = terrain["selection"]["bounded_packed_grid"]
    terrain_packed = bytes.fromhex(terrain_grid["packed_bytes_hex"])
    obstacle = navigation["obstacle_response"]["implementation_contract"]
    obstacle_actor = obstacle["source_actor"]
    obstacle_box = obstacle["obstacle_box"]
    camera = navigation["camera"]["implementation_contract"]
    camera_guard = camera["coffee_shop_guard"]
    camera_operands = camera_guard["captured_first_segment_operands"]
    locomotion = fixtures["authority_data"]["player"]["locomotion_neutral_facing"]
    input_decode = locomotion["input_decode"]
    release = locomotion["release_transition"]
    direction_resolver = input_decode["resolver_table"]
    melee = fixtures["authority_data"]["player"]["route_reachable_melee_actions"]
    close_combo = melee["close_combo"]
    melee_dispatch = melee["dispatch"]
    melee_sequences = close_combo["animation_sequences"]
    melee_selectors = close_combo["attack_selectors"]
    melee_steps = close_combo["step_values"]
    melee_strikes = []
    jump = fixtures["authority_data"]["player"][
        "directional_airborne_interruption"]["directional_actions"][
            "implementation_contract"]
    jump_vectors = jump["vector_table"]
    jump_down_vectors = jump["down_vector_table"]
    jump_sequences = jump["presentation_selector_sequences"]
    air_class03 = fixtures["authority_data"]["player"][
        "directional_airborne_interruption"]["airborne_actions"]["button1"][
            "record4_class03"]
    weapon = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    weapon_states = weapon["state_dispatch"]
    weapon_action = weapon["sufficient_action"]
    weapon_resource = weapon["resource_tick"]
    weapon_empty = weapon["empty_fallback"]
    weapon_parent = weapon["record4_parent_class0"]
    weapon_child = weapon["record4_child_class4"]
    weapon_damage = weapon["current_state_collision_damage"]
    weapon_empty_effect = weapon["empty_effect_variant1_contract"]
    weapon_frames = weapon_action["presentation_timeline"]
    empty_frames = weapon_empty["presentation_timeline"]
    weapon_return_frame = dict(weapon_frames[0])
    weapon_return_frame.update({"action_u16": 2, "substate_u8": 2})
    first_segment_bounds = next(
        run for run in global_bounds["baseline_bound_runs"]
        if run["route"] == 4 and run["bound_x"] == 720 and
        run["bound_z"] == 256 and run["frames"] == 333)
    if len(spawns) != 10 or len(commands) != len(KINDS):
        raise ValueError("SPEC-02 entry cardinality drift")
    if [int(row["sequence"]) for row in spawns] != list(range(10)):
        raise ValueError("SPEC-02 entry spawn order drift")
    if sum(LENGTHS) != len(program) or player["timer_semantics"]["loads"] != [60, 60, 44]:
        raise ValueError("SPEC-02 entry program/timer drift")
    if scheduler_order != [12, 16, 20, 24] or len(dispatches) != 16:
        raise ValueError("SPEC-02 Round 1 scheduler/dispatch drift")
    records = [int(row["animation_record"], 16) for row in presentation_rows]
    if (presentation["orphan_records"] != 0 or
        presentation["record_count"] != len(presentation_rows) or
        records != sorted(records) or len(records) != len(set(records))):
        raise ValueError("SPEC-02 class-0x1f presentation table drift")
    if (dispatch_entry != 0x060532 or state_contexts != sorted(state_contexts) or
        len(state_contexts) != len(set(state_contexts))):
        raise ValueError("SPEC-02 class-0x1f state context drift")
    if (class1f_initial["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        len(class1f_initial_actors) != 10 or
        [row["substate_u16"] for row in class1f_initial_actors] !=
            [0x1000] * 3 + [0x1200] * 4 + [0x1400] * 3 or
        [row["entry_delay_u8"] for row in class1f_initial_actors[-3:]] !=
            [9, 3, 16] or
        [row["coordinate_mode_u8"] for row in class1f_initial_actors] !=
            [1] * 10 or
        [row["palette_u8"] for row in class1f_initial_actors] !=
            [16, 17, 17, 18, 17, 16, 18, 17, 19, 19] or
        [row["object_or_u16"] for row in class1f_initial_actors] !=
            ["0x8000"] * 10 or
        class1f_initialization["rng_calls"] != 10 or
        class1f_initialization["rng_seed_after_each_source_slot"][-1] !=
            "0x16b7" or
        [row["selector_u8"] for row in class1f_sequences] !=
            [0, 1, 52, 60, 62, 76] or
        [len(row["records"]) for row in class1f_sequences] !=
            [4, 4, 4, 3, 2, 5] or
        [row["command"] for row in class1f_audio_edges] !=
            ["0x004d", "0x0118"]):
        raise ValueError("SPEC-02 class-0x1f initial transition drift")
    if (class1f_current["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_current["authority_boundary"]
            ["retained_gameplay_authority_forbidden"] is not True or
        class1f_current_spawn["first_dynamic"]["slot"] != "0xff9c40" or
        class1f_current_spawn["first_dynamic"]["writer_pc"] != "0x06b3fe" or
        class1f_current_spawn["bounded_current_state_dynamic"]["slot"] !=
            "0xffa000" or
        class1f_current_spawn["bounded_current_state_dynamic"]["writer_pc"] !=
            "0x028a3e" or
        class1f_current_spawn["controller"]["owner_source_slot"] !=
            "0x00ffb580" or
        class1f_current_spawn["controller"]["writes"][-1] !=
            "owner.timer = 360" or
        class1f_current_actions["approach_0x1600"]["ticks"] != 38 or
        class1f_current_actions["approach_0x1600"]["x_delta_s16"] != 111 or
        class1f_current_actions["approach_0x1600"]["z_delta_s16"] != -23 or
        class1f_current_actions["attack_0x1800"]["contact_offsets_u16"] !=
            [48, 119] or
        class1f_current_actions["attack_0x1800"]["damage_s16"] != 8 or
        class1f_current_damage["damage_by_player_selector_s16"] !=
            [8, 8, 10, 12] or
        class1f_current_damage["hit_ticks_u16"] != 39 or
        class1f_current_damage["ko_ticks_u16"] != 141 or
        class1f_current_reaction["hit_entry_outer_state_u16"] != 0x0202 or
        class1f_current_reaction["hit_entry_action_substate_u16"] != 0x0002 or
        class1f_current_reaction["ko_entry_outer_state_u16"] != 0x0402 or
        class1f_current_reaction["ko_entry_action_substate_u16"] != 0x0000 or
        class1f_current_reaction["terminal_release_outer_state_u16"] != 0x0600):
        raise ValueError("SPEC-02 class-0x1f current-state drift")
    if (class1f_actions["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_actions["capture_identity"]["byte_identical"] is not True or
        len(action_variants) != 10 or
        [row["action_u8"] for row in action_targets] != list(range(0, 32, 2)) or
        action_targets[11]["target"] != "0x060c2e" or
        [row["selector_u8"] for row in action_selectors] !=
            [0, 1, 34, 35, 36, 43, 52, 53, 54, 55, 56, 60, 62, 68, 69, 70,
             71, 72, 73, 74, 76, 77] or
        len(action_records) != 132 or
        [row["table_index_u8"] for row in action_movement_tables] != [1, 8] or
        any(len(row["vectors"]) != 32 for row in action_movement_tables) or
        action_movement_tables[1]["vectors"][8] != {
            "direction_u8": 8, "x_delta_s16": 2048,
            "y_delta_s16": 0} or
        action_bounds != {
            "x_max_u16": 0x05f0,
            "camera_relative_bias_u16": 0x0070,
            "camera_relative_span_u16": 0x0260,
            "failure_outer_state_u16": 0x0600,
            "comparison": "unsigned word"} or
        action_direction["upper_directions_by_a5_u8"] != [0x16, 0x0a] or
        action_direction["lower_directions_by_a5_u8"] != [0x1a, 0x06] or
        action_jump["x_velocity_table_s32_16_16"] !=
            [-0x00010000, -0x00014000, -0x00018000, -0x00020000] or
        action_attack["selector_groups_u16"] !=
            [[55], [56], [43, 43, 43, 55], [43, 43, 56]] or
        action_attack_timers != [30] * 4 + [60] * 4 + [120] * 4 + [160] * 4 or
        class1f_actions["suppression_control"]["writer_pc"] != "0x0607e8" or
        class1f_actions["suppression_control"]["suppressed_writes"] != 179 or
        class1f_actions["suppression_control"]["fixed_frame_substitute"] is not False):
        raise ValueError("SPEC-02 class-0x1f first-segment action drift")
    if (recurring["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        recurring_initializer["limit_table_u16"] != [0, 35, 55, 70] or
        recurring_initializer["observed_after"] != {
            "frame": 2073, "state_u16": 0x0200,
            "timer40_u16": 3900, "timer42_u16": 60,
            "field46_u16": 1200, "field48_u16": 2100,
            "limit_u16": 35, "index_u16": 9,
            "camera_bound_u16": 640} or
        recurring_controller["initial_spawn_transition"]["observed_after"] != {
            "frame": 2074, "living_enemy_count_u16": 10,
            "state_u16": 0x0202} or
        recurring_gate["gate_owner"]["record"] != "0xffc580" or
        recurring_gate["gate_owner"]["record_type_u8"] != 24 or
        recurring_gate["gate_owner"]["class_u8"] != "0x44" or
        recurring_gate["gate_owner"]["state_u16"] != 0x0404 or
        recurring_gate["gate_owner"]["writer_successor_pc"] != "0x08da38" or
        recurring_gate["write_values"] != {
            "source_camera_target_u16": 208,
            "camera_x_call_threshold_s16": 720,
            "conditional_phase_0x2e_u8": 1,
            "conditional_local_0x2c_u8": 0} or
        recurring["intro_gate_suppression_control"]["mutant_at_frame_4100"] != {
            "state_u16": 0x0202, "timer42_u16": 60,
            "intro_gate_u8": 0xff, "main_spawn_transactions": 0,
            "aux_spawn_transactions": 0} or
        recurring_primary["guard_branch_order"][0] !=
            "require living_enemy_count_u16 at 0xff1a18 < 8" or
        recurring_primary["guard_values"] != {
            "living_limit_u16": 8, "phase_mask_u8": 7} or
        recurring_primary["position_values"] != {
            "x_camera_offset_s16": -48, "lane_base_s16": 208,
            "lane_band_mask_u16": 0x00f0} or
        recurring_primary["rng"]["calls"] != 1 or
        recurring_tables["lane_offsets_s16"] != [24, 40, 56, 72, 88, 104] or
        recurring_tables["selector_cycle_u8"] != [0, 1, 1, 1, 0, 1, 0, 1, 1, 1] or
        len(recurring_tables["lane_bucket_u8"]) != 64 or
        recurring_tables["lane_bucket_u8"][48:] != [3] * 16 or
        len(recurring_tables["variant_u8"]) != 96 or
        recurring_auxiliary["guard_values"] != {
            "camera_x_limit_s16": 1008, "phase_add_u8": 3,
            "phase_mask_u8": 31} or
        recurring_auxiliary["write_values"] != {
            "class_u8": 0x1f, "variant_u8": 4, "timer_u16": 0,
            "x_s16": 976, "y_s16": 344, "z_s16": 344,
            "selector83_u8": 0} or
        recurring_auxiliary["rng_calls"] != 0):
        raise ValueError("SPEC-02 first-segment recurring spawn drift")
    if (auxiliary_dependencies["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        len(class09["source_slots"]) != 2 or
        class09["selector_table_u16"] != [0, 7, 8, 9, 10, 8, 9, 10] or
        class09["first_segment_calls_before_class4e"] != 44 or
        len(class09["animation_sequences"]) != 5 or
        any(len(row["records"]) != 2 for row in class09["animation_sequences"]) or
        class4e["allocation_pop_order"] !=
            ["0x00ffc500", "0x00ffc480"] or
        class4e["scheduler_order"] !=
            ["0x00ffc480", "0x00ffc500"] or
        [row["table_index"] for row in class4e["seed_after_by_scheduler_slot"]] !=
            [28, 24] or len(class4e["jitter_table_s16"]) != 8 or
        len(class4e["animation_records"]) != 5 or
        class44["dispatch"] != "0x08d9a4" or
        class44["source_slot"] != "0x00ffc580" or
        class44["state_sequence_u16"] != [0x0200, 0x0400, 0x0402, 0x0404] or
        class44["state0_presentation_actor"] != {
            "coordinate_mode_u8": 0, "palette_u8": 0, "facing_u8": 0,
            "object_or_u16": "0x8000", "object_or_writer_pc": "0x08d9d8",
            "object_or_write_frame": 2072,
            "object_or_write_mask": "0x0000ffff",
            "zero_fields_source": "accepted zero-initialized type-24 record; generic allocation writes preserve coordinate mode, palette and facing at zero"} or
        len(class44["animation_records"]) != 2 or
        class44["guard_clear_frame"] != 2250 or
        class44["second_player_origin_command_frame"] != 2255):
        raise ValueError("SPEC-02 first-segment actor dependency drift")
    if (global_bounds["x_min"] != "bound_x + 0x20" or
        global_bounds["x_max"] != "bound_x + 0x160" or
        global_bounds["z_min"] != "bound_z + 0x10" or
        global_bounds["z_max"] != "bound_z + 0x90" or
        navigation["coordinate_contract"]["up_world_z_delta_sign"] != 1 or
        navigation["coordinate_contract"]["down_world_z_delta_sign"] != -1):
        raise ValueError("SPEC-02 first-segment global bounds drift")
    if (terrain["classification"] != "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        terrain["selection"]["cell_address"] !=
            "0x904000 + (((~world_z)&0x0300)<<4) + (((~world_z)&0x00f0)>>2) + ((world_x<<2)&0x0fc0)" or
        len(terrain_selectors) != 0x1000 or
        hashlib.sha256(terrain_selectors).hexdigest() !=
            terrain_map["selector_sha256"] or
        terrain_grid["classification"] != "SOURCE_DERIVED_CONTENT_DATA" or
        terrain_grid["world_x_inclusive"] != [640, 1360] or
        terrain_grid["world_z_inclusive"] != [272, 400] or
        terrain_grid["tile_size"] != 16 or
        terrain_grid["width"] != 46 or terrain_grid["height"] != 9 or
        terrain_grid["cell_count"] != 414 or
        terrain_grid["bits_per_cell"] != 2 or
        terrain_grid["selector_code_u8"] != [0, 24, 56] or
        terrain_grid["packed_bytes"] != 104 or len(terrain_packed) != 104 or
        hashlib.sha256(terrain_packed).hexdigest() !=
            terrain_grid["packed_sha256"] or
        [row["selector_u8"] for row in terrain_records] !=
            [0, 8, 24, 56, 96, 100, 164] or
        [row["record_bytes"] for row in terrain_records] != [
            "0080808080808080", "0202808010100080",
            "020280801010ff80", "0202808010080080",
            "0604020100008080",
            "0604020100088080", "0402020100088080"]):
        raise ValueError("SPEC-02 Coffee Shop terrain implementation drift")
    if (obstacle_actor != {
            "animation_record": "0x06e136", "assembly": "0x06e196",
            "attack_selector_u8": 1, "class": "0x0a", "facing_u8": 0,
            "hurt_selector_u8": 1,
            "position_s16": {"x": 1123, "y": 323, "z": 323},
            "slot": "0xffb380", "state_u16": 0x0200,
            "substate_u16": 0, "table_set": "0x06e210", "type": 20} or
        obstacle["player_geometry"]["classification"] != "SOURCE_POINT_PROBE" or
        obstacle_box != {
            "address": "0x06e22c", "flags_u16": 0xff00,
            "x_center_s8": 0, "x_half_u8": 32,
            "y_center_s8": 0, "y_half_u8": 127,
            "z_center_s8": 0, "z_half_u8": 6} or
        obstacle["minimum_penetration"]["axis_guard"] !=
            "resolve z only when unsigned z_penetration < unsigned x_penetration; otherwise resolve x"):
        raise ValueError("SPEC-02 Coffee Shop obstacle implementation drift")
    if (camera["x_target_arithmetic"]["speed_table_u16"] !=
            [0, 1, 1, 2, 3, 4, 5, 6, 7, 7,
             8, 8, 9, 9, 10, 10, 11, 11, 11, 11] or
        camera_operands != {
            "countdown_initial_u16": 1200,
            "countdown_tick_rule":
                "decrement once per controller update while phase is 2",
            "counter_u16": 0, "snapshot_u16": 0,
            "threshold_byte_u8": 1, "threshold_ticks": 16} or
        camera_guard["fixed_frame_authority"] is not False or
        camera["world_to_plane_order"]["raw_pattern_name_offset_forbidden"]
            is not True):
        raise ValueError("SPEC-02 Coffee Shop camera implementation drift")
    if (direction_resolver != [255, 2, 6, 255, 4, 3, 5, 255,
                              0, 1, 7, 255, 255, 255, 255, 255] or
        release["walking_action"] != "0x0202" or
        release["stop_action"] != "0x0204" or
        release["stop_timer"]["ticks"] != 10 or
        release["stop_guard"] !=
            "+0x0c direction becomes negative when no valid direction is held" or
        release["cleanup_writer"] !=
            "0x01a3fa writes inner/action long 0x02000000" or
        release["idle_phase_writer"] !=
            "0x0198de writes action low byte 0x02 on the next update" or
        release["facing_rule"] !=
            "neutral performs no +0x0f write and preserves the last directional facing"):
        raise ValueError("SPEC-02 locomotion-to-neutral transition drift")
    if (melee["classification"] != "SOURCE_CLOSED" or
        melee["input_guard"] !=
            "new Button2 edge from actor +0xee/+0xef bit 5" or
        melee_dispatch["common_action"] != "0x0600" or
        melee_dispatch["target_context_action"] != "0x1400" or
        melee_dispatch["target_context_guard"] != "actor +0x5a nonzero" or
        close_combo["entry"] != "0x022588" or
        close_combo["followup_window"]["ticks"] != 30 or
        close_combo["held_input_rule"] !=
            "held Button2 does not create a new edge or auto-chain" or
        melee_selectors != [1, 2, 3, 4] or melee_steps != [0, 1, 2, 3] or
        melee["rng_consumption"] !=
            "none for selector or assembly choice; state selects the measured animation record"):
        raise ValueError("SPEC-02 route-reachable melee contract drift")
    for selector in melee_selectors:
        sequence = melee_sequences[f"close_{selector}"]
        strikes = [row for row in sequence
                   if row["attack_selector"] == selector]
        if len(strikes) != 1:
            raise ValueError("SPEC-02 melee strike presentation drift")
        melee_strikes.append(strikes[0])
    if (jump["spec_executable"] is not True or
        jump["source_input"]["button3_mask_u8"] != "0x40" or
        jump["branch_order"] != [
            "down bit", "horizontal bits", "up bit",
            "horizontal direction versus facing", "facing sign transform"] or
        len(jump_vectors) != 6 or
        [row["x_velocity_s32_16_16"]["raw_s32"]
         for row in jump_vectors] !=
            [0, 0, -0x000f0000, -0x00090000, 0x00090000, 0x00088000] or
        [row["x_acceleration_s32_16_16"]["raw_s32"]
         for row in jump_vectors] !=
            [0, 0, 0x00006800, 0x00002400, -0x00002000, -0x00002400] or
        [row["z_velocity_s32_16_16"]["raw_s32"]
         for row in jump_vectors] !=
            [0x00088000, 0x000c0000, 0x00040000,
             0x000c0000, 0x00040000, 0x000c0000] or
        [row["z_acceleration_s32_16_16"]["raw_s32"]
         for row in jump_vectors] !=
            [-0x00008000, -0x00008000, -0x00003800,
             -0x00008800, -0x00008000, -0x00008800] or
        jump_down_vectors["vertical_only"]["x_velocity_s32_16_16"]["raw_s32"] !=
            0x00060000 or
        jump_down_vectors["vertical_only"]["x_acceleration_s32_16_16"]["raw_s32"] !=
            -0x00008000 or
        jump_down_vectors["with_horizontal"]["x_velocity_s32_16_16"]["raw_s32"] !=
            0x000c0000 or
        jump_down_vectors["with_horizontal"]["x_acceleration_s32_16_16"]["raw_s32"] !=
            -0x0000a000 or
        sorted(int(key) for key in jump_sequences) !=
            [3, 4, 5, 6, 10, 15, 41, 42, 60] or
        [len(jump_sequences[str(selector)]) for selector in
         (3, 4, 5, 6, 10, 15, 41, 42, 60)] !=
            [2, 5, 7, 8, 2, 3, 2, 1, 1] or
        jump["initialization"]["non_down"][
            "opposite_facing_horizontal"]["collision_level_u8"] != 8 or
        jump["initialization"]["down"]["collision_selector_u8"] != 7 or
        jump["motion_and_landing"]["landing_0x023630"][
            "presentation_selector_u8"] != 10 or
        jump["motion_and_landing"]["phase_0x040a"][
            "negative_velocity_transition"]["phase_timer_s16"] != 10 or
        jump["presentation_actor_fields"] != {
            "coordinate_mode_u8": 0, "palette_u8": 0,
            "object_or_u16": "0x8000",
            "source_fields": {"coordinate_mode": "actor +0x0d u8",
                              "palette": "actor +0x0e u8",
                              "facing": "actor +0x0f u8",
                              "object_or": "actor +0x2e u16"},
            "capture_scope": ["neutral", "right", "left", "up", "down"]} or
        jump["rng_calls"] != []):
        raise ValueError("SPEC-02 Button3 implementation contract drift")
    if (weapon["classification"] != "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        weapon["implementation_blocker"] is not None or
        weapon["source_input"]["button1_mask"] != "0x0010" or
        weapon_states != {
            "sufficient_entry_action": "0x0c00",
            "sufficient_active_action": "0x0c02 then 0x0c04",
            "empty_entry_action": "0x1a00",
            "empty_active_action": "0x1a02",
            "cleanup_action": "0x0000",
            "return_locomotion_action": "0x0002"} or
        weapon_action["entry_tick"] != 0 or
        weapon_action["cleanup_tick"] != 19 or
        weapon_action["return_tick"] != 20 or
        weapon_action["resource_debit_u8"] != 40 or
        weapon_action["resource_clamp_min_u8"] != 0 or
        weapon_action["resource_capacity_u8"] != 64 or
        weapon_action["recharge_countdown_after_entry_u8"] != 12 or
        weapon_action["rng_calls"] != [] or
        weapon_resource["normal_recharge_reload_u8"] != 2 or
        weapon_resource["depleted_recharge_reload_u8"] != 6 or
        weapon_empty["timer_type"] != "u8" or
        weapon_empty["timer_initial"] != 16 or
        weapon_empty["cleanup_tick"] != 17 or
        weapon_empty["return_tick"] != 18 or
        weapon_empty["damaging_record4_count"] != 0):
        raise ValueError("SPEC-02 corrected Predator Button1 action/resource drift")
    if (weapon_parent["spec_executable"] is not True or
        weapon_child["spec_executable"] is not True or
        weapon_empty_effect["spec_executable"] is not True or
        weapon_parent["record_type_u8"] != 4 or
        weapon_parent["class_u8"] != 0 or
        weapon_parent["allocator"] != "0x01773e" or
        weapon_parent["dispatch"] != "0x02f870" or
        weapon_parent["state_sequence_u8"] != [0, 2, 4, 6] or
        weapon_parent["collision_table"]["table"] != "0x0002fc3c" or
        weapon_child["record_type_u8"] != 4 or
        weapon_child["class_u8"] != 4 or
        weapon_child["dispatch"] != "0x0306fe" or
        weapon_child["state_sequence_u8"] != [0, 2, 4] or
        weapon_child["collision_table"]["table"] != "0x00030cb6"):
        raise ValueError("SPEC-02 corrected Predator projectile identity drift")
    parent_init = weapon_parent["initialization"]
    parent_active = weapon_parent["active_state"]
    parent_emitter = weapon_parent["child_emitter_state"]
    parent_presentations = parent_init["presentation_records"]
    parent_selector_offsets = parent_init["selector_offsets_s16"]
    parent_route_angles = sorted(
        int(value) for value in parent_active["route_motion_vectors_s16"]["low"])
    parent_motion_low = parent_active["route_motion_vectors_s16"]["low"]
    parent_motion_high = parent_active["route_motion_vectors_s16"]["high"]
    parent_child_rows = parent_emitter["normal_rows"]
    parent_collision_child_rows = parent_emitter["collision_rows"]
    air_class03_init = air_class03["initialization"]
    air_class03_active = air_class03["active_state"]
    air_class03_emitter = air_class03["child_emitter_state"]
    air_class03_player_phase = air_class03["player_phase_0x0406"]
    air_class03_offsets = air_class03_init["selector_offsets_s16"]
    air_class03_presentations = air_class03_init["presentation_records"]
    air_class03_motion_low = air_class03_active[
        "low_nibble_motion_tables_s16"]
    air_class03_motion_high = air_class03_active[
        "high_nibble_motion_tables_s16"]
    air_class03_child_rows = air_class03_emitter["normal_rows"]
    air_class03_collision_child_rows = air_class03_emitter["collision_rows"]
    child_init = weapon_child["initialization"]
    child_sequences = child_init["variant_presentation_sequences"]
    parent_boxes = weapon_parent["collision_table"]
    child_boxes = weapon_child["collision_table"]
    parent_attack_boxes = parent_boxes["attack_entries"]
    child_attack_boxes = child_boxes["attack_entries"]
    empty_effect_offsets = weapon_empty_effect["initialization"]["variant_offsets_s16"]
    empty_effect_records = weapon_empty_effect["active_state"]["presentation_records"]
    if (len(parent_presentations) != 7 or
        len(parent_selector_offsets) != 6 or
        parent_route_angles != [17, 35, 47] or
        any(len(parent_motion_low[str(angle)]) != 16
            for angle in parent_route_angles) or
        any(len(parent_motion_high[str(angle)]) != 13
            for angle in parent_route_angles) or
        len(parent_child_rows) != 5 or
        len(parent_collision_child_rows) != 5 or
        [len(child_sequences[str(index)]) for index in range(3)] !=
            [17, 10, 16] or
        len(parent_attack_boxes) != 3 or len(child_attack_boxes) != 3 or
        len(empty_effect_offsets) != 4 or
        len(empty_effect_records) != 10):
        raise ValueError("SPEC-02 corrected projectile/effect cardinality drift")
    if (air_class03["spec_executable"] is not True or
        air_class03["record_type_u8"] != 4 or
        air_class03["class_u8"] != 3 or
        air_class03["dispatch"] != "0x030382" or
        air_class03["state_sequence_u8"] != [0, 2, 4, 6] or
        air_class03_active["direction_index_range_u8"] != [0, 63] or
        air_class03_active["vectors_per_motion_table"] != 64 or
        sorted(map(int, air_class03_motion_low)) != list(range(1, 16)) or
        sorted(map(int, air_class03_motion_high)) != list(range(1, 13)) or
        any(len(rows) != 64 for rows in air_class03_motion_low.values()) or
        any(len(rows) != 64 for rows in air_class03_motion_high.values()) or
        len(air_class03_offsets) != 7 or
        len(air_class03_presentations) != 8 or
        len(air_class03_child_rows) != 5 or
        len(air_class03_collision_child_rows) != 5 or
        air_class03_player_phase["presentation_selector_u8"] != 18 or
        len(air_class03_player_phase["presentation_records"]) != 5 or
        air_class03_emitter["cadence_reload_u8"] != 4 or
        air_class03["effect_allocation"]["record_type_u8"] != 24 or
        air_class03["effect_allocation"]["variant_u8"] != 1 or
        air_class03["effect_allocation"]["timer_u8"] != 8 or
        air_class03["effect_allocation"]["audio_command"] is not None):
        raise ValueError("SPEC-02 airborne Button1 class-3 contract drift")
    if (parent_init["object_or_u16"] != "0x8000" or
        child_init["object_or_u16"] != "0x8000" or
        parent_emitter["initial_cadence_u8"] != 1 or
        parent_emitter["cadence_reload_u8"] != 6 or
        parent_emitter["initial_child_count_u8"] != 5 or
        parent_emitter["spawn_ticks_from_parent_state4"] != [1, 7, 13, 19, 25] or
        weapon_damage["parent_contact"]["attack_selector_u8"] != 25 or
        weapon_damage["parent_contact"]["damage_u8"] != 127 or
        weapon_damage["child_contact"]["attack_selector_u8"] != 14 or
        weapon_damage["child_contact"]["damage_u8"] != 31):
        raise ValueError("SPEC-02 corrected projectile collision/damage drift")
    if ([row["tick"] for row in weapon_frames] != list(range(20)) or
        [row["tick"] for row in empty_frames] != list(range(18)) or
        weapon_frames[0]["action_u16"] != 0x0c00 or
        any(row["action_u16"] not in (0x0c02, 0x0c04)
            for row in weapon_frames[1:19]) or
        weapon_frames[19]["action_u16"] != 0 or
        empty_frames[0]["action_u16"] != 0x1a00 or
        any(row["action_u16"] != 0x1a02 for row in empty_frames[1:17]) or
        empty_frames[17]["action_u16"] != 0 or
        weapon_return_frame["action_u16"] != 2 or
        weapon_return_frame["substate_u8"] != 2 or
        weapon_return_frame["animation_record"] != "0x0015f1f4" or
        weapon_return_frame["assembly"] != "0x001626a4"):
        raise ValueError("SPEC-02 corrected Predator presentation timeline drift")

    cursor = int(player["initial_cursor"], 16)
    step_rows = []
    for index, (command, kind, length) in enumerate(zip(commands, KINDS, LENGTHS)):
        opcode = int(command["opcode"], 16)
        args = bytes.fromhex(command["arguments_hex"])
        encoded = bytes([opcode]) + args
        if encoded != program[cursor - int(player["initial_cursor"], 16):
                              cursor - int(player["initial_cursor"], 16) + length]:
            raise ValueError(f"SPEC-02 entry command {index} encoding drift")
        if len(encoded) != length:
            raise ValueError(f"SPEC-02 entry command {index} length drift")
        arg0 = arg1 = arg2 = 0
        if kind == "AVSP_ROUND1_ENTRY_SET_POSITION":
            arg0 = int(player["position"]["x"])
            arg1 = int(player["position"]["z"])
        elif kind == "AVSP_ROUND1_ENTRY_SET_SUBHANDLER":
            arg0 = 8
        elif kind == "AVSP_ROUND1_ENTRY_SOURCE_18":
            arg0 = args[0]
        elif kind == "AVSP_ROUND1_ENTRY_DWELL":
            arg0 = args[0]
            arg1 = int.from_bytes(args[1:3], "big")
        elif kind == "AVSP_ROUND1_ENTRY_SOURCE_16":
            arg0 = args[0]
        step_rows.append((kind, opcode, arg0, arg1, arg2, cursor, cursor + length))
        cursor += length
    if cursor != int(player["source_program"]["last_exclusive"], 16):
        raise ValueError("SPEC-02 entry terminal cursor drift")

    lines = [
        "#ifndef AVSP_SPEC02_ROUND1_ENTRY_DATA_H",
        "#define AVSP_SPEC02_ROUND1_ENTRY_DATA_H",
        "",
        f"/* contract_sha256={sha(CONTRACT)} */",
        f"/* fixtures_sha256={sha(FIXTURES)} */",
        f"#define AVSP_ROUND1_ENTRY_PROGRAM_SHA256 \"{player['source_program']['sha256']}\"",
        "",
        "static const unsigned char avsp_round1_entry_program[AVSP_ROUND1_ENTRY_PROGRAM_BYTES] =",
        "{",
    ]
    for offset in range(0, len(program), 13):
        chunk = ", ".join(f"0x{value:02X}u" for value in program[offset:offset + 13])
        lines.append(f"    {chunk}{',' if offset + 13 < len(program) else ''}")
    lines.extend(["};", "", "static const AvspRound1EntrySpawnSpec avsp_round1_entry_spawns[AVSP_ROUND1_FIRST_SPAWN_COUNT] =", "{"])
    for row in spawns:
        post = row["post_initial_dispatch"]
        lines.append(
            "    { %su, %du, %d, %d, %d, 0x%02Xu, %du, %du, %du, %du, %du, %su, %d }," % (
                row["slot"], row["record_type"], row["x"], row["y"], row["z"],
                int(row["class"], 16), row["variant"], row["source_action"],
                post["state"], post["substate"], post["facing"],
                post["animation_record"], post["health"]))
    lines.extend(["};", "", "static const AvspRound1EntryStepSpec avsp_round1_entry_steps[AVSP_ROUND1_ENTRY_STEP_COUNT] =", "{"])
    for kind, opcode, arg0, arg1, arg2, first, last in step_rows:
        lines.append(
            f"    {{ {kind}, 0x{opcode:02X}u, {arg0}u, {arg1}u, {arg2}u, 0x{first:08X}UL, 0x{last:08X}UL }},")
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_scheduler_pool_order[AVSP_ROUND1_SCHEDULER_POOL_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in scheduler_order),
        "};", "",
        "static const AvspRound1DispatchSpec avsp_round1_required_dispatches[AVSP_ROUND1_REQUIRED_DISPATCH_COUNT] =",
        "{",
    ])
    for record_type, actor_class in dispatches:
        lines.append(f"    {{ {record_type}u, 0x{actor_class:02X} }},")
    lines.extend([
        "};", "",
        f"#define AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT {len(presentation_rows)}u",
        "static const AvspRound1PresentationSpec avsp_round1_class1f_presentation[AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in presentation_rows:
        lines.append(
            "    { %sUL, %sUL, %du, %du }," % (
                row["animation_record"], row["assembly"],
                row["hurt_selector"], row["attack_selector"]))
    lines.extend([
        "};", "",
        f"#define AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY 0x{dispatch_entry:06X}UL",
        f"#define AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT {len(state_contexts)}u",
        "static const AvspRound1StateContextSpec avsp_round1_class1f_state_contexts[AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT] =",
        "{",
    ])
    for state, substate in state_contexts:
        lines.append(f"    {{ 0x{state:04X}u, 0x{substate:04X}u }},")
    current_initial = class1f_current_spawn["initial_actor"]
    approach_current = class1f_current_actions["approach_0x1600"]
    attack_current = class1f_current_actions["attack_0x1800"]
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fCurrentSpec avsp_round1_class1f_current =",
        "{",
        "    %sUL, %sUL, 20u, 0x01, %d, %d, %d, %d, %d, %d, %du, %du, %du, %du, %du, %du, %du," % (
            class1f_current_spawn["controller"]["owner_source_slot"],
            class1f_current_spawn["bounded_current_state_dynamic"]["slot"],
            current_initial["x_s16"], current_initial["y_s16"],
            current_initial["z_s16"], current_initial["health_s16"],
            approach_current["x_delta_s16"], approach_current["z_delta_s16"],
            approach_current["ticks"], attack_current["timer_u16"],
            attack_current["contact_offsets_u16"][0],
            attack_current["contact_offsets_u16"][1],
            attack_current["damage_s16"],
            class1f_current_damage["hit_ticks_u16"],
            class1f_current_damage["ko_ticks_u16"]),
        "    { " + ", ".join(f"{value}u" for value in
            class1f_current_damage["damage_by_player_selector_s16"]) + " },",
        "};", "",
        "static const AvspRound1RecurringSpawnSpec avsp_round1_recurring_spawn =",
        "{",
        "    0x0200u, 0x0202u, 0x0204u,",
        "    %du, %du, %du, %du, %du, %du, %d, %du," % (
            recurring_initializer["observed_after"]["timer40_u16"],
            recurring_initializer["observed_after"]["timer42_u16"],
            recurring_initializer["observed_after"]["field46_u16"],
            recurring_initializer["observed_after"]["field48_u16"],
            recurring_initializer["observed_after"]["camera_bound_u16"],
            recurring_gate["write_values"]["source_camera_target_u16"],
            recurring_gate["write_values"]["camera_x_call_threshold_s16"],
            recurring_initializer["observed_after"]["index_u16"]),
        "    { " + ", ".join(f"{value}u" for value in
            recurring_initializer["limit_table_u16"]) + " },",
        "    0x%02Xu, %du, %du, %du, %du," % (
            recurring["phase_counter"]["stable_entry_value_u8"],
            recurring_primary["guard_values"]["living_limit_u16"],
            recurring_primary["guard_values"]["phase_mask_u8"],
            recurring_auxiliary["guard_values"]["phase_add_u8"],
            recurring_auxiliary["guard_values"]["phase_mask_u8"]),
        "    %d, %d, %d, %d, %d, %du, %du," % (
            recurring_primary["position_values"]["x_camera_offset_s16"],
            recurring_auxiliary["guard_values"]["camera_x_limit_s16"],
            recurring_auxiliary["write_values"]["x_s16"],
            recurring_auxiliary["write_values"]["y_s16"],
            recurring_auxiliary["write_values"]["z_s16"],
            recurring_auxiliary["write_values"]["variant_u8"],
            recurring_auxiliary["write_values"]["selector83_u8"]),
        "    %du, %du, 0x%04Xu, 0x%02X, %du, 0x%04Xu" % (
            recurring_gate["write_values"]["conditional_phase_0x2e_u8"],
            recurring_gate["write_values"]["conditional_local_0x2c_u8"],
            int(recurring_gate["gate_owner"]["record"], 16) & 0xffff,
            int(recurring_gate["gate_owner"]["class_u8"], 16),
            recurring_gate["gate_owner"]["record_type_u8"],
            recurring_gate["gate_owner"]["state_u16"]),
        "};", "",
        "static const short avsp_round1_recurring_lane_offsets[AVSP_ROUND1_RECURRING_LANE_OFFSET_COUNT] =",
        "{",
        "    " + ", ".join(str(value) for value in
            recurring_tables["lane_offsets_s16"]),
        "};", "",
        "static const unsigned char avsp_round1_recurring_selector_cycle[AVSP_ROUND1_RECURRING_SELECTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in
            recurring_tables["selector_cycle_u8"]),
        "};", "",
        "static const unsigned char avsp_round1_recurring_lane_buckets[AVSP_ROUND1_RECURRING_LANE_BUCKET_COUNT] =",
        "{",
    ])
    for offset in range(0, len(recurring_tables["lane_bucket_u8"]), 16):
        chunk = recurring_tables["lane_bucket_u8"][offset:offset + 16]
        lines.append("    " + ", ".join(f"{value}u" for value in chunk) +
                     ("," if offset + 16 < len(recurring_tables["lane_bucket_u8"]) else ""))
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_recurring_variants[AVSP_ROUND1_RECURRING_VARIANT_COUNT] =",
        "{",
    ])
    for offset in range(0, len(recurring_tables["variant_u8"]), 16):
        chunk = recurring_tables["variant_u8"][offset:offset + 16]
        lines.append("    " + ", ".join(f"{value}u" for value in chunk) +
                     ("," if offset + 16 < len(recurring_tables["variant_u8"]) else ""))
    lines.extend([
        "};", "",
        "static const unsigned long avsp_round1_class1f_approach_records[AVSP_ROUND1_CLASS1F_APPROACH_RECORD_COUNT] =",
        "{",
        "    " + ", ".join(f"{row['animation_record']}UL" for row in
            approach_current["records"]),
        "};", "",
        "static const unsigned long avsp_round1_class1f_attack_records[AVSP_ROUND1_CLASS1F_ATTACK_RECORD_COUNT] =",
        "{",
        "    " + ", ".join(f"{row['animation_record']}UL" for row in
            attack_current["records"]),
        "};", "",
        "static const AvspRound1Class1fActionTargetSpec avsp_round1_class1f_action_targets[AVSP_ROUND1_CLASS1F_ACTION_TARGET_COUNT] =",
        "{",
    ])
    for row in action_targets:
        lines.append("    { %du, %sUL }," % (
            row["action_u8"], row["target"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fActionVariantSpec avsp_round1_class1f_action_variants[AVSP_ROUND1_CLASS1F_ACTION_VARIANT_COUNT] =",
        "{",
    ])
    for row in action_variants:
        writes = row["writes"]
        flags = 0
        if "action_u8" in writes:
            flags |= 0x01
        if "airborne_u8" in writes:
            flags |= 0x02
        if "style85_u8" in writes:
            flags |= 0x04
        if "animation_selector_u8" in writes:
            flags |= 0x08
        if writes.get("timer_aa_u8") == 216:
            flags |= 0x10
        elif writes.get("timer_aa_u8") == "entry_delay_u8":
            flags |= 0x20
        if "animation_selector_rule" in writes:
            flags |= 0x40
        if "bound_b2_u16" in writes:
            flags |= 0x80
        style = writes.get("style85_u8", 0)
        if not isinstance(style, int):
            style = 0
        lines.append(
            "    { %du, %du, %du, %du, %du, %du, %du, %du, %du, 0x%02Xu, 0x%04Xu }," % (
                row["variant_u8"], writes.get("a4_u8", 0),
                writes.get("a5_u8", 0), writes.get("a6_u8", 0),
                writes.get("action_u8", 0), writes.get("airborne_u8", 0),
                style, writes.get("animation_selector_u8", 0),
                writes.get("timer_aa_u8", 0)
                    if isinstance(writes.get("timer_aa_u8", 0), int) else 0,
                flags, 0x0420 if "bound_b2_u16" in writes else 0))
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fActionSelectorSpec avsp_round1_class1f_action_selectors[AVSP_ROUND1_CLASS1F_ACTION_SELECTOR_COUNT] =",
        "{",
    ])
    first_record = 0
    for sequence in action_selectors:
        lines.append("    { %du, %du, %du }," % (
            sequence["selector_u8"], first_record, len(sequence["records"])))
        first_record += len(sequence["records"])
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fActionRecordSpec avsp_round1_class1f_action_records[AVSP_ROUND1_CLASS1F_ACTION_RECORD_COUNT] =",
        "{",
    ])
    for row in action_records:
        lines.append(
            "    { %sUL, %sUL, %sUL, %du, %d, %du, %du, %du }," % (
                row["animation_record"], row["next_animation_record"],
                row["assembly"], row["timer_u16"], row["branch_s16"],
                row["hurt_selector_u8"], row["attack_selector_u8"],
                row["movement_table_index_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fMovementTableSpec avsp_round1_class1f_movement_tables[AVSP_ROUND1_CLASS1F_MOVEMENT_TABLE_COUNT] =",
        "{",
    ])
    for table in action_movement_tables:
        vectors = ", ".join("{ %d, %d }" % (
            row["x_delta_s16"], row["y_delta_s16"])
            for row in table["vectors"])
        lines.append("    { %du, { %s } }," % (
            table["table_index_u8"], vectors))
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_class1f_attack_timers[AVSP_ROUND1_CLASS1F_ATTACK_TIMER_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in action_attack_timers),
        "};", "",
        "static const AvspRound1Class1fActionProgramSpec avsp_round1_class1f_action_program =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu," % (
            action_bounds["x_max_u16"],
            action_bounds["camera_relative_bias_u16"],
            action_bounds["camera_relative_span_u16"],
            action_bounds["failure_outer_state_u16"]),
        "    0x%04Xu, 0x%04Xu, { 0x%02Xu, 0x%02Xu }, { 0x%02Xu, 0x%02Xu }," % (
            action_direction["upper_lane_u16"],
            action_direction["lower_lane_u16"],
            action_direction["upper_directions_by_a5_u8"][0],
            action_direction["upper_directions_by_a5_u8"][1],
            action_direction["lower_directions_by_a5_u8"][0],
            action_direction["lower_directions_by_a5_u8"][1]),
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu," % (
            action_zero["near_player_x_bias_u16"],
            action_zero["near_player_x_span_u16"],
            action_zero["near_player_z_bias_u16"],
            action_zero["near_player_z_span_u16"]),
        "    { %du, %du }, { %du, %du }, { 0x%02Xu, 0x%02Xu }," % (
            action_zero["turn_selectors_by_style_u8"][0],
            action_zero["turn_selectors_by_style_u8"][1],
            action_zero["idle_selectors_by_a3_u8"][0],
            action_zero["idle_selectors_by_a3_u8"][1],
            action_zero["movement_selector_base_by_style_u8"][0],
            action_zero["movement_selector_base_by_style_u8"][1]),
        "    { " + ", ".join("%dL" % value for value in
            action_jump["x_velocity_table_s32_16_16"]) + " },",
        "    %dL, %dL, %d, %dL," % (
            action_jump["y_velocity_s32_16_16"],
            action_jump["y_acceleration_s32_16_16"],
            action_jump["initial_y_add_s16"],
            action_fall["y_delta_s32_16_16"]),
        "    { " + ", ".join(f"{value}u" for value in
            action_attack["rng_group_table_u16"]) + " },",
        "    { 0u, 1u, 2u, 6u },",
        "    { 1u, 1u, 4u, 3u },",
        "    { " + ", ".join(f"{value}u" for group in
            action_attack["selector_groups_u16"] for value in group) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            action_attack["timer_stage_offsets_u8"]) + " },",
        "    {",
    ])
    for row in action_attack["timer_rows_u8"]:
        lines.append("        { " + ", ".join(f"{value}u" for value in row) + " },")
    lines.extend([
        "    }",
        "};", "",
        "static const AvspRound1Class1fInitialSpec avsp_round1_class1f_initial_actors[AVSP_ROUND1_CLASS1F_INITIAL_ACTOR_COUNT] =",
        "{",
    ])
    init_by_phase = {
        0x1000: class1f_initialization["phase_0x1000"],
        0x1200: class1f_initialization["phase_0x1200"],
        0x1400: class1f_initialization["phase_0x1400"],
    }
    for row in class1f_initial_actors:
        phase = row["substate_u16"]
        initializer = init_by_phase[phase]
        writes = initializer["writes"]
        source_flags = ((writes["actor+0xa5_u8"] & 1) |
                        ((writes["actor+0xa6_u8"] & 1) << 1) |
                        ((writes["actor+0xa4_u8"] & 1) << 2) |
                        ((writes["actor+0x85_u8"] & 1) << 3))
        timer = 216 if phase in (0x1000, 0x1200) else row["entry_delay_u8"]
        lines.append(
            "    { %sUL, 0x%04Xu, 0x%04Xu, %d, %d, %d, %du, %du, %du, %s, %du, 0x%02Xu, %du }," % (
                row["source_slot"], row["state_u16"], phase,
                row["x_s16"], row["y_s16"], row["z_s16"],
                row["facing_u8"], row["coordinate_mode_u8"],
                row["palette_u8"], row["object_or_u16"], timer, source_flags,
                initializer["animation_selector_u8"]))
    terminal_policies = {0: "AVSP_ROUND1_ANIMATION_TERMINAL_LOOP_FIRST",
                         1: "AVSP_ROUND1_ANIMATION_TERMINAL_LOOP_FIRST",
                         52: "AVSP_ROUND1_ANIMATION_TERMINAL_SELF_LOOP",
                         60: "AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD",
                         62: "AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD",
                         76: "AVSP_ROUND1_ANIMATION_TERMINAL_STATE_GUARD"}
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationSequenceSpec avsp_round1_class1f_initial_sequences[AVSP_ROUND1_CLASS1F_INITIAL_SEQUENCE_COUNT] =",
        "{",
    ])
    for sequence in class1f_sequences:
        rendered = []
        for row in sequence["records"]:
            rendered.append("{ %du, %d, %sUL, %sUL, %du, %du }" % (
                row["timer_u16"], row["branch_s16"], row["animation_record"],
                row["assembly"], row["hurt_selector_u8"],
                row["attack_selector_u8"]))
        while len(rendered) < 5:
            rendered.append("{ 0u, 0, 0UL, 0UL, 0u, 0u }")
        lines.append("    { %du, %du, %s, { %s } }," % (
            sequence["selector_u8"], len(sequence["records"]),
            terminal_policies[sequence["selector_u8"]], ", ".join(rendered)))
    audio_by_slot = {int(row["origin_record"], 16): int(row["command"], 16)
                     for row in class1f_audio_edges}
    lines.extend([
        "};", "",
        "static const unsigned short avsp_round1_class1f_initial_audio_commands[AVSP_ROUND1_CLASS1F_AIRBORNE_ACTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"0x{audio_by_slot.get(int(row['source_slot'], 16), 0):04X}u"
                            for row in class1f_initial_actors[-3:]),
        "};", "",
        "static const AvspRound1Class09InitialSpec avsp_round1_class09_initial_actors[AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT] =",
        "{",
    ])
    for row in class09["source_slots"]:
        lines.append("    { %sUL, %d, %d, %d, 0x%04Xu, 0x%04Xu, %du, %sUL }," % (
            row["source_slot"], row["x_s16"], row["y_s16"], row["z_s16"],
            row["state_u16"], row["substate_u16"], row["facing_u8"],
            row["animation_record"]))
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_class09_selector_table[8] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in class09["selector_table_u16"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class09_sequences[AVSP_ROUND1_CLASS09_SEQUENCE_COUNT][AVSP_ROUND1_CLASS09_SEQUENCE_RECORDS] =",
        "{",
    ])
    for sequence in class09["animation_sequences"]:
        rendered = ["{ %du, %d, %sUL, %sUL, %du, %du }" % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]) for row in sequence["records"]]
        lines.append("    { " + ", ".join(rendered) + " },")
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_class09_sequence_selectors[AVSP_ROUND1_CLASS09_SEQUENCE_COUNT] =",
        "{",
        "    " + ", ".join(f"{row['selector_u8']}u" for row in class09["animation_sequences"]),
        "};", "",
        "static const AvspRound1Class4eSpawnSpec avsp_round1_class4e_initial_spawns[AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT] =",
        "{",
    ])
    for row in class4e["initial_positions_before_rng"]:
        lines.append("    { %sUL, %d, %d, %d }," % (
            row["source_slot"], row["x_s16"], row["y_s16"], row["z_s16"]))
    lines.extend([
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_class4e_jitter[AVSP_ROUND1_CLASS4E_JITTER_COUNT] =",
        "{",
    ])
    for x, y in class4e["jitter_table_s16"]:
        lines.append(f"    {{ {x}, {y} }},")
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class4e_records[AVSP_ROUND1_CLASS4E_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4e["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class44GuardSpec avsp_round1_class44_guard =",
        "{",
        "    %sUL, %d, %d, %d, 0x%04Xu, 0x0000u, %sUL, %du, %du, %du, %su" % (
            class44["source_slot"], class44["initial_position_s16"][0],
            class44["initial_position_s16"][1],
            class44["initial_position_s16"][2],
            class44["initial_state_u16"], class44["dispatch"],
            class44["state0_presentation_actor"]["coordinate_mode_u8"],
            class44["state0_presentation_actor"]["palette_u8"],
            class44["state0_presentation_actor"]["facing_u8"],
            class44["state0_presentation_actor"]["object_or_u16"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class44_records[AVSP_ROUND1_CLASS44_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class44["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    bound_x = first_segment_bounds["bound_x"]
    bound_z = first_segment_bounds["bound_z"]
    lines.extend([
        "};", "",
        "static const AvspRound1NavigationBoundsSpec avsp_round1_first_segment_bounds =",
        "{",
        f"    {bound_x}, {bound_z}, {bound_x + 0x20}, {bound_x + 0x160},",
        f"    {bound_z + 0x10}, {bound_z + 0x90}",
        "};", "",
        "static const AvspRound1TerrainRecordSpec avsp_round1_first_segment_terrain_records[AVSP_ROUND1_TERRAIN_RECORD_COUNT] =",
        "{",
    ])
    for row in terrain_records:
        blob = bytes.fromhex(row["record_bytes"])
        lines.append("    { " + ", ".join(f"0x{value:02X}u" for value in blob) + " },")
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_first_segment_terrain_packed[AVSP_ROUND1_TERRAIN_PACKED_BYTES] =",
        "{",
    ])
    for offset in range(0, len(terrain_packed), 32):
        chunk = terrain_packed[offset:offset + 32]
        lines.append("    " + ", ".join(f"0x{value:02X}u" for value in chunk) +
                     ("," if offset + 32 < len(terrain_packed) else ""))
    lines.extend([
        "};", "",
        "static const AvspRound1ObstacleSpec avsp_round1_coffee_shop_obstacle =",
        "{",
        "    %sUL, 0x%02X, %du, 0x%04Xu, 0x%04Xu," % (
            obstacle_actor["slot"], int(obstacle_actor["class"], 16),
            obstacle_actor["type"], obstacle_actor["state_u16"],
            obstacle_actor["substate_u16"]),
        "    %d, %d, %d, %du, %sUL, %sUL, %du, %du," % (
            obstacle_actor["position_s16"]["x"],
            obstacle_actor["position_s16"]["y"],
            obstacle_actor["position_s16"]["z"],
            obstacle_actor["facing_u8"], obstacle_actor["animation_record"],
            obstacle_actor["assembly"], obstacle_actor["hurt_selector_u8"],
            obstacle_actor["attack_selector_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }" % (
            obstacle_box["x_center_s8"], obstacle_box["y_center_s8"],
            obstacle_box["x_half_u8"], obstacle_box["y_half_u8"],
            obstacle_box["z_center_s8"], obstacle_box["z_half_u8"]),
        "};", "",
        "static const AvspRound1CameraSpec avsp_round1_coffee_shop_camera =",
        "{",
        "    640, 256, 640, 832, 256, 256, 0x40u, 0x20u,",
        "    0x00C0, 0x00E0, 0x00A0, 0x0050, 0x0060, 0x0040,",
        f"    {camera_operands['threshold_byte_u8']}u, {camera_operands['countdown_initial_u16']}u,",
        "    {" + ", ".join(f"{value}u" for value in
                              camera["x_target_arithmetic"]["speed_table_u16"]) + "}",
        "};", "",
        "static const AvspRound1PlayerLocomotionSpec avsp_round1_player_locomotion =",
        "{",
        f"    {int(release['walking_action'], 16)}u,",
        f"    {int(release['stop_action'], 16)}u,",
        "    512u,",
        f"    {release['stop_timer']['ticks']}u,",
        "    {" + ", ".join(f"{value}u" for value in direction_resolver) + "}",
        "};", "",
        "static const AvspRound1PlayerMeleeSpec avsp_round1_player_melee =",
        "{",
        f"    {int(melee_dispatch['common_action'], 16)}u,",
        f"    {int(melee_dispatch['target_context_action'], 16)}u,",
        f"    {close_combo['followup_window']['ticks']}u,",
        f"    {len(melee_selectors)}u,",
        "    {" + ", ".join(f"{value}u" for value in melee_selectors) + "},",
        "    {" + ", ".join(f"{value}u" for value in melee_steps) + "}",
        "};", "",
        "static const AvspRound1PresentationSpec avsp_round1_player_melee_strikes[AVSP_ROUND1_PLAYER_MELEE_COUNT] =",
        "{",
    ])
    for row in melee_strikes:
        lines.append(
            "    { %sUL, %sUL, %du, %du }," % (
                row["record"], row["assembly"], row["hurt_selector"],
                row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerJumpVectorSpec avsp_round1_player_jump_vectors[AVSP_ROUND1_PLAYER_JUMP_VECTOR_COUNT] =",
        "{",
    ])
    for row in jump_vectors:
        lines.append("    { %dL, %dL, %dL, %dL }," % (
            row["x_velocity_s32_16_16"]["raw_s32"],
            row["x_acceleration_s32_16_16"]["raw_s32"],
            row["z_velocity_s32_16_16"]["raw_s32"],
            row["z_acceleration_s32_16_16"]["raw_s32"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerJumpVectorSpec avsp_round1_player_jump_down_vectors[AVSP_ROUND1_PLAYER_JUMP_DOWN_VECTOR_COUNT] =",
        "{",
        "    { %dL, %dL, 0L, 0L }," % (
            jump_down_vectors["vertical_only"]["x_velocity_s32_16_16"]["raw_s32"],
            jump_down_vectors["vertical_only"]["x_acceleration_s32_16_16"]["raw_s32"]),
        "    { %dL, %dL, 0L, 0L }" % (
            jump_down_vectors["with_horizontal"]["x_velocity_s32_16_16"]["raw_s32"],
            jump_down_vectors["with_horizontal"]["x_acceleration_s32_16_16"]["raw_s32"]),
        "};", "",
        "static const AvspRound1PlayerJumpSequenceSpec avsp_round1_player_jump_sequences[AVSP_ROUND1_PLAYER_JUMP_SEQUENCE_COUNT] =",
        "{",
    ])
    for selector in (3, 4, 5, 6, 10, 15, 41, 42, 60):
        records = jump_sequences[str(selector)]
        rendered = ["{ %du, %d, %sUL, %sUL, %du, %du }" % (
            row["timer_u16"], row["branch_s16"], row["record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]) for row in records]
        while len(rendered) < 8:
            rendered.append("{ 0u, 0, 0UL, 0UL, 0u, 0u }")
        lines.append("    { %du, %du, { %s } }," % (
            selector, len(records), ", ".join(rendered)))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerPresentationActorSpec avsp_round1_player_jump_actor =",
        "{",
        "    %du, %du, %su" % (
            jump["presentation_actor_fields"]["coordinate_mode_u8"],
            jump["presentation_actor_fields"]["palette_u8"],
            jump["presentation_actor_fields"]["object_or_u16"]),
        "};", "",
        "static const AvspRound1PlayerWeaponSpec avsp_round1_player_weapon =",
        "{",
        f"    {int(weapon_states['sufficient_entry_action'], 16)}u,",
        "    0x0c02u,",
        f"    {int(weapon_states['empty_entry_action'], 16)}u,",
        f"    {int(weapon_states['empty_active_action'], 16)}u,",
        f"    {int(weapon_states['cleanup_action'], 16)}u,",
        f"    {int(weapon_states['return_locomotion_action'], 16)}u,",
        f"    {weapon_empty['timer_initial']}u,",
        f"    {weapon_action['resource_capacity_u8']}u,",
        f"    {weapon_action['resource_debit_u8']}u,",
        f"    {weapon_action['recharge_countdown_after_entry_u8']}u,",
        f"    {weapon_resource['normal_recharge_reload_u8']}u,",
        f"    {weapon_resource['depleted_recharge_reload_u8']}u,",
        f"    {weapon_parent['class_u8']},",
        f"    {weapon_child['class_u8']},",
        "    0x8680u,",
        "    0x0080u,",
        "    0x8380u,",
        f"    {weapon_parent['collision_table']['table']}UL,",
        f"    {weapon_child['collision_table']['table']}UL",
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in weapon_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du }," % (
                row["action_u16"], row["substate_u8"], row["animation_record"],
                row["assembly"], row["hurt_selector_u8"],
                row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_empty_frames[AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in empty_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du }," % (
                row["action_u16"], row["substate_u8"], row["animation_record"],
                row["assembly"], row["hurt_selector_u8"],
                row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_return_frame =",
        "{",
        "    %du, %du, %sUL, %sUL, %du, %du" % (
            weapon_return_frame["action_u16"], weapon_return_frame["substate_u8"],
            weapon_return_frame["animation_record"],
            weapon_return_frame["assembly"],
            weapon_return_frame["hurt_selector_u8"],
            weapon_return_frame["attack_selector_u8"]),
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_weapon_parent_selector_offsets[AVSP_ROUND1_WEAPON_PARENT_SELECTOR_COUNT] =",
        "{",
    ])
    for x, y in parent_selector_offsets:
        lines.append(f"    {{ {x}, {y} }},")
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_weapon_parent_presentations[AVSP_ROUND1_WEAPON_PARENT_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in parent_presentations:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"], row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_weapon_parent_route_angles[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in parent_route_angles),
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_weapon_parent_motion_low[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT][AVSP_ROUND1_WEAPON_PARENT_LOW_MOTION_COUNT] =",
        "{",
    ])
    for angle in parent_route_angles:
        rows = ", ".join("{ %d, %d }" % tuple(row)
                         for row in parent_motion_low[str(angle)])
        lines.append("    { " + rows + " },")
    lines.extend([
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_weapon_parent_motion_high[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT][AVSP_ROUND1_WEAPON_PARENT_HIGH_MOTION_COUNT] =",
        "{",
    ])
    for angle in parent_route_angles:
        rows = ", ".join("{ %d, %d }" % tuple(row)
                         for row in parent_motion_high[str(angle)])
        lines.append("    { " + rows + " },")
    lines.extend([
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_air_weapon_selector_offsets[AVSP_ROUND1_AIR_WEAPON_SELECTOR_COUNT] =",
        "{",
    ])
    for x, y in air_class03_offsets:
        lines.append(f"    {{ {x}, {y} }},")
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_air_weapon_presentations[AVSP_ROUND1_AIR_WEAPON_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in air_class03_presentations:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerJumpSequenceSpec avsp_round1_air_weapon_player_sequence =",
        "{",
        "    18u, AVSP_ROUND1_AIR_WEAPON_PLAYER_PRESENTATION_COUNT,",
        "    {",
    ])
    rendered_air_player = []
    for row in air_class03_player_phase["presentation_records"]:
        rendered_air_player.append("        { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    while len(rendered_air_player) < 8:
        rendered_air_player.append(
            "        { 0u, 0, 0UL, 0UL, 0u, 0u },")
    lines.extend(rendered_air_player)
    lines.extend([
        "    }",
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_air_weapon_motion_low[AVSP_ROUND1_AIR_WEAPON_LOW_TABLE_COUNT][AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT] =",
        "{",
    ])
    for magnitude in range(16):
        rows = [[0, 0]] * 64 if magnitude == 0 else \
            air_class03_motion_low[str(magnitude)]
        lines.append("    { " + ", ".join(
            "{ %d, %d }" % tuple(row) for row in rows) + " },")
    lines.extend([
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_air_weapon_motion_high[AVSP_ROUND1_AIR_WEAPON_HIGH_TABLE_COUNT][AVSP_ROUND1_AIR_WEAPON_DIRECTION_COUNT] =",
        "{",
    ])
    for magnitude in range(13):
        rows = [[0, 0]] * 64 if magnitude == 0 else \
            air_class03_motion_high[str(magnitude)]
        lines.append("    { " + ", ".join(
            "{ %d, %d }" % tuple(row) for row in rows) + " },")
    lines.extend([
        "};", "",
        "static const AvspRound1WeaponChildSpawnSpec avsp_round1_air_weapon_child_spawn_normal[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =",
        "{",
    ])
    for row in air_class03_child_rows:
        lines.append("    { %d, %d, %d, %du }," % (
            row["x_s16"], row["y_s16"], row["z_s16"], row["variant_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1WeaponChildSpawnSpec avsp_round1_air_weapon_child_spawn_collision[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =",
        "{",
    ])
    for row in air_class03_collision_child_rows:
        lines.append("    { %d, %d, %d, %du }," % (
            row["x_s16"], row["y_s16"], row["z_s16"], row["variant_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AirWeaponProjectileSpec avsp_round1_air_weapon_projectile =",
        "{",
        f"    {air_class03['class_u8']}, 0u, 2u, 4u, 6u,",
        f"    {air_class03['allocation']['player_collision_selector_u8']}u,",
        f"    {air_class03_emitter['initial_child_count_u8']}u,",
        f"    {air_class03_emitter['initial_cadence_u8']}u,",
        f"    {air_class03_emitter['cadence_reload_u8']}u,",
        f"    {air_class03_active['substate_2']['reload_u8']}u,",
        "    5u, 0xc0u, 0x8000u,",
        f"    {air_class03['dispatch']}UL,",
        f"    {air_class03_init['collision_table_u32']}UL,",
        f"    {air_class03['effect_allocation']['record_type_u8']}u,",
        f"    {air_class03['effect_allocation']['class_u8']}u,",
        f"    {air_class03['effect_allocation']['variant_u8']}u",
        "};", "",
        "static const AvspRound1WeaponChildSpawnSpec avsp_round1_weapon_child_spawn_normal[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =",
        "{",
    ])
    for row in parent_child_rows:
        lines.append("    { %d, %d, %d, %du }," % (
            row["x_s16"], row["y_s16"], row["z_s16"], row["variant_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1WeaponChildSpawnSpec avsp_round1_weapon_child_spawn_collision[AVSP_ROUND1_WEAPON_CHILD_SPAWN_COUNT] =",
        "{",
    ])
    for row in parent_collision_child_rows:
        lines.append("    { %d, %d, %d, %du }," % (
            row["x_s16"], row["y_s16"], row["z_s16"], row["variant_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1WeaponChildSequenceSpec avsp_round1_weapon_child_sequences[AVSP_ROUND1_WEAPON_CHILD_VARIANT_COUNT] =",
        "{",
    ])
    for variant in range(3):
        records = child_sequences[str(variant)]
        rendered = ["{ %du, %d, %sUL, %sUL, %du, %du }" % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]) for row in records]
        while len(rendered) < 17:
            rendered.append("{ 0u, 0, 0UL, 0UL, 0u, 0u }")
        lines.append("    { %du, { %s } }," % (
            len(records), ", ".join(rendered)))
    lines.extend([
        "};", "",
        "static const AvspRound1WeaponProjectileSpec avsp_round1_weapon_projectile =",
        "{",
        "    0u, 2u, 4u, 6u, 0x50, 0x0220u, 0x10, 0x0120u,",
        f"    {weapon_parent['class_u8']}, {weapon_child['class_u8']},",
        f"    {parent_emitter['initial_child_count_u8']}u,",
        f"    {parent_emitter['initial_cadence_u8']}u,",
        f"    {parent_emitter['cadence_reload_u8']}u, 0x8000u,",
        f"    {weapon_parent['dispatch']}UL, {weapon_child['dispatch']}UL,",
        f"    {weapon_parent['collision_table']['table']}UL,",
        f"    {weapon_child['collision_table']['table']}UL,",
        f"    {weapon_damage['parent_contact']['damage_u8']}u,",
        f"    {weapon_damage['child_contact']['damage_u8']}u",
        "};", "",
        "static const AvspRound1CollisionBoxSpec avsp_round1_weapon_parent_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =",
        "{",
    ])
    for box in parent_attack_boxes:
        lines.append("    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            box["x_center_s8"], box["y_center_s8"], box["x_half_u8"],
            box["y_half_u8"], box["z_center_s8"], box["z_half_u8"],
            box["knockback_mode_s8"], box["hit_value_u8"],
            box["damage_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1CollisionBoxSpec avsp_round1_weapon_child_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =",
        "{",
    ])
    for box in child_attack_boxes:
        lines.append("    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            box["x_center_s8"], box["y_center_s8"], box["x_half_u8"],
            box["y_half_u8"], box["z_center_s8"], box["z_half_u8"],
            box["knockback_mode_s8"], box["hit_value_u8"],
            box["damage_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_empty_effect_variant_offsets[AVSP_ROUND1_EMPTY_EFFECT_VARIANT_COUNT] =",
        "{",
    ])
    for x, y in empty_effect_offsets:
        lines.append(f"    {{ {x}, {y} }},")
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_empty_effect_variant1_records[AVSP_ROUND1_EMPTY_EFFECT_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in empty_effect_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer"], row["branch"], row["animation_record"],
            row["assembly"], row["hurt_selector"], row["attack_selector"]))
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = build()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="ascii") != rendered:
            raise SystemExit("generated SPEC-02 Round 1 entry header is stale")
        print("SPEC-02 Round 1 entry data: PASS (generated header current)")
        return
    OUT.write_text(rendered, encoding="ascii", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
