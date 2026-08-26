#!/usr/bin/env python3
"""Mutation controls for the global audio command-handler checkpoint."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data/oracle11_global_audio_handlers.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_global_audio_handlers", ROOT / "tools" /
    "analyze_oracle11_global_audio_handlers.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted global-handler mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["coverage"]["orphan_shared_commands"] = 1
reject(mutant, "orphan shared command")

mutant = copy.deepcopy(report)
mutant["coverage"]["command_identities"] = 71
reject(mutant, "missing command identity")

mutant = copy.deepcopy(report)
mutant["handler_paths"]["orphan_paths"] = 1
reject(mutant, "orphan handler path")

mutant = copy.deepcopy(report)
mutant["logical_event_granularity"]["individual_low_high_register_writes_are_logical_events"] = True
reject(mutant, "bus writes promoted to logical events")

mutant = copy.deepcopy(report)
mutant["command_transactions"][0]["semantic_sound_name"] = "guessed sound"
reject(mutant, "semantic sound name inferred")

mutant = copy.deepcopy(report)
mutant["command_transactions"][0]["classification"] = "OBSERVED"
reject(mutant, "command transaction downgraded")

mutant = copy.deepcopy(report)
mutant["remaining_global_family_backlog"]["family_source_closed"] = True
reject(mutant, "global family prematurely closed")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["predator_warrior"] = "PARTIAL"
reject(mutant, "Predator Warrior reopened")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["packed_bcd_score_routine"] = "QSound"
reject(mutant, "score routine relabeled")

print("ORACLE-11 global audio handler tests: PASS (9 mutations rejected)")
