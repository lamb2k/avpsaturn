#!/usr/bin/env python3
"""Build the bounded SPEC-02 Round 1 route-reset dispatcher program."""
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
AUDIO = ROOT / "data/oracle11_global_audio_trigger_owners.json"
SEGMENTS = (
    ROOT / "data/oracle10_round1_census_extension_5567_6200.json",
    ROOT / "data/oracle10_round1_census_extension_13293_15039.json",
)
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_c886_program.json"

DISPATCHER_WINDOW = (0x00C7EA, 0x00C816)
TABLE_WINDOW = (0x00C816, 0x00C83C)
SLICES = ((0x00C83C, 0x00C87A), (0x00C880, 0x00C8A8))
SOURCE_FRAMES = (5523, 15020)
DIRECT_BY_FRAME = {
    5523: ("00c84c", "00c850", "00c854", "00c858", "00c866", "00cc9e"),
    15020: ("00c886", "00c88a", "00c88e", "00c892", "00c8a0", "00cc9e"),
}
CLEAR_HELPER_PCS = ("00c78a", "00c78e", "00c792", "00c796", "00c79a",
                    "00c79e", "00c7a6", "00c7aa", "00c7ae")
EXTERNAL_TRANSFER_OWNERS = {
    0x003BDC: "shared-audio-command-wrapper",
    0x00C784: "shared-route-state-clear",
    0x00C87A: "shared-route-dispatcher-continuation",
    0x00CC94: "shared-round-index-map",
    0x00CCF8: "shared-player-transition-presentation",
    0x01614A: "shared-route-result-continuation",
}
DISPATCH_OFFSETS = [38, 38, 106, 146, 106, 38, 38, 272, 106, 146,
                    106, 412, 146, 600, 146, 146, 38, 146, 704]
DISPATCH_TARGETS = [
    0x00C83C, 0x00C83C, 0x00C880, 0x00C8A8, 0x00C880, 0x00C83C,
    0x00C83C, 0x00C926, 0x00C880, 0x00C8A8, 0x00C880, 0x00C9B2,
    0x00C8A8, 0x00CA6E, 0x00C8A8, 0x00C8A8, 0x00C83C, 0x00C8A8,
    0x00CAD6,
]


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


def decode_slices(image: bytes) -> tuple[list[dict[str, object]],
                                         list[dict[str, object]],
                                         list[dict[str, object]]]:
    instructions: list[dict[str, object]] = []
    external: list[dict[str, object]] = []
    metadata: list[dict[str, object]] = []
    for first, last in SLICES:
        decoder.PROGRAM_FIRST, decoder.PROGRAM_LAST_EXCLUSIVE = first, last
        decoder.TABLES, decoder.COMPUTED_SITES = {}, {}
        decoder.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
        part, (dispatch, transfers) = decoder.decode_program(image)
        require(not dispatch, "route-reset bodies must not invent computed dispatch")
        instructions.extend(part)
        external.extend(transfers)
        metadata.append({"first": f"0x{first:06x}",
                         "last_exclusive": f"0x{last:06x}",
                         "sha256": hashlib.sha256(image[first:last]).hexdigest(),
                         "instruction_count": len(part),
                         "field_profile_count": len(decoder.field_profiles(part)),
                         "external_transfer_count": len(transfers)})
    return instructions, external, metadata


