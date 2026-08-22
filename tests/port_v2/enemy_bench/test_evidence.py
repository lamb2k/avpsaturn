#!/usr/bin/env python3
"""Validate paired EnemySalvageBench build and pinned-emulator evidence."""

import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load(relative: str):
    return json.loads((ROOT / relative).read_text())


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    contract = json.loads((HERE / "enemy_contract.json").read_text())
    builds = [load(f"build/port_v2/enemy_bench/run-{run}/build.json") for run in (1, 2)]
    normals = [load(f"build/port_v2/enemy_bench/run-{run}/iso-normalization.json") for run in (1, 2)]
    reads = [load(f"build/port_v2/enemy_bench/run-{run}/readback.json") for run in (1, 2)]
    require(builds[0]["source_commit"] == builds[1]["source_commit"], "source commit drifted")
    require(normals[0]["normalized_iso_sha256"] == normals[1]["normalized_iso_sha256"], "normalized ISO is not deterministic")
    require(builds[0]["tile_archive"] == builds[1]["tile_archive"] == {"bytes":297764,"sha256":contract["tile_archive_sha256"]}, "tile archive drifted")
    for report in reads:
        require(report["result"] == "PASS" and report["physical_saturn"] == "UNRUN", "evidence tier/result drifted")
        require(report["bounded_stability_frames"] > 0, "repeat interval absent")
        for label, expected in contract["samples"].items():
            state = report["samples"][label]
            require((state["relative_frame"],state["phase"],state["x"]) == (expected["frame"],expected["phase"],expected["x"]), f"schedule drifted: {label}")
            require((state["class_id"],state["palette_bank"],state["lane"],state["facing"]) == (31,17,200,-1), f"source actor drifted: {label}")
            require(state["render_count"] >= state["object_count"] > 0 and state["negative_rejections"] == 2, f"render/control drifted: {label}")
        screenshot = ROOT / report["final_scanout"]["screenshot"]["path"]
        require(hashlib.sha256(screenshot.read_bytes()).hexdigest() == report["final_scanout"]["screenshot"]["sha256"], "screenshot changed")
        with Image.open(screenshot) as image:
            require(image.width > 300 and image.height > 200, "screenshot is empty")
    print("EnemySalvageBench evidence: PASS")


if __name__ == "__main__":
    main()
