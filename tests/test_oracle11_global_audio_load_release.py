#!/usr/bin/env python3
"""Mutation controls for the global gameplay-audio/load/release checkpoint."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "oracle11_global_audio_load_release.json"
SPEC = importlib.util.spec_from_file_location(
    "oracle11_global_audio", ROOT / "tools" /
    "analyze_oracle11_global_audio_load_release.py")
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def reject(mutant: dict, label: str) -> None:
    try:
        oracle.validate(mutant)
    except ValueError:
        return
    raise AssertionError(f"accepted global-audio mutation: {label}")


report = json.loads(ARTIFACT.read_text(encoding="ascii"))
oracle.validate(report)

mutant = copy.deepcopy(report)
mutant["status"] = "SOURCE_CLOSED"
reject(mutant, "premature global closure")

mutant = copy.deepcopy(report)
mutant["accepted_subcheckpoint"]["source_routine"] = "0x0abdd2..0x0abe18"
reject(mutant, "score routine substituted for shared drain")

mutant = copy.deepcopy(report)
first_writer = next(iter(mutant["accepted_subcheckpoint"]["shared_payload_writers"].values()))
first_writer["count"] = 1160
reject(mutant, "missing shared payload transaction")

mutant = copy.deepcopy(report)
mutant["accepted_subcheckpoint"]["semantic_sound_names_inferred"] = True
reject(mutant, "semantic sound name inferred")

mutant = copy.deepcopy(report)
mutant["remaining_audio_trigger_backlog"]["provenance_groups"] = 174
reject(mutant, "closed trigger group hidden")

mutant = copy.deepcopy(report)
mutant["remaining_audio_trigger_backlog"]["orphan_trigger_groups"] = 1
reject(mutant, "orphan trigger owner hidden")

mutant = copy.deepcopy(report)
mutant["accepted_audio_cpu_subcheckpoints"][0]["transactions_in_each_completion"] = 1160
reject(mutant, "shared command ingress dropped")

mutant = copy.deepcopy(report)
mutant["accepted_audio_cpu_subcheckpoints"][1]["writes_per_port_in_each_completion"] = 489833
reject(mutant, "QSound-bus primitive write dropped")

mutant = copy.deepcopy(report)
mutant["remaining_transport_backlog"]["classification"] = "PARTIAL"
reject(mutant, "closed audio command handlers reopened")

mutant = copy.deepcopy(report)
mutant["accepted_audio_cpu_subcheckpoints"][2]["orphan_handler_paths"] = 1
reject(mutant, "orphan audio handler hidden")

mutant = copy.deepcopy(report)
mutant["load_release_backlog"]["boundary_frames"].pop()
reject(mutant, "load/release boundary dropped")

mutant = copy.deepcopy(report)
mutant["score_negative_control"]["accepted_as_audio_owner"] = True
reject(mutant, "score-only routine admitted")

mutant = copy.deepcopy(report)
mutant["protected_boundaries"]["spec02_active"] = True
reject(mutant, "SPEC-02 activated")

print("ORACLE-11 global audio/load/release tests: PASS (13 mutations rejected)")
