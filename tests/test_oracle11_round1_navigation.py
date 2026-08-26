#!/usr/bin/env python3
"""Mutation controls for the Round 1 navigation closure checkpoint."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_round1_navigation.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_navigation", ROOT / "tools" /
    "analyze_oracle11_round1_navigation.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted navigation mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "navigation family reopened")

mutant = copy.deepcopy(report)
mutant["capture_identity"]["byte_identical"] = False
reject(mutant, "non-deterministic baselines admitted")

mutant = copy.deepcopy(report)
mutant["capture_identity"]["perturbation_discriminated_navigation"] = False
reject(mutant, "non-discriminating perturbation admitted")

mutant = copy.deepcopy(report)
mutant["global_bounds"]["source_routine"] = "guessed rectangle"
reject(mutant, "rectangular fallback substituted for source bounds")

mutant = copy.deepcopy(report)
del mutant["global_bounds"]["writer_pcs"]["0x01b030"]
reject(mutant, "right clamp writer orphaned")

mutant = copy.deepcopy(report)
mutant["terrain_resolver"]["records"].pop()
reject(mutant, "route terrain record dropped")

mutant = copy.deepcopy(report)
mutant["terrain_resolver"]["records"][0]["source_program_match"] = False
reject(mutant, "captured terrain record detached from source data")

mutant = copy.deepcopy(report)
response = next(item for item in mutant["terrain_resolver"]["records"]
                if item["address"] == "0x0b20d6")
response["perturbed_calls"]["0x0b1c68"] = 0
reject(mutant, "discriminating terrain response removed")

mutant = copy.deepcopy(report)
mutant["navigation_bodies"]["instances"].pop()
reject(mutant, "navigation class/type body orphaned")

mutant = copy.deepcopy(report)
mutant["navigation_bodies"]["instances"][0]["complete_actor_authority"] = \
    "SOURCE_CLOSED"
reject(mutant, "destruction/presentation authority silently absorbed")

mutant = copy.deepcopy(report)
mutant["navigation_bodies"]["instances"][0]["source_block_sha256"] = "0" * 64
reject(mutant, "type-20 source routine detached")

mutant = copy.deepcopy(report)
mutant["camera"]["primary_writer"] = "fixed frame"
reject(mutant, "fixed-frame camera substitute admitted")

mutant = copy.deepcopy(report)
mutant["camera"]["camera_lock_and_unlock_runs"].pop()
reject(mutant, "camera edge orphaned")

mutant = copy.deepcopy(report)
mutant["closure"]["guessed_camera_guards"] = 1
reject(mutant, "guessed camera guard hidden")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["spec02_active"] = True
reject(mutant, "SPEC-02 activated")

print("ORACLE-11 Round 1 navigation tests: PASS (15 mutations rejected)")
