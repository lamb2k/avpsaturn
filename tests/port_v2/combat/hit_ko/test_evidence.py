#!/usr/bin/env python3
"""Validate paired target and pinned-emulator V2-B1 evidence."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inventory = json.loads((HERE / "inventory.json").read_text())
    base = inventory["build_root"]
    builds = [load(f"{base}/run-{run}/build.json") for run in (1, 2)]
    normals = [load(f"{base}/run-{run}/iso-normalization.json") for run in (1, 2)]
    reads = [load(f"{base}/run-{run}/readback.json") for run in (1, 2)]
    assert builds[0]["result"] == builds[1]["result"] == "PASS"
    assert builds[0]["source_commit"] == builds[1]["source_commit"]
    assert builds[0]["compile_profile"] == builds[1]["compile_profile"] == inventory["compile_profile"]
    assert builds[0]["manifest_profile"] == builds[1]["manifest_profile"] == inventory["manifest_profile"]
    assert builds[0]["approved_lock_sha256"] == builds[1]["approved_lock_sha256"]
    assert normals[0]["normalized_iso_sha256"] == normals[1]["normalized_iso_sha256"]
    assert reads[0]["state"] == reads[1]["state"]
    for build, normal, report in zip(builds, normals, reads):
        assert normal["production_payload_changed"] is False
        assert build["artifacts"]["game_iso"]["sha256"] == normal["normalized_iso_sha256"] == report["iso_sha256"]
        assert report["result"] == "PASS" and report["physical_saturn"] == "UNRUN"
        assert report["emulator"]["evidence_tier"] == "ONE_EMULATOR"
        state = report["state"]
        assert state["complete"] == state["runtime_ready"] == state["canary_ok"] == 1
        assert state["negative_rejections"] == 1 and state["failures"] == 0
        assert state["hit_samples"] == 37 and state["ko_samples"] == 140
        screenshot = ROOT / report["screenshot"]["path"]
        assert screenshot.is_file() and sha(screenshot) == report["screenshot"]["sha256"]
        with Image.open(screenshot) as image:
            colours = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
        assert colours is not None and len(colours) >= 2
    print("HitKoPromotionBench paired evidence: PASS")


if __name__ == "__main__":
    main()
