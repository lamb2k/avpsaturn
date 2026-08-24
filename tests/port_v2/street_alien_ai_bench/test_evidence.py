#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load(relative):
    return json.loads((ROOT / relative).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inventory = json.loads((HERE / "inventory.json").read_text())
contract = json.loads((HERE / "contract.json").read_text())
base = inventory["build_root"]
builds = [load(f"{base}/run-{run}/build.json") for run in (1,2)]
normals = [load(f"{base}/run-{run}/iso-normalization.json") for run in (1,2)]
reads = [load(f"{base}/run-{run}/readback.json") for run in (1,2)]
assert builds[0]["source_commit"] == builds[1]["source_commit"]
assert builds[0]["oracle05_sha256"] == builds[1]["oracle05_sha256"] == contract["oracle05_sha256"]
assert normals[0]["normalized_iso_sha256"] == normals[1]["normalized_iso_sha256"]
assert reads[0]["samples"] == reads[1]["samples"]
for build, normal, report in zip(builds, normals, reads):
    assert build["result"] == report["result"] == "PASS"
    assert normal["production_payload_changed"] is False
    assert build["artifacts"]["game_iso"]["sha256"] == normal["normalized_iso_sha256"] == report["iso_sha256"]
    assert report["source_commit"] == build["source_commit"]
    assert report["physical_saturn"] == "UNRUN" and report["emulator"]["evidence_tier"] == "ONE_EMULATOR"
    assert report["state"]["contacts"] == report["state"]["damage_events"] == 3
    screenshot = ROOT / report["screenshot"]["path"]
    assert screenshot.is_file() and sha(screenshot) == report["screenshot"]["sha256"]
    with Image.open(screenshot) as image:
        colours = image.convert("RGB").getcolors(maxcolors=image.width*image.height)
    assert colours is not None and len(colours) >= 2
print("StreetAlienAiSalvageBench evidence: PASS")
