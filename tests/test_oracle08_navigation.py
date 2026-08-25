#!/usr/bin/env python3
"""Committed-artifact and mutation controls for ORACLE-08."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle08_round1_navigation_bounds.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle08", ROOT / "tools" / "analyze_oracle08_navigation.py")
assert SPEC and SPEC.loader
oracle08 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle08)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle08.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-08 negative control: {label}")


report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
oracle08.validate(report)
oracle08.mutation_self_test(report)

widened = copy.deepcopy(report)
widened["boundary_counterfactuals"]["left"]["result"]["end"]["x"] = 840
reject(widened, "widened left bound")

obstacle = copy.deepcopy(report)
obstacle["boundary_counterfactuals"]["right_obstacle"]["result"]["end"]["x"] = 1184
reject(obstacle, "bypassed Coffee Shop obstacle")

terrain = copy.deepcopy(report)
terrain["boundary_counterfactuals"]["up"]["result"]["end"]["z"] = 352
reject(terrain, "removed terrain boundary")

screen = copy.deepcopy(report)
screen["walkable_shape"]["rectangular_screen_clamp"] = True
reject(screen, "arbitrary screen-space clamp")

enemy = copy.deepcopy(report)
enemy["enemy_boundary_counterfactuals"]["beyond_right"]["accepted_next_tick"]["x"] = 1184
reject(enemy, "shared player/enemy clamp")

saturn = copy.deepcopy(report)
saturn["physical_saturn"] = "PASS"
reject(saturn, "unearned physical Saturn claim")

rebuilt = oracle08.build_report()
assert oracle08.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-08 navigation/bounds tests: PASS")
