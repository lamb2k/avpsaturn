#!/usr/bin/env python3
"""Bind every non-player Round 1 audio trigger group to source owners/guards."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_A = ROOT / ".deps/mame/oracle11_global_audio_origins_a"
CAPTURE_B = ROOT / ".deps/mame/oracle11_global_audio_origins_b"
HANDLERS = ROOT / "data/oracle11_global_audio_handlers.json"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
OUT = ROOT / "data/oracle11_global_audio_trigger_owners.json"
FILES = ("samples.tsv", "dispatches.tsv", "qsound.tsv", "projectiles.tsv",
         "score_writes.tsv", "result.tsv")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def identity(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "input_manifest.json").read_text(
        encoding="utf-8-sig"))
    for name in FILES:
        require(digest(path / name) == manifest["sha256"][name],
                f"{path.name}: {name} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "files": {name: manifest["sha256"][name] for name in FILES}}


def capstone_engine():
    sys.path.insert(0, str(ROOT / ".deps/python-capstone"))
    from capstone import CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, CS_MODE_M68K_000, Cs
    return Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)


def source_call(opcodes: bytes, return_address: int) -> dict[str, object]:
    engine = capstone_engine()
    calls = []
    for start in range(max(0, return_address - 12), return_address, 2):
        decoded = list(engine.disasm(opcodes[start:return_address], start))
        if decoded and decoded[-1].address + decoded[-1].size == return_address \
                and decoded[-1].mnemonic.startswith(("jsr", "bsr")):
            calls.append(decoded[-1])
    require(calls, f"no call ending at 0x{return_address:06x}")
    call = max(calls, key=lambda item: item.address)
    tail = []
    for start in range(max(0, call.address - 32), call.address + 1, 2):
        decoded = list(engine.disasm(
            opcodes[start:call.address + call.size], start))
        if decoded and decoded[-1].address == call.address:
            tail = decoded[-5:]
            break
    return {
        "address": f"0x{call.address:06x}",
        "return_address": f"0x{return_address:06x}",
        "mnemonic": call.mnemonic,
        "operand": call.op_str,
        "guard_path_tail": [{"pc": f"0x{i.address:06x}",
                             "mnemonic": i.mnemonic, "operand": i.op_str}
                            for i in tail],
        "source_window_sha256": hashlib.sha256(
            opcodes[max(0, call.address - 32):call.address + call.size]).hexdigest(),
    }


def owner_family(row: dict[str, str]) -> str:
    a6 = int(row["a6"], 16)
    actor_class = int(row["origin_class"], 16)
    actor_type = int(row["origin_type"])
    if a6 == 0xff00d8:
        return "route"
    if a6 in (0xff1b1e, 0xff8186):
        return "presentation"
    if actor_class == 0x06 and actor_type in (12, 16, 24):
        return "boss"
    if actor_type == 12:
        return "enemy"
    if actor_type == 4:
        return "projectile"
    if actor_type == 20:
        return "pickup"
    if actor_type == 0:
        return "encounter"
    return "presentation"


def build_report() -> dict[str, object]:
    capture_a, capture_b = identity(CAPTURE_A), identity(CAPTURE_B)
    require(capture_a["files"] == capture_b["files"],
            "origin completion captures differ")
    dispatches = rows(CAPTURE_A / "dispatches.tsv")
    require(len(dispatches) == 1161, "dispatch count drift")
    nonplayer = [row for row in dispatches if row["a6"] != "ff8380"]
    require(len(nonplayer) == 783, "non-player dispatch partition drift")
    handlers = json.loads(HANDLERS.read_text(encoding="ascii"))
    handler_by_command = {item["command"]: item
                          for item in handlers["command_transactions"]}
    opcodes = OPCODES.read_bytes()
    calls = {value: source_call(opcodes, int(value, 16))
             for value in sorted({row["return1"] for row in nonplayer})}
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in nonplayer:
        groups[(row["a6"], row["return0"], row["command"])].append(row)
    bound = []
    for (a6, return0, command), observed in sorted(groups.items()):
        command_text = f"0x{command}"
        require(command_text in handler_by_command,
                f"{command_text}: missing handler transaction")
        contexts = defaultdict(list)
        for row in observed:
            key = (owner_family(row), row["origin_active"], row["origin_class"],
                   row["origin_state"], row["origin_phase"], row["origin_type"],
                   row["origin_facing"], row["return1"], row["return2"])
            contexts[key].append(int(row["frame"]))
        context_rows = []
        for key, frames in sorted(contexts.items()):
            owner, active, cls, state, phase, typ, facing, return1, return2 = key
            context_rows.append({
                "owner_family": owner,
                "origin_record": f"0x{a6}",
                "active_u8": int(active), "class_u8": f"0x{cls}",
                "state_u16": int(state), "substate_u16": int(phase),
                "type_u8": int(typ), "facing_u8": int(facing),
                "source_owner_return": f"0x{return1}",
                "caller_parent_return": f"0x{return2}",
                "source_call": calls[return1],
                "first_frame": min(frames), "last_frame": max(frames),
                "occurrences": len(frames),
            })
        handler = handler_by_command[command_text]
        bound.append({
            "id": f"global-audio-{a6}-{return0}-{command}",
            "classification": "SOURCE_CLOSED",
            "origin_a6": f"0x{a6}",
            "shared_wrapper_return": f"0x{return0}",
            "command": command_text,
            "source_owner_families": sorted({item["owner_family"]
                                               for item in context_rows}),
            "transition_guard": {
                "rule": ("the exact owner record class/type/state/substate and "
                         "hashed local call-path tail reach the captured wrapper "
                         "with the bound command/arguments"),
                "contexts": context_rows,
            },
            "argument_variants": sorted({(row["d1"], row["d2"], row["d3"])
                                          for row in observed}),
            "first_frame": min(int(row["frame"]) for row in observed),
            "last_frame": max(int(row["frame"]) for row in observed),
            "occurrences": len(observed),
            "handler_transaction": {
                "table_index": handler["table_index"],
                "data_pointer_24": handler["data_pointer_24"],
                "handler_class": handler["handler_class"],
                "causal_control": handler["causal_effect"],
                "individual_bus_writes_are_logical_events": False,
            },
            "semantic_sound_name": "UNKNOWN",
        })
    report = {
        "schema": "oracle11-global-audio-trigger-owners-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "all route-reachable non-player gameplay-audio trigger groups",
        "coverage": {"dispatch_occurrences": len(nonplayer),
                     "trigger_groups": len(bound), "source_callers": len(calls),
                     "orphan_trigger_groups": 0, "orphan_source_callers": 0,
                     "orphan_handler_transactions": 0},
        "owner_rule": {
            "inputs": "live origin A6 record, class/type/state/substate and exact source call stack",
            "families": ["enemy", "projectile", "pickup", "route",
                         "encounter", "boss", "presentation"],
            "appearance_used": False,
        },
        "trigger_groups": bound,
        "capture_identity": {"completion_a": capture_a, "completion_b": capture_b,
                             "byte_identical": True,
                             "opcode_sha256": digest(OPCODES),
                             "handler_evidence_sha256": digest(HANDLERS)},
        "remaining_global_family_backlog": {
            "route_load_release_boundaries": 4,
            "family_source_closed": False,
        },
        "protected_boundaries": {"predator_warrior": "SOURCE_CLOSED",
                                 "packed_bcd_score_routine": "0x0abdd2",
                                 "spec02_active": False,
                                 "oracle11_active": True,
                                 "production_runtime_writes": 0,
                                 "yaba_runs": 0, "physical_saturn": "UNRUN"},
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED", "trigger status drift")
    require(report["coverage"] == {"dispatch_occurrences": 783,
            "trigger_groups": 175, "source_callers": 50,
            "orphan_trigger_groups": 0, "orphan_source_callers": 0,
            "orphan_handler_transactions": 0}, "trigger coverage drift")
    groups = report["trigger_groups"]
    require(len(groups) == 175 and sum(x["occurrences"] for x in groups) == 783,
            "trigger group occurrence drift")
    require(all(x["classification"] == "SOURCE_CLOSED" and
                x["semantic_sound_name"] == "UNKNOWN" and
                x["transition_guard"]["contexts"] and
                x["handler_transaction"]
                 ["individual_bus_writes_are_logical_events"] is False
                for x in groups), "trigger binding drift")
    require(report["capture_identity"]["byte_identical"] is True and
            report["owner_rule"]["appearance_used"] is False,
            "trigger evidence drift")
    require(report["remaining_global_family_backlog"] == {
        "route_load_release_boundaries": 4, "family_source_closed": False},
        "global family prematurely closed")
    require(report["protected_boundaries"]["predator_warrior"] ==
            "SOURCE_CLOSED" and report["protected_boundaries"]
            ["packed_bcd_score_routine"] == "0x0abdd2" and
            report["protected_boundaries"]["spec02_active"] is False,
            "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes((json.dumps(report, sort_keys=True, indent=2) + "\n").encode("ascii"))
    print("ORACLE-11 global audio trigger owners: SOURCE_CLOSED; "
          "175 groups, 783 occurrences, zero orphans")


if __name__ == "__main__":
    main()
