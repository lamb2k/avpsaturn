#!/usr/bin/env python3
"""Mutation controls for the ORACLE-11 player HIT/KO checkpoint."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_hitko_continue.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_hitko", ROOT / "tools" /
    "analyze_oracle11_player_hitko_continue.py")
assert SPEC and SPEC.loader
oracle11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle11)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle11.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted HIT/KO mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle11.validate(report)

for path, value, label in (
    (("lethal_ko", "required_action_phases"),
     ["0x0202", "0x0800", "0x0404"], "fitted KO phases"),
    (("lethal_ko", "final_countdown_ticks"), 59, "short KO countdown"),
    (("failure_continue", "direction_only_confirms"), True,
     "direction-only confirmation"),
    (("failure_continue", "coin_without_start_confirms"), True,
     "coin-only confirmation"),
    (("respawn_return", "health_and_latched_health"), 100,
     "fitted respawn health"),
    (("respawn_return", "return_to_control_frame"), 6785,
     "fixed-frame control return drift"),
    (("nonlethal_hit", "return_to_control_frame"), 6856,
     "HIT recovery drift"),
    (("nonlethal_hit", "rng_consumption"), "one call", "HIT RNG"),
):
    mutant = copy.deepcopy(report)
    mutant[path[0]][path[1]] = value
    reject(mutant, label)

mutant = copy.deepcopy(report)
mutant["counterfactuals"]["health_50_suppresses_lethal_ko"] = False
reject(mutant, "health threshold control")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["yaba_run"] = True
reject(mutant, "Yaba execution")

rebuilt = oracle11.build_report()
assert oracle11.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-11 player HIT/KO tests: PASS (10 mutations rejected)")
