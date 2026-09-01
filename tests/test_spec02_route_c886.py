#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route-reset dispatcher program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_c886", ROOT / "tools/build_spec02_route_c886_program.py")
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
    value = copy.deepcopy(baseline); value["source_identity"]["dispatcher_window"]["sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["source_identity"]["table_window"]["sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["external_transfers"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatcher_contract"]["guard"] = "u8(g81af) != u8(g823d)"; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatcher_contract"]["table_offsets_s16"][2] = 38; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatcher_contract"]["round1_reachable"]["4"] = "0x00c83c"; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatcher_contract"]["other_targets"] = "SOURCE_CLOSED"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["round_index_2"]["entry"] = "0x00c880"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["round_index_2"]["ordered_writes"][-1] = "g8222:u16=1"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["round_index_4"]["ordered_writes"][-2] = "g81e8:u16=6"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["rng_calls"] = 1; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["command"] = "0xffff"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["argument_variant"][0] = "0000ff07"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["semantic_sound_name"] = "invented"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["score_or_gameplay_coupling"] = True; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["total_owned_writes"] = 30; mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["invented_rng_or_fixed_frame_rejected"] = False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x00c886 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x00c886: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
