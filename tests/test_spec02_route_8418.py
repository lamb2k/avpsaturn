#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route writer 0x008418 program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_8418", ROOT / "tools/build_spec02_route_8418_program.py")
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
    value = copy.deepcopy(baseline); value["source_identity"]["program_window"][0] = "0x008408"; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["external_transfers"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard"] = "u8(g81f3) == 0"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["guard_true_ordered_writes"][0]["operation"] = "= 6"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["ordered_helper_calls"].reverse(); mutants.append(value)
    value = copy.deepcopy(baseline); value["player_presentation_stage_binding"]["round1_reachable_stage_indices_u16"] = [4]; mutants.append(value)
    value = copy.deepcopy(baseline); value["player_presentation_stage_binding"]["pointer_table"]["bytes_hex"] = "00" * 12; mutants.append(value)
    value = copy.deepcopy(baseline); value["player_presentation_stage_binding"]["stage2_record"]["bytes_hex"] = "00" * 12; mutants.append(value)
    value = copy.deepcopy(baseline); value["player_presentation_stage_binding"]["stage4_record"]["bytes_hex"] = "00" * 12; mutants.append(value)
    value = copy.deepcopy(baseline); value["player_presentation_stage_binding"]["gameplay_authority"] = True; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["direct_writes"] = 9; mutants.append(value)
    value = copy.deepcopy(baseline); value["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["shared_route_setup_contract"]["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["implementation_rules"]["logical_audio_or_load_event"] = True; mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["invented_audio_load_or_rng_rejected"] = False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x008418 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x008418: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
