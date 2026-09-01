#!/usr/bin/env python3
"""Build the bounded SPEC-02 failure/continue state-0 program at 0x008bb2."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "route_8546_spec", ROOT / "tools/build_spec02_route_8546_program.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
decoder = prior.base

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_encounter_route_authority.json"
HITKO = ROOT / "data/oracle11_predator_hitko_continue.json"
AUDIO = ROOT / "data/oracle11_global_audio_trigger_owners.json"
LOADS = ROOT / "data/oracle11_global_load_release_boundaries.json"
SEGMENTS = (
    ROOT / "data/oracle10_round1_census_extension_5567_6200.json",
    ROOT / "data/oracle10_round1_census_extension_12478_12799.json",
)
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_8bb2_program.json"

# The accepted writer-centered evidence begins inside the extension word of
# the aligned dispatcher instruction at 0x008ba0.  The state-0 target is
# 0x008bac.  State 2 targets 0x008d62 and is the separately declared 0x0090f2
# credited-continue program, so this artifact ends at that target.
PROGRAM_FIRST = 0x008B9C
DISPATCH_LAST_EXCLUSIVE = 0x008BA8
TABLE_FIRST = 0x008BA8
STATE0_FIRST = 0x008BAC
PROGRAM_LAST_EXCLUSIVE = 0x008D62
ACCEPTED_WINDOW = (0x008BA2, 0x008BD2)
OPCODE_SHA256 = decoder.OPCODE_SHA256
SOURCE_FRAMES = {6199, 12798}
WRITER_PCS = {
    "008bb2", "008bb6", "008bcc", "008c34", "008c38", "008c3e",
    "008c44", "008c48", "008c4c", "008c76", "008d28", "008d2e",
    "008d34", "008d3a", "008d40",
}
EXTERNAL_TRANSFER_OWNERS = {
    0x003BDC: "route-audio-command-0001-wrapper",
    0x008B48: "gfxram1-91c000-mask-pass",
    0x0090C8: "shared-route-mode-8-tail",
    0x00A6E2: "gfxram1-91e000-clear",
    0x00BAD6: "source-player-selection-transition-helper",
    0x016F8C: "gfxram1-910000-player-bank-init",
    0x01808A: "gfxram1-91c000-source-copy",
    0x07CEF0: "source-record-7300-dispatch",
    0x0A99C2: "source-presentation-reset",
    0x0B27C8: "gfxram1-914000-tile-copy",
    0x0B2CD6: "gfxram1-918000-palette-copy",
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


def decode_program(image: bytes) -> tuple[list[dict[str, object]],
                                           list[dict[str, object]]]:
    # Decode the dispatcher separately so its embedded two-word table is never
    # interpreted as executable code.  Decode state 0 through the exact state-2
    # target, then bind both table entries explicitly below.
    decoder.PROGRAM_FIRST = PROGRAM_FIRST
    decoder.PROGRAM_LAST_EXCLUSIVE = DISPATCH_LAST_EXCLUSIVE
    decoder.TABLES = {}
    decoder.COMPUTED_SITES = {0x008BA4: TABLE_FIRST}
    decoder.EXTERNAL_TRANSFER_OWNERS = {}
    dispatch_instructions, dispatch_decoded = decoder.decode_program(image)
    require(dispatch_decoded == [{}, []], "failure dispatcher decode drift")

    decoder.PROGRAM_FIRST = STATE0_FIRST
    decoder.PROGRAM_LAST_EXCLUSIVE = PROGRAM_LAST_EXCLUSIVE
    decoder.TABLES = {}
    decoder.COMPUTED_SITES = {}
    decoder.EXTERNAL_TRANSFER_OWNERS = EXTERNAL_TRANSFER_OWNERS
    state0_instructions, state0_decoded = decoder.decode_program(image)
    require(state0_decoded[0] == {}, "state-0 body invented computed dispatch")
    return dispatch_instructions + state0_instructions, state0_decoded[1]


def dynamic_witness(directory: Path) -> dict[str, object]:
    writes = [row for row in rows(directory / "route_writes.tsv")
              if int(row["frame"]) in SOURCE_FRAMES and
              row["pc"].lower() in WRITER_PCS]
    writes.sort(key=lambda row: (int(row["frame"]), int(row["pc"], 16)))
    samples = [row for row in rows(directory / "route_samples.tsv")
               if any(frame - 1 <= int(row["frame"]) <= frame + 2
                      for frame in SOURCE_FRAMES)]
    rng = [row for row in rows(directory / "route_rng.tsv")
           if PROGRAM_FIRST <= int(row["pc"], 16) < PROGRAM_LAST_EXCLUSIVE]
    expected_per_frame = [
        ("008bb2", "ff8008", "00000002"),
        ("008bb6", "ff800c", "00000000"),
        ("008bcc", "ff8248", "00000101"),
        ("008c34", "ff8032", "00000000"),
        ("008c38", "ff8036", "00000000"),
        ("008c3e", "ff8034", "00000300"),
        ("008c44", "ff8038", "00000700"),
        ("008c48", "ff8278", "00000000"),
        ("008c4c", "ff827c", "00000000"),
        ("008c76", "ff804a", "0000078f"),
        ("008d28", "ff8024", "00009100"),
        ("008d2e", "ff8026", "00009140"),
        ("008d34", "ff8028", "00009180"),
        ("008d3a", "ff802c", "000091c0"),
        ("008d40", "ff802a", "000091e0"),
    ]
    expected = [(str(frame), *item) for frame in sorted(SOURCE_FRAMES)
                for item in expected_per_frame]
    actual = [(row["frame"], row["pc"].lower(), row["address"].lower(),
               row["data"].lower()) for row in writes]
    require(actual == expected and len(samples) == 8 and not rng,
            "route-0x008bb2 paired witness drift")
    return {
        "counts": {"writes": len(writes), "samples": len(samples),
                   "rng_calls": 0},
        "semantic_sha256": {
            "writes": semantic(writes), "samples": semantic(samples),
            "rng": semantic(rng)},
        "write_rows": writes,
        "sample_projection": [{key: row[key] for key in
                               ("frame", "g8004", "g8008", "g800c", "g8010",
                                "g8014", "g8248", "player_active", "player_state",
                                "player_phase", "player_x", "player_z", "population")}
                              for row in samples],
        "reference_character_branch": {
            "selected_actor_mode_bit0": 0,
            "proof": "both executions take writer 0x008c76 and set g804a=0x078f; the bit-1 branch writes g804a=0x12cf at 0x008cda",
            "source_write_frames_u16": sorted(SOURCE_FRAMES),
        },
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and decoder.base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = decoder.base.load_json(ORACLE)
    hitko = decoder.base.load_json(HITKO)
    audio = decoder.base.load_json(AUDIO)
    loads = decoder.base.load_json(LOADS)
    segments = [decoder.base.load_json(path) for path in SEGMENTS]

    edges = [row for segment in segments for row in
             segment["route_authority_extension"]["route_state_edges"]
             if row["writer_pc"] == "0x008bb2"]
    require(len(edges) == 2 and
            [(row["write_frame"], row["sample_transition_frame"]) for row in edges]
            == [(6199, 6200), (12798, 12799)] and
            all(row["transition_guard"] ==
                "failure/continue dispatcher entered state 0" for row in edges) and
            all(row["source_window"] == {
                "first": "0x008ba2", "last_exclusive": "0x008bd2",
                "sha256": "9cd8ee473c743e3b0e3597b8cd5367ffa2b6a382702ad98130e1c48f05db753f"}
                for row in edges), "accepted route-0x008bb2 edge authority drift")
    require(hitko["failure_continue"]["failure_state"] == {
        "value": 2, "frame": 6200, "write_pc": "0x008bb2"} and
        hitko["failure_continue"]["rng_consumption"] == "none",
        "accepted failure/continue authority drift")

    transactions = [row for row in oracle["route_writer_transactions"]
                    if row["writer_pc"] in {f"0x{pc}" for pc in WRITER_PCS}]
    require(len(transactions) == 15 and all(
        row["classification"] == "SOURCE_CLOSED" and row["write_count"] == 2
        for row in transactions), "route-0x008bb2 writer ownership drift")

    audio_group = next(row for row in audio["trigger_groups"]
                       if row["command"] == "0x0001")
    audio_context = next(row for row in
                         audio_group["transition_guard"]["contexts"]
                         if row["caller_parent_return"] == "0x008bd4")
    require(audio_group["classification"] == "SOURCE_CLOSED" and
            audio_group["argument_variants"] ==
                [["00000001", "00000000", "00000000"]] and
            audio_context["first_frame"] == 6199 and
            audio_context["last_frame"] == 12798 and
            audio_context["occurrences"] == 2 and
            audio_context["source_call"]["address"] == "0x003c00",
            "route-0x008bb2 command-0x0001 ownership drift")

    load_boundaries = [row for row in loads["boundaries"]
                       if row["id"] in
                       ("route-load-release-6200", "route-load-release-12799")]
    load_boundaries.sort(key=lambda row: row["visible_boundary_frame"])
    require(len(load_boundaries) == 2 and
            [row["source_write_frame"] for row in load_boundaries] ==
                [6199, 12798] and
            all(row["classification"] == "SOURCE_CLOSED" and
                row["package_identity"]["region"] == "gfxram1" and
                row["package_identity"]["write_count"] == 8960 and
                len(row["loader_callers"]) == 17
                for row in load_boundaries),
            "route-0x008bb2 load boundary ownership drift")

    image = OPCODES.read_bytes()
    require(hashlib.sha256(image[ACCEPTED_WINDOW[0]:ACCEPTED_WINDOW[1]]).hexdigest()
            == "9cd8ee473c743e3b0e3597b8cd5367ffa2b6a382702ad98130e1c48f05db753f",
            "route-0x008bb2 accepted centered source window drift")
    require(image[TABLE_FIRST:STATE0_FIRST].hex() == "000401ba",
            "failure/continue dispatcher table drift")
    instructions, external = decode_program(image)
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-0x008bb2 witness drift")

    return {
        "schema": "spec02-route-8bb2-state0-whole-program-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "aligned failure/continue dispatcher plus every state-0 branch through the separately owned state-2 target",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": decoder.base.sha256(ORACLE),
            "hitko_artifact": HITKO.relative_to(ROOT).as_posix(),
            "hitko_sha256": decoder.base.sha256(HITKO),
            "audio_artifact": AUDIO.relative_to(ROOT).as_posix(),
            "audio_sha256": decoder.base.sha256(AUDIO),
            "load_artifact": LOADS.relative_to(ROOT).as_posix(),
            "load_sha256": decoder.base.sha256(LOADS),
            "segment_artifacts": [{"path": path.relative_to(ROOT).as_posix(),
                                   "sha256": decoder.base.sha256(path)}
                                  for path in SEGMENTS],
            "entry": "0x008b9c", "writer_pc": "0x008bb2",
            "program_window": ["0x008b9c", "0x008d62"],
            "program_window_sha256": hashlib.sha256(
                image[PROGRAM_FIRST:PROGRAM_LAST_EXCLUSIVE]).hexdigest(),
            "accepted_writer_centered_window": ["0x008ba2", "0x008bd2"],
            "accepted_writer_centered_window_sha256":
                "9cd8ee473c743e3b0e3597b8cd5367ffa2b6a382702ad98130e1c48f05db753f",
            "alignment_note": "0x008ba2 is the extension word of aligned instruction 0x008ba0; executable decoding starts at 0x008b9c and skips the embedded table at 0x008ba8..0x008bac",
        },
        "dispatcher_contract": {
            "state_field": "g8008:s16 read as raw u16 table offset",
            "table_address": "0x008ba8", "table_bytes": "000401ba",
            "entries": [
                {"state_u16": 0, "offset_s16": 4, "target": "0x008bac",
                 "ownership": "this artifact"},
                {"state_u16": 2, "offset_s16": 442, "target": "0x008d62",
                 "ownership": "next P3 credited-continue program at writer 0x0090f2"},
            ],
            "current_body_guard": "u16(g8008) == 0",
            "deferred_target_is_not_decoded_here": True,
        },
        "scheduler_contract": {
            "caller_chain": ["0x0080a2", "0x000000", "0x000000"],
            "source_write_frames_u16": [6199, 12798],
            "visible_transition_frames_u16": [6200, 12799],
            "order": "main route controller dispatches state 0; route/audio setup precedes player-selection writes, the complete gfxram1 transaction, destination-base publication, presentation reset, and the guard-controlled return",
        },
        "field_types": {
            "g8008": "route_state_s16/raw_u16_dispatch_offset",
            "g800c": "route_substate_u16", "g9084": "continue_mode_u16",
            "g7300_g7304": "route_scratch_u32", "g90e8": "audio_latch_u16",
            "g8248": "route_transition_latch_u8", "g81d3": "player_selection_bits_u8",
            "g81c8": "player_mode_u16", "g9082": "selected_actor_pointer_low_u16",
            "selected_actor_d1": "selection_bit_index_u8",
            "selected_actor_d2": "presentation_mode_flags_u8",
            "selected_actor_da_dc_de": "presentation_fields_u8",
            "g908e_g9090_g9092_g9094": "saved_route_coordinates_s16",
            "g8032_g8034_g8036_g8038": "route_view_coordinates_s16",
            "g8278_g827c": "source_visible_camera_coordinates_s16",
            "g7303": "reference_character_load_variant_u8",
            "g908c_g804a": "saved_and_active_presentation_index_u16",
            "g908a": "load_complete_latch_u16",
            "g8024_g8026_g8028_g802a_g802c": "gfxram1_destination_high_word_u16",
            "g81be": "post_load_route_guard_u8",
        },
        "transition_contract": {
            "guard": "u16(g8008) == 0",
            "entry_ordered_writes": [
                {"pc": "0x008bb2", "field": "g8008:s16", "operation": "+= 2", "observed": "0->2"},
                {"pc": "0x008bb6", "field": "g800c:u16", "operation": "= 0"},
                {"pc": "0x008bb4", "field": "g9084:u16", "operation": "= 0"},
                {"pc": "0x008bb8", "field": "g7300:u32", "operation": "= 0"},
                {"pc": "0x008bbc", "field": "g7304:u32", "operation": "= 0"},
                {"pc": "0x008bc0", "field": "g90e8:u16", "operation": "= 1"},
                {"pc": "0x008bcc", "field": "g8248:u8", "operation": "= 1"},
            ],
            "player_selection_loop": {
                "iterations": 3, "first_record": "0xff8380", "stride_bytes": 256,
                "guard": "btst u8(actor+0xd1), u8(g81d3)",
                "selected_writes": ["g9082=low16(actor)", "actor+0xda:u8=1",
                                    "actor+0xdc:u8=0x21", "actor+0xde:u8=0x15"],
                "mode_2_override": "if u16(g81c8)==2 then actor+0xdc=0x31 and actor+0xde=0x1f",
            },
            "route_coordinate_writes": [
                "g908e=s16(g8278)", "g9090=s16(g827c)",
                "g9092=s16(g82f8)", "g9094=s16(g82fc)",
                "g8032=0", "g8036=0", "g8034=0x0300", "g8038=0x0700",
                "g8278=0", "g827c=0"],
            "selected_actor_mode_branches": {
                "guard": "u8(selected_actor+0xd2) & 1",
                "bit0_clear_reference_path": {
                    "writes": ["g7303:u8=1", "g908c:u16=g804a", "g804a:u16=0x078f"],
                    "tile_selectors_u16": [285, 286],
                    "palette_selectors_u16": [0, 0],
                },
                "bit0_set_static_path": {
                    "writes": ["g7303:u8=0", "g800c:u16+=2", "g9084:u16+=2",
                               "g908c:u16=g804a", "g804a:u16=0x12cf"],
                    "tile_selectors_u16": [0, 0],
                    "palette_selectors_u16": [102, 103],
                },
            },
            "common_destination_writes": [
                {"pc": "0x008d1c", "field": "g908a:u16", "operation": "= 1"},
                {"pc": "0x008d22", "field": "g8024:u16", "operation": "= 0x9100"},
                {"pc": "0x008d28", "field": "g8026:u16", "operation": "= 0x9140"},
                {"pc": "0x008d2e", "field": "g8028:u16", "operation": "= 0x9180"},
                {"pc": "0x008d34", "field": "g802c:u16", "operation": "= 0x91c0"},
                {"pc": "0x008d3a", "field": "g802a:u16", "operation": "= 0x91e0"},
            ],
            "post_load_guard": {
                "guard": "u8(g81be) != 0",
                "true": "return at 0x008d60",
                "false": "call 0x008b48 then tail-branch 0x0090c8",
            },
            "rng_calls": 0,
        },
        "audio_command_contract": {
            "owner": "route", "caller_pc": "0x008bce",
            "source_wrapper_entry": "0x003bdc", "source_owner_return": "0x008bd4",
            "command": "0x0001",
            "arguments": {"d1": "0x00000001", "d2": "0x00000000", "d3": "0x00000000"},
            "semantic_sound_name": "UNKNOWN",
            "handler_transaction": audio_group["handler_transaction"],
            "source_context": audio_context,
        },
        "load_release_contract": {
            "classification": "SOURCE_CLOSED",
            "semantic_package_name": "UNKNOWN",
            "transaction_grouping": "all source writes owned by one state-0 program execution form one logical gfxram1 load; individual writes are not independent load events",
            "boundaries": load_boundaries,
            "source_call_order": ["0x00a6e2", "0x01808a", "0x016f8c",
                                  "0x00bad6", "0x0b27c8", "0x0b27c8",
                                  "0x0b2cd6", "0x0b2cd6", "0x07cef0",
                                  "0x0a99c2"],
            "reference_path_package_sha256":
                "02fd861bf661a94320e84030c5f42901373cae22e739d9579158430d5336a836",
            "reference_path_transaction_sha256":
                "47d5ee64e221e7d1139027630492c2334ed612250557dc2cdea6dbbc8351dd61",
        },
        "helper_contracts": {
            "0x003bdc": "source route command-0x0001 wrapper bound by audio_command_contract",
            "0x00a6e2": "zero 0x91e000..0x91fffe before later package publication",
            "0x01808a": "source copy into 0x91c000/0x91c400/0x91c800/0x91cc00",
            "0x016f8c": "source player-bank initialization beginning at 0x910000",
            "0x00bad6": "source player-selection transition helper; preserve exact call position and global inputs",
            "0x0b27c8": "source tile-indexed copy into 0x914000 and 0x914400",
            "0x0b2cd6": "source palette-indexed copy into 0x918000 and 0x918100",
            "0x07cef0": "source dispatch of scratch record g7300 with d0=0",
            "0x0a99c2": "source presentation reset after destination-base publication",
            "0x008b48": "conditional mask pass over 0x91c000/0x91c800/0x91cc00",
            "0x0090c8": "conditional shared tail setting route mode 8 and clearing route substates",
        },
        "owned_writer_transactions": transactions,
        "normalized_source_program": {
            "representation": "aligned dispatcher plus bounded state-0 68000 operations with exact widths, reads, writes, branches and external transfers; translate to portable C, never interpret at runtime",
            "instruction_count": len(instructions),
            "instructions_sha256": hashlib.sha256(
                decoder.base.canonical(instructions)).hexdigest(),
            "instructions": instructions,
            "field_access_profiles": decoder.field_profiles(instructions),
            "external_transfers": external,
        },
        "dynamic_witness": witness_a,
        "paired_capture_identity": [segment["paired_capture_ceremony"]
                                    for segment in segments],
        "counterfactuals": {
            "route_wide_perturbation":
                segments[0]["route_authority_extension"]["route_wide_perturbation"],
            "failure_continue": hitko["counterfactuals"],
            "audio_command_suppression": audio_group["handler_transaction"]["causal_control"],
            "load_suppressions": [row["failure_control"] for row in load_boundaries],
        },
        "mutation_controls": {
            "misaligned_writer_window_decode_rejected": True,
            "dispatcher_table_offset_or_target_mutation_rejected": True,
            "state0_vs_state2_dispatch_mutation_rejected": True,
            "route_write_width_order_or_value_mutation_rejected": True,
            "player_selection_iteration_guard_or_stride_mutation_rejected": True,
            "reference_character_branch_selector_mutation_rejected": True,
            "alternate_branch_tile_or_palette_selector_mutation_rejected": True,
            "audio_command_or_argument_mutation_rejected": True,
            "audio_handler_suppression_is_discriminating": True,
            "load_helper_order_or_destination_mutation_rejected": True,
            "load_suppression_is_discriminating": True,
            "post_load_guard_or_tail_mutation_rejected": True,
            "invented_rng_call_rejected": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False,
            "individual_gfx_writes_are_logical_load_events": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "route-0x008bb2 status drift")
    source = value["source_identity"]
    require(source["program_window"] == ["0x008b9c", "0x008d62"] and
            source["program_window_sha256"] ==
                "74c7accc79c48dbc9ee7977bb3dfc850203fb3c8b5675b63926e6f78ee4768bc" and
            source["accepted_writer_centered_window_sha256"] ==
                "9cd8ee473c743e3b0e3597b8cd5367ffa2b6a382702ad98130e1c48f05db753f",
            "route-0x008bb2 source window drift")
    dispatch = value["dispatcher_contract"]
    require(dispatch["table_bytes"] == "000401ba" and
            dispatch["entries"] == [
                {"state_u16": 0, "offset_s16": 4, "target": "0x008bac",
                 "ownership": "this artifact"},
                {"state_u16": 2, "offset_s16": 442, "target": "0x008d62",
                 "ownership": "next P3 credited-continue program at writer 0x0090f2"}] and
            dispatch["deferred_target_is_not_decoded_here"] is True,
            "route-0x008bb2 dispatcher contract drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 95 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "ecd88f48fe728e0288a808109c1ce79523341181b0999bfbb61e9fc593d2c0ea" and
            len(program["field_access_profiles"]) == 39 and
            len(program["external_transfers"]) == 11 and
            not any(row["owner"].startswith("UNKNOWN")
                    for row in program["external_transfers"]),
            "route-0x008bb2 aligned program closure incomplete")
    transition = value["transition_contract"]
    require(transition["guard"] == "u16(g8008) == 0" and
            [row["pc"] for row in transition["entry_ordered_writes"]] ==
                ["0x008bb2", "0x008bb6", "0x008bb4", "0x008bb8",
                 "0x008bbc", "0x008bc0", "0x008bcc"] and
            [row["operation"] for row in transition["entry_ordered_writes"]] ==
                ["+= 2", "= 0", "= 0", "= 0", "= 0", "= 1", "= 1"] and
            transition["player_selection_loop"]["iterations"] == 3 and
            transition["selected_actor_mode_branches"]
                ["bit0_clear_reference_path"]["tile_selectors_u16"] == [285, 286] and
            transition["selected_actor_mode_branches"]
                ["bit0_set_static_path"]["palette_selectors_u16"] == [102, 103] and
            transition["post_load_guard"] == {
                "guard": "u8(g81be) != 0", "true": "return at 0x008d60",
                "false": "call 0x008b48 then tail-branch 0x0090c8"} and
            transition["rng_calls"] == 0,
            "route-0x008bb2 transition contract drift")
    audio = value["audio_command_contract"]
    require(audio["caller_pc"] == "0x008bce" and
            audio["command"] == "0x0001" and
            audio["handler_transaction"]["handler_class"] ==
                "GLOBAL_STATE_RESET_0x048d" and
            audio["source_context"]["occurrences"] == 2,
            "route-0x008bb2 audio contract drift")
    load = value["load_release_contract"]
    require(len(load["boundaries"]) == 2 and
            [row["visible_boundary_frame"] for row in load["boundaries"]] ==
                [6200, 12799] and
            all(row["package_identity"]["write_count"] == 8960
                for row in load["boundaries"]) and
            load["reference_path_transaction_sha256"] ==
                "47d5ee64e221e7d1139027630492c2334ed612250557dc2cdea6dbbc8351dd61",
            "route-0x008bb2 load contract drift")
    witness = value["dynamic_witness"]
    require(witness["counts"] == {"writes": 30, "samples": 8, "rng_calls": 0} and
            len(witness["write_rows"]) == 30 and
            witness["reference_character_branch"]["selected_actor_mode_bit0"] == 0,
            "route-0x008bb2 paired witness drift")
    require(len(value["owned_writer_transactions"]) == 15 and
            len(value["helper_contracts"]) == 11 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-0x008bb2 ownership or implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed route-0x008bb2 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 route-0x008bb2 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"writes={value['dynamic_witness']['counts']['writes']} "
          f"loads={len(value['load_release_contract']['boundaries'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
