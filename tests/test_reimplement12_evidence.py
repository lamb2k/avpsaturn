#!/usr/bin/env python3
"""Validate the committed REIMPLEMENT-12 evidence binding."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "reimplement12_source_closed_live_encounter.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["task"] == "REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER"
assert data["result"] == "ACCEPTED_TECHNICAL"
assert data["classification"] == [
    "TECHNICAL_PROTOTYPE", "ADAPTED_GAMEPLAY_SCAFFOLD",
    "NOT_SOURCE_CLOSED", "NOT_USER_APPROVED"]
assert sha(ROOT / "data/spec01_first_live_encounter_executable_contract.json") == data["implementation"]["spec01_sha256"]
for relative, expected in data["implementation"]["source_sha256"].items():
    assert sha(ROOT / relative) == expected, relative
assert data["validation"]["lanes"] == {
    "Fast":"PASS", "Oracle":"PASS", "Target":"BUILD_ONLY_PASS",
    "Emulator":"PASS"}
emulator = data["validation"]["emulator"]
assert emulator["cold_runs"] == 2 and emulator["sample_count_each"] == 471
assert emulator["exact_semantic_equality"] is True
assert emulator["chronology"] == {
    "player_contacts":4, "alien_contacts":1, "player_damage_events":1,
    "misses":1, "hit_events":3, "ko_events":1, "unlock_frame":450}
assert emulator["final"] == {
    "runtime_ready":1, "interface_version":2, "contract_flags":127,
    "route_unlocked":1, "continued_after_unlock":1, "failures":0,
    "fallback_count":0, "canaries_ok":1}
assert len(data["validation"]["rejected_real_mutations"]) == 10
assert data["remaining"] == [
    "QA-12 complete source/Saturn semantic and visual consistency matrix",
    "renewed USER-09 explicit review"]
assert data["physical_saturn"] == "UNRUN"
print("REIMPLEMENT-12 committed evidence binding: PASS")
