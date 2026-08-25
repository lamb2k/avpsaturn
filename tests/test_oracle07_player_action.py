#!/usr/bin/env python3
"""Committed-artifact and mutation controls for ORACLE-07."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle07_predator_warrior_action_graph_equipment.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle07", ROOT / "tools" / "analyze_oracle07_player_action.py")
assert SPEC and SPEC.loader
oracle07 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle07)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle07.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-07 negative control: {label}")


report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
oracle07.validate(report)
oracle07.mutation_self_test(report)

selector = copy.deepcopy(report)
selector["action_graph"]["close_button2"]["attack_selectors"] = [1, 4, 2, 3]
reject(selector, "arbitrary selector order")

held = copy.deepcopy(report)
held["combo_contract"]["edge_semantics"]["held_button"] = "auto-repeat"
reject(held, "held input auto-chain")

weapon = copy.deepcopy(report)
weapon["negative_controls"]["visible_weapon_inference_from_equipment_flag_forbidden"] = False
reject(weapon, "visible weapon inferred from action-local flag")

saturn = copy.deepcopy(report)
saturn["physical_saturn"] = "PASS"
reject(saturn, "unearned physical Saturn claim")

rebuilt = oracle07.build_report()
assert oracle07.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-07 player action/equipment tests: PASS")
