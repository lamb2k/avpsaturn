#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route writer 0x008546 program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_8546", ROOT / "tools/build_spec02_route_8546_program.py")
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
    value = copy.deepcopy(baseline); value["source_identity"]["program_window"][0] = "0x008536"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard"] = "u8(g81af)==0 && u8(g81d4)==0"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][0]["operation"] = "= 4"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][2]["pc"] = "0x00854e"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["ordered_helper_calls"] = []; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["rng_calls"] = 1; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["arguments"]["d1"] = "0x0000ff01"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["handler_transaction"]["handler_class"] = "UNKNOWN"; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["writes"] = 9; mutants.append(value)
    value = copy.deepcopy(baseline); value["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["fixed_frame_transition_rejected"] = False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x008546 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x008546: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
