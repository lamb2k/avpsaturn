#!/usr/bin/env python3
"""Build the complete Round 1 route-origin audio trigger family."""
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
OUT = ROOT / "data/spec02_route_audio_owner_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"
GROUP_IDS_SHA256 = "bb4937cb12bf418dd5ef6ef563a529549f40db2cd6cdb8d9cc006b1c7f3b1e2a"
CALLSITE_RAW_SHA256 = {
    "0x003c00": "cb33e21b487384221b45fdc9b50bd933a33fd85e32df4247c881490ca50703ea",
    "0x0094c4": "df5fd5b50b099d92dcaa39a0b38984122baf08da35c8808124ae410fc6344c7c",
    "0x00bfd8": "149fc31e5e4ac7c455a17c272b77233f751c2656f559e689a5e94608afb5f7b4",
    "0x00c0de": "4dba3e0a82cb8fb4a56dc6bea51e5101a5c629c54672258e0f923503ac986e9e",
    "0x00c0f0": "f1670949c05d8073ca9d8c8eb2a362451631e112b9e4e32bf047455ee8bdb8f2",
    "0x00c284": "f1670949c05d8073ca9d8c8eb2a362451631e112b9e4e32bf047455ee8bdb8f2",
    "0x00c86e": "b657fcb5f285ebc3599b3fe0c578e25e27617c3bcd900da4d8db5baf2afcb407",
}
FIELD_PROFILES = {
    "0x003c00": {"reads": ["a5-0x7162:u16"], "writes": ["d1:u32=zero-extended low u8", "d2:u32=0", "d3:u32=0"], "guard": "route context reaches shared wrapper with the low byte of u16(a5-0x7162)", "transfer": "0x003a88"},
    "0x0094c4": {"reads": ["a5+0x0c:u16"], "writes": ["a5+0x0c:u16+=2", "a5+0x10:u16=0", "a5+0x14:u16=0", "d0:u32=0x0000ffff"], "guard": "route state/substate reaches exact transition tail", "transfer": "0x003bdc"},
    "0x00bfd8": {"reads": ["a0-predecrement:u16", "a5+0x1e8:u16", "table 0x00bfea[index]:s16"], "writes": ["a0-predecrement:u16-=2"], "guard": "route selector u16(a5+0x1e8) chooses the exact signed computed target", "transfer": "computed 0x00bfea target"},
    "0x00c0de": {"reads": ["a5+0x0e:u16", "a5+0x0c:u16"], "writes": ["a5+0x0e:u16-=1", "a5+0x0c:u16+=2", "d1:u32=1"], "guard": "decremented u16(a5+0x0e)==0", "transfer": "0x00389c"},
    "0x00c0f0": {"reads": ["a5+0x12:u16"], "writes": ["a5+0x12:u16-=1"], "guard": "u16(a5+0x12) was nonzero and decrements to zero", "transfer": "0x003880"},
    "0x00c284": {"reads": ["a5+0x12:u16"], "writes": ["a5+0x12:u16-=1"], "guard": "relocated route branch: u16(a5+0x12) was nonzero and decrements to zero", "transfer": "0x003880"},
    "0x00c86e": {"reads": ["a5+0x1e8:u16", "helper 0x00ccf8 result", "helper 0x00cc94 result"], "writes": ["a5+0x1e8:u16+=2", "d0:u32=0x0000ffff"], "guard": "route dispatcher index reaches exact helper-helper-command tail", "transfer": "0x00ccf8 then 0x00cc94 then 0x003bdc"},
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
                     ["audio_owner_families"] if row["owner"] == "route")
    require(p2_family == {"first_p2_source_frame": 6199, "owner": "route"},
            "P2 route-audio family frontier drift")
    source_groups = sorted((row for row in oracle["trigger_groups"]
                            if "route" in row["source_owner_families"]),
                           key=lambda row: row["id"])
    require(hashlib.sha256(canonical([row["id"] for row in source_groups])).hexdigest() == GROUP_IDS_SHA256,
            "route-audio trigger group inventory drift")
    handler_commands = {row["command"]: row for row in handlers["command_transactions"]}
    image = OPCODES.read_bytes()
    groups = []
    callsites: dict[str, dict[str, object]] = {}
    context_count = occurrence_count = 0
    for source_group in source_groups:
        causal = source_group["handler_transaction"]["causal_control"]
        unchanged = (causal.get("gameplay_projection_unchanged") is True or
                     causal.get("gameplay_invariants", {}).get("stable_round2_result") is True)
        downstream = ("downstream_difference" in causal or
                      bool(causal.get("downstream_qsound_transactions")))
        require(source_group["classification"] == "SOURCE_CLOSED" and
                source_group["semantic_sound_name"] == "UNKNOWN" and
                source_group["handler_transaction"]["individual_bus_writes_are_logical_events"] is False and
                unchanged and downstream, f"route group {source_group['id']} boundary drift")
        require(source_group["command"] in handler_commands and
                handler_commands[source_group["command"]]["handler_class"] == source_group["handler_transaction"]["handler_class"] and
                handler_commands[source_group["command"]]["table_index"] == source_group["handler_transaction"]["table_index"],
                f"route group {source_group['id']} handler linkage drift")
        contexts = [copy.deepcopy(context) for context in source_group["transition_guard"]["contexts"]
                    if context["owner_family"] == "route"]
        require(contexts, f"route group {source_group['id']} has no route context")
        group = copy.deepcopy(source_group)
        group["group_total_occurrences"] = source_group["occurrences"]
        group["route_context_occurrences"] = sum(row["occurrences"] for row in contexts)
        group["shared_non_route_occurrences"] = source_group["occurrences"] - group["route_context_occurrences"]
        group["transition_guard"]["contexts"] = contexts
        groups.append(group)
        for context in contexts:
            context_count += 1
            occurrence_count += context["occurrences"]
            require((context["type_u8"], context["class_u8"], context["origin_record"]) ==
                    (0, "0x00", "0xff00d8"), "route pseudo-owner identity drift")
            source_call = context["source_call"]
            address = source_call["address"]
            start = int(source_call["guard_path_tail"][0]["pc"], 16)
            end = int(source_call["return_address"], 16)
            raw_sha = hashlib.sha256(image[start:end]).hexdigest()
            require(raw_sha == CALLSITE_RAW_SHA256[address], f"route callsite {address} opcode drift")
            program = {"address": address, "first": f"0x{start:06x}",
                "last_exclusive": f"0x{end:06x}", "raw_sha256": raw_sha,
                "accepted_oracle_window_sha256": source_call["source_window_sha256"],
                "instructions": source_call["guard_path_tail"],
                "instruction_semantics_sha256": hashlib.sha256(canonical(source_call["guard_path_tail"])).hexdigest(),
                "field_access_profile": FIELD_PROFILES[address], "commands": []}
            if address not in callsites:
                callsites[address] = program
            else:
                require({k: v for k, v in callsites[address].items() if k != "commands"} ==
                        {k: v for k, v in program.items() if k != "commands"},
                        f"route callsite {address} semantic drift")
            callsites[address]["commands"].append(source_group["command"])
    for program in callsites.values():
        program["commands"] = sorted(set(program["commands"]))
    commands = sorted({row["command"] for row in groups})
    require((len(groups), len(commands), context_count, occurrence_count, len(callsites)) ==
            (7, 7, 9, 11, 7), "route-audio coverage counts drift")
    return {
        "schema": "spec02-route-audio-owner-family-v1", "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "all Round 1-reachable route-origin audio trigger groups, contexts, callsite programs, command arguments and shared-dispatch effects",
        "source_identity": {"opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(), "oracle_sha256": sha(ORACLE),
            "handlers_artifact": HANDLERS.relative_to(ROOT).as_posix(), "handlers_sha256": sha(HANDLERS),
            "p2_closure_artifact": P2.relative_to(ROOT).as_posix(), "p2_closure_sha256": sha(P2),
            "first_p2_source_frame_u16": 6199, "group_ids_sha256": GROUP_IDS_SHA256},
        "coverage": {"trigger_groups": 7, "distinct_commands": 7,
            "route_source_contexts": 9, "route_dispatch_occurrences": 11,
            "source_origin_records": 1, "distinct_callsite_programs": 7,
            "record_type_class_pairs": 1, "orphan_groups": 0, "orphan_contexts": 0,
            "orphan_handler_transactions": 0, "unowned_audio_events": 0,
            "logical_load_release_events": 0, "rng_calls": 0},
        "commands": commands, "source_origin_records": ["0xff00d8"],
        "record_type_class_pairs": [{"record_type_u8": 0, "class_u8": "0x00"}],
        "trigger_groups": groups,
        "normalized_source_programs": [callsites[key] for key in sorted(callsites)],
        "handler_boundary": {"shared_dispatcher_owned_by": "global-gameplay-audio-load-release",
            "individual_qsound_writes_are_logical_events": False,
            "grouping_rule": "one route trigger and copied 16-byte command own one logical handler transaction",
            "semantic_sound_names": "UNKNOWN"},
        "transition_contract": {"guard_rule": oracle["owner_rule"],
            "ordered_effects": ["evaluate exact route pseudo-owner state/substate and local caller guard",
                "execute the accepted callsite operations with exact widths and signedness",
                "submit the exact command and argument tuple to the accepted shared wrapper",
                "apply the grouped handler/QSound transaction without inventing route progression"],
            "fixed_frame_authority": False, "route_audio_owns_route_progression": False,
            "logical_load_release_events": 0, "rng_calls": 0},
        "paired_capture_identity": oracle["capture_identity"],
        "protected_boundaries": oracle["protected_boundaries"],
        "mutation_controls": {key: True for key in (
            "missing_group_rejected", "missing_origin_record_rejected", "wrong_owner_family_rejected",
            "wrong_record_type_or_class_rejected", "wrong_context_state_or_substate_rejected",
            "wrong_callsite_rejected", "wrong_callsite_instruction_rejected",
            "wrong_operand_width_or_signed_guard_rejected", "wrong_command_rejected",
            "wrong_argument_tuple_rejected", "wrong_shared_wrapper_rejected",
            "wrong_handler_table_index_rejected", "individual_qsound_write_event_rejected",
            "missing_downstream_difference_rejected", "route_progression_coupling_rejected",
            "invented_semantic_sound_name_rejected", "invented_load_or_rng_rejected",
            "fixed_frame_trigger_rejected", "runtime_68000_interpretation_rejected")},
        "implementation_rules": {"portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False},
    }


def validate(value: dict[str, object]) -> None:
    require(value == build(), "route-audio executable family differs from accepted evidence")
    require(value["coverage"] == {"trigger_groups": 7, "distinct_commands": 7,
            "route_source_contexts": 9, "route_dispatch_occurrences": 11,
            "source_origin_records": 1, "distinct_callsite_programs": 7,
            "record_type_class_pairs": 1, "orphan_groups": 0, "orphan_contexts": 0,
            "orphan_handler_transactions": 0, "unowned_audio_events": 0,
            "logical_load_release_events": 0, "rng_calls": 0}, "route-audio coverage drift")
    require(len(value["normalized_source_programs"]) == 7 and
            {row["address"] for row in value["normalized_source_programs"]} == set(CALLSITE_RAW_SHA256) and
            all(row["raw_sha256"] == CALLSITE_RAW_SHA256[row["address"]] and
                row["field_access_profile"] == FIELD_PROFILES[row["address"]]
                for row in value["normalized_source_programs"]), "route-audio program inventory drift")
    require(value["handler_boundary"]["individual_qsound_writes_are_logical_events"] is False and
            value["transition_contract"]["route_audio_owns_route_progression"] is False and
            value["transition_contract"]["logical_load_release_events"] == 0 and
            value["transition_contract"]["rng_calls"] == 0 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "route-audio implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded, "route-audio artifact is stale")
        print("SPEC-02 route-audio owner artifact: PASS")
    else:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
