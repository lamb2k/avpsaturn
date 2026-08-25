#!/usr/bin/env python3
"""Committed-artifact and field-family mutation controls for SPEC-01."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "spec01_first_live_encounter_executable_contract.json"
SPEC = importlib.util.spec_from_file_location(
    "spec01", ROOT / "tools" / "build_spec01_encounter_contract.py")
assert SPEC and SPEC.loader
spec01 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec01)


def reject(mutant: dict, label: str) -> None:
    try:
        spec01.validate(mutant)
        spec01.execute_fixtures(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted SPEC-01 negative control: {label}")


report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
spec01.validate(report)
spec01.execute_fixtures(report)
spec01.mutation_self_test(report)

for family, mutation in (
    ("player_action_equipment", ("player", "close_combo", "automatic_selector_cycle", True)),
    ("projection", ("navigation", "screen_projection", "world_z_sign", 1)),
    ("navigation", ("navigation", "coffee_shop_player", "world_x_max", 1200)),
    ("alien_state_presentation", ("alien", "right_to_left_crossing", "facing", 1)),
    ("collision_damage", ("collision", "alien_attack_contact",
                          "maximum_measured_contact_distance_x", 160)),
    ("encounter_authority", ("encounter", "clear", "presentation_can_clear", True)),
    ("diagnostic_observability", ("diagnostics",
                                  "alien_overlay_updates_on_state_or_health_change", None, False)),
):
    mutant = copy.deepcopy(report)
    if mutation[2] is None:
        mutant[mutation[0]][mutation[1]] = mutation[3]
    else:
        mutant[mutation[0]][mutation[1]][mutation[2]] = mutation[3]
    reject(mutant, family)

unknown = copy.deepcopy(report)
unknown["field_contracts"][0]["guard"] = "UNKNOWN fallback"
reject(unknown, "required UNKNOWN behavior")

saturn = copy.deepcopy(report)
saturn["physical_saturn"] = "PASS"
reject(saturn, "unearned physical Saturn claim")

rebuilt = spec01.build_report()
assert spec01.canonical(rebuilt) == ARTIFACT.read_bytes(), "derived SPEC-01 drift"
print("SPEC-01 executable encounter contract tests: PASS")
