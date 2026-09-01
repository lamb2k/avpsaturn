#!/usr/bin/env python3
"""Mutation controls for the SPEC-02 route writer 0x0090f2 program."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "route_90f2", ROOT / "tools/build_spec02_route_90f2_program.py")
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
    value = copy.deepcopy(baseline); value["source_identity"]["program_window"][1] = "0x009112"; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatch_contract"]["substate_offsets_s16"][1] = 106; mutants.append(value)
    value = copy.deepcopy(baseline); value["dispatch_contract"]["entry_guards_in_order"][0]["guard"] = "u8(g81bf) != 0"; mutants.append(value)
    value = copy.deepcopy(baseline); value["table_contracts"]["variant_copy_offset_s8"]["bytes_hex"] = "00" + value["table_contracts"]["variant_copy_offset_s8"]["bytes_hex"][2:]; mutants.append(value)
    value = copy.deepcopy(baseline); value["table_contracts"]["palette_group_a_offsets_u16"]["sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["table_contracts"]["grid_records"]["bytes_hex"] = value["table_contracts"]["grid_records"]["bytes_hex"][:-2] + "00"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["mode8_tail"]["writes"][0] = "g8004:u16=4"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["credited_restore"]["ordered_writes"][1] = "g8008:s16=2"; mutants.append(value)
    value = copy.deepcopy(baseline); value["transition_contract"]["credited_restore"]["destination_bases_u16"][4] = 0x91e0; mutants.append(value)
    value = copy.deepcopy(baseline); value["implementation_rules"]["logical_load_on_credited_restore"] = True; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["command"] = "0x0001"; mutants.append(value)
    value = copy.deepcopy(baseline); value["audio_command_contract"]["source_owner_return"] = "0x00913e"; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["instructions_sha256"] = "0" * 64; mutants.append(value)
    value = copy.deepcopy(baseline); value["normalized_source_program"]["external_transfers"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["dynamic_witness"]["counts"]["writes"] = 23; mutants.append(value)
    value = copy.deepcopy(baseline); value["owned_writer_transactions"].pop(); mutants.append(value)
    value = copy.deepcopy(baseline); value["helper_contracts"].pop("0x01705c"); mutants.append(value)
    value = copy.deepcopy(baseline); value["mutation_controls"]["fixed_frame_or_invented_rng_mutation_rejected"] = False; mutants.append(value)
    escaped = [index for index, value in enumerate(mutants, 1)
               if not rejected(value)]
    if escaped:
        raise RuntimeError(f"route-0x0090f2 mutations escaped validation: {escaped}")
    print(f"SPEC-02 route-0x0090f2: PASS ({len(mutants)} mutations rejected)")


if __name__ == "__main__":
    main()