def dynamic_witness(directory: Path) -> dict[str, object]:
    all_rows = rows(directory / "route_writes.tsv")
    writes: list[dict[str, str]] = []
    for frame in SOURCE_FRAMES:
        wanted = set(DIRECT_BY_FRAME[frame]) | set(CLEAR_HELPER_PCS)
        selected = [row for row in all_rows if int(row["frame"]) == frame and
                    row["pc"].lower() in wanted]
        selected.sort(key=lambda row: int(row["pc"], 16))
        require(len(selected) == 15, f"route-reset frame {frame} write witness drift")
        writes.extend(selected)
    expected_direct = {
        5523: [("00c84c", "ff8008", "00000000"),
               ("00c850", "ff800c", "00000000"),
               ("00c854", "ff8010", "00000000"),
               ("00c858", "ff8014", "00000000"),
               ("00c866", "ff81e8", "00000004"),
               ("00cc9e", "ff8222", "00000000")],
        15020: [("00c886", "ff8008", "00000000"),
                ("00c88a", "ff800c", "00000000"),
                ("00c88e", "ff8010", "00000000"),
                ("00c892", "ff8014", "00000000"),
                ("00c8a0", "ff81e8", "00000006"),
                ("00cc9e", "ff8222", "00000001")],
    }
    for frame in SOURCE_FRAMES:
        actual = [(row["pc"].lower(), row["address"].lower(), row["data"].lower())
                  for row in writes if int(row["frame"]) == frame and
                  row["pc"].lower() in set(DIRECT_BY_FRAME[frame])]
        require(actual == sorted(expected_direct[frame], key=lambda row: int(row[0], 16)),
                f"route-reset frame {frame} direct write drift")
    samples = [row for row in rows(directory / "route_samples.tsv")
               if any(frame - 1 <= int(row["frame"]) <= frame + 2
                      for frame in SOURCE_FRAMES)]
    rng = [row for row in rows(directory / "route_rng.tsv")
           if any(first <= int(row["pc"], 16) < last for first, last in SLICES) or
           DISPATCHER_WINDOW[0] <= int(row["pc"], 16) < DISPATCHER_WINDOW[1]]
    require(len(writes) == 30 and len(samples) == 8 and not rng,
            "route-reset paired witness drift")
    return {
        "counts": {"route_writes": 30, "player_presentation_writes": 4,
                   "total_owned_writes": 34, "samples": 8, "rng_calls": 0},
        "semantic_sha256": {"writes": semantic(writes),
                            "samples": semantic(samples), "rng": semantic(rng)},
        "write_rows": writes,
        "player_presentation_writes": [
            {"frame": frame, "pc": "0x00cd08", "address": "active_player+0x8c",
             "type": "u8", "value": "0x40"} for frame in SOURCE_FRAMES] + [
            {"frame": frame, "pc": "0x00cd0e", "address": "active_player+0x8d",
             "type": "u8", "value": "0x0c"} for frame in SOURCE_FRAMES],
        "sample_projection": [{key: row[key] for key in
            ("frame", "g8008", "g800c", "g8010", "g8014", "g8248",
             "player_active", "player_state", "player_phase", "player_x",
             "player_z", "population")} for row in samples],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and decoder.base.sha256(OPCODES) == decoder.OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = decoder.base.load_json(ORACLE)
    handoff = decoder.base.load_json(HANDOFF)
    audio = decoder.base.load_json(AUDIO)
    segments = [decoder.base.load_json(path) for path in SEGMENTS]
    edge = next(row for row in oracle["route_state_edges"]
                if row["writer_pc"] == "0x00c886")
    require(edge["write_frame"] == 15020 and
            edge["sample_transition_frame"] == 15021 and
            edge["transition_guard"] ==
                "round-index dispatch selected the second transition body" and
            edge["source_window"] == {
                "first": "0x00c876", "last_exclusive": "0x00c8a6",
                "sha256": "0b513c6416543d878f188af34d17d574390a894d6d699dddf81990a7b3b2d320"},
            "accepted route-0x00c886 edge drift")
    segment_edges = [row for segment in segments for row in
                     segment["route_authority_extension"]["route_state_edges"]
                     if row["writer_pc"] == "0x00c886"]
    require(segment_edges == [edge], "P2 route-0x00c886 edge drift")
    require(any(row.get("tap_pc") == "0x00c886" for row in handoff["route_edges"]),
            "handoff route-0x00c886 edge missing")

    audio_group = next(row for row in audio["trigger_groups"]
                       if row["id"] == "global-audio-ff00d8-001a34-ff07")
    audio_context = next(row for row in audio_group["transition_guard"]["contexts"]
                         if row["source_call"]["address"] == "0x00c86e")
    require(audio_group["classification"] == "SOURCE_CLOSED" and
            audio_group["command"] == "0xff07" and
            audio_group["argument_variants"] ==
                [["0fffff07", "00000000", "00000000"]] and
            audio_context["first_frame"] == 5523 and
            audio_context["source_call"]["return_address"] == "0x00c874" and
            audio_group["handler_transaction"]["causal_control"]
                ["gameplay_projection_unchanged"] is True,
            "route-reset ff07 command ownership drift")

    image = OPCODES.read_bytes()
    dispatcher = source_bytes(image, *DISPATCHER_WINDOW)
    table = source_bytes(image, *TABLE_WINDOW)
    require(dispatcher["sha256"] ==
                "bf8624afff942389e26dbe04232e7aa93b5cc96fb186b8a5c99916cf80e0e9c8" and
            table["sha256"] ==
                "380bd5ffdf1b0a1fb0bc4b7032c4c600c42cfd49f8f7dcba418ce71ea38c46f3",
            "route-reset dispatcher or table bytes drift")
    offsets = [int.from_bytes(image[a:a + 2], "big", signed=True)
               for a in range(*TABLE_WINDOW, 2)]
    require(offsets == DISPATCH_OFFSETS and
            [TABLE_WINDOW[0] + offset for offset in offsets] == DISPATCH_TARGETS,
            "route-reset dispatcher table drift")
    instructions, external, slices = decode_slices(image)
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-reset witness drift")

    owner_pcs = {f"0x{pc}" for pc in
                 set(DIRECT_BY_FRAME[5523]) | set(DIRECT_BY_FRAME[15020]) |
                 set(CLEAR_HELPER_PCS)}
    transactions = [row for row in oracle["route_writer_transactions"]
                    if row["writer_pc"] in owner_pcs]
    require(len(transactions) >= 12 and all(row["classification"] == "SOURCE_CLOSED"
                                            for row in transactions),
            "route-reset owned writer provenance drift")
    return {
        "schema": "spec02-route-c886-whole-program-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "the reusable round-index route-reset dispatcher and both Round 1-reachable transition bodies",
        "source_identity": {
            "opcode_image_sha256": decoder.OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": decoder.base.sha256(ORACLE),
            "handoff_artifact": HANDOFF.relative_to(ROOT).as_posix(),
            "handoff_sha256": decoder.base.sha256(HANDOFF),
            "audio_artifact": AUDIO.relative_to(ROOT).as_posix(),
            "audio_sha256": decoder.base.sha256(AUDIO),
            "segment_artifacts": [{"path": path.relative_to(ROOT).as_posix(),
                                   "sha256": decoder.base.sha256(path)}
                                  for path in SEGMENTS],
            "entry": "0x00c7ea", "writer_pc": "0x00c886",
            "dispatcher_window": dispatcher,
            "table_window": table,
            "executable_slices": slices,
            "accepted_writer_centered_window": ["0x00c876", "0x00c8a6"],
            "accepted_writer_centered_window_sha256":
                "0b513c6416543d878f188af34d17d574390a894d6d699dddf81990a7b3b2d320",
        },
        "scheduler_contract": {
            "caller_chain": edge["caller_chain"],
            "source_write_frames_u16": list(SOURCE_FRAMES),
            "visible_transition_frames_u16": [5524, 15021],
            "order": "main route scheduler enters 0x00c7ea; the signed round-index table selects one complete body, which clears shared route state, updates active-player presentation, maps the next round index, optionally enqueues ff07, and tail-jumps to the shared result continuation",
        },
        "field_types": {
            "g81af": "route_gate_u8", "g8236": "route_gate_u8",
            "g823d": "route_gate_u8", "g823e": "route_latch_u8",
            "g8208": "post_route_player_gate_u8", "g81e8": "round_index_u16",
            "g8008": "route_state_s16", "g800c": "route_substate_u16",
            "g8010": "route_timer_u16", "g8014": "route_aux_u16",
            "g8222": "round_index_mapping_u16",
            "active_player+0x8c": "presentation_state_u8",
            "active_player+0x8d": "presentation_substate_u8",
        },
        "dispatcher_contract": {
            "guard": "u8(g81af) == u8(g823d)",
            "guard_true_write": "g823e:u8 = 1",
            "index": "g81e8:u16 is a byte offset into the signed-u16 table at 0x00c816",
            "table_offsets_s16": DISPATCH_OFFSETS,
            "table_targets": [f"0x{target:06x}" for target in DISPATCH_TARGETS],
            "round1_reachable": {"2": "0x00c83c", "4": "0x00c880"},
            "other_targets": "NOT_REQUIRED_FOR_ROUND1",
            "post_body_guard": "after the selected body returns, u8(g8208)!=0 calls 0x017080 before return",
        },
        "transition_contract": {
            "round_index_2": {
                "entry": "0x00c83c", "guard": "(u8(g8236) & u8(g81af)) == 0",
                "ordered_writes": ["g8008:s16=0", "g800c:u16=0", "g8010:u16=0",
                                   "g8014:u16=0", "g81e8:u16+=2", "g8222:u16=0"],
                "ordered_calls": ["0x00c784", "0x00ccf8", "0x00cc94",
                                  "0x003bdc(command=0xff07,args=0fffff07,0,0)"],
                "tail": "0x01614a", "visible_frame": 5524,
            },
            "round_index_4": {
                "entry": "0x00c880", "guard": "selected by exact signed dispatch table",
                "ordered_writes": ["g8008:s16=0", "g800c:u16=0", "g8010:u16=0",
                                   "g8014:u16=0", "g81e8:u16+=2", "g8222:u16=1"],
                "ordered_calls": ["0x00c784", "0x00ccf8", "0x00cc94"],
                "tail": "0x01614a", "visible_frame": 15021,
            },
            "rng_calls": 0,
        },
        "helper_contracts": {
            "0x00c784": {"owner": "shared-route-state-clear",
                          "ordered_writer_pcs": [f"0x{pc}" for pc in CLEAR_HELPER_PCS]},
            "0x00ccf8": {"owner": "shared-player-transition-presentation",
                          "active_player_scan": "three records, stride 0x100; active records only",
                          "writes": ["active_player+0x8c:u8=0x40",
                                     "active_player+0x8d:u8=0x0c"]},
            "0x00cc94": {"owner": "shared-round-index-map",
                          "round1_results": {"4": 0, "6": 1},
                          "writer_pc": "0x00cc9e", "field": "g8222:u16"},
            "0x01614a": {"owner": "shared-route-result-continuation"},
            "0x017080": {"owner": "shared-route-player-gate"},
        },
        "audio_command_contract": {
            "logical_event_id": audio_group["id"], "command": "0xff07",
            "semantic_sound_name": "UNKNOWN", "source_call": "0x00c86e",
            "return": "0x00c874", "argument_variant": audio_group["argument_variants"][0],
            "handler_transaction": audio_group["handler_transaction"],
            "score_or_gameplay_coupling": False,
        },
        "normalized_source_program": {
            "representation": "two bounded reachable 68000 route bodies with explicit widths, reads, writes, guards and transfers; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(decoder.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": decoder.field_profiles(instructions),
            "external_transfers": external,
        },
        "owned_writer_transactions": transactions,
        "dynamic_witness": witness_a,
        "paired_capture_identity": [segment["paired_capture_ceremony"]
                                    for segment in segments],
        "counterfactuals": {
            "route_wide_perturbation": segments[1]["route_authority_extension"]["route_wide_perturbation"],
            "audio_suppression": audio_group["handler_transaction"]["causal_control"],
            "handoff": handoff["counterfactuals"],
        },
        "mutation_controls": {
            "dispatcher_guard_field_or_polarity_rejected": True,
            "signed_table_offset_or_index_width_rejected": True,
            "reachable_table_target_substitution_rejected": True,
            "non_round1_target_substitution_rejected": True,
            "first_body_gate_and_vs_or_rejected": True,
            "route_write_width_order_or_field_rejected": True,
            "clear_helper_suppression_or_order_rejected": True,
            "active_player_scan_or_stride_rejected": True,
            "player_presentation_write_rejected": True,
            "round_index_increment_rejected": True,
            "round_index_map_value_rejected": True,
            "ff07_command_or_arguments_rejected": True,
            "ff07_call_suppression_rejected": True,
            "invented_second_body_audio_rejected": True,
            "tail_target_rejected": True,
            "invented_rng_or_fixed_frame_rejected": True,
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
            "route-0x00c886 status drift")
    source = value["source_identity"]
    require(source["dispatcher_window"]["sha256"] ==
                "bf8624afff942389e26dbe04232e7aa93b5cc96fb186b8a5c99916cf80e0e9c8" and
            source["table_window"]["sha256"] ==
                "380bd5ffdf1b0a1fb0bc4b7032c4c600c42cfd49f8f7dcba418ce71ea38c46f3" and
            source["accepted_writer_centered_window_sha256"] ==
                "0b513c6416543d878f188af34d17d574390a894d6d699dddf81990a7b3b2d320",
            "route-0x00c886 source identity drift")
    dispatch = value["dispatcher_contract"]
    require(dispatch["guard"] == "u8(g81af) == u8(g823d)" and
            dispatch["table_offsets_s16"] == DISPATCH_OFFSETS and
            dispatch["round1_reachable"] == {"2": "0x00c83c", "4": "0x00c880"} and
            dispatch["other_targets"] == "NOT_REQUIRED_FOR_ROUND1",
            "route-reset dispatcher contract drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 23 and
            program["instructions_sha256"] ==
                "5d817cf62826034f1bb9ec7ba0035eeaca4081742f37ba6b718b2a8ee7354225" and
            len(program["field_access_profiles"]) == 7 and
            len(program["external_transfers"]) == 10,
            "route-reset decoded program closure incomplete")
    transition = value["transition_contract"]
    require(transition["round_index_2"]["entry"] == "0x00c83c" and
            transition["round_index_4"]["entry"] == "0x00c880" and
            transition["round_index_2"]["ordered_writes"][-2:] ==
                ["g81e8:u16+=2", "g8222:u16=0"] and
            transition["round_index_4"]["ordered_writes"][-2:] ==
                ["g81e8:u16+=2", "g8222:u16=1"] and
            transition["rng_calls"] == 0,
            "route-reset transition contract drift")
    audio = value["audio_command_contract"]
    require(audio["command"] == "0xff07" and
            audio["source_call"] == "0x00c86e" and
            audio["argument_variant"] == ["0fffff07", "00000000", "00000000"] and
            audio["semantic_sound_name"] == "UNKNOWN" and
            audio["score_or_gameplay_coupling"] is False,
            "route-reset audio contract drift")
    require(value["dynamic_witness"]["counts"] == {
                "route_writes": 30, "player_presentation_writes": 4,
                "total_owned_writes": 34, "samples": 8, "rng_calls": 0} and
            len(value["owned_writer_transactions"]) >= 12 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-reset ownership or mutation closure drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build(); validate(value); encoded = canonical(value) + b"\n"
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "route-0x00c886 generated artifact stale; regenerate")
        print("SPEC-02 route-0x00c886 artifact: PASS")
        return
    OUT.write_bytes(encoded)
    print(f"wrote {OUT.relative_to(ROOT)} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
