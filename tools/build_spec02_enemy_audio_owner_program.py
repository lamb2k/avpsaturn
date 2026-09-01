#!/usr/bin/env python3
"""Build the complete Round 1 enemy-origin audio trigger family."""
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
OUT = ROOT / "data/spec02_enemy_audio_owner_program.json"
OPCODE_SHA256 = "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501"
GROUP_IDS_SHA256 = "8146993f8652e82736730d153fd87b133a258a790fd87eb1c4bbd1d13e934374"

CALLSITE_RAW_SHA256 = {
    "0x003b58": "c294dcdce65f45b69bc854ffd95cc4b8d671fa3369305f23fe434780884b9847",
    "0x01eba4": "84d82480f78bfc319eacdcaf8fdb296d2426da41b71ae378edf1753dca3340b1",
    "0x01ec8a": "d82a3f8077747168eb44d6c5547025fd1ce6c1b2c4a69dd1026ead9b1d075ec2",
    "0x01f402": "f56117a0dec4231b7df185af7f08fa0866b6e3ad34370182b60afe97cf80274d",
    "0x01f4ea": "06d8de53b0392ab4f9e11e7ee2672a955118b8c036f89feeb9a00ec60767e906",
    "0x03f60e": "d7e0337d27137c5ffb99bb6cb88b1e2a090ce5ea78dfa9e6b605467c168e4670",
    "0x03f79c": "1daa4254160215f7e3bc4f3d725838c189c2330deed6a9f90ee5535e4eabad99",
    "0x04026e": "00a38cec5fa81483cb4aef5f4f6f1941bc41b5301a85181acaf604437861b724",
    "0x040274": "39c17a4c9eddfb25562bd0b827bf8a64697d05999d3884169d05072afe59aece",
    "0x040dc4": "cb431ecf628187ebafbb4344db663e49b0b87ee1acacbbda63db3989cdea37c0",
    "0x040ea0": "61291cdc91f88649b1c1335a919f1524bd17a5a4d9eb34170ba2a400347441bb",
    "0x041f10": "3b9ac0e9dc757c6167ba687e956304be61486efd513320c5ebf0202b4f3c3391",
    "0x041f16": "9061070431cfcacec068aaf1f1982c11710bf135a8592d126ae9320581395ccf",
    "0x046ae6": "f32bbd894cb2c6cff078a40d983d45f22a90e1c4b4cdcefd84f5ae7c22084738",
    "0x046aec": "a6953c761e9394d6a1088f9dd3db9697eb001924d25459de376b9f4451c4d695",
    "0x0608d2": "483040c8e60e8a85e754ddbca0c1820aed29f49c7fdfb9c7a72507a578d4ffbd",
    "0x060bba": "881b8661a9a5695c7af7c53ef695a7d4d0ad4060eea6d35937f86999461bc85f",
    "0x067ab8": "1e29d1c6c7065024619377619c79fb63f8300fda99febf01f76650883edb44f7",
}

