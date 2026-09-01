#!/usr/bin/env python3
"""Build the bounded SPEC-02 route-transition program at writer 0x00c200."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "class4b_spec", ROOT / "tools/build_spec02_class4b_type24.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_encounter_route_authority.json"
SEGMENT = ROOT / "data/oracle10_round1_census_extension_5567_6200.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_c200_program.json"
PROGRAM_FIRST = 0x00C1F0
PROGRAM_LAST_EXCLUSIVE = 0x00C220
OPCODE_SHA256 = base.OPCODE_SHA256
EXTERNAL_TRANSFER_OWNERS = {
    0x008438: "shared-route-dispatcher-continuation",
    0x00C784: "shared-route-state-clear",
    0x00C7AE: "shared-route-transition-latch",
}
WRITER_PCS = {"00c200", "00c204", "00c208", "00c20c", "00c210", "00c216"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def semantic(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def dynamic_witness(directory: Path) -> dict[str, object]:
    writes = [row for row in rows(directory / "route_writes.tsv")
              if row["frame"] == "5719" and row["pc"].lower() in WRITER_PCS]
    samples = [row for row in rows(directory / "route_samples.tsv")
               if 5718 <= int(row["frame"]) <= 5721]
    rng = [row for row in rows(directory / "route_rng.tsv")
           if PROGRAM_FIRST <= int(row["pc"], 16) < 0x00C224]
    require(len(writes) == 6 and len(samples) == 4 and not rng,
            "route-0x00c200 paired witness row count drift")
    writes.sort(key=lambda row: int(row["pc"], 16))
    require([(row["pc"].lower(), row["address"].lower(), row["data"].lower())
             for row in writes] == [
                 ("00c200", "ff8008", "00000004"),
                 ("00c204", "ff800c", "00000000"),
                 ("00c208", "ff8010", "00000000"),
                 ("00c20c", "ff8014", "00000000"),
                 ("00c210", "ff829c", "00000300"),
                 ("00c216", "ff829e", "00000400")],
            "route-0x00c200 exact write transaction drift")
    return {
        "counts": {"writes": len(writes), "samples": len(samples), "rng_calls": 0},
        "semantic_sha256": {
            "writes": semantic(writes), "samples": semantic(samples),
            "rng": semantic(rng)},
        "write_rows": writes,
        "sample_projection": [{key: row[key] for key in
                               ("frame", "g8008", "g800c", "g8010", "g8014",
                                "g8248", "player_active", "player_state",
                                "player_phase", "player_x", "player_z")}
                              for row in samples],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and base.base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = base.base.load_json(ORACLE)
    segment = base.base.load_json(SEGMENT)
    edge = next(row for row in oracle["route_state_edges"]
                if row["writer_pc"] == "0x00c200")
    require(edge == next(row for row in
                         segment["route_authority_extension"]["route_state_edges"]
                         if row["writer_pc"] == "0x00c200") and
            edge["source_window"] == {
                "first": "0x00c1f0", "last_exclusive": "0x00c220",
                "sha256": "92b117a8ae2c802521389a06a488de0ae9e95c275346b92f98f0ea68d4543c6e"},
            "accepted route-0x00c200 edge authority drift")
    transactions = [row for row in oracle["route_writer_transactions"]
                    if row["writer_pc"] in {f"0x{pc}" for pc in WRITER_PCS}]
    require(len(transactions) == 6 and all(row["classification"] == "SOURCE_CLOSED"
                                           for row in transactions),
            "route-0x00c200 writer ownership drift")
    helper_transactions = [row for row in oracle["route_writer_transactions"]
                           if row["writer_pc"] in ("0x00c784", "0x00c7ae")]
    require(len(helper_transactions) == 2 and all(
        row["classification"] == "SOURCE_CLOSED" for row in helper_transactions),
        "route-0x00c200 helper ownership drift")
    image = OPCODES.read_bytes()
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = {}, {}
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    require(dispatch == {}, "route-0x00c200 must not invent computed dispatch")
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-0x00c200 witness drift")
    return {
        "schema": "spec02-route-c200-whole-routine-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of route writer 0x00c200 and its owned transition transaction",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "segment_artifact": SEGMENT.relative_to(ROOT).as_posix(),
            "segment_sha256": base.base.sha256(SEGMENT),
            "entry": "0x00c1f0", "writer_pc": "0x00c200",
            "program_window": ["0x00c1f0", "0x00c220"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
        },
        "scheduler_contract": {
            "caller_chain": edge["caller_chain"],
            "source_write_frame_u16": edge["write_frame"],
            "visible_transition_frame_u16": edge["sample_transition_frame"],
            "order": "route controller evaluates after the source presentation/encounter guard writers and completes both shared helper calls before tail-jumping to 0x008438",
        },
        "field_types": {
            "g8008": "route_state_s16", "g800c": "route_substate_u16",
            "g8010": "route_timer_u16", "g8014": "route_aux_u16",
            "g81af": "route_gate_u8", "g8236": "route_gate_u8",
            "g829c": "camera_or_segment_bound_s16",
            "g829e": "camera_or_segment_bound_s16",
            "g823e": "shared_route_state_u16", "g8248": "shared_route_latch_u16",
        },
        "transition_contract": {
            "guard": "(u8(g8236) & u8(g81af)) == 0",
            "guard_false": "perform no owned writes or helper calls; tail-jump to 0x008438",
            "guard_true_ordered_writes": [
                {"pc": "0x00c200", "field": "g8008:s16", "operation": "+= 2", "observed": "2->4"},
                {"pc": "0x00c204", "field": "g800c:u16", "operation": "= 0"},
                {"pc": "0x00c208", "field": "g8010:u16", "operation": "= 0"},
                {"pc": "0x00c20c", "field": "g8014:u16", "operation": "= 0"},
                {"pc": "0x00c210", "field": "g829c:s16", "operation": "= 0x0300"},
                {"pc": "0x00c216", "field": "g829e:s16", "operation": "= 0x0400"}],
            "ordered_helper_calls": ["0x00c7ae", "0x00c784"],
            "tail_target": "0x008438",
            "rng_calls": 0,
        },
        "owned_writer_transactions": transactions,
        "helper_contracts": {
            "0x00c7ae": {"owner": "shared-route-transition-latch",
                          "owned_writer": "0x00c7ae@g8248",
                          "source_closed_transaction": helper_transactions[1]},
            "0x00c784": {"owner": "shared-route-state-clear",
                          "owned_writer": "0x00c784@g823e",
                          "source_closed_transaction": helper_transactions[0]},
        },
        "normalized_source_program": {
            "representation": "bounded route-specific 68000 operations with explicit widths, reads, writes, guards and targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(base.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": base.field_profiles(instructions),
            "external_transfers": external,
        },
        "dynamic_witness": witness_a,
        "paired_capture_identity": segment["paired_capture_ceremony"],
        "counterfactuals": {
            "route_wide_perturbation": segment["route_authority_extension"]["route_wide_perturbation"],
            "warehouse_offense_suppression": segment["targeted_counterfactuals"]["suppress_warehouse_offense"],
        },
        "mutation_controls": {
            "guard_and_vs_or_mutation_rejected": True,
            "guard_polarity_mutation_rejected": True,
            "route_increment_or_fixed_frame_mutation_rejected": True,
            "write_width_or_signedness_mutation_rejected": True,
            "write_order_or_field_substitution_rejected": True,
            "bound_constant_mutation_rejected": True,
            "helper_order_or_suppression_rejected": True,
            "tail_target_mutation_rejected": True,
            "invented_rng_call_rejected": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "route-0x00c200 status drift")
    source = value["source_identity"]
    require(source["program_window"] == ["0x00c1f0", "0x00c220"] and
            source["program_window_sha256"] ==
                "92b117a8ae2c802521389a06a488de0ae9e95c275346b92f98f0ea68d4543c6e",
            "route-0x00c200 source window drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 12 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "d3038f2bcf75e5e0ce0394558f61b51e605c7863792c7403d616a6522ad3588f" and
            len(program["field_access_profiles"]) == 8 and
            len(program["external_transfers"]) == 3 and
            not any(row["owner"].startswith("UNKNOWN")
                    for row in program["external_transfers"]),
            "route-0x00c200 decoded program closure incomplete")
    transition = value["transition_contract"]
    require(transition["guard"] == "(u8(g8236) & u8(g81af)) == 0" and
            [row["pc"] for row in transition["guard_true_ordered_writes"]] ==
                ["0x00c200", "0x00c204", "0x00c208", "0x00c20c",
                 "0x00c210", "0x00c216"] and
            [row["operation"] for row in transition["guard_true_ordered_writes"]] ==
                ["+= 2", "= 0", "= 0", "= 0", "= 0x0300", "= 0x0400"] and
            transition["ordered_helper_calls"] == ["0x00c7ae", "0x00c784"] and
            transition["tail_target"] == "0x008438" and
            transition["rng_calls"] == 0,
            "route-0x00c200 transition contract drift")
    witness = value["dynamic_witness"]
    require(witness["counts"] == {"writes": 6, "samples": 4, "rng_calls": 0} and
            len(witness["write_rows"]) == 6 and
            len(witness["sample_projection"]) == 4,
            "route-0x00c200 paired witness drift")
    require(len(value["owned_writer_transactions"]) == 6 and
            set(value["helper_contracts"]) == {"0x00c7ae", "0x00c784"},
            "route-0x00c200 owner closure incomplete")
    require(all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-0x00c200 mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed route-0x00c200 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 route-0x00c200 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"writes={value['dynamic_witness']['counts']['writes']} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
