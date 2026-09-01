#!/usr/bin/env python3
"""Build the bounded SPEC-02 credited-continue state-2 program at 0x0090f2."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "route_8bb2_spec", ROOT / "tools/build_spec02_route_8bb2_program.py")
prior = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(prior)
decoder = prior.decoder

OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
ORACLE = ROOT / "data/oracle11_round1_encounter_route_authority.json"
HITKO = ROOT / "data/oracle11_predator_hitko_continue.json"
AUDIO = ROOT / "data/oracle11_global_audio_trigger_owners.json"
SEGMENTS = (
    ROOT / "data/oracle10_round1_census_extension_6201_6692.json",
    ROOT / "data/oracle10_round1_census_extension_12800_13292.json",
)
CAPTURE_A = ROOT / ".deps/mame/oracle11_round1_route_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_round1_route_b"
OUT = ROOT / "data/spec02_route_90f2_program.json"

OPCODE_SHA256 = decoder.OPCODE_SHA256
PROGRAM_SHA256 = "0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9"
PROGRAM_FIRST = 0x008D62
PROGRAM_LAST_EXCLUSIVE = 0x009144
ACCEPTED_WINDOW = (0x0090E2, 0x009112)
SOURCE_FRAMES = {6691, 13291}
WRITER_PCS = {
    "0090ec", "0090f2", "0090f8", "0090fc", "009100", "009104",
    "00910a", "009110", "009116", "00911c", "009128", "009132",
}
ROUTE_OWNER_PCS = {f"0x{pc}" for pc in WRITER_PCS} | {
    "0x017066", "0x01706c", "0x017072", "0x017078", "0x01707e"}

SLICES = (
    (0x008D62, 0x008D8C, {}, {0x008D82: 0x008D8C,
                               0x008D86: 0x00BAD6}, {
         0x0090C8: "whole-program route-mode-8 tail",
         0x0090E6: "whole-program credited-restore body",
         0x00BAD6: "source-player-selection-transition-helper",
     }),
    (0x008D90, 0x008DD8, {}, {}, {
         0x008F56: "whole-program 5x5 presentation-grid helper",
         0x0090C8: "whole-program route-mode-8 tail",
         0x07CEF0: "source-record-7300-dispatch",
         0x0A99C2: "source-presentation-reset",
     }),
    (0x008DF8, 0x008E76, {}, {}, {
         0x0090C8: "whole-program route-mode-8 tail",
         0x07CEF0: "source-record-7300-dispatch",
         0x0A99C2: "source-presentation-reset",
     }),
    (0x008F56, 0x008F8E, {}, {}, {}),
    (0x0090C8, 0x0090E6, {}, {}, {}),
    (0x0090E6, 0x009144, {}, {}, {
         0x0088EA: "credited-continue presentation/audio helper command-0x000f",
         0x01705C: "route destination-base restore helper",
         0x0ADD2C: "credited-continue route presentation helper",
         0x0A99C2: "source-presentation-reset",
     }),
)


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


def source_table(image: bytes, first: int, last: int, view: str,
                 element: str) -> dict[str, object]:
    payload = image[first:last]
    return {
        "source_view": view, "first": f"0x{first:06x}",
        "last_exclusive": f"0x{last:06x}", "element_type": element,
        "byte_count": len(payload), "bytes_hex": payload.hex(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def decode_program(image: bytes) -> tuple[list[dict[str, object]],
                                           list[dict[str, object]],
                                           dict[str, object]]:
    instructions = []
    external = []
    dispatch = {}
    for first, last, tables, computed, owners in SLICES:
        decoder.PROGRAM_FIRST, decoder.PROGRAM_LAST_EXCLUSIVE = first, last
        decoder.TABLES, decoder.COMPUTED_SITES = tables, computed
        decoder.EXTERNAL_TRANSFER_OWNERS = owners
        body, (body_dispatch, body_external) = decoder.decode_program(image)
        instructions.extend(body)
        external.extend(body_external)
        dispatch.update(body_dispatch)
    instructions.sort(key=lambda row: int(row["pc"], 16))
    return instructions, external, dispatch


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
    per_frame = {
        6691: [("0090ec", "ff8004", "00000004"),
               ("0090f2", "ff8008", "00000004"),
               ("0090f8", "ff800c", "00000000"),
               ("0090fc", "ff8010", "00000000"),
               ("009100", "ff8014", "00000000"),
               ("009104", "ff804a", "000012cf"),
               ("00910a", "ff8278", "00000400"),
               ("009110", "ff827c", "000000e0"),
               ("009116", "ff82f8", "00000200"),
               ("00911c", "ff82fc", "000000c0"),
               ("009128", "ff81d6", "00000000"),
               ("009132", "ff8240", "00000101")],
        13291: [("0090ec", "ff8004", "00000004"),
                ("0090f2", "ff8008", "00000004"),
                ("0090f8", "ff800c", "00000000"),
                ("0090fc", "ff8010", "00000000"),
                ("009100", "ff8014", "00000000"),
                ("009104", "ff804a", "000012cf"),
                ("00910a", "ff8278", "00000400"),
                ("009110", "ff827c", "000000d0"),
                ("009116", "ff82f8", "00000200"),
                ("00911c", "ff82fc", "000000b0"),
                ("009128", "ff81d6", "00000000"),
                ("009132", "ff8240", "00000101")],
    }
    expected = [(str(frame), *item) for frame in sorted(per_frame)
                for item in per_frame[frame]]
    actual = [(row["frame"], row["pc"].lower(), row["address"].lower(),
               row["data"].lower()) for row in writes]
    require(actual == expected and len(samples) == 8 and not rng,
            "route-0x0090f2 paired witness drift")
    return {
        "counts": {"writes": len(writes), "samples": len(samples),
                   "rng_calls": 0},
        "semantic_sha256": {"writes": semantic(writes),
                            "samples": semantic(samples), "rng": semantic(rng)},
        "write_rows": writes,
        "sample_projection": [{key: row[key] for key in
            ("frame", "g8004", "g8008", "g800c", "g8010", "g8014",
             "g8248", "player_active", "player_state", "player_phase",
             "player_x", "player_z", "population")} for row in samples],
    }


def build() -> dict[str, object]:
    require(OPCODES.is_file() and decoder.base.sha256(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    require(PROGRAM.is_file() and decoder.base.sha256(PROGRAM) == PROGRAM_SHA256,
            "accepted decrypted program-data image missing or drifted")
    oracle = decoder.base.load_json(ORACLE)
    hitko = decoder.base.load_json(HITKO)
    audio = decoder.base.load_json(AUDIO)
    segments = [decoder.base.load_json(path) for path in SEGMENTS]
    edges = [row for segment in segments for row in
             segment["route_authority_extension"]["route_state_edges"]
             if row["writer_pc"] == "0x0090f2"]
    require([(row["write_frame"], row["sample_transition_frame"]) for row in edges]
            == [(6691, 6692), (13291, 13292)] and
            all(row["transition_guard"] ==
                "credited continue restore dispatcher entered state 2"
                for row in edges) and all(row["source_window"] == {
                    "first": "0x0090e2", "last_exclusive": "0x009112",
                    "sha256": "407c340e5ed1daf8c1a19d3642f4b538e3daa5da4b31cf08f7e4ee12eedccad4"}
                for row in edges), "accepted route-0x0090f2 edge drift")
    require(hitko["failure_continue"]["credited_start"] == {
        "value": 4, "frame": 6692, "write_pc": "0x0090f2"} and
        hitko["failure_continue"]["rng_consumption"] == "none",
        "accepted credited-continue authority drift")
    transactions = [row for row in oracle["route_writer_transactions"]
                    if row["writer_pc"] in ROUTE_OWNER_PCS]
    require(len(transactions) == 17 and all(
        row["classification"] == "SOURCE_CLOSED" and row["write_count"] == 2
        for row in transactions), "route-0x0090f2 writer ownership drift")
    audio_group = next(row for row in audio["trigger_groups"]
                       if row["command"] == "0x000f")
    audio_context = next(row for row in
                         audio_group["transition_guard"]["contexts"]
                         if row["caller_parent_return"] == "0x009138")
    require(audio_group["classification"] == "SOURCE_CLOSED" and
            audio_group["argument_variants"] ==
                [["0000000f", "00000000", "00000000"]] and
            audio_context["first_frame"] == 6691 and
            audio_context["last_frame"] == 13291 and
            audio_context["occurrences"] == 2,
            "route-0x0090f2 command-0x000f ownership drift")

    opcodes = OPCODES.read_bytes()
    program = PROGRAM.read_bytes()
    require(hashlib.sha256(opcodes[ACCEPTED_WINDOW[0]:ACCEPTED_WINDOW[1]]).hexdigest()
            == "407c340e5ed1daf8c1a19d3642f4b538e3daa5da4b31cf08f7e4ee12eedccad4",
            "route-0x0090f2 accepted source window drift")
    instructions, external, dispatch = decode_program(opcodes)
    witness_a = dynamic_witness(CAPTURE_A)
    witness_b = dynamic_witness(CAPTURE_B)
    require(witness_a == witness_b, "paired route-0x0090f2 witness drift")

    substate_offsets = [int.from_bytes(opcodes[a:a + 2], "big", signed=True)
                        for a in range(0x008D8C, 0x008D90, 2)]
    variant_offsets = [int.from_bytes(opcodes[a:a + 1], "big", signed=True)
                       for a in range(0x008DD8, 0x008DF8)]
    palette_a = [int.from_bytes(program[a:a + 2], "big")
                 for a in range(0x008E76, 0x008EB6, 2)]
    palette_b = [int.from_bytes(program[a:a + 2], "big")
                 for a in range(0x008EB6, 0x008EF6, 2)]
    grid_offsets = [int.from_bytes(opcodes[a:a + 2], "big")
                    for a in range(0x008F8E, 0x008FCE, 2)]
    return {
        "schema": "spec02-route-90f2-state2-whole-program-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "every Round 1-reachable state-2 dispatcher, substate, table-driven presentation and credited-continue restore branch",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "program_data_sha256": PROGRAM_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": decoder.base.sha256(ORACLE),
            "hitko_artifact": HITKO.relative_to(ROOT).as_posix(),
            "hitko_sha256": decoder.base.sha256(HITKO),
            "audio_artifact": AUDIO.relative_to(ROOT).as_posix(),
            "audio_sha256": decoder.base.sha256(AUDIO),
            "segment_artifacts": [{"path": path.relative_to(ROOT).as_posix(),
                                   "sha256": decoder.base.sha256(path)}
                                  for path in SEGMENTS],
            "entry": "0x008d62", "writer_pc": "0x0090f2",
            "program_window": ["0x008d62", "0x009144"],
            "executable_slices": [[f"0x{a:06x}", f"0x{b:06x}"]
                                  for a, b, _t, _c, _o in SLICES],
            "accepted_writer_centered_window": ["0x0090e2", "0x009112"],
            "accepted_writer_centered_window_sha256":
                "407c340e5ed1daf8c1a19d3642f4b538e3daa5da4b31cf08f7e4ee12eedccad4",
        },
        "dispatch_contract": {
            "route_state_guard": "u16(g8008) == 2 selects this body from the outer dispatcher",
            "entry_guards_in_order": [
                {"guard": "u8(g81bf) == 0", "target": "0x0090c8 route-mode-8 tail"},
                {"guard": "u8(g81d4) != 0", "target": "0x0090e6 credited restore"},
                {"guard": "u8(g81af) != 0", "target": "0x0090e6 credited restore"},
                {"guard": "otherwise", "target": "g800c substate dispatch"},
            ],
            "substate_table": {"table_base": "0x008d8c", "entry_count": 2,
                               "targets": ["0x008d90", "0x008df8"]},
            "substate_offsets_s16": substate_offsets,
            "substate_targets": ["0x008d90", "0x008df8"],
        },
        "table_contracts": {
            "variant_copy_offset_s8": {
                **source_table(opcodes, 0x008DD8, 0x008DF8,
                               "accepted decrypted opcode image", "s8"),
                "values": variant_offsets,
                "selection": "s8(selected_actor+0xde) indexes 32 entries; negative selected value routes to mode-8 tail; selected offset adds to source base 0x009144 and copies eight u32 words with F000F000 OR mask to 0x91c900",
            },
            "palette_group_a_offsets_u16": {
                **source_table(program, 0x008E76, 0x008EB6,
                               "accepted decrypted program-data image", "u16_be"),
                "values": palette_a,
                "resolved_record_bases": [f"0x{0x008E76 + value:06x}" for value in palette_a],
            },
            "palette_group_b_offsets_u16": {
                **source_table(program, 0x008EB6, 0x008EF6,
                               "accepted decrypted program-data image", "u16_be"),
                "values": palette_b,
                "resolved_record_bases": [f"0x{0x008EB6 + value:06x}" for value in palette_b],
            },
            "palette_records": source_table(
                program, 0x008EF6, 0x008F56,
                "accepted decrypted program-data image", "eight 3xpair<u16_be> records"),
            "grid_offsets_u16": {
                **source_table(opcodes, 0x008F8E, 0x008FCE,
                               "accepted decrypted opcode image", "u16_be"),
                "values": grid_offsets,
                "resolved_record_bases": [f"0x{0x008F8E + value:06x}" for value in grid_offsets],
            },
            "grid_records": source_table(
                program, 0x008FCE, 0x0090C8,
                "accepted decrypted program-data image", "five 5x5 u16_be records"),
            "selection": "selected_actor+0xde indexes all 32-entry tables; substate0 uses variant copy plus grid record; substate2 copies three value pairs from each palette group with constant selector 2 and 0x20-byte destination stride",
        },
        "transition_contract": {
            "mode8_tail": {
                "entry": "0x0090c8", "writes": ["g8004:u16=8", "g8008:u16=0",
                    "g800c:u16=0", "g8010:u16=0", "g8014:u16=0", "g8220:u8=1"]},
            "credited_restore": {
                "entry": "0x0090e6",
                "ordered_writes": ["g8004:u16=4", "g8008:s16=4", "g800c:u16=0",
                    "g8010:u16=0", "g8014:u16=0", "g804a:u16=g908c",
                    "g8278:s16=g908e", "g827c:s16=g9090", "g82f8:s16=g9092",
                    "g82fc:s16=g9094", "call 0x01705c restores g8024..g802c",
                    "g81d6:u8=0", "g90e8:u16=1", "g8240:u8=1",
                    "call 0x0088ea", "call 0x0add2c", "tail 0x0a99c2"],
                "destination_bases_u16": [0x9000, 0x9040, 0x9080, 0x90c0, 0x90e0],
                "load_rule": "destination ownership is restored without a new logical data load or release boundary",
            },
            "source_write_frames_u16": [6691, 13291],
            "visible_transition_frames_u16": [6692, 13292],
            "rng_calls": 0,
        },
        "audio_command_contract": {
            "owner": "route", "caller_pc": "0x009132",
            "source_helper_entry": "0x0088ea", "source_owner_return": "0x009138",
            "command": "0x000f",
            "arguments": {"d1": "0x0000000f", "d2": "0x00000000", "d3": "0x00000000"},
            "semantic_sound_name": "UNKNOWN",
            "handler_transaction": audio_group["handler_transaction"],
            "source_context": audio_context,
        },
        "field_types": {
            "g8004_g8008_g800c_g8010_g8014": "route words; g8008 is signed state and raw dispatch offset",
            "g81bf_g81d4_g81af": "ordered route guards_u8",
            "g9082": "selected_actor_pointer_low_u16",
            "selected_actor_de": "signed presentation selector_s8",
            "g908c_g804a": "saved_active_presentation_index_u16",
            "g908e_g9090_g9092_g9094": "saved_route_coordinates_s16",
            "g8278_g827c_g82f8_g82fc": "restored_route_coordinates_s16",
            "g8024_g8026_g8028_g802a_g802c": "destination_base_high_word_u16",
            "g81d6_g8220_g8240": "route_latches_u8", "g90e8": "audio_latch_u16",
        },
        "helper_contracts": {
            "0x00bad6": "source player-selection transition helper after substate dispatch",
            "0x07cef0": "source dispatch of scratch record g7300 with d0=0",
            "0x0a99c2": "source presentation reset/tail",
            "0x01705c": "restore destination base high words 0x9000..0x90e0",
            "0x0088ea": "credited-continue presentation/audio helper owning command 0x000f",
            "0x0add2c": "credited-continue route presentation helper",
        },
        "owned_writer_transactions": transactions,
        "normalized_source_program": {
            "representation": "six bounded executable slices plus exact read-only source tables; translate to portable C, never interpret at runtime",
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
            "failure_continue": hitko["counterfactuals"],
            "audio_command_suppression": audio_group["handler_transaction"]["causal_control"],
            "route_perturbation": segments[0]["route_authority_extension"]["route_wide_perturbation"],
        },
        "mutation_controls": {
            "wrong_outer_or_substate_dispatch_rejected": True,
            "guard_order_polarity_or_field_mutation_rejected": True,
            "table_source_view_offset_or_payload_mutation_rejected": True,
            "variant_selector_signedness_or_range_mutation_rejected": True,
            "copy_count_stride_mask_or_destination_mutation_rejected": True,
            "route_write_width_order_value_or_field_mutation_rejected": True,
            "saved_coordinate_or_destination_restore_mutation_rejected": True,
            "invented_load_boundary_rejected": True,
            "audio_command_argument_or_caller_mutation_rejected": True,
            "audio_suppression_is_discriminating": True,
            "fixed_frame_or_invented_rng_mutation_rejected": True,
            "paired_semantic_witness_required": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False,
            "logical_load_on_credited_restore": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "route-0x0090f2 status drift")
    source = value["source_identity"]
    require(source["program_window"] == ["0x008d62", "0x009144"] and
            source["accepted_writer_centered_window_sha256"] ==
                "407c340e5ed1daf8c1a19d3642f4b538e3daa5da4b31cf08f7e4ee12eedccad4" and
            len(source["executable_slices"]) == 6,
            "route-0x0090f2 source boundary drift")
    require(value["dispatch_contract"]["substate_offsets_s16"] == [4, 108] and
            value["dispatch_contract"]["substate_targets"] ==
                ["0x008d90", "0x008df8"] and
            value["dispatch_contract"]["entry_guards_in_order"] == [
                {"guard": "u8(g81bf) == 0", "target": "0x0090c8 route-mode-8 tail"},
                {"guard": "u8(g81d4) != 0", "target": "0x0090e6 credited restore"},
                {"guard": "u8(g81af) != 0", "target": "0x0090e6 credited restore"},
                {"guard": "otherwise", "target": "g800c substate dispatch"}],
            "state-2 dispatch drift")
    tables = value["table_contracts"]
    expected_hashes = {
        "variant_copy_offset_s8": "f037f42dce66710e1e635b121a9ab6e00373cbee814b9796332955c55747a48b",
        "palette_group_a_offsets_u16": "442062481d47b7f83e8295e1cf7cae9f9e5abeb89ce63596e5503fc984b1bd75",
        "palette_group_b_offsets_u16": "9103943630c24712035f3df601108e07bc608095799b0ce22774c51a438630b7",
        "palette_records": "fed7e5acdac65d88a522e10838fa26bf6cba24b2deb0eb7ca9340a1db8ccc4a5",
        "grid_offsets_u16": "2ee528c86bc271ba108431a1f163f35f0b4c958a6e1395ed9125d0f6b64b55ff",
        "grid_records": "1dcea3dbff907b813b3a304ed6b46ec7e2a731a623de534a6a2cc79dc2e35488",
    }
    require(all(tables[name]["sha256"] == expected and
                hashlib.sha256(bytes.fromhex(tables[name]["bytes_hex"])).hexdigest()
                    == expected for name, expected in expected_hashes.items()),
            "route-0x0090f2 source-table identity drift")
    require(len(tables["variant_copy_offset_s8"]["values"]) == 32 and
            tables["variant_copy_offset_s8"]["values"] == [
                int.from_bytes(bytes([value]), "big", signed=True) for value in
                bytes.fromhex(tables["variant_copy_offset_s8"]["bytes_hex"])] and
            len(tables["palette_group_a_offsets_u16"]["values"]) == 32 and
            len(tables["palette_group_b_offsets_u16"]["values"]) == 32 and
            len(tables["grid_offsets_u16"]["values"]) == 32 and
            tables["palette_records"]["byte_count"] == 96 and
            tables["grid_records"]["byte_count"] == 250,
            "route-0x0090f2 table closure drift")
    restore = value["transition_contract"]["credited_restore"]
    require(restore["destination_bases_u16"] ==
            [0x9000, 0x9040, 0x9080, 0x90c0, 0x90e0] and
            restore["ordered_writes"][:5] == ["g8004:u16=4", "g8008:s16=4",
                "g800c:u16=0", "g8010:u16=0", "g8014:u16=0"] and
            value["transition_contract"]["mode8_tail"]["writes"] == [
                "g8004:u16=8", "g8008:u16=0", "g800c:u16=0", "g8010:u16=0",
                "g8014:u16=0", "g8220:u8=1"] and
            value["transition_contract"]["rng_calls"] == 0 and
            value["implementation_rules"]["logical_load_on_credited_restore"] is False,
            "credited restore semantics drift")
    audio = value["audio_command_contract"]
    require(audio["caller_pc"] == "0x009132" and
            audio["source_owner_return"] == "0x009138" and
            audio["command"] == "0x000f" and
            audio["handler_transaction"]["handler_class"] ==
                "GLOBAL_STATE_RESET_0x048d", "credited audio ownership drift")
    program = value["normalized_source_program"]
    require(program["instruction_count"] == 101 and
            program["instruction_count"] == len(program["instructions"]) and
            program["instructions_sha256"] ==
                "4e6b36dca895af1e7222a9ddc37da9bc2cc89a68c89605e0e7aeee3ea2be44fa" and
            len(program["field_access_profiles"]) == 25 and
            len(program["external_transfers"]) == 13 and
            not any(row["owner"].startswith("UNKNOWN")
                    for row in program["external_transfers"]),
            "route-0x0090f2 program closure incomplete")
    require(value["dynamic_witness"]["counts"] ==
            {"writes": 24, "samples": 8, "rng_calls": 0} and
            len(value["owned_writer_transactions"]) == 17 and
            len(value["helper_contracts"]) == 6 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["runtime_68000_interpretation_forbidden"] is True,
            "route-0x0090f2 witness or mutation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "committed route-0x0090f2 SPEC fixture is stale")
    else:
        OUT.write_bytes(encoded)
    print("SPEC-02 route-0x0090f2 PASS "
          f"instructions={value['normalized_source_program']['instruction_count']} "
          f"writes={value['dynamic_witness']['counts']['writes']} "
          f"tables={len(value['table_contracts'])} "
          f"sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