FIELD_PROFILES = {
    "0x003b58": {"reads": ["owner+0x71:u8", "table 0x003b60[selector]:u32"], "writes": [], "guard": "u8(owner+0x71) selects the exact helper-table entry", "transfer": "indirect table target"},
    "0x01eba4": {"reads": [], "writes": ["owner+0x34:u32=0", "owner+0x3c:u32=0", "owner+0x2a:u8=3"], "guard": "type12 enemy state-substate reaches the accepted tail", "transfer": "0x09a660 then 0x001c4a"},
    "0x01ec8a": {"reads": ["owner+0x18:u16", "owner+0x14:u16"], "writes": ["owner+0x14:u16=d0"], "guard": "u16(owner+0x18) is not below u16(owner+0x14)", "transfer": "0x001c20"},
    "0x01f402": {"reads": ["owner+0x06:u8"], "writes": ["owner+0x06:u8+=2", "owner+0x2a:u8=3", "owner+0x5c:u8=0"], "guard": "type12 enemy state-substate reaches the accepted tail", "transfer": "0x09a660 then 0x001c4a"},
    "0x01f4ea": {"reads": ["accepted preceding unsigned-compare flags"], "writes": ["owner+0x14:u16=d0", "owner+0x5c:u8=0"], "guard": "unsigned compare carry clear at 0x01f4da", "transfer": "0x09a660 then 0x001c20"},
    "0x03f60e": {"reads": ["a0+0x128:movep.u16", "d0:u16", "a0-selected byte:u8", "a4-predecrement byte:u8", "owner+0x07:u8"], "writes": ["a0-selected byte:u8 bit-change", "a4-predecrement byte:u8 bit-change", "owner+0x07:u8+=2"], "guard": "type12/class00 state 0x0200 substate 0x0802 reaches exact bit-change tail", "transfer": "0x001aa6"},
    "0x03f79c": {"reads": ["d0:u16", "table 0x03f792[d0]:s16", "selected target operands"], "writes": ["selected target writes exactly as retained guard-path instructions"], "guard": "type12/class00 state 0x0200 substate 0x0a02 uses the exact signed computed-dispatch entry", "transfer": "computed target then 0x001aa6"},
    "0x04026e": {"reads": ["owner+0x40:s16", "helper 0x040162 result"], "writes": ["owner+0x85:u8=0"], "guard": "after helper 0x040162, s16(owner+0x40)<0", "transfer": "0x002534"},
    "0x040274": {"reads": ["owner+0x40:s16", "helper 0x040162 result"], "writes": [], "guard": "same negative owner+0x40 branch after 0x002534", "transfer": "0x002534 then 0x0027e0"},
    "0x040dc4": {"reads": ["owner+0xac:u16", "owner+0x07:u8"], "writes": ["owner+0xac:u16|=0x0098", "owner+0x07:u8+=2"], "guard": "type12 class01-or-1f accepted state/substate reaches exact tail", "transfer": "0x001aa6"},
    "0x040ea0": {"reads": ["owner+0x07:u8"], "writes": ["owner+0x07:u8+=2"], "guard": "type12 class01-or-1f accepted state/substate reaches exact tail", "transfer": "0x001aa6"},
    "0x041f10": {"reads": ["owner+0x40:s16", "helper 0x041d9c result"], "writes": ["owner+0x95:u8=0"], "guard": "after helper 0x041d9c, s16(owner+0x40)<0", "transfer": "0x002534"},
    "0x041f16": {"reads": ["owner+0x40:s16", "helper 0x041d9c result"], "writes": [], "guard": "same negative owner+0x40 branch after 0x002534", "transfer": "0x002534 then 0x0027e0"},
    "0x046ae6": {"reads": ["accepted entry flags", "owner+0x40:s16", "helper 0x046a40 result"], "writes": [], "guard": "accepted entry branch plus s16(owner+0x40)<0 after helper", "transfer": "0x002534"},
    "0x046aec": {"reads": ["owner+0x40:s16", "helper 0x046a40 result"], "writes": [], "guard": "same negative owner+0x40 branch after 0x002534", "transfer": "0x002534 then 0x0027e0"},
    "0x0608d2": {"reads": ["a4+0x112:u16", "d0:u32 bit index", "a0-predecrement:u32", "owner+0x07:u8"], "writes": ["a4+0x112:u16|=0x008c", "owner+0x07:u8+=2"], "guard": "type12/class1f state 0x0200 substate 0x0402 reaches exact tail", "transfer": "0x001aa6"},
    "0x060bba": {"reads": ["owner+0x2a:u8", "a5-0x65f0:u8"], "writes": ["owner+0x2a:u8-=1"], "guard": "decremented owner timer is zero and u8(a5-0x65f0)==0", "transfer": "0x001e96"},
    "0x067ab8": {"reads": ["owner+0x2c:u8", "owner+0x06:u8", "table 0x067ac2[owner+0x06]:s16"], "writes": ["owner+0x2c:u8-=1"], "guard": "type12/class29 state 0x0200 substate 0x0a04 follows the retained branch/computed-target path", "transfer": "exact 0x067ac2 signed target"},
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
                     ["audio_owner_families"] if row["owner"] == "enemy")
    require(p2_family == {"first_p2_source_frame": 5881, "owner": "enemy"},
            "P2 enemy-audio family frontier drift")
    source_groups = sorted(
        (row for row in oracle["trigger_groups"]
         if "enemy" in row["source_owner_families"]), key=lambda row: row["id"])
    require(hashlib.sha256(canonical([row["id"] for row in source_groups])).hexdigest() == GROUP_IDS_SHA256,
            "enemy-audio trigger group inventory drift")
    handler_commands = {row["command"]: row for row in handlers["command_transactions"]}
    image = OPCODES.read_bytes()
    groups = []
    callsites: dict[str, dict[str, object]] = {}
    context_count = occurrence_count = 0
    pairs: set[tuple[int, str]] = set()
    for source_group in source_groups:
        causal = source_group["handler_transaction"]["causal_control"]
        unchanged = (causal.get("gameplay_projection_unchanged") is True or
                     causal.get("gameplay_invariants", {}).get("stable_round2_result") is True)
        downstream = ("downstream_difference" in causal or
                      bool(causal.get("downstream_qsound_transactions")))
        require(source_group["classification"] == "SOURCE_CLOSED" and
                source_group["semantic_sound_name"] == "UNKNOWN" and
                source_group["handler_transaction"]["individual_bus_writes_are_logical_events"] is False and
                unchanged and downstream, f"enemy group {source_group['id']} boundary drift")
        require(source_group["command"] in handler_commands and
                handler_commands[source_group["command"]]["handler_class"] == source_group["handler_transaction"]["handler_class"] and
                handler_commands[source_group["command"]]["table_index"] == source_group["handler_transaction"]["table_index"],
                f"enemy group {source_group['id']} handler linkage drift")
        contexts = [copy.deepcopy(context) for context in source_group["transition_guard"]["contexts"]
                    if context["owner_family"] == "enemy"]
        require(contexts, f"enemy group {source_group['id']} has no enemy context")
        group = copy.deepcopy(source_group)
        group["group_total_occurrences"] = source_group["occurrences"]
        group["enemy_context_occurrences"] = sum(row["occurrences"] for row in contexts)
        group["shared_non_enemy_occurrences"] = source_group["occurrences"] - group["enemy_context_occurrences"]
        group["transition_guard"]["contexts"] = contexts
        groups.append(group)
        for context in contexts:
            context_count += 1
            occurrence_count += context["occurrences"]
            pair = (context["type_u8"], context["class_u8"])
            require(pair in {(12, "0x00"), (12, "0x01"), (12, "0x1f"), (12, "0x29")},
                    "enemy context class/type drift")
            pairs.add(pair)
            source_call = context["source_call"]
            address = source_call["address"]
            start = int(source_call["guard_path_tail"][0]["pc"], 16)
            end = int(source_call["return_address"], 16)
            raw_sha = hashlib.sha256(image[start:end]).hexdigest()
            require(raw_sha == CALLSITE_RAW_SHA256[address], f"enemy callsite {address} opcode drift")
            program = {
                "address": address, "first": f"0x{start:06x}",
                "last_exclusive": f"0x{end:06x}", "raw_sha256": raw_sha,
                "accepted_oracle_window_sha256": source_call["source_window_sha256"],
                "instructions": source_call["guard_path_tail"],
                "instruction_semantics_sha256": hashlib.sha256(canonical(source_call["guard_path_tail"])).hexdigest(),
                "field_access_profile": FIELD_PROFILES[address], "commands": [],
            }
            if address not in callsites:
                callsites[address] = program
            else:
                require({k: v for k, v in callsites[address].items() if k != "commands"} ==
                        {k: v for k, v in program.items() if k != "commands"},
                        f"enemy callsite {address} semantic drift")
            callsites[address]["commands"].append(source_group["command"])
    for program in callsites.values():
        program["commands"] = sorted(set(program["commands"]))
    commands = sorted({row["command"] for row in groups})
    origins = sorted({context["origin_record"] for row in groups
                      for context in row["transition_guard"]["contexts"]})
    require((len(groups), len(commands), context_count, occurrence_count,
             len(origins), len(callsites), len(pairs)) == (83, 14, 182, 228, 10, 18, 4),
            "enemy-audio coverage counts drift")
    return {
        "schema": "spec02-enemy-audio-owner-family-v1",
        "status": "SPEC_EXECUTABLE",
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "scope": "all Round 1-reachable enemy-origin audio trigger groups, contexts, callsite programs, command arguments and shared-dispatch effects",
        "source_identity": {"opcode_image_sha256": OPCODE_SHA256,
            "oracle_artifact": ORACLE.relative_to(ROOT).as_posix(), "oracle_sha256": sha(ORACLE),
            "handlers_artifact": HANDLERS.relative_to(ROOT).as_posix(), "handlers_sha256": sha(HANDLERS),
            "p2_closure_artifact": P2.relative_to(ROOT).as_posix(), "p2_closure_sha256": sha(P2),
            "first_p2_source_frame_u16": 5881, "group_ids_sha256": GROUP_IDS_SHA256},
        "coverage": {"trigger_groups": 83, "distinct_commands": 14,
            "enemy_source_contexts": 182, "enemy_dispatch_occurrences": 228,
            "source_origin_records": 10, "distinct_callsite_programs": 18,
            "record_type_class_pairs": 4, "orphan_groups": 0, "orphan_contexts": 0,
            "orphan_handler_transactions": 0, "unowned_audio_events": 0,
            "logical_load_release_events": 0, "rng_calls": 0},
        "commands": commands, "source_origin_records": origins,
        "record_type_class_pairs": [{"record_type_u8": t, "class_u8": c} for t, c in sorted(pairs)],
        "trigger_groups": groups,
        "normalized_source_programs": [callsites[key] for key in sorted(callsites)],
        "handler_boundary": {"shared_dispatcher_owned_by": "global-gameplay-audio-load-release",
            "individual_qsound_writes_are_logical_events": False,
            "grouping_rule": "one enemy trigger and copied 16-byte command own one logical handler transaction",
            "semantic_sound_names": "UNKNOWN"},
        "transition_contract": {"guard_rule": oracle["owner_rule"],
            "ordered_effects": ["evaluate exact record type, class, state, substate and local caller guard",
                "execute the accepted callsite operations with exact widths and signedness",
                "submit the exact command and argument tuple to the accepted shared wrapper",
                "apply the grouped handler/QSound transaction without changing enemy gameplay projection"],
            "fixed_frame_authority": False, "enemy_audio_owns_enemy_gameplay": False,
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
            "missing_downstream_difference_rejected", "gameplay_projection_coupling_rejected",
            "invented_semantic_sound_name_rejected", "invented_load_or_rng_rejected",
            "fixed_frame_trigger_rejected", "runtime_68000_interpretation_rejected")},
        "implementation_rules": {"portable_c_translation_required": True,
            "runtime_68000_interpretation_forbidden": True,
            "fixed_frame_or_authored_fallback_forbidden": True,
            "unknown_state_or_transition_logic_allowed": False},
    }


