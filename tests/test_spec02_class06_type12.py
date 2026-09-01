#!/usr/bin/env python3
"""Focused class-0x06/type-12 whole-routine fixture and mutations."""
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "class06_spec", ROOT / "tools/build_spec02_class06_type12.py")
assert SPEC and SPEC.loader
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)

value = json.loads(spec.OUT.read_text(encoding="ascii"))
spec.validate(value)
assert value["source_identity"]["entry"] == "0x04956c"
assert value["normalized_source_program"]["instruction_count"] == 1788
assert len(value["reachable_state_substate_contexts"]) == 40
assert len(value["dispatch"]) == 29
assert sum(row["entry_count"] for row in value["dispatch"].values()) == 137
assert value["dispatch"]["action18_phase_with_unreachable_zero"]["unreachable_entry_0"] == "0xffff"
assert len(value["normalized_source_program"]["field_access_profiles"]) == 92
assert len(value["normalized_source_program"]["external_transfers"]) == 29


def reject(mutant, label):
    try:
        spec.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"class-0x06 mutation escaped: {label}")


mutations = []
m = copy.deepcopy(value); m["status"] = "SOURCE_CLOSED"; mutations.append((m, "status"))
m = copy.deepcopy(value); m["reachable_state_substate_contexts"].pop(); mutations.append((m, "context omission"))
m = copy.deepcopy(value); m["dispatch"].pop("action18_phase_with_unreachable_zero"); mutations.append((m, "dispatch omission"))
m = copy.deepcopy(value); m["normalized_source_program"]["instructions"][0]["operation"] = "nop"; mutations.append((m, "instruction semantics"))
m = copy.deepcopy(value); m["dynamic_witness"]["semantic_sha256"]["rng"] = "0" * 64; mutations.append((m, "RNG order"))
m = copy.deepcopy(value); m["normalized_source_program"]["field_access_profiles"].pop(next(iter(m["normalized_source_program"]["field_access_profiles"]))); mutations.append((m, "read-write profile"))
m = copy.deepcopy(value); m["normalized_source_program"]["external_transfers"].pop(); mutations.append((m, "external owner"))
m = copy.deepcopy(value); m["mutation_controls"]["unreachable_sentinel_execution_rejected"] = False; mutations.append((m, "sentinel execution"))
m = copy.deepcopy(value); m["implementation_rules"]["runtime_68000_interpretation_forbidden"] = False; mutations.append((m, "runtime interpreter"))

for mutant, label in mutations:
    reject(mutant, label)
print(f"SPEC-02 class-0x06/type-12: PASS ({len(mutations)} mutations rejected)")
