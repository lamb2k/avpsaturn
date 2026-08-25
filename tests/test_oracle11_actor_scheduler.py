#!/usr/bin/env python3
"""Committed identity and negative controls for the first ORACLE-11 family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_scheduler", ROOT / "tools" / "analyze_oracle11_actor_scheduler.py")
assert SPEC and SPEC.loader
oracle11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle11)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle11.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-11 scheduler mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle11.validate(report)

mutant = copy.deepcopy(report)
mutant["pools"][0]["stride"] = 0x80
reject(mutant, "type-12 stride")

mutant = copy.deepcopy(report)
mutant["frame_scheduler"]["required_round1_order"] = [12, 20, 16, 24]
reject(mutant, "pool update order")

mutant = copy.deepcopy(report)
mutant["pools"][0]["required_round1_dispatch"] = []
reject(mutant, "dispatch mapping removed")

mutant = copy.deepcopy(report)
mutant["pools"][2]["release"]["order"] = "FIFO"
reject(mutant, "free-list order")

mutant = copy.deepcopy(report)
mutant["closure"]["classification"] = "PARTIAL"
reject(mutant, "unclosed classification")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["user09_status"] = "ACCEPTED"
reject(mutant, "inferred USER-09 approval")

rebuilt = oracle11.build_report()
assert oracle11.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-11 actor scheduler/lifecycle tests: PASS (6 mutations rejected)")
