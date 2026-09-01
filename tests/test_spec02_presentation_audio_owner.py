#!/usr/bin/env python3
"""Focused contract and real mutations for the presentation-audio owner family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "presentation_audio_spec",
    ROOT / "tools/build_spec02_presentation_audio_owner_program.py")
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
    raise AssertionError("presentation-audio mutation was not rejected")


mutations = [
    lambda x: x["trigger_groups"].pop(),
    lambda x: x["trigger_groups"][0].update(source_owner_families=["route"]),
    lambda x: x["trigger_groups"][0].update(command="0x0035"),
    lambda x: x["trigger_groups"][0]["argument_variants"][0].__setitem__(1, "00000000"),
    lambda x: x["trigger_groups"][0]["transition_guard"]["contexts"].pop(),
    lambda x: x["trigger_groups"][0]["handler_transaction"].update(table_index="0x0035"),
    lambda x: x["trigger_groups"][0]["handler_transaction"].update(individual_bus_writes_are_logical_events=True),
    lambda x: x["trigger_groups"][0].update(semantic_sound_name="guessed"),
    lambda x: x["normalized_source_programs"].pop(),
    lambda x: x["normalized_source_programs"][0].update(address="0x001740"),
    lambda x: x["normalized_source_programs"][0].update(raw_sha256="0" * 64),
    lambda x: x["normalized_source_programs"][0]["instructions"].pop(),
    lambda x: x["coverage"].update(orphan_groups=1),
    lambda x: x["transition_contract"].update(fixed_frame_authority=True),
    lambda x: x["transition_contract"].update(presentation_owns_gameplay_result=True),
    lambda x: x["transition_contract"].update(rng_calls=1),
]
for mutation in mutations:
    rejected(mutation)

module.main = None
print(f"SPEC-02 presentation-audio owner: PASS ({len(mutations)} mutations rejected)")
