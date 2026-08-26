#!/usr/bin/env python3
"""Mutation controls for global non-player audio trigger ownership."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data/oracle11_global_audio_trigger_owners.json"
SPEC = importlib.util.spec_from_file_location("owners", ROOT / "tools" /
    "analyze_oracle11_global_audio_trigger_owners.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(oracle)

def reject(mutant, label):
    try: oracle.validate(mutant)
    except ValueError: return
    raise AssertionError(f"accepted trigger-owner mutation: {label}")

report = json.loads(ARTIFACT.read_text(encoding="ascii")); oracle.validate(report)
mutant = copy.deepcopy(report); mutant["status"] = "PARTIAL"; reject(mutant, "status")
mutant = copy.deepcopy(report); mutant["coverage"]["trigger_groups"] = 174; reject(mutant, "group hidden")
mutant = copy.deepcopy(report); mutant["coverage"]["orphan_source_callers"] = 1; reject(mutant, "caller orphan")
mutant = copy.deepcopy(report); mutant["trigger_groups"].pop(); reject(mutant, "body removed")
mutant = copy.deepcopy(report); mutant["trigger_groups"][0]["transition_guard"]["contexts"] = []; reject(mutant, "guard removed")
mutant = copy.deepcopy(report); mutant["trigger_groups"][0]["semantic_sound_name"] = "guessed"; reject(mutant, "semantic guess")
mutant = copy.deepcopy(report); mutant["trigger_groups"][0]["handler_transaction"]["individual_bus_writes_are_logical_events"] = True; reject(mutant, "bus write event")
mutant = copy.deepcopy(report); mutant["remaining_global_family_backlog"]["family_source_closed"] = True; reject(mutant, "premature family closure")
mutant = copy.deepcopy(report); mutant["protected_boundaries"]["spec02_active"] = True; reject(mutant, "SPEC-02")
print("ORACLE-11 global audio trigger-owner tests: PASS (9 mutations rejected)")
