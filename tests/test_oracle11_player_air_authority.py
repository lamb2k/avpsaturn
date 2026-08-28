#!/usr/bin/env python3
"""ORACLE-11 Predator Warrior air authority mutation controls."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_air_authority.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_air", ROOT / "tools" /
    "analyze_oracle11_player_air_authority.py")
assert SPEC and SPEC.loader
oracle11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle11)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle11.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-11 air mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle11.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "air family downgraded")

mutant = copy.deepcopy(report)
mutant["coverage_universe"]["required_route_phases"].remove("0x0406")
reject(mutant, "route-reachable Button1 air phase omitted")

mutant = copy.deepcopy(report)
mutant["coverage_universe"]["required_counterfactual_phases"].remove("0x0410")
reject(mutant, "midair Down+Button2 phase omitted")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["writer"] = "0x02385e"
reject(mutant, "wrong airborne Button1 writer")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"]["class_u8"] = 0
reject(mutant, "airborne Button1 class-3 actor replaced")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"][
    "player_phase_0x0406"]["presentation_records"][4]["branch_s16"] = -32768
reject(mutant, "airborne Button1 terminal animation branch guessed")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"]["active_state"][
    "substate_2"]["reload_u8"] = 3
reject(mutant, "airborne Button1 direction timer guessed")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"]["active_state"][
    "low_nibble_motion_tables_s16"]["1"] = \
        mutant["airborne_actions"]["button1"]["record4_class03"][
            "active_state"]["low_nibble_motion_tables_s16"]["1"][:16]
reject(mutant, "airborne Button1 motion table truncated to one quadrant")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"]["active_state"][
    "high_nibble_motion_tables_s16"]["12"][63][1] += 1
reject(mutant, "airborne Button1 direction-63 motion vector guessed")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"]["effect_allocation"][
    "audio_command"] = "0x0008"
reject(mutant, "record36 effect helper mislabeled as audio")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["record4_class03"]["effect_allocation"][
    "record_type_u8"] = 36
reject(mutant, "class-3 trail effect assigned to wrong fixed pool")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["rng_consumption"] = "one selector call"
reject(mutant, "air action RNG introduced")

mutant = copy.deepcopy(report)
mutant["counterfactuals"]["air_button2_hold_no_auto_repeat"] = False
reject(mutant, "held Button2 auto-repeat admitted")

mutant = copy.deepcopy(report)
mutant["counterfactuals"]["natural_hit_cancels_directional_air"] = False
reject(mutant, "air interruption omitted")

mutant = copy.deepcopy(report)
del mutant["not_required_for_round1"]["phases"]["0x0414"]
reject(mutant, "unreachable table body silently omitted")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["yaba_run"] = True
reject(mutant, "Yaba workflow violation")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["vector_table"][2][
    "x_velocity_s32_16_16"]["raw_s32"] = -0x000e0000
reject(mutant, "directional vector magnitude guessed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["vector_table"][4][
    "x_acceleration_s32_16_16"]["raw_s32"] = 0x00002000
reject(mutant, "directional vector sign inverted")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["input_facing_mapping"][3][
    "entry_index"] = 2
reject(mutant, "facing-relative table mapping collapsed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["branch_order"][0:2] = [
    "horizontal bits", "down bit"]
reject(mutant, "Button3 branch order changed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["initialization"][
    "non_down"]["opposite_facing_horizontal"]["collision_level_u8"] = 2
reject(mutant, "air collision selector guessed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["initialization"][
    "down"]["presentation_horizontal_u8"] = 60
reject(mutant, "Down+horizontal presentation collapsed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["motion_and_landing"][
    "landing_0x023630"]["presentation_selector_u8"] = 9
reject(mutant, "landing presentation selector changed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["motion_and_landing"][
    "phase_0x040a"]["negative_velocity_transition"]["phase_timer_s16"] = 9
reject(mutant, "Down+Button3 recovery timer changed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"][
    "presentation_selector_sequences"]["60"][0][
    "attack_selector_u8"] = 0
reject(mutant, "Down attack selector removed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"][
    "presentation_selector_sequences"]["6"][0]["record"] = "0x15f344"
reject(mutant, "facing-1 same-direction presentation collapsed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"][
    "presentation_selector_sequences"]["41"][1]["attack_selector_u8"] = 22
reject(mutant, "Down+horizontal presentation attack selector collapsed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"][
    "presentation_actor_fields"]["object_or_u16"] = "0x0000"
reject(mutant, "Button3 presentation actor priority removed")

mutant = copy.deepcopy(report)
mutant["directional_actions"]["implementation_contract"]["rng_calls"] = [
    "plausible presentation selection"]
reject(mutant, "Button3 RNG invented")

rebuilt = oracle11.build_report()
assert oracle11.canonical(rebuilt) == ARTIFACT.read_bytes(), \
    "derived air authority report drift"
print("ORACLE-11 player air authority tests: PASS (25 mutations rejected)")
