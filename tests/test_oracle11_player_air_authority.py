#!/usr/bin/env python3
"""ORACLE-11 Predator Warrior air authority mutation controls."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_air_authority.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_air", ROOT / "tools" /
    "analyze_oracle11_player_air_authority.py")
assert SPEC and SPEC.loader
oracle11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle11)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle11.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted ORACLE-11 air mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle11.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "air family downgraded")

mutant = copy.deepcopy(report)
mutant["coverage_universe"]["required_route_phases"].remove("0x0406")
reject(mutant, "route-reachable Button1 air phase omitted")

mutant = copy.deepcopy(report)
mutant["coverage_universe"]["required_counterfactual_phases"].remove("0x0410")
reject(mutant, "midair Down+Button2 phase omitted")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["button1"]["writer"] = "0x02385e"
reject(mutant, "wrong airborne Button1 writer")

mutant = copy.deepcopy(report)
mutant["airborne_actions"]["rng_consumption"] = "one selector call"
reject(mutant, "air action RNG introduced")

mutant = copy.deepcopy(report)
mutant["counterfactuals"]["air_button2_hold_no_auto_repeat"] = False
reject(mutant, "held Button2 auto-repeat admitted")

mutant = copy.deepcopy(report)
mutant["counterfactuals"]["natural_hit_cancels_directional_air"] = False
reject(mutant, "air interruption omitted")

mutant = copy.deepcopy(report)
del mutant["not_required_for_round1"]["phases"]["0x0414"]
reject(mutant, "unreachable table body silently omitted")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["yaba_run"] = True
reject(mutant, "Yaba workflow violation")

rebuilt = oracle11.build_report()
assert oracle11.canonical(rebuilt) == ARTIFACT.read_bytes(), \
    "derived air authority report drift"
print("ORACLE-11 player air authority tests: PASS (9 mutations rejected)")
