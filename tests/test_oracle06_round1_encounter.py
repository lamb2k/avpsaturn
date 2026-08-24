#!/usr/bin/env python3
"""Deterministic artifact and negative-control checks for ORACLE-06."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle06_round1_encounter.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle06", ROOT / "tools" / "analyze_oracle06_encounter.py")
assert SPEC and SPEC.loader
oracle06 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle06)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle06.validate_report(mutant)
    except AssertionError:
        return
    raise AssertionError(f"accepted ORACLE-06 negative control: {label}")


report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
oracle06.validate_report(report)
assert oracle06.canonical(report) == ARTIFACT.read_bytes(), "artifact is not canonical"

timer = copy.deepcopy(report)
timer["adapted_first_live_contract"]["clear"]["authority"] = "timer"
reject(timer, "timer-only clear")

presentation = copy.deepcopy(report)
presentation["adapted_first_live_contract"]["clear"]["authority"] = "presentation"
reject(presentation, "presentation-owned clear")

spawn = copy.deepcopy(report)
spawn["adapted_first_live_contract"]["spawn"]["slot"] = "0xffa0c0"
reject(spawn, "incorrect spawn")

unlock = copy.deepcopy(report)
unlock["adapted_first_live_contract"]["camera_unlock"]["required"] = False
reject(unlock, "missing camera unlock")

continuation = copy.deepcopy(report)
continuation["adapted_first_live_contract"]["continuation"]["required"] = False
reject(continuation, "missing continuation")

rebuilt = oracle06.build_report()
assert oracle06.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-06 round1 encounter tests: PASS")
