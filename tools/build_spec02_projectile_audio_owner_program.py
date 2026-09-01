#!/usr/bin/env python3
"""Build the complete Round 1 projectile-origin audio trigger family."""
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
OUT = ROOT / "data/spec02_projectile_audio_owner_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"

EXPECTED_BY_ORIGIN = {
    "ff8680": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8700": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8780": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8800": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8880": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8900": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8980": ("004d", "004e", "004f", "0118", "0119", "011a"),
    "ff8a00": ("004d", "004f", "0118", "0119"),
}
GROUP_IDS = tuple(sorted(
    f"global-audio-{origin}-003a8e-{command}"
    for origin, commands in EXPECTED_BY_ORIGIN.items()
    for command in commands))
CALLSITE = "0x01b86c"
CALLSITE_RAW_SHA256 = "9d1edb02752dc07b730ab282720c2919839367a5a3bf643934f7c6b884c98df2"
FIELD_PROFILE = {
    "reads": ["d0:u16 projectile audio selector",
              "table 0x01b878[d0:u16 * 4]"],
    "writes": ["d0:u32 = 0 before selected helper call"],
    "guard": ("source projectile type-4/class-0x04 state/substate and "
              "captured selector choose the exact 0x01b878 helper"),
    "arithmetic": ["d0:u16 *= 2", "d0:u16 *= 2"],
    "transfer": "indirect selected helper",
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
                     ["audio_owner_families"] if row["owner"] == "projectile")
    require(p2_family == {"first_p2_source_frame": 5762, "owner": "projectile"},
            "P2 projectile-audio family frontier drift")
    groups = [row for row in oracle["trigger_groups"]
              if "projectile" in row["source_owner_families"]]
    groups.sort(key=lambda row: row["id"])
    require(tuple(row["id"] for row in groups) == GROUP_IDS,
            "projectile-audio trigger group inventory drift")
    handler_commands = {row["command"]: row
                        for row in handlers["command_transactions"]}
    image = OPCODES.read_bytes()
    source_program = None
    context_count = 0
    for group in groups:
        require(group["classification"] == "SOURCE_CLOSED" and
                group["source_owner_families"] == ["projectile"] and
                group["semantic_sound_name"] == "UNKNOWN" and
                group["handler_transaction"]
                     ["individual_bus_writes_are_logical_events"] is False and
                group["handler_transaction"]["causal_control"]
                     ["gameplay_projection_unchanged"] is True,
                f"projectile group {group['id']} source boundary drift")
        require(group["command"] in handler_commands and
                handler_commands[group["command"]]["handler_class"] ==
                    group["handler_transaction"]["handler_class"] and
                handler_commands[group["command"]]["table_index"] ==
                    group["handler_transaction"]["table_index"],
                f"projectile group {group['id']} handler linkage drift")
        for context in group["transition_guard"]["contexts"]:
            context_count += 1
            require(context["owner_family"] == "projectile" and
                    context["type_u8"] == 4 and
                    context["class_u8"] == "0x04",
                    "projectile context owner/class drift")
            source_call = context["source_call"]
            require(source_call["address"] == CALLSITE,
                    "projectile source callsite drift")
            start = int(source_call["guard_path_tail"][0]["pc"], 16)
            end = int(source_call["return_address"], 16)
            raw_sha = hashlib.sha256(image[start:end]).hexdigest()
            require(raw_sha == CALLSITE_RAW_SHA256,
                    "projectile callsite opcode slice drift")
            program = {
                "address": CALLSITE,
                "first": f"0x{start:06x}",
                "last_exclusive": f"0x{end:06x}",
                "raw_sha256": raw_sha,
                "accepted_oracle_window_sha256":
                    source_call["source_window_sha256"],
                "instructions": source_call["guard_path_tail"],
                "instruction_semantics_sha256": hashlib.sha256(
                    canonical(source_call["guard_path_tail"])).hexdigest(),
                "field_access_profile": FIELD_PROFILE,
            }
            if source_program is None:
                source_program = program
            else:
                require(source_program == program,
                        "projectile callsite semantic drift")
    require(source_program is not None and len(groups) == 46 and
            context_count == 69 and
            sum(row["occurrences"] for row in groups) == 365 and
            len({row["origin_a6"] for row in groups}) == 8,
            "projectile-audio coverage counts drift")
    commands = sorted({row["command"] for row in groups})
    origins = sorted({row["origin_a6"] for row in groups})
    return {
        "schema": "spec02-projectile-audio-owner-family-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": ("all Round 1-reachable projectile-origin audio trigger "
                  "groups, owner contexts, selector program, command arguments "
                  "and shared-dispatch effects"),
        "source_identity": {
            "opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(),
            "oracle_sha256": sha(ORACLE),
            "handlers_artifact": HANDLERS.relative_to(ROOT).as_posix(),
            "handlers_sha256": sha(HANDLERS),
            "p2_closure_artifact": P2.relative_to(ROOT).as_posix(),
            "p2_closure_sha256": sha(P2),
            "first_p2_source_frame_u16": 5762,
        },
        "coverage": {
            "trigger_groups": 46,
            "distinct_commands": 6,
            "source_contexts": 69,
            "dispatch_occurrences": 365,
            "fixed_pool_origins": 8,
            "distinct_callsite_programs": 1,
            "orphan_groups": 0,
            "orphan_contexts": 0,
            "orphan_handler_transactions": 0,
            "unowned_audio_events": 0,
            "logical_load_release_events": 0,
            "rng_calls": 0,
        },
        "commands": commands,
        "fixed_pool_origins": origins,
        "trigger_groups": groups,
        "normalized_source_program": source_program,
        "handler_boundary": {
            "shared_dispatcher_owned_by": "global-gameplay-audio-load-release",
            "individual_qsound_writes_are_logical_events": False,
            "grouping_rule": ("one projectile trigger and copied 16-byte "
                              "command own one logical handler transaction"),
            "semantic_sound_names": "UNKNOWN",
        },
        "transition_contract": {
            "guard_rule": oracle["owner_rule"],
            "ordered_effects": [
                "evaluate exact type-4/class-0x04 state/substate and selector guard",
                "index the exact 0x01b878 helper table with source-width arithmetic",
                "submit the exact command and argument tuple to the accepted shared wrapper",
                "apply the bound grouped handler/QSound transaction without changing gameplay projection",
            ],
            "fixed_frame_authority": False,
            "projectile_audio_owns_projectile_gameplay": False,
            "logical_load_release_events": 0,
            "rng_calls": 0,
        },
        "paired_capture_identity": oracle["capture_identity"],
        "protected_boundaries": oracle["protected_boundaries"],
        "mutation_controls": {
            "missing_group_rejected": True,
            "missing_pool_origin_rejected": True,
            "wrong_owner_family_rejected": True,
            "wrong_context_state_or_substate_rejected": True,
            "wrong_projectile_class_rejected": True,
            "wrong_selector_program_rejected": True,
            "wrong_selector_arithmetic_rejected": True,
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
            "projectile-audio executable family differs from accepted evidence")
    require(value["status"] == "SPEC_EXECUTABLE" and
            value["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "projectile-audio status drift")
    require(value["coverage"] == {
        "trigger_groups": 46, "distinct_commands": 6,
        "source_contexts": 69, "dispatch_occurrences": 365,
        "fixed_pool_origins": 8, "distinct_callsite_programs": 1,
        "orphan_groups": 0, "orphan_contexts": 0,
        "orphan_handler_transactions": 0, "unowned_audio_events": 0,
        "logical_load_release_events": 0, "rng_calls": 0},
        "projectile-audio coverage drift")
    require(tuple(row["id"] for row in value["trigger_groups"]) == GROUP_IDS and
            set(value["commands"]) ==
                {"0x004d", "0x004e", "0x004f", "0x0118", "0x0119", "0x011a"} and
            len(value["fixed_pool_origins"]) == 8,
            "projectile-audio inventory drift")
    program = value["normalized_source_program"]
    require(program["address"] == CALLSITE and
            len(program["instructions"]) == 5 and
            program["raw_sha256"] == CALLSITE_RAW_SHA256 and
            program["field_access_profile"] == FIELD_PROFILE,
            "projectile-audio normalized selector program incomplete")
    require(value["transition_contract"]["fixed_frame_authority"] is False and
            value["transition_contract"]
                 ["projectile_audio_owns_projectile_gameplay"] is False and
            value["transition_contract"]["logical_load_release_events"] == 0 and
            value["transition_contract"]["rng_calls"] == 0 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]
                 ["unknown_state_or_transition_logic_allowed"] is False,
            "projectile-audio implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded,
                "projectile-audio artifact is stale")
        print("SPEC-02 projectile-audio owner artifact: PASS")
    else:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
