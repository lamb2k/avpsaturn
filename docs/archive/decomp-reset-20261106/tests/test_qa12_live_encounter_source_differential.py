#!/usr/bin/env python3
"""Validate the accepted QA-12 evidence and status shields."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/qa12_live_encounter_source_differential.json"
REIMPLEMENT = ROOT / "data/reimplement12_source_closed_live_encounter.json"
VISUAL = ROOT / "build/feedback/QA-12-source-differential"
CANDIDATE = "e23733545af0bebe1f9ae26c4f391a9080c7006f"
TREE = "ebc54deb94a0d5c6a826b63ab9e3b36ec9b70828"
ISO = "8e20cb7e8c482035578422d8d1734cd9713adfc525ac5bf7c6dd8eade386bea8"
CLASSIFICATION = ["TECHNICAL_PROTOTYPE", "ADAPTED_GAMEPLAY_SCAFFOLD",
                  "NOT_SOURCE_CLOSED", "NOT_USER_APPROVED"]


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = json.loads(REPORT.read_text())
require(report["task"] == "QA-12-LIVE-ENCOUNTER-SOURCE-DIFFERENTIAL" and
        report["result"] == "ACCEPTED_TECHNICAL", "QA-12 result drift")
require(report["classification"] == CLASSIFICATION,
        "top-level non-approval classification changed")
require(report["candidate"] == {
    "commit": CANDIDATE,
    "source_tree": TREE,
    "iso_sha256": ISO,
    "spec01_sha256": "a8a8d5ff06d70a8df4cc7687928e0eb5200927ac8901adb3eb76745c4b42bd0f",
}, "QA candidate identity drift")
require(report["validation"]["lanes"] == {
    "Fast": "PASS", "Oracle": "PASS", "Target": "BUILD_ONLY_PASS",
    "Emulator": "PASS"}, "required QA lanes incomplete")
matrix = report["validation"]["scenario_matrix"]
require(matrix["scenario_count"] == 34 and matrix["cadence_frames"] == 471 and
        matrix["cadence_sha256"] ==
        "2693b9c29b7418b90837cc0a59f198314b75de9d5e9d5bfaac92c81f59521008" and
        matrix["host_saturn_exact"] and matrix["paired_saturn_exact"],
        "QA semantic matrix drift")
require(set(matrix["rejected_mutations"]) == {
    "wrong-facing", "weapon-discontinuity", "wall-traversal",
    "alien-family-substitution", "unsupported-contact", "runtime-failure"},
    "QA mutation shield incomplete")

# The raw run slots are ignored, reusable working evidence.  Later bounded
# repairs must not invalidate frozen QA-12 merely by recording a new candidate
# in those paths.  Bind the accepted pair through the tracked QA report and its
# exact cadence digest instead.
emulator = report["validation"]["emulator"]
require(emulator == {
    "identity": "Yaba Sanshiro 1.20.37-2986eb",
    "cold_runs": 2,
    "sample_count_each": 471,
    "chronology": {
        "alien_contact": 98,
        "authored_miss": 162,
        "player_contacts": [235, 258, 282, 310],
        "route_unlock": 450,
        "last_evidence_frame": 470,
    },
    "failures": 0,
    "fallback_count": 0,
    "canaries_ok": 1,
}, "QA-12 frozen emulator evidence drift")

artifact_names = {
    "full_sequence_webp": "saturn-corrected-full-sequence.webp",
    "temporal_strip_png": "saturn-corrected-temporal-strip.png",
    "collision_overlays_png": "saturn-collision-origin-overlays.png",
    "actor_state_crops_png": "saturn-actor-state-crops.png",
    "state_contact_timeline_png": "saturn-state-contact-timeline.png",
}
for key, name in artifact_names.items():
    path = VISUAL / name
    require(path.is_file() and digest(path) ==
            report["validation"]["visual"]["artifacts"][key],
            f"visual artifact missing or changed: {name}")

reimplement = json.loads(REIMPLEMENT.read_text())
require(reimplement["implementation"]["evidence_head"] == CANDIDATE and
        reimplement["implementation"]["source_tree"] == TREE and
        reimplement["validation"]["emulator"]["iso_sha256"] == ISO,
        "REIMPLEMENT correction was not bound to QA candidate")
require(report["next"] == "renewed USER-09 explicit review only" and
        report["physical_saturn"] == "UNRUN", "next-card or hardware shield drift")
print("QA-12 live-encounter source differential: PASS")
