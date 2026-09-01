#!/usr/bin/env python3
"""Build the bounded SPEC-02 route-state 0->2 transition program."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
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
SCHEDULER = ROOT / "data/oracle11_actor_scheduler_lifecycle.json"
AUDIO = ROOT / "data/oracle11_global_audio_trigger_owners.json"
SEGMENT = ROOT / "data/oracle10_round1_census_extension_15081_15091.json"
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_83d4_program.json"

PROGRAM_FIRST = 0x0083C8
PROGRAM_LAST_EXCLUSIVE = 0x0083FC
SOURCE_FRAMES = (5561, 15088)
AUDIO_FRAMES = (5563, 15090)
DIRECT_PCS = {"0083d4", "0083d8", "0083dc", "0083e0"}
POOL_RESET_PCS = {"0174ba", "0174c2", "0174c6", "01763e"}
EXTERNAL_TRANSFER_OWNERS = {
    0x001972: "shared-ff00-command-wrapper",
    0x0083C6: "route-zero-guard-false-return",
    0x01728A: "accepted-fixed-pool-reset-entry",
    0x017CA8: "accepted-route-zero-helper-0x017ca8",
    0x0AC15E: "accepted-route-zero-helper-0x0ac15e",
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


def dynamic_witness(directory: Path) -> dict[str, object]:
    route_rows = rows(directory / "route_writes.tsv")
    direct = [row for row in route_rows if int(row["frame"]) in SOURCE_FRAMES
              and row["pc"].lower() in DIRECT_PCS]
    direct.sort(key=lambda row: (int(row["frame"]), int(row["pc"], 16)))
    expected = {
        5561: [("0083d4", "ff8008", "00000002"),
               ("0083d8", "ff800c", "00000000"),
               ("0083dc", "ff81f2", "00000000"),
               ("0083e0", "ff820a", "00000000")],
        15088: [("0083d4", "ff8008", "00000002"),
                ("0083d8", "ff800c", "00000000"),
                ("0083dc", "ff81f2", "00000000"),
                ("0083e0", "ff820a", "00000000")],
    }
    require([(int(row["frame"]), row["pc"].lower(), row["address"].lower(),
              row["data"].lower()) for row in direct] ==
            [(frame, *item) for frame in SOURCE_FRAMES for item in expected[frame]],
            "route-0x0083d4 direct writer witness drift")

    pool_reset = [row for row in route_rows
                  if int(row["frame"]) in SOURCE_FRAMES and
                  row["pc"].lower() in POOL_RESET_PCS]
    pool_reset.sort(key=lambda row: (int(row["frame"]), int(row["pc"], 16),
                                    int(row["address"], 16)))
    counts = Counter((int(row["frame"]), row["pc"].lower())
                     for row in pool_reset)
    require(counts == Counter({(5561, "0174ba"): 32,
                               (5561, "0174c2"): 1,
                               (5561, "0174c6"): 1,
                               (5561, "01763e"): 76,
                               (15088, "0174ba"): 32,
                               (15088, "0174c2"): 1,
                               (15088, "0174c6"): 1,
                               (15088, "01763e"): 76}),
            "route-0x0083d4 fixed-pool reset witness drift")

    samples = [row for row in rows(directory / "route_samples.tsv")
               if any(frame - 1 <= int(row["frame"]) <= frame + 2
                      for frame in SOURCE_FRAMES)]
    audio = [row for row in rows(directory / "dispatches.tsv")
             if int(row["frame"]) in AUDIO_FRAMES and
             row["command"].lower() == "ff00" and
             row["a6"].lower() == "ffea80" and
             row["return0"].lower() == "001a34" and
             row["return1"].lower() == "0080a2"]
    rng = [row for row in rows(directory / "route_rng.tsv")
           if int(row["frame"]) in SOURCE_FRAMES]
    require(len(direct) == 8 and len(pool_reset) == 220 and
            len(samples) == 8 and len(audio) == 2 and not rng,
            "route-0x0083d4 paired witness row count drift")
    return {
        "counts": {"direct_writes": 8, "fixed_pool_reset_writes": 220,
                   "samples": 8, "ff00_dispatches": 2, "rng_calls": 0},
        "semantic_sha256": {"direct_writes": semantic(direct),
                            "fixed_pool_reset_writes": semantic(pool_reset),
                            "samples": semantic(samples),
                            "ff00_dispatches": semantic(audio),
                            "rng": semantic(rng)},
        "direct_write_rows": direct,
        "fixed_pool_reset_summary": {
            "writer_counts": {f"{frame}:{pc}": count
                              for (frame, pc), count in sorted(counts.items())},
            "semantic_sha256": semantic(pool_reset),
        },
        "ff00_dispatch_rows": audio,
        "sample_projection": [{key: row[key] for key in
            ("frame", "g8008", "g800c", "g8010", "g8014", "g8248",
             "player_active", "player_state", "player_phase", "player_x",
             "player_z", "population")} for row in samples],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and decoder.base.sha256(OPCODES) ==
            decoder.OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = decoder.base.load_json(ORACLE)
    handoff = decoder.base.load_json(HANDOFF)
    scheduler = decoder.base.load_json(SCHEDULER)
    audio = decoder.base.load_json(AUDIO)
    segment = decoder.base.load_json(SEGMENT)
    edges = [row for row in oracle["route_state_edges"]
             if row["writer_pc"] == "0x0083d4"]
    require([(row["write_frame"], row["sample_transition_frame"])
             for row in edges] == [(5561, 5562), (15088, 15089)] and
            all(row["transition_guard"] == "s16(g837c) == 0" and
                row["source_window"] == {
                    "first": "0x0083c4", "last_exclusive": "0x0083f4",
                    "sha256": "3813fbb167fad415d00f787901e0b0e4cbafab1cbfd789d83fd9b3d9cf7d7384"}
                for row in edges), "accepted route-0x0083d4 edges drift")
    segment_edge = next(row for row in
                        segment["route_authority_extension"]["route_state_edges"]
                        if row["writer_pc"] == "0x0083d4")
    require(segment_edge == edges[1], "P2 route-0x0083d4 edge drift")
    handoff_edge = next(row for row in handoff["route_edges"]
                        if row["tap_pc"] == "0x0083d4")
    require(handoff_edge["source_frame"] == 15088 and
            handoff_edge["visible_frame"] == 15089 and
            handoff_edge["source_window"]["sha256"] ==
                "335a3f3ecf8c29ed8659930ba404b978649af1d9f70b5940bfb2fe5f8b9be9d1",
            "route-0x0083d4 handoff witness drift")

    exit_program = oracle["first_segment_recurring_spawn"]["exit_controller_program"]
    route_zero = exit_program["route_zero_program"]
    require(exit_program["spec_executable"] is True and
            route_zero["dispatcher"] == "0x00837c..0x0083c6" and
            route_zero["substates"][-1] == {
                "guard": "s16(g837c)==0",
                "routine": "0x0083c8..0x0083fa",
                "substate_u16": 4,
                "writes": "route=2; substate=0; clear withdrawal and presentation-load flags"},
            "accepted route-zero dependency drift")
    pool_contract = scheduler["pools"]
    require(any(row.get("initializer") == "0x01729e" for row in pool_contract),
            "accepted fixed-pool initializer dependency drift")

    audio_group = next(row for row in audio["trigger_groups"]
                       if row["id"] == "global-audio-ffea80-001a34-ff00")
    tail_context = next(row for row in
                        audio_group["transition_guard"]["contexts"]
                        if row["source_call"]["address"] == "0x00809e")
    require(audio_group["classification"] == "SOURCE_CLOSED" and
            audio_group["command"] == "0xff00" and
            audio_group["argument_variants"] ==
                [["0000ff00", "00000000", "00000000"]] and
            tail_context["first_frame"] == 5563 and
            tail_context["last_frame"] == 15090 and
            tail_context["occurrences"] == 2 and
            audio_group["handler_transaction"]["causal_control"]
                ["gameplay_projection_unchanged"] is True,
            "route-0x0083d4 ff00 ownership drift")

    transactions = [row for row in oracle["route_writer_transactions"]
                    if row["writer_pc"] in
                    {"0x0083d4", "0x0083d8", "0x0083dc", "0x0083e0"}]
    require(len(transactions) == 4 and
            all(row["classification"] == "SOURCE_CLOSED" and
                row["write_count"] == 2 for row in transactions),
            "route-0x0083d4 writer ownership drift")

    image = OPCODES.read_bytes()
    require(hashlib.sha256(image[0x0083C4:0x0083F4]).hexdigest() ==
                "3813fbb167fad415d00f787901e0b0e4cbafab1cbfd789d83fd9b3d9cf7d7384" and
            hashlib.sha256(image[0x0083BC:0x0083E4]).hexdigest() ==
                "335a3f3ecf8c29ed8659930ba404b978649af1d9f70b5940bfb2fe5f8b9be9d1",
            "route-0x0083d4 accepted source windows drift")
    decoder.PROGRAM_FIRST = PROGRAM_FIRST
    decoder.PROGRAM_LAST_EXCLUSIVE = PROGRAM_LAST_EXCLUSIVE
    decoder.TABLES, decoder.COMPUTED_SITES = {}, {}
    decoder.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, (dispatch, external) = decoder.decode_program(image)
    require(not dispatch, "route-0x0083d4 must not invent computed dispatch")
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-0x0083d4 witness drift")

    return {
        "schema": "spec02-route-83d4-whole-program-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "the complete Round 1-reachable substate-4 route-zero transition body selected at both Coffee Shop exit and Round 1 results exit",
        "source_identity": {
            "opcode_image_sha256": decoder.OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": decoder.base.sha256(ORACLE),
            "handoff_artifact": HANDOFF.relative_to(ROOT).as_posix(),
            "handoff_sha256": decoder.base.sha256(HANDOFF),
            "scheduler_artifact": SCHEDULER.relative_to(ROOT).as_posix(),
            "scheduler_sha256": decoder.base.sha256(SCHEDULER),
            "audio_artifact": AUDIO.relative_to(ROOT).as_posix(),
            "audio_sha256": decoder.base.sha256(AUDIO),
            "segment_artifact": SEGMENT.relative_to(ROOT).as_posix(),
            "segment_sha256": decoder.base.sha256(SEGMENT),
            "entry": "0x0083c8", "writer_pc": "0x0083d4",
            "program_window": ["0x0083c8", "0x0083fc"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
            "accepted_writer_centered_window": ["0x0083c4", "0x0083f4"],
            "accepted_writer_centered_window_sha256":
                "3813fbb167fad415d00f787901e0b0e4cbafab1cbfd789d83fd9b3d9cf7d7384",
            "accepted_handoff_window": ["0x0083bc", "0x0083e4"],
            "accepted_handoff_window_sha256":
                "335a3f3ecf8c29ed8659930ba404b978649af1d9f70b5940bfb2fe5f8b9be9d1",
        },
        "scheduler_contract": {
            "caller_chain": ["0x0080a2", "0x000000", "0x000000"],
            "source_write_frames_u16": list(SOURCE_FRAMES),
            "visible_transition_frames_u16": [5562, 15089],
            "route_zero_dependency_sha256": semantic(route_zero),
            "order": "the accepted route-zero dispatcher reaches substate 4; this body tests the signed loader-resume countdown, performs its exact writes and shared calls, then tail-enqueues ff00",
        },
        "field_types": {
            "g837c": "loader_resume_countdown_s16",
            "g8008": "route_state_s16", "g800c": "route_substate_u16",
            "g81f3": "route_clear_flag_u8",
            "g820a": "presentation_load_flag_u8",
            "g90e8": "shared_command_latch_u16",
        },
        "transition_contract": {
            "guard": "s16(g837c) == 0",
            "guard_false": "branch to 0x0083c6 and return with no owned write, helper call or audio command",
            "guard_true_ordered_writes": [
                {"instruction_pc": "0x0083ce", "tap_pc": "0x0083d4",
                 "field": "g8008:s16", "operation": "+= 2", "observed": "0->2"},
                {"instruction_pc": "0x0083d2", "tap_pc": "0x0083d8",
                 "field": "g800c:u16", "operation": "= 0"},
                {"instruction_pc": "0x0083d6", "tap_pc": "0x0083dc",
                 "field": "g81f3:u8", "operation": "= 0"},
                {"instruction_pc": "0x0083da", "tap_pc": "0x0083e0",
                 "field": "g820a:u8", "operation": "= 0"},
                {"instruction_pc": "0x0083f0", "field": "g90e8:u16",
                 "operation": "= 1"}],
            "ordered_calls": ["0x01728a", "0x0ac15e", "0x017ca8"],
            "tail_target": "0x001972", "rng_calls": 0,
        },
        "accepted_helper_dependencies": {
            "route_zero_program": route_zero,
            "fixed_pool_reset": {
                "entry": "0x01728a", "accepted_pool_contract_sha256": semantic(pool_contract),
                "initializer": "0x01729e", "writer_pcs": sorted(POOL_RESET_PCS),
                "paired_write_count": 220,
                "paired_semantic_sha256": witness_a["fixed_pool_reset_summary"]["semantic_sha256"],
            },
            "0x0ac15e": "accepted route-zero helper dependency; preserve exact call position and source effects without semantic renaming",
            "0x017ca8": "accepted route-zero helper dependency; preserve exact call position and source effects without semantic renaming",
        },
        "audio_command_contract": {
            "logical_event_id": audio_group["id"], "command": "0xff00",
            "semantic_sound_name": "UNKNOWN", "tail_entry": "0x001972",
            "argument_variant": audio_group["argument_variants"][0],
            "dispatch_frames_u16": list(AUDIO_FRAMES),
            "handler_transaction": audio_group["handler_transaction"],
            "gameplay_coupling": False,
        },
        "load_release_contract": {
            "logical_event_owned": False,
            "rule": "this route transition owns no load or release; later source loader callers and their accepted legal read windows remain separately authoritative",
        },
        "normalized_source_program": {
            "representation": "one bounded aligned route-zero body with explicit widths, reads, writes, guard, helper order and tail command; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(
                decoder.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": decoder.field_profiles(instructions),
            "external_transfers": external,
        },
        "owned_writer_transactions": transactions,
        "dynamic_witness": witness_a,
        "paired_capture_identity": segment["paired_capture_ceremony"],
        "counterfactuals": {
            "route_wide_perturbation":
                segment["route_authority_extension"]["route_wide_perturbation"],
            "audio_suppression": audio_group["handler_transaction"]["causal_control"],
            "handoff": handoff["counterfactuals"],
        },
        "mutation_controls": {
            "accepted_source_window_or_alignment_mutation_rejected": True,
            "signed_countdown_field_or_polarity_mutation_rejected": True,
            "route_add_two_or_fixed_frame_mutation_rejected": True,
            "write_width_order_or_field_mutation_rejected": True,
            "route_clear_flag_mutation_rejected": True,
            "presentation_load_flag_mutation_rejected": True,
            "fixed_pool_reset_suppression_rejected": True,
            "helper_order_or_target_mutation_rejected": True,
            "audio_latch_width_or_value_mutation_rejected": True,
            "ff00_command_arguments_or_tail_mutation_rejected": True,
            "invented_load_release_or_rng_rejected": True,
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
            "route-0x0083d4 status drift")
    source = value["source_identity"]
    require(source["program_window"] == ["0x0083c8", "0x0083fc"] and
            source["program_window_sha256"] ==
                "0af69945481bbf585d5a9fc8a171ff5d3bdd79a5015aee9482d761a4ec1bd2d3" and
            source["accepted_writer_centered_window_sha256"] ==
                "3813fbb167fad415d00f787901e0b0e4cbafab1cbfd789d83fd9b3d9cf7d7384" and
            source["accepted_handoff_window_sha256"] ==
                "335a3f3ecf8c29ed8659930ba404b978649af1d9f70b5940bfb2fe5f8b9be9d1",
            "route-0x0083d4 source identity drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 11 and
            program["instructions_sha256"] ==
                "fdeb1ff1eafc2d186424e772b0dc63d497ce8c510a207a88ed546e5be3fbab3f" and
            len(program["field_access_profiles"]) == 6 and
            len(program["external_transfers"]) == 5,
            "route-0x0083d4 decoded program closure incomplete")
    transition = value["transition_contract"]
    require(transition["guard"] == "s16(g837c) == 0" and
            [row["field"] for row in transition["guard_true_ordered_writes"]] ==
                ["g8008:s16", "g800c:u16", "g81f3:u8", "g820a:u8", "g90e8:u16"] and
            [row["operation"] for row in transition["guard_true_ordered_writes"]] ==
                ["+= 2", "= 0", "= 0", "= 0", "= 1"] and
            transition["ordered_calls"] ==
                ["0x01728a", "0x0ac15e", "0x017ca8"] and
            transition["tail_target"] == "0x001972" and
            transition["rng_calls"] == 0,
            "route-0x0083d4 transition contract drift")
    audio = value["audio_command_contract"]
    require(audio["command"] == "0xff00" and
            audio["argument_variant"] ==
                ["0000ff00", "00000000", "00000000"] and
            audio["dispatch_frames_u16"] == [5563, 15090] and
            audio["semantic_sound_name"] == "UNKNOWN" and
            audio["gameplay_coupling"] is False,
            "route-0x0083d4 audio contract drift")
    require(value["dynamic_witness"]["counts"] == {
                "direct_writes": 8, "fixed_pool_reset_writes": 220,
                "samples": 8, "ff00_dispatches": 2, "rng_calls": 0} and
            len(value["owned_writer_transactions"]) == 4 and
            value["load_release_contract"]["logical_event_owned"] is False and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-0x0083d4 ownership or mutation closure drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build(); validate(value); encoded = canonical(value) + b"\n"
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "route-0x0083d4 generated artifact stale; regenerate")
        print("SPEC-02 route-0x0083d4 artifact: PASS")
        return
    OUT.write_bytes(encoded)
    print(f"wrote {OUT.relative_to(ROOT)} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
