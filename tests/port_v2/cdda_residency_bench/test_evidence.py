#!/usr/bin/env python3
"""Validate paired CddaResidencySalvageBench target and emulator evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="ascii"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    contract = json.loads((HERE / "contract.json").read_text(encoding="utf-8"))
    builds = [load(f"build/port_v2/cdda_residency_bench/run-{run}/build.json")
              for run in (1, 2)]
    normals = [load(f"build/port_v2/cdda_residency_bench/run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(f"build/port_v2/cdda_residency_bench/run-{run}/readback.json")
             for run in (1, 2)]
    require(builds[0]["source_commit"] == builds[1]["source_commit"] and
            builds[0]["source_tree"] == builds[1]["source_tree"],
            "paired source identity drifted")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized CDDA/residency ISO is not deterministic")
    require(builds[0]["iso_members"] == builds[1]["iso_members"] and
            builds[0]["linked_work_ram_high_water"] ==
            builds[1]["linked_work_ram_high_water"],
            "paired fixture or linked high-water drifted")
    require(builds[0]["approved_contract_sha256"] ==
            builds[1]["approved_contract_sha256"],
            "approved-component locks drifted")
    for report, build, normalization in zip(reads, builds, normals):
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN" and
                report["human_review"] == "PENDING",
                "result failed or evidence tier was overstated")
        require(report["emulator"]["evidence_tier"] == "ONE_EMULATOR" and
                report["emulator"]["identity"] ==
                "Yaba Sanshiro 1.20.37-2986eb",
                "pinned emulator identity drifted")
        require(report["source_commit"] == build["source_commit"] and
                report["iso_sha256"] == build["artifacts"]["game_iso"]["sha256"] and
                report["cue_sha256"] == build["artifacts"]["game_cue"]["sha256"] and
                report["track_audio_sha256"] ==
                contract["source_audio"]["sha256"],
                "readback/build/track identity mismatch")
        require(normalization["production_payload_changed"] is False and
                normalization["normalized_iso_sha256"] ==
                build["artifacts"]["game_iso"]["sha256"],
                "ISO normalization changed payloads")
        require(report["track_command"]["command_returned"] is True and
                report["track_command"]["track"] == 2,
                "Track 2 command did not return")
        final = report["samples"]["stable"]
        for name, expected in contract["expected_final"].items():
            require(final[name] == expected,
                    f"final {name} drifted")
        require(report["bounded_stability_frames"] > 0,
                "bounded repeat was not observed")
        screenshot = ROOT / report["final_scanout"]["screenshot"]["path"]
        require(screenshot.is_file() and sha256(screenshot) ==
                report["final_scanout"]["screenshot"]["sha256"],
                "diagnostic screenshot missing or changed")
    for label in reads[0]["samples"]:
        left = {key: value for key, value in reads[0]["samples"][label].items()
                if key != "emulator_frame"}
        right = {key: value for key, value in reads[1]["samples"][label].items()
                 if key != "emulator_frame"}
        require(left == right, f"paired semantic state drifted at {label}")
    print("CddaResidencySalvageBench evidence: PASS")


if __name__ == "__main__":
    main()
