#!/usr/bin/env python3
"""Focused contract and real mutations for the projectile-audio owner family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "projectile_audio_spec",
    ROOT / "tools/build_spec02_projectile_audio_owner_program.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)

baseline = module.build()
module.validate(baseline)


def rejected(mutator) -> None:
    value = copy.deepcopy(baseline)
    mutator(value)
    try:
        module.validate(value)
    except (AssertionError, KeyError, TypeError, ValueError):
        return
    raise AssertionError("projectile-audio mutation was not rejected")


mutations = [
    lambda x: x["trigger_groups"].pop(),
    lambda x: x["fixed_pool_origins"].pop(),
    lambda x: x["trigger_groups"][0].update(source_owner_families=["enemy"]),
    lambda x: x["trigger_groups"][0].update(command="0x004c"),
    lambda x: x["trigger_groups"][0]["argument_variants"][0].__setitem__(1, "00000000"),
    lambda x: x["trigger_groups"][0]["transition_guard"]["contexts"].pop(),
    lambda x: x["trigger_groups"][0]["transition_guard"]["contexts"][0].update(class_u8="0x05"),
    lambda x: x["trigger_groups"][0]["handler_transaction"].update(table_index="0x004c"),
    lambda x: x["trigger_groups"][0]["handler_transaction"].update(individual_bus_writes_are_logical_events=True),
    lambda x: x["trigger_groups"][0].update(semantic_sound_name="guessed"),
    lambda x: x["normalized_source_program"].update(address="0x01b86e"),
    lambda x: x["normalized_source_program"].update(raw_sha256="0" * 64),
    lambda x: x["normalized_source_program"]["instructions"].pop(),
    lambda x: x["normalized_source_program"]["field_access_profile"]["arithmetic"].pop(),
    lambda x: x["coverage"].update(orphan_groups=1),
    lambda x: x["transition_contract"].update(fixed_frame_authority=True),
    lambda x: x["transition_contract"].update(projectile_audio_owns_projectile_gameplay=True),
    lambda x: x["transition_contract"].update(rng_calls=1),
]
for mutation in mutations:
    rejected(mutation)

module.main = None
print(f"SPEC-02 projectile-audio owner: PASS ({len(mutations)} mutations rejected)")
