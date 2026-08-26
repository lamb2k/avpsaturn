#!/usr/bin/env python3
"""Validate paired deterministic Round 1 startup-authority evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
contract = json.loads((ROOT / "data/reimplement13_startup_authority.json").read_text())
runs = [json.loads((ROOT / f"build/port_v2/round1_startup/run-{run}/readback.json").read_text())
        for run in (1, 2)]
for report in runs:
    assert report["result"] == "PASS"
    assert report["physical_saturn"] == "UNRUN"
    assert report["state"]["retained_before_handoff"] == 0
    assert report["state"]["p2_visible_frames"] == 0
    assert report["state"]["hidden_contacts"] == 0
    assert report["state"]["hidden_damage"] == 0
    assert report["state"]["orphan_pcm"] == 0
    assert report["state"]["duplicate_cdda"] == 0
    assert report["state"]["cdda_starts"] == 1
    assert report["state"]["first_pcm_frame"] == -1
assert runs[0]["iso_sha256"] == runs[1]["iso_sha256"]
assert runs[0]["main_sha256"] == runs[1]["main_sha256"]
assert runs[0]["trace"] == runs[1]["trace"]
assert runs[0]["state"] == runs[1]["state"]
assert runs[0]["final_scanout"]["sha256"] == runs[1]["final_scanout"]["sha256"]
assert runs[0]["emulator"]["executable_sha256"] == runs[1]["emulator"]["executable_sha256"]
inspection = contract["paired_emulator_inspection"]
assert inspection["iso_sha256"] == runs[0]["iso_sha256"]
assert inspection["main_sha256"] == runs[0]["main_sha256"]
assert inspection["saturn_scanout_sha256"] == runs[0]["final_scanout"]["sha256"]
assert contract["source_chronology"]["p2_gameplay_hud_visible"] is False
assert contract["rejected_p2_inference"]["p1_weapon_meter_asset"] == "/SPR8/HUDHEAT.BIN"
assert contract["observed_saturn_cue_diagnosis"]["semantic_sound_name_inferred"] is False
print("REIMPLEMENT-13 paired startup-authority emulator evidence: PASS")
