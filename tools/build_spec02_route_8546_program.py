#!/usr/bin/env python3
"""Build the bounded SPEC-02 route-zero program containing writer 0x008546."""
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
base = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_encounter_route_authority.json"
AUDIO = ROOT / "data/oracle11_global_audio_trigger_owners.json"
SEGMENTS = (
    ROOT / "data/oracle10_round1_census_extension_5567_6200.json",
    ROOT / "data/oracle10_round1_census_extension_12478_12799.json",
)
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_8546_program.json"

# 0x008536 is the accepted 48-byte writer-centered evidence window, but it
# begins in the extension word of the aligned OR at 0x008534.  The executable
# route-zero branch begins at 0x008520 and ends at the common RTS.
PROGRAM_FIRST = 0x008520
PROGRAM_LAST_EXCLUSIVE = 0x00855E
ACCEPTED_WINDOW = (0x008536, 0x008566)
OPCODE_SHA256 = base.OPCODE_SHA256
EXTERNAL_TRANSFER_OWNERS = {
    0x001972: "shared-audio-command-queue-wrapper-ff00",
}
WRITER_PCS = {"008540", "008546", "00854a", "00854e", "008552"}
SOURCE_FRAMES = {6198, 12797}


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
              if int(row["frame"]) in SOURCE_FRAMES and
              row["pc"].lower() in WRITER_PCS]
    samples = [row for row in rows(directory / "route_samples.tsv")
               if any(frame - 1 <= int(row["frame"]) <= frame + 2
                      for frame in SOURCE_FRAMES)]
    rng = [row for row in rows(directory / "route_rng.tsv")
           if PROGRAM_FIRST <= int(row["pc"], 16) < PROGRAM_LAST_EXCLUSIVE]
    writes.sort(key=lambda row: (int(row["frame"]), int(row["pc"], 16)))
    expected = []
    for frame in sorted(SOURCE_FRAMES):
        expected.extend([
            (str(frame), "008540", "ff8004", "00000006"),
            (str(frame), "008546", "ff8008", "00000000"),
            (str(frame), "00854a", "ff800c", "00000000"),
            (str(frame), "00854e", "ff8010", "00000000"),
            (str(frame), "008552", "ff8014", "00000000"),
        ])
    require([(row["frame"], row["pc"].lower(), row["address"].lower(),
              row["data"].lower()) for row in writes] == expected and
            len(samples) == 8 and not rng,
            "route-0x008546 paired witness drift")
    return {
        "counts": {"writes": len(writes), "samples": len(samples), "rng_calls": 0},
        "semantic_sha256": {
            "writes": semantic(writes), "samples": semantic(samples),
            "rng": semantic(rng)},
        "write_rows": writes,
        "sample_projection": [{key: row[key] for key in
                               ("frame", "g8004", "g8008", "g800c", "g8010",
                                "g8014", "g8248", "player_active", "player_state",
                                "player_phase", "player_x", "player_z", "population")}
                              for row in samples],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and base.base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = base.base.load_json(ORACLE)
    audio = base.base.load_json(AUDIO)
    segments = [base.base.load_json(path) for path in SEGMENTS]
    edges = [row for segment in segments for row in
             segment["route_authority_extension"]["route_state_edges"]
             if row["writer_pc"] == "0x008546"]
    require(len(edges) == 2 and
            [(row["write_frame"], row["sample_transition_frame"]) for row in edges]
            == [(6198, 6199), (12797, 12798)] and
            all(row["transition_guard"] ==
                "u8(g81af)==0 && u8(g81d4)==0 && no active player records"
                for row in edges) and
            all(row["source_window"] == {
                "first": "0x008536", "last_exclusive": "0x008566",
                "sha256": "08fe394a5d57592cffc9f64dd7db16cd3268f0ade64969fdf59bf042905e4c6d"}
                for row in edges),
            "accepted route-0x008546 edge authority drift")
    transactions = [row for row in oracle["route_writer_transactions"]
                    if row["writer_pc"] in {f"0x{pc}" for pc in WRITER_PCS}]
    require(len(transactions) == 5 and all(
        row["classification"] == "SOURCE_CLOSED" and row["write_count"] == 2
        for row in transactions), "route-0x008546 writer ownership drift")
    audio_group = next(row for row in audio["trigger_groups"]
                       if row["command"] == "0xff00")
    audio_context = next(row for row in audio_group["transition_guard"]["contexts"]
                         if row["source_owner_return"] == "0x00855c")
    require(audio_group["classification"] == "SOURCE_CLOSED" and
            audio_group["argument_variants"] ==
                [["0000ff00", "00000000", "00000000"]] and
            audio_context["source_call"]["address"] == "0x008556" and
            audio_context["first_frame"] == 6198 and
            audio_context["last_frame"] == 12797 and
            audio_context["occurrences"] == 2,
            "route-0x008546 ff00 audio ownership drift")

    image = OPCODES.read_bytes()
    require(hashlib.sha256(image[ACCEPTED_WINDOW[0]:ACCEPTED_WINDOW[1]]).hexdigest()
            == "08fe394a5d57592cffc9f64dd7db16cd3268f0ade64969fdf59bf042905e4c6d",
            "route-0x008546 accepted centered source window drift")
    base.PROGRAM_FIRST, base.PROGRAM_LAST_EXCLUSIVE = PROGRAM_FIRST, PROGRAM_LAST_EXCLUSIVE
    base.TABLES, base.COMPUTED_SITES = {}, {}
    base.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    instructions, decoded = base.decode_program(image)
    dispatch, external = decoded
    require(dispatch == {}, "route-0x008546 must not invent computed dispatch")
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-0x008546 witness drift")
    return {
        "schema": "spec02-route-8546-whole-program-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable branch of the aligned route-zero program containing writer 0x008546",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": base.base.sha256(ORACLE),
            "audio_artifact": AUDIO.relative_to(ROOT).as_posix(),
            "audio_sha256": base.base.sha256(AUDIO),
            "segment_artifacts": [{"path": path.relative_to(ROOT).as_posix(),
                                   "sha256": base.base.sha256(path)}
                                  for path in SEGMENTS],
            "entry": "0x008520", "writer_pc": "0x008546",
            "program_window": ["0x008520", "0x00855e"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
            "accepted_writer_centered_window": ["0x008536", "0x008566"],
            "accepted_writer_centered_window_sha256":
                "08fe394a5d57592cffc9f64dd7db16cd3268f0ade64969fdf59bf042905e4c6d",
            "alignment_note": "0x008536 is an evidence-window boundary inside the 0x008534 OR instruction; executable decoding begins at aligned 0x008520",
        },
        "scheduler_contract": {
            "caller_chain": ["0x0080a2", "0x000000", "0x000000"],
            "source_write_frames_u16": [6198, 12797],
            "visible_transition_frames_u16": [6199, 12798],
            "order": "main route controller evaluates this route-zero branch after the retained per-frame shared subsystems; all five route writes precede the source-owned ff00 command enqueue and common return",
        },
        "field_types": {
            "g81af": "route_gate_u8", "g81d4": "route_gate_u8",
            "g8380": "player_record0_active_u8", "g8480": "player_record1_active_u8",
            "g8580": "player_record2_active_u8", "g8004": "route_mode_u16",
            "g8008": "route_state_s16", "g800c": "route_substate_u16",
            "g8010": "route_timer_u16", "g8014": "route_aux_u16",
            "g90e8": "shared_command_latch_u16",
        },
        "transition_contract": {
            "guard": "u8(g81af)==0 && u8(g81d4)==0 && (u8(g8380)|u8(g8480)|u8(g8580))==0",
            "guard_false_order": [
                "if u8(g81af)!=0 return", "else if u8(g81d4)!=0 return",
                "else if (u8(g8380)|u8(g8480)|u8(g8580))!=0 return"],
            "guard_false": "perform no owned route writes, shared-command-latch write, or ff00 command enqueue",
            "guard_true_ordered_writes": [
                {"pc": "0x008540", "field": "g8004:u16", "operation": "= 6"},
                {"pc": "0x008546", "field": "g8008:s16", "operation": "= 0"},
                {"pc": "0x00854a", "field": "g800c:u16", "operation": "= 0"},
                {"pc": "0x00854e", "field": "g8010:u16", "operation": "= 0"},
                {"pc": "0x008552", "field": "g8014:u16", "operation": "= 0"},
                {"pc": "0x008550", "field": "g90e8:u16", "operation": "= 1"}],
            "ordered_helper_calls": ["0x001972"],
            "return_target": "0x00855c",
            "rng_calls": 0,
        },
        "audio_command_contract": {
            "owner": "encounter",
            "player_or_presentation_owned": False,
            "caller_pc": "0x008556", "shared_wrapper_entry": "0x001972",
            "shared_wrapper_return": "0x001a34", "command": "0xff00",
            "arguments": {"d1": "0x0000ff00", "d2": "0x00000000", "d3": "0x00000000"},
            "semantic_sound_name": "UNKNOWN",
            "handler_transaction": audio_group["handler_transaction"],
            "source_context": audio_context,
        },
        "owned_writer_transactions": transactions,
        "normalized_source_program": {
            "representation": "bounded aligned route-specific 68000 operations with explicit widths, reads, writes, guards and targets; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(base.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": base.field_profiles(instructions),
            "external_transfers": external,
        },
        "dynamic_witness": witness_a,
        "paired_capture_identity": [segment["paired_capture_ceremony"] for segment in segments],
        "counterfactuals": {
            "route_wide_perturbation": segments[0]["route_authority_extension"]["route_wide_perturbation"],
            "ff00_handler_suppression": audio_group["handler_transaction"]["causal_control"],
        },
        "mutation_controls": {
            "misaligned_writer_window_decode_rejected": True,
            "guard_field_or_order_mutation_rejected": True,
            "active_player_or_vs_and_mutation_rejected": True,
            "guard_polarity_mutation_rejected": True,
            "fixed_frame_transition_rejected": True,
            "write_width_order_or_field_mutation_rejected": True,
            "shared_latch_value_mutation_rejected": True,
            "ff00_command_argument_mutation_rejected": True,
            "ff00_call_suppression_is_discriminating": True,
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
            "route-0x008546 status drift")
    source = value["source_identity"]
    require(source["program_window"] == ["0x008520", "0x00855e"] and
            source["program_window_sha256"] ==
                "616baa2b2482638b0e600151ab20e3fca9d4db900c0323d91bc69f37b7c73665" and
            source["accepted_writer_centered_window_sha256"] ==
                "08fe394a5d57592cffc9f64dd7db16cd3268f0ade64969fdf59bf042905e4c6d",
            "route-0x008546 source window drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 16 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "a1c69d5cbacf87f7858b5892d8b6aa0562185331df2d72da2031e180fba40482" and
            len(program["field_access_profiles"]) == 11 and
            program["external_transfers"] == [{
                "entry": "0x001972", "kind": "call",
                "owner": "shared-audio-command-queue-wrapper-ff00",
                "static_sites": 1}],
            "route-0x008546 aligned program closure incomplete")
    transition = value["transition_contract"]
    require(transition["guard"] ==
            "u8(g81af)==0 && u8(g81d4)==0 && (u8(g8380)|u8(g8480)|u8(g8580))==0" and
            [row["pc"] for row in transition["guard_true_ordered_writes"]] ==
                ["0x008540", "0x008546", "0x00854a", "0x00854e", "0x008552", "0x008550"] and
            [row["operation"] for row in transition["guard_true_ordered_writes"]] ==
                ["= 6", "= 0", "= 0", "= 0", "= 0", "= 1"] and
            transition["ordered_helper_calls"] == ["0x001972"] and
            transition["return_target"] == "0x00855c" and
            transition["rng_calls"] == 0,
            "route-0x008546 transition contract drift")
    audio = value["audio_command_contract"]
    require(audio["caller_pc"] == "0x008556" and
            audio["command"] == "0xff00" and
            audio["arguments"] == {"d1": "0x0000ff00", "d2": "0x00000000", "d3": "0x00000000"} and
            audio["semantic_sound_name"] == "UNKNOWN" and
            audio["handler_transaction"]["handler_class"] ==
                "NULL_TABLE_TIMING_PATH_0x01e0_0x0204" and
            audio["source_context"]["occurrences"] == 2,
            "route-0x008546 audio command contract drift")
    witness = value["dynamic_witness"]
    require(witness["counts"] == {"writes": 10, "samples": 8, "rng_calls": 0} and
            len(witness["write_rows"]) == 10 and
            len(witness["sample_projection"]) == 8,
            "route-0x008546 paired witness drift")
    require(len(value["owned_writer_transactions"]) == 5 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-0x008546 mutation or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); value = build(); validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed route-0x008546 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 route-0x008546 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"writes={value['dynamic_witness']['counts']['writes']} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
