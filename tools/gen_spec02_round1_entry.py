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
    state_contexts = [tuple(int(part, 16) for part in context.split(":"))
                      for context in class1f["state_phase_contexts"]]
    navigation = fixtures["authority_data"]["navigation"]
    global_bounds = navigation["global_bounds"]
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
    weapon = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    weapon_states = weapon["state_dispatch"]
    weapon_volley = weapon["sufficient_volley"]
    weapon_resource = weapon["resource_tick"]
    weapon_empty = weapon["empty_fallback"]
    weapon_projectile = weapon["projectile_lifecycle_contract"]
    weapon_impact = weapon_projectile["impact_actor_contract"]
    weapon_collision = weapon_projectile["current_state_interfaces"]["collision"]
    weapon_damage = weapon_collision["damage"]
    weapon_empty_effect = weapon["empty_effect_variant1_contract"]
    weapon_frames = weapon["presentation_timeline"]
    empty_frames = weapon_empty["presentation_timeline"]
    weapon_return_frame = weapon["return_frame"]
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
    if (weapon["classification"] != "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        weapon["source_input"]["button1_mask"] != "0x0010" or
        weapon_states != {
            "sufficient_entry_action": "0x0c00",
            "sufficient_active_action": "0x0c02",
            "empty_entry_action": "0x1a00",
            "empty_active_action": "0x1a02",
            "cleanup_action": "0x0000",
            "return_locomotion_action": "0x0002"} or
        weapon_volley["attempt_counter_type"] != "s8" or
        weapon_volley["attempt_counter_initial"] != 12 or
        weapon_volley["cadence_counter_type"] != "u8" or
        weapon_volley["cadence_initial"] != 1 or
        weapon_volley["cadence_reload"] != 4 or
        weapon_volley["spawn_tick_offsets"] != list(range(0, 48, 4)) or
        weapon_volley["cleanup_tick_offset"] != 49 or
        weapon_volley["return_to_locomotion_tick_offset"] != 50 or
        weapon_volley["recovery_edge"] != {
            "input_tick_offset": 48,
            "cleanup_tick_offset": 49,
            "second_entry_tick_offset": 50} or
        weapon_volley["resource_debit"] != 3 or
        weapon_volley["resource_clamp_min"] != 0 or
        weapon_volley["resource_capacity"] != 64 or
        weapon_volley["recharge_countdown_after_success"] != 12 or
        weapon_volley["rng_calls"] != 0 or
        weapon_resource["normal_recharge_reload"] != 2 or
        weapon_resource["depleted_recharge_reload"] != 6 or
        weapon_empty["timer_type"] != "u8" or
        weapon_empty["timer_initial"] != 16 or
        weapon_empty["cleanup_tick_offset"] != 17 or
        weapon_empty["return_to_locomotion_tick_offset"] != 18 or
        weapon_empty["damaging_projectile_count"] != 0 or
        weapon["movement_facing"]["baseline_invariant"] is not True):
        raise ValueError("SPEC-02 Button1 action/resource contract drift")
    allocation = weapon_volley["successful_allocation_writes"]
    if (allocation != {
            "active_increment": 1,
            "attack_table": "0x03136a",
            "class": "0x05",
            "facing": "copy player facing",
            "owner": "player low-word pointer",
            "position": "copy player x/y/z",
            "variant": "0 except attempt counter 4 writes 1"} or
        weapon_projectile["spec_executable"] is not True or
        weapon_projectile["implementation_blocker"] is not None or
        weapon_impact["spec_executable"] is not True or
        weapon_empty_effect["spec_executable"] is not True):
        raise ValueError("SPEC-02 projectile implementation readiness drift")
    projectile_init = weapon_projectile["initialization"]
    projectile_active = weapon_projectile["active_state"]
    projectile_presentation_actor = projectile_init["presentation_actor_fields"]
    projectile_spawn_offsets = projectile_init["parent_presentation_selector"]["spawn_offsets_s16"]
    projectile_animation_selectors = projectile_init["parent_presentation_selector"]["animation_selector_u8"]
    projectile_presentations = projectile_init["parent_presentation_selector"]["presentation_sequences"]
    projectile_angles0 = projectile_init["angle"]["facing0_u8"]
    projectile_angles1 = projectile_init["angle"]["facing1_u8"]
    projectile_player_selectors = projectile_init["player_presentation_selector_u8"]
    projectile_motion = projectile_active["motion"]["vectors_s16"]
    projectile_boxes = weapon_collision["projectile_table"]
    projectile_hurt_boxes = projectile_boxes["hurt_entries"]
    projectile_attack_boxes = projectile_boxes["attack_entries"]
    impact_offsets = weapon_impact["initialization"]["variant_offsets_s16"]
    impact_records = weapon_impact["initialization"]["variant0_presentation_records"]
    impact_presentation_actor = weapon_impact["initialization"][
        "presentation_actor_fields"]
    impact_audio = weapon_impact["initialization"]["audio"]["alternating_command_u16"]
    impact_audio_selector = weapon_impact["initialization"]["audio"]["selector"]
    empty_effect_offsets = weapon_empty_effect["initialization"]["variant_offsets_s16"]
    empty_effect_records = weapon_empty_effect["active_state"]["presentation_records"]
    if (len(projectile_spawn_offsets) != 16 or
        len(projectile_animation_selectors) != 16 or
        len(projectile_presentations) != 16 or
        len(projectile_angles0) != 12 or len(projectile_angles1) != 12 or
        len(projectile_player_selectors) != 12 or
        len(projectile_motion) != 64 or len(projectile_hurt_boxes) != 1 or
        len(projectile_attack_boxes) != 3 or len(impact_offsets) != 5 or
        len(impact_records) != 5 or len(impact_audio) != 2 or
        len(empty_effect_offsets) != 4 or
        len(empty_effect_records) != 10):
        raise ValueError("SPEC-02 projectile/effect table cardinality drift")
    if (projectile_boxes["table_set"] != "0x03136a" or
        projectile_boxes["hurt_relative_s16"] != 4 or
        projectile_boxes["attack_relative_s16"] != 12 or
        weapon_impact["record_type"] != 24 or
        weapon_impact["class"] != "0x3a" or
        weapon_impact["variant"] != 0 or
        weapon_impact["dispatch"] != "0x086f62" or
        weapon_impact["state_sequence"] != [0, 2, 4] or
        projectile_presentation_actor["coordinate_mode_u8"] != 0 or
        projectile_presentation_actor["palette_u8"] != 0 or
        projectile_presentation_actor["object_or_u16"] != "0x8000" or
        impact_presentation_actor != projectile_presentation_actor or
        impact_audio != [0x007e, 0x0148] or
        impact_audio_selector != {
            "storage": "A5-0x7126 u8", "route_initial": 0,
            "read_rule": "use selector value 0 or 2 as byte offset into the two-word command table",
            "write_rule": "selector = u8(selector + 2) & 2 after the table read",
            "capture_projection": {"frame_4534": [0, 0],
                                   "frame_4535": [2, 1],
                                   "frame_4537": [0, 4]}} or
        weapon_damage["route_current_guards"] != {
            "A5_minus_0x6762_u16": 0,
            "A5_plus_0x244_u8": 0,
            "defender_plus_0x08_u8": 12,
            "defender_plus_0x73_u8": 0} or
        weapon_damage["baseline"] != {
            "attack_selector": 6, "attacker_class_index": 0,
            "damage": 24, "defender_class_index": 16,
            "defense": 33, "defense_address": "0x11420a",
            "health_after": 39, "health_before": 63,
            "matrix_address": "0x115326", "offense": 0,
            "offense_address": "0x11542a", "route_index": 10} or
        weapon_damage["mutation"]["damage"] != 31 or
        weapon_damage["mutation"]["offense"] != 4 or
        weapon_damage["suppression"]["baseline_writes"] != 8 or
        weapon_damage["suppression"]["mutated_writes"] != 4):
        raise ValueError("SPEC-02 projectile impact/collision/damage drift")
    projectile_authority = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["authority_separation"][
            "projectile_lifecycle"]
    if (projectile_authority["pool"] !=
            "record type 4; base 0xff8680; capacity 24; stride 0x80" or
        projectile_authority["allocator"] != "0x01773e" or
        projectile_authority["class"] != "0x05"):
        raise ValueError("SPEC-02 projectile allocator identity drift")
    if ([row["tick"] for row in weapon_frames] != list(range(50)) or
        [row["tick"] for row in empty_frames] != list(range(18)) or
        weapon_frames[0]["action"] != 0x0c00 or
        any(row["action"] != 0x0c02 for row in weapon_frames[1:49]) or
        weapon_frames[49]["action"] != 0 or
        empty_frames[0]["action"] != 0x1a00 or
        any(row["action"] != 0x1a02 for row in empty_frames[1:17]) or
        empty_frames[17]["action"] != 0 or
        weapon_return_frame != {
            "tick": 50, "action": 2, "substate": 2,
            "animation_record": "0x00163158",
            "assembly": "0x00165488", "hurt_selector": 1,
            "attack_selector": 0}):
        raise ValueError("SPEC-02 Button1 presentation timeline drift")

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
    lines.extend([
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
        "static const AvspRound1PlayerWeaponSpec avsp_round1_player_weapon =",
        "{",
        f"    {int(weapon_states['sufficient_entry_action'], 16)}u,",
        f"    {int(weapon_states['sufficient_active_action'], 16)}u,",
        f"    {int(weapon_states['empty_entry_action'], 16)}u,",
        f"    {int(weapon_states['empty_active_action'], 16)}u,",
        f"    {int(weapon_states['cleanup_action'], 16)}u,",
        f"    {int(weapon_states['return_locomotion_action'], 16)}u,",
        f"    {weapon_volley['attempt_counter_initial']},",
        f"    {weapon_volley['cadence_initial']}u,",
        f"    {weapon_volley['cadence_reload']}u,",
        f"    {weapon_empty['timer_initial']}u,",
        f"    {weapon_volley['resource_capacity']}u,",
        f"    {weapon_volley['resource_debit']}u,",
        f"    {weapon_volley['recharge_countdown_after_success']}u,",
        f"    {weapon_resource['normal_recharge_reload']}u,",
        f"    {weapon_resource['depleted_recharge_reload']}u,",
        "    0x05,",
        "    0x8680u,",
        "    0x0080u,",
        "    0x8380u,",
        "    0x03136aUL",
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in weapon_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du }," % (
                row["action"], row["substate"], row["animation_record"],
                row["assembly"], row["hurt_selector"],
                row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_empty_frames[AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in empty_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du }," % (
                row["action"], row["substate"], row["animation_record"],
                row["assembly"], row["hurt_selector"],
                row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_return_frame =",
        "{",
        "    %du, %du, %sUL, %sUL, %du, %du" % (
            weapon_return_frame["action"], weapon_return_frame["substate"],
            weapon_return_frame["animation_record"],
            weapon_return_frame["assembly"],
            weapon_return_frame["hurt_selector"],
            weapon_return_frame["attack_selector"]),
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_weapon_projectile_spawn_offsets[AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT] =",
        "{",
    ])
    for x, y in projectile_spawn_offsets:
        lines.append(f"    {{ {x}, {y} }},")
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_weapon_projectile_animation_selectors[AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in projectile_animation_selectors),
        "};", "",
        "static const unsigned char avsp_round1_weapon_projectile_angles_facing0[AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in projectile_angles0),
        "};", "",
        "static const unsigned char avsp_round1_weapon_projectile_angles_facing1[AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in projectile_angles1),
        "};", "",
        "static const unsigned char avsp_round1_weapon_projectile_player_selectors[AVSP_ROUND1_WEAPON_PROJECTILE_ANGLE_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in projectile_player_selectors),
        "};", "",
        "static const AvspRound1VecS16 avsp_round1_weapon_projectile_motion[AVSP_ROUND1_WEAPON_PROJECTILE_MOTION_COUNT] =",
        "{",
    ])
    for x, y in projectile_motion:
        lines.append(f"    {{ {x}, {y} }},")
    lines.extend([
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_weapon_projectile_presentations[AVSP_ROUND1_WEAPON_PROJECTILE_PRESENTATION_COUNT][2] =",
        "{",
    ])
    for sequence in projectile_presentations:
        records = [sequence["first"], sequence["terminal"]]
        rendered = []
        for row in records:
            rendered.append("{ %du, %d, %sUL, %sUL, %du, %du }" % (
                row["timer"], row["branch"], row["animation_record"],
                row["assembly"], row["hurt_selector"], row["attack_selector"]))
        lines.append("    { " + ", ".join(rendered) + " },")
    lines.extend([
        "};", "",
        "static const AvspRound1WeaponProjectileSpec avsp_round1_weapon_projectile =",
        "{",
        "    0u, 2u, 4u, 6u, 0x80u,",
        "    0x50, 0x0220u, 0x10, 0x0120u, 0x3a, 0u,",
        "    %du, %du, %su" % (
            projectile_presentation_actor["coordinate_mode_u8"],
            projectile_presentation_actor["palette_u8"],
            projectile_presentation_actor["object_or_u16"]),
        "};", "",
        "static const AvspRound1CollisionBoxSpec avsp_round1_weapon_projectile_hurt_box =",
        "{",
        "    %d, %d, %du, %du, %d, %du, 0, 0u, 0u" % (
            projectile_hurt_boxes[0]["x_center"],
            projectile_hurt_boxes[0]["y_center"],
            projectile_hurt_boxes[0]["x_half"],
            projectile_hurt_boxes[0]["y_half"],
            projectile_hurt_boxes[0]["z_center"],
            projectile_hurt_boxes[0]["z_half"]),
        "};", "",
        "static const AvspRound1CollisionBoxSpec avsp_round1_weapon_projectile_attack_boxes[AVSP_ROUND1_WEAPON_PROJECTILE_ATTACK_BOX_COUNT] =",
        "{",
    ])
    for box in projectile_attack_boxes:
        lines.append("    { %d, %d, %du, %du, %d, %du, %d, %du, %du }," % (
            box["x_center"], box["y_center"], box["x_half"], box["y_half"],
            box["z_center"], box["z_half"], box["knockback_mode"],
            box["hit_value"], box["unknown_bytes"]["0x09"]))
    baseline_damage = weapon_damage["baseline"]
    mutated_damage = weapon_damage["mutation"]
    lines.extend([
        "};", "",
        "static const AvspRound1DamageClassValueSpec avsp_round1_weapon_damage_offense[AVSP_ROUND1_WEAPON_DAMAGE_OFFENSE_COUNT] =",
        "{",
        "    { %du, %du, %du }," % (baseline_damage["attacker_class_index"], baseline_damage["route_index"], baseline_damage["offense"]),
        "    { 2u, %du, %du }" % (baseline_damage["route_index"], mutated_damage["offense"]),
        "};", "",
        "static const AvspRound1DamageClassValueSpec avsp_round1_weapon_damage_defense[AVSP_ROUND1_WEAPON_DAMAGE_DEFENSE_COUNT] =",
        "{",
        "    { %du, %du, %du }" % (baseline_damage["defender_class_index"], baseline_damage["route_index"], baseline_damage["defense"]),
        "};", "",
        "static const AvspRound1DamageMatrixValueSpec avsp_round1_weapon_damage_matrix[AVSP_ROUND1_WEAPON_DAMAGE_MATRIX_COUNT] =",
        "{",
        "    { %du, %du, %du }," % (baseline_damage["defense"], baseline_damage["offense"] + baseline_damage["attack_selector"], baseline_damage["damage"]),
        "    { %du, %du, %du }" % (baseline_damage["defense"], mutated_damage["offense"] + baseline_damage["attack_selector"], mutated_damage["damage"]),
        "};", "",
        "static const AvspRound1WeaponImpactSpec avsp_round1_weapon_impact =",
        "{",
        "    24u, 0x3a, 0u, 0u, 2u, 4u, 0x086f62UL,",
        "    %du, %du, %su," % (
            impact_presentation_actor["coordinate_mode_u8"],
            impact_presentation_actor["palette_u8"],
            impact_presentation_actor["object_or_u16"]),
        "    { " + ", ".join(f"0x{value:04x}u" for value in impact_audio) + " }",
        "};", "",
        "static const short avsp_round1_weapon_impact_variant_offsets[AVSP_ROUND1_WEAPON_IMPACT_VARIANT_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}" for value in impact_offsets),
        "};", "",
        "static const AvspRound1AnimationStateSpec avsp_round1_weapon_impact_variant0_records[AVSP_ROUND1_WEAPON_IMPACT_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in impact_records:
        lines.append("    { %du, %d, %sUL, %sUL, %du, %du }," % (
            row["timer"], row["branch"], row["animation_record"],
            row["assembly"], row["hurt_selector"], row["attack_selector"]))
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
