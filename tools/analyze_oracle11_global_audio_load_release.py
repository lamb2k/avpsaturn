#!/usr/bin/env python3
"""Start the global Round 1 gameplay-audio/load/release closure family."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_A = ROOT / ".deps" / "mame" / "oracle11_player_audio_e"
BASE_B = ROOT / ".deps" / "mame" / "oracle11_player_audio_f"
ORACLE10 = (ROOT / ".deps" / "mame" /
            "oracle10_round1_system_census_e" / "baseline")
TRANSPORT_A = ROOT / ".deps" / "mame" / "oracle11_global_audio_transport_b"
TRANSPORT_B = ROOT / ".deps" / "mame" / "oracle11_global_audio_transport_c"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
ROUTE = ROOT / "data" / "oracle10_round1_route.json"
PLAYER_AUDIO = ROOT / "data" / "oracle11_predator_player_audio.json"
HANDLERS = ROOT / "data" / "oracle11_global_audio_handlers.json"
OWNERS = ROOT / "data" / "oracle11_global_audio_trigger_owners.json"
OUT = ROOT / "data" / "oracle11_global_audio_load_release.json"
IDENTICAL_FILES = ("samples.tsv", "dispatches.tsv", "qsound.tsv",
                   "projectiles.tsv", "score_writes.tsv", "result.tsv")
TRANSPORT_FILES = IDENTICAL_FILES + ("audio_shared_reads.tsv",
                                    "audio_bus_writers.tsv")
PAYLOAD_WRITERS = {
    "0x618006": "0x0018ae", "0x618008": "0x0018b6",
    "0x618000": "0x0018be", "0x618002": "0x0018c6",
    "0x61800c": "0x0018ce", "0x61800e": "0x0018d6",
    "0x618010": "0x0018de", "0x618016": "0x0018e6",
    "0x618018": "0x0018ee", "0x618012": "0x0018f6",
    "0x618014": "0x0018fe", "0x61801e": "0x001908",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def capture_identity(path: Path, files=IDENTICAL_FILES) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    for filename in files:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {"manifest_sha256": digest(manifest_path),
            "files": {name: manifest["sha256"][name] for name in files},
            "audio_rom_sha256": manifest.get("audio_rom_sha256")}


def build_report() -> dict[str, object]:
    identity_a = capture_identity(BASE_A)
    identity_b = capture_identity(BASE_B)
    require(identity_a["files"] == identity_b["files"],
            "global baseline completion captures differ")
    dispatches = rows(BASE_A / "dispatches.tsv")
    require(len(dispatches) == 1161, "main audio enqueue count drift")

    player = [row for row in dispatches if row["a6"].lower() == "ff8380"]
    nonplayer = [row for row in dispatches if row["a6"].lower() != "ff8380"]
    require(len(player) == 378 and len(nonplayer) == 783,
            "player/global dispatch partition drift")

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in nonplayer:
        key = (row["a6"], row["return0"], row["command"])
        groups[key].append(row)
    trigger_backlog = []
    for key, observed in sorted(groups.items()):
        arguments = sorted({(row["d1"], row["d2"], row["d3"])
                            for row in observed})
        return_chains = sorted({(row["return0"], row["return1"], row["return2"])
                                for row in observed})
        trigger_backlog.append({
            "origin_a6": f"0x{key[0]}",
            "shared_wrapper_return": f"0x{key[1]}",
            "return_chain_variants": [
                [f"0x{value}" for value in chain] for chain in return_chains],
            "command": f"0x{key[2]}",
            "argument_variants": [
                {"d1": f"0x{d1}", "d2": f"0x{d2}", "d3": f"0x{d3}"}
                for d1, d2, d3 in arguments],
            "occurrences": len(observed),
            "first_frame": int(observed[0]["frame"]),
            "last_frame": int(observed[-1]["frame"]),
            "classification": "OBSERVED",
            "exact_next_experiment": (
                "bind origin class/type/state and the first source-side caller, "
                "then suppress this trigger and compare downstream audio and "
                "gameplay invariants"),
        })
    require(len(trigger_backlog) == 175,
            "global non-player trigger-provenance backlog drift")

    shared_rows = rows(ORACLE10 / "qsound_writers.tsv")
    observed_writers = {
        f"0x{int(row['address'], 16):06x}": {
            "pc": f"0x{int(row['pc'], 16):06x}",
            "count": int(row["count"]),
            "first_frame": int(row["first_frame"]),
            "last_frame": int(row["last_frame"]),
        }
        for row in shared_rows
        if int(row["address"], 16) != 0x619FFC
    }
    require(set(observed_writers) == set(PAYLOAD_WRITERS),
            "shared payload address set drift")
    require(all(observed_writers[address]["pc"] == pc and
                observed_writers[address]["count"] == len(dispatches)
                for address, pc in PAYLOAD_WRITERS.items()),
            "shared payload writer/count drift")

    transport_a = capture_identity(TRANSPORT_A, TRANSPORT_FILES)
    transport_b = capture_identity(TRANSPORT_B, TRANSPORT_FILES)
    require(transport_a["files"] == transport_b["files"],
            "audio-CPU transport captures differ")
    require(transport_a["audio_rom_sha256"] ==
            "88f7f38e64c5d5c16264768230fc599a4f8de5904633a814789a192a8baa19b3",
            "audio program ROM identity drift")
    audio_shared = rows(TRANSPORT_A / "audio_shared_reads.tsv")
    audio_bus = rows(TRANSPORT_A / "audio_bus_writers.tsv")
    shared_map = {(row["address"], row["pc"]): int(row["count"])
                  for row in audio_shared}
    expected_shared = {(f"c{offset:03x}", "0066"): 1161
                       for offset in range(0x000, 0x010)}
    expected_shared.update({("c00f", "004a"): 67189,
                            ("cffd", "0042"): 67189,
                            ("cffe", "006e"): 67189})
    require(shared_map == expected_shared,
            "audio-CPU shared-RAM reader map drift")
    bus_map = {(row["address"], row["pc"]): int(row["count"])
               for row in audio_bus}
    require(bus_map == {("d000", "0ad7"): 489834,
                        ("d001", "0ad3"): 489834,
                        ("d002", "0adb"): 489834},
            "audio-CPU QSound-bus primitive drift")

    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    player_audio = json.loads(PLAYER_AUDIO.read_text(encoding="ascii"))
    handlers = json.loads(HANDLERS.read_text(encoding="ascii"))
    owners = json.loads(OWNERS.read_text(encoding="ascii"))
    require(player_audio["status"] == "SOURCE_CLOSED" and
            player_audio["boundary"]["global_backlog_begins"].startswith(
                "0x001880"), "player/global boundary drift")
    require(handlers["status"] == "SOURCE_CLOSED" and
            handlers["coverage"]["orphan_shared_commands"] == 0 and
            handlers["coverage"]["orphan_command_identities"] == 0 and
            handlers["coverage"]["orphan_qsound_transaction_groups"] == 0 and
            handlers["handler_paths"]["orphan_paths"] == 0,
            "audio command handler checkpoint drift")
    require(owners["status"] == "SOURCE_CLOSED" and
            owners["coverage"]["trigger_groups"] == 175 and
            owners["coverage"]["orphan_trigger_groups"] == 0 and
            owners["coverage"]["orphan_source_callers"] == 0,
            "non-player trigger-owner checkpoint drift")
    owner_keys = {(item["origin_a6"], item["shared_wrapper_return"],
                   item["command"]): item for item in owners["trigger_groups"]}
    for item in trigger_backlog:
        key = (item["origin_a6"], item["shared_wrapper_return"], item["command"])
        require(key in owner_keys, f"unbound trigger owner {key}")
        item["classification"] = "SOURCE_CLOSED"
        item["source_owner_families"] = owner_keys[key]["source_owner_families"]
        item["evidence"] = "data/oracle11_global_audio_trigger_owners.json"
        item["exact_next_experiment"] = None
    opcodes = OPCODES.read_bytes()
    load_frames = route["load_release_boundary_frames"]
    require(load_frames == [5565, 5566, 6200, 12799],
            "load/release boundary frame drift")

    report = {
        "schema": "oracle11-global-gameplay-audio-load-release-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "PARTIAL",
        "scope": "global Round 1 gameplay-audio/load/release authority",
        "accepted_subcheckpoint": {
            "id": "main-queue-to-qsound-shared-ram-transport",
            "classification": "SOURCE_CLOSED",
            "source_routine": "0x001880..0x001914",
            "entry_guard": (
                "read pointer 0xff816e differs from write pointer 0xff8170 "
                "and QSound shared ready byte 0x61801f equals 0xff"),
            "queue": {
                "base": "A5-0x7578 (0xff0bd8 in the captured route)",
                "entry_size": 16,
                "pointer_mask": "0x03f0",
                "producer": "0x001922..0x001956",
                "argument_writers": ["0x00193c", "0x001940", "0x001944"],
                "consumer_pointer_writer": "0x001910",
            },
            "shared_payload_writers": observed_writers,
            "ready_release_writer": "0x001900 -> 0x61801f = 0",
            "transactions_in_each_completion": len(dispatches),
            "all_payload_writer_counts_match_transactions": True,
            "source_opcode_sha256": digest(OPCODES),
            "routine_sha256": hashlib.sha256(opcodes[0x1880:0x1916]).hexdigest(),
            "semantic_sound_names_inferred": False,
            "mutation_evidence": (
                "the accepted 38 player-edge suppressions each change the "
                "downstream QSound bus through this data-independent transport"),
        },
        "player_boundary": {
            "classification": "SOURCE_CLOSED",
            "evidence": "data/oracle11_predator_player_audio.json",
            "dispatch_occurrences": len(player),
            "ownership_ends_at": "0x001922 main-side enqueue entry",
        },
        "accepted_audio_cpu_subcheckpoints": [
            {
                "id": "qsound-shared-ram-command-ingress",
                "classification": "SOURCE_CLOSED",
                "source_routine": "audio ROM 0x0038..0x0074",
                "guards": [
                    "0xcffd equals 0x88",
                    "incremented 0xc00f command-ready byte is nonzero",
                ],
                "reads": {
                    "0xcffd": "tap PC 0x0042 / 67,189 polls",
                    "0xc00f": "tap PC 0x004a / 67,189 polls",
                    "0xc000..0xc00f": "LDIR tap PC 0x0066 / 1,161 copies",
                    "0xcffe": "tap PC 0x006e / 67,189 reads",
                },
                "writes": [
                    "copy 16-byte command to 0xf100 plus 0xf007 ring offset",
                    "advance 0xf007 by 0x10",
                    "write 0xff to 0xc00f ready byte",
                    "copy 0xcffe to 0xf040",
                ],
                "transactions_in_each_completion": 1161,
            },
            {
                "id": "qsound-bus-write-primitive",
                "classification": "SOURCE_CLOSED",
                "source_routine": "audio ROM 0x0abc..0x0adb",
                "guard": "poll 0xd007 until QSound ready bit permits the write",
                "arguments": (
                    "DE-derived 16-bit value to 0xd001 low then 0xd000 high; "
                    "0xf00d plus 0x80 to 0xd002 register select"),
                "observed_writer_pcs": {
                    "0xd001": "0x0ad3", "0xd000": "0x0ad7",
                    "0xd002": "0x0adb",
                },
                "writes_per_port_in_each_completion": 489834,
                "semantic_sound_names_inferred": False,
            },
            {
                "id": "audio-command-dispatcher-table-handlers",
                "classification": "SOURCE_CLOSED",
                "source_routine": "audio ROM 0x01bd..0x0294",
                "evidence": "data/oracle11_global_audio_handlers.json",
                "evidence_sha256": digest(HANDLERS),
                "copied_and_dispatched_commands": 1161,
                "command_identities": 72,
                "accepted_player_command_controls": 29,
                "new_global_command_controls": 43,
                "orphan_shared_commands": 0,
                "orphan_handler_paths": 0,
                "orphan_qsound_transaction_groups": 0,
                "logical_event_owner": "audio command plus handler transaction",
                "individual_bus_writes_are_logical_events": False,
                "semantic_sound_names_inferred": False,
            },
        ],
        "remaining_audio_trigger_backlog": {
            "classification": "SOURCE_CLOSED",
            "dispatch_occurrences": len(nonplayer),
            "provenance_groups": len(trigger_backlog),
            "orphan_trigger_groups": 0,
            "groups": trigger_backlog,
        },
        "remaining_transport_backlog": {
            "classification": "SOURCE_CLOSED",
            "scope": "audio-CPU command dispatch, state updates and command tables",
            "orphan_shared_commands": 0,
            "orphan_handler_paths": 0,
            "orphan_qsound_transaction_groups": 0,
            "exact_next_experiment": None,
        },
        "load_release_backlog": {
            "classification": "OBSERVED",
            "boundary_frames": load_frames,
            "exact_next_experiment": (
                "capture exact writers, callers, guards, data ownership, and "
                "paired suppressions for each of the four route boundaries"),
        },
        "score_negative_control": {
            "status": "PASS",
            "excluded_routines": ["0x0abdd2..0x0abe18", "0x0abe2a..0x0abf16"],
            "classification": "PACKED_BCD_SCORE_AUTHORITY",
            "accepted_as_audio_owner": False,
            "timing_or_temporal_adjacency_used": False,
        },
        "capture_identity": {"completion_a": identity_a,
                             "completion_b": identity_b,
                             "byte_identical": True,
                             "audio_transport_a": transport_a,
                             "audio_transport_b": transport_b,
                             "audio_transport_byte_identical": True},
        "protected_boundaries": {
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-global-gameplay-audio-load-release-v1"
            and report["status"] == "PARTIAL",
            "global family status drift")
    checkpoint = report["accepted_subcheckpoint"]
    require(checkpoint["classification"] == "SOURCE_CLOSED" and
            checkpoint["source_routine"] == "0x001880..0x001914" and
            checkpoint["transactions_in_each_completion"] == 1161 and
            checkpoint["all_payload_writer_counts_match_transactions"] is True
            and checkpoint["semantic_sound_names_inferred"] is False,
            "shared main-side transport closure drift")
    require(len(checkpoint["shared_payload_writers"]) == 12 and
            all(row["count"] == 1161
                for row in checkpoint["shared_payload_writers"].values()),
            "shared payload coverage drift")
    backlog = report["remaining_audio_trigger_backlog"]
    require(backlog["dispatch_occurrences"] == 783 and
            backlog["provenance_groups"] == 175 and
            backlog["classification"] == "SOURCE_CLOSED" and
            backlog["orphan_trigger_groups"] == 0 and
            len(backlog["groups"]) == 175 and
            all(group["classification"] == "SOURCE_CLOSED"
                for group in backlog["groups"]),
            "global trigger backlog drift")
    audio_cpu = report["accepted_audio_cpu_subcheckpoints"]
    require(len(audio_cpu) == 3 and
            all(item["classification"] == "SOURCE_CLOSED" for item in audio_cpu)
            and audio_cpu[0]["transactions_in_each_completion"] == 1161 and
            audio_cpu[1]["writes_per_port_in_each_completion"] == 489834 and
            audio_cpu[1]["semantic_sound_names_inferred"] is False and
            audio_cpu[2]["copied_and_dispatched_commands"] == 1161 and
            audio_cpu[2]["command_identities"] == 72 and
            audio_cpu[2]["orphan_shared_commands"] == 0 and
            audio_cpu[2]["orphan_handler_paths"] == 0 and
            audio_cpu[2]["orphan_qsound_transaction_groups"] == 0 and
            audio_cpu[2]["individual_bus_writes_are_logical_events"] is False,
            "audio-CPU subcheckpoint drift")
    require(report["capture_identity"]["audio_transport_byte_identical"] is True
            and report["remaining_transport_backlog"]["classification"] ==
            "SOURCE_CLOSED" and
            report["load_release_backlog"]["classification"] == "OBSERVED" and
            report["load_release_backlog"]["boundary_frames"] ==
            [5565, 5566, 6200, 12799], "remaining boundary backlog drift")
    negative = report["score_negative_control"]
    require(negative["accepted_as_audio_owner"] is False and
            negative["timing_or_temporal_adjacency_used"] is False and
            negative["classification"] == "PACKED_BCD_SCORE_AUTHORITY",
            "score-only negative control drift")
    require(report["protected_boundaries"] == {
        "production_runtime_writes": 0, "yaba_runs": 0,
        "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
        "salvage08_active": False, "physical_saturn": "UNRUN",
        "spec02_active": False, "oracle11_active": True,
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 global audio/load/release: PARTIAL; 175 trigger groups "
          "SOURCE_CLOSED; 4 load/release edges remain")


if __name__ == "__main__":
    main()
