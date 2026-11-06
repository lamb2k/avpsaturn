#!/usr/bin/env python3
"""Committed-artifact and mutation controls for ORACLE-09."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle09_street_alien_state_facing_presentation.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle09", ROOT / "tools" / "analyze_oracle09_alien_state.py")
assert SPEC and SPEC.loader
oracle09 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle09)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle09.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-09 negative control: {label}")


report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
oracle09.validate(report)
oracle09.mutation_self_test(report)

facing = copy.deepcopy(report)
facing["bounded_state_contract"]["right_to_left_crossing_0x1a00"] \
    ["same_tick_identity"]["facing"] = 1
reject(facing, "disconnected crossing facing")

assembly = copy.deepcopy(report)
assembly["bounded_state_contract"]["rng_attack_0x1800"] \
    ["first_sample"]["assembly"] = "0x12fa0c"
reject(assembly, "random attack assembly substitution")

target = copy.deepcopy(report)
target["counterfactuals"]["player_left"]["actor"]["facing"] = 0
reject(target, "generic face-target-every-frame rule")

scheduler = copy.deepcopy(report)
scheduler["scheduler_rng_hit_ko"]["scheduler"] \
    ["target_zero_based_pool_index"] = 15
reject(scheduler, "reordered source scheduler")

rendered = copy.deepcopy(report)
rendered["presentation_identity"]["rendered_source_bound_hit_identities"][0] \
    ["source_actor_tick"]["tile_identity_sha256"] = ""
reject(rendered, "vacuous rendered identity")

saturn = copy.deepcopy(report)
saturn["physical_saturn"] = "PASS"
reject(saturn, "unearned physical Saturn claim")

rebuilt = oracle09.build_report()
assert oracle09.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-09 alien state/facing/presentation tests: PASS")
