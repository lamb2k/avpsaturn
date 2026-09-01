#!/usr/bin/env python3
"""Focused class-0x00/type-12 whole-routine fixture and mutations."""
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "class00_spec", ROOT / "tools/build_spec02_class00_type12.py")
assert SPEC and SPEC.loader
class00_spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(class00_spec)

value = json.loads(class00_spec.OUT.read_text(encoding="ascii"))
class00_spec.validate(value)
assert value["source_identity"]["entry"] == "0x03f09c"
assert value["normalized_source_program"]["instruction_count"] == 904
assert len(value["reachable_state_substate_contexts"]) == 39
assert len(value["dispatch"]["active_action_high_byte"]) == 17
assert len(value["dispatch"]["action_substate_low_byte"]) == 8
assert value["dynamic_witness"]["counts"] == {
    "entries": 5821, "samples": 6397, "writes": 40876,
    "rng_calls": 194, "player_damage_writes": 2}
assert value["implementation_rules"]["runtime_68000_interpretation_forbidden"]


def reject(mutant, label):
    try:
        class00_spec.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"class-0x00 mutation escaped: {label}")


mutations = []
m = copy.deepcopy(value); m["status"] = "SOURCE_CLOSED"; mutations.append((m, "status"))
m = copy.deepcopy(value); m["reachable_state_substate_contexts"].pop(); mutations.append((m, "context omission"))
m = copy.deepcopy(value); m["dispatch"]["active_action_high_byte"]["0x10"] = "0x03f8e8"; mutations.append((m, "action dispatch"))
m = copy.deepcopy(value); m["normalized_source_program"]["instructions"][0]["operand_width"] = "u8"; mutations.append((m, "instruction width"))
m = copy.deepcopy(value); m["dynamic_witness"]["semantic_sha256"]["rng"] = "0" * 64; mutations.append((m, "RNG order"))
m = copy.deepcopy(value); m["field_types"]["actor+0x10"] = "world_x_u16"; mutations.append((m, "signed world X"))
m = copy.deepcopy(value); m["scheduler_contract"]["post_dispatch_world_x_clamp"]["maximum_s16"] = "camera_x+0x0200"; mutations.append((m, "world X clamp"))
m = copy.deepcopy(value); m["mutation_controls"]["fixed_frame_transition_rejected"] = False; mutations.append((m, "fixed-frame transition"))
m = copy.deepcopy(value); m["implementation_rules"]["runtime_68000_interpretation_forbidden"] = False; mutations.append((m, "runtime interpreter"))

for mutant, label in mutations:
    reject(mutant, label)
print(f"SPEC-02 class-0x00/type-12: PASS ({len(mutations)} mutations rejected)")
