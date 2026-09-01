#!/usr/bin/env python3
"""Focused class-0x01/type-12 whole-routine fixture and mutations."""
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "class01_spec", ROOT / "tools/build_spec02_class01_type12.py")
assert SPEC and SPEC.loader
class01_spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(class01_spec)

value = json.loads(class01_spec.OUT.read_text(encoding="ascii"))
class01_spec.validate(value)
assert value["source_identity"]["entry"] == "0x0407b0"
assert value["normalized_source_program"]["instruction_count"] == 1620
assert len(value["reachable_state_substate_contexts"]) == 32
assert len(value["dispatch"]) == 25
assert sum(row["entry_count"] for row in value["dispatch"].values()) == 119
assert value["dynamic_witness"]["counts"] == {
    "entries": 3304, "samples": 3796, "writes": 30904,
    "rng_calls": 131, "player_damage_writes": 1}
assert len(value["normalized_source_program"]["field_access_profiles"]) == 69
assert value["implementation_rules"]["runtime_68000_interpretation_forbidden"]


def reject(mutant, label):
    try:
        class01_spec.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"class-0x01 mutation escaped: {label}")


mutations = []
m = copy.deepcopy(value); m["status"] = "SOURCE_CLOSED"; mutations.append((m, "status"))
m = copy.deepcopy(value); m["reachable_state_substate_contexts"].pop(); mutations.append((m, "context omission"))
m = copy.deepcopy(value); m["dispatch"]["active_action_high_byte"]["targets"][4] = "0x040d10"; mutations.append((m, "action dispatch"))
m = copy.deepcopy(value); m["normalized_source_program"]["instructions"][0]["operation"] = "nop"; mutations.append((m, "instruction semantics"))
m = copy.deepcopy(value); m["dynamic_witness"]["semantic_sha256"]["rng"] = "0" * 64; mutations.append((m, "RNG order"))
m = copy.deepcopy(value); m["field_types"]["actor+0x10"] = "world_x_u16"; mutations.append((m, "signed world X"))
m = copy.deepcopy(value); m["normalized_source_program"]["field_access_profiles"].pop(next(iter(m["normalized_source_program"]["field_access_profiles"]))); mutations.append((m, "read-write field"))
m = copy.deepcopy(value); m["mutation_controls"]["fixed_frame_transition_rejected"] = False; mutations.append((m, "fixed-frame transition"))
m = copy.deepcopy(value); m["implementation_rules"]["runtime_68000_interpretation_forbidden"] = False; mutations.append((m, "runtime interpreter"))

for mutant, label in mutations:
    reject(mutant, label)
print(f"SPEC-02 class-0x01/type-12: PASS ({len(mutations)} mutations rejected)")
