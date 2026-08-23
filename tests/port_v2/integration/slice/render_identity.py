#!/usr/bin/env python3
"""Exact rendered street-alien identity contract for INTEGRATE-03."""

from __future__ import annotations

import copy
import hashlib
import json


FIELDS = (
    "slice_frame",
    "slice_enemy_action",
    "slice_enemy_action_frame",
    "slice_enemy_animation_record",
    "slice_enemy_palette_bank",
    "slice_enemy_object_count",
    "slice_enemy_object_identity",
    "slice_enemy_tile_identity",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def phase(sample: dict) -> str:
    frame = sample["slice_frame"]
    if sample["slice_semantic_ko"] or sample["slice_enemy_action"] == 4:
        return "KO"
    if sample["slice_semantic_hit"] or sample["slice_enemy_action"] == 3:
        return "HIT"
    if 637 <= frame < 900:
        return "RECOVERY"
    return "WALK"


def identity_row(sample: dict) -> list[int]:
    return [sample[name] for name in FIELDS]


def phase_rows(samples: list[dict], name: str) -> list[list[int]]:
    return [identity_row(sample) for sample in samples if phase(sample) == name]


def digest(rows: list[list[int]]) -> str:
    payload = json.dumps(rows, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii") + b"\n"
    return hashlib.sha256(payload).hexdigest()


def validate_trace(trace: dict, contract: dict) -> dict:
    require(trace.get("fidelity") == "ADAPTED",
            "slice choreography lost its ADAPTED label")
    require(contract.get("schema") == 1 and
            contract.get("fidelity") == "ADAPTED" and
            contract.get("actor_id") == 31 and
            contract.get("class_id") == 31,
            "render identity contract header drifted")
    samples = trace["samples"]
    phase_results = {}
    for name in ("WALK", "HIT", "RECOVERY", "KO"):
        expected = contract["phases"][name]
        selected = [sample for sample in samples if phase(sample) == name]
        rows = [identity_row(sample) for sample in selected]
        require(len(rows) == expected["sample_count"],
                f"{name} rendered identity sample count drifted")
        require(digest(rows) == expected["sequence_sha256"],
                f"{name} rendered object/tile identity sequence drifted")
        require(sorted({sample["slice_enemy_animation_record"]
                        for sample in selected}) ==
                expected["animation_records"],
                f"{name} animation-record family drifted")
        require(sorted({sample["slice_enemy_palette_bank"]
                        for sample in selected}) == expected["palette_banks"],
                f"{name} palette family drifted")
        require(all(sample["slice_enemy_object_count"] > 0 and
                    sample["slice_enemy_object_identity"] != 0 and
                    sample["slice_enemy_tile_identity"] != 0
                    for sample in selected),
                f"{name} contains an empty rendered identity")
        phase_results[name] = {
            "sample_count": len(rows),
            "sequence_sha256": digest(rows),
        }
    by_frame = {sample["slice_frame"]: sample for sample in samples}
    for anchor in contract["anchors"]:
        frame = anchor["frame"]
        require(frame in by_frame,
                f"render identity anchor frame {frame} is missing")
        actual = identity_row(by_frame[frame])
        require(actual == anchor["identity_row"],
                f"render identity anchor {frame} drifted")
    return {
        "result": "PASS",
        "contract_sha256": hashlib.sha256(
            json.dumps(contract, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True).encode("ascii") + b"\n").hexdigest(),
        "phases": phase_results,
    }


def mutation_is_rejected(trace: dict, contract: dict) -> bool:
    mutation = contract["negative_control"]
    altered = copy.deepcopy(trace)
    target = next(sample for sample in altered["samples"]
                  if sample["slice_frame"] == mutation["target_frame"])
    substitute = next(sample for sample in altered["samples"]
                      if sample["slice_frame"] ==
                      mutation["substitute_frame"])
    require(substitute["slice_enemy_object_identity"] != 0 and
            substitute["slice_enemy_tile_identity"] != 0,
            "mutation source is empty")
    target["slice_enemy_object_identity"] = \
        substitute["slice_enemy_object_identity"]
    target["slice_enemy_tile_identity"] = \
        substitute["slice_enemy_tile_identity"]
    try:
        validate_trace(altered, contract)
    except RuntimeError:
        return True
    return False