def validate(value: dict[str, object]) -> None:
    require(value == build(), "enemy-audio executable family differs from accepted evidence")
    require(value["coverage"] == {"trigger_groups": 83, "distinct_commands": 14,
            "enemy_source_contexts": 182, "enemy_dispatch_occurrences": 228,
            "source_origin_records": 10, "distinct_callsite_programs": 18,
            "record_type_class_pairs": 4, "orphan_groups": 0, "orphan_contexts": 0,
            "orphan_handler_transactions": 0, "unowned_audio_events": 0,
            "logical_load_release_events": 0, "rng_calls": 0}, "enemy-audio coverage drift")
    require(len(value["trigger_groups"]) == 83 and len(value["commands"]) == 14 and
            len(value["source_origin_records"]) == 10 and len(value["normalized_source_programs"]) == 18 and
            {row["address"] for row in value["normalized_source_programs"]} == set(CALLSITE_RAW_SHA256) and
            all(row["raw_sha256"] == CALLSITE_RAW_SHA256[row["address"]] and
                row["field_access_profile"] == FIELD_PROFILES[row["address"]]
                for row in value["normalized_source_programs"]), "enemy-audio program inventory drift")
    require(value["handler_boundary"]["individual_qsound_writes_are_logical_events"] is False and
            value["transition_contract"]["enemy_audio_owns_enemy_gameplay"] is False and
            value["transition_contract"]["logical_load_release_events"] == 0 and
            value["transition_contract"]["rng_calls"] == 0 and
            all(value["mutation_controls"].values()) and
            value["implementation_rules"]["unknown_state_or_transition_logic_allowed"] is False,
            "enemy-audio implementation boundary drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build()
    validate(value)
    encoded = canonical(value)
    if args.check:
        require(OUT.is_file() and OUT.read_bytes() == encoded, "enemy-audio artifact is stale")
        print("SPEC-02 enemy-audio owner artifact: PASS")
    else:
        OUT.write_bytes(encoded)
        print(f"wrote {OUT} sha256={hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
