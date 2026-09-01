#!/usr/bin/env python3
"""Focused class-0x3d/type-24 whole-routine fixture and mutations."""
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "class3d_spec", ROOT / "tools/build_spec02_class3d_type24.py")
assert SPEC and SPEC.loader
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)

value = json.loads(spec.OUT.read_text(encoding="ascii"))
spec.validate(value)
assert value["source_identity"]["entry"] == "0x0887c8"
assert value["normalized_source_program"]["instruction_count"] == 34
assert len(value["reachable_state_substate_contexts"]) == 3
assert sum(row["entry_count"] for row in value["dispatch"].values()) == 4
assert len(value["normalized_source_program"]["field_access_profiles"]) == 11
assert len(value["normalized_source_program"]["external_transfers"]) == 4
assert value["movement_table"]["entry_count"] == 16


def reject(mutant, label):
    try:
        spec.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"class-0x3d mutation escaped: {label}")


mutations = []
m = copy.deepcopy(value); m["status"] = "SOURCE_CLOSED"; mutations.append((m, "status"))
m = copy.deepcopy(value); m["reachable_state_substate_contexts"].pop(); mutations.append((m, "context omission"))
m = copy.deepcopy(value); m["dispatch"]["top_state_high_byte"]["targets"].pop(); m["dispatch"]["top_state_high_byte"]["entry_count"] -= 1; mutations.append((m, "dispatch omission"))
m = copy.deepcopy(value); m["normalized_source_program"]["instructions"][0]["operation"] = "nop"; mutations.append((m, "instruction semantics"))
m = copy.deepcopy(value); m["dynamic_witness"]["semantic_sha256"]["writes"] = "0" * 64; mutations.append((m, "write chronology"))
m = copy.deepcopy(value); m["normalized_source_program"]["field_access_profiles"].pop(next(iter(m["normalized_source_program"]["field_access_profiles"]))); mutations.append((m, "read-write profile"))
m = copy.deepcopy(value); m["normalized_source_program"]["external_transfers"].pop(); mutations.append((m, "external owner"))
m = copy.deepcopy(value); m["movement_table"]["values"][0][0] = -60; mutations.append((m, "movement table"))
m = copy.deepcopy(value); m["implementation_rules"]["runtime_68000_interpretation_forbidden"] = False; mutations.append((m, "runtime interpreter"))

for mutant, label in mutations:
    reject(mutant, label)
print(f"SPEC-02 class-0x3d/type-24: PASS ({len(mutations)} mutations rejected)")
