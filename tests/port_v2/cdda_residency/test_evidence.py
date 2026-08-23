#!/usr/bin/env python3
"""Validate paired target and pinned-emulator PROMOTE-07 evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "build/port_v2/cdda_residency"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(run: int, name: str) -> dict:
    return json.loads((OUTPUT / f"run-{run}/{name}").read_text(
        encoding="ascii"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    contract = json.loads((HERE / "contract.json").read_text(encoding="utf-8"))
    builds = [load(run, "build.json") for run in (1, 2)]
    normals = [load(run, "iso-normalization.json") for run in (1, 2)]
    reads = [load(run, "readback.json") for run in (1, 2)]
    require(builds[0]["source_commit"] == builds[1]["source_commit"] and
            builds[0]["source_tree"] == builds[1]["source_tree"],
            "paired promotion source identity drifted")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "promotion ISO repeat is not deterministic")
    require(builds[0]["linked_work_ram_high_water"] ==
            builds[1]["linked_work_ram_high_water"] and
            builds[0]["approved_contract_sha256"] ==
            builds[1]["approved_contract_sha256"],
            "high-water or approved locks drifted")
    for report, build, normal in zip(reads, builds, normals):
        require(report["result"] == "PASS" and
                report["human_review"] == "APPROVED" and
                report["physical_saturn"] == "UNRUN",
                "promotion result or evidence tier drifted")
        require(report["source_commit"] == build["source_commit"] and
                report["iso_sha256"] == build["artifacts"]["game_iso"]["sha256"] and
                report["track_audio_sha256"] ==
                contract["source_audio"]["sha256"],
                "promotion source/build/audio identity mismatch")
        require(normal["production_payload_changed"] is False and
                normal["normalized_iso_sha256"] == report["iso_sha256"],
                "normalization changed promotion payloads")
        final = report["samples"]["stable"]
        for group in (contract["expected_final"],
                      contract["promotion_expected"]):
            for name, expected in group.items():
                require(final[name] == expected,
                        f"promotion final {name} drifted")
        screenshot = ROOT / report["final_scanout"]["screenshot"]["path"]
        require(screenshot.is_file() and sha256(screenshot) ==
                report["final_scanout"]["screenshot"]["sha256"],
                "promotion diagnostic screenshot drifted")
    for label in reads[0]["samples"]:
        left = {key: value for key, value in reads[0]["samples"][label].items()
                if key != "emulator_frame"}
        right = {key: value for key, value in reads[1]["samples"][label].items()
                 if key != "emulator_frame"}
        require(left == right, f"promotion semantic repeat drifted at {label}")
    print("CddaResidencyPromotionBench evidence: PASS")


if __name__ == "__main__":
    main()
