#!/usr/bin/env python3
"""Build the complete Round 1 presentation-origin audio trigger family."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
ORACLE = ROOT / "data/oracle11_global_audio_trigger_owners.json"
HANDLERS = ROOT / "data/oracle11_global_audio_handlers.json"
P2 = ROOT / "data/oracle10_round1_p2_closure.json"
OUT = ROOT / "data/spec02_presentation_audio_owner_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"

GROUP_IDS = (
    "global-audio-ff1b1e-003a8e-0034",
    "global-audio-ff8186-001a78-0030",
    "global-audio-ffd180-001a34-ff05",
    "global-audio-ffd180-001a34-ff07",
    "global-audio-ffd180-003a8e-0004",
    "global-audio-ffd180-003a8e-000f",
    "global-audio-ffd180-003a8e-007d",
    "global-audio-ffd180-003a8e-0266",
)
CALLSITE_RAW_SHA256 = {
    "0x00173e": "44314e7fa78d827aee114c7832b295550f50b37945c041a3d55f7deb0909b026",
    "0x003c00": "cb33e21b487384221b45fdc9b50bd933a33fd85e32df4247c881490ca50703ea",
    "0x020bb0": "11b4c8374527307761391774d7c08412e9be9f691934d7d1f233b359a74fc26e",
    "0x028dde": "e0be6ac4ee6dbc1c308e7da8dd50871f5698b92d7cb69ed9c0d7e4018ba1ba91",
    "0x028e22": "9c082b1f755693a5f1d8cc1a27fae510577b83844c30ca4efc021daf1eeeac51",
    "0x0ac636": "92a8fdf25eafaddca0ed2d6cb6325e8e9cc7318aae0d060508453703b72ce365",
    "0x0ac760": "0cd6e3ce35fc0415d324fc0991ff1bc54b634890eb8abb7b73d7d142a355570e",
    "0x0ad1cc": "8418946b314da5617c5966922f6ffb38609c64725f56244386d5032dec08d17c",
}
FIELD_PROFILES = {
    "0x00173e": {
        "reads": ["g819f:u8"], "writes": ["g819f:u8 -= 1"],
        "guard": "u8(g819f) != 0", "transfer": "0x001a62"},
    "0x003c00": {
        "reads": ["g8e9e:u16 & 0x00ff"], "writes": [],
        "guard": "owner controller reaches the shared command wrapper",
        "transfer": "0x003a88"},
    "0x020bb0": {
        "reads": ["owner+0x2b:u8", "table 0x901340"], "writes": [],
        "guard": "u8(owner+0x2b) == 0", "transfer": "0x0026ae"},
    "0x028dde": {
        "reads": [],
        "writes": ["g81d5:u8 = 1", "g8240:u8 = 1", "g9a1e:u16 = 0"],
        "guard": "record32 class-0x02 state/substate dispatcher reaches phase 0x020a/0",
        "transfer": "0x003bdc"},
    "0x028e22": {
        "reads": ["controller phase guard"], "writes": [],
        "guard": "record32 class-0x02 state/substate dispatcher reaches phase 0x020a/0x0200",
        "transfer": "0x003bdc"},
    "0x0ac636": {
        "reads": ["presentation record+0xd2:u8", "table 0x0ac678[selector]"],
        "writes": [], "guard": "(u8(record+0xd2) & 3) selects an exact helper",
        "transfer": "indirect table target"},
    "0x0ac760": {
        "reads": ["presentation record+0x04:u8", "table 0x0ac76a[state]"],
        "writes": ["g9a62:pointer = owner"],
        "guard": "presentation record state selects an exact table target",
        "transfer": "indirect table target"},
    "0x0ad1cc": {
        "reads": ["presentation control bits:u16"], "writes": [],
        "guard": "selected control bit is zero", "transfer": "0x001a92"},
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
                     ["audio_owner_families"] if row["owner"] == "presentation")
    require(p2_family == {"first_p2_source_frame": 5719, "owner": "presentation"},
            "P2 presentation-audio family frontier drift")
    groups = [row for row in oracle["trigger_groups"]
              if "presentation" in row["source_owner_families"]]
    groups.sort(key=lambda row: row["id"])
    require(tuple(row["id"] for row in groups) == GROUP_IDS,
            "presentation-audio trigger group inventory drift")
    handler_commands = {row["command"]: row for row in handlers["command_transactions"]}
    image = OPCODES.read_bytes()
    callsites: dict[str, dict[str, object]] = {}
    context_count = 0
    for group in groups:
        require(group["classification"] == "SOURCE_CLOSED" and
                group["semantic_sound_name"] == "UNKNOWN" and
                group["handler_transaction"]["individual_bus_writes_are_logical_events"] is False and
                group["handler_transaction"]["causal_control"]["gameplay_projection_unchanged"] is True,
                f"presentation group {group['id']} source boundary drift")
        require(group["command"] in handler_commands and
                handler_commands[group["command"]]["handler_class"] ==
                    group["handler_transaction"]["handler_class"] and
                handler_commands[group["command"]]["table_index"] ==
                    group["handler_transaction"]["table_index"],
                f"presentation group {group['id']} handler linkage drift")
        for context in group["transition_guard"]["contexts"]:
            context_count += 1
            require(context["owner_family"] == "presentation",
                    "presentation context owner drift")
            source_call = context["source_call"]
            address = source_call["address"]
            start = int(source_call["guard_path_tail"][0]["pc"], 16)
            end = int(source_call["return_address"], 16)
            raw_sha = hashlib.sha256(image[start:end]).hexdigest()
            require(raw_sha == CALLSITE_RAW_SHA256[address],
                    f"presentation callsite {address} opcode slice drift")
            program = {
                "address": address,
                "first": f"0x{start:06x}", "last_exclusive": f"0x{end:06x}",
                "raw_sha256": raw_sha,
                "accepted_oracle_window_sha256": source_call["source_window_sha256"],
                "instructions": source_call["guard_path_tail"],
                "instruction_semantics_sha256": hashlib.sha256(
                    canonical(source_call["guard_path_tail"])).hexdigest(),
                "field_access_profile": FIELD_PROFILES[address],
                "commands": [],
            }
            if address not in callsites:
                callsites[address] = program
            else:
                require({k: callsites[address][k] for k in program if k != "commands"} ==
                        {k: program[k] for k in program if k != "commands"},
                        f"presentation callsite {address} semantic drift")
            callsites[address]["commands"].append(group["command"])
    for program in callsites.values():
        program["commands"] = sorted(set(program["commands"]))
    require(len(groups) == 8 and len(callsites) == 8 and context_count == 20 and
            sum(row["occurrences"] for row in groups) == 53,
            "presentation-audio coverage counts drift")
    commands = sorted({row["command"] for row in groups})
    return {
        "schema": "spec02-presentation-audio-owner-family-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "all Round 1-reachable presentation-origin audio trigger groups, contexts, callsite programs, command arguments and shared-dispatch effects",
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": sha(ORACLE),
            "handlers_artifact": HANDLERS.relative_to(ROOT).as_posix(),
            "handlers_sha256": sha(HANDLERS),
            "p2_closure_artifact": P2.relative_to(ROOT).as_posix(),
            "p2_closure_sha256": sha(P2),
            "first_p2_source_frame_u16": 5719,
        },
        "coverage": {
            "trigger_groups": 8, "distinct_commands": len(commands),
            "source_contexts": 20, "dispatch_occurrences": 53,
            "distinct_callsite_programs": 8, "orphan_groups": 0,
            "orphan_contexts": 0, "orphan_handler_transactions": 0,
            "unowned_audio_events": 0, "logical_load_release_events": 0,
            "rng_calls": 0,
        },
        "commands": commands,
        "trigger_groups": groups,
        "normalized_source_programs": [callsites[key] for key in sorted(callsites)],
        "handler_boundary": {
            "shared_dispatcher_owned_by": "global-gameplay-audio-load-release",
            "individual_qsound_writes_are_logical_events": False,
            "grouping_rule": "one source owner trigger and copied 16-byte command own one logical handler transaction",
            "semantic_sound_names": "UNKNOWN",
        },
        "transition_contract": {
            "guard_rule": oracle["owner_rule"],
            "ordered_effects": [
                "evaluate exact owner class/type/state/substate and local caller guard",
                "execute the accepted callsite operations with exact widths and signedness",
                "submit the exact command and argument tuple to the accepted shared wrapper",
                "apply the bound grouped handler/QSound transaction without changing gameplay projection",
            ],
            "fixed_frame_authority": False,
            "presentation_owns_gameplay_result": False,
            "logical_load_release_events": 0,
            "rng_calls": 0,
        },
        "paired_capture_identity": oracle["capture_identity"],
        "protected_boundaries": oracle["protected_boundaries"],
        "mutation_controls": {
            "missing_group_rejected": True,
            "wrong_owner_family_rejected": True,
            "wrong_context_state_or_substate_rejected": True,
            "wrong_callsite_rejected": True,
            "wrong_callsite_instruction_rejected": True,
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
            "presentation-audio executable family differs from accepted evidence")
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "presentation-audio status drift")
    require(value["coverage"] == {
        "trigger_groups": 8, "distinct_commands": 8,
        "source_contexts": 20, "dispatch_occurrences": 53,
        "distinct_callsite_programs": 8, "orphan_groups": 0,
        "orphan_contexts": 0, "orphan_handler_transactions": 0,
        "unowned_audio_events": 0, "logical_load_release_events": 0,
        "rng_calls": 0}, "presentation-audio coverage drift")
    require(tuple(row["id"] for row in value["trigger_groups"]) == GROUP_IDS and
            set(value["commands"]) == {"0x0004", "0x000f", "0x0030", "0x0034",
                                        "0x007d", "0x0266", "0xff05", "0xff07"},
            "presentation-audio command inventory drift")
    require(len(value["normalized_source_programs"]) == 8 and
            {row["address"] for row in value["normalized_source_programs"]} ==
                set(CALLSITE_RAW_SHA256) and
            all(len(row["instructions"]) == 5 and
                row["raw_sha256"] == CALLSITE_RAW_SHA256[row["address"]] and
                row["field_access_profile"] == FIELD_PROFILES[row["address"]]
                for row in value["normalized_source_programs"]),
            "presentation-audio normalized callsite programs incomplete")
    require(value["transition_contract"]["fixed_frame_authority"] is False and
            value["transition_contract"]["presentation_owns_gameplay_result"] is False and
            value["transition_contract"]["logical_load_release_events"] == 0 and
            value["transition_contract"]["rng_calls"] == 0 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "presentation-audio implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "presentation-audio artifact is stale")
        print("SPEC-02 presentation-audio owner artifact: PASS")
    else:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
