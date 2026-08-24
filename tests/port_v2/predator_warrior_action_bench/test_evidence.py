#!/usr/bin/env python3
"""Validate paired SALVAGE-10 build and pinned-emulator evidence."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "contract.json").read_text())
    base = inventory["build_root"]
    builds = [load(f"{base}/run-{run}/build.json") for run in (1, 2)]
    normals = [load(f"{base}/run-{run}/iso-normalization.json") for run in (1, 2)]
    reads = [load(f"{base}/run-{run}/readback.json") for run in (1, 2)]
    assert builds[0]["result"] == builds[1]["result"] == "PASS"
    assert builds[0]["source_commit"] == builds[1]["source_commit"]
    assert builds[0]["compile_profile"] == builds[1]["compile_profile"] == inventory["compile_profile"]
    assert builds[0]["manifest_profile"] == builds[1]["manifest_profile"] == inventory["manifest_profile"]
    assert builds[0]["oracle04_sha256"] == builds[1]["oracle04_sha256"] == contract["oracle04_sha256"]
    assert builds[0]["oracle06_sha256"] == builds[1]["oracle06_sha256"] == contract["oracle06_sha256"]
    assert normals[0]["normalized_iso_sha256"] == normals[1]["normalized_iso_sha256"]
    assert reads[0]["samples"] == reads[1]["samples"]
    for build, normal, report in zip(builds, normals, reads):
        assert normal["production_payload_changed"] is False
        assert build["artifacts"]["game_iso"]["sha256"] == normal["normalized_iso_sha256"] == report["iso_sha256"]
        assert report["result"] == "PASS" and report["physical_saturn"] == "UNRUN"
        assert report["emulator"]["evidence_tier"] == "ONE_EMULATOR"
        state = report["state"]
        assert state["failures"] == 0 and state["canary_ok"] == 1
        assert state["accepted_edges"] == contract["expected_accepted_edges"]
        assert state["rejected_edges"] == contract["expected_rejected_edges"]
        assert state["contact_reports"] == contract["expected_contact_reports"]
        screenshot = ROOT / report["screenshot"]["path"]
        assert screenshot.is_file() and sha(screenshot) == report["screenshot"]["sha256"]
        with Image.open(screenshot) as image:
            colours = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
        assert colours is not None and len(colours) >= 2
    print(f"{inventory['card_profile']} evidence: PASS")


if __name__ == "__main__":
    main()
