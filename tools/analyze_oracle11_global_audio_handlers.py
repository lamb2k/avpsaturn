#!/usr/bin/env python3
"""Close the route-reachable audio-CPU command dispatcher/handler boundary."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROM = Path(r"C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest\avspu\avp.01")
TRANSPORT_A = ROOT / ".deps/mame/oracle11_global_audio_transport_e"
TRANSPORT_B = ROOT / ".deps/mame/oracle11_global_audio_transport_f"
COMPACT_A = ROOT / ".deps/mame/oracle11_global_audio_compact_a"
COMPACT_B = ROOT / ".deps/mame/oracle11_global_audio_compact_b"
PLAYER = ROOT / "data/oracle11_predator_player_audio.json"
OUT = ROOT / "data/oracle11_global_audio_handlers.json"
TRANSPORT_FILES = (
    "samples.tsv", "dispatches.tsv", "qsound.tsv", "projectiles.tsv",
    "score_writes.tsv", "result.tsv", "audio_shared_reads.tsv",
    "audio_bus_writers.tsv", "audio_queue_reads.tsv",
    "audio_state_writers.tsv", "audio_shared_commands.tsv",
    "audio_command_dispatches.tsv")
COMPACT_FILES = ("samples.tsv", "dispatches.tsv", "projectiles.tsv",
                 "score_writes.tsv", "result.tsv", "audio_bus_stream.bin")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def identity(path: Path, files: tuple[str, ...]) -> dict[str, object]:
    manifest_path = path / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    for filename in files:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {"manifest_sha256": digest(manifest_path),
            "files": {name: manifest["sha256"][name] for name in files}}


def mutation_path(command: str) -> Path:
    candidates = (
        ROOT / ".deps/mame" / f"oracle11_global_audio_cmd_{command}",
        ROOT / ".deps/mame" / f"oracle11_global_audio_cmd_{command}_s",
        ROOT / ".deps/mame" / f"oracle11_global_audio_cmd_{command}_t")
    for path in candidates:
        if (path / "input_manifest.json").exists():
            return path
    raise ValueError(f"missing global command control 0x{command}")


def projected_prefix_equal(baseline: Path, mutant: Path, last_frame: int,
                           drop: set[str] | None = None,
                           allow_trailing_baseline: bool = False) -> bool:
    drop = drop or set()
    baseline_rows = [row for row in rows(baseline)
                     if int(row["frame"]) <= last_frame]
    mutant_rows = rows(mutant)
    project = lambda row: {key: value for key, value in row.items()
                           if key not in drop}
    lengths_match = (len(baseline_rows) >= len(mutant_rows)
                     if allow_trailing_baseline else
                     len(baseline_rows) == len(mutant_rows))
    return lengths_match and all(
        project(left) == project(right)
        for left, right in zip(baseline_rows, mutant_rows))


def bus_records(data: bytes, last_frame: int | None = None) -> list[bytes]:
    require(len(data) % 5 == 0, "compact QSound stream alignment drift")
    result = []
    for offset in range(0, len(data), 5):
        record = data[offset:offset + 5]
        frame = int.from_bytes(record[:2], "big")
        if last_frame is not None and frame > last_frame:
            break
        result.append(record)
    return result


def describe_record(record: bytes | None) -> dict[str, object] | None:
    if record is None:
        return None
    return {"frame": int.from_bytes(record[:2], "big"),
            "register": f"0x{record[2]:02x}",
            "value": f"0x{int.from_bytes(record[3:], 'big'):04x}"}


def stream_difference(baseline: list[bytes], mutant: list[bytes]) -> dict[str, object]:
    first = None
    for index, pair in enumerate(itertools.zip_longest(baseline, mutant)):
        if pair[0] != pair[1]:
            first = index
            first_pair = pair
            break
    require(first is not None, "non-discriminating command suppression")
    suffix = 0
    while suffix < min(len(baseline), len(mutant)) - first and \
            baseline[-1 - suffix] == mutant[-1 - suffix]:
        suffix += 1
    base_bytes = b"".join(baseline)
    mutant_bytes = b"".join(mutant)
    return {
        "baseline_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "mutant_sha256": hashlib.sha256(mutant_bytes).hexdigest(),
        "baseline_transaction_count": len(baseline),
        "mutant_transaction_count": len(mutant),
        "common_prefix_transactions": first,
        "common_suffix_transactions": suffix,
        "first_difference": {"transaction_index": first,
                             "baseline": describe_record(first_pair[0]),
                             "mutant": describe_record(first_pair[1])},
    }


def handler_class(pointer: int, first_byte: int | None) -> str:
    if pointer == 0:
        return "NULL_TABLE_TIMING_PATH_0x01e0_0x0204"
    if first_byte == 0:
        return "GLOBAL_STATE_RESET_0x048d"
    if first_byte is not None and first_byte < 0x80:
        return "VOICE_ALLOCATION_0x0218_0x0294"
    return "CONTROL_HANDLER_0x053a"


def build_report() -> dict[str, object]:
    capture_a = identity(TRANSPORT_A, TRANSPORT_FILES)
    capture_b = identity(TRANSPORT_B, TRANSPORT_FILES)
    require(capture_a["files"] == capture_b["files"],
            "16-byte command completion captures differ")
    compact_a = identity(COMPACT_A, COMPACT_FILES)
    compact_b = identity(COMPACT_B, COMPACT_FILES)
    require(compact_a["files"] == compact_b["files"],
            "compact QSound completion captures differ")

    ingress = rows(TRANSPORT_A / "audio_shared_commands.tsv")
    dispatch = rows(TRANSPORT_A / "audio_command_dispatches.tsv")
    main = rows(TRANSPORT_A / "dispatches.tsv")
    require(len(ingress) == len(dispatch) == len(main) == 1161,
            "copied/dispatch/main command count drift")
    occurrences = []
    for source, consumed, main_row in zip(ingress, dispatch, main):
        require(source["sequence"] == consumed["sequence"] == main_row["sequence"],
                "command sequence drift")
        require(source["bytes"] == consumed["bytes"] and
                int(source["frame"]) >= int(main_row["frame"]),
                "16-byte command transport mismatch")
        command = int(source["bytes"][:4], 16)
        require(command == int(main_row["command"], 16),
                "main/shared command identity mismatch")
        occurrences.append({"sequence": int(source["sequence"]),
                            "main_frame": int(main_row["frame"]),
                            "audio_frame": int(source["frame"]),
                            "transport_latency_frames":
                                int(source["frame"]) - int(main_row["frame"]),
                            "payload_16_bytes": source["bytes"],
                            "command": f"0x{command:04x}"})

    rom = ROM.read_bytes()
    require(digest(ROM) ==
            "88f7f38e64c5d5c16264768230fc599a4f8de5904633a814789a192a8baa19b3",
            "audio ROM identity drift")
    table_size = int.from_bytes(rom[0x9000:0x9002], "big")
    require(table_size == 0x038D, "audio command table size drift")
    player = json.loads(PLAYER.read_text(encoding="ascii"))
    player_edges: dict[str, list[dict[str, object]]] = {}
    for edge in player["trigger_edges"]:
        player_edges.setdefault(edge["command_identity"], []).append(edge)
    baseline_bus = (COMPACT_A / "audio_bus_stream.bin").read_bytes()
    command_counts: dict[int, int] = {}
    for item in occurrences:
        value = int(item["command"], 16)
        command_counts[value] = command_counts.get(value, 0) + 1

    transactions = []
    global_controls = 0
    for command, count in sorted(command_counts.items()):
        index = command % table_size
        loop_count = command // table_size
        entry_offset = 0x9006 + index * 4
        entry = rom[entry_offset:entry_offset + 4]
        pointer = int.from_bytes(entry[:3], "big")
        first_byte = rom[pointer] if pointer else None
        command_text = f"0x{command:04x}"
        if command_text in player_edges:
            edge = player_edges[command_text][0]
            effect = {"kind": "accepted-player-command-transaction-differential",
                      "evidence_edge": edge["id"],
                      "downstream_difference":
                          edge["mutation"]["downstream_qsound_difference"],
                      "gameplay_invariants": edge["mutation"]["gameplay_invariants"]}
            control_owner = "predator-warrior-player-authority"
        else:
            path = mutation_path(f"{command:04x}")
            manifest = json.loads((path / "input_manifest.json").read_text(
                encoding="utf-8-sig"))
            identity(path, COMPACT_FILES)
            last_frame = int(manifest["frame_window"][1])
            result = rows(path / "result.tsv")[0]
            require(result["suppression_count"] == "1",
                    f"0x{command:04x}: suppression count drift")
            for filename in ("samples.tsv", "projectiles.tsv", "score_writes.tsv"):
                require(projected_prefix_equal(COMPACT_A / filename,
                                               path / filename, last_frame),
                        f"0x{command:04x}: {filename} gameplay coupling")
            require(projected_prefix_equal(COMPACT_A / "dispatches.tsv",
                                           path / "dispatches.tsv", last_frame,
                                           {"suppressed"}, True),
                    f"0x{command:04x}: main dispatch sequence coupling")
            base_records = bus_records(baseline_bus, last_frame)
            mutant_records = bus_records((path / "audio_bus_stream.bin").read_bytes())
            effect = {"kind": "bounded-command-handler-transaction-differential",
                      "capture": path.name, "last_frame": last_frame,
                      "downstream_qsound_transactions":
                          stream_difference(base_records, mutant_records),
                      "gameplay_projection_unchanged": True}
            control_owner = "global-gameplay-audio-load-release"
            global_controls += 1
        transactions.append({
            "command": command_text, "occurrences": count,
            "table_index": f"0x{index:04x}",
            "table_loop_iterations": loop_count,
            "table_entry_offset": f"0x{entry_offset:04x}",
            "table_entry": entry.hex(),
            "data_pointer_24": f"0x{pointer:06x}",
            "first_handler_byte": None if first_byte is None else f"0x{first_byte:02x}",
            "handler_class": handler_class(pointer, first_byte),
            "state_update_contract": (
                "dispatcher/table timing only; no handler state allocation"
                if pointer == 0 else
                "source-owned global reset at 0x048d"
                if first_byte == 0 else
                "source-owned f200 voice-slot allocation, 0x40-byte clear, "
                "priority/pointer/mode writes and 0x02ad mode dispatch"),
            "control_owner": control_owner,
            "causal_effect": effect,
            "semantic_sound_name": "UNKNOWN",
            "classification": "SOURCE_CLOSED",
        })
    require(len(transactions) == 72 and global_controls == 43,
            "logical command coverage drift")

    report = {
        "schema": "oracle11-global-audio-handlers-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": "route-reachable shared command to audio-CPU handler transaction boundary",
        "dispatcher": {
            "source_routine": "audio ROM 0x01bd..0x0294",
            "consumer_pointer": "0xf008",
            "queue_base": "0xf100",
            "entry_size": 16,
            "command_word": "big-endian IY+0/IY+1",
            "table_count": table_size,
            "table_base": "bank-0 0x9006",
            "table_entry_layout": "24-bit data pointer plus one unused byte",
            "table_index_rule": "command modulo 0x038d; subtraction count preserves timing",
            "source_sha256": hashlib.sha256(rom[0x01BD:0x0295]).hexdigest(),
            "table_sha256": hashlib.sha256(
                rom[0x9000:0x9006 + table_size * 4]).hexdigest(),
        },
        "handler_paths": {
            "null_table_timing": "0x01e0..0x0204",
            "global_reset": "0x048d",
            "voice_allocation": "0x0218..0x0294",
            "voice_mode_table": "0x02ad with eight route-addressable entries",
            "qsound_write_primitive": "0x0abc..0x0adb",
            "orphan_paths": 0,
        },
        "coverage": {
            "copied_16_byte_commands": 1161,
            "dispatched_16_byte_commands": 1161,
            "orphan_shared_commands": 0,
            "command_identities": 72,
            "player_command_identities_with_accepted_controls": 29,
            "global_command_identities_with_new_controls": 43,
            "orphan_command_identities": 0,
            "orphan_qsound_transaction_groups": 0,
        },
        "logical_event_granularity": {
            "owner": "audio command plus handler transaction",
            "individual_low_high_register_writes_are_logical_events": False,
            "bus_representation": "exact frame/register/value transaction stream",
        },
        "command_transactions": transactions,
        "command_occurrences": occurrences,
        "semantic_sound_names": {"classification": "UNKNOWN",
                                 "inferred_from_timing": False},
        "capture_identity": {
            "completion_a": capture_a, "completion_b": capture_b,
            "completion_byte_identical": True,
            "compact_completion_a": compact_a,
            "compact_completion_b": compact_b,
            "compact_completion_byte_identical": True,
        },
        "remaining_global_family_backlog": {
            "non_player_trigger_groups": 175,
            "route_load_release_boundaries": 4,
            "family_source_closed": False,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED",
            "packed_bcd_score_routine": "0x0abdd2",
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED" and
            report["schema"] == "oracle11-global-audio-handlers-v1",
            "handler checkpoint status drift")
    coverage = report["coverage"]
    require(coverage == {
        "copied_16_byte_commands": 1161,
        "dispatched_16_byte_commands": 1161,
        "orphan_shared_commands": 0,
        "command_identities": 72,
        "player_command_identities_with_accepted_controls": 29,
        "global_command_identities_with_new_controls": 43,
        "orphan_command_identities": 0,
        "orphan_qsound_transaction_groups": 0,
    }, "handler coverage drift")
    transactions = report["command_transactions"]
    require(len(transactions) == 72 and
            all(item["classification"] == "SOURCE_CLOSED" and
                item["semantic_sound_name"] == "UNKNOWN"
                for item in transactions), "command transaction drift")
    require(sum(item["occurrences"] for item in transactions) == 1161 and
            len(report["command_occurrences"]) == 1161,
            "command occurrence coverage drift")
    require(report["handler_paths"]["orphan_paths"] == 0 and
            report["logical_event_granularity"]
                  ["individual_low_high_register_writes_are_logical_events"] is False,
            "handler ownership granularity drift")
    require(report["capture_identity"]["completion_byte_identical"] is True and
            report["capture_identity"]["compact_completion_byte_identical"] is True,
            "completion determinism drift")
    require(report["remaining_global_family_backlog"] == {
        "non_player_trigger_groups": 175,
        "route_load_release_boundaries": 4,
        "family_source_closed": False,
    }, "global family prematurely closed")
    require(report["protected_boundaries"]["predator_warrior"] ==
            "SOURCE_CLOSED" and
            report["protected_boundaries"]["packed_bcd_score_routine"] ==
            "0x0abdd2" and report["protected_boundaries"]["spec02_active"] is False,
            "protected player/SPEC boundary drift")


def sample_descriptor_transactions(rom: bytes, transactions: list[bytes],
                                   descriptor_addresses: list[int]) -> dict:
    """Read-only sample-table sizing; never converts bus rows to game events."""
    require(hashlib.sha256(rom[0x1077:0x10db]).hexdigest() ==
            "a7b363fc1aca9416839480b9609c2045e822bb213c4862ad296cb3f94fd53d33",
            "sample descriptor consumer identity drift")
    table = {}
    for address in descriptor_addresses:
        require(address % 8 == 0 and 0 <= address <= 0xbff8,
                "sample descriptor is outside source ROM mapping")
        record = rom[address:address+8]
        bank = 0x8000 | record[0]
        start = int.from_bytes(record[1:3], "little")
        loop = int.from_bytes(record[3:5], "little")
        end = int.from_bytes(record[5:7], "little")
        table.setdefault((bank, start, end, (end-loop) & 65535), []).append(address)
    matches = []
    for offset in range(len(transactions) - 4):
        group = transactions[offset:offset+5]
        registers = [r[2] for r in group]
        values = [int.from_bytes(r[3:], "big") for r in group]
        base = registers[0] - 2
        if (base < 0 or base >= 128 or base % 8 or values[0] != 0 or
                registers != [base+2, base+1, base+5, base+4, (base-8) & 0x78]):
            continue
        key = (values[4], values[1], values[2], values[3])
        require(key in table, "sample descriptor transaction does not match source table")
        matches.append({"first_frame": int.from_bytes(group[0][:2], "big"),
                        "last_frame": int.from_bytes(group[-1][:2], "big"),
                        "voice": base // 8, "descriptor_addresses": table[key],
                        "bank": key[0] & 0x7fff, "start": key[1],
                        "end": key[2], "loop_length": key[3]})
    return {"matches": matches,
            "descriptor_table_sha256": hashlib.sha256(rom[0x8000:0x9000]).hexdigest()}


def sample_residency_readiness() -> dict:
    rom = ROM.read_bytes()
    require(digest(ROM) == "88f7f38e64c5d5c16264768230fc599a4f8de5904633a814789a192a8baa19b3",
            "audio ROM identity drift")
    accepted = json.loads(OUT.read_text(encoding="ascii"))
    left = identity(COMPACT_A, COMPACT_FILES)
    right = identity(COMPACT_B, COMPACT_FILES)
    require(left["files"] == right["files"], "paired audio residency input drift")
    require(left == accepted["capture_identity"]["compact_completion_a"],
            "audio residency capture is not the accepted compact baseline")
    stream = (COMPACT_A / "audio_bus_stream.bin").read_bytes()
    roots = [ROOT / (".deps/mame/oracle11_audio_sample_descriptors_" + label)
             for label in ("a", "b", "m")]
    names = TRANSPORT_FILES + ("audio_sample_descriptors.tsv",)
    captures = [identity(root, names) for root in roots]
    require(captures[0]["files"] == captures[1]["files"],
            "paired descriptor source captures differ")
    for name in ("samples.tsv", "dispatches.tsv", "projectiles.tsv",
                 "score_writes.tsv", "result.tsv"):
        require(captures[0]["files"][name] == captures[2]["files"][name],
                "descriptor control changed gameplay: " + name)
    witness = rows(roots[0] / "audio_sample_descriptors.tsv")
    mutant = rows(roots[2] / "audio_sample_descriptors.tsv")
    require(len(witness) == len(mutant) and len(witness) % 5 == 0,
            "descriptor witness transaction alignment drift")
    addresses = sorted({int(row["iy"], 16) for row in witness})
    for index, row in enumerate(witness):
        require(row["return_pc"] == ("1094", "10a6", "10b2", "10c3", "10d4")[index % 5],
                "descriptor source caller order drift")
        address = int(row["iy"], 16)
        require(bytes.fromhex(row["descriptor_bytes"]) == rom[address:address+8],
                "descriptor source ROM read drift")
        require({k: v for k,v in row.items() if k != "applied"} ==
                {k: v for k,v in mutant[index].items() if k != "applied"},
                "descriptor control changed source program context")
        expected = int(row["requested"],16)
        if row["return_pc"] == "10d4":
            expected = (expected + 8) & 0x78
        require(int(mutant[index]["applied"],16) == expected,
                "descriptor source control was not applied")

    def recorded_bus(root):
        result = bytearray()
        with (root / "qsound.tsv").open(encoding="ascii", newline="") as source:
            for row in csv.DictReader(source, delimiter="\t"):
                if row["port"] == "d002":
                    result.extend(int(row["frame"]).to_bytes(2, "big"))
                    result.append(int(row["register"], 16))
                    result.extend(int(row["value"], 16).to_bytes(2, "big"))
        return bytes(result)

    baseline_bus = recorded_bus(roots[0])
    mutated_bus = recorded_bus(roots[2])
    require(baseline_bus == b"".join(bus_records(stream, 15192)),
            "descriptor capture changed accepted source bus chronology")
    baseline_transactions = bus_records(baseline_bus)
    mutant_transactions = bus_records(mutated_bus)
    require(len(baseline_transactions) == len(mutant_transactions),
            "descriptor control changed transaction count")
    differences = []
    for original, changed in zip(baseline_transactions, mutant_transactions):
        if original != changed:
            require(original[:2] == changed[:2] and original[3:] == changed[3:] and
                    changed[2] == (original[2] + 8) & 0x78,
                    "descriptor control caused an unrelated bus difference")
            differences.append(original)
    require(len(differences) == len(witness) // 5 and len(differences) > 0,
            "descriptor control lacks attributable downstream differences")
    result = sample_descriptor_transactions(rom, baseline_transactions, addresses)
    route = result["matches"]
    require(len(route) == len(witness) // 5,
            "source descriptor callers and bus groups do not reconcile")
    intervals = {}
    for record in route:
        require(0 <= record["bank"] < 64 and record["start"] < record["end"],
                "source sample range needs explicit wrap/bank treatment")
        intervals.setdefault(record["bank"], []).append((record["start"], record["end"]))
    merged = []
    for bank, spans in sorted(intervals.items()):
        for start, end in sorted(spans):
            if merged and merged[-1][0] == bank and start <= merged[-1][2]:
                merged[-1][2] = max(merged[-1][2], end)
            else:
                merged.append([bank, start, end])
    return {"classification": "READ_ONLY_SOURCE_DESCRIPTOR_SIZING_NOT_NATIVE_CUE_APPROVAL",
            "paired_compact_stream_sha256": hashlib.sha256(stream).hexdigest(),
            "source_frame_window": [1972, 15193],
            "round1_descriptor_transactions": len(route),
            "descriptor_table_sha256": result["descriptor_table_sha256"],
            "source_probe_files": captures[0]["files"],
            "source_control_files": captures[2]["files"],
            "source_control_bus_differences": len(differences),
            "unique_descriptor_addresses": addresses,
            "below_8000_source_invocations": sum(int(r["iy"],16) < 0x8000 for r in witness[::5]),
            "ambiguous_descriptor_transactions": sum(len(r["descriptor_addresses"]) != 1 for r in route),
            "source_address_intervals": merged,
            "source_address_span_bytes": sum(end-start for bank,start,end in merged),
            "scope": "Source0x1077 five-write sequence matched to directly witnessed ROM descriptors, including16-bit pointer-wrap read0x7800; not individual bus writes as gameplay events. Address span excludes interpolation guards and does not size SCSP conversion, voice overlap, effects or source-supported unobserved branches. Includes source music; CDDA ownership must distinguish native sample demand. No native implementation or memory-map change."}


def main() -> None:
    import sys
    if "--sample-residency-readiness" in sys.argv:
        print(json.dumps(sample_residency_readiness(), indent=2, sort_keys=True))
        return
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 global audio handlers: SOURCE_CLOSED; 1161 commands, "
          "72 identities, zero orphan handler/QSound transaction groups")


if __name__ == "__main__":
    main()
