#!/usr/bin/env python3
"""Close the Predator Warrior player-to-shared-gameplay-audio boundary."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_A = ROOT / ".deps" / "mame" / "oracle11_player_audio_e"
BASE_B = ROOT / ".deps" / "mame" / "oracle11_player_audio_f"
MUTATION_PREFIX = "oracle11_player_audio_mut_"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
OUT = ROOT / "data" / "oracle11_predator_player_audio.json"
FILES = ("samples.tsv", "dispatches.tsv", "qsound.tsv", "projectiles.tsv",
         "score_writes.tsv", "result.tsv")
SCORE_RANGES = ((0x0ABDD2, 0x0ABE18), (0x0ABE2A, 0x0ABF16),
                (0x0BC5FC, 0x0BC664))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream, delimiter="\t")


def manifest_identity(base: Path) -> dict[str, object]:
    manifest_path = base / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    for filename in FILES:
        require(digest(base / filename) == manifest["sha256"][filename],
                f"{base.name}: {filename} identity drift")
    return {"manifest_sha256": digest(manifest_path),
            "files": manifest["sha256"]}


def projected_first_difference(baseline: Path, mutant: Path,
                               drop: set[str]) -> dict[str, object] | None:
    for index, pair in enumerate(itertools.zip_longest(rows(baseline), rows(mutant))):
        left, right = pair
        if left is None or right is None:
            return {"row_index": index, "kind": "length",
                    "baseline": left, "mutant": right}
        left = {key: value for key, value in left.items() if key not in drop}
        right = {key: value for key, value in right.items() if key not in drop}
        if left != right:
            return {"row_index": index, "kind": "value",
                    "baseline": left, "mutant": right}
    return None


def projected_equal(baseline: Path, mutant: Path, drop: set[str]) -> bool:
    return projected_first_difference(baseline, mutant, drop) is None


def capstone_engine():
    sys.path.insert(0, str(ROOT / ".deps" / "python-capstone"))
    from capstone import CS_ARCH_M68K, CS_MODE_BIG_ENDIAN, CS_MODE_M68K_000, Cs
    return Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_000)


def instruction_ending_at(opcodes: bytes, end: int) -> dict[str, object]:
    engine = capstone_engine()
    candidates = []
    for start in range(max(0, end - 12), end, 2):
        decoded = list(engine.disasm(opcodes[start:end], start))
        if decoded and decoded[-1].address + decoded[-1].size == end and \
                decoded[-1].mnemonic.startswith(("jsr", "bsr")):
            candidates.append(decoded[-1])
    require(candidates, f"no source call instruction ending at 0x{end:06x}")
    instruction = max(candidates, key=lambda item: item.address)
    start = max(0, instruction.address - 64)
    guard_path = []
    for candidate_start in range(start, instruction.address + 1, 2):
        decoded = list(engine.disasm(
            opcodes[candidate_start:instruction.address + instruction.size],
            candidate_start))
        if decoded and decoded[-1].address == instruction.address:
            # Keep only the immediate basic-block tail. Earlier bytes can be
            # inline command tables between neighboring wrapper routines.
            guard_path = decoded[-5:]
            break
    return {
        "address": f"0x{instruction.address:06x}",
        "return_address": f"0x{end:06x}",
        "mnemonic": instruction.mnemonic,
        "operand": instruction.op_str,
        "guard_path_tail": [
            {"pc": f"0x{item.address:06x}", "mnemonic": item.mnemonic,
             "operand": item.op_str} for item in guard_path],
        "source_window": {
            "start": f"0x{start:06x}",
            "end_exclusive": f"0x{instruction.address + instruction.size:06x}",
            "sha256": hashlib.sha256(
                opcodes[start:instruction.address + instruction.size]).hexdigest(),
        },
    }


def in_score_range(value: int) -> bool:
    return any(first <= value < last for first, last in SCORE_RANGES)


def edge_is_audio_owned(edge: dict[str, object]) -> bool:
    provenance = edge.get("caller_provenance", {})
    try:
        callsite = int(str(provenance["player_side_call"]["address"]), 16)
        stack_owner = int(str(provenance["player_stack_owner_return"]), 16)
    except (KeyError, TypeError, ValueError):
        return False
    return (provenance.get("shared_audio_wrapper") == "0x003a88" and
            provenance.get("shared_dispatch_entry") == "0x001922" and
            provenance.get("queue_argument_writer") == "0x00193c" and
            not in_score_range(callsite) and not in_score_range(stack_owner))


def build_report() -> dict[str, object]:
    opcodes, program = OPCODES.read_bytes(), PROGRAM.read_bytes()
    require(len(opcodes) == len(program) == 0x200000,
            "decoded source image size drift")
    identities = {"completion_a": manifest_identity(BASE_A),
                  "completion_b": manifest_identity(BASE_B)}
    for filename in FILES:
        require(digest(BASE_A / filename) == digest(BASE_B / filename),
                f"completion captures differ: {filename}")

    baseline_dispatches = list(rows(BASE_A / "dispatches.tsv"))
    player_dispatches = [row for row in baseline_dispatches
                         if row["a6"] == "ff8380"]
    require(len(baseline_dispatches) == 1161 and len(player_dispatches) == 378,
            "route dispatch population drift")
    require(all(row["shared_dispatch"] == "001922" and
                row["write_pc"] == "00193c" and
                row["capture_pc"] == "001940" and
                row["return0"] == "003a8e" for row in player_dispatches),
            "player dispatch chain drift")

    samples_by_frame = {int(row["frame"]): row
                        for row in rows(BASE_A / "samples.tsv")}
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in player_dispatches:
        grouped[(row["return1"], row["command"])].append(row)
    require(len(grouped) == 38, "player trigger-edge count drift")

    edges = []
    total_contexts = 0
    for caller, command in sorted(grouped):
        observed = grouped[(caller, command)]
        mutation = (ROOT / ".deps" / "mame" /
                    f"{MUTATION_PREFIX}{caller}_{command}")
        require(mutation.is_dir(), f"missing mutation for {caller}/{command}")
        mutation_identity = manifest_identity(mutation)
        suppressed = [row for row in rows(mutation / "dispatches.tsv")
                      if row["suppressed"] == "1"]
        require(len(suppressed) == 1 and
                (suppressed[0]["return1"], suppressed[0]["command"]) ==
                (caller, command), f"{caller}/{command}: suppression drift")
        result_rows = list(rows(mutation / "result.tsv"))
        require(len(result_rows) == 1 and
                int(result_rows[0]["suppression_count"]) == 1,
                f"{caller}/{command}: suppression count drift")

        invariant_files = {
            "score_health_damage_resource_route": projected_equal(
                BASE_A / "samples.tsv", mutation / "samples.tsv", {"variant"}),
            "projectile_state": projected_equal(
                BASE_A / "projectiles.tsv", mutation / "projectiles.tsv", {"variant"}),
            "score_writer_sequence": projected_equal(
                BASE_A / "score_writes.tsv", mutation / "score_writes.tsv", {"variant"}),
            "main_dispatch_sequence": projected_equal(
                BASE_A / "dispatches.tsv", mutation / "dispatches.tsv",
                {"variant", "suppressed"}),
            "stable_round2_result": projected_equal(
                BASE_A / "result.tsv", mutation / "result.tsv",
                {"variant", "suppression_count"}),
        }
        require(all(invariant_files.values()),
                f"{caller}/{command}: gameplay invariant changed")
        qsound_difference = projected_first_difference(
            BASE_A / "qsound.tsv", mutation / "qsound.tsv", {"variant"})
        require(qsound_difference is not None,
                f"{caller}/{command}: no downstream audio difference")
        baseline_difference = qsound_difference.get("baseline")
        mutant_difference = qsound_difference.get("mutant")
        difference_frames = [int(row["frame"]) for row in
                             (baseline_difference, mutant_difference) if row]
        suppressed_frame = int(suppressed[0]["frame"])
        require(difference_frames and min(difference_frames) >= suppressed_frame,
                f"{caller}/{command}: downstream difference precedes trigger")

        contexts: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
        arguments: dict[tuple[str, str, str], int] = defaultdict(int)
        for row in observed:
            contexts[(row["player_state"], row["player_action"],
                      row["player_inner"])].append(row)
            arguments[(row["d1"], row["d2"], row["d3"])] += 1
        total_contexts += len(contexts)
        context_rows = []
        for key, values in sorted(contexts.items(), key=lambda item:
                                  tuple(int(part) for part in item[0])):
            frames = [int(item["frame"]) for item in values]
            context_rows.append({
                "player_state_u16": int(key[0]),
                "player_action_u16": int(key[1]),
                "player_substate_u8": int(key[2]),
                "input_words": sorted({int(samples_by_frame[frame]["input"])
                                       for frame in frames}),
                "first_frame": min(frames), "last_frame": max(frames),
                "count": len(values),
            })
        call = instruction_ending_at(opcodes, int(caller, 16))
        edge = {
            "id": f"player-audio-{caller}-{command}",
            "classification": "SOURCE_CLOSED",
            "transition_guard": {
                "rule": ("the source player dispatch reaches the exact callsite "
                         "with A6=0xff8380 and one of the bound state/action/"
                         "substate contexts; the local source guard path is "
                         "hashed and retained below"),
                "contexts": context_rows,
                "source_guard_path_tail": call["guard_path_tail"],
            },
            "caller_provenance": {
                "player_record": "0xff8380",
                "player_stack_owner_return": f"0x{caller}",
                "player_side_call": call,
                "shared_audio_wrapper": "0x003a88",
                "wrapper_return": "0x003a8e",
                "shared_dispatch_entry": "0x001922",
                "queue_argument_writer": "0x00193c",
                "queue_ring": "0xff0a88..0xff0e87",
            },
            "command_identity": f"0x{command}",
            "argument_variants": [
                {"d1": f"0x{key[0]}", "d2": f"0x{key[1]}",
                 "d3": f"0x{key[2]}", "count": count}
                for key, count in sorted(arguments.items())],
            "baseline_occurrences": len(observed),
            "mutation": {
                "kind": "replace one matching queued command low word with zero",
                "suppressed_frame": suppressed_frame,
                "suppressed_context": {
                    "state": int(suppressed[0]["player_state"]),
                    "action": int(suppressed[0]["player_action"]),
                    "substate": int(suppressed[0]["player_inner"]),
                },
                "downstream_qsound_difference": qsound_difference,
                "gameplay_invariants": invariant_files,
                "capture": mutation_identity,
            },
            "semantic_sound_name_inferred": False,
        }
        require(edge_is_audio_owned(edge), f"{caller}/{command}: ownership rejected")
        edges.append(edge)

    score_rows = list(rows(BASE_A / "score_writes.tsv"))
    score_writer_pcs = sorted({row["pc"] for row in score_rows})
    require(score_rows and all(any(first <= int(pc, 16) < last
                                   for first, last in SCORE_RANGES[:2])
                               for pc in score_writer_pcs),
            "score writer escaped packed-BCD routine")
    require(not any(in_score_range(int(edge["caller_provenance"]
                                       ["player_stack_owner_return"], 16)) or
                    in_score_range(int(edge["caller_provenance"]
                                       ["player_side_call"]["address"], 16))
                    for edge in edges), "score routine admitted as audio caller")
    fake_score_edge = {
        "caller_provenance": {
            "player_stack_owner_return": "0x0abdd2",
            "player_side_call": {"address": "0x0abdd2"},
            "shared_audio_wrapper": "0x003a88",
            "shared_dispatch_entry": "0x001922",
            "queue_argument_writer": "0x00193c",
        }}
    require(not edge_is_audio_owned(fake_score_edge),
            "packed-BCD score routine satisfied audio ownership")
    require(total_contexts == 47, "player trigger-context count drift")

    report = {
        "schema": "oracle11-predator-player-audio-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": ("every route-reachable Predator Warrior player-origin "
                  "gameplay-audio trigger through the shared main-side dispatch; "
                  "shared dispatcher-to-QSound transport remains global backlog"),
        "boundary": {
            "player_owned_through": "0x001922 main-side enqueue entry",
            "argument_writer": "0x00193c",
            "shared_wrapper": "0x003a88",
            "global_backlog_begins": "0x001880 queue drain to QSound shared RAM",
            "global_transport_owner": "gameplay-audio-load-release",
            "semantic_sound_names_inferred": False,
        },
        "coverage": {
            "completion_captures": 2,
            "completion_captures_byte_identical": True,
            "player_dispatch_occurrences": len(player_dispatches),
            "distinct_trigger_edges": len(edges),
            "state_action_substate_contexts": total_contexts,
            "mutations": len(edges),
            "all_mutations_discriminating": True,
            "all_gameplay_invariants_unchanged": True,
        },
        "trigger_edges": edges,
        "score_negative_control": {
            "status": "PASS",
            "routine": "0x0abdd2..0x0abe18",
            "other_score_only_routine": "0x0abe2a..0x0abf16",
            "classification": "PACKED_BCD_SCORE_AUTHORITY",
            "writer_pcs": [f"0x{pc}" for pc in score_writer_pcs],
            "write_count": len(score_rows),
            "audio_edge_validator_rejects_score_routine": True,
            "health_max_route": "0x0bc5fc..0x0bc664",
            "timing_or_temporal_adjacency_used": False,
        },
        "source_identity": {
            "decoded_opcodes_sha256": hashlib.sha256(opcodes).hexdigest(),
            "decrypted_program_sha256": hashlib.sha256(program).hexdigest(),
            "queue_dispatch_sha256": hashlib.sha256(opcodes[0x1880:0x1960]).hexdigest(),
            "packed_bcd_score_sha256": hashlib.sha256(opcodes[0x0ABDD2:0x0ABE18]).hexdigest(),
        },
        "capture_identity": identities,
        "protected_boundaries": {
            "production_runtime_writes": 0, "yaba_runs": 0,
            "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-predator-player-audio-v1" and
            report["status"] == "SOURCE_CLOSED", "player audio status drift")
    coverage = report["coverage"]
    require(coverage == {
        "completion_captures": 2,
        "completion_captures_byte_identical": True,
        "player_dispatch_occurrences": 378,
        "distinct_trigger_edges": 38,
        "state_action_substate_contexts": 47,
        "mutations": 38,
        "all_mutations_discriminating": True,
        "all_gameplay_invariants_unchanged": True,
    }, "player audio coverage drift")
    edges = report["trigger_edges"]
    require(len(edges) == 38 and all(edge_is_audio_owned(edge) for edge in edges),
            "player audio edge provenance drift")
    require(all(edge["classification"] == "SOURCE_CLOSED" and
                edge["semantic_sound_name_inferred"] is False and
                edge["mutation"]["downstream_qsound_difference"] is not None and
                all(edge["mutation"]["gameplay_invariants"].values())
                for edge in edges), "player audio mutation drift")
    require(report["boundary"]["global_transport_owner"] ==
            "gameplay-audio-load-release" and
            report["boundary"]["global_backlog_begins"].startswith("0x001880") and
            report["boundary"]["semantic_sound_names_inferred"] is False,
            "global transport boundary drift")
    negative = report["score_negative_control"]
    require(negative["status"] == "PASS" and
            negative["classification"] == "PACKED_BCD_SCORE_AUTHORITY" and
            negative["audio_edge_validator_rejects_score_routine"] is True and
            negative["timing_or_temporal_adjacency_used"] is False,
            "score negative control drift")
    require(report["protected_boundaries"] == {
        "production_runtime_writes": 0, "yaba_runs": 0,
        "frontend_active": False, "user09_status": "CHANGES_REQUESTED",
        "salvage08_active": False, "physical_saturn": "UNRUN",
        "spec02_active": False,
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 Predator Warrior player-origin audio: SOURCE_CLOSED "
          "(38 trigger edges; global transport retained)")


if __name__ == "__main__":
    main()
