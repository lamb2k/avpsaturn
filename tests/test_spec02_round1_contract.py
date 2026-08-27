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
assert [len(child["initialization"]["variant_presentation_sequences"][str(i)])
        for i in range(3)] == [17, 10, 16]
damage = weapon["current_state_collision_damage"]
assert damage["parent_contact"]["damage_u8"] == 127
assert damage["child_contact"]["damage_u8"] == 31
assert weapon["empty_effect_variant1_contract"]["spec_executable"] is True
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
initial = class1f["initial_transition_contract"]
assert initial["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS"
assert [row["entry_delay_u8"] for row in initial["actors"][-3:]] == [9, 3, 16]
assert [row["coordinate_mode_u8"] for row in initial["actors"]] == [1] * 10
assert [row["palette_u8"] for row in initial["actors"]] == [16, 17, 17, 18, 17, 16, 18, 17, 19, 19]
assert [row["object_or_u16"] for row in initial["actors"]] == ["0x8000"] * 10
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
dependencies = fixtures["authority_data"]["auxiliary"]["first_segment_dependencies"]
assert dependencies["class_0x09_type20_rng_owner"]["first_segment_calls_before_class4e"] == 44
assert dependencies["class_0x4e_type24_variant4_effect"]["allocation_pop_order"] == [
    "0x00ffc500", "0x00ffc480"]
navigation = fixtures["authority_data"]["navigation"]
assert len(navigation["terrain_resolver"]["records"]) == 6
assert navigation["terrain_resolver"]["implementation_contract"]["handlers"]["6"][
    "selected_entry"] == "0x0b1e9c"
assert navigation["obstacle_response"]["implementation_contract"]["player_geometry"][
    "box"] is None
assert navigation["obstacle_response"]["implementation_contract"]["obstacle_box"][
    "x_half_u8"] == 32
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
assert button3["presentation_records"][-2]["attack_selector_u8"] == 35
assert button3["presentation_actor_fields"]["object_or_u16"] == "0x8000"
assert button3["rng_calls"] == []
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
f = copy.deepcopy(fixtures); next(row for row in next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["presentation_and_collision"]["records"] if row["animation_record"] == "0x0012dd50")["assembly"] = "0x0013020c"; mutations.append((contract, f, "class1f HIT presentation mutation"))
f = copy.deepcopy(fixtures); next(row for row in next(item for item in f["authority_data"]["enemies"]["archetypes"] if item["class"] == "0x1f")["presentation_and_collision"]["records"] if row["animation_record"] == "0x0012e214")["hurt_selector"] = 1; mutations.append((contract, f, "class1f KO selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x09_type20_rng_owner"]["selector_table_u16"][0] = 1; mutations.append((contract, f, "class09 RNG selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["auxiliary"]["first_segment_dependencies"]["class_0x4e_type24_variant4_effect"]["allocation_pop_order"].reverse(); mutations.append((contract, f, "class4e allocation-order mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["terrain_resolver"]["records"][4]["decoded_six_fields"]["z_parameter_s8"] = -8; mutations.append((contract, f, "terrain record sign mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["obstacle_response"]["implementation_contract"]["obstacle_box"]["x_half_u8"] = 16; mutations.append((contract, f, "obstacle box mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["navigation"]["camera"]["implementation_contract"]["coffee_shop_guard"]["phase2_unlock_guard"] = "frame >= 4992"; mutations.append((contract, f, "camera unlock guard mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["vector_table"][2]["x_velocity_s32_16_16"]["raw_s32"] = -0x000e0000; mutations.append((contract, f, "Button3 vector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["input_facing_mapping"][3]["entry_index"] = 2; mutations.append((contract, f, "Button3 facing map mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["initialization"]["non_down"]["opposite_facing_horizontal"]["collision_level_u8"] = 2; mutations.append((contract, f, "Button3 collision selector mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["motion_and_landing"]["phase_0x040a"]["negative_velocity_transition"]["phase_timer_s16"] = 9; mutations.append((contract, f, "Button3 timer mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["rng_calls"] = ["guess"]; mutations.append((contract, f, "Button3 RNG mutation"))
f = copy.deepcopy(fixtures); f["authority_data"]["player"]["directional_airborne_interruption"]["directional_actions"]["implementation_contract"]["presentation_actor_fields"]["object_or_u16"] = "0x0000"; mutations.append((contract, f, "Button3 presentation actor mutation"))
m = copy.deepcopy(contract); m["protected_boundaries"]["physical_saturn"] = "PASS"; mutations.append((m, fixtures, "hardware overclaim"))
m = copy.deepcopy(contract); m["next_card"] = "SALVAGE-08-FRONTEND"; mutations.append((m, fixtures, "frontend bypass"))
for args in mutations:
    reject(*args)
print(f"SPEC-02 Round 1 executable contract: PASS ({len(mutations)} mutations rejected)")
