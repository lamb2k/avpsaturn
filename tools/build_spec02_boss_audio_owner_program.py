#!/usr/bin/env python3
"""Build the complete Round 1 boss-origin audio trigger family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_global_audio_trigger_owners.json"
HANDLERS = ROOT / "data/oracle11_global_audio_handlers.json"
P2 = ROOT / "data/oracle10_round1_p2_closure.json"
OUT = ROOT / "data/spec02_boss_audio_owner_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"

GROUP_IDS = (
    "global-audio-ffa3c0-003a8e-003d",
    "global-audio-ffa3c0-003a8e-003e",
    "global-audio-ffa3c0-003a8e-003f",
    "global-audio-ffa3c0-003a8e-0072",
    "global-audio-ffa3c0-003a8e-0073",
    "global-audio-ffa3c0-003a8e-0079",
    "global-audio-ffa3c0-003a8e-0108",
    "global-audio-ffa3c0-003a8e-0109",
    "global-audio-ffa3c0-003a8e-010a",
    "global-audio-ffa3c0-003a8e-013d",
    "global-audio-ffac00-003a8e-0083",
    "global-audio-ffac00-003a8e-014a",
    "global-audio-ffac80-003a8e-0082",
    "global-audio-ffac80-003a8e-014b",
    "global-audio-ffad00-003a8e-0082",
    "global-audio-ffad00-003a8e-0083",
    "global-audio-ffad00-003a8e-014a",
    "global-audio-ffad00-003a8e-014b",
    "global-audio-ffad80-003a8e-0082",
    "global-audio-ffad80-003a8e-0083",
    "global-audio-ffad80-003a8e-014a",
    "global-audio-ffae00-003a8e-0082",
    "global-audio-ffae00-003a8e-014a",
    "global-audio-ffae00-003a8e-014b",
    "global-audio-ffc600-003a8e-0088",
)

CALLSITE_RAW_SHA256 = {
    "0x003b58": "c294dcdce65f45b69bc854ffd95cc4b8d671fa3369305f23fe434780884b9847",
    "0x01eba4": "84d82480f78bfc319eacdcaf8fdb296d2426da41b71ae378edf1753dca3340b1",
    "0x01ec8a": "d82a3f8077747168eb44d6c5547025fd1ce6c1b2c4a69dd1026ead9b1d075ec2",
    "0x01f402": "f56117a0dec4231b7df185af7f08fa0866b6e3ad34370182b60afe97cf80274d",
    "0x01f4ea": "06d8de53b0392ab4f9e11e7ee2672a955118b8c036f89feeb9a00ec60767e906",
    "0x03542a": "410bc5d58e558877658c54058c21409f016f481a1e2d16e7fd3122daa5dd7c11",
    "0x035562": "5ed11f0849d5fe48932a3124442006a36f5f8aee1ed90763dd48bbf5afa48d2b",
    "0x049582": "2913422a1f5491d83a2eef76b5ec569b5ca2c1961acc32a1b43af2a48127219d",
    "0x0496f0": "df01b8d4dc31e434f7c06ef1f4f4e79cd511f0546b8dc0954cc2b125ce72cc6b",
    "0x049832": "d3fd394e1b63eb97edaa4b4e4dd0ff60bf9f4ad12343d3c0e56ded5336654401",
    "0x049c14": "2800971b7d0e55d1a61f29d96684ad55c57de145d832a7ed65fb631d50da6c86",
    "0x04a482": "364a098b707eb9e290736b03f7b349ad5e9d5f0d84f26bc96a83d2ff58f8c093",
    "0x07733e": "b5ad00f599a65dec65fc402cfade53f61a7e56352032d59deb502bd54ed9c230",
    "0x07736a": "49ca10f49465338754bc2dbf21790d48adc30cf86c63adcd7d8957d01ac3ead3",
}

FIELD_PROFILES = {
    "0x003b58": {"reads": ["owner+0x71:u8", "table 0x003b60[selector]"],
                  "writes": [], "guard": "owner context reaches selector; u8(owner+0x71) indexes the exact helper table", "transfer": "indirect table target"},
    "0x01eba4": {"reads": [], "writes": ["owner+0x34:u32=0", "owner+0x3c:u32=0", "owner+0x2a:u8=3"],
                  "guard": "type12/class06 state-substate context reaches the accepted tail", "transfer": "0x09a660 then 0x001c4a"},
    "0x01ec8a": {"reads": ["owner+0x18:u16", "owner+0x14:u16"], "writes": ["owner+0x14:u16=d0"],
                  "guard": "unsigned u16(owner+0x18) is not below u16(owner+0x14)", "transfer": "0x001c20"},
    "0x01f402": {"reads": ["owner+0x06:u8"], "writes": ["owner+0x06:u8+=2", "owner+0x2a:u8=3", "owner+0x5c:u8=0"],
                  "guard": "type12/class06 state-substate context reaches the accepted tail", "transfer": "0x09a660 then 0x001c4a"},
    "0x01f4ea": {"reads": ["condition codes from the accepted preceding unsigned compare"], "writes": ["owner+0x14:u16=d0", "owner+0x5c:u8=0"],
                  "guard": "unsigned compare carry clear at 0x01f4da in state 0x0402/substate 0x0600", "transfer": "0x09a660 then 0x001c20"},
    "0x03542a": {"reads": ["d3:u32", "d4:u32", "d5:u8", "owner+0x0f:u8"], "writes": ["owner+0x3c:u32=d3", "owner+0x54:u32=d4", "owner+0x0f:u8^=d5", "owner+0x4f:u8=owner+0x0f"],
                  "guard": "type16/class06 state 0x0200/substate 0 reaches selected helper", "transfer": "0x00279c"},
    "0x035562": {"reads": ["d0:u32", "owner+0x18:u32", "owner+0x18:u16", "owner+0x14:u16"], "writes": ["owner+0x18:u32+=d0"],
                  "guard": "type16/class06 state 0x0200/substate 0 selects movement helper call entry 0x035562", "transfer": "0x0027e0"},
    "0x049582": {"reads": ["signed branch flags", "a5+0x022a:u8"], "writes": ["a5+0x022a:u8=1"],
                  "guard": "signed-negative prior result and u8(a5+0x022a)==0", "transfer": "0x002588"},
    "0x0496f0": {"reads": ["owner+0x06:u8", "table 0x049700[index]:s16"], "writes": [],
                  "guard": "0x04ae28 returns nonzero, then action high byte selects exact class06 target", "transfer": "computed target in 0x049700 table"},
    "0x049832": {"reads": ["owner+0x24:s16", "owner+0x25:u8"], "writes": [],
                  "guard": "s16(owner+0x24)>=0 and u8(owner+0x25)!=0", "transfer": "0x00255e"},
    "0x049c14": {"reads": ["condition codes returned by 0x04a76e"], "writes": [],
                  "guard": "0x04a76e returns carry clear; carry-set path tails to 0x016536", "transfer": "0x001c20"},
    "0x04a482": {"reads": [], "writes": ["owner+0x5c:u8=2", "d0:u16=0x0015"],
                  "guard": "type12/class06 action 0x0e/substate 0x0202 reaches accepted branch", "transfer": "0x016536 or 0x001c20 by exact branch"},
    "0x07733e": {"reads": ["a5+0x0209:u8", "owner+0x05:u8"], "writes": ["owner+0x05:u8+=2"],
                  "guard": "type24/class06 state 0x0202/substate 0 and u8(a5+0x0209)!=0", "transfer": "0x0028ae"},
    "0x07736a": {"reads": ["a5+0x0209:u8", "owner+0x05:u8"], "writes": ["owner+0x05:u8+=2"],
                  "guard": "type24/class06 state 0x0206/substate 0 and u8(a5+0x0209)==4", "transfer": "0x0028ae"},
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, object]:
    require(OPCODES.is_file() and sha(OPCODES) == OPCODE_SHA256,
            "accepted decrypted opcode image missing or drifted")
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    handlers = json.loads(HANDLERS.read_text(encoding="utf-8"))
    p2 = json.loads(P2.read_text(encoding="utf-8"))
    p2_family = next(row for row in p2["p3_reusable_program_controller_families"]
                     ["audio_owner_families"] if row["owner"] == "boss")
    require(p2_family == {"first_p2_source_frame": 5867, "owner": "boss"},
            "P2 boss-audio family frontier drift")
    source_groups = [row for row in oracle["trigger_groups"]
                     if "boss" in row["source_owner_families"]]
    source_groups.sort(key=lambda row: row["id"])
    require(tuple(row["id"] for row in source_groups) == GROUP_IDS,
            "boss-audio trigger group inventory drift")
    handler_commands = {row["command"]: row
                        for row in handlers["command_transactions"]}
    image = OPCODES.read_bytes()
    groups = []
    callsites: dict[str, dict[str, object]] = {}
    context_count = occurrence_count = 0
    for source_group in source_groups:
        causal = source_group["handler_transaction"]["causal_control"]
        causal_projection_unchanged = (
            causal.get("gameplay_projection_unchanged") is True or
            causal.get("gameplay_invariants", {}).get("stable_round2_result")
                is True)
        causal_downstream_bound = (
            "downstream_difference" in causal or
            bool(causal.get("downstream_qsound_transactions")))
        require(source_group["classification"] == "SOURCE_CLOSED" and
                source_group["semantic_sound_name"] == "UNKNOWN" and
                source_group["handler_transaction"]
                    ["individual_bus_writes_are_logical_events"] is False and
                causal_projection_unchanged and causal_downstream_bound,
                f"boss group {source_group['id']} source boundary drift")
        require(source_group["command"] in handler_commands and
                handler_commands[source_group["command"]]["handler_class"] ==
                    source_group["handler_transaction"]["handler_class"] and
                handler_commands[source_group["command"]]["table_index"] ==
                    source_group["handler_transaction"]["table_index"],
                f"boss group {source_group['id']} handler linkage drift")
        contexts = [copy.deepcopy(context)
                    for context in source_group["transition_guard"]["contexts"]
                    if context["owner_family"] == "boss"]
        require(contexts, f"boss group {source_group['id']} has no boss context")
        group = copy.deepcopy(source_group)
        group["group_total_occurrences"] = source_group["occurrences"]
        group["boss_context_occurrences"] = sum(row["occurrences"]
                                                for row in contexts)
        group["shared_non_boss_occurrences"] = (
            source_group["occurrences"] - group["boss_context_occurrences"])
        group["transition_guard"]["contexts"] = contexts
        groups.append(group)
        for context in contexts:
            context_count += 1
            occurrence_count += context["occurrences"]
            require(context["class_u8"] == "0x06" and
                    context["type_u8"] in {12, 16, 24},
                    "boss context class/type drift")
            source_call = context["source_call"]
            address = source_call["address"]
            start = int(source_call["guard_path_tail"][0]["pc"], 16)
            end = int(source_call["return_address"], 16)
            raw_sha = hashlib.sha256(image[start:end]).hexdigest()
            require(raw_sha == CALLSITE_RAW_SHA256[address],
                    f"boss callsite {address} opcode slice drift")
            program = {
                "address": address,
                "first": f"0x{start:06x}",
                "last_exclusive": f"0x{end:06x}",
                "raw_sha256": raw_sha,
                "accepted_oracle_window_sha256":
                    source_call["source_window_sha256"],
                "instructions": source_call["guard_path_tail"],
                "instruction_semantics_sha256": hashlib.sha256(
                    canonical(source_call["guard_path_tail"])).hexdigest(),
                "field_access_profile": FIELD_PROFILES[address],
                "commands": [],
            }
            if address not in callsites:
                callsites[address] = program
            else:
                require({key: callsites[address][key] for key in program
                         if key != "commands"} ==
                        {key: program[key] for key in program
                         if key != "commands"},
                        f"boss callsite {address} semantic drift")
            callsites[address]["commands"].append(source_group["command"])
    for program in callsites.values():
        program["commands"] = sorted(set(program["commands"]))
    commands = sorted({row["command"] for row in groups})
    origins = sorted({context["origin_record"] for row in groups
                      for context in row["transition_guard"]["contexts"]})
    require(len(groups) == 25 and len(commands) == 15 and
            context_count == 42 and occurrence_count == 110 and
            len(callsites) == 14 and len(origins) == 7,
            "boss-audio coverage counts drift")
    return {
        "schema": "spec02-boss-audio-owner-family-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "all Round 1-reachable boss-origin audio trigger groups, contexts, callsite programs, command arguments and shared-dispatch effects",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": sha(ORACLE),
            "handlers_artifact": HANDLERS.relative_to(ROOT).as_posix(),
            "handlers_sha256": sha(HANDLERS),
            "p2_closure_artifact": P2.relative_to(ROOT).as_posix(),
            "p2_closure_sha256": sha(P2),
            "first_p2_source_frame_u16": 5867,
        },
        "coverage": {
            "trigger_groups": 25, "distinct_commands": 15,
            "boss_source_contexts": 42, "boss_dispatch_occurrences": 110,
            "source_origin_records": 7, "distinct_callsite_programs": 14,
            "record_type_class_pairs": 3,
            "orphan_groups": 0, "orphan_contexts": 0,
            "orphan_handler_transactions": 0, "unowned_audio_events": 0,
            "logical_load_release_events": 0, "rng_calls": 0,
        },
        "commands": commands,
        "source_origin_records": origins,
        "record_type_class_pairs": [
            {"record_type_u8": 12, "class_u8": "0x06"},
            {"record_type_u8": 16, "class_u8": "0x06"},
            {"record_type_u8": 24, "class_u8": "0x06"},
        ],
        "trigger_groups": groups,
        "normalized_source_programs": [callsites[key]
                                       for key in sorted(callsites)],
        "handler_boundary": {
            "shared_dispatcher_owned_by": "global-gameplay-audio-load-release",
            "individual_qsound_writes_are_logical_events": False,
            "grouping_rule": "one boss trigger and copied 16-byte command own one logical handler transaction",
            "semantic_sound_names": "UNKNOWN",
        },
        "transition_contract": {
            "guard_rule": oracle["owner_rule"],
            "ordered_effects": [
                "evaluate exact record type, class, state, substate and local caller guard",
                "execute the accepted callsite operations with exact widths and signedness",
                "submit the exact command and argument tuple to the accepted shared wrapper",
                "apply the grouped handler/QSound transaction without changing boss gameplay projection",
            ],
            "fixed_frame_authority": False,
            "boss_audio_owns_boss_gameplay": False,
            "logical_load_release_events": 0,
            "rng_calls": 0,
        },
        "paired_capture_identity": oracle["capture_identity"],
        "protected_boundaries": oracle["protected_boundaries"],
        "mutation_controls": {
            "missing_group_rejected": True,
            "missing_origin_record_rejected": True,
            "wrong_owner_family_rejected": True,
            "wrong_record_type_or_class_rejected": True,
            "wrong_context_state_or_substate_rejected": True,
            "wrong_callsite_rejected": True,
            "wrong_callsite_instruction_rejected": True,
            "wrong_operand_width_or_signed_guard_rejected": True,
            "wrong_command_rejected": True,
            "wrong_argument_tuple_rejected": True,
            "wrong_shared_wrapper_rejected": True,
            "wrong_handler_table_index_rejected": True,
            "individual_qsound_write_event_rejected": True,
            "missing_downstream_difference_rejected": True,
            "gameplay_projection_coupling_rejected": True,
            "invented_semantic_sound_name_rejected": True,
            "invented_load_or_rng_rejected": True,
            "fixed_frame_trigger_rejected": True,
            "runtime_68000_interpretation_rejected": True,
        },
        "implementation_rules": {
            "portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False,
        },
    }


def validate(value: dict[str, object]) -> None:
    require(value == build(),
            "boss-audio executable family differs from accepted evidence")
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "boss-audio status drift")
    require(value["coverage"] == {
        "trigger_groups": 25, "distinct_commands": 15,
        "boss_source_contexts": 42, "boss_dispatch_occurrences": 110,
        "source_origin_records": 7, "distinct_callsite_programs": 14,
        "record_type_class_pairs": 3,
        "orphan_groups": 0, "orphan_contexts": 0,
        "orphan_handler_transactions": 0, "unowned_audio_events": 0,
        "logical_load_release_events": 0, "rng_calls": 0},
        "boss-audio coverage drift")
    require(tuple(row["id"] for row in value["trigger_groups"]) == GROUP_IDS and
            len(value["commands"]) == 15 and
            len(value["source_origin_records"]) == 7,
            "boss-audio inventory drift")
    programs = value["normalized_source_programs"]
    require(len(programs) == 14 and
            {row["address"] for row in programs} == set(CALLSITE_RAW_SHA256) and
            all(len(row["instructions"]) == 5 and
                row["raw_sha256"] == CALLSITE_RAW_SHA256[row["address"]] and
                row["field_access_profile"] == FIELD_PROFILES[row["address"]]
                for row in programs),
            "boss-audio normalized callsite programs incomplete")
    require(value["transition_contract"]["fixed_frame_authority"] is False and
            value["transition_contract"]["boss_audio_owns_boss_gameplay"] is False and
            value["transition_contract"]["logical_load_release_events"] == 0 and
            value["transition_contract"]["rng_calls"] == 0 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "boss-audio implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "boss-audio artifact is stale")
        print("SPEC-02 boss-audio owner artifact: PASS")
    else:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
