#!/usr/bin/env python3
"""Mutation controls for the committed Predator Warrior audio boundary."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_predator_player_audio.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_player_audio", ROOT / "tools" / "analyze_oracle11_player_audio.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted player-audio mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "PARTIAL"
reject(mutant, "player audio downgraded")

mutant = copy.deepcopy(report)
mutant["coverage"]["distinct_trigger_edges"] = 37
reject(mutant, "missing trigger edge")

mutant = copy.deepcopy(report)
mutant["trigger_edges"][0]["caller_provenance"]["shared_dispatch_entry"] = "0x0abdd2"
reject(mutant, "score routine substituted for dispatcher")

mutant = copy.deepcopy(report)
mutant["trigger_edges"][0]["mutation"]["downstream_qsound_difference"] = None
reject(mutant, "non-discriminating mutation")

mutant = copy.deepcopy(report)
mutant["trigger_edges"][0]["mutation"]["gameplay_invariants"]["projectile_state"] = False
reject(mutant, "projectile coupling introduced")

mutant = copy.deepcopy(report)
mutant["trigger_edges"][0]["semantic_sound_name_inferred"] = True
reject(mutant, "semantic sound name inferred")

mutant = copy.deepcopy(report)
mutant["boundary"]["global_transport_owner"] = "predator-warrior-player-authority"
reject(mutant, "global transport assigned to player")

mutant = copy.deepcopy(report)
mutant["score_negative_control"]["classification"] = "QSOUND_AUTHORITY"
reject(mutant, "packed-BCD routine relabeled audio")

mutant = copy.deepcopy(report)
mutant["score_negative_control"]["timing_or_temporal_adjacency_used"] = True
reject(mutant, "timing used for audio ownership")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["spec02_active"] = True
reject(mutant, "SPEC-02 activated")

print("ORACLE-11 player-audio tests: PASS (10 mutations rejected)")
