#!/usr/bin/env python3
"""Focused class-0x4e/type-24 whole-routine fixture and mutations."""
import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "class4e_spec", ROOT / "tools/build_spec02_class4e_type24.py")
assert SPEC and SPEC.loader
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)

value = json.loads(spec.OUT.read_text(encoding="ascii"))
spec.validate(value)
assert value["source_identity"]["entry"] == "0x0927f6"
assert value["normalized_source_program"]["instruction_count"] == 31
assert len(value["reachable_state_substate_contexts"]) == 3
assert sum(row["entry_count"] for row in value["dispatch"].values()) == 4
assert len(value["normalized_source_program"]["field_access_profiles"]) == 8
assert len(value["normalized_source_program"]["external_transfers"]) == 5
assert value["variant_tables"]["entry_count"] == 26
assert len(value["presentation_collision"]["records"]) == 53


def reject(mutant, label):
    try:
        spec.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"class-0x4e mutation escaped: {label}")


mutations = []
m = copy.deepcopy(value); m["status"] = "SOURCE_CLOSED"; mutations.append((m, "status"))
m = copy.deepcopy(value); m["reachable_state_substate_contexts"].pop(); mutations.append((m, "context omission"))
m = copy.deepcopy(value); m["dispatch"]["top_state_byte"]["targets"].pop(); m["dispatch"]["top_state_byte"]["entry_count"] -= 1; mutations.append((m, "dispatch omission"))
m = copy.deepcopy(value); m["normalized_source_program"]["instructions"][0]["operation"] = "nop"; mutations.append((m, "instruction semantics"))
m = copy.deepcopy(value); m["dynamic_witness"]["semantic_sha256"]["rng"] = "0" * 64; mutations.append((m, "RNG chronology"))
m = copy.deepcopy(value); m["normalized_source_program"]["external_transfers"].pop(); mutations.append((m, "external owner"))
m = copy.deepcopy(value); m["variant_tables"]["animation_record_offset_table"]["sha256"] = "0" * 64; mutations.append((m, "animation selector table"))
m = copy.deepcopy(value); m["variant_tables"]["rng_jitter_table"]["values"][3][0] = 5; mutations.append((m, "jitter table"))
m = copy.deepcopy(value); m["state_contract"]["variant10_collision_effect"]["shared_dispatch_reachable_variant_programs"].pop("20"); mutations.append((m, "reachable impact variant"))
m = copy.deepcopy(value); m["presentation_collision"]["records"].pop(); mutations.append((m, "presentation record"))
m = copy.deepcopy(value); m["implementation_rules"]["runtime_68000_interpretation_forbidden"] = False; mutations.append((m, "runtime interpreter"))

for mutant, label in mutations:
    reject(mutant, label)
print(f"SPEC-02 class-0x4e/type-24: PASS ({len(mutations)} mutations rejected)")
