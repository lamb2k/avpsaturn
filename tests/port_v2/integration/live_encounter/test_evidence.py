#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent
inventory=json.loads((HERE/"inventory.json").read_text()); base=inventory["build_root"]
def load(path): return json.loads((ROOT/path).read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
builds=[load(f"{base}/run-{n}/build.json") for n in (1,2)]
normals=[load(f"{base}/run-{n}/iso-normalization.json") for n in (1,2)]
reads=[load(f"{base}/run-{n}/readback.json") for n in (1,2)]
visual=load(f"{base}/visual-qa.json")
assert builds[0]["source_commit"] == builds[1]["source_commit"]
assert normals[0]["normalized_iso_sha256"] == normals[1]["normalized_iso_sha256"]
assert reads[0]["samples"] == reads[1]["samples"]
for build,normal,report in zip(builds,normals,reads):
    assert build["result"] == report["result"] == "PASS"
    assert normal["production_payload_changed"] is False
    assert build["artifacts"]["game_iso"]["sha256"] == normal["normalized_iso_sha256"] == report["iso_sha256"]
    assert report["source_commit"] == build["source_commit"] and report["physical_saturn"] == "UNRUN"
    assert report["chronology"]["player_contacts"] >= 4 and report["chronology"]["alien_contacts"] >= 1
    assert report["visual_scanout"] == "UNAVAILABLE_WINDOWS_ACCELERATED_SURFACE"
assert visual["source_commit"] == builds[0]["source_commit"] and visual["result"] == "PASS"
assert 180 <= visual["gameplay_frame"] <= 320
image=ROOT/visual["screenshot"]["path"]
assert image.is_file() and sha(image) == visual["screenshot"]["sha256"]
assert visual["capture_method"] == "Windows.Graphics.Capture via @oai/sky"
assert visual["physical_saturn"] == "UNRUN"
print("INTEGRATE-04A paired live encounter emulator evidence: PASS")
