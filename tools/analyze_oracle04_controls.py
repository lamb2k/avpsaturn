#!/usr/bin/env python3
"""Validate ORACLE-04 private controls and emit a source-only public report."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "oracle04_controls"
VSLICE = ROOT / ".deps" / "mame" / "vertical_slice"
CONTRACT = ROOT / "data" / "avsp_source_combat_presentation_contract.json"
OUT = ROOT / "data" / "oracle04_predator_warrior_control_actions.json"
HEADER = [
    "frame", "input_word", "p_state", "p_class", "p_sub", "p_action",
    "p_type", "p_facing", "p_x", "p_y", "p_z", "p_anim", "p_timer",
    "p_health", "p_hit", "p_source", "p_hurt", "p_attack",
]
MOVEMENTS = {
    "right": (2525, 2544, 8, "p_x"),
    "left": (2585, 2604, 4, "p_x"),
    "up_lane": (2645, 2664, 128, "p_z"),
    "down_lane": (2705, 2724, 256, "p_z"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii") + b"\n"


def load_rows(path: Path) -> list[dict[str, int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].split("\t") != HEADER:
        raise ValueError("ORACLE-04 control schema mismatch")
    rows = []
    for index, line in enumerate(lines[1:]):
        fields = line.split("\t")
        if len(fields) != len(HEADER):
            raise ValueError("ORACLE-04 control row is incomplete")
        row = {name: int(value, 16) if name == "p_anim" else int(value)
               for name, value in zip(HEADER, fields)}
        if row["frame"] != 2500 + index:
            raise ValueError("ORACLE-04 control frames are not contiguous")
        rows.append(row)
    if len(rows) != 261 or rows[-1]["frame"] != 2760:
        raise ValueError("ORACLE-04 control window mismatch")
    return rows


def by_frame(rows: list[dict[str, int]]) -> dict[int, dict[str, int]]:
    return {row["frame"]: row for row in rows}


def movement_report(rows: list[dict[str, int]]) -> list[dict[str, object]]:
    indexed = by_frame(rows)
    reports = []
    for name, (start, end, bit, axis) in MOVEMENTS.items():
        if any(indexed[f]["input_word"] & bit == 0 for f in range(start, end + 1)):
            raise ValueError(f"{name}: input pulse is incomplete")
        before = indexed[start - 1]
        response = None
        for frame in range(start, min(end + 8, 2760) + 1):
            row = indexed[frame]
            if (row[axis] != before[axis] or row["p_facing"] != before["p_facing"] or
                    row["p_action"] != before["p_action"]):
                response = frame
                break
        if response is None:
            raise ValueError(f"{name}: no source response")
        after = indexed[min(end + 6, 2760)]
        reports.append({
            "name": name,
            "input_frames": [start, end],
            "input_bit": bit,
            "response_frame": response,
            "latency_frames": response - start,
            "before": {k: before[k] for k in ("p_x", "p_y", "p_z", "p_facing", "p_action", "p_sub")},
            "after": {k: after[k] for k in ("p_x", "p_y", "p_z", "p_facing", "p_action", "p_sub")},
            "axis_delta": after[axis] - before[axis],
            "visual_witness_sha256": {
                "before": digest(RAW / "cold_run_1" / "frames" / f"{start - 1:05d}.png"),
                "response": digest(RAW / "cold_run_1" / "frames" / f"{response:05d}.png"),
            },
        })
    return reports


def parse_tsv(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:] if line]


def attack_report(contract: dict) -> list[dict[str, object]]:
    run1_path = VSLICE / "cold_run_1" / "samples.tsv"
    run2_path = VSLICE / "cold_run_2" / "samples.tsv"
    if digest(run1_path) != digest(run2_path):
        raise ValueError("existing paired combat captures are not identical")
    rows = by_frame([{k: int(v, 16) if k in ("p_anim", "e_anim") else int(v)
                      for k, v in row.items()}
                     for row in parse_tsv(run1_path)])
    attacks = []
    for event in contract["events"]:
        input_frame = int(event["attack_input_frame"])
        contact = int(event["contact_frame"])
        window = [int(v) for v in event["player_presentation_window"]]
        selector = int(event["attack_selector"])
        first_active = next((frame for frame in range(input_frame, window[1] + 1)
                             if rows[frame]["p_attack"] == selector), None)
        if first_active is None or rows[contact]["p_attack"] != selector:
            raise ValueError(f"selector {selector}: input/action binding drift")
        return_frame = next((frame for frame in range(window[1] + 1, min(window[1] + 20, 5469) + 1)
                             if rows[frame]["p_attack"] == 0), None)
        attacks.append({
            "selector": selector,
            "input_frame": input_frame,
            "presentation_window": window,
            "first_active_frame": first_active,
            "contact_frame": contact,
            "startup_to_presentation_frames": window[0] - input_frame,
            "startup_to_active_frames": first_active - input_frame,
            "startup_to_contact_frames": contact - input_frame,
            "return_to_nonattack_frame": return_frame,
            "player_action_at_contact": rows[contact]["p_action"],
            "player_substate_at_contact": rows[contact]["p_sub"],
            "health_before": int(event["health_before"]),
            "health_after": int(event["health_after"]),
            "hit_value": int(event["hit_value"]),
            "attack_box": event["collision"]["attack_box"],
            "enemy_hurt_box": event["collision"]["hurt_box"],
            "visual_witness_sha256": digest(VSLICE / "cold_run_1" / "frames" / f"{contact:05d}.png"),
        })
    return attacks


def build_report() -> dict:
    manifest = json.loads((RAW / "input_manifest.json").read_text(encoding="utf-8-sig"))
    if [r["name"] for r in manifest["runs"]] != [
            "cold_run_1", "cold_run_2", "one_frame_perturbation"]:
        raise ValueError("ORACLE-04 run inventory mismatch")
    base1_path = RAW / "cold_run_1" / "samples.tsv"
    base2_path = RAW / "cold_run_2" / "samples.tsv"
    perturb_path = RAW / "one_frame_perturbation" / "samples.tsv"
    base1, base2, perturb = load_rows(base1_path), load_rows(base2_path), load_rows(perturb_path)
    if base1 != base2 or digest(base1_path) != digest(base2_path):
        raise ValueError("ORACLE-04 cold runs are not byte-identical")
    differing_inputs = [row["frame"] for row, other in zip(base1, perturb)
                        if row["input_word"] != other["input_word"]]
    if differing_inputs != [2525]:
        raise ValueError("ORACLE-04 perturbation is not exactly one input frame")
    projection = ("p_state", "p_sub", "p_action", "p_facing", "p_x", "p_y", "p_z", "p_anim")
    downstream = next((row["frame"] for row, other in zip(base1, perturb)
                       if any(row[key] != other[key] for key in projection)), None)
    if downstream is None:
        raise ValueError("ORACLE-04 input perturbation has no downstream effect")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    attacks = attack_report(contract)
    return {
        "schema": 1,
        "task": "ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS",
        "classification": "MEASURED_MAME_SOURCE_SUBSET",
        "target": {"set": "avspu", "revision": "USA 940520"},
        "scope": "Predator Warrior first-live-encounter subset only; not a complete move set",
        "provenance": {
            "mame": manifest["mame"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "rom_sha256": {entry["name"]: entry["sha256"] for entry in manifest["roms"]},
            "control_samples_sha256": digest(base1_path),
            "combat_samples_sha256": digest(VSLICE / "cold_run_1" / "samples.tsv"),
            "source_combat_contract_sha256": digest(CONTRACT),
        },
        "determinism": {
            "control_cold_runs_byte_identical": True,
            "control_frame_count_each": len(base1),
            "combat_cold_runs_byte_identical": True,
            "combat_frame_count_each": 1390,
        },
        "movement": movement_report(base1),
        "attacks": attacks,
        "negative_control": {
            "kind": "one_frame_directional_input_perturbation",
            "input_frame": 2525,
            "differing_input_frames": differing_inputs,
            "first_downstream_different_frame": downstream,
            "perturbed_samples_sha256": digest(perturb_path),
        },
        "bounded_findings": {
            "horizontal_and_lane_control": "MEASURED",
            "facing": "MEASURED",
            "four_attack_selectors": "MEASURED",
            "attack_timing_and_boxes": "MEASURED",
            "enemy_health_hit_and_ko_sequence": "MEASURED",
            "player_hit_ko_return_to_control": "PARTIAL_PRIOR_CAPTURE_NOT_ORACLE04_PAIRED",
            "interruption_and_cancellation": "UNKNOWN",
            "player_side_rng_consumption": "UNKNOWN_NO_RNG_STATE_ASSERTED",
            "complete_move_set": "UNKNOWN",
        },
        "evidence_tier": "MAME_TRACE_AND_FRAME_INDEXED_CAPTURE",
        "saturn_emulator": "UNRUN",
        "physical_saturn": "UNRUN",
    }


def validate(report: dict) -> None:
    if report["classification"] != "MEASURED_MAME_SOURCE_SUBSET":
        raise ValueError("ORACLE-04 classification drift")
    if len(report["movement"]) != 4 or len(report["attacks"]) != 4:
        raise ValueError("ORACLE-04 bounded coverage drift")
    if report["determinism"] != {
            "control_cold_runs_byte_identical": True,
            "control_frame_count_each": 261,
            "combat_cold_runs_byte_identical": True,
            "combat_frame_count_each": 1390}:
        raise ValueError("ORACLE-04 deterministic repeat drift")
    movements = report["movement"]
    if [entry["name"] for entry in movements] != list(MOVEMENTS):
        raise ValueError("ORACLE-04 movement inventory drift")
    if [entry["latency_frames"] for entry in movements] != [2, 2, 2, 2]:
        raise ValueError("ORACLE-04 input latency drift")
    deltas = [entry["axis_delta"] for entry in movements]
    if not (deltas[0] > 0 and deltas[1] < 0 and deltas[2] > 0 and deltas[3] < 0):
        raise ValueError("ORACLE-04 directional response drift")
    if [entry["selector"] for entry in report["attacks"]] != [1, 2, 3, 4]:
        raise ValueError("ORACLE-04 selector sequence drift")
    if [entry["startup_to_active_frames"] for entry in report["attacks"]] != [4, 5, 7, 8]:
        raise ValueError("ORACLE-04 active-window timing drift")
    if [entry["startup_to_contact_frames"] for entry in report["attacks"]] != [5, 6, 8, 9]:
        raise ValueError("ORACLE-04 contact timing drift")
    if [(entry["health_before"], entry["health_after"], entry["hit_value"])
            for entry in report["attacks"]] != [
                (87, 63, 8), (63, 39, 8), (39, 8, 10), (8, -1, 12)]:
        raise ValueError("ORACLE-04 damage/KO sequence drift")
    if report["negative_control"]["differing_input_frames"] != [2525]:
        raise ValueError("ORACLE-04 negative control drift")
    if report["negative_control"]["first_downstream_different_frame"] != 2527:
        raise ValueError("ORACLE-04 perturbation response drift")
    if report["physical_saturn"] != "UNRUN" or report["saturn_emulator"] != "UNRUN":
        raise ValueError("ORACLE-04 overclaims Saturn evidence")
    if report["bounded_findings"]["complete_move_set"] != "UNKNOWN":
        raise ValueError("ORACLE-04 overclaims complete move-set coverage")
    if report["bounded_findings"]["interruption_and_cancellation"] != "UNKNOWN":
        raise ValueError("ORACLE-04 overclaims interruption/cancellation")
    if report["bounded_findings"]["player_side_rng_consumption"] != "UNKNOWN_NO_RNG_STATE_ASSERTED":
        raise ValueError("ORACLE-04 overclaims player RNG ownership")
    for name in ("control_samples_sha256", "combat_samples_sha256",
                 "source_combat_contract_sha256"):
        value = report["provenance"][name]
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError("ORACLE-04 provenance hash drift")


def self_test(report: dict) -> None:
    mutations = []
    changed = copy.deepcopy(report)
    changed["attacks"][2]["selector"] = 2
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["negative_control"]["differing_input_frames"] = []
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["physical_saturn"] = "PASS"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["bounded_findings"]["complete_move_set"] = "MEASURED"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["movement"][2]["axis_delta"] = 0
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["attacks"][0]["startup_to_active_frames"] = 5
    mutations.append(changed)
    for index, mutation in enumerate(mutations):
        try:
            validate(mutation)
        except ValueError:
            continue
        raise ValueError(f"ORACLE-04 negative mutation {index} unexpectedly passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    report = build_report() if args.generate else json.loads(OUT.read_text(encoding="utf-8"))
    validate(report)
    self_test(report)
    if args.generate:
        OUT.write_bytes(canonical(report))
    print("ORACLE-04 Predator Warrior control/action evidence: PASS")
    print(f"movement={len(report['movement'])} attacks={len(report['attacks'])}")
    print(f"control_sha256={report['provenance']['control_samples_sha256']}")


if __name__ == "__main__":
    main()
