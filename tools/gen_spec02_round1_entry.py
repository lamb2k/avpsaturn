#!/usr/bin/env python3
"""Generate the bounded native Round 1 entry tables from SPEC-02 fixtures."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/spec02_round1_generated_fixtures.json"
CONTRACT = ROOT / "data/spec02_round1_executable_contract.json"
ROUTE_CENSUS = ROOT / "data/round1_route_census.json"
OUT = ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h"
OUT_CONTENT = ROOT / "src/port_v2/gameplay/round1/spec02_round1_content_image.c"

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


def split_target_content(rendered: str) -> tuple[str, str]:
    """Keep host fixtures inline but make every Target constant cart-backed."""
    source_lines = rendered.splitlines()
    output: list[str] = []
    members: list[str] = []
    initializers: list[str] = []
    index = 0
    declaration = re.compile(
        r"(?s)^static const\s+(.+?)\s+(avsp_round1_[A-Za-z0-9_]+)"
        r"((?:\[[^\n]+?\])*)\s*$")
    while index < len(source_lines):
        line = source_lines[index]
        if not line.startswith("static const "):
            output.append(line)
            index += 1
            continue
        block = [line]
        brace_depth = line.count("{") - line.count("}")
        while not (brace_depth == 0 and block[-1].rstrip().endswith(";")):
            index += 1
            if index >= len(source_lines):
                raise ValueError("unterminated generated static constant")
            block.append(source_lines[index])
            brace_depth += source_lines[index].count("{")
            brace_depth -= source_lines[index].count("}")
        text = "\n".join(block)
        left, initializer = text.rsplit(";", 1)[0].split("=", 1)
        match = declaration.match(left.strip())
        if match is None:
            raise ValueError(f"unsupported generated declaration: {left}")
        value_type, name, dimensions = match.groups()
        member = f"    {value_type} content_{name}{dimensions};"
        members.append(member)
        initializers.append(initializer.strip())
        output.extend([
            "#if defined(__sh__)",
            f"#define {name} (avsp_round1_content->content_{name})",
            "#else",
            text,
            "#endif",
        ])
        index += 1
    if not members:
        raise ValueError("no generated Round 1 constants found")
    if output[-1] != "#endif":
        raise ValueError("generated Round 1 header guard drift")
    output[-1:-1] = [
        "#if defined(__sh__)",
        "typedef struct",
        "{",
        "    unsigned long magic;",
        "    unsigned long version;",
        "    unsigned long bytes;",
        *members,
        "} AvspRound1ContentArchive;",
        "extern const AvspRound1ContentArchive *avsp_round1_content;",
        "#define AVSP_ROUND1_CONTENT_ARCHIVE_MAGIC 0x52314341UL",
        "#define AVSP_ROUND1_CONTENT_ARCHIVE_VERSION 1UL",
        "#define AVSP_ROUND1_CONTENT_ARCHIVE_BYTES \\",
        "    ((unsigned long)sizeof(AvspRound1ContentArchive))",
        "#endif",
        "",
    ]
    content = [
        "/* Generated target-endian image; compile only for archive extraction. */",
        "#include \"round1.h\"",
        "#include \"spec02_round1_entry_data.h\"",
        "",
        "const AvspRound1ContentArchive avsp_round1_content_image",
        "    __attribute__((section(\".round1content\"), used)) =",
        "{",
        "    AVSP_ROUND1_CONTENT_ARCHIVE_MAGIC,",
        "    AVSP_ROUND1_CONTENT_ARCHIVE_VERSION,",
        "    sizeof(AvspRound1ContentArchive),",
    ]
    for initializer in initializers:
        rendered_initializer = initializer.splitlines()
        content.extend(f"    {row}" for row in rendered_initializer)
        content[-1] += ","
    content.extend(["};", ""])
    return "\n".join(output) + "\n", "\n".join(content)


def build() -> str:
    fixtures = json.loads(FIXTURES.read_text(encoding="ascii"))
    route_census = json.loads(ROUTE_CENSUS.read_text(encoding="ascii"))
    scene_input_runs = []
    for group in route_census["groups"]:
        cursor = group["first_frame"]
        for input_word, frames in group["input_word_runs"]:
            native_input = 0
            if input_word & 0x04:
                native_input |= 0x0008
            if input_word & 0x08:
                native_input |= 0x0010
            if input_word & 0x10:
                native_input |= 0x0020
            if input_word & 0x20:
                native_input |= 0x0040
            run_first = cursor
            run_last = cursor + frames - 1
            cursor += frames
            clipped_first = max(run_first, 2040)
            clipped_last = min(run_last, 5566)
            if clipped_first > clipped_last:
                continue
            if (scene_input_runs and
                    scene_input_runs[-1][2] == native_input and
                    scene_input_runs[-1][1] + 1 == clipped_first):
                scene_input_runs[-1] = (
                    scene_input_runs[-1][0], clipped_last, native_input)
            else:
                scene_input_runs.append(
                    (clipped_first, clipped_last, native_input))
    if (not scene_input_runs or scene_input_runs[0][0] != 2040 or
            scene_input_runs[-1][1] != 5566 or
            any(first != scene_input_runs[index - 1][1] + 1
                for index, (first, _last, _word) in
                enumerate(scene_input_runs[1:], 1))):
        raise ValueError("Coffee Shop input ledger does not tile 2040..5566")
    body = fixtures["authority_data"]["route"]["first_entry_body"]
    spawns = body["spawn_table"]["rows"]
    player = body["player_entry_script"]
    commands = player["source_program"]["commands"]
    program = bytes.fromhex(player["source_program"]["hex"])
    scheduler = fixtures["authority_data"]["scheduler"]
    scheduler_globals = fixtures["authority_data"]["navigation"][
        "scheduler_visible_globals"]
    scheduler_global_fields = scheduler_globals["fields"]
    if (scheduler_globals["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        scheduler_globals["consumer"]["routine"] != "0x041c36" or
        [(row["a5_offset_u16"], row["absolute_address"], row["type"],
          row["width_bytes"], row["native_scheduler_field"])
         for row in scheduler_global_fields] != [
            (0x0278, "0xff8278", "s16", 2, "camera_x_previous"),
            (0x027c, "0xff827c", "s16", 2, "camera_z_previous")]):
        raise ValueError("SPEC-02 scheduler-visible globals drift")
    scheduler_order = [row["record_type"] for row in
                       scheduler["frame_scheduler"]["full_order"]
                       if row["record_type"] in (12, 16, 20, 24, 28, 36)]
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
    class1f_collision_reaction_facing = class1f_current_damage[
        "common_collision_reaction_facing"]
    class1f_current_reaction = class1f_current_damage[
        "accepted_port_v2_reaction_mapping"]
    class1f_source_hit = class1f_current_damage["source_hit_entry_program"]
    class1f_source_hit_program = class1f_source_hit["source_hit_program"]
    class1f_source_hit_launch = class1f_source_hit_program[
        "phase_0x0200_launch"]
    class1f_source_hit_first_flight = class1f_source_hit_program[
        "phase_0x0202_first_flight"]
    class1f_source_hit_landing_hold = class1f_source_hit_program[
        "phase_0x0204_landing_hold"]
    class1f_source_hit_bounce = class1f_source_hit_program[
        "phase_0x0206_bounce"]
    class1f_source_hit_rng_hold = class1f_source_hit_program[
        "phase_0x0208_rng_hold"]
    class1f_source_hit_terminal = class1f_source_hit_program[
        "phase_0x020a_terminal_animation"]
    class1f_source_hit_sequences = class1f_source_hit_program[
        "animation_sequences"]
    class1f_source_hit_return = class1f_source_hit_program["normal_return"]
    class1f_source_hit_resume = class1f_source_hit_return[
        "preserved_resume_fields"]
    class1f_source_hit_reaction_records = class1f_source_hit_sequences[
        "reaction_0x36"]["records"]
    class1f_source_hit_landing_record = class1f_source_hit_sequences[
        "landing_0x37"]["records"][0]
    class1f_source_hit_bounce_record = class1f_source_hit_sequences[
        "bounce_0x38"]["records"][0]
    class1f_source_hit_rng_hold_record = class1f_source_hit_sequences[
        "rng_hold_0x39"]["records"][0]
    class1f_source_hit_rng = class1f_source_hit["rng"]
    class1f_source_ko = class1f_current_damage["source_projectile_ko_program"]
    class1f_source_ko_handoff = class1f_source_ko["scheduler_handoff"]
    class1f_source_ko_program = class1f_source_ko["state_program"]
    class1f_source_ko_launch = class1f_source_ko_program["launch"]
    class1f_source_ko_landing = class1f_source_ko_program["first_landing"]
    class1f_source_ko_bounce = class1f_source_ko_program["bounce"]
    class1f_source_ko_hold = class1f_source_ko_program["removal_hold"]
    class1f_source_ko_release = class1f_source_ko_program["release"]
    class1f_source_ko_sequences = class1f_source_ko_program["animation_sequences"]
    class1f_source_ko_reaction_records = class1f_source_ko_sequences[
        "reaction_0x36"]["records"]
    class1f_source_ko_landing_record = class1f_source_ko_sequences[
        "landing_0x37_and_hold_0x39"]["records"][0]
    class1f_source_ko_bounce_record = class1f_source_ko_sequences[
        "bounce_0x38"]["records"][0]
    class1f_actions = class1f["first_segment_action_execution_contract"]
    class1f_inner8 = class1f_actions["inner_state_0x08_program"]
    class1f_inner8_records = class1f_inner8["animation_records"]
    class1f_inner8_movement_tables = class1f_inner8["movement"]["tables"]
    class1f_inner8_terrain_tail = class1f_inner8["movement"]["terrain_tail"]
    class1f_inner8_path = class1f_inner8["observed_path_program"]
    class1f_inner8_action10 = class1f_inner8_path["action_0x10"]
    class1f_inner8_action10_init = class1f_inner8_action10["initializer"]
    class1f_inner8_action10_movement = class1f_inner8_action10_init[
        "movement_binding"]
    class1f_inner8_action10_phase_movement = class1f_inner8_action10[
        "phase_terminal_movement_binding"]
    class1f_inner8_action4 = class1f_inner8_path["action_0x04"]
    class1f_inner8_action4_contact = class1f_inner8_action4[
        "complete_dispatch_contract"]["post_movement_terrain_direction"]
    class1f_inner8_action4_timer = class1f_inner8_action4[
        "timer_selector_program"]
    class1f_inner8_action2 = class1f_inner8_path["action_0x02"]
    class1f_inner8_action6 = class1f_inner8_path["action_0x06"]
    class1f_inner8_action8 = class1f_inner8_path["action_0x08"]
    class1f_inner8_action0c = class1f_inner8_path["action_0x0c"]
    class1f_inner8_action0c_phase0 = class1f_inner8_action0c["phase_0"]
    class1f_inner8_action0c_phase2 = class1f_inner8_action0c["phase_2"]
    class1f_inner8_tables = class1f_inner8_path["source_tables"]
    class1f_inner8_movement_selectors = class1f_inner8_tables[
        "movement_selector_by_style_relation"]["rows"]
    class1f_inner8_action10_phase_selectors = class1f_inner8_tables[
        "action10_phase_terminal_selector_by_style_relation"]["rows"]
    class1f_inner8_groups = class1f_inner8_path[
        "wander_group_occupancy_program"]
    class1f_inner8_motion = class1f_inner8["action_0x0e_motion"]
    class1f_inner8_scene_clear = class1f_inner8[
        "scene_clear_interruption"]
    class1f_inner8_timeout = class1f_inner8["route_interaction"][
        "timeout_return"]
    action_variants = class1f_actions["initializer"]["variants"]
    action_targets = class1f_actions["current_dispatch"]["action_targets"]
    action_selectors = class1f_actions["animation_selector_table"]["selectors"]
    action_records = [record for sequence in action_selectors
                      for record in sequence["records"]]
    action_movement_tables = class1f_actions["movement_tables"]
    action_attack_timers = class1f_actions["attack_timer_table_u8"]
    action_player_collision = class1f_actions[
        "current_state_player_collision"]
    action_programs = class1f_actions["action_programs"]
    action_bounds = action_programs["source_bounds"]
    action_animation_movement = action_programs[
        "animation_movement_helper_0x0165c4"]
    action_direction = action_programs["direction_helper_0x061032"]
    action_zero = action_programs["action_0x00"]
    action_fall = action_programs["action_0x0c"]
    action_jump = action_programs["action_0x0e"]
    action_attack = action_programs["action_0x04"]
    recurring = fixtures["authority_data"]["route"][
        "first_segment_recurring_spawn"]
    source_update_cadence = recurring["source_update_cadence"]
    source_update_exceptions = source_update_cadence["exceptions"]
    recurring_controller = recurring["controller_program"]
    recurring_initializer = recurring_controller["initializer"]
    recurring_gate = recurring_controller["intro_gate_transition"]
    recurring_camera_edge = recurring_controller["camera_edge_transition"]
    recurring_primary = recurring["primary_writer"]
    recurring_post_allocation = recurring_primary[
        "post_allocation_dispatch"]["same_frame"]
    recurring_fixed_point_reuse = recurring_primary[
        "fixed_point_record_reuse"]
    recurring_auxiliary = recurring["auxiliary_writer"]
    recurring_progress = recurring["progress_increment_boundary"]
    recurring_tables = recurring_primary["tables"]
    coffee_exit = recurring["exit_controller_program"]
    coffee_exit_controller = coffee_exit["controller_dispatch"]
    coffee_exit_handoff = coffee_exit_controller["withdrawal_route_handoff"]
    coffee_exit_script = coffee_exit["player_withdrawal_script"]
    coffee_exit_route_zero = coffee_exit["route_zero_program"]
    coffee_exit_next_scene = coffee_exit_route_zero[
        "next_scene_reinitialization"]
    coffee_exit_callbacks = coffee_exit_script["source_display_callback_program"]
    coffee_exit_ballistic = coffee_exit_script["ballistic_mode_3"]
    class1f_initial_actors = class1f_initial["actors"]
    class1f_initialization = class1f_initial["initialization"]
    class1f_sequences = class1f_initial["animation_sequences"]
    class1f_phase1400 = class1f_initial["phase_0x1400"]
    class1f_audio_edges = class1f_phase1400["substates"][2]["audio_edges"]
    auxiliary_dependencies = fixtures["authority_data"]["auxiliary"][
        "first_segment_dependencies"]
    class08_pickup = auxiliary_dependencies[
        "class_0x08_type20_health_pickup"]
    class05_prop = auxiliary_dependencies[
        "class_0x05_type20_reactive_prop"]
    class09 = auxiliary_dependencies["class_0x09_type20_rng_owner"]
    class4e = auxiliary_dependencies["class_0x4e_type24_variant4_effect"]
    class4e_variant0 = class4e["variant0_collision_effect"]
    class4e_variant1 = class4e["variant1_collision_effect"]
    player_special_target_collision = class4e_variant1[
        "player_special_collision"]
    player_special_source_ko = player_special_target_collision[
        "class1f_target"]["source_ko"]
    class4e_variant10 = class4e["variant10_collision_effect"]
    class4e_reachable = class4e_variant10[
        "shared_dispatch_reachable_variant_programs"]
    class4e_variant5 = class4e_reachable["5"]
    class4e_variant20 = class4e_reachable["20"]
    class4e_rng = class4e["seed_transaction_by_scheduler_slot"]
    class44 = auxiliary_dependencies["class_0x44_type24_command_guard_owner"]
    class43 = auxiliary_dependencies[
        "class_0x43_type24_class01_scene_population"]
    class45 = auxiliary_dependencies["class_0x45_type24_scene_population"]
    class47 = auxiliary_dependencies[
        "class_0x47_type24_class02_child_presentation"]
    special_effects = auxiliary_dependencies[
        "predator_special_type24_effects"]
    class4b = special_effects["class_0x4b"]
    class3d = special_effects["class_0x3d"]
    class16 = auxiliary_dependencies[
        "class_0x1f_type16_0x06_projectile"]
    scene_components = fixtures["authority_data"]["auxiliary"][
        "coffee_shop_scene_component_identities"]
    class01 = next(item for item in scene_components["components"]
                   if item["type"] == 20 and item["class"] == "0x01")
    class02 = next(item for item in scene_components["components"]
                   if item["type"] == 20 and item["class"] == "0x02")
    class0f = next(item for item in scene_components["components"]
                   if item["type"] == 20 and item["class"] == "0x0f")
    class0a = next(item for item in scene_components["components"]
                   if item["type"] == 24 and item["class"] == "0x0a")
    class00_companion = next(item for item in scene_components["components"]
                             if item["type"] == 28 and
                             item["class"] == "0x00")
    class01_contract = class01["implementation_contract"]
    class02_contract = class02["implementation_contract"]
    class0f_contract = class0f["implementation_contract"]
    class0a_contract = class0a["implementation_contract"]
    class00_companion_contract = class00_companion["implementation_contract"]
    type36_classes = fixtures["authority_data"]["auxiliary"][
        "coffee_shop_type36_presentation"]["classes"]
    class03_type36 = next(item for item in type36_classes
                          if item["class"] == "0x03")
    class03_type36_contract = class03_type36["implementation_contract"]
    class03_type36_records = class03_type36_contract["state_0x0000"][
        "animation_binding"]["record_sequence"]
    class04_type36 = next(item for item in type36_classes
                          if item["class"] == "0x04")
    class04_type36_contract = class04_type36["implementation_contract"]
    class04_type36_records = class04_type36_contract["state_0x0000"][
        "animation_binding"]["record_sequence"]
    coffee_scene_records = sorted(
        class01_contract["stage_records"] +
        class02_contract["stage_records"] +
        class0f_contract["stage_records"] +
        class05_prop["stage_records"],
        key=lambda row: int(row["address"], 16))
    class01_records = class01_contract["initialization"][
        "animation_records"]
    class02_records = class02_contract["initialization"][
        "animation_records"]
    class0f_records = class0f_contract["initialization"][
        "animation_records"]
    class0a_records = class0a_contract["animation_selector"][
        "coffee_shop_records"]
    class0a_cadence = class0a_contract["scheduler_cadence"]
    class00_companion_records = class00_companion_contract[
        "animation_selector"]["records"]
    class00_companion_parent_animations = class00_companion_contract[
        "parent_projection"]["coffee_shop_animation_record_branches"]
    class00_companion_parent_entries = class00_companion_contract[
        "parent_projection"]["coffee_shop_entries"]
    class00_companion_cadence = class00_companion_contract[
        "scheduler_cadence"]
    class00_companion_exit_phase = class00_companion_cadence[
        "exit_callback_phase"]
    class00_exit_phase_program = class00_companion_exit_phase["program"]
    class0f_selector1 = class0f_contract["state_program"]["0x0400"][
        "selector_1"]
    class0f_selector0 = class0f_contract["state_program"]["0x0400"][
        "selector_0"]
    class02_collision = class02_contract["collision_damage"]
    class05_records = class05_prop["presentation_records"]
    class05_collision = class05_prop["current_state_collision"]
    class05_reaction = class05_prop["reaction_program"]
    class05_motion = class05_reaction["state_0x0404"]
    class02_source_cadence = class02_contract["scheduler_phase_evidence"][
        "class02_source_update_cadence"]
    class02_source_exceptions = class02_source_cadence["exceptions"]
    record20_exit_prefix = class02_contract["scheduler_phase_evidence"][
        "record20_exit_prefix_scheduler"]
    record20_exit_prefix_groups = record20_exit_prefix["groups"]
    coffee_stage_setup = fixtures["authority_data"]["rng"]["owner_partition"][
        "global_route_and_controller"]["groups"][0][
            "coffee_shop_entry_transaction"]
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
    terrain_selector_runs = []
    for selector in terrain_selectors:
        if (terrain_selector_runs and
                terrain_selector_runs[-1][1] == selector and
                terrain_selector_runs[-1][0] < 256):
            terrain_selector_runs[-1] = (
                terrain_selector_runs[-1][0] + 1, selector)
        else:
            terrain_selector_runs.append((1, selector))
    terrain_grid = terrain["selection"]["bounded_packed_grid"]
    terrain_packed = bytes.fromhex(terrain_grid["packed_bytes_hex"])
    terrain_stream = terrain["selection"]["camera_streaming_program"]
    terrain_stream_transactions = terrain_stream["transactions"]
    terrain_stream_writes = []
    terrain_stream_ranges = []
    for transaction in terrain_stream_transactions:
        terrain_stream_ranges.append(
            (len(terrain_stream_writes), len(transaction["writes"])))
        terrain_stream_writes.extend(transaction["writes"])
    obstacle = navigation["obstacle_response"]["implementation_contract"]
    obstacle_lifecycle = navigation["obstacle_response"]["lifecycle_contract"]
    obstacle_parent_records = obstacle_lifecycle["presentation"]["records"]
    obstacle_child = obstacle_lifecycle["child_presentation"]
    obstacle_child_sequences = obstacle_child["variant_sequences"]
    obstacle_scene_record = obstacle_lifecycle["source_scene_record"]
    obstacle_initializer = obstacle_lifecycle["initializer"]
    obstacle_state_program = obstacle_lifecycle["state_program"]
    obstacle_break = obstacle_state_program["state_0400"]
    obstacle_collision = obstacle_lifecycle["collision_damage"]
    obstacle_player_attack = obstacle_collision["player_attack_record"]
    obstacle_hurt = obstacle_collision["obstacle_hurt_record"]
    obstacle_actor = obstacle["source_actor"]
    obstacle_box = obstacle["obstacle_box"]
    camera = navigation["camera"]["implementation_contract"]
    camera_guard = camera["coffee_shop_guard"]
    camera_operands = camera_guard["captured_first_segment_operands"]
    locomotion = fixtures["authority_data"]["player"]["locomotion_neutral_facing"]
    player_hit = fixtures["authority_data"]["player"][
        "hit_ko_failure_continue_respawn"]["nonlethal_hit"][
            "first_segment_execution_contract"]
    player_hit_states = player_hit["states"]
    player_hit_entry = player_hit["entry_writes"]["carried_record"]
    player_hit_phase0 = player_hit["phase_0x0200"]
    player_hit_motion = player_hit["phase_0x0202"]
    player_hit_return = player_hit["phase_0x0204"]
    player_hit_program = fixtures["authority_data"]["player"][
        "hit_ko_failure_continue_respawn"]["nonlethal_hit"][
            "coffee_shop_reachable_program"]
    player_hit_interruption = player_hit_program[
        "source_action_interruption"]
    player_hit_reactions = []
    player_hit_seen = set()
    for instance in player_hit_program["instances"]:
        key = instance["attack_record"]
        if key not in player_hit_seen:
            player_hit_seen.add(key)
            player_hit_reactions.append(instance)
    input_decode = locomotion["input_decode"]
    release = locomotion["release_transition"]
    locomotion_execution = locomotion["first_segment_execution_contract"]
    locomotion_pipeline = locomotion_execution["controller_pipeline"]
    locomotion_presentation = locomotion_execution["presentation"]
    locomotion_records = locomotion_presentation["records"]
    direction_resolver = input_decode["resolver_table"]
    melee = fixtures["authority_data"]["player"]["route_reachable_melee_actions"]
    close_combo = melee["close_combo"]
    melee_dispatch = melee["dispatch"]
    melee_sequences = close_combo["animation_sequences"]
    melee_selectors = close_combo["attack_selectors"]
    melee_steps = close_combo["step_values"]
    contextual_melee = melee["contextual_melee"]["implementation_contract"]
    contextual_sequences = contextual_melee["presentation_sequences"]
    hit_interaction = fixtures["authority_data"]["player"][
        "route_pickup_resource_audio_load_ownership"][
            "interaction_action_and_interruption"]["implementation_contract"]
    hit_interaction_player_records = hit_interaction["entry"][
        "player_presentation"]
    hit_interaction_effect = hit_interaction["class20_effect"]
    hit_interaction_collision = hit_interaction["current_state_collision"]
    hit_interaction_eligibility = hit_interaction_collision[
        "target_eligibility"]
    hit_interaction_latch = hit_interaction_collision[
        "collision_identity_latch"]
    hit_interaction_target_reaction = hit_interaction_collision[
        "target_reaction"]
    if (hit_interaction_eligibility["pool"] != "record12" or
        hit_interaction_eligibility["scan_order"] !=
            "ascending source-slot order" or
        hit_interaction_eligibility["reaction_state_exclusion"] is not False or
        hit_interaction_eligibility["coffee_shop_first_eligible_target"] != {
            "source_slot": "0x00ff9dc0", "state_u16": 0x0208,
            "substate_u16": 0x0c02}):
        raise ValueError("SPEC-02 player interaction target eligibility drift")
    if (hit_interaction_latch["damage_writes_while_held_u8"] != 1 or
        hit_interaction_latch["independent_from_melee_attack_active"] is not True or
        hit_interaction_latch["reset_guard"] !=
            "interaction ends or current attack selector leaves 10"):
        raise ValueError("SPEC-02 player interaction collision latch drift")
    melee_strikes = []
    jump = fixtures["authority_data"]["player"][
        "directional_airborne_interruption"]["directional_actions"][
            "implementation_contract"]
    jump_vectors = jump["vector_table"]
    jump_down_vectors = jump["down_vector_table"]
    jump_sequences = jump["presentation_selector_sequences"]
    jump_witness = jump["coffee_shop_right_facing1_witness"]
    air_class03 = fixtures["authority_data"]["player"][
        "directional_airborne_interruption"]["airborne_actions"]["button1"][
            "record4_class03"]
    weapon = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    player_special = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["special_implementation_contract"]
    weapon_states = weapon["state_dispatch"]
    weapon_action = weapon["sufficient_action"]
    weapon_stage_progress = weapon_action["source_stage_progress"]
    weapon_stage_progress_helper = weapon_stage_progress["helper"]
    weapon_stage_progress_layout = weapon_stage_progress_helper["field_layout"]
    weapon_action_entry = weapon_action["entry_projection"]
    weapon_animation_execution = weapon_action["animation_execution"]
    weapon_resource = weapon["resource_tick"]
    weapon_empty = weapon["empty_fallback"]
    weapon_empty_entry = weapon_empty["entry_projection"]
    weapon_parent = weapon["record4_parent_class0"]
    weapon_child = weapon["record4_child_class4"]
    weapon_damage = weapon["current_state_collision_damage"]
    weapon_collision_registration = weapon_damage[
        "registration_and_pair_eligibility"]
    weapon_empty_effect = weapon["empty_effect_variant1_contract"]
    weapon_frames = weapon_action["presentation_timeline"]
    weapon_selector_contract = weapon_action["presentation_selector_contract"]
    weapon_selector_timelines = weapon_selector_contract["selector_timelines"]
    weapon_selectors = list(range(
        weapon_selector_contract["selector_range_u8"][0],
        weapon_selector_contract["selector_range_u8"][1] + 1))
    weapon_selector_sequences = {}
    for selector in weapon_selectors:
        sequence = []
        for row in weapon_selector_timelines[str(selector)][1:19]:
            if not sequence or row["animation_record"] != \
                    sequence[-1]["animation_record"]:
                sequence.append(row)
        weapon_selector_sequences[str(selector)] = sequence
    empty_frames = weapon_empty["presentation_timeline"]
    weapon_return_frame = dict(weapon_frames[0])
    weapon_return_frame.update({"action_u16": 2, "substate_u8": 2})
    first_segment_bounds = next(
        run for run in global_bounds["baseline_bound_runs"]
        if run["route"] == 4 and run["bound_x"] == 720 and
        run["bound_z"] == 256 and run["frames"] == 333)
    if (player_hit["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        player_hit["spec_executable"] is not True or
        player_hit_states != {
            "control_outer_u16": 0x0200, "hit_outer_u16": 0x0202,
            "entry_substate_u16": 0, "shake_substate_u16": 0x0200,
            "motion_substate_u16": 0x0202,
            "return_substate_u16": 0x0204} or
        player_hit["entry_writes"]["shake_countdown_u8"] != 10 or
        player_hit["entry_writes"]["motion_index_u8"] != 2 or
        player_hit_phase0["writes"] != {
            "next_substate_u16": 0x0202,
            "x_velocity_s32_16_16": 0x0001C000,
            "x_acceleration_s32_16_16": -0x00002000} or
        player_hit_phase0["motion_table"]["index_u8"] != 2 or
        player_hit_phase0["motion_table"]["row_hex"] !=
            "0001c000ffffe000" or
        player_hit["shake"]["table_s16"] != [2, -2] * 16 or
        player_hit_motion["animation_loop"] != {
            "timer_u16": 8, "branch_s16": -0x8000} or
        player_hit_return["return_visible_frame_u16"] != 2778 or
        player_hit["audio"]["command_u16"] != 0x003b or
        player_hit["rng"] != {"calls": [], "consumption_order": []}):
        raise ValueError("SPEC-02 first-segment player HIT drift")
    if (player_hit_program["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        player_hit_program["spec_executable"] is not True or
        len(player_hit_program["instances"]) != 5 or
        len(player_hit_reactions) != 3 or
        [row["attack_record"] for row in player_hit_reactions] !=
            ["0x00130b5c", "0x0003589e", "0x00130b8c"] or
        [row["source_attack_selector_u8"] for row in player_hit_reactions] !=
            [1, 0, 4] or
        [row["hit_kind_u8"] for row in player_hit_reactions] != [6, 9, 10] or
        [row["presentation_selector_u8"] for row in
         player_hit_reactions] != [7, 10, 11] or
        [row["active_body_selector_u8"] for row in
         player_hit_reactions] != [0, 0, 0] or
        [row["shake_count_u8"] for row in player_hit_reactions] !=
            [10, 20, 10] or
        [row["motion_index_u8"] for row in player_hit_reactions] !=
            [2, 8, 4] or
        player_hit_interruption["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        player_hit_interruption["spec_executable"] is not True or
        player_hit_interruption["guard_routine"] != "0x01a7e6" or
        player_hit_interruption["action_writer"] !=
            "0x01a892..0x01a8a0" or
        player_hit_interruption["hit_phase_dispatch_pc"] != "0x01ab52" or
        player_hit_interruption["dispatch_substate_u16"] != 0x0202 or
        player_hit_interruption["terminal_hit_visible_frame_u16"] != 3877 or
        player_hit_interruption["special_entry_visible_frame_u16"] != 3878 or
        player_hit_interruption["special_startup_visible_frame_u16"] != 3879 or
        player_hit_interruption["special_entry_state_u16"] != 0x0200 or
        player_hit_interruption["special_entry_substate_u16"] != 0x0800 or
        player_hit_interruption["mutation_control"] != {
            "reject_edge_loss_during_shake": True,
            "reject_dispatch_before_phase_0x0202": True,
            "reject_fixed_frame_special_entry": True} or
        player_hit_program["mutation_control"]["mutated_writes_u16"] != 2):
        raise ValueError("SPEC-02 Coffee Shop player HIT program drift")
    if len(spawns) != 10 or len(commands) != len(KINDS):
        raise ValueError("SPEC-02 entry cardinality drift")
    if (coffee_stage_setup["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
            coffee_stage_setup["source_frame"] != 2072 or
            coffee_stage_setup["guard"] != {
                "route_state_s16": 2,
                "player_variant_u16": 1,
                "stage_record_type_u8": "0x1c",
                "stage_record_pointer": "0x0011759a",
            } or
            coffee_stage_setup["writes"]["stage_parameter_s16"] != 8 or
            coffee_stage_setup["writes"]["rng_seed_u16"] != "0xa998"):
        raise ValueError("SPEC-02 Coffee Shop stage setup drift")
    if [int(row["sequence"]) for row in spawns] != list(range(10)):
        raise ValueError("SPEC-02 entry spawn order drift")
    if sum(LENGTHS) != len(program) or player["timer_semantics"]["loads"] != [60, 60, 44]:
        raise ValueError("SPEC-02 entry program/timer drift")
    if scheduler_order != [12, 16, 20, 24, 28, 36] or len(dispatches) != 16:
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
        [row["hurt_selector_u8"] for row in class1f_initial_actors] !=
            [1] * 10 or
        [row["attack_selector_u8"] for row in class1f_initial_actors] !=
            [1] * 10 or
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
        class1f_current_reaction["terminal_release_outer_state_u16"] != 0x0600 or
        class1f_collision_reaction_facing["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_collision_reaction_facing["source_entry"] != "0x01d416" or
        class1f_collision_reaction_facing["reaction_facing_writer"] !=
            "0x01d448" or
        class1f_collision_reaction_facing["facing_xor_writer"] !=
            "0x01d44e" or
        class1f_collision_reaction_facing["source_window_sha256"] !=
            "aab16f054a654c0cbb500ed9df53f80b56ee323a7bee89b03351f1f69f3564e6" or
        class1f_collision_reaction_facing["guard"] != {
            "excluded_target_type_u8": 0x14,
            "excluded_target_classes_u8": [0x11, 0x20, 0x10, 0x26],
            "coffee_shop_class1f_type12_reaches_writer": True,
            "coffee_shop_attack_record": "0x02fc58",
        } or
        class1f_collision_reaction_facing["facing_xor_u8"] != 1 or
        class1f_collision_reaction_facing["coffee_shop_control"] != {
            "source_frame_u16": 3830,
            "target_slot": "0x00ffa000",
            "reaction_facing_u8": 1,
            "facing_u8": 0,
            "health_s16": -1,
            "outer_state_u16": 0x0400,
        } or
        class1f_source_hit["entry_guard"]["hit_kind_actor_49_u8"] != 0x15 or
        class1f_source_hit["entry_guard"]["recovery_timer_actor_2c_u8"] != 8 or
        class1f_source_hit["reaction_table"]
            ["reaction_selector_actor_4d_u8"] != 0x36 or
        class1f_source_hit["reaction_table"]["hit_mode_actor_46_u8"] != 2 or
        class1f_source_hit["reaction_record"]["animation_record"] !=
            "0x0012e04c" or
        class1f_source_hit["reaction_record"]["assembly"] != "0x001308a6" or
        class1f_source_hit["reaction_record"]["hurt_selector_u8"] != 0 or
        class1f_source_hit["reaction_record"]["attack_selector_u8"] != 0 or
        class1f_source_hit["visible_result"]["state_u16"] != 0x0202 or
        class1f_source_hit["visible_result"]["action_phase_u16"] != 0x0002 or
        class1f_source_hit["recovery"]["next_action_phase_u16"] != 0x0200 or
        class1f_source_hit["recovery"]["transition_scheduler_boundary"] != {
            "recovery_transition_returns_before_action_dispatch": True,
            "transition_visible_source_frame": 2317,
            "transition_visible_substate_u16": 0x0200,
            "transition_visible_animation_record": "0x0012e04c",
            "transition_visible_x_fp_u32": 0x02AC4C00,
            "transition_visible_y_fp_u32": 0x0136D600,
            "launch_visible_source_frame": 2318,
            "launch_visible_substate_u16": 0x0202,
            "launch_visible_animation_record": "0x0012e05c",
            "launch_visible_x_fp_u32": 0x02AA8C00,
            "launch_visible_y_fp_u32": 0x01425600,
        } or
        class1f_source_hit["entry_writes_in_order"][1] !=
            "actor+0x2a:u8 = 4" or
        class1f_source_hit["action_dispatch"]["required_action_phases_u16"] !=
            [0x0200, 0x0202, 0x0204, 0x0206, 0x0208, 0x020A] or
        class1f_source_hit_launch["observed_written_motion"] != {
            "x_velocity_s32_16_16": -0x1C000,
            "x_acceleration_s32_16_16": 0,
            "y_velocity_s32_16_16": 0xB8000,
            "y_acceleration_s32_16_16": -0x8000} or
        class1f_source_hit_first_flight["landing_selector_u8"] != 0x37 or
        class1f_source_hit_landing_hold["captured_values_before_decrement"] !=
            [3, 2, 1] or
        class1f_source_hit_bounce["observed_motion_after_facing"] != {
            "x_velocity_s32_16_16": -0x20000,
            "x_acceleration_s32_16_16": 0x1000,
            "y_velocity_s32_16_16": 0x40000,
            "y_acceleration_s32_16_16": -0xC000} or
        class1f_source_hit_rng_hold["captured_values_before_decrement"] !=
            [10, 9, 8, 7, 6, 5, 4, 3, 2, 1] or
        len(class1f_source_hit_terminal["records"]) != 11 or
        class1f_source_hit_terminal["records"][-1]["animation_record"] !=
            "0x0012ded8" or
        len(class1f_source_hit_reaction_records) != 6 or
        class1f_source_hit_reaction_records[0]["animation_record"] !=
            "0x0012e04c" or
        class1f_source_hit_reaction_records[-1]["next_animation_record"] !=
            "0x0012e04c" or
        class1f_source_hit_landing_record["animation_record"] !=
            "0x0012ddb0" or
        class1f_source_hit_bounce_record["animation_record"] !=
            "0x0012dd9c" or
        class1f_source_hit_program["selector_context_rule"]
            ["generic_action_selector_0x36_record"] != "0x0012e410" or
        class1f_source_hit_program["selector_context_rule"]
            ["generic_action_selector_binding_forbidden"] is not True or
        class1f_source_hit_resume != {
            "source_frame": 2413,
            "dispatch_pc": "0x0607e8",
            "actor_85_style_u8": 0,
            "actor_a3_u8": 0,
            "actor_a4_u8": 1,
            "actor_a5_u8": 1,
            "actor_a6_u8": 1,
            "actor_b0_u8": 2,
            "facing_u8": 1,
            "actor_x_s16": 582,
            "actor_z_s16": 310,
            "player_x_s16": 944,
            "player_z_s16": 320,
        } or
        class1f_source_hit_rng["seed_before_u16"] != 0xEDD9 or
        class1f_source_hit_rng["seed_after_u16"] != 0xC9A2 or
        class1f_source_hit_rng["result_low_nibble_u8"] != 2 or
        class1f_source_hit_rng["timer_table_row_u8"] !=
            [10, 10, 10, 10, 40, 40, 40, 40,
             60, 60, 60, 90, 90, 90, 120, 120] or
        class1f_source_hit_rng["selected_timer_u8"] != 10):
        raise ValueError("SPEC-02 class-0x1f current-state drift")
    if (class1f_source_ko["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_source_ko["collision_visible_result"]["outer_state_u16"] !=
            0x0400 or
        class1f_source_ko_handoff["outer_state_u16"] != 0x0402 or
        class1f_source_ko_handoff["active_u8"] != 2 or
        class1f_source_ko_handoff["recovery_timer_actor_2c_u8"] != 8 or
        class1f_source_ko_handoff["reaction_selector_actor_4d_u8"] != 0x36 or
        class1f_source_ko_handoff["hit_mode_actor_46_u8"] != 0 or
        class1f_source_ko_handoff["hit_kind_actor_49_u8"] != 0x15 or
        class1f_source_ko_program["states_u16"] !=
            [0x0400, 0x0402, 0x0404, 0x0600] or
        class1f_source_ko_program["action_phases_u16"] !=
            [0, 0x0200, 0x0400, 0x0600] or
        class1f_source_ko_launch["x_velocity_s32_16_16_before_facing"] !=
            0x1C000 or
        class1f_source_ko_launch["y_velocity_s32_16_16"] != 0x98000 or
        class1f_source_ko_launch["y_acceleration_s32_16_16"] != -0x5000 or
        class1f_source_ko_landing["timer_actor_2a_u8"] != 3 or
        class1f_source_ko_bounce["x_velocity_s32_16_16_before_facing"] !=
            0x20000 or
        class1f_source_ko_bounce["y_velocity_s32_16_16"] != 0x40000 or
        class1f_source_ko_bounce["y_acceleration_s32_16_16"] != -0xC000 or
        class1f_source_ko_hold["outer_state_u16"] != 0x0404 or
        class1f_source_ko_hold["timer_actor_2a_u8"] != 60 or
        class1f_source_ko_release["outer_state_u16"] != 0x0600 or
        class1f_source_ko_release["release_writer"] != "0x0176ba" or
        class1f_source_ko_program["rng_calls"] != [] or
        len(class1f_source_ko_reaction_records) != 6 or
        class1f_source_ko_landing_record["animation_record"] !=
            "0x0012ddb0" or
        class1f_source_ko_bounce_record["animation_record"] !=
            "0x0012dd9c"):
        raise ValueError("SPEC-02 class-0x1f projectile KO drift")
    if (source_update_cadence["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        source_update_cadence["default_updates_per_source_frame_u8"] != 1 or
        [(row["source_frame_u16"], row["updates_u8"])
         for row in source_update_exceptions] !=
            [(2075, 3), (2165, 4), (2260, 0), (2265, 0)] or
        source_update_cadence["fixed_frame_gameplay_transition_forbidden"]
            is not True):
        raise ValueError("SPEC-02 Coffee Shop source update cadence drift")
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
        action_bounds["activation_field_u8"] != "actor+0x01" or
        action_bounds["latched_field_u8"] != "actor+0xa2" or
        action_bounds["camera_operand_u16"] != "0xff8278" or
        action_bounds["phase_guard_field_u8"] != "0xff8019" or
        action_bounds["phase_guard_mask_u8"] != 1 or
        action_bounds["coffee_shop_hit_return_boundary"]["phase_odd"]
            ["phase_counter_u8"] != 0x97 or
        action_bounds["coffee_shop_hit_return_boundary"]["phase_even"]
            ["relative_u16"] != "0xfff9" or
        action_bounds["coffee_shop_hit_return_boundary"]["phase_even"]
            ["next_visible_source_frame_u16"] != 2471 or
        action_bounds["x_max_u16"] != 0x05f0 or
        action_bounds["camera_relative_bias_u16"] != 0x0070 or
        action_bounds["camera_relative_span_u16"] != 0x0260 or
        action_bounds["failure_outer_state_u16"] != 0x0600 or
        action_bounds["comparison"] != "unsigned word" or
        action_bounds["coffee_shop_observation"]["result"] !=
            "pass after x_max; camera-relative test skipped" or
        action_animation_movement["source_body_sha256"] !=
            "b35c9aaf0a5328ff35e6ccb5c9d278fef7f898201fc6e005e69d11bd566a970b" or
        action_animation_movement["movement_cadence"] !=
            "only on timer expiry after binding the next animation record" or
        action_animation_movement["movement_record"] !=
            "newly bound next animation record" or
        action_direction["upper_directions_by_a5_u8"] != [0x16, 0x0a] or
        action_direction["lower_directions_by_a5_u8"] != [0x1a, 0x06] or
        action_jump["z_velocity_table_s32_16_16"] !=
            [-0x00010000, -0x00014000, -0x00018000, -0x00020000] or
        action_attack["selector_groups_u16"] !=
            [[55], [56], [43, 43, 43, 55], [43, 43, 56]] or
        action_attack["coffee_shop_observation"]["guard_field_u8"] != 1 or
        action_attack["phase_0_guard_ownership"]["field"] !=
            "actor+0x6e:u8" or
        action_attack["phase_0_guard_ownership"]["initial_group_rule"] !=
            "phase 0 performs no direct actor+0x6e write; the source selector-registration helper owns the clear before later collision can set it" or
        action_attack["phase_0_guard_ownership"]
            ["collision_set_captured_pc"] != "0x01cbba" or
        action_attack["phase_0_guard_ownership"]
            ["selector_rebind_clear_captured_pc"] != "0x01d76e" or
        action_attack["phase_0_guard_ownership"]["capture_identity"]
            ["byte_identical"] is not True or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["transition_latch_u8"] != 1 or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["a6_u8"] != 2 or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["seed_before_u16"] != 0x4bdf or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["seed_after_u16"] != 0xe3c2 or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["next_action_u8"] != 0x1a or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["selector_u8"] != 35 or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["animation_record_u32"] != "0x0012d5e4" or
        action_programs["action_0x16"]["latched_retry_transition"]
            ["fixed_frame_substitute_forbidden"] is not True or
        action_attack_timers != [30] * 4 + [60] * 4 + [120] * 4 + [160] * 4 or
        class1f_actions["suppression_control"]["writer_pc"] != "0x0607e8" or
        class1f_actions["suppression_control"]["suppressed_writes"] != 179 or
        class1f_actions["suppression_control"]["fixed_frame_substitute"] is not False or
        action_player_collision["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        action_player_collision["capture_identity"]["byte_identical"] is not True or
        action_player_collision["attacker"]["table_set"] != "0x130ac8" or
        action_player_collision["attacker"]["attack_record"] != "0x130b5c" or
        action_player_collision["attacker"]["attack_selector_u8"] != 1 or
        action_player_collision["attacker"]["hit_value_u8"] != 10 or
        action_player_collision["defender"]["table_set"] != "0x11ae02" or
        action_player_collision["defender"]["hurt_record"] != "0x11ae8e" or
        action_player_collision["defender"]["hurt_selector_u8"] != 17 or
        action_player_collision["observed_transaction"]["writer_pc"] !=
            "0x01d5ee" or
        action_player_collision["observed_transaction"]["damage_s16"] != 10 or
        action_player_collision["observed_transaction"]["hitstop_u8"] != 10 or
        action_player_collision["observed_transaction"]
            ["attack_advance_frame_u16"] != 2762):
        raise ValueError("SPEC-02 class-0x1f first-segment action drift")
    if (class1f_actions["initializer"]["variant_field_u8"] != "actor+0x03" or
        class1f_actions["initializer"]["variant_clear_writer"] != "0x0605ec" or
        class1f_actions["initializer"]["post_initialization_variant_u8"] != 0):
        raise ValueError("SPEC-02 class-0x1f initializer variant-clear drift")
    if (class1f_inner8["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        len(class1f_inner8_records) != 152 or
        len(class1f_inner8_movement_tables) != 10 or
        [row["table_index_u8"] for row in class1f_inner8_movement_tables] !=
            [4, 11, 12, 14, 15, 18, 19, 23, 25, 27] or
        class1f_inner8["entry_transition"]["timer_u16"] != 600 or
        class1f_inner8_path["action_0x00"]["captured_rng_call_counts"] != {
            "frame_3004_style_match": 4,
            "frame_3061_style_mismatch": 1,
            "frame_3282_style_mismatch": 1} or
        class1f_inner8_action6["selector_by_style"] != [
            {"style85_u8": 0, "selector_u8": 34,
             "start_animation_record": "0x0012d590"},
            {"style85_u8": 1, "selector_u8": 35,
             "start_animation_record": "0x0012d5e4"}] or
        len(class1f_inner8_action6["Coffee_Shop_observed_runs"]) != 11 or
        class1f_inner8_action6["mutation_control"]
            ["first_discriminating_source_frame"] != 3242 or
        class1f_inner8_action8["phase_2"]["Coffee_Shop_control"] != {
            "source_frame_u16": 3752,
            "source_slot": "0x00ff9dc0",
            "prior_substate_u16": "0x0802",
            "substate_u16": "0x0e00",
            "style85_u8": 0,
            "animation_record": "0x0012d678",
            "animation_timer_u16": 3,
            "animation_branch_s16": -32768} or
        class1f_inner8_action10["overlap_transition"]
            ["base_writes"]["writer"] != "0x04130e" or
        class1f_inner8_action10["overlap_transition"]
            ["style85_nonzero_override"] != {
                "guard": "actor+0x85 style85_u8 is nonzero",
                "action_u8": 8,
                "action_phase_u8": 2,
                "selector_u8": 36,
                "start_animation_record": "0x0012d628",
                "writers": ["0x041318", "0x04131e", "0x041324"]} or
        class1f_inner8_action10["overlap_transition"]
            ["Coffee_Shop_control"]["result_substate_u16"] != "0x0802" or
        class1f_inner8_action10_init["action_timer_u8"] != 4 or
        class1f_inner8_action10_init["lifetime_timer_u8"] != 240 or
        class1f_inner8_action10_init[
            "x_offset_selector_by_rng_low_nibble_u8"] !=
            [0, 0, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4] or
        class1f_inner8_action10_init["x_offsets_s16"] != [96, 112, 208] or
        class1f_inner8_action10_movement["source_entry"] != "0x0419a4" or
        class1f_inner8_action10_movement[
            "fixed_style_record_forbidden"] is not True or
        class1f_inner8_action10_movement["Coffee_Shop_control"] != {
            "source_frame_u16": 3655,
            "source_slot": "0x00ffa3c0",
            "direction_u8": 30,
            "facing_u8": 1,
            "style85_u8": 1,
            "relation_u8": 0,
            "selector_u8": 26,
            "animation_record": "0x0012d50c"} or
        class1f_inner8_action10_phase_movement["source_entry"] !=
            "0x041a00" or
        class1f_inner8_action10_phase_movement[
            "fixed_style_or_regular_movement_record_forbidden"] is not True or
        class1f_inner8_action10_phase_movement["Coffee_Shop_control"] != {
            "source_frame_u16": 3697,
            "source_slot": "0x00ff9dc0",
            "prior_substate_u16": "0x1006",
            "substate_u16": "0x1000",
            "direction_u8": 6,
            "facing_u8": 1,
            "style85_u8": 1,
            "relation_u8": 1,
            "selector_u8": 66,
            "animation_record": "0x0012ee98",
            "animation_timer_u16": 4,
            "animation_branch_s16": 19,
            "x_fp_s32_16_16": "0x0429bf00",
            "y_fp_s32_16_16": "0x01223f00",
            "z_s16": 290} or
        class1f_inner8_action4_timer["Coffee_Shop_stage_parameter_u16"] != 9 or
        class1f_inner8_action4_timer[
            "variant0_bank_by_stage_parameter_u8"][9] != 1 or
        len(class1f_inner8_action4_timer["signed_timer_banks_s8"]) != 8 or
        any(len(row) != 16 for row in
            class1f_inner8_action4_timer["signed_timer_banks_s8"]) or
        class1f_inner8_action4_timer["signed_timer_banks_s8"][1][2] != -1 or
        class1f_inner8_action2["Coffee_Shop_observed_frames"] != 79 or
        class1f_inner8_action2["presentation_binding"]
            ["selector_by_style"] != [
                {"style85_u8": 0, "selector_u8": 0,
                 "start_animation_record": "0x0012e8a8"},
                {"style85_u8": 1, "selector_u8": 1,
                 "start_animation_record": "0x0012e8ec"}] or
        class1f_inner8_action2["presentation_binding"]
            ["movement_on_bind"] is not False or
        len(class1f_inner8_action2["Coffee_Shop_observed_runs"]) != 6 or
        class1f_inner8_action2["mutation_control"]
            ["position_unchanged_on_bind"] is not True or
        class1f_inner8_terrain_tail["source_entry"] != "0x0b1baa" or
        class1f_inner8_terrain_tail[
            "Coffee_Shop_reachable_class1f_sync_guard_zero"] is not True or
        class1f_inner8_terrain_tail["mutation_control"]
            ["proposed_world_z_without_tail_s16"] != 338 or
        class1f_inner8_terrain_tail["mutation_control"]
            ["resolved_world_z_s16"] != 327 or
        class1f_inner8_terrain_tail["mutation_control"]
            ["omitted_tail_rejected"] is not True or
        class1f_inner8_action0c["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_inner8_action0c["Coffee_Shop_observed_actor_frames"] != 236 or
        class1f_inner8_action0c_phase0[
            "variant0_plan_by_rng_index_u16"][15] != 14 or
        class1f_inner8_action0c_phase0["selector_rows"][6]
            ["selector_u8"] != 48 or
        class1f_inner8_action0c_phase2["timer_row_u8"][29] != 14 or
        len(class1f_inner8_action0c_phase2["timer_rows_u8"]) != 5 or
        any(len(row) != 32 for row in
            class1f_inner8_action0c_phase2["timer_rows_u8"]) or
        class1f_inner8_action0c_phase2["timer_rows_u8"][1][29] != 14 or
        class1f_inner8_action0c_phase2["stage_offsets_u8"][11] != 32 or
        class1f_inner8_action0c_phase2[
            "fixed_observed_stage_guard_forbidden"] is not True or
        class1f_inner8_action0c["collision_damage"]
            ["Coffee_Shop_player_damage"]["damage_s16"] != 15 or
        class1f_inner8_action0c["phase_exclusive_hit_ko_dispatch_guard"]
            ["Coffee_Shop_negative_control"]["reaction_dispatch"] is not False or
        class1f_inner8_action0c["phase_exclusive_hit_ko_dispatch_guard"]
            ["accepted_reaction_state_pairs"] != [
                {"recovery_kind_u16": 1, "outer_states_u16": [0x0202]},
                {"recovery_kind_u16": 2,
                 "outer_states_u16": [0x0402, 0x0404]},
                {"recovery_kind_u16": 3,
                 "outer_states_u16": [0x0402, 0x0404]}] or
        class1f_inner8_action4["complete_dispatch_contract"]
            ["per_update_proximity_first"]["helper"] != "0x041db8" or
        class1f_inner8_action4["complete_dispatch_contract"]["clear_tail"]
            ["Coffee_Shop_control"]["animation_timer_u16"] != 5 or
        class1f_inner8_action4["complete_dispatch_contract"]
            ["mutation_control"]["omitted_clear_tail_rejected"] is not True or
        class1f_inner8_action4_contact["writer_pcs"] !=
            ["0x040cf0", "0x0419f2"] or
        class1f_inner8_action4_contact["direction_delta_u8"] != 16 or
        class1f_inner8_action4_contact["direction_mask_u8"] != 31 or
        class1f_inner8_action4_contact["Coffee_Shop_control"] != {
            "source_frame_u16": 3654,
            "source_slot": "0x00ffa3c0",
            "direction_before_u8": 14,
            "direction_after_u8": 30,
            "animation_record": "0x0012d4f8",
            "world_z_s16": 224} or
        class1f_inner8_action4["complete_dispatch_contract"]
            ["mutation_control"]
            ["omitted_post_terrain_direction_rejected"] is not True or
        class1f_inner8_action4["complete_dispatch_contract"]
            ["mutation_control"]
            ["zero_contact_direction_change_rejected"] is not True or
        class1f_inner8_motion["motion_selector_u16"] != 24 or
        class1f_inner8_motion["phase_4_arithmetic"][3] !=
            "on landing retain the accumulated y_fp unchanged; do not snap its high word to z_s16" or
        class1f_inner8_motion["phase_4_Coffee_Shop_control"]
            ["result_y_fp_s32_16_16"] != "0x013aba00" or
        class1f_inner8_motion["phase_6"] !=
            "step animation; each positive actor+0x25 event calls 0x0413d2; terminal increments phase and writes action_timer_u8=8" or
        class1f_inner8_motion["phase_8_terminal_writes"] != {
            "source_entry": "0x040e40", "action_u16": 0,
            "wander_cursor_u8": 0, "field95_u8": 0} or
        class1f_inner8_scene_clear["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_inner8_scene_clear["source_entry"] != "0x0610f6" or
        class1f_inner8_scene_clear["source_reset_helper"] != "0x0610d4" or
        class1f_inner8_scene_clear["source_action_tail"] != "0x060dcc" or
        class1f_inner8_scene_clear["result"] != {
            "outer_state_u16": 0x0200,
            "action_substate_u16": 0x1e00,
            "special_latch_ad_u8": 0,
            "inner_timer_u16": 0,
            "direction_xor_u8": 1,
            "direction_shift_u8": 4,
            "direction_bias_u8": 8,
            "selectors_by_style85_u8": [0, 1],
            "rng_calls": 0,
        } or
        class1f_inner8_scene_clear["coffee_shop_control"]
            ["first_visible_result_frame_u16"] != 5155 or
        class1f_inner8_scene_clear["mutation_control"]
            ["fixed_frame_forbidden"] is not True or
        class1f_inner8_timeout["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class1f_inner8_timeout["source_entry"] != "0x0610f6" or
        class1f_inner8_timeout["source_exit_helper"] != "0x0610d4" or
        class1f_inner8_timeout["source_window_sha256"] !=
            "e1e231c72ee8540740c632f54bcb2f960262dfd88f1b657fbce4be1d82b497cf" or
        class1f_inner8_timeout["timer_field"] != "actor+0xa8:u16" or
        class1f_inner8_timeout["writes"] != {
            "special_latch_ad_u8": 0,
            "inner_timer_u16": 0,
            "outer_state_u16": 0x0200,
            "action_substate_u16": 0,
            "direction_u8": "((a5_u8 ^ 1) << 4) + 8",
        } or
        class1f_inner8_timeout["source_exit_window_sha256"] !=
            "6b09506d487a9af8c04d737045639bd17c60f20cfc96530015bfd1e31703c70a" or
        class1f_inner8_timeout["coffee_shop_control"]
            ["return_frame_u16"] != 3881 or
        class1f_inner8_timeout["coffee_shop_control"]
            ["direction_writer_pc"] != "0x0610f0" or
        class1f_inner8_timeout["coffee_shop_control"]
            ["direction_after_u8"] != 8 or
        class1f_inner8_tables["field88_by_rng_low_nibble_u8"] !=
            [1, 2, 1, 2, 1, 1, 2, 1, 2, 1, 1, 1, 1, 2, 1, 2] or
        len(class1f_inner8_tables["wander_direction_delta_same_style_u8"]) != 32 or
        len(class1f_inner8_tables["direction_octant_base_u8"]) != 32 or
        [row["start_animation_record"] for row in
         class1f_inner8_movement_selectors] !=
            ["0x0012d380", "0x0012d404", "0x0012d488", "0x0012d50c"] or
        [row["start_animation_record"] for row in
         class1f_inner8_action10_phase_selectors] !=
            ["0x0012ed90", "0x0012ee14",
             "0x0012ee98", "0x0012ef1c"] or
        class1f_inner8_path["fixed_frame_or_authored_transition_forbidden"]
            is not True):
        raise ValueError("SPEC-02 class-0x1f inner-state 0x08 drift")
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
        recurring_camera_edge["observed_transition"] != {
            "camera_x_s16": 832, "field44_after_u16": 1,
            "field46_after_u16": 837, "field46_before_u16": 838,
            "field48_u16": 2100,
            "progress_snapshot_writer_pc": "0x02895e",
            "progress_u16": 1, "substate_after_u16": 0x0200,
            "substate_before_u16": 0, "visible_frame_u16": 2680,
            "writer_frame_u16": 2679, "writer_pc": "0x02894e"} or
        recurring_camera_edge["native_adapter_binding"] != {
            "source_read": "camera_x_s16 at controller dispatch",
            "runtime_field": "camera_x_position",
            "reason": "the corrected native player/camera chronology has camera_x_position=832 and camera_x_previous=830 at source writer frame 2679; the source controller reads the current 0xff8278 camera value 832 before writing the edge transition"} or
        recurring_camera_edge["transition_values"] != {
            "camera_edge_x_s16": 832,
            "conditional_local_0x2c_u8": 0,
            "conditional_phase_0x2e_u8": 1,
            "field46_phase_threshold_u16": 600} or
        recurring_camera_edge["mutation_control"]
            ["fixed_frame_substitute"] is not False or
        recurring_camera_edge["mutation_control"]
            ["accepted_current_camera_x_s16"] != 832 or
        recurring_camera_edge["mutation_control"]
            ["rejected_previous_camera_x_s16"] != 830 or
        recurring_camera_edge["mutation_control"]
            ["previous_runtime_sample_rejected"] is not True or
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
        recurring["phase_counter"]["native_entry_handoff_value_u8"] != 0x06 or
        recurring["phase_counter"]["native_entry_handoff_frame_u16"] != 2072 or
        recurring["controller_guard"]["first_spawn_index_transition"] != {
            "source_frame_u16": 2510, "before_u16": 9,
            "after_u16": 8,
            "guard": "successful primary record-12 allocation"} or
        recurring_post_allocation != {
            "state_u16": 0x0200, "substate_u16": 0,
            "facing_u8": 1, "health_s16": 87,
            "animation_record": "0x0012ddb0",
            "animation_timer_u16": 0x0fff,
            "animation_branch_s16": -0x8000,
            "assembly": "0x00130346",
            "hurt_selector_u8": 1, "attack_selector_u8": 1} or
        recurring_primary["post_allocation_dispatch"]
            ["presentation_ownership"] != "reused_record_residue" or
        recurring_primary["post_allocation_dispatch"]
            ["presentation_writer_pcs"] != [] or
        recurring_auxiliary["post_allocation_dispatch"]
            ["presentation_ownership"] != "reused_record_residue" or
        recurring_auxiliary["post_allocation_dispatch"]
            ["presentation_writer_pcs"] != [] or
        recurring_auxiliary["post_allocation_dispatch"]["source_samples"]
            ["post_allocation_frame_2572"]["animation_record"] !=
                "0x0012e778" or
        recurring_auxiliary["post_allocation_dispatch"]["source_samples"]
            ["first_action_frame_2573"]["logical_selector_u8"] != 0x35 or
        action_fall["initial_selector_u8"] != 0x35 or
        action_fall["middle_selector_u8"] != 0x36 or
        recurring_fixed_point_reuse["field_types"] != {
            "x_fp": "s32 16.16", "y_fp": "s32 16.16",
            "x_writer": "s16 high word", "y_writer": "s16 high word"} or
        recurring_fixed_point_reuse["source_samples"]
            ["post_allocation_frame_2511"] != {
                "x_fp_s32": "0x02a08000", "y_fp_s32": "0x01489000"} or
        recurring_fixed_point_reuse["mutation_control"]
            ["rejected_frame_2514"] != {
                "x_fp_s32": "0x02a76200", "y_fp_s32": "0x01467900"} or
        recurring_fixed_point_reuse["spec_executable"] is not True or
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
        recurring_auxiliary["rng_calls"] != 0 or
        recurring_progress["writer_pc"] != "0x061070" or
        recurring_progress["transition_guard"] != {
            "record_type_u8": 12, "class_u8": "0x1f",
            "state_u16": 0x0402, "substate_u16": 0,
            "health_s16": -1} or
        recurring_progress["increment_u16"] != 1 or
        len(recurring_progress["observed_transactions"]) != 20 or
        recurring_progress["observed_transactions"][-1] != {
            "frame": 5150, "slot": "0xff9c40",
            "progress_before_u16": 19, "progress_after_u16": 20} or
        recurring_progress["mutation_control"]["fixed_frame_substitute"] is not
            False or
        coffee_exit["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        coffee_exit["spec_executable"] is not True or
        [row["substate_u16"] for row in coffee_exit_controller["phases"]] !=
            [0x0200, 0x0400, 0x0600] or
        coffee_exit_controller["withdrawal_visibility"] != {
            "scheduler_write_source_frame_u16": 5151,
            "source_visible_frame_u16": 5152,
            "source_visible_timer_u16": 300,
            "first_decrement_visible_frame_u16": 5153,
            "first_decrement_timer_u16": 299,
            "route_state_during_transition_s16": 4,
            "player_update_after_controller_same_source_frame": True,
            "source_observations": [
                {"frame_u16": 5150, "state_u16": 0x0204,
                 "substate_u16": 0x0600, "timer42_u16": 0xffff,
                 "progress_u16": 19},
                {"frame_u16": 5151, "state_u16": 0x0204,
                 "substate_u16": 0x0600, "timer42_u16": 0xffff,
                 "progress_u16": 20},
                {"frame_u16": 5152, "state_u16": 0x0400,
                 "substate_u16": 0, "timer42_u16": 300,
                 "progress_u16": 20},
                {"frame_u16": 5153, "state_u16": 0x0400,
                 "substate_u16": 0, "timer42_u16": 299,
                 "progress_u16": 20},
            ],
        } or
        coffee_exit_handoff["controller_gate_writer"] != "0x028bba" or
        coffee_exit_handoff["gate_write_source_frame_u16"] != 5451 or
        coffee_exit_handoff["gate_visible_frame_u16"] != 5452 or
        coffee_exit_handoff["route_dispatcher"] !=
            "0x00840a..0x008438" or
        coffee_exit_handoff["route_writer"] != "0x008418" or
        coffee_exit_handoff["route_write_source_frame_u16"] != 5452 or
        coffee_exit_handoff["route_visible_frame_u16"] != 5453 or
        coffee_exit_handoff["same_invocation_gate_consumption"] is not
            False or
        coffee_exit_handoff[
            "player_gameplay_update_after_gate_write_same_source_frame"] is
            not True or
        [(row["frame_u16"], row["route_state_s16"],
          row["player_state_u16"], row["timer42_u16"],
          row["player_substate_u16"], row["player_x_fp_s32_16_16"],
          row["player_y_fp_s32_16_16"],
          row["player_animation_record_u32"],
          row["player_animation_timer_u16"],
          row["player_animation_branch_s16"], row["player_facing_u8"],
          row["player_action_timer_u16"])
         for row in coffee_exit_handoff["source_observations"]] != [
            (5451, 4, 0x0200, 1, 0x0202, 0x05509000, 0x013fa800,
             0x0015f218, 2, 0, 1, 0),
            (5452, 4, 0x0200, 0, 0x0204, 0x05509000, 0x013fa800,
             0x0015f218, 1, 0, 1, 0x0a00),
            (5453, 6, 0x0800, 0, 0, 0x05509000, 0x013fa800,
             0x0015f218, 1, 0, 1, 0x0a00)] or
        coffee_exit_handoff["player_gate_transition_rule"] != {
            "guard": "u8(g81f3) becomes nonzero before the player pool update",
            "movement": "suppress the pending directional delta and preserve signed 16.16 x/y",
            "transition": "player substate 0x0202 -> 0x0204 while the current walk record advances once",
            "route_handoff": "the following 0x008418 route write changes outer state to 0x0800 without truncating either fixed-point fraction",
        } or
        coffee_exit_controller["withdrawal"]["timer_u16"] != 300 or
        coffee_exit_controller["withdrawal"]
            ["living_enemy_count_is_not_a_guard"] is not True or
        [(row["from_s16"], row["to_s16"], row["source_write_frame_u16"])
         for row in coffee_exit["route_edges"]] !=
            [(4, 6, 5452), (6, 0, 5523), (0, 2, 5561)] or
        [row["cursor"] for row in coffee_exit_script["steps"]] != [
            "0x00129b64", "0x00129b68", "0x00129b6e",
            "0x00129b70", "0x00129b74", "0x00129b78",
            "0x00129b7a", "0x00129b80", "0x00129b84"] or
        len(coffee_exit_script["motion_vectors"]) != 32 or
        coffee_exit_script["motion_vectors"][8] !=
            {"x_s16": 576, "z_s16": 0} or
        coffee_exit_script["steps"][5]["kind"] != "ballistic" or
        len(coffee_exit_callbacks["groups"]) != 25 or
        sum(row["display_ticks_u8"] for row in
            coffee_exit_callbacks["groups"]) != 71 or
        len(coffee_exit_callbacks["fixed_pool_scheduler_groups"]) != 16 or
        sum(row["display_ticks_u8"] for row in
            coffee_exit_callbacks["fixed_pool_scheduler_groups"]) != 71 or
        coffee_exit_callbacks["fixed_pool_timer_witness"]
            ["projection_sha256"] !=
            "0bb621d48e4b77e591f9f6f48bc9d0632b5424cf1767acb568c912228f3fc497" or
        coffee_exit_ballistic["selector_u8"] != 6 or
        tuple(coffee_exit_ballistic[name] for name in
              ("x_velocity_s32", "x_acceleration_s32",
               "y_velocity_s32", "y_acceleration_s32")) !=
            (0x50000, -0x1000, 0x80000, -0x6000) or
        [row["display_frames_u16"] for row in
         coffee_exit_route_zero["resident_load_stalls"]] != [26, 9, 1] or
        coffee_exit_next_scene["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        coffee_exit_next_scene["camera_reset_visible_frame_u16"] != 5563 or
        coffee_exit_next_scene["camera_reset_x_s16"] != 0 or
        coffee_exit_next_scene["camera_reset_z_s16"] != 0 or
        coffee_exit_next_scene["camera_reset_target_x_s16"] != 128 or
        coffee_exit_next_scene["player_position_visible_frame_u16"] != 5564 or
        coffee_exit_next_scene["entry_controller_visible_frame_u16"] != 5566 or
        coffee_exit_next_scene["player_x_fp_s32_16_16"] != 0x04009200 or
        coffee_exit_next_scene["player_y_fp_s32_16_16"] != 0x0120d000 or
        coffee_exit_next_scene["player_z_s16"] != 288 or
        coffee_exit_next_scene["player_state_u16"] != 0x0800 or
        coffee_exit_next_scene["player_substate_u16"] != 0 or
        coffee_exit_next_scene["player_facing_before_controller_u8"] != 1 or
        coffee_exit_next_scene["player_facing_after_controller_u8"] != 0 or
        coffee_exit_next_scene["camera_x_s16"] != 776 or
        coffee_exit_next_scene["camera_z_s16"] != 224 or
        coffee_exit_next_scene["camera_target_x_s16"] != 776 or
        coffee_exit_next_scene["entry_controller_state_u16"] != 0x0200 or
        any(row["native_binding"] != "ADAPTED_PRESENTATION_RESIDENCY_NOOP"
            for row in coffee_exit["load_boundaries"])):
        raise ValueError("SPEC-02 first-segment recurring spawn drift")
    if (class08_pickup["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class08_pickup["spec_executable"] is not True or
        class08_pickup["fixed_frame_substitute_forbidden"] is not True or
        class08_pickup["stage_spawn"]["record"] != {
            "allocator_selector_u16": 4,
            "character_guard_u8": 0,
            "class_variant_word_u16": "0x0800",
            "gate_u16": 816,
            "lane_guard_s8": 0,
            "x_s16": 1280,
            "y_s16": 317} or
        class08_pickup["parent"]["source_slot"] != "0x00ffb200" or
        class08_pickup["parent"]["record_type_u8"] != 20 or
        class08_pickup["parent"]["class_u8"] != "0x08" or
        class08_pickup["parent"]["current_state_collision"]
            ["attack_record"]["address"] != "0x0002fc58" or
        class08_pickup["parent"]["current_state_collision"]
            ["reaction_direction"]["result_u8"] != 1 or
        class08_pickup["parent"]["current_state_collision"]
            ["reaction_direction"]["visible_witness"] != {
                "impact_source_slot": "0x00ffb680",
                "impact_visible_frame_u16": 2906,
                "impact_facing_u8": 1} or
        class08_pickup["parent"]["drop"]["seed_before"] != "0x8be5" or
        class08_pickup["parent"]["drop"]["seed_after"] != "0xa388" or
        class08_pickup["parent"]["drop"]["selector_source"]
            ["row_u8"] != [0x12] * 32 or
        class08_pickup["parent"]["state_sequence_u16"] !=
            [0,0x0200,0x0400,0x0402,0x0404,0x0604] or
        class08_pickup["parent"]["post_drop_program"]["debris"]
            ["primary"]["x_velocity_s32"] != 0x00050000 or
        not class08_pickup["parent"]["post_drop_program"]["debris"]
            ["internal_coordinate_format"].startswith(
                "two signed 24.8 trajectories") or
        not class08_pickup["parent"]["post_drop_program"]["debris"]
            ["visible_position_projection"].startswith(
                "0x06d72e copies only") or
        class08_pickup["parent"]["post_drop_program"]["debris"]
            ["alternate"]["freeze_result"] != {
                "x_fp_s32":0x05580000,"y_fp_s32":0x01370000} or
        class08_pickup["pickup"]["source_slot"] != "0x00ffcd00" or
        class08_pickup["pickup"]["record_type_u8"] != 28 or
        class08_pickup["pickup"]["class_u8"] != "0x0a" or
        class08_pickup["pickup"]["subtype_u8"] != "0x12" or
        class08_pickup["pickup"]["initialization"]
            ["motion_substate_u16"] != 0x0002 or
        class08_pickup["pickup"]["movement"]["first_landing_result"]
            ["position_write"] !=
            "replace only y_fp high word with ground_z and preserve the current fractional low word" or
        class08_pickup["pickup"]["movement"]["second_landing_result"]
            ["position_write"] !=
            "replace only y_fp high word with ground_z and preserve the current fractional low word" or
        "including the substate-0 to substate-2 update" not in
            class08_pickup["pickup"]["movement"]["animation_timer_rule"] or
        class08_pickup["pickup"]["player_interaction"]["action_u16"] !=
            "0x0e00" or
        not class08_pickup["pickup"]["player_interaction"]
            ["input_sample_rule"].startswith(
                "the eligible current-frame target/input guard latches pickup ownership") or
        class08_pickup["pickup"]["player_interaction"]["health_cap_s16"] !=
            101 or
        class08_pickup["pickup"]["player_interaction"]["audio_edge"]
            ["command_u16"] != "0x0206" or
        len(class08_pickup["pickup"]["player_interaction"]
            ["presentation_records"]) != 2):
        raise ValueError("SPEC-02 Coffee Shop class-0x08 pickup drift")
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
        [(row["seed_before"], row["seed_after"], row["table_index"])
         for row in class4e_rng] !=
            [("0xcdb5", "0x691e", 28), ("0x691e", "0x3b59", 24)] or
        len(class4e["jitter_table_s16"]) != 8 or
        len(class4e["animation_records"]) != 5 or
        class4e["terminal_transition"]["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class4e["terminal_transition"]["source_slots"] !=
            ["0x00ffc480", "0x00ffc500"] or
        class4e["terminal_transition"]["before"] != {
            "visible_frame_u16": 2258, "state_u16": "0x0200",
            "animation_record": "0x000929f0", "timer_u16": 4095,
            "branch_s16": -32768} or
        class4e["terminal_transition"]["after"] != {
            "visible_frame_u16": 2259, "state_u16": "0x0400",
            "animation_record": "0x000929f0", "timer_u16": 4094,
            "branch_s16": -32768} or
        class4e["terminal_transition"]["mutation_control"] !=
            "reject state advance before terminal timer decrement" or
        class4e_variant0["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class4e_variant0["scene_lifetime_count_u16"] != 2 or
        class4e_variant0["first_collision"]["attacker_attack_record"] !=
            "0x00130b5c" or
        class4e_variant0["first_collision"]["defender_hurt_record"] !=
            "0x0011ae8e" or
        class4e_variant0["allocation"]["source_slot"] != "0x00ffc300" or
        class4e_variant0["allocation"]["variant_field"]["variant_u8"] != 0 or
        class4e_variant0["allocation"]["first_spawn_position_s16"] !=
            [1095, 369, 319] or
        class4e_variant0["state0"]["first_seed_before"] != "0xeea3" or
        class4e_variant0["state0"]["first_seed_after"] != "0xcb6e" or
        class4e_variant0["state0"]["first_table_offset_u8"] != 12 or
        len(class4e_variant0["active_state"]["animation_records"]) != 3 or
        class4e_variant0["release_state"]["first_absent_frame"] != 2762 or
        class4e_variant0["fixed_frame_substitute_forbidden"] is not True or
        class4e_variant1["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class4e_variant1["scene_lifetime_count_u16"] != 23 or
        class4e_variant1["first_collision"]["attacker_attack_record"] !=
            "0x00030cd2" or
        class4e_variant1["allocation"]["variant_u8"] != 1 or
        class4e_variant1["allocation"]["first_spawn_position_s16"] !=
            [717, 336, 309] or
        class4e_variant1["state0"]["first_seed_before"] != "0x19c4" or
        class4e_variant1["state0"]["first_seed_after"] != "0x4d11" or
        len(class4e_variant1["active_state"]["animation_records"]) != 3 or
        player_special_target_collision["source_frame_u16"] != 2804 or
        player_special_target_collision["attack_selector_u8"] != 11 or
        player_special_target_collision["attack_record"]["address"] !=
            "0x0011af76" or
        player_special_target_collision["class1f_target"]["source_slot"] !=
            "0x00ffa240" or
        player_special_target_collision["class1f_target"]["hurt_record"]
            ["address"] != "0x00130ad4" or
        player_special_target_collision["class1f_target"]["damage_s16"] != 127 or
        player_special_target_collision["class1f_target"]
            ["health_after_clamp_s16"] != -1 or
        player_special_target_collision["class1f_traversal_cadence"] != {
            "max_damage_targets_per_frame_u8": 1,
            "registration_retained_after_contact": True,
            "next_frame_resumes_after_ineligible_prior_targets": True,
            "coffee_shop_witnesses": [
                {"source_frame_u16": 4394,
                 "source_slot": "0x00ff9c40"},
                {"source_frame_u16": 4395,
                 "source_slot": "0x00ff9e80"}]} or
        player_special_target_collision["impact_allocation"]["variant_u8"] != 1 or
        len(player_special_target_collision["record20_targets"]) != 2 or
        class4e_variant1["fixed_frame_substitute_forbidden"] is not True or
        class4e_variant10["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class4e_variant10["scene_lifetime_count_u16"] != 5 or
        class4e_variant10["first_collision"]["attacker_attack_record"] !=
            "0x0002fc58" or
        class4e_variant10["allocation"]["variant_field"] != {
            "attack_record_offset_u8": 8, "type": "u8", "signed": False,
            "rule": "copy absolute signed byte at attack-record +0x08",
            "raw_u8": 10, "variant_u8": 10} or
        class4e_variant10["allocation"]["first_spawn_position_s16"] !=
            [833, 325, 311] or
        class4e_variant10["state0"]["first_seed_before"] != "0x37cd" or
        class4e_variant10["state0"]["first_seed_after"] != "0xa774" or
        class4e_variant10["state0"]["first_table_offset_u8"] != 20 or
        len(class4e_variant10["active_state"]["animation_records"]) != 6 or
        class4e_variant10["release_state"]["first_absent_frame"] != 2371 or
        class4e_variant10["fixed_frame_substitute_forbidden"] is not True or
        class4e_variant5["variant_u8"] != 5 or
        len(class4e_variant5["animation_records"]) != 5 or
        [row["visible_frame_u16"] for row in
         class4e_variant5["allocations"]] != [4034] or
        class4e_variant20["variant_u8"] != 20 or
        len(class4e_variant20["animation_records"]) != 8 or
        [row["visible_frame_u16"] for row in
         class4e_variant20["allocations"]] != [3264, 3856] or
        any(row["scheduler_rule"] !=
            "collision allocation occurs after the type-24 pool; state-0 initialization and RNG occur on the next source frame"
            for row in (class4e_variant5, class4e_variant20)) or
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
        class44["second_player_origin_command_frame"] != 2255 or
        class45["dispatch"] != "0x08dc1c" or
        len(class45["source_slots_scheduler_order"]) != 28 or
        class45["source_slots_scheduler_order"][0] != "0x00ffb680" or
        class45["source_slots_scheduler_order"][-1] != "0x00ffc400" or
        len(class45["spawn_owner"]["groups"]) != 3 or
        len(class45["state0"]["animation_selector_table_u8"]) != 32 or
        len(class45["state0"]["animation_records"]) != 5 or
        len(class45["state0"]["motion_table"]) != 8 or
        class45["rng_calls_per_actor_u8"] != 7 or
        class45["fixed_frame_substitute_forbidden"] is not True or
        class47["classification"] != "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class47["dispatch"] != "0x08eb86" or
        class47["spawn_routine"] != "0x08eb1c" or
        class47["record_type_u8"] != 24 or
        class47["class_u8"] != "0x47" or
        class47["variant_u8"] != 0 or
        class47["spawn_owner"]["source_slot"] != "0x00ffb300" or
        class47["spawn_owner"]["caller_pc"] != "0x06b61a" or
        class47["spawn_owner"]["attempts_u16"] != 4 or
        len(class47["source_slots_scheduler_order"]) != 4 or
        len(class47["state0"]["animation_selector_table_u8"]) != 32 or
        len(class47["state0"]["animation_records"]) != 9 or
        len(class47["state0"]["motion_table"]) != 8 or
        class47["rng_calls_per_actor_u8"] != 7 or
        class47["rng_calls_total_u16"] != 28 or
        class47["fixed_frame_substitute_forbidden"] is not True or
        class16["classification"] != "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class16["spec_executable"] is not True or
        class16["record_type_u8"] != 16 or
        class16["class_u8"] != "0x06" or
        class16["dispatch"] != "0x03537e" or
        class16["state_sequence_u16"] != [0, 0x0200, 0x0400, 0x0600] or
        len(class16["initialization"]["variant_motion_16_16"]) != 3 or
        len(class16["spawn_owner"]["parent_animation_records"]) != 11 or
        len(class16["active_state"]["animation_records"]) != 4 or
        len(class16["terminal_state"]["animation_records"]) != 7 or
        class16["current_state_collision"]["attack_record"]["address"] !=
            "0x0003589e" or
        class16["current_state_collision"]["player_hurt_selector_u8"] != 17 or
        class16["current_state_collision"]["player_hurt_record"]["address"] !=
            "0x0011ae8e" or
        class16["current_state_collision"]["route_character_damage_s16"] != 17 or
        class16["rng_calls"] != 0 or
        class16["fixed_frame_substitute_forbidden"] is not True):
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
        len(terrain_selector_runs) != 383 or
        bytes(selector for length, selector in terrain_selector_runs
              for _ in range(length)) != terrain_selectors or
        hashlib.sha256(terrain_packed).hexdigest() !=
            terrain_grid["packed_sha256"] or
        [row["selector_u8"] for row in terrain_records] !=
            [0, 4, 8, 20, 24, 56, 96, 100, 164] or
        [row["record_bytes"] for row in terrain_records] != [
            "0080808080808080", "0200808010100080",
            "0202808010100080", "020080801010ff80",
            "020280801010ff80", "0202808010080080",
            "0604020100008080",
            "0604020100088080", "0402020100088080"] or
        terrain_stream["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        terrain_stream["initial_phase_x_u8"] != 0x10 or
        terrain_stream["transaction_count_u16"] != 41 or
        terrain_stream["write_count_u16"] != 1476 or
        len(terrain_stream_transactions) != 41 or
        len(terrain_stream_writes) != 1476 or
        any(transaction["write_count_u8"] != 36 or
            len(transaction["writes"]) != 36
            for transaction in terrain_stream_transactions) or
        terrain_stream["mutation_control"] != {
            "suppressed_writer": "0x0b2832",
            "mutated_writes_u16": 828,
            "baseline_frame_3578_player_z_s16": 319,
            "mutant_frame_3578_player_z_s16": 320,
            "fixed_frame_or_static_snapshot_substitute_rejected": True,
        }):
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
    if (obstacle_lifecycle["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        obstacle_lifecycle["source_scene_record"]["camera_threshold_u16"] != 688 or
        obstacle_lifecycle["spawn"]["slot"] != "0xffb380" or
        not obstacle_lifecycle["spawn"]["camera_sample_order"]["native_rule"].startswith(
            "scheduler guard uses camera_x_previous") or
        obstacle_lifecycle["initializer"]["child_allocation"]["variant_order_u8"] !=
            [3, 2, 1, 0] or
        obstacle_lifecycle["initializer"]["child_allocation"]["source_slots_in_allocation_order"] !=
            ["0xffe240", "0xffe200", "0xffe1c0", "0xffe180"] or
        [len(obstacle_child_sequences[str(index)]) for index in range(4)] !=
            [5, 8, 6, 6] or
        obstacle_child["release_record"]["animation_record"] != "0x09bd90" or
        obstacle_child["dispatch_table"]["offsets_u16"] != [8, 48, 82, 82] or
        obstacle_child["state_program"]["state_0200"]["guard"] !=
            "u8(parent+0x04) >= 4" or
        obstacle_player_attack != {
            "address": "0x11af76", "x_center_s8": 0,
            "y_center_s8": 48, "x_half_u8": 88,
            "y_half_u8": 48, "z_center_s8": 0,
            "z_half_u8": 40, "hit_value_u8": 3,
            "knockback_mode_s8": 1, "damage_s16": 25} or
        obstacle_hurt != {
            "address": "0x06e21c", "x_center_s8": 0,
            "y_center_s8": 64, "x_half_u8": 16,
            "y_half_u8": 64, "z_center_s8": 0,
            "z_half_u8": 6} or
        obstacle_break["presentation_rng_transaction"]["calls_u8"] != 1 or
        obstacle_break["presentation_rng_transaction"]["rng_entry"] !=
            "0x017c5e" or
        obstacle_break["presentation_rng_transaction"]["rng_call_pc"] !=
            "0x0bc6b4" or
        obstacle_break["audio_transaction"]["command_u16"] != "0x0142" or
        obstacle_break["audio_transaction"]["arguments_u32"] !=
            ["0x00000142", "0x00001b00", "0x00000000"] or
        obstacle_state_program["state_0404"]["transition_initialization_order"]
            ["source_update_frame"] != 2815 or
        obstacle_state_program["state_0404"]["transition_initialization_order"]
            ["fixed_frame_delay_forbidden"] is not True or
        obstacle_state_program["state_0404"]["channel_seeds"]["primary"]
            ["fp68_u32"] != "0x01730002" or
        obstacle_state_program["state_0404"]["channel_seeds"]["alternate"]
            ["animation_record"] != "0x06e182" or
        obstacle_state_program["state_0404"]["direction_control"]["field"] !=
            "actor+0x4f:u8" or
        obstacle_state_program["state_0404"]["selection_witness"][1] != {
            "frame": 2817, "channel": "alternate", "x_s16": 1127,
            "y_s16": 328, "animation_record": "0x06e182"} or
        obstacle_lifecycle["transition_suppression"]["suppressed_writes"] != 18 or
        obstacle_lifecycle["fixed_frame_substitute_forbidden"] is not True):
        raise ValueError("SPEC-02 Coffee Shop obstacle lifecycle drift")
    if (camera["x_target_arithmetic"]["speed_table_u16"] !=
            [0, 1, 1, 2, 3, 4, 5, 6, 7, 7,
             8, 8, 9, 9, 10, 10, 11, 11, 11, 11] or
        camera_operands != {
            "countdown_initial_u16": 1200,
            "countdown_tick_rule":
                "decrement once per controller update while phase is 2",
            "counter_u16": 0, "snapshot_u16": 0,
            "threshold_byte_u8": 1, "threshold_ticks": 16} or
        camera["initialization"]["first_control_chronology"] != [
            {"source_frame_u16": 2237, "route_state_s16": 2,
             "player_x_s16": 944, "camera_x_s16": 640,
             "camera_target_x_s16": 640},
            {"source_frame_u16": 2238, "route_state_s16": 4,
             "player_x_s16": 944, "camera_x_s16": 648,
             "camera_target_x_s16": 648},
            {"source_frame_u16": 2239, "route_state_s16": 4,
             "player_x_s16": 944, "camera_x_s16": 655,
             "camera_target_x_s16": 655}] or
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
            "neutral performs no +0x0f write and preserves the last directional facing" or
        locomotion_execution["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        locomotion_execution["spec_executable"] is not True or
        locomotion_pipeline["direction_latency_samples"] != 2 or
        locomotion_pipeline["first_visible_result"] != {
            "frame": 2602, "state_u16": "0x0200",
            "substate_u16": "0x0200", "facing_u8": 1,
            "x_fp_s16_16": "0x03b24000",
            "animation_record": "0x0015f208",
            "assembly": "0x00160a02", "animation_timer_u16": 4,
            "current_hurt_selector_u8": 17,
            "current_attack_selector_u8": 0} or
        locomotion_execution["movement"]["right_delta_s16_16"] !=
            "0x00024000" or
        locomotion_presentation["ticks_per_record"] != 4 or
        locomotion_execution["current_collision_selector_projection"] != {
            "guard": "the current locomotion animation record owns collision lookup metadata",
            "actor_hurt_selector_u8": 17,
            "actor_attack_selector_u8": 0,
            "collision_lookup_hurt_selector_u8": 17,
            "rule": "native current selectors derive from animation-record bytes +0x08/+0x09; captured actor event/link bytes are rejected",
            "source_frames": [2602, 2678]} or
        len(locomotion_records) != 12 or
        [row["animation_record"] for row in locomotion_records] !=
            [f"0x{address:06x}" for address in
             range(0x15F208, 0x15F2B9, 0x10)] or
        locomotion_records[0]["assembly"] != "0x160a02" or
        locomotion_records[-1]["assembly"] != "0x160b9e"):
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
    if (contextual_melee["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        contextual_melee["spec_executable"] is not True or
        contextual_melee["target_link"]["target_low_u16"] != 0xce00 or
        contextual_melee["target_link"]["source_frame_u16"] != 2074 or
        contextual_melee["target_link"]["player_to_target_writer"] !=
            "0x0212ce" or
        contextual_melee["target_link"]
            ["target_actor_program_spec_executable"] is not False or
        contextual_melee["dispatch"]["entry_action_u16"] != 0x1400 or
        contextual_melee["dispatch"]["active_action_u16"] != 0x1402 or
        [row["selector_u8"] for row in contextual_sequences] != [21, 20] or
        [len(row["records"]) for row in contextual_sequences] != [5, 6] or
        contextual_melee["movement"]["rng_calls"] != [] or
        [row["command_u16"] for row in contextual_melee["audio_edges"]] !=
            [0x0036, 0x0101]):
        raise ValueError("SPEC-02 contextual Button2 contract drift")
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
            "same_facing_horizontal"]["presentation_level_u8"] != 5 or
        jump["initialization"]["non_down"][
            "opposite_facing_horizontal"]["collision_level_u8"] != 8 or
        jump["initialization"]["down"]["collision_selector_u8"] != 7 or
        jump["motion_and_landing"]["landing_0x023630"][
            "presentation_selector_u8"] != 10 or
        jump["motion_and_landing"]["phase_0x040a"][
            "negative_velocity_transition"]["phase_timer_s16"] != 10 or
        jump_witness["physical_input_frame"] != 3440 or
        jump_witness["pipeline_edge_frame"] != 3441 or
        jump_witness["jump_dispatch_frame"] != 3442 or
        jump_witness["landing_frame"] != 3482 or
        jump_witness["neutral_return_frame"] != 3484 or
        jump_witness["presentation_selector_u8"] != 5 or
        len(jump_witness["chronology"]) != 46 or
        jump_witness["chronology"][-1]["animation_timer_u16"] != 4095 or
        jump_witness["chronology"][-1]["animation_branch_s16"] != -32768 or
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
        weapon["source_input"]["native_input_pipeline_updates_u8"] != 1 or
        weapon["source_input"]["action_dispatch_delay_updates_u8"] != 1 or
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
        weapon_action["resource_debit_tick"] != 1 or
        weapon_action["parent_allocation_tick"] != 1 or
        weapon_action["recharge_countdown_after_entry_u8"] != 12 or
        weapon_action["rng_calls"] != [] or
        weapon_stage_progress["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        weapon_stage_progress["spec_executable"] is not True or
        weapon_stage_progress["caller"]["player_state_program"] !=
            "0x024060" or
        weapon_stage_progress["caller"]["delta_load_pc"] != "0x024094" or
        weapon_stage_progress["caller"]["helper_call_pc"] != "0x024096" or
        weapon_stage_progress["caller"]["delta_u16"] != 3 or
        weapon_stage_progress["caller"]["action_entry_tick_u8"] != 0 or
        weapon_stage_progress_helper["entry"] != "0x0179e2" or
        weapon_stage_progress_helper["return"] != "0x017b74" or
        weapon_stage_progress_helper["guard"] != {
            "field": "a5+0x01b0:u8",
            "predicate": "u8(a5+0x01b0) == 0",
            "checked_before_add_and_before_route_bounds": True} or
        weapon_stage_progress_layout != {
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
                         "signed": False}} or
        weapon_stage_progress_helper["progress_threshold_u16"] != 8 or
        weapon_stage_progress_helper["progress_mask_u16"] != 7 or
        weapon_stage_progress_helper["stage_domain_limit_u16"] != 32 or
        weapon_stage_progress_helper["stage_domain_mask_u16"] != 31 or
        weapon_stage_progress_helper["coffee_shop_lower_bound_s16"] != 8 or
        weapon_stage_progress_helper["coffee_shop_upper_bound_s16"] != 16 or
        weapon_stage_progress_helper["rng_calls"] != [] or
        [(row["source_frame_u16"], row["progress_before_u16"],
          row["progress_after_add_u16"], row["progress_after_mask_u16"],
          row["stage_before_s16"], row["stage_after_s16"])
         for row in weapon_stage_progress["coffee_shop_calls"][:3]] != [
            (2252, 0, 3, 3, 8, 8),
            (2342, 3, 6, 6, 8, 8),
            (2432, 6, 9, 1, 8, 9)] or
        len(weapon_stage_progress["coffee_shop_calls"]) != 15 or
        weapon_stage_progress["capture_identity"][
            "byte_identical_selected_rows"] is not True or
        weapon_stage_progress["fixed_frame_substitute"] is not False or
        weapon_resource["dispatch_guard"]["routine"] != "0x01a6f4" or
        weapon_resource["dispatch_guard"]["empty_action_u16"] !=
            "0x1a00" or
        weapon_resource["dispatch_guard"]["rule"] !=
            "player+0x8b:u8 nonzero owns the empty-resource Button1 "
            "dispatch; the instantaneous player+0x8c resource value does "
            "not override that latch" or
        weapon_resource["normal_tick"]["reload_u8"] != 3 or
        weapon_resource["depleted_tick"]["reload_u8"] != 6 or
        weapon_resource["depleted_tick"]["clear_latch_writer_pc"] !=
            "0x0adfe6" or
        weapon_resource["coffee_shop_projection"]
            ["before_empty_dispatch"]["resource_u8"] != 13 or
        weapon_resource["coffee_shop_projection"]
            ["before_empty_dispatch"]["depleted_u8"] != 1 or
        weapon_resource["mutation_control"]
            ["high_resource_depleted_witness"]["resource_u8"] != 43 or
        weapon_resource["mutation_control"]
            ["high_resource_depleted_witness"]["substate_u16"] !=
            "0x1a00" or
        weapon_empty["timer_type"] != "u8" or
        weapon_empty["timer_initial"] != 16 or
        weapon_empty["cleanup_tick"] != 17 or
        weapon_empty["return_tick"] != 18 or
        weapon_empty["damaging_record4_count"] != 0 or
        weapon_empty_entry["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        weapon_empty_entry["spec_executable"] is not True or
        weapon_empty_entry["entry_writes"] != {
            "state_u16": "0x0200", "action_u16": "0x1a00",
            "substate_u16": "0x1a00"} or
        weapon_empty_entry["entry_preserves"] != [
            "animation_record:u32", "assembly:u32",
            "animation_timer:u16", "animation_branch:s16",
            "current_hurt_selector:u8", "current_attack_selector:u8"] or
        weapon_empty_entry["active_replacement"] != {
            "visible_update_offset_u8": 1,
            "state_u16": "0x0200", "action_u16": "0x1a02",
            "substate_u16": "0x1a02",
            "animation_record": "0x0015fcfc",
            "assembly": "0x00161772", "animation_timer_u16": 4095,
            "animation_branch_s16": -32768,
            "current_hurt_selector_u8": 1,
            "current_attack_selector_u8": 0} or
        weapon_empty_entry["coffee_shop_witnesses"][1]
            ["entry_animation_record"] != "0x0015f228" or
        weapon_empty_entry["rng_calls"] != []):
        raise ValueError("SPEC-02 corrected Predator Button1 action/resource drift")
    if (weapon_selector_contract["selection_tick"] != 0 or
        weapon_selector_contract[
            "projectile_angle_and_player_presentation_share_scan"] is not True or
        weapon_selectors != [4, 5, 6, 7] or
        sorted(map(int, weapon_selector_timelines)) != weapon_selectors or
        any(len(weapon_selector_timelines[str(selector)]) != 20
            for selector in weapon_selectors) or
        weapon_selector_timelines["4"] != weapon_frames or
        weapon_selector_timelines["5"][1]["animation_record"] !=
            "0x0015e594" or
        weapon_animation_execution["entry_rebind_updates_u8"] != [1, 2] or
        weapon_animation_execution["writers"] != {
            "record_bind": "0x01652a then 0x016588",
            "timer_bind": "0x01652e then 0x01658c",
            "branch_bind": "0x016534 then 0x016592",
            "timer_decrement": "0x016574"} or
        any(len(weapon_selector_sequences[str(selector)]) != 5
            for selector in weapon_selectors) or
        any([row["timer_u16"] for row in
             weapon_selector_sequences[str(selector)]] !=
            [2, 1, 2, 1, 4095]
            for selector in weapon_selectors)):
        raise ValueError("SPEC-02 Predator Button1 target presentation drift")
    if (weapon_parent["spec_executable"] is not True or
        weapon_child["spec_executable"] is not True or
        weapon_empty_effect["spec_executable"] is not True or
        weapon_empty_effect["variant"] != 0 or
        weapon_empty_effect["allocation"]["allocation_update_after_entry_u8"] != 1 or
        weapon_empty_effect["allocation"]["unwritten_fields_retained"] !=
            ["x_fraction:u16", "y_fraction:u16", "z:s16"] or
        weapon_empty_effect["initialization"]["selected_offset_s16"] != [0, 84] or
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
    parent_target = parent_active["target_selection"]
    parent_emitter = weapon_parent["child_emitter_state"]
    parent_effect = weapon_parent["effect_allocation"]
    parent_presentations = parent_init["presentation_records"]
    parent_selector_offsets = parent_init["selector_offsets_s16"]
    parent_route_angles = sorted(
        int(value) for value in parent_active["route_motion_vectors_s16"]["low"])
    parent_motion_low = parent_active["route_motion_vectors_s16"]["low"]
    parent_motion_high = parent_active["route_motion_vectors_s16"]["high"]
    parent_base_motion = parent_active["base_motion_vectors_s16"]
    parent_target_thresholds = parent_target["distance_thresholds_u16"]
    parent_target_presentations = parent_target["presentation_selectors_u8"]
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
    if (len(parent_presentations) != 8 or
        parent_presentations[-1]["animation_record"] != "0x0002fbb8" or
        parent_presentations[-1]["branch_s16"] >= 0 or
        len(parent_selector_offsets) != 6 or
        parent_route_angles != list(range(17, 48)) or
        sorted(map(int, parent_base_motion)) != list(range(17, 48)) or
        len(parent_target_thresholds) != 16 or
        parent_target_thresholds != sorted(parent_target_thresholds) or
        parent_target_presentations !=
            [7, 7, 7, 7, 6, 6, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4] or
        parent_emitter.get("position_rule") !=
            "child x uses parent x plus facing-adjusted row x; child y and z both use parent z plus their signed row field" or
        parent_emitter.get("child_initial_facing_u8") != 0 or
        parent_emitter.get("child_facing_rule") !=
            "the record-4 allocator clears child facing to zero; parent facing is read only for the row-x sign and is not copied" or
        [(row["source_slot"], row["variant_u8"], row["facing_u8"],
          row["parent_facing_u8"]) for row in
         parent_emitter.get("coffee_shop_collision_child_witnesses", [])] != [
            ("0x00ff8900", 1, 0, 1), ("0x00ff8800", 2, 0, 1)] or
        any(len(parent_motion_low[str(angle)]) != 16
            for angle in parent_route_angles) or
        any(len(parent_motion_high[str(angle)]) != 13
            for angle in parent_route_angles) or
        len(parent_child_rows) != 5 or
        len(parent_collision_child_rows) != 5 or
        parent_effect["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        parent_effect["helper"] != "0x08f0c6" or
        parent_effect["record_type_u8"] != 24 or
        parent_effect["class_u8"] != 0x49 or
        parent_effect["variant_u8"] != 0 or
        parent_effect["timer_u8"] != 8 or
        parent_effect["state0"].get("falls_through_to_state2") is not True or
        parent_effect["fixed_slot_reuse_presentation"]["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        parent_effect["fixed_slot_reuse_presentation"][
            "unwritten_retained_fields"] != [
                "animation_timer actor+0x0a:u16",
                "animation_branch actor+0x24:s16"] or
        tuple(parent_effect["fixed_slot_reuse_presentation"][
            "prior_owner"][field] for field in (
                "class_u8", "visible_frame_u16", "animation_record",
                "animation_timer_u16", "animation_branch_s16")) !=
            ("0x4e", 2259, "0x000929f0", 4094, -32768) or
        [(row["source_slot"], row["visible_frame_u16"],
          row["animation_timer_u16"], row["animation_branch_s16"])
         for row in parent_effect["fixed_slot_reuse_presentation"][
             "first_reuses"]] != [
                ("0x00ffc500", 2262, 4094, -32768),
                ("0x00ffc480", 2264, 4094, -32768)] or
        parent_effect["native_phase_projection"] != {
            "counter": "scheduler_frames before the record-4 update",
            "mask_u8": 1, "expected_u8": 1,
            "proof": "accepted Coffee Shop update cadence maps the first two visible lifetimes to source frames 2262 and 2264 from pre-update scheduler counts 193 and 195",
        } or
        parent_effect["scene_actor_rows_u16"] != 793 or
        parent_effect["scene_lifetime_count_u16"] != 113 or
        parent_effect["rng_calls"] != [] or
        parent_effect["fixed_frame_substitute_forbidden"] is not True or
        [len(child_sequences[str(index)]) for index in range(3)] !=
            [17, 10, 16] or
        len(parent_attack_boxes) != 3 or len(child_attack_boxes) != 3 or
        parent_attack_boxes[1]["impact_variant_u8"] != 10 or
        [row["impact_variant_u8"] for row in child_attack_boxes] != [0, 1, 1] or
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
        parent_boxes["attack_relative_s16"] != 12 or
        child_boxes["attack_relative_s16"] != 12 or
        [int(row["address"], 16) for row in parent_attack_boxes] !=
            [int(parent_boxes["table"], 16) + 12 + index * 16
             for index in range(len(parent_attack_boxes))] or
        [int(row["address"], 16) for row in child_attack_boxes] !=
            [int(child_boxes["table"], 16) + 12 + index * 16
             for index in range(len(child_attack_boxes))] or
        parent_emitter["initial_cadence_u8"] != 1 or
        parent_emitter["cadence_reload_u8"] != 6 or
        parent_emitter["initial_child_count_u8"] != 5 or
        parent_emitter["spawn_ticks_from_parent_state4"] != [1, 7, 13, 19, 25] or
        weapon_damage["parent_contact"]["attack_selector_u8"] != 25 or
        weapon_damage["parent_contact"]["damage_u8"] != 127 or
        weapon_damage["child_contact"]["attack_selector_u8"] != 14 or
        weapon_damage["child_contact"]["damage_u8"] != 31):
        raise ValueError("SPEC-02 corrected projectile collision/damage drift")
    if (weapon_collision_registration["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        weapon_collision_registration["spec_executable"] is not True or
        weapon_collision_registration["visibility"]["x_guard"] !=
            "u16(actor_x - camera_x + 0x0040) <= 0x0200" or
        weapon_collision_registration["visibility"]["y_guard"] !=
            "u16(actor_y - camera_z + 0x0020) <= 0x0140" or
        weapon_collision_registration["visibility"]["update_order"] != [
            "actor state/action/movement/animation",
            "visibility guard and actor+0x01 write",
            "record-type collision-list registration",
            "record4-v-record12 collision scheduler"] or
        weapon_collision_registration["registration"]["record4"][
            "writer"] != "0x01681e..0x016828" or
        weapon_collision_registration["registration"]["record12"][
            "writer"] != "0x016864..0x01686e" or
        weapon_collision_registration["identity_writer"][
            "coffee_shop_counter_before_parent_u8"] != 0x25 or
        [row["identity_u8"] for row in
         weapon_collision_registration["identity_writer"]["assignments"]] !=
            [0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b] or
        weapon_collision_registration["types_and_signedness"][
            "defender_latches"] != "defender+0x68:u8[8]" or
        weapon_collision_registration["pair_guards"][0:3] != [
            "defender+0x6d:u8 < 4 in scheduler",
            "defender+0x00:u8 == 1",
            "defender+0x70:u8 == 0"] or
        weapon_collision_registration["coffee_shop_projection"][
            "first_registered_frame"] != 2296 or
        weapon_collision_registration["coffee_shop_projection"][
            "first_contact_frame"] != 2306 or
        weapon_collision_registration["mutation_control"][
            "target_first_contact_frame_after"] != 2311 or
        weapon_collision_registration["mutation_control"][
            "suppressed_writes"] != 15):
        raise ValueError("SPEC-02 collision registration/eligibility drift")
    reaction_handoff = weapon_collision_registration[
        "collision_to_reaction_handoff"]
    if (reaction_handoff["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        reaction_handoff["spec_executable"] is not True or
        reaction_handoff["coffee_shop_slot_0xffa180"] != {
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
            "next_attack_selector_u8": 1} or
        reaction_handoff["mutation_control"][
            "first_rejected_visible_frame_u16"] != 2307):
        raise ValueError("SPEC-02 collision-to-reaction handoff drift")
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
    special_records = player_special["initialization"]["presentation_records"]
    special_durations = [row["visible_duration_u16"] for row in
                         player_special["initialization"]
                             ["visible_presentation_runs"]]
    class4b_records = class4b["state0"]["animation_records"]
    class3d_records = class3d["state0"]["animation_records"]
    class3d_offsets = class3d["state_0x0200"]["movement_offsets_s16"]
    if (player_special["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        player_special["source_input"]["guard_routine"] != "0x01a7e6" or
        player_special["source_input"]["action_writer"] != "0x01a89a" or
        player_special["state_dispatch"]["entry"] != "0x023132" or
        player_special["state_dispatch"]["route_state_sequence_u16"] !=
            [0x0800, 0x0802, 0x0804] or
        len(special_records) != 17 or
        special_durations !=
            [4, 4, 3, 1, 5, 4, 4, 4, 4, 4, 6, 4, 4, 4, 4, 16, 1] or
        special_records[4]["attack_selector_u8"] != 11 or
        special_records[-1]["branch_s16"] != -32768 or
        player_special["active_state"]["source_audio_commands"] !=
            ["0x0091", "0x0096"] or
        player_special["completion"]["health_cost_s16"] != 6 or
        special_effects["player_dispatch_entry"] != "0x023132" or
        special_effects["record_type_u8"] != 24 or
        class4b["class_u8"] != "0x4b" or
        class4b["dispatch"] != "0x08f86e" or
        class4b["state_sequence_u16"] != [0, 0x0200, 0x0400] or
        not class4b["state_0x0200"]["owner_contact_lifetime"].startswith(
            "player writer 0x01986a clears") or
        class4b["state_0x0200"]["coffee_shop_wrap_witness"] != {
            "terminal_record_frame_u16": 2835,
            "wrapped_record_frame_u16": 2836,
            "wrapped_animation_record": "0x0008f8e0"} or
        len(class4b_records) != 32 or
        [row["branch_s16"] for row in class4b_records[:16]] !=
            list(range(16)) or
        class4b_records[-1]["branch_s16"] != -32753 or
        class3d["class_u8"] != "0x3d" or
        class3d["dispatch"] != "0x0887c8" or
        class3d["state_sequence_u16"] != [0, 0x0200, 0x0400] or
        class3d["unwritten_field_retention"]["prior_y_s16"] != 343 or
        class3d["unwritten_field_retention"]["first_class3d_y_s16"] != 343 or
        len(class3d_records) != 9 or
        class3d_records[-1]["branch_s16"] != -32768 or
        len(class3d_offsets) != 16 or
        class3d_offsets[0] != [-61, -13] or
        class3d_offsets[8] != [61, 13] or
        special_effects["fixed_frame_substitute_forbidden"] is not True):
        raise ValueError("SPEC-02 Predator special scene population drift")
    if (class01["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class01["implementation_status"] != "SPEC_EXECUTABLE" or
        class02["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class02["implementation_status"] != "SPEC_EXECUTABLE" or
        class0f["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class0f["implementation_status"] != "SPEC_EXECUTABLE" or
        class0a["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class0a["implementation_status"] != "SPEC_EXECUTABLE" or
        class00_companion["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class00_companion["implementation_status"] != "SPEC_EXECUTABLE" or
        class03_type36["classification"] != "SOURCE_CLOSED_PRESENTATION" or
        class03_type36_contract["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class03_type36_contract["spec_executable"] is not True or
        class03_type36_contract["pool_and_scheduler"]["allocator"] !=
            "0x017876" or
        class03_type36_contract["pool_and_scheduler"]["release_routine"] !=
            "0x01788c" or
        class03_type36_contract["state_0x0000"]["variant"][
            "coffee_shop_reachable_u8"] != 1 or
        class03_type36_contract["state_0x0000"]["motion_s16_16"] != {
            "phase1_x_velocity": -0x00028000,
            "phase3_x_velocity": -0x00044000,
            "initial_y_velocity": 0,
            "y_acceleration": 0x00001000} or
        len(class03_type36_records) != 9 or
        class03_type36_records[0]["animation_record"] != "0x0009a884" or
        class03_type36_records[-1]["branch_s16"] != -32768 or
        len(class03_type36_contract["state_0x0200"]["phase_programs"]) != 4 or
        class03_type36_contract["effects"]["rng_calls_u8"] != 0 or
        class03_type36_contract["effects"]["audio_commands"] != [] or
        class03_type36_contract["fixed_frame_substitute_forbidden"] is not True or
        class03_type36_contract["retained_gameplay_authority"] is not False or
        class04_type36["classification"] != "SOURCE_CLOSED_PRESENTATION" or
        class04_type36_contract["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class04_type36_contract["spec_executable"] is not True or
        class04_type36_contract["pool_and_scheduler"]["allocator"] !=
            "0x017876" or
        class04_type36_contract["pool_and_scheduler"]["release_routine"] !=
            "0x01788c" or
        class04_type36_contract["state_0x0000"]["offset_lookup"][
            "coffee_shop_reachable_selector_u8"] != 0 or
        class04_type36_contract["state_0x0000"]["offset_lookup"][
            "offset_x_s16"] != 5 or
        class04_type36_contract["state_0x0000"]["offset_lookup"][
            "offset_y_s16"] != 86 or
        len(class04_type36_records) != 10 or
        class04_type36_records[0]["animation_record"] != "0x0009ac82" or
        class04_type36_records[-1]["branch_s16"] != -32768 or
        class04_type36_contract["state_0x0200"]["guard"] !=
            "s16(0xff81e8) == 10" or
        "s16(0xff82c0)" not in class04_type36_contract[
            "state_0x0200"]["guard_true_arithmetic"] or
        class04_type36_contract["effects"]["rng_calls_u8"] != 0 or
        class04_type36_contract["effects"]["audio_commands"] != [] or
        class04_type36_contract["fixed_frame_substitute_forbidden"] is not True or
        class04_type36_contract["retained_gameplay_authority"] is not False or
        [(row["address"], row["observed_source_slot"],
          row["camera_threshold_u16"], row["class_u8"], row["variant_u8"])
         for row in coffee_scene_records] != [
            ("0x0015c108", "0x00ffb600", 512, 2, 0),
            ("0x0015c128", "0x00ffb580", 512, 1, 0),
            ("0x0015c158", "0x00ffb400", 672, 1, 1),
            ("0x0015c178", "0x00ffb300", 736, 2, 0),
            ("0x0015c188", "0x00ffb280", 816, 5, 0),
            ("0x0015c1a8", "0x00ffb180", 816, 5, 0),
            ("0x0015c1b8", "0x00ffb100", 816, 15, 0)] or
        [row["animation_record"] for row in class01_records] !=
            ["0x0006b45a", "0x0006b46a", "0x0006b47a"] or
        [row["animation_record"] for row in class02_records] !=
            ["0x0006b66c", "0x0006b680"] or
        [row["animation_record"] for row in class0f_records] !=
            ["0x0006ee4a", "0x0006ee5e", "0x0006ee72"] or
        [(row["hurt_selector_u8"], row["attack_selector_u8"])
         for row in class0f_records] != [(1, 1), (2, 2), (0, 3)] or
        class05_prop["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class05_prop["spec_executable"] is not True or
        [row["animation_record"] for row in class05_records] !=
            ["0x0006cc62", "0x0006cc8a", "0x0006cc9a",
             "0x0006ccae", "0x0006ccc2"] or
        class05_collision["attack_record"]["address"] != "0x0011af76" or
        class05_collision["hurt_record"]["address"] != "0x0006cd50" or
        class05_reaction["state_0x0400"]["seed_after"] != "0x61a7" or
        class05_motion["primary"]["x_velocity_s32"] != -0x00050000 or
        class05_prop["fixed_frame_substitute_forbidden"] is not True or
        class01_contract["rng"] != {"calls": 0, "consumption_order": []} or
        class02_contract["rng"] != {"calls": 0, "consumption_order": []} or
        sorted((row["address"], row["writer_source_frame_u16"],
                row["camera_x_u16"], row["first_actor_visible_frame_u16"])
               for contract in (class01_contract, class02_contract,
                                class0f_contract)
               for row in contract["stage_spawn_guard"]
                   ["camera_sample_order"]["records"]) != [
            ("0x0015c108", 2072, 640, 2073),
            ("0x0015c128", 2072, 640, 2073),
            ("0x0015c158", 2242, 675, 2243),
            ("0x0015c178", 2617, 736, 2618),
            ("0x0015c1b8", 2672, 817, 2673)] or
        class01_contract["route_interaction"]["clear_writer"] !=
            "0x0289fc (captured successor 0x028a02) in recurring controller writes 0" or
        class02_collision["attack_record"] != "0x0011af76" or
        class02_collision["reaction_delay"]["value_u16"] != 3 or
        class02_collision["reaction_delay"]["coffee_shop_witness"] != {
            "bound_frame_u16": 2806,
            "retained_through_frame_u16": 2808,
            "first_animation_decrement_frame_u16": 2809,
            "retained_animation_timer_u16": 4095} or
        class02_collision["hurt_record"]["address"] != "0x0006b6f4" or
        class02_collision["reaction_direction"]["attack_mode_guard"] !=
            "attack_record+0x0a:s8 is +1; zero preserves the copied attacker facing and negative XORs it" or
        class02_collision["reaction_direction"]["observed_inputs"] !=
            {"source_frame": 2804, "attacker_x_u16": 1091,
             "defender_x_u16": 1152, "attack_mode_s8": 1} or
        class02_collision["reaction_direction"]["result_u8"] != 1 or
        class02_collision["health_after_clamp_s16"] != -1 or
        class02_contract["scheduler_phase_evidence"]["byte_identical"] is
            not True or
        [row["dispatch_count_u8"] for row in class02_contract[
            "scheduler_phase_evidence"]["class02_dispatch_counts"]] !=
            [1, 1, 2, 2, 1] or
        [row["dispatch_count_u8"] for row in class02_contract[
            "scheduler_phase_evidence"]["controller_dispatch_counts"]] !=
            [0, 1, 3, 1, 1] or
        class02_contract["scheduler_phase_evidence"]
            ["fixed_frame_gameplay_authority_forbidden"] is not True or
        class0f_contract["source_body"] != {
            "first": "0x0006ed3e", "last_exclusive": "0x0006ee42",
            "sha256": "d3ae68e588d84042b1f937279588d4974bc1bbd64778c8e77625735b859ba8de"} or
        [row["offsets_s16"] for row in class0f_contract["dispatch_tables"]] !=
            [[8, 64, 112, 242], [4, 6], [10, 4]] or
        class0f_selector1["allocation"]["variant_iteration_s8"] !=
            [3, 2, 1, 0] or
        class0f_selector1["allocation"]["child_rng_calls_u8"] != 28 or
        class0f_selector0["first_source_effect"]["record_type_u8"] != 28 or
        class0f_selector0["first_source_effect"]["class_u8"] != 9 or
        [row["command_u16"] for row in
         class0f_contract["audio_transactions"]] != ["0x0077", "0x0142"] or
        {row["argument1_u32"] for row in
         class0f_contract["audio_transactions"]} != {"0x00002000"} or
        class0f_contract["rng"]["direct_calls"] != 0 or
        class0f_contract["retained_gameplay_authority"] is not False or
        class0f_contract["fixed_frame_substitute_forbidden"] is not True or
        class0a_contract["source_body"] != {
            "first": "0x00077ccc", "last_exclusive": "0x00077d26",
            "sha256": "43f6bb2d20750b41ec6e03b6eed22488fee5db651d0680ad2c600e2b53ac0089"} or
        class0a_contract["dispatch_table"]["offsets_s16"] != [8, 30, 72] or
        class0a_contract["animation_selector"]["table_address"] !=
            "0x00077d26" or
        class0a_contract["animation_selector"]["offsets_s16"] != [
            74, 126, 178, 302, 338, 390, 514, 638, 762, 814, 866,
            918, 970, 1022, 1074, 1126, 1178, 1230, 1282, 1406,
            1426, 1462, 1514, 1638, 1666, 1774] or
        [row["animation_record"] for row in class0a_records] != [
            "0x00077e54", "0x00077e5c", "0x000782a4", "0x000782ac"] or
        [row["attack_selector_u8"] for row in class0a_records] !=
            [16, 16, 4, 7] or
        class0a_contract["direct_effects"]["rng_calls_u8"] != 0 or
        class0a_contract["direct_effects"]["collision_memberships_u8"] != 0 or
        class0a_contract["counterfactual"]["byte_identical"] is not True or
        class0a_cadence["classification"] !=
            "SOURCE_CAPTURE_PROJECTION_ONLY" or
        class0a_cadence["exception_count_u8"] != 70 or
        class0a_cadence["dispatch_count_u16"] != 3597 or
        class0a_contract["retained_gameplay_authority"] is not False or
        class0a_contract["fixed_frame_substitute_forbidden"] is not True or
        class00_companion_contract["source_body"] != {
            "first": "0x0009e098", "last_exclusive": "0x0009e5be",
            "sha256": "5ae219377db297092601b14a1e9f055fc7c18a6ccd6358c6dbbb55e3d586f3e1"} or
        class00_companion_contract["active_helper"]["sha256"] !=
            "af83dda6984a7ba504945d4ee313b6b133d342e1fac8fb7e51edba4f655161e1" or
        class00_companion_contract["dispatch"][
            "outer_state_high_byte_offsets_s16"] != [8, 112, 980, 1006] or
        class00_companion_contract["allocation_initialization"][
            "source_slot"] != "0x00ffce00" or
        class00_companion_contract["allocation_initialization"][
            "lifetime"] != {
                "allocation_source_frame_u16": 2074,
                "first_visible_source_frame_u16": 2075,
                "last_visible_source_frame_u16": 5550} or
        len(class00_companion_parent_animations) != 109 or
        len({row["animation_record"] for row in
             class00_companion_parent_animations}) != 109 or
        any(row["parent_animation_branch_u8"] < 0 or
            row["parent_animation_branch_u8"] > 255
            for row in class00_companion_parent_animations) or
        len(class00_companion_parent_entries) != 37 or
        [row["parent_animation_branch_u8"] for row in
         class00_companion_parent_entries] != [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
            15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 29, 30,
            42, 43, 44, 51, 52, 86, 89, 90, 97] or
        len(class00_companion_records) != 11 or
        [row["animation_record"] for row in class00_companion_records] != [
            "0x0009e606", "0x0009e61a", "0x0009e62e", "0x0009e656", "0x0009e66a",
            "0x0009e692", "0x0009e6e2", "0x0009e6f6", "0x0009e70a",
            "0x0009e71e", "0x0009e732"] or
        any(row["hurt_selector_u8"] != 0 or row["attack_selector_u8"] != 0
            for row in class00_companion_records) or
        class00_companion_cadence["dispatch_count_u16"] != 3595 or
        class00_companion_cadence["exception_count_u8"] != 70 or
        class00_companion_exit_phase["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class00_companion_exit_phase["byte_identical"] is not True or
        class00_companion_exit_phase["sha256"] !=
            "06db63941a57793c60fedc63698db6c6bdd2c93a524e0de8c2af055e3683a0eb" or
        class00_companion_exit_phase["player_program_projection"][
            "dispatcher_events_u16"] != 213 or
        class00_companion_exit_phase["player_program_projection"][
            "native_program_applications_u16"] != 203 or
        len(class00_exit_phase_program) != 71 or
        class00_exit_phase_program[7]["events"] != "PADCPADCPADCP" or
        class00_exit_phase_program[8]["events"] != "ADCPADCPADCP" or
        class00_exit_phase_program[52]["player_program_apply_mask_u8"] != 6 or
        class00_exit_phase_program[53]["player_program_apply_mask_u8"] != 6 or
        max(len(row["events"]) for row in class00_exit_phase_program) != 16 or
        class00_companion_exit_phase["frame_5460_witness"] != {
            "player_updates_u8": 4,
            "record28_traversals_u8": 3,
            "final_traversal_child_x_fp": "0x05320000",
            "final_traversal_child_z_s16": 311,
            "post_traversal_player_x_fp": "0x0539ad00",
            "next_visible_child_x_fp": "0x05320000",
            "next_visible_child_z_s16": 311} or
        class00_companion_contract["direct_effects"]["rng_calls_u8"] != 0 or
        class00_companion_contract["direct_effects"][
            "collision_memberships_u8"] != 0 or
        class00_companion_contract["counterfactual"]["classification"] !=
            "SOURCE_STATE_MUTATION_CONTROL_WITH_MATCHED_NORMALIZATION" or
        class00_companion_contract["retained_gameplay_authority"] is not False or
        class00_companion_contract["fixed_frame_substitute_forbidden"] is not True):
        raise ValueError("SPEC-02 Coffee Shop component implementation drift")
    if (class02_source_cadence["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        class02_source_cadence["source_slot"] != "0x00ffb600" or
        class02_source_cadence["default_updates_per_source_frame_u8"] != 1 or
        class02_source_cadence["exceptions_sha256"] !=
            "edef59d16bb596ec4b9a583eeb19052e125c371f2b72bc61ffb3b2f7410728da" or
        len(class02_source_exceptions) != 113 or
        [(row["source_frame_u16"], row["updates_u8"])
         for row in class02_source_exceptions[:5]] !=
            [(2075, 2), (2076, 2), (2165, 4), (2260, 0), (2265, 0)] or
        class02_source_cadence["fixed_frame_gameplay_authority_forbidden"]
            is not True):
        raise ValueError("SPEC-02 Coffee Shop class-0x02 source cadence drift")
    if (record20_exit_prefix["classification"] !=
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        record20_exit_prefix["source_frame_range_inclusive_u16"] !=
            [5453, 5523] or
        record20_exit_prefix["source_pool_scheduler"] !=
            "0x01bc38..0x01bc78" or
        record20_exit_prefix["indirect_caller_pc"] != "0x01bc6e" or
        record20_exit_prefix["source_phase_split_after_slot"] !=
            "0x00ffb500" or
        record20_exit_prefix["suffix_first_slot"] != "0x00ffb600" or
        [(row["program_tick_u8"], row["display_ticks_u8"],
          row["updates_u8"]) for row in record20_exit_prefix_groups] !=
            [(0, 5, 1), (5, 10, 3), (15, 1, 4), (16, 15, 3),
             (31, 1, 4), (32, 7, 3), (39, 1, 4), (40, 6, 3),
             (46, 1, 4), (47, 6, 3), (53, 1, 4), (54, 4, 3),
             (58, 1, 4), (59, 5, 3), (64, 6, 4), (70, 1, 1)] or
        record20_exit_prefix["byte_identical"] is not True or
        record20_exit_prefix["fixed_frame_gameplay_authority_forbidden"]
            is not True):
        raise ValueError("SPEC-02 Coffee Shop record-20 prefix phase drift")

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
    lines.extend([
        "};", "",
        "static const AvspRound1CoffeeStageSetupSpec avsp_round1_coffee_stage_setup =",
        "{",
        "    2, 1u, 0x1Cu, 14, 25u, 14u, 22u, -4, -8, 0, 0x18u, 0, 0,",
        "    8, 16, 0x8DEFu, 0xA998u, 8",
        "};", "",
        "static const AvspRound1EntryStepSpec avsp_round1_entry_steps[AVSP_ROUND1_ENTRY_STEP_COUNT] =", "{"])
    for kind, opcode, arg0, arg1, arg2, first, last in step_rows:
        lines.append(
            f"    {{ {kind}, 0x{opcode:02X}u, {arg0}u, {arg1}u, {arg2}u, 0x{first:08X}UL, 0x{last:08X}UL }},")
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_scheduler_pool_order[AVSP_ROUND1_SCHEDULER_POOL_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in scheduler_order),
        "};", "",
        "static const AvspRound1SchedulerGlobalSpec avsp_round1_scheduler_globals[AVSP_ROUND1_SCHEDULER_GLOBAL_COUNT] =",
        "{",
    ])
    binding_names = {
        "camera_x_previous": "AVSP_ROUND1_SCHEDULER_GLOBAL_CAMERA_X_PREVIOUS",
        "camera_z_previous": "AVSP_ROUND1_SCHEDULER_GLOBAL_CAMERA_Z_PREVIOUS",
    }
    for row in scheduler_global_fields:
        lines.append(
            "    { 0x%04Xu, %sUL, %du, %s }," % (
                row["a5_offset_u16"], row["absolute_address"],
                row["width_bytes"], binding_names[row["native_scheduler_field"]]))
    lines.extend([
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
        "static const unsigned char avsp_round1_class1f_collision_reaction_facing_xor = %du;" % (
            class1f_collision_reaction_facing["facing_xor_u8"]),
        "static const unsigned long avsp_round1_class1f_collision_reaction_attack_record = %sUL;" % (
            class1f_collision_reaction_facing["guard"]
                ["coffee_shop_attack_record"]),
        "",
        "static const AvspRound1Class1fSourceHitSpec avsp_round1_class1f_source_hit =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, %sUL, %sUL," % (
            class1f_source_hit["visible_result"]["state_u16"],
            class1f_source_hit["visible_result"]["action_phase_u16"],
            class1f_source_hit["recovery"]["next_action_phase_u16"],
            class1f_source_hit["reaction_record"]["animation_record"],
            class1f_source_hit["reaction_record"]["assembly"]),
        "    0x%02Xu, %du, 0x%02Xu, %du, 4u, 1u, %du, %du," % (
            class1f_source_hit["reaction_table"]
                ["reaction_selector_actor_4d_u8"],
            class1f_source_hit["reaction_table"]["hit_mode_actor_46_u8"],
            class1f_source_hit["entry_guard"]["hit_kind_actor_49_u8"],
            class1f_source_hit["entry_guard"]
                ["recovery_timer_actor_2c_u8"],
            class1f_source_hit["reaction_record"]["hurt_selector_u8"],
            class1f_source_hit["reaction_record"]["attack_selector_u8"]),
        "    { " + ", ".join(
            f"0x{value:04X}u" for value in
            class1f_source_hit["action_dispatch"]
                ["required_action_phases_u16"]) + " },",
        "    %dL, %dL, %dL, %dL," % tuple(
            class1f_source_hit_launch["motion"][key]
            for key in ("x_velocity_s32_16_16_before_facing",
                        "x_acceleration_s32_16_16_before_facing",
                        "y_velocity_s32_16_16",
                        "y_acceleration_s32_16_16")),
        "    %dL, %dL, %dL, %dL," % (
            -class1f_source_hit_bounce["observed_motion_after_facing"]
                ["x_velocity_s32_16_16"],
            -class1f_source_hit_bounce["observed_motion_after_facing"]
                ["x_acceleration_s32_16_16"],
            class1f_source_hit_bounce["observed_motion_after_facing"]
                ["y_velocity_s32_16_16"],
            class1f_source_hit_bounce["observed_motion_after_facing"]
                ["y_acceleration_s32_16_16"]),
        "    %du, 0x%02Xu, 0x%02Xu, 0x%02Xu, 0x%02Xu," % (
            class1f_source_hit_landing_hold
                ["captured_values_before_decrement"][0],
            class1f_source_hit_first_flight["landing_selector_u8"],
            class1f_source_hit_bounce["selector_u8"],
            class1f_source_hit_rng_hold["selector_u8"],
            class1f_source_hit_terminal["selector_u8"]),
        "    0x%04Xu, 0x%04Xu, %du, %du," % (
            class1f_source_hit_rng["seed_before_u16"],
            class1f_source_hit_rng["seed_after_u16"],
            class1f_source_hit_rng["result_low_nibble_u8"],
            class1f_source_hit_rng["hit_count_actor_6d_u8"]),
        "    { " + ", ".join(f"{value}u" for value in
            class1f_source_hit_rng["timer_table_row_u8"]) + " },",
        "    %du, 0u, %du," % (
            class1f_source_hit_rng["selected_timer_u8"],
            len(class1f_source_hit_reaction_records)),
        "    {",
    ])
    for record in class1f_source_hit_reaction_records:
        lines.append(
            "        { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "    },",
    ])
    for record in (class1f_source_hit_landing_record,
                   class1f_source_hit_bounce_record,
                   class1f_source_hit_rng_hold_record):
        lines.append(
            "    { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "    %du," % len(class1f_source_hit_terminal["records"]),
        "    {",
    ])
    for record in class1f_source_hit_terminal["records"]:
        lines.append(
            "        { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "    },",
        "    0x0200u, 0x0000u, 0x1600u, %du," % (
            class1f_source_hit_return["class_tail"]["style85_after_u8"]),
        "    %du, %du, %du, %du, %du, %du, %du," % (
            class1f_source_hit_resume["actor_85_style_u8"],
            class1f_source_hit_resume["actor_a3_u8"],
            class1f_source_hit_resume["actor_a4_u8"],
            class1f_source_hit_resume["actor_a5_u8"],
            class1f_source_hit_resume["actor_a6_u8"],
            class1f_source_hit_resume["actor_b0_u8"],
            class1f_source_hit_resume["facing_u8"]),
        "    %d, %d, %d, %d," % (
            class1f_source_hit_resume["actor_x_s16"],
            class1f_source_hit_resume["actor_z_s16"],
            class1f_source_hit_resume["player_x_s16"],
            class1f_source_hit_resume["player_z_s16"]),
        "};", "",
        "static const AvspRound1Class1fSourceKoSpec avsp_round1_class1f_source_ko =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu," % (
            class1f_source_ko["collision_visible_result"]
                ["outer_state_u16"],
            class1f_source_ko_handoff["outer_state_u16"],
            class1f_source_ko_hold["outer_state_u16"],
            class1f_source_ko_release["outer_state_u16"]),
        "    { " + ", ".join(
            f"0x{value:04X}u" for value in
            class1f_source_ko_program["action_phases_u16"]) + " },",
        "    %du, 0x%02Xu, %du, 0x%02Xu, %du, %du, %du, %du," % (
            class1f_source_ko_handoff["active_u8"],
            class1f_source_ko_handoff["reaction_selector_actor_4d_u8"],
            class1f_source_ko_handoff["hit_mode_actor_46_u8"],
            class1f_source_ko_handoff["hit_kind_actor_49_u8"],
            class1f_source_ko_handoff["recovery_timer_actor_2c_u8"],
            class1f_source_ko_landing["timer_actor_2a_u8"],
            class1f_source_ko_hold["timer_actor_2a_u8"],
            len(class1f_source_ko_reaction_records)),
        "    %dL, %dL, %dL, %dL," % (
            class1f_source_ko_launch[
                "x_velocity_s32_16_16_before_facing"],
            class1f_source_ko_launch[
                "x_acceleration_s32_16_16_before_facing"],
            class1f_source_ko_launch["y_velocity_s32_16_16"],
            class1f_source_ko_launch["y_acceleration_s32_16_16"]),
        "    %dL, %dL, %dL, %dL," % (
            class1f_source_ko_bounce[
                "x_velocity_s32_16_16_before_facing"],
            class1f_source_ko_bounce[
                "x_acceleration_s32_16_16_before_facing"],
            class1f_source_ko_bounce["y_velocity_s32_16_16"],
            class1f_source_ko_bounce["y_acceleration_s32_16_16"]),
        "    {",
    ])
    for record in class1f_source_ko_reaction_records:
        lines.append(
            "        { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "    },",
    ])
    for record in (class1f_source_ko_landing_record,
                   class1f_source_ko_bounce_record):
        lines.append(
            "    { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fSourceKoSpec avsp_round1_class1f_player_special_ko =",
        "{",
        "    0x0400u, 0x0402u, 0x0404u, 0x0600u,",
        "    { " + ", ".join(
            f"0x{value:04X}u" for value in
            player_special_source_ko["action_phases_u16"]) + " },",
        "    %du, 0u, 0u, 2u, %du, %du, %du, %du," % (
            player_special_source_ko["dispatch_active_u8"],
            player_special_source_ko["entry_hold_ticks_u8"],
            player_special_source_ko["landing_hold_ticks_u8"],
            player_special_source_ko["removal_hold_ticks_u8"],
            len(player_special_source_ko["reaction_records"])),
        "    %dL, %dL, %dL, %dL," % (
            player_special_source_ko[
                "launch_x_velocity_before_facing_16_16"],
            player_special_source_ko["launch_x_acceleration_16_16"],
            player_special_source_ko["launch_y_velocity_16_16"],
            player_special_source_ko["launch_y_acceleration_16_16"]),
        "    %dL, %dL, %dL, %dL," % (
            player_special_source_ko[
                "bounce_x_velocity_before_facing_16_16"],
            player_special_source_ko["bounce_x_acceleration_16_16"],
            player_special_source_ko["bounce_y_velocity_16_16"],
            player_special_source_ko["bounce_y_acceleration_16_16"]),
        "    {",
    ])
    for record in player_special_source_ko["reaction_records"]:
        lines.append(
            "        { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "    },",
    ])
    for record in (player_special_source_ko["landing_record"],
                   player_special_source_ko["falling_record"]):
        lines.append(
            "    { %du, %d, %sUL, %sUL, %du, %du }," % (
                record["timer_u16"], record["branch_s16"],
                record["animation_record"], record["assembly"],
                record["hurt_selector_u8"], record["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1RecurringSpawnSpec avsp_round1_recurring_spawn =",
        "{",
        "    0x0200u, 0x0202u, 0x0204u, 0x%04Xu, %du, %du, %du," % (
            recurring_camera_edge["observed_transition"]
                ["substate_after_u16"],
            recurring_camera_edge["transition_values"]
                ["field46_phase_threshold_u16"],
            recurring_camera_edge["transition_values"]["camera_edge_x_s16"],
            1 if recurring_camera_edge["native_adapter_binding"]
                ["runtime_field"] == "camera_x_position" else 0),
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
            recurring["phase_counter"]["native_entry_handoff_value_u8"],
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
        "    %du, %du, 0x%04Xu, 0x%02X, %du, 0x%04Xu," % (
            recurring_gate["write_values"]["conditional_phase_0x2e_u8"],
            recurring_gate["write_values"]["conditional_local_0x2c_u8"],
            int(recurring_gate["gate_owner"]["record"], 16) & 0xffff,
            int(recurring_gate["gate_owner"]["class_u8"], 16),
            recurring_gate["gate_owner"]["record_type_u8"],
            recurring_gate["gate_owner"]["state_u16"]),
        "    0x%04Xu, 0x%04Xu, %d, %du," % (
            recurring_progress["transition_guard"]["state_u16"],
            recurring_progress["transition_guard"]["substate_u16"],
            recurring_progress["transition_guard"]["health_s16"],
            recurring_progress["increment_u16"]),
        "    1u, 1u",
        "};", "",
        "static const AvspRound1CoffeeExitSpec avsp_round1_coffee_exit =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x0400u," % tuple(
            row["substate_u16"] for row in coffee_exit_controller["phases"]),
        "    16u, 600u, 1008u, %du, 1152u," %
            coffee_exit_controller["withdrawal"]["timer_u16"],
        "    %d, %d, %d, %du," % (
            coffee_exit["route_edges"][0]["to_s16"],
            coffee_exit["route_edges"][1]["to_s16"],
            coffee_exit["route_edges"][2]["to_s16"],
            coffee_exit_route_zero["guard_countdown"]["initial_u16"]),
        "    %du, %du, %du, %du, %du," % (
            coffee_exit_route_zero["resident_load_stalls"][0]
                ["display_frames_u16"],
            coffee_exit_route_zero["resident_load_stalls"][1]
                ["display_frames_u16"],
            coffee_exit_route_zero["resident_load_stalls"][2]
                ["display_frames_u16"],
            coffee_exit_route_zero["teardown_visible_frame_u16"],
            coffee_exit_route_zero["next_scene_substate2_visible_frame_u16"]),
        "    0x%04Xu, %sUL, %sUL," % (
            coffee_exit_script["outer_state_u16"],
            coffee_exit_script["source_program_address"],
            coffee_exit_script["steps"][-1]["cursor"]),
        "    0x%04Xu, 0x%04Xu," % (
            coffee_exit_handoff["source_observations"][0]
                ["player_substate_u16"],
            coffee_exit_handoff["source_observations"][1]
                ["player_substate_u16"]),
        "    0x%08XL, 0x%08XL, 0x%08XUL," % (
            coffee_exit_handoff["source_observations"][1]
                ["player_x_fp_s32_16_16"],
            coffee_exit_handoff["source_observations"][1]
                ["player_y_fp_s32_16_16"],
            coffee_exit_handoff["source_observations"][1]
                ["player_animation_record_u32"]),
        "    %du, %du, %d, %du," % (
            coffee_exit_handoff["source_observations"][0]
                ["player_animation_timer_u16"],
            coffee_exit_handoff["source_observations"][1]
                ["player_animation_timer_u16"],
            coffee_exit_handoff["source_observations"][1]
                ["player_animation_branch_s16"],
            coffee_exit_handoff["source_observations"][1]
                ["player_facing_u8"]),
        "    1u, 1u, 1u,",
        "    %d, %d, %d," % (
            coffee_exit_next_scene["camera_reset_x_s16"],
            coffee_exit_next_scene["camera_reset_z_s16"],
            coffee_exit_next_scene["camera_reset_target_x_s16"]),
        "    0x%08XL, 0x%08XL, %d, 0x%04Xu, 0x%04Xu," % (
            coffee_exit_next_scene["player_x_fp_s32_16_16"],
            coffee_exit_next_scene["player_y_fp_s32_16_16"],
            coffee_exit_next_scene["player_z_s16"],
            coffee_exit_next_scene["player_state_u16"],
            coffee_exit_next_scene["player_substate_u16"]),
        "    %du, %du, %d, %d, %d, 0x%04Xu" % (
            coffee_exit_next_scene["player_facing_before_controller_u8"],
            coffee_exit_next_scene["player_facing_after_controller_u8"],
            coffee_exit_next_scene["camera_x_s16"],
            coffee_exit_next_scene["camera_z_s16"],
            coffee_exit_next_scene["camera_target_x_s16"],
            coffee_exit_next_scene["entry_controller_state_u16"]),
        "};", "",
        "static const AvspRound1CoffeeExitStepSpec avsp_round1_coffee_exit_steps[AVSP_ROUND1_COFFEE_EXIT_STEP_COUNT] =",
        "{",
    ])
    exit_kind = {
        "bootstrap": "AVSP_ROUND1_EXIT_STEP_BOOTSTRAP",
        "move_to": "AVSP_ROUND1_EXIT_STEP_MOVE_TO",
        "set_mode": "AVSP_ROUND1_EXIT_STEP_SET_MODE",
        "dwell": "AVSP_ROUND1_EXIT_STEP_DWELL",
        "terminate": "AVSP_ROUND1_EXIT_STEP_TERMINATE",
        "ballistic": "AVSP_ROUND1_EXIT_STEP_BALLISTIC",
    }
    for step in coffee_exit_script["steps"]:
        lines.append(
            "    { %sUL, %sUL, %sUL, %d, %d, %du, %s, %du, %du }," % (
                step["cursor"], step["next_cursor"],
                step.get("animation_record", "0x00000000"),
                step.get("x_s16", 0), step.get("z_s16", 0),
                step.get("ticks_u16", 0), exit_kind[step["kind"]],
                step.get("mode_u8", 0), step.get("subhandler_u8", 0)))
    lines.extend([
        "};", "",
        "static const AvspRound1CoffeeExitMotionSpec avsp_round1_coffee_exit_motion[AVSP_ROUND1_COFFEE_EXIT_MOTION_COUNT] =",
        "{",
    ])
    for row in coffee_exit_script["motion_vectors"]:
        lines.append("    { %d, %d }," % (row["x_s16"], row["z_s16"]))
    lines.extend([
        "};", "",
        "#define AVSP_ROUND1_COFFEE_EXIT_CALLBACK_FIRST_SOURCE_FRAME %du" %
            coffee_exit_callbacks["source_visible_frame_range_inclusive"][0],
        "#define AVSP_ROUND1_COFFEE_EXIT_CALLBACK_LAST_SOURCE_FRAME %du" %
            coffee_exit_callbacks["source_visible_frame_range_inclusive"][1],
        "",
        "static const AvspRound1CoffeeExitCallbackGroupSpec avsp_round1_coffee_exit_callbacks[AVSP_ROUND1_COFFEE_EXIT_CALLBACK_GROUP_COUNT] =",
        "{",
    ])
    for row in coffee_exit_callbacks["groups"]:
        lines.append("    { %du, %du, %du }," % (
            row["program_tick_u8"], row["display_ticks_u8"],
            row["updates_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1CoffeeExitCallbackGroupSpec avsp_round1_coffee_exit_scheduler_callbacks[AVSP_ROUND1_COFFEE_EXIT_SCHEDULER_GROUP_COUNT] =",
        "{",
    ])
    for row in coffee_exit_callbacks["fixed_pool_scheduler_groups"]:
        lines.append("    { %du, %du, %du }," % (
            row["program_tick_u8"], row["display_ticks_u8"],
            row["updates_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1CoffeeExitCallbackGroupSpec avsp_round1_coffee_exit_record20_prefix_callbacks[AVSP_ROUND1_COFFEE_EXIT_RECORD20_PREFIX_GROUP_COUNT] =",
        "{",
    ])
    for row in record20_exit_prefix_groups:
        lines.append("    { %du, %du, %du }," % (
            row["program_tick_u8"], row["display_ticks_u8"],
            row["updates_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1CoffeeExitBallisticSpec avsp_round1_coffee_exit_ballistic =",
        "{",
        "    %dL, %dL, %dL, %dL, %du, %du" % (
            coffee_exit_ballistic["x_velocity_s32"],
            coffee_exit_ballistic["x_acceleration_s32"],
            coffee_exit_ballistic["y_velocity_s32"],
            coffee_exit_ballistic["y_acceleration_s32"],
            coffee_exit_ballistic["selector_u8"],
            coffee_exit_ballistic["terminal_substate_u8"]),
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
        "static const AvspRound1Class1fActionRecordSpec avsp_round1_class1f_inner8_records[AVSP_ROUND1_CLASS1F_INNER8_RECORD_COUNT] =",
        "{",
    ])
    for row in class1f_inner8_records:
        lines.append(
            "    { %sUL, %sUL, %sUL, %du, %d, %du, %du, %du }," % (
                row["animation_record"], row["next_animation_record"],
                row["assembly"], row["timer_u16"], row["branch_s16"],
                row["hurt_selector_u8"], row["attack_selector_u8"],
                row["movement_table_index_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fMovementTableSpec avsp_round1_class1f_inner8_movement_tables[AVSP_ROUND1_CLASS1F_INNER8_MOVEMENT_TABLE_COUNT] =",
        "{",
    ])
    for table in class1f_inner8_movement_tables:
        vectors = ", ".join("{ %d, %d }" % (
            row["x_delta_s16"], row["y_delta_s16"])
            for row in table["vectors"])
        lines.append("    { %du, { %s } }," % (
            table["table_index_u8"], vectors))
    action0e_phase2 = class1f_inner8_motion["phase_2_terminal"]
    lines.extend([
        "};", "",
        "static const AvspRound1Class1fInner8ProgramSpec avsp_round1_class1f_inner8_program =",
        "{",
        "    0x%04Xu," % (int(class1f_inner8_path["source_slot"], 16) & 0xffff),
        "    %du, 0x%04Xu, 0x%04Xu, %du," % (
            class1f_inner8["entry_transition"]["timer_u16"],
            class1f_inner8_timeout["writes"]["outer_state_u16"],
            class1f_inner8_timeout["writes"]["action_substate_u16"],
            class1f_inner8_timeout["writes"]["special_latch_ad_u8"]),
        "    1u, 4u, 8u,",
        "    %su, %su, %du, %du," % (
            class1f_inner8_tables["action0_style_bits_u16"],
            class1f_inner8_tables["action4_choice_bits_u16"],
            class1f_inner8_action4_contact["direction_delta_u8"],
            class1f_inner8_action4_contact["direction_mask_u8"]),
        "    %du," % class1f_inner8_action4_timer[
            "Coffee_Shop_stage_parameter_u16"],
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_action4_timer[
                "variant0_bank_by_stage_parameter_u8"]) + " },",
        "    {",
    ])
    for timer_row in class1f_inner8_action4_timer["signed_timer_banks_s8"]:
        lines.append("        { " + ", ".join(str(value) for value in
            timer_row) + " },")
    lines.extend([
        "    },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_tables["field88_by_rng_low_nibble_u8"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_tables["wander_quadrant_delta_by_rng_low_nibble_u8"]) + " },",
        "    { " + ", ".join(str(value) for value in
            class1f_inner8_tables["wander_target_offsets_s16"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_tables["wander_direction_delta_same_style_u8"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_tables["wander_direction_delta_other_style_u8"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_tables["direction_axis_equal_u8"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_tables["direction_octant_base_u8"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_groups["camera_band_thresholds_u16"]) + " },",
        "    %d, %du, %du," % (
            class1f_inner8_tables["wander_target_origin"]["z_offset_s16"],
            class1f_inner8_groups["group_count_u8"],
            class1f_inner8_groups["cursor_limit_u8"]),
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_action10_init[
                "x_offset_selector_by_rng_low_nibble_u8"]) + " },",
        "    { " + ", ".join(str(value) for value in
            class1f_inner8_action10_init["x_offsets_s16"]) + " },",
        "    %d, %du, %du," % (
            class1f_inner8_action10_init["z_offset_s16"],
            class1f_inner8_action10_init["action_timer_u8"],
            class1f_inner8_action10_init["lifetime_timer_u8"]),
        "    { " + ", ".join(
            f"{row['start_animation_record']}UL" for row in
            class1f_inner8_action6["selector_by_style"]) + " }, { " + ", ".join(
            f"{row['start_animation_record']}UL" for row in
            class1f_inner8_movement_selectors) + " }, { " + ", ".join(
            f"{row['start_animation_record']}UL" for row in
            class1f_inner8_action10_phase_selectors) + " },",
        "    0x0012D488UL, 0x0012D404UL, 0x0012D628UL,",
        "    0x0012E65CUL, 0x0012D50CUL, 0x0012E604UL, 0x0012E638UL, 0x0012E550UL,",
        "    96u, 12u, 16u, 12u, %du, %du," % (
            class1f_inner8_path["action_0x0e"]["terminal_delay_u8"],
            class1f_inner8_motion["motion_selector_u16"]),
        "    { %dL, %dL }, %dL, %dL, %dL," % (
            action0e_phase2["x_velocity_by_facing_s32_16_16"][0],
            action0e_phase2["x_velocity_by_facing_s32_16_16"][1],
            action0e_phase2["x_acceleration_s32_16_16"],
            action0e_phase2["y_velocity_s32_16_16"],
            action0e_phase2["y_acceleration_s32_16_16"]),
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_action0c_phase0[
                "variant0_plan_by_rng_index_u16"]) + " },",
        "    {",
    ])
    for sequence in class1f_inner8_action0c_phase0[
            "selector_sequences_by_plan"]:
        values = list(sequence["values_s16"])
        values.extend([-1] * (5 - len(values)))
        lines.append("        { " + ", ".join(str(value) for value in values) +
                     " },")
    lines.extend([
        "    },",
        "    { " + ", ".join(f"{row['selector_u8']}u" for row in
            class1f_inner8_action0c_phase0["selector_rows"]) + " },",
        "    { " + ", ".join(f"{row['start_animation_record']}UL" for row in
            class1f_inner8_action0c_phase0["selector_rows"]) + " },",
        "    { " + ", ".join(f"{value}u" for value in
            class1f_inner8_action0c_phase2["stage_offsets_u8"]) + " },",
        "    {",
    ])
    for row in class1f_inner8_action0c_phase2["timer_rows_u8"]:
        lines.append("        { " + ", ".join(
            f"{value}u" for value in row) + " },")
    lines.extend([
        "    },",
        "    %du," % class1f_inner8_action0c_phase2[
            "Coffee_Shop_stage_parameter_u16"],
        "    { " + ", ".join(
            f"0x{int(row['source_slot'], 16) & 0xffff:04X}u" for row in
            class1f_inner8_action0c["audio_triggers"]) + " },",
        "    { " + ", ".join(f"{row['command']}u" for row in
            class1f_inner8_action0c["audio_triggers"]) + " },",
        "    0x%04Xu, 0x%04Xu, %du, 0x%04Xu," % (
            class1f_inner8_scene_clear["result"]["outer_state_u16"],
            class1f_inner8_scene_clear["result"]["action_substate_u16"],
            class1f_inner8_scene_clear["result"]["special_latch_ad_u8"],
            class1f_inner8_scene_clear["result"]["inner_timer_u16"]),
        "    %du, %du, %du, { %du, %du }" % (
            class1f_inner8_scene_clear["result"]["direction_xor_u8"],
            class1f_inner8_scene_clear["result"]["direction_shift_u8"],
            class1f_inner8_scene_clear["result"]["direction_bias_u8"],
            class1f_inner8_scene_clear["result"]
                ["selectors_by_style85_u8"][0],
            class1f_inner8_scene_clear["result"]
                ["selectors_by_style85_u8"][1]),
        "};", "",
        "static const unsigned char avsp_round1_class1f_attack_timers[AVSP_ROUND1_CLASS1F_ATTACK_TIMER_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in action_attack_timers),
        "};", "",
        "static const AvspRound1Class1fActionProgramSpec avsp_round1_class1f_action_program =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu, %du," % (
            action_bounds["x_max_u16"],
            action_bounds["camera_relative_bias_u16"],
            action_bounds["camera_relative_span_u16"],
            action_bounds["failure_outer_state_u16"],
            action_bounds["phase_guard_mask_u8"]),
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
            action_jump["z_velocity_table_s32_16_16"]) + " },",
        "    %dL, %dL, %d, %dL," % (
            action_jump["y_velocity_s32_16_16"],
            action_jump["y_acceleration_s32_16_16"],
            action_jump["initial_y_add_s16"],
            action_fall["y_delta_s32_16_16"]),
        "    %du, %du, %du, %du, %du," % (
            action_fall["initial_selector_u8"],
            action_fall["middle_selector_u8"],
            action_jump["initial_selector_u8"],
            action_jump["landing_selector_u8"],
            action_jump["terminal_style85_u8"]),
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
        "static const AvspRound1Class1fPlayerCollisionSpec avsp_round1_class1f_player_collision =",
        "{",
        "    %sUL, %sUL, %sUL, %sUL, %sUL, %sUL," % (
            action_player_collision["attacker"]["table_set"],
            action_player_collision["attacker"]["attack_record"],
            action_player_collision["defender"]["table_set"],
            action_player_collision["defender"]["hurt_record"],
            action_player_collision["defender"]["animation_record"],
            action_player_collision["observed_transaction"]["writer_pc"]),
        "    %du, %du, %du, %du, %du," % (
            action_player_collision["observed_transaction"]
                ["source_frame_u16"],
            action_player_collision["attacker"]["attack_selector_u8"],
            action_player_collision["defender"]["hurt_selector_u8"],
            action_player_collision["observed_transaction"]["damage_s16"],
            action_player_collision["observed_transaction"]["hitstop_u8"]),
        "    { %d, %d, %du, %du, %d, %du, %d, %du, 0u }," % (
            action_player_collision["attacker"]["box"]["x_center"],
            action_player_collision["attacker"]["box"]["y_center"],
            action_player_collision["attacker"]["box"]["x_half"],
            action_player_collision["attacker"]["box"]["y_half"],
            action_player_collision["attacker"]["box"]["z_center"],
            action_player_collision["attacker"]["box"]["z_half"],
            action_player_collision["attacker"]["knockback_mode_s8"],
            action_player_collision["attacker"]["hit_value_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }," % (
            action_player_collision["defender"]["box"]["x_center"],
            action_player_collision["defender"]["box"]["y_center"],
            action_player_collision["defender"]["box"]["x_half"],
            action_player_collision["defender"]["box"]["y_half"],
            action_player_collision["defender"]["box"]["z_center"],
            action_player_collision["defender"]["box"]["z_half"]),
        "    %sUL, %du, %su, %su, %d, %d, %d, %du, %s, %du" % (
            class4e_variant0["allocation"]["source_slot"],
            class4e_variant0["allocation"]["visible_frame_u16"],
            class4e_variant0["state0"]["first_seed_before"],
            class4e_variant0["state0"]["first_seed_after"],
            *class4e_variant0["allocation"]["first_spawn_position_s16"],
            class4e_variant0["allocation"]["record_type_u8"],
            class4e_variant0["allocation"]["class_u8"],
            class4e_variant0["allocation"]["variant_field"]["variant_u8"]),
        "};", "",
        "static const AvspRound1PlayerSpecialTargetCollisionSpec avsp_round1_player_special_class1f_collision =",
        "{",
        "    0x0011AE02UL, %sUL, %sUL, %sUL," % (
            player_special_target_collision["attack_record"]["address"],
            player_special_target_collision["class1f_target"]["table_set"],
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["address"]),
        "    %sUL, %sUL, %sUL, %sUL," % (
            player_special_target_collision["class1f_target"]["damage_writer"],
            player_special_target_collision["class1f_target"]["clamp_writer"],
            player_special_target_collision["class1f_target"]["reaction_writer"],
            player_special_target_collision["class1f_target"]["source_slot"]),
        "    %du, 0x0200u, 0x0402u, %d, %d, %d," % (
            player_special_target_collision["source_frame_u16"],
            player_special_target_collision["class1f_target"]["health_before_s16"],
            player_special_target_collision["class1f_target"]
                ["health_after_damage_s16"],
            player_special_target_collision["class1f_target"]
                ["health_after_clamp_s16"]),
        "    %du, %du, %du, %du," % (
            player_special_target_collision["attack_selector_u8"],
            player_special_target_collision["class1f_target"]
                ["hurt_selector_u8"],
            player_special_target_collision["class1f_target"]["damage_s16"],
            player_special_target_collision["impact_allocation"]["variant_u8"]),
        "    { %d, %d, %du, %du, %d, %du, %d, %du, 0u }," % (
            player_special_target_collision["attack_record"]["x_center_s8"],
            player_special_target_collision["attack_record"]["y_center_s8"],
            player_special_target_collision["attack_record"]["x_half_u8"],
            player_special_target_collision["attack_record"]["y_half_u8"],
            player_special_target_collision["attack_record"]["z_center_s8"],
            player_special_target_collision["attack_record"]["z_half_u8"],
            player_special_target_collision["attack_record"]["knockback_mode_s8"],
            player_special_target_collision["attack_record"]["hit_value_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }," % (
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["x_center_s8"],
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["y_center_s8"],
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["x_half_u8"],
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["y_half_u8"],
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["z_center_s8"],
            player_special_target_collision["class1f_target"]["hurt_record"]
                ["z_half_u8"]),
        "    %sUL, %du, %d, %d, %d, %du" % (
            player_special_target_collision["class1f_target"]
                ["impact_source_slot"],
            player_special_target_collision["class1f_target"]
                ["impact_visible_frame_u16"],
            *player_special_target_collision["class1f_target"]
                ["impact_spawn_position_s16"],
            player_special_target_collision["class1f_target"]
                ["impact_facing_u8"]),
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
            "    { %sUL, 0x%04Xu, 0x%04Xu, %d, %d, %d, %du, %du, %du, %s, %du, 0x%02Xu, %du, %du, %du }," % (
                row["source_slot"], row["state_u16"], phase,
                row["x_s16"], row["y_s16"], row["z_s16"],
                row["facing_u8"], row["coordinate_mode_u8"],
                row["palette_u8"], row["object_or_u16"], timer, source_flags,
                initializer["animation_selector_u8"], row["hurt_selector_u8"],
                row["attack_selector_u8"]))
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
        "static const AvspRound1Type16Spec avsp_round1_type16 =",
        "{",
    ])
    type16_collision = class16["current_state_collision"]
    type16_attack = type16_collision["attack_record"]
    type16_hurt = type16_collision["player_hurt_record"]
    lines.extend([
        "    %sUL, %sUL, %sUL, %sUL, %sUL, %sUL, %sUL, %sUL," % (
            class16["dispatch"], class16["spawn_owner"]["routine"],
            class16["spawn_owner"]["allocator"],
            class16["release_state"]["release_routine"],
            class16["initialization"]["collision_table"],
            type16_attack["address"], type16_collision["player_table"],
            type16_hurt["address"]),
        "    %d, %d, 0x0058u, 0x0232u, %d, %du, 0x%02X, %du, %du, %du," % (
            class16["spawn_owner"]["position_offset_s16"][0],
            class16["spawn_owner"]["position_offset_s16"][1],
            type16_collision["route_character_damage_s16"],
            class16["record_type_u8"], int(class16["class_u8"], 16),
            class16["current_state_collision"]["attack_selector_u8"],
            class16["current_state_collision"]["player_hurt_selector_u8"],
            type16_attack["hit_value_u8"]),
        "    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            type16_attack["x_center_s8"], type16_attack["y_center_s8"],
            type16_attack["x_half_u8"], type16_attack["y_half_u8"],
            type16_attack["z_center_s8"], type16_attack["z_half_u8"],
            type16_attack["knockback_mode_s8"],
            type16_attack["hit_value_u8"],
            type16_attack["damage_selector_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }" % (
            type16_hurt["x_center_s8"], type16_hurt["y_center_s8"],
            type16_hurt["x_half_u8"], type16_hurt["y_half_u8"],
            type16_hurt["z_center_s8"], type16_hurt["z_half_u8"]),
        "};", "",
        "static const AvspRound1Type16MotionSpec avsp_round1_type16_motion[AVSP_ROUND1_TYPE16_MOTION_COUNT] =",
        "{",
    ])
    for row in class16["initialization"]["variant_motion_16_16"]:
        values = [row[name] for name in
                  ("x_velocity_16_16", "x_acceleration_16_16",
                   "y_velocity_16_16", "y_acceleration_16_16",
                   "z_velocity_16_16")]
        values = [value - 0x100000000 if value >= 0x80000000 else value
                  for value in values]
        lines.append("    { %dL, %dL, %dL, %dL, %dL }," % tuple(values))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_type16_parent_records[AVSP_ROUND1_TYPE16_PARENT_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class16["spawn_owner"]["parent_animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_type16_records[AVSP_ROUND1_TYPE16_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in (class16["active_state"]["animation_records"] +
                class16["terminal_state"]["animation_records"]):
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    class08_parent = class08_pickup["parent"]
    class08_drop = class08_parent["drop"]
    class08_post_drop = class08_parent["post_drop_program"]
    class08_debris = class08_post_drop["debris"]
    health_pickup = class08_pickup["pickup"]
    pickup_initial = health_pickup["initialization"]
    pickup_interaction = health_pickup["player_interaction"]
    parent_collision = class08_parent["current_state_collision"]
    stage_record = class08_pickup["stage_spawn"]["record"]
    parent_attack_box = parent_collision["attack_record"]
    parent_hurt_box = parent_collision["hurt_record"]
    player_hurt_box = pickup_interaction["player_hurt_record"]
    pickup_hurt_box = pickup_interaction["pickup_hurt_record"]
    pickup_motion = pickup_initial["velocity_acceleration_16_16"]
    first_landing = health_pickup["movement"]["first_landing_result"]
    lines.extend([
        "};", "",
        "static const AvspRound1Class08HealthPickupSpec avsp_round1_class08_health_pickup =",
        "{",
        "    %sUL, %sUL, %sUL, %sUL, %sUL," % (
            class08_pickup["stage_spawn"]["stage_record_address"],
            class08_parent["source_slot"], health_pickup["source_slot"],
            class08_parent["dispatch"], health_pickup["dispatch"]),
        "    %sUL, %sUL, %sUL, %sUL," % (
            parent_attack_box["address"], parent_hurt_box["address"],
            player_hurt_box["address"], pickup_hurt_box["address"]),
        "    %du, %du, %su, %d, %d, %d, %d, %d," % (
            stage_record["gate_u16"], stage_record["allocator_selector_u16"],
            stage_record["class_variant_word_u16"], stage_record["x_s16"],
            stage_record["y_s16"], parent_collision["health_before_s16"],
            parent_collision["damage_s16"],
            parent_collision["health_after_clamp_s16"]),
        "    0x0400u, %du, %su, %su, 0x0200u, %du, 0x0004u, 0x0200u, 0x0600u," % (
            class08_drop["reaction_timer_u8"],
            class08_drop["audio"]["command_u16"],
            health_pickup["subtype_u8"],
            pickup_initial["motion_substate_u16"]),
        "    %d, %d, %d, %dL, %dL, %dL, %dL, %dL," % (
            pickup_initial["position_s16"][0],
            pickup_initial["position_s16"][1],
            pickup_initial["position_s16"][2], pickup_motion["x"],
            pickup_motion["y"], pickup_motion["y_acceleration"],
            first_landing["y_velocity_16_16"],
            first_landing["y_acceleration_16_16"]),
        "    %su, %d, %d, %su, %su, %su," % (
            pickup_interaction["action_u16"],
            pickup_interaction["subtype_amount_s16"],
            pickup_interaction["health_cap_s16"],
            pickup_interaction["audio_edge"]["command_u16"],
            class08_drop["seed_before"], class08_drop["seed_after"]),
        "    %du, %s, %du, %s, %du, %du, %du, %du, %du, %du, %du, %su, %su, %du," % (
            class08_parent["record_type_u8"], class08_parent["class_u8"],
            health_pickup["record_type_u8"], health_pickup["class_u8"],
            parent_collision["hurt_selector_u8"],
            pickup_interaction["pickup_hurt_selector_u8"],
            pickup_interaction["player_hurt_selector_u8"],
            parent_attack_box["impact_variant_u8"],
            parent_attack_box["damage_selector_u8"],
            parent_attack_box["hit_value_u8"], class08_drop["rng_calls_u8"],
            class08_drop["selector_mask_u8"],
            class08_drop["selector_source"]["value_u8"],
            pickup_initial["field5c_u8"]),
        "    %du," % pickup_initial["field64_u8"],
        "    { " + ", ".join(f"{value}u" for value in
            class08_drop["selector_source"]["row_u8"]) + " },",
        "    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            parent_attack_box["x_center_s8"],
            parent_attack_box["y_center_s8"],
            parent_attack_box["x_half_u8"],
            parent_attack_box["y_half_u8"],
            parent_attack_box["z_center_s8"],
            parent_attack_box["z_half_u8"],
            parent_attack_box["knockback_mode_s8"],
            parent_attack_box["hit_value_u8"],
            parent_attack_box["damage_selector_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }," % (
            parent_hurt_box["x_center_s8"], parent_hurt_box["y_center_s8"],
            parent_hurt_box["x_half_u8"], parent_hurt_box["y_half_u8"],
            parent_hurt_box["z_center_s8"], parent_hurt_box["z_half_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }," % (
            player_hurt_box["x_center_s8"], player_hurt_box["y_center_s8"],
            player_hurt_box["x_half_u8"], player_hurt_box["y_half_u8"],
            player_hurt_box["z_center_s8"], player_hurt_box["z_half_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }" % (
            pickup_hurt_box["x_center_s8"], pickup_hurt_box["y_center_s8"],
            pickup_hurt_box["x_half_u8"], pickup_hurt_box["y_half_u8"],
            pickup_hurt_box["z_center_s8"], pickup_hurt_box["z_half_u8"]),
        "};", "",
        "static const AvspRound1Class08DebrisSpec avsp_round1_class08_debris =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu, %d," % (
            class08_debris["state_u16"],
            class08_debris["alternate"]["landing_substate_u16"],
            class08_debris["primary"]["landing_state_u16"],
            class08_debris["primary"]["landing_substate_u16"],
            class08_debris["ground_s16"]),
        "    %dL, %dL, %dL, %dL, %dL," % (
            class08_debris["primary"]["initial_x_fp_s32"],
            class08_debris["primary"]["initial_y_fp_s32"],
            class08_debris["primary"]["x_velocity_s32"],
            class08_debris["primary"]["y_velocity_s32"],
            class08_debris["primary"]["y_acceleration_s32"]),
        "    %dL, %dL, %dL, %dL, %dL, %dL, %dL" % (
            class08_debris["alternate"]["initial_x_fp_s32"],
            class08_debris["alternate"]["initial_y_fp_s32"],
            class08_debris["alternate"]["x_velocity_s32"],
            class08_debris["alternate"]["y_velocity_s32"],
            class08_debris["alternate"]["y_acceleration_s32"],
            class08_debris["alternate"]["freeze_result"]["x_fp_s32"],
            class08_debris["alternate"]["freeze_result"]["y_fp_s32"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class08_parent_records[AVSP_ROUND1_CLASS08_PARENT_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in [class08_parent["initialization"]["animation_record"],
                class08_drop["animation_record"],
                class08_post_drop["reaction_hold"]["terminal_prelude"],
                class08_debris["primary"]["animation_record"],
                class08_debris["alternate"]["animation_record"]]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_health_pickup_records[AVSP_ROUND1_HEALTH_PICKUP_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in [pickup_initial["animation_record"]]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_player_pickup_records[AVSP_ROUND1_PLAYER_PICKUP_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in pickup_interaction["presentation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
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
        "static const AvspRound1Class4eRngSpec avsp_round1_class4e_rng[AVSP_ROUND1_CLASS09_INITIAL_ACTOR_COUNT] =",
        "{",
    ])
    for row in class4e_rng:
        lines.append("    { %sUL, %su, %su, %du }," % (
            row["source_slot"], row["seed_before"], row["seed_after"],
            row["table_index"]))
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
        "static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant0_records[AVSP_ROUND1_CLASS4E_VARIANT0_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4e_variant0["active_state"]["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant1_records[AVSP_ROUND1_CLASS4E_VARIANT1_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4e_variant1["active_state"]["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant10_records[AVSP_ROUND1_CLASS4E_VARIANT10_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4e_variant10["active_state"]["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant5_records[AVSP_ROUND1_CLASS4E_VARIANT5_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4e_variant5["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class4e_variant20_records[AVSP_ROUND1_CLASS4E_VARIANT20_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4e_variant20["animation_records"]:
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
    class43_sequences = class43["state0"]["animation_sequences"]
    class43_sequence_offsets = []
    class43_records = []
    for sequence in class43_sequences:
        class43_sequence_offsets.append(len(class43_records))
        class43_records.extend(sequence["records"])
    lines.extend([
        "};", "",
        "static const AvspRound1Class43Spec avsp_round1_class43 =",
        "{",
        "    %s, %du, %du, %du, %du, %d, %d, %sUL" % (
            class43["class_u8"], class43["variant_u8"],
            class43["spawn_owner"]["groups_u8"],
            class43["spawn_owner"]["attempts_per_group_u8"],
            class43["rng_calls_per_actor_u8"], 80, -1,
            class43["dispatch"]),
        "};", "",
        "static const unsigned char avsp_round1_class43_animation_selectors[AVSP_ROUND1_CLASS43_SELECTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in
                              class43["state0"]["animation_selector_table_u8"]),
        "};", "",
        "static const unsigned char avsp_round1_class43_sequence_offsets[AVSP_ROUND1_CLASS43_SEQUENCE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in
                              class43_sequence_offsets),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class43_records[AVSP_ROUND1_CLASS43_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class43_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class45MotionSpec avsp_round1_class43_motion[AVSP_ROUND1_CLASS43_MOTION_COUNT] =",
        "{",
    ])
    for row in class43["state0"]["motion_table"]:
        lines.append("    { %d, %d, %d, %d, %d, %d }," % (
            row["primary_x_velocity_s16"],
            row["primary_y_velocity_s16"],
            row["primary_y_acceleration_s16"],
            row["alternate_x_velocity_s16"],
            row["alternate_y_velocity_s16"],
            row["alternate_y_acceleration_s16"]))
    lines.extend([
        "};", "",
        "static const unsigned long avsp_round1_class45_source_slots[AVSP_ROUND1_CLASS45_SCENE_ACTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"{slot}UL" for slot in
                              class45["source_slots_scheduler_order"]),
        "};", "",
        "static const AvspRound1Class45SpawnGroupSpec avsp_round1_class45_spawn_groups[AVSP_ROUND1_CLASS45_SPAWN_GROUP_COUNT] =",
        "{",
    ])
    for group in class45["spawn_owner"]["groups"]:
        attempts = group["attempts_u16"]
        attempts_value = 0xffff if isinstance(attempts, str) else attempts
        lines.append("    { %du, %d, %d, %d }," % (
            attempts_value, group["x_offset_s16"], group["y_offset_s16"],
            group["z_offset_s16"]))
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_class45_animation_selectors[AVSP_ROUND1_CLASS45_SELECTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in
                              class45["state0"]["animation_selector_table_u8"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class45_records[AVSP_ROUND1_CLASS45_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class45["state0"]["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class45MotionSpec avsp_round1_class45_motion[AVSP_ROUND1_CLASS45_MOTION_COUNT] =",
        "{",
    ])
    for row in class45["state0"]["motion_table"]:
        lines.append("    { %d, %d, %d, %d, %d, %d }," % (
            row["primary_x_velocity_s16"],
            row["primary_y_velocity_s16"],
            row["primary_y_acceleration_s16"],
            row["alternate_x_velocity_s16"],
            row["alternate_y_velocity_s16"],
            row["alternate_y_acceleration_s16"]))
    lines.extend([
        "};", "",
        "static const unsigned long avsp_round1_class47_source_slots[AVSP_ROUND1_CLASS47_SCENE_ACTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"{slot}UL" for slot in
                              class47["source_slots_scheduler_order"]),
        "};", "",
        "static const AvspRound1Class47Spec avsp_round1_class47 =",
        "{",
        "    %s, %du, %du, %du, %d, %d, %sUL" % (
            class47["class_u8"], class47["variant_u8"],
            class47["spawn_owner"]["attempts_u16"],
            class47["rng_calls_per_actor_u8"],
            80, -1, class47["dispatch"]),
        "};", "",
        "static const unsigned char avsp_round1_class47_animation_selectors[AVSP_ROUND1_CLASS47_SELECTOR_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in
                              class47["state0"]["animation_selector_table_u8"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class47_records[AVSP_ROUND1_CLASS47_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class47["state0"]["animation_records"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class45MotionSpec avsp_round1_class47_motion[AVSP_ROUND1_CLASS47_MOTION_COUNT] =",
        "{",
    ])
    for row in class47["state0"]["motion_table"]:
        lines.append("    { %d, %d, %d, %d, %d, %d }," % (
            row["primary_x_velocity_s16"],
            row["primary_y_velocity_s16"],
            row["primary_y_acceleration_s16"],
            row["alternate_x_velocity_s16"],
            row["alternate_y_velocity_s16"],
            row["alternate_y_acceleration_s16"]))
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
        "static const AvspRound1TerrainSelectorRunSpec avsp_round1_first_segment_terrain_selector_runs[AVSP_ROUND1_TERRAIN_SELECTOR_RUN_COUNT] =",
        "{",
    ])
    for length, selector in terrain_selector_runs:
        lines.append(
            f"    {{ {length - 1}u, 0x{selector:02X}u }},")
    lines.extend([
        "};", "",
        "static const AvspRound1TerrainStreamWriteSpec avsp_round1_coffee_shop_terrain_stream_writes[AVSP_ROUND1_TERRAIN_STREAM_WRITE_COUNT] =",
        "{",
    ])
    for index, selector, attribute in terrain_stream_writes:
        lines.append(f"    {{ {index}u, 0x{selector:02X}u, 0x{attribute:02X}u }},")
    lines.extend([
        "};", "",
        "static const AvspRound1TerrainStreamTransactionSpec avsp_round1_coffee_shop_terrain_stream_transactions[AVSP_ROUND1_TERRAIN_STREAM_TRANSACTION_COUNT] =",
        "{",
    ])
    for transaction, (first_write, write_count) in zip(
            terrain_stream_transactions, terrain_stream_ranges):
        lines.append(
            "    { %d, %d, %du, %du, %du, 0x%02Xu, %du, %du }," % (
                transaction["camera_x_observed_s16"],
                transaction["camera_z_observed_s16"],
                transaction["camera_x_tile_u8"],
                transaction["camera_z_tile_u8"],
                transaction["direction_u8"],
                transaction["phase_after_u8"],
                first_write, write_count))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_coffee_shop_obstacle_records[AVSP_ROUND1_OBSTACLE_PARENT_RECORD_COUNT] =",
        "{",
    ])
    for row in obstacle_parent_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1ObstacleChildSequenceSpec avsp_round1_coffee_shop_obstacle_child_sequences[AVSP_ROUND1_OBSTACLE_CHILD_VARIANTS] =",
        "{",
    ])
    for variant in range(4):
        sequence = obstacle_child_sequences[str(variant)]
        rendered = ["{ %du, %d, %sUL, %sUL, %du, %du }" % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]) for row in sequence]
        while len(rendered) < 8:
            rendered.append("{ 0u, 0, 0UL, 0UL, 0u, 0u }")
        lines.append("    { %du, { %s } }," % (
            len(sequence), ", ".join(rendered)))
    release_record = obstacle_child["release_record"]
    physics = obstacle_state_program["state_0404"]["initial_fields_s16"]
    child_alloc = obstacle_initializer["child_allocation"]
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_coffee_shop_obstacle_child_release =",
        "{ %du, %d, %sUL, %sUL, %du, %du };" % (
            release_record["timer_u16"], release_record["branch_s16"],
            release_record["animation_record"], release_record["assembly"],
            release_record["hurt_selector_u8"],
            release_record["attack_selector_u8"]),
        "", "static const AvspRound1ObstacleLifecycleSpec avsp_round1_coffee_shop_obstacle_lifecycle =",
        "{",
        "    %sUL, %sUL, 0x06DE92UL, %sUL," % (
            obstacle_scene_record["address"], obstacle_lifecycle["spawn"]["slot"],
            obstacle_state_program["state_0200"]["player_trigger"]["attack_record"]),
        "    %du, %d, %d, %d, %d," % (
            obstacle_scene_record["camera_threshold_u16"],
            obstacle_scene_record["x_s16"], obstacle_scene_record["y_s16"],
            obstacle_scene_record["y_s16"], obstacle_initializer["writes"]["health_s16"]),
        "    0x0200u, 0x0400u, 0x0402u, 0x0404u, 0x0604u,",
        "    0x8000u, 0x1Du, %du, 0x%02X, %du," % (
            child_alloc["record_type_u8"], child_alloc["class_u8"],
            child_alloc["count"]),
        "    { " + ", ".join(f"{value}u" for value in
            child_alloc["variant_order_u8"]) + " },",
        "    %du, %du, %du, %du, %d," % (
            obstacle_state_program["state_0400"]["timer_high_byte_u8"],
            obstacle_state_program["state_0200"]["player_trigger"]["damage_s16"],
            obstacle_state_program["state_0200"]["player_trigger"]["edge_to_damage_ticks_u8"],
            obstacle_player_attack["hit_value_u8"],
            obstacle_player_attack["knockback_mode_s8"]),
        "    %du, %su," % (
            obstacle_break["presentation_rng_transaction"]["calls_u8"],
            obstacle_break["audio_transaction"]["command_u16"]),
        "    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            obstacle_player_attack["x_center_s8"],
            obstacle_player_attack["y_center_s8"],
            obstacle_player_attack["x_half_u8"],
            obstacle_player_attack["y_half_u8"],
            obstacle_player_attack["z_center_s8"],
            obstacle_player_attack["z_half_u8"],
            obstacle_player_attack["knockback_mode_s8"],
            obstacle_player_attack["hit_value_u8"],
            obstacle_player_attack["damage_s16"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }," % (
            obstacle_hurt["x_center_s8"], obstacle_hurt["y_center_s8"],
            obstacle_hurt["x_half_u8"], obstacle_hurt["y_half_u8"],
            obstacle_hurt["z_center_s8"], obstacle_hurt["z_half_u8"]),
        "    { %d, %d, %d, %d, %d, %d, %d, %d }" % (
            physics["field30"], physics["field34"], physics["field38"],
            physics["field3c"], physics["field32"], physics["field36"],
            physics["field3a"], physics["field3e"]),
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
        f"    {int(locomotion_execution['movement']['right_delta_s16_16'], 16)}L,",
        f"    {locomotion_execution['current_collision_selector_projection']['actor_hurt_selector_u8']}u,",
        f"    {locomotion_execution['current_collision_selector_projection']['actor_attack_selector_u8']}u,",
        "    {" + ", ".join(f"{value}u" for value in direction_resolver) + "}",
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_player_walk_records[AVSP_ROUND1_PLAYER_WALK_PRESENTATION_COUNT] =",
        "{",
    ])
    for index, row in enumerate(locomotion_records):
        lines.append("    { 4u, %d, 0x%08XUL, 0x%08XUL, %du, %du }," % (
            -32768 if index + 1 == len(locomotion_records) else 0,
            int(row["animation_record"], 16), int(row["assembly"], 16),
            row["hurt_selector"], row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerHitSpec avsp_round1_player_hit =",
        "{",
        "    %sUL, %sUL, %sUL, %sUL, %sUL, %sUL," % (
            player_hit["source_routines"]["outer_dispatch_entry"],
            player_hit["source_routines"]["entry_body"],
            player_hit["source_routines"]["active_body"],
            player_hit["source_routines"]["phase_0x0200"],
            player_hit["source_routines"]["phase_0x0202"],
            player_hit["source_routines"]["phase_0x0204"]),
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu," % (
            player_hit_states["control_outer_u16"],
            player_hit_states["hit_outer_u16"],
            player_hit_states["entry_substate_u16"],
            player_hit_states["shake_substate_u16"],
            player_hit_states["motion_substate_u16"],
            player_hit_states["return_substate_u16"]),
        "    %du, %du, %du, %du, 0x%04Xu, %du," % (
            player_hit["entry_writes"]["shake_countdown_u8"],
            player_hit["entry_writes"]["motion_index_u8"],
            player_hit_return["writes"]["invulnerability_u8"],
            player_hit_return["writes"]["facing_u8"],
            player_hit["audio"]["command_u16"],
            1 if player_hit_interruption["mutation_control"]
                ["reject_edge_loss_during_shake"] else 0),
        "    %dL, %dL," % (
            player_hit_phase0["writes"]["x_velocity_s32_16_16"],
            player_hit_phase0["writes"]["x_acceleration_s32_16_16"]),
        "    { %du, 0, %sUL, %sUL, %du, %du }," % (
            player_hit_entry["visible_timer_u16"],
            player_hit_entry["animation_record"],
            player_hit_entry["assembly"],
            player_hit_entry["hurt_selector_u8"],
            player_hit_entry["attack_selector_u8"]),
        "    { %du, %d, %sUL, %sUL, %du, %du }," % (
            player_hit_phase0["presentation"]["timer_u16"],
            player_hit_phase0["presentation"]["branch_s16"],
            player_hit_phase0["presentation"]["animation_record"],
            player_hit_phase0["presentation"]["assembly"],
            player_hit_phase0["presentation"]["hurt_selector_u8"],
            player_hit_phase0["presentation"]["attack_selector_u8"]),
        "    { %du, %d, %sUL, %sUL, %du, %du }," % (
            player_hit_return["presentation"]["timer_u16"],
            player_hit_return["presentation"]["branch_s16"],
            player_hit_return["presentation"]["animation_record"],
            player_hit_return["presentation"]["assembly"],
            player_hit_return["presentation"]["hurt_selector_u8"],
            player_hit_return["presentation"]["attack_selector_u8"]),
        "    { " + ", ".join(str(value) for value in
            player_hit["shake"]["table_s16"]) + " }",
        "};", "",
        "static const AvspRound1PlayerHitReactionSpec avsp_round1_player_hit_reactions[AVSP_ROUND1_PLAYER_HIT_REACTION_COUNT] =",
        "{",
    ])
    for row in player_hit_reactions:
        presentation = row["presentation"]
        motion = row["motion"]
        lines.append(
            "    { %sUL, %dL, %dL, { %du, %d, %sUL, %sUL, %du, %du }, %d, %du, 0x%02x, %du, %du, %du, %du, %du, %du }," % (
                row["attack_record"],
                motion["x_velocity_s32_16_16"],
                motion["x_acceleration_s32_16_16"],
                presentation["timer_u16"], presentation["branch_s16"],
                presentation["animation_record"], presentation["assembly"],
                presentation["hurt_selector_u8"],
                presentation["attack_selector_u8"], row["damage_s16"],
                row["source_record_type_u8"], row["source_class_s8"],
                row["source_attack_selector_u8"], row["hit_kind_u8"],
                row["presentation_selector_u8"],
                row["active_body_selector_u8"], row["shake_count_u8"],
                row["motion_index_u8"]))
    lines.extend([
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
        "static const AvspRound1PlayerContextualMeleeSpec avsp_round1_player_contextual_melee =",
        "{",
        "    %sUL, %sUL, %sUL, %sUL," % (
            contextual_melee["target_link"]["clear_writer"],
            contextual_melee["target_link"]["allocator_entry"],
            contextual_melee["target_link"]["target_to_player_writer"],
            contextual_melee["target_link"]["player_to_target_writer"]),
        "    %sUL, %sUL, %sUL, %sUL," % (
            contextual_melee["state_program"]["entry_body"],
            contextual_melee["state_program"]["active_body"],
            contextual_melee["state_program"]["common_reset"],
            contextual_melee["target_link"]["target_slot"]),
        "    %du, %du, %du, %du, %du, %du, %du," % (
            contextual_melee["target_link"]["target_low_u16"],
            contextual_melee["target_link"]["target_state_u16"],
            contextual_melee["target_link"]["target_substate_u16"],
            contextual_melee["dispatch"]["common_action_u16"],
            contextual_melee["dispatch"]["entry_action_u16"],
            contextual_melee["dispatch"]["active_action_u16"],
            30),
        "    { " + ", ".join("%du" % row["command_u16"] for row in
                              contextual_melee["audio_edges"]) + " },",
        "    %du, %d" % (
            contextual_melee["target_link"]["target_record_type_u8"],
            contextual_melee["target_link"]["target_class_s8"]),
        "};", "",
        "static const AvspRound1PlayerContextualMeleeSequenceSpec avsp_round1_player_contextual_melee_sequences[AVSP_ROUND1_PLAYER_CONTEXTUAL_MELEE_SEQUENCE_COUNT] =",
        "{",
    ])
    for sequence in contextual_sequences:
        rendered = ["{ %du, %d, %sUL, %sUL, %du, %du }" % (
            row["timer_u16"], row["branch_s16"],
            row["animation_record"], row["assembly"],
            row["hurt_selector_u8"], row["attack_selector_u8"])
            for row in sequence["records"]]
        while len(rendered) < 6:
            rendered.append("{ 0u, 0, 0UL, 0UL, 0u, 0u }")
        lines.append("    { %du, %du, %du, { %s } }," % (
            sequence["facing_u8"], sequence["selector_u8"],
            len(sequence["records"]), ", ".join(rendered)))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerHitInteractionSpec avsp_round1_player_hit_interaction =",
        "{",
        "    4u, %du, %du, %du," % (
            hit_interaction["entry"]["writes"]["outer_state_u16"],
            hit_interaction["entry"]["writes"]["action_u16"],
            hit_interaction["active"]["button1_interruption"]
                ["next_action_u16"]),
        "    0x0001abfcUL, 0x0001ac48UL, 0x0001a3faUL, %sUL," %
            hit_interaction_effect["dispatch"],
        "    1u, %du, %d, %du, %du" % (
            hit_interaction["entry"]["allocation"]["record_type_u8"],
            int(hit_interaction["entry"]["allocation"]["class_u8"], 16),
            hit_interaction["entry"]["allocation"]["variant_u8"],
            hit_interaction["entry"]["selector_argument_u8"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_player_hit_interaction_records[AVSP_ROUND1_PLAYER_HIT_INTERACTION_RECORD_COUNT] =",
        "{",
    ])
    for row in hit_interaction_player_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class20_interaction_records[AVSP_ROUND1_CLASS20_INTERACTION_RECORD_COUNT] =",
        "{",
    ])
    for row in hit_interaction_effect["presentation"]:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1CollisionBoxSpec avsp_round1_player_hit_interaction_attack_box =",
        "{ %d, %d, %du, %du, %d, %du, %d, %du, %du };" % (
            hit_interaction_collision["attack_record"]["x_center_s8"],
            hit_interaction_collision["attack_record"]["y_center_s8"],
            hit_interaction_collision["attack_record"]["x_half_u8"],
            hit_interaction_collision["attack_record"]["y_half_u8"],
            hit_interaction_collision["attack_record"]["z_center_s8"],
            hit_interaction_collision["attack_record"]["z_half_u8"],
            hit_interaction_collision["attack_record"]["knockback_mode_s8"],
            hit_interaction_collision["attack_record"]["hit_value_u8"],
            hit_interaction_collision["attack_record"]["damage_selector_u8"]),
        "static const AvspRound1CollisionBoxSpec avsp_round1_player_hit_interaction_hurt_box =",
        "{ %d, %d, %du, %du, %d, %du, 0, 0u, 0u };" % (
            hit_interaction_collision["hurt_record"]["x_center_s8"],
            hit_interaction_collision["hurt_record"]["y_center_s8"],
            hit_interaction_collision["hurt_record"]["x_half_u8"],
            hit_interaction_collision["hurt_record"]["y_half_u8"],
            hit_interaction_collision["hurt_record"]["z_center_s8"],
            hit_interaction_collision["hurt_record"]["z_half_u8"]),
        "static const short avsp_round1_player_hit_interaction_damage = %d;" %
            hit_interaction_collision["damage_s16"],
        "static const unsigned char avsp_round1_player_hit_interaction_impact_variant = %du;" %
            hit_interaction_collision["impact"]["variant_u8"],
        "",
        "static const AvspRound1PlayerHitInteractionTargetReactionSpec avsp_round1_player_hit_interaction_target_reaction =",
        "{",
        "    0x%04Xu, 0x%04Xu, 0x%04Xu, 0x%04Xu," % (
            hit_interaction_target_reaction["collision_handoff"]
                ["state_u16"],
            hit_interaction_target_reaction["collision_handoff"]
                ["substate_u16"],
            hit_interaction_target_reaction["reaction_entry"]
                ["substate_u16"],
            hit_interaction_target_reaction["first_flight"]
                ["substate_u16"]),
        "    %sUL, %sUL, 0x%04Xu, %du, %du, %du, %du, %du," % (
            hit_interaction_target_reaction["reaction_entry"]["record"]
                ["animation_record"],
            hit_interaction_target_reaction["first_flight"]
                ["terminal_record"]["animation_record"],
            hit_interaction_target_reaction["audio"]["command_u16"],
            hit_interaction_target_reaction["reaction_entry"]
                ["collision_freeze_ticks_u8"],
            hit_interaction_target_reaction["reaction_entry"]
                ["landing_hold_ticks_u8"],
            hit_interaction_target_reaction["reaction_entry"]
                ["preserved_collision_selectors"]["hurt_selector_u8"],
            hit_interaction_target_reaction["reaction_entry"]
                ["preserved_collision_selectors"]["attack_selector_u8"],
            1 if hit_interaction_target_reaction["shared_tail_overrides"]
                ["landing"]["same_dispatch_hold_decrement"] else 0),
        "    %dL, %dL, %dL, %dL" % (
            hit_interaction_target_reaction["first_flight"]
                ["x_velocity_s32_16_16"],
            hit_interaction_target_reaction["first_flight"]
                ["x_acceleration_s32_16_16"],
            hit_interaction_target_reaction["first_flight"]
                ["y_velocity_s32_16_16"],
            hit_interaction_target_reaction["first_flight"]
                ["y_acceleration_s32_16_16"]),
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
        "static const AvspRound1PlayerJumpTimingSpec avsp_round1_player_jump_timing =",
        "{",
        "    %du, %du, %du, %du, %du, 1u, %du, %d" % (
            jump_witness["pipeline_edge_frame"] -
                jump_witness["physical_input_frame"],
            jump_witness["jump_dispatch_frame"] -
                jump_witness["pipeline_edge_frame"],
            jump_witness["jump_dispatch_frame"] -
                jump_witness["physical_input_frame"],
            jump_witness["presentation_selector_u8"],
            jump["motion_and_landing"]["landing_0x023630"][
                "presentation_selector_u8"],
            jump_witness["chronology"][-1]["animation_timer_u16"],
            jump_witness["chronology"][-1]["animation_branch_s16"]),
        "};", "",
        "static const AvspRound1PlayerSpecialSpec avsp_round1_player_special =",
        "{",
        "    0x0800u, 0x0802u, 0x0804u, 0x0804u, 0x0000u,",
        "    %du, %du, %du, %du, 0x%02X, %du, 0x%02X," % (
            player_special["initialization"]["presentation_selector_u8"],
            player_special["active_state"]["contact_attack_selector_u8"],
            player_special["completion"]["health_cost_s16"],
            player_special["active_state"]["class4b_record_type_u8"],
            int(player_special["active_state"]["class4b_class_u8"], 16),
            player_special["active_state"]["class3d_record_type_u8"],
            int(player_special["active_state"]["class3d_class_u8"], 16)),
        "    %su, %su" % tuple(
            player_special["active_state"]["source_audio_commands"]),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_player_special_records[AVSP_ROUND1_PLAYER_SPECIAL_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in special_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"],
            row["animation_record"], row["assembly"],
            row["hurt_selector_u8"], row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_player_special_visible_durations[AVSP_ROUND1_PLAYER_SPECIAL_PRESENTATION_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in special_durations),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class4b_records[AVSP_ROUND1_CLASS4B_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class4b_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"],
            row["animation_record"], row["assembly"],
            row["hurt_selector_u8"], row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class3d_records[AVSP_ROUND1_CLASS3D_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class3d_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"],
            row["animation_record"], row["assembly"],
            row["hurt_selector_u8"], row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_class3d_offsets[AVSP_ROUND1_CLASS3D_OFFSET_COUNT] =",
        "{",
    ])
    for x, z in class3d_offsets:
        lines.append(f"    {{ {x}, {z} }},")
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerStageProgressSpec avsp_round1_player_stage_progress =",
        "{",
        f"    {weapon_stage_progress_helper['entry']}UL,",
        f"    {weapon_stage_progress['caller']['delta_load_pc']}UL,",
        f"    {weapon_stage_progress['caller']['helper_call_pc']}UL,",
        f"    0x{weapon_stage_progress_layout['guard']['a5_offset_u16']:04x}u,",
        f"    0x{weapon_stage_progress_layout['stage_parameter']['a5_offset_u16']:04x}u,",
        f"    0x{weapon_stage_progress_layout['upper_bound']['a5_offset_u16']:04x}u,",
        f"    0x{weapon_stage_progress_layout['lower_bound']['a5_offset_u16']:04x}u,",
        f"    0x{weapon_stage_progress_layout['progress']['a5_offset_u16']:04x}u,",
        f"    {weapon_stage_progress['caller']['delta_u16']}u,",
        f"    {weapon_stage_progress_helper['progress_threshold_u16']}u,",
        f"    {weapon_stage_progress_helper['progress_mask_u16']}u,",
        f"    {weapon_stage_progress_helper['stage_domain_limit_u16']}u,",
        f"    {weapon_stage_progress_helper['stage_domain_mask_u16']}u,",
        f"    {weapon_stage_progress_helper['coffee_shop_lower_bound_s16']},",
        f"    {weapon_stage_progress_helper['coffee_shop_upper_bound_s16']},",
        f"    {weapon_stage_progress['caller']['action_entry_tick_u8']}u",
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
        f"    {weapon['source_input']['action_dispatch_delay_updates_u8']}u,",
        f"    {weapon_action['parent_allocation_tick']}u,",
        f"    {weapon_action['resource_debit_tick']}u,",
        f"    {weapon_action['resource_capacity_u8']}u,",
        f"    {weapon_action['resource_debit_u8']}u,",
        f"    {weapon_action['recharge_countdown_after_entry_u8']}u,",
        f"    {weapon_resource['normal_tick']['reload_u8']}u,",
        f"    {weapon_resource['depleted_tick']['reload_u8']}u,",
        "    1u,",
        f"    {1 if weapon_action_entry['entry_preserves_current_presentation'] else 0}u,",
        "    1u,",
        f"    {weapon_empty_effect['variant']}u,",
        f"    {weapon_empty_effect['allocation']['allocation_update_after_entry_u8']}u,",
        "    1u,",
        f"    {weapon_parent['class_u8']},",
        f"    {weapon_child['class_u8']},",
        "    0x8680u,",
        "    0x0080u,",
        "    0x8380u,",
        f"    {weapon_parent['collision_table']['table']}UL,",
        f"    {weapon_child['collision_table']['table']}UL",
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_SELECTOR_COUNT][AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =",
        "{",
    ])
    for selector in weapon_selectors:
        lines.append("    {")
        for row in weapon_selector_timelines[str(selector)]:
            lines.append(
                "        { %du, %du, %sUL, %sUL, %du, %du, %du, %d }," % (
                    row["action_u16"], row["substate_u8"],
                    row["animation_record"], row["assembly"],
                    row["hurt_selector_u8"], row["attack_selector_u8"],
                    row["timer_u16"], row["branch_s16"]))
        lines.append("    },")
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_sequences[AVSP_ROUND1_PLAYER_WEAPON_SELECTOR_COUNT][AVSP_ROUND1_PLAYER_WEAPON_SEQUENCE_COUNT] =",
        "{",
    ])
    for selector in weapon_selectors:
        lines.append("    {")
        for row in weapon_selector_sequences[str(selector)]:
            lines.append(
                "        { %du, %du, %sUL, %sUL, %du, %du, %du, %d }," % (
                    row["action_u16"], row["substate_u8"],
                    row["animation_record"], row["assembly"],
                    row["hurt_selector_u8"], row["attack_selector_u8"],
                    row["timer_u16"], row["branch_s16"]))
        lines.append("    },")
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_empty_frames[AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in empty_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du, %du, %d }," % (
                row["action_u16"], row["substate_u8"], row["animation_record"],
                row["assembly"], row["hurt_selector_u8"],
                row["attack_selector_u8"], row["timer_u16"],
                row["branch_s16"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_return_frame =",
        "{",
        "    %du, %du, %sUL, %sUL, %du, %du, %du, %d" % (
            weapon_return_frame["action_u16"], weapon_return_frame["substate_u8"],
            weapon_return_frame["animation_record"],
            weapon_return_frame["assembly"],
            weapon_return_frame["hurt_selector_u8"],
            weapon_return_frame["attack_selector_u8"],
            weapon_return_frame["timer_u16"],
            weapon_return_frame["branch_s16"]),
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
        "static const unsigned short avsp_round1_weapon_target_distance_thresholds[AVSP_ROUND1_WEAPON_TARGET_DISTANCE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in parent_target_thresholds),
        "};", "",
        "static const unsigned char avsp_round1_weapon_target_presentation_selectors[AVSP_ROUND1_WEAPON_TARGET_DISTANCE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in parent_target_presentations),
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
        "static const AvspRound1VecS16 avsp_round1_weapon_parent_base_motion[AVSP_ROUND1_WEAPON_PARENT_ROUTE_ANGLE_COUNT] =",
        "{",
    ])
    for angle in parent_route_angles:
        lines.append("    { %d, %d }," % tuple(parent_base_motion[str(angle)]))
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
        "static const unsigned char avsp_round1_weapon_child_initial_facing = %du;" %
            parent_emitter["child_initial_facing_u8"], "",
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
        "static const AvspRound1PlayerWeaponEffectSpec avsp_round1_parent_weapon_effect =",
        "{",
        "    0x08F080UL, %du, 0x%02X, %du, %du, %du, %du" % (
            parent_effect["record_type_u8"], parent_effect["class_u8"],
            parent_effect["variant_u8"], parent_effect["timer_u8"],
            parent_effect["native_phase_projection"]["mask_u8"],
            parent_effect["native_phase_projection"]["expected_u8"]),
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
        f"    {parent_boxes['attack_relative_s16']},",
        f"    {child_boxes['attack_relative_s16']}, 16u,",
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
        "static const unsigned char avsp_round1_weapon_parent_impact_variants[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =",
        "{",
        "    " + ", ".join(f"{box['impact_variant_u8']}u" for box in parent_attack_boxes),
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
        "static const unsigned char avsp_round1_weapon_child_impact_variants[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =",
        "{",
        "    " + ", ".join(f"{box['impact_variant_u8']}u" for box in child_attack_boxes),
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
    lines.extend([
        "};", "",
        "static const AvspRound1CoffeeSceneRecordSpec avsp_round1_coffee_scene_records[AVSP_ROUND1_COFFEE_SCENE_RECORD_COUNT] =",
        "{",
    ])
    for row in coffee_scene_records:
        lines.append(
            "    { %sUL, %sUL, %du, %du, %d, %d, %du, 0x%02X, %du, %d, %du, %du, %du, %du }," % (
                row["address"], row["observed_source_slot"],
                row["observed_source_frame"], row["camera_threshold_u16"],
                row["x_s16"], row["y_s16"], row["allocator_u16"],
                row["class_u8"], row["variant_u8"], row["guard_0a_s8"],
                row["guard_0b_u8"], row["facing_u8"],
                row["field_0d_u8"], row["timer_u16"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class01_records[AVSP_ROUND1_CLASS01_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class01_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class02_records[AVSP_ROUND1_CLASS02_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class02_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class0f_records[AVSP_ROUND1_CLASS0F_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class0f_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class0a_records[AVSP_ROUND1_CLASS0A_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class0a_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class00CompanionAnimationSpec avsp_round1_class00_companion_records[AVSP_ROUND1_CLASS00_COMPANION_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class00_companion_records:
        lines.append("    { %du, { %du, %d, %sUL, %sUL, %du, %du } }," % (
            row["branch_s16"] + 32768, row["timer_u16"],
            row["branch_s16"], row["animation_record"], row["assembly"],
            row["hurt_selector_u8"], row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class00CompanionParentAnimationSpec avsp_round1_class00_companion_parent_animations[AVSP_ROUND1_CLASS00_COMPANION_PARENT_ANIMATION_COUNT] =",
        "{",
    ])
    for row in class00_companion_parent_animations:
        lines.append("    { %sUL, %du }," % (
            row["animation_record"],
            row["parent_animation_branch_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Class00CompanionParentEntrySpec avsp_round1_class00_companion_parent_entries[AVSP_ROUND1_CLASS00_COMPANION_PARENT_ENTRY_COUNT] =",
        "{",
    ])
    for row in class00_companion_parent_entries:
        lines.append("    { %du, %d, %d, %du, %du }," % (
            row["parent_animation_branch_u8"], row["x_offset_s8"],
            row["y_offset_s8"], row["animation_selector_u8"],
            row["parent_field56_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_type36_class03_records[AVSP_ROUND1_TYPE36_CLASS03_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class03_type36_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    class03_motion = class03_type36_contract["state_0x0000"][
        "motion_s16_16"]
    lines.extend([
        "};", "",
        "static const AvspRound1Type36Class03Spec avsp_round1_type36_class03 =",
        "{",
        "    0x09A67EUL, 0x0009A884UL, %dL, %dL, %dL, %dL," % (
            class03_motion["phase1_x_velocity"],
            class03_motion["phase3_x_velocity"],
            class03_motion["initial_y_velocity"],
            class03_motion["y_acceleration"]),
        "    0x0200u, 0x0400u, 0x0600u, 0x03, 36u, 1u",
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_type36_class04_records[AVSP_ROUND1_TYPE36_CLASS04_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class04_type36_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    lines.extend([
        "};", "",
        "static const AvspRound1Type36Class04Spec avsp_round1_type36_class04 =",
        "{",
        "    0x09AA90UL, 0x02F8DCUL, 0x0009AC82UL,",
        "    0x8380u, 0x0200u, 0x0400u, 0x0600u, 5, 86, 10u, 0x04, 36u, 0u",
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_class05_records[AVSP_ROUND1_CLASS05_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in class05_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer_u16"], row["branch_s16"], row["animation_record"],
            row["assembly"], row["hurt_selector_u8"],
            row["attack_selector_u8"]))
    class01_audio = class01_contract["audio_transactions"]
    attack_box = class02_collision["attack_box"]
    hurt_box = class02_collision["hurt_record"]
    class05_attack = class05_collision["attack_record"]
    class05_hurt = class05_collision["hurt_record"]
    lines.extend([
        "};", "",
        "static const AvspRound1Class05Spec avsp_round1_class05 =",
        "{",
        "    %sUL, 0x0006CD44UL, %sUL, %sUL," % (
            class05_prop["dispatch"], class05_attack["address"],
            class05_hurt["address"]),
        "    0x0200u, 0x0400u, 0x0402u, 0x0404u, 0x0200u, 0x0604u, 0x0300u,",
        "    %du, %su, %d, %d, 0x05, %du, %du, %du," % (
            class05_reaction["state_0x0400"]["timer_u16"],
            class05_reaction["state_0x0400"]["audio_command_u16"],
            class05_collision["damage_s16"],
            class05_collision["health_after_clamp_s16"],
            class05_prop["initialization"]["animation_record"]
                ["hurt_selector_u8"],
            class05_collision["impact_allocation"]["variant_u8"],
            class05_prop["initialization"]["field64_u8"]),
        "    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            class05_attack["x_center_s8"], class05_attack["y_center_s8"],
            class05_attack["x_half_u8"], class05_attack["y_half_u8"],
            class05_attack["z_center_s8"], class05_attack["z_half_u8"],
            class05_attack["knockback_mode_s8"],
            class05_attack["hit_value_u8"],
            class05_attack["damage_selector_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }" % (
            class05_hurt["x_center_s8"], class05_hurt["y_center_s8"],
            class05_hurt["x_half_u8"], class05_hurt["y_half_u8"],
            class05_hurt["z_center_s8"], class05_hurt["z_half_u8"]),
        "};", "",
        "static const AvspRound1Class05MotionSpec avsp_round1_class05_motion =",
        "{",
        "    %d, %dL, %dL, %dL, %dL, %dL, %dL, %dL, %dL" % (
            class05_motion["primary"]["initial_y_offset_s16"],
            class05_motion["primary"]["x_velocity_s32"],
            class05_motion["primary"]["y_velocity_s32"],
            class05_motion["primary"]["x_acceleration_s32"],
            class05_motion["primary"]["y_acceleration_s32"],
            class05_motion["alternate"]["x_velocity_s32"],
            class05_motion["alternate"]["y_velocity_s32"],
            class05_motion["alternate"]["x_acceleration_s32"],
            class05_motion["alternate"]["y_acceleration_s32"]),
        "};", "",
        "static const AvspRound1Class01Spec avsp_round1_class01 =",
        "{",
        "    0x06B2FAUL, 0x06B520UL, 240u, 60u, 360u, 192u, 40u,",
        "    5u, 6u, 0x1F, 5u, %su, %su" % (
            class01_audio[0]["command_u16"],
            class01_audio[1]["command_u16"]),
        "};", "",
        "static const AvspRound1Class02Spec avsp_round1_class02 =",
        "{",
        "    0x06B534UL, 0x06B6EAUL, %sUL, %sUL," % (
            class02_collision["attack_record"],
            class02_collision["hurt_record"]["address"]),
        "    16u, 0x01A0u, 5u, 28u, 0x05, 1u, 8, 64, -8, %d, %d, %su, 1u, 0u," % (
            class02_collision["damage_s16"],
            class02_collision["health_after_clamp_s16"],
            class02_contract["audio_transactions"][0]["command_u16"]),
        "    { %d, %d, %du, %du, %d, %du, %d, %du, 0u }," % (
            attack_box["x_center_s8"], attack_box["y_center_s8"],
            attack_box["x_half_u8"], attack_box["y_half_u8"],
            attack_box["z_center_s8"], attack_box["z_half_u8"],
            attack_box["knockback_mode_s8"], attack_box["hit_value_u8"]),
        "    { %d, %d, %du, %du, %d, %du, 0, 0u, 0u }" % (
            hurt_box["x_center_s8"], hurt_box["y_center_s8"],
            hurt_box["x_half_u8"], hurt_box["y_half_u8"],
            hurt_box["z_center_s8"], hurt_box["z_half_u8"]),
        "};", "",
        "static const AvspRound1Class0fSpec avsp_round1_class0f =",
        "{",
        "    0x06ED3EUL, 0x06EE42UL, 0x06EEE6UL,",
        "    0x0200u, 0x0202u, 0x0400u, 0x0600u, 2u, 0x1Du,",
        "    24u, 0x11, 4u, -1, 28u, 0x09, 80, -8, %su, %su, %sUL" % (
            class0f_contract["audio_transactions"][0]["command_u16"],
            class0f_contract["audio_transactions"][1]["command_u16"],
            class0f_contract["audio_transactions"][0]["argument1_u32"]),
        "};", "",
        "static const AvspRound1Class0aSpec avsp_round1_class0a =",
        "{",
        "    0x077CCCUL, 0x077D26UL, 0x0200u, 0x0400u, 0x0920u,",
        "    { 0x0Au, 0x0Cu, 0x0Eu }, 0x00FFC600UL, 0x00FFC580UL,",
        "    0x26u, 0x06u",
        "};", "",
        "static const AvspRound1Class00CompanionSpec avsp_round1_class00_companion =",
        "{",
        "    0x09E098UL, 0x0BCA3AUL, 0x00FFCE00UL, 0x8380u,",
        "    0x0206u, 0x0200u, 0x8000u, 0x22u, 0xFFu,",
        "    0x13u, 0xFFu, 0u",
        "};", "",
        "/* Source-display cadence derived from the accepted recurring-controller",
        " * transaction ledger. This is diagnostic replay timing, not a gameplay",
        " * transition trigger. */",
        "#define AVSP_ROUND1_COFFEE_SHOP_DEFAULT_SOURCE_UPDATES %su" %
            source_update_cadence["default_updates_per_source_frame_u8"],
        f"#define AVSP_ROUND1_COFFEE_SHOP_UPDATE_CADENCE_COUNT {len(source_update_exceptions)}",
        "static const AvspRound1SceneUpdateCadence avsp_round1_coffee_shop_update_cadence[AVSP_ROUND1_COFFEE_SHOP_UPDATE_CADENCE_COUNT] =",
        "{",
    ])
    for row in source_update_exceptions:
        lines.append("    { %su, %su }," % (
            row["source_frame_u16"], row["updates_u8"]))
    lines.extend([
        "};", "",
        "/* Source-display class-0x02 dispatch cadence from the accepted",
        " * record-20 indirect caller ledger. This is used only to align the",
        " * scene differential with source scheduler phases. */",
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS02_DEFAULT_SOURCE_UPDATES %su" %
            class02_source_cadence["default_updates_per_source_frame_u8"],
        f"#define AVSP_ROUND1_COFFEE_SHOP_CLASS02_UPDATE_CADENCE_COUNT {len(class02_source_exceptions)}",
        "static const AvspRound1SceneUpdateCadence avsp_round1_coffee_shop_class02_update_cadence[AVSP_ROUND1_COFFEE_SHOP_CLASS02_UPDATE_CADENCE_COUNT] =",
        "{",
    ])
    for row in class02_source_exceptions:
        lines.append("    { %su, %su }," % (
            row["source_frame_u16"], row["updates_u8"]))
    lines.extend([
        "};", "",
        "/* Source-display class-0x0a fixed-pool dispatch cadence. This",
        " * aligns the scene differential only and never owns gameplay. */",
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS0A_FIRST_SOURCE_FRAME %su" %
            class0a_cadence["source_frame_range_inclusive_u16"][0],
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS0A_LAST_SOURCE_FRAME %su" %
            class0a_cadence["source_frame_range_inclusive_u16"][1],
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS0A_DEFAULT_SOURCE_UPDATES %su" %
            class0a_cadence["default_updates_per_source_frame_u8"],
        f"#define AVSP_ROUND1_COFFEE_SHOP_CLASS0A_UPDATE_CADENCE_COUNT {len(class0a_cadence['exceptions'])}",
        "static const AvspRound1SceneUpdateCadence avsp_round1_coffee_shop_class0a_update_cadence[AVSP_ROUND1_COFFEE_SHOP_CLASS0A_UPDATE_CADENCE_COUNT] =",
        "{",
    ])
    for row in class0a_cadence["exceptions"]:
        lines.append("    { %su, %su }," % (
            row["source_frame_u16"], row["updates_u8"]))
    lines.extend([
        "};", "",
        "/* Source-display class-0x00 record-28 dispatch cadence. This",
        " * aligns the source-owned player companion with its pool phase;",
        " * it is not a fixed-frame gameplay transition. */",
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS00_FIRST_SOURCE_FRAME %su" %
            class00_companion_cadence[
                "source_frame_range_inclusive_u16"][0],
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS00_LAST_SOURCE_FRAME %su" %
            class00_companion_cadence[
                "source_frame_range_inclusive_u16"][1],
        "#define AVSP_ROUND1_COFFEE_SHOP_CLASS00_DEFAULT_SOURCE_UPDATES %su" %
            class00_companion_cadence[
                "default_updates_per_source_frame_u8"],
        f"#define AVSP_ROUND1_COFFEE_SHOP_CLASS00_UPDATE_CADENCE_COUNT {len(class00_companion_cadence['exceptions'])}",
        "static const AvspRound1SceneUpdateCadence avsp_round1_coffee_shop_class00_update_cadence[AVSP_ROUND1_COFFEE_SHOP_CLASS00_UPDATE_CADENCE_COUNT] =",
        "{",
    ])
    for row in class00_companion_cadence["exceptions"]:
        lines.append("    { %su, %su }," % (
            row["source_frame_u16"], row["updates_u8"]))
    lines.extend([
        "};", "",
        "/* Complete route-6 callback/fixed-pool phase program from the",
        " * paired class-0x00 scheduler witness. Two bits encode each event",
        " * from least-significant to most-significant. */",
        "#define AVSP_ROUND1_COFFEE_EXIT_CLASS00_PHASE_FIRST_SOURCE_FRAME 5453u",
        f"#define AVSP_ROUND1_COFFEE_EXIT_CLASS00_PHASE_COUNT {len(class00_exit_phase_program)}",
        "static const AvspRound1CoffeeExitClass00PhaseSpec avsp_round1_coffee_exit_class00_phase[AVSP_ROUND1_COFFEE_EXIT_CLASS00_PHASE_COUNT] =",
        "{",
    ])
    phase_codes = {"P": 0, "A": 1, "D": 2, "C": 3}
    for row in class00_exit_phase_program:
        packed = 0
        for index, event in enumerate(row["events"]):
            packed |= phase_codes[event] << (index * 2)
        lines.append("    { %su, 0x%02Xu, 0x%08XUL }," % (
            len(row["events"]), row["player_program_apply_mask_u8"], packed))
    lines.extend([
        "};", "",
        "/* Diagnostic-only replay of the accepted ORACLE-10 Coffee Shop",
        " * controller ledger. Native gameplay remains controller-driven;",
        " * this table exists only for source/native scene differential runs. */",
        f"#define AVSP_ROUND1_COFFEE_SHOP_INPUT_RUN_COUNT {len(scene_input_runs)}",
        "static const AvspRound1SceneInputRun avsp_round1_coffee_shop_input_runs[AVSP_ROUND1_COFFEE_SHOP_INPUT_RUN_COUNT] =",
        "{",
    ])
    for first, last, word in scene_input_runs:
        lines.append(f"    {{ {first}u, {last}u, 0x{word:04X}u }},")
    lines.extend(["};", "", "#endif", ""])
    return split_target_content("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered, content = build()
    if args.check:
        if (not OUT.exists() or OUT.read_text(encoding="ascii") != rendered or
                not OUT_CONTENT.exists() or
                OUT_CONTENT.read_text(encoding="ascii") != content):
            raise SystemExit("generated SPEC-02 Round 1 entry header is stale")
        print("SPEC-02 Round 1 entry data: PASS "
              "(generated header and cart image current)")
        return
    OUT.write_text(rendered, encoding="ascii", newline="\n")
    OUT_CONTENT.write_text(content, encoding="ascii", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"wrote {OUT_CONTENT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
