#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route writer 0x0083d4 program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_83d4", ROOT / "tools/build_spec02_route_83d4_program.py")
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
    baseline = module.build(); module.validate(baseline); mutants = []
    value = copy.deepcopy(baseline); value["source_identity"]["program_window"][0] = "0x0083c4"; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["external_transfers"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard"] = "s16(g837c) != 0"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][0]["field"] = "g800c:u16"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][0]["operation"] = "= 2"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["ordered_calls"].reverse(); mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["tail_target"] = "0x0083fc"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["command"] = "0xff01"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["argument_variant"][0] = "0000ff01"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["dispatch_frames_u16"] = [5563]; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["fixed_pool_reset_writes"] = 219; mutants.append(value)
    value = copy.deepcopy(baseline); value["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["load_release_contract"]["logical_event_owned"] = True; mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["invented_load_release_or_rng_rejected"] = False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x0083d4 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x0083d4: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
