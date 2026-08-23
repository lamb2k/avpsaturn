#!/usr/bin/env python3
"""Validate the pinned rendered-identity contract and its mutation control."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module():
    path = HERE / "render_identity.py"
    spec = importlib.util.spec_from_file_location("render_identity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    contract = json.loads(
        (HERE / "render_identity_contract.json").read_text(encoding="utf-8"))
    require(contract["schema"] == 1 and contract["fidelity"] == "ADAPTED",
            "render identity contract header drifted")
    require(set(contract["phases"]) == {"WALK", "HIT", "RECOVERY", "KO"},
            "render identity phases drifted")
    require(all(entry["sample_count"] > 0 and
                len(entry["sequence_sha256"]) == 64 and
                entry["animation_records"] and entry["palette_banks"]
                for entry in contract["phases"].values()),
            "a rendered identity phase is not pinned")
    by_frame = {entry["frame"]: entry for entry in contract["anchors"]}
    mutation = contract["negative_control"]
    require(mutation["target_frame"] in by_frame and
            mutation["substitute_frame"] in by_frame,
            "mutation frames are not exact anchors")
    target = by_frame[mutation["target_frame"]]["identity_row"]
    substitute = by_frame[mutation["substitute_frame"]]["identity_row"]
    require(target[-2] != 0 and target[-1] != 0 and
            substitute[-2] != 0 and substitute[-1] != 0 and
            target[-2:] != substitute[-2:],
            "wrong-family mutation is empty or indistinguishable")
    module = load_module()
    require(module.digest([target]) != module.digest([substitute]),
            "wrong nonzero object/tile family mutation was accepted")
    print("INTEGRATE-03 exact rendered street-alien identity contract: PASS")


if __name__ == "__main__":
    main()
