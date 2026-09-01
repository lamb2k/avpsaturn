#!/usr/bin/env python3
"""Real mutation controls for the SPEC-02 boss-audio owner family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "boss_audio", ROOT / "tools/build_spec02_boss_audio_owner_program.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
baseline = module.build()
module.validate(baseline)

mutants = []
for mutate in (
    lambda x: x["trigger_groups"].pop(),
    lambda x: x["source_origin_records"].pop(),
    lambda x: x["trigger_groups"][0]["transition_guard"]["contexts"][0].update({"owner_family": "enemy"}),
    lambda x: x["record_type_class_pairs"][0].update({"class_u8": "0x05"}),
    lambda x: x["trigger_groups"][0]["transition_guard"]["contexts"][0].update({"state_u16": 0}),
    lambda x: x["normalized_source_programs"][0].update({"address": "0x000000"}),
    lambda x: x["normalized_source_programs"][0]["instructions"][0].update({"mnemonic": "nop"}),
    lambda x: x["normalized_source_programs"][2]["field_access_profile"].update({"guard": "signed guess"}),
    lambda x: x["trigger_groups"][0].update({"command": "0xffff"}),
    lambda x: x["trigger_groups"][0]["argument_variants"][0].__setitem__(0, "ffffffff"),
    lambda x: x["trigger_groups"][0].update({"shared_wrapper_return": "0x000000"}),
    lambda x: x["trigger_groups"][0]["handler_transaction"].update({"table_index": "0xffff"}),
    lambda x: x["handler_boundary"].update({"individual_qsound_writes_are_logical_events": True}),
    lambda x: x["trigger_groups"][0]["handler_transaction"]["causal_control"].pop("downstream_difference"),
    lambda x: x["transition_contract"].update({"boss_audio_owns_boss_gameplay": True}),
    lambda x: x["handler_boundary"].update({"semantic_sound_names": "invented"}),
    lambda x: x["transition_contract"].update({"rng_calls": 1}),
    lambda x: x["transition_contract"].update({"fixed_frame_authority": True}),
    lambda x: x["implementation_rules"].update({"runtime_68000_interpretation_forbidden": False}),
):
    item = copy.deepcopy(baseline)
    mutate(item)
    mutants.append(item)

for mutant in mutants:
    try:
        module.validate(mutant)
    except ValueError:
        continue
    raise AssertionError("boss-audio mutation was accepted")

print(f"SPEC-02 boss-audio owner: PASS ({len(mutants)} mutations rejected)")
