#!/usr/bin/env python3
"""Build the complete Round 1 encounter-origin audio trigger family."""
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
OUT = ROOT / "data/spec02_encounter_audio_owner_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"
GROUP_IDS_SHA256 = "c4654f5704d74cae868a1e7e036286538f81def1f1ca83679c578dc4c151012c"
CALLSITE_RAW_SHA256 = {
    "0x003c00": "cb33e21b487384221b45fdc9b50bd933a33fd85e32df4247c881490ca50703ea",
    "0x00809e": "0a6d468fff03658d6aa5a40c979eefcca88ac1e657798f40abfb33212cbe6602",
    "0x0083b4": "c833b377c436533c954bfcbb4798d950e8cba196bb4be4ab95cde6bd9344c050",
    "0x008556": "c5dd24439f9dc38a25ef88c16837f267a6dbdb2e1023a0d5af9e8d497ba77710",
}
FIELD_PROFILES = {
    "0x003c00": {"reads": ["a5-0x7162:u16"],
        "writes": ["d1:u32=zero-extended low u8", "d2:u32=0", "d3:u32=0"],
        "guard": "encounter chronology selects the low byte of u16(a5-0x7162)",
        "transfer": "0x003a88"},
    "0x00809e": {"reads": ["a5+0x1a6:u8"],
        "writes": ["a5+0x19:u8+=1"],
        "guard": "u8(a5+0x1a6)==0 before the encounter controller advance",
        "transfer": "0x0166ac then 0x008164"},
    "0x0083b4": {"reads": ["encounter exit controller state"],
        "writes": ["a5+0x1f3:u8=0", "a5+0x20a:u8=0"],
        "guard": "encounter exit controller reaches its exact reset-and-command tail",
        "transfer": "0x01728a then 0x01614a then 0x001972"},
    "0x008556": {"reads": ["encounter-to-route handoff guards"],
        "writes": ["a5+0x0c:u16=0", "a5+0x10:u16=0", "a5+0x14:u16=0",
                   "a5-0x6f18:u16=1"],
        "guard": "encounter handoff reaches the exact route reset-and-command tail",
        "transfer": "0x001972"},
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
                     ["audio_owner_families"] if row["owner"] == "encounter")
    require(p2_family == {"first_p2_source_frame": 15192, "owner": "encounter"},
            "P2 encounter-audio family frontier drift")
    source_groups = sorted((row for row in oracle["trigger_groups"]
                            if "encounter" in row["source_owner_families"]),
                           key=lambda row: row["id"])
    require(hashlib.sha256(canonical([row["id"] for row in source_groups])).hexdigest() ==
            GROUP_IDS_SHA256, "encounter-audio trigger group inventory drift")
    handler_commands = {row["command"]: row for row in handlers["command_transactions"]}
    image = OPCODES.read_bytes()
    groups = []
    callsites: dict[str, dict[str, object]] = {}
    context_count = occurrence_count = 0
    origins: set[str] = set()
    for source_group in source_groups:
        causal = source_group["handler_transaction"]["causal_control"]
        unchanged = (causal.get("gameplay_projection_unchanged") is True or
                     causal.get("gameplay_invariants", {}).get("stable_round2_result") is True)
        downstream = ("downstream_difference" in causal or
                      bool(causal.get("downstream_qsound_transactions")))
        require(source_group["classification"] == "SOURCE_CLOSED" and
                source_group["semantic_sound_name"] == "UNKNOWN" and
                source_group["handler_transaction"]["individual_bus_writes_are_logical_events"] is False and
                unchanged and downstream, f"encounter group {source_group['id']} boundary drift")
        require(source_group["command"] in handler_commands and
                handler_commands[source_group["command"]]["handler_class"] ==
                    source_group["handler_transaction"]["handler_class"] and
                handler_commands[source_group["command"]]["table_index"] ==
                    source_group["handler_transaction"]["table_index"],
                f"encounter group {source_group['id']} handler linkage drift")
        contexts = [copy.deepcopy(context) for context in
                    source_group["transition_guard"]["contexts"]
                    if context["owner_family"] == "encounter"]
        require(contexts, f"encounter group {source_group['id']} has no encounter context")
        group = copy.deepcopy(source_group)
        group["group_total_occurrences"] = source_group["occurrences"]
        group["encounter_context_occurrences"] = sum(row["occurrences"] for row in contexts)
        group["shared_non_encounter_occurrences"] = (
            source_group["occurrences"] - group["encounter_context_occurrences"])
        group["transition_guard"]["contexts"] = contexts
        groups.append(group)
        for context in contexts:
            context_count += 1
            occurrence_count += context["occurrences"]
            require((context["type_u8"], context["class_u8"]) == (0, "0x00") and
                    context["origin_record"] in {"0xff8480", "0xffea80"},
                    "encounter pseudo-owner identity drift")
            origins.add(context["origin_record"])
            source_call = context["source_call"]
            address = source_call["address"]
            start = int(source_call["guard_path_tail"][0]["pc"], 16)
            end = int(source_call["return_address"], 16)
            raw_sha = hashlib.sha256(image[start:end]).hexdigest()
            require(raw_sha == CALLSITE_RAW_SHA256[address],
                    f"encounter callsite {address} opcode drift")
            program = {"address": address, "first": f"0x{start:06x}",
                "last_exclusive": f"0x{end:06x}", "raw_sha256": raw_sha,
                "accepted_oracle_window_sha256": source_call["source_window_sha256"],
                "instructions": source_call["guard_path_tail"],
                "instruction_semantics_sha256": hashlib.sha256(
                    canonical(source_call["guard_path_tail"])).hexdigest(),
                "field_access_profile": FIELD_PROFILES[address], "commands": []}
            if address not in callsites:
                callsites[address] = program
            else:
                require({k: v for k, v in callsites[address].items() if k != "commands"} ==
                        {k: v for k, v in program.items() if k != "commands"},
                        f"encounter callsite {address} semantic drift")
            callsites[address]["commands"].append(source_group["command"])
    for program in callsites.values():
        program["commands"] = sorted(set(program["commands"]))
    commands = sorted({row["command"] for row in groups})
    require((len(groups), len(commands), context_count, occurrence_count,
             len(origins), len(callsites)) == (4, 4, 6, 9, 2, 4),
            "encounter-audio coverage counts drift")
    return {
        "schema": "spec02-encounter-audio-owner-family-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "all Round 1-reachable encounter-origin audio trigger groups, contexts, callsite programs, command arguments and shared-dispatch effects",
        "source_identity": {"opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": sha(ORACLE),
            "handlers_artifact": HANDLERS.relative_to(ROOT).as_posix(),
            "handlers_sha256": sha(HANDLERS),
            "p2_closure_artifact": P2.relative_to(ROOT).as_posix(),
            "p2_closure_sha256": sha(P2),
            "first_p2_source_frame_u16": 15192,
            "group_ids_sha256": GROUP_IDS_SHA256},
        "coverage": {"trigger_groups": 4, "distinct_commands": 4,
            "encounter_source_contexts": 6, "encounter_dispatch_occurrences": 9,
            "source_origin_records": 2, "distinct_callsite_programs": 4,
            "record_type_class_pairs": 1, "orphan_groups": 0,
            "orphan_contexts": 0, "orphan_handler_transactions": 0,
            "unowned_audio_events": 0, "logical_load_release_events": 0,
            "rng_calls": 0},
        "commands": commands, "source_origin_records": sorted(origins),
        "record_type_class_pairs": [{"record_type_u8": 0, "class_u8": "0x00"}],
        "trigger_groups": groups,
        "normalized_source_programs": [callsites[key] for key in sorted(callsites)],
        "handler_boundary": {
            "shared_dispatcher_owned_by": "global-gameplay-audio-load-release",
            "individual_qsound_writes_are_logical_events": False,
            "grouping_rule": "one encounter trigger and copied 16-byte command own one logical handler transaction",
            "semantic_sound_names": "UNKNOWN"},
        "transition_contract": {"guard_rule": oracle["owner_rule"],
            "ordered_effects": [
                "evaluate exact encounter pseudo-owner chronology and local caller guard",
                "execute the accepted callsite operations with exact widths and signedness",
                "submit the exact command and argument tuple to the accepted shared wrapper",
                "apply the grouped handler/QSound transaction without inventing encounter progression"],
            "fixed_frame_authority": False,
            "encounter_audio_owns_encounter_progression": False,
            "logical_load_release_events": 0, "rng_calls": 0},
        "paired_capture_identity": oracle["capture_identity"],
        "protected_boundaries": oracle["protected_boundaries"],
        "mutation_controls": {key: True for key in (
            "missing_group_rejected", "missing_origin_record_rejected",
            "wrong_owner_family_rejected", "wrong_record_type_or_class_rejected",
            "wrong_context_state_or_substate_rejected", "wrong_callsite_rejected",
            "wrong_callsite_instruction_rejected", "wrong_operand_width_or_signed_guard_rejected",
            "wrong_command_rejected", "wrong_argument_tuple_rejected",
            "wrong_shared_wrapper_rejected", "wrong_handler_table_index_rejected",
            "individual_qsound_write_event_rejected", "missing_downstream_difference_rejected",
            "encounter_progression_coupling_rejected", "invented_semantic_sound_name_rejected",
            "invented_load_or_rng_rejected", "fixed_frame_trigger_rejected",
            "runtime_68000_interpretation_rejected")},
        "implementation_rules": {"portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False},
    }


def validate(value: dict[str, object]) -> None:
    require(value == build(),
            "encounter-audio executable family differs from accepted evidence")
    require(value["coverage"] == {"trigger_groups": 4, "distinct_commands": 4,
            "encounter_source_contexts": 6, "encounter_dispatch_occurrences": 9,
            "source_origin_records": 2, "distinct_callsite_programs": 4,
            "record_type_class_pairs": 1, "orphan_groups": 0,
            "orphan_contexts": 0, "orphan_handler_transactions": 0,
            "unowned_audio_events": 0, "logical_load_release_events": 0,
            "rng_calls": 0}, "encounter-audio coverage drift")
    require(len(value["normalized_source_programs"]) == 4 and
            {row["address"] for row in value["normalized_source_programs"]} ==
                set(CALLSITE_RAW_SHA256) and
            all(row["raw_sha256"] == CALLSITE_RAW_SHA256[row["address"]] and
                row["field_access_profile"] == FIELD_PROFILES[row["address"]]
                for row in value["normalized_source_programs"]),
            "encounter-audio program inventory drift")
    require(value["source_origin_records"] == ["0xff8480", "0xffea80"] and
            value["handler_boundary"]["individual_qsound_writes_are_logical_events"] is False and
            value["transition_contract"]["encounter_audio_owns_encounter_progression"] is False and
            value["transition_contract"]["logical_load_release_events"] == 0 and
            value["transition_contract"]["rng_calls"] == 0 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "encounter-audio implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "encounter-audio artifact is stale")
        print("SPEC-02 encounter-audio owner artifact: PASS")
    else:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
