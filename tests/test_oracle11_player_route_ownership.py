#!/usr/bin/env python3
"""Mutation controls for Predator route interaction/resource ownership."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_route_ownership.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_route_ownership",
    ROOT / "tools" / "analyze_oracle11_player_route_ownership.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted route-ownership mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "status downgrade")

mutant = copy.deepcopy(report)
mutant["action_phase_reconciliation"]["unmapped_player_phases"] = ["0x0e00"]
reject(mutant, "unmapped interaction phase")

mutant = copy.deepcopy(report)
mutant["health_pickup"]["natural_witness"]["health_after"] = 96
reject(mutant, "fitted health result")

mutant = copy.deepcopy(report)
mutant["temporary_resource_pickup"]["grant"]["value"] = 599
reject(mutant, "fitted resource timer")

mutant = copy.deepcopy(report)
mutant["temporary_resource_pickup"]["natural_route_classification"] = "SOURCE_CLOSED"
reject(mutant, "unreached resource pickup called required")

mutant = copy.deepcopy(report)
mutant["interaction_action_and_interruption"]["natural_completion"]["last"] = 4058
reject(mutant, "fitted interaction completion")

mutant = copy.deepcopy(report)
mutant["audio_ownership"]["route_audio_owner"] = "predator-warrior-player-authority"
reject(mutant, "route audio assigned to player")

mutant = copy.deepcopy(report)
mutant["load_release_ownership"]["bulk_loader_uses_player_actor_base"] = True
reject(mutant, "bulk loader assigned to player")

mutant = copy.deepcopy(report)
mutant["remaining_player_unknowns"] = ["load writer"]
reject(mutant, "player unknown admitted")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["yaba_runs"] = 1
reject(mutant, "Yaba run admitted")

rebuilt = oracle.build_report()
assert oracle.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived report drift"
print("ORACLE-11 player route-ownership tests: PASS (10 mutations rejected)")
