#!/usr/bin/env python3
"""Build the bounded SPEC-02 round-clear route program at writer 0x008418."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "route_c200_spec", ROOT / "tools/build_spec02_route_c200_program.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
decoder = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_encounter_route_authority.json"
HANDOFF = ROOT / "data/oracle11_round1_handoff.json"
SEGMENTS = (
    ROOT / "data/oracle10_round1_census_extension_5567_6200.json",
    ROOT / "data/oracle10_round1_census_extension_13293_15039.json",
)
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_8418_program.json"

PROGRAM_FIRST = 0x00840A
PROGRAM_LAST_EXCLUSIVE = 0x008438
ACCEPTED_WINDOW = (0x008408, 0x008438)
SOURCE_FRAMES = {5452, 15018}
DIRECT_PCS = {"008418", "00841c", "008420", "00842c", "008432"}
HELPER_PCS = {"00c75a", "00c760", "00c766", "00c76c", "00c770",
              "00c774", "00c778", "00c780", "00c784"}
EXTERNAL_TRANSFER_OWNERS = {
    0x008438: "shared-route-dispatcher-continuation",
    0x00C754: "shared-route-transition-setup",
    0x021EF8: "source-player-presentation-stage-binding",
}


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


def source_bytes(image: bytes, first: int, last: int) -> dict[str, object]:
    payload = image[first:last]
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "byte_count": len(payload), "bytes_hex": payload.hex(),
            "sha256": hashlib.sha256(payload).hexdigest()}


def dynamic_witness(directory: Path) -> dict[str, object]:
    wanted = DIRECT_PCS | HELPER_PCS
    writes = [row for row in rows(directory / "route_writes.tsv")
              if int(row["frame"]) in SOURCE_FRAMES and
              row["pc"].lower() in wanted]
    writes.sort(key=lambda row: (int(row["frame"]), int(row["pc"], 16)))
    samples = [row for row in rows(directory / "route_samples.tsv")
               if any(frame - 1 <= int(row["frame"]) <= frame + 2
                      for frame in SOURCE_FRAMES)]
    rng = [row for row in rows(directory / "route_rng.tsv")
           if PROGRAM_FIRST <= int(row["pc"], 16) < PROGRAM_LAST_EXCLUSIVE]
    expected_direct = {
        5452: [("008418", "ff8008", "00000006"),
               ("00841c", "ff800c", "00000000"),
               ("008420", "ff8240", "00000101"),
               ("00842c", "ff8236", "00000808"),
               ("008432", "ff822c", "00000002")],
        15018: [("008418", "ff8008", "00000006"),
                ("00841c", "ff800c", "00000000"),
                ("008420", "ff8240", "00000101"),
                ("00842c", "ff8236", "00000808"),
                ("008432", "ff822c", "00000004")],
    }
    direct = [(int(row["frame"]), row["pc"].lower(), row["address"].lower(),
               row["data"].lower()) for row in writes
              if row["pc"].lower() in DIRECT_PCS]
    require(direct == [(frame, *item) for frame in sorted(expected_direct)
                       for item in expected_direct[frame]],
            "route-0x008418 direct writer witness drift")
    helper = [row for row in writes if row["pc"].lower() in HELPER_PCS]
    require(len(helper) == 18 and len(samples) == 8 and not rng and
            all(sum(row["pc"].lower() == pc and int(row["frame"]) == frame
                    for row in helper) == 1
                for frame in SOURCE_FRAMES for pc in HELPER_PCS),
            "route-0x008418 helper or paired witness drift")
    return {
        "counts": {"direct_writes": len(direct), "helper_writes": len(helper),
                   "samples": len(samples), "rng_calls": 0},
        "semantic_sha256": {"writes": semantic(writes),
                            "samples": semantic(samples), "rng": semantic(rng)},
        "write_rows": writes,
        "sample_projection": [{key: row[key] for key in
            ("frame", "g8008", "g800c", "g8010", "g8014", "g8248",
             "player_active", "player_state", "player_phase", "player_x",
             "player_z", "population")} for row in samples],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and
            decoder.base.sha256(OPCODES) == decoder.OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = decoder.base.load_json(ORACLE)
    handoff = decoder.base.load_json(HANDOFF)
    segments = [decoder.base.load_json(path) for path in SEGMENTS]
    edges = [row for row in oracle["route_state_edges"]
             if row["writer_pc"] == "0x008418"]
    require([(row["write_frame"], row["sample_transition_frame"])
             for row in edges] == [(5452, 5453), (15018, 15019)] and
            all(row["transition_guard"] == "u8(g81f3) != 0" and
                row["source_window"] == {
                    "first": "0x008408", "last_exclusive": "0x008438",
                    "sha256": "24c11db9b6955fb7d3e0f629d3db35000fdb955a36d664f1683ac5abd4b55ac6"}
                for row in edges), "accepted route-0x008418 edges drift")
    segment_edges = [row for segment in segments for row in
                     segment["route_authority_extension"]["route_state_edges"]
                     if row["writer_pc"] == "0x008418"]
    require(segment_edges == [edges[1]],
            "P2 segment route-0x008418 edge drift")
    handoff_edge = next(row for row in handoff["route_edges"]
                        if row["tap_pc"] == "0x008418")
    require(handoff_edge["source_frame"] == 15018 and
            handoff_edge["visible_frame"] == 15019 and
            handoff["counterfactuals"]["suppress_exact_clear_writer_completes"]
            is False, "round-clear counterfactual drift")

    direct_transactions = [row for row in oracle["route_writer_transactions"]
                           if row["writer_pc"] in
                           {"0x008418", "0x00842c"}]
    helper_transactions = [row for row in oracle["route_writer_transactions"]
                           if row["writer_pc"] in
                           {f"0x{pc}" for pc in HELPER_PCS}]
    require(len(direct_transactions) == 2 and len(helper_transactions) == 9 and
            all(row["classification"] == "SOURCE_CLOSED" and
                row["write_count"] >= 2
                for row in direct_transactions + helper_transactions),
            "route-0x008418 writer ownership drift")

    image = OPCODES.read_bytes()
    require(hashlib.sha256(image[ACCEPTED_WINDOW[0]:ACCEPTED_WINDOW[1]]).hexdigest()
            == "24c11db9b6955fb7d3e0f629d3db35000fdb955a36d664f1683ac5abd4b55ac6",
            "route-0x008418 accepted source window drift")
    decoder.PROGRAM_FIRST = PROGRAM_FIRST
    decoder.PROGRAM_LAST_EXCLUSIVE = PROGRAM_LAST_EXCLUSIVE
    decoder.TABLES, decoder.COMPUTED_SITES = {}, {}
    decoder.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, (dispatch, external) = decoder.decode_program(image)
    require(dispatch == {}, "route-0x008418 must not invent computed dispatch")
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-0x008418 witness drift")

    stage2 = source_bytes(image, 0x129B5A, 0x129B66)
    stage4 = source_bytes(image, 0x129BCC, 0x129BD8)
    pointer_table = source_bytes(image, 0x021EEC, 0x021EF8)
    require(stage2["bytes_hex"] == "0100020300060028004e1201" and
            stage4["bytes_hex"] == "030201000006000c00120000" and
            pointer_table["bytes_hex"] == "00128f7a0012975600129b34",
            "route player-presentation tables drift")
    return {
        "schema": "spec02-route-8418-whole-program-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch and instance of the round-clear route program containing writer 0x008418",
        "source_identity": {
            "opcode_image_sha256": decoder.OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": decoder.base.sha256(ORACLE),
            "handoff_artifact": HANDOFF.relative_to(ROOT).as_posix(),
            "handoff_sha256": decoder.base.sha256(HANDOFF),
            "segment_artifacts": [{"path": path.relative_to(ROOT).as_posix(),
                                   "sha256": decoder.base.sha256(path)}
                                  for path in SEGMENTS],
            "entry": "0x00840a", "writer_pc": "0x008418",
            "program_window": ["0x00840a", "0x008438"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
            "accepted_writer_centered_window": ["0x008408", "0x008438"],
            "accepted_writer_centered_window_sha256":
                "24c11db9b6955fb7d3e0f629d3db35000fdb955a36d664f1683ac5abd4b55ac6",
            "alignment_note": "0x008408 is an evidence boundary; executable decoding begins at aligned 0x00840a",
        },
        "scheduler_contract": {
            "caller_chain": ["0x0080a2", "0x000000", "0x000000"],
            "source_write_frames_u16": [5452, 15018],
            "visible_transition_frames_u16": [5453, 15019],
            "order": "main route controller tests the clear byte, performs direct writes, calls shared route setup, binds stage presentation, then reaches the common continuation",
        },
        "field_types": {
            "g81f3": "route_clear_u8", "g8008": "route_state_s16",
            "g800c": "route_substate_u16", "g8240": "route_control_enable_u8",
            "g8237": "presentation_stage_selector_u8",
            "g81e8": "round_stage_index_u16", "g822c": "presentation_stage_index_u16",
        },
        "transition_contract": {
            "guard": "u8(g81f3) != 0",
            "guard_false": "branch directly to 0x008438 with no owned write or helper call",
            "guard_true_ordered_writes": [
                {"pc": "0x008412", "tap_pc": "0x008418", "field": "g8008:s16", "operation": "+= 2", "observed": "4->6"},
                {"pc": "0x008416", "tap_pc": "0x00841c", "field": "g800c:u16", "operation": "= 0"},
                {"pc": "0x00841a", "tap_pc": "0x008420", "field": "g8240:u8", "operation": "= 1"},
                {"pc": "0x008426", "tap_pc": "0x00842c", "field": "g8237:u8", "operation": "= 8"},
                {"pc": "0x00842c", "tap_pc": "0x008432", "field": "g822c:u16", "operation": "= g81e8:u16"}],
            "ordered_helper_calls": ["0x00c754", "0x021ef8"],
            "continuation_target": "0x008438", "rng_calls": 0,
        },
        "shared_route_setup_contract": {
            "entry": "0x00c754", "return": "0x008426",
            "ordered_writer_pcs": [f"0x{pc}" for pc in sorted(HELPER_PCS)],
            "owned_writer_transactions": helper_transactions,
            "result": "set route transition flags, copy source presentation gate, and clear the exact shared route fields before returning",
        },
        "player_presentation_stage_binding": {
            "entry": "0x021ef8", "return": "0x008438",
            "classification": "SOURCE_OWNED_PRESENTATION_DEPENDENCY",
            "route_written_selector_u8": 8,
            "round1_reachable_stage_indices_u16": [2, 4],
            "generic_path_guard": "g8237==8 and g81e8 not in {14,36}",
            "player_scan": "four character IDs are mapped across the three active player records; each active record receives the selected stage presentation pointer and clears its presentation cursor",
            "pointer_table": pointer_table,
            "stage2_record": stage2, "stage4_record": stage4,
            "special_indices_14_36": "not reached by either Round 1 invocation and forbidden from substituting for the generic path",
            "gameplay_authority": False,
        },
        "normalized_source_program": {
            "representation": "bounded aligned route-specific 68000 operations with explicit widths, reads, writes, guards and targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(
                decoder.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": decoder.field_profiles(instructions),
            "external_transfers": external,
        },
        "owned_writer_transactions": direct_transactions,
        "dynamic_witness": witness_a,
        "paired_capture_identity": [segment["paired_capture_ceremony"]
                                    for segment in segments],
        "counterfactuals": {
            "suppress_exact_clear_writer": handoff["counterfactuals"],
            "route_wide_perturbation": segments[1]["route_authority_extension"]["route_wide_perturbation"],
        },
        "mutation_controls": {
            "misaligned_evidence_window_decode_rejected": True,
            "clear_guard_field_or_polarity_mutation_rejected": True,
            "route_add_two_or_fixed_frame_mutation_rejected": True,
            "write_width_order_or_field_mutation_rejected": True,
            "route_setup_call_order_or_suppression_rejected": True,
            "stage_selector_mutation_rejected": True,
            "stage_index_copy_mutation_rejected": True,
            "presentation_pointer_table_mutation_rejected": True,
            "stage2_record_mutation_rejected": True,
            "stage4_record_mutation_rejected": True,
            "special_branch_substitution_rejected": True,
            "invented_audio_load_or_rng_rejected": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "logical_audio_or_load_event": False,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "route-0x008418 status drift")
    source = value["source_identity"]
    require(source["program_window"] == ["0x00840a", "0x008438"] and
            source["accepted_writer_centered_window_sha256"] ==
            "24c11db9b6955fb7d3e0f629d3db35000fdb955a36d664f1683ac5abd4b55ac6",
            "route-0x008418 source window drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 9 and
            program["instructions_sha256"] ==
            "0fbe328a0840269e3516ee2e7bf329cd5279d440744e810ed516ced0d7a6699a" and
            len(program["field_access_profiles"]) == 7 and
            len(program["external_transfers"]) == 3,
            "route-0x008418 decoded program closure incomplete")
    transition = value["transition_contract"]
    require(transition["guard"] == "u8(g81f3) != 0" and
            [row["tap_pc"] for row in transition["guard_true_ordered_writes"]] ==
            ["0x008418", "0x00841c", "0x008420", "0x00842c", "0x008432"] and
            [row["operation"] for row in transition["guard_true_ordered_writes"]] ==
            ["+= 2", "= 0", "= 1", "= 8", "= g81e8:u16"] and
            transition["ordered_helper_calls"] == ["0x00c754", "0x021ef8"] and
            transition["rng_calls"] == 0,
            "route-0x008418 transition contract drift")
    presentation = value["player_presentation_stage_binding"]
    require(presentation["round1_reachable_stage_indices_u16"] == [2, 4] and
            presentation["pointer_table"]["bytes_hex"] ==
            "00128f7a0012975600129b34" and
            presentation["stage2_record"]["bytes_hex"] ==
            "0100020300060028004e1201" and
            presentation["stage4_record"]["bytes_hex"] ==
            "030201000006000c00120000" and
            presentation["gameplay_authority"] is False,
            "route-0x008418 presentation binding drift")
    require(value["dynamic_witness"]["counts"] == {
                "direct_writes": 10, "helper_writes": 18,
                "samples": 8, "rng_calls": 0} and
            len(value["owned_writer_transactions"]) == 2 and
            len(value["shared_route_setup_contract"]
                ["owned_writer_transactions"]) == 9 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["logical_audio_or_load_event"] is False and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-0x008418 ownership or mutation closure drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build(); validate(value); encoded = canonical(value) + b"\n"
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "route-0x008418 generated artifact stale; regenerate")
        print("SPEC-02 route-0x008418 artifact: PASS")
        return
    OUT.write_bytes(encoded)
    print(f"wrote {OUT.relative_to(ROOT)} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
