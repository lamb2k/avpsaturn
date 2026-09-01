#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route writer 0x008bb2 program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_8bb2", ROOT / "tools/build_spec02_route_8bb2_program.py")
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
    baseline = module.build()
    module.validate(baseline)
    mutants = []
    value = copy.deepcopy(baseline); value["source_identity"]["program_window"][0] = "0x008ba2"; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatcher_contract"]["table_bytes"] = "000401b8"; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatcher_contract"]["entries"][1]["target"] = "0x008d60"; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["entry_ordered_writes"][0]["operation"] = "= 2"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["player_selection_loop"]["iterations"] = 2; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["selected_actor_mode_branches"]["bit0_clear_reference_path"]["tile_selectors_u16"] = [0, 0]; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["selected_actor_mode_branches"]["bit0_set_static_path"]["palette_selectors_u16"] = [0, 0]; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["post_load_guard"]["false"] = "return"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["command"] = "0x000f"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["handler_transaction"]["handler_class"] = "UNKNOWN"; mutants.append(value)
    value = copy.deepcopy(baseline); value["load_release_contract"]["boundaries"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["load_release_contract"]["boundaries"][0]["package_identity"]["write_count"] = 8959; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["writes"] = 29; mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["reference_character_branch"]["selected_actor_mode_bit0"] = 1; mutants.append(value)
    value = copy.deepcopy(baseline); value["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["helper_contracts"].pop("0x00a6e2"); mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["invented_rng_call_rejected"] = False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x008bb2 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x008bb2: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
