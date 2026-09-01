#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route writer 0x00c200 program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_c200", ROOT / "tools/build_spec02_route_c200_program.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def rejected(value: dict[str, object]) -> bool:
    try:
        module.validate(value)
    except ValueError:
        return True
    return False


def main() -> None:
    baseline = module.build(); module.validate(baseline)
    mutants = []
    value = copy.deepcopy(baseline); value["transition_contract"]["guard"] = "u8(g8236) == 0"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][0]["operation"] = "= 4"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][2]["pc"] = "0x00c20c"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["ordered_helper_calls"].reverse(); mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["tail_target"] = "0x00843a"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["rng_calls"] = 1; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["writes"] = 5; mutants.append(value)
    value = copy.deepcopy(baseline); value["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["helper_contracts"].pop("0x00c784"); mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["fixed_frame_transition_rejected"] = False if "fixed_frame_transition_rejected" in value["mutation_controls"] else False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x00c200 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x00c200: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
